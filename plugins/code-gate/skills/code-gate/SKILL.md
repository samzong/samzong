---
name: code-gate
description: Route the Code Gate maintainer workflow in Codex. Use when the user invokes code-gate directly, asks for an ambiguous gate, or wants the umbrella workflow entrypoint.
---

# Code Gate

Use this skill as the umbrella router for the `code-gate` maintainer workflow. It is a Codex-native wrapper around the shared protocol in `../../shared/protocol.md`.

Prefer the gate-specific Codex skills when the request clearly matches them:

- `init` for starting or reusing a case file
- `status` for read-only status checks
- `next` for read-only next-step suggestions
- `feasibility` for first maintainer decisions
- `adversarial` for challenge passes
- `source-align` for source-backed alignment checks
- `merge-value` for merge-worthiness decisions
- `reply` for paste-ready review replies
- `sync` for refreshing case state
- `close` for closing cases
- `review` as a high-level convenience entry for feasibility, adversarial, source-align, or merge-value review gates

Use this umbrella skill for direct `code-gate <gate>` invocations or ambiguous routing.

## Core Rule

Run exactly one gate per user request. Do not continue from one gate to the next unless the user explicitly asks for the next gate.

## First Step

Read these files before acting:

- `../../shared/protocol.md`
- `../../references/case-file-template.md` when running `init`

Treat the protocol as the source of truth for status values, discovery, state transitions, case file format, and output contract.

## Supported Gates

- `init`: create or reuse the root-level case file and set `status: intake`
- `status`: read the current case file only
- `next`: read the current case file and suggest one next gate
- `feasibility`: decide whether the task should be fixed and set positive cases to `execute`
- `adversarial`: challenge the current story and append evidence without changing status
- `source-align`: compare the implementation with original source context, PR/issue discussion, and upstream state using the source-backed maintainer review lens
- `merge-value`: decide whether the change is worth merging using upstream-baseline evidence, owner/boundary fit, contract/security impact, best possible solution, and remaining risk
- `reply`: draft a paste-ready review reply without reading or writing case state unless needed for context
- `sync`: refresh the case file without changing status
- `close`: freeze the final verdict and set `status: closed`

## Invocation Mapping

Accept natural Codex requests and map them to one gate:

- `code-gate init ...` -> `init`
- `code-gate status` -> `status`
- `code-gate next` -> `next`
- `code-gate feasibility ...` -> `feasibility`
- `code-gate adversarial ...` -> `adversarial`
- `code-gate source-align ...` -> `source-align`
- `code-gate merge-value ...` -> `merge-value`
- `code-gate reply ...` -> `reply`
- `code-gate sync ...` -> `sync`
- `code-gate close ...` -> `close`

If the user asks for multiple gates in one message, run only the first gate and report the next explicit command to run.

## Codex Behavior

- Follow the repository plan gate before mutating files unless the user explicitly invoked a mutating Code Gate command.
- `status`, `next`, and `reply` are read-only by default.
- `init`, `feasibility`, `adversarial`, `source-align`, `merge-value`, `sync`, and `close` may update the case file exactly as the protocol requires.
- If a stateful gate is requested and no valid case file exists, auto-create a minimal case file first, then continue the requested gate. Do not stop just to ask the user to run `init`.
- Do not auto-create a case file for `status`, `next`, or `reply`.
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
Suggested next: code-gate <gate> - <why>
Alternative: <if re-run warranted, or "None">
```

For `reply`, also include:

```md
Reply: <paste-ready sentence or short paragraph>
```
