---
name: vibe-calibrate
description: >
  Cross-tool vibe coding profiler. Scans AI coding tool data on the machine
  (Claude Code sessions, OpenCode DB, Codex sessions),
  combined with git history and project memory, to build a true user portrait,
  discover workflow automation opportunities, and update the target tool's
  instruction file (CLAUDE.md or AGENTS.md) accordingly.
  Use when: "calibrate", "vibe-calibrate", "分析我的习惯", "profile me",
  "update my CLAUDE.md based on my history", "我的效率怎么提升",
  "analyze my patterns", "优化我的配置", or at the start of a long-term
  engagement with a new user.
argument-hint: "[--tool claude|codex|opencode] [--quick|--full] [--dry-run]"
---

IRON LAW: NEVER UPDATE ANY INSTRUCTION FILE BASED ON ASSUMPTIONS. EVERY CHANGE MUST TRACE TO OBSERVED DATA.

LANGUAGE RULE: Respond in the same language the user used in their most recent message.
All internal skill text (checkpoints, report templates) is in English. Output language follows the user.

# Vibe Calibrate

Build a true user portrait from cross-tool behavioral data, find error patterns,
diagnose instruction file misconfigurations, and propose targeted improvements.

## Tool Config Map

| Tool | Global instruction file | Notes |
|------|------------------------|-------|
| Claude Code | `~/.claude/CLAUDE.md` | Canonical source. Full rule set. |
| Codex | `~/.codex/AGENTS.md` | Exclude: skill references (`/skill`), `settings.json` audit rules, Claude Code hooks |
| OpenCode | `~/.config/opencode/AGENTS.md` | Same exclusions as Codex |

Each run targets ONE tool.

## Options

- `--tool <name>`: target tool — `claude` (default), `codex`, `opencode`.
- `--quick`: scan last 20 sessions per source. Skip Layer 3 calibration. Target: <60 seconds.
- `--full`: scan all sessions. Full pipeline including Layer 3 calibration.
- `--dry-run`: present findings and proposed diff without writing. Can combine with either mode.
- (no `--tool`): use AskUserQuestion to ask which tool to optimize before proceeding.
- (no `--quick`/`--full`): use AskUserQuestion to let the user choose scan depth.

## Scope Control

Two tiers only. No middle ground — 20 sessions vs all.
Session selection for quick: sort by file modification time descending, take top 20 per source.
All sample-size thresholds (3+ occurrences for rules, 5+ for claim reliability) still apply —
quick mode may produce more "insufficient data" caveats, which is correct behavior.

Settings.json audit is always performed for Claude Code (cheap and always useful). Not gated behind a flag.

## Target Tool Resolution

Before any data collection, resolve `TARGET_TOOL`:

1. If `--tool <name>` is provided, use it.
2. Otherwise, use AskUserQuestion:
   > Which tool do you want to optimize?
   > 1. **Claude Code** (`~/.claude/CLAUDE.md`)
   > 2. **Codex** (`~/.codex/AGENTS.md`)
   > 3. **OpenCode** (`~/.config/opencode/AGENTS.md`)

Set `TARGET_FILE` from the Tool Config Map based on selection.
All subsequent phases (data collection, diagnosis, output, apply) operate on `TARGET_FILE` only.

## Phase 0: Discover Data Sources + Pre-read [BLOCKING]

Locate ALL AI coding tool data on this machine. Run ALL of these in parallel
(data source probes + reference reads are independent — do not serialize):

**Data source probes** (parallel bash):
- [ ] `find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -not -path "*/subagents/*" | wc -l` — Claude Code sessions
- [ ] `ls -la ~/.local/share/opencode/opencode.db` — OpenCode SQLite
- [ ] `cat ~/.config/opencode/opencode.json` — OpenCode config
- [ ] `cat ~/.claude/settings.json` — Claude Code settings
- [ ] `find ~/.codex/sessions -name "*.jsonl" | wc -l` — Codex sessions
- [ ] `find ~/.claude/projects -path "*/memory/*.md" | wc -l` — Project memory files (feedback_*.md are high-value)
- [ ] `find ~ -maxdepth 4 -name "*.db" \( -path "*opencode*" -o -path "*codex*" \) 2>/dev/null` — Other tool data

