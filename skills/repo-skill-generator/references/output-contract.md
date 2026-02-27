# Output Contract

The generator writes repo-local artifacts under the install root:

```text
<install-root>/
  .agents/
    skills/
      .repo-skill-generator-manifest.json
      <repo>-coding/
      <repo>-review/
  .claude/
    skills -> ../.agents/skills
```

When `--module` is provided, the coding skill name becomes:

```text
<repo>-coding-<module>
```

The review skill remains repo-level.

All generated prose and evidence are written in English.
