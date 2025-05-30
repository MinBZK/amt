import logging
import re
from abc import ABC, abstractmethod
from enum import Enum, StrEnum, auto
from typing import Any, Final, TypeVar, cast

from fastapi import Request
from starlette.responses import HTMLResponse

from amt.api.editable_value_providers import EditableValuesProvider
from amt.api.template_classes import LocaleJinja2Templates
from amt.models.base import Base
from amt.schema.webform_classes import WebFormFieldImplementationTypeFields, WebFormOption
from amt.services.services_provider import ServicesProvider

EditableType = TypeVar("EditableType", bound="Editable")
FormStateType = TypeVar("FormStateType", bound="FormState")
ResolvedEditableType = TypeVar("ResolvedEditableType", bound="ResolvedEditable")

logger = logging.getLogger(__name__)


class EditModes(StrEnum):
    EDIT = "EDIT"
    VIEW = "VIEW"
    SAVE = "SAVE"
    SAVE_NEW = "SAVE_NEW"
    DELETE = "DELETE"


class FormState(Enum):
    """
    The FormState is used to streamline the form flow for
    the inline editor. States can have a hook attacked to it, which is
    registered in the Editable object.
    """

    VALIDATE = auto()
    PRE_CONFIRM = auto()
    CONFIRM_SAVE = auto()
    PRE_SAVE = auto()
    SAVE = auto()
    POST_SAVE = auto()
    COMPLETED = auto()

    @classmethod
    def pre_save_states(cls) -> frozenset["FormState"]:
        return frozenset({cls.PRE_CONFIRM, cls.CONFIRM_SAVE, cls.PRE_SAVE})

    @classmethod
    def post_save_states(cls) -> frozenset["FormState"]:
        return frozenset({cls.POST_SAVE, cls.COMPLETED})

    def is_before_save(self) -> bool:
        return self in self.pre_save_states()

    def is_validate(self) -> bool:
        return self == self.VALIDATE

    def is_after_save(self) -> bool:
        return self in self.post_save_states()

    def is_save(self) -> bool:
        return self == self.SAVE

    @classmethod
    def get_next_state(cls, state: "FormState") -> "FormState":
        if state.value >= cls.COMPLETED.value:
            return cls.COMPLETED
        next_state = cls(state.value + 1)
        logger.info(f"FormState is moving to next state: {next_state}")
        return next_state

    @classmethod
    def all_states_after(cls, state: "FormState") -> list["FormState"]:
        return [s for s in cls if s.value > state.value]

    @classmethod
    def from_string(cls, state_name: str) -> "FormState":
        try:
            return cast(FormState, cls[state_name])
        except KeyError as e:
            raise ValueError(f"Invalid state name: {state_name}") from e


