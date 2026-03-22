from fastapi.testclient import TestClient

from relationship_os.main import create_app


def test_runtime_websocket_stream_subscription_receives_trace_and_projection_updates() -> None:
    with TestClient(create_app()) as client:
        create_response = client.post(
            "/api/v1/sessions",
            json={"session_id": "ws-session"},
        )
        assert create_response.status_code == 201

        with client.websocket_connect("/api/v1/ws/runtime") as websocket:
            hello = websocket.receive_json()
            assert hello["type"] == "hello"
            assert hello["runtime"]["app"] == "RelationshipOS"

            websocket.send_json(
                {
                    "type": "subscribe",
                    "stream_id": "ws-session",
                    "include_backlog": True,
                }
            )

            subscribed = websocket.receive_json()
            trace_snapshot = websocket.receive_json()
            projection_snapshot = websocket.receive_json()

            assert subscribed["type"] == "subscribed"
            assert subscribed["subscription"]["stream_id"] == "ws-session"
            assert trace_snapshot["type"] == "trace_snapshot"
            assert trace_snapshot["stream_id"] == "ws-session"
            assert any(
                event["event_type"] == "session.started"
                for event in trace_snapshot["trace"]
            )
            assert projection_snapshot["type"] == "session_projection"
            assert projection_snapshot["projection"]["state"]["session"]["started"] is True

            turn_response = client.post(
                "/api/v1/sessions/ws-session/turns",
                json={"content": "我想继续推进，但也想先稳住节奏。"},
            )
            assert turn_response.status_code == 201

            trace_batch = websocket.receive_json()
            projection_update = websocket.receive_json()

            assert trace_batch["type"] == "trace_batch"
            assert trace_batch["stream_id"] == "ws-session"
            assert any(
                event["event_type"] == "assistant.message.sent"
                for event in trace_batch["events"]
            )
            assert projection_update["type"] == "session_projection"
            assert projection_update["projection"]["state"]["turn_count"] == 1


def test_runtime_websocket_stream_subscription_receives_job_and_archive_updates() -> None:
    with TestClient(create_app()) as client:
        first_turn_response = client.post(
            "/api/v1/sessions/ws-job-session/turns",
            json={"content": "Please consolidate this session and archive it when ready."},
        )
        assert first_turn_response.status_code == 201
        second_turn_response = client.post(
            "/api/v1/sessions/ws-job-session/turns",
            json={"content": "Please also keep the next step grounded and easy to follow."},
        )
        assert second_turn_response.status_code == 201

        with client.websocket_connect("/api/v1/ws/runtime") as websocket:
            hello = websocket.receive_json()
            assert hello["type"] == "hello"

            websocket.send_json(
                {
                    "type": "subscribe",
                    "stream_id": "ws-job-session",
                }
            )
            subscribed = websocket.receive_json()
            assert subscribed["type"] == "subscribed"

            create_job_response = client.post(
                "/api/v1/jobs/offline-consolidation",
                json={"session_id": "ws-job-session"},
            )
            assert create_job_response.status_code == 202

            completed_job = None
            archive_update = None
            runtime_overview = None
            for _ in range(24):
                message = websocket.receive_json()
                if message["type"] == "job_update" and message["job"]["status"] == "completed":
                    completed_job = message["job"]
                elif message["type"] == "archive_update":
                    archive_update = message
                elif message["type"] == "runtime_overview":
                    runtime_overview = message
                if completed_job and archive_update and runtime_overview:
                    break

            assert completed_job is not None
            assert completed_job["session_id"] == "ws-job-session"
            assert completed_job["last_worker_id"]
            assert archive_update is not None
            assert (
                archive_update["event"]["event_type"] == "system.session.archived"
            )
            assert runtime_overview is not None
            assert runtime_overview["runtime"]["job_runtime"]["worker_id"]
