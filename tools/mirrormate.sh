#!/usr/bin/env bash

set -e
set -u
set -o pipefail

cleanup() {
  if [[ -n "${current_tmp:-}" && -e "$current_tmp" ]]; then
    rm -f "$current_tmp"
  fi
}
trap cleanup EXIT ERR INT

# Prefix mapping rules (key-value list for older bash)
prefix_mappings=(
  "docker.io|m.daocloud.io/docker.io"
  "gcr.io|m.daocloud.io/gcr.io"
  "ghcr.io|m.daocloud.io/ghcr.io"
  "registry.k8s.io|m.daocloud.io/registry.k8s.io"
  "nvcr.io|m.daocloud.io/nvcr.io"
  "quay.io|m.daocloud.io/quay.io"
)

# Image regex: supports port, multi-path, tag or digest
image_regex='[a-zA-Z0-9.-]+(:[0-9]+)?(/[a-zA-Z0-9._-]+)+(@sha256:[0-9a-fA-F]{64}|:[a-zA-Z0-9._-]+)?'

print_usage() {
  cat <<'USAGE'
Usage: mirrormate.sh [OPTIONS] [DIRECTORY]

Options:
  -y, --yes       Auto-apply all changes
  -n, --dry-run   Preview diff only; no write, no backup
  -q, --quiet     Quiet mode; minimal output
  -h, --help      Show help

Environment variables:
  NO_COLOR=1      Disable colored diff output

Notes:
  - Interactive by default: show diff per file, then ask to apply
  - Backups in /tmp as mirrormate.<path with slashes -> underscores>.bak
  - Directory defaults to current '.'

Examples:
  mirrormate.sh ./deploy
  mirrormate.sh -n ./deploy
  mirrormate.sh -y -q ./deploy
USAGE
}

rewrite_line() {
  local line="$1"
  local remaining="$line"
  local rebuilt=""

  while [[ $remaining =~ $image_regex ]]; do
    local match="${BASH_REMATCH[0]}"
    local before="${remaining%%"$match"*}"
    rebuilt+="$before"
    remaining="${remaining#*"$match"}"

    local replacement="$match"
    local mapping old_prefix new_prefix
    for mapping in "${prefix_mappings[@]}"; do
      old_prefix="${mapping%%|*}"
      new_prefix="${mapping#*|}"
      if [[ $match == "$old_prefix"* ]]; then
        replacement="${new_prefix}${match#$old_prefix}"
        break
      fi
    done

    rebuilt+="$replacement"
  done

  printf '%s' "$rebuilt$remaining"
}

auto_apply=false
preview_only=false
quiet=false
show_help=false
current_tmp=""
directory="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      auto_apply=true
      shift
      ;;
    -n|--dry-run)
      preview_only=true
      shift
      ;;
    -q|--quiet)
      quiet=true
      shift
      ;;
    -h|--help)
      show_help=true
      shift
      ;;
    *)
      directory="$1"
      shift
      ;;
  esac
done

if [[ "$show_help" == true ]]; then
  print_usage
  exit 0
fi

# Find all yaml/yml files and process; keep original backup and write only when changed
while IFS= read -r -d '' file; do
  dir_name="$(dirname "$file")"
  base_name="$(basename "$file")"
  tmp_file="$(mktemp "$dir_name/$base_name.tmp.XXXXXX")"
  current_tmp="$tmp_file"

  # Process line by line; support multiple images per line
  while IFS= read -r line || [[ -n $line ]]; do
    rewrite_line "$line" >> "$tmp_file"
    printf '\n' >> "$tmp_file"
  done < "$file"

  if cmp -s "$tmp_file" "$file"; then
    rm -f "$tmp_file"
    current_tmp=""
    continue
  fi

  if [[ "$quiet" != true ]]; then
    echo "==> File: $file"
    if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
      diff -U 0 "$file" "$tmp_file" | awk '
        BEGIN { red="\033[31m"; green="\033[32m"; reset="\033[0m"; }
        /^---/ || /^\+\+\+/ || /^@@/ { next }
        /^-/ && !/^---/ { print red $0 reset; next }
        /^\+/ && !/^\+\+\+/ { print green $0 reset; next }
        { next }
      ' || true
    else
      diff -U 0 "$file" "$tmp_file" | awk '
        /^---/ || /^\+\+\+/ || /^@@/ { next }
        (/^-/ && !/^---/) || (/^\+/ && !/^\+\+\+/) { print; next }
        { next }
      ' || true
    fi
  fi
  if [[ "$preview_only" == true ]]; then
    rm -f "$tmp_file"
    current_tmp=""
    if [[ "$quiet" != true ]]; then
      echo "Dry run: no changes applied"
    fi
  elif [[ "$auto_apply" == true ]]; then
    backup_file="/tmp/mirrormate.${file//\//_}.bak"
    if [[ ! -e "$backup_file" ]]; then
      cp "$file" "$backup_file"
    fi
    mv "$tmp_file" "$file"
    current_tmp=""
  else
    echo -n "Apply changes? [y/N] "
    response=""
    if ! read -r response </dev/tty; then
      response=""
    fi
    case "$response" in
      y|Y)
        backup_file="/tmp/mirrormate.${file//\//_}.bak"
        if [[ ! -e "$backup_file" ]]; then
          cp "$file" "$backup_file"
        fi
        mv "$tmp_file" "$file"
        current_tmp=""
        ;;
      *)
        rm -f "$tmp_file"
        current_tmp=""
        if [[ "$quiet" != true ]]; then
          echo "Skipped"
        fi
        ;;
    esac
  fi
done < <(find "$directory" -type f \( -iname "*.yaml" -o -iname "*.yml" \) -print0)
