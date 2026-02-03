# GitHub Contributions by Year

Collect GitHub contributions by year: PRs, Issues, and Repositories.
Outputs activity log Markdown files organized by year and month.

## Prerequisites

- Python 3.6+
- GitHub CLI (`gh`) installed and authenticated
  ```bash
  gh auth login
  ```

## Usage

```bash
# Default: Current year only
python tools/github_contributions_by_year.py <username>

# Specific year
python tools/github_contributions_by_year.py <username> --year 2024

# Year range
python tools/github_contributions_by_year.py <username> --year 2021-2025

# All years from registration to now
python tools/github_contributions_by_year.py <username> --year all

# Custom output directory
python tools/github_contributions_by_year.py <username> --year all --output ./my-contributions
```

## Output

Generates one Markdown file per year in the output directory:

```
contributions/
├── 2021.md
├── 2022.md
├── 2023.md
├── 2024.md
└── 2025.md
```

Each file contains:

1. **Summary** - Total PRs, Issues, Repositories Created/Contributed
2. **Repositories Created** - New repos created in that year
3. **Repositories Contributed** - Repos with any PR/Issue activity
4. **Monthly Activity Log** - Detailed list of PRs and Issues by month

## Example Output

```markdown
# 2024 GitHub Contributions

> Generated for [samzong](https://github.com/samzong)

## Summary

- **PRs**: 313 (authored: 221, reviewed: 68, commented: 24)
- **Issues**: 61 (authored: 32, commented: 29)
- **Repositories Created**: 21
- **Repositories Contributed**: 55

## 2024-01

### PRs

- 🟣 [#3393](url) - DaoCloud/DaoCloud-docs - "PR Title" - merged (reviewed)
- 🟢 [#123](url) - org/repo - "PR Title" - open (authored)
- 🔴 [#456](url) - org/repo - "PR Title" - closed (authored)

### Issues

- 🟢 [#789](url) - org/repo - "Issue Title" - open (authored)
- 🔴 [#101](url) - org/repo - "Issue Title" - closed (commented)
```

## Notes

- Uses GitHub GraphQL API (5,000 points/hour limit)
- Requires authenticated `gh` CLI
- PR/Issue state icons: 🟣 merged, 🟢 open, 🔴 closed
