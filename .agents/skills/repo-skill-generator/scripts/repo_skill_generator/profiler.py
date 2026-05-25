from __future__ import annotations

from .models import RepositoryContext
from .util import now_utc, slugify


def build_coding_profile(context: RepositoryContext) -> dict:
    repo_name = context.identity.repo_name
    module = context.identity.module
    scope_label = module or "repository"
    scope_slug = slugify(scope_label)
    skill_name = f"{repo_name}-coding" if module is None else f"{repo_name}-coding-{scope_slug}"

    naming_rules = derive_naming_rules(context)
    error_rules = derive_error_rules(context)
    testing_rules = derive_testing_rules(context)
    comment_rules = derive_comment_rules(context)
    boundary_rules = derive_boundary_rules(context)
    commit_message_rules = derive_commit_message_rules(context)
    toolchain_rules = derive_toolchain_rules(context)

    rules = dedupe(
        boundary_rules
        + naming_rules["rules"]
        + error_rules["rules"]
        + testing_rules["rules"]
        + comment_rules["rules"]
        + commit_message_rules["rules"]
        + toolchain_rules["rules"]
    )
    anti_patterns = dedupe(
        naming_rules["anti_patterns"]
        + error_rules["anti_patterns"]
        + testing_rules["anti_patterns"]
        + comment_rules["anti_patterns"]
        + commit_message_rules["anti_patterns"]
        + toolchain_rules["anti_patterns"]
        + [
            "Do not import style or abstraction patterns from unrelated subsystems when the local scope already has a stable path-local convention.",
            "Do not rely on old repository history when the recent scoped window already provides enough evidence.",
        ]
    )

    return {
        "schema_version": "0.2",
        "generated_at_utc": now_utc(),
        "kind": "coding",
        "skill_name": skill_name,
        "repo": context.identity.repo_slug,
        "scope": scope_label,
        "evidence_window": {
            "since_months": context.identity.since_months,
            "used_recent_window": context.coding.used_recent_window,
            "cutoff_date": context.coding.cutoff_date,
            "recent_commit_count": context.coding.recent_commit_count,
            "full_commit_count": context.coding.full_commit_count,
            "analyzed_commit_count": context.coding.analyzed_commit_count,
        },
        "core_authors": context.coding.core_authors,
        "dominant_extensions": context.coding.dominant_extensions,
        "top_paths": context.coding.top_paths,
        "sample_commits": context.coding.sample_commits,
        "naming_patterns": context.coding.naming_patterns,
        "error_patterns": context.coding.error_patterns,
        "test_patterns": context.coding.test_patterns,
        "comment_patterns": context.coding.comment_patterns,
        "commit_message_patterns": context.coding.commit_message_patterns,
        "subsystem_profiles": context.coding.subsystem_profiles,
        "toolchain_signals": context.coding.toolchain_signals,
        "diff_examples": context.coding.diff_examples,
        "subsystem_notes": context.coding.subsystem_notes,
        "rules": rules,
        "anti_patterns": anti_patterns,
    }


def build_review_profile(context: RepositoryContext) -> dict:
    if context.review is None:
        raise RuntimeError("review context is missing")

    focus_names = [entry["name"] for entry in context.review.focus_areas[:3]]
    blocking_names = [entry["name"] for entry in context.review.blocking_areas[:3]]
    tone = context.review.tone_patterns

    rules = [
        "Review against the repository's observed maintainer bar, not generic best-practice theater.",
        "Call out blocking issues first and keep lighter suggestions clearly non-blocking.",
    ]
    if focus_names:
        rules.append(
            f"Prioritize the focus areas that repeatedly surfaced in real maintainer feedback: {', '.join(focus_names)}."
        )
    if blocking_names:
        rules.append(
            f"Treat the recurring blocking themes as first-class review gates: {', '.join(blocking_names)}."
        )
    if tone.get("polite_requests", 0):
        rules.append("Use direct but polite language when asking for changes.")
    if tone.get("question_driven", 0) >= tone.get("directive_requests", 0):
        rules.append("Phrase ambiguous concerns as concrete questions when the evidence suggests maintainers do the same.")
    if tone.get("approval_shorthand", 0):
        rules.append("Keep obvious approvals concise; maintainers often use short approval messages.")

    blocking_patterns = []
    if blocking_names:
        for name in blocking_names:
            blocking_patterns.append(f"Repeated maintainer feedback treated `{name}` issues as merge blockers.")
    blocking_patterns.extend(
        [
            "Missing validation or tests for behavior-changing diffs is repeatedly risky unless local evidence clearly shows otherwise.",
            "Changes that do not fit the existing subsystem boundaries attract maintainer attention quickly.",
        ]
    )

    return {
        "schema_version": "0.2",
        "generated_at_utc": now_utc(),
        "kind": "review",
        "skill_name": f"{context.identity.repo_name}-review",
        "repo": context.identity.repo_slug,
        "scope": "repository",
        "evidence_window": {
            "effective_review_target": context.identity.effective_review_target,
            "effective_review_count": context.review.effective_review_count,
            "candidate_pr_count": context.review.candidate_pr_count,
            "scanned_pr_count": context.review.scanned_pr_count,
        },
        "core_maintainers": context.review.core_maintainers,
        "reviewer_stats": context.review.reviewer_stats,
        "focus_areas": context.review.focus_areas,
        "blocking_areas": context.review.blocking_areas,
        "tone_patterns": context.review.tone_patterns,
        "sample_prs": context.review.sample_prs,
        "review_examples": context.review.review_examples,
        "excluded_prs": context.review.excluded_prs,
        "rules": dedupe(rules),
        "blocking_patterns": dedupe(blocking_patterns),
    }


