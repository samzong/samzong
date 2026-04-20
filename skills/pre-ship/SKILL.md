---
name: pre-ship
description: >
  Pre-push bot-adversarial self-review gate. Simulates 7 AI reviewer lenses
  (coderabbit / copilot / codex / strict-maintainer / gemini / claude-code /
  greptileai) on staged or just-committed diff, auto-fixes MUST-FIX findings
  atomically, loops to convergence (hard cap 2 rounds), writes audit trail to
  commit body and a sentinel file for the Claude Code hook. Self-contained —
  does NOT call `pr-eval` (which is post-push only). Invoked by `ship` Step 3.5,
  by `commit` before commit, or manually before any push.
  Use when: "pre-ship", "pre-push scan", "bot exhaust", "ship-ready check",
  "push 之前扫一遍", "本地审", or invoked from `ship`.
argument-hint: "[--staged | --committed] [--round N]"
---

**回复语言**：进度、分析、verdict 解释使用中文。文件引用（`path:42`）、符号名、YAML 字段、shell 命令保持英文原样。

# Pre-Ship: Bot-Adversarial Self-Review Gate

**Goal**: The diff you push must have already passed 7 simulated bot lenses. Real bots on GitHub then find nothing new. AI-era code review does not happen on GitHub — it finishes here.

Triggered by `ship` Step 3.5, by `commit` before committing, or by user directly. Self-contained: scans, classifies, fixes MUST-FIX atomically, loops to convergence, writes audit trail, writes sentinel.

## Input Mode

- `--staged` (default when invoked standalone): scan `git diff --cached`. Fix → `git add` updated paths only.
- `--committed` (default when invoked from `ship`): scan `git diff HEAD~1..HEAD`. Fix → `git add` + `git commit --amend --no-edit` (preserves signing).
- `--round N`: current round number, default 1. Auto-incremented per iteration.

## Budget (hard limits — over = STOP, do NOT write sentinel)

- `max_fix_delta_per_round`: 30 (sum of +added / -removed across all MUST-FIX fixes)
- `max_rounds`: 2
- `max_new_files`: 0 (fixes may only touch files already in the diff)

Over any limit → abort with specific blocker message. Budget failures are **signals** the commit is too large — the remedy is to split it, not to raise the budget.

## Verdict Schema (bot-adversarial, deterministic)

| Verdict | Trigger | Action |
|---|---|---|
| `MUST-FIX` | Named runtime error with traceable path / CVE-class security (injection, SSRF, traversal, secret leak) / breaks existing test or compile / breaks documented public API / PR-introduced regression | Fix atomically |
| `BOT-WRONG` | Code reading disproves claim (condition doesn't occur / already handled / pattern doesn't match this project) | Record for audit trail — rebuttal |
| `BOT-NIT` | JSDoc / naming / format / extract-helper with <2 call sites / premature abstraction / style | Record for audit trail — defer reply |
| `BOT-SCOPE` | Would touch file not in current diff / cross-file refactor / rename public symbol / new abstraction layer | Record — defer + follow-up ref |
| `BOT-TASTE` | Uses softeners ("consider", "suggest", "could", "might want") AND no MUST-FIX trigger | Record — defer ack |

**Only MUST-FIX touches code.** All other verdicts go into the audit trail only.

**Tiebreak on ambiguity → defer, not fix.** Priority: `MUST-FIX > BOT-WRONG > BOT-SCOPE > BOT-NIT > BOT-TASTE`.

Never upgrade BOT-NIT → MUST-FIX because "it would be nicer". Never downgrade a real bug → BOT-TASTE because claim is softly worded.

## Phase 1: Collect Diff

```bash
if [ "$mode" = "--staged" ]; then
  git diff --cached
  git diff --cached --name-only
else
  git diff HEAD~1..HEAD
  git diff HEAD~1..HEAD --name-only
fi
```

Zero diff → "Nothing to pre-ship" + write sentinel + exit 0 (vacuously passed).

## Phase 2: 7-Lens Parallel Scan

