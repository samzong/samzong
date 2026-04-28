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
- Apply the Source-Backed Maintainer Review Lens from the protocol.
- Compare original issue/PR discussion, upstream-baseline behavior, and the
  current implementation. Say whether the task is still real, already
  implemented, duplicated/superseded, or no longer aligned.
- For PRs, inspect the PR body, diff, touched files, comments, and
  upstream-baseline behavior before deciding whether the PR still matches the
  original problem.
- Record the best possible solution and remaining risk/open question when they
  affect what should happen next.
