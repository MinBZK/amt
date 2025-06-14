from amt.api.lifecycles import Lifecycles
from amt.enums.tasks import Status
from amt.models import Algorithm, Authorization
from amt.repositories.deps import AsyncSessionWithCommitFlag

from tests.constants import (
    default_algorithm_with_lifecycle,
    default_organization,
    default_task,
    default_user,
)
from tests.database_test_utils import DatabaseTestUtils


async def setup_database_e2e(session: AsyncSessionWithCommitFlag) -> None:
    db_e2e = DatabaseTestUtils(session)

    await db_e2e.given([default_user()])
    await db_e2e.given([default_algorithm_with_lifecycle()])
    await db_e2e.given([default_organization()])
    await db_e2e.given([default_user(id="4738b1e151dc46219556a5662b26517c", name="Test User")])
    await db_e2e.init_authorizations_and_roles()

    algorithms: list[Algorithm] = []
    for idx in range(120):
        algorithms.append(default_algorithm_with_lifecycle(name=f"Algorithm {idx}", lifecycle=Lifecycles.DESIGN))

    await db_e2e.given([*algorithms])

    for algorithm in algorithms:
        await db_e2e.given(
            [Authorization(user_id=default_user().id, role_id=4, type_id=algorithm.id, type="Algorithm")]
        )

    task1 = default_task(title="task1", status_id=Status.TODO, sort_order=-3, algorithm_id=1)
    task2 = default_task(title="task2", status_id=Status.TODO, sort_order=-2, algorithm_id=1)
    task3 = default_task(title="task3", status_id=Status.TODO, sort_order=-1, algorithm_id=1)

    await db_e2e.given([task1, task2, task3])
