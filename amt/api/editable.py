import logging
import typing
from collections.abc import Generator
from enum import StrEnum
from typing import Any, Final, cast

from starlette.requests import Request

from amt.api.editable_converters import (
    EditableConverter,
    EditableConverterForOrganizationInAlgorithm,
    StatusConverterForSystemcard,
)
from amt.api.editable_enforcers import EditableEnforcer, EditableEnforcerForOrganizationInAlgorithm
from amt.api.editable_validators import EditableValidator, EditableValidatorMinMaxLength, EditableValidatorSlug
from amt.api.lifecycles import get_localized_lifecycles
from amt.api.routes.shared import UpdateFieldModel, nested_value
from amt.core.exceptions import AMTNotFound
from amt.models import Algorithm, Organization
from amt.models.base import Base
from amt.schema.webform import WebFormFieldImplementationType, WebFormFieldImplementationTypeFields, WebFormOption
from amt.services.algorithms import AlgorithmsService
from amt.services.organizations import OrganizationsService

type EditableType = Editable
type ResolvedEditableType = ResolvedEditable


class Editable:
    """
    Editable contains all basic information for editing a field in a resources, like changing the name
    of an algorithm.

    It requires the 'full_resource_path' in a resolvable format, like algorithm/{algorithm_id}/system_card/name.
    The implementation_type tells how this field can be edited using WebFormFieldImplementationType, like a 'plain'
    TEXT field or SELECT_MY_ORGANIZATIONS.
    The couples links fields together, if one is changed, so is the other.
    The children field is for editing multiple fields at one (to be implemented).
    The enforcer checks permissions and business rules.
    The converter converts data between read and write when needed.
    """

    full_resource_path: Final[str]

    def __init__(
        self,
        full_resource_path: str,
        implementation_type: WebFormFieldImplementationTypeFields,
        couples: set[EditableType] | None = None,
        children: set[EditableType] | None = None,
        converter: EditableConverter | None = None,
        enforcer: EditableEnforcer | None = None,
        validator: EditableValidator | None = None,
    ) -> None:
        self.full_resource_path = full_resource_path
        self.implementation_type = implementation_type
        self.couples = set[EditableType]() if couples is None else couples
        self.children = set[EditableType]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator

    def add_bidirectional_couple(self, target: EditableType) -> None:
        """
        Changing an editable may require an update on another field as well, like when changing the name
        of an algorithm; this is stored in two different places. Making it a couple ensures both values are
        updated when one is changed.
        :param target: the target editable type
        :return: None
        """
        self.couples.add(target)
        target.couples.add(self)

    def add_child(self, target: EditableType) -> None:
        """
        An editable can be a container (parent) for other elements.
        :param target: the target editable type
        :return: None
        """
        self.children.add(target)


class ResolvedEditable:
    value: Any | None
    # TODO: find out of holding resource_object in memory for many editables is wise / needed
    resource_object: Any | None
    relative_resource_path: str | None
    form_options: list[WebFormOption] | None

    def __init__(
        self,
        # fields copied from the Editable class
        full_resource_path: str,
        implementation_type: WebFormFieldImplementationTypeFields,
        couples: set[ResolvedEditableType] | None = None,
        children: set[ResolvedEditableType] | None = None,
        converter: EditableConverter | None = None,
        enforcer: EditableEnforcer | None = None,
        validator: EditableValidator | None = None,
        # resolved only fields
        value: str | None = None,
        resource_object: Base | None = None,
        relative_resource_path: str | None = None,
    ) -> None:
        self.full_resource_path = full_resource_path
        self.implementation_type = implementation_type
        self.couples = set[ResolvedEditableType]() if couples is None else couples
        self.children = set[ResolvedEditableType]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator
        # resolved only fields
        self.value = value
        self.resource_object = resource_object
        self.relative_resource_path = relative_resource_path


