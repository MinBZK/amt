import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.core.exceptions import AMTRepositoryError
from amt.models import Project
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class ProjectsRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]) -> None:
        self.session = session

    def find_all(self) -> Sequence[Project]:
        return self.session.execute(select(Project)).scalars().all()

    def delete(self, project: Project) -> None:
        """
        Deletes the given status in the repository.
        :param status: the status to store
        :return: the updated status after storing
        """
        try:
            self.session.delete(project)
            self.session.commit()
        except Exception as e:
            logger.exception("Error deleting project")
            self.session.rollback()
            raise AMTRepositoryError from e
        return None

    def save(self, project: Project) -> Project:
        try:
            self.session.add(project)
            self.session.commit()
            self.session.refresh(project)
        except SQLAlchemyError as e:
            logger.exception("Error saving project")
            self.session.rollback()
            raise AMTRepositoryError from e
        return project

    def find_by_id(self, project_id: int) -> Project:
        try:
            statement = select(Project).where(Project.id == project_id)
            return self.session.execute(statement).scalars().one()
        except NoResultFound as e:
            logger.exception("Project not found")
            raise AMTRepositoryError from e

    def paginate(self, skip: int, limit: int, search: str) -> list[Project]:
        try:
            statement = select(Project)
            if search != "":
                statement = statement.filter(Project.name.ilike(f"%{escape_like(search)}%"))
            statement = statement.order_by(func.lower(Project.name)).offset(skip).limit(limit)
            return list(self.session.execute(statement).scalars())
        except Exception as e:
            logger.exception("Error paginating projects")
            raise AMTRepositoryError from e
