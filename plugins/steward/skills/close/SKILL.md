---
name: close
description: Manually archive a Steward case by freezing the final verdict and setting the case status to closed. Use when the user explicitly asks for steward close or needs to clean up abnormal case state.
---

# Close

Use this skill as an explicit escape hatch to manually archive a Steward case.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, close behavior, update rules, and output.

## Gate

Run only the `close` gate.

## Behavior

- Freeze the final verdict, verification status, limits, and follow-ups.
- Set status to `closed`.
- Clear the current pointer if it points to this case file.
- Warn if the case is already closed.
- If no valid case file exists, say no current case exists; do not auto-create a case only to close it.
- Do not run another gate.
- Do not implement product or code changes.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
