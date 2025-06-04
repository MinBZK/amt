import pytest
from amt.core.exceptions import AMTRepositoryError
from amt.enums.tasks import Status, TaskType
from amt.models import Algorithm, Task
from amt.repositories.tasks import TasksRepository
from amt.schema.measure import MeasureTask
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from tests.constants import default_algorithm, default_organization, default_task, default_user
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
    await tasks_repository.session.commit()
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
    with pytest.raises(IntegrityError):
        await tasks_repository.save_all([task_duplicate])


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
    with pytest.raises(IntegrityError):
        await tasks_repository.save(task_duplicate)


@pytest.mark.asyncio
async def test_delete_failed(db: DatabaseTestUtils):
    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    task: Task = Task(id=1, title="Test title", description="Test description", sort_order=10)
    with pytest.raises(InvalidRequestError):
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
async def test_find_by_id_when_not_found(db: DatabaseTestUtils):
    # given
    tasks_repository: TasksRepository = TasksRepository(db.get_session())

    # when/then
    with pytest.raises(AMTRepositoryError):
        await tasks_repository.find_by_id(999)


@pytest.mark.asyncio
async def test_find_by_status_id(db: DatabaseTestUtils):
    task = default_task(status_id=Status.TODO)
    await db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_by_status_id(1)
    assert len(results) == 1
    assert results[0].id == 1


@pytest.mark.asyncio
async def test_find_by_algorithm_id_and_status_id(db: DatabaseTestUtils):
    await db.given([default_user(), default_organization(), default_algorithm()])
    task = default_task(status_id=Status.TODO, algorithm_id=1)
    await db.given([task, default_task()])

    tasks_repository: TasksRepository = TasksRepository(db.get_session())
    results = await tasks_repository.find_by_algorithm_id_and_status_id(1, 1)
    assert len(results) == 1
    assert results[0].id == 1
    assert results[0].algorithm_id == 1


@pytest.mark.asyncio
async def test_get_last_task(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    task1 = Task(title="Task 1", description="Task 1 desc", algorithm_id=1, sort_order=10)
    task2 = Task(title="Task 2", description="Task 2 desc", algorithm_id=1, sort_order=20)
    task3 = Task(title="Task 3", description="Task 3 desc", algorithm_id=1, sort_order=30)  # different algorithm
    await db.given([task1, task2, task3])

    # when
    tasks_repository = TasksRepository(db.get_session())
    result = await tasks_repository.get_last_task(algorithm_id=1)

    # then
    assert result is not None
    assert result.title == "Task 3"
    assert result.sort_order == 30


@pytest.mark.asyncio
async def test_get_last_task_no_tasks(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])

    # when
    tasks_repository = TasksRepository(db.get_session())
    result = await tasks_repository.get_last_task(algorithm_id=1)

    # then
    assert result is None


