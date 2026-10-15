---
name: mirror
description: Check consequential engineering decisions against owner intent and actual evidence. Use for material contract, data, security, operational, or irreversible risk; skip routine reversible work.
---

# Mirror

Keep the engineering decision tied to the owner's outcome. A correct implementation of an unnecessary mechanism still fails. Model agreement, an elaborate review, and green generic tests do not establish value or prove the affected behavior.

Mirror is instruction-only: `plan`, `review`, and `ship` select references, never shell subcommands. It does not grant mutation authority or create a second defect ledger.

## Activation

Use Mirror when the actual decision or change materially affects:

- architecture or an abstraction expensive to reverse;
- public API, protocol, schema, serialization, or compatibility;
- persistence, migration, deletion, recovery, or source of truth;
- authentication, authorization, secrets, privacy, or a trust boundary;
- concurrency, ownership, ordering, idempotency, retries, or a state machine;
- billing, quotas, cost, availability, latency, capacity, or an SLO;
- a production dependency or external integration;
- data, history, or infrastructure that a simple follow-up cannot restore;
- a broad refactor with uncertain blast radius;
- an unresolved owner decision or mechanism assumption that could change the target, scope, public meaning, or implementation substantially.

A file's subject, an imported library, or the word “state” alone does not activate Mirror. First determine what behavior changes. A missing easy test calls for finding a credible verifier, not automatically treating a routine edit as a consequential decision. When explicitly invoked for routine work, say the extra decision review is unnecessary and use normal verification.

## Apply the relevant mode

- [Plan](references/plan.md): before committing to a consequential mechanism.
- [Review](references/review.md): when evaluating whether an implemented change fulfills the accepted decision.
- [Ship](references/ship.md): when a shipping workflow needs residual-risk disposition for the final verified artifact.

Do not automatically emit all three reports for every consequential task. Preserve the accepted decision and reuse its evidence. Reopen only the part changed by new facts, scope, or a real owner trade-off. Read only the reference for the current mode.

## Decision discipline

- Separate owner requirements from examples, background, and agent-added assumptions. Treat a proposed mechanism as a hypothesis unless it was explicitly specified as a constraint.
- Trace existing ownership and data flow before adding another layer. Compare a credible alternative when the choice changes complexity, maintenance, or user effort; do not manufacture alternatives for an obvious edit.
- Distinguish inspectable facts, inferences, assumptions, and owner value choices. Use labels only where the distinction changes the decision.
- Investigate the most plausible decision-changing failure or objection, if one exists. Attempt to refute it with code or runtime. “No material objection found” is valid; do not invent one to fill an output field.
- State what observable result would defeat the recommendation. Verification should exercise the real entrypoint and affected contract. Never claim evidence from a check that was not run.
- Preserve the distinction between technical uncertainty the agent should resolve and owner-owned decisions. Do not claim acceptance of a risk without an explicit response to that risk. Prior scoped implementation or shipping authority persists when no such decision changes.

## Verification

Choose the narrowest credible evidence for the claim, reusing existing coverage:

- Bugs: reproduce the named symptom and retest it. Add a durable regression test only for an uncovered stable contract or non-obvious recurrence risk.
- APIs, formats, and migrations: inspect callers and old/new behavior; use representative contract or migration checks where affected.
- Data changes that could lose or corrupt authoritative user data: exercise rollback or restore on representative data and verify the recovered invariants. A recovery plan or backup alone is not proof; report unavailable recovery verification explicitly.
- Concurrency and state: identify ownership and transitions, then exercise the relevant ordering or failure path.
- Performance: use the named workload, a baseline, and measured changes; do not substitute a smaller convenient workload.
- Security/privacy: trace trust boundaries and exercise meaningful negative paths.
- UI: inspect the actual rendered state and interaction, not only an intermediate prototype.
- External tools: verify supported behavior using version-matched official material or a real invocation.
- Product value and agent policies: separate consistency checks from observed user outcomes. A parser, a model's approval, or a hypothetical scenario cannot prove real-use quality; report the actual scope of the evidence.

Stop the affected action for contradictory evidence, missing authority, or an unresolved material owner decision. Continue independent authorized work and make already-authorized corrections; a newly discovered implementation detail does not by itself require another approval.
