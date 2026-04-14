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
    llm_backend: Literal["mock", "litellm", "minimax"] = "mock"
    llm_model: str = "openai/gpt-5"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 30
    llm_api_base: str | None = None
    llm_api_key: str | None = None
    runtime_profile: str = "default"
    policy_root_path: str = "policies"
    edge_allow_cloud_escalation: bool = True
    edge_target_latency_seconds: float = 5.0
    edge_hard_latency_seconds: float = 10.0
    edge_max_memory_items: int = 4
    edge_max_prompt_tokens: int = 1800
    edge_max_completion_tokens: int = 260
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
    api_key: str = ""
    cors_origins: str = ""
    default_projector_version: str = Field(default="v2")
    persona_file: str = "persona.md"
    entity_id: str = "server"
    entity_name: str = "大猫皮层"
    entity_persona_seed_file: str = ""
    search_enabled: bool = True
    memory_index_enabled: bool = True
    fact_memory_backend: Literal["native", "mem0_shadow", "mem0_primary"] = "mem0_shadow"
    memory_index_store_path: str = ".relationship_os/memory_index"
    memory_index_text_provider: Literal["hash", "aliyun", "openai_compatible"] = "aliyun"
    memory_index_text_model: str = "text-embedding-v4"
    memory_index_text_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    memory_index_text_api_key: str | None = None
    memory_index_text_dimensions: int = 1024
    memory_index_multimodal_provider: Literal[
        "none",
        "aliyun",
        "google",
        "openai_compatible",
    ] = "aliyun"
    memory_index_multimodal_model: str = "qwen3-vl-embedding"
    memory_index_multimodal_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    memory_index_multimodal_api_key: str | None = None
    memory_index_reranker_enabled: bool = True
    memory_index_reranker_provider: Literal["aliyun", "openai_compatible"] = "aliyun"
    memory_index_reranker_model: str = "qwen3-vl-rerank"
    memory_index_reranker_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    memory_index_reranker_api_key: str | None = None
    mem0_qdrant_path: str = ".relationship_os/mem0/qdrant"
    mem0_history_db_path: str = ".relationship_os/mem0/history.db"
    mem0_embed_model: str = "intfloat/multilingual-e5-small"
    mem0_retrieval_limit: int = 12

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
