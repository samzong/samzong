---
name: liability-review
description: Read-only review of a local diff or existing PR for correctness, evidence, and maintainer risk. Use pr-eval for existing review comments.
---

# Liability Review

Decide whether a change deserves maintainer responsibility. Review the exact
artifact, not an imagined patch. Technical evidence establishes a defect; user
and operational consequences justify investment; the cost of delay determines
urgency. Findings require a concrete failure path and inspectable evidence.

This skill is read-only with respect to the repository: do not edit files,
create files anywhere inside the worktree, mutate the index, create commits,
push, post comments, submit reviews, merge, or change PR state. Behavioral
probes and scratch files live outside the repository — session scratchpad, temp
directory, or a throwaway module that references the repo by path. Running
builds and tests is allowed; gitignored build artifacts are an acceptable side
effect. Any other worktree mutation voids the review.

Use Chinese for analysis and verdicts. Keep commands, paths, symbols, and quoted
repository text in their original language.

## Choose a mode

- `local`: uncommitted, staged, branch, or commit diff in the current repository.
- `pr`: an existing GitHub PR identified by URL, number, or current branch.

Infer `pr` only when a PR is explicitly identified. Otherwise use `local`. If
the target cannot be resolved to one immutable comparison, return `INPUT_ERROR`.

## Local target adapter

Start with `git status --short --branch`, applicable repository instructions,
and the exact request. Resolve one target:

- `--staged`: `git diff --cached --binary`
- `--uncommitted`: `git diff HEAD --binary`, plus every relevant untracked file
  selected from `git status --short`; list any excluded untracked paths
- `--base <ref>`: resolve `git merge-base HEAD <ref>`, then review that base to
  `HEAD`
- `--commit <sha>`: resolve the full SHA, then review `<sha>^!`

Record the resolved refs and a fingerprint of the reviewed content with
`git hash-object --stdin`. For included untracked files, record each blob hash.

Read surrounding code and all relevant callers, tests, contracts, and canonical
owner modules. A staged target may coexist with unrelated local work, but do not
claim a runtime verifier covered the staged snapshot when other worktree changes
could have affected that command.

## PR target adapter

For `pr` mode only, read [PR target](references/pr-target.md) to resolve the
exact head, checks, and review threads before triage. Skip it in `local` mode.

## Review objective

Evaluate the accepted goal and reviewed action within owner constraints and
exclusions. Code proves behavior, not demand; do not invent user scale, product
stage, or owner priorities. Supported use comes from repository instructions,
`CONTEXT.md`, the exact request, and explicit owner statements; when none of
them states it, label it unknown and do not downgrade on that basis. Missing
context warrants a question only when it changes the decision.

Judge the patch and proposed corrections against that goal. Before judging code
quality, check that the chosen mechanism actually serves the complete outcome.
Challenge added guarantees, state, retries, fallbacks, compatibility, or controls
when they have no demonstrated role in the accepted need. A smaller diff or fewer
lines is not a substitute for this judgment; necessary behavior must remain.


- Identify who encounters the failure, under which supported workload and
  environment, and which user task or operational obligation suffers. Separate
  computational hot paths from user-critical paths; consider repeated daily
  friction and first-use blockage without automatically ranking either higher.
- Use the quantity that drives cost (files, requests, concurrency, storage), not
  total users as a proxy. An extreme benchmark or code smell alone does not
  establish real-use performance harm; missing measurements do not prove safety.
- Separate disproven candidates, unverified risks, and confirmed defects. For a
  confirmed defect, weigh benefit and cost of delay against correction effort,
  regression risk, maintenance burden, and displaced work. Explain a causal
  trade-off, not an invented numerical score. Deferral needs a reason and a
  concrete condition for reconsideration; it is not evidence that a defect is fake.
- Preserve required gates and explicit contracts. Low frequency or small scale
  does not excuse security exposure, irreversible loss, or a blocked critical
  task. Credible future exposure and long remediation lead time can justify
  action before incidents; speculative growth cannot.

## Triage

After resolving the target, classify the change. The tier is set by what the
diff touches, never by line count — a one-line change to a top-consequence
surface outranks five hundred lines of fixtures:

- `T0`: purely mechanical — generated-file refreshes, formatting, lockfiles,
  typo fixes with zero semantic delta. Run fingerprint discipline plus the
  repository gate; skip the liability gates.
- `T1`: reversible change touching no top-consequence surface. The standard
  single-pass contract.
