"""Shared test fixtures for RelationshipOS."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from relationship_os.core.config import Settings, get_settings
from relationship_os.main import create_app

if TYPE_CHECKING:
    pass

_TEST_ENV_OVERRIDES = {
    "RELATIONSHIP_OS_EVENT_STORE_BACKEND": "memory",
    "RELATIONSHIP_OS_LLM_BACKEND": "mock",
    "RELATIONSHIP_OS_DATABASE_URL": "",
    "RELATIONSHIP_OS_API_KEY": "",
    "RELATIONSHIP_OS_CORS_ORIGINS": "",
    "RELATIONSHIP_OS_MEMORY_INDEX_ENABLED": "true",
    "RELATIONSHIP_OS_MEMORY_INDEX_STORE_PATH": ".pytest_memory_index",
    "RELATIONSHIP_OS_MEMORY_INDEX_TEXT_PROVIDER": "hash",
    "RELATIONSHIP_OS_MEMORY_INDEX_MULTIMODAL_PROVIDER": "none",
    "RELATIONSHIP_OS_MEMORY_INDEX_RERANKER_ENABLED": "false",
}


@pytest.fixture(autouse=True, scope="session")
def _force_memory_backend() -> None:
    """Ensure every test uses the in-memory event store, regardless of .env."""
    original_values = {key: os.environ.get(key) for key in _TEST_ENV_OVERRIDES}
    for key, value in _TEST_ENV_OVERRIDES.items():
        os.environ[key] = value
    get_settings.cache_clear()
    yield
    for key, original in original_values.items():
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original
    get_settings.cache_clear()


def _test_settings() -> Settings:
    """Build settings that guarantee hermetic in-memory tests regardless of .env."""
    return Settings(
        event_store_backend="memory",
        llm_backend="mock",
        database_url="",
        api_key="",
        cors_origins="",
        memory_index_enabled=True,
        memory_index_store_path=".pytest_memory_index",
        memory_index_text_provider="hash",
        memory_index_multimodal_provider="none",
        memory_index_reranker_enabled=False,
        _env_file=None,  # type: ignore[call-arg]
    )


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI TestClient with fresh in-memory state."""
    return TestClient(create_app(settings=_test_settings()))


@pytest.fixture
def session_with_turn(client: TestClient) -> dict:
    """Create a session with one Chinese-language turn and return the response body."""
    resp = client.post(
        "/api/v1/sessions/fixture-session/turns",
        json={"content": "我有点焦虑，想先把计划推进下去。"},
    )
    assert resp.status_code == 201
    return resp.json()
