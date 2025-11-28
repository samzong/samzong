#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

import urllib.request
import urllib.error
import ssl
import time


API_ROOT = "https://api.github.com"

# Global configuration and stats
API_CONFIG = {"verbose": False}
API_STATS = {"count": 0}
USER_DETAILS_CACHE: Dict[str, Optional[str]] = {}


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(dt_obj: dt.datetime) -> str:
    return dt_obj.astimezone(dt.timezone.utc).isoformat()


def parse_ts(ts: Optional[str]) -> Optional[dt.datetime]:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def read_repo_from_git() -> Optional[Tuple[str, str]]:
    try:
        import subprocess

        url = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        if not url:
            return None
        m = re.search(r"github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
        if not m:
            return None
        return m.group("owner"), m.group("repo")
    except Exception:
        return None


def build_opener(token: Optional[str]) -> urllib.request.OpenerDirector:
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "repo-health-analyzer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    opener.addheaders = list(headers.items())
    return opener


def read_json(opener: urllib.request.OpenerDirector, url: str, timeout: int = 15, retries: int = 3) -> Optional[Dict]:
    API_STATS["count"] += 1
    if API_CONFIG["verbose"]:
        print(f"Fetching: {url}", file=sys.stderr)

    for i in range(retries):
        try:
            with opener.open(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403 or e.code == 429:
                print(f"Rate limit exceeded or unauthorized: {e}", file=sys.stderr)
            if i == retries - 1:
                return None
            time.sleep(1.5 * (i + 1))
        except (urllib.error.URLError, OSError):
            if i == retries - 1:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception:
            if i == retries - 1:
                return None
            time.sleep(1.5 * (i + 1))
    return None


def get_user_company(opener: urllib.request.OpenerDirector, login: str) -> Optional[str]:
    if login in USER_DETAILS_CACHE:
        return USER_DETAILS_CACHE[login]
    
    data = read_json(opener, f"{API_ROOT}/users/{login}")
    company = None
    if data and data.get("company"):
        company = data["company"].strip()
        if company.startswith("@"):
            company = company[1:].strip()
            
    USER_DETAILS_CACHE[login] = company
    return company


def paged_get(opener: urllib.request.OpenerDirector, url: str, per_page: int = 100) -> List[Dict]:
    items: List[Dict] = []
    page = 1
    while True:
        chunk = read_json(opener, f"{url}&per_page={per_page}&page={page}")
        if not isinstance(chunk, list) or not chunk:
            break
        items.extend(chunk)
        page += 1
        if page > 1000:
            break
    return items


def fetch_repo(opener: urllib.request.OpenerDirector, owner: str, repo: str) -> Dict:
    data = read_json(opener, f"{API_ROOT}/repos/{owner}/{repo}")
    return data or {}


def fetch_latest_release(opener: urllib.request.OpenerDirector, owner: str, repo: str) -> Optional[Dict]:
    return read_json(opener, f"{API_ROOT}/repos/{owner}/{repo}/releases/latest")


def is_bot_user(user: Optional[Dict]) -> bool:
    if not user:
        return False
    if user.get("type") == "Bot":
        return True
    l = (user.get("login") or "").lower()
    known_bots = {"dependabot", "renovate", "github-actions", "codecov", "vercel"}
    return any(b in l for b in known_bots) or l.endswith("-bot") or l.endswith("[bot]")


def fetch_commits(opener: urllib.request.OpenerDirector, owner: str, repo: str, since: Optional[str]) -> List[Dict]:
    url = f"{API_ROOT}/repos/{owner}/{repo}/commits?"
    if since:
        url += f"since={since}"
    return paged_get(opener, url)


def fetch_issues(opener: urllib.request.OpenerDirector, owner: str, repo: str, since: Optional[str]) -> List[Dict]:
    url = f"{API_ROOT}/repos/{owner}/{repo}/issues?state=all"
    if since:
        url += f"&since={since}"
    all_items = paged_get(opener, url)
    return [i for i in all_items if "pull_request" not in i]


def fetch_prs(opener: urllib.request.OpenerDirector, owner: str, repo: str, since_dt: Optional[dt.datetime]) -> List[Dict]:
    def collect(state: str) -> List[Dict]:
        items: List[Dict] = []
        page = 1
        while True:
            url = f"{API_ROOT}/repos/{owner}/{repo}/pulls?state={state}&sort=updated&direction=desc&per_page=100&page={page}"
            chunk = read_json(opener, url)
            if not isinstance(chunk, list) or not chunk:
                break
            # early stop when updated_at older than window
            stop = False
            for p in chunk:
                try:
                    u = (p.get("updated_at") or "").replace("Z", "+00:00")
                    u_dt = dt.datetime.fromisoformat(u)
                except Exception:
                    u_dt = None
                if since_dt and u_dt and u_dt < since_dt:
                    stop = True
                    break
                items.append(p)
            if stop:
                break
            page += 1
            if page > 100:
                break
        return items

    return collect("open") + collect("closed")


def tally_commits(commits: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for c in commits:
        user = c.get("author") or c.get("committer")
        if is_bot_user(user):
            continue
        login = (user.get("login") if user else None) or "unknown"
        counts[login] = counts.get(login, 0) + 1
    return counts


def tally_items(items: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for i in items:
        user = i.get("user")
        if is_bot_user(user):
            continue
        login = (user.get("login") if user else None) or "unknown"
        counts[login] = counts.get(login, 0) + 1
    return counts


def tally_active(commit_counts: Dict[str, int], issues: List[Dict], prs: List[Dict], since_dt: dt.datetime, limit: int = 10) -> List[Dict]:
    issue_counts: Dict[str, int] = {}
    pr_counts: Dict[str, int] = {}
    for i in issues:
        user = i.get("user")
        if is_bot_user(user):
            continue
        login = (user.get("login") if user else None) or "unknown"
        issue_counts[login] = issue_counts.get(login, 0) + 1
    for p in prs:
        user = p.get("user")
        if is_bot_user(user):
            continue
        u_dt = parse_ts(p.get("updated_at"))
        if u_dt and u_dt < since_dt:
            continue
        login = (user.get("login") if user else None) or "unknown"
        pr_counts[login] = pr_counts.get(login, 0) + 1
    logins = set(commit_counts.keys()) | set(issue_counts.keys()) | set(pr_counts.keys())
    rows: List[Dict] = []
    for login in logins:
        c = commit_counts.get(login, 0)
        pi = pr_counts.get(login, 0)
        ii = issue_counts.get(login, 0)
        score = c * 3 + pi * 2 + ii
        rows.append({
            "login": login,
            "commits": c,
            "opened_prs": pi,
            "opened_issues": ii,
            "score": score,
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:limit]


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def health_summary(
    commit_counts: Dict[str, int],
    issues: List[Dict],
    prs: List[Dict],
    since_days: int,
) -> Dict:
    # unify bot filtering for numerators and denominators
    filtered_issues = [i for i in issues if not is_bot_user(i.get("user"))]
    filtered_prs = [p for p in prs if not is_bot_user(p.get("user"))]

    total_commits = sum(commit_counts.values())
    total_issues = len(filtered_issues)
    total_prs = len(filtered_prs)
    
    # Calculate active participants (union of committers, issue openers, pr openers)
    issue_logins = {i.get("user", {}).get("login") for i in filtered_issues if i.get("user")}
    pr_logins = {p.get("user", {}).get("login") for p in filtered_prs if p.get("user")}
    commit_logins = {login for login, count in commit_counts.items() if count > 0}
    
    all_active_logins = issue_logins | pr_logins | commit_logins
    active_contributors = len(all_active_logins)

    top_share = 0.0
    if total_commits > 0 and commit_counts:
        top_share = round(max(commit_counts.values()) / total_commits, 4)

    closed_issues = sum(1 for i in filtered_issues if i.get("state") == "closed")
    merged_prs = sum(1 for p in filtered_prs if p.get("merged_at"))
    closed_prs = sum(1 for p in filtered_prs if p.get("state") == "closed")

    return {
        "window_days": since_days,
        "totals": {
            "commits": total_commits,
            "issues": total_issues,
            "prs": total_prs,
        },
        "contributors": {
            "active_count": active_contributors,
            "top_commit_share": top_share,
            "by_login": commit_counts,
        },
        "quality": {
            "issue_close_rate": ratio(closed_issues, total_issues),
            "pr_merge_rate": ratio(merged_prs, total_prs),
            "pr_close_rate": ratio(closed_prs, total_prs),
        },
    }


def print_report(owner: str, repo: str, summary: Dict) -> None:
    totals = summary["totals"]
    contributors = summary["contributors"]
    quality = summary["quality"]
    lines = []
    lines.append(
        f"Contributors: active={contributors['active_count']} top_commit_share={contributors['top_commit_share']}"
    )
    lines.append(
        f"Quality: issue_close_rate={quality['issue_close_rate']} pr_merge_rate={quality['pr_merge_rate']} pr_close_rate={quality['pr_close_rate']}"
    )
    # health hint
    health = "healthy"
    if contributors["active_count"] == 0 or contributors["top_commit_share"] > 0.7:
        health = "at_risk"
    lines.append(f"Health: {health}")
    print("\n".join(lines))


def week_start(dt_obj: dt.datetime) -> dt.datetime:
    d = dt_obj.astimezone(dt.timezone.utc)
    # Monday as start of week
    start = d - dt.timedelta(days=d.weekday())
    return dt.datetime(start.year, start.month, start.day, tzinfo=dt.timezone.utc)


def make_weeks(since_dt: dt.datetime, until_dt: dt.datetime) -> List[dt.datetime]:
    weeks = []
    cur = week_start(since_dt)
    end = week_start(until_dt)
    while cur <= end:
        weeks.append(cur)
        cur = cur + dt.timedelta(days=7)
    return weeks


def bucket_increment(buckets: Dict[dt.datetime, int], when: Optional[dt.datetime]) -> None:
    if not when:
        return
    wk = week_start(when)
    buckets[wk] = buckets.get(wk, 0) + 1


def parse_dt(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:
        return None


def plot_lines(weeks: List[dt.datetime], series: Dict[str, List[int]], title: str, ylabel: str, outfile: str) -> None:
    import matplotlib.pyplot as plt
    x = [w.date().isoformat() for w in weeks]
    plt.figure(figsize=(12, 6))
    for name, values in series.items():
        plt.plot(x, values, label=name)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Week")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()


def plot_issue_trends(weeks: List[dt.datetime], issues: List[Dict], owner: str, repo: str) -> str:
    filtered_issues = [i for i in issues if not is_bot_user(i.get("user"))]
    iss_created: Dict[dt.datetime, int] = {}
    iss_closed: Dict[dt.datetime, int] = {}
    for i in filtered_issues:
        bucket_increment(iss_created, parse_dt(i.get("created_at")))
        bucket_increment(iss_closed, parse_dt(i.get("closed_at")))
    created_vals = [iss_created.get(w, 0) for w in weeks]
    closed_vals = [iss_closed.get(w, 0) for w in weeks]
    issues_png = os.path.join(".", "issues_trend.png")
    plot_lines(weeks, {"issues_created": created_vals, "issues_closed": closed_vals},
               f"Issues Weekly Trend ({owner}/{repo})", "count", issues_png)
    return issues_png


def plot_pr_trends(weeks: List[dt.datetime], prs: List[Dict], owner: str, repo: str) -> str:
    filtered_prs = [p for p in prs if not is_bot_user(p.get("user"))]
    prs_created: Dict[dt.datetime, int] = {}
    prs_merged: Dict[dt.datetime, int] = {}
    for p in filtered_prs:
        bucket_increment(prs_created, parse_dt(p.get("created_at")))
        bucket_increment(prs_merged, parse_dt(p.get("merged_at")))
    prc_vals = [prs_created.get(w, 0) for w in weeks]
    prm_vals = [prs_merged.get(w, 0) for w in weeks]
    prs_png = os.path.join(".", "prs_trend.png")

    import matplotlib.pyplot as plt
    x = [w.date().isoformat() for w in weeks]
    plt.figure(figsize=(12, 6))
    ax1 = plt.gca()
    ax1.plot(x, prc_vals, label="prs_created", color="tab:blue")
    ax1.plot(x, prm_vals, label="prs_merged", color="tab:green")
    ax1.set_ylabel("count")
    plt.xticks(rotation=45, ha="right")

    # average close days
    close_sum: Dict[dt.datetime, float] = {}
    close_cnt: Dict[dt.datetime, int] = {}
    for p in filtered_prs:
        ca = parse_dt(p.get("created_at"))
        cl = parse_dt(p.get("closed_at"))
        if not ca or not cl:
            continue
        wk = week_start(cl)
        delta = (cl - ca).total_seconds() / 86400.0
        close_sum[wk] = close_sum.get(wk, 0.0) + delta
        close_cnt[wk] = close_cnt.get(wk, 0) + 1
    avg_close = [(close_sum.get(w, 0.0) / close_cnt.get(w, 1)) if close_cnt.get(w, 0) > 0 else 0.0 for w in weeks]

    ax2 = ax1.twinx()
    ax2.plot(x, avg_close, color="tab:red", label="avg_close_days")
    ax2.set_ylabel("avg_close_days")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    plt.title(f"PRs Weekly Trend ({owner}/{repo})")
    plt.legend(lines1 + lines2, labels1 + labels2)
    plt.tight_layout()
    plt.savefig(prs_png)
    plt.close()
    return prs_png


def plot_top_devs_trends(weeks: List[dt.datetime], commits: List[Dict], issues: List[Dict], prs: List[Dict], summary: Dict, owner: str, repo: str, opener: urllib.request.OpenerDirector) -> str:
    top_logins = [row["login"] for row in summary.get("active_devs_top", [])]

    # commits per login
    commits_by_week_login: Dict[str, Dict[dt.datetime, int]] = {ln: {} for ln in top_logins}
    for c in commits:
        user = c.get("author") or c.get("committer")
        login = (user.get("login") if user else None) or "unknown"
        if login not in commits_by_week_login:
            continue
        when = parse_dt((c.get("commit") or {}).get("author", {}).get("date")) or parse_dt((c.get("commit") or {}).get("committer", {}).get("date"))
        if not when:
            continue
        wk = week_start(when)
        d = commits_by_week_login[login]
        d[wk] = d.get(wk, 0) + 1

    # opened issues per login
    filtered_issues = [i for i in issues if not is_bot_user(i.get("user"))]
    issues_by_week_login: Dict[str, Dict[dt.datetime, int]] = {ln: {} for ln in top_logins}
    for i in filtered_issues:
        login = (i.get("user") or {}).get("login") or "unknown"
        if login not in issues_by_week_login:
            continue
        when = parse_dt(i.get("created_at"))
        wk = week_start(when) if when else None
        if not wk:
            continue
        d = issues_by_week_login[login]
        d[wk] = d.get(wk, 0) + 1

    # opened prs per login
    filtered_prs = [p for p in prs if not is_bot_user(p.get("user"))]
    prs_by_week_login: Dict[str, Dict[dt.datetime, int]] = {ln: {} for ln in top_logins}
    for p in filtered_prs:
        login = (p.get("user") or {}).get("login") or "unknown"
        if login not in prs_by_week_login:
            continue
        when = parse_dt(p.get("created_at"))
        wk = week_start(when) if when else None
        if not wk:
            continue
        d = prs_by_week_login[login]
        d[wk] = d.get(wk, 0) + 1

    # build series
    series: Dict[str, List[int]] = {}
    for ln in top_logins:
        vals: List[int] = []
        for w in weeks:
            c = commits_by_week_login.get(ln, {}).get(w, 0)
            pi = prs_by_week_login.get(ln, {}).get(w, 0)
            ii = issues_by_week_login.get(ln, {}).get(w, 0)
            vals.append(c * 3 + pi * 2 + ii)
        
        # Add company to label
        company = get_user_company(opener, ln)
        label = f"{ln} ({company})" if company else ln
        series[label] = vals

    top_png = os.path.join(".", "top_devs_weekly.png")
    plot_lines(weeks, series, f"Top Devs Weekly Score ({owner}/{repo})", "score", top_png)
    return top_png


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repo health over a time window",
        epilog=(
            "Environment variables:\n"
            "  GITHUB_TOKEN  Personal Access Token for GitHub API to increase rate limits"
        ),
    )
    parser.add_argument("--repo", help="owner/repo")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--top", type=int, default=10, help="number of top developers to show")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--plot", action="store_true", help="generate PNG charts into current directory")
    parser.add_argument("--verbose", action="store_true", help="print detailed logs during execution")
    args = parser.parse_args()

    API_CONFIG["verbose"] = args.verbose

    # Immediate dependency check for plotting
    if args.plot:
        try:
            import matplotlib  # noqa: F401
        except Exception:
            print("matplotlib not found; please install via 'pip install matplotlib' to enable plotting", file=sys.stderr)
            return 2
    else:
        # Non-blocking tip if matplotlib missing
        try:
            import matplotlib  # noqa: F401
        except Exception:
            print("Tip: install matplotlib via 'pip install matplotlib' to enable --plot charts", file=sys.stderr)

    owner_repo = None
    if args.repo:
        m = re.match(r"^([^/]+)/([^/]+)$", args.repo)
        if not m:
            print("Invalid --repo", file=sys.stderr)
            return 2
        owner_repo = (m.group(1), m.group(2))
    else:
        owner_repo = read_repo_from_git()

    if not owner_repo:
        print("Cannot determine repository", file=sys.stderr)
        return 2

    owner, repo = owner_repo
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set. Rate limits will be low (60 req/hr).", file=sys.stderr)
        print("         Set GITHUB_TOKEN environment variable to avoid 403/429 errors.", file=sys.stderr)

    opener = build_opener(token)

    since_dt = now_utc() - dt.timedelta(days=args.days)
    since = iso(since_dt)

    if not args.json:
        print(f"Repository: {owner}/{repo}")
        print(f"Windows: {args.days}d")

    repo_info = fetch_repo(opener, owner, repo)
    latest = fetch_latest_release(opener, owner, repo)
    
    commits = fetch_commits(opener, owner, repo, since)
    if not args.json:
        print(f"Totals: commits={len(commits)} ...", end="\r", flush=True)
        
    issues = fetch_issues(opener, owner, repo, since)
    if not args.json:
        print(f"Totals: commits={len(commits)} issues={len([i for i in issues if not is_bot_user(i.get('user'))])} ...", end="\r", flush=True)

    prs = fetch_prs(opener, owner, repo, since_dt)
    if not args.json:
        print(f"Totals: commits={len(commits)} issues={len([i for i in issues if not is_bot_user(i.get('user'))])} prs={len([p for p in prs if not is_bot_user(p.get('user'))])}", flush=True)

    commit_counts = tally_commits(commits)
    summary = health_summary(commit_counts, issues, prs, args.days)

    # repo hints
    summary["repo_archived"] = bool(repo_info.get("archived"))
    pushed = parse_ts(repo_info.get("pushed_at"))
    summary["days_since_last_commit"] = (now_utc() - pushed).days if pushed else None
    if latest:
        ltp = parse_ts(latest.get("published_at") or latest.get("created_at"))
        summary["latest_release_days_ago"] = (now_utc() - ltp).days if ltp else None
    else:
        summary["latest_release_days_ago"] = None
    summary["active_devs_top"] = tally_active(commit_counts, issues, prs, since_dt, limit=args.top)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_report(owner, repo, summary)
        if summary.get("active_devs_top"):
            print("Active developers (Top):")
            for row in summary["active_devs_top"]:
                company = get_user_company(opener, row['login'])
                company_str = f" ({company})" if company else ""
                print(f"  {row['login']}{company_str}: commits={row['commits']} prs={row['opened_prs']} issues={row['opened_issues']} score={row['score']}")
    
    print(f"Total GitHub API calls: {API_STATS['count']}", file=sys.stderr)

    # plotting
    if args.plot:
        until_dt = now_utc()
        weeks = make_weeks(since_dt, until_dt)
        
        issues_png = plot_issue_trends(weeks, issues, owner, repo)
        prs_png = plot_pr_trends(weeks, prs, owner, repo)
        top_png = plot_top_devs_trends(weeks, commits, issues, prs, summary, owner, repo, opener)
        
        print(f"Built charts: {issues_png}, {prs_png}, {top_png}")
    else:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