Run 7 lenses on the same diff. Each has a sharp zone — stay silent outside it. Cross-lens duplicates on same `file:line + claim` deduplicated; keep the strictest verdict.

1. `coderabbit-style` — null/undefined deref without guard; unchecked `await` at IO boundary; off-by-one on indexing; incorrect type narrowing; magic numbers outside constants; swallowed exceptions (`catch {}`, re-throw losing cause); unhandled promise rejection; dead branches; shadowed vars; unused imports. Skews: `MUST-FIX` / `BOT-NIT`.

2. `copilot-style` — SQLi / XSS / SSRF / path-traversal / command-injection / open-redirect; secrets in logs or error messages; unclosed resources (streams / handles / DB conns); missing `finally` / `using` / `defer`; deprecated API; input-validation gaps at system boundary; outdated syntax where modern idiom is standard. Skews: `MUST-FIX` on security; `BOT-NIT` on idiom.

3. `codex-style` — edge cases (empty / max bound / concurrent / reentrancy / TOCTOU); race conditions on shared mutable state; assumption violations ("X is always defined" — prove it); error propagation clarity; behavior when dependency fails or returns empty. **Most likely source of real `MUST-FIX`.**

4. `strict-maintainer-style` — public API design (extensibility, back-compat, unflagged breaking change); new-code test coverage gaps; CHANGELOG entry presence; commit-message / scope discipline; module-boundary violations; undocumented public contract. Skews: `MUST-FIX` on contract break; `BOT-SCOPE` otherwise.

5. `gemini-style` — performance anti-patterns (O(n²) in hot paths, redundant allocations, sync-in-async, unnecessary cloning, unawaited promises in loops); readability (deep nesting, long param lists, unclear public-API names, primitive obsession); architecture consistency (layering violation, inappropriate cross-module imports); missing public-API docstrings. Skews: `BOT-NIT` / `BOT-TASTE`; real perf regressions → `MUST-FIX`.

6. `claude-code-style` — semantic mismatch (name / comment ≠ behavior); implicit or surprising side effects; missing error context on re-throw (lost `cause`); simpler equally-clear alternative; testability (hard-to-mock dependency); missing test for new logic branch; invariant should lift out of loop. Broadest lens — tiebreak to `BOT-TASTE` when purely preferential.

7. `greptileai-style` — **codebase-aware**. Inconsistency with existing patterns in THIS repo; duplicate logic where a utility already exists; naming / convention divergence from neighboring modules; similar bug fixed elsewhere but not applied here. **Before emitting a finding, run `Grep` or `Glob` to cite both the divergent site(s) AND the canonical site(s) in `evidence`. Never invent "inconsistency" without a concrete counter-site on disk.** Zero findings is valid.

**Zero findings from a lens is a valid output. Never invent findings to look thorough.**

## Phase 3: Verification

For every finding before emission:
1. `Read` the actual code + surrounding context
2. `Grep` for existing handling — concern may be addressed elsewhere
3. If asserting a project convention, sample 2-3 similar sites

Never trust the lens. Verify independently.

**Lens-7 extra check**: if a `greptileai-style` finding's `evidence` does not contain at least one concrete `file:line` reference to a counter-site → reject the finding silently.

## Phase 4: Classify & Branch

Build internal verdict table:

```yaml
round: 1
stats: { MUST-FIX: 1, BOT-WRONG: 0, BOT-NIT: 2, BOT-SCOPE: 1, BOT-TASTE: 1 }
findings:
  - id: 1
    lens: codex-style
    file: src/gateway/chat-attachments.ts
    line: 394
    claim: "OOXML sniff downgrades to application/zip"
    verdict: MUST-FIX
    evidence: "L394 finalMime prefers sniffedMime; isGenericMime guard missing"
    fix_plan: "Route MIME resolution through detectMime({buffer, headerMime, filePath})"
    fix_delta: "+3/-5"
    fix_files: [src/gateway/chat-attachments.ts]
  - id: 2
    lens: coderabbit-style
    file: src/gateway/chat-attachments.ts
    line: 458
    claim: "extract helper for marker logic"
    verdict: BOT-NIT
    evidence: "single call site"
    defer_reply: "Single call site — extraction is premature abstraction. Not changing."
```

