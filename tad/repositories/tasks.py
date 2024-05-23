from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, select

from tad.models import Task
from tad.repositories.deps import get_session


class TasksRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]):
        self.session = session

    def create_example_tasks(self):
        # todo (robbert) find_all should be a count query
        if len(self.find_all()) == 0:
            self.session.add(
                Task(
                    status_id=1,
                    title="IAMA",
                    description="Impact Assessment Mensenrechten en Algoritmes",
                    sort_order=10,
                )
            )
            self.session.add(Task(status_id=1, title="SHAP", description="SHAP", sort_order=20))
            self.session.add(
                Task(status_id=1, title="This is title 3", description="This is description 3", sort_order=30)
            )
            self.session.commit()

    def find_all(self) -> Sequence[Task]:
        """Returns all the tasks from the repository."""
        return self.session.exec(select(Task)).all()

    def find_by_status_id(self, status_id) -> Sequence[Task]:
        statement = select(Task).where(Task.status_id == status_id).order_by(Task.sort_order)
        return self.session.exec(statement).all()

    def save(self, task) -> Task:
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def find_by_id(self, task_id) -> Task:
        statement = select(Task).where(Task.id == task_id)
        return self.session.exec(statement).one()
