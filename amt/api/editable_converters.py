from typing import Any, Final, cast

from starlette.requests import Request

from amt.api.editable_classes import EditableConverter, ResolvedEditable
from amt.api.lifecycles import Lifecycles
from amt.core.dynamic_translations import ExternalFieldsTranslations
from amt.models import Organization
from amt.schema.webform_classes import WebFormOption
from amt.services.authorization import AuthorizationsService
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider


class EditableConverterForAuthorizationRole(EditableConverter):
    async def view(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any | dict[str, Any]],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        if services_provider is None:
            raise TypeError("Services provider must be provided")
        authorizations_service = await services_provider.get(AuthorizationsService)
        role = await authorizations_service.get_role_by_id(int(in_value))
        display_value = ExternalFieldsTranslations.translate(role.name, request) if role else "Unknown"
        return WebFormOption(
            value=int(in_value),
            display_value=display_value,
        )

    async def read(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any | dict[str, Any]],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return await self.view(in_value, request, editable, editable_context, services_provider)

    async def write(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any | dict[str, Any]],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return await self.view(in_value, request, editable, editable_context, services_provider)


class EditableConverterForOrganizationInAlgorithm(EditableConverter):
    async def read(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any | dict[str, Any]],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return WebFormOption(
            value=str(cast(Organization, in_value).id), display_value=cast(Organization, in_value).name
        )

    async def write(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        if services_provider is None:
            raise TypeError("Services provider must be provided")
        organizations_service = await services_provider.get(OrganizationsService)
        organization = await organizations_service.find_by_id_and_user_id(
            organization_id=int(in_value), user_id=editable_context["user_id"]
        )
        return WebFormOption(value=organization, display_value=organization.name)

    async def view(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return WebFormOption(
            value=str(cast(Organization, in_value).id), display_value=cast(Organization, in_value).name
        )


class StatusConverterForSystemcard(EditableConverter):
    phases: Final[dict[str, Lifecycles]] = {
        "Organisatieverantwoordelijkheden": Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES,
        "Probleemanalyse": Lifecycles.PROBLEM_ANALYSIS,
        "Ontwerp": Lifecycles.DESIGN,
        "Dataverkenning en datapreparatie": Lifecycles.DATA_EXPLORATION_AND_PREPARATION,
        "Ontwikkelen": Lifecycles.DEVELOPMENT,
        "Verificatie en validatie": Lifecycles.VERIFICATION_AND_VALIDATION,
        "Implementatie": Lifecycles.IMPLEMENTATION,
        "Monitoring en beheer": Lifecycles.MONITORING_AND_MANAGEMENT,
        "Uitfaseren": Lifecycles.PHASING_OUT,
    }

    async def read(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None = None,
        editable: ResolvedEditable | None = None,
        editable_context: dict[str, Any] | None = None,
        services_provider: ServicesProvider | None = None,
    ) -> WebFormOption:
        # we want to do a case-insensitive lookup, so we make own loop
        for key, lifecycle in self.phases.items():
            if key.casefold() == in_value.casefold():
                return WebFormOption(value=lifecycle.value, display_value=lifecycle.name)
        return WebFormOption(value=in_value, display_value=in_value)

    async def write(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        result = next((k for k, v in self.phases.items() if v.value == in_value), "Unknown")
        return WebFormOption(value=result, display_value=in_value)
