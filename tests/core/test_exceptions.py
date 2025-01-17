from gettext import NullTranslations

import pytest
from amt.core.exceptions import (
    AMTAuthorizationFlowError,
    AMTCSRFProtectError,
    AMTError,
    AMTInstrumentError,
    AMTNotFound,
    AMTPermissionDenied,
    AMTSettingsError,
)


def test_settings_error():
    with pytest.raises(AMTSettingsError) as exc_info:
        raise AMTSettingsError("Wrong")

    assert (
        exc_info.value.detail
        == "An error occurred while configuring the options for 'Wrong'. Please check the settings and try again."
    )


def test_instrument_error():
    with pytest.raises(AMTInstrumentError) as exc_info:
        raise AMTInstrumentError()

    assert exc_info.value.detail == "An error occurred while processing the instrument. Please try again later."


def test_RepositoryNoResultFound():
    with pytest.raises(AMTNotFound) as exc_info:
        raise AMTNotFound()

    assert (
        exc_info.value.detail == "The requested page or resource could not be found, "
        "or you do not have the correct permissions to access it. "
        "Please check the URL or query and try again."
    )


def test_AMTError():
    e = AMTError()
    e.detail = "test"  # pyright: ignore [reportAttributeAccessIssue]
    res = e.getmessage(NullTranslations())  # pyright: ignore [reportArgumentType]

    assert res == "test"


def test_AMTCSRFProtectError():
    with pytest.raises(AMTCSRFProtectError) as exc_info:
        raise AMTCSRFProtectError()

    assert exc_info.value.detail == "CSRF check failed."


def test_AMTPermissionDenied():
    with pytest.raises(AMTPermissionDenied) as exc_info:
        raise AMTPermissionDenied()

    assert (
        exc_info.value.detail == "The requested page or resource could not be found, "
        "or you do not have the correct permissions to access it. "
        "Please check the URL or query and try again."
    )


def test_AMTAuthorizationFlowError():
    with pytest.raises(AMTAuthorizationFlowError) as exc_info:
        raise AMTAuthorizationFlowError()

    assert exc_info.value.detail == "Something went wrong during the authorization flow. Please try again later."
