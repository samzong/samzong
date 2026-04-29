---
name: status
description: Show the current Code Gate case status without writing files. Use when the user asks where a Code Gate review stands, wants the current verdict, or asks for code-gate status.
---

# Status

Use this skill for the read-only Code Gate status check.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, status values, and output.

## Gate

Run only the `status` gate.

## Behavior

- Read the current root-level Code Gate case file only.
- Do not create a case file if none exists.
- Do not edit files.
- Report the current status, verdict, next action, blockers, branch, issue, PR, and latest decision log entry when present.
- If `updated_at` is stale by more than 24 hours, note that and suggest `code-gate sync`.
- If no case file exists, suggest `code-gate init`.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
