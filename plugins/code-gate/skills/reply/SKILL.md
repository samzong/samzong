---
name: reply
description: Draft a paste-ready Code Gate review reply. Use when the user asks for code-gate reply or wants a concise maintainer response.
---

# Reply

Use this skill to draft a concise Code Gate review reply.

## First Step

Read `../../shared/protocol.md` before acting. Treat it as the source of truth for reply behavior and output.

## Gate

Run only the `reply` gate.

## Behavior

- Draft a paste-ready review-thread reply.
- Lead with the conclusion and cite key evidence briefly.
- Do not require a case file.
- Do not create a case file if none exists.
- Do not update case state unless the case file is explicitly needed for context and the protocol requires an update.
- Do not run another gate.

## Output

Use the protocol output contract and include `Reply`:

```md
Verdict: <short sentence>
Why: <short paragraph>
Missing evidence: <short list or "None">
Next action: <one concrete next step>
Case file: <absolute path>
Reply: <paste-ready sentence or short paragraph>
```
