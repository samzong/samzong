---
name: pr-eval
description: >
  Evaluate existing GitHub PR review comments against the current code. Use when
  asked whether reviewer or bot feedback is correct, actionable, stale, or
  should be fixed, deferred, or dismissed. When the user explicitly invokes
  this skill's owned-PR repair workflow or authorizes fixing their PR, continue
  through verified merge-blocking repairs, signed commits,
  pushes, fixed-thread resolution, repository-specific re-review, and current-head
  monitoring without asking between blocker rounds. Discover the repository's
  actual review mechanism before requesting review: use @codex review only when
  the PR received an automatic initial Codex review, ask before using another
  bot's proven trigger, and stop when review is not user-controllable. External
  PRs, explicit read-only requests, ambiguous ownership, and non-blocking findings
  remain read-only and produce no GitHub comments or thread mutations. Use
  liability-review for the final merge gate and pre-ship before each owned-PR
  commit.
---

# PR Eval

Evaluate claims, not reviewer authority. Support two modes:

- `EVALUATE_ONLY`: read-only evaluation when repair is not authorized, including
  ordinary review requests, external PRs, and ambiguous ownership.
- `OWNED_PR_LOOP`: continuously repair only verified merge blockers on a PR the
  user owns.

Use Chinese for analysis. Preserve paths, symbols, commands, and quoted review
text in their original language.

## 1. Select the mode

An explicit read-only request always selects `EVALUATE_ONLY`.

Select `OWNED_PR_LOOP` only when repair is authorized and at least one ownership
signal is verified:

- the user explicitly identifies the PR as theirs; or
- the PR author login matches the authenticated `gh` login.

Ambiguous ownership selects `EVALUATE_ONLY`. Never infer ownership from repository
membership, local filesystem access, branch naming, or write permission.

The user explicitly invoking `$pr-eval` or `/pr-eval` authorizes the owned-PR
blocker workflow unless their request limits it to evaluation. A user request to
fix the PR or an existing scoped repair authorization also suffices. The model
implicitly selecting this skill does not authorize mutation; ownership alone
does not turn "evaluate these comments" into "fix them".

Authorized invocation in `OWNED_PR_LOOP` covers the blocker-only workflow
defined below: edit the matching local PR branch, verify, create signed commits,
push, resolve threads fixed by those commits, use only the review mechanism
selected under Section 4, and monitor the new head. It does not authorize merging,
releasing, deployment, worktree lifecycle changes, scope expansion, unproven bot
mentions, or prose comments on GitHub.

Use an existing checkout or worktree matching the PR head. If none exists, or it
contains unrelated changes that cannot be preserved safely, stop with `BLOCKED`.

## 2. Resolve one PR revision and contract

Resolve the repository and PR number from the supplied URL/number or the current
branch. Do not guess across repositories. Collect the current head OID:

```bash
gh api user --jq .login
gh pr view <number> --repo <owner/name> \
  --json number,url,title,body,state,isDraft,author,createdAt,commits,headRefName,headRefOid,baseRefOid,statusCheckRollup
gh pr diff <number> --repo <owner/name>
```

Record `headRefOid`; all verdicts and writes apply only to that revision. Establish
the accepted PR contract from explicit user instructions, repository guidance,
the PR title/body, linked issue or specification, and the current diff. Ordinary
review comments do not redefine the PR contract.

## 3. Collect all review threads

`reviewThreads` is not a `gh pr view --json` field. Query it through GraphQL and
paginate until `hasNextPage` is false:

```bash
gh api graphql --paginate \
  -f owner='<owner>' -f name='<name>' -F number=<number> \
  -f query='query($owner:String!,$name:String!,$number:Int!,$endCursor:String){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100,after:$endCursor){nodes{id isResolved isOutdated path line comments(first:100){nodes{author{login}body url createdAt}}}pageInfo{hasNextPage endCursor}}}}}'
gh api --paginate 'repos/<owner>/<name>/pulls/<number>/reviews?per_page=100'
gh api --paginate 'repos/<owner>/<name>/pulls/<number>/comments?per_page=100'
gh api --paginate 'repos/<owner>/<name>/issues/<number>/comments?per_page=100'
gh api --paginate -H 'Accept: application/vnd.github+json' \
  'repos/<owner>/<name>/issues/<number>/reactions?per_page=100'
```

