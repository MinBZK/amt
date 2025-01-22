from amt.api.lifecycles import Lifecycles
from amt.enums.tasks import Status
from amt.models import Algorithm, Organization
from sqlalchemy.ext.asyncio.session import AsyncSession

from tests.constants import default_algorithm_with_lifecycle, default_task, default_user
from tests.database_test_utils import DatabaseTestUtils


async def setup_database_e2e(session: AsyncSession) -> None:
    db_e2e = DatabaseTestUtils(session)

    await db_e2e.given([default_user()])
    default_organization_db = (await db_e2e.get(Organization, "id", 1))[0]
    await db_e2e.given(
        [default_user(id="4738b1e151dc46219556a5662b26517c", name="Test User", organizations=[default_organization_db])]
    )

    algorithms: list[Algorithm] = []
    for idx in range(120):
        algorithms.append(default_algorithm_with_lifecycle(name=f"Algorithm {idx}", lifecycle=Lifecycles.DESIGN))

    await db_e2e.given([*algorithms])

    task1 = default_task(title="task1", status_id=Status.TODO, sort_order=-3, algorithm_id=algorithms[0].id)
    task2 = default_task(title="task2", status_id=Status.TODO, sort_order=-2, algorithm_id=algorithms[0].id)
    task3 = default_task(title="task3", status_id=Status.TODO, sort_order=-1, algorithm_id=algorithms[0].id)

    await db_e2e.given([task1, task2, task3])
