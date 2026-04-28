# Dev Style Gate Protocol

This plugin is an explicit maintainer workflow. It is not a generic coding
assistant and it is not an autopilot.

## Core Rules

- Run only the command the user explicitly invoked.
- Never auto-advance to another gate.
- Never auto-ship.
- Never write live execution state into `todo.md`.
- Keep one live case file in the repo root for the current task.
- Update the case file on state transitions and meaningful evidence changes, not
  after every command.
- Write the case file in the same language the user is currently using in
  conversation. Detect from the user's most recent message; do not ask.

## Case File Contract

- Path: `<repo-root>/case-YYYY-MM-DD-<slug>.md`
- The date is the creation date. A task started 2026-04-02 keeps that date forever.
- Reuse the existing case file if the task already has one.
- Never create a nested `dev-style/` directory.

## Case File Discovery Algorithm

All commands MUST use this algorithm:

1. `git rev-parse --show-toplevel` for repo root. If that fails, use cwd and say so.
2. Glob `case-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md` at repo root.
3. Filter: keep only files with a `status:` frontmatter field matching a valid status value.
4. If multiple: ask the user which one.
5. If none:
   - For `init`, proceed to create.
   - For `reply`, continue stateless.
   - For `status` or `next`, say no case file exists and suggest `init`.
   - For stateful gates (`feasibility`, `adversarial`, `source-align`,
     `merge-value`, `sync`, `close`), auto-create a minimal case file first,
     then run the requested gate.

## Auto-Init Fallback

When a stateful gate auto-creates a case file:

- Derive the slug from raw arguments first.
- If raw arguments are empty, derive the slug from the current branch name.
- If both are unavailable, use `current-task`.
- Capture the requested gate as the next intended gate.
- Set initial status to `intake`, then immediately apply the requested gate's
  normal status/update rules.
- Do not inspect PRs, upstream state, or unrelated diffs just to create the case
  file. Evidence gathering belongs to the requested gate after the case exists.

## Slug Derivation

- From GitHub URL `https://github.com/org/repo/issues/42` → `case-2026-04-06-repo-issue-42.md`
- From free text "fix telegram reaction" → `case-2026-04-06-fix-telegram-reaction.md`
- Kebab-case, first 4-5 meaningful words.

## Allowed Status Values

Exactly one of: `intake`, `feasibility`, `execute`, `adversarial`, `source-align`,
`merge-value`, `ship`, `post-ship`, `closed`.

## Output Contract

Every command stops after its own gate and returns:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```

For `reply`, also return:

```md
Reply: <paste-ready sentence or short paragraph>
```

## Source-Backed Maintainer Review Lens

Use this lens inside the requested gate whenever the task involves an issue, PR,
diff, or merge decision. It is a maintainer evidence frame, not a separate gate
and not an auto-close policy.

- Treat issue and PR discussion as evidence. Read the body, comments, linked
  items, review notes, and timeline signals before deciding.
- Use the upstream baseline, preferring the upstream remote default branch
  (`upstream/HEAD`, commonly `upstream/main`); if unavailable, fall back to the
  origin remote default branch (`origin/HEAD`, commonly `origin/main`) and
  record the resolved ref and commit SHA. Verify whether the reported gap or
  proposed change is already implemented, obsolete, duplicated, or still real.
  Prefer concrete source, docs, tests, commit SHAs, and related issue/PR state
  over title-level matches.
- Search for synonyms, old names, moved ownership, and adjacent implementations.
  Do not decide from one `rg` hit or one nearby file.
- For PRs, inspect the PR body, diff, touched files, comments, and
  upstream-baseline behavior before deciding whether the work is useful,
  redundant, or stale.
- For PRs, run a security and supply-chain surface pass when the diff touches CI
  workflows, GitHub Action refs, dependencies, lockfiles, release scripts,
  package metadata, secrets handling, permissions, downloaded artifacts,
  generated/vendor code, or other code execution paths.
- Identify owner and boundary fit: core vs plugin, shared seam vs owner module,
  docs vs code, current repo vs external administration.
- Identify public contract, data-access, permission, and compatibility
  expansion. If the implementation is technically correct but the remaining
  question is product or maintainer policy, say that explicitly instead of
  inventing a code bug.
- Keep high-confidence negative decisions rare. If you cannot cite concrete
  code/docs/tests/history/related-item evidence, keep the item alive and mark
  the missing evidence.
- Always state the best possible solution: land, narrow, redact, split, defer,
  close as duplicate, move to plugin/ClawHub-style work, or keep open for
  maintainer judgment.
- Separate remaining risks from open questions. Code defects, CI failures,
  security risks, and product-policy decisions should not be collapsed into one
  vague blocker.

## Gate Definitions

### `init` (start)

- Create or reuse the case file.
- Capture task goal, current hypothesis, and next intended gate.
- Set status to `intake`.

### `feasibility`

- Answer whether the task should be fixed.
- Answer whether the proposed approach is acceptable.
- Identify the smallest acceptable fix.
- Call out wrong premises directly.

### `adversarial`

- Try to break the current story.
- Identify missing evidence, hidden assumptions, and regression risk.
- This is not a summary pass.

### `source-align`

- Check the original issue, report, PR context, and `upstream/main`.
- State whether the fix still matches the original problem.
- State whether the fix is already present upstream.
- State whether the scope claim is honest.
- Apply the Source-Backed Maintainer Review Lens when an issue, PR, or diff is
  available.
- Include the best possible solution and remaining risk/open question in the
  decision log entry when they affect the next action.

### `merge-value`

- Separate correctness from merge-worthiness.
- State whether the change is real, narrow, strategic, or noisy.
- State whether the maintenance cost is justified.
- Apply the Source-Backed Maintainer Review Lens before deciding value.
- Explicitly cover upstream-baseline gap, owner/boundary fit, tests/docs evidence,
  security/data-access/contract impact, best possible solution, and remaining
  risk/open question.

### `reply`

- Output a concise review-thread reply.
- Lead with the conclusion, cite key evidence briefly.
- Stateless — does not require or update the case file.

### `sync`

- Refresh the case file without changing status.
- Use before context handoff, tool switching, or session restart.

### `close`

- Freeze the final verdict, verification status, limits, and follow-ups.
- Set status to `closed`.

## State Machine

```
intake → feasibility
feasibility (positive) → execute (user codes, no command)
feasibility (negative) → close
execute → adversarial | source-align
adversarial ←→ source-align (either order, both repeatable)
adversarial/source-align → merge-value
merge-value (positive) → ship (user ships) → close
merge-value (negative) → adversarial (re-verify)
ship → post-ship → close
```

## Repeatability

| Category | Commands | Write? | Repeat? |
|----------|----------|--------|---------|
| Transition | init, close | Yes | Guard: warn if already done |
| Decision | feasibility, merge-value | Yes | Show previous verdict for comparison |
| Verification | adversarial, source-align | Yes | Append to decision log, do NOT change status |
| Utility | status, next, reply, sync | Mixed | Always ok |

## Stale Detection

When displaying case file state (in `status` or `next`), if `updated_at` is more
than 24 hours old, note this to the user.

## Update Rules

Always update the case file when any of these change:
- status, verdict, next action, blockers
- issue, PR, or branch identifiers
- verification result, rejected path

Do not update for: routine file reads, repetitive search noise, every shell command.
