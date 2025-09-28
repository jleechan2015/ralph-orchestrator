"""Configuration settings for the application."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    APP_NAME: str = "Task Management API"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="development-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./tasks.db")

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["*"])

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()