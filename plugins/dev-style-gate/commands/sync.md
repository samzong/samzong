---
description: Refresh case file for cross-session handoff
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Sync

Refresh the case file without changing the workflow status. This is a write operation.

## Use When

- Switching to another LLM
- Opening a new conversation
- Changing tools
- Pausing work
- After meaningful new evidence appears

## Execution

1. Run the case file discovery algorithm.
2. Read the current case file.
3. Update the snapshot section with current state from the codebase and git.
4. Update `updated_at` in frontmatter.
5. Append a decision log entry with sync reason.

## Case File Update

- Do NOT change the status field. Sync preserves workflow position.
- Update: snapshot fields, `updated_at`, touched files, verification state.
- Append: decision log entry explaining what changed and why sync was needed.

## Distinction from Status

`status` = read-only "where am I?"
`sync` = write "make case file current for the next reader"

Both show state, but only `sync` writes.

## Output

Return the standard output format:

```
Verdict: <short sentence summarizing current state>
Why: <what was updated and why>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```
