# Full collision audit checklist

Run for every finalist. **RED = drop.** **YELLOW = note, penalize score.** **GREEN = proceed.**

User mandated full audit (2026-06-07).

## 1. npm

```bash
npm view <name> name 2>/dev/null || echo "GREEN: npm free"
```

Also check likely variants: `<name>-cli`, `@<name>/cli`

## 2. GitHub repository search

```bash
gh search repos "<name>" --limit 10 --json nameWithOwner,description
```

RED if: same name + agent/memory/cli/rust/shell/coding in description.

## 3. GitHub org/user squat

```bash
gh api users/<name> 2>/dev/null | jq -r '.login // "GREEN"'
```

YELLOW if user exists; OK if `samzong/<name>` repo path still free.

## 4. crates.io (Rust)

```bash
cargo search <name> --limit 5 2>/dev/null || curl -s "https://crates.io/api/v1/crates/<name>" | jq -r '.crate.name // "GREEN"'
```

## 5. Go module

```bash
curl -s "https://proxy.golang.org/github.com/samzong/<name>/@v/list" | head -1
# GREEN if 404/empty for unknown projects
```

## 6. Domain spot check (manual or curl)

Check availability signal (not purchase):
- `<name>.dev`
- `<name>.io`
- `<name>.sh` (CLI tools)

```bash
# Quick HEAD — interpret cautiously
curl -sI "https://<name>.dev" | head -1
```

YELLOW if active product site; GREEN if NXDOMAIN or parked.

## 7. Semantic competitor search

Web search or:
```bash
gh search repos "<name> agent memory" --limit 5 --json nameWithOwner,description
gh search repos "<name> coding cli" --limit 5 --json nameWithOwner,description
```

RED if positioning overlap >50% with finalist.

## 8. Portfolio matrix collision

Read `portfolio-matrix.md`:
- Same slot + confusable name?
- Story pitch already uses this metaphor?

## 9. Steipete pass (Lane B or daily CLI)

Ask:
1. Is it a verb the user already says? ("pick an issue")
2. One syllable beats two?
3. Would this be mistaken for a git subcommand or POSIX util?

RED for Lane B if activity noun only (scout, radar) without user override.

## 10. CLI ergonomics

```bash
# Length
echo -n "<name>" | wc -c   # must be ≤6

# Shell friction
echo <name> | rg '^[a-z][a-z0-9]*$'  # lowercase alphanumeric only
```

## Audit record template

```markdown
| Name | npm | gh repo | crate | go | domain | semantic | matrix | steipete | CLI | Verdict |
|------|-----|---------|-------|----|---------|---------|---------|---------|-----|---------|
| barrow | GREEN | GREEN | GREEN | — | GREEN | GREEN | GREEN | n/a | GREEN | PASS |
```

## Fast audit mode

User says `/namecraft audit <name>` — run steps 1–7 only, skip intake/diverge.

## After openclaw / oneira lessons

- Never recommend on "sounds good" without npm + GitHub
- Dream/memory names: extra semantic search pass
- Verb names: npm lock check first (pick lesson)