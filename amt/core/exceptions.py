from gettext import gettext as _

from babel.support import NullTranslations
from fastapi import status
from fastapi.exceptions import HTTPException


class AMTHTTPException(HTTPException):
    def getmessage(self, translations: NullTranslations) -> str:
        return translations.gettext(self.detail)


class AMTError(Exception):
    def getmessage(self, translations: NullTranslations) -> str:
        return translations.gettext(self.detail)  # type: ignore


class AMTSettingsError(AMTError):
    def __init__(self, field: str) -> None:
        self.detail: str = _(
            "An error occurred while configuring the options for '{field}'. Please check the settings and try again."
        ).format(field=field)
        super().__init__(self.detail)


class AMTRepositoryError(AMTHTTPException):
    def __init__(self, detail: str | None = "Repository error") -> None:
        self.detail: str = _("An internal server error occurred while processing your request. Please try again later.")
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, self.detail)


class AMTInstrumentError(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("An error occurred while processing the instrument. Please try again later.")
        super().__init__(status.HTTP_501_NOT_IMPLEMENTED, self.detail)


class AMTNotFound(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _(
            "The requested page or resource could not be found, "
            "or you do not have the correct permissions to access it. Please check the "
            "URL or query and try again."
        )
        super().__init__(status.HTTP_404_NOT_FOUND, self.detail)


class AMTCSRFProtectError(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("CSRF check failed.")
        super().__init__(status.HTTP_401_UNAUTHORIZED, self.detail)


class AMTOnlyStatic(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("Only static files are supported.")
        super().__init__(status.HTTP_400_BAD_REQUEST, self.detail)


class AMTKeyError(AMTHTTPException):
    def __init__(self, field: str) -> None:
        self.detail: str = _("Key not correct: {field}").format(field=field)
        super().__init__(status.HTTP_400_BAD_REQUEST, self.detail)


class AMTValueError(AMTHTTPException):
    def __init__(self, field: str) -> None:
        self.detail: str = _("Value not correct: {field}").format(field=field)
        super().__init__(status.HTTP_400_BAD_REQUEST, self.detail)


class AMTAuthorizationError(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("Failed to authorize, please login and try again.")
        super().__init__(status.HTTP_401_UNAUTHORIZED, self.detail)


class AMTAuthorizationFlowError(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("Something went wrong during the authorization flow. Please try again later.")
        super().__init__(status.HTTP_401_UNAUTHORIZED, self.detail)


class AMTPermissionDenied(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _(
            "The requested page or resource could not be found, "
            "or you do not have the correct permissions to access it. Please check the "
            "URL or query and try again."
        )
        super().__init__(status.HTTP_404_NOT_FOUND, self.detail)


class AMTStorageError(AMTHTTPException):
    def __init__(self) -> None:
        self.detail: str = _("Something went wrong storing your file. PLease try again later.")
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, self.detail)
