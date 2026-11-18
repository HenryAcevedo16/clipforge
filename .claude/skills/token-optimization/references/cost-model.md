# Cost model

Prices live in `scripts/prices.json`; the table below is generated from it. Edit that file, then run `python3 scripts/prices.py --doc`. CI runs `--check`, so the doc cannot drift from the calculator. Checked 2026-10-22 at https://platform.claude.com/docs/en/about-claude/pricing.

Cost is the objective; correctness is a constraint. The rules below follow from one fact: every request re-sends the whole context.

## Contents
- Prices
- How a session is billed
- What a request costs
- The lifetime of a tool output
- Choosing the TTL
- What invalidates the cache
- Cache mechanics that bite
- Cache habits
- The clear-or-keep test
- Measuring a session
- Worked example
- /compact versus /clear
- Subagents
- Fixed per-request overhead

## Prices (USD per million tokens)

<!-- prices:start -->
| Model | Input | 5-min write | 1-hour write | Cache read | Output | Read ÷ input |
|---|---|---|---|---|---|---|
| Fable 5.1 | 10 | 12.5 | 20 | 0.25 | 50 | 0.025 |
| Opus 4.5 | 5 | 6.25 | 10 | 0.5 | 25 | 0.1 |
| Opus 4.6 | 5 | 6.25 | 10 | 0.5 | 25 | 0.1 |
| Opus 4.7 | 5 | 6.25 | 10 | 0.5 | 25 | 0.1 |
| Opus 4.8 | 5 | 6.25 | 10 | 0.5 | 25 | 0.1 |
| Opus 5 | 5 | 6.25 | 10 | 0.5 | 25 | 0.1 |
| Opus 5.5 | 4 | 5 | 8 | 0.2 | 20 | 0.05 |
| Sonnet 4.5 | 3 | 3.75 | 6 | 0.3 | 15 | 0.1 |
| Sonnet 4.6 | 3 | 3.75 | 6 | 0.3 | 15 | 0.1 |
| Sonnet 5 | 2 | 2.5 | 4 | 0.2 | 10 | 0.1 |
| Sonnet 5.5 | 2 | 2.5 | 4 | 0.1 | 10 | 0.05 |
| Haiku 4.5 | 1 | 1.25 | 2 | 0.1 | 5 | 0.1 |
| Haiku 5.5 | 0.1 | 0.125 | 0.2 | 0.01 | 0.5 | 0.1 |
<!-- prices:end -->

- On every model listed, a 5-minute cache write costs 1.25× input, a 1-hour write costs 2× and output costs 5×.
- Haiku 5.5 prompts over 100k tokens cost 5× the rates above.
- Fast mode (Opus 5.5: $8 input, $40 output) doubles the price. Cache multipliers apply on top of it.

## How a session is billed

