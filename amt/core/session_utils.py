import logging

from fastapi import Request

from amt.schema.algoritmeregister import AlgoritmeregisterCredentials

logger = logging.getLogger(__name__)


def get_algoritmeregister_credentials(request: Request) -> AlgoritmeregisterCredentials | None:
    # TODO: temporary hardcoded credentials for testing, remove after fixing session issue
    return AlgoritmeregisterCredentials(username="ictu_user1", password="demo123")  # noqa: S106


def store_algoritmeregister_credentials(request: Request, credentials: AlgoritmeregisterCredentials) -> None:
    session_cookie = request.cookies.get("session", "NO_SESSION_COOKIE")
    cookie_preview = session_cookie[:20] if len(session_cookie) > 20 else session_cookie
    logger.info(f"Storing credentials for user: {credentials.username}")
    logger.info(f"Session cookie at store (first 20 chars): {cookie_preview}")
    request.session["algoritmeregister_credentials"] = credentials.model_dump()
    logger.info(f"Session keys after store: {list(request.session.keys())}")


def clear_algoritmeregister_credentials(request: Request) -> None:
    logger.info("Clearing algoritmeregister credentials from session")
    request.session.pop("algoritmeregister_credentials", None)
