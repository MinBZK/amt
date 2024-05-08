import pytest
from tad.core.exceptions import SettingsError


def test_environment_settings():
    with pytest.raises(SettingsError) as exc_info:
        raise SettingsError("Wrong settings")  # noqa: TRY003

    assert exc_info.value.message == "Wrong settings"
