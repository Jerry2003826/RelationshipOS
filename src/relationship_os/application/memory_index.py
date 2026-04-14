from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import httpx

from relationship_os.core.logging import get_logger

_LOGGER = get_logger("relationship_os.memory_index")
_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff:.-]+")
_MAX_MEDIA_FETCH_BYTES = 5 * 1024 * 1024
_DEFAULT_VECTOR_DIMENSIONS = 128
_ALIYUN_TEXT_EMBEDDING_MAX_BATCH = 10


def _utc_iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _normalize_text(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(value.casefold()))


def _safe_scope_filename(scope_id: str) -> str:
    digest = hashlib.sha1(scope_id.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9_-]+", "_", scope_id.casefold()).strip("_")[:40]
    return f"{slug or 'scope'}_{digest}.json"


def _normalize_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0:
        return values
    return [value / norm for value in values]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right, strict=False)))


def _response_error_detail(response: httpx.Response) -> str:
    content_type = (response.headers.get("content-type") or "").lower()
    if "text/html" in content_type:
        return "html_frontend_response"
    try:
        payload = response.json()
    except Exception:
        text = response.text.strip()
        return text[:200] if text else f"http_{response.status_code}"
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return f"http_{response.status_code}"


def _raise_for_proxy_response(response: httpx.Response) -> None:
    if response.status_code >= 400:
        detail = _response_error_detail(response)
        raise ValueError(f"provider_unavailable[{response.status_code}]: {detail}")
    content_type = (response.headers.get("content-type") or "").lower()
    if "text/html" in content_type:
        raise ValueError("provider_unavailable[html_frontend_response]")


def _candidate_api_v1_urls(api_base: str, suffix: str) -> list[str]:
    base = api_base.rstrip("/")
    if base.endswith("/api/v1"):
        trimmed = base[: -len("/api/v1")]
        return [f"{base}{suffix}", f"{trimmed}{suffix}"]
    return [f"{base}/api/v1{suffix}", f"{base}{suffix}"]


