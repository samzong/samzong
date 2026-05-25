---
name: handoff
description: >
  Export current session state as a structured HANDOFF.md for another LLM to continue work.
  Captures: current goal, files changed, what was tried, what worked, dead ends, and next steps.
  Use when: user says "handoff", "export state", "save progress", "session export",
  "pass to another LLM", "clone yourself", "create handoff", "wrap up", "done for now",
  "bye", or at session end when ongoing work needs continuity. Output is a self-contained
  prompt that another LLM can use to resume work exactly where this session left off.
---

# Handoff

Export current session state to `./HANDOFF.md` so another LLM can continue seamlessly.

## What to Capture

Gather all of the following from the current session context:

1. **Current Goal** — What the user is trying to accomplish (one sentence)
2. **Status** — Where things stand right now (in progress / blocked / partially done)
3. **Files Changed** — List every file modified, created, or deleted this session with a one-line summary of each change
4. **What Was Tried** — Approaches attempted, in chronological order
5. **What Worked** — Successful approaches and confirmed solutions
6. **Dead Ends** — Failed approaches and why they failed (save the next LLM from repeating mistakes)
7. **Key Decisions** — Important architectural or design choices made and their rationale
8. **Open Questions** — Unresolved ambiguities or decisions deferred to the user
9. **Next Steps** — Concrete, actionable items the next session should start with

## Output Format

Write to `./HANDOFF.md` using this template:

```markdown
# Handoff — {project name}

**Date**: {date}
**Branch**: {current branch}
**Status**: {in progress | blocked | partially done}

## Goal

{One sentence describing what the user wants to accomplish}

## Files Changed

| File | Change |
|------|--------|
| `path/to/file` | Brief description |

## What Was Tried

1. {Approach 1} — {outcome}
2. {Approach 2} — {outcome}

## What Worked

- {Confirmed solution or successful approach}

## Dead Ends (Do Not Retry)

- {Failed approach} — {why it failed}

## Key Decisions

- {Decision}: {rationale}

## Open Questions

- {Unresolved question}

## Next Steps

1. {First thing the next session should do}
2. {Second thing}
3. {Third thing}

## Context Files

Key files the next LLM should read first:
- `path/to/important/file` — {why}
```

## Rules

- Be factual. Only include what actually happened, not speculation.
- Include enough context that an LLM with zero prior knowledge of this session can pick up immediately.
- Do not pad. If a section is empty (e.g., no dead ends), write "None" and move on.
- The HANDOFF.md must be self-contained — no references to "the conversation above".
