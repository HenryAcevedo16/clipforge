#!/usr/bin/env python3
"""Lint the context a repo loads on every request.

Checks the invariants from references/repo-setup.md: the entry file and its
imports stay under a token budget, STATUS.md stays short, large docs are
navigable by section, no section is a wall of text, every referenced path and
relative link exists, duplicate prose is flagged, imports are one level deep
and docs/MAP.md is fresh. Prints only problems and a summary, so CI stays quiet.

    lint_context.py --root . --strict
    lint_context.py --entry AGENTS.md --status docs/STATUS.md --docs docs --map docs/MAP.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ENTRY = "AGENTS.md"
DEFAULT_STATUS = "docs/STATUS.md"
DEFAULT_DOCS = "docs"
DEFAULT_MAP = "docs/MAP.md"
DEFAULT_MAX_ENTRY_TOKENS = 5_000
DEFAULT_MAX_STATUS_LINES = 40
DEFAULT_MAX_DOC_LINES = 300
DEFAULT_MAX_SECTION_LINES = 120
DEFAULT_MIN_DUPLICATE_CHARS = 240
MIN_DOC_SECTIONS = 3

IMPORT = re.compile(r"^@(\S+)\s*$")
BACKTICK = re.compile(r"`([^`]+)`")
PATH_EXT = re.compile(r"\.(md|mdx|markdown|py|sh|json|toml|ya?ml|rs|ts|tsx|js|go|txt)$")
HEADING = re.compile(r"^##\s")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = ("```", "~~~")


def estimate_tokens(text: str) -> int:
    """About 4 characters per token, measured in UTF-8 bytes."""
    return max(1, round(len(text.encode("utf-8")) / 4))


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def imports(text: str) -> list[str]:
    return [match.group(1) for line in text.splitlines()
            if (match := IMPORT.match(line.strip()))]


def heading_count(text: str) -> int:
    """`##` headings outside fenced code blocks."""
    fenced = False
    count = 0
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and HEADING.match(line):
            count += 1
    return count


def sections(text: str) -> list[tuple[str, int, int]]:
    """`##` sections as (title, start_line, end_line), 1-based and end-exclusive."""
    found = []
    current: tuple[str, int] | None = None
    fenced = False
    lines = text.splitlines()
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if line.startswith(FENCE):
            fenced = not fenced
            continue
        if fenced or not line.startswith("## "):
            continue
        if current:
            found.append((current[0], current[1], number))
        current = (line[3:].strip().rstrip("#").strip(), number)
    if current:
        found.append((current[0], current[1], len(lines) + 1))
    return found


def path_token(token: str) -> str | None:
    """A backticked path, with a `:SECTION` or `:LINE` suffix removed; None otherwise."""
    token = token.strip().rstrip(".,;:")
    if token.startswith(("http://", "https://", "mailto:")):
        return None
    if ":" in token:
        head, _, tail = token.partition(":")
        if re.fullmatch(r"[A-Za-z0-9._#<>-]+", tail) and ("/" in head or PATH_EXT.search(head)):
            token = head
    if not token or " " in token or any(ch in token for ch in "<>{}$*~|`@"):
        return None
    if "/" not in token and not PATH_EXT.search(token):
        return None
    return token


def document_paths(text: str) -> list[str]:
    """Backticked paths anywhere in a doc, outside fenced code blocks."""
    found = []
    fenced = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(FENCE):
            fenced = not fenced
            continue
        if fenced:
            continue
        for token in BACKTICK.findall(line):
            cleaned = path_token(token)
            if cleaned:
                found.append(cleaned)
    return found


def relative_links(text: str) -> list[str]:
    """Local Markdown link targets, with any anchor or query removed."""
    found = []
    for match in LINK.finditer(text):
        target = match.group(1).strip()
        if target.startswith(("#", "http://", "https://", "mailto:")) or target.startswith("/"):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        if target:
            found.append(target)
    return found


def paragraphs(text: str) -> list[str]:
    """Paragraphs outside fenced code, joined with single spaces."""
    found = []
    buffer: list[str] = []
    fenced = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(FENCE):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line:
            buffer.append(line)
        elif buffer:
            found.append(" ".join(buffer))
            buffer = []
    if buffer:
        found.append(" ".join(buffer))
    return found


def duplicate_paragraphs(docs: list[tuple[str, str]], min_chars: int) -> list[tuple[str, str, int]]:
    """(doc, earlier doc, characters) for prose copied between docs."""
    seen: dict[str, str] = {}
    found = []
    for relative, text in docs:
        for paragraph in paragraphs(text):
            normalized = re.sub(r"\s+", " ", paragraph).strip()
            if len(normalized) < min_chars or normalized.count(" ") < 25:
                continue
            if normalized.startswith(("|", "#", "- ", "* ")):
                continue
            earlier = seen.get(normalized)
            if earlier and earlier != relative:
                found.append((relative, earlier, len(normalized)))
            else:
                seen.setdefault(normalized, relative)
    return found


def referenced_paths(lines: list[str]) -> list[str]:
    """Backticked paths in doc-map rows, bullets and numbered steps."""
    found = []
    for line in lines:
        stripped = line.strip()
        if not (stripped.startswith("|") or stripped.startswith("- ") or re.match(r"^\d+\.\s", stripped)):
            continue
        for token in BACKTICK.findall(line):
            token = token.strip().rstrip(".,;:")
            if not token or " " in token or "://" in token:
                continue
            if any(ch in token for ch in "<>{}$*~|"):
                continue
            if "/" not in token and not PATH_EXT.search(token):
                continue
            found.append(token)
    return found


def check(root: Path, args) -> tuple[list[str], list[str], int]:
    """Return (problems, warnings, checks run)."""
    problems: list[str] = []
    warnings: list[str] = []
    checks = 0

    entry_path = root / args.entry
    entry_text = read(entry_path)
    if entry_text is None:
        warnings.append(f"no entry file at {args.entry} (see references/repo-setup.md)")
    else:
        checks += 1
        loaded = estimate_tokens(entry_text)
        for target in imports(entry_text):
            imported = (entry_path.parent / target).resolve()
            text = read(imported)
            if text is None:
                problems.append(f"{args.entry}: imported file not found: {target}")
                continue
            loaded += estimate_tokens(text)
            nested = imports(text)
            if nested:
                problems.append(f"{target}: imports {len(nested)} more file(s); "
                                "keep @ imports one level deep")
        if loaded > args.max_entry_tokens:
            problems.append(f"{args.entry}: ~{loaded:,} tokens always loaded "
                            f"(limit {args.max_entry_tokens:,}); move detail into on-demand docs")
        for token in referenced_paths(entry_text.splitlines()):
            if not (root / token).exists():
                problems.append(f"{args.entry}: referenced path does not exist: {token}")

    status_text = read(root / args.status)
    if status_text is None:
        warnings.append(f"no handoff file at {args.status}")
    else:
        checks += 1
        count = len(status_text.splitlines())
        if count > args.max_status_lines:
            problems.append(f"{args.status}: {count} lines (limit {args.max_status_lines}); "
                            "a large reload makes every clear expensive")
        for token in referenced_paths(status_text.splitlines()):
            if not (root / token).exists():
                problems.append(f"{args.status}: referenced path does not exist: {token}")

    docs = root / args.docs
    map_path = (root / args.map).resolve()
    if not docs.is_dir():
        warnings.append(f"no docs directory at {args.docs}")
    else:
        doc_texts = []
        for path in sorted(docs.rglob("*.md")):
            if path.resolve() == map_path:
                continue
            text = read(path)
            if text is None:
                continue
            checks += 1
            relative = path.relative_to(root).as_posix()
            doc_texts.append((relative, text))
            count = len(text.splitlines())
            if count > args.max_doc_lines and heading_count(text) < MIN_DOC_SECTIONS:
                problems.append(f"{relative}: {count} lines with fewer than {MIN_DOC_SECTIONS} "
                                "`##` sections; split it or add sections so it can be read by range")
            if args.max_section_lines:
                for title, start, end in sections(text):
                    length = end - start
                    if length > args.max_section_lines:
                        problems.append(f"{relative}: section `{title}` is {length} lines "
                                        f"(limit {args.max_section_lines}); split it so one read stays small")
            for token in document_paths(text):
                if not (root / token).exists():
                    problems.append(f"{relative}: referenced path does not exist: {token}")
            for target in relative_links(text):
                if not (path.parent / target).resolve().exists():
                    problems.append(f"{relative}: link target does not exist: {target}")
        if args.min_duplicate_chars:
            for relative, earlier, size in duplicate_paragraphs(doc_texts, args.min_duplicate_chars):
                warnings.append(f"{relative}: duplicate paragraph also in {earlier} "
                                f"(~{size / 4:.0f} tokens); link to one copy instead")

    current = read(map_path)
    if current is None:
        warnings.append(f"no code map at {args.map}; generate it with gen_map.py")
    else:
        checks += 1
        try:
            from gen_map import build_map
        except ImportError:
            warnings.append("gen_map.py not found next to lint_context.py; skipped the map check")
        else:
            if build_map(root, map_path) != current:
                problems.append(f"{args.map}: stale; regenerate with gen_map.py --out {args.map}")

    if args.strict:
        problems.extend(warnings)
        warnings = []
    return problems, warnings, checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint the context a repo loads on every request.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root; default: current directory")
    parser.add_argument("--entry", default=DEFAULT_ENTRY,
                        help=f"always-loaded entry file; default {DEFAULT_ENTRY}")
    parser.add_argument("--status", default=DEFAULT_STATUS, help=f"handoff file; default {DEFAULT_STATUS}")
    parser.add_argument("--docs", default=DEFAULT_DOCS, help=f"docs directory; default {DEFAULT_DOCS}")
    parser.add_argument("--map", default=DEFAULT_MAP, help=f"generated code map; default {DEFAULT_MAP}")
    parser.add_argument("--max-entry-tokens", type=int, default=DEFAULT_MAX_ENTRY_TOKENS,
                        help=f"entry file plus imports token budget; default {DEFAULT_MAX_ENTRY_TOKENS}")
    parser.add_argument("--max-status-lines", type=int, default=DEFAULT_MAX_STATUS_LINES,
                        help=f"STATUS.md line limit; default {DEFAULT_MAX_STATUS_LINES}")
    parser.add_argument("--max-doc-lines", type=int, default=DEFAULT_MAX_DOC_LINES,
                        help=f"docs above this need >= {MIN_DOC_SECTIONS} `##` sections; "
                             f"default {DEFAULT_MAX_DOC_LINES}")
    parser.add_argument("--max-section-lines", type=int, default=DEFAULT_MAX_SECTION_LINES,
                        help=f"maximum lines in one `##` section; 0 disables; "
                             f"default {DEFAULT_MAX_SECTION_LINES}")
    parser.add_argument("--min-duplicate-chars", type=int, default=DEFAULT_MIN_DUPLICATE_CHARS,
                        help=f"flag prose at least this long copied between docs; 0 disables; "
                             f"default {DEFAULT_MIN_DUPLICATE_CHARS}")
    parser.add_argument("--strict", action="store_true",
                        help="treat missing files and skipped checks as failures (for CI)")
    args = parser.parse_args(argv)

    problems, warnings, checks = check(args.root.resolve(), args)
    for message in problems:
        print(f"FAIL {message}")
    for message in warnings:
        print(f"WARN {message}")
    print(f"context lint: {len(problems)} problem(s), {len(warnings)} warning(s), {checks} check(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
