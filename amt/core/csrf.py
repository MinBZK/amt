from typing import Any

from fastapi_csrf_protect import CsrfProtect  # type: ignore

from amt.core.config import get_settings


@CsrfProtect.load_config  # type: ignore
def get_csrf_config() -> list[tuple[Any, ...]]:
    settings = get_settings()
    config = [
        ("secret_key", settings.CSRF_PROTECT_SECRET_KEY),
        ("token_location", settings.CSRF_TOKEN_LOCATION),
        ("token_key", settings.CSRF_TOKEN_KEY),
        ("cookie_samesite", settings.CSRF_COOKIE_SAMESITE),
    ]

    return config
