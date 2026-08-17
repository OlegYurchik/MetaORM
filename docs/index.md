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

!!! note
    The package is installed directly from GitHub because `metaorm` depends on a patched version of `pydantic-filters` that is not yet available on PyPI.

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

## Next steps

- Read the [User Guide](guide/getting-started.md) for detailed explanations.
- Browse the [API Reference](api.md) for auto-generated docs.
- Explore [Examples](examples.md) for common patterns.
