---
description: Assess whether the change is worth merging
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Merge Value

Separate correctness from merge-worthiness. "Technically valid" is not the same as "worth landing."

## Execution

1. Run the case file discovery algorithm.
2. Read the case file and review the implementation.

## Required Checks

- Is the change real?
- Is it narrow or strategic?
- Is the maintenance cost justified?
- Is the diff clean enough for maintainer review?

## Repeatability

If re-running (decision log already has a merge-value entry):
- Show the previous verdict for comparison.
- Highlight what changed since the last run.

## Case File Update

- Set status to `merge-value`.
- Append a decision log entry with verdict, evidence, and recommendation.

## Output

Return the standard output format:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```
