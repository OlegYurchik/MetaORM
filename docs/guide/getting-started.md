# Getting Started

## Installation

MetaORM requires Python **3.12 or higher**.

```bash
pip install "git+https://github.com/OlegYurchik/metaorm.git"
```

## Core concepts

MetaORM is built on three pillars:

1. **BaseTable** — a `SQLModel` subclass that defines your database schema and optional DTO mapping.
2. **BaseRepository** — provides CRUD methods for a specific table.
3. **RepositoriesContainer** — manages the async engine and sessions, enabling multi-repository transactions.

## Minimal example

```python
import asyncio
from metaorm import BaseFilter, BaseRepository, BaseTable, Field, RepositorySettings


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
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    repo = UserRepository(settings=settings)

    await repo.create_tables()

    user = await repo.create_item(UserTable(name="Alice", email="alice@example.com"))
    print(f"Created user {user.id}")

    users = [u async for u in repo.get_items()]
    print(f"Total users: {len(users)}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Constructor modes

### Simple mode

Create a repository directly with `settings`. An internal container is created automatically:

```python
repo = UserRepository(settings=RepositorySettings(dsn="sqlite+aiosqlite:///:memory:"))
```

### Advanced mode

Reuse a `RepositoriesContainer` when you need atomic transactions across multiple repositories:

```python
container = RepositoriesContainer(settings=settings)
user_repo = UserRepository(container=container)
order_repo = OrderRepository(container=container)
```

See [Multi-Repo Transactions](container.md) for details.
