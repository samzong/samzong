---
description: 评估任务是否值得修复、方案是否可行
argument-hint: "[issue, todo, PR, or context]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `feasibility` gate.

Rules:

- If re-running (decision log already has a feasibility entry), show previous
  verdict for comparison.
- If positive: set status to `execute`.
- If negative: suggest `/code-gate:close`. Do not drift into implementation.
- Append decision log entry.
