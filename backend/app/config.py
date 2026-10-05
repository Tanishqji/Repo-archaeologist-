from functools import lru_cache
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env if present
load_dotenv()

class Settings(BaseSettings):
    # GitHub Integration
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # LLM Settings
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    llm_model: Optional[str] = Field(default=None, alias="LLM_MODEL")

    # Storage & Cache
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    sqlite_db_path: str = Field(default="./data/cache.db", alias="SQLITE_DB_PATH")
    chroma_dir: str = Field(default="./data/chroma", alias="CHROMA_DIR")

    # Budgets & Limits
    max_files_read: int = Field(default=150, alias="MAX_FILES_READ")
    max_file_bytes: int = Field(default=200000, alias="MAX_FILE_BYTES")
    max_repo_size_mb: int = Field(default=500, alias="MAX_REPO_SIZE_MB")
    context_token_budget: int = Field(default=30000, alias="CONTEXT_TOKEN_BUDGET")
    analysis_timeout_seconds: int = Field(default=90, alias="ANALYSIS_TIMEOUT_SECONDS")

    # Rate Limiting
    rate_limit_analyze_per_hour: int = Field(default=5, alias="RATE_LIMIT_ANALYZE_PER_HOUR")
    rate_limit_chat_per_hour: int = Field(default=30, alias="RATE_LIMIT_CHAT_PER_HOUR")
    cache_ttl_hours: int = Field(default=24, alias="CACHE_TTL_HOURS")

    # Networking & App
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    prompt_version: str = Field(default="v1", alias="PROMPT_VERSION")
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid_providers = {"gemini", "anthropic", "openai"}
        val = v.lower().strip()
        if val not in valid_providers:
            raise ValueError(f"Invalid LLM_PROVIDER '{v}'. Must be one of {valid_providers}")
        return val

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

@lru_cache()
def get_settings() -> Settings:
    # Ensure data directory exists
    Path("./data").mkdir(parents=True, exist_ok=True)
    return Settings()
