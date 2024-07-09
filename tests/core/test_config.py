import pytest
from amt.core.config import Settings
from amt.core.exceptions import SettingsError


def test_default_settings():
    settings = Settings(_env_file=None)  # pyright: ignore [reportCallIssue]

    assert settings.ENVIRONMENT == "local"
    assert settings.LOGGING_LEVEL == "INFO"
    assert settings.APP_DATABASE_SCHEME == "sqlite"
    assert settings.APP_DATABASE_SERVER == "db"
    assert settings.APP_DATABASE_PORT == 5432
    assert settings.APP_DATABASE_USER == "amt"
    assert settings.APP_DATABASE_DB == "amt"


def test_environment_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "mysecret")
    monkeypatch.setenv("APP_DATABASE_SCHEME", "postgresql")
    monkeypatch.setenv("APP_DATABASE_USER", "amt2")
    monkeypatch.setenv("APP_DATABASE_DB", "amt2")
    monkeypatch.setenv("APP_DATABASE_PASSWORD", "mypassword")
    settings = Settings(_env_file=None)  # pyright: ignore [reportCallIssue]

    assert settings.SECRET_KEY == "mysecret"  # noqa: S105
    assert settings.ENVIRONMENT == "production"
    assert settings.LOGGING_LEVEL == "INFO"
    assert settings.APP_DATABASE_SCHEME == "postgresql"
    assert settings.APP_DATABASE_SERVER == "db"
    assert settings.APP_DATABASE_PORT == 5432
    assert settings.APP_DATABASE_USER == "amt2"
    assert settings.APP_DATABASE_DB == "amt2"
    assert settings.SQLALCHEMY_DATABASE_URI == "postgresql://amt2:mypassword@db:5432/amt2"


def test_environment_settings_production_sqlite_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("APP_DATABASE_SCHEME", "sqlite")
    with pytest.raises(SettingsError) as e:
        _settings = Settings(_env_file=None)  # pyright: ignore [reportCallIssue]

    assert e.value.message == "Settings error for options APP_DATABASE_SCHEME"


def test_environment_settings_production_debug_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("APP_DATABASE_SCHEME", "postgresql")
    with pytest.raises(SettingsError) as e:
        _settings = Settings(_env_file=None)  # pyright: ignore [reportCallIssue]

    assert e.value.message == "Settings error for options DEBUG"


def test_environment_settings_production_autocreate_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "True")
    monkeypatch.setenv("APP_DATABASE_SCHEME", "postgresql")
    with pytest.raises(SettingsError) as e:
        _settings = Settings(_env_file=None)  # pyright: ignore [reportCallIssue]

    assert e.value.message == "Settings error for options AUTO_CREATE_SCHEMA"