- `T2`: the diff touches any top-consequence surface — persistence and
  migrations, security and trust boundaries, money, concurrency, public
  contracts and serialized formats — or is hard to reverse (applied
  migrations, released artifacts, protocol or schema changes). Full contract
  plus the adversarial protocol below.

Escalation is one-way and triggered only by facts: a finding, or a newly
discovered top-consequence surface. Doubt about which surfaces the diff touches
is resolved by reading until the answer is known, never by escalating. A tier is
never lowered mid-review, and an initial `T0`/`T1` call is never a reason to
stop digging. Record the tier and its trigger in the verdict. The expensive
failure mode of tiering is the innocent-looking one-liner classified low, so
enumerate the changed surfaces (see Coverage) before recording the tier.

## T2 adversarial protocol

For `T2` targets only. Independence means a reviewer that never saw this
review's reasoning: a different agent CLI, or a fresh subagent — never a
context-inheriting fork. Budget per review round: one refutation pass and at
most one finder pass.

- Refutation pass: after the primary review, hand every blocking finding
  (`P0`/`P1`) in one packet to an independent reviewer instructed to kill each
  against actual code or runtime, challenging both defect validity and the
  impact, likelihood, recovery, and blocking rationale. A valid defect may
  still merit a priority downgrade. `REFUTED` with E0/E1 evidence → withdraw or
  downgrade; `STANDS` or `UNDECIDED` keeps the finding. Disagreement without
  evidence is not a refutation.
- Finder pass: only when the primary review has zero blocking findings and the
  `T2` trigger surface is persistence, security, money, or an irreversible
  change. The independent reviewer cold-reviews the same diff under the same
  evidence contract with zero findings valid; confirmed new findings enter the
  ledger with IDs, and an empty return is recorded in `Verification`. For other
  `T2` triggers record `finder: skipped (<trigger>)`.
- Independent results are claims: verify the cited evidence before adopting or
  dropping anything, and discard any result whose fingerprint does not match
  the reviewed target.

When the protocol requires a refutation or finder pass, read
[Independent reviewer](references/independent-review.md) for delivery, evidence
packets, and unavailable-review handling. Otherwise skip that reference.

## Evidence discipline

Label the strongest evidence behind every claim:

- `E0`: executed during this review — the command and its observed output.
- `E1`: current code quoted at `file:line` with a closed causal chain.
- `E2`: external or platform semantics believed from docs or memory, not
  exercised here.
- `E3`: assumption.

Rules:

- Evidence may cite only commands actually executed during this review. Naming
  a check that never ran is fabrication, even when the conclusion happens to be
  right.
- `P0`/`P1` require every load-bearing link of the failure path at `E0` or
  `E1`. When a finding rests on an `E2`/`E3` premise, either upgrade the
  premise cheaply (run it, read the vendored source, read the authoritative
  doc) or cap the finding at `P2` / move it to `Unverified`.
- Attempt to refute each finding before reporting it: search for the guard,
  caller-side check, test, or configuration that would prevent the failure.
  Report the finding only if the refutation fails, and record what you checked.
- Record the fingerprint and relevant inputs for verification. A final verdict
  must cover the current complete target; carry earlier evidence only after the
  drift/re-review checks establish that its behavior, inputs, and environment
  still match. Do not treat a changed fingerprint as automatic invalidation of
  every independent check.

## Drift protocol

Recompute every recorded fingerprint (and `headRefOid` in PR mode) immediately
before the verdict. If anything changed:

1. Diff the drifted content against what was reviewed.
2. If the drift is disjoint from every file cited in a finding and from every
   input an executed verifier depended on, re-anchor: record `old → new`
   fingerprints, state the disjointness evidence, and continue.
3. Otherwise inspect the full delta, update affected findings, and rerun every
   load-bearing verifier whose inputs or behavior changed. Re-anchor the final
   verdict only after the complete target is covered; retain demonstrably
   unaffected evidence with its provenance. Return `INPUT_ERROR` (local) or
   `HOLD` (pr) if the new target cannot be resolved or safely reviewed within the
   current request. Never silently apply stale evidence to changed behavior.

## Coverage

Before deep review, enumerate the changed surfaces and rank them by
consequence: the top-consequence surfaces from Triage first, then everything
else. Spend depth by rank, not by file order.