- Each request re-sends the whole context. The prefix that hits the cache costs the read price. Everything after the last hit is written to the cache at the write price, or billed as plain input if it isn't cached.
- A cache hit refreshes the entry's TTL for free. The TTL counts from the *start* of a request, so a long generation uses up part of it. Work in bursts inside the TTL window: keep requests flowing, and if a pause longer than the TTL is coming, checkpoint (clear) first.
- Claude Code caches automatically. The sessions this skill was built in (Claude Code on a subscription plan) used the 1-hour TTL, falling back to 5 minutes during usage overage. Check what your setup uses: on the API, `usage.cache_creation` splits writes by TTL.
- Thinking is billed as output. Recent models keep earlier turns' thinking blocks in the prompt, so long thinking is also carried forward like any other context.
- Totals: `input_tokens` is only the uncached remainder. The full prompt is `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.
- **Measure, don't assume.** In Claude Code, `/context` shows the cache breakdown; on the API, watch the `cache_read` share of the full prompt. If it drops mid-session, something in the prefix changed (see the invalidation table) — find and fix it before it compounds across every later request.

## What a request costs

Each request re-sends the whole context, so its size sets the cost of every round trip. On Opus 5.5 (read 0.05×, $4/M input):

| Context | One request | 10 requests | 100 requests |
|---|---|---|---|
| 50k | $0.01 | $0.10 | $1.00 |
| 100k | $0.02 | $0.20 | $2.00 |
| 150k | $0.03 | $0.30 | $3.00 |
| 200k | $0.04 | $0.40 | $4.00 |

- Ten thousand tokens carried for 100 requests cost 0.05 × 10k × 100 = 50k equivalents ($0.20). That is the price of one avoidable section of a doc per work package.
- Merging eight sequential lookups into two calls at 150k saves six round trips, about $0.18. The lookups themselves are cheap; the requests are the cost.
- Parallel calls are not free either. They save round trips, but a speculative read is paid once and then carried; parallelize only when every result will be used.

## The lifetime of a tool output

A write is paid once; the carry is paid every request. For X tokens of tool output over c requests:

`cost = w·X + r·X·c`

On Opus 5.5 (w = 2, r = 0.05), over a 100-request WP:

| Output | Write | Carried | Total | USD |
|---|---|---|---|---|
| 1k | 2k | 5k | 7k | $0.03 |
| 10k | 20k | 50k | 70k | $0.28 |
| 30k | 60k | 150k | 210k | $0.84 |
| 100k | 200k | 500k | 700k | $2.80 |

This is why a 30k dump is not "30k tokens": it is 210k equivalents. Read lazily, filter at the source, and prefer a saved file plus a grep over a full read. A stale doc that causes 20k of exploration costs ~$0.56 the same way.

## Choosing the TTL

A cache write costs 1.25× input on the 5-minute TTL and 2× on the 1-hour TTL. Compare the premium with what it avoids:

- **No pause longer than 5 minutes:** the 5m TTL wins; its only write is 0.75×C cheaper than 1h. A cache hit refreshes the TTL for free, so a steady stream of requests keeps a 5m entry alive indefinitely.
- **One expiry-driven rewrite:** 5m pays 1.25×C twice (2.5×C); 1h pays 2×C and wins. Human-paced work pauses for more than 5 minutes often, so 1h is usually right at a keyboard.
- Continuous automation with no human pauses is the case for 5m; a human-paced session is the case for 1h.

Claude Code picks the TTL for you (1-hour on subscription plans, falling back to 5 minutes during overage), so this matters when the TTL is under your control on the API or through a gateway.

## What invalidates the cache

The cache is a prefix in the order tools → system → messages. A change invalidates its own level and everything after it.

| Change | What is re-written |
|---|---|
| Switching model | everything (caches are per model) |
| Toggling fast mode (speed) | system and messages |
| Changing thinking or effort settings | messages, and more on some models |
| Changing tool definitions (adding/removing an MCP server, plugin or skill) | everything |
| Editing the system prompt or an entry file (AGENTS.md, CLAUDE.md, `@` imports) | system and messages |
| Idling longer than the TTL | everything |

Each change re-writes the cache from its point onward, so bundle every prefix-breaking change — model, speed, effort, tools, entry files — into one burst right after a `/clear`. Never make them one by one partway through a long session: each one makes everything after it a cache miss.

## Cache mechanics that bite

Details from the [prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) that surprise people:

- **The lookback window is 20 blocks.** Cache reads walk back at most 20 positions from the breakpoint looking for an entry a prior request wrote. If a turn adds 20+ blocks, the last write falls out of the window and the next request re-writes everything. A run of consecutive `tool_use` blocks counts as *one* position (same for `tool_result`), so batching independent calls in parallel protects the cache; many small sequential turns erode it.
- **Minimum cacheable length.** Prompts shorter than the model's minimum are silently not cached (no error; both cache usage fields are 0): 512 tokens for Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1; 1,024 for Sonnet 5 and Opus 4.8; 4,096 for Opus 4.5/4.6 and Haiku 4.5. Don't micro-optimize tiny contexts — there is nothing to cache.
- **A cache entry is usable only after the first response starts.** Concurrent requests fired at once can all miss; stagger them if the hits matter.
- **Thinking blocks.** On Opus 4.5+, Sonnet 4.6+ and Haiku 5.5, thinking blocks are preserved and stay in the cached prefix (and count as input when read from cache). On older models, adding any non-tool-result content strips previously cached thinking and invalidates everything after it.
- **Breakpoint placement.** The breakpoint belongs on the last block whose prefix is identical across requests — never on a varying suffix like a timestamp or the incoming message. In a growing conversation the final block works as long as each turn adds fewer than 20 blocks.

**Tracking.** In Claude Code, `/usage` shows a "Prompt cache" line: requests, % of input served from cache, misses (with a likely cause, e.g. "tool definitions changed"), and warm/cold state; `/context` shows the size breakdown. On the API, `cache_read_input_tokens` ÷ (`cache_read` + `cache_creation` + `input`) is your hit rate. A dropping hit rate means a prefix change — find it in the table above.

**Offline bulk work.** The Batch API prices messages at 50% and stacks with the cache multipliers — use it for evals, bulk rewrites and other non-interactive work.

## Cache habits

- **Append-only:** treat the transcript as a log. Corrections go in a new message; `/rewind` only to a prefix that existed. Rewriting earlier turns invalidates the cache from that point.
- **Don't clear, reload, then walk away:** the reload is written at 2×; if you pause past the TTL before using it, that write is wasted. Clear when you are about to work, not before a break.
- **Stagger parallel sessions and subagents** by a second or two: a cache entry is usable only after the first response starts, so the later one can hit the shared base.

## The clear-or-keep test

Symbols:
- D: tokens in context that the next work won't use.
- R: tokens the next work must load again after a clear, plus re-orientation.
- c: requests ahead (each tool round trip is one request).
- r: the read multiplier.
- w: the write multiplier.

The calculation, while the cache is warm:
- Keeping carries D through c requests and costs r·D·c. The part the next work needs is carried either way, so it cancels out.
- Clearing reloads R once and costs w·R.
- Clear when r·D·c > w·R, which is the same as D·c > (w ÷ r)·R.

**Keep R small.** R is the reload after a clear: a tight STATUS.md (≤ 40 lines), the doc map and one roadmap section. The smaller R is, the cheaper every clear is, so clear more readily. A bloated handoff makes keeping look artificially cheap.

| Read multiplier | w ÷ r, 1-hour TTL (w = 2) | w ÷ r, 5-minute TTL (w = 1.25) |
|---|---|---|
| 0.1 (most models) | 20 | 12.5 |
| 0.05 (Opus 5.5, Sonnet 5.5) | 40 | 25 |
| 0.025 (Fable 5.1) | 80 | 50 |

The break-even number of requests is c* = (w ÷ r)·R ÷ D. With a ratio of 40 and R = 25k:

| D | c* |
|---|---|
| 10k | 100 requests |
| 50k | 20 requests |
| 100k | 10 requests |

Read the other way, as a threshold on D (ratio 40, R ≈ 25k):

| Work ahead | Clear when the unused context exceeds about |
|---|---|
| A follow-up (~10 requests) | 100k |
| A small task (~50 requests) | 20k |
| A full work package (100+ requests) | 10k |

**Cold cache.** After an idle gap longer than the TTL, keeping re-writes the whole context, D included, and costs w·D + r·D·c. The needed part is written either way, so clearing costs only the re-orientation share of R. Clear unless D is small.

**Estimating sizes.** English and code run about 4 characters per token, and 100 lines of code is roughly 1k tokens. For a file, use `wc -c FILE` ÷ 4. In Claude Code, `/context` shows the actual total.

## Measuring a session

Keep a ledger (`docs/COST.md`, from `templates/COST.template.md`) with one row per work package: requests, total prompt tokens, cache-hit share, output tokens, dollars, and the clear-or-keep decision. Take the numbers from `/usage` or a statusline at the checkpoint.

Run `scripts/cost_report.py` at each checkpoint (or in CI with `--max-median`): it prints median, p75, the last-five trend, the cache trend and any WP at more than twice the median. `audit_transcript.py` reads one session JSONL and names the files read most, the re-reads, the largest turn and the estimated cost.

- **Cost per completed WP is the metric**, not cost per session. A cheap session that has to be redone is not cheap.
- A WP at more than twice the median is a leak: a stale map, a grown entry file, rework, or an unusually large reload.
- The cache-hit share should stay high. A drop mid-session means a prefix change; find it in the invalidation table.
- Give each WP a dollar budget. Exceeding it usually means the WP was too big; split it next time.

Prompt tokens are `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; `input_tokens` alone is only the uncached remainder.

