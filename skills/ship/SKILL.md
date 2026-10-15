---
name: ship
description: >
  Ship staged changes through preflight, final review, commit, push, and
  pull-request creation or reuse. Use when the user invokes $ship, or in draft
  mode when the AGENTS.md delivery loop reaches its PR step; do not invoke it
  from ordinary-language Git requests or for commit-only,
  push-only, PR-only, or existing-PR editing work. All generated git and GitHub
  text must be in English.
---

# Ship

Run the entire flow without repeated confirmation after the final authority gate passes. Lead the final report with the PR link and retain decision-relevant handoffs.

The invocation authorizes this shipping flow for the staged scope. It also
permits necessary in-scope corrections to defects or validation failures found
by the flow; it does not authorize adjacent features or unrelated unstaged work.
Make those corrections, stage only your own authorized correction hunks, update
the exact target and affected evidence, and resume. Never bypass a failed gate.
Stop the affected step for unknown authority, a new owner decision, an unresolved
blocker, or a failed external operation; do not ask again for unchanged authority.

## Modes

- `$ship`: the explicit invocation authorizes this flow and a ready-for-review PR.
- Draft mode: the AGENTS.md delivery loop authorizes this flow for its task scope. Before Step 0, stage only the task's own changes in its `gmc` worktree. Run every step unchanged except: apply the delivery loop's stop-before-push conditions before Step 6; create the PR with `gh pr create --draft`; leave a reused PR's draft state alone; state the acceptance check, its evidence, and what remains unverified in the body's verification or testing section, or a `### Verification` section in the fallback body; Step 7 also returns the harvest packet.

- [ ] Step 0: Preflight ⛔ BLOCKING
  - [ ] Run `git status -sb`
  - [ ] Run `git diff --cached --name-only` and stop if nothing is staged
  - [ ] Inspect both staged and unstaged deltas on overlapping paths. Preserve intentional partial staging and unrelated edits. If unstaged hunks are your own already-authorized corrections, stage only those hunks and resolve the new target; ask only when the intended content cannot be determined.
  - [ ] Run `git branch --show-current` and stop if it is empty (detached HEAD)
  - [ ] Confirm `origin` exists
  - [ ] Run `gh auth status`
- [ ] Step 1: Language validation
  - [ ] Inspect added CJK text by role, not merely by character range. Enforce applicable English-language rules for authored code identifiers, change descriptions, and repository documentation.
  - [ ] Preserve legitimate non-English test inputs, fixtures, translations, quoted upstream text, and exact proper/legal names. Do not rewrite test data as Unicode escapes just to satisfy a scanner.
  - [ ] Honor explicit user/repository language exceptions, including mixed Chinese and English in personal agent configuration. Correct an actual language violation within the authorized scope; do not alter product wording or semantics without the required owner decision.
- [ ] Step 2: Pre-Ship Gate ⛔ BLOCKING
  - [ ] Invoke `/pre-ship --staged` on the staged diff before committing
  - [ ] Require `Pre-Ship: PASS`. On `BLOCK` or `INPUT_ERROR`, inspect the evidence: make authorized in-scope corrections or resolve the target, then resume the gate. Stop if the blocker cannot be resolved within the accepted scope and authority.
  - [ ] On `UNVERIFIED`, obtain missing evidence within the accepted scope when possible and resume the gate. If proof remains unavailable, report exactly what is missing and stop the gated action; continuing requires the literal reply `豁免` where pre-ship permits it.
  - [ ] Carry confirmed deferred defects from the liability ledger or pre-ship block into the owner report, with their consequence, deferral reason, and follow-up location or concrete revisit condition. Omit disproven candidates and cosmetic notes; keep review notes out of the PR body and comments. Reporting does not establish owner acceptance or waive a blocker.
  - [ ] Record the reviewed staged-diff fingerprint; re-read `git diff --cached` and confirm the scope still matches the authorizing request
