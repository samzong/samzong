---
name: issue-cleaner-master
description: >
  GitHub issue management toolkit for project maintainers and contributors.
  Four modes: (1) scan — find contributable issues ranked P0-P5,
  (2) reply — draft and post concise maintainer responses to specific issues,
  (3) triage — classify issues and assign/remove labels,
  (4) analyze — deep root-cause or feature-design analysis saved to markdown.
  Use when: managing GitHub issues, finding contribution opportunities,
  replying to issues, triaging issues, labeling issues, analyzing bugs,
  designing features from issues, "what can I work on", "reply to this issue",
  "triage issues", "analyze this bug", "label these issues", "find easy issues",
  "show me contributable issues", issue cleanup, issue management, project
  maintenance, open source contribution discovery.
  Do not use for: PR review, code review, issue creation from scratch, or
  general GitHub operations unrelated to issue management.
argument-hint: "<scan|reply|triage|analyze> [#issue...] [--repo owner/repo] [--quick] [--min-priority P0-P5] [--format json|md|both] [--output file.md]"
---

IRON LAW: NEVER POST A REPLY, APPLY A LABEL, OR MODIFY ANY ISSUE WITHOUT SHOWING THE EXACT CONTENT TO THE USER AND GETTING EXPLICIT CONFIRMATION FIRST. FOR READ-ONLY MODES, NEVER FABRICATE DATA NOT RETURNED BY THE API.

# Issue Cleaner Master

Use the loaded skill base directory as `SKILL_DIR` when running bundled scripts.

Route `$ARGUMENTS` into exactly one mode: `scan`, `reply`, `triage`, or `analyze`.

## Routing

| Input pattern | Mode |
|---------------|------|
| No mode keyword, or `scan` | scan |
| `reply #N [#N...]` | reply |
| `triage [#N...]` | triage |
| `analyze #N [#N...]` | analyze |

If ambiguous, ask one focused question before proceeding.

---

## Mode: scan

Find contributable issues ranked by priority. Contributor perspective.

**Options**: `--repo owner/repo`, `--min-priority P0-P5`, `--format json|md|both`, `--quick`

- [ ] Step 0: Fetch data ⛔ BLOCKING
  - [ ] Run `bash "$SKILL_DIR/scripts/fetch-issues.sh"` (pass `--repo` if provided)
  - [ ] If the script fails, stop and report the error
- [ ] Step 1: Filter and rank ⚠️ REQUIRED
  - [ ] Load `references/priority-labels.md` for label mappings
  - [ ] Apply filtering rules (see below)
  - [ ] Assign priorities P0-P5; respect `--min-priority`
- [ ] Step 2: Confirm scope ⚠️ REQUIRED (skip if `--quick`)
  - [ ] Show: total fetched, included, excluded, priority distribution
  - [ ] Ask user to proceed or adjust
- [ ] Step 3: Generate reports
  - [ ] Load `references/output-examples.md` for templates
  - [ ] Write `issues-report.json` and/or `issues-report.md` per `--format`

### Filtering rules (scan)

Evaluate each issue in order. First matching rule wins.

**Exclude if:**
1. `has_open_pr == true` → "Has in-progress PR"
2. `has_merged_pr == true` → "Fixed by merged PR"
3. Assignees non-empty AND `updated_at` within 30 days → "Assigned and active"
4. Non-code contribution: labels contain `question`/`support`/`duplicate`/`wontfix`/`invalid`, or title ends with `?` / starts with "How to"/"Why does"/"What is". If only title matches, fetch first 500 chars of body before deciding.

**Include if:**
5. Assignees non-empty AND `updated_at` > 30 days AND no open PR → "Assigned but stale" (mark `[Stale]`)
6. All others → included

**Priority** (first match; see `references/priority-labels.md` for label variants):
P0: `help-wanted` + `good-first-issue` | P1: `good-first-issue` | P2: `help-wanted` | P3: `bug`/`kind/bug` | P4: `documentation`/`kind/documentation`/`kind/cleanup` | P5: rest

**Conservative principle**: if uncertain, include for user judgment.

---

## Mode: reply

