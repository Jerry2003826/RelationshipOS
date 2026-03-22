from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RelationshipOS"
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    database_url: str = ""
    event_store_backend: Literal["memory", "postgres"] = "memory"
    llm_backend: Literal["mock", "litellm"] = "mock"
    llm_model: str = "openai/gpt-5"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 30
    llm_api_base: str | None = None
    llm_api_key: str | None = None
    job_max_attempts: int = 2
    job_poll_interval_seconds: float = 0.5
    job_worker_id: str | None = None
    job_claim_ttl_seconds: float = 5.0
    job_heartbeat_interval_seconds: float = 1.0
    runtime_quality_doctor_interval_turns: int = 3
    runtime_quality_doctor_window_turns: int = 4
    proactive_followup_worker_id: str | None = None
    proactive_followup_poll_interval_seconds: float = 5.0
    proactive_followup_max_dispatch_per_cycle: int = 2
    default_projector_version: str = Field(default="v1")

    model_config = SettingsConfigDict(
        env_prefix="RELATIONSHIP_OS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def require_database_url(self) -> str:
        database_url = self.database_url.strip()
        if not database_url:
            raise ValueError("RELATIONSHIP_OS_DATABASE_URL must be set")
        return database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
