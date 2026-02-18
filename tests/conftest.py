import asyncio
import hashlib
import logging
import os
import re
from collections.abc import AsyncIterator, Callable, Generator
from multiprocessing import Process
from pathlib import Path
from typing import Any

import httpx
import nest_asyncio  # pyright: ignore [(reportMissingTypeStubs)]
import pytest
import pytest_asyncio
import uvicorn
import vcr  # pyright: ignore[reportMissingTypeStubs]
from amt.models.base import Base
from amt.repositories.deps import AsyncSessionWithCommitFlag
from amt.server import create_app
from httpx import ASGITransport, AsyncClient
from playwright.sync_api import Browser, BrowserContext, Page
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from vcr.config import RecordMode  # pyright: ignore[reportMissingTypeStubs]

from tests.constants import default_auth_user
from tests.database_e2e_setup import setup_database_e2e
from tests.database_test_utils import DatabaseTestUtils

logger = logging.getLogger(__name__)

# Dubious choice here: allow nested event loops.
nest_asyncio.apply()  # type: ignore [(reportUnknownMemberType)]

# VCR intercepts HTTP requests at the httpcore level, but httpx still logs as if requests were made.
# We suppress httpx/httpcore/vcr logging to avoid confusion - the requests are served from VCR cassettes.
logging.getLogger("vcr").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# we use a custom VCR as I could not find out how to use global settings
# ONCE mode plays back existing cassettes but blocks new unrecorded requests (safer for CI)
amt_vcr = vcr.VCR(ignore_hosts=["127.0.0.1", "localhost", "testserver"], record_mode=RecordMode.ONCE)

global_e2e_engine: AsyncEngine | None = None


def run_server_uvicorn(database_file: Path, host: str = "127.0.0.1", port: int = 3462) -> None:
    os.environ["APP_DATABASE_FILE"] = "/" + str(database_file)
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
    os.environ["DISABLE_AUTH"] = "true"
    os.environ["OIDC_CLIENT_ID"] = "AMT"
    os.environ["OIDC_DISCOVERY_URL"] = (
        "https://keycloak.rig.prd1.gn2.quattro.rijksapps.nl/realms/amt-test/.well-known/openid-configuration"
    )
    logger.info(os.environ["APP_DATABASE_FILE"])
    app = create_app()
    uvicorn.run(app, host=host, port=port, loop="asyncio")


@pytest.fixture(scope="session")
async def setup_db_and_server(
    tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
) -> AsyncIterator[str]:
    global global_e2e_engine
    test_dir = tmp_path_factory.mktemp("e2e_database")
    database_file = test_dir / "test.sqlite3"

    if request.config.getoption("--db") == "postgresql":
        engine = create_async_engine(get_db_uri())
    else:
        engine = create_async_engine(f"sqlite+aiosqlite:///{database_file}", connect_args={"check_same_thread": False})

    global_e2e_engine = engine

    metadata = Base.metadata

    process = Process(target=run_server_uvicorn, args=(database_file,))
    process.start()
    yield "http://127.0.0.1:3462"
    process.terminate()

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture(autouse=True)
def disable_auth(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = request.node.get_closest_marker("enable_auth")  # type: ignore [(reportUnknownMemberType)]

    if marker:
        monkeypatch.setenv("DISABLE_AUTH", "false")
    else:
        monkeypatch.setenv("DISABLE_AUTH", "true")
        monkeypatch.setenv("AUTO_LOGIN_UUID", default_auth_user()["sub"])
    return


def pytest_configure(config: pytest.Config) -> None:
    if "APP_DATABASE_SCHEME" not in os.environ:
        os.environ["APP_DATABASE_SCHEME"] = str(config.getoption("--db"))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--db", action="store", default="sqlite", help="db: sqlite or postgresql", choices=("sqlite", "postgresql")
    )


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]):
    # this hook into pytest makes sure that the e2e tests are run last
    e2e_tests: list[pytest.Item] = []
    tests: list[pytest.Item] = []

    for item in items:
        if item.location[0].startswith("tests/e2e") or item.location[0].startswith("tests/regression"):
            e2e_tests.append(item)
        else:
            tests.append(item)

    e2e_tests.sort(key=lambda item: item.name)

    logger.info("e2e test order:")
    for item in e2e_tests:
        logger.info(item.name)

    items[:] = tests + e2e_tests


@pytest_asyncio.fixture  # type: ignore [(reportUnknownMemberType)]
async def client(db: DatabaseTestUtils, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    # overwrite db url
    monkeypatch.setenv("APP_DATABASE_FILE", "/" + str(db.get_database_file()))

    from amt.core.db import reset_engine
    from amt.repositories.deps import get_session

    reset_engine()
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=True), base_url="http://testserver/"
    ) as ac:
        app.dependency_overrides[get_session] = db.get_session
        ac.timeout = 5
        yield ac


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {**browser_context_args, "base_url": "http://127.0.0.1:3462"}