def _fallback_embedding(text: str, *, dimensions: int = _DEFAULT_VECTOR_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    tokens = _TOKEN_RE.findall(text.casefold())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    return _normalize_vector(vector)


@dataclass(slots=True, frozen=True)
class MemoryMediaAttachment:
    type: str
    url: str = ""
    mime_type: str = ""
    filename: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class MemoryIndexRecord:
    record_id: str
    scope_id: str
    user_id: str | None
    session_id: str | None
    layer: str
    memory_kind: str
    text: str
    normalized_key: str
    occurred_at: str | None = None
    last_seen_at: str | None = None
    mention_count: int = 1
    importance_score: float = 0.0
    confidence_score: float = 0.0
    retention_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    attachments: list[MemoryMediaAttachment] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class MemoryIndexHit:
    record: MemoryIndexRecord
    index_kind: str
    vector_score: float
    rank: int


class TextEmbedder(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class MultimodalEmbedder(Protocol):
    async def embed_query(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        ...

    async def embed_record(self, record: MemoryIndexRecord) -> list[float]:
        ...


class HashTextEmbedder:
    def __init__(self, *, dimensions: int = _DEFAULT_VECTOR_DIMENSIONS) -> None:
        self._dimensions = max(32, dimensions)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_fallback_embedding(text, dimensions=self._dimensions) for text in texts]


class OpenAICompatibleTextEmbedder:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        dimensions: int = 1024,
        fallback: TextEmbedder | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://api.apiyi.com").rstrip("/")
        self._dimensions = dimensions
        self._fallback = fallback or HashTextEmbedder(dimensions=min(dimensions, 256))
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "openai_compatible",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            self._status = {
                "provider": "openai_compatible",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "fallback",
                "fallback": True,
                "reason": "missing_api_key",
            }
            return await self._fallback.embed_texts(texts)
        payload: dict[str, Any] = {
            "model": self._model,
            "input": texts,
        }
        if self._dimensions > 0:
            payload["dimensions"] = self._dimensions
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        unavailable_error: Exception | None = None
        for url in self._candidate_urls("/embeddings"):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    _raise_for_proxy_response(response)
                data = response.json().get("data", [])
                embeddings = [item.get("embedding", []) for item in data]
                if len(embeddings) != len(texts) or not embeddings:
                    raise ValueError("OpenAI-compatible embedding response length mismatch")
                self._status = {
                    "provider": "openai_compatible",
                    "model": self._model,
                    "api_base": self._api_base,
                    "mode": "provider",
                    "fallback": False,
                    "url": url,
                    "dimensions": len(embeddings[0]),
                }
                return [
                    _normalize_vector([float(value) for value in embedding])
                    for embedding in embeddings
                ]
            except Exception as exc:
                last_error = exc
                if "provider_unavailable" in str(exc) and unavailable_error is None:
                    unavailable_error = exc
        resolved_error = unavailable_error or last_error
        _LOGGER.warning(
            "openai_compatible_text_embedding_failed",
            model=self._model,
            api_base=self._api_base,
            error=str(resolved_error) if resolved_error else "unknown_error",
        )
        self._status = {
            "provider": "openai_compatible",
            "model": self._model,
            "api_base": self._api_base,
            "mode": (
                "unavailable"
                if resolved_error and "provider_unavailable" in str(resolved_error)
                else "fallback"
            ),
            "fallback": True,
            "error": str(resolved_error) if resolved_error else "unknown_error",
        }
        return await self._fallback.embed_texts(texts)

    def _candidate_urls(self, suffix: str) -> list[str]:
        if self._api_base.endswith("/v1"):
            trimmed = self._api_base[: -len("/v1")]
            return [f"{self._api_base}{suffix}", f"{trimmed}{suffix}"]
        return [f"{self._api_base}/v1{suffix}", f"{self._api_base}{suffix}"]

    def status(self) -> dict[str, Any]:
        return dict(self._status)


class AliyunTextEmbedder:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        dimensions: int = 1024,
        fallback: TextEmbedder | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://dashscope.aliyuncs.com/api/v1").rstrip("/")
        self._dimensions = dimensions
        self._fallback = fallback or HashTextEmbedder(dimensions=min(dimensions, 256))
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "aliyun",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            self._status = {
                "provider": "aliyun",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "fallback",
                "fallback": True,
                "reason": "missing_api_key",
            }
            return await self._fallback.embed_texts(texts)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        unavailable_error: Exception | None = None
        for url in _candidate_api_v1_urls(
            self._api_base,
            "/services/embeddings/text-embedding/text-embedding",
        ):
            try:
                vectors = await self._embed_texts_via_url(
                    url=url,
                    texts=texts,
                    headers=headers,
                )
                self._status = {
                    "provider": "aliyun",
                    "model": self._model,
                    "api_base": self._api_base,
                    "mode": "provider",
                    "fallback": False,
                    "url": url,
                    "dimensions": len(vectors[0]),
                }
                return [
                    _normalize_vector([float(value) for value in vector]) for vector in vectors
                ]
            except Exception as exc:
                last_error = exc
                if "provider_unavailable" in str(exc) and unavailable_error is None:
                    unavailable_error = exc
        resolved_error = unavailable_error or last_error
        _LOGGER.warning(
            "aliyun_text_embedding_failed",
            model=self._model,
            api_base=self._api_base,
            error=str(resolved_error) if resolved_error else "unknown_error",
        )
        self._status = {
            "provider": "aliyun",
            "model": self._model,
            "api_base": self._api_base,
            "mode": (
                "unavailable"
                if resolved_error and "provider_unavailable" in str(resolved_error)
                else "fallback"
            ),
            "fallback": True,
            "error": str(resolved_error) if resolved_error else "unknown_error",
        }
        return await self._fallback.embed_texts(texts)

    def status(self) -> dict[str, Any]:
        return dict(self._status)

    async def _embed_texts_via_url(
        self,
        *,
        url: str,
        texts: list[str],
        headers: dict[str, str],
    ) -> list[list[float]]:
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            for batch_start in range(0, len(texts), _ALIYUN_TEXT_EMBEDDING_MAX_BATCH):
                batch = texts[
                    batch_start : batch_start + _ALIYUN_TEXT_EMBEDDING_MAX_BATCH
                ]
                payload: dict[str, Any] = {
                    "model": self._model,
                    "input": {"texts": batch},
                }
                if self._dimensions > 0:
                    payload["parameters"] = {"dimension": self._dimensions}
                response = await client.post(url, headers=headers, json=payload)
                _raise_for_proxy_response(response)
                body = response.json()
                embeddings = body.get("output", {}).get("embeddings", [])
                if len(embeddings) != len(batch) or not embeddings:
                    raise ValueError("Aliyun text embedding response length mismatch")
                vectors.extend(
                    item.get("embedding", [])
                    for item in sorted(
                        embeddings,
                        key=lambda item: int(
                            item.get("text_index", item.get("index", 0))
                        ),
                    )
                )
        return vectors


class AliyunMultimodalEmbedder:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        dimensions: int = 1024,
        fallback: TextEmbedder | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://dashscope.aliyuncs.com/api/v1").rstrip("/")
        self._dimensions = dimensions
        self._fallback = fallback or HashTextEmbedder()
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "aliyun",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def embed_query(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        return await self._embed_parts(text=text, attachments=attachments)

    async def embed_record(self, record: MemoryIndexRecord) -> list[float]:
        return await self._embed_parts(text=record.text, attachments=record.attachments)

    async def _embed_parts(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        if not self._api_key:
            self._status = {
                "provider": "aliyun",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "fallback",
                "fallback": True,
                "reason": "missing_api_key",
            }
            return (await self._fallback.embed_texts([self._fallback_text(text, attachments)]))[0]

        contents: list[dict[str, Any]] = []
        if text.strip():
            contents.append({"text": text})
        contents.extend(await self._materialize_attachments(attachments))
        if not contents:
            return (await self._fallback.embed_texts([""]))[0]

        payload = {
            "model": self._model,
            "input": {"contents": contents},
            "parameters": {"dimension": self._dimensions},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        unavailable_error: Exception | None = None
        for url in _candidate_api_v1_urls(
            self._api_base,
            "/services/embeddings/multimodal-embedding/multimodal-embedding",
        ):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    _raise_for_proxy_response(response)
                body = response.json()
                embeddings = body.get("output", {}).get("embeddings", [])
                if not embeddings:
                    raise ValueError("Aliyun multimodal embedding returned no embeddings")
                vector = embeddings[0].get("embedding", [])
                self._status = {
                    "provider": "aliyun",
                    "model": self._model,
                    "api_base": self._api_base,
                    "mode": "provider",
                    "fallback": False,
                    "url": url,
                    "dimensions": len(vector),
                }
                return _normalize_vector([float(value) for value in vector])
            except Exception as exc:
                last_error = exc
                if "provider_unavailable" in str(exc) and unavailable_error is None:
                    unavailable_error = exc
        resolved_error = unavailable_error or last_error
        _LOGGER.warning(
            "aliyun_multimodal_embedding_failed",
            model=self._model,
            api_base=self._api_base,
            error=str(resolved_error) if resolved_error else "unknown_error",
        )
        self._status = {
            "provider": "aliyun",
            "model": self._model,
            "api_base": self._api_base,
            "mode": (
                "unavailable"
                if resolved_error and "provider_unavailable" in str(resolved_error)
                else "fallback"
            ),
            "fallback": True,
            "error": str(resolved_error) if resolved_error else "unknown_error",
        }
        return (await self._fallback.embed_texts([self._fallback_text(text, attachments)]))[0]

    async def _materialize_attachments(
        self,
        attachments: list[MemoryMediaAttachment],
    ) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []
        for attachment in attachments[:4]:
            if attachment.url:
                if attachment.type == "image":
                    contents.append({"image": attachment.url})
                elif attachment.type == "video":
                    contents.append({"video": attachment.url})
                else:
                    descriptor = " ".join(
                        part
                        for part in [
                            attachment.type,
                            attachment.filename,
                            attachment.mime_type,
                            str(attachment.metadata.get("caption", "")),
                            str(attachment.metadata.get("summary", "")),
                        ]
                        if part
                    ).strip()
                    if descriptor:
                        contents.append({"text": descriptor})
        return contents

    def _fallback_text(
        self,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> str:
        descriptors = [
            " ".join(
                part
                for part in [
                    attachment.type,
                    attachment.filename,
                    attachment.mime_type,
                    str(attachment.metadata.get("caption", "")),
                    str(attachment.metadata.get("summary", "")),
                ]
                if part
            ).strip()
            for attachment in attachments
        ]
        return " ".join(part for part in [text.strip(), *descriptors] if part)

    def status(self) -> dict[str, Any]:
        return dict(self._status)


class GoogleMultimodalEmbedder:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        fallback: TextEmbedder | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self._fallback = fallback or HashTextEmbedder()
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "google",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def embed_query(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        return await self._embed_parts(text=text, attachments=attachments)

    async def embed_record(self, record: MemoryIndexRecord) -> list[float]:
        return await self._embed_parts(text=record.text, attachments=record.attachments)

    async def _embed_parts(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        if not self._api_key:
            self._status = {
                "provider": "google",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "fallback",
                "fallback": True,
                "reason": "missing_api_key",
            }
            return (await self._fallback.embed_texts([self._fallback_text(text, attachments)]))[0]

        parts: list[dict[str, Any]] = []
        if text.strip():
            parts.append({"text": text})
        media_parts = await self._materialize_attachments(attachments)
        parts.extend(media_parts)
        if not parts:
            return (await self._fallback.embed_texts([""]))[0]

        url = f"{self._api_base}/models/{self._model}:embedContent"
        payload = {"content": {"parts": parts}}
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    url,
                    params={"key": self._api_key},
                    json=payload,
                )
                _raise_for_proxy_response(response)
            values = response.json().get("embedding", {}).get("values", [])
            if not values:
                raise ValueError("Google multimodal embedding returned no values")
            self._status = {
                "provider": "google",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "provider",
                "fallback": False,
                "url": url,
                "dimensions": len(values),
            }
            return _normalize_vector([float(value) for value in values])
        except Exception as exc:
            _LOGGER.warning(
                "google_multimodal_embedding_failed",
                model=self._model,
                api_base=self._api_base,
                error=str(exc),
            )
            self._status = {
                "provider": "google",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "unavailable" if "provider_unavailable" in str(exc) else "fallback",
                "fallback": True,
                "error": str(exc),
            }
            return (await self._fallback.embed_texts([self._fallback_text(text, attachments)]))[0]

    async def _materialize_attachments(
        self,
        attachments: list[MemoryMediaAttachment],
    ) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = []
        for attachment in attachments[:4]:
            if not attachment.url:
                continue
            blob = await self._fetch_attachment_bytes(attachment)
            if blob is None:
                continue
            parts.append(
                {
                    "inline_data": {
                        "mime_type": attachment.mime_type or "application/octet-stream",
                        "data": base64.b64encode(blob).decode("ascii"),
                    }
                }
            )
        return parts

    async def _fetch_attachment_bytes(
        self,
        attachment: MemoryMediaAttachment,
    ) -> bytes | None:
        try:
            if attachment.url.startswith(("http://", "https://")):
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(attachment.url)
                    response.raise_for_status()
                    return response.content[:_MAX_MEDIA_FETCH_BYTES]
            path = Path(attachment.url)
            if path.is_file():
                return await asyncio.to_thread(path.read_bytes)
        except Exception as exc:
            _LOGGER.warning(
                "multimodal_attachment_fetch_failed",
                url=attachment.url,
                error=str(exc),
            )
        return None

    def _fallback_text(
        self,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> str:
        descriptors = [
            " ".join(
                part
                for part in [
                    attachment.type,
                    attachment.filename,
                    attachment.mime_type,
                    attachment.metadata.get("caption", ""),
                ]
                if part
            ).strip()
            for attachment in attachments
        ]
        return " ".join(part for part in [text.strip(), *descriptors] if part)

    def status(self) -> dict[str, Any]:
        return dict(self._status)


class DescriptorMultimodalEmbedder:
    def __init__(self, *, text_embedder: TextEmbedder) -> None:
        self._text_embedder = text_embedder

    async def embed_query(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        descriptor = self._descriptor_text(text=text, attachments=attachments)
        return (await self._text_embedder.embed_texts([descriptor]))[0]

    async def embed_record(self, record: MemoryIndexRecord) -> list[float]:
        descriptor = self._descriptor_text(text=record.text, attachments=record.attachments)
        return (await self._text_embedder.embed_texts([descriptor]))[0]

    def _descriptor_text(
        self,
        *,
        text: str,
        attachments: list[MemoryMediaAttachment],
    ) -> str:
        attachment_lines = [
            " ".join(
                part
                for part in [
                    attachment.type,
                    attachment.filename,
                    attachment.mime_type,
                    str(attachment.metadata.get("caption", "")),
                    str(attachment.metadata.get("scene", "")),
                    str(attachment.metadata.get("summary", "")),
                ]
                if part
            ).strip()
            for attachment in attachments
        ]
        return " ".join(part for part in [text.strip(), *attachment_lines] if part)

    def status(self) -> dict[str, Any]:
        return {
            "provider": "descriptor",
            "mode": "descriptor",
            "fallback": False,
            "native_multimodal": False,
        }


class MemoryIndex(Protocol):
    async def write_many(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        ...

    async def search(
        self,
        *,
        scope_id: str,
        query: str,
        limit: int,
        attachments: list[MemoryMediaAttachment] | None = None,
        use_reranker: bool = True,
    ) -> list[MemoryIndexHit]:
        ...

    async def delete_user(self, *, scope_id: str) -> None:
        ...

    async def rebuild_user(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        ...


class NullMemoryIndex:
    async def write_many(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        return None

    async def search(
        self,
        *,
        scope_id: str,
        query: str,
        limit: int,
        attachments: list[MemoryMediaAttachment] | None = None,
        use_reranker: bool = True,
    ) -> list[MemoryIndexHit]:
        del use_reranker
        return []

    async def delete_user(self, *, scope_id: str) -> None:
        return None

    async def rebuild_user(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        return None


class MemoryReranker(Protocol):
    async def rerank(
        self,
        *,
        query: str,
        hits: list[MemoryIndexHit],
        limit: int,
    ) -> list[MemoryIndexHit]:
        ...


class NullMemoryReranker:
    async def rerank(
        self,
        *,
        query: str,
        hits: list[MemoryIndexHit],
        limit: int,
    ) -> list[MemoryIndexHit]:
        return hits[:limit]

    def status(self) -> dict[str, Any]:
        return {
            "provider": "none",
            "mode": "disabled",
            "fallback": False,
        }


class OpenAICompatibleMemoryReranker:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://api.apiyi.com").rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "openai_compatible",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def rerank(
        self,
        *,
        query: str,
        hits: list[MemoryIndexHit],
        limit: int,
    ) -> list[MemoryIndexHit]:
        if not self._api_key or not hits:
            self._status = {
                "provider": "openai_compatible",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "disabled" if not self._api_key else "skipped",
                "fallback": False,
                "reason": "missing_api_key" if not self._api_key else "no_hits",
            }
            return hits[:limit]
        candidates = hits[: max(limit * 2, len(hits))]
        system_prompt = (
            "Rank memory candidates for a relationship assistant. "
            "Prefer factual relevance, persistence, and consistency. "
            "Return strict JSON: {\"ordered_ids\": [\"...\"]}."
        )
        user_payload = {
            "query": query,
            "candidates": [
                {
                    "record_id": hit.record.record_id,
                    "text": hit.record.text,
                    "layer": hit.record.layer,
                    "memory_kind": hit.record.memory_kind,
                    "importance_score": hit.record.importance_score,
                    "confidence_score": hit.record.confidence_score,
                    "vector_score": hit.vector_score,
                }
                for hit in candidates
            ],
        }
        body = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        unavailable_error: Exception | None = None
        for url in self._candidate_urls("/chat/completions"):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=body,
                    )
                    _raise_for_proxy_response(response)
                content = (
                    response.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "{}")
                )
                ordered_ids = list(json.loads(content).get("ordered_ids", []))
                order_map = {record_id: index for index, record_id in enumerate(ordered_ids)}
                reranked = sorted(
                    candidates,
                    key=lambda hit: (
                        order_map.get(hit.record.record_id, len(order_map) + hit.rank),
                        -hit.vector_score,
                    ),
                )
                self._status = {
                    "provider": "openai_compatible",
                    "model": self._model,
                    "api_base": self._api_base,
                    "mode": "provider",
                    "fallback": False,
                    "url": url,
                }
                return reranked[:limit]
            except Exception as exc:
                last_error = exc
                if "provider_unavailable" in str(exc) and unavailable_error is None:
                    unavailable_error = exc
        resolved_error = unavailable_error or last_error
        _LOGGER.warning(
            "memory_reranker_failed",
            model=self._model,
            api_base=self._api_base,
            error=str(resolved_error) if resolved_error else "unknown_error",
        )
        self._status = {
            "provider": "openai_compatible",
            "model": self._model,
            "api_base": self._api_base,
            "mode": (
                "unavailable"
                if resolved_error and "provider_unavailable" in str(resolved_error)
                else "fallback"
            ),
            "fallback": True,
            "error": str(resolved_error) if resolved_error else "unknown_error",
        }
        return candidates[:limit]

    def _candidate_urls(self, suffix: str) -> list[str]:
        if self._api_base.endswith("/v1"):
            trimmed = self._api_base[: -len("/v1")]
            return [f"{self._api_base}{suffix}", f"{trimmed}{suffix}"]
        return [f"{self._api_base}/v1{suffix}", f"{self._api_base}{suffix}"]

    def status(self) -> dict[str, Any]:
        return dict(self._status)


class AliyunNativeMemoryReranker:
    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        api_base: str | None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._model = model
        self._api_key = api_key or ""
        self._api_base = (api_base or "https://dashscope.aliyuncs.com/api/v1").rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._status: dict[str, Any] = {
            "provider": "aliyun",
            "model": model,
            "api_base": self._api_base,
            "mode": "uninitialized",
            "fallback": False,
        }

    async def rerank(
        self,
        *,
        query: str,
        hits: list[MemoryIndexHit],
        limit: int,
    ) -> list[MemoryIndexHit]:
        if not self._api_key or not hits:
            self._status = {
                "provider": "aliyun",
                "model": self._model,
                "api_base": self._api_base,
                "mode": "disabled" if not self._api_key else "skipped",
                "fallback": False,
                "reason": "missing_api_key" if not self._api_key else "no_hits",
            }
            return hits[:limit]
        candidates = hits[: max(limit * 2, len(hits))]
        payload = {
            "model": self._model,
            "input": {
                "query": query,
                "documents": [{"text": hit.record.text} for hit in candidates],
            },
            "parameters": {
                "return_documents": False,
                "top_n": min(limit, len(candidates)),
            },
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        unavailable_error: Exception | None = None
        for url in _candidate_api_v1_urls(
            self._api_base,
            "/services/rerank/text-rerank/text-rerank",
        ):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    _raise_for_proxy_response(response)
                body = response.json()
                results = body.get("output", {}).get("results", [])
                if not isinstance(results, list):
                    raise ValueError("Aliyun reranker returned invalid results")
                order_map = {
                    int(item.get("index", 0)): rank for rank, item in enumerate(results)
                }
                reranked = sorted(
                    candidates,
                    key=lambda hit: (
                        order_map.get(hit.rank - 1, len(order_map) + hit.rank),
                        -hit.vector_score,
                    ),
                )
                self._status = {
                    "provider": "aliyun",
                    "model": self._model,
                    "api_base": self._api_base,
                    "mode": "provider",
                    "fallback": False,
                    "url": url,
                }
                return reranked[:limit]
            except Exception as exc:
                last_error = exc
                if "provider_unavailable" in str(exc) and unavailable_error is None:
                    unavailable_error = exc
        resolved_error = unavailable_error or last_error
        _LOGGER.warning(
            "aliyun_memory_reranker_failed",
            model=self._model,
            api_base=self._api_base,
            error=str(resolved_error) if resolved_error else "unknown_error",
        )
        self._status = {
            "provider": "aliyun",
            "model": self._model,
            "api_base": self._api_base,
            "mode": (
                "unavailable"
                if resolved_error and "provider_unavailable" in str(resolved_error)
                else "fallback"
            ),
            "fallback": True,
            "error": str(resolved_error) if resolved_error else "unknown_error",
        }
        return candidates[:limit]

    def status(self) -> dict[str, Any]:
        return dict(self._status)


class FileBackedMemoryIndex:
    def __init__(
        self,
        *,
        root_path: str,
        text_embedder: TextEmbedder,
        multimodal_embedder: MultimodalEmbedder | None = None,
        reranker: MemoryReranker | None = None,
    ) -> None:
        self._root = Path(root_path)
        self._root.mkdir(parents=True, exist_ok=True)
        self._text_embedder = text_embedder
        self._multimodal_embedder = multimodal_embedder
        self._reranker = reranker or NullMemoryReranker()
        self._scope_cache: dict[str, dict[str, Any] | None] = {}
        self._text_query_cache: dict[str, list[float]] = {}
        self._multimodal_query_cache: dict[str, list[float]] = {}
        self._scope_cache_limit = 64
        self._query_cache_limit = 128

    async def write_many(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        multimodal_records = multimodal_records or []
        existing_payload = await self._load_scope(scope_id)
        existing_text_entries = {
            str(item.get("record", {}).get("record_id", "")): item
            for item in (existing_payload or {}).get("text_records", [])
            if item.get("record", {}).get("record_id")
        }
        existing_multimodal_entries = {
            str(item.get("record", {}).get("record_id", "")): item
            for item in (existing_payload or {}).get("multimodal_records", [])
            if item.get("record", {}).get("record_id")
        }
        text_vectors = await self._resolve_text_vectors(
            records=text_records,
            existing_payload=existing_payload,
        )
        for record, vector in zip(text_records, text_vectors, strict=False):
            existing_text_entries[record.record_id] = {
                "record": asdict(record),
                "vector": vector,
            }
        payload = {
            "scope_id": scope_id,
            "updated_at": _utc_iso_now(),
            "text_records": [
                existing_text_entries[key] for key in sorted(existing_text_entries)
            ],
            "multimodal_records": [
                existing_multimodal_entries[key]
                for key in sorted(existing_multimodal_entries)
            ],
        }
        if multimodal_records and self._multimodal_embedder is not None:
            multimodal_vectors = await self._resolve_multimodal_vectors(
                records=multimodal_records,
                existing_payload=existing_payload,
            )
            for record, vector in zip(
                multimodal_records,
                multimodal_vectors,
                strict=False,
            ):
                existing_multimodal_entries[record.record_id] = {
                    "record": asdict(record),
                    "vector": vector,
                }
            payload["multimodal_records"] = [
                existing_multimodal_entries[key]
                for key in sorted(existing_multimodal_entries)
            ]
        await asyncio.to_thread(self._write_scope_payload, scope_id, payload)
        self._remember_cache(
            self._scope_cache,
            scope_id,
            payload,
            limit=self._scope_cache_limit,
        )

    async def search(
        self,
        *,
        scope_id: str,
        query: str,
        limit: int,
        attachments: list[MemoryMediaAttachment] | None = None,
        use_reranker: bool = True,
    ) -> list[MemoryIndexHit]:
        payload = await self._load_scope(scope_id)
        if payload is None:
            return []
        attachments = attachments or []
        query_vector = await self._get_text_query_vector(query)
        hits = self._score_payload_records(
            payload.get("text_records", []),
            query_vector,
            limit=limit,
            index_kind="text",
        )
        if (
            attachments
            and payload.get("multimodal_records")
            and self._multimodal_embedder is not None
        ):
            multi_query_vector = await self._get_multimodal_query_vector(
                query=query,
                attachments=attachments,
            )
            hits.extend(
                self._score_payload_records(
                    payload.get("multimodal_records", []),
                    multi_query_vector,
                    limit=limit,
                    index_kind="multimodal",
                )
            )
        hits.sort(key=lambda item: item.vector_score, reverse=True)
        if not use_reranker:
            return hits[:limit]
        return await self._reranker.rerank(query=query, hits=hits, limit=limit)

    async def delete_user(self, *, scope_id: str) -> None:
        path = self._scope_path(scope_id)
        if path.exists():
            await asyncio.to_thread(path.unlink)
        self._scope_cache.pop(scope_id, None)

    async def rebuild_user(
        self,
        *,
        scope_id: str,
        text_records: list[MemoryIndexRecord],
        multimodal_records: list[MemoryIndexRecord] | None = None,
    ) -> None:
        await self.delete_user(scope_id=scope_id)
        await self.write_many(
            scope_id=scope_id,
            text_records=text_records,
            multimodal_records=multimodal_records,
        )

    async def _resolve_text_vectors(
        self,
        *,
        records: list[MemoryIndexRecord],
        existing_payload: dict[str, Any] | None,
    ) -> list[list[float]]:
        existing_vectors = self._existing_vectors(
            existing_payload=existing_payload,
            key="text_records",
        )
        resolved: list[list[float] | None] = [None] * len(records)
        missing_indexes: list[int] = []
        missing_texts: list[str] = []
        for index, record in enumerate(records):
            cached = existing_vectors.get(record.record_id)
            if cached is not None:
                cached_text = str(cached.get("record", {}).get("text", ""))
                if cached_text == record.text:
                    resolved[index] = [float(value) for value in cached.get("vector", [])]
                    continue
            missing_indexes.append(index)
            missing_texts.append(record.text)
        if missing_texts:
            embedded = await self._text_embedder.embed_texts(missing_texts)
            for index, vector in zip(missing_indexes, embedded, strict=False):
                resolved[index] = vector
        return [vector or [] for vector in resolved]

    async def _resolve_multimodal_vectors(
        self,
        *,
        records: list[MemoryIndexRecord],
        existing_payload: dict[str, Any] | None,
    ) -> list[list[float]]:
        existing_vectors = self._existing_vectors(
            existing_payload=existing_payload,
            key="multimodal_records",
        )
        resolved: list[list[float] | None] = [None] * len(records)
        for index, record in enumerate(records):
            cached = existing_vectors.get(record.record_id)
            if cached is not None:
                cached_text = str(cached.get("record", {}).get("text", ""))
                if cached_text == record.text:
                    resolved[index] = [float(value) for value in cached.get("vector", [])]
                    continue
            resolved[index] = await self._multimodal_embedder.embed_record(record)
        return [vector or [] for vector in resolved]

    def _existing_vectors(
        self,
        *,
        existing_payload: dict[str, Any] | None,
        key: str,
    ) -> dict[str, dict[str, Any]]:
        if not existing_payload:
            return {}
        existing_records = existing_payload.get(key, [])
        if not isinstance(existing_records, list):
            return {}
        vectors: dict[str, dict[str, Any]] = {}
        for item in existing_records:
            if not isinstance(item, dict):
                continue
            record = item.get("record", {})
            record_id = str(record.get("record_id", "") or "")
            if record_id:
                vectors[record_id] = item
        return vectors

    def _scope_path(self, scope_id: str) -> Path:
        return self._root / _safe_scope_filename(scope_id)

    def _write_scope_payload(self, scope_id: str, payload: dict[str, Any]) -> None:
        path = self._scope_path(scope_id)
        temp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "utf-8",
        )
        temp_path.replace(path)

    async def _load_scope(self, scope_id: str) -> dict[str, Any] | None:
        cached = self._scope_cache.get(scope_id)
        if cached is not None:
            return cached
        path = self._scope_path(scope_id)
        if not path.exists():
            return None
        raw = await asyncio.to_thread(path.read_text, "utf-8")
        if not raw.strip():
            _LOGGER.warning(
                "memory_index_scope_empty_recovered",
                scope_id=scope_id,
                path=str(path),
            )
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            _LOGGER.warning(
                "memory_index_scope_corrupt_recovered",
                scope_id=scope_id,
                path=str(path),
            )
            return None
        self._remember_cache(
            self._scope_cache,
            scope_id,
            payload,
            limit=self._scope_cache_limit,
        )
        return payload

    async def _get_text_query_vector(self, query: str) -> list[float]:
        cached = self._text_query_cache.get(query)
        if cached is not None:
            return list(cached)
        vector = (await self._text_embedder.embed_texts([query]))[0]
        self._remember_cache(
            self._text_query_cache,
            query,
            list(vector),
            limit=self._query_cache_limit,
        )
        return vector

    async def _get_multimodal_query_vector(
        self,
        *,
        query: str,
        attachments: list[MemoryMediaAttachment],
    ) -> list[float]:
        cache_key = self._multimodal_query_cache_key(
            query=query,
            attachments=attachments,
        )
        cached = self._multimodal_query_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        vector = await self._multimodal_embedder.embed_query(
            text=query,
            attachments=attachments,
        )
        self._remember_cache(
            self._multimodal_query_cache,
            cache_key,
            list(vector),
            limit=self._query_cache_limit,
        )
        return vector

    def _multimodal_query_cache_key(
        self,
        *,
        query: str,
        attachments: list[MemoryMediaAttachment],
    ) -> str:
        parts = [query]
        for attachment in attachments:
            parts.append(
                "|".join(
                    [
                        attachment.type,
                        attachment.url,
                        attachment.mime_type,
                        attachment.filename,
                        json.dumps(
                            attachment.metadata,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    ]
                )
            )
        return "\n".join(parts)

    def _remember_cache(
        self,
        cache: dict[str, Any],
        key: str,
        value: Any,
        *,
        limit: int,
    ) -> None:
        if key in cache:
            cache.pop(key)
        cache[key] = value
        while len(cache) > limit:
            cache.pop(next(iter(cache)))

    def _score_payload_records(
        self,
        stored: list[dict[str, Any]],
        query_vector: list[float],
        *,
        limit: int,
        index_kind: str,
    ) -> list[MemoryIndexHit]:
        hits: list[MemoryIndexHit] = []
        for item in stored:
            record_payload = item.get("record", {})
            vector = [float(value) for value in item.get("vector", [])]
            score = _cosine_similarity(query_vector, vector)
            if score <= 0:
                continue
            record = MemoryIndexRecord(
                **{
                    **record_payload,
                    "attachments": [
                        MemoryMediaAttachment(**attachment)
                        for attachment in record_payload.get("attachments", [])
                    ],
                }
            )
            hits.append(
                MemoryIndexHit(
                    record=record,
                    index_kind=index_kind,
                    vector_score=round(score, 4),
                    rank=0,
                )
            )
        hits.sort(key=lambda item: item.vector_score, reverse=True)
        return [
            MemoryIndexHit(
                record=hit.record,
                index_kind=hit.index_kind,
                vector_score=hit.vector_score,
                rank=index + 1,
            )
            for index, hit in enumerate(hits[:limit])
        ]


def build_memory_index(
    *,
    enabled: bool,
    root_path: str,
    text_provider: str,
    text_model: str,
    text_api_key: str | None,
    text_api_base: str | None,
    text_dimensions: int,
    multimodal_provider: str,
    multimodal_model: str,
    multimodal_api_key: str | None,
    multimodal_api_base: str | None,
    reranker_enabled: bool,
    reranker_provider: str,
    reranker_model: str,
    reranker_api_key: str | None,
    reranker_api_base: str | None,
) -> MemoryIndex:
    if not enabled:
        return NullMemoryIndex()

    fallback_text_embedder = HashTextEmbedder(dimensions=min(max(text_dimensions, 64), 256))
    if text_provider == "aliyun":
        text_embedder = AliyunTextEmbedder(
            model=text_model,
            api_key=text_api_key,
            api_base=text_api_base,
            dimensions=text_dimensions,
            fallback=fallback_text_embedder,
        )
    elif text_provider == "openai_compatible":
        text_embedder: TextEmbedder = OpenAICompatibleTextEmbedder(
            model=text_model,
            api_key=text_api_key,
            api_base=text_api_base,
            dimensions=text_dimensions,
            fallback=fallback_text_embedder,
        )
    else:
        text_embedder = fallback_text_embedder

    multimodal_embedder: MultimodalEmbedder | None = None
    if multimodal_provider == "aliyun":
        multimodal_embedder = AliyunMultimodalEmbedder(
            model=multimodal_model,
            api_key=multimodal_api_key,
            api_base=multimodal_api_base,
            dimensions=text_dimensions,
            fallback=fallback_text_embedder,
        )
    elif multimodal_provider == "google":
        multimodal_embedder = GoogleMultimodalEmbedder(
            model=multimodal_model,
            api_key=multimodal_api_key,
            api_base=multimodal_api_base,
            fallback=fallback_text_embedder,
        )
    elif multimodal_provider == "openai_compatible":
        multimodal_embedder = DescriptorMultimodalEmbedder(text_embedder=text_embedder)

    reranker: MemoryReranker | None = None
    if reranker_enabled and reranker_model:
        if reranker_provider == "aliyun":
            reranker = AliyunNativeMemoryReranker(
                model=reranker_model,
                api_key=reranker_api_key,
                api_base=reranker_api_base,
            )
        else:
            reranker = OpenAICompatibleMemoryReranker(
                model=reranker_model,
                api_key=reranker_api_key,
                api_base=reranker_api_base,
            )

    return FileBackedMemoryIndex(
        root_path=root_path,
        text_embedder=text_embedder,
        multimodal_embedder=multimodal_embedder,
        reranker=reranker,
    )
