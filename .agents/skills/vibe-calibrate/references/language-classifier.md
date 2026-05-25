# Tag Definitions

This file defines WHAT each tag means: semantics, boundary, signal words, and counter-examples.
It does NOT define how tagging is performed — that is in `classification-protocol.md`.

Tags are non-exclusive. A single message can carry multiple tags.

## cat1: Precise Instructions

The user provides a specific, actionable request with enough detail to execute without interpretation.

Signals:
- File paths, line numbers, function names
- Code snippets or exact strings to change
- "改 X 文件的 Y 函数，把 Z 换成 W"
- References to error messages, log output, or stack traces

Counter-examples:
- "应该是改那个文件吧" — hedging makes this cat3, not cat1
- "帮我优化下那个组件" — no specifics, this is cat2

Note: cat1 measures clarity of expression. Whether the instruction is technically correct
is a separate question (Claim Reliability axis). A message can be cat1 AND wrong.

## cat2: Intent Signals

The user describes a desired outcome, feeling, or direction without specifying implementation.

Signals:
- "感觉应该改改", "能不能优化下", "这个不太好"
- "我想要...", "我希望..."
- Desired outcome without how: "能不能让这个更快"
- UI/UX feedback: "太丑了", "不够明显", "位置不对"

Counter-examples:
- "能不能把 Button 的 padding 改成 8px" — specific enough for cat1
- "你觉得应该怎么优化" — seeking judgment, this is cat4

## cat3: Unverified Claims

The user expresses a technical hypothesis with uncertainty, or makes a technical assertion
without providing evidence. The hedging language itself signals that verification is needed.

Signals:
- "我记得是..." (I remember it's...)
- "好像是..." (It seems like...)
- "应该是..." (It should be...)
- "之前是..." without referencing specific commits or versions
- "大概是...", "可能是..."
- Any technical claim with hedging language

Counter-examples:
- "根据这个报错信息，问题是 X" — user provides evidence, may be cat1
- "你觉得是不是 X 的问题" — seeking judgment, this is cat4

Note: if the AI acts on a cat3 claim without verifying and it turns out wrong,
that is an AI behavior failure, not a user accuracy failure.

## cat4: Requests for Expert Judgment

The user explicitly asks the AI for analysis, opinion, or recommendation.

Signals:
- "第一性原理" (first principles)
- "最佳实践" (best practice)
- "你觉得呢" (what do you think)
- "从根本上分析" (analyze fundamentally)
- "应该怎么做" (how should I do this)
- "有什么好的方案" (any good approach)
- "帮我分析下" (help me analyze)

Counter-examples:
- "你直接改吧" — not seeking judgment, this is delegation
- "把它改成 X" — directive, this is cat1

Note: cat4 is a collaborative signal, NOT a delegation signal. "你觉得呢" means
"let's think together", not "you decide alone."

## cat5: Corrections / Rejections

The user signals that the AI's preceding action was wrong, unwanted, or off-target.

Signals:
- "不对" (wrong), "错了" (that's wrong)
- "不是这样" (not like this), "离谱" (absurd)
- "假的" (fake), "废话" (useless talk)
- "不要" (don't), "不需要" (don't need)
- "算了" (forget it), "重来" (redo)

Counter-examples:
- "这个函数的返回值不对" — describing a code bug, not correcting AI
- "不要用 var，要用 const" — this is cat1 (a specific instruction), even though it contains "不要"
- "我不需要这个功能了" — may be a goal change, not necessarily a correction of AI error

CRITICAL: cat5 is a signal about the AI's preceding behavior, not about the user's
technical accuracy. The root cause of a correction must be attributed via behavioral
analysis (Layer 2), not by text pattern alone.

## Delegation Signals (not a tag — used for Axis 4 only)

These phrases indicate the user wants the AI to act autonomously. They are detected
separately from cat1-5 and feed only into the Delegation Preference axis.

Signals:
- "你决定" (you decide)
- "你直接改" (just change it)
- "你判断就行" (your judgment is fine)
- "你看着办" (handle it as you see fit)
- "直接做" (just do it)
- User provides a goal with no implementation guidance and no request for options

These are NOT cat4. Cat4 seeks discussion; delegation signals expect execution.
