---
name: bugfix-dispatch
description: >
  Read a bug/task report file and dispatch fixes into isolated git worktrees.
  Splits bugs into conflict-free PR-sized units, creates a worktree per PR via `gmc wt add`,
  and writes an LLM-friendly todo.md in each worktree for vibe-coding handoff.
  Use when: user says "dispatch bugs", "split into PRs", "create worktrees from report",
  "dispatch fixes", "bugfix dispatch", "triage bugs to worktrees", "split tasks",
  or provides a bug report file and wants to distribute work into worktrees.
  Also triggers on: "dispatch", "triage to PRs", "split bugs".
  Requires: gmc CLI installed, git repository context.
---

# Bugfix Dispatch

Read a bug/task report file. Split into conflict-free PRs. Create worktrees. Write LLM-ready todo.md.

## Workflow

### Phase 1: Parse Input File

1. Read the file the user provides (typically `bugs_*.md` from critical-bug-finder, or any task/issue list).
2. Extract all actionable items. Each item needs: location (file path), description, severity, suggested fix.
3. **If the file contains zero actionable items** (empty `critical_bugs`, no tasks, or all items are informational), respond:
   > No actionable development tasks found in `{filename}`.
   Then stop. Do not create worktrees or todo files.

### Phase 2: Group into PRs

Group bugs by **file-level conflict risk**. The goal: each PR can be developed and merged independently without code conflicts.

**Grouping rules (in priority order):**

1. **Same file, same function** → must be in the same PR (cannot split within a function)
2. **Same file, different functions** → prefer same PR, but split if logically independent and the file is large
3. **Different files, same module/directory** → same PR only if they share a logical fix (e.g., a type change that propagates)
4. **Different files, different modules** → separate PRs (ideal: zero conflict risk)

**Conflict detection:**
- Two bugs touch the same file → potential conflict → same PR unless the file regions are clearly isolated
- Two bugs touch files that import each other → check if the fix changes the interface → if yes, same PR
- Two bugs are completely independent files → separate PRs (best case)

**When conflicts are unavoidable across PRs**, define a merge order:
```
PR merge order: fix/auth-bypass → fix/session-cleanup → fix/input-validation
Reason: auth-bypass changes the User type that session-cleanup depends on
```

**PR naming convention:** `fix/{short-slug}` (e.g., `fix/sql-injection-user-query`, `fix/race-condition-file-write`)

### Phase 3: Create Worktrees

For each PR, run:

```bash
gmc wt add fix/{short-slug}
```

CRITICAL: The command is `gmc wt add`, NOT `gmc add`.

After creation, note the worktree path returned by gmc.

If creating multiple independent worktrees, batch them:

```bash
gmc wt add fix/slug-1 fix/slug-2 fix/slug-3
```

### Phase 4: Write todo.md

Write a `todo.md` in the **root of each worktree**. This file is the sole input for an LLM developer doing vibe coding. It must be self-contained and unambiguous.

**todo.md template:**

````markdown
# PR: fix/{short-slug}

## Branch

`fix/{short-slug}`

## Objective

{One sentence: what this PR fixes and why it matters. Be specific about the consequence if unfixed.}

## Merge Order

{If this PR has ordering dependencies, state them here. Otherwise write "No ordering constraints — merge independently."}

## Tasks

### Task 1: {verb} {what} in `{file}`

**File**: `{relative/path/to/file}`
**Function/Symbol**: `{functionName}` (line ~{N})

**Current behavior (bug)**:
{Describe exactly what the code does now that is wrong. Include a minimal code snippet showing the problematic code.}

```{lang}
{the buggy code, 5-15 lines of context}
```

**Expected behavior (fix)**:
{Describe exactly what the code should do instead. Be specific about the invariant or contract being restored.}

**Suggested fix**:
```{lang}
{the fixed code, showing only the changed region with enough context to locate it}
```

**Verification**:
{How to verify the fix works: specific test command, curl example, or manual check step.}

### Task 2: ...

## Scope Constraints

- ONLY modify files listed above
- Do NOT refactor surrounding code
- Do NOT add comments explaining the fix
- Do NOT change formatting of untouched lines
- Keep the diff minimal

## Context

{Any additional context the LLM developer needs: related files, type definitions, protocol specs, etc. Only include what is necessary to understand the fix. Do not dump entire file contents.}
````

**Key principles for todo.md content:**

- Write for an LLM, not a human. Be explicit about file paths, function names, line numbers.
- Include the buggy code snippet so the LLM can locate it via string matching.
- Include the suggested fix as a complete replacement, not a diff description.
- The "Verification" section must be concrete: a command to run, not "test thoroughly".
- Scope Constraints prevent the LLM from over-engineering or drifting.

### Phase 5: Summary

After all worktrees and todo files are created, output a summary table:

```markdown
## Dispatch Summary

| PR Branch | Worktree Path | Files Touched | Severity |
|-----------|--------------|---------------|----------|
| fix/slug-1 | /path/to/wt | file1.ts, file2.ts | CRITICAL |
| fix/slug-2 | /path/to/wt | file3.ts | HIGH |

### Merge Order
1. `fix/slug-1` (no dependencies)
2. `fix/slug-2` (depends on fix/slug-1 — changes to `UserType` interface)
3. `fix/slug-3` (no dependencies, can merge in parallel with #1)
```

If all PRs are independent, state: "All PRs are conflict-free — merge in any order."
