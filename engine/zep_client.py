"""Small, synchronous wrapper around the current Zep Cloud Python SDK.

Each student has a Zep user graph.  Confusion events are structured JSON
episodes, rather than chat messages, so their original event time and fields
remain available for the tutor's timeline and as-of views.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar

import httpx
from dotenv import load_dotenv
from zep_cloud.client import Zep
from zep_cloud.core import ApiError
from zep_cloud.errors import ConflictError, NotFoundError
from zep_cloud.types import (
    DateFilter,
    EpisodeMetadataFilter,
    MetadataFilterGroup,
    SearchFilters,
)

from engine.schema import ConfusionEvent

_client: Optional[Zep] = None
_T = TypeVar("_T")
_MAX_INGEST_ATTEMPTS = 4


def get_client() -> Zep:
    """Return the process-wide Zep client, loading a local ``.env`` if present."""
    global _client
    if _client is None:
        load_dotenv()
        api_key = os.environ.get("ZEP_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ZEP_API_KEY is not configured. Copy .env.example to .env and add "
                "a Zep Cloud API key, or export ZEP_API_KEY before running the seed."
            )
        _client = Zep(api_key=api_key)
    return _client


def zep_user_id(tenant_id: str, student_ref: str) -> str:
    return f"{tenant_id}:{student_ref}"


def _zep_timestamp(value: datetime) -> str:
    """Serialize an event time as the timezone-aware ISO-8601 value Zep expects."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _retry_ingest(operation: Callable[[], _T]) -> _T:
    """Retry transient network, rate-limit, and server failures with backoff."""
    for attempt in range(_MAX_INGEST_ATTEMPTS):
        try:
            return operation()
        except (httpx.HTTPError, ApiError) as exc:
            retryable = not isinstance(exc, ApiError) or exc.status_code in {
                429,
                500,
                502,
                503,
                504,
            }
            if not retryable or attempt == _MAX_INGEST_ATTEMPTS - 1:
                raise
            time.sleep(0.5 * (2**attempt))
    raise AssertionError("unreachable")


def ensure_user(tenant_id: str, student_ref: str) -> str:
    """Idempotently create the Zep user graph for this tenant/student pair."""
    uid = zep_user_id(tenant_id, student_ref)
    try:
        get_client().user.get(uid)
    except NotFoundError:
        try:
            get_client().user.add(user_id=uid)
        except ConflictError:
            # Another worker created the same user after our lookup.
            pass
    return uid


def log_event(event: ConfusionEvent) -> None:
    """Ingest one confusion event into the student's isolated user graph.

    ``graph.add`` is Zep's non-conversational episode API.  ``created_at``
    records the synthetic or observed event time rather than ingestion time.
    """
    uid = ensure_user(event.tenant_id, event.student_ref)
    created_at = _zep_timestamp(event.timestamp)
    payload = {
        "event_type": "confusion_event",
        "tenant_id": event.tenant_id,
        "student_ref": event.student_ref,
        "pair_id": event.pair_id,
        "correct": event.correct,
        "context": event.context,
        "timestamp": created_at,
    }
    metadata = {
        "event_type": "confusion_event",
        "pair_id": event.pair_id,
        "correct": event.correct,
    }
    _retry_ingest(
        lambda: get_client().graph.add(
            data=json.dumps(payload, ensure_ascii=False),
            type="json",
            created_at=created_at,
            metadata=metadata,
            user_id=uid,
            source_description="Adaptive tutor confusion event",
        )
    )


def _event_from_episode(episode: Any, pair_id: str) -> Optional[dict[str, Any]]:
    """Return our event record when an episode is one of this pair's events."""
    metadata = getattr(episode, "metadata", None) or {}
    if metadata.get("event_type") != "confusion_event" or metadata.get("pair_id") != pair_id:
        return None
    try:
        payload = json.loads(episode.content)
    except (TypeError, json.JSONDecodeError):
        return None
    if payload.get("event_type") != "confusion_event":
        return None
    return {
        "timestamp": payload.get("timestamp", episode.created_at),
        "correct": payload.get("correct"),
        "context": payload.get("context"),
        "episode_uuid": episode.uuid_,
    }


def _events_for_pair(uid: str, pair_id: str) -> list[dict[str, Any]]:
    # ``lastn`` is Zep's documented episode-listing argument (not pagination).
    response = get_client().graph.episode.get_by_user_id(user_id=uid, lastn=100)
    events = [
        parsed
        for episode in response.episodes
        if (parsed := _event_from_episode(episode, pair_id)) is not None
    ]
    return sorted(events, key=lambda item: item["timestamp"])


def _edge_dict(edge: Any) -> dict[str, Any]:
    return {
        "uuid": edge.uuid_,
        "fact": edge.fact,
        "name": edge.name,
        "valid_at": edge.valid_at,
        "invalid_at": edge.invalid_at,
        "created_at": edge.created_at,
        "expired_at": edge.expired_at,
    }


def _pair_filter(pair_id: str) -> MetadataFilterGroup:
    """Restrict graph results to facts derived from this pair's episodes."""
    return MetadataFilterGroup(
        type="and",
        filters=[
            EpisodeMetadataFilter(
                comparison_operator="=",
                property_name="event_type",
                property_value="confusion_event",
            ),
            EpisodeMetadataFilter(
                comparison_operator="=",
                property_name="pair_id",
                property_value=pair_id,
            ),
        ],
    )


def get_current_state(tenant_id: str, student_ref: str, pair_id: str) -> dict:
    """Return raw event history plus Zep's currently valid graph facts for a pair."""
    uid = zep_user_id(tenant_id, student_ref)
    result = get_client().graph.search(
        user_id=uid,
        query=f"confusion event for concept pair {pair_id}",
        scope="edges",
        limit=50,
        search_filters=SearchFilters(
            invalid_at=[[DateFilter(comparison_operator="IS NULL")]],
            episode_metadata_filters=_pair_filter(pair_id),
        ),
    )
    return {
        "user_id": uid,
        "pair_id": pair_id,
        "events": _events_for_pair(uid, pair_id),
        "recent_facts": [_edge_dict(edge) for edge in result.edges],
    }


def get_state_as_of(
    tenant_id: str, student_ref: str, pair_id: str, as_of: datetime
) -> dict:
    """Return the pair's event timeline and graph facts valid at ``as_of``.

    Zep's edge search supports bi-temporal filtering: a fact was true at the
    requested instant when it had become valid and was either never invalidated
    or was invalidated later.  Event episodes are also filtered locally because
    datetime filters apply only to edge-scope searches in the Zep API.
    """
    uid = zep_user_id(tenant_id, student_ref)
    timestamp = _zep_timestamp(as_of)
    result = get_client().graph.search(
        user_id=uid,
        query=f"confusion event for concept pair {pair_id}",
        scope="edges",
        limit=50,
        search_filters=SearchFilters(
            valid_at=[[DateFilter(comparison_operator="<=", date=timestamp)]],
            invalid_at=[
                [DateFilter(comparison_operator="IS NULL")],
                [DateFilter(comparison_operator=">", date=timestamp)],
            ],
            episode_metadata_filters=_pair_filter(pair_id),
        ),
    )
    events = [event for event in _events_for_pair(uid, pair_id) if event["timestamp"] <= timestamp]
    return {
        "user_id": uid,
        "pair_id": pair_id,
        "as_of": timestamp,
        "events": events,
        "recent_facts": [_edge_dict(edge) for edge in result.edges],
    }
