#!/usr/bin/env python3
"""Print the context a fresh session needs, in one tool call.

The reload after a clear is `STATUS.md`, one roadmap section and the doc map.
Reading them one at a time costs several requests, and every request re-sends
the whole context. This prints the same material in one call.

    start.py
    start.py --root .. --status docs/STATUS.md --roadmap docs/ROADMAP.md --entry AGENTS.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

MILESTONE = re.compile(r"\*\*Milestone:\*\*\s*([A-Za-z0-9._-]+)")
NEXT_WP = re.compile(r"\*\*Next WP:\*\*\s*([A-Za-z0-9._-]+)")
MAJOR = re.compile(r"^(M[0-9]+)")
HEADING = re.compile(r"^##\s")


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def milestone_id(status: str) -> str | None:
    """The milestone named by STATUS.md, else the major part of the next WP."""
    for pattern in (MILESTONE, NEXT_WP):
        match = pattern.search(status)
        if match:
            return match.group(1)
    return None


def section(text: str, ident: str) -> str | None:
    """The `## <ident>` block of a document, up to the next `## ` heading."""
    lines = text.splitlines()
    pattern = re.compile(rf"^##\s+{re.escape(ident)}(?:\s|$)")
    start = next((i for i, line in enumerate(lines) if pattern.match(line)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if HEADING.match(lines[i])), len(lines))
    return "\n".join(lines[start:end]).rstrip()


def current_section(roadmap: str, ident: str) -> tuple[str, str] | None:
    """The named section, falling back from `M1.2` to `M1` when only the milestone exists."""
    found = section(roadmap, ident)
    if found is None:
        major = MAJOR.match(ident)
        if major and major.group(1) != ident:
            ident = major.group(1)
            found = section(roadmap, ident)
    return (ident, found) if found is not None else None


def doc_map(entry: str, limit: int = 12) -> list[str]:
    rows = [line.rstrip() for line in entry.splitlines()
            if line.lstrip().startswith("|") and "---" not in line]
    return rows[:limit]


def cap(text: str, limit: int) -> str:
    lines = text.splitlines()
    if len(lines) <= limit:
        return text.rstrip()
    return "\n".join(lines[:limit]).rstrip() + f"\n... ({len(lines) - limit} more lines)"


def render(root: Path, status: str, roadmap: str, entry: str, limit: int = 100) -> str:
    out = []
    status_text = read(root / status)
    if status_text is None:
        out.append(f"(no {status})")
    else:
        out.extend([f"=== {status} ===", cap(status_text, limit)])

    ident = milestone_id(status_text) if status_text else None
    if ident:
        roadmap_text = read(root / roadmap)
        if roadmap_text is None:
            out.append(f"(no {roadmap})")
        else:
            found = current_section(roadmap_text, ident)
            if found is None:
                out.append(f"(no `## {ident}` section in {roadmap})")
            else:
                label, body = found
                out.extend([f"=== {roadmap} §{label} ===", cap(body, limit)])

    entry_text = read(root / entry)
    if entry_text is None:
        out.append(f"(no {entry})")
    else:
        rows = doc_map(entry_text)
        if rows:
            out.extend([f"=== {entry} · doc map ===", "\n".join(rows)])

    return "\n\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print STATUS, the current roadmap section and the doc map in one call.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root; default: current directory")
    parser.add_argument("--status", default="docs/STATUS.md", help="handoff file; default docs/STATUS.md")
    parser.add_argument("--roadmap", default="docs/ROADMAP.md", help="roadmap file; default docs/ROADMAP.md")
    parser.add_argument("--entry", default="AGENTS.md", help="entry file with the doc map; default AGENTS.md")
    parser.add_argument("--max-lines", type=int, default=100,
                        help="lines to print per file or section; default 100")
    args = parser.parse_args(argv)
    print(render(args.root, args.status, args.roadmap, args.entry, args.max_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
