from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from relationship_os.domain.events import StoredEvent

ProjectionStateT = TypeVar("ProjectionStateT")


class UnknownProjectorError(LookupError):
    """Raised when a projector cannot be resolved by name and version."""


class Projector(Protocol[ProjectionStateT]):
    name: str
    version: str

    def initial_state(self) -> ProjectionStateT: ...

    def apply(self, state: ProjectionStateT, event: StoredEvent) -> ProjectionStateT: ...


@dataclass(slots=True)
class VersionedProjectorRegistry:
    _projectors: dict[tuple[str, str], Projector[Any]]

    def __init__(self) -> None:
        self._projectors = {}

    def register(self, projector: Projector[Any]) -> None:
        key = (projector.name, projector.version)
        self._projectors[key] = projector

    def resolve(self, *, name: str, version: str) -> Projector[Any]:
        projector = self._projectors.get((name, version))
        if projector is None:
            raise UnknownProjectorError(f"Unknown projector {name}:{version}")
        return projector

    def list_projectors(self) -> list[dict[str, str]]:
        return [
            {"name": name, "version": version} for name, version in sorted(self._projectors.keys())
        ]
