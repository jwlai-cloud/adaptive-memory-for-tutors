import unittest

from engine.insight_engine import _has_sustained_resolution


class InsightMasteryRuleTests(unittest.TestCase):
    def test_requires_three_final_correct_attempts(self) -> None:
        self.assertFalse(_has_sustained_resolution([{"correct": True}, {"correct": True}]))
        self.assertFalse(
            _has_sustained_resolution(
                [{"correct": True}, {"correct": False}, {"correct": True}, {"correct": True}]
            )
        )
        self.assertTrue(
            _has_sustained_resolution(
                [{"correct": False}, {"correct": True}, {"correct": True}, {"correct": True}]
            )
        )
