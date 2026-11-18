# AGENTS.md

Entry point for AI agents working on **<project>**. Every request carries this file, so it stays short; read everything else on demand.

<One paragraph: what the project is, its stack, and the repo URL.>

## Standing directives (from the owner; always apply)

1. **Smallest high impact:** the least output — reply, edit, file, command — that fully meets the goal and proves it. Cut what doesn't change the result; never cut what acceptance needs.
2. **Cost is the objective; correctness and safety are hard constraints.** Never ship wrong code to save tokens; never spend tokens that don't improve the result.
3. **Checkpoint after each WP** (done, docs updated, committed, pushed, CI green). Decide clear or keep with `docs/CHECKPOINTS.md`, append the WP row to `docs/COST.md`, then <continue into the next WP if keeping wins | stop either way> and end with its checkpoint line. Only the owner can clear.
4. **Offer options:** 2–4 with a recommended default; record the outcome in `docs/DECISIONS.md`. Decide small, reversible details yourself and note them.
5. **Keep docs true:** update them in the same commit as the change that would make them stale.
6. **Commit every significant change** (Conventional Commits) and keep `main` green.
7. **Stop at green:** once `<check command>` passes and the WP's criteria are met, stop. Put opportunistic work in ROADMAP.md's `## Later` list; no unrequested cleanup or extra tests.

## Session protocol

1. **Start:** run `python3 scripts/start.py` (STATUS.md, the current milestone and the doc map in one call), then only the docs the WP lists.
2. **Locate** with `docs/MAP.md` and grep; read a module's contract (header comment) before its code, and large files by line range.
3. **Work** on one WP at a time, tests alongside the code. Verify in a ladder: touched file → targeted test → one full check at the finish. If it outgrows the session, split it in ROADMAP.md and checkpoint.
4. **Finish:** `<check command>` → tick ROADMAP.md → rewrite `docs/STATUS.md` (≤ 40 lines) → append the WP row to `docs/COST.md` → run `scripts/cost_report.py` → commit → push → CI green → checkpoint (directive 3).

## Token rules

- Never read <lockfiles, generated code, build output, data files, snapshots unless reviewing them>.
- Quiet commands: `<check command>`, `<failures-only test command>`, `gh run view --log-failed`.
- One call, not five: merge independent lookups into one shell command and batch tool calls. Don't re-read what is in context and unchanged. Write new files in one pass; edit existing ones.
- Source files ≤ ~400 lines, one concept each; extend through data (one small file per addition).
- Enforce what you can: permissions and hooks (`.claude/settings.json`), not prose. The entry file keeps judgment rules only.
- Reusable artifacts (plans, reviews, specs) go to a file; the reply is a five-line summary.
- Command sheet: `<build>` · `<one test>` · `<lint one file>` · `<run>` · `<map>`.

## Doc map (read on demand)

| Need | Read |
|---|---|
| Where we are, what's next | `docs/STATUS.md` |
| Work packages, acceptance criteria | `docs/ROADMAP.md` (one milestone) |
| Decisions, open options | `docs/DECISIONS.md` |
| What the last WPs cost | `docs/COST.md` |
| Clear or keep at a checkpoint | `docs/CHECKPOINTS.md` |
| Where code lives | `docs/MAP.md` (generated) |
| <need> | <doc> |

## Definition of done (per WP)

Acceptance criteria met · tests added, `<check command>` green · ROADMAP ticked, STATUS rewritten · decisions recorded · cost row added · committed and pushed · CI green · checkpoint made · stopped at green.