def derive_naming_rules(context: RepositoryContext) -> dict[str, list[str]]:
    naming = context.coding.naming_patterns
    rules: list[str] = []
    anti_patterns: list[str] = []
    if not should_use_global_naming_rules(context):
        rules.append(
            "Do not apply one repository-wide naming rule blindly; use the subsystem-specific naming signals in `profiles/` and `references/` for the path you are editing."
        )
        anti_patterns.append(
            "Do not force one language's naming style onto another subsystem when the repository history is clearly multi-modal."
        )
    else:
        function_style = dominant_style(naming.get("function_styles", []))
        if function_style:
            rules.append(
                f"Prefer `{function_style}` for function-level names in this scope; it was the dominant style in sampled diffs."
            )
            anti_patterns.append(
                f"Do not mix multiple function naming styles when `{function_style}` already dominates the scoped history."
            )

        type_style = dominant_style(naming.get("type_styles", []))
        if type_style:
            rules.append(
                f"Keep type and API surface names aligned with the dominant `{type_style}` style observed in the scope."
            )
            anti_patterns.append(
                f"Do not introduce type names that break the dominant `{type_style}` pattern without clear local precedent."
            )

    test_style = dominant_style(naming.get("test_name_styles", []))
    if test_style:
        rules.append(
            f"Match the local test naming pattern (`{test_style}`) when adding or renaming tests."
        )

    return {"rules": rules, "anti_patterns": anti_patterns}


def derive_error_rules(context: RepositoryContext) -> dict[str, list[str]]:
    counts = context.coding.error_patterns.get("counts", {})
    rules: list[str] = []
    anti_patterns: list[str] = []

    if counts.get("go_if_err", 0) or counts.get("return_err", 0):
        rules.append(
            "Use explicit error propagation patterns when modifying Go code; the sampled diffs repeatedly use `if err != nil` and direct error returns."
        )
        anti_patterns.append(
            "Do not hide ordinary error handling behind new helper layers unless the local path already uses them."
        )
    if counts.get("python_raise", 0) or counts.get("python_except", 0):
        rules.append(
            "In Python paths, keep error handling explicit with local `raise` / `except` flows instead of silent fallbacks."
        )
    if counts.get("js_throw", 0):
        rules.append(
            "In JS/TS paths, preserve explicit thrown-error behavior where the current code already signals failure that way."
        )
    if counts.get("panic_or_fatal", 0):
        anti_patterns.append(
            "Do not escalate to `panic` or fatal logging casually; use it only where the profiled scope already treats the path as unrecoverable."
        )

    return {"rules": rules, "anti_patterns": anti_patterns}


def derive_testing_rules(context: RepositoryContext) -> dict[str, list[str]]:
    testing = context.coding.test_patterns
    rules: list[str] = []
    anti_patterns: list[str] = []

    if testing.get("changed_test_commits", 0):
        ratio = testing.get("changed_test_commit_ratio", 0.0)
        frameworks = [entry["name"] for entry in testing.get("framework_hits", [])[:3]]
        framework_text = f" using the existing patterns ({', '.join(frameworks)})" if frameworks else ""
        if ratio >= 0.2:
            rules.append(
                f"Add or update tests alongside behavior changes{framework_text}; test files are touched in a meaningful share of sampled commits."
            )
        else:
            rules.append(
                f"When behavior changes are non-trivial, check whether the scoped history expects matching test updates{framework_text}."
            )
        anti_patterns.append(
            "Do not land behavior-changing code without checking whether nearby commits in the same scope normally add or update tests."
        )

    return {"rules": rules, "anti_patterns": anti_patterns}


