## Mode: review

Judge whether the actual implementation fulfills the accepted decision with proportionate complexity. Read the diff and relevant runtime evidence. Map semantic changes to the outcome, inspect ownership and new mechanisms, and compare any material departure from the accepted plan.

`liability-review` owns code findings. Reuse its current verdict and valid verification when available; Mirror adds only the decision/value assessment it lacks. A decision review alone does not require a duplicate full code review. If code review is required by the task or shipping workflow and none exists, obtain it before claiming readiness.

Investigate a concrete decision-changing failure or contract objection when evidence suggests one; no material objection is a valid result. Do not disguise speculative demand or a style preference as a defect. If a new defect is found, record its evidence for the same liability ledger and obtain the needed targeted review; do not discard unrelated valid findings or restart the entire process solely to change report ownership.

Reuse evidence whose target behavior, relevant inputs, environment, and coverage still match. Inspect changed behavior and rerun the affected checks or explicitly fresh repository gates. Separate code correctness from product value that remains unverified.

Report only the decision-relevant assessment. When explicitly invoked or needed by a caller, include:

```text
MIRROR / REVIEW
Contract match: MATCH | DRIFT | NO CONTRACT — <reason>
Evidence: <decisive code or runtime evidence>
Unverified: <material uncertainty, or none identified>
Verdict: ACCEPT | CORRECT | HOLD | REJECT
Required correction: <smallest necessary correction, or none>
```

A confirmed in-scope correction goes back to the authorized implementation flow. Ask the owner only if correcting it would change an owner-owned decision, accepted scope, or authority boundary.
