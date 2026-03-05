---
name: coding-global-memory
description: >
  Cross-tool project memory system using pure Markdown files as source of truth.
  Provides /read-memory and /write-memory commands for persistent project knowledge.
  Use when: (1) starting a new session and need project context (/read-memory),
  (2) ending a session and want to persist learnings (/write-memory),
  (3) user says "read memory", "load memory", "remember", "save memory", "write memory",
  (4) user wants to check or update project knowledge base.
  Triggers: /read-memory, /write-memory, "读取记忆", "写入记忆", "保存记忆".
---

# Memory System

Pure Markdown memory files are stored at `~/.agents/memories/{project-name}/`.

## Project Name Derivation

Convert the current working directory path by replacing all `/` with `-`.

Example: `/Users/x/projects/my-app` → `-Users-x-projects-my-app`

## MEMORY.md Format

```markdown
---
updated: YYYY-MM-DD
project: {original path}
description: {one-line project purpose}
---

# {Project Name} Memory

## Index

> Sub-memory files for this project. Read only when relevant.

- [frontend.md](frontend.md) — Frontend architecture and patterns
- [backend.md](backend.md) — Backend API and data layer

## Architecture

{High-level architecture summary}

## Key Decisions

{Important technical decisions and their rationale}

## Conventions

{Code patterns, naming conventions, project-specific rules}

## Known Issues

{Active bugs, technical debt, gotchas}
```

Sections are flexible. The AI determines appropriate sections based on the project. The Index section lists sub-memory files only when they exist.

## /read-memory

1. Derive `project-name` from the current working directory.
2. Set `MEMORY_DIR` = `~/.agents/memories/{project-name}`.
3. IF `MEMORY_DIR/MEMORY.md` does not exist:
   - Print: "No memory found for this project. Use /write-memory to create one."
   - Stop execution.
4. Read `MEMORY.md`.
5. Parse `updated` from the frontmatter.
6. IF `updated` is older than 30 days:
   - Print warning: "Memory is stale (last updated: {date}). Consider running /write-memory to refresh based on current codebase."
7. Output memory contents to context.

## /write-memory

1. Derive `project-name` from the current working directory.
2. Set `MEMORY_DIR` = `~/.agents/memories/{project-name}`.
3. Execute `mkdir -p $MEMORY_DIR`.

### First Write (no existing MEMORY.md)

4. Scan project structure (top-level directories, key configuration files, `package.json`/`Cargo.toml`/`go.mod`, etc.).
5. Summarize conversation learnings.
6. Generate `MEMORY.md` with:
   - Frontmatter (`updated: today`, `project: {path}`, `description: {one-line purpose}`).
   - Sections automatically determined from the project type.
   - An Index section (initially empty, populated when sub-files are created).
7. Write to `$MEMORY_DIR/MEMORY.md`.

### Update Write (existing MEMORY.md)

4. Read existing `MEMORY.md`.
5. Summarize new learnings from the current conversation.
6. Merge new learnings into appropriate sections:
   - Append to existing sections where relevant.
   - Create new sections only if no existing section fits.
   - Remove outdated information that contradicts new learnings.
7. Update `updated` date in frontmatter.
8. Write back to `$MEMORY_DIR/MEMORY.md`.

### Splitting to Sub-files

IF `MEMORY.md` exceeds ~150 lines:

1. Identify sections that can be extracted (e.g., frontend-specific, backend-specific).
2. Create sub-files in `$MEMORY_DIR/` (e.g., `frontend.md`, `backend.md`).
3. Add entries to the Index section in `MEMORY.md`.
4. Maintain `MEMORY.md` as the summary index with cross-references.

## Memory Content Guidelines

Write memories that are:
- **Actionable**: facts that modify how to operate on this project.
- **Stable**: unlikely to change within weeks.
- **Non-obvious**: information not inferable from code review.

Do NOT memorize:
- File contents. Read the file instead.
- Temporary state (current branch, in-progress work).
- Generic knowledge (language syntax, framework basics).