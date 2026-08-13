from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    dsn: str = Field(default="sqlite+aiosqlite:///db.sqlite3", pattern=r"^.+://")
    pool_size: int = Field(default=5, ge=1)
    pool_recycle: int = Field(default=60, ge=1)  # in seconds: 1 minute
    pool_timeout: int = Field(default=60, ge=1)  # in seconds: 1 minute
