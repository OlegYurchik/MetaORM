import asyncio

from pydantic_filters import BaseFilter, BaseSort, OffsetPagination
from sqlmodel import Field

from metaorm import BaseRepository, BaseTable, DatabaseSettings


class BookTable(BaseTable, table=True):
    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    year: int


class BookFilter(BaseFilter):
    title: str | None = None
    year: int | None = None


class BookRepository(BaseRepository):
    def get_db_table(self) -> type[BookTable]:
        return BookTable

    def get_filter_type(self) -> type[BookFilter]:
        return BookFilter


async def main() -> None:
    settings = DatabaseSettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = BookRepository(settings=settings)

    await repository.create_tables()

    # Seed data
    for index in range(10):
        await repository.create_item(
            BookTable(title=f"Book {index}", year=2020 + index),
        )

    # Filter by year = 2025
    year_filter = BookFilter(year=2025)
    filtered = [item async for item in repository.get_items(filter_=year_filter)]
    print(f"Year = 2025: {[book.title for book in filtered]}")

    # Filter by exact title
    title_filter = BookFilter(title="Book 5")
    filtered = [item async for item in repository.get_items(filter_=title_filter)]
    print(f"Title = 'Book 5': {[book.title for book in filtered]}")

    # Pagination
    pagination = OffsetPagination(offset=2, limit=3)
    page = [item async for item in repository.get_items(pagination=pagination)]
    print(f"Page (offset=2, limit=3): {[book.title for book in page]}")

    # Sorting descending
    sort = BaseSort(sort_by="year", sort_by_order="desc")
    sorted_items = [item async for item in repository.get_items(sort=sort)]
    print(f"Sorted by year desc: {[book.year for book in sorted_items]}")


if __name__ == "__main__":
    asyncio.run(main())
