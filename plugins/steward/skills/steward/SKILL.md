---
name: steward
description: Route the Steward maintainer workflow in Codex. Use when the user invokes steward directly, asks for an ambiguous gate, or wants the umbrella workflow entrypoint.
---

# Steward

Use this skill as the umbrella router for the `steward` maintainer workflow. It is a Codex-native wrapper around the shared protocol in `../../shared/protocol.md`.

Prefer the gate-specific Codex skills when the request clearly matches them:

- `feasibility` for first maintainer decisions using the Requirement Deletion Lens
- `adversarial` for challenge passes, especially debatable requirements and abstractions
- `source-align` for source-backed alignment checks
- `merge-value` for merge-worthiness decisions
- `status` for read-only status checks
- `next` for read-only next-step suggestions
- `reply` for paste-ready review replies
- `sync` for refreshing case state
- `review` as a high-level convenience entry for feasibility, adversarial, source-align, or merge-value review gates
- `close` only as a manual archive escape hatch

Use this umbrella skill for direct `steward <gate>` invocations or ambiguous routing.

## Core Rule

Run exactly one gate per user request. Do not continue from one gate to the next unless the user explicitly asks for the next gate.

## First Step

Read these files before acting:

- `../../shared/protocol.md`

Treat the protocol as the source of truth for status values, discovery, state transitions, case file format, and output contract.

## Supported Gates

- `feasibility`: decide whether the task should be fixed using the Requirement Deletion Lens and set positive cases to `execute`
- `adversarial`: challenge the current story using the Requirement Deletion Lens when requirements or abstractions are debatable, and append evidence without changing status
- `source-align`: compare the implementation with original source context, PR/issue discussion, and upstream state using the source-backed maintainer review lens
- `merge-value`: decide whether the change is worth merging using upstream-baseline evidence, owner/boundary fit, contract/security impact, best possible solution, and remaining risk
- `status`: read the current case file only
- `next`: read the current case file and suggest one next gate
- `reply`: draft a paste-ready review reply without reading or writing case state unless needed for context
- `sync`: refresh the case file without changing status
- `close`: manually archive the case by freezing the final verdict and setting `status: closed`

## Invocation Mapping

Accept natural Codex requests and map them to one gate:

- `steward status` -> `status`
- `steward next` -> `next`
- `steward feasibility ...` -> `feasibility`
- `steward adversarial ...` -> `adversarial`
- `steward source-align ...` -> `source-align`
- `steward merge-value ...` -> `merge-value`
- `steward reply ...` -> `reply`
- `steward sync ...` -> `sync`
- `steward close ...` -> `close`

If the user asks for multiple gates in one message, run only the first gate and report the next explicit command to run.

## Codex Behavior

- Follow the repository plan gate before mutating files unless the user explicitly invoked a mutating Steward command.
- `status`, `next`, and `reply` are read-only by default.
- `feasibility`, `adversarial`, `source-align`, `merge-value`, `sync`, and `close` may update the case file exactly as the protocol requires.
- Resolve the current case through the Git-local current pointer before globbing case files.
- If a stateful judgment gate is requested and no valid case file exists, auto-create a minimal case file first, write it to the current pointer, then continue the requested gate.
- Do not auto-create a case file for `status`, `next`, `reply`, or `close`.
- Keep the case file in the repository root using `case-YYYY-MM-DD-<slug>.md`.
- Use the same language as the user's latest message for case file content.
- Prefer `rg`, `git`, and `gh` for evidence gathering when relevant.
- Do not implement product or code changes while running a gate.

## Output

For all gates except `next`, use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```

For `next`, output:

```md
Current status: <status>
Suggested next: steward <gate> - <why>
Alternative: <if re-run warranted, or "None">
```

For `reply`, also include:

```md
Reply: <paste-ready sentence or short paragraph>
```
