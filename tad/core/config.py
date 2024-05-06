import secrets
import warnings
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    PROJECT_NAME: str = "TAD"

    SQLALCHEMY_SCHEME: str = "sqlite"

    APP_DATABASE_SERVER: str = "db"
    APP_DATABASE_PORT: int = 5432
    APP_DATABASE_USER: str = "tad"
    APP_DATABASE_PASSWORD: str
    APP_DATABASE_DB: str = "tad"

    SQLITE_FILE: str = "./database"

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.SQLALCHEMY_SCHEME == "sqlite":
            return str(MultiHostUrl.build(scheme=self.SQLALCHEMY_SCHEME, host="", path=self.SQLITE_FILE))

        return str(
            MultiHostUrl.build(
                scheme=self.SQLALCHEMY_SCHEME,
                username=self.APP_DATABASE_USER,
                password=self.APP_DATABASE_PASSWORD,
                host=self.APP_DATABASE_SERVER,
                port=self.APP_DATABASE_PORT,
                path=self.APP_DATABASE_DB,
            )
        )

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", ' "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("APP_DATABASE_PASSWORD", self.APP_DATABASE_PASSWORD)

        return self


settings = Settings()  # type: ignore
