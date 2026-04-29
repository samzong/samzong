---
name: merge-value
description: Decide whether a change is worth merging after source-backed review. Use when the user asks for code-gate merge-value or wants a maintainer merge-worthiness verdict.
---

# Merge Value

Use this skill for the Code Gate merge-value decision.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for the Source-Backed Maintainer Review Lens, case file discovery, update rules, state transitions, and output.

## Gate

Run only the `merge-value` gate.

## Behavior

- Separate correctness from merge-worthiness.
- State whether the change is real, narrow, strategic, or noisy.
- State whether the maintenance cost is justified.
- Apply the Source-Backed Maintainer Review Lens before deciding value.
- Cover upstream-baseline gap, owner and boundary fit, tests and docs evidence, security/data-access/contract impact, best possible solution, and remaining risk or open question.
- If re-running and a merge-value entry already exists, show the previous verdict for comparison.
- If no valid case file exists, auto-create a minimal case file first, then run merge-value.
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
