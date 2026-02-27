#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repo_skill_generator.collector import collect_repository_context
from repo_skill_generator.generator import install_generated_skills
from repo_skill_generator.models import ReviewEvidence
from repo_skill_generator.profiler import build_coding_profile, build_review_profile
from repo_skill_generator.verifier import verify_installation

REVIEW_EVIDENCE_PRESETS: dict[str, dict[str, int]] = {
    "default": {
        "min_effective_reviews": 8,
        "min_unique_human_reviewers": 2,
        "min_substantive_excerpts": 5,
    },
    "solo": {
        "min_effective_reviews": 3,
        "min_unique_human_reviewers": 1,
        "min_substantive_excerpts": 2,
    },
    "strict": {
        "min_effective_reviews": 20,
        "min_unique_human_reviewers": 3,
        "min_substantive_excerpts": 10,
    },
}


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
        "--review-evidence-preset",
        type=str,
        choices=sorted(REVIEW_EVIDENCE_PRESETS.keys()),
        default="default",
        help="Review evidence sufficiency preset. Use 'solo' for repositories with sparse review activity.",
    )
    parser.add_argument(
        "--min-effective-reviews",
        type=int,
        default=None,
        help="Override preset: minimum effective review PRs required to generate a review skill.",
    )
    parser.add_argument(
        "--min-unique-human-reviewers",
        type=int,
        default=None,
        help="Override preset: minimum number of unique human reviewers required to generate a review skill.",
    )
    parser.add_argument(
        "--min-substantive-excerpts",
        type=int,
        default=None,
        help="Override preset: minimum number of substantive review excerpts required to generate a review skill.",
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
    review_thresholds = resolve_review_thresholds(args)

    context = collect_repository_context(
        repo_root=args.repo_root,
        module=args.module,
        since_months=args.since_months,
        effective_review_target=args.effective_review_target,
        max_prs=args.max_prs,
        include_review=not args.coding_only,
    )
    coding_profile = build_coding_profile(context)
    review_profile = None
    review_generation = {
        "requested": not args.coding_only,
        "generated": False,
        "reason": None,
        "preset": args.review_evidence_preset,
        "evidence": None,
    }
    if not args.coding_only:
        ok, gate = review_evidence_sufficient(
            context.review,
            min_effective_reviews=review_thresholds["min_effective_reviews"],
            min_unique_human_reviewers=review_thresholds["min_unique_human_reviewers"],
            min_substantive_excerpts=review_thresholds["min_substantive_excerpts"],
        )
        review_generation["evidence"] = gate
        if ok:
            review_profile = build_review_profile(context)
            review_generation["generated"] = True
        else:
            review_generation["reason"] = "insufficient_review_evidence"

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
            include_review=review_profile is not None,
        )

    summary = {
        "repo_root": str(context.repo_root),
        "install_root": str(install_root),
        "module": context.module,
        "coding_skill": result["coding_skill_name"],
        "review_skill": result.get("review_skill_name"),
        "review_generation": review_generation,
        "dry_run": args.dry_run,
        "verification": verification,
    }
    print(json.dumps(summary, indent=2))
    return 0


def resolve_review_thresholds(args: argparse.Namespace) -> dict[str, int]:
    preset = REVIEW_EVIDENCE_PRESETS[args.review_evidence_preset]
    resolved = dict(preset)
    if args.min_effective_reviews is not None:
        resolved["min_effective_reviews"] = args.min_effective_reviews
    if args.min_unique_human_reviewers is not None:
        resolved["min_unique_human_reviewers"] = args.min_unique_human_reviewers
    if args.min_substantive_excerpts is not None:
        resolved["min_substantive_excerpts"] = args.min_substantive_excerpts
    return resolved


def review_evidence_sufficient(
    review: ReviewEvidence | None,
    *,
    min_effective_reviews: int,
    min_unique_human_reviewers: int,
    min_substantive_excerpts: int,
) -> tuple[bool, dict]:
    if review is None:
        return (
            False,
            {
                "effective_reviews": 0,
                "unique_human_reviewers": 0,
                "substantive_excerpts": 0,
                "thresholds": {
                    "min_effective_reviews": min_effective_reviews,
                    "min_unique_human_reviewers": min_unique_human_reviewers,
                    "min_substantive_excerpts": min_substantive_excerpts,
                },
                "failed_checks": ["review_collection_missing"],
            },
        )

    effective_reviews = int(review.effective_review_count)
    unique_human_reviewers = len({str(entry.get("login")) for entry in review.reviewer_stats if entry.get("login")})
    substantive_excerpts = len(review.review_examples)

    failed_checks: list[str] = []
    if effective_reviews < min_effective_reviews:
        failed_checks.append("effective_reviews")
    if unique_human_reviewers < min_unique_human_reviewers:
        failed_checks.append("unique_human_reviewers")
    if substantive_excerpts < min_substantive_excerpts:
        failed_checks.append("substantive_excerpts")

    gate = {
        "effective_reviews": effective_reviews,
        "unique_human_reviewers": unique_human_reviewers,
        "substantive_excerpts": substantive_excerpts,
        "thresholds": {
            "min_effective_reviews": min_effective_reviews,
            "min_unique_human_reviewers": min_unique_human_reviewers,
            "min_substantive_excerpts": min_substantive_excerpts,
        },
        "failed_checks": failed_checks,
    }
    return len(failed_checks) == 0, gate


if __name__ == "__main__":
    raise SystemExit(main())
