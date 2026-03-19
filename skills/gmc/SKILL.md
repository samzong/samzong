---
name: gmc
description: >
  Git workflow automation via `gmc` CLI: LLM-powered commit messages, worktree lifecycle management
  (bare repo pattern), PR-aware worktree cleanup, shared resource discovery and sync.
  Use when: (1) user says "gmc" and wants to create/manage worktrees, (2) user wants to clean up
  merged worktrees, (3) user wants to discover and sync shared files across worktrees,
  (4) user wants to generate commit messages with gmc, (5) user mentions "worktree", "wt",
  "gmc wt add", "gmc cleanup", "gmc share", "gmc prune", "gmc sync".
  Triggers on: gmc, worktree management, worktree cleanup, worktree share, worktree sync.
  CRITICAL: All worktree commands are subcommands of `gmc wt`, NOT `gmc` directly.
  `gmc add` is INVALID. The correct command is `gmc wt add`.
---

# gmc

`gmc` is a Go CLI at `/Users/x/go/bin/gmc` (installed via Homebrew).

## Quick Reference

| Task | Command |
|---|---|
| Commit with LLM message | `gmc -a -y` |
| Create worktree | `gmc wt add <name>` |
| Create from specific base | `gmc wt add <name> -b <branch>` |
| List worktrees | `gmc wt ls` |
| Switch worktree | `gmc wt switch` |
| Remove worktree | `gmc wt rm <name>` |
| Remove + delete branch | `gmc wt rm -D <name>` |
| Prune merged worktrees | `gmc wt prune` |
| Clone as bare repo | `gmc wt clone <url>` |
| PR review worktree | `gmc wt pr-review <PR#>` |
| Parallel dev worktrees | `gmc wt dup [count]` |
| Promote temp branch | `gmc wt promote <wt> <branch>` |
| Sync base branch | `gmc wt sync` |
| Manage shared files | `gmc wt share [add|ls|rm|sync]` |
| Suggest version tag | `gmc tag` |

## IMPORTANT: Command Structure

`gmc` has TWO top-level modes:
- `gmc [flags]` — commit mode (generate commit messages)
- `gmc wt <subcommand>` — worktree mode (all worktree operations)

**`gmc add` is NOT a valid command.** Worktree creation is `gmc wt add`.
Never run `gmc add`, `gmc rm`, `gmc prune`, `gmc clone` etc. — always prefix with `gmc wt`.

## Workflow 1: Create Worktree

When user says "add worktree X", "create worktree X", or "gmc wt add X":

```bash
gmc wt add <name>
gmc wt add <name> --sync          # pull latest base first
gmc wt add <name> -b <branch>     # from specific branch
gmc wt add name1 name2 name3      # multiple at once
```

After creation, report the worktree path. Directory names use `--` as separator (e.g., `feat--my-feature`).

## Workflow 2: Cleanup Merged Worktrees

When user says "gmc cleanup", "clean worktrees", or "prune merged":

### Option A: Quick (git-only, no GitHub check)
```bash
gmc wt prune --dry-run   # preview
gmc wt prune             # execute
```

### Option B: PR-aware (checks GitHub PR status)
Run the bundled script:
```bash
bash <skill-dir>/scripts/wt-cleanup.sh --dry-run   # preview
bash <skill-dir>/scripts/wt-cleanup.sh              # execute
```

The script cross-references each worktree's branch against GitHub PRs via `gh`:
- **MERGED PR + clean worktree** -> safe to remove (with `-D` to delete branch)
- **MERGED PR + dirty worktree** -> skipped unless `--force`
- **CLOSED PR (not merged)** -> skipped
- **No PR / open PR** -> skipped

Always show dry-run output first and confirm with user before actual removal.

## Workflow 3: Share Discovery and Sync

When user says "gmc share", "discover shared files", or "sync worktrees":

### Auto-discover shareable files
```bash
bash <skill-dir>/scripts/wt-share-discover.sh --dry-run   # preview
bash <skill-dir>/scripts/wt-share-discover.sh --auto       # add and sync
```

Scans main worktree for common shareable files:
- **Copy strategy** (isolated per wt): `.env`, `.env.local`, `.claude/settings.json`, `.claude/CLAUDE.md`, `.serena/project.yml`
- **Link strategy** (shared, saves disk): `node_modules`, `.venv`, `vendor`

### Manual share management
```bash
gmc wt share add .env --strategy copy
gmc wt share add node_modules --strategy link
gmc wt share ls
gmc wt share sync
gmc wt share rm <path>
```

Strategy guidance:
- **copy**: Files that may differ per worktree (env files, local config)
- **link**: Large identical directories (node_modules, .venv)

## Workflow 4: Commit with LLM

```bash
gmc                    # interactive: review diff, generate message, confirm
gmc -y                 # auto-confirm
gmc -a -y              # stage all + auto-confirm
gmc -a -y -p "context" # with extra context for LLM
gmc --dry-run          # generate message only
```

## Notes

- `gmc wt` uses the bare repository pattern (`.bare/` + worktree dirs as siblings)
- Worktree directory names replace `/` with `--` in branch names
- `gmc wt switch` requires shell integration: `eval "$(gmc wt init zsh)"`
- Share config lives at `.bare/gmc-share.yml` (or `.git/gmc-share.yml`)
- Always `cd` into a worktree directory before running gmc commands
- Replace `<skill-dir>` with the actual skill directory path when running scripts
