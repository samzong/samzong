#!/usr/bin/env python3
"""
Collect GitHub contributions by year: PRs, Issues, Commits, and Repositories.
Outputs activity log Markdown files organized by year and month.
"""

import json
import argparse
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = int(os.getenv("GH_MAX_WORKERS", "8"))


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated"""
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: gh CLI is not installed.", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True, check=True)
        if 'Logged in' in result.stdout or 'Logged in' in result.stderr:
            return True
    except subprocess.CalledProcessError:
        pass
    
    print("Error: gh CLI is not authenticated. Run 'gh auth login' first.", file=sys.stderr)
    sys.exit(1)


def run_gh_api(query: str, is_graphql: bool = False) -> dict:
    """Execute gh CLI command and return JSON result"""
    try:
        if is_graphql:
            cmd = ['gh', 'api', 'graphql', '-f', f'query={query}']
        else:
            cmd = ['gh', 'api', query]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        if 'rate limit' in (e.stderr or '').lower():
            print(f"Error: GitHub API rate limit exceeded.", file=sys.stderr)
        return {}
    except json.JSONDecodeError:
        return {}


def graphql_search_all(query: str) -> List[dict]:
    """Execute GraphQL search with pagination"""
    results: List[dict] = []
    cursor = None
    while True:
        if cursor:
            modified_query = query.replace('first: 100', f'first: 100, after: "{cursor}"')
        else:
            modified_query = query
        data = run_gh_api(modified_query, is_graphql=True)
        if not data or 'data' not in data:
            break
        search_data = data['data'].get('search', {})
        nodes = search_data.get('nodes', [])
        results.extend(nodes)
        page_info = search_data.get('pageInfo', {})
        if not page_info.get('hasNextPage', False):
            break
        cursor = page_info.get('endCursor')
    return results


def get_user_info(username: str) -> Dict:
    """Get user information including registration date"""
    data = run_gh_api(f'users/{username}')
    return {
        'login': data.get('login', username),
        'name': data.get('name', ''),
        'created_at': data.get('created_at', ''),
        'public_repos': data.get('public_repos', 0),
    }


def get_user_repos_created_in_year(username: str, year: int) -> List[dict]:
    """Get repositories created by user in a specific year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    query = f'''
    {{
      search(query: "user:{username} created:{start_date}..{end_date}", type: REPOSITORY, first: 100) {{
        repositoryCount
        nodes {{
          ... on Repository {{
            nameWithOwner
            name
            description
            createdAt
            url
            isPrivate
            stargazerCount
          }}
        }}
        pageInfo {{
          hasNextPage
          endCursor
        }}
      }}
    }}
    '''
    
    results = []
    cursor = None
    while True:
        if cursor:
            modified_query = query.replace('first: 100', f'first: 100, after: "{cursor}"')
        else:
            modified_query = query
        data = run_gh_api(modified_query, is_graphql=True)
        if not data or 'data' not in data:
            break
        search_data = data['data'].get('search', {})
        nodes = search_data.get('nodes', [])
        results.extend(nodes)
        page_info = search_data.get('pageInfo', {})
        if not page_info.get('hasNextPage', False):
            break
        cursor = page_info.get('endCursor')
    
    return results


