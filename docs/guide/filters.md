# Filters, Pagination & Sorting

MetaORM delegates filtering, pagination and sorting to `pydantic-filters`. All you need is a `BaseFilter` subclass.

## Filters

```python
from metaorm import BaseFilter


class BookFilter(BaseFilter):
    title: str | None = None
    year: int | None = None
```

Use the filter when querying:

```python
# Exact match
items = [item async for item in repo.get_items(filter_=BookFilter(year=2025))]

# Single item
single = await repo.get_item(filter_=BookFilter(title="Book 5"))
```

## Pagination

```python
from metaorm import OffsetPagination

pagination = OffsetPagination(offset=2, limit=3)
page = [item async for item in repo.get_items(pagination=pagination)]
```

## Sorting

```python
from metaorm import BaseSort

sort = BaseSort(sort_by="year", sort_by_order="desc")
sorted_items = [item async for item in repo.get_items(sort=sort)]
```

## Combining all three

```python
items = [
    item
    async for item in repo.get_items(
        filter_=BookFilter(year=2025),
        pagination=OffsetPagination(offset=0, limit=10),
        sort=BaseSort(sort_by="title", sort_by_order="asc"),
    )
]
```