**Pre-reads** (parallel Read tool — always needed, fetch now to avoid later serial wait):
- [ ] `TARGET_FILE` — the instruction file for the selected tool
- [ ] `references/classification-protocol.md` — tagging protocol
- [ ] `references/language-classifier.md` — tag definitions

Report which sources exist and their sizes. Missing sources are fine — work with what's available.

**Output checkpoint:**
```
[Sources] Claude Code: N sessions, OpenCode: N sessions, Codex: N sessions
[Scope] <mode>: scanning N most recent per source (M sessions total)
```

## Phase 1: Quantitative Profile [REQUIRED]

**PERFORMANCE RULE**: Use bash/python scripts for data extraction. NEVER spawn agents
for data extraction — agents add 90-210s overhead for work a script does in <10s.
Agents are only justified for tasks requiring iterative reasoning across multiple
external API responses where the next query depends on the previous result.
Run all independent scripts in parallel.

### 1A. Claude Code Sessions — Direct Script [PARALLEL]

Run this python script via a single Bash tool call. It extracts everything needed
for Phase 1 (stats), Phase 2 (message texts), and Phase 2.5 (skill invocations)
in one pass. Set `VC_LIMIT` env var: `20` for `--quick`, `0` for `--full`.

```python
import json, glob, os, re
from collections import Counter

LIMIT = int(os.environ.get("VC_LIMIT", "20")) or None

sessions = sorted(
    [f for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
     if "/subagents/" not in f],
    key=os.path.getmtime, reverse=True
)
if LIMIT:
    sessions = sessions[:LIMIT]

total_user = total_asst = total_tools = 0
parse_errors = 0
sessions_failed = 0
messages_skipped = 0
session_stats = []
all_messages = []
skill_invocations = []

def is_skip(text):
    """Structural detection: identify system-injected content."""
    if not text: return True
    if text.startswith('<') and ('>' in text[:60]): return True
    if text.startswith('[Request interrupted'): return True
    if len(text) > 500 and re.match(r'^(---|#\s+[A-Z]|Base directory for this skill:)', text): return True
    return False

def extract_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        return " ".join(
            p.get("text", "") for p in content
            if isinstance(p, dict) and p.get("type") == "text"
        )
    return ""

for sf in sessions:
    sid = os.path.basename(sf)[:8]
    u = a = t = 0
    first_msg = ""
    session_err = 0
    with open(sf) as f:
        for line in f:
            try:
                obj = json.loads(line)
                typ = obj.get("type")
                if typ in ("human", "user"):
                    text = extract_text(obj.get("message", {}).get("content", "")).strip()
                    cmd_match = re.search(r'<command-name>(/\S+)</command-name>', text) if text else None
                    if text and text.startswith('/'):
                        skill_invocations.append(f"{sid}|{text.split()[0]}")
                        messages_skipped += 1
                        continue
                    if cmd_match:
                        skill_invocations.append(f"{sid}|{cmd_match.group(1)}")
                        messages_skipped += 1
                        continue
                    if is_skip(text):
                        messages_skipped += 1
                        continue
                    u += 1
                    if not first_msg:
                        first_msg = text[:100]
                    all_messages.append(f"{sid}|{text[:200]}")
                elif typ == "assistant":
                    a += 1
                    for part in obj.get("message", {}).get("content", []):
                        if isinstance(part, dict) and part.get("type") == "tool_use":
                            t += 1
            except Exception:
                parse_errors += 1
                session_err += 1
    if session_err > 0 and u == 0 and a == 0:
        sessions_failed += 1
    total_user += u; total_asst += a; total_tools += t
    session_stats.append((sid, u, a, t, first_msg))

buckets = Counter()
for _, u, *_ in session_stats:
    if u < 10: buckets["<10"] += 1
    elif u < 50: buckets["10-50"] += 1
    elif u < 100: buckets["50-100"] += 1
    else: buckets[">100"] += 1

print("=== STATS ===")
print(f"sessions_scanned={len(sessions)} sessions_failed={sessions_failed}")
print(f"user_msgs={total_user} asst_msgs={total_asst} tools={total_tools}")
print(f"parse_errors={parse_errors} messages_skipped={messages_skipped}")
print(f"avg_user={total_user/max(len(sessions),1):.1f} avg_tools={total_tools/max(len(sessions),1):.1f}")
print(f"buckets: {dict(buckets)}")
if parse_errors > total_user * 0.1:
    print("[DEGRADED] parse_errors exceed 10% of user messages — results may be unreliable")
print("=== SESSIONS ===")
for sid, u, a, t, fm in session_stats:
    print(f"{sid}|u={u}|a={a}|t={t}|{fm}")
print("=== MESSAGES ===")
for m in all_messages:
    print(m)
print("=== SKILLS ===")
for s in skill_invocations:
    print(s)
```

