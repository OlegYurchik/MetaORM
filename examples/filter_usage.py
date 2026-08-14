import asyncio

from metaorm import (
    BaseFilter,
    BaseRepository,
    BaseSort,
    BaseTable,
    Field,
    OffsetPagination,
    RepositorySettings,
)


class BookTable(BaseTable, table=True):
    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    year: int


class BookFilter(BaseFilter):
    title: str | None = None
    year: int | None = None


class BookRepository(BaseRepository, table=BookTable, filter_=BookFilter):
    pass


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = BookRepository(settings=settings)

    await repository.create_tables()

    # Seed data
    for index in range(10):
        await repository.create_item(
            BookTable(title=f"Book {index}", year=2020 + index),
        )

    # Get single item by filter
    year_filter = BookFilter(year=2025)
    single = await repository.get_item(filter_=year_filter)
    print(f"Single year = 2025: {single.title if single else None}")

    # Filter by year = 2025
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
