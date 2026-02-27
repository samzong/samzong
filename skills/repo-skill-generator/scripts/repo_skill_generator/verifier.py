from __future__ import annotations

from pathlib import Path


def verify_installation(
    *,
    install_root: Path,
    coding_skill_name: str,
    review_skill_name: str | None,
    include_review: bool,
) -> dict:
    managed_root = install_root / ".agents" / "skills"
    claude_link = install_root / ".claude" / "skills"

    checks = {
        "managed_root_exists": managed_root.is_dir(),
        "claude_link_exists": claude_link.exists() or claude_link.is_symlink(),
        "claude_link_is_symlink": claude_link.is_symlink(),
        "coding_skill_exists": (managed_root / coding_skill_name / "SKILL.md").is_file(),
        "coding_profile_exists": (managed_root / coding_skill_name / "profiles" / "coding-profile.json").is_file(),
        "manifest_exists": (managed_root / ".repo-skill-generator-manifest.json").is_file(),
    }
    if include_review and review_skill_name is not None:
        checks["review_skill_exists"] = (managed_root / review_skill_name / "SKILL.md").is_file()
        checks["review_profile_exists"] = (
            managed_root / review_skill_name / "profiles" / "review-profile.json"
        ).is_file()

    checks["all_passed"] = all(checks.values())
    return checks
