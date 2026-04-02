---
description: Generate paste-ready reply for review comment
argument-hint: "[comment-text-or-github-url]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(gh:*)
---

@${CLAUDE_PLUGIN_ROOT}/skills/protocol/SKILL.md

# Reply

Produce a concise reply for a review comment or maintainer thread.

## Input

`$ARGUMENTS` is the review comment text or a GitHub URL.

- If `$ARGUMENTS` is a GitHub URL, fetch the comment content with `gh`.
- If `$ARGUMENTS` is empty, ask the user once: what comment should be replied to?
- If `$ARGUMENTS` is inline text, use it directly.

## Execution

1. Understand the comment's claim or suggestion.
2. Check the codebase for evidence.
3. Draft a reply.

## Rules

- Reply with the conclusion, not the whole investigation.
- If the suggested fix is wrong, say so directly and explain the evidence.
- Keep it short enough to paste into GitHub.

## Stateless

This command does NOT update the case file. It does not require a case file to exist.

## Output

Return the standard output format plus:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path or "N/A">

Reply: <paste-ready text>
```
