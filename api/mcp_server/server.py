"""
MCP server surface (see docs/design_doc.md §5).

This is the primary intended integration path: any Codex/Claude-built
tutor agent adds this server's URL and immediately gets memory-augmented
tutoring, no custom integration code needed.

TODO:
- Confirm current `mcp` package API shape (this scaffolds the intended
  tool names/signatures per the design doc; verify against whatever MCP
  SDK version ends up installed).
- Add get_confusion_heatmap once the underlying multi-pair query exists.
"""

from mcp.server.fastmcp import FastMCP

from engine.insight_engine import evaluate
from engine.schema import ConfusionEvent
from engine.zep_client import log_event

mcp = FastMCP("adaptive-memory-for-tutors")


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
    # TODO: implement against persisted InsightLog / Zep current-state query
    raise NotImplementedError("See TODO in engine/zep_client.py get_current_state")


if __name__ == "__main__":
    mcp.run()
