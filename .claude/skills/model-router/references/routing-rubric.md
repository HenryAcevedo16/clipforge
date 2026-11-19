# Routing rubric — ClipForge

Route by ambiguity, scope, blast radius and how easy the result is to verify.

## Roles

| Work | Agent | Why |
|---|---|---|
| Architecture, ambiguous requirements, coordination | Opus Architect | Highest judgment load |
| Exact symbol search, logs, doc lookup, bounded extraction | Haiku Investigator | Mechanical and easy to verify |
| Feature implementation, bug fixes, focused tests | Sonnet Developer | Best default cost/quality |
| Independent review of completed diff | Sonnet Reviewer | Separate quality gate without using Opus for routine review |
| High-risk architecture/security review or unresolved multi-system issue | Opus Architect | Higher blast radius warrants deeper reasoning |

## Rules

- Default implementation to Sonnet.
- Downgrade to Haiku only for fully specified work with an obvious pass/fail check.
- Escalate to Opus when requirements are ambiguous, multiple subsystems interact, the change is difficult to reverse, a cheaper attempt failed, or coordination itself is the task.
- Run Sonnet Reviewer after non-trivial implementation. It must not make edits.
- A routine code review routes to Sonnet Reviewer, not Opus.
- Security-sensitive or high-blast-radius changes receive an additional Opus assessment; do not use Sonnet review as a substitute for necessary security judgment.
- Never escalate solely because a task is large. Decompose it and keep each agent's context bounded.

## ClipForge examples

| Task | Agent |
|---|---|
| Locate the timestamp conversion helper and its callers | Haiku Investigator |
| Summarize a yt-dlp error log and identify the failing stage | Haiku Investigator |
| Add a caption style following an approved design | Sonnet Developer |
| Fix a bounded FFmpeg argument bug and add a regression test | Sonnet Developer |
| Review the finished caption-style diff and tests | Sonnet Reviewer |
| Determine why live clips are duplicated across chunks | Opus Architect |
| Design a new cancellation model spanning FastAPI, jobs and FFmpeg | Opus Architect |
| Review a high-impact credential-handling or file-access change | Sonnet Reviewer + Opus assessment |

## Token discipline

- Do not delegate if the result is smaller and cheaper to inspect directly.
- Keep worker reports below 40 lines with file:line references.
- Never return entire files, huge logs, generated builds, media, model weights or node_modules to the coordinator.
- Reuse Graphify, docs/STATUS.md and docs/MAP.md to avoid repeated repository exploration.
- Stop verification when the relevant checks pass; do not run repeated full builds without a reason.
