# Prompt and output patterns

Each request re-sends the whole context, and output — thinking included — costs 5×. A few sentences in the request and a hard output format cut both sides. These patterns are cheap to type and easy to record in the task or the WP.

## The task brief

For anything larger than a one-line fix, give the model five lines:

- **Goal:** one sentence, in the user's terms.
- **Acceptance:** the command or test that proves it is done. If there isn't one, say what to demonstrate.
- **Non-goals:** what not to touch, rename or "improve".
- **Known locations:** files, if you know them. This is the cheapest way to skip exploration.
- **Budget:** the WP id and an estimated request count (S≈20, M≈50, L≈100), so the model splits rather than sprawls.

An ambiguous ask costs a round trip to clarify *plus* the exploration that guessed wrong. The brief is the cheapest document in the repo.

## Ask for the smallest high-impact answer

The test for every reply: **does the extra text change what the reader does next?** If not, cut it. Smallest is not skimpy: an answer that forces a follow-up question is bigger than the words it saved. Lead with the result, cite the evidence (`path:line` or the one command) and the next step, then stop.

- "Report only the files and line numbers that need to change; do not paste code."
- "One short paragraph. Do not restate the plan or the diff."
- "Failures only; a passing run gets one line."
- "No summary at the end. The diff is the explanation."
- "Answer with `path:line` references, not excerpts."

A cap on the reply is worth more than a cap on reading: reply tokens are written at 5× and then carried by every later request.

## Negative instructions

Say what not to do, explicitly. Models default to thoroughness; thoroughness is what costs money.

- "Do not read lockfiles, generated code, build output, snapshots or vendored data."
- "Do not run the full suite. Run `<check path>` and only widen if it passes."
- "Do not refactor or format anything outside the named files."
- "Do not add tests for unchanged code."

## Stop at green

Once the acceptance command passes and the WP's criteria are met, stop. Unrequested cleanup, extra tests and opportunistic refactors are full-context round trips with no acceptance value, and each one risks rework. "While I'm here" is the most expensive phrase in an agent session.

Put this in the definition of done: **check green · criteria met · stop.**

When you notice an unrelated improvement, add one line to ROADMAP's Later list and continue.

## Verify in a ladder

Per edit: lint the touched file. Per change: the targeted test. Once per WP: one full `check`. Details: [reading-playbook.md](reading-playbook.md).

## Ask once, before exploring

If the request has an open choice that changes the shape of the work, ask one batched question (2–4 options, recommended default first) *before* reading code. Exploration before the answer is usually wasted, and every round trip carries the exploration forward. Record the answer in `DECISIONS.md` so it is never asked again.

Details that are small, reversible and implied by the code: decide them, note them, move on.

If the user reports a failure, ask for the exact command and output before reproducing it; their artifact is already filtered.

## Write docs breadth-first

Put the answer in the first five lines: what this doc decides, what to do with it, where the details are. An agent that reads 20 lines should already have what it needs to act; the rest is for the human who asked "why". Long preambles are paid for by every future session that skims the file.

## Put reusable output on disk

If the result is a plan, review, spec or report that will be used later, write it to a file and reply with a five-line summary. Chat output is paid at 5× and then carried by every later request; a file is written once and read only when needed. A three-line answer belongs in chat: a file read is a round trip.

## Subagent return contract

A subagent's report enters the main context at the write price and is carried by every later request. State the contract in the spawn prompt:

- at most ~40 lines;
- `path:line` references, no code blocks or file dumps;
- the answer to the question first, then at most three supporting facts;
- "if you cannot answer in that space, say what you checked and stop."

Every extra 4k tokens of report costs about 0.08 per 100 remaining requests on Opus 5.5. Stagger parallel subagents by a second or two: the later ones can then hit the first one's cached system prompt and tool definitions instead of all missing.

## Generate, don't author

For repetitive changes — a new endpoint, migration, fixture, or a rename across files — reach for a codemod, scaffold or generator instead of writing the files out. The command is a few dozen output tokens; the authored files are thousands at 5×, and the generator does not typo. Review the diff, then run the check.
