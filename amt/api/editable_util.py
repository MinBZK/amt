import re

from amt.api.editable_classes import ResolvedEditable
from amt.api.update_utils import extract_number_and_string
from amt.schema.webform import WebFormFieldImplementationType


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


def is_parent_editable(editables: dict[str, ResolvedEditable], full_resource_path: str) -> bool:
    full_resource_path = replace_digits_in_brackets(full_resource_path)
    editable = editables.get(full_resource_path)
    if editable is None:
        return False
    result = editable.implementation_type == WebFormFieldImplementationType.PARENT
    return result
