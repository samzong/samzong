---
name: nobs-review
description: Multi-model code review for pull requests and git diffs. Use when asked to "review my code", "review this PR", "review my changes", "find reviewers", or "run a code review". Suggests appropriate reviewers based on which files changed, runs iterative review rounds across multiple AI models, and tracks findings across sessions.
---

# Review

Multi-model review without runtime interception.

- A single shared contract per review: `.reviews/<review_id>/contract.json`
- Rounds accumulate in: `.reviews/<review_id>/rounds/rNNN/`

## Interaction Order

1. Run initialization. Report detected development tool and confidence level.
2. Report risk analysis.
3. Report recommended reviewers.
4. Prompt the user to confirm or override selections.
5. Execute the review.

IF detected development tool confidence is low, THEN state the low confidence and proceed.

## Workflow

### 1) Init

```bash
python3 skills/nobs-review/scripts/init_review.py --task "<what to review>"
```

To override tool detection:

```bash
python3 skills/nobs-review/scripts/init_review.py --task "<what to review>" --dev-tool claude
```

To refresh an existing review and preserve history:

```bash
python3 skills/nobs-review/scripts/init_review.py --id <review_id> --task "<updated scope>" --refresh
```

The `init` command performs the following actions:
- Detects the current development tool.
- Analyzes diff risk.
- Pre-enables recommended reviewers in the contract.
- Sets `.reviews/.active_review_id`.

### 2) Confirm Reviewers

Perform the following checks in `.reviews/<id>/contract.json`:
- `reviewers[].enabled`
- `reviewers[].command_template`

Accept the recommendation or select custom reviewers.

### 3) Run Round

```bash
python3 skills/nobs-review/scripts/run_review.py --id <review_id> --round auto
```

Or use the active ID:

```bash
python3 skills/nobs-review/scripts/run_review.py --round auto
```

To limit reviewers:

```bash
python3 skills/nobs-review/scripts/run_review.py --id <review_id> --round auto --reviewers codex_high,claude_opus
```

### 4) Merge Findings

```bash
python3 skills/nobs-review/scripts/merge_review.py --id <review_id> --round latest
```

The `--round auto` argument is treated as `latest` during the merge operation.

Outputs per round include: `merged.md` and `resolution.md` located in `.reviews/<id>/rounds/rNNN/`.
The latest pointers at the review root (`merged-latest.md`, `resolution-latest.md`) are ephemeral. They are overwritten on each subsequent merge.

For persistent checklist edits, use the round-scoped `resolution.md`.

### 5) Review Auto-Fix Candidates

After merging, check `auto-fix-candidates.md` in the round directory or `auto-fix-candidates-latest.md` at the review root.

Findings listed in this file satisfy both conditions:
- `fix_determinism = high` (exactly one correct fix, no judgment required)
- `fix_scope = local` (change confined to 1–3 lines within a single function)

Perform the following steps for each fix:
- Apply the fix.
- Mark `Applied: [x]`.
- Commit the changes.
- Run a new round to verify:
    ```bash
    python3 skills/nobs-review/scripts/run_review.py --round auto
    python3 skills/nobs-review/scripts/merge_review.py --round latest
    ```

Findings not appearing in `auto-fix-candidates.md` require human judgment and are tracked in `resolution.md`.

The `auto_fix_threshold` in `contract.json → policy` controls the boundary:

```json
"auto_fix_threshold": { "determinism": "high", "scope": "local" }
```

To expand the set of auto-fix candidates, raise `determinism` to `medium` or `scope` to `cross-file`.

### 6) Fix and Re-review

```bash
python3 skills/nobs-review/scripts/run_review.py --id <review_id> --round auto
python3 skills/nobs-review/scripts/merge_review.py --id <review_id> --round latest
```

This process creates `r001 -> r002 -> ...`, preserving history.

## Rules

- IF a reviewer CLI is missing, THEN fail and do not fake the output.
- IF JSON output is invalid, THEN keep raw output and mark the parse as failed.
- No single round constitutes the final truth; comparison across multiple rounds is required.

## Output Contract

- [references/schema.md](references/schema.md)
- [references/providers.md](references/providers.md)

## Notes

- Deterministic logic resides in scripts; this skill is intentionally thin.
- For high-risk diffs, employ at least two strong reviewers.
- The user determines the final reviewer set; recommendations are advisory.