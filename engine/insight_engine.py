"""
The actual novel part of this project (see docs/design_doc.md §2).

Zep/Graphiti owns the ground truth of *what changed and when*.
This module owns the reasoning about *what to do about it* --
escalate drilling, retire a resolved confusion, or hold steady --
and writes back a one-line human-readable justification.

TODO:
- Replace the placeholder prompt with one tuned against real seeded
  data (see engine/seed.py) before recording the demo.
- Decide whether InsightLog entries are stored as their own Zep
  episodes (simplest) or derived purely from edge invalidation
  (more elegant, more work) -- see design_doc.md §3.1 for the tradeoff.
"""

import os
from openai import OpenAI

from engine.schema import ConfusionEvent, InsightDecision, InsightLog
from engine.zep_client import get_current_state

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


INSIGHT_PROMPT = """You are a tutoring insight engine. Given the recent history \
of a student's performance on a specific concept-pair, decide one of three \
actions: escalate (confusion is persisting or worsening -- drill more), \
retire (resolved -- stop actively drilling), or no_change (not enough \
signal yet).

Respond in the format:
DECISION: <escalate|retire|no_change>
REASONING: <one sentence, plain language, suitable to show a teacher or the \
student themselves>

Recent history:
{history}
"""


def evaluate(event: ConfusionEvent) -> InsightLog:
    """Given a new confusion event, pull the student's recent state for
    this pair and decide what to do about it."""
    state = get_current_state(event.tenant_id, event.student_ref, event.pair_id)

    # TODO: format `state["recent_facts"]` into a readable history string
    # once get_current_state is actually wired up against Zep.
    history_str = f"Latest event: {'correct' if event.correct else 'incorrect'} " \
                   f"({event.context or 'no context given'})"

    response = get_openai_client().chat.completions.create(
        model="gpt-5.6",
        messages=[
            {"role": "user", "content": INSIGHT_PROMPT.format(history=history_str)}
        ],
    )

    text = response.choices[0].message.content or ""
    decision = InsightDecision.NO_CHANGE
    reasoning = text.strip()

    for line in text.splitlines():
        if line.upper().startswith("DECISION:"):
            raw = line.split(":", 1)[1].strip().lower()
            try:
                decision = InsightDecision(raw)
            except ValueError:
                pass
        if line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    return InsightLog(
        tenant_id=event.tenant_id,
        pair_id=event.pair_id,
        student_ref=event.student_ref,
        decision=decision,
        reasoning=reasoning,
    )
