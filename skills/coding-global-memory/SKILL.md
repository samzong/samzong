---
name: coding-global-memory
description: >
  Read, write, and sync project memory stored as Markdown under
  `~/.agents/memories/{project-name}/`. Use when starting work and needing
  project context, when the user asks to read or update memory, or when ending
  a session and preserving stable learnings. Triggers: "read memory", "load memory",
  "write memory", "save memory", "update memory", "sync memory", "refresh memory",
  "读取记忆", "加载记忆", "写入记忆", "保存记忆", "更新记忆", "同步记忆".
---

# Coding Global Memory

## Setup

1. Derive `project-name`: replace all `/` in CWD with `-`.
   Example: `/Users/x/projects/my-app` → `-Users-x-projects-my-app`
2. Set `MEMORY_DIR` = `~/.agents/memories/{project-name}/`.

All workflows below assume setup is done.

## Memory Layout

```
~/.agents/memories/{project-name}/
├── MEMORY.md          # Main file (frontmatter: updated, project, description)
└── {topic}.md         # Optional sub-files, split by project's actual modules
```

Sub-file topics should be derived from the project's real structure — not from a fixed list. Analyze the codebase to determine what modules warrant separate memory files.

MEMORY.md sections: Index (only if sub-files exist), Architecture, Key Decisions, Conventions, Known Issues. Sections are flexible.

## Read Memory

1. If `MEMORY.md` does not exist → report "No memory found." and stop.
2. Read `MEMORY.md`. If `updated` is older than 30 days, warn about staleness.
3. Read sub-files only when the current task needs them.
4. Summarize relevant facts into working context. Do not paste entire memory.

## Write Memory

1. Run `mkdir -p $MEMORY_DIR`.
2. If `MEMORY.md` exists → read it first, then merge new stable learnings. Remove outdated statements.
3. If `MEMORY.md` does not exist → scan project structure, summarize stable learnings, create new file.
4. Update the `updated` date in frontmatter.
5. Write back to `MEMORY.md`.

## Splitting Rules

If `MEMORY.md` exceeds ~150 lines:
- Extract stable sections into sub-files.
- Add them to the Index.
- Keep `MEMORY.md` as summary and navigation.

## Memory Quality

Write only what is **actionable**, **stable**, and **non-obvious**.

Do not store: full file contents, temporary branch state, scratch notes, generic language/framework knowledge.

## Anti-Patterns

- Writing memory before checking if older memory exists.
- Dumping raw code when a short summary suffices.
