from collections.abc import Iterable
from typing import TypeVar


class SafeDict(dict[str, str | int]):
    """
    A dictionary that if the key is missing returns the key as 'python replacement string', e.g. {key}
    instead of throwing an exception.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


T = TypeVar("T")


def compare_lists(
    current_list: Iterable[T],
    new_list: Iterable[T],
    current_attr_name: str,
    new_attr_name: str,
) -> tuple[list[T], list[T]]:
    """
    Compare two lists by attributes and return a tuple of two lists: added items and removed items.
    """
    current_attributes = {getattr(item, current_attr_name, None) for item in current_list}
    new_attributes = {getattr(item, new_attr_name, None) for item in new_list}

    added_attributes = new_attributes - current_attributes
    removed_attributes = current_attributes - new_attributes

    added_items = [item for item in new_list if getattr(item, current_attr_name, None) in added_attributes]
    removed_items = [item for item in current_list if getattr(item, current_attr_name, None) in removed_attributes]

    return added_items, removed_items
