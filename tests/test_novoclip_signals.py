"""Regression tests for audience-aware moment scoring."""

import unittest

from novoclip_signals import audience_bonus, overlap_ratio, replay_intervals


class OverlapRatioTests(unittest.TestCase):
    def test_merges_overlapping_intervals_without_double_counting(self):
        self.assertAlmostEqual(
            overlap_ratio(0, 10, [(0, 5), (3, 8), (8, 11)]),
            0.8,
        )

    def test_clips_intervals_to_candidate_and_ignores_invalid_values(self):
        self.assertAlmostEqual(
            overlap_ratio(5, 15, [(-5, 7), (9, 12), (12, 12), ("bad", 20), (float("nan"), 30)]),
            0.5,
        )

    def test_zero_or_invalid_candidate_duration_has_no_overlap(self):
        self.assertEqual(overlap_ratio(5, 5, [(0, 10)]), 0.0)
        self.assertEqual(overlap_ratio("bad", 10, [(0, 10)]), 0.0)


class ReplayIntervalsTests(unittest.TestCase):
    def test_extracts_and_merges_top_replayed_sections(self):
        heatmap = [
            {"start_time": 0, "end_time": 5, "value": 0.05},
            {"start_time": 5, "end_time": 10, "value": 0.10},
            {"start_time": 10, "end_time": 15, "value": 0.20},
            {"start_time": 15, "end_time": 20, "value": 0.90},
            {"start_time": 20, "end_time": 25, "value": 0.85},
        ]
        self.assertEqual(replay_intervals(heatmap), [(15.0, 25.0)])

    def test_flat_or_too_short_heatmap_produces_no_signal(self):
        flat = [{"start_time": n, "end_time": n + 1, "value": 0.5} for n in range(5)]
        short = [{"start_time": n, "end_time": n + 1, "value": n} for n in range(3)]
        self.assertEqual(replay_intervals(flat), [])
        self.assertEqual(replay_intervals(short), [])

    def test_malformed_points_are_ignored(self):
        heatmap = [
            {"start_time": 0, "end_time": 5, "value": 0.1},
            {"start_time": 5, "end_time": 10, "value": 0.2},
            {"start_time": 10, "end_time": 15, "value": 0.3},
            {"start_time": 15, "end_time": 20, "value": 0.9},
            {"start_time": 20, "end_time": 25, "value": 0.85},
            {"start_time": "oops", "end_time": 30, "value": 1.0},
        ]
        self.assertEqual(replay_intervals(heatmap), [(15.0, 25.0)])


class AudienceBonusTests(unittest.TestCase):
    def test_chat_and_replay_add_bounded_explanations(self):
        score, reasons = audience_bonus(0, 20, [(0, 5)], [(10, 15)])
        self.assertAlmostEqual(score, 5.0)
        self.assertEqual(
            reasons,
            ["pico de actividad en el chat", "tramo repetido por la audiencia"],
        )

    def test_no_audience_signal_does_not_change_score(self):
        self.assertEqual(audience_bonus(0, 20, [], []), (0.0, []))


if __name__ == "__main__":
    unittest.main()
