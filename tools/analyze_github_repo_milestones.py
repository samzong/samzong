#!/usr/bin/env python3
import datetime as dt
import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

import logging


 

HEADERS = [
    "Accept: application/vnd.github+json",
    "X-GitHub-Api-Version: 2022-11-28",
]

MAX_WORKERS = int(os.getenv("GH_MAX_WORKERS", "16"))


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_ts(ts: Optional[str]) -> Optional[dt.datetime]:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:
        return None


def run_cmd(args: List[str], env: Optional[Dict[str, str]] = None, timeout: int = 20) -> Tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True, env=env, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def ensure_env_and_gh() -> Tuple[str, Dict[str, str]]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN is not set.", file=sys.stderr)
        return "", {}
    code, _, err = run_cmd(["gh", "--version"])
    if code != 0:
        print("Error: gh CLI is not available.", file=sys.stderr)
        if err:
            print(err.strip(), file=sys.stderr)
        return "", {}
    env = dict(os.environ)
    env["GITHUB_TOKEN"] = token
    return token, env


def gh_api(path: str, env: Dict[str, str], params: Optional[Dict[str, Any]] = None, paginate: bool = False, per_page: int = 100, max_pages: int = 50, retries: int = 2) -> Any:
    base = ["gh", "api"]
    for h in HEADERS:
        base.extend(["-H", h])
    def run_once(extra: List[str]) -> Tuple[int, str, str]:
        args = base + extra
        return run_cmd(args, env=env)
    if paginate:
        items: List[Any] = []
        page = 1
        while page <= max_pages:
            qp: Dict[str, Any] = dict(params or {})
            qp["per_page"] = per_page
            qp["page"] = page
            query = "?" + "&".join(f"{k}={v}" for k, v in qp.items()) if qp else ""
            extra = [path + query]
            logging.info("gh api GET %s page=%d", path, page)
            ok = False
            for r in range(retries + 1):
                code, out, err = run_once(extra)
                if code == 0:
                    ok = True
                    break
                logging.warning("gh api failed: %s", err.strip())
            if not ok:
                return None
            try:
                chunk = json.loads(out)
            except Exception:
                return None
            if not isinstance(chunk, list) or not chunk:
                logging.info("gh api GET %s done at page=%d", path, page)
                break
            items.extend(chunk)
            page += 1
        logging.info("gh api GET %s total_items=%d", path, len(items))
        return items
    else:
        query = "?" + "&".join(f"{k}={v}" for k, v in (params or {}).items()) if params else ""
        extra = [path + query]
        logging.info("gh api GET %s", path)
        ok = False
        out: str = ""
        err: str = ""
        for r in range(retries + 1):
            code, out, err = run_once(extra)
            if code == 0:
                ok = True
                break
            logging.warning("gh api failed: %s", err.strip())
        if not ok:
            return None
        try:
            return json.loads(out)
        except Exception:
            return None


def gh_api_search_issues(env: Dict[str, str], q: str, per_page: int = 100, max_pages: int = 50) -> Dict[str, Any]:
    base = ["gh", "api", "search/issues"]
    for h in HEADERS:
        base.extend(["-H", h])
    items: List[Dict[str, Any]] = []
    total_count: Optional[int] = None
    page = 1
    while page <= max_pages:
        logging.info("gh api SEARCH q=%s page=%d", q, page)
        args = base + ["-F", f"q={q}", "-F", f"per_page={per_page}", "-F", f"page={page}"]
        code, out, err = run_cmd(args, env=env)
        if code != 0:
            logging.warning("gh api search failed: %s", err.strip())
            break
        try:
            data = json.loads(out)
        except Exception:
            break
        if total_count is None and isinstance(data, dict) and "total_count" in data:
            try:
                total_count = int(data.get("total_count") or 0)
            except Exception:
                total_count = 0
        chunk = data.get("items") if isinstance(data, dict) else None
        if not isinstance(chunk, list) or not chunk:
            logging.info("gh api SEARCH q=%s done at page=%d", q, page)
            break
        items.extend(chunk)
        page += 1
    logging.info("gh api SEARCH q=%s total_items=%d total_count=%s", q, len(items), str(total_count))
    return {"items": items, "total_count": total_count if total_count is not None else len(items)}


