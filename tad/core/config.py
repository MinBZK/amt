import logging
import secrets
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
    # todo(berry): investigate multiple .env files support for SettingsConfigDict
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.test", ".env.prod"), env_ignore_empty=True, extra="ignore"
    )
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

    STATIC_DIR: str = "tad/site/static/"
    TEMPLATE_DIR: str = "tad/site/templates"

    # todo(berry): create submodel for database settings
    APP_DATABASE_SCHEME: DatabaseSchemaType = "sqlite"
    APP_DATABASE_DRIVER: str | None = None

    APP_DATABASE_SERVER: str = "db"
    APP_DATABASE_PORT: int = 5432
    APP_DATABASE_USER: str = "tad"
    APP_DATABASE_PASSWORD: str | None = None
    APP_DATABASE_DB: str = "tad"

    APP_DATABASE_FILE: str = "database.sqlite3"

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        logging.info(f"test: {self.APP_DATABASE_SCHEME}")

        if self.APP_DATABASE_SCHEME == "sqlite":
            return str(MultiHostUrl.build(scheme=self.APP_DATABASE_SCHEME, host="", path=self.APP_DATABASE_FILE))

        scheme: str = (
            f"{self.APP_DATABASE_SCHEME}+{self.APP_DATABASE_DRIVER}"
            if isinstance(self.APP_DATABASE_DRIVER, str)
            else self.APP_DATABASE_SCHEME
        )

        return str(
            MultiHostUrl.build(
                scheme=scheme,
                username=self.APP_DATABASE_USER,
                password=self.APP_DATABASE_PASSWORD,
                host=self.APP_DATABASE_SERVER,
                port=self.APP_DATABASE_PORT,
                path=self.APP_DATABASE_DB,
            )
        )

    @model_validator(mode="after")
    def _enforce_database_rules(self: SelfSettings) -> SelfSettings:
        if self.ENVIRONMENT != "local" and self.APP_DATABASE_SCHEME == "sqlite":
            raise SettingsError("SQLite is not supported in production")
        return self


settings = Settings()  # type: ignore
