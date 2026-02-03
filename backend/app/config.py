"""
Configuration management for Law Assistant backend.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Settings loaded from environment variables."""
    
    # LLM Provider
    llm_provider: str = "openai"  # openai or gemini
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"  # gpt-4, gpt-4-turbo, gpt-3.5-turbo
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"  # Stable, fast, cost-efficient model
    
    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./law_assistant.db"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
