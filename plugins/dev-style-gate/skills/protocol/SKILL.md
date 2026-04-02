---
name: dev-style-gate-protocol
description: Shared protocol for dev-style-gate plugin — case file contract, discovery, status values, output format, update rules, control model
user-invocable: false
---

# Dev Style Gate Protocol

This is a decision protocol, not a coding skill and not a shipping skill.
It exists to make the user's maintainer workflow repeatable without taking
control away from them.

## Control Model

The user wants absolute control.

- Run only the command the user explicitly asks for.
- Never auto-advance to the next gate.
- Never auto-trigger `/ship`.
- Never turn this into a full-run orchestrator.
- Stop after the requested command and return a short verdict.

## Case File Contract

Every task gets one live case file in the current worktree root.

- Path: `<repo-root>/YYYY-MM-DD-<slug>.md`
- The date is the creation date. A task started 2026-04-02 keeps that date forever.
- Never write state into `todo.md`.
- Never create a nested `dev-style/` directory.

## Case File Discovery Algorithm

All commands MUST use this exact algorithm to find the active case file:

1. Run `git rev-parse --show-toplevel` to find repo root. If that fails, use cwd and say so.
2. Glob `YYYY-MM-DD-*.md` at repo root (pattern: `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md`).
3. Filter results: read frontmatter of each match, keep only files with a `status:` field that is a valid gate status value (exclude README, CHANGELOG, etc.).
4. If multiple valid case files: ask the user which one. Do not guess.
5. If none found: say so. For `init`, proceed to create. For other commands, suggest running `init` first.

## Slug Derivation

- From GitHub URL `https://github.com/org/repo/issues/42` → `repo-issue-42`
- From free text "fix telegram reaction" → `fix-telegram-reaction`
- Kebab-case, first 4-5 meaningful words, no filler words.

## Allowed Status Values

Exactly one of:

- `intake`
- `feasibility`
- `execute`
- `adversarial`
- `source-align`
- `merge-value`
- `ship`
- `post-ship`
- `closed`

## Standard Output Format

After every command, stop and return:

```
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <path>
```

For `reply`, add:

```
Reply: <paste-ready text>
```

## Case File Template

Read @${CLAUDE_PLUGIN_ROOT}/references/case-file-template.md before creating a case file.

## Update Rules

Always update the case file when any of these change:

- status
- verdict
- next action
- blockers
- issue, PR, or branch identifiers
- verification result
- rejected path

Do not update the case file for:

- every shell command
- routine file reads
- repetitive search noise

Prefer one meaningful append per state transition.

## Writing Rules

- Be direct.
- Challenge wrong premises early.
- Prefer evidence over interpretation.
- Keep outputs short enough to scan fast.
- Record dead ends and rejected paths so the next session does not retry them.

## Do Not

- Write live progress into `todo.md`
- Create a global tracker across unrelated tasks
- Auto-run every gate
- Auto-ship
- Let the case file turn into a raw command log
- Write broad generic handoff prose when a tighter case update is enough

## Stale Detection

When displaying case file state (in `status` or `next`), if the `updated_at` frontmatter field is more than 24 hours old, note this to the user.
