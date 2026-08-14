from collections.abc import AsyncGenerator, Sequence
from typing import Any

from pydantic import BaseModel
from pydantic_filters import BaseFilter, BasePagination, BaseSort
from pydantic_filters.drivers.sqlalchemy import append_to_statement
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import delete, insert, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from .container import RepositoriesContainer
from .exceptions import AlreadyExistsError, DatabaseException
from .settings import RepositorySettings
from .tables import BaseTable


class BaseRepository:
    def __init_subclass__(
        cls,
        table: type[BaseTable] | None = None,
        filter_: type[BaseFilter] | None = None,
        dto: type[BaseModel] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)

        if (table := table or getattr(cls, "_table_type", None)) is None:
            raise TypeError(
                f"{cls.__name__} must specify 'table' keyword argument",
            )
        if (filter_ := filter_ or getattr(cls, "_filter_type", None)) is None:
            raise TypeError(
                f"{cls.__name__} must specify 'filter_' keyword argument",
            )

        cls._table_type = table
        cls._filter_type = filter_
        cls._dto_type = dto or getattr(cls, "_dto_type", None)

    def __init__(
        self,
        settings: RepositorySettings | None = None,
        container: RepositoriesContainer | None = None,
    ):
        if container is not None:
            self._container = container
        elif settings is not None:
            self._container = RepositoriesContainer(settings=settings)
        else:
            raise TypeError("Either 'container' or 'settings' must be provided")

    async def get_items_count(
        self,
        filter_: BaseFilter | None = None,
    ) -> int:
        table = self.get_table_type()
        statement = select(func.count()).select_from(table)
        statement = append_to_statement(
            statement=statement,
            model=table,
            filter_=filter_,
        )

        async with self.transaction():
            result = await self.session.exec(statement)
            items_count = result.first()

        return items_count

    async def get_item(
        self,
        filter_: BaseFilter | None = None,
        sort: BaseSort | None = None,
    ) -> BaseModel | None:
        async for item in self.get_items(filter_=filter_, sort=sort):
            return item

    async def get_items(
        self,
        filter_: BaseFilter | None = None,
        pagination: BasePagination | None = None,
        sort: BaseSort | None = None,
        options: Sequence[Any] | None = None,
    ) -> AsyncGenerator[BaseModel]:
        table = self.get_table_type()
        statement = select(table)
        statement = append_to_statement(
            statement=statement,
            model=table,
            filter_=filter_,
            pagination=pagination,
            sort=sort,
        )
        if options:
            statement = statement.options(*options)

        async with self.transaction():
            result = await self.session.exec(statement)
            result = result.yield_per(100)
            for db_item in result:
                yield self._convert_from_table(db_item)

    async def create_item(self, item: BaseModel) -> BaseModel:
        table = self.get_table_type()
        values = self._convert_to_table(item).to_values()
        statement = insert(table).values(values).returning(table)

        async with self.transaction():
            try:
                result = await self.session.exec(statement)
            except IntegrityError as error:
                error_message = str(error.orig).lower()
                if "unique" in error_message or "duplicate" in error_message:
                    raise AlreadyExistsError(
                        f"Record for model '{table.__name__}' already exists",
                    ) from error
                raise DatabaseException(
                    f"Integrity error for model '{table.__name__}'",
                ) from error
            db_item = result.scalar_one()

        return self._convert_from_table(db_item)

    async def update_items(
        self,
        filter_: BaseFilter | None = None,
        options: Sequence[Any] | None = None,
        **values,
    ) -> AsyncGenerator[BaseModel]:
        table = self.get_table_type()
        statement = update(table)
        statement = append_to_statement(
            statement=statement,
            model=table,
            filter_=filter_,
        )
        statement = statement.values(**values).returning(table)
        if options:
            statement = statement.options(*options)

        async with self.transaction():
            result = await self.session.exec(statement)
            result = result.yield_per(100)
            for db_item in result.scalars():
                yield self._convert_from_table(db_item)

    async def delete_items(
        self,
        filter_: BaseFilter | None = None,
    ) -> None:
        table = self.get_table_type()
        statement = delete(table)
        statement = append_to_statement(
            statement=statement,
            model=table,
            filter_=filter_,
        )

        async with self.transaction():
            await self.session.exec(statement)

    @property
    def session(self) -> AsyncSession | None:
        return self._container.session

    @property
    def transaction(self):
        return self._container.transaction

    @property
    def nested_transaction(self):
        return self._container.nested_transaction

    async def create_tables(self) -> None:
        table = self.get_table_type()
        async with self._container.engine.begin() as connection:
            await connection.run_sync(
                table.metadata.create_all,
                tables=[table.__table__],
            )

    def _convert_to_table(self, item: BaseModel) -> BaseModel:
        table = self.get_table_type()
        if isinstance(item, table):
            return item
        return table.from_item(item=item)

    def _convert_from_table(self, table: BaseTable) -> BaseModel:
        if self.get_dto_type() is None:
            return table
        return table.to_item()

    @classmethod
    def get_table_type(cls) -> type[BaseTable] | None:
        return cls._table_type

    @classmethod
    def get_filter_type(cls) -> type[BaseFilter] | None:
        return cls._filter_type

    @classmethod
    def get_dto_type(cls) -> type[BaseModel] | None:
        return cls._dto_type
