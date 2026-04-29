---
name: sync
description: Refresh the current Code Gate case file without changing status. Use before handoff, tool switching, restart, or when the user asks for code-gate sync.
---

# Sync

Use this skill to refresh Code Gate case state.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, update rules, and output.

## Gate

Run only the `sync` gate.

## Behavior

- Refresh the current root-level case file.
- Do not change status.
- Update meaningful evidence, blockers, identifiers, verification result, or rejected path when they changed.
- Do not update for routine file reads or repetitive search noise.
- If no valid case file exists, auto-create a minimal case file first, then run sync.
- Do not run another gate.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
