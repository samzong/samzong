---
name: commit
description: >
  Explicit conventional commit workflow with optional push and no PR creation.
  Use only when the user invokes $commit; do not invoke it from ordinary-language
  Git requests. Use $ship instead when the user explicitly requests its full PR
  workflow. All git text must be in English.
---

# Commit

Lightweight explicit commit flow. No PR and no repeated confirmation after the final authority gate passes.

## Step 1: Preflight

- [ ] Run `git status -sb`
- [ ] If nothing is staged, stop: "Nothing staged to commit."
- [ ] Stop and report the exact paths if any staged path also has unstaged changes; do not edit or stage those paths.
- [ ] If unstaged or untracked files exist, report that they are not included. Do not stage them.
- [ ] Run `git diff --cached --stat` to see what will be committed

## Step 2: Generate Commit Message

- [ ] Run `git diff --cached` to read the actual changes
- [ ] Draft a conventional commit subject: `type(scope): description`
  - Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `build`, `style`
  - Scope: infer from changed files (optional if changes span many areas)
  - Description: imperative mood, lowercase, no period, under 72 chars
- [ ] Run `git log --oneline -3` for style reference
- [ ] Match the repo's signing convention

## Step 3: Pre-Ship Gate

- [ ] Invoke `/pre-ship --staged` before committing.
- [ ] If `pre-ship` is unavailable in this runtime, stop unless the user explicitly opts out.
- [ ] Require `Pre-Ship: PASS`; on `BLOCK` or `INPUT_ERROR`, stop and report the evidence. Do not edit or commit.
- [ ] On `UNVERIFIED`, report the exact missing evidence and stop. Continue only if the user then replies with the literal word `豁免`; capture the target fingerprint, missing evidence, and reply for the commit body.
- [ ] Record the reviewed staged-diff fingerprint and ensure the staged scope still matches the user's request.
- [ ] Capture any `## Considered and deferred` block emitted by `pre-ship` for the pending commit body.

## Step 4: Final Authority Gate

- [ ] Treat the reviewed staged diff as final; it must be verified or explicitly exempted under Step 3.
- [ ] If the diff is consequential under the applicable AGENTS instructions, apply Mirror `ship` mode to that exact staged diff.
- [ ] Stop on `BLOCK`, `HOLD`, `Contract decision: PENDING`, or `Risk disposition: OWNER ACCEPTANCE REQUIRED`.
- [ ] Continue without another confirmation when Mirror reports unchanged scope with `Risk disposition: BOUNDED` or `ACCEPTED AFTER REPORT`; the explicit `$commit` invocation remains the Git authorization.
- [ ] Recompute the staged-diff fingerprint immediately before commit.
- [ ] On a staged-diff change after Step 3, the AGENTS evidence-reuse rule governs (inspect every semantic delta; do not discard valid checks bound to unchanged content). Re-verify the delta itself; Steps 3 and 4 re-run only where the delta adds scope, a new owner decision, or behavior the recorded target does not cover.

## Step 5: Commit

- [ ] Run `git diff --cached` immediately before committing.
- [ ] Commit with `git commit -s -m "<subject>"`; append any Step 3 deferred block and `## Verification exemption` record to the commit body.
- [ ] Show the commit hash and message

## Step 6: Push (conditional)

If user said "push", "push it", or "commit and push":
- [ ] `git push -u origin HEAD`
- [ ] Show the remote URL

If user only said "commit":
- [ ] Do NOT push
- [ ] Report: "Committed locally. Run `git push` when ready."

## CJK Guard

Check added lines for CJK characters in non-i18n source files (same rules as /ship).
If found, warn but do not block — just flag it.

## Do not

- Do not create branches
- Do not create PRs
- Do not ask for confirmation unless Step 4 reports a new owner decision, new scope, or `OWNER ACCEPTANCE REQUIRED`
- Do not push unless explicitly requested
- Do not generate non-English git text
- Do not stage unstaged or untracked files yourself
- Do not stage files the user explicitly excluded