This produces four sections in one output:
- `=== STATS ===` — aggregate numbers + reliability indicators for Phase 1
- `=== SESSIONS ===` — per-session breakdown
- `=== MESSAGES ===` — user message texts for Phase 2 tagging (preambles excluded)
- `=== SKILLS ===` — skill/command invocation sequence for Phase 2.5 workflow discovery

### 1B. OpenCode Database — Direct SQL [PARALLEL]

Schema reference: `references/data-sources.md` (OpenCode SQLite section).
Key fact: `message` has NO `role`/`content` columns — role is in `json_extract(data, '$.role')`.
User text lives in `part.data` where `type="text"`, not in `message.data`.

**Always probe schema first** to guard against version drift:

```bash
sqlite3 ~/.local/share/opencode/opencode.db << 'SQL'
.headers on
PRAGMA table_info(message);
PRAGMA table_info(session);

SELECT 'totals' as q, COUNT(*) as sessions FROM session;
SELECT 'roles' as q, json_extract(data, '$.role') as role, COUNT(*) as n
  FROM message GROUP BY role;
SELECT 'long_sessions' as q, COUNT(*) as n FROM (
  SELECT session_id FROM message GROUP BY session_id HAVING COUNT(*) > 100);
SELECT 'tools' as q, json_extract(data, '$.tool') as tool,
  SUM(CASE WHEN json_extract(data, '$.state.status')='error' THEN 1 ELSE 0 END) as errors,
  COUNT(*) as total
  FROM part WHERE json_extract(data, '$.type')='tool'
  GROUP BY tool ORDER BY errors DESC LIMIT 15;
SELECT 'recent_user_msgs' as q, substr(json_extract(p.data, '$.text'), 1, 200) as text
  FROM part p JOIN message m ON p.message_id = m.id
  WHERE json_extract(m.data, '$.role') = 'user'
    AND json_extract(p.data, '$.type') = 'text'
    AND length(json_extract(p.data, '$.text')) > 20
  ORDER BY p.time_created DESC LIMIT 100;
SQL
```

If `PRAGMA table_info` shows unexpected columns, adapt queries to match.
If the DB file does not exist, skip OpenCode analysis entirely.

### 1C. Git History — Bash + jq [PARALLEL, BACKGROUND]

Two independent bash calls, both run in parallel. Git data is only consumed in
Phase 4 (report), not Phase 2 (tagging), so run in background — do not block
Phase 2 on these results.

**Call 1 — local git stats (instant):**
```bash
echo "=== GIT LOCAL ==="
echo "total_commits=$(git log main --oneline | wc -l | tr -d ' ')"
echo "=== COMMIT STYLE ==="
git log main --format='%s' -100 | grep -oE '^[^ :(]+' | sort | uniq -c | sort -rn | head -10
echo "fix_count=$(git log main --format='%s' | grep -ciE '^\[Fix\]|^\[Bug\]|^fix[(:]|^fix:')"
echo "=== FIX SAMPLES ==="
git log main --format='%s' | grep -iE '^\[Fix\]|^\[Bug\]|^fix[(:]|^fix:' | head -15
```

The COMMIT STYLE section shows the repo's actual prefix distribution. Use it to
determine which prefixes count as "fix" — do not assume a format. If no clear
fix-style prefix is detectable, output `fix_style=unknown` and note in the report
that fix ratio is not inferable.

