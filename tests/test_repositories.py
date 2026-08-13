import pytest
from pydantic_filters import BaseSort, OffsetPagination
from sqlalchemy.orm import joinedload

from metaorm import AlreadyExistsError, DatabaseSettings, HaveNoSessionError
from tests.models import (
    AuthorRepository,
    AuthorTable,
    BookRepository,
    BookTable,
    ProductFilter,
    ProductRepository,
    ProductTable,
    User,
    UserRepository,
)


class TestBaseRepository:
    async def test_session_raises_error_without_transaction(
        self,
        user_repository: UserRepository,
    ) -> None:
        with pytest.raises(HaveNoSessionError):
            _ = user_repository.session

    async def test_create_item(self, user_repository: UserRepository) -> None:
        user = User(name="Alice", email="alice@example.com")

        created = await user_repository.create_item(user)

        assert created.id is not None
        assert created.name == "Alice"
        assert created.email == "alice@example.com"

    async def test_get_items(self, user_repository: UserRepository) -> None:
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        await user_repository.create_item(user1)
        await user_repository.create_item(user2)

        items = [item async for item in user_repository.get_items()]

        assert len(items) == 2
        assert {item.name for item in items} == {"Alice", "Bob"}

    async def test_get_items_count(self, user_repository: UserRepository) -> None:
        await user_repository.create_item(
            User(name="Alice", email="alice@example.com"),
        )
        await user_repository.create_item(
            User(name="Bob", email="bob@example.com"),
        )

        count = await user_repository.get_items_count()

        assert count == 2

    async def test_update_items(self, user_repository: UserRepository) -> None:
        await user_repository.create_item(
            User(name="Alice", email="alice@example.com"),
        )
        await user_repository.create_item(
            User(name="Bob", email="bob@example.com"),
        )

        updated = [item async for item in user_repository.update_items(name="Updated")]

        assert len(updated) == 2
        assert all(item.name == "Updated" for item in updated)

    async def test_delete_items(self, user_repository: UserRepository) -> None:
        await user_repository.create_item(
            User(name="Alice", email="alice@example.com"),
        )
        await user_repository.create_item(
            User(name="Bob", email="bob@example.com"),
        )

        await user_repository.delete_items()

        count = await user_repository.get_items_count()

        assert count == 0

    async def test_create_item_raises_already_exists_on_duplicate(
        self,
        user_repository: UserRepository,
    ) -> None:
        user = User(name="Alice", email="alice@example.com")
        await user_repository.create_item(user)

        with pytest.raises(AlreadyExistsError):
            await user_repository.create_item(user)

    async def test_transaction_reuses_existing_session(
        self,
        user_repository: UserRepository,
    ) -> None:
        async with user_repository.transaction():
            _ = user_repository.session

    async def test_get_items_with_pagination(
        self,
        user_repository: UserRepository,
    ) -> None:
        for index in range(5):
            await user_repository.create_item(
                User(name=f"User{index}", email=f"user{index}@example.com"),
            )

        pagination = OffsetPagination(offset=1, limit=2)
        items = [
            item async for item in user_repository.get_items(pagination=pagination)
        ]

        assert len(items) == 2

    async def test_get_items_with_sort(
        self,
        user_repository: UserRepository,
    ) -> None:
        await user_repository.create_item(
            User(name="Charlie", email="c@example.com"),
        )
        await user_repository.create_item(
            User(name="Alice", email="a@example.com"),
        )
        await user_repository.create_item(
            User(name="Bob", email="b@example.com"),
        )

        sort = BaseSort(sort_by="name", sort_by_order="asc")
        items = [item async for item in user_repository.get_items(sort=sort)]

        assert [item.name for item in items] == ["Alice", "Bob", "Charlie"]

    async def test_init_with_settings_creates_container(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        product = ProductTable(name="Widget", price=9.99)

        created = await product_repository_settings.create_item(product)

        assert created.id is not None
        assert created.name == "Widget"

    async def test_get_filter_type(self) -> None:
        repository = ProductRepository(settings=DatabaseSettings())

        filter_type = repository.get_filter_type()

        assert filter_type is ProductFilter

    async def test_get_items_with_filter(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        await product_repository_settings.create_item(
            ProductTable(name="Alpha", price=10.0),
        )
        await product_repository_settings.create_item(
            ProductTable(name="Beta", price=20.0),
        )

        items = [
            item
            async for item in product_repository_settings.get_items(
                filter_=ProductFilter(name="Alpha"),
            )
        ]

        assert len(items) == 1
        assert items[0].name == "Alpha"

    async def test_get_items_with_options(
        self,
        author_repository: AuthorRepository,
        book_repository: BookRepository,
    ) -> None:
        author = await author_repository.create_item(AuthorTable(name="Tolkien"))
        await book_repository.create_item(
            BookTable(title="The Hobbit", author_id=author.id),
        )

        books = [
            item
            async for item in book_repository.get_items(
                options=[joinedload(BookTable.author)],
            )
        ]

        assert len(books) == 1
        assert books[0].title == "The Hobbit"
        assert books[0].author.name == "Tolkien"

    async def test_update_items_with_options(
        self,
        author_repository: AuthorRepository,
        book_repository: BookRepository,
    ) -> None:
        from sqlalchemy.orm import raiseload

        author = await author_repository.create_item(AuthorTable(name="Tolkien"))
        await book_repository.create_item(
            BookTable(title="The Hobbit", author_id=author.id),
        )

        updated = [
            item
            async for item in book_repository.update_items(
                title="Updated",
                options=[raiseload(BookTable.author)],
            )
        ]

        assert len(updated) == 1
        assert updated[0].title == "Updated"
