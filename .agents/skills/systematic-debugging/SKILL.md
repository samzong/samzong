---
name: systematic-debugging
description: Diagnose bugs, failed tests, incidents, or unexpected behavior before changing code. Find the cause and verify the correction with a narrow feedback loop.
---

**Reply language**: use Chinese for all analysis, reports, verdicts, and recommendations. Keep file references (`path/to/x.ts:42`), symbols, and Git objects (branches, hashes, and PR numbers) in their original English form.

# Systematic Debugging

## Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Establish an evidence-backed failure mechanism before proposing a fix. Use only the steps below needed to explain the failure and verify the correction; they are not a checklist to exhaust.

## When to Use

Any technical issue: test failure, bug, unexpected behavior, performance problem, build failure, integration issue.

**Especially when:**
- You already tried 1-2 fixes that didn't work
- "Just one quick fix" feels obvious
- Under time pressure
- Previous fix didn't stick

## Phase 0: Build a Feedback Loop

**This is the skill. Everything else is mechanical.**

Start by reading the reported error, relevant code, logs, configuration, and recent changes. Use that evidence to form testable hypotheses and build the narrowest agent-runnable signal before changing behavior. Prefer a fast deterministic reproduction; incident investigation may instead begin with a captured trace, log row, or persisted state that can be rechecked.

Choose the cheapest existing signal that can distinguish the failure from a correct result. The options below are alternatives, not a sequence; stop building the loop once it provides credible feedback.

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Browser loop** via `browser-cdp` — use its supported transport to assert DOM, console, or network behavior.
5. **Replay a captured trace** — save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness** — minimal subset of the system (one service, mocked deps) that exercises the bug code path with a single function call.
7. **Property / fuzz loop** — when input variation is relevant, use a bounded sample targeting the failure hypothesis.
8. **Bisection harness** — if the bug appeared between two known states, automate "boot at state X, check, repeat" so `git bisect run` works.
9. **Differential loop** — same input through old-version vs new-version (or two configs), diff outputs.
10. **HITL bash script** — last resort. Drive the human with a structured loop so the captured output still feeds back.

### Iterate on the loop itself

Improve the loop only when its current cost or noise prevents diagnosis:
- Faster? Cache setup, skip unrelated init, narrow scope.
- Sharper signal? Assert on the specific symptom, not "didn't crash".
- More deterministic? Pin time, seed RNG, isolate filesystem, freeze network.

Do not optimize a sufficient loop instead of fixing the evidenced fault.

### Non-deterministic bugs

Use bounded repetition, controlled scheduling, or captured traces to distinguish hypotheses. Record attempts and failures; choose the budget from the observed rate and cost. Stop when the evidence is sufficient or the next attempt cannot answer a new question. A low reproduction rate alone does not justify an unbounded stress run.

### When you genuinely cannot build a loop

Continue read-only investigation while existing code or incident evidence can distinguish hypotheses. State what remains unverified and what each hypothesis predicts. When the next step needs unavailable evidence, ask for the specific environment access or captured artifact, or permission for temporary production instrumentation. Do not change behavior or claim a verified fix until a credible signal can test the proposed correction.

## Phase 1: Root Cause Investigation

Use the relevant steps until the failure mechanism and correction verifier are established:

1. **Read the error completely.** Full stack trace, line numbers, error codes. Errors often contain the exact answer — do not skip past them.
2. **Reproduce when feasible.** If you cannot trigger it reliably, use the incident evidence below to test hypotheses and identify the missing verification signal.
3. **Check recent changes.** `git diff`, recent commits, new deps, config changes, environment differences.
4. **Instrument an unresolved boundary** only when existing evidence cannot locate the failure. Capture the minimum relevant input and output without exposing secrets; do not instrument every layer by default. Production instrumentation requires authorization.
5. **Trace data flow backward.** Where does the bad value originate? What called this with it? Keep tracing until you reach the source. Fix at the source, not at the symptom.

### Incident evidence

For production incidents or abnormal behavior:

- Reconstruct the user-visible timeline. If an exact timestamp or actor is unavailable, mark it `UNKNOWN` and name the missing artifact.
- Trace `entrypoint -> callsite -> state mutation -> output`. Root-cause claims need a mechanism and a re-checkable witness such as a log row, DB row, command output, returned payload, or file/line.
- Check workers, queues, retries, callbacks, cron jobs, sessions, or parallel writers when the failure mechanism could depend on them.
- Separate symptom, trigger, root cause, and contributing factors. Record competing hypotheses checked, unresolved hypotheses, recurrence risk, and whether state was preserved, restored, overwritten, or lost.
- If new evidence overturns an earlier hypothesis, correct it explicitly.

