# MetaORM

Async repository layer over [SQLModel](https://sqlmodel.tiangolo.com). Define a table, a repository with keyword arguments, and you have a complete async CRUD layer.

- **Minimal API** — `create_item`, `get_items`, `update_items`, `delete_items`. That's it.
- **Built-in DTO mapping** — return table instances directly or map to separate Pydantic models.
- **Intuitive transactions** — every CRUD call runs in a transaction; explicit `transaction()` context manager for custom scopes.
- **Nested transactions (savepoints)** — `nested_transaction()` allows partial rollback inside a shared transaction.
- **Multi-repo atomic transactions** — `RepositoriesContainer` lets several repositories share one atomic transaction.
- **Filters, pagination, sorting** — powered by `pydantic-filters`.
- **Eager loading** — pass SQLAlchemy `joinedload` / `selectinload` via `options`.

## Install

```bash
pip install "git+https://github.com/OlegYurchik/metaorm.git"
```

Requires Python `>=3.12`.

> **Note:** The package is installed directly from GitHub because `metaorm` depends on a patched version of `pydantic-filters` (from `so-saf/pydantic-filters`) that is not yet available on PyPI.

## Quick start

```python
from metaorm import BaseFilter, BaseRepository, BaseTable, RepositorySettings, Field


class UserTable(BaseTable, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)


class UserFilter(BaseFilter):
    name: str | None = None
    email: str | None = None


class UserRepository(BaseRepository, table=UserTable, filter_=UserFilter):
    pass


async def main():
    repo = UserRepository(
        settings=RepositorySettings(dsn="sqlite+aiosqlite:///:memory:"),
    )
    await repo.create_tables()

    user = await repo.create_item(UserTable(name="Alice", email="alice@example.com"))
    print(user.id, user.name)

    all_users = [u async for u in repo.get_items()]
    print(len(all_users))
```

## Repository API

Subclass `BaseRepository` with keyword arguments `table`, `filter_`, and optionally `dto`:

```python
class MyRepository(BaseRepository, table=MyTable, filter_=MyFilter):
    pass  # returns table instances directly


class MyRepositoryWithDto(BaseRepository, table=MyTable, filter_=MyFilter, dto=MyDto):
    pass  # maps rows to MyDto
```

Keyword arguments are checked at class-definition time. If you forget `table` or `filter_`, Python raises `TypeError` immediately. `table=` must still be provided on the first subclass in the hierarchy.

### Constructor

```python
# Simple — container is created internally
repo = MyRepository(settings=RepositorySettings(dsn="..."))

# Advanced — share a container for atomic multi-repo transactions
container = RepositoriesContainer(settings=settings)
repo = MyRepository(container=container)
```

### Methods

| Method | Signature | Description |
|---|---|---|
| `create_tables` | `async () -> None` | Creates the table in the database. |
| `create_item` | `async (item) -> Any` | Inserts one row. Returns the table instance or DTO when `dto=` is set. |
| `get_items` | `async (filter_=None, pagination=None, sort=None, options=None) -> AsyncGenerator[Any]` | Streams matching rows. `options` accepts SQLAlchemy eager-loading strategies such as `joinedload`. |
| `get_items_count` | `async (filter_=None) -> int` | Returns the number of matching rows. |
| `update_items` | `async (filter_=None, options=None, **values) -> AsyncGenerator[Any]` | Updates matching rows and yields the updated instances. |
| `delete_items` | `async (filter_=None) -> None` | Deletes matching rows. |
| `transaction` | `async contextmanager () -> AsyncSession` | Explicit transaction scope. Automatically used by all CRUD methods. Reuses an existing session when nested. |
| `nested_transaction` | `async contextmanager () -> AsyncSession` | Creates a savepoint (nested transaction). Rolls back only the inner scope on error while leaving the outer transaction intact. |

### Multi-repository transactions

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

`container.transaction()` stores the session in a `contextvars.ContextVar`. All repository operations within the `async with` block automatically reuse that session. Nested `transaction()` calls yield the same session.

For partial rollback inside a shared transaction use `container.nested_transaction()` (or `repository.nested_transaction()`). It creates a SQLAlchemy savepoint: an error inside the block rolls back only the savepoint, leaving the outer transaction open for further operations or commit.

## More examples

See [`examples/`](examples/) for detailed usage patterns:

- [`basic_usage.py`](examples/basic_usage.py) — CRUD with tables directly
- [`dto_usage.py`](examples/dto_usage.py) — DTO mapping via `dto=` keyword
- [`transactions.py`](examples/transactions.py) — Explicit transaction management
- [`nested_transactions.py`](examples/nested_transactions.py) — Savepoints and partial rollback
- [`filter_usage.py`](examples/filter_usage.py) — Query filters, pagination and sorting
- [`relationships.py`](examples/relationships.py) — Eager loading with `joinedload`
- [`container_usage.py`](examples/container_usage.py) — Multi-repository atomic transactions

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
