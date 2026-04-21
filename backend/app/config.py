from functools import lru_cache
import re

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


class Settings(BaseSettings):
    app_name: str = "ysj.brief API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./ysj_brief.db"
    db_schema: str = "public"
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_days: int = 30
    cookie_secure: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    anthropic_api_key: str | None = None
    claude_model: str = "claude-haiku-4-5"
    timezone: str = "Asia/Seoul"
    mock_claude: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            origins: list[str] = []
        elif isinstance(value, str):
            raw = value.strip()
            if raw.startswith("[") and raw.endswith("]"):
                items = [item.strip().strip('"').strip("'") for item in raw[1:-1].split(",")]
                origins = [item for item in items if item]
            else:
                origins = [item.strip() for item in raw.split(",") if item.strip()]
        elif isinstance(value, list):
            origins = [str(item).strip() for item in value if str(item).strip()]
        else:
            origins = [str(value).strip()]

        merged: list[str] = []
        for origin in [*origins, *DEV_CORS_ORIGINS]:
            if origin and origin not in merged:
                merged.append(origin)
        return merged

    @field_validator("db_schema")
    @classmethod
    def validate_db_schema(cls, value: str) -> str:
        schema = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise ValueError("db_schema must be a valid PostgreSQL identifier")
        return schema

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
