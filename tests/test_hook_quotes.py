"""Tests for source-backed spoken hook excerpts."""

import unittest

from pipeline import _line_features, _spoken_quote


class SpokenQuoteTests(unittest.TestCase):
    def test_extracts_real_words_in_source_time_order(self):
        words = [
            {"w": "final", "s": 6.2, "e": 6.5},
            {"w": "primera", "s": 1.0, "e": 1.3},
            {"w": "segunda", "s": 1.4, "e": 1.8},
            {"w": "tercera", "s": 1.9, "e": 2.2},
        ]
        self.assertEqual(_spoken_quote(words, 1.0), "primera segunda tercera")

    def test_limits_excerpt_to_seven_words(self):
        words = [
            {"w": f"palabra{i}", "s": i * 0.3, "e": i * 0.3 + 0.2}
            for i in range(12)
        ]
        self.assertEqual(
            _spoken_quote(words, 0.0),
            "palabra0 palabra1 palabra2 palabra3 palabra4 palabra5 palabra6",
        )

    def test_returns_empty_when_no_transcribed_words_near_start(self):
        words = [{"w": "lejos", "s": 20.0, "e": 20.4}]
        self.assertEqual(_spoken_quote(words, 0.0), "")


class NarrativeFeatureTests(unittest.TestCase):
    def test_detects_an_open_ending(self):
        features = _line_features([{"text": "Y esto pasa porque"}], [0.0])
        self.assertEqual(features[0]["open_end"], 1)

    def test_accepts_a_closed_sentence(self):
        features = _line_features([{"text": "Y esto pasa."}], [0.0])
        self.assertEqual(features[0]["open_end"], 0)


if __name__ == "__main__":
    unittest.main()
