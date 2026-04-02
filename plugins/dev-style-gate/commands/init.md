---
description: Create case file and initialize task snapshot
argument-hint: "[issue-url-or-task-description]"
allowed-tools: Read, Glob, Bash(git:*), Write
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Init

Create the case file and initialize the task snapshot.

## Input

`$ARGUMENTS` is the issue URL or task description.

- If `$ARGUMENTS` is empty, ask the user once: what is the task?
- If it looks like a GitHub URL, extract the slug as `<repo>-issue-<number>`.
- If it is free text, derive a kebab-case slug from the first 4-5 meaningful words.

## Guard

Run the case file discovery algorithm first. If a valid case file already exists at repo root, stop and ask: reuse the existing file or overwrite it?

## Execution

1. Find repo root via `git rev-parse --show-toplevel`.
2. Get current branch via `git branch --show-current`.
3. Read @${CLAUDE_PLUGIN_ROOT}/references/case-file-template.md for the template.
4. Create the case file at `<repo-root>/YYYY-MM-DD-<slug>.md` using today's date.
5. Fill in: task goal, current hypothesis, status `intake`, branch, issue URL if provided.
6. Append an initial decision log entry.

## Output

Return the standard output format:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <what is not yet known>
Next action: <one concrete next step>
Case file: <path to created file>
```
