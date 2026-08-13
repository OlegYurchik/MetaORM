from sqlalchemy.ext.asyncio import AsyncEngine

from metaorm import RepositoriesContainer
from tests.models import UserRepository


class TestRepositoriesContainer:
    async def test_engine_property_returns_async_engine(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        assert isinstance(repositories_container.engine, AsyncEngine)

    async def test_session_is_none_without_transaction(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        assert repositories_container.session is None

    async def test_transaction_creates_session(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        assert repositories_container.session is None

        async with repositories_container.transaction() as session:
            assert session is not None
            assert repositories_container.session is session

        assert repositories_container.session is None

    async def test_nested_transaction_yields_same_session(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        async with (
            repositories_container.transaction() as outer_session,
            repositories_container.transaction() as inner_session,
        ):
            assert inner_session is outer_session

    async def test_get_repository_returns_repository_instance(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        repository = repositories_container.get_repository(UserRepository)

        assert isinstance(repository, UserRepository)
