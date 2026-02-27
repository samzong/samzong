# Output Contract

The generator writes repo-local artifacts under the install root:

```text
<install-root>/
  .agents/
    skills/
      .repo-skill-generator-manifest.json
      <repo>-coding/
      <repo>-review/   # present only when review evidence passes sufficiency gates
  .claude/
    skills -> ../.agents/skills
```

When `--module` is provided, the coding skill name becomes:

```text
<repo>-coding-<module>
```

The review skill remains repo-level.

All generated prose and evidence are written in English.

Runtime summary JSON includes a `review_generation` section with gate metrics and skip reason when review output is omitted.
The same section also reports the selected review evidence preset (`default`, `solo`, or `strict`).
