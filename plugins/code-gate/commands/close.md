---
description: 冻结 case file 并记录最终结论
argument-hint: "[final outcome or closing note]"
allowed-tools: Read, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `close` gate.

Rules:

- Guard: if already `closed`, refuse and show the file.
- Set status to `closed`.
- Record final verdict, outcome, verification, follow-ups.
- Do not turn this into a generic handoff dump.