## Worked example (Opus 5.5, 1-hour TTL)

At the end of a work package the context holds 120k tokens: 30k of base prompt, 20k the next package needs, and 70k it won't use. The next package will take about 100 requests.

- Keeping costs 0.05 × 70k × 100 = 350k input-token equivalents ($1.40).
- Clearing costs 2 × 25k = 50k equivalents ($0.20). **Clear.**

If the next step were a 10-request follow-up instead, keeping would cost 35k against 50k for clearing. **Keep.**

## /compact versus /clear

`/compact` reads the whole context once (at the read price if the cache is warm), writes a summary as output (5×), and starts a new context from that summary at the write price. With 150k of context and an 8k summary on Opus 5.5 (1-hour TTL), that is 0.05 × 150k + 5 × 8k + 2 × 8k ≈ 63k equivalents. A clear plus a 25k reload costs about 50k.

The costs are similar, but the compact summary is ad hoc and nobody reviews it. Prefer a maintained `STATUS.md` with `/clear`, and leave auto-compact as the safety net.

## Subagents

A subagent starts with a fresh context. It pays for its own base prompt and everything it reads at the write price, and hands back only its final report. That saves tokens when the main session would otherwise carry the raw material through many requests.

Example: a search reads 60k tokens to produce a 2k answer, and the main session has 100 requests ahead. Done inline, it costs about 2 × 60k + 0.05 × 58k × 100 ≈ 410k equivalents. In a subagent it costs about 2 × (60k + its base prompt), well under that. For small lookups, work inline.

