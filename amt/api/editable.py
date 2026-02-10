import logging
import re
from collections.abc import Generator
from functools import lru_cache
from typing import Any, cast

from starlette.requests import Request

from amt.api.editable_classes import Editable, EditModes, FormState, ResolvedEditable
from amt.api.editable_converters import (
    EditableConverterForAuthorizationRole,
    EditableConverterForOrganizationInAlgorithm,
    StatusConverterForSystemcard,
)
from amt.api.editable_enforcers import (
    EditableEnforcerForOrganizationInAlgorithm,
    EditableEnforcerMustHaveMaintainer,
    EditableEnforcerMustHaveMaintainerForLists,
)
from amt.api.editable_hooks import (
    PreConfirmAIActHook,
    RedirectMembersHook,
    RedirectOrganizationHook,
    SaveAuthorizationHook,
    UpdateAIActHook,
)
from amt.api.editable_util import (
    replace_wildcard_with_digits_in_brackets,
)
from amt.api.editable_validators import (
    EditableValidatorMinMaxLength,
    EditableValidatorMustHaveItems,
    EditableValidatorRequiredField,
    EditableValidatorSlug,
)
from amt.api.editable_value_providers import AIActValuesProvider, RolesValuesProvider
from amt.api.lifecycles import get_localized_lifecycles
from amt.api.routes.shared import nested_value
from amt.api.update_utils import extract_number_and_string, set_path
from amt.api.utils import SafeDict
from amt.core.exceptions import AMTNotFound
from amt.models import Algorithm, Authorization, Organization
from amt.schema.webform_classes import WebFormFieldImplementationType, WebFormOption
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider

logger = logging.getLogger(__name__)


class Editables:
    ROLE_EDITABLE: Editable = Editable(
        full_resource_path="authorization",
        implementation_type=WebFormFieldImplementationType.PARENT,
        validator=EditableValidatorMustHaveItems(),
        enforcer=EditableEnforcerMustHaveMaintainerForLists(),
        hooks={
            FormState.SAVE: SaveAuthorizationHook(),
            FormState.COMPLETED: RedirectMembersHook(),
        },
        children=[
            Editable(
                full_resource_path="authorization/user_id",
                implementation_type=WebFormFieldImplementationType.PRE_CHOSEN,
            ),
            Editable(
                full_resource_path="authorization/role_id",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=RolesValuesProvider(),
                converter=EditableConverterForAuthorizationRole(),
            ),
            Editable(
                full_resource_path="authorization/type", implementation_type=WebFormFieldImplementationType.HIDDEN
            ),
            Editable(
                full_resource_path="authorization/type_id",
                implementation_type=WebFormFieldImplementationType.HIDDEN,
            ),
        ],
    )

    AUTHORIZATION_ROLE = Editable(
        full_resource_path="authorization/{authorization_id}/role_id",
        implementation_type=WebFormFieldImplementationType.SELECT,
        values_provider=RolesValuesProvider(),
        converter=EditableConverterForAuthorizationRole(),
        enforcer=EditableEnforcerMustHaveMaintainer(),
    )

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
        hooks={FormState.POST_SAVE: RedirectOrganizationHook()},
    )

    ALGORITHM_EDITABLE_AIACT = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile",
        implementation_type=WebFormFieldImplementationType.PARENT,
        hooks={FormState.PRE_CONFIRM: PreConfirmAIActHook(), FormState.POST_SAVE: UpdateAIActHook()},
        children=[
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/role",
                implementation_type=WebFormFieldImplementationType.MULTIPLE_CHECKBOX_AI_ACT,
                values_provider=AIActValuesProvider(type="role"),
                validator=EditableValidatorRequiredField(),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/type",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="type"),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/open_source",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="open_source"),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/risk_group",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="risk_group"),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/conformity_assessment_body",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="conformity_assessment_body"),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/systemic_risk",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="systemic_risk"),
            ),
            Editable(
                full_resource_path="algorithm/{algorithm_id}/system_card/ai_act_profile/transparency_obligations",
                implementation_type=WebFormFieldImplementationType.SELECT,
                values_provider=AIActValuesProvider(type="transparency_obligations"),
            ),
        ],
    )

    # TODO: rethink if this is a wise solution.. we do this to keep all elements in 1 class and still
    #  be able to execute other code (like making relationships)
    def __iter__(self) -> Generator[tuple[str, Any], Any, Any]:
        yield from [
            getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))
        ]


editables = Editables()


async def get_enriched_resolved_editable(
    full_resource_path: str,
    edit_mode: EditModes,
    context_variables: dict[str, str | int],
    services_provider: ServicesProvider,
    request: Request | None = None,
) -> ResolvedEditable:
    """
    Using the given full_resource_path, resolves the resource and current value.
    For example, using /algorithm/1/systemcard/info, the value of the info field and the resource,
    being an algorithm object, are available. The first is used in 'get' situations, the resource_object
    can be used to store a new value.

    May raise an AMTNotFound error in case a resource can not be found.
    """

    _, list_index = extract_number_and_string(full_resource_path)

    if list_index is not None:
        context_variables["index"] = list_index

    # TODO: it would be better to only resolve the required / requested editable and not everything
    editable = get_resolved_editables(context_variables=context_variables).get(full_resource_path)
    if not editable:
        logger.error(f"Unknown editable for path: {full_resource_path}")
        raise AMTNotFound()

    return await enrich_editable(
        editable,
        edit_mode=edit_mode,
        editable_context=context_variables,
        services_provider=services_provider,
        request=request,
    )


