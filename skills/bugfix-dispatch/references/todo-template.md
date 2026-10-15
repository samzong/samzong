# todo.md template

Use this template when writing the per-worktree handoff file.

````md
# PR: fix/<slug>

## Objective

<one sentence: what this PR fixes and why it matters>

## Merge Order

<dependency note, or "No ordering constraints." when this PR can merge independently>

## Tasks

### Task 1: <verb> <what> in `<file>`

- File: `<relative/path>`
- Symbol: `<function or class>`
- Current bug: <what is wrong now>
- Expected behavior: <what must be true after the fix>
- Suggested fix: <minimal change direction>
- Verification: <specific command or manual check>

## Scope Constraints

- Only modify listed files
- No refactors
- No added comments
- Keep the diff minimal

## Context

<only the supporting details needed to implement the fix>
````

Add a short code snippet only when file path plus symbol is not enough to locate the change.
