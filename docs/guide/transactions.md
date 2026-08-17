# Transactions

Every repository method (`get_items`, `create_item`, etc.) wraps its operation in a transaction via `self.transaction()`. `self.transaction()` reuses an existing session from the context if one exists, otherwise creates a new one.

## Explicit transaction

You can open an explicit transaction when you need to group several operations:

```python
async with repository.transaction():
    product1 = await repository.create_item(ProductTable(name="Laptop", price=999.99))
    product2 = await repository.create_item(ProductTable(name="Mouse", price=29.99))
```

If any operation raises an exception, the entire transaction is rolled back.

## Reusing an existing session

Nested `transaction()` calls yield the same session — no new savepoint is created:

```python
async with repository.transaction(), repository.transaction():
    items = [item async for item in repository.get_items()]
```

## Nested transactions (savepoints)

`nested_transaction()` creates a SQLAlchemy savepoint. When no outer session exists it starts a new session with a savepoint. On exception the savepoint is rolled back, leaving any outer transaction unaffected:

```python
try:
    async with repository.nested_transaction():
        await repository.create_item(ProductTable(name="Keyboard", price=79.99))
        raise ValueError("Rollback nested")
except ValueError:
    pass

# Keyboard was rolled back; previous items remain
```

This is useful for partial rollback inside a larger transaction. See [Multi-Repo Transactions](container.md) for container-level savepoints.