**Call 2 — GitHub PR stats (~20-30s API IO, use Bash tool's `run_in_background` parameter):**
```bash
if command -v gh &>/dev/null; then
  gh pr list --state merged --limit 200 \
    --json number,title,additions,changedFiles \
    --jq '
      "total_prs=\(length)",
      "violations=\([.[] | select(.additions > 500 or .changedFiles > 30)] | length)",
      "avg_additions=\([.[].additions] | add / length | floor)",
      "avg_files=\([.[].changedFiles] | add / length | floor)",
      "=== TOP VIOLATORS ===",
      (.[] | select(.additions > 500 or .changedFiles > 30)
       | "#\(.number) +\(.additions)/\(.changedFiles)f \(.title)")
    '
else
  echo "gh not available — skipping PR stats"
fi
```

Compute (from the jq output — no agent reasoning needed):
- Fix commit ratio (fix / total)
- PR budget violation rate (>500 lines or >30 files)
- Fix commits by scope (which areas break most)

### Phase 1 Parallelism Plan

```
                    ┌── 1A: python script (Claude Code) ──── <10s
Phase 0 complete ──├── 1B: sqlite3 batch (OpenCode) ──────── <10s
                    ├── 1C-local: git log (instant) ────────── <1s
                    ├── 1C-gh: gh pr list + jq (BACKGROUND) ── ~20-30s (API IO)
                    └── Bash: settings.json + codex stats ──── <5s

Phase 2 starts immediately after 1A+1B complete (~10s).
1C-gh results arrive during Phase 2, consumed in Phase 4 report.
```

**Output checkpoint** (emit as each completes):
```
[Stats] Claude Code: N user msgs, N tool uses, avg N msgs/session
[Stats] OpenCode: N user msgs, N tool uses
[Stats] Git: N commits, N% fix ratio (or "unknown" if commit style not inferable), N PR budget violations
[Flag] N sessions >100 msgs (possible scope creep / missing handoff)
```

## Phase 2: Behavioral Pattern Analysis [REQUIRED]

### 2A. Message Tagging Protocol

Tag user messages using the 3-layer protocol defined in `references/classification-protocol.md`.

Key constraints:
- Tags are **non-exclusive**. One message can carry multiple tags.
- Each tag has one of three states: `hard` (high-confidence deterministic match), `soft` (candidate, not confirmed), or `unclassified`.
- The primary tagger is Layer 1 (deterministic signal extraction). LLM is NOT used for bulk classification.
- Tag definitions and signal lists are in `references/language-classifier.md`. That file defines WHAT each tag means. The protocol file defines HOW tagging is performed.

Output:
- Per-tag prevalence (hard count, soft count)
- Hard coverage rate, soft coverage rate, unclassified rate
- All rates are over total user messages as denominator

**Output checkpoint:**
```
[Tags] N corrections (N hard, N soft), N hedged claims, N judgment requests
[Tags] Hard coverage: N%, Unclassified: N%
```

### 2B. Correction Attribution

For all cat5 hard and soft candidates, run the Layer 2 behavior attribution protocol
(defined in `references/classification-protocol.md`, Layer 2 section).

This step does NOT re-classify text. It inspects the AI action immediately preceding the
correction and the behavioral change immediately following it.

**Data dependency**: Layer 2 requires the AI messages before and after each correction.
Phase 1A's 200-char message truncation is insufficient for this. When attributing a
cat5 candidate, read the original session JSONL to retrieve full context (3 turns
before and after the correction message).

Attribution buckets:
- `after_unverified_assumption`
- `after_scope_creep`
- `after_quality_issue`
- `after_user_claim_disproven`
- `unknown_or_mixed`

When evidence is insufficient, default to `unknown_or_mixed`.

**Output checkpoint** (report top 3 causes only):
```
[Attribution] Top correction cause: <bucket> (N/total, N%)
[Attribution] N corrections were IGNORED by AI — highest value signal
```

### 2C. User Portrait (4 axes)

Compute 4 independent axes — never collapse into one number:

1. **Instruction Precision** — how specific and executable are user requests?
   Source: cat1 hard + soft tag prevalence (hard tags carry full weight; soft tags
   are reported separately so the reader can judge). See expanded cat1 hard-tag
   rules in `references/classification-protocol.md`.
   Measures clarity of expression, not technical correctness.

2. **Claim Reliability** — when user makes verifiable technical claims, how often are they correct?
   Source: standalone claim extraction protocol (see `references/classification-protocol.md`,
   Claim Reliability section). This is independent of the correction chain — it captures
   both AI-proactively-caught wrong claims AND confirmed-correct claims, not just
   correction-triggered ones.
   Always report sample size. Confidence:
   - <5 verifiable claims: **insufficient data** — do not use for profiling
   - 5-20: **weak confidence** — report as tentative / directional only
   - \>20: **moderate confidence** — usable for profiling

3. **Correction Intensity** — how often does the user reject or redirect AI output?
   Source: cat5 hard + confirmed-soft prevalence, with root-cause breakdown from 2B.
   This is NOT a negative signal about the user.

4. **Delegation Preference** — directive / collaborative / delegative / mixed?
   Cannot be inferred from cat1-5 tags alone. Requires explicit delegation signals
   detected as a separate pass in Layer 1 (see `references/classification-protocol.md`,
   Delegation Signal Detection section). Delegation signals are NOT part of the cat1-5
   tag system and do not appear in tag prevalence tables.
   If evidence is unclear, report as "mixed".

### 2D. User Archetype (derived from 4 axes)

Map the 4-axis profile to an archetype. These are interaction styles, not competence labels:

- **High-precision operator**: high precision, high correction, high claim accuracy.
  → AI should execute faithfully, minimize unsolicited additions.
- **Intent-driven product thinker**: high intent signals, high judgment requests, few verifiable claims.
  → AI must do technical convergence. Propose before building.
- **Hypothesis-heavy explorer**: high unverified claim rate, medium-high corrections.
  Claim accuracy may vary or be insufficient data — do not assume it is low.
  → AI MUST verify before acting on any claim.
- **Low-friction delegator**: low correction, explicit delegation signals.
  → AI can be more autonomous, but must still verify facts.

If the user doesn't fit cleanly, report the two closest with relative weight.

### 2E. Error Cascades

Find sequences where:
1. User makes a claim (especially cat3 with hedging language)
2. AI acts on it WITHOUT verifying
3. Correction follows or build/test fails
4. Multiple follow-up messages to fix the chain

Attribute using Layer 2 rules. If attribution is unclear, label `unknown_or_mixed`.

### 2F. Session Length Distribution

Flag:
- Many <5 msg sessions = possible abandonment
- Many >100 msg sessions = scope creep, missing HANDOFF checkpoints

### 2G. Cross-Tool Consistency

Compare rules/configs across tools:
- Claude Code settings.json vs CLAUDE.md (contradictions?)
- OpenCode opencode.json permissions vs user expectations
- Different tools getting different instructions for the same project
- CLAUDE.md vs AGENTS.md drift (flag if detected, but do not auto-sync)

### 2H. Layer 3 Calibration [CONDITIONAL]

**Skip if `--quick`** — sample size too small for meaningful calibration. Report `[Layer 3 skipped: quick mode]`.

Otherwise, run the sampled adjudication protocol from `references/classification-protocol.md`, Layer 3.

Purpose: check whether Layer 1 and Layer 2 have systematic bias or blind spots.
This is calibration, not ground truth. Report any detected biases in the final output.

## Phase 2.5: Workflow Automation Discovery [REQUIRED]

Identify repetitive multi-step interaction patterns that could be abstracted into
skills, commands, or pipelines to reduce manual overhead.

### Procedure

1. **Extract workflow sequences**: For each session, reconstruct the sequence of
   user actions (message intents + skill invocations). Look for recurring N-step
   sequences (N >= 2) that appear across 3+ sessions.

2. **Inventory existing skills**: List all skills available in the current environment
   (from `~/.claude/skills/`, enabled plugins, and built-in slash commands).

3. **Cross-reference and classify** each detected pattern:

   | Status | Meaning | Action |
   |--------|---------|--------|
   | `covered` | An existing skill or command chain already handles this workflow | Explain WHY the user still performs manual steps despite coverage (e.g., "reviews almost always have blockers requiring human judgment, so further automation adds no value") |
   | `partial` | Existing skills cover some steps but gaps remain | Identify the specific uncovered gap and whether it's automatable |
   | `opportunity` | No existing skill covers this pattern | Propose a concrete skill with name, trigger, and what it automates |

4. **Filter for real value**: Only surface opportunities where:
   - The pattern occurs 3+ times across sessions (not a one-off)
   - The manual steps are genuinely repetitive (not just "similar but each requires unique judgment")
   - Automation would save meaningful interaction rounds (>= 2 msgs eliminated per occurrence)

5. **For each `covered` pattern**: Analyze the actual session data to determine if
   the multi-step nature is inherent or accidental:
   - `covered — inherent`: Steps require human judgment between them (e.g., review
     findings need human triage before fix). Do NOT propose further automation.
   - `covered — accidental`: Existing skills cover all steps and no human judgment is
     needed between them, but the user currently invokes them manually in sequence.
     Propose a pipeline skill that chains them.

### Output checkpoint
```
[Workflow] N recurring patterns detected, N covered, N partial, N opportunity
[Opportunity] "<name>" — <trigger> — saves ~N msgs/session — <brief description>
```

### Output format (in Phase 4 report)

```markdown
## Workflow Automation Discovery

| # | Pattern | Sessions | Status | Existing Skill | Gap / Proposal |
|---|---------|----------|--------|----------------|----------------|
| 1 | ... | N | covered — inherent | /skill-name | Why manual steps remain |
| 2 | ... | N | opportunity | — | Proposed /skill-name + description |
```

## Phase 3: Instruction File Diagnosis [REQUIRED]

### 3A. TARGET_FILE Diagnosis

Read `TARGET_FILE` and evaluate:

- [ ] Does the Persona section match the portrait from Phase 2C?
- [ ] Do the Core Rules match actual behavior patterns?
- [ ] Are there dead rules the user routinely violates or AI routinely ignores?
- [ ] Are there recurring errors from Phase 2E that have no corresponding rule?
- [ ] Are there tool-specific contradictions? (e.g., settings.json vs CLAUDE.md for Claude Code,
      config.toml vs AGENTS.md for Codex)

### 3B. Settings/Config Audit [ALWAYS for Claude Code, BEST-EFFORT for others]

Check for:
- `bypassPermissions` vs git safety rules (contradiction)
- Conflicting effortLevel in multiple places (settings.json `effortLevel` vs env `CLAUDE_CODE_EFFORT_LEVEL`)
- Disabled safety features (`DISABLE_GIT_INSTRUCTIONS`, etc.) vs CLAUDE.md safety rules
- Permission rules that block desired workflows

**Output checkpoint:**
```
[Dead rule] "<rule text>" — 0 corrections, 0 violations found in scanned sessions
[Missing rule] <pattern description> — N corrections, no CLAUDE.md rule covers this
[Ignored rule] "<rule text>" — rule exists but N corrections show AI bypassed it
[Conflict] settings.json <field>=<value> vs CLAUDE.md "<rule text>"
```

## Phase 3.5: Axis → Rule Mapping [REQUIRED]

For each axis, check against the mapping table below. Only propose rules where
the condition is met AND no equivalent rule already exists in `TARGET_FILE`.

### Mapping Table

| Condition | Rule template | Applies when |
|---|---|---|
| Correction cause `scope_creep` >= 30% of attributions | "Do not add features, UI, or code beyond what was explicitly requested" | Always |
| Correction cause `unverified_assumption` >= 25% | "When user says '我记得/好像/应该是', verify via tool call before acting" | Always |
| Correction cause `quality_issue` >= 25% | "Run [project verification gate] before claiming done" | If project has a gate |
| Corrections with `ai_response=ignored` >= 2 | Strengthen the specific ignored rule with [HIGH] marker | Per-rule |
| Hedge signals (cat3) > 20% of user msgs | "Default to verify-first on all technical claims" | Claim Reliability < 70% or insufficient data |
| Judgment requests (cat4) > 15% | "Propose before building on non-trivial changes" | Delegation != delegative |
| Delegation signals dominant | "Can proceed without confirmation on routine changes within stated scope" | Low correction rate |
| Delegation signals rare + high correction | "Always present plan before mutating" | Always |
| settings.json contradiction found | Report contradiction with specific fix for each side | Always |

### Rule dedup protocol

Before proposing a new rule:
1. Grep existing `TARGET_FILE` for keyword overlap (>50% shared terms) — if equivalent exists, skip or propose strengthening
2. If contradicts existing rule, propose replacement not addition
3. Never exceed ~150-line budget — if at limit, propose which rule to remove

## Phase 4: Present Findings [REQUIRED]

```markdown
## Tagging Summary
- Total user messages analyzed: [N]
- Hard-tagged: [N] ([%])
- Soft candidates: [N] ([%])
- Unclassified: [N] ([%])
- Per-tag prevalence (hard / soft): cat1=[N]/[N], cat2=..., cat3=..., cat4=..., cat5=...
- Layer 3 calibration: [any detected biases, "no systematic bias detected", or "skipped (quick mode)"]

## User Portrait (4-axis)
- Instruction Precision: [rate] — [interpretation]
- Claim Reliability: [verified_true/total_verifiable] (n=[sample_size], confidence=[level]) — [interpretation]
- Correction Intensity: [rate] — root-cause breakdown (count or rate):
  - after_unverified_assumption: [N or rate]
  - after_scope_creep: [N or rate]
  - after_quality_issue: [N or rate]
  - after_user_claim_disproven: [N or rate]
  - unknown_or_mixed: [N or rate]
- Delegation Preference: [directive / collaborative / delegative / mixed]
- Archetype: [one or two from 2D]

## Correction Root Cause Analysis
Top corrections with attributed cause:
1. [correction text] — cause: [bucket or unknown]
(If chain is ambiguous, mark unknown. Do not force.)

## Error Pattern Ranking (by cost)
1. [Pattern] — [frequency] — [evidence]

## Settings/Config Audit
- [Conflict] / [Dead setting] / [No issues] with evidence for each finding

## Workflow Automation Discovery
| # | Pattern | Sessions | Status | Existing Skill | Gap / Proposal |
|---|---------|----------|--------|----------------|----------------|
[For each detected pattern, one row. Status: covered — inherent, covered — accidental, partial, opportunity]

## TARGET_FILE Issues
1. [Rule/section] — [problem] — [evidence]

## Proposed Changes (from Phase 3.5 mapping)
[Specific diffs. Each must cite: (1) which mapping table row triggered it, (2) the data threshold that was met, (3) verification that no equivalent rule exists]

## Reliability Caveats
- [List any axes, rates, or conclusions that are directional-only due to low sample size]
- [List any known Layer 3 calibration issues]
```

## Phase 5: Apply Changes [CONDITIONAL]

- If `--dry-run`: stop after Phase 4
- Otherwise: apply changes to `TARGET_FILE` after user confirms the diff
- Re-read the file after writing to verify correctness
- NEVER change settings.json / config.toml without explicit user approval

## Anti-Patterns

- Do not use LLM for bulk message classification. LLM is Layer 3 calibration only.
- Do not treat cat1-5 as mutually exclusive. They are non-exclusive tags.
- Do not force attribution when evidence is insufficient. Use `unknown_or_mixed`.
- Do not use the word "ground truth" for LLM judgments. LLM does adjudication, not ground truth.
- Do not profile from a single session — need cross-session data.
- Do not add rules to instruction files for one-off incidents — require 3+ occurrences.
- Do not let any instruction file exceed ~150 lines.
- Do not interpret correction rate as user competence. It is an AI behavior signal.
- Do not draw Claim Reliability conclusions from <5 verifiable samples.
- **Do not spawn agents for data extraction.** Agents add 90-210s overhead for work a
  bash/python script does in <10s. The Phase 1 python script extracts stats, message texts,
  and skill invocations in one pass — do not create separate extraction steps.
- **Do not serialize reference file reads.** Read `classification-protocol.md`,
  `language-classifier.md`, and `CLAUDE.md` in Phase 0 alongside data source probes.
  These are always needed and cost <2s each — waiting until Phase 2 to read them wastes
  a serial round trip.
