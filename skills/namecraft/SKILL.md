---
name: namecraft
disable-model-invocation: true
description: >
  Project naming for samzong's Agent Bench portfolio. Dual-lane naming
  (poetic flagship vs steipete verb CLI), ≤6-letter hard limit, full collision
  audit, matrix fit scoring, and storytelling pitch. Use ONLY when the user
  explicitly invokes /namecraft or asks to run the namecraft skill for naming
  a new project, renaming, or portfolio matrix work. Do not auto-invoke on
  casual mentions of "name" or "rename".
---

# Namecraft

Name new projects and renames for the **Agent Bench** portfolio.

Read before every run:
- `references/portfolio-matrix.md` — slot map, backfilled projects, story script
- `references/naming-sessions.md` — prior decisions (Barrow, merge-scout, HiClaw)
- `references/reject-lexicon.md` — hard rejects
- `references/audit-checklist.md` — collision audit commands

## Worldview (non-negotiable)

**The Agent Bench** — tools that let coding agents work like senior engineers.

Two materials coexist in one story:
- **Workshop** — shaping, parallel runs, signals at the bench (lathe, gmc, mote)
- **Strata** — what the bench produces sinks underground: layered, excavated, dreamed (barrow)

CLI name = brand name. No separate marketing alias.

English only. No Chinese brand names.

## Lane selection (Step 2)

| Lane | When | Style | Examples |
|------|------|-------|----------|
| **A — Strata** | Flagship, worldview, memory/depth products | Poetic noun, myth/literary/craft metaphor, memory or earth texture | barrow, stele, alethe |
| **B — Bench** | Utility CLI, daily-driver tools | Verb-first, steipete line, Unix tool family | pick, recall, lathe* |

\* `lathe` is workshop craft but short enough to be a proper noun tool — treat as **Bench craft** slot, not Strata.

**Decision tree:**
1. Is this a flagship / narrative anchor / memory layer? → Lane A
2. Is this a CLI the user types 20× per day? → Lane B
3. If both (embeddable crate + CLI): pick ONE word ≤6 letters; prefer matrix slot over lane purity

## Hard constraints

- **Length:** ≤6 letters for repo, crate, npm, and CLI binary. No hyphens in the primary name.
- **Collision:** Full audit before recommending (see `references/audit-checklist.md`). One RED = drop.
- **Implementation leak:** Name must not encode internal algorithms (e.g. `merge` for merge-probability).
- **Normal words ban:** See `references/reject-lexicon.md` for default rejects; add project-specific bans in intake.
- **Matrix fit:** Name must occupy a clear slot in `portfolio-matrix.md` or justify a new slot.

## Workflow

### Step 1 — Intake

Ask or infer:

```
Product one-liner:
User action (verb):
Stack (rust/go/ts/...):
Lane A or B (or unsure):
Matrix slot (Shaping / Parallel / Strata / Discovery / Signal / Craft / Peripheral):
Flagship or utility:
Prior names considered:
Rename or greenfield:
```

If intake is incomplete, ask **at most 3** targeted questions, then proceed.

### Step 2 — Diverge (15–20 candidates)

Generate across these angles (not all required):
- Strata: earth, burial, inscription, amber, palimpsest, dream-consolidation
- Workshop: lathe, forge, bench, chisel, tap, die
- Bench verbs: pick, recall, sift, glean, tap, cast
- Short fusions: ≤6 letters only (aletir, barve, steir — only if natural to pronounce)

Tag each candidate: lane, letters, matrix slot, one-line metaphor.

### Step 3 — Reject pass

Drop any candidate that:
- Exceeds 6 letters
- Hits `reject-lexicon.md`
- Duplicates an existing portfolio name or confusable sibling
- Fails pronunciation as CLI (`barve` OK; `aletve` borderline — note in output)

### Step 4 — Full audit (mandatory)

Run checks in `references/audit-checklist.md` for top 8–10 survivors. Record GREEN/YELLOW/RED.

Steipete pass (Lane B or borderline): *Would Peter name it this? One syllable verb beats two-word compound.*

### Step 5 — Matrix fit score

For each audited survivor, score 1–5:

| Criterion | Question |
|-----------|----------|
| Metaphor precision | Does it map 1:1 to core differentiation? |
| Matrix slot | Clear place in Agent Bench story? |
| CLI ergonomics | Easy to type, no confusion with git/docker/npm builtins? |
| Collision cleanliness | All audits GREEN? |
| Story hook | One sentence in the portfolio pitch? |

Recommend the highest total. Tie-break: fewer YELLOW, better matrix narrative.

### Step 6 — Deliver

Output this structure:

```markdown
## Namecraft verdict: <recommended>

### Intake summary
...

### Top 5 (audited)
| Rank | Name | Lane | Letters | Matrix slot | Audit | Score | Story hook |
...

### Recommended: **<name>**
- Why this name
- Matrix sentence (where it sits in Agent Bench)
- CLI examples: `<name> <subcommand> ...`
- Collision summary

### Runners-up
...

### If rename: touch list estimate
(package.json, bin/, skills/, cache path, docs — enumerate)

### Portfolio pitch snippet
(2–3 sentences placing this project in the Bench story)
```

### Step 7 — Update references (when user confirms a name)

After user picks a winner:
1. Append decision to `references/naming-sessions.md` (date, name, lane, runners-up, audit notes)
2. Update `references/portfolio-matrix.md` (new row or rename old → new)
3. Do not commit unless user asks

## Subcommands (user may say)

| User says | Action |
|-----------|--------|
| `/namecraft` | Full workflow from intake |
| `/namecraft audit <name>` | Collision audit only |
| `/namecraft matrix` | Print portfolio story + slot map |
| `/namecraft rename <project>` | Intake + audit for existing repo rename |
| `/namecraft backfill` | Refresh matrix from ~/git/samzong/ |

## Anti-patterns (learned from prior sessions)

- **merge-scout** — activity word + leaks `merge` implementation; user rejected
- **Oneira** — beautiful but RED on GitHub (dreaming AI agent) + oneira.dev
- **pick** — perfect steipete but npm taken
- **oss-scout** — GREEN npm but semantic collision with OSS health tools
- **Hyphen compounds** (issue-pick) — acceptable only if ≤6 letters total impossible; user prefers single word
- **Long fusions** (Alethebarrow, Oneirstele) — user explicitly dislikes

## Related skills

- Renaming an existing repo: namecraft deliverable includes touch list; implementation uses normal agent edit flow
- Shipping renamed project: `/ship` after rename commit
