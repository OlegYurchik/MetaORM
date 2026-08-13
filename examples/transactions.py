import asyncio

from sqlmodel import Field

from metaorm import BaseRepository, BaseTable, DatabaseSettings


class ProductTable(BaseTable, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float


class ProductRepository(BaseRepository):
    def get_db_table(self) -> type[ProductTable]:
        return ProductTable


async def main() -> None:
    settings = DatabaseSettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = ProductRepository(settings=settings)

    await repository.create_tables()

    # Explicit transaction via repository
    async with repository.transaction():
        product1 = await repository.create_item(
            ProductTable(name="Laptop", price=999.99),
        )
        product2 = await repository.create_item(
            ProductTable(name="Mouse", price=29.99),
        )
        print(f"Created in transaction: {product1.name}, {product2.name}")

    # Nested transaction reuses existing session
    async with repository.transaction(), repository.transaction():
        items = [item async for item in repository.get_items()]
        print(f"Items in nested transaction: {len(items)}")


if __name__ == "__main__":
    asyncio.run(main())