## Phase 2: Pattern Analysis

- Compare a working example when it can distinguish the remaining hypotheses.
- Read the relevant execution path and contract of an external reference, including edge cases the proposed correction depends on.
- Investigate differences that could explain the failure; do not inventory unrelated differences.

## Phase 3: Hypothesis

- State one hypothesis clearly: "I think X is the cause because Y."
- Test with the smallest possible change. One variable at a time.
- If wrong, form a new hypothesis. Do not stack fixes on top of each other.
- "I don't understand X" is a valid state. Say it and investigate.

## Diagnosis Exit Gate

Before Phase 4, write each item with a re-checkable witness, or `UNKNOWN` plus the missing artifact. An item that cannot apply gets one line saying why.

1. **Reporter claims.** Each claimed symptom, impact, and scope → evidence → holds / does not hold / unverified. Never repeat an unverified impact claim as fact.
2. **Current state.** Code and runtime changes since the report (`git log --since=<report date>`, recent logs or metrics). The failure may already be mitigated, or worse.
3. **Same mechanism elsewhere.** Other callers, environments, and deployments that reach the same faulty path.
4. **Detection gap.** Why the failure ran unnoticed, and which signal would have caught it.
5. **Residual damage.** State lost, delayed, or corrupted, and whether the correction alone repairs it.

In a delivery loop, a fresh independent subagent tries to refute items 1–5 when the runtime supports delegation. Adopt its claims only after checking their evidence.

## Phase 4: Implementation

1. **Verify the correction through the Phase 0 signal.** Rerun the reproduction across the fix, or use a representative replay or focused behavior check that exercises the evidenced failure mechanism. Historical evidence can establish what happened; it cannot alone prove a correction works.
2. Make ONE change addressing the root cause. No "while I'm here" cleanup.
3. Verify the correction through the loop and required affected checks. Reuse unchanged evidence; do not rerun the same signal merely to complete another phase.
4. Persist the loop as a test only when the global test policy justifies it: a stable behavior contract that existing coverage misses. Otherwise keep the loop evidence in the report and add no test.

## Phase 4.5: Repeated Failed Corrections

After repeated failed corrections, stop speculative edits and return to the
feedback loop and root-cause investigation. Continue authorized investigation;
the number of failures alone does not establish an architectural defect.

Patterns that warrant checking the design boundary:
- Each fix reveals a new problem in a different place
- Fixes require "massive refactoring" to land
- Each fix creates a new symptom elsewhere

Use these observations to test whether the failure crosses an ownership or
design boundary. Ask the user only if the verified correction changes accepted
scope, product semantics, compatibility cost, or another owner decision. An
in-scope technical correction remains authorized.

Escalate a design decision only when the investigation establishes one.

## Diagnosis Mode Report

When entering diagnosis mode, do not edit code. Return:

1. observed failures;
2. verified facts;
3. current hypothesis;
4. suspected blast radius;
5. missing artifact or test needed to proceed;
6. the smallest next verification step.

## Red Flags — Stop and Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try X and see if it works"
- "I see the problem" (before tracing data flow)
- Another speculative edit without a new distinguishing signal
- Proposing a solution before gathering evidence
- Each fix reveals a different problem → test whether they share a cause or cross the accepted design boundary

## Rationalization Prevention

| Excuse | Reality |
|---|---|
| "Simple bug, don't need the process" | Simple bugs have root causes too. The process is fast for them. |
| "Emergency, no time for the process" | Systematic debugging is faster than thrashing. Measure it. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll verify after confirming the fix" | Unverified fixes do not stick. Red→green through the loop proves it. |
| "Multiple fixes at once saves time" | Cannot isolate what worked. Creates new bugs. |
| "I see the symptom, let me fix it" | Symptoms ≠ root cause. |
| "One more speculative fix" | Return to a verifier that can distinguish causes. |

## When Investigation Reveals "No Root Cause"

If investigation genuinely shows the issue is environmental, timing-dependent, or external:

1. You have completed the process.
2. Document what was investigated.
3. Implement appropriate handling (retry, timeout, clear error message, monitoring).

But 95% of "no root cause" cases are incomplete investigation. Be honest about which case this is.
