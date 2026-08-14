from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from metaorm import RepositoriesContainer, RepositorySettings

from .models import (
    AuthorRepository,
    BookRepository,
    ProductRepository,
    UserRepository,
)


@pytest.fixture
def database_settings() -> RepositorySettings:
    return RepositorySettings(
        dsn="sqlite+aiosqlite:///:memory:",
        pool_size=1,
        pool_recycle=60,
        pool_timeout=60,
    )


@pytest_asyncio.fixture
async def repositories_container(
    database_settings: RepositorySettings,
) -> AsyncGenerator[RepositoriesContainer, None]:
    container = RepositoriesContainer(settings=database_settings)
    yield container
    await container.engine.dispose()


@pytest_asyncio.fixture
async def user_repository(
    repositories_container: RepositoriesContainer,
) -> AsyncGenerator[UserRepository, None]:
    repository = repositories_container.get_repository(UserRepository)
    await repository.create_tables()
    yield repository


@pytest_asyncio.fixture
async def product_repository_settings(
    database_settings: RepositorySettings,
) -> AsyncGenerator[ProductRepository, None]:
    repository = ProductRepository(settings=database_settings)
    await repository.create_tables()
    yield repository


@pytest_asyncio.fixture
async def book_repository(
    repositories_container: RepositoriesContainer,
) -> AsyncGenerator[BookRepository, None]:
    repository = repositories_container.get_repository(BookRepository)
    await repository.create_tables()
    yield repository


@pytest_asyncio.fixture
async def author_repository(
    repositories_container: RepositoriesContainer,
) -> AsyncGenerator[AuthorRepository, None]:
    repository = repositories_container.get_repository(AuthorRepository)
    await repository.create_tables()
    yield repository
