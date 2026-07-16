"""
REST API surface (see docs/design_doc.md §5).

Run locally:
    uvicorn api.rest.app:app --reload

TODO before demo:
- Add auth (API key header check) -- currently wide open, fine for local
  dev only.
- Add the /v1/pairs listing endpoint (needs a small store/lookup over
  seed-data/*.json or a real ConceptPair table -- currently only events
  and insights are wired).
"""

from fastapi import FastAPI, HTTPException

from engine.insight_engine import evaluate
from engine.schema import ConfusionEvent, InsightLog
from engine.zep_client import log_event

app = FastAPI(title="Adaptive Memory for Tutors API")


@app.post("/v1/events", response_model=InsightLog)
def post_event(event: ConfusionEvent) -> InsightLog:
    """Log a confusion event and return the resulting insight.

    This is the one call an integrating tutor needs: send us what
    happened, get back what to do next and why.
    """
    try:
        log_event(event)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Zep write failed: {e}")

    return evaluate(event)


@app.get("/v1/insights/{pair_id}")
def get_insight(pair_id: str, tenant_id: str, student_ref: str) -> dict:
    """TODO: return the latest stored InsightLog for this pair/student,
    once InsightLog persistence is decided (see engine/insight_engine.py
    module docstring)."""
    raise HTTPException(
        status_code=501,
        detail="Not yet implemented -- see TODO in api/rest/app.py",
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
