## Mode: ship

Inspect the final artifact and reuse the existing review and verification packet. A shipping workflow's required `liability-review` verdict must cover the final target; update it for any new delta under that skill's drift/re-review rules. Mirror does not produce another defect list or repeat completed checks.

Add only a missing material risk disposition: whether the verified result meets owner intent, what remains uncertain, and what would expose or reverse a failure. Do not invent a residual risk merely because an output field exists. Missing material evidence or unresolved counterevidence still blocks a readiness claim.

Use these statuses for callers:

- `PASS WITH RESIDUAL RISK`: relevant verification passed, no blocker remains, and uncertainty is bounded or explicitly accepted after disclosure.
- `HOLD`: material verification, an owner decision, or risk acceptance is missing.
- `BLOCK`: the implementation is wrong, unsafe, outside scope, or contradicted by the evidence.

Report the status and any information the existing packet does not already establish:

```text
MIRROR / SHIP
Status: PASS WITH RESIDUAL RISK | HOLD | BLOCK
Contract decision: CONFIRMED | PENDING
Residual risk: <material remaining uncertainty, or no material risk identified>
Risk disposition: BOUNDED | OWNER ACCEPTANCE REQUIRED | ACCEPTED AFTER REPORT
Risk evidence: <verifier and bounds, or the exact post-disclosure owner response>
```

Include a failure signal, first diagnostic step, and safe rollback when a real remaining risk or the changed operation needs them. Never claim that “no material risk identified” proves universal safety.

`BOUNDED` requires relevant verification and no unresolved contradiction or new owner-owned trade-off. `OWNER ACCEPTANCE REQUIRED` returns `HOLD`. `ACCEPTED AFTER REPORT` requires the owner's explicit response to that exact disclosed risk; do not infer it from a prior implementation or shipping request. That prior authority nevertheless remains valid for unchanged scope with `BOUNDED` risk.

If the artifact changes, assess the delta, update the final target and affected review/verification evidence, and revisit only the risk decisions the delta changes. Never publish an artifact whose final content is outside the reviewed target. A fingerprint change alone does not revoke the owner's authority or require rerunning unrelated valid checks.
