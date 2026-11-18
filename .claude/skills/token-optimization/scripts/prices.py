#!/usr/bin/env python3
"""One source of truth for prices, and the generated cost-model table.

Prices live in `prices.json`. `clear_or_keep.py` imports `MODELS` and
`WRITE_MULTIPLIERS` from here, and `--doc` rewrites the table between the
`<!-- prices:start -->` and `<!-- prices:end -->` markers in
`references/cost-model.md`. `--check` fails when the doc is stale, so CI
catches a price edit that was not propagated.

    prices.py --table          # print the Markdown table
    prices.py --doc            # regenerate the table in cost-model.md
    prices.py --check          # exit 1 if the doc table is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "prices.json"
DOC = HERE.parent / "references" / "cost-model.md"
START = "<!-- prices:start -->"
END = "<!-- prices:end -->"
COLUMNS = ("Model", "Input", "5-min write", "1-hour write", "Cache read", "Output", "Read ÷ input")


def load(path: Path = DATA) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        raise SystemExit(f"cannot read {path}: {err.strerror or err}") from None
    except ValueError as err:
        raise SystemExit(f"{path}: invalid JSON: {err}") from None
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        raise SystemExit(f"{path}: no models")
    return data


PRICES = load()
MODELS = {name: (entry["read"] / entry["input"], float(entry["input"]))
          for name, entry in PRICES["models"].items()}
WRITE_MULTIPLIERS = {name: float(value) for name, value in PRICES["ttl_write_multipliers"].items()}
PRICE_DATE = PRICES["checked"]
PRICE_SOURCE = PRICES["source"]


def fmt_price(value: float) -> str:
    """10, 12.5, 0.125, 0.01: no trailing zeros, no gratuitous decimals."""
    return f"{value:.3f}".rstrip("0").rstrip(".")


def table() -> str:
    rows = [f"| {' | '.join(COLUMNS)} |", "|" + "---|" * len(COLUMNS)]
    for entry in sorted(PRICES["models"].values(), key=lambda item: (-item["input"], item["label"])):
        read_ratio = entry["read"] / entry["input"]
        rows.append("| " + " | ".join((
            entry["label"], fmt_price(entry["input"]), fmt_price(entry["write_5m"]),
            fmt_price(entry["write_1h"]), fmt_price(entry["read"]), fmt_price(entry["output"]),
            fmt_price(read_ratio),
        )) + " |")
    return "\n".join(rows)


def replace_table(text: str) -> str:
    start, end = text.find(START), text.find(END)
    if start < 0 or end < 0 or end < start:
        raise SystemExit(f"{DOC}: missing {START} / {END} markers")
    return text[: start + len(START)] + "\n" + table() + "\n" + text[end:]


def check(path: Path = DOC) -> tuple[bool, str]:
    try:
        current = path.read_text(encoding="utf-8")
    except OSError as err:
        return False, f"cannot read {path}: {err.strerror or err}"
    return replace_table(current) == current, f"{path}: price table is stale; run prices.py --doc"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Single-source prices and the cost-model table.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--table", action="store_true", help="print the Markdown table")
    group.add_argument("--doc", action="store_true", help="rewrite the table in cost-model.md")
    group.add_argument("--check", action="store_true", help="exit 1 if cost-model.md is stale")
    parser.add_argument("--path", type=Path, default=DOC, help=f"doc to read or write; default {DOC}")
    args = parser.parse_args(argv)
    if args.table:
        print(table())
    elif args.doc:
        args.path.write_text(replace_table(args.path.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        fresh, message = check(args.path)
        if not fresh:
            print(message, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
