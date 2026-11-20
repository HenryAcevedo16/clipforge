"""Tests for source-backed spoken hook excerpts."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from pipeline import _audio_waveform, _line_features, _spoken_quote


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

    def test_does_not_join_words_across_a_long_pause(self):
        words = [
            {"w": "primera", "s": 1.0, "e": 1.3},
            {"w": "segunda", "s": 1.4, "e": 1.7},
            {"w": "después", "s": 3.0, "e": 3.3},
        ]
        self.assertEqual(_spoken_quote(words, 1.0), "primera segunda")


class AudioWaveformTests(unittest.TestCase):
    def test_returns_normalized_audio_peaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.mp4"
            source.touch()
            samples = np.array([0.1, 0.1, 0.9, 0.9], dtype=np.float32)
            result = subprocess.CompletedProcess(["ffmpeg"], 0, samples.tobytes(), b"")
            with patch("pipeline._sp_run", return_value=result):
                waveform = _audio_waveform(source, 0.0, 2.0, bins=2)
        self.assertEqual(len(waveform), 2)
        self.assertAlmostEqual(waveform[1], 1.0)
        self.assertGreater(waveform[0], 0.0)
        self.assertLess(waveform[0], 1.0)

    def test_returns_empty_when_source_is_missing(self):
        self.assertEqual(_audio_waveform(Path("missing-source.mp4"), 0.0, 2.0), [])


class NarrativeFeatureTests(unittest.TestCase):
    def test_detects_an_open_ending(self):
        features = _line_features([{"text": "Y esto pasa porque"}], [0.0])
        self.assertEqual(features[0]["open_end"], 1)

    def test_accepts_a_closed_sentence(self):
        features = _line_features([{"text": "Y esto pasa."}], [0.0])
        self.assertEqual(features[0]["open_end"], 0)


if __name__ == "__main__":
    unittest.main()
