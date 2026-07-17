"""MCP tools for integrating the tutoring-memory engine into an agent."""

import os

from mcp.server.fastmcp import FastMCP

from engine.insight_engine import evaluate
from engine.schema import ConfusionEvent
from engine.zep_client import get_current_state, get_latest_insight, log_event

# FastMCP 1.x configures HTTP bind settings at construction time. Cloud Run
# injects PORT; the values are unused for the default local stdio transport.
mcp = FastMCP(
    "adaptive-memory-for-tutors",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8080")),
)


@mcp.tool()
def log_confusion_event(
    tenant_id: str,
    pair_id: str,
    student_ref: str,
    correct: bool,
    context: str | None = None,
) -> dict:
    """Log that a student got a concept-pair question right or wrong.
    Returns the resulting insight (decision + reasoning) so the calling
    tutor agent can immediately adjust its next drill."""
    event = ConfusionEvent(
        tenant_id=tenant_id,
        pair_id=pair_id,
        student_ref=student_ref,
        correct=correct,
        context=context,
    )
    log_event(event)
    insight = evaluate(event)
    return insight.model_dump(mode="json")


@mcp.tool()
def get_insight_state(tenant_id: str, pair_id: str, student_ref: str) -> dict:
    """Get the current insight state for a student/concept-pair, without
    logging a new event. Use this before generating a new drill."""
    state = get_current_state(tenant_id, student_ref, pair_id)
    insight = get_latest_insight(tenant_id, student_ref, pair_id)
    return {
        "insight": insight.model_dump(mode="json") if insight else None,
        "recent_facts": state["recent_facts"],
        "graph_facts": state["graph_facts"],
    }


if __name__ == "__main__":
    # Cloud Run provides PORT and requires an HTTP listener; local tool clients
    # can retain the stdio default by omitting MCP_TRANSPORT.
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
