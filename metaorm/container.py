import contextvars
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .settings import DatabaseSettings

RepositoryType = TypeVar("RepositoryType", bound="BaseRepository")  # noqa: F821


class RepositoriesContainer:
    def __init__(self, settings: DatabaseSettings):
        engine_parameters = {
            "url": settings.dsn,
            "pool_recycle": settings.pool_recycle,
        }
        if not settings.dsn.startswith("sqlite"):
            engine_parameters["pool_timeout"] = settings.pool_timeout
            engine_parameters["pool_size"] = settings.pool_size

        self._engine = create_async_engine(**engine_parameters)
        self._session_context = contextvars.ContextVar(
            "session_context",
            default=None,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session(self) -> AsyncSession | None:
        return self._session_context.get(None)

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        existing_session = self._session_context.get()
        if existing_session is not None:
            yield existing_session
            return

        session_parameters = {
            "bind": self._engine,
            "expire_on_commit": False,
        }
        async with AsyncSession(**session_parameters) as session:
            token = self._session_context.set(session)
            try:
                async with session.begin():
                    yield session
            finally:
                self._session_context.reset(token)

    def get_repository(self, repository_class: type[RepositoryType]) -> RepositoryType:
        return repository_class(container=self)
