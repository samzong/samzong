from __future__ import annotations

from pathlib import Path

from .models import RepositoryContext
from .util import ensure_directory, ensure_relative_symlink, replace_path, write_json, write_text


def install_generated_skills(
    *,
    context: RepositoryContext,
    coding_profile: dict,
    review_profile: dict | None,
    install_root: Path,
    dry_run: bool,
) -> dict:
    managed_root = install_root / ".agents" / "skills"
    coding_skill_name = str(coding_profile["skill_name"])
    review_skill_name = None if review_profile is None else str(review_profile["skill_name"])

    if dry_run:
        return {
            "coding_skill_name": coding_skill_name,
            "review_skill_name": review_skill_name,
        }

    ensure_directory(managed_root)

    coding_dir = managed_root / coding_skill_name
    replace_path(coding_dir)
    write_coding_skill(coding_dir, context, coding_profile)

    if review_profile is not None:
        review_dir = managed_root / review_skill_name
        replace_path(review_dir)
        write_review_skill(review_dir, context, review_profile)

    manifest = {
        "schema_version": "0.2",
        "generator": "repo-skill-generator",
        "repo": context.identity.repo_slug,
        "coding_skill": coding_skill_name,
        "review_skill": review_skill_name,
        "module": context.identity.module,
    }
    write_json(managed_root / ".repo-skill-generator-manifest.json", manifest)

    ensure_relative_symlink(install_root / ".claude" / "skills", managed_root)
    return {
        "coding_skill_name": coding_skill_name,
        "review_skill_name": review_skill_name,
    }


def write_coding_skill(skill_dir: Path, context: RepositoryContext, profile: dict) -> None:
    template = load_asset("coding_skill.md.tmpl")
    scope_label = str(profile["scope"])
    content = template.format(
        skill_name=profile["skill_name"],
        repo_name=context.identity.repo_name,
        scope_label=scope_label,
        title=f"{context.identity.repo_name} Coding",
        scope_sentence="" if scope_label == "repository" else f" within the `{scope_label}` scope",
    )
    write_text(skill_dir / "SKILL.md", content)
    write_json(skill_dir / "profiles" / "coding-profile.json", profile)
    write_text(skill_dir / "profiles" / "coding-summary.md", render_coding_summary(profile))
    write_text(skill_dir / "references" / "evidence.md", render_coding_evidence(profile))
    write_text(skill_dir / "references" / "anti-patterns.md", render_list_doc("Anti-Patterns", profile["anti_patterns"]))
    write_text(skill_dir / "references" / "examples.md", render_coding_examples(profile))
    write_json(skill_dir / "generator-meta.json", render_generator_meta(profile))


def write_review_skill(skill_dir: Path, context: RepositoryContext, profile: dict) -> None:
    template = load_asset("review_skill.md.tmpl")
    content = template.format(
        skill_name=profile["skill_name"],
        repo_name=context.identity.repo_name,
        title=f"{context.identity.repo_name} Review",
    )
    write_text(skill_dir / "SKILL.md", content)
    write_json(skill_dir / "profiles" / "review-profile.json", profile)
    write_text(skill_dir / "profiles" / "review-summary.md", render_review_summary(profile))
    write_text(skill_dir / "references" / "evidence.md", render_review_evidence(profile))
    write_text(skill_dir / "references" / "blocking-patterns.md", render_list_doc("Blocking Patterns", profile["blocking_patterns"]))
    write_text(skill_dir / "references" / "examples.md", render_review_examples(profile))
    write_json(skill_dir / "generator-meta.json", render_generator_meta(profile))


def load_asset(filename: str) -> str:
    return (Path(__file__).resolve().parents[2] / "assets" / filename).read_text(encoding="utf-8")


def render_generator_meta(profile: dict) -> dict:
    return {
        "managed_by": "repo-skill-generator",
        "skill_name": profile["skill_name"],
        "kind": profile["kind"],
        "scope": profile["scope"],
        "schema_version": profile["schema_version"],
    }


