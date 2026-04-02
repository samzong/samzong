---
description: Hostile implementation review — find what can still break
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Adversarial

Review the implementation from the hostile angle. Try to break the current story.

## Execution

1. Run the case file discovery algorithm.
2. Read the case file and the actual implementation.

## Required Checks

- What can still break?
- What evidence is missing?
- What assumptions were never proven?
- What regression risk is still open?

This is not a summary pass. Actively try to find failures.

## Repeatability

Explicitly repeatable. Each run appends a new decision log entry. This is by design — adversarial review should be run after each round of fixes.

## Case File Update

- Do NOT change the status field. Verification gates preserve current status.
- Append a new decision log entry with findings, evidence, and suggested actions.

## Output

Return the standard output format:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```
