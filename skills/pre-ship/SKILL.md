---
name: pre-ship
description: Verify a staged or just-committed change before commit or push. Read-only; reuse the liability-review verdict and valid verification for the exact target.
---

# Pre-Ship

Prove that the exact change about to leave the machine has no known blocker and
has passed a relevant project verifier. This is a gate, not a repair loop.

Use Chinese for analysis and verdicts. Keep paths, symbols, commands, and Git or
GitHub text in English.

## Modes

- `--staged` (default): review `git diff --cached`.
- `--committed`: review `git diff HEAD~1..HEAD` for an existing local commit,
  or its root diff when the initial commit has no parent.

No mode may edit files, mutate the index, amend a commit, stage fixes, create a
PR, or post a comment. Return concrete corrections to the caller. A caller may
make already-authorized in-scope corrections and resume without another approval;
then resolve the new exact target and update the affected evidence before PASS.

## 1. Resolve the exact target

Start with:

```bash
git status --short --branch
```

For `--staged`:

```bash
git diff --cached --binary
git diff --cached --name-only
git diff --cached --check
```

Inspect staged and unstaged deltas when a staged path also has unstaged changes.
The index remains the target; never silently include the working-tree version.
Review the staged content directly. Use runtime evidence only when it actually
covers that staged content and all relevant inputs. If this cannot be established,
report the exact mismatch as `UNVERIFIED`; if the intended target is ambiguous,
return `INPUT_ERROR`. The caller may resolve its own authorized corrections; this
read-only gate never stages them or overwrites intentional partial staging.

For `--committed`:

```bash
git diff HEAD~1..HEAD --binary
git diff HEAD~1..HEAD --name-only
git diff HEAD~1..HEAD --check
```

For an initial root commit, use `git diff-tree --root --no-commit-id -p HEAD`
with the corresponding `--binary`, `--name-only`, and `--check` options.

Require an empty index. Review the committed content even when the working tree
has later changes, but do not use a contaminated working-tree verifier as proof
of that commit. Report an unresolved verification mismatch as `UNVERIFIED`.

If the diff is empty, report `Nothing to pre-ship` and stop without claiming a
behavioral verification pass.

Resolve the full refs and fingerprint the binary diff:

```bash
<exact diff command> | git hash-object --stdin
```

Record unrelated unstaged and untracked paths. Path non-overlap alone does not
prove that a project verifier is isolated from those changes.

### Tier

Classify the resolved target. `T0` is purely mechanical — generated-file
refreshes, formatting-only, lockfile-only, typo fixes with zero semantic delta.
For `T0`: keep the fingerprint discipline, verify the mechanical property itself
(regenerate and diff-clean, formatter or parser check, plus the `--check` output
above), skip Step 2 and Step 3's behavior verifier, and report `PASS` with
`Tier: T0`. Escalation is one-way: any semantic delta or doubt, now or later in
the run, raises to the full flow immediately; never downgrade mid-run. Everything
else runs the full flow as `Tier: full`.

## 2. Review ownership

`pre-ship` produces no findings of its own. Defects belong to
`liability-review`, and one fingerprint is reviewed once:

- If a `liability-review` verdict bound to this exact fingerprint exists in the
  session, carry it forward unchanged.
- Otherwise run `liability-review` in `local` mode on the same target
  (`--staged`, or `--commit HEAD` for `--committed`) and use its verdict.

Map the verdict without changing the reviewer's findings:

- Any open `P0`/`P1`, `REJECT_LOCAL`, `INPUT_ERROR`, mixed scope, or materially ambiguous intent → `BLOCK`.
- `REQUEST_CHANGES` caused only by missing required review coverage or verification → `UNVERIFIED`; a concrete defect or an unclear reason → `BLOCK`.
- A `T2` target whose required independent pass is `not available` → `UNVERIFIED`.
- `ACCEPT_LOCAL` with no blocker → continue to Step 3; carry `P2` items into the deferred block.

A later green verifier does not erase a pending defect or required review gap.
If the existing liability verdict withheld acceptance only for a named check,
its successful exact-target result can update that verdict without repeating
unaffected analysis. Return new evidence or disagreements to the same liability
ledger; do not generate a second findings list here.

## 3. Establish canonical verification

Discover the repository-declared gate from the closest `AGENTS.md`, contribution
guide, package scripts, Makefile/justfile, or CI configuration. Reuse a successful
result already recorded in the session when its exact command, target fingerprint,
relevant inputs, environment, and behavior coverage still match. Otherwise run
the narrowest credible command that exercises the changed behavior. Run any gate
the repository explicitly requires afresh, plus the diff check from Step 1.
Prefer an existing focused test over a broad generic suite.

