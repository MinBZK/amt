import logging
from collections.abc import Sequence
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like  # pyright: ignore[reportMissingTypeStubs, reportUnknownVariableType]

from amt.api.risk_group import RiskGroup
from amt.core.authorization import AuthorizationType
from amt.core.exceptions import AMTRepositoryError
from amt.models import Algorithm, Authorization
from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session
from amt.repositories.repository_classes import BaseRepository

logger = logging.getLogger(__name__)


def sort_by_lifecycle(algorithm: Algorithm) -> int:
    if algorithm.lifecycle:
        return algorithm.lifecycle.index
    else:
        return -1


def sort_by_lifecycle_reversed(algorithm: Algorithm) -> int:
    if algorithm.lifecycle:
        return -algorithm.lifecycle.index
    else:
        return 1


class AlgorithmsRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSessionWithCommitFlag, Depends(get_session)]) -> None:
        super().__init__(session)

    async def find_all(self) -> Sequence[Algorithm]:
        result = await self.session.execute(select(Algorithm).where(Algorithm.deleted_at.is_(None)))
        return result.scalars().all()

    async def delete(self, algorithm: Algorithm) -> None:
        """
        Deletes the given status in the repository.
        :param status: the status to store
        :return: the updated status after storing
        """
        await self.session.delete(algorithm)
        self.session.should_commit = True

    async def save(self, algorithm: Algorithm) -> Algorithm:
        self.session.add(algorithm)
        await self.session.flush()
        self.session.should_commit = True
        return algorithm

    async def find_by_id(self, algorithm_id: int) -> Algorithm:
        try:
            statement = select(Algorithm).where(Algorithm.id == algorithm_id).where(Algorithm.deleted_at.is_(None))
            result = await self.session.execute(statement)
            return result.scalars().one()
        except NoResultFound as e:
            logger.exception("Algorithm not found")
            raise AMTRepositoryError from e

    async def paginate(  # noqa
        self, skip: int, limit: int, search: str, filters: dict[str, str | list[str | int]], sort: dict[str, str]
    ) -> list[Algorithm]:
        try:
            statement = select(Algorithm)
            if search != "":
                statement = statement.filter(Algorithm.name.ilike(f"%{escape_like(search)}%"))
            if filters:
                for key, value in filters.items():
                    match key:
                        case "user_id":
                            user_id = (
                                UUID(filters["user_id"]) if isinstance(filters["user_id"], str) else filters["user_id"]
                            )
                            statement = (
                                statement.where(Authorization.type_id == Algorithm.id)
                                .where(Authorization.user_id == user_id)
                                .where(Authorization.type == AuthorizationType.ALGORITHM)
                            )
                        case "id":
                            statement = statement.where(Algorithm.id == int(cast(str, value)))
                        case "lifecycle":
                            statement = statement.filter(Algorithm.lifecycle == value)
                        case "risk-group":
                            statement = statement.filter(
                                Algorithm.system_card_json["ai_act_profile"]["risk_group"].as_string()
                                == RiskGroup[cast(str, value)].value
                            )
                        case "organization-id":
                            value = [int(value)] if not isinstance(value, list) else [int(v) for v in value]
                            statement = statement.filter(Algorithm.organization_id.in_(value))
                        case _:
                            raise TypeError(f"Unknown filter type with key: {key}")  # noqa
            if sort:
                if "name" in sort and sort["name"] == "ascending":
                    statement = statement.order_by(func.lower(Algorithm.name).asc())
                elif "name" in sort and sort["name"] == "descending":
                    statement = statement.order_by(func.lower(Algorithm.name).desc())
                elif "last_update" in sort and sort["last_update"] == "ascending":
                    statement = statement.order_by(Algorithm.last_edited.asc())
                elif "last_update" in sort and sort["last_update"] == "descending":
                    statement = statement.order_by(Algorithm.last_edited.desc())
            else:
                statement = statement.order_by(func.lower(Algorithm.name))
            statement = statement.filter(Algorithm.deleted_at.is_(None))
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
            logger.exception("Error paginating algorithms")
            raise AMTRepositoryError from e

    async def get_by_user_and_organization(self, user_id: UUID, organization_id: int) -> Sequence[Algorithm]:
        statement = (
            select(Algorithm)
            .join(Authorization, Authorization.type_id == Algorithm.id)
            .where(Authorization.type == AuthorizationType.ALGORITHM)
            .where(Authorization.user_id == user_id)
            .where(Algorithm.organization_id == organization_id)
        )
        return (await self.session.execute(statement)).scalars().all()
