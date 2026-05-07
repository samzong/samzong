---
name: adversarial
description: Challenge the current Steward story and append adversarial evidence without changing status. Use when the user asks for steward adversarial or wants hidden assumptions tested.
---

# Adversarial

Use this skill for the Steward adversarial pass.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for case file discovery, update rules, and output.

## Gate

Run only the `adversarial` gate.

## Behavior

- Try to break the current story.
- Identify missing evidence, hidden assumptions, and regression risk.
- Apply the Requirement Deletion Lens from the shared protocol when the story
  depends on a debatable requirement, new abstraction, workflow, or automation.
- Append a decision log entry.
- Do not change status.
- If no valid case file exists, auto-create a minimal case file first, write it to the current pointer, then run adversarial.
- Do not summarize neutrally; this is a challenge pass.
- Do not implement product or code changes.

## Output

Use the protocol output contract:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
```
