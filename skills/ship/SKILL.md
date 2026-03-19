---
name: ship
description: >
  Ship staged changes through a narrow release flow: optionally clean staged files,
  optionally block unexpected non-i18n CJK additions, create or keep a branch,
  commit staged work, push, and open a pull request.
  Use mainly when the user explicitly invokes `/ship` or says "ship it",
  "push and PR", or "commit and PR". Do not use for commit-only, push-only,
  PR-only, or existing-PR editing requests. All generated git and GitHub text
  must be in English.
---

IRON LAW: NEVER PUSH OR OPEN A PR WITHOUT SHOWING THE EXACT STAGED SCOPE, BRANCH NAME, COMMIT MESSAGE, AND PR DRAFT FIRST.

# Ship

Stop immediately and report the failure if any required step fails.

Copy this checklist and check off items as you complete them:

- [ ] Step 0: Preflight ⛔ BLOCKING
  - [ ] Run `git diff --cached --name-only` and stop if nothing is staged
  - [ ] Run `git branch --show-current`
  - [ ] Confirm `origin` exists
  - [ ] Run `gh auth status`
- [ ] Step 1: Review staged scope
  - [ ] Run `git diff --cached --stat`
  - [ ] List staged files for the user
- [ ] Step 2: Optional cleanup confirmation ⚠️ REQUIRED
  - [ ] Ask whether to simplify staged source files and remove AI narration comments before commit
  - [ ] If the `no-comment` skill is available, prefer it for staged narration comment stripping
  - [ ] If approved, touch staged files only
  - [ ] Keep why-comments, lint directives, suppression comments, JSDoc/TSDoc, and license headers
- [ ] Step 3: Content validation ⚠️ REQUIRED
  - [ ] Check added lines only for CJK characters
  - [ ] Ignore i18n or translation paths such as `**/i18n/**`, `**/locales/**`, `**/translations/**`, `*.zh*.json`, `*.zh*.ts`, `*.zh*.yaml`, `*zh-CN*`, `*zh-TW*`
  - [ ] Stop if non-i18n files contain added CJK lines
- [ ] Step 4: Branch and commit draft
  - [ ] Stay on the current branch if it is not `main`
  - [ ] If on `main`, create a branch like `feat/<slug>`, `fix/<slug>`, `refactor/<slug>`, `docs/<slug>`, or `build/<slug>`
  - [ ] Run `git log --oneline -10` for commit style reference
  - [ ] Draft one commit message in conventional format: `type(scope): description`
- [ ] Step 5: Publish confirmation ⚠️ REQUIRED
  - [ ] Show the staged files, branch name, commit message, PR title, and PR body draft
  - [ ] Ask the user to continue or revise
- [ ] Step 6: Commit
  - [ ] Do not run `git add`
  - [ ] Match the repo's normal signing convention before committing
  - [ ] Commit staged changes only, for example `git commit -m "type(scope): description"` or `git commit -s -m "type(scope): description"`
- [ ] Step 7: Push and open PR
  - [ ] Run `git push -u origin HEAD`
  - [ ] If `.github/PULL_REQUEST_TEMPLATE.md` exists, follow it
  - [ ] Otherwise use the fallback body below
- [ ] Step 8: Report
  - [ ] Report cleanup count, branch name, commit message, and PR URL

## Cleanup rules

Remove staged single-line comments that only narrate the next line, such as `// Create the ...`, `// Initialize ...`, `// Handle ...`, `// Set up ...`, `// Update ...`, `// This is ...`, or `// We need to ...`.

Keep comments that explain why the code exists or preserve tooling behavior.

Typical downstream: after `critical-bug-finder` or `bugfix-dispatch` has produced and implemented a focused fix, use this skill to publish the staged result.

## PR title

Map the commit type to a PR title prefix:

- `feat` -> `[Feat]`
- `fix` -> `[Fix]`
- `docs` -> `[Docs]`
- `refactor` -> `[Refactor]`
- `build` -> `[Build]`
- `chore` -> `[Chore]`

## Fallback PR body

```md
### What's changed?

- <concise bullet(s)>

### Why

- <reason / motivation>
```

## Do not

- Do not trigger this skill for broad PR-only requests like "open PR"
- Do not run `git add`
- Do not include unstaged changes
- Do not invent validation results or claim commands were run when they were not
- Do not continue after auth, push, or PR creation failures
- Do not generate non-English git or GitHub text
