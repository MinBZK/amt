import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.api.publication_category import PublicationCategories
from amt.core.exceptions import AMTRepositoryError
from amt.models import Project
from amt.repositories.deps import get_session

logger = logging.getLogger(__name__)


def sort_by_lifecycle(project: Project) -> int:
    if project.lifecycle:
        return project.lifecycle.index
    else:
        return -1


def sort_by_lifecycle_reversed(project: Project) -> int:
    if project.lifecycle:
        return -project.lifecycle.index
    else:
        return 1


class ProjectsRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]) -> None:
        self.session = session

    async def find_all(self) -> Sequence[Project]:
        result = await self.session.execute(select(Project).where(Project.deleted_at.is_(None)))
        return result.scalars().all()

    async def delete(self, project: Project) -> None:
        """
        Deletes the given status in the repository.
        :param status: the status to store
        :return: the updated status after storing
        """
        try:
            await self.session.delete(project)
            await self.session.commit()
        except Exception as e:
            logger.exception("Error deleting project")
            await self.session.rollback()
            raise AMTRepositoryError from e
        return None

    async def save(self, project: Project) -> Project:
        try:
            self.session.add(project)
            await self.session.commit()
            await self.session.refresh(project)
        except SQLAlchemyError as e:
            logger.exception("Error saving project")
            await self.session.rollback()
            raise AMTRepositoryError from e
        return project

    async def find_by_id(self, project_id: int) -> Project:
        try:
            statement = select(Project).where(Project.id == project_id).where(Project.deleted_at.is_(None))
            result = await self.session.execute(statement)
            return result.scalars().one()
        except NoResultFound as e:
            logger.exception("Project not found")
            raise AMTRepositoryError from e

    async def paginate(  # noqa
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
                            raise TypeError(f"Unknown filter type with key: {key}")  # noqa
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
            statement = statement.filter(Project.deleted_at.is_(None))
            statement = statement.offset(skip).limit(limit)
            db_result = await self.session.execute(statement)
            result = list(db_result.scalars())
            # todo: the good way to do sorting is to use an enum field (or any int field)
            #  in the database so we can sort on that
            if result and sort and "lifecycle" in sort:
                if sort["lifecycle"] == "ascending":
                    result = sorted(result, key=sort_by_lifecycle)
                else:
                    result = sorted(result, key=sort_by_lifecycle_reversed)
            return result  # noqa
        except Exception as e:
            logger.exception("Error paginating projects")
            raise AMTRepositoryError from e
