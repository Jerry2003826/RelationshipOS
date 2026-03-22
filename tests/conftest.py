"""Shared test fixtures for RelationshipOS."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from relationship_os.main import create_app

if TYPE_CHECKING:
    pass


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI TestClient with fresh in-memory state."""
    return TestClient(create_app())


@pytest.fixture
def session_with_turn(client: TestClient) -> dict:
    """Create a session with one Chinese-language turn and return the response body."""
    resp = client.post(
        "/api/v1/sessions/fixture-session/turns",
        json={"content": "我有点焦虑，想先把计划推进下去。"},
    )
    assert resp.status_code == 201
    return resp.json()
