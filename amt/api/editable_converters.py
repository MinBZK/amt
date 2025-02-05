from typing import Any, Final

from amt.api.lifecycles import Lifecycles
from amt.core.exceptions import AMTAuthorizationError
from amt.models import Organization


class EditableConverter:
    """
    Converters are meant for converting data between read, write and view when needed.
    An example is choosing an organization, the input value is the organization_id,
    but the needed 'write' value is the organization object, the view value is
    the name.
    """

    async def read(self, in_value: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        return in_value

    async def write(self, in_value: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        return in_value

    async def view(self, in_value: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        return in_value


class EditableConverterForOrganizationInAlgorithm(EditableConverter):
    async def read(self, in_value: Organization, **kwargs: Any) -> Any:  # noqa: ANN401
        return in_value.id

    async def write(self, in_value: str, **kwargs: Any) -> Organization:  # noqa: ANN401
        organization = await kwargs["organizations_service"].find_by_id_and_user_id(
            organization_id=int(in_value), user_id=kwargs["user_id"]
        )
        if organization is None:
            raise AMTAuthorizationError()
        return organization

    async def view(self, in_value: Organization, **kwargs: Any) -> str:  # noqa: ANN401
        return in_value.name


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

    async def read(self, in_value: str, **kwargs: Any) -> Any:  # noqa: ANN401
        # we want to do a case-insensitive lookup, so we make own loop
        for key, lifecycle in self.phases.items():
            if key.casefold() == in_value.casefold():
                return lifecycle.value
        return None

    async def write(self, in_value: str, **kwargs: Any) -> str:  # noqa: ANN401
        return next((k for k, v in self.phases.items() if v.value == in_value), "Unknown")
