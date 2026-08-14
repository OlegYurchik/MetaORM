import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from metaorm import RepositoriesContainer
from tests.models import User, UserRepository


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

    async def test_nested_transaction_creates_session(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        assert repositories_container.session is None

        async with repositories_container.nested_transaction() as session:
            assert session is not None
            assert repositories_container.session is session

        assert repositories_container.session is None

    async def test_nested_transaction_reuses_outer_session(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        async with (
            repositories_container.transaction() as outer_session,
            repositories_container.nested_transaction() as inner_session,
        ):
            assert inner_session is outer_session

    async def test_nested_transaction_rollbacks_on_exception(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        repository = repositories_container.get_repository(UserRepository)
        await repository.create_tables()

        with pytest.raises(ValueError):
            async with repositories_container.nested_transaction():
                await repository.create_item(
                    User(name="Alice", email="alice@example.com"),
                )
                raise ValueError("boom")

        count = await repository.get_items_count()
        assert count == 0

    async def test_nested_transaction_in_outer_transaction_rollbacks_only_inner(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        repository = repositories_container.get_repository(UserRepository)
        await repository.create_tables()

        async with repositories_container.transaction():
            await repository.create_item(
                User(name="Bob", email="bob@example.com"),
            )
            with pytest.raises(ValueError):
                async with repositories_container.nested_transaction():
                    await repository.create_item(
                        User(name="Alice", email="alice@example.com"),
                    )
                    raise ValueError("boom")

        count = await repository.get_items_count()
        assert count == 1

        items = [item async for item in repository.get_items()]
        assert items[0].name == "Bob"

    async def test_get_repository_returns_repository_instance(
        self,
        repositories_container: RepositoriesContainer,
    ) -> None:
        repository = repositories_container.get_repository(UserRepository)

        assert isinstance(repository, UserRepository)
