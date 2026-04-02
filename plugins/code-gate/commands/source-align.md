---
description: 校验实现是否匹配原始 issue 和上游状态
argument-hint: "[issue or PR context]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `source-align` gate.

Rules:

- Explicitly repeatable. Each run appends a new decision log entry.
- Do NOT change the status field.
