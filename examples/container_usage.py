import asyncio

from sqlmodel import Field

from metaorm import BaseRepository, BaseTable, DatabaseSettings, RepositoriesContainer


class UserTable(BaseTable, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str


class OrderTable(BaseTable, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    total: float


class UserRepository(BaseRepository):
    def get_db_table(self) -> type[UserTable]:
        return UserTable


class OrderRepository(BaseRepository):
    def get_db_table(self) -> type[OrderTable]:
        return OrderTable


async def main() -> None:
    settings = DatabaseSettings(dsn="sqlite+aiosqlite:///:memory:")
    container = RepositoriesContainer(settings=settings)

    user_repo = container.get_repository(UserRepository)
    order_repo = container.get_repository(OrderRepository)

    await user_repo.create_tables()
    await order_repo.create_tables()

    # Atomic transaction across two repositories
    async with container.transaction():
        user = await user_repo.create_item(UserTable(name="Alice"))
        await order_repo.create_item(OrderTable(user_id=user.id, total=100.00))
        await order_repo.create_item(OrderTable(user_id=user.id, total=250.50))

    # Verify results
    users = [item async for item in user_repo.get_items()]
    orders = [item async for item in order_repo.get_items()]

    print(f"Users: {[user.name for user in users]}")
    print(f"Orders: {[(order.user_id, order.total) for order in orders]}")
    print(f"Orders count: {len(orders)}")


if __name__ == "__main__":
    asyncio.run(main())
