import logging
import typing
from typing import Any, cast

from starlette.requests import Request

from amt.api.editable_classes import Editable, EditableType, EditModes, ResolvedEditable
from amt.api.editable_converters import EditableConverterForOrganizationInAlgorithm, StatusConverterForSystemcard
from amt.api.editable_enforcers import EditableEnforcerForOrganizationInAlgorithm
from amt.api.editable_util import (
    extract_number_and_string,
    replace_digits_in_brackets,
    replace_wildcard_with_digits_in_brackets,
)
from amt.api.editable_validators import EditableValidatorMinMaxLength, EditableValidatorSlug
from amt.api.lifecycles import get_localized_lifecycles
from amt.api.routes.shared import nested_value
from amt.api.utils import SafeDict
from amt.core.exceptions import AMTNotFound
from amt.models import Algorithm, Organization
from amt.schema.webform import WebFormFieldImplementationType, WebFormOption
from amt.services.algorithms import AlgorithmsService
from amt.services.organizations import OrganizationsService


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

    ALGORITHM_EDITABLE_SYSTEMCARD_OWNERS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/organization",
                implementation_type=WebFormFieldImplementationType.TEXT,
                validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/oin",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/name",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/email",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/owners[*]/role",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        ],
    )

    ALGORITHM_EDITABLE_SYSTEMCARD_LABELS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/labels[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/labels[*]/name",
                implementation_type=WebFormFieldImplementationType.TEXT,
                validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/labels[*]/value",
                implementation_type=WebFormFieldImplementationType.TEXT,
                validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
            ),
        ],
    )

    ALGORITHM_EDITABLE_SYSTEMCARD_REFERENCES = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/references[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/references[*]/name",
                implementation_type=WebFormFieldImplementationType.TEXT,
                validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/references[*]/link",
                implementation_type=WebFormFieldImplementationType.TEXT,
                validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
            ),
        ],
    )

    ALGORITHM_EDITABLE_SYSTEMCARD_LEGAL_BASE = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/legal_base[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/legal_base[*]/name",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/legal_base[*]/link",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        ],
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

    ALGORITHM_EDITABLE_PROVENANCE = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/provenance",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/provenance/author",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/provenance/git_commit_hash",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/provenance/uri",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        ],
    )

    ALGORITHM_EDITABLE_VERSION = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/version",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )

    ALGORITHM_EDITABLE_UPL = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/upl",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )

    ALGORITHM_EDITABLE_BEGIN_DATE = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/begin_date",
        implementation_type=WebFormFieldImplementationType.DATE,
    )

    ALGORITHM_EDITABLE_END_DATE = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/end_date",
        implementation_type=WebFormFieldImplementationType.DATE,
    )

    ALGORITHM_EDITABLE_GOAL_AND_IMPACT = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/goal_and_impact",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_CONSIDERATIONS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/considerations",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_RISK_MANAGEMENT = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/risk_management",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_RISK_HUMAN_INTERVENTION = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/human_intervention",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_PRODUCT_MARKINGS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/product_markings[*]",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_HARDWARE_REQUIREMENTS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/hardware_requirements[*]",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_DEPLOYMENT_VARIANTS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/deployment_variants[*]",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_RISK_VERSION_REQUIREMENTS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/version_requirements[*]",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_RISK_INTERACTION_DETAILS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/interaction_details[*]",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )

    ALGORITHM_EDITABLE_EXTERNAL_PROVIDERS = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/external_providers[*]",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_TECHNICAL_DESIGN = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/technical_design",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_USED_DATA = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/used_data",
        implementation_type=WebFormFieldImplementationType.TEXTAREA,
    )

    ALGORITHM_EDITABLE_USER_INTERFACE = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/user_interface[*]",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/user_interface[*]/description",
                implementation_type=WebFormFieldImplementationType.TEXTAREA,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/user_interface[*]/link",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/user_interface[*]/snapshot",
                implementation_type=WebFormFieldImplementationType.TEXT,
            ),
        ],
    )

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
    def __iter__(self) -> typing.Generator[tuple[str, Any], Any, Any]:
        yield from [
            getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))
        ]