def get_prs_in_year(username: str, year: int) -> List[dict]:
    """Get all PRs where user is author/reviewer/commenter in a specific year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    all_prs = []
    
    queries = [
        ('authored', f'author:{username} type:pr created:{start_date}..{end_date}'),
        ('reviewed', f'reviewed-by:{username} type:pr created:{start_date}..{end_date}'),
        ('commented', f'commenter:{username} type:pr created:{start_date}..{end_date}'),
    ]
    
    def fetch_prs(search_query: str, activity_type: str) -> List[dict]:
        query = f'''
        {{
          search(query: "{search_query}", type: ISSUE, first: 100) {{
            issueCount
            nodes {{
              ... on PullRequest {{
                number
                title
                state
                createdAt
                mergedAt
                url
                repository {{
                  nameWithOwner
                }}
                author {{
                  login
                }}
              }}
            }}
            pageInfo {{
              hasNextPage
              endCursor
            }}
          }}
        }}
        '''
        nodes = graphql_search_all(query)
        for pr in nodes:
            pr['activity_type'] = activity_type
        return nodes
    
    with ThreadPoolExecutor(max_workers=min(len(queries), MAX_WORKERS)) as ex:
        futs = {ex.submit(fetch_prs, q, t): t for t, q in queries}
        for fut in as_completed(futs):
            try:
                all_prs.extend(fut.result())
            except Exception:
                pass
    
    return all_prs


def get_issues_in_year(username: str, year: int) -> List[dict]:
    """Get all Issues where user is author/commenter in a specific year"""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    all_issues = []
    
    queries = [
        ('authored', f'author:{username} type:issue created:{start_date}..{end_date}'),
        ('commented', f'commenter:{username} type:issue created:{start_date}..{end_date}'),
    ]
    
    def fetch_issues(search_query: str, activity_type: str) -> List[dict]:
        query = f'''
        {{
          search(query: "{search_query}", type: ISSUE, first: 100) {{
            issueCount
            nodes {{
              ... on Issue {{
                number
                title
                state
                createdAt
                closedAt
                url
                repository {{
                  nameWithOwner
                }}
                author {{
                  login
                }}
              }}
            }}
            pageInfo {{
              hasNextPage
              endCursor
            }}
          }}
        }}
        '''
        nodes = graphql_search_all(query)
        for issue in nodes:
            issue['activity_type'] = activity_type
        return nodes
    
    with ThreadPoolExecutor(max_workers=min(len(queries), MAX_WORKERS)) as ex:
        futs = {ex.submit(fetch_issues, q, t): t for t, q in queries}
        for fut in as_completed(futs):
            try:
                all_issues.extend(fut.result())
            except Exception:
                pass
    
    return all_issues


def dedupe_items(items: List[dict], key_func) -> List[dict]:
    """Deduplicate items by a key function"""
    seen = set()
    result = []
    for item in items:
        key = key_func(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def group_by_month(items: List[dict], date_field: str = 'createdAt') -> Dict[str, List[dict]]:
    """Group items by month (YYYY-MM)"""
    grouped = defaultdict(list)
    for item in items:
        date_str = item.get(date_field, '')
        if date_str:
            month = date_str[:7]  # YYYY-MM
            grouped[month].append(item)
    return dict(grouped)


def generate_year_markdown(
    username: str,
    year: int,
    repos_created: List[dict],
    prs: List[dict],
    issues: List[dict],
) -> str:
    """Generate Markdown content for a year"""
    lines = []
    
    # Header
    lines.append(f"# {year} GitHub Contributions\n")
    lines.append(f"> Generated for [{username}](https://github.com/{username})\n")
    
    # Deduplicate
    prs = dedupe_items(prs, lambda x: (x.get('repository', {}).get('nameWithOwner'), x.get('number')))
    issues = dedupe_items(issues, lambda x: (x.get('repository', {}).get('nameWithOwner'), x.get('number')))
    
    # Count by type
    prs_authored = [p for p in prs if p.get('activity_type') == 'authored']
    prs_reviewed = [p for p in prs if p.get('activity_type') == 'reviewed']
    prs_commented = [p for p in prs if p.get('activity_type') == 'commented']
    issues_authored = [i for i in issues if i.get('activity_type') == 'authored']
    issues_commented = [i for i in issues if i.get('activity_type') == 'commented']
    
    # Contributed repos (unique repos from PRs and Issues)
    contributed_repos: Dict[str, Dict[str, int]] = defaultdict(lambda: {'prs': 0, 'issues': 0})
    for pr in prs:
        repo = pr.get('repository', {}).get('nameWithOwner', '')
        if repo:
            contributed_repos[repo]['prs'] += 1
    for issue in issues:
        repo = issue.get('repository', {}).get('nameWithOwner', '')
        if repo:
            contributed_repos[repo]['issues'] += 1
    
    # Summary
    lines.append("\n## Summary\n")
    lines.append(f"- **PRs**: {len(prs)} (authored: {len(prs_authored)}, reviewed: {len(prs_reviewed)}, commented: {len(prs_commented)})")
    lines.append(f"- **Issues**: {len(issues)} (authored: {len(issues_authored)}, commented: {len(issues_commented)})")
    lines.append(f"- **Repositories Created**: {len(repos_created)}")
    lines.append(f"- **Repositories Contributed**: {len(contributed_repos)}")
    
    # Repositories Created
    if repos_created:
        lines.append("\n## Repositories Created\n")
        for repo in sorted(repos_created, key=lambda x: x.get('createdAt', ''), reverse=True):
            name = repo.get('nameWithOwner', '')
            url = repo.get('url', f'https://github.com/{name}')
            desc = repo.get('description', '') or ''
            created = repo.get('createdAt', '')[:10]
            stars = repo.get('stargazerCount', 0)
            star_str = f" ⭐ {stars}" if stars > 0 else ""
            lines.append(f"- [{name}]({url}) - {created}{star_str}")
            if desc:
                lines.append(f"  - {desc}")
    
    # Repositories Contributed
    if contributed_repos:
        lines.append("\n## Repositories Contributed\n")
        sorted_repos = sorted(contributed_repos.items(), key=lambda x: x[1]['prs'] + x[1]['issues'], reverse=True)
        for repo, counts in sorted_repos:
            parts = []
            if counts['prs'] > 0:
                parts.append(f"PRs: {counts['prs']}")
            if counts['issues'] > 0:
                parts.append(f"Issues: {counts['issues']}")
            lines.append(f"- [{repo}](https://github.com/{repo}) ({', '.join(parts)})")
    
    # Activity by month
    prs_by_month = group_by_month(prs)
    issues_by_month = group_by_month(issues)
    all_months = sorted(set(prs_by_month.keys()) | set(issues_by_month.keys()))
    
    for month in all_months:
        lines.append(f"\n## {month}\n")
        
        month_prs = prs_by_month.get(month, [])
        month_issues = issues_by_month.get(month, [])
        
        if month_prs:
            lines.append("\n### PRs\n")
            for pr in sorted(month_prs, key=lambda x: x.get('createdAt', '')):
                number = pr.get('number', '')
                url = pr.get('url', '')
                repo = pr.get('repository', {}).get('nameWithOwner', '')
                title = pr.get('title', '')
                state = pr.get('state', '').lower()
                activity = pr.get('activity_type', '')
                
                # State emoji
                if state == 'merged' or pr.get('mergedAt'):
                    state_icon = "🟣"
                    state_text = "merged"
                elif state == 'open':
                    state_icon = "🟢"
                    state_text = "open"
                else:
                    state_icon = "🔴"
                    state_text = "closed"
                
                lines.append(f"- {state_icon} [#{number}]({url}) - {repo} - \"{title}\" - {state_text} ({activity})")
        
        if month_issues:
            lines.append("\n### Issues\n")
            for issue in sorted(month_issues, key=lambda x: x.get('createdAt', '')):
                number = issue.get('number', '')
                url = issue.get('url', '')
                repo = issue.get('repository', {}).get('nameWithOwner', '')
                title = issue.get('title', '')
                state = issue.get('state', '').lower()
                activity = issue.get('activity_type', '')
                
                state_icon = "🟢" if state == 'open' else "🔴"
                lines.append(f"- {state_icon} [#{number}]({url}) - {repo} - \"{title}\" - {state} ({activity})")
    
    return '\n'.join(lines)


def parse_year_arg(year_arg: str, registration_year: int) -> List[int]:
    """Parse year argument into list of years"""
    current_year = datetime.now().year
    
    if year_arg == 'all':
        return list(range(registration_year, current_year + 1))
    
    if '-' in year_arg:
        parts = year_arg.split('-')
        if len(parts) == 2:
            start = int(parts[0])
            end = int(parts[1])
            return list(range(start, end + 1))
    
    return [int(year_arg)]


def main():
    parser = argparse.ArgumentParser(
        description="Collect GitHub contributions by year",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s samzong                    # Current year only
  %(prog)s samzong --year 2024        # Specific year
  %(prog)s samzong --year 2021-2025   # Year range
  %(prog)s samzong --year all         # From registration to now
        """
    )
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--year", default=str(datetime.now().year),
                        help="Year(s) to collect: YYYY, YYYY-YYYY, or 'all' (default: current year)")
    parser.add_argument("--output", default="./contributions",
                        help="Output directory (default: ./contributions)")
    args = parser.parse_args()
    
    check_gh_auth()
    
    username = args.username
    output_dir = args.output
    
    print(f"Fetching user info for {username}...")
    user_info = get_user_info(username)
    created_at = user_info.get('created_at', '')
    registration_year = int(created_at[:4]) if created_at else datetime.now().year
    print(f"User registered: {created_at[:10] if created_at else 'unknown'}")
    
    years = parse_year_arg(args.year, registration_year)
    print(f"Years to collect: {years}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for year in years:
        print(f"\n{'='*60}")
        print(f"Collecting {year}...")
        print('='*60)
        
        print(f"  Fetching repositories created in {year}...")
        repos = get_user_repos_created_in_year(username, year)
        print(f"    Found {len(repos)} repositories")
        
        print(f"  Fetching PRs in {year}...")
        prs = get_prs_in_year(username, year)
        print(f"    Found {len(prs)} PR activities")
        
        print(f"  Fetching Issues in {year}...")
        issues = get_issues_in_year(username, year)
        print(f"    Found {len(issues)} Issue activities")
        
        md_content = generate_year_markdown(username, year, repos, prs, issues)
        
        output_file = os.path.join(output_dir, f"{year}.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  ✓ Saved to {output_file}")
    
    print(f"\n{'='*60}")
    print(f"Done! Files saved to {output_dir}/")
    print('='*60)


if __name__ == '__main__':
    main()
