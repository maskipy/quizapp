"""
Application settings, loaded from environment variables (and .env locally).

Import `settings` anywhere you need config — never read os.environ directly
elsewhere in the app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Settings class is used to define the configuration for the application. 
# It inherits from BaseSettings provided by Pydantic, 
# which allows for easy loading of environment variables and .env files.
class Settings(BaseSettings):
    # The model_config attribute is used to configure the behavior of the Settings class.
    # It specifies that the environment variables should be loaded from a .env file with UTF-8 encoding, and any extra environment variables not defined in the Settings class should be ignored.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # The following attributes define the configuration settings for the application, including the environment and database URL.
    environment: str = "development"
    database_url: str = "postgresql+psycopg://quizapp:devpassword@localhost:5430/quizapp"

# The get_settings function is decorated with lru_cache to cache the settings instance.
# cached settings instance ensures that the environment variables are only read once per process, improving performance.
@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is only read once per process."""
    return Settings()

# The settings variable is initialized by calling the get_settings function,
# which returns the cached instance of the Settings class.
settings = get_settings()