import asyncio

from metaorm import BaseFilter, BaseRepository, BaseTable, Field, RepositorySettings


class ProductTable(BaseTable, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float


class ProductFilter(BaseFilter):
    name: str | None = None


class ProductRepository(BaseRepository, table=ProductTable, filter_=ProductFilter):
    pass


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = ProductRepository(settings=settings)

    await repository.create_tables()

    # Standalone nested transaction: rollback only the inner scope
    try:
        async with repository.nested_transaction():
            await repository.create_item(ProductTable(name="Laptop", price=999.99))
            await repository.create_item(ProductTable(name="Mouse", price=29.99))
            raise ValueError("Simulated error inside nested transaction")
    except ValueError:
        pass

    count = await repository.get_items_count()
    print(f"Items after standalone nested rollback: {count}")  # 0

    # Nested transaction inside an outer transaction
    async with repository.transaction():
        await repository.create_item(ProductTable(name="Keyboard", price=79.99))

        try:
            async with repository.nested_transaction():
                await repository.create_item(
                    ProductTable(name="Monitor", price=299.99),
                )
                raise ValueError("Nested rollback")
        except ValueError:
            pass

        # Monitor is rolled back, Keyboard stays in the outer transaction
        items = [item async for item in repository.get_items()]
        print(f"Items after partial rollback: {len(items)}")  # 1
        print(items[0].name)  # Keyboard

    # Verify committed results
    all_items = [item async for item in repository.get_items()]
    print(f"Final items: {[item.name for item in all_items]}")  # ["Keyboard"]


if __name__ == "__main__":
    asyncio.run(main())
