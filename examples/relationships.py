import asyncio

from sqlalchemy.orm import joinedload

from metaorm import (
    BaseFilter,
    BaseRepository,
    BaseTable,
    Field,
    Relationship,
    RepositoriesContainer,
    RepositorySettings,
)


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


class BookFilter(BaseFilter):
    title: str | None = None
    author_id: int | None = None


class AuthorFilter(BaseFilter):
    name: str | None = None


class BookRepository(BaseRepository, table=BookTable, filter_=BookFilter):
    pass


class AuthorRepository(BaseRepository, table=AuthorTable, filter_=AuthorFilter):
    pass


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    container = RepositoriesContainer(settings=settings)

    author_repo = AuthorRepository(container=container)
    book_repo = BookRepository(container=container)

    await author_repo.create_tables()
    await book_repo.create_tables()

    # Create author and books
    author = await author_repo.create_item(AuthorTable(name="Tolkien"))
    await book_repo.create_item(BookTable(title="The Hobbit", author_id=author.id))
    await book_repo.create_item(BookTable(title="LOTR", author_id=author.id))

    # Load books with authors using joinedload
    books = [
        item
        async for item in book_repo.get_items(
            options=[joinedload(BookTable.author)],
        )
    ]
    for book in books:
        print(f"Book: {book.title}, Author: {book.author.name}")


if __name__ == "__main__":
    asyncio.run(main())
