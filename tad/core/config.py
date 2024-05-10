import secrets
import warnings
from typing import Any, TypeVar

from pydantic import (
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from tad.core.exceptions import SettingsError
from tad.core.types import DatabaseSchemaType, EnvironmentType, LoggingLevelType

# Self type is not available in Python 3.10 so create our own with TypeVar
SelfSettings = TypeVar("SelfSettings", bound="Settings")


class Settings(BaseSettings):
    # todo(berry): investigate yaml, toml or json file support for SettingsConfigDict
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")
    SECRET_KEY: str = secrets.token_urlsafe(32)

    DOMAIN: str = "localhost"
    ENVIRONMENT: EnvironmentType = "local"

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    VERSION: str = "0.1.0"

    LOGGING_LEVEL: LoggingLevelType = "INFO"
    LOGGING_CONFIG: dict[str, Any] | None = None

    PROJECT_NAME: str = "TAD"
    PROJECT_DESCRIPTION: str = "Transparency of Algorithmic Decision making"

    STATIC_DIR: str = "tad/static"

    # todo(berry): create submodel for database settings
    APP_DATABASE_SCHEME: DatabaseSchemaType = "sqlite"
    APP_DATABASE_SERVER: str = "db"
    APP_DATABASE_PORT: int = 5432
    APP_DATABASE_USER: str = "tad"
    APP_DATABASE_PASSWORD: str
    APP_DATABASE_DB: str = "tad"

    SQLITE_FILE: str = "//./database"

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.APP_DATABASE_SCHEME == "sqlite":
            return str(MultiHostUrl.build(scheme=self.APP_DATABASE_SCHEME, host="", path=self.SQLITE_FILE))

        return str(
            MultiHostUrl.build(
                scheme=self.APP_DATABASE_SCHEME,
                username=self.APP_DATABASE_USER,
                password=self.APP_DATABASE_PASSWORD,
                host=self.APP_DATABASE_SERVER,
                port=self.APP_DATABASE_PORT,
                path=self.APP_DATABASE_DB,
            )
        )

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = f'The value of {var_name} is "changethis", ' "for security, please change it"
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise SettingsError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self: SelfSettings) -> SelfSettings:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("APP_DATABASE_PASSWORD", self.APP_DATABASE_PASSWORD)

        return self

    @model_validator(mode="after")
    def _enforce_database_rules(self: SelfSettings) -> SelfSettings:
        if self.ENVIRONMENT != "local" and self.APP_DATABASE_SCHEME == "sqlite":
            raise SettingsError("SQLite is not supported in production")  # noqa: TRY003
        return self


settings = Settings()  # type: ignore
