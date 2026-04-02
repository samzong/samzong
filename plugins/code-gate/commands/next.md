---
description: 根据当前状态建议下一个 gate（仅展示）
disable-model-invocation: true
allowed-tools: Read, Glob, Bash(git:*), AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Run only the `next` command. Display only — NEVER auto-execute.

Apply the state machine from the protocol. Output:

```
Current status: <status>
Suggested next: /code-gate:<command> — <why>
Alternative: <if re-run warranted, or "None">
```

Backward detection: if status is `merge-value` or later and there are new commits
since the last adversarial/source-align log entry, suggest re-running verification.

If no case file found, suggest `/code-gate:init`.
