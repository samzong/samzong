---
name: gmc
description: >
  Use the `gmc` CLI for Git worktree lifecycle requests, including create,
  remove, and prune, without requiring the user to name gmc. Also use for
  explicit gmc requests to generate commit messages, manage tags, or discover
  and sync shared resources. Do not use for ordinary Git requests unrelated
  to worktrees unless the user specifically wants gmc.
---

IRON LAW: ALL WORKTREE OPERATIONS MUST USE `gmc wt <subcommand>`. NEVER INVENT `gmc add`, `gmc rm`, `gmc prune`, `gmc clone`, OR OTHER TOP-LEVEL WORKTREE COMMANDS.

# gmc

Invocation hint: `[commit|wt add <name>|wt prune|wt share|wt sync|tag] [--dry-run] [--sync] [-b branch] [--force] [--auto] [-a] [-y]`

Use `$ARGUMENTS` and the user's words to route into exactly one mode.

Copy this checklist and check off items as you complete them:

- [ ] Step 0: Parse intent [BLOCKING]
  - [ ] Classify the request as `commit`, `wt add`, `wt prune`, `wt share`, `wt sync`, `wt rm`, `wt ls`, `wt dup`, `wt pr-review`, or `tag`
  - [ ] If the intent is unclear, ask one focused question before running commands
- [ ] Step 1: Validate context [BLOCKING]
  - [ ] Confirm `gmc` exists
  - [ ] Confirm the current directory is a git repo when the command needs repo context
  - [ ] If the action depends on GitHub state, confirm `gh` works first
- [ ] Step 2: Preview plan [REQUIRED]
  - [ ] Show the exact command you plan to run
  - [ ] For destructive or bulk actions, prefer `--dry-run` first
- [ ] Step 3: Execute exactly one workflow
  - [ ] `commit`
  - [ ] `wt add`
  - [ ] `wt prune`
  - [ ] `wt share`
  - [ ] other `gmc wt` subcommand or `tag`
- [ ] Step 4: Report result
  - [ ] State the exact command run
  - [ ] Report the created path, cleaned worktrees, synced resources, or generated message
  - [ ] State what was not run

## Routing

- `commit` uses top-level `gmc`
- Any worktree action uses `gmc wt <subcommand>`
- If the user says `gmc add`, translate it to `gmc wt add` and say so
- Worktree lifecycle requests use this skill under the global routing rule; other generic Git requests do not trigger it without an explicit gmc request

## Common commands

- `gmc`
- `gmc -y`
- `gmc -a -y`
- `gmc -a -y -p "context"`
- `gmc --dry-run`
- `gmc wt add <name>`
- `gmc wt add <name> --sync`
- `gmc wt add <name> -b <branch>`
- `gmc wt ls`
- `gmc wt rm <name>`
- `gmc wt rm -D <name>`
- `gmc wt prune`
- `gmc wt sync`
- `gmc wt share ls`
- `gmc wt share add <path> --strategy copy`
- `gmc wt share add <path> --strategy link`
- `gmc wt share sync`
- `gmc tag`

## Workflow: commit mode

- Use top-level `gmc`, not `gmc wt`
- Default to interactive `gmc` unless the user explicitly wants automation
- Ask before `gmc -a -y` because it stages all files and auto-confirms
- Use `gmc --dry-run` when the user wants a suggested message without committing

## Workflow: create worktree

- Use `gmc wt add <name>`
- Use `-b <branch>` only if the user provided a base branch or asked for one
- Use `--sync` only when the user wants the latest base first
- After creation, report the worktree path

## Workflow: prune merged worktrees

- Run `gmc wt prune --dry-run` first to preview
- Use `gmc wt prune --pr-aware` to check PR state before pruning
- Ask before actual removal
- Use `--force` only with explicit user approval

## Workflow: shared resources

- For discovery, run `gmc wt share discover --dry-run`
- Use `gmc wt share discover --auto` only with explicit approval
- For manual control, use `gmc wt share add`, `gmc wt share ls`, `gmc wt share rm`, or `gmc wt share sync`
- Prefer `copy` for env files or local config
- Prefer `link` for large identical directories such as `node_modules` or `.venv`

## Confirmation gates

- Ask before `gmc -a -y`
- Ask before `gmc wt rm -D <name>`
- Ask before any non-dry-run prune
- Ask before `gmc wt share discover --auto`
- Ask before `--force`

## Do not

- Do not run `gmc add`, `gmc rm`, `gmc prune`, `gmc clone`, or `gmc share`
- Do not skip dry-run for cleanup when a preview exists
- Do not use `--auto`, `-a -y`, `-D`, or `--force` without explicit user approval
- Do not guess worktree paths, base branches, or GitHub state
- Do not mix commit mode and worktree mode in the same command
