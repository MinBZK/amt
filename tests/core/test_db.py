import logging
from pathlib import Path

import pytest
from amt.core.db import (
    check_db,
)
from pytest_mock import MockFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def test_check_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mocker: MockFixture):
    database_file = tmp_path / "database.sqlite3"
    monkeypatch.setenv("APP_DATABASE_FILE", str(database_file))
    org_exec = Session.execute
    Session.execute = mocker.MagicMock()
    check_db()

    assert Session.execute.call_args is not None
    assert str(select(1)) == str(Session.execute.call_args.args[0])
    Session.execute = org_exec
