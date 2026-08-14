import pytest

from metaorm import BaseTable, Field
from tests.models import User


class TestBaseTable:
    def test_to_values_returns_column_data(self) -> None:
        from tests.models import UserTable

        user_table = UserTable(id=1, name="Alice", email="alice@example.com")

        values = user_table.to_values()

        assert values == {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
        }

    def test_from_item_not_implemented_in_base_class(self) -> None:
        class DummyFromItemTable(BaseTable[User], table=True):
            __tablename__ = "dummy_from_item"
            id: int | None = Field(default=None, primary_key=True)

        with pytest.raises(NotImplementedError):
            DummyFromItemTable.from_item(
                User(name="Alice", email="alice@example.com"),
            )

    def test_to_item_not_implemented_in_base_class(self) -> None:
        class DummyToItemTable(BaseTable[User], table=True):
            __tablename__ = "dummy_to_item"
            id: int | None = Field(default=None, primary_key=True)

        dummy = DummyToItemTable(id=1, name="Alice", email="alice@example.com")

        with pytest.raises(NotImplementedError):
            dummy.to_item()
