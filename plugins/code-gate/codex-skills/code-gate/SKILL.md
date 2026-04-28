---
name: code-gate
description: Run the Code Gate maintainer workflow in Codex or Codex IDE. Use when the user invokes code-gate, asks for a gated feasibility/adversarial/source-align/merge-value/status/next/reply/sync/close pass, or wants a live case file for a task.
---

# Code Gate

Use this skill for the `code-gate` maintainer workflow. It is a Codex-native wrapper around the shared protocol in `../../shared/protocol.md`.

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
- `source-align`: compare the implementation with original source context and upstream state
- `merge-value`: decide whether the change is worth merging
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
