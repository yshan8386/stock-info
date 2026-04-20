from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ysj.brief API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./ysj_brief.db"
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_days: int = 30
    cookie_secure: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    anthropic_api_key: str | None = None
    claude_model: str = "claude-haiku-4-5"
    timezone: str = "Asia/Seoul"
    mock_claude: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

