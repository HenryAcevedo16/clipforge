#!/usr/bin/env python3
"""Deny a whole-file Read of a large file, before its bytes enter context.

A single 2,000-line file can write ~25k tokens and then ride along in every
later request. The fix is to read a line range. Prose in an entry file can be
forgotten; this hook is enforced by the client and costs nothing until it
fires.

Wire it as a `PreToolUse` hook for `Read` (see `templates/settings.template.json`):

    {"type": "command", "command": "python3 .claude/hooks/guard_read.py --max-lines 600"}

It allows any read that already carries `offset` or `limit`, allows small files,
non-Read tools and unreadable paths, and emits one short denial otherwise. The
line limit can also come from `TOKEN_GUARD_MAX_LINES`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_MAX_LINES = 600
DEFAULT_REASON = ("{path} is {lines}+ lines; read a range with offset/limit "
                  "or `sed -n '120,180p' {path}` instead of the whole file.")


def line_count(path: Path, stop_after: int) -> tuple[int, bool] | None:
    """(lines, is_binary) up to `stop_after`; None when the file cannot be read."""
    try:
        with path.open("rb") as handle:
            head = handle.read(4096)
            if b"\0" in head:
                return None
            count = head.count(b"\n")
            while count <= stop_after:
                chunk = handle.read(65_536)
                if not chunk:
                    break
                count += chunk.count(b"\n")
            return count, False
    except OSError:
        return None


def decide(payload: dict, max_lines: int = DEFAULT_MAX_LINES) -> dict | None:
    """The hook's JSON output, or None to let the read proceed."""
    if payload.get("tool_name") != "Read":
        return None
    arguments = payload.get("tool_input")
    if not isinstance(arguments, dict) or arguments.get("offset") is not None or arguments.get("limit") is not None:
        return None
    raw_path = arguments.get("file_path")
    if not isinstance(raw_path, str) or not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_file():
        return None
    counted = line_count(path, max_lines)
    if counted is None or counted[0] <= max_lines:
        return None
    lines = f"{counted[0]:,}" if counted[0] <= max_lines + 65_536 else f">{max_lines:,}"
    reason = DEFAULT_REASON.format(path=raw_path, lines=lines)
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deny whole-file reads of large files.")
    parser.add_argument("--max-lines", type=int,
                        default=int(os.environ.get("TOKEN_GUARD_MAX_LINES", DEFAULT_MAX_LINES)),
                        help=f"files above this need offset/limit; default {DEFAULT_MAX_LINES}")
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    decision = decide(payload if isinstance(payload, dict) else {}, args.max_lines)
    if decision is not None:
        print(json.dumps(decision, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
