import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlmodel import Session, select

from tad.core.exceptions import RepositoryError
from tad.models import Project
from tad.repositories.deps import get_session

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
