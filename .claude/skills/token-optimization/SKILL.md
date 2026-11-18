---
name: token-optimization
description: Cuts tokens and cost per task in Claude Code: smallest high-impact output, progressive loading, batching, cache-aware /clear-or-keep checkpoints, a cost ledger, and a cheap repo setup. Use when saving tokens or cost, when context grows long, at a checkpoint, or when setting up or auditing a repo for agent work.
license: MIT OR Apache-2.0
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)
---

# Token optimization

Goal: the lowest cost per completed task. Correctness and safety are constraints, not competing objectives; a wrong answer is the most expensive outcome.

**Prerogative: smallest high impact.** Every output — reply, edit, file, command — is the least that fully meets the goal and proves it. Impact per token, not brevity for its own sake: cut what does not change the result, never what the task needs. Ask "what is the smallest thing that makes this true?", do that, and stop.

Read only what the task needs:

| Task | Also read |
|---|---|
| Working rules, checkpoints | nothing: both are below |
| Exact prices, cache invalidation, /compact, subagent maths | [references/cost-model.md](references/cost-model.md) |
| Quiet commands per ecosystem | [references/reading-playbook.md](references/reading-playbook.md) |
| Task briefs, output caps, stop-at-green | [references/prompt-patterns.md](references/prompt-patterns.md) |
| Set up or audit a repo | [references/repo-setup.md](references/repo-setup.md), then the [templates/](templates/) it names |

## Why

Every request re-sends the whole context. Relative to fresh input: cached context costs 0.025–0.1× on *every* request, new context costs 1.25× (5-min TTL) or 2× (1-hour TTL) once, and output, thinking included, costs 5×. After the TTL passes, everything is written again. So: keep what enters small, make fewer round trips, write less, and don't reload what you already carry. At 150k, one extra round trip costs about $0.03 on Opus 5.5; 100 requests cost $3 in reads. A 10k tool output costs 2×10k to write and 0.05×10k×100 to carry: 70k equivalents over a 100-request WP, not 20k.

## Rules

1. **Load progressively:** entry file (automatic) → `STATUS.md` → the current roadmap section → only the docs it names.
2. **Locate before reading:** code map → module contract (header comment) → `grep -n` → a line range. For a long doc, `grep -n '^## ' FILE` and read one section.
3. **Skip bulky files:** lockfiles, generated code, build output, vendored data, snapshots (unless reviewing them).
4. **Quiet commands:** failures-only tests, summarized checks, `gh run view --log-failed`; cap with `head`, `tail`, `cut -c1-200`, `--stat`, `jq`. Grep a saved large output instead of reading it. Check paths and quoting *before* running a command: a failed call's error enters context at the write price, and so does the retry. If a hook or permission can enforce a rule, put it there; prose in an entry file is paid on every request.
5. **Batch and merge:** independent tool calls in one message; merge lookups into one shell call (`sed -n '40,80p;210,240p' FILE`); parallelize only when every result is needed.
6. **Don't re-read** what is in context and unchanged, including files you just wrote or edited.
7. **Write less:** new files in one pass, targeted edits to existing ones, short replies that don't echo tool output, diffs or file contents. Output that will be reused goes to a file, not the transcript; reply with a five-line summary. Match thinking effort to the task.
8. **Look facts up once:** fetch with an extraction prompt or a page's `.md` version, record the result with date and source (e.g. DECISIONS.md), and cite the record afterwards.
9. **Decide once, ask once:** put every open question in one batched message (2–4 options, recommended default first); record the outcome; never reopen it without the owner. Each round trip re-reads the whole context.
10. **Subagents start cold:** use one only when it keeps far more out of the main context than its run costs. Cap the return (~40 lines, `file:line`, no code dumps).
11. **Break the cache rarely, and all at once:** changing tools, plugins, skills, fast mode or an entry file re-writes the cache from that point on. Bundle them right after a `/clear`, never mid-session.
12. **No idle burn:** scheduled loops, cross-session messages, goal check-ins and idle compaction each re-send the full context on a timer. Turn off what you don't use.
13. **Avoid rework:** plan first, stop at the first wrong turn, do the uncertain part first on a thin slice, and stop at green. Opportunistic work goes on the roadmap's Later list.
14. **Verify in a ladder:** touched file → targeted test → one full check at the end. Stop at the first failure and quarantine flaky tests; a retry is another full-context request.

## Checkpoints: clear or keep

Only the user can run `/clear`. At a natural boundary (task done, docs updated, committed and pushed):

- **D** = context the next work won't use. **R** = what it must reload after a clear plus re-orientation. **c** = requests ahead (a full WP is 100+). Clear when **D × c > ratio × R**.
- **Keep R small:** a tight `STATUS.md` (≤ 40 lines), the doc map and one roadmap section make each clear cheap. Measure it:
  `python3 ${CLAUDE_SKILL_DIR}/scripts/clear_or_keep.py --unused 60k --requests 100 --measure docs/STATUS.md docs/ROADMAP.md:M<n> [--model M] [--ttl 5m] [--cold] [--next '<task>'] [--session '<usage>']`
  It sums the real files (bytes ÷ 4), adds re-orientation, and prints the checkpoint line. Exact ratios and thresholds are in [references/cost-model.md](references/cost-model.md) and `CHECKPOINTS.md`.
- **Measure the session:** at each checkpoint run `/usage`, act on its recommendations, append the WP row to `docs/COST.md`, and pass `--session '61 requests, 58% cached, $1.84'`. Cost per completed WP is the metric; `cost_report.py` gives median, p75 and outliers.
- **TTL:** 5m writes cost 1.25× and 1h writes 2×; with no pause over 5 minutes the 5m TTL wins, and one expiry makes 1h win. A hit refreshes it for free.
- **Cold cache** (idle longer than the TTL): clear unless most of the context is still needed.
- **Cost is the objective; correctness is a constraint.** Keep when the next task needs details a handoff cannot carry, because rework costs more. Clear when a long context blurs details.
- **Before any clear,** rewrite `STATUS.md`, commit and push. Prefer `/clear` + `STATUS.md` to `/compact`. Make prefix-breaking changes (tools, entry files, fast mode) right after a clear, never mid-session.
- **Mid-task,** apply the test only when quality slips or the user will be away longer than the TTL.

End the reply with one of these. When keeping and the repo's directives say to continue, carry on instead.
- `✅ Checkpoint — /clear recommended (<why>; session: <r> requests, <p>% cached, $<x>). Next: <task>. After clearing, say "continue".`
- `✅ Checkpoint — keep context (<why>; session: <r> requests, <p>% cached, $<x>). Next: <task>. Say "continue" within <TTL>; after that, /clear first.`
