# MetaORM

Async repository layer over SQLModel. Provides a simple pattern for database access with optional DTO mapping, automatic transaction management via contextvars, and built-in filter/pagination/sort support via `pydantic-filters`.

## Project Structure

```
metaorm/
    __init__.py          # Public API exports
    repositories.py      # BaseRepository
    tables.py            # BaseTable
    container.py         # RepositoriesContainer (session/transaction manager)
    settings.py          # RepositorySettings (Pydantic model)
    exceptions.py        # Domain exceptions
examples/                # Usage examples
    basic_usage.py       # Simple CRUD with tables directly
    dto_usage.py         # DTO mapping via dto= keyword
    transactions.py      # Explicit transaction management
    nested_transactions.py # Savepoints and partial rollback
    filter_usage.py      # Query filters, pagination and sorting
    relationships.py     # Eager loading with joinedload/selectinload
    container_usage.py   # Multi-repository atomic transactions
docs/                    # MkDocs documentation
    index.md             # Home page
    api.md               # API Reference (auto-generated)
    examples.md          # Embedded examples
    guide/               # User guide pages
.github/workflows/
    docs.yml             # GitHub Pages deploy workflow
tests/                   # Pytest suite
    conftest.py          # Fixtures
    models.py            # Test models (User, UserTable, UserRepository)
    test_*.py            # Unit tests
```

## Core Concepts

### BaseTable

`BaseTable[ItemType]` is a generic `SQLModel` subclass that acts as the database table. It requires implementing `from_item` and `to_item` for DTO mapping, and provides `to_values()` for insert/update operations.

```python
class UserTable(BaseTable[User], table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str

    @classmethod
    def from_item(cls, item: User) -> "UserTable":
        return cls(id=item.id, name=item.name)

    def to_item(self) -> User:
        return User(id=self.id, name=self.name)
```

If `ItemType` is not specified (e.g. `BaseTable` without generic arg), `from_item`/`to_item` remain as `NotImplementedError` and the table works directly without DTO conversion.

### BaseRepository

`BaseRepository` uses `__init_subclass__` to enforce keyword arguments at class-definition time.

- `table` — required. The SQLModel table class. Must be specified on the first concrete subclass; intermediate bases that already specify it do not need to repeat it.
- `filter_` — required. A `BaseFilter` subclass.
- `dto` — optional. When provided, repository methods map table rows to that DTO type.

`table=` must be provided on the first subclass in the hierarchy.

The following introspection helpers are available as classmethods:

- `get_table_type()` — returns the `table` class specified at definition time.
- `get_filter_type()` — returns the `filter_` class.
- `get_dto_type()` — returns the `dto` class, or `None` if no DTO was set.

```python
class UserRepository(BaseRepository, table=UserTable, filter_=UserFilter, dto=User):
    pass  # Methods return User instances
```

If `dto` is omitted, repository methods return table instances directly:

```python
class ProductRepository(BaseRepository, table=ProductTable, filter_=ProductFilter):
    pass  # Methods return ProductTable instances
```

Note: `pydantic-filters` from GitHub is required for filter support (PyPI version is broken with pydantic v2). The project currently uses a fork with Python 3.14 lazy-annotations support: `git+https://github.com/OlegYurchik/pydantic-filters.git@fix/compare-to-pydantic-2.12`.

#### Single item retrieval

`get_item(filter_=..., sort=...)` returns the first matching record (or `None` if no records match). It delegates to `get_items` under the hood, so filter and sort semantics are identical:

```python
user = await user_repository.get_item(filter_=UserFilter(email="alice@example.com"))
if user is not None:
    print(user.name)
```

#### Eager loading (options)

`get_items()` and `update_items()` accept an optional `options` parameter for SQLAlchemy eager loading strategies such as `joinedload` or `selectinload`:

```python
from sqlalchemy.orm import joinedload

books = [
    item
    async for item in book_repository.get_items(
        options=[joinedload(BookTable.author)],
    )
]
```

#### Constructor

```python
# Simple: create container internally
repo = UserRepository(settings=RepositorySettings(dsn="sqlite+aiosqlite:///:memory:"))

# Advanced: reuse container for shared transactions
container = RepositoriesContainer(settings=settings)
repo = UserRepository(container=container)
```

### RepositoriesContainer

Manages the async SQLAlchemy engine and sessions via `contextvars`. Used directly only when you need **atomic transactions across multiple repositories**.

```python
container = RepositoriesContainer(settings=settings)
user_repo = container.get_repository(UserRepository)
order_repo = container.get_repository(OrderRepository)

async with container.transaction():
    user = await user_repo.create_item(User(name="Alice"))
    await order_repo.create_item(Order(user_id=user.id, total=100))
```

`container.transaction()` creates an `AsyncSession`, stores it in a context var, and all repository operations within the `async with` block automatically use that session. Nested `container.transaction()` calls yield the same session.

### Session Management

- Each repository method (`get_items`, `create_item`, etc.) wraps its operation in a transaction via `self.transaction()`.
- `self.transaction()` reuses an existing session from the context if one exists, otherwise creates a new one.
- `repository.session` and `container.session` both return the current `AsyncSession` or `None` if no session is active. Both `repository.transaction()` and `container.transaction()` yield the `AsyncSession` and handle nested calls by reusing the same session.
- `repository.nested_transaction()` and `container.nested_transaction()` create a SQLAlchemy savepoint (`begin_nested()`). When no outer session exists they start a new session with a savepoint. On exception the savepoint is rolled back, leaving any outer transaction unaffected.

## Development

### Environment

The project uses `uv` for dependency management and a local `.venv`:

```bash
# Sync dependencies
uv sync

# Run tests
.venv/bin/python -m pytest tests/ -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=metaorm

# Run specific example
PYTHONPATH=. .venv/bin/python examples/basic_usage.py
```

### Documentation

Documentation is built with MkDocs (Material theme) and deployed to GitHub Pages automatically via `.github/workflows/docs.yml`.

```bash
# Serve locally with live-reload
uv run mkdocs serve

# Build static site
uv run mkdocs build

# Deploy to gh-pages
uv run mkdocs gh-deploy --force
```

Docs dependencies: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`.

### Test Conventions

- Tests live in `tests/` and mirror the package structure.
- All async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.
- Fixtures are in `conftest.py` at the test package root.
- Use `parametrize` for data-driven tests.
- Do not use `monkeypatch`; prefer dependency injection with constructor arguments.
- Do not test protected methods or internal implementation details.

### Code Style

- PEP 8, enforced by `ruff`.
- Import grouping: stdlib, third-party, project-local (each block alphabetically sorted).
- `__init__.py` files explicitly declare `__all__` as a tuple with comment headers.
- No wildcard imports.
- No `from __future__ import annotations`.
- No `if TYPE_CHECKING:` blocks.
- Full variable names (no abbreviations like `idx`, `cfg`, `msg`).

## Publishing

`pyproject.toml` includes `[build-system]` and `[project.urls]` for PyPI. To publish via `uv`:

```bash
uv build
uv publish
```

For TestPyPI:

```bash
uv publish --index testpypi
```

## Key Dependencies

- `sqlmodel>=0.0.22` — SQLAlchemy + Pydantic ORM layer
- `pydantic-filters` (GitHub) — Query filter, pagination, sort models
- `sqlalchemy>=2.0` — Async engine/session

Dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `aiosqlite`.

## Exceptions Hierarchy

```
DatabaseException
├── NotFoundError
├── HaveNoSessionError
└── AlreadyExistsError
```

All repository methods raise `DatabaseException` subclasses or SQLAlchemy errors.
