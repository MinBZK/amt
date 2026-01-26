from enum import StrEnum
from typing import Any, cast

from fastapi import Request

from amt.core.exceptions import AMTRedirectError
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials


class PublishStep(StrEnum):
    EXPLANATION = "explanation"
    STATUS = "status"
    CONNECTION = "connection"
    PREPARE = "prepare"
    PREVIEW = "preview"
    CONFIRM = "confirm"


def get_algoritmeregister_credentials(request: Request) -> AlgoritmeregisterCredentials | None:
    credentials_data = cast(dict[str, Any] | None, request.session.get("algoritmeregister_credentials"))
    return AlgoritmeregisterCredentials(**credentials_data) if credentials_data else None


def get_algoritmeregister_credentials_or_trigger_redirect(
    request: Request, algorithm_id: int
) -> AlgoritmeregisterCredentials:
    credentials = get_algoritmeregister_credentials(request)
    if credentials is None:
        raise AMTRedirectError(redirect_url=f"/algorithm/{algorithm_id}/publish/connection")
    return credentials


def store_algoritmeregister_credentials(request: Request, credentials: AlgoritmeregisterCredentials) -> None:
    request.session["algoritmeregister_credentials"] = credentials.model_dump()


def clear_algoritmeregister_credentials(request: Request) -> None:
    request.session.pop("algoritmeregister_credentials", None)


def get_publish_step(request: Request, algorithm_id: int) -> PublishStep | None:
    """Get the current publish step for a specific algorithm."""
    publish_steps = cast(dict[str, str] | None, request.session.get("publish_steps"))
    if publish_steps is None:
        return None
    step_value = publish_steps.get(str(algorithm_id))
    return PublishStep(step_value) if step_value else None


def set_publish_step(request: Request, algorithm_id: int, step: PublishStep) -> None:
    """Set the current publish step for a specific algorithm."""
    publish_steps = cast(dict[str, str] | None, request.session.get("publish_steps"))
    if publish_steps is None:
        publish_steps = {}
    publish_steps[str(algorithm_id)] = step.value
    request.session["publish_steps"] = publish_steps


def clear_publish_step(request: Request, algorithm_id: int) -> None:
    """Clear the publish step for a specific algorithm."""
    publish_steps = cast(dict[str, str] | None, request.session.get("publish_steps"))
    if publish_steps is not None:
        publish_steps.pop(str(algorithm_id), None)
        request.session["publish_steps"] = publish_steps
