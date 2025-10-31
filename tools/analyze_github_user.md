# GitHub User Activity Analyzer

Analyze GitHub user activity: PRs, Issues, and monthly distribution across all repositories.

## Prerequisites

- Python 3.6+
- GitHub CLI (`gh`) installed and authenticated
  ```bash
  gh auth login
  ```

## Usage

```bash
python tools/analyze_github_user.py <github_username>
```

**Example:**

```bash
python tools/analyze_github_user.py cr7258
```

## Output

Generates two files:

- `{username}_repo_month.csv` - Long format CSV (Repository, Month, PRs Authored, PRs Commented, PRs Reviewed, PRs Total, Issues Authored, Issues Commented, Issues Total, Total Activity)
- `{username}_tables.md` - Markdown report with user info, statistics, trends, and repository summary

## Notes

- Requires authenticated `gh` CLI
- Uses GitHub GraphQL API (5,000 points/hour limit)
- CSV uses long format for easy data analysis and multi-user merging
