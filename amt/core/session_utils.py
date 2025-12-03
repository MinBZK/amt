from typing import cast

from fastapi import Request

from amt.schema.algoritmeregister import AlgoritmeregisterCredentials


def get_algoritmeregister_credentials(request: Request) -> AlgoritmeregisterCredentials | None:
    credentials_data = cast(dict[str, str] | None, request.session.get("algoritmeregister_credentials"))
    return AlgoritmeregisterCredentials(**credentials_data) if credentials_data else None

def store_algoritmeregister_credentials(request: Request, credentials: AlgoritmeregisterCredentials) -> None:
    request.session["algoritmeregister_credentials"] = credentials.model_dump()

def clear_algoritmeregister_credentials(request: Request) -> None:
    request.session.pop("algoritmeregister_credentials", None)