class Editables:
    ALGORITHM_EDITABLE_NAME: Editable = Editable(
        full_resource_path="algorithm/{algorithm_id}/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_NAME = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
    )
    ALGORITHM_EDITABLE_NAME.add_bidirectional_couple(ALGORITHM_EDITABLE_SYSTEMCARD_NAME)

    ALGORITHM_EDITABLE_SYSTEMCARD_MODEL = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
    )

    ALGORITHM_EDITABLE_AUTHOR = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/provenance/author",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )
    # TODO: parent below is not yet implemented
    ALGORITHM_EDITABLE_SYSTEMCARD_OWNERS = Editable(
        full_resource_path="DISABLED_algorithm/{algorithm_id}/system_card/owners[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children={
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/organization",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/oin",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        },
    )

    ALGORITHM_EDITABLE_ORGANIZATION = Editable(
        full_resource_path="algorithm/{algorithm_id}/organization",
        implementation_type=WebFormFieldImplementationType.SELECT_MY_ORGANIZATIONS,
        enforcer=EditableEnforcerForOrganizationInAlgorithm(),
        converter=EditableConverterForOrganizationInAlgorithm(),
    )
    ALGORITHM_EDITABLE_DESCRIPTION = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/description",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )
    ALGORITHM_EDITABLE_LIFECYCLE = Editable(
        full_resource_path="algorithm/{algorithm_id}/lifecycle",
        implementation_type=WebFormFieldImplementationType.SELECT_LIFECYCLE,
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_STATUS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/status",
        implementation_type=WebFormFieldImplementationType.SELECT_LIFECYCLE,
        converter=StatusConverterForSystemcard(),
    )
    ALGORITHM_EDITABLE_LIFECYCLE.add_bidirectional_couple(ALGORITHM_EDITABLE_SYSTEMCARD_STATUS)

    ORGANIZATION_NAME = Editable(
        full_resource_path="organization/{organization_id}/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
    )

    ORGANIZATION_SLUG = Editable(
        full_resource_path="organization/{organization_id}/slug",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorSlug(),
    )

    # TODO: rethink if this is a wise solution.. we do this to keep all elements in 1 class and still
    #  be able to execute other code (like making relationships)
    def __iter__(self) -> Generator[tuple[str, Any], Any, Any]:
        yield from [
            getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))
        ]


editables = Editables()


