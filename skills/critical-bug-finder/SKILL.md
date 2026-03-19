---
name: critical-bug-finder
description: >
  Find critical implementation bugs that cause crashes, data corruption, security vulnerabilities,
  deadlocks, race conditions, or fundamentally broken logic. Use when: user says "find bugs",
  "find critical bugs", "audit for bugs", "check for fatal bugs", "security audit code",
  "find vulnerabilities", "bug hunt", "reliability check", or any request to scan code for
  severe implementation defects. Also triggers on: "crash", "data loss", "race condition",
  "deadlock", "SQL injection", "XSS", "RCE". Does NOT trigger for: code review, refactoring,
  style checks, performance optimization, or design feedback.
---

# Critical Bug Finder

Assume the role of a Senior Reliability & Security Engineer. The sole mission: find implementation
bugs that would cause production incidents.

## Qualifying Bug Categories (report ONLY these)

1. **Crash / panic / uncaught exception** - unhandled error paths, null dereferences, type errors at runtime
2. **Data corruption / loss / silent wrong results** - write-after-write conflicts, truncated writes, missing atomicity
3. **Security vulnerabilities** - SQL injection, XSS, RCE, path traversal, auth bypass, credential exposure, SSRF
4. **Infinite loop / deadlock / resource exhaustion** - unbounded allocations, lock ordering violations, missing loop exits
5. **Race conditions** - TOCTOU, unprotected shared state, non-atomic check-then-act
6. **Core logic errors** - actual behavior contradicts documented/intended behavior

## Strict Exclusions (NEVER report)

- Design opinions, architecture suggestions, naming conventions
- Performance issues (slow queries, missing indexes, O(n^2) unless it causes OOM)
- Code style, readability, documentation gaps
- Refactoring opportunities, DRY violations
- "Nice to have" improvements

## Workflow

### Phase 1: Scope

1. If user specifies files/directories, scope to those. Otherwise scan the full project.
2. Read CLAUDE.md or equivalent to understand the project's expected behavior.
3. Identify high-risk areas: state mutations, DB/file operations, concurrency, input handling, auth checks.

### Phase 2: Systematic Audit

Use a multi-agent team for large codebases. Assign each agent a directory or module.

For each file, analyze in order of risk:

1. **Input boundaries** - user input, API params, file reads, env vars. Check: validation, sanitization, type coercion.
2. **State mutations** - DB writes, file writes, in-memory state changes. Check: atomicity, error rollback, ordering.
3. **Concurrency** - shared mutable state, async operations, locks. Check: race conditions, deadlocks, TOCTOU.
4. **Error paths** - catch blocks, error callbacks, finally blocks. Check: swallowed errors, incomplete cleanup, resource leaks.
5. **Auth/authz** - permission checks, session handling, token validation. Check: bypass routes, privilege escalation.
6. **Crypto/secrets** - key handling, hashing, random generation. Check: hardcoded secrets, weak algorithms, timing attacks.

### Phase 3: Validate Findings

For each candidate bug, verify:
- It actually triggers under realistic conditions (not just theoretical)
- The consequence matches one of the 6 qualifying categories
- A concrete exploit path or failure scenario exists

Discard anything that doesn't pass all three checks.

### Phase 4: Output

Save results to `./bugs_{4-random-chars}.md` in the project root.

Use this exact format:

````markdown
# Critical Bug Audit Report

**Project**: {project name}
**Date**: {date}
**Scope**: {files/dirs audited}

## Findings

```json
{
  "critical_bugs": [
    {
      "severity": "CRITICAL or HIGH",
      "location": "file:line or function_name",
      "description": "One sentence: what the bug is",
      "why_fatal": "Why this causes one of the 6 qualifying consequences",
      "trigger": "Concrete scenario that triggers this bug",
      "suggested_fix": "Minimal code patch (only necessary changes)"
    }
  ],
  "files_audited": ["list of files examined"],
  "summary": "Found N critical bugs across M files"
}
```

## Details

For each bug, include:
- Full code context (the vulnerable code block)
- Step-by-step trigger scenario
- Suggested fix with diff
````

If zero qualifying bugs are found, output:

```json
{"critical_bugs": [], "files_audited": [...], "summary": "No critical implementation bugs found"}
```

## Checklist Reference

See [references/checklist.md](references/checklist.md) for the detailed per-language vulnerability checklist
used during Phase 2 analysis.