Decision:
- `MUST-FIX == 0` → go to Phase 6 (audit trail + sentinel)
- `MUST-FIX > 0`:
  - Sum fix_delta > 30 → STOP: "fix surface exceeds budget (${delta} > 30) — split the commit"
  - Any fix needs new file → STOP: "fix requires new file ${f} — out of commit scope"
  - Round > 2 → STOP: "gate did not converge in 2 rounds — this commit must be split"
  - Else → Phase 5

## Phase 5: Atomic Fix (MUST-FIX > 0)

Apply **ALL** MUST-FIX `fix_plan`s in **one atomic edit pass**. Not one-by-one. The goal is one fix round = one conceptual convergence step, not a cascade of partial edits.

```bash
# After edits:
git add <fix_files only — never stage untracked or new files>

if [ "$mode" = "--committed" ]; then
  git commit --amend --no-edit  # preserves signing
fi
```

Re-enter Phase 1 with `round += 1`. Loop until `MUST-FIX == 0` or a STOP condition fires.

## Phase 6: Audit Trail + Sentinel

**Only reached when `MUST-FIX == 0`.**

### Build deferred block

From all non-MUST-FIX findings across the final round:

```
## Considered and deferred

- <file:line> [<verdict>]: <defer_reply>
- <file:line> [<verdict>]: <defer_reply>
```

Omit the entire block if zero deferred findings.

### Attach to commit body

- `--committed` mode: amend commit body to append the block:
  ```bash
  git commit --amend -m "$(git log -1 --pretty=%B)

  ## Considered and deferred

  - ..."
  ```
- `--staged` mode: print the block to stdout; the caller (ship / commit skill / user) is responsible for including it in the pending commit message.

### Write sentinel

```bash
cwd_hash=$(echo -n "$PWD" | shasum -a 256 | cut -c1-16)
touch "/tmp/.preship-ok-${cwd_hash}"
```

The Claude Code PreToolUse hook reads this sentinel. mtime within 5 minutes → allow `git commit` / `git push`. Absent or stale → block with instructions to run `/pre-ship` first.

**Never write the sentinel if any STOP condition fired, even if some MUST-FIX were resolved.** Partial progress ≠ gate passed.

## Phase 7: Report

Human-readable summary:

```markdown
## Pre-Ship — round <r>/2 (<mode>)

Findings: N total | MUST-FIX: M resolved | deferred: D
Fix delta applied: +<a>/-<b> | Exhausted: YES | Sentinel: /tmp/.preship-ok-<hash>

### Applied fixes (atomic)
| # | file:line | summary | delta |

### Deferred (written to commit body)
| # | verdict | file:line | defer_reply |
```

## Edge Cases

- No diff → "Nothing to pre-ship" + write sentinel + exit 0
- First-round fix delta already > 30 → STOP. Suggest `git reset HEAD <file>` + split via `gmc wt` or hunk staging.
- Lens 7 finding with empty / non-`file:line` evidence → silently drop (don't trust unverified inconsistency claims)
- Sentinel write fails (e.g. `/tmp` unwritable) → warn, continue. Hook will fail-safe (no sentinel = block), which is correct behavior.
- Invocation from `commit` skill (not yet wired) → use `--staged` mode; caller amends commit message

## Anti-patterns (bugs in this skill)

- Inventing lens findings to appear thorough
- Applying MUST-FIX one-by-one instead of atomic pass
- Fixing BOT-NIT / BOT-TASTE because "it's easy, might as well"
- Downgrading real bug to BOT-TASTE because claim was softly worded
- Extending scope beyond the diff being scanned
- Running a 3rd round despite `max_rounds = 2`
- Writing sentinel when any STOP fired (partial progress leaked)
- Lens 7 emitting "inconsistent with convention" without cited counter-site
