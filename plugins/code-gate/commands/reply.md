---
description: 生成可直接粘贴的 review 回复
argument-hint: "[comment-text-or-github-url]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(gh:*), AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `reply` gate.

Rules:

- If `$ARGUMENTS` is a GitHub URL, fetch with `gh`.
- If empty, ask once: what comment to reply to?
- Stateless — does NOT update the case file.
