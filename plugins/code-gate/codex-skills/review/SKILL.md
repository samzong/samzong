---
name: review
description: Run one evaluative Code Gate review gate for a task, issue, PR, or change. Use for feasibility, adversarial, source-align, or merge-value review requests when the user wants maintainer judgment.
---

# Review

Use this skill for Code Gate review gates that evaluate whether work is sound, aligned, and worth merging.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, state transitions, case file format, and output.

## Supported Review Gates

- `feasibility`: decide whether the task should be fixed and set positive cases to `execute`
- `adversarial`: challenge the current story and append evidence without changing status
- `source-align`: compare the implementation with original source context, PR/issue discussion, and upstream state
- `merge-value`: decide whether the change is worth merging using upstream-baseline evidence, owner/boundary fit, contract/security impact, best possible solution, and remaining risk

## Behavior

- Run exactly one review gate per user request.
- Map natural-language requests to one of the supported review gates.
- If the user asks for multiple review gates in one message, run only the first and report the next explicit command to run.
- If no valid case file exists, auto-create a minimal case file first, then continue the requested review gate.
- Keep the case file in the repository root using `case-YYYY-MM-DD-<slug>.md`.
- Use the same language as the user's latest message for case file content.
- Prefer `rg`, `git`, and `gh` for evidence gathering when relevant.
- Do not implement product or code changes while running a review gate.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
