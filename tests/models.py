from pydantic import BaseModel

from metaorm import BaseFilter, BaseRepository, BaseTable, Field, Relationship


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


class UserFilter(BaseFilter):
    name: str | None = None
    email: str | None = None


class UserRepository(BaseRepository, table=UserTable, filter_=UserFilter, dto=User):
    pass


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


class AuthorFilter(BaseFilter):
    name: str | None = None


class BookFilter(BaseFilter):
    title: str | None = None
    author_id: int | None = None


class AuthorRepository(BaseRepository, table=AuthorTable, filter_=AuthorFilter):
    pass


class BookRepository(BaseRepository, table=BookTable, filter_=BookFilter):
    pass
