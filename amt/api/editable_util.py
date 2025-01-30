import re


def replace_digits_in_brackets(string: str) -> str:
    return re.sub(r"\[(\d+)]", "[*]", string)


def replace_wildcard_with_digits_in_brackets(string: str, index: int) -> str:
    return re.sub(r"\[\*]", "[" + str(index) + "]", string)


def resolve_resource_list_path(full_resource_path_resolved: str, relative_resource_path: str) -> str:
    """
    Given a full_resource_path_resolved that contains a list, like /algorithm/1/system_card/list[1], resolves
    a relative_resource_path like /algorithm/1/system_card/list[*]/name so the result is /algorithm/1/system_card/list[1]/name.
    """
    full_resource_path, index = extract_number_and_string(full_resource_path_resolved)
    return replace_wildcard_with_digits_in_brackets(relative_resource_path, index)


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
