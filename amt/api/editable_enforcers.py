from abc import ABC, abstractmethod
from typing import Any

from amt.core.exceptions import AMTAuthorizationError


class EditableEnforcer(ABC):
    """
    Enforcers are meant for checking authorization permissions and business rules.
    """

    @abstractmethod
    async def enforce(self, **kwargs: Any) -> None:  # noqa: ANN401
        pass


class EditableEnforcerForOrganizationInAlgorithm(EditableEnforcer):
    async def enforce(self, **kwargs: Any) -> None:  # noqa: ANN401
        organization = await kwargs["organizations_service"].find_by_id_and_user_id(
            # TODO: using kwargs and new_values is 'a lot of assumptions' that a value is available under this key
            organization_id=int(kwargs["new_values"]["organization"]),
            user_id=kwargs["user_id"],
        )
        if organization is None:
            raise AMTAuthorizationError()
