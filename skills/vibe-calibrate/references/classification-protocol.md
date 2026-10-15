# Classification Protocol

This file defines HOW messages are tagged. Tag definitions (WHAT each tag means) are in
`language-classifier.md`. This file covers analysis units, multi-label rules, the 3-layer
tagging pipeline, attribution logic, sampling strategy, and reporting rules.

## Analysis Unit

- Unit = one user message.
- If a message contains multiple text parts (e.g., OpenCode's `part` table), concatenate
  all text parts belonging to the same message before analysis.
- Attachments, file paths in tool calls, and error output are context for the message,
  not independent units.
- System-injected content (skill preambles, mode markers like `[search-mode]`,
  `[BACKGROUND TASK COMPLETED]`) are NOT user messages. Filter them out before tagging.

## Multi-Label Rules

- Tags cat1-cat5 are **non-exclusive**. A single message can carry 0, 1, or multiple tags.
- Common valid multi-tag combinations:
  - cat1 + cat3: "改 gateway-client.ts 的 reconnect 函数，我记得是在第 200 行左右" (specific + hedged)
  - cat2 + cat4: "能不能优化下性能，你觉得瓶颈在哪" (intent + judgment request)
  - cat1 + cat5: "不对，应该改的是 utils.ts 不是 helpers.ts" (correction + specific redirect)
- Prevalence per tag is computed independently. Rates do not need to sum to 100%.

## Layer 1: Deterministic Signal Extraction

The primary tagger. Operates on text patterns only. No LLM involved.

### Procedure

For each user message:

1. **Normalize**: strip leading/trailing whitespace, collapse multiple spaces.
2. **Filter**: skip messages that are pure tool invocations, empty, or system-injected.
3. **Scan for signal patterns** (defined below). Each pattern match produces a tag candidate.
4. **Assign confidence**:
   - `hard`: the signal pattern is unambiguous in isolation (see hard-tag rules below)
   - `soft`: the signal pattern matched, but context could change the meaning
5. **If no pattern matches**: mark `unclassified`. Do not guess.

### Hard-Tag Rules (high confidence, no context needed)

| Tag | Hard condition |
|---|---|
| cat1 | Message contains ANY of: (a) file path + action verb, (b) specific function/symbol/class name + explicit change ("把 X 改成 Y"), (c) exact string or code block to insert/replace/delete, (d) error message or stack trace + explicit action to take |
| cat3 | Message contains a **technical claim** (about code, config, behavior, architecture, tooling, or process) AND hedging language as a main clause: `我记得`, `好像是`, `大概是`, `可能是`, `似乎`. Non-technical hedging ("我记得你说过", "可能是我没表达清楚") does NOT qualify. |
| cat4 | Message contains: `第一性原理`, `最佳实践`, `你觉得呢`, `你觉得`, `从根本上`, `帮我分析` |
| cat5 | First 30 characters of message contain: `不对`, `错了`, `离谱`, `假的`, `废话`, `重来`, `算了` AS a standalone clause (not embedded in a description like "返回值不对") |

### Soft-Tag Rules (need context or Layer 2/3 to confirm)

| Tag | Soft condition |
|---|---|
| cat1 | Contains a function name or technical term with action intent, but specificity is borderline |
| cat2 | Contains `我想`, `我希望`, `能不能`, `感觉`, `太丑`, `不够` without specifics |
| cat3 | Contains `应该是`, `之前是` (ambiguous — could be cat1 if stated with full confidence) |
| cat5 | Contains `不要`, `不需要`, `不是这样` (ambiguous — could be cat1 instruction or goal change) |

### Delegation Signal Detection (separate from cat1-5 tagging)

Delegation is NOT a tag in the cat1-5 system. It is a separate signal detected in
Layer 1 but reported only to Axis 4 (Delegation Preference). It does not appear in
tag prevalence tables or coverage rates.

Detect as soft signals (never hard — delegation is always context-dependent):
- `你决定`, `你直接`, `你判断`, `你看着办`, `直接做`
- User gives a goal with no implementation guidance and no request for discussion

### Disambiguation of "不对" and similar patterns

"不对" appearing in a message does NOT automatically mean cat5. Apply these checks:

- If "不对" is the opening word or the first clause → likely cat5 (hard if within first 10 chars)
- If "不对" follows a noun phrase describing code behavior ("返回值不对", "状态不对") → NOT cat5, it describes a bug. May be cat2 (intent to fix) or cat1 (if specific enough).
- If "不对" appears mid-sentence in a technical description → soft cat5 at best, likely not cat5
- When in doubt → soft candidate, not hard tag

Similarly for "不要":
- "不要加注释" → cat1 (specific instruction), not cat5
- "不要！" or "不要这样" at message start → likely cat5
- "不要废话" → cat5

### Handling ambiguous / unclassifiable messages

- If a message matches zero hard or soft patterns → `unclassified`
- If a message could fit multiple categories and the dominant one is unclear → apply all
  matching soft tags, do not pick one
- Never synthesize a classification from surrounding messages. Each message is tagged
  based on its own content only. (Context is used in Layer 2 for attribution, not in
  Layer 1 for tagging.)

## Layer 2: Behavior Attribution

Scope: only processes cat5 hard and soft candidates from Layer 1.
Purpose: determine the root cause of each correction by examining what the AI did
before and after the correction message.

### Procedure

For each cat5 candidate:

1. **Retrieve the preceding AI turn**: the AI message(s) and tool calls immediately
   before the correction.

2. **Retrieve the following AI turn**: the AI message(s) and tool calls immediately
   after the correction.

3. **Check AI response to the correction**:
   - Did the AI change its approach? → normal correction, proceed to attribution.
   - Did the AI continue the same approach unchanged? → the correction was **ignored**.
     Do NOT remove the cat5 tag. This is still a real correction — and often the most
     valuable failure sample. Add the flag `ai_response=ignored` alongside the
     root-cause bucket. (If the Layer 1 tag was hard, the text evidence is strong enough
     to stand on its own regardless of AI's subsequent behavior.)
   - Only downgrade/remove cat5 if step 1+2 show the message was not addressed to
     the AI at all (e.g., user describing a code bug to themselves, quoting someone else).

4. **Attribute root cause** by examining the preceding AI turn:

   | Check | If true → bucket |
   |---|---|
   | AI's preceding action was based on a user cat3 message that AI did not verify (no tool call to check code/docs/logs between the cat3 message and the action) | `after_unverified_assumption` |
   | AI introduced content, features, UI elements, or scope that the user did not request in any preceding message | `after_scope_creep` |
   | AI's output had an observable defect: build failure, wrong file, broken UI, incorrect code, test failure | `after_quality_issue` |
   | User previously stated X with confidence (not hedged), AI verified or could verify, and X was factually wrong | `after_user_claim_disproven` |
   | None of the above clearly applies, or multiple apply, or evidence is insufficient | `unknown_or_mixed` |

5. **Rules**:
   - Apply at most one primary bucket. If genuinely two causes contributed, use `unknown_or_mixed`.
   - Only `after_user_claim_disproven` feeds into Claim Reliability (Axis 2).
   - The other buckets feed into CLAUDE.md rule recommendations.
   - When the conversation context is unavailable (e.g., truncated transcript), mark `unknown_or_mixed`.

## Layer 3: Sampled Adjudication

Scope: calibration check on Layer 1 and Layer 2 outputs.
This is NOT bulk classification. This is NOT ground truth. This is bias detection.

### Sampling Strategy

Draw a stratified sample from Layer 1 output:

| Stratum | What to sample | Target count |
|---|---|---|
| Hard positives | Messages with at least one hard tag | ~10-15 |
| Soft candidates | Messages with only soft tags | ~10-15 |
| Unclassified | Messages with no tags | ~10-15 |
| Layer 2 attributed | Cat5 candidates that received a root-cause bucket | ~5-10 |

Exact counts depend on available data. If total user messages are <100, sample proportionally
but do not skip any stratum.

### Adjudication Procedure

For each sampled message:

1. Present the message WITH full surrounding context (3 messages before and after).
2. The adjudicator (LLM) assigns tags and, for cat5, a root-cause bucket.
3. Compare with Layer 1/2 output.

### What to report

- Per-tag agreement rate between Layer 1 and adjudication
- Any systematic patterns in disagreement (e.g., Layer 1 over-tags cat5, or misses cat3)
- For Layer 2: agreement rate on root-cause buckets
- If agreement is low for a specific tag or bucket, flag that tag/bucket as
  **unreliable in this dataset** in the final report

### What Layer 3 is NOT

- It is not a replacement for Layer 1. Even if the LLM "disagrees" on a specific message,
  that does not automatically override Layer 1.
- It is not ground truth. LLM adjudication has its own biases (self-evaluation bias,
  recency bias, verbosity bias).
- Its purpose is to detect SYSTEMATIC errors in Layer 1/2, not to correct individual cases.

## Reporting Rules

### Rates and counts

- Always report both raw count and rate.
- For breakdown buckets with fewer than 5 items, report count only, not rate.
- When sample size is insufficient for a metric, label it `directional only` or
  `insufficient data`. Do not present it as a reliable finding.

### Claim Reliability extraction protocol

Claim Reliability (Axis 2) requires its own extraction pass, independent of corrections.
Do NOT rely solely on correction chains to populate this axis — that would miss two
critical sample types: (a) wrong claims that the AI caught and corrected proactively,
and (b) correct claims that were verified and confirmed.

**Step 1: Identify verifiable claim candidates**

Scan for user messages where:
- The user asserts a technical fact with reasonable confidence (not pure hedging)
- The claim is about something objectively checkable: file location, function behavior,
  config value, API response, error cause, version number, build step, etc.
- Examples: "这个 bug 是 reconnect 导致的", "release 流程是改 package.json 然后打 tag",
  "这个接口返回的是 JSON array"

Cat3 (hedged) messages are excluded unless the user also stated a concrete verifiable detail.
Cat2 (intent), cat4 (judgment requests), and cat5 (corrections) are excluded.

**Step 2: Check verification**

For each candidate, check whether subsequent conversation provides **tool-backed** verification:
- AI ran a tool call whose output confirmed or denied the claim (read file, grep, run command, check docs)
- Build/test result confirmed or denied
- AI cited specific tool output, file content, or runtime evidence when confirming or denying

What does NOT count as verification:
- AI stating "that's correct" or "that's wrong" without citing tool output or evidence
- AI proceeding to act on the claim without checking (this is unverified, not verified-true)
- AI's own reasoning or knowledge claims without tool backing

If no tool-backed verification occurred in the conversation, the claim is **unverified**
and does NOT enter the metric in either direction.

**Step 3: Tally**

- `verified_true`: user claimed X, verification confirmed X
- `verified_false`: user claimed X, verification showed not-X
  (includes both `after_user_claim_disproven` from Layer 2 AND proactively-caught wrong claims)
- `unverified`: no verification available — excluded from the metric

`verified_claim_accuracy = verified_true / (verified_true + verified_false)`

- Sample size thresholds:
  - <5: insufficient data — do not use for profiling decisions
  - 5-20: weak confidence — report as tentative
  - \>20: moderate confidence — usable for profiling

### Delegation Preference special rules

- Cannot be derived from cat1-5 tag distribution alone.
- Requires explicit delegation signal detection (separate from cat1-5 tagging; see
  "Delegation Signal Detection" section in Layer 1).
- If fewer than 3 explicit delegation signals found, report as "insufficient signal / mixed".

### Reliability caveats section

Every report MUST include a caveats section listing:
- Which axes have insufficient data
- Which tags showed low Layer 3 agreement
- Which root-cause buckets are dominated by `unknown_or_mixed`
- Any known limitations of the available data sources
