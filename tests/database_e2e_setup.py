from amt.api.lifecycles import Lifecycles
from amt.enums.status import Status
from amt.models import Project
from sqlalchemy.ext.asyncio.session import AsyncSession

from tests.constants import default_project_with_lifecycle, default_task, default_user
from tests.database_test_utils import DatabaseTestUtils


async def setup_database_e2e(session: AsyncSession) -> None:
    db_e2e = DatabaseTestUtils(session)

    await db_e2e.given([default_user()])

    projects: list[Project] = []
    for idx in range(120):
        projects.append(default_project_with_lifecycle(name=f"Project {idx}", lifecycle=Lifecycles.DESIGN))

    await db_e2e.given([*projects])

    task1 = default_task(title="task1", status_id=Status.TODO, sort_order=-3, project_id=projects[0].id)
    task2 = default_task(title="task2", status_id=Status.TODO, sort_order=-2, project_id=projects[0].id)
    task3 = default_task(title="task3", status_id=Status.TODO, sort_order=-1, project_id=projects[0].id)

    await db_e2e.given([task1, task2, task3])
