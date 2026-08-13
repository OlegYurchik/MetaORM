# MetaORM

Async repository layer over [SQLModel](https://sqlmodel.tiangolo.com). Provides a minimal, explicit pattern for database access with optional DTO mapping, automatic transaction management via `contextvars`, and built-in filter / pagination / sort support via `pydantic-filters`.

## Install

```bash
pip install "git+https://github.com/OlegYurchik/metaorm.git"
```

Requires Python `>=3.12`.

> **Note:** The package is installed directly from GitHub because `metaorm` depends on a patched version of `pydantic-filters` (from `so-saf/pydantic-filters`) that is not yet available on PyPI.

## Quick start

The simplest mode works with SQLModel tables directly — no DTOs, no generics, no magic:

```python
from sqlmodel import Field
from metaorm import BaseRepository, BaseTable, DatabaseSettings


class UserTable(BaseTable, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)


class UserRepository(BaseRepository):
    def get_db_table(self) -> type[UserTable]:
        return UserTable


async def main():
    repo = UserRepository(
        settings=DatabaseSettings(dsn="sqlite+aiosqlite:///:memory:"),
    )
    await repo.create_tables()

    user = await repo.create_item(
        UserTable(name="Alice", email="alice@example.com"),
    )
    print(user.id, user.name)

    all_users = [u async for u in repo.get_items()]
    print(len(all_users))
```

## DTO mapping

When you want repository methods to return separate Pydantic models instead of table instances, override `get_dto_type()` and implement `from_item` / `to_item` on the table:

```python
from pydantic import BaseModel
from sqlmodel import Field
from metaorm import BaseRepository, BaseTable, DatabaseSettings


class User(BaseModel):
    id: int | None = None
    name: str


class UserTable(BaseTable[User], table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str

    @classmethod
    def from_item(cls, item: User) -> "UserTable":
        return cls(id=item.id, name=item.name)

    def to_item(self) -> User:
        return User(id=self.id, name=self.name)


class UserRepository(BaseRepository):
    def get_db_table(self) -> type[UserTable]:
        return UserTable

    def get_dto_type(self) -> type[User]:
        return User


async def main():
    repo = UserRepository(
        settings=DatabaseSettings(dsn="sqlite+aiosqlite:///:memory:"),
    )
    await repo.create_tables()

    user = await repo.create_item(User(name="Alice"))
    # user is a User DTO, not UserTable
    print(user.model_dump())
```

## Filters, pagination and sorting

`pydantic-filters` provides `BaseFilter`, `BasePagination` and `BaseSort`. Pass them to `get_items`:

```python
from pydantic_filters import BaseFilter, BaseSort, OffsetPagination

class BookFilter(BaseFilter):
    title: str | None = None
    year: int | None = None


class BookRepository(BaseRepository):
    def get_db_table(self) -> type[BookTable]:
        return BookTable

    def get_filter_type(self) -> type[BookFilter]:
        return BookFilter


# Exact match filter
filtered = [
    item
    async for item in repo.get_items(filter_=BookFilter(year=2025))
]

# Pagination
page = [
    item
    async for item in repo.get_items(
        pagination=OffsetPagination(offset=10, limit=20),
    )
]

# Sorting
sorted_items = [
    item
    async for item in repo.get_items(
        sort=BaseSort(sort_by="year", sort_by_order="desc"),
    )
]
```

## Explicit transactions

Each repository method already runs inside a transaction automatically. If you need an explicit scope (e.g. to read `repository.session`), use `repository.transaction()`:

```python
async with repo.transaction():
    user = await repo.create_item(UserTable(name="Alice"))
    # nested transaction reuses the same session
    async with repo.transaction():
        items = [item async for item in repo.get_items()]
```

## Atomic transactions across multiple repositories

Use `RepositoriesContainer` when you need a single atomic transaction spanning multiple repositories:

```python
from metaorm import RepositoriesContainer

container = RepositoriesContainer(settings=settings)
user_repo = container.get_repository(UserRepository)
order_repo = container.get_repository(OrderRepository)

async with container.transaction():
    user = await user_repo.create_item(UserTable(name="Alice"))
    await order_repo.create_item(OrderTable(user_id=user.id, total=100))
```

`container.transaction()` stores the session in a `contextvars.ContextVar`. All repository operations within the `async with` block automatically reuse that session. Nested `container.transaction()` calls yield the same session.

## Eager loading

`get_items()` and `update_items()` accept an optional `options` parameter for SQLAlchemy eager loading strategies:

```python
from sqlalchemy.orm import joinedload

books = [
    item
    async for item in book_repo.get_items(
        options=[joinedload(BookTable.author)],
    )
]
```

## Exceptions

```
DatabaseException
├── NotFoundError
├── HaveNoSessionError
└── AlreadyExistsError
```

All repository methods raise `DatabaseException` subclasses or SQLAlchemy errors.

## License

MIT