A report is written at 5× and then carried at the read price by every later request: a 5k report over 100 requests costs 0.05 × 5k × 100 = 25k equivalents (about $0.10). Cap it at ~40 lines, `file:line` references and no code dumps. Stagger parallel subagents by a second or two: a cache entry is usable only after the first response starts, so later subagents can hit the first one's cached system prompt and tool definitions. Only that shared prefix is reused; their own reading is still paid in full.


## Fixed per-request overhead

Some tokens ride on every request before any work happens: the system prompt, tool definitions (including every enabled MCP server's tools), the listing of installed skills, and the entry files (CLAUDE.md, AGENTS.md and their `@` imports). They are cheap per request because they are cached, but they are paid on every request of every session, and a change to any of them re-writes the cache from that point on.

- An entry file of 1k tokens costs 0.05 × 1k × 100 = 5k equivalents per 100-request session on Opus 5.5, plus 2k for writing it into the cache. Every line has to earn that.
- Measure the total once per session with `/context` and keep it under ~15k. 10k of tool definitions or plugin tools costs 0.05 × 10k × 100 = 50k equivalents (about $0.20) per 100-request WP.
- Disable MCP servers and plugins a project doesn't use (`/mcp`, `/plugin`). Claude Code defers many tool schemas until they're searched for, but their names and descriptions still load.
- `/context` shows the breakdown for the current session.
- Every line in the entry file is paid on every request; a hook or permission is free until it fires. Move anything enforceable out of prose.
