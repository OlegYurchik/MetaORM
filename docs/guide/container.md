# Multi-Repo Transactions

Use `RepositoriesContainer` when you need a single atomic transaction spanning multiple repositories.

## Creating a container

```python
from metaorm import RepositoriesContainer, RepositorySettings

settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
container = RepositoriesContainer(settings=settings)
```

## Getting repositories

```python
user_repo = container.get_repository(UserRepository)
order_repo = container.get_repository(OrderRepository)
```

## Atomic transaction across repositories

```python
async with container.transaction():
    user = await user_repo.create_item(UserTable(name="Alice"))
    await order_repo.create_item(OrderTable(user_id=user.id, total=100))
```

`container.transaction()` stores the session in a `contextvars.ContextVar`. All repository operations within the `async with` block automatically reuse that session. Nested `transaction()` calls yield the same session.

## Creating tables via container

You can also create tables for multiple repositories at once:

```python
await container.create_tables(UserRepository, OrderRepository)
```

## Nested transactions (savepoints)

For partial rollback inside a shared transaction use `container.nested_transaction()` (or `repository.nested_transaction()`). It creates a SQLAlchemy savepoint: an error inside the block rolls back only the savepoint, leaving the outer transaction open for further operations or commit.

```python
async with container.transaction():
    user = await user_repo.create_item(UserTable(name="Bob"))
    try:
        async with container.nested_transaction():
            await order_repo.create_item(OrderTable(user_id=user.id, total=999.99))
            raise ValueError("Rollback nested order")
    except ValueError:
        pass
    # Bob stays, the order is rolled back
```
