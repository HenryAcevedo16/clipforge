# Claude Code setup — ClipForge

## Agent files

These project agents live in `.claude/agents/`:

- `opus-worker.md`: architect and coordinator (Opus)
- `haiku-worker.md`: investigator (Haiku)
- `sonnet-worker.md`: implementer (Sonnet)
- `sonnet-reviewer.md`: independent reviewer (Sonnet)

Claude Code loads project agents from this directory. If you create a new agent file while Claude Code is running, restart the session if it does not appear in the agent list.

## Recommended session model

For non-trivial tasks that need coordination, start Claude Code with Opus as the main coordinator:

```bash
claude --model opus
```

In Claude Code Desktop, select Opus for the coordinating session. The subagents retain their own `model` values from frontmatter. If you choose Sonnet as the main session model, Sonnet can still invoke the model-pinned agents when available, but Opus is no longer the main dispatcher.

## Delegation workflow

1. Opus defines the implementation plan and acceptance criteria.
2. Haiku researches bounded questions and returns references, not broad source dumps.
3. Sonnet implements and runs focused tests.
4. Sonnet Reviewer reads the diff independently and reports findings; it must not edit.
5. Sonnet addresses confirmed findings and reruns tests.
6. Opus is called again only when architecture, risk or unresolved trade-offs require it.

For a trivial, well-scoped change, Sonnet may work directly without spawning all roles.

## Verify model availability

Agent frontmatter requests a model alias; it does not bypass plan, organization, or account availability. Confirm that the agent/model is actually available in the current Claude Code session. If an agent unexpectedly inherits the main model, inspect its selected model in Claude Code before assuming routing worked.

## Local verification

From the repository root:

```bash
python3 .claude/skills/model-router/scripts/route.py "find the function that parses timestamps" --files 1
python3 .claude/skills/model-router/scripts/route.py "design a safer live chunk processing architecture" --files 8
python3 .claude/skills/model-router/scripts/route.py "review the frontend diff" --files 2
```
