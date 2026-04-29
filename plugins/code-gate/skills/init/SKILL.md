---
name: init
description: Create or reuse the root-level Code Gate case file and set it to intake. Use when the user starts a Code Gate case or asks for code-gate init.
---

# Init

Use this skill to start a Code Gate case.

## First Step

Read these files before acting:

- `../../shared/protocol.md`
- `../../references/case-file-template.md`

Treat the protocol as the source of truth for discovery, case file format, status values, and output.

## Gate

Run only the `init` gate.

## Behavior

- Create or reuse the root-level case file.
- Keep the file at `case-YYYY-MM-DD-<slug>.md` in the repository root.
- Capture task goal, current hypothesis, and next intended gate.
- Set status to `intake`.
- Use the same language as the user's latest message for case file content.
- Do not run any follow-up gate.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