def render_coding_summary(profile: dict) -> str:
    author_lines = render_count_lines(profile["core_authors"], unit="commits")
    extension_lines = render_count_lines(profile["dominant_extensions"], unit="touches")
    path_lines = render_count_lines(profile["top_paths"], unit="touches")
    function_style_lines = render_count_lines(profile["naming_patterns"]["function_styles"], unit="hits")
    type_style_lines = render_count_lines(profile["naming_patterns"]["type_styles"], unit="hits")
    error_lines = render_mapping_lines(profile["error_patterns"]["counts"], unit="hits")
    test_framework_lines = render_count_lines(profile["test_patterns"]["framework_hits"], unit="hits")
    commit_type_lines = render_count_lines(profile["commit_message_patterns"]["types"], unit="commits")
    commit_scope_lines = render_count_lines(profile["commit_message_patterns"]["scopes"], unit="commits")
    subsystem_profile_lines = render_subsystem_profiles(profile["subsystem_profiles"])
    toolchain_lines = render_toolchain_signals(profile["toolchain_signals"])
    rule_lines = render_flat_lines(profile["rules"])
    subsystem_lines = render_flat_lines(profile["subsystem_notes"])

    return f"""# Coding Summary

## Scope

- Repository: `{profile['repo']}`
- Scope: `{profile['scope']}`
- Since months: `{profile['evidence_window']['since_months']}`
- Used recent window: `{profile['evidence_window']['used_recent_window']}`
- Cutoff date: `{profile['evidence_window']['cutoff_date']}`
- Recent commit count: `{profile['evidence_window']['recent_commit_count']}`
- Full scoped commit count: `{profile['evidence_window']['full_commit_count']}`
- Analyzed commits: `{profile['evidence_window']['analyzed_commit_count']}`

## Core Authors

{author_lines}

## Dominant Extensions

{extension_lines}

## Dominant Paths

{path_lines}

## Function Naming

{function_style_lines}

## Type Naming

{type_style_lines}

## Error Handling Signals

{error_lines}

## Test Signals

- Test-touch commit ratio: `{profile['test_patterns']['changed_test_commit_ratio']}`
- Test-touch commits: `{profile['test_patterns']['changed_test_commits']}`
{test_framework_lines}

## Comment Signals

- Added code lines: `{profile['comment_patterns']['added_code_lines']}`
- Added comment lines: `{profile['comment_patterns']['added_comment_lines']}`
- Comment ratio: `{profile['comment_patterns']['comment_ratio']}`
- Doc-comment ratio: `{profile['comment_patterns']['doc_comment_ratio']}`

## Commit Message Signals

### Types

{commit_type_lines}

### Scopes

{commit_scope_lines}

## Subsystem Profiles

{subsystem_profile_lines}

## Build And CI Signals

{toolchain_lines}

## Working Rules

{rule_lines}

## Scope Notes

{subsystem_lines}
"""


def render_coding_evidence(profile: dict) -> str:
    commit_lines = "\n".join(
        f"- `{entry['sha'][:12]}` {entry['date']} `{entry['author']}`: {entry['subject']}"
        for entry in profile["sample_commits"]
    ) or "- No sample commits collected."
    sample_subjects = render_subject_lines(profile["commit_message_patterns"].get("sample_subjects", []))
    subsystem_lines = render_subsystem_profiles(profile["subsystem_profiles"])
    toolchain_lines = render_toolchain_signals(profile["toolchain_signals"])
    diff_index_lines = render_diff_example_index(profile["diff_examples"])
    return f"""# Coding Evidence

This profile was built from real git history and diff content.

## Sample Commits

{commit_lines}

## Commit Subject Samples

{sample_subjects}

## Subsystem Evidence

{subsystem_lines}

## Build And CI Evidence

{toolchain_lines}

## Diff Evidence Index

{diff_index_lines}

Raw diff excerpts are stored in `profiles/coding-profile.json` under `diff_examples`.
"""


