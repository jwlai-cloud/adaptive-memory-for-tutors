"""GPT-powered pedagogical decisions over Zep's student event timeline.

Zep/Graphiti remains the source of truth for events and temporal facts.  This
module makes the separate, auditable decision about what a tutor should do.
"""

import json
import os
from datetime import timezone
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from engine.schema import ConfusionEvent, InsightDecision, InsightLog
from engine.zep_client import get_current_state, log_insight

_client: OpenAI | None = None
_HISTORY_LIMIT = 8
# Luna is sufficient for the tightly constrained three-way classification and
# keeps demo iteration inexpensive; set INSIGHT_MODEL=gpt-5.6-terra or
# gpt-5.6-sol if later evaluation quality calls for a stronger tier.
INSIGHT_MODEL = os.environ.get("INSIGHT_MODEL", "gpt-5.6-luna")


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Add it to .env or export it "
                "before evaluating tutoring insights."
            )
        _client = OpenAI(api_key=api_key)
    return _client


INSIGHT_PROMPT = """You are an auditable tutoring insight engine.

Classify the student's current state for one concept pair using only the
chronological event history. Return exactly one decision and one sentence of
plain-language reasoning suitable for a teacher or student.

Decision rules:
- retire: the student has a clear recent correct streak after earlier
  mistakes, showing resolution. Require at least three consecutive recent
  correct answers, with no newer mistake.
- escalate: incorrect answers are still persistent or worsening (for example,
  at least two of the final three answers are incorrect).
- no_change: the evidence is mixed or insufficient for either action.

Do not claim a trend that is not present in the history. Keep reasoning to one
sentence and mention the relevant outcome trend.
"""

_INSIGHT_SCHEMA = {
    "name": "tutoring_insight",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "decision": {
                "type": "string",
                "enum": [decision.value for decision in InsightDecision],
            },
            "reasoning": {"type": "string", "minLength": 1},
        },
        "required": ["decision", "reasoning"],
    },
}


def format_history(recent_facts: list[dict[str, Any]]) -> str:
    """Format the last source episodes in chronological order for GPT-5.6."""
    if not recent_facts:
        return "No recorded attempts are available for this concept pair."

    lines = []
    for index, fact in enumerate(recent_facts[-_HISTORY_LIMIT:], start=1):
        outcome = "correct" if fact.get("correct") is True else "incorrect"
        timestamp = fact.get("timestamp", "unknown time")
        context = fact.get("context") or "no context recorded"
        lines.append(f"{index}. {timestamp}: {outcome} — {context}")
    return "\n".join(lines)


def _timestamp_for_prompt(event: ConfusionEvent) -> str:
    timestamp = event.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _history_with_current_event(
    recent_facts: list[dict[str, Any]], event: ConfusionEvent
) -> list[dict[str, Any]]:
    """Include the triggering event when Zep's episode listing is still catching up."""
    current = {
        "timestamp": _timestamp_for_prompt(event),
        "correct": event.correct,
        "context": event.context,
    }
    current_key = (current["timestamp"], current["correct"], current["context"])
    existing_keys = {
        (fact.get("timestamp"), fact.get("correct"), fact.get("context"))
        for fact in recent_facts
    }
    if current_key not in existing_keys:
        recent_facts = [*recent_facts, current]
    return sorted(recent_facts, key=lambda fact: fact.get("timestamp", ""))


def _parse_insight(content: str) -> tuple[InsightDecision, str]:
    """Validate the structured model response before returning it to callers."""
    try:
        parsed = json.loads(content)
        decision = InsightDecision(parsed["decision"])
        reasoning = str(parsed["reasoning"]).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("GPT-5.6 returned an invalid tutoring insight response") from exc
    if not reasoning:
        raise RuntimeError("GPT-5.6 returned an empty tutoring insight reasoning")
    return decision, reasoning


def evaluate(event: ConfusionEvent) -> InsightLog:
    """Evaluate the student's latest state and persist the resulting insight."""
    state = get_current_state(event.tenant_id, event.student_ref, event.pair_id)
    recent_facts = _history_with_current_event(state["recent_facts"], event)
    history_str = format_history(recent_facts)
    response = get_openai_client().chat.completions.create(
        model=INSIGHT_MODEL,
        messages=[
            {"role": "system", "content": INSIGHT_PROMPT},
            {"role": "user", "content": f"Concept pair: {event.pair_id}\n\nHistory:\n{history_str}"},
        ],
        response_format={"type": "json_schema", "json_schema": _INSIGHT_SCHEMA},
    )
    content = response.choices[0].message.content or ""
    decision, reasoning = _parse_insight(content)
    insight = InsightLog(
        tenant_id=event.tenant_id,
        pair_id=event.pair_id,
        student_ref=event.student_ref,
        decision=decision,
        reasoning=reasoning,
    )

    # Insights are separate Zep episodes: the demo needs an auditable insight
    # feed, and keeping decisions separate from observations preserves the
    # distinction between Graphiti's ground truth and our reasoning layer.
    log_insight(insight)
    return insight
