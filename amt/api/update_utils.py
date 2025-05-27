import logging
import typing
from types import UnionType
from typing import Any, Union, cast, get_args, get_origin
from uuid import UUID

from sqlalchemy.orm import Mapped

logger = logging.getLogger(__name__)

T = typing.TypeVar("T")


def convert_int(v: Any) -> int | None:  # noqa: ANN401
    if (isinstance(v, str) and v.strip()) or (v is not None and not isinstance(v, str)):
        return int(v)
    return None


def convert_str(v: Any) -> str | None:  # noqa: ANN401
    return str(v) if v is not None else None


def convert_float(v: Any) -> float | None:  # noqa: ANN401
    if (isinstance(v, str) and v.strip()) or (v is not None and not isinstance(v, str)):
        return float(v)
    return None


def convert_uuid(v: Any) -> UUID | object:  # noqa: ANN401
    return UUID(v) if isinstance(v, str) else v


def convert_bool(v: Any) -> bool | Any:  # noqa: ANN401
    if isinstance(v, str):
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
    return v


convertable_types = {int: convert_int, str: convert_str, float: convert_float, UUID: convert_uuid, bool: convert_bool}


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
        obj[attrs[-1]] = convert_value_if_needed(attrs[-1], obj, value)  # pyright: ignore[reportUnknownArgumentType]
    else:
        attr, index = extract_number_and_string(attrs[-1])
        if index is not None:
            cast(list[Any], getattr(obj, attr))[index] = convert_value_if_needed(attr, obj, value)
        else:
            setattr(obj, attrs[-1], convert_value_if_needed(attrs[-1], obj, value))


def extract_type_from_union(type_annotation: Any) -> type[Any] | None:  # noqa: ANN401
    origin = get_origin(type_annotation)
    if origin is Union or origin is UnionType:
        args = get_args(type_annotation)
        # we cannot guess the type if the union is of other types than: Type | None (e.g., str | int | Any | None)
        if len(args) == 2 and type(None) in args:
            return next(arg for arg in args if arg is not type(None))
        return None
    return type_annotation


def get_all_annotations(cls: type) -> dict[str, Any]:
    """
    Recursively collect annotations from a class and all its base classes.
    Child class annotations override parent annotations with the same name.
    """
    annotations: dict[str, Any] = {}

    for base in cls.__bases__:
        base_annotations = get_all_annotations(base)
        annotations.update(base_annotations)
    current_annotations = getattr(cls, "__annotations__", {})
    annotations.update(current_annotations)

    return annotations


def convert_value_if_needed(attr_name: str, obj: dict[str, Any] | object, value: Any) -> Any:  # noqa: ANN401
    """
    Convert the given value to the type of the attribute specified in the class definition of the object if possible
    :param attr_name: the name of the attribute
    :param obj: the object
    :param value: the value to convert
    :return: the converted value or the original value if no conversion was possible or if already of the correct type.
    """
    target_class = type(obj)
    annotations = get_all_annotations(target_class)
    if attr_name in annotations:
        target_type = annotations[attr_name]
        if typing.get_origin(target_type) is Mapped:
            mapped_args = typing.get_args(target_type)
            if mapped_args:
                target_type = mapped_args[0]
        target_type = extract_type_from_union(target_type)
        if target_type is not None and target_type in convertable_types and not isinstance(value, target_type):
            converter_func = convertable_types[target_type]  # type: ignore
            value = converter_func(value)  # type: ignore
            logger.debug(
                "Converted value %s to type %s in object %s with path %s", value, target_type, target_class, attr_name
            )
    return value


def extract_number_and_string(input_string: str) -> tuple[str, int | None]:
    """
    Extracts the number within square brackets and the string before the brackets
    from a given input string.

    Returns:
      A tuple containing:
        - The string before the brackets.
        - The number within the brackets (as an integer) or None if no number is found within brackets.
    """
    # Look for pattern that ends with [number]
    if input_string.endswith("]"):
        last_open = input_string.rfind("[")
        if last_open != -1:
            number = int(input_string[last_open + 1 : -1])
            return input_string[:last_open], number
    return input_string, None
