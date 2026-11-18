#!/usr/bin/env python3
"""Audit one Claude Code transcript JSONL for the leaks a repo check cannot see.

Reads a session export (`--path session.jsonl`, or `-` for stdin) and reports
where the prompt tokens went: requests, cache read/write/input, output, hit
rate, estimated cost, tool calls, the files read most, re-reads, and the largest
number of tool calls in one turn. The schema is best-effort: it accepts usage
under `message.usage` or `usage`, and `Read` paths under `file_path` or `path`.

    audit_transcript.py session.jsonl
    audit_transcript.py session.jsonl --model sonnet-5.5 --ttl 5m
    zcat transcript.jsonl.gz | audit_transcript.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from prices import MODELS, WRITE_MULTIPLIERS

DEFAULT_MODEL = "opus-5.5"
DEFAULT_TTL = "1h"


@dataclass
class Usage:
    input: int = 0
    creation: int = 0
    read: int = 0
    output: int = 0

    @property
    def prompt(self) -> int:
        return self.input + self.creation + self.read

    def add(self, other: "Usage") -> None:
        self.input += other.input
        self.creation += other.creation
        self.read += other.read
        self.output += other.output


@dataclass
class Audit:
    requests: int = 0
    usage: Usage = None  # type: ignore[assignment]
    tools: Counter = None  # type: ignore[assignment]
    files: Counter = None  # type: ignore[assignment]
    turns: int = 0
    max_turn_tools: int = 0
    turn_tools: int = 0

    def __post_init__(self) -> None:
        self.usage = Usage()
        self.tools = Counter()
        self.files = Counter()


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def usage_of(payload: dict) -> Usage | None:
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    usage = message.get("usage") or payload.get("usage")
    if not isinstance(usage, dict) or not usage:
        return None
    creation = usage.get("cache_creation_input_tokens")
    if creation is None:
        creation = usage.get("cache_creation")
        if isinstance(creation, dict):
            creation = sum(_int(value) for value in creation.values())
    return Usage(
        input=_int(usage.get("input_tokens")),
        creation=_int(creation),
        read=_int(usage.get("cache_read_input_tokens")),
        output=_int(usage.get("output_tokens")),
    )


def parse(text: str) -> Audit:
    audit = Audit()
    for line in text.splitlines():
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        usage = usage_of(payload)
        if usage is not None:
            audit.requests += 1
            audit.usage.add(usage)
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = str(block.get("name") or "unknown")
                audit.tools[name] += 1
                audit.turn_tools += 1
                if name == "Read":
                    arguments = block.get("input") if isinstance(block.get("input"), dict) else {}
                    path = arguments.get("file_path") or arguments.get("path")
                    if isinstance(path, str) and path:
                        audit.files[path] += 1
        if payload.get("type") == "user":
            audit.turns += 1
            audit.max_turn_tools = max(audit.max_turn_tools, audit.turn_tools)
            audit.turn_tools = 0
    audit.max_turn_tools = max(audit.max_turn_tools, audit.turn_tools)
    return audit


def cost_of(usage: Usage, model: str, ttl: str) -> float:
    read_mult, input_price = MODELS[model]
    write_mult = WRITE_MULTIPLIERS[ttl]
    equivalents = (usage.input + write_mult * usage.creation + read_mult * usage.read
                   + 5 * usage.output)
    return equivalents * input_price / 1_000_000


def fmt_tokens(n: float) -> str:
    if n >= 999_500:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0k", "k")
    return str(round(n))


def render(audit: Audit, model: str, ttl: str, top: int) -> str:
    usage = audit.usage
    hit = usage.read / usage.prompt if usage.prompt else 0
    lines = [f"transcript: {audit.requests} requests · prompt {fmt_tokens(usage.prompt)} "
             f"(input {fmt_tokens(usage.input)}, write {fmt_tokens(usage.creation)}, "
             f"read {fmt_tokens(usage.read)}) · {hit:.0%} cached · output {fmt_tokens(usage.output)}"]
    lines.append(f"cost: ${cost_of(usage, model, ttl):.2f} at {model} / {ttl} TTL")
    lines.append(f"turns: {audit.turns} user turns · max {audit.max_turn_tools} tool calls in one turn · "
                 f"avg {sum(audit.tools.values()) / audit.turns:.1f}" if audit.turns else
                 "turns: no user turns found")
    lines.append("tools: " + (", ".join(f"{name} {count}" for name, count in audit.tools.most_common(top))
                              or "none"))
    rereads = sum(count - 1 for count in audit.files.values() if count > 1)
    lines.append(f"files read: {len(audit.files)} unique · {rereads} re-reads")
    for path, count in audit.files.most_common(top):
        lines.append(f"  {count}× {path}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a Claude Code transcript JSONL for token leaks.")
    parser.add_argument("path", help="transcript JSONL, or - for stdin")
    parser.add_argument("--model", choices=sorted(MODELS), default=DEFAULT_MODEL,
                        help=f"price preset; default {DEFAULT_MODEL}")
    parser.add_argument("--ttl", choices=sorted(WRITE_MULTIPLIERS), default=DEFAULT_TTL,
                        help=f"cache TTL; default {DEFAULT_TTL}")
    parser.add_argument("--top", type=int, default=10, help="tools and files to list; default 10")
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--max-cost", type=float, metavar="USD",
                        help="exit 1 when the estimated cost exceeds this")
    args = parser.parse_args(argv)
    try:
        text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")
    except OSError as err:
        print(f"cannot read {args.path}: {err.strerror or err}", file=sys.stderr)
        return 1
    audit = parse(text)
    if not audit.requests:
        print(f"{args.path}: no usage records found", file=sys.stderr)
        return 1
    cost = cost_of(audit.usage, args.model, args.ttl)
    if args.json:
        print(json.dumps({
            "requests": audit.requests,
            "usage": asdict(audit.usage),
            "cache_hit": audit.usage.read / audit.usage.prompt if audit.usage.prompt else 0,
            "cost_usd": round(cost, 4),
            "model": args.model,
            "ttl": args.ttl,
            "turns": audit.turns,
            "max_turn_tools": audit.max_turn_tools,
            "tools": dict(audit.tools),
            "files": dict(audit.files),
        }, ensure_ascii=False, indent=2))
    else:
        print(render(audit, args.model, args.ttl, args.top))
    if args.max_cost is not None and cost > args.max_cost:
        print(f"estimated cost ${cost:.2f} exceeds the ${args.max_cost:.2f} budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
