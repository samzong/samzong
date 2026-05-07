#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


GRAPHQL_URL = "https://api.github.com/graphql"
SCHEMA_VERSION = 1
PAGE_SIZE = 100


def normalize_repo(value: str) -> str:
    value = value.strip().removesuffix(".git")
    match = re.search(r"(?:github\.com[:/])?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)$", value)
    if not match:
        raise SystemExit(f"Invalid repo: {value}")
    return match.group(1)


def gh_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        raise SystemExit("GITHUB_TOKEN is not set and `gh auth token` failed") from exc
    token = result.stdout.strip()
    if not token:
        raise SystemExit("GitHub token is empty")
    return token


def graphql(token: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "samzong-github-repo-pr-rank",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub GraphQL HTTP {exc.code}: {detail}") from exc
    if payload.get("errors"):
        raise SystemExit(json.dumps(payload["errors"], ensure_ascii=False, indent=2))
    return payload["data"]


def default_cache_dir() -> Path:
    return Path(__file__).resolve().parent / ".cache" / "github_repo_pr_rank"


def cache_path(cache_dir: Path, repo: str, state: str) -> Path:
    return cache_dir / f"{repo.replace('/', '__')}-{state}.json"


def load_cache(path: Path, repo: str, state: str) -> Dict[str, Any]:
    if not path.exists():
        return empty_cache(repo, state)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_cache(repo, state)
    if (
        data.get("schema_version") != SCHEMA_VERSION
        or data.get("repo") != repo
        or data.get("state") != state
        or not isinstance(data.get("pull_requests"), dict)
    ):
        return empty_cache(repo, state)
    return data


def empty_cache(repo: str, state: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "repo": repo,
        "state": state,
        "complete": False,
        "fetched_at": None,
        "api_calls": 0,
        "pull_requests": {},
    }


def save_cache(path: Path, cache: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def state_arg(state: str) -> str:
    if state == "merged":
        return "states: MERGED,"
    if state == "open":
        return "states: OPEN,"
    if state == "closed":
        return "states: CLOSED,"
    return ""


def pr_query(state: str) -> str:
    return f"""
query RepoPullRequestRank($owner: String!, $name: String!, $after: String) {{
  repository(owner: $owner, name: $name) {{
    pullRequests({state_arg(state)} first: {PAGE_SIZE}, after: $after, orderBy: {{ field: UPDATED_AT, direction: DESC }}) {{
      totalCount
      pageInfo {{
        hasNextPage
        endCursor
      }}
      nodes {{
        number
        title
        state
        mergedAt
        updatedAt
        url
        author {{
          __typename
          login
          url
          ... on User {{
            id
            databaseId
          }}
          ... on Bot {{
            id
          }}
          ... on Organization {{
            id
            databaseId
          }}
        }}
      }}
    }}
  }}
}}
"""


def normalize_pr(node: Dict[str, Any]) -> Dict[str, Any]:
    author = node.get("author") or {}
    return {
        "number": node.get("number"),
        "title": node.get("title") or "",
        "state": node.get("state") or "",
        "merged_at": node.get("mergedAt"),
        "updated_at": node.get("updatedAt"),
        "url": node.get("url") or "",
        "author": {
            "type": author.get("__typename") or "Unknown",
            "login": author.get("login") or "ghost",
            "id": author.get("id"),
            "database_id": author.get("databaseId"),
            "url": author.get("url"),
        },
    }


def fetch_rank_data(
    repo: str,
    state: str,
    cache: Dict[str, Any],
    force: bool,
    max_pages: Optional[int],
) -> Dict[str, Any]:
    owner, name = repo.split("/", 1)
    token = gh_token()
    cached_prs = cache.get("pull_requests", {})
    next_prs = {} if force else dict(cached_prs)
    seen_cached_boundary = False
    after = None
    api_calls = 0
    pages = 0
    total_count = cache.get("total_count")

    while True:
        pages += 1
        data = graphql(token, pr_query(state), {"owner": owner, "name": name, "after": after})
        api_calls += 1
        prs = data["repository"]["pullRequests"]
        total_count = prs["totalCount"]
        nodes = prs["nodes"] or []
        for node in nodes:
            pr = normalize_pr(node)
            key = str(pr["number"])
            old = cached_prs.get(key)
            if (
                not force
                and cache.get("complete") is True
                and old
                and old.get("updated_at") == pr["updated_at"]
            ):
                seen_cached_boundary = True
            next_prs[key] = pr

        page_info = prs["pageInfo"]
        if max_pages and pages >= max_pages:
            complete = False
            break
        if not page_info.get("hasNextPage"):
            complete = True
            break
        if seen_cached_boundary:
            complete = cache.get("complete") is True
            break
        after = page_info.get("endCursor")
        if not after:
            complete = False
            break

    cache.update(
        {
            "schema_version": SCHEMA_VERSION,
            "repo": repo,
            "state": state,
            "complete": complete,
            "total_count": total_count,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "api_calls": int(cache.get("api_calls") or 0) + api_calls,
            "last_run_api_calls": api_calls,
            "pull_requests": next_prs,
        }
    )
    return cache


def rank(cache: Dict[str, Any], include_bots: bool) -> List[Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for pr in cache.get("pull_requests", {}).values():
        author = pr.get("author") or {}
        login = author.get("login") or "ghost"
        actor_type = author.get("type") or "Unknown"
        if not include_bots and actor_type == "Bot":
            continue
        row = rows.setdefault(
            login,
            {
                "login": login,
                "github_id": author.get("database_id"),
                "node_id": author.get("id"),
                "type": actor_type,
                "url": author.get("url"),
                "prs": 0,
                "merged_prs": 0,
                "open_prs": 0,
                "closed_prs": 0,
            },
        )
        row["prs"] += 1
        state = pr.get("state")
        if state == "MERGED":
            row["merged_prs"] += 1
        elif state == "OPEN":
            row["open_prs"] += 1
        elif state == "CLOSED":
            row["closed_prs"] += 1
    ranked = sorted(rows.values(), key=lambda item: (-item["prs"], item["login"].lower()))
    total = sum(item["prs"] for item in ranked)
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
        item["share_percent"] = round(item["prs"] / total * 100, 4) if total else 0.0
    return ranked


def print_table(rows: List[Dict[str, Any]], total_prs: int, limit: int) -> None:
    print(f"{'#':>4}  {'login':<24} {'github_id':>10} {'type':<12} {'prs':>6} {'share':>8}")
    print("-" * 72)
    for row in rows[:limit]:
        github_id = row["github_id"] if row["github_id"] is not None else "-"
        print(
            f"{row['rank']:>4}  {row['login']:<24.24} {str(github_id):>10} "
            f"{row['type']:<12.12} {row['prs']:>6} {row['share_percent']:>7.3f}%"
        )
    print("-" * 72)
    print(f"Ranked PRs: {total_prs}")


def csv_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fields = ["rank", "login", "github_id", "node_id", "type", "url", "prs", "merged_prs", "open_prs", "closed_prs", "share_percent"]
    return [{field: row.get(field) for field in fields} for row in rows]


def write_csv(rows: List[Dict[str, Any]], output: Optional[str]) -> None:
    fields = ["rank", "login", "github_id", "node_id", "type", "url", "prs", "merged_prs", "open_prs", "closed_prs", "share_percent"]
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(csv_rows(rows))
        print(f"Wrote {len(rows)} rows to {path}")
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    writer.writerows(csv_rows(rows))


def filter_user(rows: List[Dict[str, Any]], user: Optional[str]) -> List[Dict[str, Any]]:
    if not user:
        return rows
    wanted = user.lower()
    return [row for row in rows if row["login"].lower() == wanted]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank all GitHub PR authors for a repository with an incremental local cache",
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--state",
        choices=["merged", "all", "open", "closed"],
        default="merged",
        help="PR state to rank; default: merged",
    )
    parser.add_argument("--limit", type=int, default=50, help="rows to print; default: 50")
    parser.add_argument("--cache-dir", default=str(default_cache_dir()))
    parser.add_argument("--force", action="store_true", help="ignore cache and refetch all pages")
    parser.add_argument("--include-bots", action="store_true", help="include Bot actors in ranking")
    parser.add_argument("--user", help="show only one GitHub login")
    parser.add_argument("--csv", action="store_true", help="print ranking as CSV")
    parser.add_argument("--output", help="write --csv output to this file")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument(
        "--max-pages",
        type=int,
        help="debug/smoke option: fetch at most N pages, cache remains marked incomplete",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = normalize_repo(args.repo)
    cache_file = cache_path(Path(args.cache_dir).expanduser(), repo, args.state)
    cache = load_cache(cache_file, repo, args.state)
    cache = fetch_rank_data(repo, args.state, cache, args.force, args.max_pages)
    save_cache(cache_file, cache)
    rows = rank(cache, include_bots=args.include_bots)
    output_rows = filter_user(rows, args.user)
    if args.user and not output_rows:
        raise SystemExit(f"User not found in cached {args.state} PR authors: {args.user}")
    total_ranked_prs = sum(row["prs"] for row in rows)

    if args.csv:
        write_csv(output_rows, args.output)
        return 0

    if args.json:
        print(
            json.dumps(
                {
                    "repo": repo,
                    "state": args.state,
                    "cache_file": str(cache_file),
                    "complete": cache.get("complete") is True,
                    "total_count": cache.get("total_count"),
                    "cached_prs": len(cache.get("pull_requests", {})),
                    "last_run_api_calls": cache.get("last_run_api_calls"),
                    "ranking": output_rows,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"Repository: {repo}")
    print(f"State: {args.state}")
    print(f"Cache: {cache_file}")
    print(
        f"Cache status: {'complete' if cache.get('complete') else 'incomplete'}; "
        f"cached PRs={len(cache.get('pull_requests', {}))}; "
        f"last run API calls={cache.get('last_run_api_calls')}"
    )
    print()
    print_table(output_rows, total_ranked_prs, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
