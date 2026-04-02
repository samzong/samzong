#!/usr/bin/env bash
set -euo pipefail

REPO_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: fetch-issues.sh [--repo owner/repo]"
      echo ""
      echo "Fetch open issues and PR linkage data from GitHub."
      echo "Outputs combined JSON to stdout."
      echo ""
      echo "Options:"
      echo "  --repo owner/repo   Target a specific repository"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI required. Install from https://cli.github.com" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "Error: gh not authenticated. Run: gh auth login" >&2
  exit 1
fi

if [[ -n "$REPO_OVERRIDE" ]]; then
  REPO_FULL="$REPO_OVERRIDE"
else
  REPO_FULL=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
    echo "Error: not in a GitHub repository or no GitHub remote configured" >&2
    exit 1
  }
fi

OWNER="${REPO_FULL%%/*}"
REPO="${REPO_FULL##*/}"
echo "Fetching data for $REPO_FULL ..." >&2

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

gh api graphql --paginate \
  -f owner="$OWNER" -f repo="$REPO" \
  -f query='
query($owner: String!, $repo: String!, $endCursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(states: OPEN, first: 100, after: $endCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url createdAt updatedAt
        labels(first: 20) { nodes { name } }
        assignees(first: 10) { nodes { login } }
      }
    }
  }
}' > "$TMPDIR/issues.json" 2>/dev/null

gh api graphql --paginate \
  -f owner="$OWNER" -f repo="$REPO" \
  -f query='
query($owner: String!, $repo: String!, $endCursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(states: OPEN, first: 100, after: $endCursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        closingIssuesReferences(first: 10) { nodes { number } }
      }
    }
  }
}' > "$TMPDIR/open_prs.json" 2>/dev/null

gh api graphql \
  -f owner="$OWNER" -f repo="$REPO" \
  -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(states: MERGED, first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        closingIssuesReferences(first: 10) { nodes { number } }
      }
    }
  }
}' > "$TMPDIR/merged_prs.json" 2>/dev/null

python3 - "$TMPDIR" "$REPO_FULL" << 'PYEOF'
import json, sys, os
from datetime import datetime, timezone

tmpdir, repo = sys.argv[1], sys.argv[2]

def load(name, *keys):
    with open(os.path.join(tmpdir, name)) as f:
        d = json.load(f)
    for k in keys:
        d = d.get(k, {})
    return d if isinstance(d, list) else []

issues = load("issues.json", "data", "repository", "issues", "nodes")
open_prs = load("open_prs.json", "data", "repository", "pullRequests", "nodes")
merged_prs = load("merged_prs.json", "data", "repository", "pullRequests", "nodes")

def collect_linked_issues(pr_nodes):
    result = set()
    for pr in pr_nodes:
        for ref in pr.get("closingIssuesReferences", {}).get("nodes", []):
            result.add(ref["number"])
    return result

with_open_pr = collect_linked_issues(open_prs)
with_merged_pr = collect_linked_issues(merged_prs)

print(json.dumps({
    "repository": repo,
    "scan_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "total_open_issues": len(issues),
    "issues": [{
        "number": i["number"],
        "title": i["title"],
        "url": i["url"],
        "created_at": i["createdAt"][:10],
        "updated_at": i["updatedAt"][:10],
        "labels": [l["name"] for l in i.get("labels", {}).get("nodes", [])],
        "assignees": [a["login"] for a in i.get("assignees", {}).get("nodes", [])],
        "has_open_pr": i["number"] in with_open_pr,
        "has_merged_pr": i["number"] in with_merged_pr
    } for i in issues]
}, indent=2))
PYEOF
