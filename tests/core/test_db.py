import logging
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, select
from tad.core.config import Settings
from tad.core.db import check_db, init_db
from tad.models import Status, Task, User

logger = logging.getLogger(__name__)


def test_check_database():
    org_exec = Session.exec
    Session.exec = MagicMock()
    check_db()

    assert Session.exec.call_args is not None
    assert str(select(1)) == str(Session.exec.call_args.args[0])
    Session.exec = org_exec


@pytest.mark.parametrize(
    "patch_settings",
    [{"ENVIRONMENT": "demo", "AUTO_CREATE_SCHEMA": True}],
    indirect=True,
)
def test_init_database_none(patch_settings: Settings):
    org_exec = Session.exec
    Session.exec = MagicMock()
    Session.exec.return_value.first.return_value = None

    init_db()

    expected = [
        (select(User).where(User.name == "Robbert"),),
        (select(Status).where(Status.name == "Todo"),),
        (select(Task).where(Task.title == "First task"),),
    ]

    for i, call_args in enumerate(Session.exec.call_args_list):
        assert str(expected[i][0]) == str(call_args.args[0])

    Session.exec = org_exec


@pytest.mark.parametrize(
    "patch_settings",
    [{"ENVIRONMENT": "demo", "AUTO_CREATE_SCHEMA": True}],
    indirect=True,
)
def test_init_database(patch_settings: Settings):
    org_exec = Session.exec
    Session.exec = MagicMock()

    init_db()

    expected = [
        (select(User).where(User.name == "Robbert"),),
        (select(Status).where(Status.name == "Todo"),),
        (select(Task).where(Task.title == "First task"),),
    ]

    for i, call_args in enumerate(Session.exec.call_args_list):
        assert str(expected[i][0]) == str(call_args.args[0])

    Session.exec = org_exec
