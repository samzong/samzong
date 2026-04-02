---
description: Show current case file state (read-only)
allowed-tools: Read, Glob, Bash(git:*)
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Status

Show current case file state. Pure read — no file writes.

## Execution

1. Run the case file discovery algorithm.
2. If no case file found, suggest running `/dev-style-gate:init`.
3. Read the case file.
4. Check `updated_at` — if more than 24 hours old, note staleness.

## Output

Display a formatted summary:

```
Status: <current status>
Verdict: <current verdict or "None yet">
Next action: <current next action>
Blockers: <current blockers or "None">
Branch: <branch>
Issue: <issue URL or "None">
PR: <PR URL or "None">
Last decision log: <summary of most recent entry>
```

If `updated_at` is stale (>24h), append:

```
⚠ Case file last updated <timestamp> — consider running /dev-style-gate:sync
```

Do NOT modify the case file.
