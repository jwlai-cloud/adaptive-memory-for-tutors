"""
Thin wrapper over the Zep Cloud SDK.

Scoping convention (see docs/design_doc.md §3.2):
- One Zep "user" per (tenant_id, student_ref) pair -> one isolated graph
  per student, fully separated from every other student and tenant.
- We namespace the Zep user_id as f"{tenant_id}:{student_ref}" so two
  different schools can each have a "student-042" without collision.

TODO (Day 1 exit criteria, see docs/handover_doc.md):
- Confirm the exact zep-cloud SDK method names against current docs
  (the SDK has changed shape across versions -- verify before relying
  on this against a real API key).
- Add retry/backoff around episode ingestion (episodes can take up to
  a few minutes to process per Zep's own FAQ).
"""

import os
from datetime import datetime
from typing import Optional

from zep_cloud.client import Zep

from engine.schema import ConfusionEvent

_client: Optional[Zep] = None


def get_client() -> Zep:
    global _client
    if _client is None:
        api_key = os.environ["ZEP_API_KEY"]
        _client = Zep(api_key=api_key)
    return _client


def zep_user_id(tenant_id: str, student_ref: str) -> str:
    return f"{tenant_id}:{student_ref}"


def ensure_user(tenant_id: str, student_ref: str) -> str:
    """Idempotently ensure a Zep user (= one isolated graph) exists for
    this student. Returns the Zep user_id."""
    client = get_client()
    uid = zep_user_id(tenant_id, student_ref)
    try:
        client.user.add(user_id=uid)
    except Exception:
        # TODO: narrow this to "already exists" specifically once verified
        # against the current SDK's exception types.
        pass
    return uid


def log_event(event: ConfusionEvent) -> None:
    """Ingest a ConfusionEvent as a Zep episode on the student's graph."""
    uid = ensure_user(event.tenant_id, event.student_ref)
    client = get_client()
    episode_text = (
        f"Concept pair {event.pair_id}: student answered "
        f"{'correctly' if event.correct else 'incorrectly'}"
        f"{f' ({event.context})' if event.context else ''} "
        f"at {event.timestamp.isoformat()}."
    )
    client.memory.add(
        session_id=uid,  # TODO: verify current SDK param name (session vs user vs thread)
        messages=[{"role": "system", "content": episode_text}],
    )


def get_current_state(tenant_id: str, student_ref: str, pair_id: str) -> dict:
    """Fetch the current (most recent, non-invalidated) confusion state
    for this student/pair. Returns a dict the insight engine can reason
    over. TODO: replace with an actual graph query once the SDK's
    fact-retrieval / as-of query surface is confirmed."""
    uid = zep_user_id(tenant_id, student_ref)
    client = get_client()
    # Placeholder shape -- fill in against real SDK response once wired up.
    return {
        "user_id": uid,
        "pair_id": pair_id,
        "recent_facts": [],
    }


def get_state_as_of(
    tenant_id: str, student_ref: str, pair_id: str, as_of: datetime
) -> dict:
    """Point-in-time query -- the demo-critical 'as-of two weeks ago' call.
    TODO: implement against Graphiti's valid_at/invalid_at filtering once
    confirmed in the current Zep search API."""
    raise NotImplementedError(
        "Wire this up against Zep's temporal search API -- see design_doc.md §3.1"
    )
