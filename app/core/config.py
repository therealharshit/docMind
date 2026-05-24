from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Intelligent Document Ingestion System"
    app_env: str = "development"
    log_level: str = "INFO"

    storage_dir: Path = Path("storage")
    database_url: str = "sqlite:///storage/app.db"
    max_upload_mb: int = 100

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout_seconds: int = 45
    ollama_num_parallel: int = 1

    pipeline_mode: str = Field(default="fast", pattern="^(fast|quality)$")
    fast_mode_max_chars: int = 18_000
    quality_mode_max_chars: int = 60_000
    worker_poll_seconds: float = 1.0

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def result_dir(self) -> Path:
        return self.storage_dir / "results"

    @property
    def sqlite_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported in this slice")
        return Path(self.database_url.removeprefix("sqlite:///"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
