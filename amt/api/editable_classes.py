import re
from enum import StrEnum
from typing import Any, Final

from amt.api.editable_converters import (
    EditableConverter,
)
from amt.api.editable_enforcers import EditableEnforcer
from amt.api.editable_validators import EditableValidator
from amt.api.editable_value_providers import EditableValuesProvider
from amt.models.base import Base
from amt.schema.webform import WebFormFieldImplementationTypeFields, WebFormOption

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
        couples: set[EditableType] | None = None,
        children: list[EditableType] | None = None,
        converter: EditableConverter | None = None,
        enforcer: EditableEnforcer | None = None,
        validator: EditableValidator | None = None,
        # TODO: determine if relative resource path is really required for editable
        relative_resource_path: str | None = None,
    ) -> None:
        self.full_resource_path = full_resource_path
        self.implementation_type = implementation_type
        self.values_provider = values_provider
        self.couples = set[EditableType]() if couples is None else couples
        self.children = list[EditableType]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator
        self.relative_resource_path = relative_resource_path

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
        self.children.append(target)


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
        values_provider: EditableValuesProvider | None = None,
        couples: set[ResolvedEditableType] | None = None,
        children: list[ResolvedEditableType] | None = None,
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
        self.values_provider = values_provider
        self.couples = set[ResolvedEditableType]() if couples is None else couples
        self.children = list[ResolvedEditableType]() if children is None else children
        self.converter = converter
        self.enforcer = enforcer
        self.validator = validator
        # resolved only fields
        self.value = value
        self.resource_object = resource_object
        self.relative_resource_path = relative_resource_path

    def last_path_item(self) -> str:
        return self.full_resource_path.split("/")[-1]

    def safe_html_path(self) -> str:
        """
        The relative resource path with special characters replaced so it can be used in HTML/Javascript.
        """
        if self.relative_resource_path is not None:
            return re.sub(r"[\[\]/*]", "_", self.relative_resource_path)  # pyright: ignore[reportUnknownVariableType, reportCallIssue]
        raise ValueError("Can not convert path to save html path as it is None")


class EditModes(StrEnum):
    EDIT = "EDIT"
    VIEW = "VIEW"
    SAVE = "SAVE"
