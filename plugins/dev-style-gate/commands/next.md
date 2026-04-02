---
description: Suggest next gate based on current status (display-only)
allowed-tools: Read, Glob, Bash(git:*)
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Next

Suggest the next gate based on current status. Display only — NEVER auto-execute.

## Execution

1. Run the case file discovery algorithm.
2. If no case file found, suggest running `/dev-style-gate:init`.
3. Read the case file status and decision log.
4. Apply the state machine logic below.
5. Check for backward detection.

## State Machine

```
intake → feasibility
feasibility (positive) → execute (user codes, no command)
feasibility (negative) → close
execute → adversarial | source-align
adversarial ←→ source-align (either order, both repeatable)
adversarial/source-align → merge-value
merge-value (positive) → ship (user ships externally) → close
merge-value (negative) → adversarial (address issues, re-verify)
ship → post-ship → close
```

## Backward Detection

If current status is `merge-value` or later, check whether there are new commits since the last adversarial or source-align decision log entry. If yes, suggest re-running verification gates before proceeding.

## Output

```
Current status: <status>
Suggested next: /dev-style-gate:<command> — <why>
Alternative: <if re-run warranted, or "None">
```

If `updated_at` is stale (>24h), note it.

Do NOT modify the case file. Do NOT execute the suggested command.