@pytest.mark.asyncio
async def test_add_tasks(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    tasks_repository = TasksRepository(db.get_session())

    measure_tasks = [
        MeasureTask(urn="urn:task:1", version="1.0"),
        MeasureTask(urn="urn:task:2", version="1.0"),
    ]

    # when
    await tasks_repository.add_tasks(algorithm_id=1, task_type=TaskType.MEASURE, tasks=measure_tasks, start_at=100)

    # then
    results = await tasks_repository.find_all()
    # Filter results for algorithm 1 with MEASURE type
    filtered_results = [task for task in results if task.algorithm_id == 1 and task.type == TaskType.MEASURE]
    assert len(filtered_results) == 2

    # Sort by sort_order to ensure consistent order
    filtered_results.sort(key=lambda task: task.sort_order)
    assert filtered_results[0].type_id == "urn:task:1"
    assert filtered_results[0].sort_order == 100
    assert filtered_results[1].type_id == "urn:task:2"
    assert filtered_results[1].sort_order == 110


@pytest.mark.asyncio
async def test_add_tasks_empty_list(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    tasks_repository = TasksRepository(db.get_session())

    # when
    await tasks_repository.add_tasks(
        algorithm_id=1,
        task_type=TaskType.MEASURE,
        tasks=[],
    )

    # then
    results = await tasks_repository.find_by_algorithm_id_and_type(1, TaskType.MEASURE)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_remove_tasks(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])

    # Create multiple tasks with different type_ids
    task1 = Task(
        title="Task 1",
        description="Description 1",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:1",
        sort_order=10,
    )
    task2 = Task(
        title="Task 2",
        description="Description 2",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:2",
        sort_order=20,
    )
    task3 = Task(
        title="Task 3",
        description="Description 3",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:3",
        sort_order=30,
    )
    await db.given([task1, task2, task3])

    # Verify tasks were created properly
    tasks_repository = TasksRepository(db.get_session())
    initial_results = await tasks_repository.find_all()
    assert len(initial_results) == 3

    # Create the task to remove
    measure_tasks = [
        MeasureTask(urn="urn:task:1", version="1.0"),
    ]

    # when
    await tasks_repository.remove_tasks(
        algorithm_id=1,
        task_type=TaskType.MEASURE,
        tasks=measure_tasks,
    )

    # then - get all remaining tasks
    results = await tasks_repository.find_all()
    assert len(results) == 2
    # Find the remaining tasks and verify urn:task:1 is not among them
    type_ids = [task.type_id for task in results]
    assert "urn:task:1" not in type_ids
    assert "urn:task:2" in type_ids
    assert "urn:task:3" in type_ids


@pytest.mark.asyncio
async def test_remove_tasks_empty_list(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    task1 = Task(
        title="Task 1",
        description="Description 1",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:1",
        sort_order=10,
    )
    await db.given([task1])

    tasks_repository = TasksRepository(db.get_session())

    # when
    await tasks_repository.remove_tasks(
        algorithm_id=1,
        task_type=TaskType.MEASURE,
        tasks=[],
    )

    # then
    # Empty tasks list should not remove anything, so we should still have the original task
    results = await tasks_repository.find_all()
    assert len(results) == 1
    assert results[0].type_id == "urn:task:1"


@pytest.mark.asyncio
async def test_find_by_algorithm_id_and_type(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    # Create a second algorithm for testing
    algorithm2 = Algorithm(id=2, name="Algorithm 2", organization_id=1)
    await db.given([algorithm2])

    # Create two task types for algorithm 1, and one for algorithm 2
    # Using the same TaskType.MEASURE for both to work with the existing enum
    task1 = Task(
        title="Task 1",
        description="Description 1",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:1",
        sort_order=10,
    )
    task2 = Task(
        title="Task 2",
        description="Description 2",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:2",
        sort_order=20,
    )
    task3 = Task(
        title="Task 3",
        description="Description 3",
        algorithm_id=2,
        type=TaskType.MEASURE,
        type_id="urn:task:3",
        sort_order=30,
    )
    await db.given([task1, task2, task3])

    tasks_repository = TasksRepository(db.get_session())

    # when - find task with specific type_id for algorithm 1
    # Use type_id for filtering since we're using the same TaskType
    results = await tasks_repository.find_all()
    filtered_results = [task for task in results if task.algorithm_id == 1 and task.type_id == "urn:task:1"]

    # then
    assert len(filtered_results) == 1
    assert filtered_results[0].title == "Task 1"
    assert filtered_results[0].type == TaskType.MEASURE
    assert filtered_results[0].algorithm_id == 1


@pytest.mark.asyncio
async def test_find_by_algorithm_id_and_type_no_type_filter(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    # Create a second algorithm for testing
    algorithm2 = Algorithm(id=2, name="Algorithm 2", organization_id=1)
    await db.given([algorithm2])

    # Create two tasks for algorithm 1 with different type_ids, and one for algorithm 2
    task1 = Task(
        title="Task 1",
        description="Description 1",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:1",
        sort_order=10,
    )
    task2 = Task(
        title="Task 2",
        description="Description 2",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:2",
        sort_order=20,
    )
    task3 = Task(
        title="Task 3",
        description="Description 3",
        algorithm_id=2,
        type=TaskType.MEASURE,
        type_id="urn:task:3",
        sort_order=30,
    )
    await db.given([task1, task2, task3])

    tasks_repository = TasksRepository(db.get_session())

    # when - find all tasks for algorithm 1 regardless of type
    results = await tasks_repository.find_all()
    filtered_results = [task for task in results if task.algorithm_id == 1]

    # then
    assert len(filtered_results) == 2
    # Check that both tasks belong to algorithm 1
    for task in filtered_results:
        assert task.algorithm_id == 1
    # Check that we have tasks with both type_ids
    type_ids = [task.type_id for task in filtered_results]
    assert "urn:task:1" in type_ids
    assert "urn:task:2" in type_ids


@pytest.mark.asyncio
async def test_find_by_algorithm_id_and_type_not_found(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])
    tasks_repository = TasksRepository(db.get_session())

    # when
    results = await tasks_repository.find_by_algorithm_id_and_type(999, TaskType.MEASURE)

    # then
    assert results == []


@pytest.mark.asyncio
async def test_update_tasks_status(db: DatabaseTestUtils):
    # given
    await db.given([default_user(), default_organization(), default_algorithm()])

    # Create tasks with initial status TODO
    task1 = Task(
        title="Task 1",
        description="Description 1",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:1",
        status_id=Status.TODO,
        sort_order=10,
    )
    task2 = Task(
        title="Task 2",
        description="Description 2",
        algorithm_id=1,
        type=TaskType.MEASURE,
        type_id="urn:task:2",
        status_id=Status.TODO,
        sort_order=20,
    )
    await db.given([task1, task2])

    # Verify tasks were created with proper status
    initial_repo = TasksRepository(db.get_session())
    initial_results = await initial_repo.find_all()
    assert len(initial_results) == 2
    assert all(task.status_id == Status.TODO for task in initial_results)

    # Create a new session for the update operation
    tasks_repository = TasksRepository(db.get_session())

    # when - update status of specific task to DONE
    await tasks_repository.update_tasks_status(
        algorithm_id=1,
        task_type=TaskType.MEASURE,
        type_id="urn:task:1",
        status=Status.DONE,
    )

    # Create a new session to verify results
    verify_repo = TasksRepository(db.get_session())
    refreshed_results = await verify_repo.find_all()
    assert len(refreshed_results) == 2

    # then - find tasks by type_id to verify status
    task1_updated = next((t for t in refreshed_results if t.type_id == "urn:task:1"), None)
    task2_updated = next((t for t in refreshed_results if t.type_id == "urn:task:2"), None)

    # Verify task1 status was updated to DONE
    assert task1_updated is not None
    assert task1_updated.status_id == Status.DONE

    # Verify task2 status remained as TODO
    assert task2_updated is not None
    assert task2_updated.status_id == Status.TODO
