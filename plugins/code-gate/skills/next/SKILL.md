---
name: next
description: Suggest the next Code Gate step from the current case file without writing files. Use when the user asks what Code Gate should do next or asks for code-gate next.
---

# Next

Use this skill for the read-only Code Gate next-step recommendation.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, status values, transitions, and output.

## Gate

Run only the `next` gate.

## Behavior

- Read the current root-level Code Gate case file only.
- Do not create a case file if none exists.
- Do not edit files.
- Suggest exactly one next gate based on the current case state and missing evidence.
- If no case file exists, suggest `code-gate init`.
- If a re-run is warranted, include it as the alternative instead of suggesting multiple next gates.

## Output

Use this output shape:

```md
Current status: <status>
Suggested next: code-gate <gate> - <why>
Alternative: <if re-run warranted, or "None">
```
