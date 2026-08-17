import asyncio

from metaorm import (
    BaseFilter,
    BaseRepository,
    BaseTable,
    Field,
    RepositoriesContainer,
    RepositorySettings,
)


class UserTable(BaseTable, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str


class OrderTable(BaseTable, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    total: float


class UserFilter(BaseFilter):
    name: str | None = None


class OrderFilter(BaseFilter):
    user_id: int | None = None


class UserRepository(BaseRepository, table=UserTable, filter_=UserFilter):
    pass


class OrderRepository(BaseRepository, table=OrderTable, filter_=OrderFilter):
    pass


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    container = RepositoriesContainer(settings=settings)

    user_repo = container.get_repository(UserRepository)
    order_repo = container.get_repository(OrderRepository)

    # Create tables for all repositories at once via the container
    await container.create_tables(UserRepository, OrderRepository)

    # Or create tables individually per repository
    # await user_repo.create_tables()
    # await order_repo.create_tables()

    # Atomic transaction across two repositories
    async with container.transaction():
        user = await user_repo.create_item(UserTable(name="Alice"))
        await order_repo.create_item(OrderTable(user_id=user.id, total=100.00))
        await order_repo.create_item(OrderTable(user_id=user.id, total=250.50))

    # Nested transaction inside outer transaction (savepoint)
    async with container.transaction():
        user = await user_repo.create_item(UserTable(name="Bob"))
        try:
            async with container.nested_transaction():
                await order_repo.create_item(
                    OrderTable(user_id=user.id, total=999.99),
                )
                raise ValueError("Rollback nested order")
        except ValueError:
            pass
        # Bob stays, the order is rolled back

    # Verify results
    users = [item async for item in user_repo.get_items()]
    orders = [item async for item in order_repo.get_items()]

    print(f"Users: {[user.name for user in users]}")
    print(f"Orders: {[(order.user_id, order.total) for order in orders]}")
    print(f"Orders count: {len(orders)}")

    # Get single user by name
    single_user = await user_repo.get_item(filter_=UserFilter(name="Alice"))
    print(f"Single user: {single_user.name if single_user else None}")


if __name__ == "__main__":
    asyncio.run(main())
