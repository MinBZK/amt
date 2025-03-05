import re
import typing
from typing import Any, cast


def set_path(obj: dict[str, Any] | object, path: str, value: typing.Any) -> None:  # noqa: ANN401, C901
    if not path:
        raise ValueError("Path cannot be empty")

    attrs = path.lstrip("/").split("/")
    for attr in attrs[:-1]:
        attr, index = extract_number_and_string(attr)
        if isinstance(obj, dict):
            obj = cast(dict[str, Any], obj)
            if attr not in obj:
                obj[attr] = {}
            obj = obj[attr]
        else:
            if not hasattr(obj, attr):  # pyright: ignore[reportUnknownArgumentType]
                setattr(obj, attr, {})  # pyright: ignore[reportUnknownArgumentType]
            obj = getattr(obj, attr)  # pyright: ignore[reportUnknownArgumentType]
        if obj and index is not None:
            obj = cast(list[Any], obj)[index]  # pyright: ignore[reportArgumentType, reportUnknownVariableType, reportUnknownArgumentType]

    if isinstance(obj, dict):
        obj[attrs[-1]] = value
    else:
        attr, index = extract_number_and_string(attrs[-1])
        if index is not None:
            cast(list[Any], getattr(obj, attr))[index] = value
        else:
            setattr(obj, attrs[-1], value)


def extract_number_and_string(input_string: str) -> tuple[str, int | None]:
    """
    Extracts the number within square brackets and the string before the brackets
    from a given input string.

    Returns:
      A tuple containing:
        - The string before the brackets.
        - The number within the brackets (as an integer) or None if no number is found within brackets.
    """
    match = re.search(r"(.+)\[(\d+)]", input_string)
    if match:
        string_before = match.group(1)
        number_in_brackets = int(match.group(2))
        return string_before, number_in_brackets
    else:
        return input_string, None
