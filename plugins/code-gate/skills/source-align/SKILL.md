---
name: source-align
description: Compare the implementation with original source context, PR or issue discussion, and upstream state. Use when the user asks for code-gate source-align or wants source-backed maintainer review.
---

# Source Align

Use this skill for the Code Gate source-alignment pass.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for the Source-Backed Maintainer Review Lens, case file discovery, update rules, and output.

## Gate

Run only the `source-align` gate.

## Behavior

- Check the original issue, report, PR context, and upstream baseline.
- State whether the fix still matches the original problem.
- State whether the fix is already present upstream.
- State whether the scope claim is honest.
- Apply the Source-Backed Maintainer Review Lens when an issue, PR, or diff is available.
- Include the best possible solution and remaining risk or open question when they affect next action.
- Append a decision log entry.
- Do not change status.
- If no valid case file exists, auto-create a minimal case file first, then run source-align.
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
