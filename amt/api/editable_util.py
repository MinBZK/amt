import re

from jinja2 import StrictUndefined

from amt.api.editable_classes import ResolvedEditable
from amt.api.update_utils import extract_number_and_string
from amt.schema.webform_classes import WebFormFieldImplementationType


def replace_digits_in_brackets(string: str) -> str:
    return re.sub(r"\[(\d+)]", "[*]", string)


def replace_wildcard_with_digits_in_brackets(string: str, index: int | None) -> str:
    if index is not None:
        return re.sub(r"\[\*]", "[" + str(index) + "]", string)
    else:
        return string


def resolve_resource_list_path(full_resource_path_resolved: str, relative_resource_path: str) -> str:
    """
    Given a full_resource_path_resolved that contains a list, like /algorithm/1/system_card/list[1], resolves
    a relative_resource_path like /algorithm/1/system_card/list[*]/name
    so the result is /algorithm/1/system_card/list[1]/name.
    Note this method assumes and only works with 1 list item, nested lists are not supported.
    """
    _, index = extract_number_and_string(full_resource_path_resolved)
    return replace_wildcard_with_digits_in_brackets(relative_resource_path, index)


def is_editable_resource(full_resource_path: str, editables: dict[str, ResolvedEditable]) -> bool:
    return editables.get(replace_digits_in_brackets(full_resource_path), None) is not None


def is_parent_editable(editables: dict[str, ResolvedEditable] | None, full_resource_path: str) -> bool:
    if isinstance(editables, StrictUndefined) or not editables:
        return False
    editable = editables.get(full_resource_path)
    # FIXME: this method is used in list cases /algoritmes/list[*] as resolved /algoritmes/list[1]
    #  this causes problems for the matching of the right editable element
    if editable is None:
        editable = editables.get(replace_digits_in_brackets(full_resource_path))
        if editable is None:
            return False
    return editable.implementation_type == WebFormFieldImplementationType.PARENT