For a semantic change, formatting, lint, type checking, code reading, or another
model alone is not a behavior-level verifier. If the repository has no credible
executable signal for the changed behavior, return `UNVERIFIED` and name the
missing proof. Documentation or declarative-only changes may use their canonical
build, parser, schema, or link check when that is the relevant contract.

The verifier must cover the reviewed target:

- If it reads the working tree, confirm reviewed paths match the staged or
  committed content.
- If unrelated local changes could affect dependencies, configuration, generated
  inputs, compilation, or test selection, its result does not prove the target.
  Return `UNVERIFIED` unless isolation is explicit or those paths are proven
  irrelevant to that command.
- Do not stash, checkout, reset, or create a worktree to manufacture isolation.

After verification, rerun `git status`, the exact diff command, and its
fingerprint. If the target changed, inspect the delta and re-resolve the target.
Update the liability verdict under its drift/re-review contract and rerun checks
whose relevant inputs changed; preserve demonstrably unaffected evidence. Do not
PASS until the current complete target is covered. Ambiguous targets return
`INPUT_ERROR`. Normal ignored outputs do not invalidate the target unless they
change an input the verifier depends on.

## 4. Explicit verification exemption

`UNVERIFIED` is fail-closed, not a permanent dead end. The caller must report
the exact missing evidence and its cost, then stop. It may continue only after
the user replies with the literal word `豁免` after seeing that report.

An accepted exemption does not turn the result into `PASS`. Record it as
`Pre-Ship: UNVERIFIED — EXEMPTED` with the target fingerprint, missing evidence,
and the owner's literal reply. It cannot override `BLOCK`, `INPUT_ERROR`, a
failing verifier, or a changed target. `ship` must discard this record instead
of publishing it in a PR body or comment.

## 5. Deferred audit block

On `PASS`, emit only confirmed non-blocking defects deferred from this change,
with their consequence, reason for deferral, and follow-up location or concrete
revisit condition:

```text
## Considered and deferred

- <finding ID, file:line> [DEFERRED]: <consequence; deferral reason; follow-up location or revisit condition>
```

Omit the block when empty; omit disproven candidates and cosmetic notes. `ship`
carries these defects into its owner report, not the PR body or comments, and
still excludes verification exemptions from external artifacts. `commit` may
append the block to the pending commit body. A direct caller chooses an
appropriate durable review artifact; `pre-ship` itself writes none. Reporting a
defect does not establish owner acceptance or change its blocking disposition.

## 6. Optional hook receipt

After `PASS`, record the reviewed target only when an active PreToolUse hook
uses `bin/pre-ship-gate`. This applies to Codex and Claude alike:

```bash
~/.agents/bin/pre-ship-gate record --mode staged --cwd "$PWD"
~/.agents/bin/pre-ship-gate record --mode committed --cwd "$PWD"
```

Run only the command matching the resolved review mode. An installed copy of
this helper may be used when the source checkout has not yet been updated.
The receipt binds the canonical worktree, HEAD, target diff fingerprint, and
creation time for five minutes. A changed target needs renewed review; touching
a file does not renew it. Commit and push require separate staged and committed
receipts. Do not combine staging or source changes with the guarded operation.
When a client hook omits the execution tool working directory, use explicit
`git -C <reviewed-repository>` so the hook can resolve the same target.

If no active hook consumes it, do nothing. Never record after `BLOCK`,
`UNVERIFIED`, an exemption, or `INPUT_ERROR`. The receipt is the only permitted
side effect. It prevents ordinary mistakes; it is not a security boundary and
cannot inspect opaque scripts, interactive tool continuations, or every tool.

## Verdict and output

- `PASS`: the final resolved or re-anchored target is stable and fully covered,
  no blocker remains, and the relevant canonical verifier passed.
- `BLOCK`: code, scope, contract, or verification evidence shows a blocker.
- `UNVERIFIED`: the change may be correct, but the required target-specific proof
  is missing or contaminated; only the explicit exemption protocol above may
  allow a caller to continue.
- `INPUT_ERROR`: target resolution failed, or target drift remains unresolved
  or uncovered by the updated review and verification.

```text
Pre-Ship: <PASS | BLOCK | UNVERIFIED | INPUT_ERROR>
Target: <mode, refs, fingerprint>
Tier: <T0 | full>
Review: <liability-review verdict and tier bound to this fingerprint, or T0 mechanical check>
Verification: <exact commands and results>
Blockers: <liability-review finding IDs or none>
Deferred: <count>
Exemption: <not required | required | accepted with recorded evidence>
```

Never claim exhaustion, safety, or bot convergence. This gate reports only the
evidence actually collected for this exact target.
