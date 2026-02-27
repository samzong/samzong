#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repo_skill_generator.collector import collect_repository_context
from repo_skill_generator.generator import install_generated_skills
from repo_skill_generator.profiler import build_coding_profile, build_review_profile
from repo_skill_generator.verifier import verify_installation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repo-local coding/review skills from git and GitHub history."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository to analyze. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--install-root",
        type=Path,
        default=None,
        help="Directory where generated repo-local skills are installed. Defaults to --repo-root.",
    )
    parser.add_argument(
        "--module",
        type=str,
        default=None,
        help="Optional module or path scope for generating only a module-specific coding skill.",
    )
    parser.add_argument(
        "--since-months",
        type=int,
        default=6,
        help="Coding evidence lookback window in months before falling back to full subsystem history.",
    )
    parser.add_argument(
        "--effective-review-target",
        type=int,
        default=100,
        help="Target number of effective review PRs to collect before stopping.",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=250,
        help="Maximum merged PRs to scan while looking for effective review samples.",
    )
    parser.add_argument(
        "--coding-only",
        action="store_true",
        help="Generate only the coding skill and skip GitHub review collection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and profile data but do not write files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    install_root = args.install_root or args.repo_root

    context = collect_repository_context(
        repo_root=args.repo_root,
        module=args.module,
        since_months=args.since_months,
        effective_review_target=args.effective_review_target,
        max_prs=args.max_prs,
        include_review=not args.coding_only,
    )
    coding_profile = build_coding_profile(context)
    review_profile = None if args.coding_only else build_review_profile(context)

    result = install_generated_skills(
        context=context,
        coding_profile=coding_profile,
        review_profile=review_profile,
        install_root=install_root,
        dry_run=args.dry_run,
    )

    verification = {
        "skipped": args.dry_run,
        "result": None,
    }
    if not args.dry_run:
        verification["result"] = verify_installation(
            install_root=install_root,
            coding_skill_name=result["coding_skill_name"],
            review_skill_name=result.get("review_skill_name"),
            include_review=not args.coding_only,
        )

    summary = {
        "repo_root": str(context.repo_root),
        "install_root": str(install_root),
        "module": context.module,
        "coding_skill": result["coding_skill_name"],
        "review_skill": result.get("review_skill_name"),
        "dry_run": args.dry_run,
        "verification": verification,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
