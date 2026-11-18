# Checkpoints: clear or keep

Read this at a checkpoint (see AGENTS.md, directive 3). Only the owner can clear context.

## Cost model

<Agent and model>, <1-hour> cache TTL. Prices checked <YYYY-MM-DD>. Relative to fresh input (1×):
- Cached context costs <0.05×> per request, and every request (each tool round trip) re-reads all of it.
- New tokens are written to the cache once at <2×>, then carried at the read price.
- Output, thinking included, costs 5×.
- After the TTL passes without a request, the next request re-writes the whole context.
- One round trip is not free even when the cache is warm: at 150k of context it costs about <$0.03> on <model>. Merge lookups and batch independent calls.

## The test

Keeping costs read × D per request, where D is the context the next work won't use. Clearing costs write × R once, where R is what the next work must load again plus re-orientation (typically 20–30k tokens). **Clear when D × (requests ahead) > <ratio> × R.**

| Work ahead | Clear when the unused context exceeds about |
|---|---|
| A follow-up (~10 requests) | <100k> |
| A small WP (~50 requests) | <20k> |
| A full WP (100+ requests) | <10k> |

- Measure R with the skill's `clear_or_keep.py --measure docs/STATUS.md docs/ROADMAP.md:M<n>`: it sums the actual files (bytes ÷ 4) and adds re-orientation. A guessed R makes the thresholds meaningless.
- When the next WP reuses most of what is loaded, D is small and keeping usually wins.
- Cold cache (idle longer than the TTL): clear unless most of the context is still needed.
- Cost is the objective; correctness is a constraint. Keep when the next WP depends on details STATUS.md can't carry, because rework costs more; clear when a long context starts to blur details.
- Mid-WP: apply the test only when quality slips or the owner will be away longer than the TTL. Make `docs/STATUS.md` carry the state before stopping.
- Keep R small: a tight `docs/STATUS.md` (≤ 40 lines), the doc map and one roadmap section make each clear cheap.
- Break the cache rarely, all at once: change MCPs/plugins/skills, fast mode or entry files only right after a clear; each change re-writes the cache from that point on.
- Append-only: corrections go forward, not into earlier turns. Clear when you are about to work; clearing then reloading and walking away wastes the write.
- TTL: 5-minute writes cost 1.25× and 1-hour writes 2×. With no pause over 5 minutes, 5m is cheaper; after one expiry, 1h wins. A cache hit refreshes the TTL for free.

## The ledger

At every checkpoint append one row to `docs/COST.md` (from `templates/COST.template.md`): requests, prompt tokens, cached share, output, dollars and the decision. Take the numbers from `/usage`. Cost per completed WP, not per session, is the metric; a WP at twice the median is a leak. Run `scripts/cost_report.py` for median, p75, trend and outliers.

## Checkpoint lines

End the reply with one of these, with the measured session numbers:
- `✅ Checkpoint — /clear recommended (<why>; session: <r> requests, <p>% cached, $<x>). Next: <WP id + title>. After clearing, say "continue".`
- `✅ Checkpoint — keep context (<why>; session: <r> requests, <p>% cached, $<x>). Next: <WP id + title>. Say "continue" within <TTL>; after that, /clear first.`
