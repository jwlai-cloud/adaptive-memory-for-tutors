"""Authenticated REST API surface for the tutor-memory engine."""

import hmac
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from engine.insight_engine import evaluate
from engine.schema import ConceptPair, ConfusionEvent, InsightLog
from engine.zep_client import (
    get_current_state,
    get_insight_history,
    get_latest_insight,
    log_event,
)

load_dotenv()


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    """Minimal bearer-token check for the hackathon demo API."""
    expected = os.environ.get("API_KEY")
    scheme, _, token = (authorization or "").partition(" ")
    if not expected or scheme.lower() != "bearer" or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


app = FastAPI(title="Adaptive Memory for Tutors API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
_SEED_DATA_DIR = (Path(__file__).resolve().parents[2] / "seed-data").resolve()
api = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


@api.post("/events", response_model=InsightLog)
def post_event(event: ConfusionEvent) -> InsightLog:
    """Log a confusion event and return the resulting insight.

    This is the one call an integrating tutor needs: send us what
    happened, get back what to do next and why.
    """
    try:
        log_event(event)
        return evaluate(event)
    except Exception as e:
        # This route depends on both managed services; do not expose a raw
        # traceback to an integrating tutor when either upstream is unavailable.
        raise HTTPException(status_code=502, detail=f"Insight processing failed: {e}") from e


@api.get("/insights/{pair_id}")
def get_insight(pair_id: str, tenant_id: str, student_ref: str) -> dict:
    """Return the latest persisted GPT-derived decision for a pair."""
    insight = get_latest_insight(tenant_id, student_ref, pair_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="No insight has been recorded for this pair")
    return insight.model_dump(mode="json")


@api.get("/insights/{pair_id}/history", response_model=list[InsightLog])
def get_insight_feed(pair_id: str, tenant_id: str, student_ref: str) -> list[InsightLog]:
    """Return the chronological audit feed of persisted insight decisions."""
    return get_insight_history(tenant_id, student_ref, pair_id)


@api.get("/state/{pair_id}")
def get_state(pair_id: str, tenant_id: str, student_ref: str) -> dict:
    """Return source-event history plus the latest decision for a pair."""
    state = get_current_state(tenant_id, student_ref, pair_id)
    latest = get_latest_insight(tenant_id, student_ref, pair_id)
    return {
        **state,
        "latest_insight": latest.model_dump(mode="json") if latest else None,
    }


@api.get("/pairs", response_model=list[ConceptPair])
def get_pairs(domain: str = Query(..., min_length=1)) -> list[ConceptPair]:
    """List illustrative concept pairs from the requested seed-data domain."""
    if not re.fullmatch(r"[a-z0-9-]+", domain):
        raise HTTPException(status_code=404, detail=f"Unknown domain: {domain}")
    path = (_SEED_DATA_DIR / f"domain-{domain}.json").resolve()
    if not path.is_relative_to(_SEED_DATA_DIR) or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Unknown domain: {domain}")
    data = json.loads(path.read_text())
    tenant_id = os.environ.get("DEFAULT_TENANT_ID", "demo-school")
    return [
        ConceptPair(
            id=pair["id"],
            tenant_id=tenant_id,
            domain=data["domain"],
            label_a=pair["label_a"],
            label_b=pair["label_b"],
            description=pair.get("description"),
        )
        for pair in data["pairs"]
    ]


app.include_router(api)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
