import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypeVar, cast, get_type_hints

from fastapi import Depends

from amt.repositories.deps import AsyncSessionWithCommitFlag, get_session, get_session_non_generator
from amt.repositories.repository_classes import BaseRepository
from amt.services.service_classes import BaseService

logger = logging.getLogger(__name__)

S = TypeVar("S", bound=BaseService)
R = TypeVar("R", bound=BaseRepository)
T = TypeVar("T", bound=BaseService | BaseRepository)


class ServicesProvider:
    """
    ServicesProvider manages the creation and lifecycle of services and repositories.

    This class implements a dependency injection container that lazily instantiates
    services and repositories when requested, and automatically resolves their
    dependencies.

    The ServiceProvider can be used both with or without FastAPI dependency injection. In
    the last case, it creates a databases session itself.

    Usage:
        # In FastAPI routes
        @app.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            provider: Annotated[ServiceProvider, Depends(get_service_provider)]
        ):
            user_service = await provider.get(UserService)
            return await user_service.get_user(user_id)

        # In non-FastAPI routes
        async def process_job():
            provider = ServiceProvider()
            async with provider.session_scope():
                job_service = await provider.get(UserService)
                return await user_service.get_user(user_id)
    """

    def __init__(self, session: AsyncSessionWithCommitFlag | None = None) -> None:
        self._session = session
        if self._session:
            logger.debug(
                f"ServiceProvider {id(self)} initialized with session {self._session.info.get('id', 'unknown')}"
            )
        self._services: dict[type[BaseService], BaseService] = {}
        self._repositories: dict[type[BaseRepository], BaseRepository] = {}
        self._should_close_session = False

    async def initialize_session_if_needed(self) -> AsyncSessionWithCommitFlag:
        if self._session is None:
            self._session = await get_session_non_generator()
            self._should_close_session = True
            conn = (await self._session.connection()).sync_connection.connection.driver_connection  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportOptionalMemberAccess, reportAttributeAccessIssue]
            logger.debug(
                f"ServiceProvider {id(self)} created a new session {conn} / {self._session.info.get('id', 'unknown')}"
            )
        else:
            conn = (await self._session.connection()).sync_connection.connection.driver_connection  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportOptionalMemberAccess, reportAttributeAccessIssue]
            logger.debug(f"ServiceProvider {id(self)} using session {conn} / {self._session.info.get('id', 'unknown')}")

        return self._session

    async def get_session(self) -> AsyncSessionWithCommitFlag:
        return await self.initialize_session_if_needed()

    async def close(self) -> None:
        if self._should_close_session and self._session is not None:
            logger.debug(f"ServiceProvider {id(self)} closes session {id(self._session)}")
            await self._session.close()
            self._session = None
            self._should_close_session = False

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator["ServicesProvider", None]:
        """
        For use outside the FastAPI scope, use this context manager instead.
        """
        try:
            await self.initialize_session_if_needed()
            yield self
        finally:
            logger.debug(f"ServiceProvider {id(self)} contextmanager closes session {id(self._session)}")
            await self.close()

    async def get_repository(self, repo_class: type[R]) -> R:
        if repo_class not in self._repositories:
            repo_instance = await self._resolve_dependencies(repo_class)
            self._repositories[repo_class] = repo_instance
            logger.debug(f"ServiceProvider {id(self)} instantiated a new repository {repo_class.__name__}")

        return cast(R, self._repositories[repo_class])

    async def get(self, service_class: type[S]) -> S:
        if service_class not in self._services:
            service = await self._resolve_dependencies(service_class)
            self._services[service_class] = service
            logger.debug(f"ServiceProvider {id(self)} instantiated a new service {service_class.__name__}")

        return cast(S, self._services[service_class])

    async def _resolve_dependencies(self, target_class: type[T]) -> T:
        init_params: dict[str, Any] = {}
        param_hints = get_type_hints(target_class.__init__)

        await self.get_session()

        for param_name, param_type in param_hints.items():
            if param_name == "self":
                continue
            if param_type is AsyncSessionWithCommitFlag:
                init_params[param_name] = await self.get_session()
            elif param_type and isinstance(param_type, type) and issubclass(param_type, BaseRepository):
                init_params[param_name] = await self.get_repository(param_type)
            elif param_type and isinstance(param_type, type) and issubclass(param_type, BaseService):
                init_params[param_name] = await self.get(param_type)
        return target_class(**init_params)


async def get_service_provider(
    session: Annotated[AsyncSessionWithCommitFlag | None, Depends(get_session)] = None,
) -> ServicesProvider:
    return ServicesProvider(session)
