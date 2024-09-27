import pytest
from amt.core.exceptions import AMTInstrumentError, AMTNotFound, AMTSettingsError


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
        exc_info.value.detail
        == "The requested page or resource could not be found. Please check the URL or query and try again."
    )
