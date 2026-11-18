# Cost ledger

One row per work package, appended at its checkpoint (AGENTS.md, directive 3). It is the only way to tell whether the token rules are paying off.

Read it as a trend: **cost per completed WP**, not per session. A WP at more than twice the median means a leak — a stale map, a grown entry file, rework, or an unusually large reload.

| Date | WP | Model | Requests | Prompt tokens | Cached | Output | Cost | Decision |
|---|---|---|---|---|---|---|---|---|
| <YYYY-MM-DD> | M0.1 | <model> | 61 | 2.4M | 58% | 28k | $1.84 | /clear |

- Take the numbers from `/usage` (or a statusline) at the checkpoint. Prompt tokens are `input + cache_creation + cache_read`.
- Run `scripts/cost_report.py --path docs/COST.md` to get median, p75, the last-five trend, the cache trend and outliers; add `--max-median` in CI as a budget.
- `Cost` and `cost per WP` are the metrics. Keep the last ~20 rows here and archive older ones.
- Note a one-off in the WP column (`M0.1 (rework)`), so a bad week does not look like a bad rule.
- Give each WP a dollar budget. Exceeding it usually means the WP was too big; split it next time.
