import logging
from pathlib import Path

import pytest
from amt.core.db import (
    check_db,
    init_db,
    reset_engine,
)
from pytest_mock import MockFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_check_and_init_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mocker: MockFixture):
    database_file = tmp_path / "database.sqlite3"
    monkeypatch.setenv("APP_DATABASE_FILE", str(database_file))
    reset_engine()
    org_exec = AsyncSession.execute
    AsyncSession.execute = mocker.AsyncMock()
    await check_db()
    await init_db()

    assert AsyncSession.execute.call_args is not None
    assert str(select(1)) == str(AsyncSession.execute.call_args.args[0])
    AsyncSession.execute = org_exec
