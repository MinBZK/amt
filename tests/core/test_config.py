import os

import pytest
from tad.core.config import Settings
from tad.core.exceptions import SettingsError


def test_default_settings():
    settings = Settings(_env_file="nonexisitingfile")  # type: ignore

    assert settings.DOMAIN == "localhost"
    assert settings.ENVIRONMENT == "local"
    assert settings.server_host == "http://localhost"
    assert settings.VERSION == "0.1.0"
    assert settings.LOGGING_LEVEL == "INFO"
    assert settings.PROJECT_NAME == "TAD"
    assert settings.PROJECT_DESCRIPTION == "Transparency of Algorithmic Decision making"
    assert settings.APP_DATABASE_SCHEME == "sqlite"
    assert settings.APP_DATABASE_SERVER == "db"
    assert settings.APP_DATABASE_PORT == 5432
    assert settings.APP_DATABASE_USER == "tad"
    assert settings.APP_DATABASE_DB == "tad"
    assert settings.SQLITE_FILE == "//./database"
    assert settings.SQLALCHEMY_DATABASE_URI == "sqlite://///database"


def test_environment_settings():
    os.environ["DOMAIN"] = "google.com"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["PROJECT_NAME"] = "TAD2"
    os.environ["SECRET_KEY"] = "mysecret"  # noqa: S105
    os.environ["APP_DATABASE_SCHEME"] = "postgresql"
    os.environ["APP_DATABASE_USER"] = "tad2"
    os.environ["APP_DATABASE_DB"] = "tad2"
    os.environ["APP_DATABASE_PASSWORD"] = "mypassword"  # noqa: S105
    settings = Settings(_env_file="nonexisitingfile")  # type: ignore

    assert settings.SECRET_KEY == "mysecret"  # noqa: S105
    assert settings.DOMAIN == "google.com"
    assert settings.ENVIRONMENT == "production"
    assert settings.server_host == "https://google.com"
    assert settings.VERSION == "0.1.0"
    assert settings.LOGGING_LEVEL == "INFO"
    assert settings.PROJECT_NAME == "TAD2"
    assert settings.PROJECT_DESCRIPTION == "Transparency of Algorithmic Decision making"
    assert settings.APP_DATABASE_SCHEME == "postgresql"
    assert settings.APP_DATABASE_SERVER == "db"
    assert settings.APP_DATABASE_PORT == 5432
    assert settings.APP_DATABASE_USER == "tad2"
    assert settings.APP_DATABASE_PASSWORD == "mypassword"  # noqa: S105
    assert settings.APP_DATABASE_DB == "tad2"
    assert settings.SQLITE_FILE == "//./database"
    assert settings.SQLALCHEMY_DATABASE_URI == "postgresql://tad2:mypassword@db:5432/tad2"


def test_environment_settings_production_sqlite_error():
    os.environ["ENVIRONMENT"] = "production"
    os.environ["APP_DATABASE_SCHEME"] = "sqlite"
    os.environ["APP_DATABASE_PASSWORD"] = "32452345432"  # noqa: S105
    with pytest.raises(SettingsError) as e:
        _settings = Settings(_env_file="nonexisitingfile")  # type: ignore

    assert e.value.message == "SQLite is not supported in production"


def test_environment_settings_production_nopassword_error():
    os.environ["ENVIRONMENT"] = "production"

    with pytest.raises(SettingsError):
        _settings = Settings(_env_file="nonexisitingfile")  # type: ignore
