from tad.models import Status, Task, User


def default_status():
    return Status(name="Todo", sort_order=1)


def todo_status() -> Status:
    return default_status()


def in_progress_status() -> Status:
    return Status(name="In progress", sort_order=2)


def in_review_status() -> Status:
    return Status(name="In review", sort_order=3)


def done_status() -> Status:
    return Status(name="Done", sort_order=4)


def all_statusses() -> list[Status]:
    return [todo_status(), in_progress_status(), in_review_status(), done_status()]


def default_user(name: str = "default user", avatar: str | None = None) -> User:
    return User(name=name, avatar=avatar)


def default_task(
    title: str = "Default Task",
    description: str = "My default task",
    sort_order: float = 1.0,
    status_id: int | None = None,
    user_id: int | None = None,
) -> Task:
    return Task(title=title, description=description, sort_order=sort_order, status_id=status_id, user_id=user_id)