def parse_resource_path(path: str) -> tuple[str | None, int | None, str | None]:
    parts = path.split("/")

    resource_name = parts[0] if parts[0] else None

    if len(parts) == 1:
        return resource_name, None, None

    try:
        resource_id = int(parts[1])
        relative_path = "/".join(parts[2:]) if len(parts) > 2 else None
    except (ValueError, IndexError):
        resource_id = None
        relative_path = "/".join(parts[1:]) if len(parts) > 1 else None
        if relative_path == "":
            relative_path = None

    return resource_name, resource_id, relative_path


async def enrich_editable(  # noqa: C901
    editable: ResolvedEditable,
    edit_mode: EditModes,
    editable_context: dict[str, Any],
    services_provider: ServicesProvider | None,
    request: Request | None = None,
    resource_object: Any | None = None,  # noqa: ANN401
) -> ResolvedEditable:
    resource_name, resource_id, relative_resource_path = parse_resource_path(editable.full_resource_path)
    editable.relative_resource_path = relative_resource_path
    if resource_object is not None:
        # if the object is provided, we copy it, it may be a custom object, but this depends
        #  on too many assumptions and maybe should be done differently
        editable.resource_object = resource_object
    elif edit_mode is not EditModes.SAVE_NEW:
        if services_provider is None or resource_id is None:
            raise TypeError("services_provider must be provided and resource_id can not be None")
        match resource_name:
            case "authorization":
                editable.resource_object = await (await services_provider.get(AuthorizationsService)).get_by_id(
                    resource_id
                )
            case "algorithm":
                algorithms_service = await services_provider.get(AlgorithmsService)
                editable.resource_object = await algorithms_service.get(resource_id)
            case "organization":
                editable.resource_object = await (await services_provider.get(OrganizationsService)).get_by_id(
                    resource_id
                )
            case _:
                logger.error(f"Unknown resource: {resource_name}")
                raise AMTNotFound()

    if editable.implementation_type != WebFormFieldImplementationType.PARENT and editable.resource_object is not None:
        if relative_resource_path is None:
            raise TypeError("relative_resource_path can not be None")
        current_value = nested_value(editable.resource_object, relative_resource_path)
        if editable.converter and current_value:
            current_value = await editable.converter.view(
                current_value, request, editable, editable_context, services_provider
            )
        if isinstance(current_value, WebFormOption):
            editable.value = current_value
        else:
            # TODO: this is most likely a text field
            editable.value = WebFormOption(value=current_value, display_value=current_value)

    for child_editable in editable.children:
        await enrich_editable(
            child_editable,
            edit_mode,
            editable_context,
            services_provider,
            request,
            resource_object,  # TODO this is a test, think of a better solution!!
        )
    for couple_editable in editable.couples:
        await enrich_editable(
            couple_editable,
            edit_mode,
            editable_context,
            services_provider,
            request,
            resource_object,  # TODO this is a test, think of a better solution!!
        )

    # TODO: can we move this to the editable object instead of here?
    # TODO: consider if values_providers could solve & replace the specific conditions below
    if edit_mode == EditModes.EDIT:
        if editable.values_provider:
            if request is None:
                raise TypeError("Request is required when resolving an 'editable values provider'")
            editable.form_options = await editable.values_provider.get_values(request)
        elif editable.implementation_type == WebFormFieldImplementationType.SELECT_MY_ORGANIZATIONS:
            if services_provider is None:
                raise TypeError("services_provider must be provided")
            user_id = editable_context.get("user_id")
            if user_id:
                my_organizations = await (await services_provider.get(OrganizationsService)).get_organizations_for_user(
                    user_id=user_id
                )
                editable.form_options = [
                    WebFormOption(value=str(organization.id), display_value=organization.name)
                    for organization in my_organizations
                ]
        elif editable.implementation_type == WebFormFieldImplementationType.SELECT_LIFECYCLE:
            if request is None:
                raise ValueError("Request is required when resolving a lifecycle")
            editable.form_options = [
                WebFormOption(value=str(lifecycle.value), display_value=lifecycle.display_value)
                for lifecycle in get_localized_lifecycles(request)
                if lifecycle is not None
            ]

    return editable


