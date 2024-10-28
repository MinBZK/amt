import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.enums.status import Status
from amt.models import Task
from amt.repositories.tasks import TasksRepository
from tests.constants import default_project, default_task
from tests.database_test_utils import DatabaseTestUtils


@pytest.mark.asyncio
async def test_find_all(db: DatabaseTestUtils):
    await db.given([default_task(), default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_all()
    assert results[0].id == 1
    assert results[1].id == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_find_all_no_results(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_all()
    assert len(results) == 0


@pytest.mark.asyncio
async def test_save(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    await tasks_repository.save(task)
    result = await tasks_repository.find_by_id(1)

    assert result.id == 1
    assert result.title == "Test title"
    assert result.description == "Test description"
    assert result.sort_order == 10

    await tasks_repository.delete(task)  # cleanup


@pytest.mark.asyncio
async def test_save_all(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task_1: Task = Task(id=1, title="Test title 1", description="Test description 1", sort_order=10)
    task_2: Task = Task(id=2, title="Test title 2", description="Test description 2", sort_order=11)
    await tasks_repository.save_all([task_1, task_2])
    result_1 = await tasks_repository.find_by_id(1)
    result_2 = await tasks_repository.find_by_id(2)

    assert result_1.id == 1
    assert result_1.title == "Test title 1"
    assert result_1.description == "Test description 1"
    assert result_1.sort_order == 10

    assert result_2.id == 2
    assert result_2.title == "Test title 2"
    assert result_2.description == "Test description 2"
    assert result_2.sort_order == 11

    await tasks_repository.delete(task_1)  # cleanup
    await tasks_repository.delete(task_2)  # cleanup


@pytest.mark.asyncio
async def test_save_all_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    await tasks_repository.save_all([task])
    task_duplicate: Task = Task(id=1, title="Test title duplicate", description="Test description", sort_order=10)
    with pytest.raises(AMTRepositoryError):
        await tasks_repository.save_all([task_duplicate])

    await tasks_repository.delete(task)  # cleanup


@pytest.mark.asyncio
async def test_delete_task(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)

    await tasks_repository.save(task)
    await tasks_repository.delete(task)  # cleanup

    results = await tasks_repository.find_all()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_save_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    await tasks_repository.save(task)
    task_duplicate: Task = Task(id=1, title="Test title duplicate", description="Test description", sort_order=10)
    with pytest.raises(AMTRepositoryError):
        await tasks_repository.save(task_duplicate)

    await tasks_repository.delete(task)  # cleanup


@pytest.mark.asyncio
async def test_delete_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    with pytest.raises(AMTRepositoryError):
        await tasks_repository.delete(task)


@pytest.mark.asyncio
async def test_find_by_id(db: DatabaseTestUtils):
    task = default_task()
    await db.given([task])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    result: Task = await tasks_repository.find_by_id(1)
    assert result.id == 1
    assert result.title == "Default Task"


@pytest.mark.asyncio
async def test_find_by_id_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    with pytest.raises(AMTRepositoryError):
        await tasks_repository.find_by_id(1)


@pytest.mark.asyncio
async def test_find_by_status_id(db: DatabaseTestUtils):
    task = default_task(status_id=Status.TODO)
    await db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_by_status_id(1)
    assert len(results) == 1
    assert results[0].id == 1


@pytest.mark.asyncio
async def test_find_by_project_id_and_status_id(db: DatabaseTestUtils):
    await db.given([default_project()])
    task = default_task(status_id=Status.TODO, project_id=1)
    await db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_by_project_id_and_status_id(1, 1)
    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].project_id == 1
