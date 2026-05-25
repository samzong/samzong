# Analysis Output Template

Use this template when writing the output file for `analyze` mode.

## File structure

One H1 header with metadata, then one H2 section per analyzed issue.

````md
# Issue Analysis

> Repository: owner/repo
> Analyzed: YYYY-MM-DD
> Issues: #N, #N

## Issue #N: <title>

### Classification

Bug / Feature Request / Enhancement / Refactor

### Summary

<one sentence: what the issue is about>

### Investigation

<what was examined: files, execution paths, relevant code>

### Findings

**For bugs:**
- **Root cause**: <specific mechanism and location>
- **Location**: `file:line` or symbol name
- **Trigger**: <concrete reproduction scenario>
- **Impact**: <what breaks, who's affected>

**For features:**
- **Current state**: <how the system handles this today>
- **Gap**: <what's missing or insufficient>

### Recommendation

**For bugs — fix direction:**
- Approach: <minimal fix>
- Files to modify: <list>
- Risk: <what could go wrong>
- Verification: <how to confirm the fix>

**For features — design options:**

#### Option A: <name>
- Approach: <description>
- Files: <what changes>
- Pros / Cons

#### Option B: <name>
- ...

**Recommended**: Option X because <reason>

### Scope Estimate

Small / Medium / Large — <brief justification>
````

Rules:
- Include only sections that apply (bug sections for bugs, feature sections for features)
- Reference specific files and symbols, not vague module names
- Keep recommendations actionable — another engineer should be able to start work from this
