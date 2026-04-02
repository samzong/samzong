---
description: 显示当前 case file 状态（只读）
disable-model-invocation: true
allowed-tools: Read, Glob, Bash(git:*), AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Run only the `status` command. Pure read — no file writes.

Display: status, verdict, next action, blockers, branch, issue, PR, last decision
log entry.

If `updated_at` is stale (>24h), note it and suggest `/code-gate:sync`.
If no case file found, suggest `/code-gate:init`.
