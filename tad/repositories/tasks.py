from collections.abc import Sequence

from sqlmodel import Session, select

from tad.core.db import engine
from tad.core.singleton import Singleton
from tad.models import Task


class TasksRepository(metaclass=Singleton):
    def __init__(self):
        tasks = self.find_all()
        if len(tasks) == 0:
            self.__add_test_tasks()

    def __add_test_tasks(self):
        with Session(engine) as session:
            session.add(
                Task(
                    status_id=1,
                    title="IAMA",
                    description="Impact Assessment Mensenrechten en Algoritmes",
                    sort_order=10,
                )
            )
            session.add(Task(status_id=1, title="SHAP", description="SHAP", sort_order=20))
            session.add(Task(status_id=1, title="This is title 3", description="This is description 3", sort_order=30))
            session.commit()

    def find_all(self) -> Sequence[Task]:
        """Returns all the tasks from the repository."""
        with Session(engine) as session:
            statement = select(Task)
            return session.exec(statement).all()

    def find_by_status_id(self, status_id) -> Sequence[Task]:
        with Session(engine) as session:
            statement = select(Task).where(Task.status_id == status_id).order_by(Task.sort_order)
            return session.exec(statement).all()

    def save(self, task) -> Task:
        with Session(engine) as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def find_by_id(self, task_id) -> Task:
        with Session(engine) as session:
            statement = select(Task).where(Task.id == task_id)
            return session.exec(statement).one()
