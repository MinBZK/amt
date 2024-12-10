import json
import typing

from amt.api.decorators import add_permissions
from amt.core.authorization import AuthorizationResource, AuthorizationVerb
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]

app = FastAPI()


@app.get("/unauthorized")
@add_permissions(permissions={"algoritme/1": [AuthorizationVerb.CREATE]})
async def unauthorized(request: Request):
    return {"message": "Hello World"}


@app.get("/authorized")
@add_permissions(permissions={})
async def authorized(request: Request):
    return {"message": "Hello World"}


@app.get("/norequest")
@add_permissions(permissions={})
async def norequest():
    return {"message": "Hello World"}


@app.get("/authorizedparameters/{organization_id}")
@add_permissions(permissions={AuthorizationResource.ORGANIZATION_INFO: [AuthorizationVerb.CREATE]})
async def authorizedparameters(request: Request, organization_id: int):
    return {"message": "Hello World"}


@app.middleware("http")
async def add_authorizations(request: Request, call_next: RequestResponseEndpoint):
    if "X-Permissions" in request.headers:
        request.state.permissions = json.loads(request.headers["X-Permissions"])
    return await call_next(request)


def test_permission_decorator_norequest():
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/norequest")
    assert response.status_code == 400


def test_permission_decorator_unauthorized():
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/unauthorized")
    assert response.status_code == 401


def test_permission_decorator_authorized():
    client = TestClient(app, base_url="https://testserver")
    response = client.get(
        "/authorized",
    )
    assert response.status_code == 200


def test_permission_decorator_authorized_permission():
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/unauthorized", headers={"X-Permissions": '{"algoritme/1": ["Create"]}'})
    assert response.status_code == 200


def test_permission_decorator_authorized_permission_missing():
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/unauthorized", headers={"X-Permissions": '{"algoritme/1": ["Read"]}'})
    assert response.status_code == 401


def test_permission_decorator_authorized_permission_variable():
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/authorizedparameters/1", headers={"X-Permissions": '{"organization/1": ["Create"]}'})
    assert response.status_code == 200


def test_permission_decorator_unauthorized_permission_variable():
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/authorizedparameters/4453546", headers={"X-Permissions": '{"organization/1": ["Create"]}'})
    assert response.status_code == 401
