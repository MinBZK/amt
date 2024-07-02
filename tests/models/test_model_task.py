from tad.models.task import Task


def test_model_basic_task():
    # given

    task = Task(title="Test task", description="", sort_order=1.0)

    # then
    assert task.title == "Test task"
