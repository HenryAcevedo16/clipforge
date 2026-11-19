---
name: model-router
description: Assign ClipForge/NovoClip engineering tasks to the project team: Opus architect, Haiku investigator, Sonnet developer, and Sonnet reviewer. Use for task planning, model selection, delegation, or token-cost optimization.
---

# ClipForge Model Router

Choose the lowest-cost role that can complete the task correctly. The standard team is fixed:

| Role | Agent | Model | Route tasks here |
|---|---|---|---|
| Architect / coordinator | `opus-worker` | Opus | Ambiguous requirements, architecture, multi-module changes, root-cause analysis, high-impact decisions |
| Investigator | `haiku-worker` | Haiku | Mechanical, bounded, verifiable search, symbol location, documentation lookup, log summaries, test discovery |
| Developer | `sonnet-worker` | Sonnet | Normal feature work, bug fixes, refactors, tests, integrations |
| Independent reviewer | `sonnet-reviewer` | Sonnet | Review the completed diff, check acceptance criteria and report defects without editing |

## Dispatch policy

1. For a non-trivial request, Opus coordinates: define objective, scope, acceptance criteria and risk. Use Opus as the main Claude Code session model when the session requires multi-agent coordination.
2. Use Haiku only when the task is fully specified and the pass/fail check is obvious. Haiku reports evidence with file and line references; it does not invent architecture.
3. Sonnet is the default implementer. Keep implementation in one agent at a time.
4. After implementation, Sonnet Reviewer inspects the diff independently. The reviewer must not edit files.
5. Sonnet fixes confirmed findings and reruns focused tests.
6. Opus returns for high-risk architecture/security decisions, cross-system failures or unresolved disagreement.

## Cost and context rules

- Do not call all four agents for every task. For a one-line, well-understood change, Sonnet can implement and a focused test may be enough.
- Delegate only when the smaller result keeps more context out of the coordinator than the call costs.
- Cap agent reports at 30–40 lines. Return findings, file:line, command/result, decision and next step; no full-file dumps.
- Never send the same file to multiple agents for concurrent edits.
- A context overrun means decompose the task, not automatically switch to a more expensive model.
- Load `clipforge-media-pipeline` or `clipforge-frontend` only when the task enters those domains.
- The project has no Fable tier. The supported model tiers are Haiku, Sonnet and Opus.

## Classifier

Run:

```bash
python3 .claude/skills/model-router/scripts/route.py "describe the task" --files 3
```

The classifier is a transparent heuristic, not an autonomous dispatcher. Claude Code delegates through the agents' descriptions and the policy above. If the classifier output conflicts with the actual ambiguity or risk, use judgment and explain why.

Read `docs/AI_TEAM.md` for the complete project workflow.