- The verdict declares coverage honestly per surface: `traced` (callers and
  tests read, behavior exercised), `read`, or `skimmed`/`skipped`. One line
  suffices for a small diff. A declared gap is acceptable; silent truncation
  is not.
- `ACCEPT_LOCAL`/`MERGE` require every top-consequence surface traced; a gap
  there forces `REQUEST_CHANGES` or `HOLD` instead.
- When the diff touches a trust boundary, run the minimum security sweep and
  note it in one line: untrusted input paths, injection (shell, SQL, path,
  template), secrets in code, logs, or written artifacts, authorization
  changes, unsafe deserialization or file handling.

## Common liability gates

Evaluate only decision-relevant behavior:

1. **Need**: the patch addresses a reproduced bug or an accepted requirement
   and connects to the review objective. Reproduction alone does not justify
   investment; PR prose alone does not prove owner acceptance. An explicit
   owner request satisfies this gate; a fake-need judgment on an
   owner-requested fix is a `Deferred` observation, not a finding.
2. **Invariant and root cause**: for a bug, state the broken invariant and show
   why the patch fixes the cause rather than one symptom.
3. **Owner boundary**: the behavior lives in the canonical owner; repeated
   call-site patches are challenged when one shared seam owns the invariant.
4. **Patch mapping**: every semantic change maps to the accepted need. Flag
   unrelated behavior, compatibility scaffolding, and speculative flexibility.
5. **Correctness**: trace inputs, outputs, errors, cleanup, retries, concurrency,
   trust boundaries, persistence, compatibility, and callers only where the
   diff makes those risks relevant.
6. **Verification**: run or inspect the narrowest credible executable evidence
   for the changed behavior. Model agreement, code reading, and generic green CI
   do not replace a missing behavior-level verifier.
7. **Blast radius**: search for sibling paths, residual references, generated
   artifacts, migrations, and external contracts affected by the change.
8. **Test audit**: every added or modified test must name the behavior contract
   it protects. Tombstone shapes are findings with correction "delete", not
   "reword": tests locking error copy, flag spelling, absence of deleted
   symbols, literal mappings, or other implementation details; tests mirroring
   the implementation; test-only abstractions heavier than the behavior under
   test. The one exception mirrors the global test policy: a negative or
   regression test stands when the failure or absence it locks is itself a
   current API, security, or persistence contract that existing coverage
   misses. For any test presented as a regression guard, verify it fails against
   the pre-change code: export the base revision outside the repository with
   `git archive <base-sha> | tar -x -C <scratchpad>/base-<short-sha>`, copy
   the added or modified test files in, symlink dependency directories from
   the main worktree when needed, and run the narrowest test command there.
   Never use a worktree, checkout, or stash for this. When the base cannot be
   built or run at proportionate cost, record the test as `regression guard
   unverified` at `P2` instead of blocking. A regression test that passes on
   the unfixed base protects nothing. The
   inverse is equally a finding: deleting or weakening an assertion that
   guards a still-supported contract.

- Urgency, business impact, or forceful prose never lowers the bar; demand a
  narrower scope and stronger proof when pressure is high.
- Reject false-PR shapes: speculative hardening, refactors presented as bug
  fixes, fallback without failure evidence, test-passing fixes in the wrong
  owner, and PR claims stronger than code evidence.
- Check user/invariant, implementation/owner, and operations/rollback views,
  then choose a verdict. The final answer must not be neutral.

Verify reviewer or tool claims against code or runtime before adopting them.
Zero findings is valid. Do not manufacture nits to appear thorough.

## Findings

Report only concrete defects or missing decision evidence:

- `P0`: critical actual risk requiring immediate containment, such as widespread
  irreversible loss, an exploitable severe security breach, or a severe outage.
- `P1`: material actual risk that warrants blocking the reviewed action until
  corrected or explicitly accepted by the owner. Justify the impact, exposure,
  and recovery burden; reproducibility alone is insufficient.
- `P2`: a concrete, bounded defect suitable for follow-up without blocking the
  reviewed action; never use this priority for taste.

Separate defect validity, consequence severity, remediation priority, and the
blocking decision. `T0`–`T2` determine review depth, not defect severity. A stable
controlled reproduction proves the failure path exists, not that users commonly
encounter it; a confirmed defect does not automatically block merge or release.

