---
name: feasibility
description: Decide whether a task should be fixed and whether the proposed approach is acceptable. Use when the user asks for code-gate feasibility or wants a first maintainer decision.
---

# Feasibility

Use this skill for the Code Gate feasibility decision.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, state transitions, update rules, and output.

## Gate

Run only the `feasibility` gate.

## Behavior

- Decide whether the task should be fixed.
- Decide whether the proposed approach is acceptable.
- Identify the smallest acceptable fix.
- Call out wrong premises directly.
- If re-running and a feasibility entry already exists, show the previous verdict for comparison.
- If positive, set status to `execute`.
- If negative, suggest `code-gate close`.
- If no valid case file exists, auto-create a minimal case file first, then run feasibility.
- Do not drift into implementation.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
