import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.api.publication_category import PublicationCategories
from amt.core.exceptions import AMTRepositoryError
from amt.models import Project
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


def sort_by_phase(project: Project) -> int:
    if project.lifecycle:
        return project.lifecycle.index
    else:
        return -1


def sort_by_phase_reversed(project: Project) -> int:
    if project.lifecycle:
        return -project.lifecycle.index
    else:
        return 1


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

    def paginate(  # noqa
        self, skip: int, limit: int, search: str, filters: dict[str, str], sort: dict[str, str]
    ) -> list[Project]:
        try:
            statement = select(Project)
            if search != "":
                statement = statement.filter(Project.name.ilike(f"%{escape_like(search)}%"))
            if filters:
                for key, value in filters.items():
                    match key:
                        case "lifecycle":
                            statement = statement.filter(Project.lifecycle == value)
                        case "publication-category":
                            statement = statement.filter(
                                Project.system_card_json["ai_act_profile"]["publication_category"].as_string()
                                == PublicationCategories[value].value
                            )
                        case _:
                            raise TypeError("Unknown filter type")  # noqa
            if sort:
                if "name" in sort and sort["name"] == "ascending":
                    statement = statement.order_by(func.lower(Project.name).asc())
                elif "name" in sort and sort["name"] == "descending":
                    statement = statement.order_by(func.lower(Project.name).desc())
                elif "last_update" in sort and sort["last_update"] == "ascending":
                    statement = statement.order_by(Project.last_edited.asc())
                elif "last_update" in sort and sort["last_update"] == "descending":
                    statement = statement.order_by(Project.last_edited.desc())
            else:
                statement = statement.order_by(func.lower(Project.name))
            statement = statement.offset(skip).limit(limit)
            result = list(self.session.execute(statement).scalars())
            # todo: the good way to do sorting is to use an enum field (or any int field)
            #  in the database so we can sort on that
            if result and sort and "phase" in sort:
                if sort["phase"] == "ascending":
                    result = sorted(result, key=sort_by_phase)
                else:
                    result = sorted(result, key=sort_by_phase_reversed)
            return result  # noqa
        except Exception as e:
            logger.exception("Error paginating projects")
            raise AMTRepositoryError from e
