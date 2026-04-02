---
description: 对抗性审查 — 找出实现中的薄弱点
argument-hint: "[what to challenge]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `adversarial` gate.

Rules:

- Explicitly repeatable. Each run appends a new decision log entry.
- Do NOT change the status field.
- Do not move into other gates on your own.
