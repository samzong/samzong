#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[gh-pr-review] $*" >&2
}

die() {
  log "ERROR: $*"
  exit 1
}

usage() {
  cat >&2 <<'EOF'
Usage:
  gh_pr_review.sh <PR_URL|PR_NUMBER> [--output-dir DIR] [--repo owner/repo] [--artifacts-dir DIR]

Behavior:
  - Requires `gh` (GitHub CLI). All GitHub interactions go through `gh`.
  - If input is a PR number, resolves repo from git remotes (prefer upstream, else origin),
    unless --repo is provided.
  - Writes artifacts to .gh-pr-review/pr-<n>/ by default (repo root if in a git repo).
  - Generates a starter review doc: review-<n>.md (Chinese doc, English copy-paste comments).
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

parse_repo_from_remote_url() {
  # Supports:
  # - git@github.com:owner/repo.git
  # - https://github.com/owner/repo.git
  # - https://github.com/owner/repo
  # - ssh://git@github.com/owner/repo.git
  local url="$1"

  url="${url%.git}"

  if [[ "$url" == git@github.com:* ]]; then
    echo "${url#git@github.com:}"
    return 0
  fi

  if [[ "$url" == https://github.com/* ]]; then
    echo "${url#https://github.com/}"
    return 0
  fi

  if [[ "$url" == http://github.com/* ]]; then
    echo "${url#http://github.com/}"
    return 0
  fi

  if [[ "$url" == ssh://git@github.com/* ]]; then
    echo "${url#ssh://git@github.com/}"
    return 0
  fi

  die "Unsupported remote URL format: $url"
}

resolve_repo_from_git() {
  git rev-parse --show-toplevel >/dev/null 2>&1 || die "Not a git repository; provide a full PR URL instead."

  local remote=""
  if git remote get-url upstream >/dev/null 2>&1; then
    remote="upstream"
  elif git remote get-url origin >/dev/null 2>&1; then
    remote="origin"
  else
    die "Could not find git remote 'upstream' or 'origin' to resolve repo. Provide --repo owner/repo."
  fi

  local remote_url
  remote_url="$(git remote get-url "$remote")"
  parse_repo_from_remote_url "$remote_url"
}

is_number() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

resolve_pr_and_repo() {
  local input="$1"
  local forced_repo="${2:-}"

  local pr=""
  local repo=""

  if [[ "$input" =~ ^https?://github\.com/[^/]+/[^/]+/pull/[0-9]+ ]]; then
    # shellcheck disable=SC2001
    pr="$(echo "$input" | sed -E 's#^https?://github\.com/[^/]+/[^/]+/pull/([0-9]+).*$#\1#')"
    # shellcheck disable=SC2001
    repo="$(echo "$input" | sed -E 's#^https?://github\.com/([^/]+/[^/]+)/pull/[0-9]+.*$#\1#')"
    echo "$pr $repo"
    return 0
  fi

  if is_number "$input"; then
    pr="$input"
    if [[ -n "$forced_repo" ]]; then
      repo="$forced_repo"
    else
      repo="$(resolve_repo_from_git)"
    fi
    echo "$pr $repo"
    return 0
  fi

  die "Unsupported input: '$input' (expected PR URL or PR number)"
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
    usage
    exit 2
  fi

  local input="$1"
  shift

  local output_dir="."
  local artifacts_dir=""
  local forced_repo=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --output-dir)
        output_dir="${2:-}"
        shift 2
        ;;
      --artifacts-dir)
        artifacts_dir="${2:-}"
        shift 2
        ;;
      --repo)
        forced_repo="${2:-}"
        shift 2
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done

  require_cmd gh
  require_cmd python3

  gh auth status -h github.com >/dev/null 2>&1 || die "gh is not authenticated or lacks access. Run 'gh auth login' and ensure repo access."

  local pr repo
  read -r pr repo < <(resolve_pr_and_repo "$input" "$forced_repo")

  log "Target PR: #$pr in $repo"

  if [[ -z "$artifacts_dir" ]]; then
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
      local root
      root="$(git rev-parse --show-toplevel)"
      artifacts_dir="$root/.gh-pr-review/pr-$pr"
    else
      artifacts_dir="$(pwd)/.gh-pr-review/pr-$pr"
    fi
  fi

  mkdir -p "$artifacts_dir"
  mkdir -p "$output_dir"

  local pr_json="$artifacts_dir/pr.json"
  local diff_patch="$artifacts_dir/diff.patch"
  local checks_txt="$artifacts_dir/checks.txt"
  local failed_logs="$artifacts_dir/failed-logs.txt"
  local changed_json="$artifacts_dir/changed-lines.json"

  log "Fetching PR metadata..."
  gh pr view "$pr" --repo "$repo" \
    --json number,title,url,author,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,createdAt,updatedAt,labels \
    > "$pr_json"

  local head_sha
  head_sha="$(gh pr view "$pr" --repo "$repo" --json headRefOid --jq '.headRefOid')"

  log "Fetching PR diff..."
  gh pr diff "$pr" --repo "$repo" > "$diff_patch"

  log "Parsing diff for changed line mapping..."
  python3 "$(dirname "$0")/parse_unified_diff.py" --input "$diff_patch" --output "$changed_json"

  log "Fetching checks summary..."
  if gh pr checks "$pr" --repo "$repo" > "$checks_txt" 2>&1; then
    true
  else
    log "gh pr checks failed; falling back to statusCheckRollup..."
    gh pr view "$pr" --repo "$repo" --json statusCheckRollup > "$checks_txt" 2>&1 || true
  fi

  log "Fetching failed workflow logs (best-effort)..."
  : > "$failed_logs"
  {
    echo "Head SHA: $head_sha"
    echo "Repo: $repo"
    echo "PR: #$pr"
    echo
  } >> "$failed_logs"

  local failed_ids=""
  if failed_ids="$(gh run list --repo "$repo" --commit "$head_sha" --json databaseId,conclusion,status,name,workflowName,event --jq '.[] | select(.conclusion=="failure") | .databaseId' 2>/dev/null || true)"; then
    true
  fi

  if [[ -z "${failed_ids//$'\n'/}" ]]; then
    echo "No failed workflow runs detected (or unable to query runs)." >> "$failed_logs"
  else
    while IFS= read -r run_id; do
      [[ -z "$run_id" ]] && continue
      {
        echo
        echo "=============================="
        echo "Failed run: $run_id"
        echo "=============================="
      } >> "$failed_logs"
      gh run view "$run_id" --repo "$repo" --log-failed >> "$failed_logs" 2>&1 || true
    done <<< "$failed_ids"
  fi

  local template_path
  template_path="$(cd "$(dirname "$0")/../assets" && pwd)/review-template.md"
  local out_md="$output_dir/review-$pr.md"

  log "Generating starter review doc: $out_md"
  python3 "$(dirname "$0")/generate_review_md.py" \
    --pr-json "$pr_json" \
    --checks "$checks_txt" \
    --failed-logs "$failed_logs" \
    --changed-lines "$changed_json" \
    --template "$template_path" \
    --output "$out_md"

  log "Done."
  log "Artifacts: $artifacts_dir"
  log "Review doc: $out_md"
}

main "$@"

