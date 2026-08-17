# Tables & DTOs

## BaseTable

`BaseTable[ItemType]` is a generic `SQLModel` subclass that acts as the database table. It is the bridge between your database and your application code.

### Without DTO mapping

If you don't need a separate data-transfer object, use `BaseTable` directly:

```python
class UserTable(BaseTable, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
```

Repository methods will return `UserTable` instances directly.

### With DTO mapping

When you want repository methods to return a separate Pydantic model instead of the raw table, specify a generic argument and implement `from_item` / `to_item`:

```python
from pydantic import BaseModel
from metaorm import BaseTable, Field


class User(BaseModel):
    id: int | None = None
    name: str
    email: str


class UserTable(BaseTable[User], table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)

    @classmethod
    def from_item(cls, item: User) -> "UserTable":
        return cls(id=item.id, name=item.name, email=item.email)

    def to_item(self) -> User:
        return User(id=self.id, name=self.name, email=self.email)
```

Then pass `dto=User` to the repository:

```python
class UserRepository(BaseRepository, table=UserTable, filter_=UserFilter, dto=User):
    pass
```

`BaseTable` also provides `to_values()` for insert / update operations.

## Introspection helpers

- `get_table_type()` — returns the SQLModel table class.
- `get_filter_type()` — returns the filter class.
- `get_dto_type()` — returns the DTO class or `None`.
