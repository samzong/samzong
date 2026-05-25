from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RepositoryIdentity:
    repo_name: str
    repo_slug: str
    repo_root: str
    module: str | None
    since_months: int
    effective_review_target: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodingEvidence:
    scope_label: str
    used_recent_window: bool
    cutoff_date: str
    recent_commit_count: int
    full_commit_count: int
    analyzed_commit_count: int
    core_authors: list[dict[str, Any]] = field(default_factory=list)
    dominant_extensions: list[dict[str, Any]] = field(default_factory=list)
    top_paths: list[dict[str, Any]] = field(default_factory=list)
    sample_commits: list[dict[str, Any]] = field(default_factory=list)
    naming_patterns: dict[str, Any] = field(default_factory=dict)
    error_patterns: dict[str, Any] = field(default_factory=dict)
    test_patterns: dict[str, Any] = field(default_factory=dict)
    comment_patterns: dict[str, Any] = field(default_factory=dict)
    commit_message_patterns: dict[str, Any] = field(default_factory=dict)
    subsystem_profiles: list[dict[str, Any]] = field(default_factory=list)
    toolchain_signals: dict[str, Any] = field(default_factory=dict)
    diff_examples: list[dict[str, Any]] = field(default_factory=list)
    subsystem_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewEvidence:
    candidate_pr_count: int
    scanned_pr_count: int
    effective_review_count: int
    effective_review_target: int
    excluded_prs: dict[str, int] = field(default_factory=dict)
    core_maintainers: list[dict[str, Any]] = field(default_factory=list)
    reviewer_stats: list[dict[str, Any]] = field(default_factory=list)
    focus_areas: list[dict[str, Any]] = field(default_factory=list)
    blocking_areas: list[dict[str, Any]] = field(default_factory=list)
    tone_patterns: dict[str, Any] = field(default_factory=dict)
    sample_prs: list[dict[str, Any]] = field(default_factory=list)
    review_examples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepositoryContext:
    repo_root: str
    install_repo_name: str
    identity: RepositoryIdentity
    coding: CodingEvidence
    review: ReviewEvidence | None

    @property
    def module(self) -> str | None:
        return self.identity.module

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "install_repo_name": self.install_repo_name,
            "identity": self.identity.to_dict(),
            "coding": self.coding.to_dict(),
            "review": None if self.review is None else self.review.to_dict(),
        }
