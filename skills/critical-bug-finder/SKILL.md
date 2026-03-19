---
name: critical-bug-finder
description: >
  Find critical implementation bugs that can crash production, corrupt data,
  bypass security, deadlock, race, or break core logic. Use for explicit fatal
  bug hunts such as "find critical bugs", "audit for fatal bugs",
  "security vulnerability audit", "race condition audit", "find crash or
  data loss bugs", or reliability incident reviews. Do not use for general
  code review, refactoring, style feedback, or routine performance analysis.
argument-hint: [path] [--full] [--quick] [--security-only|--concurrency-only] [--format json|md] [--write-report] [--max-findings N]
---

IRON LAW: NEVER REPORT A BUG WITHOUT A CONCRETE TRIGGER, A REAL FAILURE MODE, AND A SEVERE CONSEQUENCE.

# Critical Bug Finder

Use `$ARGUMENTS` and the user's wording to define scope before scanning.

## Options

- `<path>`: file or directory to audit
- `--full`: audit the full repository
- `--quick`: skip confirmation gates when scope and output mode are explicit
- `--security-only`: only report security vulnerabilities
- `--concurrency-only`: only report races, deadlocks, or TOCTOU bugs
- `--format json|md`: output format, default `md`; if `json`, load `references/output-format.md`
- `--write-report`: write a report file after presenting findings
- `--max-findings N`: cap reported findings, default `10`

Copy this checklist and check off items as you complete them:

- [ ] Step 0: Define scope [BLOCKING]
  - [ ] Parse `$ARGUMENTS`
  - [ ] If `<path>` is provided, scope to it
  - [ ] If `--full` is provided, scan the full repo
  - [ ] If scope is unclear and `--full` is absent, ask one focused question before scanning
- [ ] Step 1: Build the risk map [BLOCKING]
  - [ ] Identify high-risk files first: input boundaries, state mutations, DB or file writes, auth checks, concurrency, error handling
  - [ ] For large repos, split one top-level directory or subsystem per subagent, starting with the riskiest areas first
- [ ] Step 2: Audit [REQUIRED]
  - [ ] Load `references/checklist.md`
  - [ ] Ask: can bad input crash this path, corrupt state, bypass auth, exhaust resources, or create a race
  - [ ] Ask: can two requests or two processes break assumptions here
  - [ ] Ask: does the code mutate state without atomicity, rollback, or ordering guarantees
- [ ] Step 3: Validate candidates [REQUIRED]
  - [ ] Keep only findings with a concrete trigger scenario
  - [ ] Keep only findings with a real severe consequence
  - [ ] Keep only findings with a specific code location
  - [ ] Discard theoretical, stylistic, or low-impact issues
- [ ] Step 4: Present findings [REQUIRED]
  - [ ] Report the highest-confidence findings first
  - [ ] Respect `--max-findings N`
  - [ ] State audited scope and anything not checked
- [ ] Step 5: Write report (conditional)
  - [ ] Only if the user requested file output or passed `--write-report`
  - [ ] Unless `--quick` was passed with explicit output mode, ask before writing files

## Qualifying categories

- Crash, panic, uncaught exception, or unrecoverable runtime failure
- Data corruption, data loss, or silently wrong results
- Security vulnerability such as SQL injection, XSS, RCE, SSRF, path traversal, auth bypass, or secret exposure
- Infinite loop, deadlock, resource exhaustion, or unbounded growth that can take the system down
- Race condition or TOCTOU bug with a realistic failure path
- Core logic contradiction that breaks documented or clearly intended behavior

## Exclusions

- Architecture opinions, refactors, naming, readability, or style
- Performance complaints unless they realistically cause outage, OOM, or resource exhaustion
- Missing tests, docs, or logging by themselves
- "Could be risky" claims without a concrete exploit or failure path

## Output

If `--format json`, load `references/output-format.md` and follow its schema exactly.

For each finding, include:

- `severity`: `CRITICAL` or `HIGH`
- `location`: `file:line` or exact symbol
- `category`: one qualifying category
- `description`: one sentence
- `trigger`: concrete scenario
- `why_fatal`: why the impact is severe
- `suggested_fix`: minimal fix direction

If no qualifying bugs are found, say so clearly and list the audited scope.

## Report file

If writing a file, save it in the project root as `bugs_<4-char>.md`.

Typical downstream: use `bugfix-dispatch` when the user wants to split confirmed findings into PR-sized worktrees.

## Do not

- Do not report generic code review issues
- Do not report speculative vulnerabilities without a trigger path
- Do not inflate severity for medium or low issues
- Do not write a report file unless the user asked for it or passed `--write-report`
- Do not claim a full-repo audit if the scan was partial
