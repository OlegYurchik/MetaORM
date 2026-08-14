import pytest
from sqlalchemy.orm import joinedload

from metaorm import (
    AlreadyExistsError,
    BaseRepository,
    BaseSort,
    OffsetPagination,
    RepositorySettings,
)
from tests.models import (
    AuthorRepository,
    AuthorTable,
    BookRepository,
    BookTable,
    ProductFilter,
    ProductRepository,
    ProductTable,
    User,
    UserFilter,
    UserRepository,
    UserTable,
)


class TestBaseRepository:
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

    async def test_transaction_scope_allows_crud(
        self,
        user_repository: UserRepository,
    ) -> None:
        async with user_repository.transaction():
            count = await user_repository.get_items_count()
        assert count == 0

    async def test_session_is_none_without_transaction(
        self,
        user_repository: UserRepository,
    ) -> None:
        assert user_repository.session is None

    async def test_session_returns_session_inside_transaction(
        self,
        user_repository: UserRepository,
    ) -> None:
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with user_repository.transaction() as session:
            assert isinstance(user_repository.session, AsyncSession)
            assert user_repository.session is session

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
        product_repository = ProductRepository(settings=RepositorySettings())
        user_repository = UserRepository(settings=RepositorySettings())

        assert product_repository.get_filter_type() is ProductFilter
        assert user_repository.get_filter_type() is UserFilter

    async def test_get_dto_type(self) -> None:
        product_repository = ProductRepository(settings=RepositorySettings())
        user_repository = UserRepository(settings=RepositorySettings())

        assert product_repository.get_dto_type() is None
        assert user_repository.get_dto_type() is User

    async def test_get_item_returns_first_item(
        self,
        user_repository: UserRepository,
    ) -> None:
        await user_repository.create_item(
            User(name="Alice", email="alice@example.com"),
        )
        await user_repository.create_item(
            User(name="Bob", email="bob@example.com"),
        )

        item = await user_repository.get_item()

        assert item is not None
        assert item.name == "Alice"

    async def test_get_item_returns_none_when_empty(
        self,
        user_repository: UserRepository,
    ) -> None:
        item = await user_repository.get_item()

        assert item is None

    async def test_get_item_with_filter(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        await product_repository_settings.create_item(
            ProductTable(name="Alpha", price=10.0),
        )
        await product_repository_settings.create_item(
            ProductTable(name="Beta", price=20.0),
        )

        item = await product_repository_settings.get_item(
            filter_=ProductFilter(name="Beta"),
        )

        assert item is not None
        assert item.name == "Beta"

    async def test_get_item_with_sort(
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
        item = await user_repository.get_item(sort=sort)

        assert item is not None
        assert item.name == "Alice"

    async def test_get_items_count_with_filter(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        await product_repository_settings.create_item(
            ProductTable(name="Alpha", price=10.0),
        )
        await product_repository_settings.create_item(
            ProductTable(name="Beta", price=20.0),
        )

        count = await product_repository_settings.get_items_count(
            filter_=ProductFilter(name="Alpha"),
        )

        assert count == 1

    async def test_delete_items_with_filter(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        await product_repository_settings.create_item(
            ProductTable(name="Alpha", price=10.0),
        )
        await product_repository_settings.create_item(
            ProductTable(name="Beta", price=20.0),
        )

        await product_repository_settings.delete_items(
            filter_=ProductFilter(name="Alpha"),
        )

        count = await product_repository_settings.get_items_count()
        assert count == 1

        remaining = [item async for item in product_repository_settings.get_items()]
        assert remaining[0].name == "Beta"

    async def test_update_items_with_filter(
        self,
        product_repository_settings: ProductRepository,
    ) -> None:
        await product_repository_settings.create_item(
            ProductTable(name="Alpha", price=10.0),
        )
        await product_repository_settings.create_item(
            ProductTable(name="Beta", price=20.0),
        )

        updated = [
            item
            async for item in product_repository_settings.update_items(
                filter_=ProductFilter(name="Alpha"),
                name="Gamma",
            )
        ]

        assert len(updated) == 1
        assert updated[0].name == "Gamma"

        all_items = [item async for item in product_repository_settings.get_items()]
        assert len(all_items) == 2
        names = {item.name for item in all_items}
        assert names == {"Gamma", "Beta"}

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

    async def test_init_raises_without_container_or_settings(self) -> None:
        with pytest.raises(TypeError):
            BaseRepository()

    async def test_repository_without_table_raises(self) -> None:
        with pytest.raises(TypeError):
            class BadRepository(BaseRepository, filter_=UserFilter):
                pass

    async def test_nested_transaction_property_allows_crud(
        self,
        user_repository: UserRepository,
    ) -> None:
        async with user_repository.nested_transaction():
            count = await user_repository.get_items_count()
        assert count == 0

    async def test_nested_transaction_rollbacks_inner_scope(
        self,
        user_repository: UserRepository,
    ) -> None:
        with pytest.raises(ValueError):
            async with user_repository.nested_transaction():
                await user_repository.create_item(
                    User(name="Alice", email="alice@example.com"),
                )
                raise ValueError("boom")

        count = await user_repository.get_items_count()
        assert count == 0

    async def test_nested_transaction_in_outer_transaction_rollbacks_only_inner(
        self,
        user_repository: UserRepository,
    ) -> None:
        async with user_repository.transaction():
            await user_repository.create_item(
                User(name="Bob", email="bob@example.com"),
            )
            with pytest.raises(ValueError):
                async with user_repository.nested_transaction():
                    await user_repository.create_item(
                        User(name="Alice", email="alice@example.com"),
                    )
                    raise ValueError("boom")

        count = await user_repository.get_items_count()
        assert count == 1

        items = [item async for item in user_repository.get_items()]
        assert items[0].name == "Bob"

    async def test_params_via_intermediate_base_class(self) -> None:
        class IntermediateRepository(
            BaseRepository,
            table=UserTable,
            filter_=UserFilter,
            dto=User,
        ):
            pass

        class ConcreteRepository(IntermediateRepository):
            pass

        repository = ConcreteRepository(settings=RepositorySettings())

        assert repository.get_filter_type() is UserFilter
        assert repository.get_dto_type() is User
