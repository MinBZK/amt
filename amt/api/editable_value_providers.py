from abc import ABC, abstractmethod

from starlette.requests import Request

from amt.api.ai_act_profile import SelectAiProfileItem, get_ai_act_profile_selector
from amt.core.authorization import AuthorizationType
from amt.core.dynamic_translations import ExternalFieldsTranslations
from amt.schema.webform_classes import WebFormOption


class EditableValuesProvider(ABC):
    @abstractmethod
    async def get_values(self, request: Request) -> list[WebFormOption]:
        pass


class RolesValuesProvider(EditableValuesProvider):
    async def get_values(self, request: Request) -> list[WebFormOption]:
        # TODO: this is a bit of a hack but we have no other way to pass variables
        options = {}
        if request.state.authorization_type == AuthorizationType.ORGANIZATION:
            options = {
                "1": "Organization Maintainer",
                "2": "Organization Member",
                "3": "Organization Viewer",
            }
        elif request.state.authorization_type == AuthorizationType.ALGORITHM:
            options = {
                "4": "Algorithm Maintainer",
                "5": "Algorithm Member",
                "6": "Algorithm Viewer",
            }
        return [
            WebFormOption(value=key, display_value=ExternalFieldsTranslations.translate(value, request))
            for key, value in options.items()
        ]


class AIActValuesProvider(EditableValuesProvider):
    def __init__(self, type: str) -> None:
        self.type = type

    async def get_values(self, request: Request) -> list[WebFormOption]:
        profile = get_ai_act_profile_selector(request)
        target_ai_act_profile: SelectAiProfileItem | None = next(
            (
                ai_act_profile
                for ai_act_profile in (profile.dropdown_select or []) + (profile.multiple_select or [])
                if ai_act_profile.target_name == self.type
            ),
            None,
        )
        if target_ai_act_profile is not None and target_ai_act_profile.options is not None:
            return [WebFormOption(value=option, display_value=option) for option in target_ai_act_profile.options]
        return []