For each finding, assess impact and affected scope, triggering conditions and
likelihood in supported real use, detectability, recoverability, and recovery
cost. Distinguish automatic recovery, manual repair, and irreversible loss;
losing reconstructible registration metadata is not equivalent to losing user
content. Support likelihood with observations or explicit exposure assumptions;
label it unknown when evidence is missing rather than inventing a frequency or
treating uncertainty as low risk. Evidence confidence qualifies the assessment;
it does not replace it.

State why the assessed risk and cost of delay justify blocking the specific
reviewed action, or why correction can be deferred and what would reopen it.
Preserve explicit owner constraints and mandatory verification gates; distinguish
a pending gate from a demonstrated high-impact defect.

Each finding must include `file:line` or PR evidence, the failing scenario, why
current handling is insufficient, and the smallest viable correction. Deduplicate
the same root cause. Assign each finding a stable ID (`F1`, `F2`, …) that
persists across review rounds of the same change.

## Re-review rounds

When re-reviewing the same logical change after fixes:

- Resolve and fingerprint the new target as usual.
- Verify each previously blocking finding closed with fresh `E0` evidence —
  never accept the fixer's word or a green gate alone.
- Review the full delta since the last reviewed fingerprint and trace its
  affected boundaries. Reuse checks and findings whose relevant inputs remain
  unchanged; do not repeat an independent pass unless the new delta, a changed
  failure hypothesis, or a required gate justifies it.
- Carry finding IDs forward with status `open`, `fixed-verified`, or
  `withdrawn`. Include concrete defects discovered by another workflow in this
  same ledger after verifying them. Previously accepted scope and authorization
  stay accepted absent a material change.

## Verdicts

Local mode:

- `ACCEPT_LOCAL`: exact target is stable, no blocking finding remains, top
  surfaces are traced, and the relevant verification is sufficient.
- `REQUEST_CHANGES`: a risk-justified blocking defect or required verification
  gap remains; non-blocking defects alone do not require this verdict.
- `REJECT_LOCAL`: the patch solves the wrong problem or has a fundamentally
  unacceptable owner/scope shape.
- `INPUT_ERROR`: the target is missing, ambiguous, or has drift that has not
  been resolved and covered by the updated review and verification.

PR mode:

- `MERGE`: exact head is stable, no blocking finding remains, required checks
  pass, and merge/review state is acceptable.
- `HOLD`: evidence or external state is pending, missing, or stale.
- `REQUEST_CHANGES`: the current head has a concrete correctable defect whose
  assessed risk justifies blocking merge.
- `REJECT`: the change solves the wrong problem or should not enter the codebase
  in its current shape.
- `INPUT_ERROR`: repository or PR resolution failed.

`MERGE` is impossible when the PR is draft, a required check is pending or
failing, mergeability is conflicting or unknown, a verified blocking review
thread is unresolved, required decision evidence is missing, or a head change
has not been resolved and covered by the final review and verification.

## Output

Lead with the verdict and findings. Scale the report to the diff — a small
clean diff earns a short report. Do not emit a fixed multi-section essay, and
do not embed option menus; the verdict is the decision.

```text
Verdict: <verdict>
Target: <mode, refs or PR URL, fingerprint (old → new if re-anchored)>
Objective: <accepted user outcome, reviewed action, acceptance evidence; n/a for T0>
Tier: <T0|T1|T2 — trigger; for T2: refute <reviewer id|fresh subagent|not available>, finder <reviewer id|skipped: reason|not available>>
Coverage: <per-surface depth, or "full" for small diffs; security sweep note when relevant>

Findings:
- [P1][F3][E0] <title> — <file:line>
  Failure: <concrete scenario>
  Evidence: <executed command and output, or quoted code>
  Risk: <impact/scope; real-use likelihood and basis or unknown; detectability; recovery/cost>
  Disposition: <block or defer; cost of delay versus correction risk/cost; reopen condition if deferred>
  Refutation: <what was checked that could have killed this finding>
  Correction: <smallest viable change>

Verification: <commands → results, each bound to the fingerprint it ran under>
Unverified: <missing evidence, or none>
Self-audit: fingerprints <clean|re-anchored|non-disjoint drift>; probes outside repo <yes|n/a>; all cited commands executed <yes>; independent passes <reviewer id|reviewer id (same agent, separate process)|fresh subagent|not available|n/a>
```

Omit `Findings` when empty. Keep non-blocking observations to at most three,
labeled `Deferred`; they do not change the verdict. The self-audit line is
mandatory: answer it from what actually happened, and a dirty answer must be
stated in the verdict, never silently normalized.
