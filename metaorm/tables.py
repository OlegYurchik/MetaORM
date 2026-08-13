from typing import Any, Self

from pydantic import BaseModel
from sqlmodel import SQLModel


class BaseTable[ItemType: BaseModel](SQLModel):
    @classmethod
    def from_item(cls, item: ItemType) -> Self:
        raise NotImplementedError

    def to_item(self) -> ItemType:
        raise NotImplementedError

    def to_values(self) -> dict[str, Any]:
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
