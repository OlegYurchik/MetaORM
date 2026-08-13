from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from pydantic import BaseModel
from pydantic_filters import BaseFilter, BasePagination, BaseSort
from pydantic_filters.drivers.sqlalchemy import append_to_statement
from pydantic_filters.filter._fields import FilterFieldInfo
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import delete, insert, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from .container import RepositoriesContainer
from .exceptions import AlreadyExistsError, DatabaseException, HaveNoSessionError
from .settings import DatabaseSettings
from .tables import BaseTable


class BaseRepository:
    def __init__(
        self,
        settings: DatabaseSettings | None = None,
        container: RepositoriesContainer | None = None,
    ):
        if container is not None:
            self._container = container
        elif settings is not None:
            self._container = RepositoriesContainer(settings=settings)
        else:
            raise TypeError("Either 'container' or 'settings' must be provided")

    def get_db_table(self) -> type[BaseTable]:
        raise NotImplementedError

    def get_dto_type(self) -> type[BaseModel] | None:
        return None

    def get_filter_type(self) -> type[BaseFilter] | None:
        return None

    @property
    def session(self) -> AsyncSession:
        session = self._container.session
        if session is None:
            raise HaveNoSessionError()
        return session

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        existing_session = self._container.session
        if existing_session is not None:
            yield
            return

        async with self._container.transaction():
            yield

    async def create_tables(self) -> None:
        table = self.get_db_table()
        async with self._container.engine.begin() as connection:
            await connection.run_sync(
                table.metadata.create_all,
                tables=[table.__table__],
            )

    async def get_items_count(
        self,
        filter_: BaseFilter | None = None,
    ) -> int:
        if filter_ is not None:
            self._ensure_filter_fields(type(filter_))
        table = self.get_db_table()
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

    async def get_items(
        self,
        filter_: BaseFilter | None = None,
        pagination: BasePagination | None = None,
        sort: BaseSort | None = None,
        options: Sequence[Any] | None = None,
    ) -> AsyncGenerator[BaseModel]:
        if filter_ is not None:
            self._ensure_filter_fields(type(filter_))
        table = self.get_db_table()
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
            result = await self.session.execute(statement)
            result = result.yield_per(100)
            for db_item in result.scalars():
                yield self._convert_from_table(db_item)

    async def create_item(self, item: BaseModel) -> BaseModel:
        table = self.get_db_table()
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
        if filter_ is not None:
            self._ensure_filter_fields(type(filter_))
        table = self.get_db_table()
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
        if filter_ is not None:
            self._ensure_filter_fields(type(filter_))
        table = self.get_db_table()
        statement = delete(table)
        statement = append_to_statement(
            statement=statement,
            model=table,
            filter_=filter_,
        )

        async with self.transaction():
            await self.session.exec(statement)

    def _convert_to_table(self, item: BaseModel) -> BaseModel:
        table = self.get_db_table()
        if isinstance(item, table):
            return item
        return table.from_item(item=item)

    def _convert_from_table(self, table: BaseTable) -> BaseModel:
        dto_type = self.get_dto_type()
        if dto_type is None:
            return table
        return table.to_item()

    def _ensure_filter_fields(self, filter_class: type[BaseFilter]) -> None:
        """Workaround for pydantic-filters not registering filter_fields with pydantic v2."""
        if getattr(filter_class, "filter_fields", None):
            return

        filter_fields: dict[str, FilterFieldInfo] = {}
        for field_name, field_info in filter_class.model_fields.items():
            if field_info.annotation is None:
                continue
            annotation = field_info.annotation
            # unwrap Optional[X] -> X
            origin = getattr(annotation, "__origin__", None)
            if origin is type | None:
                args = getattr(annotation, "__args__", ())
                if args and args[0] is not type(None):
                    annotation = args[0]

            is_sequence = hasattr(
                annotation, "__origin__"
            ) and annotation.__origin__ in (list, set)
            filter_fields[field_name] = FilterFieldInfo(
                target=field_name,
                type_="eq",
                is_sequence=is_sequence,
            )
        filter_class.filter_fields = filter_fields
