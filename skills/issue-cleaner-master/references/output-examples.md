# Output Format Examples

This document provides detailed examples of the required output files.

## JSON Report (`issues-report.json`)

Complete audit data for all issues in machine-readable format:

```json
{
  "metadata": {
    "repository": "kubernetes-sigs/gateway-api",
    "scan_time": "2024-02-28T10:30:00Z",
    "total_open_issues": 150,
    "included_count": 25,
    "excluded_count": 125
  },
  "issues": [
    {
      "number": 123,
      "title": "Fix typo in README",
      "url": "https://github.com/.../issues/123",
      "labels": ["good-first-issue", "help-wanted"],
      "assignees": [],
      "created_at": "2024-01-15",
      "updated_at": "2024-02-20",
      "included": true,
      "priority": "P0",
      "status": null,
      "include_reason": "Has good-first-issue + help-wanted labels, no assignee, no linked PR"
    },
    {
      "number": 456,
      "title": "Refactor auth module",
      "url": "https://github.com/.../issues/456",
      "labels": ["kind/feature"],
      "assignees": ["alice"],
      "created_at": "2024-01-01",
      "updated_at": "2024-01-05",
      "included": true,
      "priority": "P5",
      "status": "stale",
      "include_reason": "Assigned but stale (>30 days), no linked PR, may politely ask to contribute"
    },
    {
      "number": 789,
      "title": "How to configure TLS?",
      "url": "https://github.com/.../issues/789",
      "labels": ["question"],
      "assignees": [],
      "created_at": "2024-02-01",
      "updated_at": "2024-02-01",
      "included": false,
      "priority": null,
      "status": null,
      "exclude_reason": "Has question label, non-code contribution type"
    },
    {
      "number": 999,
      "title": "Fix API timeout",
      "url": "https://github.com/.../issues/999",
      "labels": ["kind/bug"],
      "assignees": ["bob"],
      "created_at": "2024-02-25",
      "updated_at": "2024-02-27",
      "included": false,
      "priority": null,
      "status": null,
      "exclude_reason": "Already assigned and active (updated within 30 days)"
    },
    {
      "number": 888,
      "title": "Add retry logic",
      "url": "https://github.com/.../issues/888",
      "labels": ["kind/feature"],
      "assignees": [],
      "created_at": "2024-02-10",
      "updated_at": "2024-02-10",
      "included": false,
      "priority": null,
      "status": null,
      "exclude_reason": "Has open PR #901 linked"
    }
  ]
}
```

## Reason Templates

| Scenario | Reason Example |
|----------|----------------|
| Include-P0 | "Has good-first-issue + help-wanted labels, no assignee, no linked PR" |
| Include-Stale | "Assigned but stale (>30 days), no linked PR, may politely ask to contribute" |
| Exclude-Assigned | "Already assigned and active (updated within 30 days)" |
| Exclude-Has PR | "Has open PR #N linked" |
| Exclude-Fixed | "Fixed by merged PR #N" |
| Exclude-Non-code | "Has question label, non-code contribution type" |
| Exclude-Title | "Title ends with question mark, classified as inquiry" |

## Markdown Report (`issues-report.md`)

Human-readable report grouped by priority:

```markdown
# Issue Screening Results

> Repository: kubernetes-sigs/gateway-api  
> Scan Time: 2024-02-28 10:30:00  
> Full Data: [issues-report.json](./issues-report.json)

## P0: Beginner-Friendly + Help Wanted (2)

| # | Title | Labels | Status | Created |
|---|-------|--------|--------|---------|
| [#123](https://...) | Fix typo in README | `good-first-issue`, `help-wanted` | - | 2024-01-15 |
| [#456](https://...) | Add missing test | `good-first-issue`, `help-wanted` | [Stale] | 2024-02-01 |

## P3: Bug Fixes (1)

| # | Title | Labels | Status | Created |
|---|-------|--------|--------|---------|
| [#789](https://...) | API returns 500 on edge case | `kind/bug` | - | 2024-02-20 |

---

## Summary

- Total open issues: 150
- Contributable issues: 25 (stale: 3)
- Excluded issues: 125
- P0: 2 | P1: 5 | P2: 8 | P3: 3 | P4: 4 | P5: 3

## Exclusion Reasons Distribution

| Reason | Count |
|--------|-------|
| Already assigned and active | 45 |
| Has open PR linked | 32 |
| Fixed by merged PR | 28 |
| Non-code contribution | 20 |
```

`[Stale]` indicates the issue has been assigned but inactive for over 30 days. You may politely ask if help is needed before contributing.

Skip empty priority groups in the output.
