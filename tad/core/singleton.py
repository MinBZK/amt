from typing import ClassVar


class Singleton(type):
    """The Singleton metaclass can be used to mark classes as singleton.
    Based on https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-singleton-in-python

    Usage: class Classname(metaclass=Singleton):
    """

    _instances = ClassVar[{}]

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
