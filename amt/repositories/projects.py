import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlmodel import Session, select

from amt.core.exceptions import RepositoryError, RepositoryNoResultFound
from amt.models import Project
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


class ProjectsRepository:
    def __init__(self, session: Annotated[Session, Depends(get_session)]) -> None:
        self.session = session

    def find_all(self) -> Sequence[Project]:
        return self.session.exec(select(Project)).all()

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
            self.session.rollback()
            raise RepositoryError from e
        return None

    def save(self, project: Project) -> Project:
        try:
            self.session.add(project)
            self.session.commit()
            self.session.refresh(project)
        except SQLAlchemyError as e:
            logger.debug(f"Error saving project: {project}")
            self.session.rollback()
            raise RepositoryError from e
        return project

    def find_by_id(self, project_id: int) -> Project:
        try:
            statement = select(Project).where(Project.id == project_id)
            return self.session.exec(statement).one()
        except NoResultFound as e:
            raise RepositoryError from e

    def paginate(self, skip: int, limit: int) -> list[Project]:
        try:
            statement = select(Project).order_by(func.lower(Project.name)).offset(skip).limit(limit)
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise RepositoryNoResultFound from e
