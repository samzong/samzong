---
name: bugfix-dispatch
description: >
  Dispatch a bug or task report into conflict-aware PR-sized worktrees with
  `gmc wt add` and write LLM-ready `todo.md` files in each worktree. Use when
  the user explicitly asks to dispatch bugs from a report, split a bug or task
  report into PRs, create worktrees from a report, or hand off fixes into
  separate worktrees. Typical input is the output of `critical-bug-finder` or
  any structured bug report with identifiable files, problems, and fix goals.
  Do not use for generic bug finding, generic issue triage, or normal project
  planning without a report file.
argument-hint: "<report-file> [--plan-only] [--quick] [--severity CRITICAL|HIGH] [--max-prs N] [--output todo.md]"
---

IRON LAW: NEVER CREATE A WORKTREE OR WRITE A TODO FILE BEFORE SHOWING A CONFLICT-AWARE DISPATCH PLAN.

# Bugfix Dispatch

Use `$ARGUMENTS` to identify the report file, filters, and execution mode.

Typical pipeline: `critical-bug-finder` -> `bugfix-dispatch` -> implement fixes -> `ship`.

## Options

- `<report-file>`: required input report
- `--plan-only`: build the dispatch plan and stop
- `--quick`: skip the confirmation gate after the plan
- `--severity CRITICAL|HIGH`: filter items by minimum severity
- `--max-prs N`: cap the number of generated PRs
- `--output todo.md`: todo filename to write in each worktree, default `todo.md`

Copy this checklist and check off items as you complete them:

- [ ] Step 0: Validate input [BLOCKING]
  - [ ] Confirm the report file exists
  - [ ] Confirm the current directory is a git repo
  - [ ] Confirm `gmc` exists
  - [ ] Parse filters from `$ARGUMENTS`
- [ ] Step 1: Extract actionable items [BLOCKING]
  - [ ] Read the report file
  - [ ] Accept structured Markdown, JSON, or similar text only if each item exposes a file or symbol, a concrete problem, and a fix objective
  - [ ] Keep only items with a concrete location, problem, and fix objective
  - [ ] If no actionable items remain, stop and say so
- [ ] Step 2: Build the dispatch plan [REQUIRED]
  - [ ] Group by conflict risk, not by report order
  - [ ] Use `fix/<slug>` branch names
  - [ ] Define merge order only when dependencies are real
  - [ ] Respect `--max-prs N`
- [ ] Step 3: Present the plan [REQUIRED]
  - [ ] Show each planned branch, files touched, severity, and merge order
  - [ ] If `--plan-only`, stop here
  - [ ] Unless `--quick` was passed, ask before creating worktrees or writing files
- [ ] Step 4: Create worktrees
  - [ ] Use `gmc wt add`, never `gmc add`
  - [ ] Batch creation only for independent branches
  - [ ] Record the returned worktree path for each branch
- [ ] Step 5: Write todo files
  - [ ] Load `references/todo-template.md`
  - [ ] Write one self-contained todo file in the root of each worktree
  - [ ] Include only the context needed to implement the fix
- [ ] Step 6: Report results
  - [ ] Output a summary table with branch, worktree path, files touched, and severity
  - [ ] State whether PRs are independent or ordered

## Grouping rules

- Same file and same function: same PR
- Same file but different functions: keep together unless the edits are clearly isolated
- Shared interface, shared type, or ordering dependency: same PR or explicit merge order
- Different modules with no dependency: separate PRs by default
- When `--max-prs` forces consolidation, merge the lowest-risk related items first; never split one conflict zone across PRs

## todo file rules

- Write for another LLM, not for a human reviewer
- Name exact files and symbols
- State current bug, expected behavior, and minimal fix direction
- Give a concrete verification step
- Keep scope tight: only listed files, no refactors, no comments, minimal diff
- Include small code snippets only when they are needed to locate the edit

## Do not

- Do not trigger this skill without a report file
- Do not create worktrees before showing the plan
- Do not split fixes that touch the same conflict zone into separate PRs
- Do not dump entire files into `todo.md`
- Do not invent merge dependencies that are not real
- Do not use `gmc add`; the correct command is `gmc wt add`
