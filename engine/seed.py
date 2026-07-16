"""
Generates synthetic practice history for a demo student, so the demo UI
opens already "knowing" the student instead of requiring 3 real weeks
of use.

IMPORTANT -- credit safety guard (see docs/design_doc.md §6.2 and
docs/handover_doc.md §5): Zep's free tier bills per episode written.
If this script gets re-run accidentally on every dev-server reload
while iterating with Codex, it will silently burn through free-tier
credits for no reason. The guard below writes a local marker file and
refuses to re-seed the same (tenant, student, domain) combo unless
--force is passed explicitly.

Usage:
    python -m engine.seed --student demo-student-1 --domain japanese-kana
    python -m engine.seed --student demo-student-1 --domain japanese-kana --force
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine.schema import ConfusionEvent
from engine.zep_client import log_event

MARKER_DIR = Path(".seed-markers")


def _marker_path(tenant_id: str, student_ref: str, domain: str) -> Path:
    MARKER_DIR.mkdir(exist_ok=True)
    return MARKER_DIR / f"{tenant_id}__{student_ref}__{domain}.seeded"


def _load_domain_seed(domain: str) -> dict:
    path = Path("seed-data") / f"domain-{domain}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No seed data found for domain '{domain}' at {path}. "
            f"Add one under seed-data/ following the existing format."
        )
    return json.loads(path.read_text())


def seed_student(tenant_id: str, student_ref: str, domain: str, force: bool = False) -> None:
    marker = _marker_path(tenant_id, student_ref, domain)
    if marker.exists() and not force:
        print(
            f"Already seeded {tenant_id}/{student_ref}/{domain} "
            f"(marker: {marker}). Pass --force to re-seed and consume "
            f"more Zep credits intentionally."
        )
        sys.exit(0)

    domain_seed = _load_domain_seed(domain)
    now = datetime.now(timezone.utc)

    events_written = 0
    for pair in domain_seed["pairs"]:
        for i, outcome in enumerate(pair["synthetic_history"]):
            event = ConfusionEvent(
                tenant_id=tenant_id,
                pair_id=pair["id"],
                student_ref=student_ref,
                timestamp=now - timedelta(days=(len(pair["synthetic_history"]) - i) * 2),
                correct=outcome["correct"],
                context=outcome.get("context"),
            )
            log_event(event)
            events_written += 1

    marker.write_text(datetime.now(timezone.utc).isoformat())
    print(f"Seeded {events_written} events for {student_ref} in domain '{domain}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default=os.environ.get("DEFAULT_TENANT_ID", "demo-school"))
    parser.add_argument("--student", required=True)
    parser.add_argument("--domain", required=True, help="e.g. japanese-kana, chemistry-notation")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    seed_student(args.tenant, args.student, args.domain, force=args.force)
