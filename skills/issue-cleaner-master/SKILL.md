---
name: issue-cleaner-master
description: Analyze GitHub repository issues by checking assignee status, linked PRs, and label signals, then filter and rank contributable issues by priority (P0-P5). Outputs machine-readable JSON and human-readable Markdown reports. Use when looking for contributable issues, finding contribution opportunities, searching for good-first-issue, finding help-wanted issues, or discovering beginner-friendly tasks.
---

# Issue Cleaner Master

Analyze GitHub issues in the current repository and filter high-quality issues suitable for contribution.

## Workflow

### Step 1: Get Repository Info

Get the current repository's owner and repo name:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Parse into `{owner}` and `{repo}` variables for subsequent use.

**Validation**: Ensure the output is in `owner/repo` format. If empty or error, verify you're in a git repository with a GitHub remote.

### Step 2: Fetch Issue Data

Use GraphQL API to fetch all open issues (supports pagination, no limit):

```bash
gh api graphql --paginate -f query='
query($endCursor: String) {
  repository(owner: "{owner}", name: "{repo}") {
    issues(states: OPEN, first: 100, after: $endCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        createdAt
        updatedAt
        labels(first: 20) { nodes { name } }
        assignees(first: 10) { nodes { login } }
      }
    }
  }
}'
```

**Validation**: Verify response contains `data.repository.issues.nodes` array. Handle errors:
- `401/403`: Run `gh auth status` to check authentication
- Rate limit: Wait and retry, or reduce `first` parameter
- Empty nodes: Valid for new repos, proceed with empty issue list

### Step 3: Detect Issues with Linked PRs

Fetch all open PRs and their linked issues via `closingIssuesReferences`:

```bash
gh api graphql --paginate -f query='
query($endCursor: String) {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequests(states: OPEN, first: 100, after: $endCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        closingIssuesReferences(first: 10) {
          nodes { number }
        }
      }
    }
  }
}'
```

Also fetch recently merged PRs (to exclude already-fixed issues):

```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequests(states: MERGED, first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        closingIssuesReferences(first: 10) {
          nodes { number }
        }
      }
    }
  }
}'
```

Aggregate all PR-linked issue numbers into two categories:
- `issues_with_open_pr`: Issues with in-progress PRs
- `issues_with_merged_pr`: Issues fixed by merged PRs

**Validation**: Both queries should return valid arrays. If `closingIssuesReferences` is empty for all PRs, that's valid (PRs may not link issues).

### Step 4: Apply Filtering Rules

**Exclusion Conditions** (exclude if any match):

| Condition | Detection Method |
|-----------|------------------|
| Assigned and active | `assignees` non-empty AND `updatedAt` within last 30 days |
| Has in-progress PR | In `issues_with_open_pr` set |
| Fixed by merged PR | In `issues_with_merged_pr` set |
| Non-code contribution | See smart detection rules below |

**Special Inclusion** (include even if assigned):

| Condition | Description |
|-----------|-------------|
| Assigned but stale | `assignees` non-empty, but `updatedAt` >30 days ago AND not in `issues_with_open_pr` |

Mark these issues as `[Stale]` in output, suggesting users may politely ask if help is needed.

**Non-Code Contribution Detection** (smart detection, not just labels):

1. **Label signals** (strong): Contains `question`/`support`/`duplicate`/`wontfix`/`invalid`
2. **Title patterns** (medium):
   - Ends with `?`
   - Starts with "How to"/"How do I"/"Why does"/"What is"
   - Contains "[Question]"/"[Help]"/"[Support]" prefix
3. **Combined judgment**: If only title signals exist without label signals, use `gh issue view {number} --json body` to read first 500 chars of body for further judgment

**Conservative Principle**: When uncertain, keep the issue in the list for user judgment.

### Step 5: Group by Priority

Refer to `references/priority-labels.md` for priority definitions:

| Priority | Condition | Description |
|----------|-----------|-------------|
| P0 | Both `help-wanted` AND `good-first-issue` | Reserved for community newcomers |
| P1 | Has `good-first-issue` | Beginner-friendly task |
| P2 | Has `help-wanted` | Needs community help |
| P3 | Has `kind/bug` or `bug` | Clear problem description |
| P4 | Has `kind/documentation` / `kind/cleanup` / `documentation` | Small optimization tasks |
| P5 | Other | May need more context |

### Step 6: Generate Report Files

**Must generate two files** in current working directory:

#### 6.1 `issues-report.json` (Machine-readable)

Complete audit data for all issues. See `references/output-examples.md` for detailed schema and examples.

Key fields:
- `metadata`: Repository info, scan time, counts
- `issues[]`: Each issue with `included`, `priority`, `status`, and `include_reason`/`exclude_reason`

#### 6.2 `issues-report.md` (Human-readable)

Grouped by priority with Markdown tables. See `references/output-examples.md` for format template.

Key sections:
- Priority groups (P0-P5) with issue tables
- Summary statistics
- Exclusion reasons distribution

Skip empty priority groups.

## Hard Constraints

- Use `gh` CLI GraphQL API to ensure complete data retrieval
- Only analyze the GitHub project corresponding to the current git repository
- Read-only operations, do not modify any issue status
- PR linkage detection uses official `closingIssuesReferences` field, do not parse PR body
- **Must generate both `issues-report.json` and `issues-report.md` files**
- **Every issue must include `include_reason` or `exclude_reason` for auditability**

## Error Recovery

| Error | Recovery Action |
|-------|-----------------|
| `gh` not installed | Prompt user to install GitHub CLI |
| Not authenticated | Run `gh auth login` |
| Not a git repository | Prompt user to navigate to a git repo |
| No GitHub remote | Verify remote URL points to GitHub |
| Rate limited | Wait for reset or reduce batch size |
| Empty repository | Generate report with zero issues |
