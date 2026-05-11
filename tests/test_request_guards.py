from fastapi.testclient import TestClient

from relationship_os.api.middleware import RateLimitMiddleware
from relationship_os.core.config import Settings
from relationship_os.main import create_app


def test_request_body_size_guard_rejects_oversized_json_body() -> None:
    client = TestClient(create_app(Settings(max_request_bytes=32)))

    response = client.post(
        "/api/v1/sessions/body-too-large/turns",
        json={"content": "x" * 128},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_request_json_depth_guard_rejects_deep_metadata() -> None:
    client = TestClient(create_app(Settings(max_json_depth=3)))

    response = client.post(
        "/api/v1/sessions",
        json={
            "session_id": "too-deep",
            "metadata": {"a": {"b": {"c": {"d": "too deep"}}}},
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Request JSON too deeply nested"


def test_rate_limit_rejects_excess_requests_for_same_identity() -> None:
    client = TestClient(
        create_app(
            Settings(
                rate_limit_requests=2,
                rate_limit_window_seconds=60,
            )
        )
    )
    headers = {"X-User-ID": "limited-user"}

    first = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"session_id": "rate-limit-a"},
    )
    second = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"session_id": "rate-limit-b"},
    )
    third = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"session_id": "rate-limit-c"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429
    assert third.json()["detail"] == "Rate limit exceeded"


def test_rate_limit_prunes_expired_buckets_when_over_budget() -> None:
    middleware = RateLimitMiddleware(
        app=None,
        max_requests=2,
        window_seconds=10,
        max_buckets=2,
    )
    middleware._buckets = {
        "expired-a": (0.0, 1),
        "expired-b": (1.0, 1),
        "active": (95.0, 1),
    }

    middleware._prune_buckets(now=100.0)

    assert middleware._buckets == {"active": (95.0, 1)}
