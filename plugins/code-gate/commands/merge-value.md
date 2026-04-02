---
description: 判断变更是否值得合并
argument-hint: "[PR, diff, or current change]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `merge-value` gate.

Rules:

- If re-running (decision log already has a merge-value entry), show previous
  verdict for comparison.
- Set status to `merge-value`.
- Append decision log entry.
