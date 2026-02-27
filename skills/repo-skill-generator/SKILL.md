---
name: repo-skill-generator
description: Generate repo-local coding and review skills from a repository's git history and GitHub PR review activity. Use when asked to create, refresh, or update repository-specific coding/review skills, learn from PRs, analyze commit history, extract coding patterns, or generate coding guidelines for the current repo or a specific module.
---

# Repo Skill Generator

## Overview

Generate two repo-local skills from real repository history:

- a `coding` skill derived from git commits and diffs
- a `review` skill derived from GitHub PR review activity

The generated artifacts are installed into:

- `./.agents/skills/` as the canonical repo-local source
- `./.claude/skills` as a symlink pointing to `./.agents/skills`

All generated content is written in English.

## Hard Gates

- Stop if the target `repo-root` is not a git repository. → Fix: `cd` to a valid git repo or pass `--repo-root` pointing to one.
- Stop if `gh` is missing when generating review data. → Fix: tell the user to install GitHub CLI (see https://cli.github.com/).
- Stop if `gh` is unauthenticated. → Run `gh auth status` before generating review data; if not logged in, tell the user to run `gh auth login`.
- Stop if the install target cannot be written. → Fix: check directory permissions or use `--install-root` to specify a writable path.
- Do not touch skills outside the generator-managed coding/review skill names.

## Default Workflow

### 1) Pre-flight checks

```bash
gh auth status
```

Confirm `gh` is authenticated. If not, tell the user to run `gh auth login`.

### 2) Generate skills

Pick the command that matches the use case:

```bash
# Current repo
python3 skills/repo-skill-generator/scripts/generate_repo_skills.py

# Different repo
python3 skills/repo-skill-generator/scripts/generate_repo_skills.py \
  --repo-root /path/to/repo

# Module-level coding skill only
python3 skills/repo-skill-generator/scripts/generate_repo_skills.py \
  --repo-root /path/to/repo \
  --module src/router

# Safe install root for testing
python3 skills/repo-skill-generator/scripts/generate_repo_skills.py \
  --repo-root /path/to/repo \
  --install-root /tmp/repo-skill-generator-smoke
```

### 3) Verify output

After generation completes, confirm all three:

1. `generator-meta.json` exists in each generated skill directory.
2. `.repo-skill-generator-manifest.json` exists at the skill root.
3. `.claude/skills` symlink points to `.agents/skills/`.

If any check fails, review the script's stderr for which step errored and re-run from step 2.

## What The Script Produces

For each generated skill:

- `SKILL.md`
- `profiles/*.json`
- `profiles/*-summary.md`
- `references/evidence.md`
- `references/anti-patterns.md` or `references/blocking-patterns.md`
- `references/examples.md`
- `generator-meta.json`

At the skill root:

- `.repo-skill-generator-manifest.json`

## Notes

- The generator collects real git and GitHub review evidence before producing skills.
- It writes repo-local skill directories and installs the `.claude/skills` symlink.
- The analyzer is conservative when evidence is weak and says so through the generated evidence layer.

## References

- Output contract: [references/output-contract.md](references/output-contract.md)
- Profile fields: [references/profile-fields.md](references/profile-fields.md)
