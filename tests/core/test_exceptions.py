from pathlib import Path

import pytest
from tad.core.exceptions import InstrumentError, SettingsError, UnsafeFileError


def test_settings_error():
    with pytest.raises(SettingsError) as exc_info:
        raise SettingsError("Wrong")

    assert exc_info.value.message == "Settings error for options Wrong"


def test_instrument_error():
    with pytest.raises(InstrumentError) as exc_info:
        raise InstrumentError()

    assert exc_info.value.message == "Instrument error"


def test_unsafefile_error():
    test = Path("test")
    with pytest.raises(UnsafeFileError) as exc_info:
        raise UnsafeFileError(test)

    assert exc_info.value.message == f"Unsafe file error for file {test}"
