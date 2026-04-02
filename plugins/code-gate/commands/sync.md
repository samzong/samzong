---
description: 刷新 case file 用于跨会话交接
argument-hint: "[new evidence or reason]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `sync` command.

Rules:

- Do NOT change the status field.
- Update snapshot fields and `updated_at`.
- Append decision log entry with sync reason.
- `status` = read-only. `sync` = write. Both show state, only sync writes.
