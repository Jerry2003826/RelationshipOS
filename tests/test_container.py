import pytest

from relationship_os.application.container import build_container
from relationship_os.application.llm import LiteLLMClient, MockLLMClient
from relationship_os.core.config import Settings
from relationship_os.infrastructure.event_store.memory import InMemoryEventStore
from relationship_os.infrastructure.event_store.postgres import PostgresEventStore


def test_build_container_defaults_to_in_memory_event_store() -> None:
    container = build_container(Settings())

    assert isinstance(container.event_store, InMemoryEventStore)
    assert container.evaluation_service is not None
    assert container.audit_service is not None
    assert container.memory_service is not None
    assert container.proactive_followup_service is not None
    assert container.proactive_followup_dispatcher is not None
    assert container.job_service is not None
    assert container.job_executor is not None
    assert isinstance(container.llm_client, MockLLMClient)
    assert container.runtime_service is not None
    assert container.llm_client is not None
    assert container.database_engine is None


def test_build_container_can_switch_to_postgres_event_store() -> None:
    settings = Settings(
        event_store_backend="postgres",
        database_url="postgresql+psycopg://postgres:postgres@localhost:5432/relationship_os",
    )

    container = build_container(settings)

    assert isinstance(container.event_store, PostgresEventStore)
    assert container.evaluation_service is not None
    assert container.audit_service is not None
    assert container.memory_service is not None
    assert container.proactive_followup_service is not None
    assert container.proactive_followup_dispatcher is not None
    assert container.job_service is not None
    assert container.job_executor is not None
    assert container.runtime_service is not None
    assert container.database_engine is not None


def test_build_container_requires_database_url_for_postgres_backend() -> None:
    with pytest.raises(ValueError, match="RELATIONSHIP_OS_DATABASE_URL must be set"):
        build_container(Settings(event_store_backend="postgres"))


def test_build_container_can_switch_to_litellm_client() -> None:
    container = build_container(
        Settings(
            llm_backend="litellm",
            llm_model="openai/gpt-5-mini",
        )
    )

    assert isinstance(container.llm_client, LiteLLMClient)