class SafeDict(dict[str, str | int]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class EditModes(StrEnum):
    EDIT = "EDIT"
    VIEW = "VIEW"
    SAVE = "SAVE"


async def get_enriched_resolved_editable(
    context_variables: dict[str, str | int],
    full_resource_path: str,
    edit_mode: EditModes,
    algorithms_service: AlgorithmsService | None = None,
    organizations_service: OrganizationsService | None = None,
    user_id: str | None = None,
    request: Request | None = None,
) -> ResolvedEditable:
    """
    Using the given full_resource_path, resolves the resource and current value.
    For example, using /algorithm/1/systemcard/info, the value of the info field and the resource,
    being an algorithm object, are available. The first is used in 'get' situations, the resource_object
    can be used to store a new value.

    May raise an AMTNotFound error in case a resource can not be found.

    :param edit_mode: the edit mode
    :param request: the current request
    :param user_id: the current user
    :param context_variables: a dictionary of context variables, f.e. {'algorithm_id': 1}
    :param full_resource_path: the full path of the resource, e.g. /algorithm/1/systemcard/info
    :param algorithms_service: the algorithm service
    :param organizations_service:  the organization service
    :return: a ResolvedEditable instance enriched with the requested resource and current value
    """

    editable = get_resolved_editables(context_variables=context_variables).get(full_resource_path)
    if not editable:
        logging.error(f"Unknown editable for path: {full_resource_path}")
        raise AMTNotFound()

    return await enrich_editable(
        editable,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        edit_mode=edit_mode,
        user_id=user_id,
        request=request,
    )


async def enrich_editable(  # noqa: C901
    editable: ResolvedEditable,
    edit_mode: EditModes,
    algorithms_service: AlgorithmsService | None = None,
    organizations_service: OrganizationsService | None = None,
    user_id: str | None = None,
    request: Request | None = None,
) -> ResolvedEditable:
    resource_name, resource_id, relative_resource_path = editable.full_resource_path.split("/", 2)
    editable.relative_resource_path = relative_resource_path
    match resource_name:
        case "algorithm":
            if algorithms_service is None:
                raise ValueError("Algorithms service is required when resolving an algorithm")
            editable.resource_object = await algorithms_service.get(int(resource_id))
        case "organization":
            if organizations_service is None:
                raise ValueError("Organization service is required when resolving an organization")
            editable.resource_object = await organizations_service.get_by_id(int(resource_id))
        case _:
            logging.error(f"Unknown resource: {resource_name}")
            raise AMTNotFound()

    editable.value = nested_value(editable.resource_object, relative_resource_path)
    for child_editable in editable.children:
        await enrich_editable(
            child_editable,
            edit_mode=edit_mode,
            algorithms_service=algorithms_service,
            organizations_service=organizations_service,
            user_id=user_id,
            request=request,
        )
    for couple_editable in editable.couples:
        await enrich_editable(
            couple_editable,
            edit_mode=edit_mode,
            algorithms_service=algorithms_service,
            organizations_service=organizations_service,
            user_id=user_id,
            request=request,
        )

    # TODO: can we move this to the editable object instead of here?
    if edit_mode == EditModes.EDIT:
        if editable.implementation_type == WebFormFieldImplementationType.SELECT_MY_ORGANIZATIONS:
            if organizations_service is None:
                raise ValueError("Organization service is required when resolving an organization")
            my_organizations = await organizations_service.get_organizations_for_user(user_id=user_id)
            editable.form_options = [
                WebFormOption(value=str(organization.id), display_value=organization.name)
                for organization in my_organizations
            ]
        elif editable.implementation_type == WebFormFieldImplementationType.SELECT_LIFECYCLE:
            if algorithms_service is None:
                raise ValueError("Algorithms service is required when resolving an algorithm")
            if request is None:
                raise ValueError("Request is required when resolving a lifecycle")
            editable.form_options = [
                WebFormOption(value=str(lifecycle.value), display_value=lifecycle.display_value)
                for lifecycle in get_localized_lifecycles(request)
                if lifecycle is not None
            ]

    return editable


def get_resolved_editables(context_variables: dict[str, str | int]) -> dict[str, ResolvedEditable]:
    """
    Returns a list of all known editables with the resource path resolved using the given context_variables.
    :param context_variables: a dictionary of context variables, f.e. {'algorithm_id': 1}
    :return: a dict of resolved editables, with the resolved path as key
    """
    editables_resolved: list[ResolvedEditable] = []

    def resolve_editable_path(
        editable: Editable, context_variables: dict[str, str | int], include_couples: bool
    ) -> ResolvedEditable:
        couples = None
        if include_couples:
            couples = {resolve_editable_path(couple, context_variables, False) for couple in editable.couples}
        children = {resolve_editable_path(child, context_variables, True) for child in editable.children}

        return ResolvedEditable(
            full_resource_path=editable.full_resource_path.format_map(SafeDict(context_variables)),
            implementation_type=editable.implementation_type,
            couples=couples,
            children=children,
            converter=editable.converter,
            enforcer=editable.enforcer,
            validator=editable.validator,
        )

    for editable in editables:
        editables_resolved.append(
            resolve_editable_path(
                editable=cast(EditableType, editable), context_variables=context_variables, include_couples=True
            )
        )
    return {editable.full_resource_path: editable for editable in editables_resolved}


async def save_editable(  # noqa: C901
    editable: ResolvedEditable,
    update_data: UpdateFieldModel,
    editable_context: dict[str, Any],
    do_save: bool,
    algorithms_service: AlgorithmsService | None = None,
    organizations_service: OrganizationsService | None = None,
) -> ResolvedEditable:
    # we validate on 'raw' form fields, so validation is done before the converter
    # TODO: validate all fields (child and couples) before saving!
    if editable.validator and editable.relative_resource_path is not None:
        await editable.validator.validate(update_data.value, editable.relative_resource_path)

    if editable.enforcer:
        await editable.enforcer.enforce(**editable_context)

    editable.value = update_data.value
    if editable.converter:
        editable.value = await editable.converter.write(editable.value, **editable_context)

    if editable.relative_resource_path is None or editable.value is None:
        raise TypeError("Cannot save editable without a relative_resource_path or value")
    set_path(editable.resource_object, editable.relative_resource_path, editable.value)

    # TODO: child objects not implemented, this should be done later

    for couple_editable in editable.couples:
        # if couples are within the same resource_object, only 1 save is required
        do_save_couple = editable.resource_object != couple_editable.resource_object
        await save_editable(
            couple_editable,
            update_data=update_data,
            editable_context=editable_context,
            algorithms_service=algorithms_service,
            organizations_service=organizations_service,
            do_save=do_save_couple,
        )

    if do_save:
        match editable.resource_object:
            case Algorithm():
                if algorithms_service is None:
                    raise ValueError("Algorithms service is required when saving an algorithm")
                editable.resource_object = await algorithms_service.update(editable.resource_object)
            case Organization():
                if organizations_service is None:
                    raise ValueError("Organization service is required when saving an organization")
                editable.resource_object = await organizations_service.update(editable.resource_object)
            case _:
                logging.error(f"Unknown resource type: {type(editable.resource_object)}")
                raise AMTNotFound()

    return editable


def set_path(algorithm: dict[str, Any] | object, path: str, value: typing.Any) -> None:  # noqa: ANN401
    if not path:
        raise ValueError("Path cannot be empty")

    attrs = path.lstrip("/").split("/")
    obj: Any = algorithm
    for attr in attrs[:-1]:
        if isinstance(obj, dict):
            obj = cast(dict[str, Any], obj)
            if attr not in obj:
                obj[attr] = {}
            obj = obj[attr]
        else:
            if not hasattr(obj, attr):
                setattr(obj, attr, {})
            obj = getattr(obj, attr)

    if isinstance(obj, dict):
        obj[attrs[-1]] = value
    else:
        setattr(obj, attrs[-1], value)