def get_resolved_editable(
    editable: Editable, context_variables: dict[str, Any], include_couples: bool
) -> ResolvedEditable:
    couples = None
    if include_couples:
        couples = [get_resolved_editable(couple, context_variables, False) for couple in editable.couples]
    children = [get_resolved_editable(child, context_variables, True) for child in editable.children]

    full_resource_path = editable.full_resource_path.format_map(SafeDict(context_variables))
    # TODO: maybe the list index should not be resolved here (for all possible editables)
    if "index" in context_variables:
        full_resource_path = replace_wildcard_with_digits_in_brackets(
            full_resource_path, int(context_variables["index"])
        )

    _, _, relative_resource_path = parse_resource_path(full_resource_path)

    return ResolvedEditable(
        full_resource_path=full_resource_path,
        relative_resource_path=relative_resource_path,
        implementation_type=editable.implementation_type,
        values_provider=editable.values_provider,
        couples=couples,
        children=children,
        converter=editable.converter,
        enforcer=editable.enforcer,
        validator=editable.validator,
        hooks=editable.hooks,
    )


@lru_cache(maxsize=1024)
def compile_extraction_pattern(editable_key: str) -> re.Pattern[str]:
    # First, escape any regex special characters except { } and *
    escaped_key = re.sub(r"([.^$+()[\]|])", r"\\\1", editable_key)
    # Convert placeholders to named capture groups
    pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+)", escaped_key)
    # Convert [*] to a capture group for indices
    pattern = re.sub(r"\\\[\*\\]", r"\\[(?P<index>\\d+)\\]", pattern)
    return re.compile(f"^{pattern}$")


def find_matching_editable(concrete_path: str) -> tuple[Editable, dict[str, str | Any]]:
    for editable in editables:
        pattern = compile_extraction_pattern(cast(Editable, editable).full_resource_path)
        match = pattern.match(concrete_path)
        if match:
            context_variables = match.groupdict()
            return cast(Editable, editable), context_variables
    logger.warning(f"Unable to find editable from path {concrete_path!r}")
    raise AMTNotFound


def get_resolved_editables(context_variables: dict[str, str | int]) -> dict[str, ResolvedEditable]:
    """
    Returns a list of all known editables with the resource path resolved using the given context_variables.
    :param context_variables: a dictionary of context variables, f.e. {'algorithm_id': 1}
    :return: a dict of resolved editables, with the resolved path as key
    """

    editables_resolved: list[ResolvedEditable] = []

    for editable in editables:
        editables_resolved.append(
            get_resolved_editable(
                editable=cast(Editable, editable), context_variables=context_variables, include_couples=True
            )
        )
    return {editable.full_resource_path: editable for editable in editables_resolved}


# TODO: this probably should be a method of ResolvedEditable
async def save_editable(  # noqa: C901
    editable: ResolvedEditable,
    editable_context: dict[str, Any],
    edit_mode: EditModes,
    request: Request,
    do_save: bool,
    services_provider: ServicesProvider,
) -> ResolvedEditable:
    if editable.children:
        for child_editable in editable.children:
            # if couples are within the same resource_object, only 1 save is required
            do_save_child = editable.resource_object != child_editable.resource_object
            await save_editable(
                child_editable,
                editable_context,
                edit_mode,
                request,
                do_save_child,
                services_provider,
            )
    else:
        field_name, index = extract_number_and_string(editable.last_path_item())
        new_values_dict = editable_context.get("new_values", {})

        if index is not None:
            index = 0  # TODO: the form post is always for one list item, so the index does not change
            new_value = new_values_dict.get(field_name, [])[index] if field_name in new_values_dict else None
        else:
            new_value = new_values_dict.get(editable.last_path_item())

        # we validate on 'raw' form fields, so validation is done before the converter
        if editable.validator and editable.relative_resource_path is not None:
            await editable.validator.validate(request, editable, editable_context, edit_mode, services_provider)

        if editable.enforcer:
            await editable.enforcer.enforce(request, editable, editable_context, edit_mode, services_provider)

        if editable.converter:
            editable.value = await editable.converter.write(
                new_value, request, editable, editable_context, services_provider
            )
            # Ensure the converted value is used for setting the path
            if editable.value and editable.value.value is not None:
                new_value = editable.value.value
        else:
            if new_value is None:
                raise TypeError("Cannot save editable without a new value")
            editable.value = WebFormOption(value=new_value, display_value=new_value)

        if editable.relative_resource_path is None:
            raise TypeError("Cannot save editable without a relative_resource_path")
        set_path(editable.resource_object, editable.relative_resource_path, editable.value.value)

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
            editable_context,
            edit_mode,
            request,
            do_save_couple,
            services_provider,
        )

    if do_save:
        match editable.resource_object:
            # TODO: this could be made more generic, using the service provider directly and adding
            #  an update function to each service
            case Authorization():
                editable.resource_object = await (await services_provider.get(AuthorizationsService)).update(
                    editable.resource_object
                )
            case Algorithm():
                editable.resource_object = await (await services_provider.get(AlgorithmsService)).update(
                    editable.resource_object
                )
            case Organization():
                editable.resource_object = await (await services_provider.get(OrganizationsService)).update(
                    editable.resource_object
                )
            case _:
                # For custom dictionaries or other types in tests, don't raise an error
                if isinstance(editable.resource_object, dict):
                    pass  # Dictionary resource objects are allowed for testing
                else:
                    logger.error(f"Unknown resource type: {type(editable.resource_object)}")
                    raise AMTNotFound()

    return editable
