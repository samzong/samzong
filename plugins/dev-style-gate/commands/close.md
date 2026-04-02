---
description: Freeze case file with final verdict
allowed-tools: Read, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Close

Freeze the case file for this task.

## Guard

Run the case file discovery algorithm. If the case file status is already `closed`, refuse to modify it and display the file contents instead.

## Execution

1. Read the case file.
2. Set status to `closed`.
3. Update `updated_at`.
4. Record final verdict, outcome, verification status, and any follow-ups or known limits.
5. Append a final decision log entry.

## Case File Update

- Set status to `closed`.
- Fill in final verdict and outcome in the snapshot section.
- Record any follow-ups or known limits.

Do not turn `close` into a generic handoff dump. Keep it specific to this case.

## Output

Return the standard output format:

```
Verdict: <final verdict>
Why: <short paragraph>
Missing evidence: <remaining gaps or "None">
Next action: <follow-ups or "None — case closed">
Case file: <path>
```
