from amt.enums.status import Status
from amt.models import Project
from sqlmodel import Session

from tests.constants import default_project, default_task, default_user
from tests.database_test_utils import DatabaseTestUtils


def setup_database_e2e(session: Session) -> None:
    db_e2e = DatabaseTestUtils(session)

    db_e2e.given([default_user()])

    task1 = default_task(title="task1", status_id=Status.TODO, sort_order=-3)
    task2 = default_task(title="task2", status_id=Status.TODO, sort_order=-2)
    task3 = default_task(title="task3", status_id=Status.TODO, sort_order=-1)

    db_e2e.given([task1, task2, task3])

    projects: list[Project] = []
    for _ in range(120):
        projects.append(default_project())

    db_e2e.given([*projects])