def render_coding_examples(profile: dict) -> str:
    if not profile["diff_examples"]:
        return "# Examples\n\nNo examples collected.\n"

    entries = []
    for idx, example in enumerate(profile["diff_examples"], start=1):
        entries.append(
            "\n".join(
                [
                    f"## Example {idx}: `{example['path']}`",
                    "",
                    f"- Commit: `{example['sha'][:12]}`",
                    f"- Subject: {example['subject']}",
                    f"- Subsystem: `{example['subsystem']}`",
                    f"- Language: `{example['language']}`",
                    f"- Preview: `{excerpt_preview(example['excerpt'])}`",
                ]
            )
        )
    return (
        "# Examples\n\n"
        "This file is an annotated index. Canonical raw snippets remain in `profiles/coding-profile.json` (`diff_examples`).\n\n"
        + "\n\n".join(entries)
        + "\n"
    )


def render_review_summary(profile: dict) -> str:
    maintainer_lines = render_count_lines(profile["core_maintainers"], unit="weighted actions")
    focus_lines = render_count_lines(profile["focus_areas"], unit="hits")
    blocking_lines = render_count_lines(profile["blocking_areas"], unit="hits")
    reviewer_stats_lines = []
    for entry in profile["reviewer_stats"]:
        reviewer_stats_lines.append(
            f"- `{entry['login']}`: score={entry['score']} approvals={entry['approvals']} changes_requested={entry['changes_requested']} commented_reviews={entry['commented_reviews']} issue_comments={entry['issue_comments']}"
        )
    reviewer_stats = "\n".join(reviewer_stats_lines) or "- No reviewer stats recorded."
    tone_lines = render_mapping_lines(profile["tone_patterns"], unit="hits")
    rule_lines = render_flat_lines(profile["rules"])
    note_lines = []
    if not any(int(entry["changes_requested"]) for entry in profile["reviewer_stats"]):
        note_lines.append(
            "No `CHANGES_REQUESTED` reviews were observed in the sampled window, so blocking patterns were inferred from substantive comments and inline review text."
        )
    notes = render_flat_lines(note_lines)

    return f"""# Review Summary

## Scope

- Repository: `{profile['repo']}`
- Effective review target: `{profile['evidence_window']['effective_review_target']}`
- Effective review count: `{profile['evidence_window']['effective_review_count']}`
- Candidate PR count: `{profile['evidence_window']['candidate_pr_count']}`
- Scanned PR count: `{profile['evidence_window']['scanned_pr_count']}`

## Core Maintainers

{maintainer_lines}

## Reviewer Stats

{reviewer_stats}

## Focus Areas

{focus_lines}

## Blocking Areas

{blocking_lines}

## Tone Signals

{tone_lines}

## Sampling Notes

{notes}

## Working Rules

{rule_lines}
"""


def render_review_evidence(profile: dict) -> str:
    excluded = render_mapping_lines(profile["excluded_prs"], unit="prs")
    samples = []
    for entry in profile["sample_prs"]:
        focus = ", ".join(entry["focus_areas"]) if entry["focus_areas"] else "none"
        blocking = ", ".join(entry["blocking_areas"]) if entry["blocking_areas"] else "none"
        samples.append(
            f"- PR #{entry['number']} `{entry['title']}` reviewers={', '.join(entry['reviewers']) or 'none'} states={', '.join(entry['states']) or 'none'} focus={focus} blocking={blocking} human_reviews={entry['human_review_count']} human_comments={entry['human_comment_count']}"
        )
    sample_lines = "\n".join(samples) or "- No sample PRs collected."
    excerpt_lines = render_review_excerpt_index(profile.get("review_examples", []))

    return f"""# Review Evidence

This profile was generated from real GitHub PR review activity.

## Excluded PR Buckets

{excluded}

## Sample Effective Review PRs

{sample_lines}

## Substantive Review Excerpts Index

{excerpt_lines}
"""


def render_review_examples(profile: dict) -> str:
    entries = []
    for example in profile["review_examples"]:
        lines = [f"## PR #{example['number']} `{example['author']}` `{example['kind']}`", ""]
        if example.get("path"):
            lines.extend([f"- Path: `{example['path']}`", ""])
        lines.append(example["excerpt"])
        entries.append("\n".join(lines))
    return "# Examples\n\n" + ("\n\n".join(entries) if entries else "No review examples collected.\n")


