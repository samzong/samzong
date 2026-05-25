---
name: simplify
description: >
  Ruthless code simplifier: flatten abstractions, inline wrappers, remove unnecessary layers,
  delete dead code — without changing behavior. Use when: user says "simplify", "simplify this",
  "flatten", "inline", "too complex", "over-engineered", "remove abstraction", "unwrap",
  "reduce complexity", "make it simpler", "this is too complicated", or points at code that
  has unnecessary indirection. Does NOT change behavior, break public APIs, or remove
  meaningful error handling.
---

# Simplify

Ruthless code simplifier. Make code shorter, flatter, more direct. Never change behavior.

## Step 1: Identify Target

If user specifies a file or symbol, focus there. Otherwise check recently modified files or ask.

## Step 2: Diagnose Complexity

Look for:
- Wrapper functions/classes that add no logic
- Interfaces/abstractions used in only one place
- Intermediate variables that don't aid readability
- Factory/builder/strategy patterns where a plain function suffices
- Catch-and-rethrow with no transformation
- Dependency injection for things that never vary
- Config objects with only one consumer

## Step 3: Simplify

For each issue:
- Inline wrappers
- Delete unused abstractions
- Replace single-use interfaces with concrete types
- Flatten nested callbacks or promise chains
- Remove dead code paths

**Do NOT:**
- Change behavior
- Remove meaningful error handling
- Break public APIs
- Rename without clear reason

## Step 4: Report

Show diff-style summary with specific justification per change:
- "Removed `FooWrapper` — only called `foo()` with no modification"
- "Inlined `buildConfig()` — called exactly once, no reuse"
