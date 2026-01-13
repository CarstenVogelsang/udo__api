"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application Settings"""

    # SQLite (Development/Production)
    sqlite_database_url: str = "sqlite+aiosqlite:///./data/udo.db"

    # Legacy MS SQL Server (READ-ONLY!)
    mssql_host: str = "192.168.91.22"
    mssql_port: int = 1433
    mssql_database: str = "toyware"
    mssql_user: str = ""
    mssql_password: str = ""

    # API Settings
    api_prefix: str = "/api/v1"
    api_title: str = "UDO API"
    api_version: str = "0.2.0"
    debug: bool = False

    # JWT Authentication
    jwt_secret_key: str = "dev-secret-key-change-in-production"  # Override in .env!
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