def render_subsystem_profiles(items: list[dict]) -> str:
    if not items:
        return "- No subsystem profiles recorded."
    lines = []
    for entry in items:
        languages = ", ".join(f"{item['name']} ({item['count']})" for item in entry.get("dominant_languages", [])[:3]) or "none"
        function_styles = ", ".join(f"{item['name']} ({item['count']})" for item in entry.get("function_styles", [])[:2]) or "none"
        type_styles = ", ".join(f"{item['name']} ({item['count']})" for item in entry.get("type_styles", [])[:2]) or "none"
        test_frameworks = ", ".join(f"{item['name']} ({item['count']})" for item in entry.get("test_frameworks", [])[:2]) or "none"
        lines.append(
            f"- `{entry['path']}`: touches={entry.get('touches', 0)} languages={languages}; functions={function_styles}; types={type_styles}; tests={test_frameworks}"
        )
    return "\n".join(lines)


def render_toolchain_signals(signals: dict) -> str:
    lines = []
    build_files = signals.get("root_build_files", [])
    if build_files:
        lines.append(f"- Root build files: {', '.join(f'`{item}`' for item in build_files)}")
    workflow_files = signals.get("workflow_files", [])
    if workflow_files:
        lines.append(f"- Workflow files: {', '.join(f'`{item}`' for item in workflow_files[:6])}")
    makefile_sources = signals.get("makefile_sources", [])
    if makefile_sources:
        lines.append(f"- Makefile sources: {', '.join(f'`{item}`' for item in makefile_sources[:10])}")
    workflow_commands = signals.get("workflow_commands", [])
    if workflow_commands:
        lines.append(
            "- Workflow commands: "
            + ", ".join(f"`{entry['name']}` ({entry['count']})" for entry in workflow_commands[:6])
        )
    make_targets = signals.get("make_targets", [])
    if make_targets:
        lines.append(f"- Make targets: {', '.join(f'`{item}`' for item in make_targets[:10])}")
    contributing_commands = signals.get("contributing_commands", [])
    if contributing_commands:
        lines.append(f"- CONTRIBUTING commands: {', '.join(f'`{item}`' for item in contributing_commands[:8])}")
    return "\n".join(lines) or "- No build or CI signals recorded."


def render_subject_lines(items: list[str]) -> str:
    if not items:
        return "- No commit subjects recorded."
    return "\n".join(f"- {item}" for item in items)


def render_diff_example_index(items: list[dict]) -> str:
    if not items:
        return "- No diff examples recorded."
    lines = []
    for entry in items:
        lines.append(
            f"- `{entry['path']}` @ `{entry['sha'][:12]}` subsystem=`{entry['subsystem']}` language=`{entry['language']}`"
        )
    return "\n".join(lines)


def excerpt_preview(text: str, *, limit: int = 120) -> str:
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if len(first) <= limit:
        return first
    return first[: limit - 3].rstrip() + "..."


def render_review_excerpt_index(items: list[dict]) -> str:
    if not items:
        return "- No substantive excerpts recorded."
    lines = []
    for entry in items:
        lines.append(
            f"- PR #{entry['number']} `{entry['kind']}` by `{entry['author']}`: `{excerpt_preview(entry['excerpt'])}`"
        )
    return "\n".join(lines)


def render_flat_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) or "- No items recorded."


def render_count_lines(items: list[dict], *, unit: str) -> str:
    if not items:
        return "- No items recorded."
    return "\n".join(f"- `{entry['name']}`: {entry['count']} {unit}" for entry in items)


def render_mapping_lines(items: dict[str, int], *, unit: str) -> str:
    if not items:
        return "- No items recorded."
    return "\n".join(f"- `{key}`: {value} {unit}" for key, value in items.items())


def render_list_doc(title: str, items: list[str]) -> str:
    lines = "\n".join(f"- {item}" for item in items) or "- No items recorded."
    return f"# {title}\n\n{lines}\n"
