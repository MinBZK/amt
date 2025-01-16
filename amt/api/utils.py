class SafeDict(dict[str, str | int]):
    """
    A dictionary that if the key is missing returns the key as 'python replacement string', e.g. {key}
    instead of throwing an exception.
    """

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
