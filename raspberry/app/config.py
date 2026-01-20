from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://council_user:pass123@postgres:5432/ai_council"
    
    # LLM Configuration
    ollama_base_url: str = "http://ollama:11434"
    
    # Model names
    model_name_1: str = "llama3.2:1b"
    model_name_2: str = "mistral:7b"
    model_name_3: str = "gemma:2b"
    
    # Timeout for LLM requests (in seconds)
    llm_timeout: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from old .env files
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
