import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from engine.zep_client import _event_from_episode, _parse_zep_timestamp


class ZepEpisodeTimestampTests(unittest.TestCase):
    def test_normalizes_datetime_fallback_to_iso_string(self) -> None:
        episode = SimpleNamespace(
            metadata={"event_type": "confusion_event", "pair_id": "pair-1"},
            content=json.dumps(
                {
                    "event_type": "confusion_event",
                    "correct": True,
                    "context": "correct response",
                }
            ),
            created_at=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
            uuid_="episode-1",
        )

        event = _event_from_episode(episode, "pair-1")

        self.assertIsNotNone(event)
        self.assertEqual(event["timestamp"], "2026-07-17T12:00:00Z")
        self.assertEqual(
            _parse_zep_timestamp(event["timestamp"]),
            datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
        )

    def test_rejects_non_boolean_correctness_values(self) -> None:
        episode = SimpleNamespace(
            metadata={"event_type": "confusion_event", "pair_id": "pair-1"},
            content=json.dumps(
                {
                    "event_type": "confusion_event",
                    "correct": "true",
                    "context": "malformed third-party event",
                }
            ),
            created_at=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
            uuid_="episode-2",
        )

        self.assertIsNone(_event_from_episode(episode, "pair-1"))
