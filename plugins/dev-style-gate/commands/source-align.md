---
description: Verify implementation matches original issue and upstream
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Source Align

Re-check the work against the external source of truth.

## Execution

1. Run the case file discovery algorithm.
2. Read the case file for the original issue, PR, and branch context.
3. Check the original issue or user report.
4. Check current PR description or review context if relevant.
5. Check `upstream/main` or equivalent current base branch state.

## Required Answers

- Does the fix still match the original problem?
- Is the fix already present upstream?
- Is the PR scope honest about what it solves and what it does not solve?

## Repeatability

Explicitly repeatable. Each run appends a new decision log entry.

## Case File Update

- Do NOT change the status field. Verification gates preserve current status.
- Append a new decision log entry with alignment findings.

## Output

Return the standard output format:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```