editables = Editables()


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

    _, list_index = extract_number_and_string(full_resource_path)

    if list_index is not None:
        context_variables["list_index"] = list_index

    # TODO: it would be better to only resolve the required / requested editable and not everything
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

    if editable.implementation_type != WebFormFieldImplementationType.PARENT:
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

    def resolve_editable_path(
        editable: Editable, context_variables: dict[str, str | int], include_couples: bool
    ) -> ResolvedEditable:
        couples = None
        if include_couples:
            couples = {resolve_editable_path(couple, context_variables, False) for couple in editable.couples}
        children = [resolve_editable_path(child, context_variables, True) for child in editable.children]

        full_resource_path = editable.full_resource_path.format_map(SafeDict(context_variables))
        # TODO: maybe the list index should not be resolved here (for all possible editables)
        if "list_index" in context_variables:
            full_resource_path = replace_wildcard_with_digits_in_brackets(
                full_resource_path, int(context_variables["list_index"])
            )

        _, _, relative_resource_path = full_resource_path.split("/", 2)
        editable.relative_resource_path = relative_resource_path

        return ResolvedEditable(
            full_resource_path=full_resource_path,
            relative_resource_path=relative_resource_path,
            implementation_type=editable.implementation_type,
            couples=couples,
            children=children,
            converter=editable.converter,
            enforcer=editable.enforcer,
            validator=editable.validator,
        )

    editables_resolved: list[ResolvedEditable] = []

    for editable in editables:
        editables_resolved.append(
            resolve_editable_path(
                editable=cast(EditableType, editable), context_variables=context_variables, include_couples=True
            )
        )
    return {editable.full_resource_path: editable for editable in editables_resolved}


async def save_editable(  # noqa: C901
    editable: ResolvedEditable,
    editable_context: dict[str, Any],
    do_save: bool,
    algorithms_service: AlgorithmsService | None = None,
    organizations_service: OrganizationsService | None = None,
) -> ResolvedEditable:
    if editable.children:
        for child_editable in editable.children:
            # if couples are within the same resource_object, only 1 save is required
            do_save_child = editable.resource_object != child_editable.resource_object
            await save_editable(
                child_editable,
                editable_context=editable_context,
                algorithms_service=algorithms_service,
                organizations_service=organizations_service,
                do_save=do_save_child,
            )
    else:
        new_value = editable_context.get("new_values", {}).get(editable.last_path_item())

        # we validate on 'raw' form fields, so validation is done before the converter
        # TODO: validate all fields (child and couples) before saving!
        if editable.validator and editable.relative_resource_path is not None:
            await editable.validator.validate(new_value, editable)  # pyright: ignore[reportUnknownMemberType]

        if editable.enforcer:
            await editable.enforcer.enforce(**editable_context)

        editable.value = new_value
        if editable.converter:
            editable.value = await editable.converter.write(editable.value, **editable_context)

        if editable.relative_resource_path is None or editable.value is None:
            raise TypeError("Cannot save editable without a relative_resource_path or value")
        set_path(editable.resource_object, editable.relative_resource_path, editable.value)

    for couple_editable in editable.couples:
        # if couples are within the same resource_object, only 1 save is required
        do_save_couple = editable.resource_object != couple_editable.resource_object
        # couples may not have the same resource name, so we copy the new value with the associated resource name
        if couple_editable.last_path_item() not in editable_context.get("new_values", {}):
            editable_context.get("new_values", {}).update(
                {
                    couple_editable.last_path_item(): editable_context.get("new_values", {}).get(
                        editable.last_path_item()
                    ),
                }
            )
        await save_editable(
            couple_editable,
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


def set_path(obj: dict[str, Any] | object, path: str, value: typing.Any) -> None:  # noqa: ANN401, C901
    if not path:
        raise ValueError("Path cannot be empty")

    attrs = path.lstrip("/").split("/")
    for attr in attrs[:-1]:
        attr, index = extract_number_and_string(attr)
        if isinstance(obj, dict):
            obj = cast(dict[str, Any], obj)
            if attr not in obj:
                obj[attr] = {}
            obj = obj[attr]
        else:
            if not hasattr(obj, attr):  # pyright: ignore[reportUnknownArgumentType]
                setattr(obj, attr, {})  # pyright: ignore[reportUnknownArgumentType]
            obj = getattr(obj, attr)  # pyright: ignore[reportUnknownArgumentType]
        if obj and index is not None:
            obj = cast(list[Any], obj)[index]  # pyright: ignore[reportArgumentType, reportUnknownVariableType, reportUnknownArgumentType]

    if isinstance(obj, dict):
        obj[attrs[-1]] = value
    else:
        attr, index = extract_number_and_string(attrs[-1])
        if index is not None:
            cast(list[Any], getattr(obj, attr))[index] = value
        else:
            setattr(obj, attrs[-1], value)


def is_editable_resource(full_resource_path: str, editables: dict[str, ResolvedEditable]) -> bool:
    return editables.get(replace_digits_in_brackets(full_resource_path), None) is not None


def is_parent_editable(editables: dict[str, ResolvedEditable], full_resource_path: str) -> bool:
    full_resource_path = replace_digits_in_brackets(full_resource_path)
    editable = editables.get(full_resource_path)
    if editable is None:
        print(full_resource_path + " : " + "false, no match")
        return False
    result = editable.implementation_type == WebFormFieldImplementationType.PARENT
    print(full_resource_path + " : " + str(result))
    return result
