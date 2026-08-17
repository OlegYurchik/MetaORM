# Repositories

Subclass `BaseRepository` with keyword arguments `table`, `filter_`, and optionally `dto`:

```python
class MyRepository(BaseRepository, table=MyTable, filter_=MyFilter):
    pass  # returns table instances directly


class MyRepositoryWithDto(BaseRepository, table=MyTable, filter_=MyFilter, dto=MyDto):
    pass  # maps rows to MyDto
```

Keyword arguments are checked at class-definition time. If you forget `table` or `filter_`, Python raises `TypeError` immediately. `table=` must still be provided on the first subclass in the hierarchy.

## Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_tables` | `async () -> None` | Creates the table in the database. |
| `create_item` | `async (item) -> Any` | Inserts one row. Returns the table instance or DTO when `dto=` is set. |
| `get_items` | `async (filter_=None, pagination=None, sort=None, options=None) -> AsyncGenerator[Any]` | Streams matching rows. `options` accepts SQLAlchemy eager-loading strategies such as `joinedload`. |
| `get_items_count` | `async (filter_=None) -> int` | Returns the number of matching rows. |
| `update_items` | `async (filter_=None, options=None, **values) -> AsyncGenerator[Any]` | Updates matching rows and yields the updated instances. |
| `delete_items` | `async (filter_=None) -> None` | Deletes matching rows. |
| `transaction` | `async contextmanager () -> AsyncSession` | Explicit transaction scope. Automatically used by all CRUD methods. Reuses an existing session when nested. |
| `nested_transaction` | `async contextmanager () -> AsyncSession` | Creates a savepoint (nested transaction). Rolls back only the inner scope on error while leaving the outer transaction intact. |

## Single item retrieval

`get_item(filter_=..., sort=...)` returns the first matching record (or `None` if no records match). It delegates to `get_items` under the hood:

```python
user = await user_repository.get_item(filter_=UserFilter(email="alice@example.com"))
if user is not None:
    print(user.name)
```

## Eager loading (options)

`get_items()` and `update_items()` accept an optional `options` parameter for SQLAlchemy eager loading strategies such as `joinedload` or `selectinload`:

```python
from sqlalchemy.orm import joinedload

books = [
    item
    async for item in book_repository.get_items(
        options=[joinedload(BookTable.author)],
    )
]
```
