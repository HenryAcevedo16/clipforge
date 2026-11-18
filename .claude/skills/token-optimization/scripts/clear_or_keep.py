#!/usr/bin/env python3
"""Decide whether to /clear or keep an agent's context, using prompt-cache prices.

Keeping carries the context the next work won't use (D) through the requests
ahead (c) at the cache-read price. Clearing reloads what the next work needs,
plus re-orientation (R), at the cache-write price, once. Costs are in
fresh-input-token equivalents so they compare across models; dollar figures
use the model's base input price.

    clear_or_keep.py --unused 60k --reload 25k --requests 100 --next "M0.3 Web skeleton"
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from prices import MODELS, WRITE_MULTIPLIERS

TTL_LABELS = {"5m": "5 min", "1h": "1 h"}
DEFAULT_REORIENT = 10_000
DEFAULT_RELOAD = 25_000

_TOKENS = re.compile(r"^([0-9][0-9_,]*(?:\.[0-9]+)?)([km]?)$", re.IGNORECASE)


@dataclass(frozen=True)
class Verdict:
    keep_cost: float  # fresh-input-token equivalents
    clear_cost: float
    ratio: float  # write multiplier / read multiplier
    break_even_requests: float | None  # None when the cache is cold or nothing is unused
    clear: bool


def parse_tokens(text: str) -> int:
    """Parse '60k', '1.5M', '25,000' or '25000' into a token count."""
    match = _TOKENS.match(text.strip())
    if not match:
        raise ValueError(f"not a token count: {text!r} (use e.g. 60k, 1.5M or 25000)")
    number = float(match.group(1).replace("_", "").replace(",", ""))
    return round(number * {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()])


def fmt_tokens(n: float) -> str:
    """Format a token count compactly: 950, 7.5k, 350k, 1.5M."""
    if n >= 999_500:
        value, suffix = n / 1_000_000, "M"
    elif n >= 1_000:
        value, suffix = n / 1_000, "k"
    else:
        return str(round(n))
    text = f"{value:.0f}" if value >= 100 else f"{value:.1f}".rstrip("0").rstrip(".")
    return text + suffix


def fmt_usd(amount: float) -> str:
    return "<$0.01" if amount < 0.01 else f"${amount:.2f}"


def estimate_tokens(text: str) -> int:
    """About 4 characters per token, measured in UTF-8 bytes."""
    return max(1, round(len(text.encode("utf-8")) / 4))


def section_text(text: str, section: str) -> str:
    """The text of the `## <section>` block, up to the next `## ` heading."""
    lines = text.splitlines(keepends=True)
    heading = re.compile(rf"^##\s+{re.escape(section)}(?:\s|$)")
    start = None
    for index, line in enumerate(lines):
        if heading.match(line.rstrip("\r\n")):
            start = index
            break
    if start is None:
        raise ValueError(f"section {section!r} not found")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^##\s", lines[i])), len(lines))
    return "".join(lines[start:end])


def measure_spec(spec: str) -> dict:
    """Tokens in a file, or in one `## section` of it: `FILE` or `FILE:SECTION`."""
    path, section = Path(spec), None
    if ":" in spec:
        head, tail = spec.rsplit(":", 1)
        if Path(head).is_file() and re.fullmatch(r"[A-Za-z0-9._#-]+", tail):
            path, section = Path(head), tail
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        raise ValueError(f"cannot read {path}: {err.strerror or err}") from None
    if section:
        text = section_text(text, section)
    return {"spec": spec, "path": str(path), "section": section, "tokens": estimate_tokens(text)}


def decide(unused, reload, requests, read_mult, write_mult, cold=False, reorient=DEFAULT_REORIENT) -> Verdict:
    """Compare carrying `unused` tokens for `requests` more requests with reloading `reload` tokens."""
    for name, value in (("unused", unused), ("reload", reload), ("requests", requests), ("reorient", reorient)):
        if value < 0:
            raise ValueError(f"{name} must not be negative")
    if read_mult <= 0 or write_mult <= 0:
        raise ValueError("price multipliers must be positive")
    carry = read_mult * unused * requests
    if cold:
        # Everything is re-written either way; only the unused part and re-orientation differ.
        keep, clear, break_even = write_mult * unused + carry, write_mult * min(reorient, reload), None
    else:
        keep, clear = carry, write_mult * reload
        break_even = clear / (read_mult * unused) if unused else None
    return Verdict(keep, clear, write_mult / read_mult, break_even, clear < keep)


def checkpoint_line(verdict: Verdict, unused, requests, ttl, cold, next_task, usd, session=None) -> str:
    scope = "cache expired" if cold else f"~{requests} requests ahead"
    measured = f"; session: {session}" if session else ""
    if verdict.clear:
        saving = fmt_usd(usd(verdict.keep_cost - verdict.clear_cost))
        why = f"~{fmt_tokens(unused)} unused, {scope}; saves ~{saving}{measured}"
        return f'✅ Checkpoint — /clear recommended ({why}). Next: {next_task}. After clearing, say "continue".'
    extra = fmt_usd(usd(verdict.clear_cost - verdict.keep_cost))
    why = f"~{fmt_tokens(unused)} unused, {scope}; clearing costs ~{extra} more{measured}"
    return (f"✅ Checkpoint — keep context ({why}). Next: {next_task}. "
            f'Say "continue" within {TTL_LABELS[ttl]}; after that, /clear first.')


def report(args, verdict: Verdict, read_mult, write_mult, usd, reload, measured, details) -> str:
    def cost(equivalents):
        return f"{fmt_tokens(equivalents)} input-token equivalents ({fmt_usd(usd(equivalents))})"

    unused = fmt_tokens(args.unused)
    lines = [f"Model {args.model} · TTL {TTL_LABELS[args.ttl]}{' (expired)' if args.cold else ''} · "
             f"cache read {read_mult:g}× · write {write_mult:g}× · ratio {verdict.ratio:g}"]
    if details:
        listed = ", ".join(f"{item['spec']} ~{fmt_tokens(item['tokens'])}" for item in details)
        lines.append(f"Reload measured: {fmt_tokens(measured)} ({listed}) + "
                     f"{fmt_tokens(args.reorient)} re-orientation = {fmt_tokens(reload)}")
    if args.cold:
        lines.append(f"Keep:  {write_mult:g} × {unused} unused re-written + "
                     f"{read_mult:g} × {unused} × {args.requests} requests = {cost(verdict.keep_cost)}")
        reorient = fmt_tokens(min(args.reorient, reload))
        lines.append(f"Clear: {write_mult:g} × {reorient} re-orientation = {cost(verdict.clear_cost)}")
    else:
        lines.append(f"Keep:  {read_mult:g} × {unused} unused × {args.requests} requests = {cost(verdict.keep_cost)}")
        lines.append(f"Clear: {write_mult:g} × {fmt_tokens(reload)} reload = {cost(verdict.clear_cost)}")
        if verdict.break_even_requests is not None:
            lines.append(f"Break-even: {math.ceil(verdict.break_even_requests)} requests")
    saving = abs(verdict.keep_cost - verdict.clear_cost)
    lines.append(f"Verdict: {'/clear' if verdict.clear else 'keep'}, saving ~{cost(saving)}")
    lines.append("Cost is the objective; correctness is a constraint. Keep when a handoff can't carry the detail, because rework costs more.")
    return "\n".join(lines)


def _tokens_arg(text: str) -> int:
    try:
        return parse_tokens(text)
    except ValueError as err:
        raise argparse.ArgumentTypeError(str(err)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decide whether to /clear or keep an agent's context, using prompt-cache prices.")
    add = parser.add_argument
    add("--unused", required=True, type=_tokens_arg, help="context the next work won't use (D), e.g. 60k")
    add("--reload", type=_tokens_arg, default=None,
        help="tokens to load again after a clear, plus re-orientation (R); default 25k or as measured by --measure")
    add("--measure", action="extend", nargs="+", default=[], metavar="FILE[:SECTION]",
        help="measure R from files and `## SECTION`s instead of guessing (one or more); adds --reorient")
    add("--requests", type=int, default=100, help="requests ahead (c); a full work package takes 100+; default 100")
    add("--model", choices=sorted(MODELS), default="opus-5.5", help="price preset; default opus-5.5")
    add("--ttl", choices=sorted(WRITE_MULTIPLIERS), default="1h", help="cache TTL; default 1h")
    add("--read-mult", type=float, help="override the cache-read multiplier")
    add("--write-mult", type=float, help="override the cache-write multiplier")
    add("--cold", action="store_true", help="the cache has expired (idle longer than the TTL)")
    add("--reorient", type=_tokens_arg, default=DEFAULT_REORIENT,
        help="re-orientation tokens: added to --measure and used with --cold; default 10k")
    add("--next", dest="next_task", default="<task>", help="the next task, for the checkpoint line")
    add("--session", help="measured session summary for the checkpoint line, "
                        "e.g. '61 requests, 58%% cached, $1.84'")
    add("--json", action="store_true", help="print JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    default_read, input_price = MODELS[args.model]
    read_mult = default_read if args.read_mult is None else args.read_mult
    write_mult = WRITE_MULTIPLIERS[args.ttl] if args.write_mult is None else args.write_mult
    if args.reload is not None and args.measure:
        parser.error("use either --reload or --measure, not both")
    details = []
    for spec in args.measure:
        try:
            details.append(measure_spec(spec))
        except ValueError as err:
            parser.error(str(err))
    measured = sum(item["tokens"] for item in details)
    if args.reload is not None:
        reload = args.reload
    elif args.measure:
        reload = measured + args.reorient
    else:
        reload = DEFAULT_RELOAD
    try:
        verdict = decide(args.unused, reload, args.requests, read_mult, write_mult, args.cold, args.reorient)
    except ValueError as err:
        parser.error(str(err))

    def usd(equivalents: float) -> float:
        return equivalents * input_price / 1_000_000

    line = checkpoint_line(verdict, args.unused, args.requests, args.ttl, args.cold, args.next_task, usd,
                           args.session)
    if args.json:
        print(json.dumps({
            "verdict": "clear" if verdict.clear else "keep",
            "model": args.model,
            "ttl": args.ttl,
            "cold": args.cold,
            "read_multiplier": read_mult,
            "write_multiplier": write_mult,
            "ratio": verdict.ratio,
            "unused": args.unused,
            "reload": reload,
            "measured_reload": measured,
            "measure": details,
            "requests": args.requests,
            "session": args.session,
            "keep_cost": verdict.keep_cost,
            "clear_cost": verdict.clear_cost,
            "keep_usd": round(usd(verdict.keep_cost), 4),
            "clear_usd": round(usd(verdict.clear_cost), 4),
            "break_even_requests": verdict.break_even_requests,
            "checkpoint_line": line,
        }, ensure_ascii=False, indent=2))
    else:
        print(report(args, verdict, read_mult, write_mult, usd, reload, measured, details))
        print()
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