def derive_comment_rules(context: RepositoryContext) -> dict[str, list[str]]:
    comment_patterns = context.coding.comment_patterns
    rules: list[str] = []
    anti_patterns: list[str] = []

    comment_ratio = float(comment_patterns.get("comment_ratio", 0.0))
    doc_ratio = float(comment_patterns.get("doc_comment_ratio", 0.0))
    if comment_ratio <= 0.08:
        rules.append(
            "Keep comments sparse and targeted; the sampled diffs skew toward code changes rather than heavy explanatory commentary."
        )
        anti_patterns.append(
            "Do not add verbose narrative comments to straightforward code paths."
        )
    if doc_ratio >= 0.03:
        rules.append(
            "Use doc-style comments where the local scope already documents exposed or user-facing APIs."
        )

    return {"rules": rules, "anti_patterns": anti_patterns}


def derive_boundary_rules(context: RepositoryContext) -> list[str]:
    top_paths = [entry["name"] for entry in context.coding.top_paths[:3]]
    rules: list[str] = []
    if top_paths:
        rules.append(
            f"Respect existing subsystem boundaries; the sampled history clusters most changes in these paths: {', '.join(top_paths)}."
        )
    if context.coding.subsystem_profiles and context.identity.module is None:
        named = ", ".join(profile["path"] for profile in context.coding.subsystem_profiles[:4])
        rules.append(
            f"When working repo-wide, pick the local convention from the nearest subsystem profile instead of averaging across {named}."
        )
    return rules


def derive_commit_message_rules(context: RepositoryContext) -> dict[str, list[str]]:
    patterns = context.coding.commit_message_patterns
    rules: list[str] = []
    anti_patterns: list[str] = []
    commit_types = patterns.get("types", [])
    scopes = patterns.get("scopes", [])

    if not commit_types:
        return {"rules": rules, "anti_patterns": anti_patterns}

    unclassified = next((int(entry["count"]) for entry in commit_types if entry["name"] == "unclassified"), 0)
    classified = sum(int(entry["count"]) for entry in commit_types) - unclassified
    if classified > unclassified:
        rules.append("Follow the repository's conventional commit style: `type(scope): summary` when a stable scope exists.")
        anti_patterns.append("Do not use free-form commit subjects when nearby history already uses typed commit headers.")
    if scopes:
        scope_names = ", ".join(entry["name"] for entry in scopes[:6])
        rules.append(f"Prefer existing commit scopes when they fit the touched subsystem, such as: {scope_names}.")

    return {"rules": rules, "anti_patterns": anti_patterns}


def derive_toolchain_rules(context: RepositoryContext) -> dict[str, list[str]]:
    signals = context.coding.toolchain_signals
    rules: list[str] = []
    anti_patterns: list[str] = []
    make_targets = signals.get("make_targets", [])
    workflow_commands = signals.get("workflow_commands", [])

    if make_targets:
        rules.append(
            f"Prefer repository entrypoints that already exist in `Makefile`, especially these targets: {', '.join(make_targets[:6])}."
        )
        anti_patterns.append("Do not invent one-off local validation commands before checking the repository Makefile and CI entrypoints.")
    if workflow_commands:
        commands = ", ".join(entry["name"] for entry in workflow_commands[:5])
        rules.append(f"Match the CI-visible validation paths already present in workflows: {commands}.")

    return {"rules": rules, "anti_patterns": anti_patterns}


def should_use_global_naming_rules(context: RepositoryContext) -> bool:
    if context.identity.module:
        return True
    if len(context.coding.subsystem_profiles) <= 1:
        return True

    top_paths = context.coding.top_paths
    if not top_paths:
        return True
    total = sum(int(entry["count"]) for entry in top_paths)
    if total <= 0:
        return True
    return int(top_paths[0]["count"]) / total >= 0.7


def dominant_style(entries: list[dict]) -> str | None:
    if not entries:
        return None
    top = entries[0]
    total = sum(int(entry["count"]) for entry in entries)
    if total <= 0 or int(top["count"]) < 3:
        return None
    if int(top["count"]) / total < 0.45:
        return None
    return str(top["name"])


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
