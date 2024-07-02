from pathlib import Path

from fastapi import status
from fastapi.exceptions import HTTPException, ValidationException


class TADHTTPException(HTTPException):
    pass


class TADValidationException(ValidationException):
    pass


class TADError(RuntimeError):
    """
    A generic, Tad-specific error.
    """


class SettingsError(TADError):
    def __init__(self, field: str) -> None:
        self.message: str = f"Settings error for options {field}"
        exception_name: str = self.__class__.__name__
        super().__init__(f"{exception_name}: {self.message}")


class RepositoryError(TADHTTPException):
    def __init__(self, message: str = "Repository error") -> None:
        self.message: str = message
        exception_name: str = self.__class__.__name__
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, f"{exception_name}: {self.message}")


class InstrumentError(TADHTTPException):
    def __init__(self, message: str = "Instrument error") -> None:
        self.message: str = message
        exception_name: str = self.__class__.__name__
        super().__init__(status.HTTP_501_NOT_IMPLEMENTED, f"{exception_name}: {self.message}")


class UnsafeFileError(TADHTTPException):
    def __init__(self, file: Path) -> None:
        self.message: str = f"Unsafe file error for file {file}"
        exception_name: str = self.__class__.__name__
        super().__init__(status.HTTP_400_BAD_REQUEST, f"{exception_name}: {self.message}")
