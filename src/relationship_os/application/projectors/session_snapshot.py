"""SessionSnapshotProjector — snapshot history tracking."""

from typing import Any

from relationship_os.domain.event_types import SESSION_SNAPSHOT_CREATED
from relationship_os.domain.events import StoredEvent
from relationship_os.domain.projectors import Projector


class SessionSnapshotProjector(Projector[dict[str, Any]]):
    name = "session-snapshots"
    version = "v1"

    def initial_state(self) -> dict[str, Any]:
        return {
            "snapshots": [],
            "snapshot_count": 0,
            "latest_snapshot_id": None,
        }

    def apply(self, state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        next_state = {
            "snapshots": list(state["snapshots"]),
            "snapshot_count": state["snapshot_count"],
            "latest_snapshot_id": state["latest_snapshot_id"],
        }
        if event.event_type != SESSION_SNAPSHOT_CREATED:
            return next_state

        snapshot = dict(event.payload)
        next_state["snapshots"].append(snapshot)
        next_state["snapshots"] = next_state["snapshots"][-50:]
        next_state["snapshot_count"] += 1
        next_state["latest_snapshot_id"] = snapshot.get("snapshot_id")
        return next_state