Use GraphQL for thread state and the paginated REST results for complete review,
inline-comment, and issue-comment bodies. Keep the thread ID, comment URL,
author, path/line, resolution state, and outdated state. Deduplicate repeated
claims by root cause, but preserve every source URL. When a relevant reaction is
on an issue comment rather than the PR body, fetch that comment's reactions by
comment ID to identify the actor; do not rely on aggregate counts.

## 4. Discover the repository review mechanism

In `OWNED_PR_LOOP`, complete this read-only discovery before the first mutation.
Use the current PR's creation time, commits, reviews, review threads, issue
comments, checks, and timeline ordering. Inspect repository guidance,
`.github/workflows`, `CODEOWNERS`, rulesets, and a small number of recent PRs only
when the current PR does not establish the mechanism. Never post a mention,
request a reviewer, rerun a workflow, or create another PR to probe a bot.

Record the reviewer identity, triggering event, exact trigger if one exists, and
the evidence URL or repository path. Do not infer that a login ending in `[bot]`,
an installed app, a workflow name, or a review on another repository supports a
particular mention.

Treat an `eyes` (`👀`) reaction as an automation-activity signal only. Many bots
use it. Correlate its actor and timestamp with a later completed review from the
same identifiable bot or app and verify that no request comment preceded the
reaction. The reaction alone proves neither Codex identity, a completed review,
nor a reusable trigger; without the later review, wait or use `REVIEW_UNKNOWN`
rather than mentioning any bot.

Select one mechanism:

- `CODEX_AUTO_ON_PUSH`: the current PR proves Codex automatically reviewed the
  initial head after PR creation, no comment requested that review, and later
  pushed heads are also reviewed without a request. After a push, wait; post no
  review comment.
- `CODEX_COMMENT`: the current PR proves Codex automatically reviewed the initial
  head after PR creation and no earlier comment requested it, but automatic
  review on later pushes is not established. This is the only evidence that
  pre-authorizes the exact comment `@codex review`.
- `OTHER_REVIEW`: the repository uses another bot or review system. If primary
  repository or PR-history evidence shows an exact user-controllable mechanism,
  stop with `REVIEW_TRIGGER_DECISION_REQUIRED`, report the reviewer, trigger, and
  evidence, and ask whether to use it. Do not invoke it until the user explicitly
  approves it; that approval is scoped to this PR and exact mechanism.
- `REVIEW_UNCONTROLLABLE`: review is human-only, automatic only at an event the
  user cannot reproduce, controlled by maintainers or external policy, or has no
  evidenced user trigger. Stop without mutation.
- `REVIEW_UNKNOWN`: evidence cannot identify the mechanism. Stop without mutation.

Without the automatic initial Codex-review evidence above, never post
`@codex review`. A configured Codex app or workflow, a Codex review preceded by a
request comment, or behavior observed only on another PR is insufficient; use
`REVIEW_UNKNOWN` unless evidence positively establishes an uncontrollable process.

If the user approves an `OTHER_REVIEW` mechanism, record it as
`OTHER_REVIEW_APPROVED`. Use only its exact evidenced trigger. Prefer a proven
automatic-on-push mechanism over a comment trigger because it creates no PR
noise. Never try `@codex review` as a fallback for another reviewer.

Before posting any authorized trigger, re-read current-head issue comments and
review events. Never request the same reviewer twice for one head. If one trigger
does not produce a review for that head after a bounded wait appropriate to the
repository, stop with `REVIEW_UNRESPONSIVE`; do not retry or try another bot.

## 5. Record CI context

Run:

```bash
gh pr checks <number> --repo <owner/name>
```

Classify CI as `PASSING`, `PENDING`, `CI_FAILING`, or `UNKNOWN`. A non-zero exit
from `gh pr checks` may simply represent failed checks; preserve check names and
states.

`CI_FAILING` is context, not proof that a review comment is correct. In
`EVALUATE_ONLY`, do not diagnose CI. In `OWNED_PR_LOOP`, diagnose required checks
through the repository's designated CI-debugging workflow. Repair automatically
only when evidence ties the failure to a merge-blocking defect in the accepted PR
contract. Infrastructure or unrelated failures stop with `BLOCKED`; do not rerun
or mutate them without separate authorization.