class EditableValidator(ABC):
    """
    Validators are used to validate (input) data for logical rules, like length and allowed characters.
    """

    @abstractmethod
    async def validate(
        self,
        request: Request,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        pass

    @staticmethod
    def get_new_value(
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
    ) -> Any:  # noqa: ANN401
        return editable_context.get("new_values", {}).get(editable.last_path_item())


class EditableEnforcer(ABC):
    """
    Enforcers are meant for checking authorization permissions and business rules.
    """

    @abstractmethod
    async def enforce(
        self,
        request: Request,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        pass


class EditableHook(ABC):
    """
    Hooks can be used to run a function at a specific moment in the FormState flow.
    """

    @abstractmethod
    async def execute(
        self,
        request: Request,
        templates: LocaleJinja2Templates,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        service_provider: ServicesProvider,
    ) -> HTMLResponse | None:
        pass


class EditableConverter:
    """
    Converters are meant for converting data between read, write and view when needed.
    An example is choosing an organization, the input value is the organization_id,
    but the needed 'write' value is the organization object, the view value is
    the name.
    """

    async def read(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return WebFormOption(value=in_value, display_value=in_value)

    async def write(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return WebFormOption(value=in_value, display_value=in_value)

    async def view(
        self,
        in_value: Any,  # noqa: ANN401
        request: Request | None,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        services_provider: ServicesProvider | None,
    ) -> WebFormOption:
        return WebFormOption(value=in_value, display_value=in_value)


class Editable:
    """
    Editable contains all basic information for editing a field in a resources, like changing the name
    of an algorithm.

    It requires the 'full_resource_path' in a resolvable format, like algorithm/{algorithm_id}/system_card/name.
    The implementation_type tells how this field can be edited using WebFormFieldImplementationType, like a 'plain'
    TEXT field or SELECT_MY_ORGANIZATIONS.
    The couples links fields together, if one is changed, so is the other.
    The children field is for grouping multiple fields as one 'action',
      it requires a WebFormFieldImplementationType.PARENT parent editable
    The enforcer checks permissions and business rules.
    The converter converts data between read, write and display (view) when needed.
    """

    full_resource_path: Final[str]

    def __init__(
        self,
        full_resource_path: str,
        implementation_type: WebFormFieldImplementationTypeFields,
        values_provider: EditableValuesProvider | None = None,
        couples: list["Editable"] | None = None,
        children: list["Editable"] | None = None,
        converter: EditableConverter | None = None,
        enforcer: EditableEnforcer | None = None,
        validator: EditableValidator | None = None,
        hooks: dict[FormState, EditableHook] | None = None,
        # TODO: determine if relative resource path is really required for editable
        relative_resource_path: str | None = None,
    ) -> None:
        self.full_resource_path = full_resource_path
        self.implementation_type = implementation_type
        self.values_provider = values_provider
        self.couples = list["Editable"]() if couples is None else couples
        self.children = list["Editable"]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator
        self.relative_resource_path = relative_resource_path
        self.hooks = hooks

    def add_bidirectional_couple(self, target: "Editable") -> None:
        """
        Changing an editable may require an update on another field as well, like when changing the name
        of an algorithm; this is stored in two different places. Making it a couple ensures both values are
        updated when one is changed.
        :param target: the target editable type
        :return: None
        """
        self.couples.append(target)
        target.couples.append(self)


T = TypeVar("T")


class ResolvedEditable:
    value: WebFormOption | None
    # TODO: find out of holding resource_object in memory for many editables is wise / needed
    resource_object: Any | None
    relative_resource_path: str | None
    form_options: list[WebFormOption] | None

    def __init__(
        self,
        # fields copied from the Editable class
        full_resource_path: str,
        implementation_type: WebFormFieldImplementationTypeFields,
        values_provider: EditableValuesProvider | None = None,
        couples: list["ResolvedEditable"] | None = None,
        children: list["ResolvedEditable"] | None = None,
        converter: EditableConverter | None = None,
        enforcer: EditableEnforcer | None = None,
        validator: EditableValidator | None = None,
        # resolved only fields
        value: WebFormOption | None = None,
        resource_object: Base | None = None,
        relative_resource_path: str | None = None,
        hooks: dict[FormState, EditableHook] | None = None,
    ) -> None:
        self.full_resource_path = full_resource_path
        self.implementation_type = implementation_type
        self.values_provider = values_provider
        self.couples = list["ResolvedEditable"]() if couples is None else couples
        self.children = list["ResolvedEditable"]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator
        # resolved only fields
        self.value = value
        self.resource_object = resource_object
        self.relative_resource_path = relative_resource_path
        self.hooks = hooks
        self.form_options = []

    def last_path_item(self) -> str:
        stripped = self.full_resource_path.strip("/")
        if "/" in stripped:
            return self.full_resource_path.split("/")[-1]
        return stripped

    def first_path_item(self) -> str:
        stripped = self.full_resource_path.strip("/")
        if "/" in stripped:
            parts = stripped.split("/")
            return parts[0] if parts else ""
        return stripped

    def safe_html_path(self) -> str:
        """
        The relative resource path with special characters replaced so it can be used in HTML/Javascript.
        """
        # TODO: the path probably should include the id of the resource to be correctly targetable
        if self.relative_resource_path is not None:
            return re.sub(r"[\[\]/*]", "_", self.relative_resource_path)  # pyright: ignore[reportUnknownVariableType, reportCallIssue]
        return re.sub(r"[\[\]/*]", "_", self.first_path_item())

    def has_hook(self, state: FormState) -> bool:
        if self.hooks is None:
            return False
        return state in self.hooks

    def get_hook(self, state: FormState) -> EditableHook | None:
        if self.hooks is None:
            return None
        return self.hooks.get(state)

    async def run_hook(
        self,
        state: FormState,
        request: Request,
        templates: LocaleJinja2Templates,
        editable: "ResolvedEditable",
        editable_context: dict[str, Any],
        service_provider: ServicesProvider,
    ) -> HTMLResponse | None:
        if self.hooks is not None and self.has_hook(state):
            logger.debug(f"Running hook for state {state} for editable {self.full_resource_path}")
            return await self.hooks[state].execute(request, templates, editable, editable_context, service_provider)
        return None

    async def validate(
        self,
        request: Request,
        editable_context: dict[str, Any],
        services_provider: ServicesProvider,
        edit_mode: EditModes,
    ) -> None:
        # TODO: there may be cases, when validating couples, that a couple raises a validation error
        #  but because it is not part of the current form, we can not display the error, so an error
        #  from a coupled field, should be displayed in its current editable error path (last_path_item).
        editables_to_validate = [self] + (self.couples or []) + (self.children or [])
        for editable in editables_to_validate:
            if editable.validator is not None:
                await editable.validator.validate(request, editable, editable_context, edit_mode, services_provider)
            if editable.enforcer:
                await editable.enforcer.enforce(request, editable, editable_context, edit_mode, services_provider)

    def get_resource_object(self, cls: type[T]) -> T:
        if not isinstance(self.resource_object, cls):
            raise TypeError(f"Resource object is not of type {cls.__name__}")
        return self.resource_object
