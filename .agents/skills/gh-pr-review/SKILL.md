---
name: gh-pr-review
description: Review a GitHub Pull Request as a responsible project owner using the `gh` CLI. Use when the user provides a PR URL (e.g. https://github.com/ORG/REPO/pull/N) or a PR number for the current git repo (prefer upstream, else origin) and wants an owner-grade review document `review-N.md` written in Chinese with copy-pastable GitHub comments in English. Scope the review to lines changed by the PR (do not nitpick unrelated pre-existing code), but apply best practices and flag any clear bugs, security issues, or CI failures caused by the change.
---

# Gh Pr Review

## Overview

Generate an owner-grade PR review. The review must be strict regarding correctness and safety while maintaining a gentle tone with contributors, and it must be scoped to the PR's diff. Produce `review-<pr>.md`, which includes a Chinese narrative and English comment snippets ready for pasting into GitHub.

## Hard Gates

- IF `gh` is not installed THEN terminate execution and instruct the user to install and configure it.
- IF `gh auth status` fails OR repository access is missing THEN terminate execution and instruct the user to resolve authentication or permissions issues.

## Workflow (v1.0)

### 1) Collect PR Facts (gh-only)

Execute the following script:
```bash
bash skills/gh-pr-review/scripts/gh_pr_review.sh <PR_URL|PR_NUMBER>
# Example: bash skills/gh-pr-review/scripts/gh_pr_review.sh https://github.com/org/repo/pull/42
# Example: bash skills/gh-pr-review/scripts/gh_pr_review.sh 42
```
This action creates the directory `.gh-pr-review/pr-<n>/` and a starter document `review-<n>.md` in the current working directory.

Artifacts produced:
- `pr.json`: Contains metadata (title, author, base/head branches, head SHA).
- `diff.patch`: Contains the unified diff.
- `changed-lines.json`: Provides per-file hunk and new-side line mapping.
- `checks.txt`: Summarizes checks.
- `failed-logs.txt`: Contains failed workflow logs (best-effort collection).

### 2) Understand What Module Changed (Owner Context)

- Utilize the file paths within `changed-lines.json` to identify the affected subsystem (e.g., `src/router/*`, `docs/*`, `tests/*`).
- Read only the code or documentation relevant to the changed hunks to fully comprehend intent and behavior.
- DO NOT review unrelated lines within the same file. Recommendations for best practices are permissible only if they directly impact the correctness, maintainability, or safety of the changed code.

### 3) Check CI / Jobs and Attribute Failures

- Review `checks.txt` and `failed-logs.txt` (if present).
- IF failures are plausibly caused by the PR THEN identify the changed file(s) and line(s) and propose a concrete fix.
- IF failures are unrelated to the PR THEN explicitly state this and DO NOT block the merge.

### 4) Apply "Current Version" Best Practices

- Detect software versions from the repository when possible (e.g., from `pyproject.toml`, `requirements*.txt`, `package.json`, `go.mod`, `Cargo.toml`, toolchain files).
- WHEN uncertain, prioritize official documentation for the exact major version in use.
- AVOID recommending deprecated configurations or APIs.

### 5) Write the Review Document

- Edit `review-<n>.md` and complete the placeholders.
- The narrative and rationale sections must be in Chinese.
- The copy-paste GitHub comments must be in English, polite, actionable, and scoped to changes introduced by the PR.
- The default stance is to accept unless there is a clear bug, security issue, unnecessary code, or significant regression risk.

## Comment Style Guide (English, Copy-Paste Ready)

- Begin by stating the observation (specific line or hunk).
- Explain the impact (bug, risk, or maintainability issue).
- Offer a concrete fix or alternative (a code-level suggestion).
- Maintain a warm tone, assume good intent, and assist the contributor in succeeding.

Example:
```
In `src/auth/login.py:47`, the token is compared with `==` instead of `hmac.compare_digest`.
This opens a timing-attack vector on token validation.
Suggestion: replace with `hmac.compare_digest(token, expected)`.
```

## Scripts

All scripts are located under `skills/gh-pr-review/scripts/` relative to the repository root.

- `gh_pr_review.sh`: This is the entry point. It fetches PR metadata, diffs, checks, and logs, then invokes the two helper scripts, and finally outputs the `review-<n>.md` skeleton.
- `parse_unified_diff.py`: Maps diff hunks to new-side line numbers for scope enforcement.
- `generate_review_md.py`: Renders `review-<n>.md` using artifacts and a template.

Reference: [assets/](`skills/gh-pr-review/assets/`) — This directory contains the review template and prompt fragments.