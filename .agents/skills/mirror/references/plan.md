## Mode: plan

Read the relevant code, callers, contracts, and actual input or runtime before choosing a mechanism. Establish the observable result, the information available to the caller, and the existing path that comes closest to the result. Distinguish authoritative data from rebuildable or transient state before choosing guarantees. For a consequential choice, check whether the proposed layer is necessary or compensates for a wrong owner or data-flow boundary.

Resolve technical uncertainty yourself. Ask only when an unresolved owner decision would materially change the outcome or accepted scope; batch known questions and continue independent work. Prior explicit decisions and scoped implementation authority remain valid.

Give a compact recommendation scaled to the task:

- the outcome and essential constraints;
- the chosen mechanism, strongest credible alternative, and the evidence deciding between them;
- any decision-relevant assumption and the observation that would disprove it;
- verification at the affected entrypoint, and rollback when the change needs one.

Do not turn this into a template the owner must fill out. Include only the facts and uncertainties needed to judge the recommendation. If there is no material objection, say so rather than manufacturing one.

For an explicit Mirror invocation or a workflow that needs the decision status, end with:

```text
MIRROR / PLAN
Verdict: PROCEED | HOLD | REJECT
Owner decision: NOT REQUIRED | REQUIRED — <specific unresolved choice, if any>
```

- `PROCEED`: the mechanism fits the outcome, remaining technical assumptions can be tested within authorized reversible work, and rollback is credible where needed.
- `HOLD`: a material owner decision, authority boundary, or indispensable evidence cannot be resolved within that work.
- `REJECT`: evidence contradicts the premise, the mechanism solves the wrong problem, or its cost/risk is disproportionate.

The verdict grants no mutation authority. With prior scoped authority and `PROCEED / NOT REQUIRED`, implement without another confirmation. On `HOLD` or `REJECT`, stop the affected action, explain the exact reason, and continue independent authorized work.
