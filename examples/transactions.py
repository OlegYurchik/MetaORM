import asyncio

from metaorm import BaseFilter, BaseRepository, BaseTable, Field, RepositorySettings


class ProductTable(BaseTable, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float


class ProductFilter(BaseFilter):
    name: str | None = None
    price: int | None = None


class ProductRepository(BaseRepository, table=ProductTable, filter_=ProductFilter):
    pass


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
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

    # Reusing an existing session (no new savepoint)
    async with repository.transaction(), repository.transaction():
        items = [item async for item in repository.get_items()]
        print(f"Items in reused session: {len(items)}")

    # True nested transaction (savepoint) via repository
    try:
        async with repository.nested_transaction():
            await repository.create_item(
                ProductTable(name="Keyboard", price=79.99),
            )
            raise ValueError("Rollback nested")
    except ValueError:
        pass

    count = await repository.get_items_count()
    print(f"Items after nested rollback: {count}")  # 2

    # Read single item inside a transaction
    async with repository.transaction():
        item = await repository.get_item(filter_=ProductFilter(name="Laptop"))
        print(f"Single in transaction: {item.name if item else None}")


if __name__ == "__main__":
    asyncio.run(main())