## 6. Verify and classify every claim

For each distinct claim:

1. State the concrete alleged failure and requested action.
2. Inspect the cited current-head code and enough surrounding control flow.
3. Search callers, canonical helpers, tests, and contracts that could handle or
   contradict it.
4. If the comment is outdated or resolved, verify whether the same failure still
   exists on the recorded head; thread metadata alone is not a verdict.
5. Run the narrowest safe executable check when code reading cannot settle the
   claim. Never invent a result.
6. Separate a real current defect from taste, speculative hardening, conservative
   capability omission, scope expansion, or a correct concern already addressed
   elsewhere.

Assign one evidence verdict:

- `VALID`: the current head has the claimed failure.
- `PARTIAL`: a real concern exists, but the claim, severity, or proposed fix is
  materially overstated.
- `INVALID`: current code or runtime evidence disproves the claim.
- `STALE`: the cited revision had the concern, but the recorded head no longer
  does.
- `UNPROVEN`: available evidence cannot establish or refute the claim.

Then assign one merge-impact action:

- `BLOCKING_FIX`: a verified current defect violates the accepted PR contract,
  makes the intended behavior incorrect or unsafe, regresses a supported public
  contract, risks data loss, or causes a required check to fail because of the PR.
- `NON_BLOCKING`: a valid concern that is an enhancement, conservative capability
  loss, optional compatibility widening, refactor, style preference, speculative
  hardening, out-of-scope work, or an owner decision rather than a correctness
  requirement for this PR.
- `DISMISS`: invalid or based on a false premise.
- `NO_ACTION`: stale, already resolved, or duplicate.

Reviewer severity does not determine merge impact. `VALID` does not imply
`BLOCKING_FIX`. `UNPROVEN` cannot become `BLOCKING_FIX` because a reviewer or bot
stated it confidently; assign it `NO_ACTION`, name the missing evidence, and use
`BLOCKED` only when that missing evidence prevents a safe owned-PR merge decision.

## 7. Enforce the non-blocking handoff boundary

Never edit code, commit, push, comment, reply, resolve a thread, rerun a workflow,
create an issue, or change PR state for `NON_BLOCKING`, `DISMISS`, `NO_ACTION`, or
`UNPROVEN` findings.

If blockers and non-blockers coexist, process only the blockers. Leave every
non-blocking thread untouched. Finish the current blocker batch through its
selected review mechanism and current-head classification; that review verifies
the blocker repair and is not a disposition of the non-blocking finding. As soon
as the current-head review has no blocker, stop with `HANDOFF_NON_BLOCKING` and
report the untouched findings to the user. Do not make the user's defer, rejection,
reply, or resolution decision on their behalf.

## 8. Run the owned-PR blocker loop

For each root-cause group classified `BLOCKING_FIX`:

1. Require a mechanism selected under Section 4. For `OTHER_REVIEW`, require the
   user's explicit approval before mutation. Stop if review is unknown or
   uncontrollable.
2. Re-read the PR head OID and local HEAD immediately before mutation. Stop with
   `STALE_ANALYSIS` if either differs from the evaluated revision.
