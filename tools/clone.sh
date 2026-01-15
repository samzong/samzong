#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <user1> [user2] ..." >&2
  exit 1
fi

readonly BASE_DIR="$(pwd)"
readonly PARALLEL_JOBS="${CLONE_PARALLEL:-4}"

sync_repo() {
  local repo="$1" target_dir="$2"
  local reponame="${repo#*/}"
  local repo_path="$target_dir/$reponame"

  if [[ -d "$repo_path/.git" ]]; then
    git -C "$repo_path" pull --ff-only --quiet 2>/dev/null \
      && echo "✓ $repo" \
      || echo "✗ $repo (pull failed)"
  else
    rm -rf "$repo_path" 2>/dev/null || true
    gh repo clone "$repo" "$repo_path" >/dev/null 2>&1 \
      && echo "★ $repo" \
      || echo "✗ $repo (clone failed)"
  fi
}
export -f sync_repo

for user in "$@"; do
  target_dir="$BASE_DIR/$user"
  mkdir -p "$target_dir"
  export target_dir

  echo "=== $user ==="
  gh repo list "$user" --limit 1000 -q '.[].nameWithOwner' --json nameWithOwner \
    | xargs -P "$PARALLEL_JOBS" -I {} bash -c 'sync_repo "$1" "$target_dir"' _ {}
done
