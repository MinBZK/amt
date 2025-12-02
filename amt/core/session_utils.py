import logging
from typing import Any

from fastapi import Request

from amt.schema.algoritmeregister import AlgoritmeregisterCredentials

logger = logging.getLogger(__name__)


def get_algoritmeregister_credentials(request: Request) -> AlgoritmeregisterCredentials | None:
    session_keys = list(request.session.keys())
    session_cookie = request.cookies.get("session", "NO_SESSION_COOKIE")
    logger.info(f"Session cookie (first 20 chars): {session_cookie[:20] if len(session_cookie) > 20 else session_cookie}")
    logger.info(f"Session keys: {session_keys}")

    credentials_data: Any = request.session.get("algoritmeregister_credentials")
    has_credentials = credentials_data is not None
    logger.info(f"Credentials found in session: {has_credentials}")
    if has_credentials and isinstance(credentials_data, dict):
        logger.info(f"Credentials username: {credentials_data.get('username', 'N/A')}")

    if credentials_data:
        if isinstance(credentials_data, dict):
            return AlgoritmeregisterCredentials(**credentials_data)  # type: ignore
        return credentials_data
    return None


def store_algoritmeregister_credentials(request: Request, credentials: AlgoritmeregisterCredentials) -> None:
    session_cookie = request.cookies.get("session", "NO_SESSION_COOKIE")
    logger.info(f"Storing credentials for user: {credentials.username}")
    logger.info(f"Session cookie at store (first 20 chars): {session_cookie[:20] if len(session_cookie) > 20 else session_cookie}")
    request.session["algoritmeregister_credentials"] = credentials.model_dump()
    logger.info(f"Session keys after store: {list(request.session.keys())}")


def clear_algoritmeregister_credentials(request: Request) -> None:
    logger.info("Clearing algoritmeregister credentials from session")
    request.session.pop("algoritmeregister_credentials", None)