def find_milestone(env: Dict[str, str], owner: str, repo: str, title: str) -> Optional[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/milestones"
    logging.info("Fetching milestones for %s/%s", owner, repo)
    items = gh_api(path, env, params={"state": "all"}, paginate=True)
    if not isinstance(items, list):
        return None
    for m in items:
        if (m.get("title") or "") == title:
            logging.info("Found milestone %s (#%s)", title, str(m.get("number")))
            return m
    logging.info("Milestone %s not found; will fallback to search", title)
    return None


def build_stats(m: Dict[str, Any]) -> Dict[str, Any]:
    open_issues = int(m.get("open_issues") or 0)
    closed_issues = int(m.get("closed_issues") or 0)
    total = open_issues + closed_issues
    completion = round((closed_issues / total) * 100.0, 2) if total > 0 else 0.0
    due_on = parse_ts(m.get("due_on"))
    days_remaining: Optional[int] = None
    if due_on:
        delta = (due_on - now_utc()).days
        days_remaining = delta
    return {
        "title": m.get("title"),
        "number": m.get("number"),
        "total": total,
        "open": open_issues,
        "closed": closed_issues,
        "completion_pct": completion,
        "due_on": due_on.isoformat() if due_on else None,
        "days_remaining": days_remaining,
    }


def list_issues(env: Dict[str, str], owner: str, repo: str, milestone_number: Optional[int], milestone_title: Optional[str], state: str, assignee: Optional[str], per_page: int = 100) -> List[Dict[str, Any]]:
    if milestone_number is not None:
        path = f"repos/{owner}/{repo}/issues"
        params: Dict[str, Any] = {"milestone": milestone_number, "state": state}
        if assignee is not None:
            params["assignee"] = assignee
        items = gh_api(path, env, params=params, paginate=True, per_page=per_page)
        logging.info("List issues via milestone number=%s state=%s assignee=%s count=%d", str(milestone_number), state, str(assignee), len(items) if isinstance(items, list) else 0)
        return [i for i in items if isinstance(items, list) and "pull_request" not in i] if isinstance(items, list) else []
    else:
        q = f"repo:{owner}/{repo} is:issue is:{state} milestone:\"{milestone_title}\""
        if assignee == "none":
            q += " no:assignee"
        elif assignee == "*":
            q += " assignee:*"
        data = gh_api_search_issues(env, q, per_page=per_page)
        items = data.get("items", [])
        logging.info("List issues via search state=%s assignee=%s count=%d", state, str(assignee), len(items))
        return [i for i in items if "pull_request" not in i]


def analyze_unassigned(env: Dict[str, str], owner: str, repo: str, milestone_number: Optional[int], milestone_title: Optional[str]) -> Dict[str, Any]:
    logging.info("Analyzing unassigned open issues")
    iss = list_issues(env, owner, repo, milestone_number, milestone_title, state="open", assignee="none")
    with_discussion = sum(1 for i in iss if int(i.get("comments") or 0) > 0)
    without_discussion = sum(1 for i in iss if int(i.get("comments") or 0) == 0)
    return {"total_unassigned": len(iss), "with_discussion": with_discussion, "without_discussion": without_discussion, "items": iss}


def issue_timeline(env: Dict[str, str], owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/issues/{issue_number}/timeline"
    items = gh_api(path, env, params={}, paginate=True)
    if isinstance(items, list):
        return items
    return []


def extract_linked_pr_numbers(events: List[Dict[str, Any]]) -> List[int]:
    prs: List[int] = []
    for e in events:
        ev = e.get("event")
        src = e.get("source") or {}
        issue_obj = src.get("issue") or {}
        if ev in ("connected", "cross-referenced") and isinstance(issue_obj, dict):
            if issue_obj.get("pull_request"):
                num = issue_obj.get("number")
                if isinstance(num, int):
                    prs.append(num)
    return list(sorted(set(prs)))


def assignee_str(issue: Dict[str, Any]) -> str:
    a = issue.get("assignees")
    if isinstance(a, list) and a:
        names = []
        for u in a:
            login = (u or {}).get("login")
            if login:
                names.append(f"@{login}")
        if names:
            return ", ".join(names)
    single = issue.get("assignee")
    if isinstance(single, dict) and single.get("login"):
        return f"@{single.get('login')}"
    return "none"


def issue_creator_mention(issue: Dict[str, Any]) -> Optional[str]:
    user = issue.get("user") or {}
    login = user.get("login")
    return f"@{login}" if login else None


def get_pr(env: Dict[str, str], owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/pulls/{pr_number}"
    data = gh_api(path, env)
    if isinstance(data, dict):
        return data
    return None


def get_pr_reviews(env: Dict[str, str], owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    items = gh_api(path, env, paginate=True)
    if isinstance(items, list):
        return items
    return []


def get_issue_comments(env: Dict[str, str], owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/issues/{pr_number}/comments"
    items = gh_api(path, env, paginate=True)
    if isinstance(items, list):
        return items
    return []


def get_pr_review_comments(env: Dict[str, str], owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    path = f"repos/{owner}/{repo}/pulls/{pr_number}/comments"
    items = gh_api(path, env, paginate=True)
    if isinstance(items, list):
        return items
    return []


def detect_stalled(env: Dict[str, str], owner: str, repo: str, milestone_number: Optional[int], milestone_title: Optional[str]) -> Dict[str, Any]:
    logging.info("Detecting stalled progress for assigned open issues")
    assigned = list_issues(env, owner, repo, milestone_number, milestone_title, state="open", assignee="*")
    warn: List[Dict[str, Any]] = []
    reassign: List[Dict[str, Any]] = []
    if not assigned:
        logging.info("No assigned open issues")
        return {"warning_7d": warn, "reassign_15d": reassign}
    issue_numbers = [int(i.get("number")) for i in assigned if i.get("number")]
    logging.info("Fetching timelines concurrently for %d issues", len(issue_numbers))
    from concurrent.futures import ThreadPoolExecutor, as_completed
    timelines: Dict[int, List[Dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(issue_timeline, env, owner, repo, n): n for n in issue_numbers}
        for fut in as_completed(futs):
            n = futs[fut]
            try:
                timelines[n] = fut.result()
            except Exception:
                timelines[n] = []
    all_pr_numbers: List[int] = []
    for i in assigned:
        n = int(i.get("number"))
        events = timelines.get(n, [])
        all_pr_numbers.extend(extract_linked_pr_numbers(events))
    unique_prs = sorted(set(all_pr_numbers))
    pr_map: Dict[int, Dict[str, Any]] = {}
    if unique_prs:
        logging.info("Fetching PR details concurrently for %d PRs", len(unique_prs))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(get_pr, env, owner, repo, pn): pn for pn in unique_prs}
            for fut in as_completed(futs):
                pn = futs[fut]
                try:
                    pr = fut.result()
                except Exception:
                    pr = None
                if pr:
                    pr_map[pn] = pr
    skipped_with_active_pr = 0
    treated_as_no_pr = 0
    for i in assigned:
        n = int(i.get("number"))
        events = timelines.get(n, [])
        pr_numbers = extract_linked_pr_numbers(events)
        if pr_numbers:
            has_active = False
            for pn in pr_numbers:
                pr = pr_map.get(pn)
                st = (pr or {}).get("state")
                merged = (pr or {}).get("merged_at")
                if (st or "").lower() == "open" or merged:
                    has_active = True
                    break
            if has_active:
                skipped_with_active_pr += 1
                continue
            else:
                treated_as_no_pr += 1
        last_activity: Optional[dt.datetime] = parse_ts(i.get("updated_at"))
        if not last_activity:
            continue
        days = (now_utc() - last_activity).days
        row = {"issue": i, "days_since_activity": days, "linked_prs": pr_numbers}
        if days >= 15:
            reassign.append(row)
        elif days >= 7:
            warn.append(row)
    logging.info("Stalled detection done: warning=%d reassign=%d skipped_with_active_pr=%d treated_as_no_pr=%d", len(warn), len(reassign), skipped_with_active_pr, treated_as_no_pr)
    return {"warning_7d": warn, "reassign_15d": reassign}


def evaluate_pr_status(env: Dict[str, str], owner: str, repo: str, milestone_number: Optional[int], milestone_title: Optional[str]) -> Dict[str, Any]:
    logging.info("Evaluating PR review status for issues linked to milestone")
    issues = list_issues(env, owner, repo, milestone_number, milestone_title, state="open", assignee=None)
    pr_set: Dict[int, Dict[str, Any]] = {}
    if not issues:
        logging.info("No issues for PR status evaluation")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    numbers = [int(i.get("number")) for i in issues if i.get("number")]
    timelines: Dict[int, List[Dict[str, Any]]] = {}
    if numbers:
        logging.info("Fetching timelines concurrently for %d issues", len(numbers))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(issue_timeline, env, owner, repo, n): n for n in numbers}
            for fut in as_completed(futs):
                n = futs[fut]
                try:
                    timelines[n] = fut.result()
                except Exception:
                    timelines[n] = []
    pr_numbers: List[int] = []
    for i in issues:
        n = int(i.get("number"))
        events = timelines.get(n, [])
        pr_numbers.extend(extract_linked_pr_numbers(events))
    unique_prs = sorted(set(pr_numbers))
    if unique_prs:
        logging.info("Fetching PR details concurrently for %d PRs", len(unique_prs))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(get_pr, env, owner, repo, pn): pn for pn in unique_prs}
            for fut in as_completed(futs):
                pn = futs[fut]
                try:
                    pr = fut.result()
                except Exception:
                    pr = None
                if pr:
                    pr_set[pn] = pr
    draft_3d: List[Dict[str, Any]] = []
    awaiting_3d: List[Dict[str, Any]] = []
    changes_req: List[Dict[str, Any]] = []
    review_cache: Dict[int, List[Dict[str, Any]]] = {}
    if pr_set:
        logging.info("Fetching PR reviews concurrently for %d PRs", len(pr_set))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = {ex.submit(get_pr_reviews, env, owner, repo, pn): pn for pn in pr_set.keys()}
            for fut in as_completed(futs):
                pn = futs[fut]
                try:
                    review_cache[pn] = fut.result()
                except Exception:
                    review_cache[pn] = []
    issue_comment_cache: Dict[int, List[Dict[str, Any]]] = {}
    pr_comment_cache: Dict[int, List[Dict[str, Any]]] = {}
    if pr_set:
        logging.info("Fetching PR comments concurrently for %d PRs", len(pr_set))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs_issue = {ex.submit(get_issue_comments, env, owner, repo, pn): pn for pn in pr_set.keys()}
            futs_pr = {ex.submit(get_pr_review_comments, env, owner, repo, pn): pn for pn in pr_set.keys()}
            for fut in as_completed(futs_issue):
                pn = futs_issue[fut]
                try:
                    issue_comment_cache[pn] = fut.result()
                except Exception:
                    issue_comment_cache[pn] = []
            for fut in as_completed(futs_pr):
                pn = futs_pr[fut]
                try:
                    pr_comment_cache[pn] = fut.result()
                except Exception:
                    pr_comment_cache[pn] = []
    for pn, pr in pr_set.items():
        st = (pr.get("state") or "").lower()
        if st != "open":
            continue
        created = parse_ts(pr.get("created_at"))
        is_draft = bool(pr.get("draft"))
        age_days = (now_utc() - created).days if created else None
        if is_draft and age_days is not None and age_days >= 3:
            draft_3d.append(pr)
        reviews = review_cache.get(pn, [])
        latest_state: Optional[str] = None
        latest_review_dt: Optional[dt.datetime] = None
        if reviews:
            r = max(reviews, key=lambda x: parse_ts(x.get("submitted_at")) or parse_ts(x.get("created_at")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
            latest_state = r.get("state")
            latest_review_dt = parse_ts(r.get("submitted_at")) or parse_ts(r.get("created_at"))
        issue_comments = issue_comment_cache.get(pn, [])
        pr_comments = pr_comment_cache.get(pn, [])
        latest_comment_dt: Optional[dt.datetime] = None
        if issue_comments:
            c = max(issue_comments, key=lambda x: parse_ts(x.get("updated_at")) or parse_ts(x.get("created_at")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
            latest_comment_dt = parse_ts(c.get("updated_at")) or parse_ts(c.get("created_at"))
        if pr_comments:
            c2 = max(pr_comments, key=lambda x: parse_ts(x.get("updated_at")) or parse_ts(x.get("created_at")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
            dt2 = parse_ts(c2.get("updated_at")) or parse_ts(c2.get("created_at"))
            if dt2 and (latest_comment_dt is None or dt2 > latest_comment_dt):
                latest_comment_dt = dt2
        if latest_state == "CHANGES_REQUESTED":
            changes_req.append(pr)
        else:
            # Strict rule: Only include OPEN PRs with no reviews and no comments in last 3 days
            if (pr.get("state") or "").lower() == "open" and not is_draft:
                three_days_ago = now_utc() - dt.timedelta(days=3)
                has_recent_review = False
                if reviews:
                    # any review within 3 days
                    for rv in reviews:
                        rv_dt = parse_ts(rv.get("submitted_at")) or parse_ts(rv.get("created_at"))
                        if rv_dt and rv_dt >= three_days_ago:
                            has_recent_review = True
                            break
                has_recent_comment = False
                if issue_comments:
                    for cm in issue_comments:
                        cm_dt = parse_ts(cm.get("updated_at")) or parse_ts(cm.get("created_at"))
                        if cm_dt and cm_dt >= three_days_ago:
                            has_recent_comment = True
                            break
                if not has_recent_comment and pr_comments:
                    for cm in pr_comments:
                        cm_dt = parse_ts(cm.get("updated_at")) or parse_ts(cm.get("created_at"))
                        if cm_dt and cm_dt >= three_days_ago:
                            has_recent_comment = True
                            break
                if (not has_recent_review) and (not has_recent_comment):
                    awaiting_3d.append(pr)
    logging.info("PR status: draft_3d=%d awaiting_3d=%d changes_requested=%d", len(draft_3d), len(awaiting_3d), len(changes_req))
    return {"draft_3d": draft_3d, "awaiting_review_3d": awaiting_3d, "changes_requested": changes_req}


def make_md_link_issue(owner: str, repo: str, issue: Dict[str, Any]) -> str:
    num = int(issue.get("number"))
    url = f"https://github.com/{owner}/{repo}/issues/{num}"
    title = (issue.get("title") or "").strip()
    return f"[#{num}]({url}) — {title}"


def make_md_link_pr(owner: str, repo: str, pr: Dict[str, Any]) -> str:
    num = int(pr.get("number"))
    url = f"https://github.com/{owner}/{repo}/pull/{num}"
    title = (pr.get("title") or "").strip()
    return f"[#{num}]({url}) — {title}"


def build_markdown(owner: str, repo: str, stats: Dict[str, Any], unassigned: Dict[str, Any], stalled: Dict[str, Any], pr_status: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# Milestone {stats.get('title')} — Progress Report ({owner}/{repo})")
    lines.append("## Milestone Statistics")
    lines.append(f"- Total: {stats.get('total')}")
    lines.append(f"- Open: {stats.get('open')}")
    lines.append(f"- Closed: {stats.get('closed')}")
    lines.append(f"- Completion: {stats.get('completion_pct')}%")
    lines.append(f"- Deadline: {stats.get('due_on') or 'N/A'}")
    lines.append(f"- Days Remaining: {stats.get('days_remaining') if stats.get('days_remaining') is not None else 'N/A'}")
    lines.append("## Unassigned Tasks Analysis")
    lines.append(f"- Unassigned Open Issues: {unassigned.get('total_unassigned')}")
    lines.append(f"- With Discussion Comments: {unassigned.get('with_discussion')}")
    lines.append(f"- 🔥🔥🔥 **Without Discussion: {unassigned.get('without_discussion')} (needs clarification)**")
    if unassigned.get("items"):
        lines.append("- Examples:")
        for i in unassigned["items"][:10]:
            ass = assignee_str(i)
            base = f"  - {make_md_link_issue(owner, repo, i)} — assignee: {ass}"
            try:
                comments = int(i.get("comments") or 0)
            except Exception:
                comments = 0
            if ass == "none" and comments == 0:
                creator = issue_creator_mention(i)
                if creator:
                    base += f" — creator: {creator}"
            lines.append(base)
    lines.append("## Stalled Progress Detection")
    lines.append(f"- Warning (≥7 days inactivity): {len(stalled.get('warning_7d') or [])}")
    lines.append(f"- 🔥🔥🔥 **Suggest Reassignment (≥15 days inactivity): {len(stalled.get('reassign_15d') or [])}**")
    if stalled.get("warning_7d"):
        lines.append("- Warning Items:")
        for row in stalled["warning_7d"][:10]:
            lines.append(f"  - {make_md_link_issue(owner, repo, row['issue'])} — assignee: {assignee_str(row['issue'])} — {row['days_since_activity']} days")
    if stalled.get("reassign_15d"):
        lines.append("- Reassignment Candidates:")
        for row in stalled["reassign_15d"][:10]:
            lines.append(f"  - {make_md_link_issue(owner, repo, row['issue'])} — assignee: {assignee_str(row['issue'])} — {row['days_since_activity']} days")
    lines.append("## PR Review Status")
    lines.append(f"- Draft ≥3 days: {len(pr_status.get('draft_3d') or [])}")
    lines.append(f"- 🔥🔥🔥 **Awaiting review ≥3 days: {len(pr_status.get('awaiting_review_3d') or [])}**")
    lines.append(f"- Changes requested: {len(pr_status.get('changes_requested') or [])}")
    if pr_status.get("draft_3d"):
        lines.append("- Drafts:")
        for pr in pr_status["draft_3d"][:10]:
            lines.append(f"  - {make_md_link_pr(owner, repo, pr)}")
    if pr_status.get("awaiting_review_3d"):
        lines.append("- Awaiting Review:")
        for pr in pr_status["awaiting_review_3d"][:10]:
            lines.append(f"  - {make_md_link_pr(owner, repo, pr)}")
    if pr_status.get("changes_requested"):
        lines.append("- Changes Requested:")
        for pr in pr_status["changes_requested"][:10]:
            lines.append(f"  - {make_md_link_pr(owner, repo, pr)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate milestone progress report via GitHub CLI")
    parser.add_argument("--repo", required=True, help="owner/repo, e.g., vllm-project/semantic-router")
    parser.add_argument("--milestone", required=True, help="milestone title")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    token, env = ensure_env_and_gh()
    if not token:
        return 2

    if not args.repo or "/" not in args.repo:
        print("Error: --repo must be in 'owner/repo' format", file=sys.stderr)
        return 2
    owner, repo = args.repo.split("/", 1)
    milestone_title = args.milestone

    logging.info("Starting report for %s/%s milestone=%s", owner, repo, milestone_title)
    m = find_milestone(env, owner, repo, milestone_title)
    if m:
        stats = build_stats(m)
        milestone_number: Optional[int] = int(stats["number"]) if stats.get("number") is not None else None
        milestone_title: Optional[str] = stats.get("title")
    else:
        logging.info("Using search API to compute milestone stats")
        q_open = f"repo:{owner}/{repo} is:issue is:open milestone:\"{milestone_title}\""
        q_closed = f"repo:{owner}/{repo} is:issue is:closed milestone:\"{milestone_title}\""
        open_data = gh_api_search_issues(env, q_open)
        closed_data = gh_api_search_issues(env, q_closed)
        open_count = int(open_data.get("total_count") or 0)
        closed_count = int(closed_data.get("total_count") or 0)
        total = open_count + closed_count
        completion = round((closed_count / total) * 100.0, 2) if total > 0 else 0.0
        stats = {
            "title": milestone_title,
            "number": None,
            "total": total,
            "open": open_count,
            "closed": closed_count,
            "completion_pct": completion,
            "due_on": None,
            "days_remaining": None,
        }
        milestone_number = None
        milestone_title = milestone_title
    logging.info("Stats: total=%d open=%d closed=%d completion=%.2f%%", stats["total"], stats["open"], stats["closed"], stats["completion_pct"])
    unassigned = analyze_unassigned(env, owner, repo, milestone_number, milestone_title)
    stalled = detect_stalled(env, owner, repo, milestone_number, milestone_title)
    pr_status = evaluate_pr_status(env, owner, repo, milestone_number, milestone_title)
    logging.info("Building Markdown report")
    md = build_markdown(owner, repo, stats, unassigned, stalled, pr_status)
    print(md)
    outfile = os.path.join(".", f"{owner}_{repo}_milestone_{milestone_title}.md")
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(md)
        logging.info("Saved report to %s", outfile)
    except Exception as e:
        logging.warning("Failed to save report: %s", str(e))
    logging.info("Report generation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
