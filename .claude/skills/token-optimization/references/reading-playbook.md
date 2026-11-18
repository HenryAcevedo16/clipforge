# Reading and command playbook

Every line of output lands in context once at the write price and is then carried by every later request. Ask for the smallest output that answers the question.

## One call, not five

A read-only lookup costs a request, and every request re-sends the whole context: about $0.03 per round trip at 150k on Opus 5.5. Merge lookups instead of asking five times.

```bash
sed -n '40,80p;210,240p' FILE        # two ranges, one call
grep -n '^## ' docs/*.md             # every doc's sections, one call
for f in a.rs b.rs; do echo "=== $f ==="; sed -n '1,40p' "$f"; done
```

Batching independent calls in one message saves round trips, but a speculative read does not: anything read is paid once and carried by every later request. Parallelize only when every result will be used.

## Finding things

| Need | Command |
|---|---|
| The sections of a long doc | `grep -n '^## ' docs/ROADMAP.md`, then read one section by line range |
| Where a symbol is defined | `git grep -n 'fn parse_uci'` or `grep -rn --include='*.rs' 'fn parse_uci' crates/` |
| Only the matching file names | `grep -rl 'TODO' src/` or `git ls-files 'crates/*/src/lib.rs'` |
| What a file is for | the code map (`docs/MAP.md`), or `head -20 FILE` for its contract |
| How big a file is before reading it | `wc -l FILE` (about 10 tokens per line of code) |
| Long lines in any output | append `\| cut -c1-200` |
| Counts instead of lists | `grep -c PATTERN FILE`, or `... \| sort \| uniq -c \| sort -rn \| head` |
| The behaviour a module promises | `pytest --collect-only -q` (test names are a cheap spec) |
| Callers of a symbol | `ast-grep -p 'call($$$)'`, or `git grep -n 'name('` |

## Reading

- Read the contract (the module's header comment) before the implementation.
- Read the test before the implementation: it states the expected behaviour in fewer lines than the code that implements it.
- Once you know where to look, read a line range: the Read tool's offset and limit, or `sed -n '120,180p' FILE`.
- Reuse what is already in context. After an edit, trust the edit result instead of re-reading the file.
- When a tool saves a large output to a file, run `grep -n PATTERN that-file | head` instead of reading the whole file.
- Combine several small read-only lookups into one shell call. Separate them with `echo '=== name ==='` so each result stays labelled.

## Git

`git status --short` · `git diff --stat` · `git diff -U1 FILE` · `git log --oneline -10` · `git show --stat HEAD`

## Builds and tests: failures only

| Ecosystem | Quiet form |
|---|---|
| Rust | `cargo build -q` · `cargo clippy -q -- -D warnings` · `cargo nextest run --status-level fail --final-status-level fail` · `cargo test -q` |
| Python | `pytest -q -x --tb=short` · `python3 -m unittest discover -q` |
| JS/TS | `vitest run --reporter=dot` · `jest --silent` · `tsc --noEmit --pretty false` |
| Go | `go vet ./...` · `go test ./... 2>&1 \| grep -Ev '^(ok\|\?) '` |
| Anything noisy | `CMD > /tmp/out.log 2>&1; echo "exit $?"; tail -20 /tmp/out.log`, then grep the log only if needed |
| GitHub CI | `gh run list -L 3` · `gh run watch --exit-status` · `gh run view RUN_ID --log-failed` |
| JSON | `jq '.field'` · `gh ... --json name,status --jq '.[] \| ...'` |

The best single investment is a repo-level `check` command that runs everything CI gates on and prints only a summary and the failures: one call, one short output.

## Verification ladder

Run the cheapest check that can catch the error, and stop as soon as it fails:

1. The touched file: `tsc --noEmit` / `ruff check FILE` / `cargo check -q`.
2. The targeted test: `pytest -q path::test_name` / `vitest run path`.
3. One full `check` at the end of the WP, not after every edit.

Order the full check fastest-and-most-likely-to-fail first, and make it stop at the first failure. A failure should print `file:line` and the likely fix, so the correction costs no exploration. Quarantine flaky tests instead of retrying: a retry is another full-context request plus its log. Give each WP one full-check budget.

## Filter before it enters context

- A `PreToolUse` hook can rewrite a noisy command (for example append `2>&1 | grep -A5 -E '(FAIL|ERROR)' | head -100` to a test run) so the full log never lands in context. Stronger than quiet flags when a tool's output is huge.
- A `PreToolUse` guard can deny a whole-file read of a large file and ask for `offset`/`limit`; see `scripts/guard_read.py` and `templates/settings.template.json`. Enforce the rule instead of repeating it in every prompt.
- Prefer CLI tools (`gh`, `aws`, `gcloud`, …) over MCP servers when both exist: an MCP server adds tool names and descriptions to every request even when deferred, a CLI adds nothing. Disable servers you aren't using (`/mcp`).
- In typed languages, a code-intelligence plugin (LSP) replaces grep-plus-read with go-to-definition, and reports type errors after edits without a compiler run.

## Cap output at the source

- `BASH_MAX_OUTPUT_LENGTH` (default 30,000 characters) and `MAX_MCP_OUTPUT_TOKENS` (default 25,000) bound how much one tool can inject. Lower them to your worst useful log. Truncation drops the tail, so redirect a huge log to a file first and grep it.
- For repeated changes, run a codemod, generator or scaffold and review the diff instead of authoring the files: output costs 5×, and a generator does not typo.

## Docs you write

Put the answer in the first five lines; details below. Every future session pays for the preamble, and most of them only need the answer.

If the artifact will be reused or is longer than ~50 lines, write the file and reply with a five-line summary. The file is written once at 5× and read only when needed; the same text in chat is carried by every later request. A three-line answer stays in chat: a file read is a round trip.

## The web

- Fetch with a prompt that names exactly the facts to extract.
- Prefer machine-friendly sources. Many docs sites serve a `.md` version of each page, and an `llms.txt` index.
- Record what you learned with the date and the source URL, so nobody fetches it again.

## Asking the user

- One question with 2–4 options and a recommended default costs less than a wrong guess plus the rework that follows.
- If the user reports a failure, ask for the exact command and output before reproducing it; their artifact is already filtered.
- Record the answer (in DECISIONS.md, or wherever the repo keeps decisions) so the question is never asked again.
