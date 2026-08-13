from pydantic import BaseModel
from pydantic_filters import BaseFilter
from sqlmodel import Field, Relationship

from metaorm import BaseRepository, BaseTable


class User(BaseModel):
    id: int | None = None
    name: str
    email: str


class UserTable(BaseTable[User], table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)

    @classmethod
    def from_item(cls, item: User) -> "UserTable":
        return cls(id=item.id, name=item.name, email=item.email)

    def to_item(self) -> User:
        return User(id=self.id, name=self.name, email=self.email)


class UserRepository(BaseRepository):
    def get_db_table(self) -> type[UserTable]:
        return UserTable

    def get_dto_type(self) -> type[User]:
        return User


class ProductTable(BaseTable, table=True):
    __tablename__ = "products"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float


class ProductFilter(BaseFilter):
    name: str | None = None
    price: int | None = None


class ProductRepository(BaseRepository):
    def get_db_table(self) -> type[ProductTable]:
        return ProductTable

    def get_filter_type(self) -> type[ProductFilter]:
        return ProductFilter


class AuthorTable(BaseTable, table=True):
    __tablename__ = "authors"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    books: list["BookTable"] = Relationship(back_populates="author")


class BookTable(BaseTable, table=True):
    __tablename__ = "books"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="authors.id")
    author: AuthorTable = Relationship(back_populates="books")


class AuthorRepository(BaseRepository):
    def get_db_table(self) -> type[AuthorTable]:
        return AuthorTable


class BookRepository(BaseRepository):
    def get_db_table(self) -> type[BookTable]:
        return BookTable
