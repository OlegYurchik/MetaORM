# Eager Loading

MetaORM supports SQLAlchemy eager loading strategies via the `options` parameter in `get_items()` and `update_items()`.

## joinedload

Load related objects in the same query using a SQL JOIN:

```python
from sqlalchemy.orm import joinedload

books = [
    item
    async for item in book_repo.get_items(
        options=[joinedload(BookTable.author)],
    )
]
for book in books:
    print(f"Book: {book.title}, Author: {book.author.name}")
```

## selectinload

For collections (one-to-many), `selectinload` is often more efficient:

```python
from sqlalchemy.orm import selectinload

authors = [
    item
    async for item in author_repo.get_items(
        options=[selectinload(AuthorTable.books)],
    )
]
```

## Defining relationships

Relationships are defined with SQLModel's `Relationship`:

```python
from metaorm import BaseTable, Field, Relationship


class AuthorTable(BaseTable, table=True):
    __tablename__ = "authors"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    books: list["BookTable"] = Relationship(back_populates="author")


class BookTable(BaseTable, table=True):
    __tablename__ = "books"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="authors.id")
    author: AuthorTable = Relationship(back_populates="books")
```

Both `Field` and `Relationship` are re-exported from `metaorm` for convenience.
