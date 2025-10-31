#!/usr/bin/env python3
"""
Analyze GitHub user activity: PRs, Issues, and monthly distribution
"""

import json
import subprocess
import sys
import csv
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

def check_gh_auth():
    """Check if gh CLI is authenticated and print status"""
    print("Checking gh CLI installation...", end=' ')
    try:
        # First check if gh exists
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
        print("✓")
    except FileNotFoundError:
        print("✗")
        print("Error: gh CLI is not installed. Please install it first.", file=sys.stderr)
        print("Visit: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("✗")
        print("Error: Failed to check gh CLI version.", file=sys.stderr)
        sys.exit(1)
    
    print("Checking gh authentication status...", end=' ')
    try:
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            check=True
        )
        # Check if output contains "Logged in"
        if 'Logged in' in result.stdout or 'Logged in' in result.stderr:
            print("✓")
            return True
        print("✗")
        print("Error: gh CLI is not authenticated. Please run 'gh auth login' first.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("✗")
        print("Error: gh CLI is not authenticated. Please run 'gh auth login' first.", file=sys.stderr)
        sys.exit(1)

def run_gh_api(query: str, is_graphql: bool = False) -> dict:
    """Execute gh CLI command and return JSON result
    
    Note: GitHub API rate limits:
    - REST API: 5,000 requests/hour for authenticated users
    - GraphQL API: 5,000 points/hour for authenticated users
    - GraphQL search queries are expensive (multiple points per query)
    - This script may make many API calls due to pagination
    """
    try:
        if is_graphql:
            cmd = ['gh', 'api', 'graphql', '-f', f'query={query}']
        else:
            cmd = ['gh', 'api', query]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        # Check for rate limit errors
        error_output = e.stderr or ''
        if 'rate limit' in error_output.lower() or '429' in error_output:
            print(f"\nError: GitHub API rate limit exceeded. Please wait and try again later.", file=sys.stderr)
            print(f"Rate limit info: https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting", file=sys.stderr)
        else:
            print(f"Error running gh command: {e}", file=sys.stderr)
            print(f"Error output: {e.stderr}", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return {}

def get_user_info(username: str) -> Dict:
    """Get user information"""
    query = f'users/{username}'
    data = run_gh_api(query)
    return {
        'login': data.get('login', username),
        'name': data.get('name', ''),
        'bio': data.get('bio', ''),
        'created_at': data.get('created_at', '')
    }

def get_all_prs(username: str) -> List[dict]:
    """Get all PRs where user is author, commenter, or reviewer"""
    all_prs = []
    
    # GraphQL query to get PRs as author
    query_author = f'''
    {{
      search(query: "author:{username} type:pr", type: ISSUE, first: 100) {{
        issueCount
        nodes {{
          ... on PullRequest {{
            number
            title
            state
            createdAt
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
    
    # Also search for PRs where user commented
    query_comments = f'''
    {{
      search(query: "commenter:{username} type:pr", type: ISSUE, first: 100) {{
        issueCount
        nodes {{
          ... on PullRequest {{
            number
            title
            state
            createdAt
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
    
    # Get PRs as reviewer
    query_reviews = f'''
    {{
      search(query: "reviewed-by:{username} type:pr", type: ISSUE, first: 100) {{
        issueCount
        nodes {{
          ... on PullRequest {{
            number
            title
            state
            createdAt
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
    
    # Fetch all PRs
    for query_type, query in [('author', query_author), ('comments', query_comments), ('reviews', query_reviews)]:
        cursor = None
        while True:
            if cursor:
                # Add pagination
                modified_query = query.replace('first: 100', f'first: 100, after: "{cursor}"')
            else:
                modified_query = query
            
            data = run_gh_api(modified_query, is_graphql=True)
            if not data or 'data' not in data:
                break
                
            search_data = data['data'].get('search', {})
            nodes = search_data.get('nodes', [])
            
            for pr in nodes:
                pr['activity_type'] = query_type
                all_prs.append(pr)
            
            page_info = search_data.get('pageInfo', {})
            if not page_info.get('hasNextPage', False):
                break
            cursor = page_info.get('endCursor')
    
    return all_prs

def get_all_issues(username: str) -> List[dict]:
    """Get all Issues where user is author or commenter"""
    all_issues = []
    
    # GraphQL query to get Issues as author
    query_author = f'''
    {{
      search(query: "author:{username} type:issue", type: ISSUE, first: 100) {{
        issueCount
        nodes {{
          ... on Issue {{
            number
            title
            state
            createdAt
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
    
    # Get Issues where user commented
    query_comments = f'''
    {{
      search(query: "commenter:{username} type:issue", type: ISSUE, first: 100) {{
        issueCount
        nodes {{
          ... on Issue {{
            number
            title
            state
            createdAt
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
    
    # Fetch all Issues
    for query_type, query in [('author', query_author), ('comments', query_comments)]:
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
            
            for issue in nodes:
                issue['activity_type'] = query_type
                all_issues.append(issue)
            
            page_info = search_data.get('pageInfo', {})
            if not page_info.get('hasNextPage', False):
                break
            cursor = page_info.get('endCursor')
    
    return all_issues

def analyze_activity(prs: List[dict], issues: List[dict]) -> Dict:
    """Analyze and group activities by repository and month"""
    repo_stats = defaultdict(lambda: {
        'prs_author': 0,
        'prs_commenter': 0,
        'prs_reviewer': 0,
        'issues_author': 0,
        'issues_commenter': 0,
        'prs': [],
        'issues': []
    })
    
    monthly_stats = defaultdict(lambda: {
        'prs': 0,
        'issues': 0
    })
    
    # Cross-table: repo x month with detailed breakdown
    repo_month_stats = defaultdict(lambda: defaultdict(lambda: {
        'prs_author': 0,
        'prs_commenter': 0,
        'prs_reviewer': 0,
        'prs': 0,
        'issues_author': 0,
        'issues_commenter': 0,
        'issues': 0
    }))
    
    # Process PRs
    for pr in prs:
        repo = pr.get('repository', {}).get('nameWithOwner', 'unknown')
        activity_type = pr.get('activity_type', 'unknown')
        created_at = pr.get('createdAt', '')
        
        if repo not in repo_stats:
            repo_stats[repo] = {
                'prs_author': 0,
                'prs_commenter': 0,
                'prs_reviewer': 0,
                'issues_author': 0,
                'issues_commenter': 0,
                'prs': [],
                'issues': []
            }
        
        if activity_type == 'author':
            repo_stats[repo]['prs_author'] += 1
        elif activity_type == 'comments':
            repo_stats[repo]['prs_commenter'] += 1
        elif activity_type == 'reviews':
            repo_stats[repo]['prs_reviewer'] += 1
        
        repo_stats[repo]['prs'].append(pr)
        
        # Monthly stats with detailed breakdown
        if created_at:
            month = created_at[:7]  # YYYY-MM
            monthly_stats[month]['prs'] += 1
            
            if activity_type == 'author':
                repo_month_stats[repo][month]['prs_author'] += 1
            elif activity_type == 'comments':
                repo_month_stats[repo][month]['prs_commenter'] += 1
            elif activity_type == 'reviews':
                repo_month_stats[repo][month]['prs_reviewer'] += 1
            
            repo_month_stats[repo][month]['prs'] += 1
    
    # Process Issues
    for issue in issues:
        repo = issue.get('repository', {}).get('nameWithOwner', 'unknown')
        activity_type = issue.get('activity_type', 'unknown')
        created_at = issue.get('createdAt', '')
        
        if repo not in repo_stats:
            repo_stats[repo] = {
                'prs_author': 0,
                'prs_commenter': 0,
                'prs_reviewer': 0,
                'issues_author': 0,
                'issues_commenter': 0,
                'prs': [],
                'issues': []
            }
        
        if activity_type == 'author':
            repo_stats[repo]['issues_author'] += 1
        elif activity_type == 'comments':
            repo_stats[repo]['issues_commenter'] += 1
        
        repo_stats[repo]['issues'].append(issue)
        
        # Monthly stats with detailed breakdown
        if created_at:
            month = created_at[:7]  # YYYY-MM
            monthly_stats[month]['issues'] += 1
            
            if activity_type == 'author':
                repo_month_stats[repo][month]['issues_author'] += 1
            elif activity_type == 'comments':
                repo_month_stats[repo][month]['issues_commenter'] += 1
            
            repo_month_stats[repo][month]['issues'] += 1
    
    return {
        'repo_stats': dict(repo_stats),
        'monthly_stats': dict(monthly_stats),
        'repo_month_stats': dict(repo_month_stats)
    }

def generate_repo_summary_table(analysis: Dict, output_format: str = 'csv') -> str:
    """Generate repository summary table"""
    repo_stats = analysis['repo_stats']
    
    # Sort repos by total activity
    repo_list = []
    for repo, stats in repo_stats.items():
        total_prs = stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']
        total_issues = stats['issues_author'] + stats['issues_commenter']
        total_activity = total_prs + total_issues
        repo_list.append({
            'repo': repo,
            'prs_authored': stats['prs_author'],
            'prs_commented': stats['prs_commenter'],
            'prs_reviewed': stats['prs_reviewer'],
            'prs_total': total_prs,
            'issues_authored': stats['issues_author'],
            'issues_commented': stats['issues_commenter'],
            'issues_total': total_issues,
            'total_activity': total_activity
        })
    
    repo_list.sort(key=lambda x: x['total_activity'], reverse=True)
    
    if output_format == 'csv':
        output = []
        output.append(['Repository', 'PRs Authored', 'PRs Commented', 'PRs Reviewed', 'PRs Total', 
                      'Issues Authored', 'Issues Commented', 'Issues Total', 'Total Activity'])
        for repo_data in repo_list:
            output.append([
                repo_data['repo'],
                repo_data['prs_authored'],
                repo_data['prs_commented'],
                repo_data['prs_reviewed'],
                repo_data['prs_total'],
                repo_data['issues_authored'],
                repo_data['issues_commented'],
                repo_data['issues_total'],
                repo_data['total_activity']
            ])
        return '\n'.join([','.join(map(str, row)) for row in output])
    
    elif output_format == 'markdown':
        output = []
        output.append('| Repository | PRs Authored | PRs Commented | PRs Reviewed | PRs Total | '
                     'Issues Authored | Issues Commented | Issues Total | Total Activity |')
        output.append('|------------|--------------|---------------|--------------|-----------|'
                     '----------------|------------------|--------------|----------------|')
        for repo_data in repo_list:
            repo_link = f"[{repo_data['repo']}](https://github.com/{repo_data['repo']})"
            output.append(
                f"| {repo_link} | {repo_data['prs_authored']} | "
                f"{repo_data['prs_commented']} | {repo_data['prs_reviewed']} | "
                f"{repo_data['prs_total']} | {repo_data['issues_authored']} | "
                f"{repo_data['issues_commented']} | {repo_data['issues_total']} | "
                f"{repo_data['total_activity']} |"
            )
        return '\n'.join(output)
    
    return ''

def generate_repo_month_table_csv(analysis: Dict) -> str:
    """Generate repository x month table in long format (CSV only)"""
    repo_month_stats = analysis['repo_month_stats']
    monthly_stats = analysis['monthly_stats']
    
    # Get all months sorted
    all_months = sorted(monthly_stats.keys())
    
    # Get all repos sorted by total activity
    repo_stats = analysis['repo_stats']
    repo_list = []
    for repo, stats in repo_stats.items():
        total_prs = stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']
        total_issues = stats['issues_author'] + stats['issues_commenter']
        total_activity = total_prs + total_issues
        repo_list.append((repo, total_activity))
    repo_list.sort(key=lambda x: x[1], reverse=True)
    repos = [repo for repo, _ in repo_list]
    
    # Generate long format: each row is a Repository-Month combination
    output = []
    header = ['Repository', 'Month', 'PRs Authored', 'PRs Commented', 'PRs Reviewed', 
              'PRs Total', 'Issues Authored', 'Issues Commented', 'Issues Total', 'Total Activity']
    output.append(header)
    
    for repo in repos:
        for month in all_months:
            month_data = repo_month_stats.get(repo, {}).get(month, {})
            prs_authored = month_data.get('prs_author', 0)
            prs_commented = month_data.get('prs_commenter', 0)
            prs_reviewed = month_data.get('prs_reviewer', 0)
            prs_total = month_data.get('prs', 0)
            issues_authored = month_data.get('issues_author', 0)
            issues_commented = month_data.get('issues_commenter', 0)
            issues_total = month_data.get('issues', 0)
            total_activity = prs_total + issues_total
            
            # Only include rows with activity (columns are fixed, rows vary)
            if total_activity > 0:
                output.append([
                    repo,
                    month,
                    prs_authored,
                    prs_commented,
                    prs_reviewed,
                    prs_total,
                    issues_authored,
                    issues_commented,
                    issues_total,
                    total_activity
                ])
    
    return '\n'.join([','.join(map(str, row)) for row in output])

def generate_repo_month_table_markdown(analysis: Dict) -> str:
    """Generate repository x month cross table in wide format (Markdown only)"""
    repo_month_stats = analysis['repo_month_stats']
    monthly_stats = analysis['monthly_stats']
    
    # Get all months sorted
    all_months = sorted(monthly_stats.keys())
    
    # Get all repos sorted by total activity
    repo_stats = analysis['repo_stats']
    repo_list = []
    for repo, stats in repo_stats.items():
        total_prs = stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']
        total_issues = stats['issues_author'] + stats['issues_commenter']
        total_activity = total_prs + total_issues
        repo_list.append((repo, total_activity))
    repo_list.sort(key=lambda x: x[1], reverse=True)
    repos = [repo for repo, _ in repo_list]
    
    output = []
    # Header
    header = '| Repository |'
    for month in all_months:
        header += f' {month} (PRs) | {month} (Issues) |'
    header += ' Total PRs | Total Issues | Total Activity |'
    output.append(header)
    
    # Separator
    sep = '|------------|'
    for _ in all_months:
        sep += '------------|------------|'
    sep += '------------|-------------|----------------|'
    output.append(sep)
    
    # Rows
    for repo in repos:
        row = f'| {repo} |'
        repo_total_prs = 0
        repo_total_issues = 0
        
        for month in all_months:
            month_data = repo_month_stats.get(repo, {}).get(month, {})
            prs = month_data.get('prs', 0)
            issues = month_data.get('issues', 0)
            row += f' {prs} | {issues} |'
            repo_total_prs += prs
            repo_total_issues += issues
        
        row += f' {repo_total_prs} | {repo_total_issues} | {repo_total_prs + repo_total_issues} |'
        output.append(row)
    
    return '\n'.join(output)

def generate_markdown_summary(username: str, user_info: Dict, analysis: Dict) -> str:
    """Generate Markdown summary section"""
    repo_stats = analysis['repo_stats']
    monthly_stats = analysis['monthly_stats']
    
    output = []
    output.append('# GitHub User Activity Analysis Report\n')
    output.append('\n## User Information\n')
    
    # User info
    name = user_info.get('name', '')
    bio = user_info.get('bio', '')
    created_at = user_info.get('created_at', '')
    
    if name:
        output.append(f'- **Username**: {username} ({name})\n')
    else:
        output.append(f'- **Username**: {username}\n')
    output.append(f'- **Registration Date**: {created_at}\n')
    if bio:
        output.append(f'- **Bio**: {bio}\n')
    
    # Overall statistics - as a single row table
    output.append('\n## Overall Statistics\n\n')
    
    total_prs_authored = sum(s['prs_author'] for s in repo_stats.values())
    total_prs_commented = sum(s['prs_commenter'] for s in repo_stats.values())
    total_prs_reviewed = sum(s['prs_reviewer'] for s in repo_stats.values())
    total_issues_authored = sum(s['issues_author'] for s in repo_stats.values())
    total_issues_commented = sum(s['issues_commenter'] for s in repo_stats.values())
    total_prs = total_prs_authored + total_prs_commented + total_prs_reviewed
    total_issues = total_issues_authored + total_issues_commented
    total_activity = total_prs + total_issues
    
    # Single row table with all metrics as columns
    output.append('| Total Repositories | PRs Authored | PRs Commented | PRs Reviewed | Total PRs | ')
    output.append('Issues Authored | Issues Commented | Total Issues | Total Activity |\n')
    output.append('|-------------------|--------------|---------------|--------------|-----------|')
    output.append('------------------|----------------|---------------|---------------|\n')
    output.append(f'| {len(repo_stats)} | {total_prs_authored} | {total_prs_commented} | {total_prs_reviewed} | {total_prs} | ')
    output.append(f'{total_issues_authored} | {total_issues_commented} | {total_issues} | {total_activity} |\n\n')
    
    # Activity trends
    sorted_months = sorted(monthly_stats.keys())
    output.append('\n## Activity Trend Analysis\n\n')
    
    if sorted_months:
        peak_month = max(sorted_months, key=lambda m: monthly_stats[m]['prs'] + monthly_stats[m]['issues'])
        peak_stats = monthly_stats[peak_month]
        peak_total = peak_stats['prs'] + peak_stats['issues']
        
        output.append('### Peak Activity Period\n')
        output.append(f'- **Highest Peak**: {peak_month} ({peak_total} activities)\n')
        
        # Analyze recent activity
        recent_months = sorted_months[-12:] if len(sorted_months) >= 12 else sorted_months
        recent_total = sum(monthly_stats[m]['prs'] + monthly_stats[m]['issues'] for m in recent_months)
        if len(recent_months) >= 6:
            output.append(f'- **Last {len(recent_months)} months**: {recent_total} activities\n')
    
    output.append('\n### Main Contribution Areas\n')
    
    # Identify main contribution areas
    repo_list = []
    for repo, stats in repo_stats.items():
        total_prs = stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']
        total_issues = stats['issues_author'] + stats['issues_commenter']
        total_activity = total_prs + total_issues
        repo_list.append((repo, stats, total_activity))
    
    repo_list.sort(key=lambda x: x[2], reverse=True)
    main_repos = [repo for repo, _, _ in repo_list[:3]]
    for idx, repo in enumerate(main_repos, 1):
        repo_link = f"[{repo}](https://github.com/{repo})"
        output.append(f'{idx}. {repo_link}\n')
    
    return ''.join(output)

def save_tables_to_files(username: str, user_info: Dict, analysis: Dict):
    """Save tables to CSV and Markdown files"""
    # Generate Markdown summary
    md_summary_section = generate_markdown_summary(username, user_info, analysis)
    
    # Repository summary table for Markdown
    md_summary = generate_repo_summary_table(analysis, 'markdown')
    
    # Repository x Month table
    csv_long = generate_repo_month_table_csv(analysis)
    md_cross = generate_repo_month_table_markdown(analysis)
    
    # Save CSV file (long format)
    csv_file = f'{username}_repo_month.csv'
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_long)
    
    # Save Markdown file with summary and tables
    md_file = f'{username}_tables.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_summary_section)
        f.write('\n---\n\n')
        f.write('## Repository Summary Table\n\n')
        f.write('This table shows all repositories with activity summary.\n\n')
        f.write(md_summary)
        f.write('\n')
    
    print(f"\nTables saved to:")
    print(f"  - {csv_file} (CSV - Long format)")
    print(f"  - {md_file} (Markdown - Summary + Tables)")

def print_report(username: str, created_at: str, analysis: Dict):
    """Print analysis report"""
    repo_stats = analysis['repo_stats']
    monthly_stats = analysis['monthly_stats']
    
    print("=" * 80)
    print(f"GitHub User Analysis: {username}")
    print("=" * 80)
    print(f"Registration Date: {created_at}")
    print(f"Total Repositories Involved: {len(repo_stats)}")
    print()
    
    # Repository statistics
    print("=" * 80)
    print("Repository Activity Summary")
    print("=" * 80)
    
    # Sort repos by total activity
    repo_list = []
    for repo, stats in repo_stats.items():
        total_prs = stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']
        total_issues = stats['issues_author'] + stats['issues_commenter']
        total_activity = total_prs + total_issues
        repo_list.append((repo, stats, total_activity))
    
    repo_list.sort(key=lambda x: x[2], reverse=True)
    
    for repo, stats, total_activity in repo_list:
        print(f"\nRepository: {repo}")
        print(f"  Total Activity: {total_activity}")
        print(f"  PRs:")
        print(f"    - Authored: {stats['prs_author']}")
        print(f"    - Commented: {stats['prs_commenter']}")
        print(f"    - Reviewed: {stats['prs_reviewer']}")
        print(f"    - Total PRs: {stats['prs_author'] + stats['prs_commenter'] + stats['prs_reviewer']}")
        print(f"  Issues:")
        print(f"    - Authored: {stats['issues_author']}")
        print(f"    - Commented: {stats['issues_commenter']}")
        print(f"    - Total Issues: {stats['issues_author'] + stats['issues_commenter']}")
    
    # Monthly distribution
    print("\n" + "=" * 80)
    print("Monthly Activity Distribution")
    print("=" * 80)
    
    sorted_months = sorted(monthly_stats.keys())
    for month in sorted_months:
        stats = monthly_stats[month]
        total = stats['prs'] + stats['issues']
        print(f"{month}: PRs={stats['prs']}, Issues={stats['issues']}, Total={total}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Overall Summary")
    print("=" * 80)
    
    total_prs_authored = sum(s['prs_author'] for s in repo_stats.values())
    total_prs_commented = sum(s['prs_commenter'] for s in repo_stats.values())
    total_prs_reviewed = sum(s['prs_reviewer'] for s in repo_stats.values())
    total_issues_authored = sum(s['issues_author'] for s in repo_stats.values())
    total_issues_commented = sum(s['issues_commenter'] for s in repo_stats.values())
    
    print(f"Total PRs Authored: {total_prs_authored}")
    print(f"Total PRs Commented: {total_prs_commented}")
    print(f"Total PRs Reviewed: {total_prs_reviewed}")
    print(f"Total PRs: {total_prs_authored + total_prs_commented + total_prs_reviewed}")
    print(f"Total Issues Authored: {total_issues_authored}")
    print(f"Total Issues Commented: {total_issues_commented}")
    print(f"Total Issues: {total_issues_authored + total_issues_commented}")
    print(f"Total Activity: {total_prs_authored + total_prs_commented + total_prs_reviewed + total_issues_authored + total_issues_commented}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_github_user.py <github_username>")
        sys.exit(1)
    
    # Check if gh CLI is installed and authenticated
    check_gh_auth()
    print()
    
    username = sys.argv[1]
    
    print(f"Fetching user information for {username}...")
    user_info = get_user_info(username)
    created_at = user_info.get('created_at', '')
    print(f"User registered at: {created_at}")
    
    print(f"\nFetching PRs for {username}")
    prs = get_all_prs(username)
    print(f"Found {len(prs)} PR activities")
    
    print(f"\nFetching Issues for {username}")
    issues = get_all_issues(username)
    print(f"Found {len(issues)} Issue activities")
    
    analysis = analyze_activity(prs, issues)
    
    save_tables_to_files(username, user_info, analysis)

if __name__ == '__main__':
    main()

