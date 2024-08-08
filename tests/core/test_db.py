import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from amt.core.db import (
    check_db,
)
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def test_check_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    database_file = tmp_path / "database.sqlite3"
    monkeypatch.setenv("APP_DATABASE_FILE", str(database_file))
    org_exec = Session.exec
    Session.exec = MagicMock()
    check_db()

    assert Session.exec.call_args is not None
    assert str(select(1)) == str(Session.exec.call_args.args[0])
    Session.exec = org_exec
