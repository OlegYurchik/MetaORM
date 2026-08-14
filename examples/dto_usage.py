import asyncio

from pydantic import BaseModel

from metaorm import BaseFilter, BaseRepository, BaseTable, Field, RepositorySettings


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


async def main() -> None:
    settings = RepositorySettings(dsn="sqlite+aiosqlite:///:memory:")
    repository = UserRepository(settings=settings)

    await repository.create_tables()

    # Create using DTO
    user = await repository.create_item(
        User(name="Alice", email="alice@example.com"),
    )
    print(f"Created DTO: {user.model_dump()}")

    # Read single DTO
    single = await repository.get_item(
        filter_=UserFilter(email="alice@example.com"),
    )
    print(f"Single DTO: {single.model_dump() if single else None}")

    # Read all — returned as DTOs
    items = [item async for item in repository.get_items()]
    print(f"Items as DTOs: {[item.model_dump() for item in items]}")


if __name__ == "__main__":
    asyncio.run(main())
