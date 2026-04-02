---
description: 初始化或复用任务的 case file
argument-hint: "[issue-url-or-task-description]"
allowed-tools: Read, Glob, Bash(git:*), Write, AskUserQuestion
---

Read these files before acting:

- `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md`
- `${CLAUDE_PLUGIN_ROOT}/references/case-file-template.md`

Raw arguments:
`$ARGUMENTS`

Run only the `init` gate.

Rules:

- If `$ARGUMENTS` is empty, ask once: what is the task?
- If it looks like a GitHub URL, extract slug as `<repo>-issue-<number>`.
- If free text, derive kebab-case slug from first 4-5 words.
- Guard: if case file exists, ask — reuse or overwrite?
- Set branch from `git branch --show-current`.
- Stop after creating/updating the case file.