3. Fix the root cause with the smallest change inside the accepted PR contract.
4. Use existing verification first. Add focused regression coverage only for a
   stable observable boundary that would fail before the fix and can realistically
   regress. Do not add tombstone tests, literal-mapping tests, or tests whose sole
   purpose is proving removed behavior remains absent — unless that failure or
   absence is itself a current API, security, or persistence contract that
   existing coverage misses (the global test policy's exception).
5. Run the narrowest reliable behavior check and the repository-required gate.
6. Inspect and stage only the blocker fix. Run `pre-ship` against the exact staged
   diff.
7. Create one signed commit per causal batch with a message matching the diff, then
   push the existing PR branch.
8. Re-fetch the pushed head. If it equals the pushed commit and local HEAD, adopt
   it as the new recorded revision, re-collect current state, and verify each fixed
   claim against it. Any other head change is `STALE_ANALYSIS`.
9. Resolve only the review threads whose blocking claims were verified fixed on
   that new recorded revision. Do not post a prose reply:

   ```bash
   gh api graphql -f threadId='<thread ID>' \
     -f query='mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{isResolved}}}'
   ```

10. Use the selected review mechanism exactly once for the new head:

    - `CODEX_AUTO_ON_PUSH`: post nothing and wait for the automatic review.
    - `CODEX_COMMENT`: after the duplicate check, run:

      ```bash
      gh pr comment <number> --repo <owner/name> --body '@codex review'
      ```

    - `OTHER_REVIEW_APPROVED`: use only the exact user-approved automatic or
      mechanical trigger. Add no prose and no fallback mention.

11. Keep the task active while review and required CI are pending. Use bounded
    waits and concise progress updates rather than ending the task merely because
    review is pending. If the selected mechanism is unresponsive, stop without a
    retry.
12. When the new review arrives, discard claims tied only to older heads, collect
    the current-head threads, and repeat classification.

Every new commit must name an established blocker in the task ledger. Never create
a commit solely because a valid non-blocking suggestion exists. Once the current
head is green and reviewed, do not change it without new current-head blocking
evidence.

## 9. Stop conditions

Stop the autonomous loop only when one condition is reached:

- `COMPLETE`: `EVALUATE_ONLY` finished current-head classification without any
  external write.
- `MERGE_READY`: current-head blockers are fixed, their threads are resolved,
  required CI passes, no untouched non-blocking finding needs user disposition,
  and `liability-review` reports no merge blocker.
- `HANDOFF_NON_BLOCKING`: no blocker remains, but one or more non-blocking findings
  need the user's disposition. Leave those findings and all related GitHub state
  untouched.
- `REVIEW_TRIGGER_DECISION_REQUIRED`: another repository-specific review mechanism
  is evidenced and needs the user's approval before use.
- `REVIEW_UNCONTROLLABLE`: the repository review process has no evidenced trigger
  available to the user.
- `REVIEW_UNKNOWN`: the repository review mechanism cannot be established.
- `REVIEW_UNRESPONSIVE`: one authorized trigger produced no current-head review;
  no retry or fallback was attempted.
- `OWNER_DECISION_REQUIRED`: a possible fix changes product semantics, public
  scope, compatibility policy, architecture, or another owner-owned trade-off;
  or GitHub requires disposition of an untouched non-fix thread before merge.
- `BLOCKED`: permissions, missing matching checkout, unrelated dirty state,
  infrastructure failure, or unavailable evidence prevents safe continuation.
- `STALE_ANALYSIS`: the PR or local head changed before an intended mutation or
  final report.

Do not merge the PR. `MERGE_READY` means report that the user can merge it.

## 10. Guard against stale analysis

Immediately before every mutation and final report, re-read `headRefOid`. If it
differs from the revision used for the current classifications, return
`STALE_ANALYSIS`; do not present old classifications as current and do not write to
GitHub. The only expected revision change is this workflow's own push: adopt it
only through Step 8 after proving the remote head equals both the pushed commit and
local HEAD.

## Output

```text
PR Eval: COMPLETE | MERGE_READY | HANDOFF_NON_BLOCKING | REVIEW_TRIGGER_DECISION_REQUIRED | REVIEW_UNCONTROLLABLE | REVIEW_UNKNOWN | REVIEW_UNRESPONSIVE | OWNER_DECISION_REQUIRED | BLOCKED | STALE_ANALYSIS | INPUT_ERROR
Mode: EVALUATE_ONLY | OWNED_PR_LOOP
PR: <url> @ <head OID>
CI: <PASSING | PENDING | CI_FAILING | UNKNOWN> — <check summary>
Review mechanism: <mechanism, reviewer, exact trigger or none, evidence, authorization>

| Source | Claim | Evidence verdict | Merge impact | Evidence | Action taken |
|---|---|---|---|---|---|
| <comment URL> | <concise claim> | <verdict> | <action> | <file:line, command, or contract> | <none or commit/thread resolution> |

Fixed blockers: <ordered commit and resolved-thread evidence, or none>
Untouched handoff: <non-blocking findings requiring user disposition, or none>
GitHub prose comments posted: none
Review requests posted: <none or one exact authorized trigger per head>
Verdict: <can merge, needs user disposition, or blocked reason>
```

Keep evidence concise and specific. Zero `BLOCKING_FIX` items is valid. Never
describe an untouched non-blocking finding as resolved, accepted, rejected, or
deferred by the user.
