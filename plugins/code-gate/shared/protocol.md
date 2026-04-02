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

## Case File Contract

- Path: `<repo-root>/YYYY-MM-DD-<slug>.md`
- The date is the creation date. A task started 2026-04-02 keeps that date forever.
- Reuse the existing case file if the task already has one.
- Never create a nested `dev-style/` directory.

## Case File Discovery Algorithm

All commands MUST use this algorithm:

1. `git rev-parse --show-toplevel` for repo root. If that fails, use cwd and say so.
2. Glob `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md` at repo root.
3. Filter: keep only files with a `status:` frontmatter field matching a valid status value.
4. If multiple: ask the user which one.
5. If none: say so. For `init`, proceed to create. For others, suggest `init`.

## Slug Derivation

- From GitHub URL `https://github.com/org/repo/issues/42` → `repo-issue-42`
- From free text "fix telegram reaction" → `fix-telegram-reaction`
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

### `merge-value`

- Separate correctness from merge-worthiness.
- State whether the change is real, narrow, strategic, or noisy.
- State whether the maintenance cost is justified.

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
