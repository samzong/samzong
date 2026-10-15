# Independent reviewer

Honor explicit user reviewer or model constraints. Otherwise prefer a fresh
in-runtime subagent that receives only the self-contained packet and evidence
contract, never a fork of this session (`fork_turns: "none"` where supported).
Independence requires separate context, not a different model or vendor.

Use Confer as a fallback when that path is unavailable or fails to produce a
valid result. Choose an available reviewer from
[`reviewers.json`](../assets/reviewers.json); its entries are exact `agent`,
`model`, and `reasoning_effort` presets, not a mandatory attempt order. Read
the current `confer` skill only when using that path, and follow its room,
seat, and delivery mechanics; never invoke participant CLIs directly.
Liability Review owns the evidence packet and attempt deadline, not Confer
lifecycle semantics. Never install or repair a review transport during a
read-only review.

For Confer, resolve the current host agent and pass it as
`host_agent` when creating rooms. Confirm the returned `room.host_agent`; if
the author cannot be determined, return `INPUT_ERROR` instead of claiming an
independent pass.

Use the same room for fallback attempts, following Confer's current
host-session reuse rule. When a new room is needed, request only the selected
reviewer seat. In a reused room, use `add_seat`
to start the review in a fresh private seat. Confirm from `create_room` or
`add_seat` that the actual seat matches the requested agent, model, and effort
and was not replaced. For each later attempt, use `add_seat`
with a short unique name in the same room and perform the same check. Retire an
unexpected replacement without messaging it, then try another available reviewer.

Send every reviewer packet privately to only its seat. Poll the same delivery
with `wait_output` calls no longer than `60000` milliseconds until it completes
or reaches a total attempt deadline of `600000` milliseconds. A timed-out poll
or `session_pending` is live work, not a failed attempt. Advance only after an
explicit failed delivery, the total attempt deadline, or a completed but
invalid result. If Confer MCP registration is missing, this fallback is
unavailable. For each required pass, stop after the first valid independent
result; do not run another review solely for model diversity.

The message must be self-contained and contain the repository path, exact
target refs, target fingerprint, task, accepted goal and exclusions, known
supported-use context (unknowns labeled), acceptance evidence, the Review
objective criteria from SKILL.md, evidence contract, and required JSON shape.
It must instruct the reviewer not to use Confer, delegate, invoke review skills,
edit files, stage, commit, or write inside the repository. Do not send
the primary review's reasoning beyond the blocking findings in a refutation
packet.

For refutation, send every blocking finding in one packet:
`{"repo", "fingerprint", "target", "findings": [{"id", "priority", "file",
"line", "failure", "evidence", "risk", "disposition"}]}`. Require exactly one result per finding, in
the same order:

```json
{"results":[{"id":"F1","verdict":"STANDS|REFUTED|UNDECIDED","evidence":[{"level":"E0|E1","ref":"<command or file:line>","quote":"<observed output or quoted code>"}],"note":"<what was checked>"}]}
```

For a finder pass, send the exact resolved target and fingerprint without any
primary findings. Require:

```json
{"findings":[{"priority":"P0|P1|P2","title":"<title>","file":"<path>","line":1,"failure":"<failure path>","evidence":[{"level":"E0|E1","ref":"<command or file:line>","quote":"<observed output or quoted code>"}],"risk":"<user/operational impact, supported exposure and recovery>","disposition":"<block or defer, cost of delay versus correction cost/risk>","correction":"<smallest correction>"}]}
```

Extract one JSON object from a plain or fenced response, then reject malformed
shapes, missing or extra result entries, evidence below E0/E1 for a blocking
claim, and any result that cannot be bound to the exact fingerprint. Name the
completed reviewer agent in the verdict's `Tier` and `Self-audit` lines.

Record a reviewer using the author's agent as
`<reviewer agent> (same agent, separate context)` in the verdict.
If no available path produces a valid result, record
`independent passes: not available`. A `T2` target then cannot reach
`ACCEPT_LOCAL` or `MERGE`: return `REQUEST_CHANGES` (local) or `HOLD` (pr)
naming the pending pass. The user may lift this with the literal reply
`豁免`, recorded in the verdict.
