# API Reference

## BaseRepository

::: metaorm.repositories.BaseRepository
    options:
      show_source: true
      members:
        - __init_subclass__
        - __init__
        - get_items_count
        - get_item
        - get_items
        - create_item
        - update_items
        - delete_items
        - create_tables
        - get_table_type
        - get_filter_type
        - get_dto_type

## BaseTable

::: metaorm.tables.BaseTable

## RepositoriesContainer

::: metaorm.container.RepositoriesContainer
    options:
      show_source: true

## RepositorySettings

::: metaorm.settings.RepositorySettings

## Exceptions

::: metaorm.exceptions.DatabaseException
::: metaorm.exceptions.NotFoundError
::: metaorm.exceptions.HaveNoSessionError
::: metaorm.exceptions.AlreadyExistsError

## Re-exports

The following symbols are re-exported from `metaorm` for convenience:

- `BaseFilter`, `BasePagination`, `BaseSort`, `OffsetPagination`, `PagePagination` — from `pydantic-filters`
- `Field`, `Relationship` — from `sqlmodel`
