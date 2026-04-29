---
name: close
description: Freeze the final Code Gate verdict and set the case status to closed. Use when the user asks for code-gate close or wants to finish a case.
---

# Close

Use this skill to close a Code Gate case.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, close behavior, update rules, and output.

## Gate

Run only the `close` gate.

## Behavior

- Freeze the final verdict, verification status, limits, and follow-ups.
- Set status to `closed`.
- Warn if the case is already closed.
- If no valid case file exists, auto-create a minimal case file first, then run close.
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
