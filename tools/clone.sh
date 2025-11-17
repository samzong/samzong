#!/usr/bin/env bash
set -euo pipefail

# Require at least one user argument
if [ $# -eq 0 ]; then
  echo "Usage: $0 <user1> [user2] ..." >&2
  exit 1
fi

USERS=("$@")

for u in "${USERS[@]}"; do
  mkdir -p "$u"
  cd "$u" || exit 1

  gh repo list "$u" --limit 1000 --json nameWithOwner \
    | jq -r '.[] | .nameWithOwner' \
    | while read -r repo; do
        reponame="${repo#*/}"
        if [ -d "$reponame" ]; then
          cd "$reponame" || exit 1
          gh repo sync >/dev/null 2>&1 && echo "$repo Updated" || echo "$repo Update failed"
          cd ..
        else
          echo "★ New repo $repo"
          gh repo clone "$repo" >/dev/null 2>&1 && echo "$repo Cloned" || echo "$repo Clone failed"
        fi
      done

  cd ..
done
