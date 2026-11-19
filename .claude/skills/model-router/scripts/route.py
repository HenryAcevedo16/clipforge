#!/usr/bin/env python3
"""Deterministic task-to-agent classifier for ClipForge's four-role workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys

AGENTS = {
    "haiku": {"agent": "haiku-worker", "model": "haiku", "effort": "low"},
    "sonnet": {"agent": "sonnet-worker", "model": "sonnet", "effort": "medium"},
    "opus": {"agent": "opus-worker", "model": "opus", "effort": "high"},
    "review": {"agent": "sonnet-reviewer", "model": "sonnet", "effort": "medium"},
}

MECHANICAL = re.compile(
    r"\b(grep|find|search|locate|list|count|rename|reformat|format|convert|"
    r"transcode|extract|parse|deduplicate|dedupe|sort|filter|lint|classify|"
    r"tag|label|summarize logs|inspect logs|find tests|find callers)\b", re.I
)
HARD = re.compile(
    r"\b(architect|architecture|design|redesign|strategy|plan the|planning|"
    r"trade-?off|root cause|debug across|cross-file|multi-file|refactor the "
    r"(system|codebase)|migrat(e|ion)|concurrency|distributed|race condition|"
    r"orchestrat|ambiguous|underspecified|figure out why|why (is|does|isn't)|"
    r"live pipeline|cancellation model)\b", re.I
)
REVIEW = re.compile(
    r"\b(code[ -]?review|security[ -]?review|review(ing)? (this|the|my|our)\b"
    r"[^.]{0,50}\b(pr|pull request|diff|branch|change|patch|code|commit|file|work)s?"
    r"|review the diff|review the changes|review this diff|security audit|"
    r"threat ?model|vulnerability assessment)\b", re.I
)
REVIEW_FOLLOWUP = re.compile(
    r"\b(apply|implement|fix|address|resolve|respond to) (the |these |those |all )?"
    r"(\w+ )?(review|findings|comments|feedback)\b", re.I
)
HIGH_RISK = re.compile(
    r"\b(security|credential|secret|auth|permission|path traversal|"
    r"data loss|production migration|irreversible|privacy)\b", re.I
)


def route(
    task: str,
    files_touched: int = 0,
    est_input_tokens: int = 0,
    prior_failures: int = 0,
    irreversible: bool = False,
) -> dict:
    """Return the recommended agent, model alias, effort and routing reasons."""
    text = task or ""
    reasons: list[str] = []
    is_review = bool(REVIEW.search(text)) and not REVIEW_FOLLOWUP.search(text)

    if is_review:
        tier = "review"
        reasons.append("independent diff review -> Sonnet Reviewer")
    else:
        tier = "sonnet"
        reasons.append("default implementation -> Sonnet Developer")
        small = files_touched <= 1 and est_input_tokens <= 8000
        if MECHANICAL.search(text) and small and not HARD.search(text):
            tier = "haiku"
            reasons.append("bounded mechanical task with clear verification -> Haiku Investigator")

        if HARD.search(text):
            tier = "opus"
            reasons.append("architectural or root-cause reasoning -> Opus Architect")
        if files_touched >= 6:
            tier = "opus"
            reasons.append(f"wide scope ({files_touched} files) -> Opus Architect")
        if irreversible or HIGH_RISK.search(text):
            tier = "opus"
            reasons.append("high-impact or sensitive change -> Opus assessment")

    if prior_failures > 0:
        if tier in ("haiku", "review"):
            tier = "sonnet"
            reasons.append("escalated to Sonnet after a failed lower-cost attempt")
        elif tier == "sonnet":
            tier = "opus"
            reasons.append("escalated to Opus after a failed Sonnet attempt")

    selected = AGENTS[tier]
    return {
        "tier": tier,
        "agent": selected["agent"],
        "model_cc": selected["model"],
        "effort": selected["effort"],
        "reasons": reasons,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Route a ClipForge task to its Claude Code agent.")
    parser.add_argument("task", help="task description")
    parser.add_argument("--files", type=int, default=0, help="estimated number of files affected")
    parser.add_argument("--tokens", type=int, default=0, help="estimated input tokens")
    parser.add_argument("--prior-failures", type=int, default=0, help="failed lower-tier attempts")
    parser.add_argument("--irreversible", action="store_true", help="high-cost or irreversible change")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    result = route(args.task, args.files, args.tokens, args.prior_failures, args.irreversible)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"agent={result['agent']} model={result['model_cc']} "
            f"effort={result['effort']} tier={result['tier']}"
        )
        for reason in result["reasons"]:
            print(f"  - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
