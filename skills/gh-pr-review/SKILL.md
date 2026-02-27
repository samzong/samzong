---
name: gh-pr-review
description: Review a GitHub Pull Request as a responsible project owner using the `gh` CLI. Use when the user provides a PR URL (e.g. https://github.com/ORG/REPO/pull/N) or a PR number for the current git repo (prefer upstream, else origin) and wants an owner-grade review document `review-N.md` written in Chinese with copy-pastable GitHub comments in English. Scope the review to lines changed by the PR (do not nitpick unrelated pre-existing code), but apply best practices and flag any clear bugs, security issues, or CI failures caused by the change.
---

# Gh Pr Review

## Overview

Generate an owner-grade PR review that is strict about correctness and safety, gentle with contributors, and scoped to the PR’s diff. Produce `review-<pr>.md` (Chinese narrative + English comment snippets ready to paste into GitHub).

## Hard Gates (Stop Early)

- If `gh` is missing: stop and tell the user to install/configure it.
- If `gh auth status` fails or repo access is missing: stop and ask the user to fix auth/permissions.

## Workflow (v1.0)

### 1) Collect PR Facts (gh-only)

```bash
bash skills/gh-pr-review/scripts/gh_pr_review.sh <PR_URL|PR_NUMBER>
# Example: bash skills/gh-pr-review/scripts/gh_pr_review.sh https://github.com/org/repo/pull/42
# Example: bash skills/gh-pr-review/scripts/gh_pr_review.sh 42
```

Creates `.gh-pr-review/pr-<n>/` and a starter doc `review-<n>.md` in the current directory.

Artifacts produced:
- `pr.json`: metadata (title, author, base/head, head SHA)
- `diff.patch`: unified diff
- `changed-lines.json`: per-file hunk + new-side line mapping
- `checks.txt`: checks summary
- `failed-logs.txt`: failed workflow logs (best-effort)

### 2) Understand What Module Changed (Owner Context)

- Use the file paths in `changed-lines.json` to identify the subsystem (e.g. `src/router/*`, `docs/*`, `tests/*`).
- Read only the relevant code/docs around the changed hunks (enough to fully understand intent and behavior).
- Do **not** review unrelated lines in the same file. You may mention best practices when they directly affect the changed code’s correctness, maintainability, or safety.

### 3) Check CI / Jobs and Attribute Failures

- Read `checks.txt` and (if present) `failed-logs.txt`.
- If failures are plausibly caused by the PR: point to the changed file(s)/line(s) and propose a concrete fix.
- If failures are unrelated to the PR: say so explicitly and do not block merge on it.

### 4) Apply “Current Version” Best Practices (Avoid Stale Advice)

- Detect versions from the repo when possible (examples: `pyproject.toml`, `requirements*.txt`, `package.json`, `go.mod`, `Cargo.toml`, toolchain files).
- When uncertain, prefer official docs for the exact major version in use.
- Avoid recommending deprecated configs or APIs.

### 5) Write the Review Document

- Edit `review-<n>.md` and complete the placeholders.
- Narrative and rationale: Chinese.
- Copy-paste GitHub comments: English, polite, actionable, and scoped to PR-introduced changes.
- Default stance: accept unless there is a clear bug, security issue, unnecessary code, or meaningful regression risk.

## Comment Style Guide (English, Copy-Paste Ready)

- Start with what you observed (specific line/hunk).
- Explain impact (bug/risk/maintainability).
- Offer a concrete fix or alternative (code-level suggestion).
- Keep tone warm: assume good intent and help the contributor succeed.

Example:
```
In `src/auth/login.py:47`, the token is compared with `==` instead of `hmac.compare_digest`.
This opens a timing-attack vector on token validation.
Suggestion: replace with `hmac.compare_digest(token, expected)`.
```

## Scripts

All scripts live under `skills/gh-pr-review/scripts/` relative to the repo root.

- `gh_pr_review.sh`: entry point — fetch PR metadata/diff/checks/logs, invoke the two helpers, output `review-<n>.md` skeleton.
- `parse_unified_diff.py`: map diff hunks to new-side line numbers (scope enforcement).
- `generate_review_md.py`: render `review-<n>.md` from artifacts + template.

Reference: [assets/](`skills/gh-pr-review/assets/`) — review template and prompt fragments.
