lint:
	uv run ruff check metaorm/ tests/

test:
	uv run pytest tests/ -v --cov=metaorm

build:
	uv build

publish:
	uv publish

publish-test:
	uv publish --index testpypi

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov

format:
	uv run ruff format metaorm/ tests/
	uv run ruff check --fix metaorm/ tests/
