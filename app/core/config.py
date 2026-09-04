"""
Application settings, loaded from environment variables (and .env locally).

Import `settings` anywhere you need config — never read os.environ directly
elsewhere in the app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "postgresql+psycopg://quizapp:devpassword@localhost:5430/quizapp"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is only read once per process."""
    return Settings()


settings = get_settings()