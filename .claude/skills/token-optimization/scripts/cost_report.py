#!/usr/bin/env python3
"""Turn the cost ledger into a trend: median, p75 and the expensive outliers.

`docs/COST.md` is written one row per work package. A raw table hides the
signal; this prints the few numbers that change a decision: cost per completed
WP, the recent trend, the cache-hit trend, and anything at more than twice the
median. Point it at the ledger at each checkpoint, or run it in CI with
`--max-median` as a budget.

    cost_report.py
    cost_report.py --path docs/COST.md --max-median 2.50
    cost_report.py --json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PATH = Path("docs/COST.md")
_NUMBER = re.compile(r"^\s*\$?\s*([0-9][0-9_,]*(?:\.[0-9]+)?)\s*([kmb]?)", re.IGNORECASE)
_SUFFIX = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


@dataclass(frozen=True)
class Row:
    wp: str
    cost: float
    requests: int | None = None
    prompt: int | None = None
    cached: float | None = None
    output: int | None = None
    decision: str = ""


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _number(text: str) -> float | None:
    match = _NUMBER.match(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "").replace("_", ""))
    return value * _SUFFIX[match.group(2).lower()]


def _column(header: list[str], *names: str) -> int | None:
    for index, cell in enumerate(header):
        normal = re.sub(r"[^a-z0-9% ]", "", cell.lower())
        if any(name == normal or name in normal for name in names):
            return index
    return None


def parse_table(text: str) -> list[Row]:
    """Rows from the first Markdown table that has a WP and a cost column."""
    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        header = _cells(line)
        if _column(header, "cost") is not None and _column(header, "wp", "work package") is not None:
            header_index = index
            break
    if header_index is None:
        return []
    header = [re.sub(r"\s+", " ", cell.lower()) for cell in _cells(lines[header_index])]
    columns = {
        "wp": _column(header, "wp", "work package"),
        "cost": _column(header, "cost"),
        "requests": _column(header, "request"),
        "prompt": _column(header, "prompt"),
        "cached": _column(header, "cached", "cache"),
        "output": _column(header, "output"),
        "decision": _column(header, "decision"),
    }
    rows = []
    for line in lines[header_index + 1:]:
        if not line.strip().startswith("|"):
            break
        cells = _cells(line)
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if any("<" in cell or ">" in cell for cell in cells):
            continue
        cost = _number(cells[columns["cost"]]) if columns["cost"] is not None and columns["cost"] < len(cells) else None
        if cost is None:
            continue

        def value(name: str):
            index = columns[name]
            return cells[index] if index is not None and index < len(cells) else ""

        cached_text = value("cached")
        cached = _number(cached_text.rstrip("%")) if cached_text else None
        rows.append(Row(
            wp=value("wp") or f"row {len(rows) + 1}",
            cost=cost,
            requests=int(_number(value("requests"))) if _number(value("requests")) is not None else None,
            prompt=int(_number(value("prompt"))) if _number(value("prompt")) is not None else None,
            cached=cached,
            output=int(_number(value("output"))) if _number(value("output")) is not None else None,
            decision=value("decision"),
        ))
    return rows


def percentile(values: list[float], share: float) -> float:
    """Nearest-rank percentile: p75 of 12 values is the 9th smallest."""
    ordered = sorted(values)
    index = max(0, math.ceil(share * len(ordered)) - 1)
    return ordered[index]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _window(rows: list[Row], field: str, size: int = 5) -> tuple[float, float] | None:
    values = [getattr(row, field) for row in rows if getattr(row, field) is not None]
    if len(values) < 2 * size:
        return None
    return _mean(values[-size:]), _mean(values[-2 * size:-size])


def summarize(rows: list[Row]) -> dict:
    costs = [row.cost for row in rows]
    median = _median(costs)
    cache_rows = [row for row in rows if row.cached is not None]
    cost_window = _window(rows, "cost")
    cache_window = _window(cache_rows, "cached")
    outliers = [row for row in rows if median and row.cost > 2 * median]
    return {
        "count": len(rows),
        "total": sum(costs),
        "median": median,
        "p75": percentile(costs, 0.75),
        "mean": _mean(costs),
        "cost_window": cost_window,
        "cache_window": cache_window,
        "outliers": outliers,
        "costliest": max(rows, key=lambda row: row.cost),
        "cheapest": min(rows, key=lambda row: row.cost),
        "cache_average": _mean([row.cached for row in cache_rows]) if cache_rows else None,
    }


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _delta(last: float, prior: float, points: bool = False) -> str:
    if points:
        change = last - prior
        return f"{change:+.0f} pts"
    if prior == 0:
        return "n/a"
    return f"{(last - prior) / prior * 100:+.0f}%"


def render(data: dict, path: Path) -> str:
    lines = [f"{path}: {data['count']} WPs · ${data['total']:.2f} total · "
             f"median ${data['median']:.2f}/WP · p75 ${data['p75']:.2f}"]
    if data["cost_window"]:
        last, prior = data["cost_window"]
        lines.append(f"Trend: last 5 ${last:.2f}/WP vs prior 5 ${prior:.2f} ({_delta(last, prior)})")
    else:
        lines.append("Trend: needs at least 10 WPs with costs")
    if data["cache_window"]:
        last, prior = data["cache_window"]
        lines.append(f"Cache: last 5 {last:.0f}% vs prior 5 {prior:.0f}% ({_delta(last, prior, points=True)}); "
                     f"overall {data['cache_average']:.0f}%")
    else:
        lines.append("Cache: not enough cached% rows")
    if data["outliers"]:
        listed = ", ".join(f"{row.wp} ${row.cost:.2f} ({row.cost / data['median']:.1f}×)"
                           for row in data["outliers"][:5])
        lines.append(f"Outliers (>2× median): {listed}")
    else:
        lines.append("Outliers (>2× median): none")
    lines.append(f"Costliest: {data['costliest'].wp} ${data['costliest'].cost:.2f} · "
                 f"cheapest: {data['cheapest'].wp} ${data['cheapest'].cost:.2f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize docs/COST.md: median, p75, trend, outliers.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH, help=f"ledger; default {DEFAULT_PATH}")
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--max-median", type=float, metavar="USD",
                        help="exit 1 when the median cost per WP exceeds this (a CI budget)")
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8")
    except OSError as err:
        print(f"cannot read {args.path}: {err.strerror or err}", file=sys.stderr)
        return 1
    rows = parse_table(text)
    if not rows:
        print(f"{args.path}: no cost rows; add the table from templates/COST.template.md", file=sys.stderr)
        return 1
    data = summarize(rows)
    if args.json:
        print(json.dumps({
            **{key: value for key, value in data.items()
               if key not in ("outliers", "costliest", "cheapest", "cost_window", "cache_window")},
            "cost_window": list(data["cost_window"]) if data["cost_window"] else None,
            "cache_window": list(data["cache_window"]) if data["cache_window"] else None,
            "outliers": [asdict(row) for row in data["outliers"]],
            "costliest": asdict(data["costliest"]),
            "cheapest": asdict(data["cheapest"]),
            "rows": [asdict(row) for row in rows],
        }, ensure_ascii=False, indent=2))
    else:
        print(render(data, args.path))
    if args.max_median is not None and data["median"] > args.max_median:
        print(f"median ${data['median']:.2f}/WP exceeds the ${args.max_median:.2f} budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
