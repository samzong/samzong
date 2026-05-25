---
name: ship
description: >
  Ship staged changes through a narrow release flow: auto-clean staged files,
  block unexpected non-i18n CJK additions, create or keep a branch,
  commit staged work, push, and open a pull request — all without confirmation.
  Use mainly when the user explicitly invokes `/ship` or says "ship it",
  "push and PR", or "commit and PR". Do not use for commit-only, push-only,
  PR-only, or existing-PR editing requests. All generated git and GitHub text
  must be in English.
---

# Ship

Run the entire flow without stopping for confirmation. The user expects a PR link as the only meaningful output.

Stop immediately and report the failure if any required step fails.

- [ ] Step 0: Preflight ⛔ BLOCKING
  - [ ] Run `git diff --cached --name-only` and stop if nothing is staged
  - [ ] Run `git branch --show-current`
  - [ ] Confirm `origin` exists
  - [ ] Run `gh auth status`
- [ ] Step 1: Auto-cleanup staged files
  - [ ] Strip narration comments from staged source files (if `no-comment` skill is available, use it)
  - [ ] Touch staged files only
  - [ ] Keep why-comments, lint directives, suppression comments, JSDoc/TSDoc, and license headers
  - [ ] Re-stage any cleaned files with `git add <file>`
- [ ] Step 2: CJK validation ⛔ BLOCKING
  - [ ] Check added lines only for CJK characters
  - [ ] Ignore i18n or translation paths such as `**/i18n/**`, `**/locales/**`, `**/translations/**`, `*.zh*.json`, `*.zh*.ts`, `*.zh*.yaml`, `*zh-CN*`, `*zh-TW*`
  - [ ] Stop if non-i18n files contain added CJK lines
- [ ] Step 3: Branch, commit, push
  - [ ] If on `main`, create a branch like `feat/<slug>`, `fix/<slug>`, `refactor/<slug>`, `docs/<slug>`, or `build/<slug>`
  - [ ] If not on `main`, validate the branch name matches `<type>/<slug>` where type is one of `feat|fix|refactor|docs|build|chore|test`. If it does not match, rename the branch in-place (`git branch -m <new-name>`) to a conforming name derived from the staged diff — no confirmation needed
  - [ ] Run `git log --oneline -5` for commit style reference
  - [ ] Draft one commit message in conventional format: `type(scope): description`
  - [ ] Commit staged changes only (do not run `git add` on unstaged files)
  - [ ] Match the repo's normal signing convention before committing
  - [ ] Run `git push -u origin HEAD`
- [ ] Step 4: PR body — template-first ⛔ MUST READ BEFORE WRITING
  - [ ] Run `cat .github/PULL_REQUEST_TEMPLATE.md` (or the repo-root equivalent). If the file exists and is non-empty, you MUST use it as the PR body structure — fill in every section with content derived from the diff. Do NOT skip sections or replace the template with the fallback.
  - [ ] Only if no template file exists anywhere in the repo, use the fallback body below.
- [ ] Step 5: Create PR
  - [ ] Use `gh pr create` with the title and body from above
- [ ] Step 6: Report
  - [ ] Output: cleanup count, branch name, commit message, **PR URL**

## Cleanup rules

Remove staged single-line comments that only narrate the next line, such as `// Create the ...`, `// Initialize ...`, `// Handle ...`, `// Set up ...`, `// Update ...`, `// This is ...`, `// We need to ...`.

Keep comments that explain why the code exists or preserve tooling behavior.

## PR title

Map the commit type to a PR title prefix:

- `feat` -> `[Feat]`
- `fix` -> `[Fix]`
- `docs` -> `[Docs]`
- `refactor` -> `[Refactor]`
- `build` -> `[Build]`
- `chore` -> `[Chore]`

## Fallback PR body (ONLY when no `.github/PULL_REQUEST_TEMPLATE.md` exists)

```md
### What's changed?

- <concise bullet(s)>

### Why

- <reason / motivation>
```

## Do not

- Do not ask for confirmation at any step
- Do not show drafts and wait for approval
- Do not trigger this skill for broad PR-only requests like "open PR"
- Do not run `git add` on unstaged files
- Do not include unstaged changes
- Do not invent validation results or claim commands were run when they were not
- Do not continue after auth, push, or PR creation failures
- Do not generate non-English git or GitHub text
