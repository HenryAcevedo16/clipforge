"""Lightweight audience signals used by NovoClip's local highlight ranker.

This module intentionally has no OpenCV, NumPy, FFmpeg or AI dependency so its
interval math can be tested independently.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping


def _valid_intervals(intervals: Iterable) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for item in intervals or ():
        try:
            start, end = float(item[0]), float(item[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if math.isfinite(start) and math.isfinite(end) and end > start:
            out.append((start, end))
    return sorted(out)


def overlap_ratio(start: float, end: float, intervals: Iterable) -> float:
    """Return the fraction of [start, end] covered by the supplied intervals.

    Overlapping input intervals are merged first, so duplicate chat/replay
    signals cannot inflate coverage above 1.0.
    """
    try:
        start, end = float(start), float(end)
    except (TypeError, ValueError):
        return 0.0
    duration = end - start
    if not math.isfinite(start) or not math.isfinite(end) or duration <= 0:
        return 0.0

    clipped = []
    for a, b in _valid_intervals(intervals):
        left, right = max(start, a), min(end, b)
        if right > left:
            clipped.append((left, right))
    if not clipped:
        return 0.0

    clipped.sort()
    covered = 0.0
    left, right = clipped[0]
    for a, b in clipped[1:]:
        if a <= right:
            right = max(right, b)
        else:
            covered += right - left
            left, right = a, b
    covered += right - left
    return min(1.0, max(0.0, covered / duration))


def replay_intervals(heatmap: Iterable[Mapping]) -> list[tuple[float, float]]:
    """Extract unusually replayed sections from yt-dlp's YouTube heatmap.

    A heatmap entry uses start_time, end_time and value. Flat or malformed
    heatmaps produce no signal instead of marking arbitrary parts as popular.
    """
    rows: list[tuple[float, float, float]] = []
    for item in heatmap or ():
        try:
            start = float(item.get("start_time"))
            end = float(item.get("end_time"))
            value = float(item.get("value"))
        except (AttributeError, TypeError, ValueError):
            continue
        if all(math.isfinite(x) for x in (start, end, value)) and end > start:
            rows.append((start, end, value))

    if len(rows) < 4:
        return []
    values = sorted(row[2] for row in rows)
    low, high = values[0], values[-1]
    if high - low < 1e-6:
        return []

    median = (values[(len(values) - 1) // 2] + values[len(values) // 2]) / 2
    q75_index = max(0, min(len(values) - 1, math.ceil(0.75 * len(values)) - 1))
    q75 = values[q75_index]
    threshold = max(q75, median + 0.25 * (high - median))
    if threshold >= high:
        threshold = high

    selected = sorted((a, b) for a, b, value in rows if value >= threshold and value > low)
    if not selected:
        return []

    merged: list[list[float]] = []
    for a, b in selected:
        if merged and a <= merged[-1][1] + 0.25:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]



def audience_bonus(start: float, end: float, chat: Iterable, replay: Iterable) -> tuple[float, list[str]]:
    """Small, capped ranking bonus for audience reactions; never a standalone picker."""
    chat_ratio = overlap_ratio(start, end, chat)
    replay_ratio = overlap_ratio(start, end, replay)
    score = 12.0 * chat_ratio + 8.0 * replay_ratio
    reasons = []
    if chat_ratio >= 0.10:
        reasons.append("pico de actividad en el chat")
    if replay_ratio >= 0.15:
        reasons.append("tramo repetido por la audiencia")
    return score, reasons
