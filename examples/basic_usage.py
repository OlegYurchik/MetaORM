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


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = UserRepository(settings=settings)

    await repository.create_tables()

    # Create
    user = await repository.create_item(
        UserTable(name="Alice", email="alice@example.com"),
    )
    print(f"Created: {user.name}, {user.email}")

    # Read all
    items = [item async for item in repository.get_items()]
    print(f"All items: {[(item.name, item.email) for item in items]}")

    # Count
    count = await repository.get_items_count()
    print(f"Count: {count}")

    # Update
    updated = [item async for item in repository.update_items(name="Updated")]
    print(f"Updated: {[(item.name, item.email) for item in updated]}")

    # Delete
    await repository.delete_items()
    count = await repository.get_items_count()
    print(f"Count after delete: {count}")


if __name__ == "__main__":
    asyncio.run(main())
