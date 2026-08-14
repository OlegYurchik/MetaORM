import pytest
from pydantic import ValidationError

from metaorm import RepositorySettings


class TestRepositorySettings:
    def test_default_values(self) -> None:
        settings = RepositorySettings()

        assert settings.dsn == "sqlite+aiosqlite:///db.sqlite3"
        assert settings.pool_size == 5
        assert settings.pool_recycle == 60
        assert settings.pool_timeout == 60

    def test_custom_values(self) -> None:
        settings = RepositorySettings(
            dsn="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=10,
            pool_recycle=120,
            pool_timeout=30,
        )

        assert settings.dsn == "postgresql+asyncpg://user:pass@localhost/db"
        assert settings.pool_size == 10
        assert settings.pool_recycle == 120
        assert settings.pool_timeout == 30

    def test_dsn_must_match_pattern(self) -> None:
        with pytest.raises(ValidationError):
            RepositorySettings(dsn="invalid_dsn")

    @pytest.mark.parametrize(
        "field_name,invalid_value",
        [
            ("pool_size", 0),
            ("pool_recycle", 0),
            ("pool_timeout", 0),
        ],
    )
    def test_integer_fields_must_be_greater_or_equal_one(
        self,
        field_name: str,
        invalid_value: int,
    ) -> None:
        with pytest.raises(ValidationError):
            RepositorySettings(**{field_name: invalid_value})
