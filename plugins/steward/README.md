# Steward

Steward is a maintainer decision workflow for AI coding agents. It provides a small set of explicit review gates, a shared protocol, and a live case file so long-running issue, PR, and implementation decisions do not collapse into ad-hoc chat.

It is intentionally not an autopilot. Each command runs one gate, records only meaningful state changes, and then stops.

## What Steward is for

Use Steward when you need maintainer-grade judgment on questions like:

- Should this task be fixed at all?
- Is the proposed approach the smallest acceptable fix?
- Does the implementation still match the original issue or PR context?
- Is the change real, narrow, aligned with ownership boundaries, and worth merging?
- What concise maintainer reply should be posted back to a review thread?

## What Steward is not

Steward does not:

- auto-implement code changes;
- auto-advance through the full workflow;
- auto-ship or open PRs;
- write live execution state into `todo.md`;
- replace project-specific coding, testing, or release rules.

## Workflow gates

| Gate | Purpose |
| --- | --- |
| `status` | Read the current case state without writing files. |
| `next` | Suggest exactly one next Steward gate. |
| `feasibility` | Decide whether the task should be fixed and whether the approach is acceptable. |
| `adversarial` | Challenge the current story, hidden assumptions, and regression risk. |
| `source-align` | Compare the change with issue/PR context and the upstream baseline. |
| `merge-value` | Separate correctness from merge-worthiness. |
| `review` | Route a high-level review request to one supported judgment gate. |
| `reply` | Draft a concise paste-ready maintainer reply. |
| `sync` | Refresh the case file without changing status. |
| `close` | Archive the case by setting it to `closed`. |

A typical flow is:

```text
intake → feasibility → execute → adversarial/source-align → merge-value → ship → post-ship → closed
```

Steward still runs only the gate explicitly requested by the user. It never moves to the next gate on its own.

## Case files

Steward keeps one live case file in the repository root:

```text
case-YYYY-MM-DD-<slug>.md
```

The case file stores the current verdict, blockers, scope, touched files, rejected paths, verification state, and decision log. It is the continuity artifact for switching sessions, tools, or agents.

The current case pointer is stored through Git's local path resolution:

```sh
git rev-parse --git-path steward/current
```

This avoids hard-coding `.git/steward/current`, which breaks in linked worktrees.

## Invocation examples

Use the command or skill syntax supported by the host agent. For Codex-style natural invocations:

```text
steward status
steward feasibility fix telegram reaction handling
steward adversarial
steward source-align https://github.com/org/repo/pull/123
steward merge-value
steward reply draft a response explaining why this should be narrowed
steward close
```

Some hosts may expose the same gates as slash commands, for example:

```text
/steward:feasibility fix telegram reaction handling
/steward:status
```

## Directory layout

```text
steward/
├── .claude-plugin/plugin.json     # Claude plugin metadata
├── .codex-plugin/plugin.json      # Codex plugin metadata and UI metadata
├── assets/steward.svg             # Plugin icon
├── references/
│   ├── case_template.md           # Case file template
│   └── why.md                     # Design rationale
├── shared/
│   └── protocol.md                # Source of truth for the workflow
└── skills/
    └── */SKILL.md                 # Gate-specific agent instructions
```

## Source of truth

`shared/protocol.md` defines the authoritative behavior for:

- case discovery;
- valid status values;
- state transitions;
- auto-create fallback for stateful judgment gates;
- output contract;
- source-backed maintainer review lens;
- requirement deletion lens;
- stale case detection;
- update rules.

When changing a skill, keep it aligned with `shared/protocol.md` instead of duplicating new rules locally.

## Design principles

- Explicit commands over a broad mode parser.
- One gate at a time.
- Root-level case files for easy cross-session recovery.
- `todo.md` remains for planned work, not live judgment state.
- Rejected paths are first-class evidence.
- Negative decisions require concrete source, issue, PR, test, or history evidence.