- [ ] Step 2.5: Final Authority Gate ⛔ BLOCKING
  - [ ] Treat the reviewed staged diff as final; it must be verified or explicitly exempted under Step 2
  - [ ] If the diff is consequential under the applicable AGENTS instructions, apply Mirror `ship` mode to that exact staged diff
  - [ ] Stop on `BLOCK`, `HOLD`, `Contract decision: PENDING`, or `Risk disposition: OWNER ACCEPTANCE REQUIRED`
  - [ ] Continue without another confirmation when Mirror reports unchanged scope with `Risk disposition: BOUNDED` or `ACCEPTED AFTER REPORT`; the authorizing invocation remains the Git authorization
  - [ ] Recompute the staged-diff fingerprint immediately before commit
  - [ ] If the staged diff changes, review its delta and update Steps 2 and 2.5 for the final target. Reuse demonstrably unaffected evidence under their contracts; do not commit until the complete final target is covered.
- [ ] Step 3: Branch + commit
  - [ ] Normalize branch name (see **Branch naming**). On default branch (`main`/`master`), create `<type>/<slug>`. For a nonconforming existing branch, first run `gh pr list --head "$(git branch --show-current)" --state open`: with an open PR, keep the name and report the nonconformity; without one, `git branch -m <type>/<slug>`, and if the old name was already pushed, report the stale remote branch instead of deleting it.
  - [ ] Run `git log --oneline -5` for commit style reference
  - [ ] Draft `type(scope): description` — use it for the commit subject and, when creating a PR, its title (squash merge)
  - [ ] Commit only the verified staged content with DCO sign-off. Never sweep unrelated or intentionally excluded working-tree changes into the commit.
  - [ ] Match the repo's normal signing convention before committing
- [ ] Step 4: Resolve PR
  - [ ] Run exactly:
    ```bash
    gh pr list --head "$(git branch --show-current)" --state open --limit 2 --json number,url,title
    ```
  - [ ] Stop if the query exits non-zero.
  - [ ] On 0 results, continue to Step 5. On 1 result, capture its number, URL, title, and live body, validate that body per **PR body validation**, skip Step 5, and continue to Step 6. On more than 1 result, stop and report the ambiguity.
  - [ ] Do not overwrite existing PR content.
- [ ] Step 5: PR content ⛔ MUST READ BEFORE WRITING
  - [ ] Run only when Step 4 returned 0 results.
  - [ ] Discover tracked templates with `git ls-files`, not a default hidden-file-skipping search. Use `git ls-files | rg -i '(^|/)(pull_request_template\.md|pull_request_template/.*\.md)$'` and read the selected template completely.
  - [ ] Build body per **PR body priority**. Fill every required section from the diff and checks actually run. For consequential decisions, link the existing canonical design document containing the chosen mechanism, strongest alternative, and deciding fact; if none exists, preserve that rationale in the body's relevant section without adding a parallel decision log. Include only accepted, audience-appropriate decisions; unresolved owner decisions stay in the owner report.
  - [ ] If `CONTRIBUTING.md` exists, also satisfy PR gates the template does not cover (proof, disclosure, verification).
  - [ ] Scrub template/helper cruft: HTML comments, placeholders, `TODO`/`TBD`, hidden reminders. Remove unselected placeholder-only alternatives rather than publishing placeholder text. Keep reviewer-visible content only.
  - [ ] Validate the candidate body per **PR body validation** and stop before PR creation if it fails.
- [ ] Step 6: Push + create or reuse PR
  - [ ] Resolve the current GitHub login as `pr_author`.
  - [ ] Run `PR_BODY="$pr_body" PR_AUTHOR="$pr_author" git push -u origin HEAD` only after the commit and PR-body validation succeed. These exact values let repository pre-push hooks validate the same candidate body that `$ship` will publish. Stop if the hook or push fails.
  - [ ] When Step 4 returned 0 results, run `gh pr create --title "<Step 3 subject>" --body "$pr_body"` with that exact validated body. No `[Type]` titles.
  - [ ] Verify the created or reused PR with `gh pr view --json number,url,title,state,body`; capture its number, URL, and title, then validate the returned live body per **PR body validation**.
