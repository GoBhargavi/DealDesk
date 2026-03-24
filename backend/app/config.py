"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/dealdesk"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    
    # AWS/S3
    S3_BUCKET: str = "dealdesk-documents"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