@pytest.fixture
def reset_database() -> None:
    loop = asyncio.get_event_loop()

    async def async_reset() -> None:
        if not global_e2e_engine:
            raise ValueError("Engine should be available for E2E testing")

        metadata = Base.metadata
        async with global_e2e_engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
            await conn.run_sync(metadata.create_all)

        async_session = async_sessionmaker(global_e2e_engine, expire_on_commit=False, class_=AsyncSessionWithCommitFlag)
        async with async_session() as session:
            await setup_database_e2e(session)

    loop.run_until_complete(async_reset())


@pytest.fixture
def page(context: BrowserContext, reset_database: None) -> Page:
    # Create and return the page
    page = context.new_page()
    do_e2e_login(page)
    return page


@pytest.fixture
def page_no_login(context: BrowserContext, reset_database: None) -> Page:
    return context.new_page()


@pytest.fixture(scope="session")
def browser(
    launch_browser: Callable[[], Browser],
    setup_db_and_server: AsyncIterator[str],
) -> Generator[Browser, None, None]:
    transport = httpx.HTTPTransport(retries=5)

    loop = asyncio.get_event_loop()
    url = loop.run_until_complete(setup_db_and_server.__anext__())

    with httpx.Client(transport=transport, verify=False, timeout=0.7) as client:  # noqa: S501
        client.get(f"{url}/")

    browser = launch_browser()
    yield browser
    browser.close()
    # Clean up by consuming the rest of the generator.
    try:  # noqa
        loop.run_until_complete(setup_db_and_server.__anext__())
    except StopAsyncIteration:
        pass


def get_db_uri() -> str:
    user = os.getenv("APP_DATABASE_USER", "amt")
    password = os.getenv("APP_DATABASE_PASSWORD", "changethis")
    server = os.getenv("APP_DATABASE_SERVER", "db")
    driver = os.getenv("APP_DATABASE_DRIVER", "asyncpg")
    port = os.getenv("APP_DATABASE_PORT", "5432")
    db = os.getenv("APP_DATABASE_DB", "amt")
    return f"postgresql+{driver}://{user}:{password}@{server}:{port}/{db}"


async def create_db(new_db: str) -> str:
    url = get_db_uri()
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")

    if new_db == os.getenv("APP_DATABASE_USER", "amt"):
        return url

    logger.info(f"Creating database {new_db}")
    user = os.getenv("APP_DATABASE_USER", "amt")

    async with engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {new_db};"))  # type: ignore
        await conn.execute(text(f"CREATE DATABASE {new_db} OWNER {user};"))  # type: ignore
        await conn.commit()

    path = Path(url)
    return str(path.parent / new_db).replace("postgresql+asyncpg:/", "postgresql+asyncpg://")


def generate_db_name(request: pytest.FixtureRequest) -> str:
    pattern = re.compile(r"[^a-zA-Z0-9_]")

    inverted_modulename = ".".join(request.module.__name__.split(".")[::-1])  # type: ignore
    testname = request.node.name  # type: ignore

    db_name = testname + "_" + inverted_modulename  # type: ignore
    sanitized_name = pattern.sub("_", db_name)  # type: ignore

    # postgres has a limit of 63 bytes for database names
    if len(sanitized_name) > 63:
        hash_suffix = hashlib.md5(sanitized_name.encode()).hexdigest()[:8]  # noqa: S324
        sanitized_name = sanitized_name[:54] + "_" + hash_suffix

    return sanitized_name


@pytest_asyncio.fixture  # type: ignore [(reportUnknownMemberType)]
async def db(
    tmp_path: Path, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[DatabaseTestUtils]:
    database_file = tmp_path / "test.sqlite3"

    if request.config.getoption("--db") == "postgresql":
        db_name: str = generate_db_name(request)
        url = await create_db(db_name)
        monkeypatch.setenv("APP_DATABASE_DB", db_name)
        engine = create_async_engine(url)
    else:
        engine = create_async_engine(f"sqlite+aiosqlite:///{database_file}", connect_args={"check_same_thread": False})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSessionWithCommitFlag)
    async with async_session() as session:
        thread = (await session.connection()).sync_connection.connection.driver_connection  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportOptionalMemberAccess, reportAttributeAccessIssue]
        logger.debug(f"Creating session on thread {thread}")
        session.info["id"] = str(id(session)) + " (pytest)"
        db = DatabaseTestUtils(session, database_file)
        yield db
        await db.close()


def do_e2e_login(page: Page):
    page.goto("/")
    page.locator("#header-link-login").click()
    page.fill("#username", "default")
    page.fill("#password", "default")
    page.locator("#kc-login").click()