Draft and post concise maintainer responses. Maintainer perspective.

- [ ] Step 0: Load issues ⛔ BLOCKING
  - [ ] Fetch each issue: `gh issue view #N --json number,title,body,comments,labels,assignees,state`
  - [ ] Read the full conversation thread to avoid repeating what was already said
- [ ] Step 1: Understand project context ⚠️ REQUIRED
  - [ ] From the issue content, identify relevant source files, docs, or config
  - [ ] Read enough code to give an informed, specific response
- [ ] Step 2: Draft replies ⚠️ REQUIRED
  - [ ] One draft per issue
  - [ ] Follow reply style rules (see below)
- [ ] Step 3: Confirm ⚠️ REQUIRED (**never** skip, even with `--quick`)
  - [ ] Show each draft with target issue number and title
  - [ ] Ask user to approve, edit, or skip each one
- [ ] Step 4: Post approved replies
  - [ ] `gh issue comment #N --body "..."`
  - [ ] Report posted vs skipped

### Reply style

- Open with direct answer or acknowledgment, not pleasantries
- Short paragraphs; no walls of text
- Reference code with backticks: `path/to/file.ts:42`
- Use "we" for project decisions, "you" for the reporter
- End with a clear next step: fix incoming, label assigned, needs repro, or wontfix with reason
- Ask specific questions when more info is needed, never vague "could you provide more details"

---

## Mode: triage

Classify issues and manage labels. PM perspective.

- [ ] Step 0: Load data ⛔ BLOCKING
  - [ ] If specific numbers given, fetch each with `gh issue view #N --json number,title,body,labels`
  - [ ] If no numbers, run `bash "$SKILL_DIR/scripts/fetch-issues.sh"` for all open issues
  - [ ] Fetch available labels: `gh label list --json name,description --limit 200`
- [ ] Step 1: Classify ⚠️ REQUIRED
  - [ ] Load `references/priority-labels.md` for taxonomy
  - [ ] For each issue, suggest: type label, priority label, and any other applicable labels
  - [ ] Match against existing repo labels only — never suggest labels that don't exist
- [ ] Step 2: Present plan ⚠️ REQUIRED (**never** skip, even with `--quick`)
  - [ ] Show table: issue #, title, current labels → suggested adds/removes
  - [ ] Ask user to approve, edit, or skip each
- [ ] Step 3: Apply approved changes
  - [ ] `gh issue edit #N --add-label "label1,label2"` for additions
  - [ ] `gh issue edit #N --remove-label "label"` for removals
  - [ ] Report what was changed vs skipped

---

## Mode: analyze

Deep technical analysis. Senior engineer perspective.

**Options**: `--output file.md` (default `issue-analysis.md`), `--quick`

- [ ] Step 0: Load issues ⛔ BLOCKING
  - [ ] Fetch each issue: `gh issue view #N --json number,title,body,comments,labels`
  - [ ] Read the full conversation thread
- [ ] Step 1: Investigate ⚠️ REQUIRED
  - [ ] Identify affected code areas from the issue
  - [ ] Read relevant source, tests, and dependencies
  - [ ] For bugs: trace execution to root cause
  - [ ] For features: map current architecture and constraints
- [ ] Step 2: Document findings ⚠️ REQUIRED
  - [ ] Load `references/analysis-template.md`
  - [ ] For bugs: root cause, reproduction path, fix direction
  - [ ] For features: design options with trade-offs, recommended approach
- [ ] Step 3: Confirm ⚠️ REQUIRED (skip if `--quick`)
  - [ ] Show summary of findings
  - [ ] Ask before writing file
- [ ] Step 4: Write output
  - [ ] Write to `--output` path
  - [ ] Report file path

---

## Do not

- Do not post replies or apply labels without explicit user confirmation — **never**
- Do not suggest labels that don't exist in the repository
- Do not fabricate issue data, code analysis, or API results
- Do not skip confirmation for `reply` or `triage` even with `--quick`
- Do not generate empty priority groups in scan reports
- Do not parse PR body text for issue links — use `closingIssuesReferences` from fetch script
- Do not modify issue state (open/close) — this skill manages labels and comments only
