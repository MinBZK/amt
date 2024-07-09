import logging
from unittest.mock import MagicMock

import amt.core.db as testdb
import pytest
from amt.core.config import Settings
from amt.core.db import (
    add_demo_statuses,
    add_demo_tasks,
    add_demo_users,
    check_db,
    init_db,
    remove_old_demo_objects,
)
from amt.models import Status, Task, User
from sqlmodel import Session, SQLModel, select

from tests.constants import (
    default_status,
    default_task,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils

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
    [
        ({"ENVIRONMENT": "demo", "AUTO_CREATE_SCHEMA": True}),
        ({"ENVIRONMENT": "demo", "AUTO_CREATE_SCHEMA": False}),
        ({"ENVIRONMENT": "production"}),
    ],
    indirect=True,
)
def test_init_database(patch_settings: Settings):
    remove_old_demo_objects_orig = testdb.remove_old_demo_objects
    testdb.remove_old_demo_objects = MagicMock()
    create_all_orig = SQLModel.metadata.create_all
    SQLModel.metadata.create_all = MagicMock()

    init_db()

    if patch_settings.ENVIRONMENT == "demo":
        assert testdb.remove_old_demo_objects.called
    if patch_settings.AUTO_CREATE_SCHEMA is True:
        assert SQLModel.metadata.create_all.called

    testdb.remove_old_demo_objects = remove_old_demo_objects_orig
    SQLModel.metadata.create_all = create_all_orig


def test_remove_old_demo_objects(db: DatabaseTestUtils):
    org_delete = db.get_session().delete
    db_session = db.get_session()
    db_session.delete = MagicMock()

    user = User(name="Robbert", avatar=None)
    status = Status(name="todo", sort_order=1)
    task = Task(title="First task", description="This is the first task", sort_order=1, status_id=status.id)
    db.given([user, status, task])

    remove_old_demo_objects(db.get_session())
    assert db_session.delete.call_count == 3

    db.get_session().delete = org_delete


def test_remove_old_demo_objects_nothing_to_delete(db: DatabaseTestUtils):
    org_delete = db.get_session().delete
    db_session = db.get_session()
    db_session.delete = MagicMock()

    remove_old_demo_objects(db.get_session())
    assert db_session.delete.call_count == 0

    db.get_session().delete = org_delete


def test_add_demo_user(db: DatabaseTestUtils):
    user_names = [default_user().name]
    add_demo_users(db.get_session(), user_names)
    assert db.exists(User, User.name, user_names[0])


def test_add_demo_user_nothing_to_add(db: DatabaseTestUtils):
    db.given([default_user()])

    orig_add = db.get_session().add
    db_session = db.get_session()
    db_session.add = MagicMock()

    add_demo_users(db.get_session(), [default_user().name])

    assert db_session.add.call_count == 0

    db.get_session().add = orig_add


def test_add_demo_status(db: DatabaseTestUtils):
    add_demo_statuses(db.get_session(), [default_status().name])
    assert db.exists(Status, Status.name, default_status().name)


def test_add_demo_status_nothing_to_add(db: DatabaseTestUtils):
    db.given([default_status()])

    orig_add = db.get_session().add
    db_session = db.get_session()
    db_session.add = MagicMock()

    add_demo_statuses(db.get_session(), [default_status().name])

    assert db_session.add.call_count == 0
    db.get_session().add = orig_add


def test_add_demo_tasks(db: DatabaseTestUtils):
    add_demo_tasks(db.get_session(), default_status(), 3)
    assert db.exists(Task, Task.title, "Example task 1")
    assert db.exists(Task, Task.title, "Example task 2")
    assert db.exists(Task, Task.title, "Example task 3")


def test_add_demo_tasks_nothing_to_add(db: DatabaseTestUtils):
    db.given(
        [
            default_task(title="Example task 1"),
            default_task(title="Example task 2"),
            default_task(title="Example task 3"),
        ]
    )

    orig_add = db.get_session().add
    db_session = db.get_session()
    db_session.add = MagicMock()

    add_demo_tasks(db.get_session(), default_status(), 3)
    assert db_session.add.call_count == 0
    db.get_session().add = orig_add


def test_add_demo_tasks_no_status(db: DatabaseTestUtils):
    orig_add = db.get_session().add
    db_session = db.get_session()
    db_session.add = MagicMock()

    add_demo_tasks(db.get_session(), None, 3)
    assert db_session.add.call_count == 0
    db.get_session().add = orig_add
