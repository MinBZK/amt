from typing import Any

from fastapi import Request

from amt.schema.algoritmeregister import AlgoritmeregisterCredentials


def get_algoritmeregister_credentials(request: Request) -> AlgoritmeregisterCredentials | None:
    credentials_data: Any = request.session.get("algoritmeregister_credentials")
    if credentials_data:
        if isinstance(credentials_data, dict):
            return AlgoritmeregisterCredentials(**credentials_data)  # type: ignore
        return credentials_data
    return None


def store_algoritmeregister_credentials(request: Request, credentials: AlgoritmeregisterCredentials) -> None:
    request.session["algoritmeregister_credentials"] = credentials.model_dump()


def clear_algoritmeregister_credentials(request: Request) -> None:
    request.session.pop("algoritmeregister_credentials", None)
