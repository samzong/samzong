---
description: Evaluate whether fix is warranted and approach is sound
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Feasibility

Answer two questions before code:

1. Should this be fixed?
2. Is the proposed approach acceptable?

## Execution

1. Run the case file discovery algorithm.
2. Read the case file for context: task goal, hypothesis, scope.
3. Investigate the codebase as needed.

## Required Checks

- Identify the smallest acceptable fix.
- Call out wrong premises directly.
- Separate the real problem from the proposed fix.
- State scope boundaries and risks.

## Repeatability

If re-running feasibility (decision log already has a feasibility entry):
- Show the previous verdict for comparison.
- Highlight what changed since the last run.

## Case File Update

- If verdict is positive: set status to `execute` (signal to start coding).
- If verdict is negative: suggest `/dev-style-gate:close`.
- Append a decision log entry with summary, evidence, decision, and next step.

If the answer is no, stop there. Do not drift into implementation advice unless needed to explain the rejection.

## Output

Return the standard output format:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```