- [ ] Step 7: Report
  - [ ] Output: branch name, commit subject, actual PR title, **PR URL**, and any confirmed deferred defects retained in Step 2. Present unresolved owner decisions as yes/no or keep/drop; do not request a decision for already accepted or technically resolved items.

## Branch naming

Format: `<type>/<slug>` where type is `feat|fix|refactor|docs|build|chore|test` and slug is kebab-case from the staged diff.

Reject and `git branch -m` when the name is not `<type>/<slug>` or any segment/token contains an AI-tool slug (case-insensitive):

`cursor`, `codex`, `claude`, `copilot`, `windsurf`, `aider`, `cody`, `continue`, `devin`, `augment`, `grok`, `gemini`, `openai`, `anthropic`, `tabnine`, `replit`, `bolt`, `codeium`, `sourcegraph`, `opencode`, `trae`, `kiro`, `qoder`, `tongyi`, `lingma`, `qwen`, `comate`, `wenxin`, `codegeex`, `zhipu`, `marscode`, `doubao`, `codefuse`, `iflycode`, `iflytek`, `kwaipilot`, `codearts`, `stepfun`, `minimax`, `joycoder`, `catpaw`, `huawei`

Infer type/slug from the change; never keep tool tokens. Example: `trae/feat-oauth-flow` → `feat/oauth-flow`.

Never rename a branch that already has an open PR — renaming orphans the PR; keep its name and report the nonconformity instead.

## PR title

For a new PR, use `type(scope): description` — imperative, lowercase, no period, ≤72 chars — and match the commit subject exactly. A reused PR keeps its existing title. Repo docs override only when they explicitly require a different title format.

## PR body priority

1. PR template discovered from tracked files — prefer `.github/pull_request_template.md` case-insensitively, then other `pull_request_template.md` or `pull_request_template/*.md` files
2. Contribution docs — `CONTRIBUTING.md`, `.github/CONTRIBUTING.md`, `docs/CONTRIBUTING.md`, `contributing.md` (body structure only when no template)
3. Fallback body below

## PR body validation

Before creating a PR, and before reusing or reporting an existing one:

1. Search tracked workflow, package, and script sources for repository-owned PR-body checks such as `pull_request.body`, `PR_BODY`, `docs-impact`, required headings, and exact checkbox labels. Read the validator and its CI invocation rather than inferring the contract from prose.
2. Run each applicable repository-owned validator against the exact candidate or live body, supplying the same event and author inputs used by CI. For example, when CI invokes `node scripts/docs-impact-check.mjs` from `PR_BODY`, run that script locally with `GITHUB_EVENT_NAME=pull_request`, the current GitHub login as `PR_AUTHOR`, and the exact body as `PR_BODY`.
3. Stop on any validation failure. Do not create a PR that is known to fail a body-only CI gate, and do not overwrite a reused PR merely to make it pass.

The candidate body must exist before push. Always pass that exact body and the authenticated author to `git push` as `PR_BODY` and `PR_AUTHOR` so a repository pre-push hook can run the same validator as CI. Create the PR with the unchanged candidate after the push.

## Fallback PR body

```md
### What's changed?

- <concise bullet(s)>

### Why

- <reason / motivation>
```

## Do not

- Do not ask for confirmation unless Step 2.5 reports a new owner decision, new scope, or `OWNER ACCEPTANCE REQUIRED`
- Do not show drafts and wait for approval
- Do not trigger this skill for broad PR-only requests like "open PR"
- Do not stage unrelated changes or override intentional partial staging
- Do not commit content outside the verified staged target
- Do not invent validation results or claim commands were run when they were not
- Do not continue after auth, push, or PR creation failures
- Do not generate non-English git or GitHub text
- Do not publish non-blocking review notes or verification exemptions in the PR body or comments
