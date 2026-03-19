---
name: ship
description: >
  Strict release automation: strip AI comments from staged files, check for Chinese characters,
  create branch, commit with conventional format, push, and open PR via gh CLI.
  Use when: user says "ship", "ship it", "open PR", "create PR", "push and PR",
  "commit and PR", "send it", or wants to go from staged changes to a merged-ready PR
  in one shot. ALL generated output (commit messages, branch names, PR titles, PR body)
  MUST be in English.
---

# Ship — Clean, Commit, and Open PR

Strict release automation agent. **ALL output (commit messages, branch names, PR titles, PR body) MUST be in English.**

Stop immediately and report to the user if any step fails.

## Step 1: Simplify + Strip AI Comments

Run `git diff --cached --name-only` to get staged files. **Only touch staged files.**

**1a. Simplify** — For each staged source file, apply the `simplify` skill logic: inline single-use wrappers, delete unused abstractions, flatten unnecessary indirection. Do NOT change behavior or break APIs.

**1b. Strip AI comments** — For each staged source file (`.ts`, `.tsx`, `.js`, `.jsx`, `.css`), remove single-line comments that are AI narration:

**Remove**: `// Create the ...`, `// Initialize ...`, `// Handle ...`, `// Set up ...`, `// Update ...`,
`// TODO: added by ...`, `// This is ...`, `// We need to ...`, or any comment that restates what the next line does.

**Keep**: why-comments (business logic, gotchas), `// eslint-disable`, `// @ts-ignore`, `// NOTE:`, `// HACK:`, `// FIXME:`, JSDoc/TSDoc, license headers, tooling-referenced comments.

Use the Edit tool. Track removed count and simplification count.

## Step 2: Chinese Character Check (HARD STOP)

Run `git diff` and check **added lines only** (`+` lines) for CJK characters (`\u4e00-\u9fff`, `\u3400-\u4dbf`, `\uff00-\uffef`).

**Exclude from this check** (these files legitimately contain CJK):
- `**/i18n/**`, `**/locales/**`, `**/locale/**`, `**/lang/**`, `**/translations/**`
- Files matching `*.zh*.json`, `*.zh*.ts`, `*.zh*.yaml`, `*zh-CN*`, `*zh-TW*`
- Any file whose path clearly indicates it is an internationalization/translation resource

- **Found in non-i18n files**: STOP. List files and lines. Ask user to fix. Do not proceed.
- **Found only in i18n files**: OK. Continue.
- **Clean**: Continue.

## Step 3: Branch

Check `git branch --show-current`.

- Non-`main` branch: stay.
- On `main`: create branch from change type:
  - `feat/<slug>`, `fix/<slug>`, `refactor/<slug>`, `docs/<slug>`, `build/<slug>`
  - Slug: 2-4 lowercase hyphenated words. English only.

## Step 4: Commit

1. `git log --oneline -10` for style reference.
2. **Do NOT run `git add`.** Only commit what is already staged. If staging area is empty, STOP.
3. One-line conventional commit: `type(scope): description` — lowercase, imperative, no period, under 72 chars.
4. Commit with sign-off, no Co-Authored-By:

```bash
git commit -s -m "type(scope): description"
```

## Step 5: Push

```bash
git push -u origin HEAD
```

## Step 6: Create PR

1. Read `.github/PULL_REQUEST_TEMPLATE.md` if it exists.
2. PR type prefix from commit type: `feat`→`[Feat]`, `fix`→`[Fix]`, `ui`→`[UI]`, `docs`→`[Docs]`, `refactor`→`[Refactor]`, `build`→`[Build]`, `chore`→`[Chore]`.
3. Analyze all commits on branch vs `main`.

```bash
gh pr create --base main --title "[Type] Short description" --body "$(cat <<'EOF'
## Summary

<1-3 sentences: what changed and why>

## Type of change

- [x] `[Type]` ...

## Why is this needed?

<problem statement>

## What changed?

- <bullet list>

## Linked issues

Closes #N (or "N/A")

## Validation

- [x] `pnpm typecheck`
- [ ] `pnpm test`
- [ ] `pnpm build`
- [ ] Manual smoke test
- [ ] Not run

Commands, screenshots, or notes:

```text
<verification output>
```

## Screenshots or recordings

N/A

## Release note

- [x] No user-facing change. Release note is `NONE`.

```release-note
NONE
```

## Checklist

- [x] The PR title uses at least one approved prefix
- [x] The summary explains both what changed and why
- [x] Validation reflects the commands actually run for this PR
- [x] The release note block is accurate
EOF
)"
```

Check only what was actually run. Be honest.

## Step 7: Report

Print:
- Simplifications applied count
- Comments removed count
- Branch name
- Commit message
- PR URL
