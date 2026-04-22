from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Attachment:
    """A user-supplied media attachment (image, audio, file)."""

    type: str  # "image" | "audio" | "file"
    url: str = ""
    mime_type: str = ""
    filename: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TurnInput:
    """Unified carrier for a single user turn, text + optional media."""

    text: str
    attachments: list[Attachment] = field(default_factory=list)

    @property
    def has_media(self) -> bool:
        return bool(self.attachments)

    @property
    def images(self) -> list[Attachment]:
        return [a for a in self.attachments if a.type == "image"]

    @property
    def audio(self) -> Attachment | None:
        return next((a for a in self.attachments if a.type == "audio"), None)

    @property
    def files(self) -> list[Attachment]:
        return [a for a in self.attachments if a.type == "file"]


@dataclass(slots=True, frozen=True)
class PerceptionResult:
    """Multimodal perception signals fused from non-text inputs.

    Populated by perception analyzers when media is present;
    ``None`` fields mean no signal was detected.
    """

    image_descriptions: list[str] = field(default_factory=list)
    detected_emotion_from_voice: str | None = None  # "calm" | "anxious" | "excited" | ...
    voice_energy_level: float | None = None  # 0.0 ~ 1.0
    scene_context: str | None = None  # "outdoor_park" | "office" | ...
    modality_flags: list[str] = field(default_factory=list)  # ["has_image", "has_audio"]
