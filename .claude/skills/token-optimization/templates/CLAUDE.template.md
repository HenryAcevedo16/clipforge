@AGENTS.md

## Claude Code specifics

- When a checkpoint says stop, make the checkpoint line the last thing in the reply. When it says continue, note the finished WP in one line and start the next.
- Present options with AskUserQuestion: 2–4 choices, the recommended one first, labelled "(Recommended)".
- Read big docs by section: `grep -n '^## ' <file>`, then Read with offset and limit. If a whole-file read is denied by `.claude/settings.json`, the guard is working: retry with offset/limit.
- After pushing, `gh run watch --exit-status`; on failure, `gh run view --log-failed`.
- Prefer `/clear` with `docs/STATUS.md` as the handoff over `/compact`.
- At each checkpoint run `/usage`: act on its recommendations, check the prompt-cache line (hit rate, miss causes), append the row to `docs/COST.md` and run `scripts/cost_report.py`. Cap sessions with `--max-budget-usd`.
- Statusline: show context size and session cost from the stdin JSON (`cost.total_cost_usd`). It renders client-side, so it costs no tokens.
- Bound output at the source: `BASH_MAX_OUTPUT_LENGTH` (default 30,000 characters) and `MAX_MCP_OUTPUT_TOKENS` (default 25,000). Lower them to your worst useful log; redirect huge logs to a file and grep it.
- If `/usage` shows idle burn, turn off prompt suggestions, idle compaction, unused `/loop` tasks; hold cross-session messages.
- Complex tasks: plan mode first, verification targets in the prompt, `Esc`/`/rewind` at the first wrong turn. Verify in a ladder: touched file → targeted test → one full check; stop at the first failure.
- Agent teams cost ~7× a normal session: keep them small, on Sonnet, with focused spawn prompts, and shut teammates down when done.
