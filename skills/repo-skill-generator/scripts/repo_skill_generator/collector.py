from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import CodingEvidence, RepositoryContext, RepositoryIdentity, ReviewEvidence
from .util import compact_whitespace, is_bot_login, months_ago, run, run_json, top_n, truncate


MIN_RECENT_SCOPE_COMMITS = 20
MAX_CODING_CANDIDATE_COMMITS = 240
MAX_CODING_ANALYZED_COMMITS = 140
MAX_DIFF_EXAMPLES = 16
MAX_DIFF_EXAMPLE_CANDIDATES = 96
MAX_REVIEW_EXAMPLES = 16
MAX_REVIEW_EXAMPLE_CANDIDATES = 64
MIN_SUBSTANTIVE_REVIEW_EXAMPLES = 6
MIN_DISTINCT_REVIEW_EXAMPLE_PRS = 3

CODE_EXTENSIONS = {
    ".go": "go",
    ".py": "python",
    ".rs": "rust",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".kt": "kotlin",
    ".swift": "swift",
    ".sh": "shell",
}

TEST_FILE_MARKERS = ("_test.go", "_test.py", ".spec.", ".test.", "/test/", "/tests/", "/testing/")

FUNCTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*func(?:\s*\([^)]*\))?\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
    re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"
    ),
)

TYPE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:struct|interface)"),
    re.compile(r"^\s*(?:struct|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_$][A-Za-z0-9_$]*)"),
    re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*="),
)

ERROR_PATTERNS: dict[str, re.Pattern[str]] = {
    "go_if_err": re.compile(r"\bif\s+err\s*!=\s*nil\b"),
    "return_err": re.compile(r"\breturn\b.*\berr\b"),
    "python_raise": re.compile(r"^\s*raise\b"),
    "python_except": re.compile(r"^\s*except\b"),
    "js_throw": re.compile(r"\bthrow\b"),
    "panic_or_fatal": re.compile(r"\bpanic\s*\(|\blog\.(?:Fatal|Panic)\b"),
    "rust_result": re.compile(r"\bResult<"),
    "rust_question": re.compile(r"\?\s*(?:[,;)\]}]|$)"),
}

TEST_FRAMEWORK_PATTERNS_BY_LANGUAGE: dict[str, dict[str, re.Pattern[str]]] = {
    "go": {
        "go_testing": re.compile(r"\bt\.Run\s*\(|\btesting\.T\b"),
        "testify": re.compile(r"\b(?:assert|require)\.[A-Za-z_]+\s*\("),
    },
    "python": {
        "pytest": re.compile(r"\bpytest\b"),
        "unittest": re.compile(r"\bTestCase\b|\bself\.assert"),
    },
    "typescript": {
        "jest_vitest": re.compile(r"\b(?:describe|it|test|expect)\s*\("),
    },
    "javascript": {
        "jest_vitest": re.compile(r"\b(?:describe|it|test|expect)\s*\("),
    },
    "rust": {
        "rust_test": re.compile(r"#\s*\[\s*test\s*\]|\bassert!\s*\("),
    },
}

CONVENTIONAL_COMMIT_RE = re.compile(r"^\[?(?P<type>[a-zA-Z]+)\]?(?:\((?P<scope>[^)]+)\))?!?:")

REVIEW_AREA_KEYWORDS: dict[str, tuple[str, ...]] = {
    "testing": ("test", "tests", "coverage", "assert", "integration test", "e2e"),
    "documentation": ("doc", "docs", "documentation", "readme", "comment"),
    "naming": ("name", "naming", "rename", "terminology"),
    "architecture": ("architecture", "boundary", "layer", "abstraction", "responsibility"),
    "api": ("api", "interface", "contract", "endpoint", "schema"),
    "configuration": ("config", "configuration", "flag", "option", "env"),
    "error-handling": ("error", "errors", "panic", "exception", "retry", "fallback"),
    "performance": ("perf", "performance", "latency", "memory", "cache"),
    "security": ("security", "auth", "permission", "secret", "token"),
    "compatibility": ("compat", "backward", "migration", "upgrade", "breaking"),
    "scope": ("scope", "too much", "separate pr", "follow-up", "split"),
}

AUTO_COMMENT_MARKERS = (
    "automatically generated",
    "generated based on",
    "deploy preview",
    "benchmark results",
    "white paper build",
    "copilot",
    "ai review",
    "powered by",
)

NON_SUBSTANTIVE_CODE_PREFIXES = (
    "import ",
    "from ",
    "package ",
    "use ",
    "export default",
)

CONTROL_FLOW_RE = re.compile(r"^(?:[)}\]]\s*)?(?:if|for|while|switch|case|return|raise|throw|await|match)\b")

MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s|$)")
COMMAND_SNIPPET_RE = re.compile(r"^\s*(make [A-Za-z0-9_.-]+|go test \S+|pytest(?: \S+)?|cargo test(?: \S+)?|pnpm test(?: \S+)?|npm test(?: \S+)?|pre-commit run(?: \S+)?)\s*$")


def collect_repository_context(
    *,
    repo_root: Path,
    module: str | None,
    since_months: int,
    effective_review_target: int,
    max_prs: int,
    include_review: bool,
) -> RepositoryContext:
    repo_root = resolve_repo_root(repo_root)
    repo_slug = resolve_repo_slug(repo_root, include_review=include_review)
    repo_name = repo_slug.split("/")[-1]
    identity = RepositoryIdentity(
        repo_name=repo_name,
        repo_slug=repo_slug,
        repo_root=str(repo_root),
        module=module,
        since_months=since_months,
        effective_review_target=effective_review_target,
    )

    coding = collect_coding_evidence(
        repo_root=repo_root,
        repo_slug=repo_slug,
        module=module,
        since_months=since_months,
    )
    review = None
    if include_review:
        review = collect_review_evidence(
            repo_root=repo_root,
            repo_slug=repo_slug,
            effective_review_target=effective_review_target,
            max_prs=max_prs,
        )

    return RepositoryContext(
        repo_root=str(repo_root),
        install_repo_name=repo_name,
        identity=identity,
        coding=coding,
        review=review,
    )


def resolve_repo_root(repo_root: Path) -> Path:
    try:
        resolved = run(["git", "rev-parse", "--show-toplevel"], cwd=repo_root).strip()
    except RuntimeError as exc:
        raise RuntimeError(f"repo-root must point to a git repository: {exc}") from exc
    return Path(resolved)


def resolve_repo_slug(repo_root: Path, *, include_review: bool) -> str:
    if include_review:
        try:
            payload = run_json(["gh", "repo", "view", "--json", "nameWithOwner"], cwd=repo_root)
            if isinstance(payload, dict) and payload.get("nameWithOwner"):
                return str(payload["nameWithOwner"])
        except Exception:
            pass

    for remote_name in ("upstream", "origin"):
        try:
            remote_url = run(["git", "remote", "get-url", remote_name], cwd=repo_root).strip()
        except RuntimeError:
            continue
        parsed = parse_remote_slug(remote_url)
        if parsed:
            return parsed

    return repo_root.name


def parse_remote_slug(remote_url: str) -> str | None:
    url = remote_url.removesuffix(".git")
    prefixes = (
        "https://github.com/",
        "http://github.com/",
        "ssh://git@github.com/",
        "git@github.com:",
    )
    for prefix in prefixes:
        if url.startswith(prefix):
            return url[len(prefix) :]
    return None


def collect_coding_evidence(
    *,
    repo_root: Path,
    repo_slug: str,
    module: str | None,
    since_months: int,
) -> CodingEvidence:
    cutoff = months_ago(since_months)
    pathspec = build_pathspec(module)

    recent_commit_count = git_commit_count(repo_root, since=cutoff.isoformat(), pathspec=pathspec)
    full_commit_count = git_commit_count(repo_root, since=None, pathspec=pathspec)
    use_recent = recent_commit_count >= MIN_RECENT_SCOPE_COMMITS
    analysis_since = cutoff.isoformat() if use_recent else None

    raw_commits = git_log_entries(
        repo_root,
        since=analysis_since,
        pathspec=pathspec,
        limit=MAX_CODING_CANDIDATE_COMMITS,
    )
    diff_analysis = analyze_code_history(repo_root, raw_commits, pathspec=pathspec)
    toolchain_signals = collect_toolchain_signals(repo_root)
    commit_message_patterns = analyze_commit_messages(diff_analysis["analyzed_commits"])
    subsystem_profiles = build_subsystem_profiles(diff_analysis["subsystem_aggregates"])

    subsystem_notes = []
    if use_recent:
        subsystem_notes.append(
            f"Recent scoped history was sufficient, so the analyzer used the last {since_months} months as the primary coding window."
        )
    else:
        subsystem_notes.append(
            "Recent scoped history was too thin, so the analyzer fell back to the full scoped history for coding evidence."
        )
    if module:
        subsystem_notes.append(f"The coding scope was restricted to the `{module}` module path.")
    if subsystem_profiles:
        named = ", ".join(profile["path"] for profile in subsystem_profiles[:4])
        subsystem_notes.append(f"Subsystem-specific conventions were extracted for: {named}.")

    return CodingEvidence(
        scope_label=module or "repository",
        used_recent_window=use_recent,
        cutoff_date=cutoff.isoformat(),
        recent_commit_count=recent_commit_count,
        full_commit_count=full_commit_count,
        analyzed_commit_count=len(diff_analysis["analyzed_commits"]),
        core_authors=git_shortlog(repo_root, since=analysis_since, pathspec=pathspec),
        dominant_extensions=sorted_counter(diff_analysis["extension_counts"], limit=8),
        top_paths=sorted_counter(diff_analysis["path_counts"], limit=10),
        sample_commits=diff_analysis["sample_commits"],
        naming_patterns=diff_analysis["naming_patterns"],
        error_patterns=diff_analysis["error_patterns"],
        test_patterns=diff_analysis["test_patterns"],
        comment_patterns=diff_analysis["comment_patterns"],
        commit_message_patterns=commit_message_patterns,
        subsystem_profiles=subsystem_profiles,
        toolchain_signals=toolchain_signals,
        diff_examples=diff_analysis["diff_examples"],
        subsystem_notes=subsystem_notes,
    )


def build_pathspec(module: str | None) -> list[str]:
    return [] if not module else ["--", module]


def git_commit_count(repo_root: Path, *, since: str | None, pathspec: list[str]) -> int:
    args = ["git", "rev-list", "--count", "HEAD"]
    if since:
        args.insert(2, f"--since={since}")
    args.extend(pathspec)
    output = run(args, cwd=repo_root).strip()
    return int(output or "0")


def git_log_entries(repo_root: Path, *, since: str | None, pathspec: list[str], limit: int) -> list[dict[str, str]]:
    args = [
        "git",
        "log",
        "--date=short",
        "--pretty=format:%H%x09%ad%x09%an%x09%s",
        "-n",
        str(limit),
    ]
    if since:
        args.append(f"--since={since}")
    args.extend(pathspec)
    output = run(args, cwd=repo_root)
    commits: list[dict[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t", maxsplit=3)
        if len(parts) != 4:
            continue
        commits.append(
            {
                "sha": parts[0],
                "date": parts[1],
                "author": parts[2],
                "subject": parts[3],
            }
        )
    return commits


def git_shortlog(repo_root: Path, *, since: str | None, pathspec: list[str]) -> list[dict[str, int | str]]:
    args = ["git", "shortlog", "-sn", "--all"]
    if since:
        args.append(f"--since={since}")
    args.extend(pathspec)
    output = run(args, cwd=repo_root)
    result: list[dict[str, int | str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t", maxsplit=1)
        if len(parts) != 2:
            continue
        result.append({"name": parts[1].strip(), "count": int(parts[0].strip())})
    return result[:5]


def analyze_code_history(repo_root: Path, commits: list[dict[str, str]], *, pathspec: list[str]) -> dict:
    function_styles: Counter[str] = Counter()
    type_styles: Counter[str] = Counter()
    test_name_styles: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    test_frameworks: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    path_counts: Counter[str] = Counter()
    changed_test_files: set[str] = set()
    analyzed_commits: list[dict[str, str]] = []
    sample_commits: list[dict[str, str]] = []
    diff_example_candidates: list[dict[str, object]] = []
    comment_lines = 0
    doc_comment_lines = 0
    code_lines = 0
    blank_lines = 0
    changed_test_commits = 0
    subsystem_aggregates: dict[str, dict] = {}

    for commit in commits:
        if len(analyzed_commits) >= MAX_CODING_ANALYZED_COMMITS:
            break
        patch = git_patch(repo_root, sha=commit["sha"], pathspec=pathspec)
        patch_summary = analyze_patch(
            patch,
            sha=commit["sha"],
            subject=commit["subject"],
            function_styles=function_styles,
            type_styles=type_styles,
            test_name_styles=test_name_styles,
            error_counts=error_counts,
            test_frameworks=test_frameworks,
            extension_counts=extension_counts,
            path_counts=path_counts,
            changed_test_files=changed_test_files,
            diff_example_candidates=diff_example_candidates,
            subsystem_aggregates=subsystem_aggregates,
        )
        if not patch_summary["has_code"]:
            continue

        analyzed_commits.append(commit)
        if len(sample_commits) < 12:
            sample_commits.append(commit)
        comment_lines += patch_summary["comment_lines"]
        doc_comment_lines += patch_summary["doc_comment_lines"]
        code_lines += patch_summary["code_lines"]
        blank_lines += patch_summary["blank_lines"]
        if patch_summary["touched_test_file"]:
            changed_test_commits += 1

    total_added_lines = comment_lines + code_lines + blank_lines
    return {
        "analyzed_commits": analyzed_commits,
        "sample_commits": sample_commits,
        "extension_counts": extension_counts,
        "path_counts": path_counts,
        "naming_patterns": {
            "function_styles": sorted_counter(function_styles, limit=8),
            "type_styles": sorted_counter(type_styles, limit=8),
            "test_name_styles": sorted_counter(test_name_styles, limit=5),
        },
        "error_patterns": {
            "counts": dict(sorted(error_counts.items())),
        },
        "test_patterns": {
            "changed_test_commits": changed_test_commits,
            "changed_test_commit_ratio": ratio(changed_test_commits, len(analyzed_commits)),
            "changed_test_files": sorted(changed_test_files)[:30],
            "framework_hits": sorted_counter(test_frameworks, limit=8),
        },
        "comment_patterns": {
            "added_comment_lines": comment_lines,
            "added_doc_comment_lines": doc_comment_lines,
            "added_code_lines": code_lines,
            "added_blank_lines": blank_lines,
            "comment_ratio": ratio(comment_lines, total_added_lines),
            "doc_comment_ratio": ratio(doc_comment_lines, total_added_lines),
        },
        "diff_examples": select_diff_examples(diff_example_candidates),
        "subsystem_aggregates": subsystem_aggregates,
    }


def git_patch(repo_root: Path, *, sha: str, pathspec: list[str]) -> str:
    args = ["git", "show", "--format=", "--unified=1", "--no-ext-diff", sha]
    args.extend(pathspec)
    return run(args, cwd=repo_root)


def analyze_patch(
    patch: str,
    *,
    sha: str,
    subject: str,
    function_styles: Counter[str],
    type_styles: Counter[str],
    test_name_styles: Counter[str],
    error_counts: Counter[str],
    test_frameworks: Counter[str],
    extension_counts: Counter[str],
    path_counts: Counter[str],
    changed_test_files: set[str],
    diff_example_candidates: list[dict[str, object]],
    subsystem_aggregates: dict[str, dict],
) -> dict[str, int | bool]:
    current_file: str | None = None
    current_language: str | None = None
    current_subsystem: str | None = None
    current_is_code = False
    current_is_test = False
    hunk_lines: list[str] = []
    hunk_has_code = False
    hunk_score = 0
    touched_test_file = False
    has_code = False
    comment_lines = 0
    doc_comment_lines = 0
    code_lines = 0
    blank_lines = 0
    in_python_multiline_string = False
    in_block_comment = False

    def flush_hunk() -> None:
        nonlocal hunk_lines, hunk_has_code, hunk_score
        if current_file and current_is_code and hunk_has_code and hunk_lines:
            candidate = {
                "sha": sha,
                "path": current_file,
                "subsystem": current_subsystem or ".",
                "language": current_language or "unknown",
                "subject": subject,
                "excerpt": "\n".join(hunk_lines[:10]).strip(),
                "score": hunk_score + len(hunk_lines),
            }
            add_diff_example_candidate(diff_example_candidates, candidate)
        hunk_lines = []
        hunk_has_code = False
        hunk_score = 0

    for line in patch.splitlines():
        if line.startswith("+++ "):
            flush_hunk()
            if line == "+++ /dev/null":
                current_file = None
                current_language = None
                current_subsystem = None
                current_is_code = False
                current_is_test = False
                in_python_multiline_string = False
                in_block_comment = False
                continue
            current_file = line[6:] if line.startswith("+++ b/") else line[4:]
            current_language = detect_language(current_file)
            current_subsystem = top_level_path(current_file)
            current_is_code = current_language is not None
            current_is_test = is_test_path(current_file)
            in_python_multiline_string = False
            in_block_comment = False
            if current_is_code:
                extension_counts[current_language] += 1
                path_counts[current_subsystem or "."] += 1
                subsystem = subsystem_aggregates.setdefault(
                    current_subsystem or ".",
                    {
                        "languages": Counter(),
                        "function_styles": Counter(),
                        "type_styles": Counter(),
                        "error_counts": Counter(),
                        "test_frameworks": Counter(),
                        "test_file_touches": 0,
                    },
                )
                subsystem["languages"][current_language] += 1
                if current_is_test:
                    touched_test_file = True
                    changed_test_files.add(current_file)
                    subsystem["test_file_touches"] += 1
            continue

        if line.startswith("@@ "):
            flush_hunk()
            continue

        if not line.startswith("+") or line.startswith("+++"):
            continue
        if not current_file or not current_is_code:
            continue

        content = line[1:]
        stripped = content.strip()
        subsystem = subsystem_aggregates[current_subsystem or "."]

        if not stripped:
            blank_lines += 1
            continue

        if current_language == "python":
            quote_count = count_python_triple_quotes(content)
            if in_python_multiline_string:
                comment_lines += 1
                if quote_count % 2 == 1:
                    in_python_multiline_string = False
                continue
            if quote_count:
                comment_lines += 1
                doc_comment_lines += 1
                if quote_count % 2 == 1:
                    in_python_multiline_string = True
                continue

        if in_block_comment:
            comment_lines += 1
            if "*/" in stripped:
                in_block_comment = False
            continue

        if stripped.startswith("/*") and "*/" not in stripped:
            comment_lines += 1
            in_block_comment = True
            continue

        if is_comment_line(stripped):
            comment_lines += 1
            if is_doc_comment_line(stripped):
                doc_comment_lines += 1
            continue
        else:
            has_code = True
            code_lines += 1
            hunk_has_code = True
            framework_labels = detect_test_framework_labels(stripped, language=current_language)
            hunk_score += score_code_line(
                stripped,
                is_test=current_is_test,
                has_framework_signal=bool(framework_labels),
            )
            if len(hunk_lines) < 10 and keep_in_diff_example(stripped):
                hunk_lines.append(content.rstrip())

        function_name = extract_name(stripped, FUNCTION_PATTERNS)
        if function_name:
            style = classify_name_style(function_name)
            function_styles[style] += 1
            subsystem["function_styles"][style] += 1
            if current_is_test:
                test_name_styles[classify_test_name(function_name)] += 1

        type_name = extract_name(stripped, TYPE_PATTERNS)
        if type_name:
            style = classify_name_style(type_name)
            type_styles[style] += 1
            subsystem["type_styles"][style] += 1

        for label, pattern in ERROR_PATTERNS.items():
            if pattern.search(stripped):
                error_counts[label] += 1
                subsystem["error_counts"][label] += 1

        for label in detect_test_framework_labels(stripped, language=current_language):
            test_frameworks[label] += 1
            subsystem["test_frameworks"][label] += 1

    flush_hunk()
    return {
        "has_code": has_code,
        "comment_lines": comment_lines,
        "doc_comment_lines": doc_comment_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "touched_test_file": touched_test_file,
    }


def add_diff_example_candidate(candidates: list[dict[str, object]], candidate: dict[str, object]) -> None:
    if len(candidates) >= MAX_DIFF_EXAMPLE_CANDIDATES:
        lowest = min(candidates, key=lambda item: (int(item["score"]), len(str(item["excerpt"]))))
        if int(candidate["score"]) <= int(lowest["score"]):
            return
        candidates.remove(lowest)
    candidates.append(candidate)


def select_diff_examples(candidates: list[dict[str, object]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    per_subsystem: Counter[str] = Counter()
    per_language: Counter[str] = Counter()

    ordered = sorted(
        candidates,
        key=lambda item: (-int(item["score"]), str(item["subsystem"]), str(item["path"]), str(item["sha"])),
    )
    for item in ordered:
        subsystem = str(item["subsystem"])
        language = str(item["language"])
        if per_subsystem[subsystem] >= 3:
            continue
        if per_language[language] >= 5:
            continue
        excerpt = str(item["excerpt"]).strip()
        if not excerpt or excerpt.count("\n") < 1:
            continue
        selected.append(
            {
                "sha": str(item["sha"]),
                "path": str(item["path"]),
                "subsystem": subsystem,
                "language": language,
                "subject": str(item["subject"]),
                "excerpt": excerpt,
            }
        )
        per_subsystem[subsystem] += 1
        per_language[language] += 1
        if len(selected) >= MAX_DIFF_EXAMPLES:
            break
    return selected


def keep_in_diff_example(stripped: str) -> bool:
    if not stripped:
        return False
    if stripped.startswith(NON_SUBSTANTIVE_CODE_PREFIXES):
        return False
    if re.fullmatch(r"[\"'`].+[\"'`],?", stripped):
        return False
    return looks_like_code_statement(stripped)


def score_code_line(stripped: str, *, is_test: bool, has_framework_signal: bool) -> int:
    score = 1
    if extract_name(stripped, FUNCTION_PATTERNS):
        score += 4
    if extract_name(stripped, TYPE_PATTERNS):
        score += 4
    if any(pattern.search(stripped) for pattern in ERROR_PATTERNS.values()):
        score += 3
    if is_test or has_framework_signal:
        score += 2
    if CONTROL_FLOW_RE.search(stripped):
        score += 1
    if len(stripped) >= 48:
        score += 1
    if stripped.startswith(NON_SUBSTANTIVE_CODE_PREFIXES):
        score -= 2
    return score


def looks_like_code_statement(stripped: str) -> bool:
    if stripped in {"(", ")", "{", "}", "[", "]", "},", "),", "};"}:
        return False
    if stripped.startswith(("- ", "* ")):
        return False
    if extract_name(stripped, FUNCTION_PATTERNS) or extract_name(stripped, TYPE_PATTERNS):
        return True
    if any(pattern.search(stripped) for pattern in ERROR_PATTERNS.values()):
        return True
    if CONTROL_FLOW_RE.search(stripped):
        return True
    if re.match(r"^[A-Za-z_][A-Za-z0-9_?]*\s*:\s*[\w\[\]<>{}*]", stripped):
        return True
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s+[A-Za-z0-9_<>\[\]\*]+(?:\s+`[^`]+`)?[,}]?$", stripped):
        return True
    if any(token in stripped for token in ("{", "}", "[", "]", "=", ":=", "=>", "::", "->")):
        return True
    return False


def detect_test_framework_labels(line: str, *, language: str | None) -> list[str]:
    if not language:
        return []
    patterns = TEST_FRAMEWORK_PATTERNS_BY_LANGUAGE.get(language, {})
    hits = []
    for label, pattern in patterns.items():
        if pattern.search(line):
            hits.append(label)
    return hits


def count_python_triple_quotes(line: str) -> int:
    return line.count('"""') + line.count("'''")


def detect_language(path: str) -> str | None:
    suffix = Path(path).suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return CODE_EXTENSIONS[suffix]
    return None


def top_level_path(path: str) -> str:
    parts = Path(path).parts
    return parts[0] if parts else "."


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    base = Path(path).name.lower()
    return (
        any(marker in lowered for marker in TEST_FILE_MARKERS)
        or base.startswith("test_")
        or base.endswith("_test")
    )


def is_comment_line(stripped: str) -> bool:
    return stripped.startswith(("#", "//", "/*", "*", "*/", "--", "<!--", '"""', "'''"))


def is_doc_comment_line(stripped: str) -> bool:
    return stripped.startswith(("///", "/**", '"""', "'''")) or (
        stripped.startswith("//") and len(stripped) > 3 and stripped[2:3].isupper()
    )


def extract_name(line: str, patterns: tuple[re.Pattern[str], ...]) -> str | None:
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def classify_name_style(name: str) -> str:
    if "-" in name:
        return "kebab-case"
    if name.isupper() and "_" in name:
        return "UPPER_SNAKE_CASE"
    if "_" in name and name.lower() == name:
        return "snake_case"
    if name[0].isupper() and "_" not in name:
        return "PascalCase"
    if name[0].islower() and any(char.isupper() for char in name[1:]):
        return "camelCase"
    if name.islower():
        return "lowercase"
    return "mixed"


def classify_test_name(name: str) -> str:
    if name.startswith("Test"):
        return "TestX"
    if name.startswith("test_"):
        return "test_x"
    if name.startswith("should"):
        return "shouldX"
    return classify_name_style(name)


def analyze_commit_messages(commits: list[dict[str, str]]) -> dict[str, object]:
    commit_types: Counter[str] = Counter()
    scopes: Counter[str] = Counter()
    sample_subjects: list[str] = []
    for commit in commits:
        subject = commit["subject"]
        if len(sample_subjects) < 12:
            sample_subjects.append(subject)
        match = CONVENTIONAL_COMMIT_RE.match(subject)
        if not match:
            commit_types["unclassified"] += 1
            continue
        commit_types[match.group("type").lower()] += 1
        scope = match.group("scope")
        if scope:
            scopes[scope.lower()] += 1
    return {
        "types": sorted_counter(commit_types, limit=8),
        "scopes": sorted_counter(scopes, limit=12),
        "sample_subjects": sample_subjects,
    }


def build_subsystem_profiles(subsystem_aggregates: dict[str, dict]) -> list[dict[str, object]]:
    profiles = []
    for path, data in subsystem_aggregates.items():
        language_entries = sorted_counter(data["languages"], limit=4)
        if not language_entries:
            continue
        touches = sum(int(entry["count"]) for entry in language_entries)
        profiles.append(
            {
                "path": path,
                "touches": touches,
                "dominant_languages": language_entries,
                "function_styles": sorted_counter(data["function_styles"], limit=4),
                "type_styles": sorted_counter(data["type_styles"], limit=4),
                "error_patterns": sorted_counter(data["error_counts"], limit=6),
                "test_frameworks": sorted_counter(data["test_frameworks"], limit=4),
                "test_file_touches": data["test_file_touches"],
            }
        )
    return sorted(
        profiles,
        key=lambda item: (
            -sum(int(entry["count"]) for entry in item["dominant_languages"]),
            item["path"],
        ),
    )[:8]


def collect_toolchain_signals(repo_root: Path) -> dict[str, object]:
    workflow_commands: Counter[str] = Counter()
    workflow_files = []
    make_targets = []
    makefile_sources = []
    contributing_commands = []
    build_files = []
    for relative in (
        "Makefile",
        "go.mod",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
    ):
        if (repo_root / relative).exists():
            build_files.append(relative)

    workflow_dir = repo_root / ".github" / "workflows"
    if workflow_dir.is_dir():
        for workflow in sorted(workflow_dir.glob("*.y*ml")):
            workflow_files.append(str(workflow.relative_to(repo_root)))
            text = workflow.read_text(encoding="utf-8", errors="ignore")
            for command in ("make", "go test", "pytest", "cargo test", "npm test", "pnpm test", "uv run"):
                if command in text:
                    workflow_commands[command] += text.count(command)

    makefile = repo_root / "Makefile"
    makefiles_to_scan = collect_makefiles(repo_root, makefile)
    for source in makefiles_to_scan:
        makefile_sources.append(str(source.relative_to(repo_root)))
        for raw_line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = MAKE_TARGET_RE.match(raw_line)
            if not match:
                continue
            target = match.group(1)
            if target.startswith(".") or "%" in target:
                continue
            make_targets.append(target)
        make_targets = sorted(dict.fromkeys(make_targets))[:20]

    contributing = repo_root / "CONTRIBUTING.md"
    if contributing.exists():
        for raw_line in contributing.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = raw_line.strip().strip("`")
            match = COMMAND_SNIPPET_RE.match(stripped)
            if match:
                contributing_commands.append(match.group(1))
        contributing_commands = list(dict.fromkeys(contributing_commands))[:12]

    return {
        "root_build_files": build_files,
        "workflow_files": workflow_files[:12],
        "workflow_commands": sorted_counter(workflow_commands, limit=10),
        "makefile_sources": makefile_sources[:20],
        "make_targets": make_targets,
        "contributing_commands": contributing_commands,
    }


def collect_makefiles(repo_root: Path, makefile: Path) -> list[Path]:
    if not makefile.exists():
        return []
    results = [makefile]
    text = makefile.read_text(encoding="utf-8", errors="ignore")
    for match in re.finditer(r"-f\s+([A-Za-z0-9_./-]+\.mk)", text):
        candidate = repo_root / match.group(1)
        if candidate.exists():
            results.append(candidate)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in results:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def sorted_counter(counter: Counter[str] | dict[str, int], *, limit: int) -> list[dict[str, int | str]]:
    data = dict(counter)
    return top_n(data, limit)


def collect_review_evidence(
    *,
    repo_root: Path,
    repo_slug: str,
    effective_review_target: int,
    max_prs: int,
) -> ReviewEvidence:
    run(["gh", "auth", "status"], cwd=repo_root)
    candidates = run_json(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "merged",
            "--limit",
            str(max_prs),
            "--json",
            "number,title,mergedAt,reviewDecision,isDraft,author",
        ],
        cwd=repo_root,
    )
    if not isinstance(candidates, list):
        raise RuntimeError("unexpected response from gh pr list")

    excluded: Counter[str] = Counter()
    reviewer_scores: Counter[str] = Counter()
    reviewer_stats: dict[str, dict[str, int | str]] = {}
    focus_areas: Counter[str] = Counter()
    blocking_areas: Counter[str] = Counter()
    tone_stats: Counter[str] = Counter()
    sample_prs: list[dict[str, object]] = []
    review_example_candidates: list[dict[str, object]] = []

    scanned_pr_count = 0
    effective_count = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("isDraft"):
            excluded["draft"] += 1
            continue
        if not candidate.get("reviewDecision"):
            excluded["no_review_decision"] += 1
            continue

        scanned_pr_count += 1
        detail = fetch_pr_detail(repo_root, int(candidate["number"]))
        if detail is None:
            excluded["malformed_detail"] += 1
            continue

        pr_author = nested_login(detail.get("author"))
        inline_comments = fetch_inline_review_comments(repo_root, repo_slug=repo_slug, number=int(detail["number"]))
        human_reviews = collect_human_reviews(detail.get("reviews", []), pr_author=pr_author)
        human_comments = collect_human_issue_comments(detail.get("comments", []), pr_author=pr_author)
        human_inline_comments = collect_human_inline_comments(inline_comments, pr_author=pr_author)

        if not human_reviews and not human_comments and not human_inline_comments:
            excluded["no_human_review_activity"] += 1
            continue

        effective_count += 1
        pr_focus: Counter[str] = Counter()
        pr_blocking: Counter[str] = Counter()
        pr_reviewers: set[str] = set()
        pr_states: set[str] = set()
        changed_paths = [entry["path"] for entry in detail.get("files", []) if isinstance(entry, dict) and entry.get("path")]

        for review in human_reviews:
            login = review["login"]
            pr_reviewers.add(login)
            pr_states.add(str(review["state"]))
            update_reviewer_stats(reviewer_stats, login, review_type=str(review["state"]))
            reviewer_scores[login] += review_weight(str(review["state"]))
            areas = classify_review_areas(review["body"]) or infer_areas_from_paths(changed_paths)
            for area in areas:
                focus_areas[area] += 1
                pr_focus[area] += 1
            if is_blocking_review(review):
                blocking_for_review = areas or ["general"]
                for area in blocking_for_review:
                    blocking_areas[area] += 1
                    pr_blocking[area] += 1
            update_tone_stats(tone_stats, review["body"], state=str(review["state"]))
            maybe_add_review_example_candidate(
                review_example_candidates,
                number=int(detail["number"]),
                author=login,
                kind=f"review:{review['state'].lower()}",
                body=review["body"],
                path=None,
            )

        for comment in human_comments:
            login = comment["login"]
            pr_reviewers.add(login)
            update_reviewer_stats(reviewer_stats, login, review_type="ISSUE_COMMENT")
            reviewer_scores[login] += 1
            areas = classify_review_areas(comment["body"]) or infer_areas_from_paths(changed_paths)
            for area in areas:
                focus_areas[area] += 1
                pr_focus[area] += 1
            if is_blocking_text(comment["body"]):
                blocking_for_comment = areas or ["general"]
                for area in blocking_for_comment:
                    blocking_areas[area] += 1
                    pr_blocking[area] += 1
            update_tone_stats(tone_stats, comment["body"], state="COMMENT")
            maybe_add_review_example_candidate(
                review_example_candidates,
                number=int(detail["number"]),
                author=login,
                kind="comment",
                body=comment["body"],
                path=None,
            )

        for comment in human_inline_comments:
            login = comment["login"]
            pr_reviewers.add(login)
            update_reviewer_stats(reviewer_stats, login, review_type="INLINE_COMMENT")
            reviewer_scores[login] += 2
            areas = classify_review_areas(comment["body"]) or infer_areas_from_paths([comment["path"]])
            for area in areas:
                focus_areas[area] += 1
                pr_focus[area] += 1
            if is_blocking_text(comment["body"]):
                blocking_for_comment = areas or ["general"]
                for area in blocking_for_comment:
                    blocking_areas[area] += 1
                    pr_blocking[area] += 1
            update_tone_stats(tone_stats, comment["body"], state="INLINE_COMMENT")
            maybe_add_review_example_candidate(
                review_example_candidates,
                number=int(detail["number"]),
                author=login,
                kind="inline-comment",
                body=comment["body"],
                path=comment["path"],
            )

        if not pr_focus:
            for area in infer_areas_from_paths(changed_paths):
                pr_focus[area] += 1

        sample_prs.append(
            {
                "number": int(detail["number"]),
                "title": str(detail.get("title") or ""),
                "merged_at": str(detail.get("mergedAt") or ""),
                "reviewers": sorted(pr_reviewers),
                "states": sorted(pr_states),
                "focus_areas": [item["name"] for item in sorted_counter(pr_focus, limit=4)],
                "blocking_areas": [item["name"] for item in sorted_counter(pr_blocking, limit=3)],
                "human_review_count": len(human_reviews),
                "human_comment_count": len(human_comments) + len(human_inline_comments),
                "file_count": len(detail.get("files", [])) if isinstance(detail.get("files"), list) else 0,
            }
        )

        if (
            effective_count >= effective_review_target
            and len(review_example_candidates) >= MIN_SUBSTANTIVE_REVIEW_EXAMPLES
            and len({str(item["number"]) for item in review_example_candidates}) >= MIN_DISTINCT_REVIEW_EXAMPLE_PRS
            and sum(blocking_areas.values()) > 0
        ):
            break

    review_examples = select_review_examples(review_example_candidates)
    return ReviewEvidence(
        candidate_pr_count=len(candidates),
        scanned_pr_count=scanned_pr_count,
        effective_review_count=effective_count,
        effective_review_target=effective_review_target,
        excluded_prs=dict(sorted(excluded.items())),
        core_maintainers=sorted_counter(reviewer_scores, limit=5),
        reviewer_stats=sorted(reviewer_stats.values(), key=lambda item: (-int(item["score"]), str(item["login"])))[:12],
        focus_areas=sorted_counter(focus_areas, limit=10),
        blocking_areas=sorted_counter(blocking_areas, limit=10),
        tone_patterns=dict(sorted(tone_stats.items())),
        sample_prs=sample_prs[:12],
        review_examples=review_examples,
    )


def fetch_pr_detail(repo_root: Path, number: int) -> dict | None:
    detail = run_json(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,author,reviews,comments,files,reviewRequests,mergedAt",
        ],
        cwd=repo_root,
    )
    return detail if isinstance(detail, dict) else None


def fetch_inline_review_comments(repo_root: Path, *, repo_slug: str, number: int) -> list[dict]:
    try:
        payload = run_json(
            [
                "gh",
                "api",
                f"repos/{repo_slug}/pulls/{number}/comments?per_page=100",
            ],
            cwd=repo_root,
        )
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def nested_login(value: object) -> str | None:
    if isinstance(value, dict):
        login = value.get("login")
        if isinstance(login, str):
            return login
        user = value.get("user")
        if isinstance(user, dict) and isinstance(user.get("login"), str):
            return str(user["login"])
    return None


def collect_human_reviews(reviews: object, *, pr_author: str | None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if not isinstance(reviews, list):
        return result
    for item in reviews:
        if not isinstance(item, dict):
            continue
        login = nested_login(item.get("author"))
        body = compact_whitespace(str(item.get("body") or ""))
        state = str(item.get("state") or "").upper()
        if not login or login == pr_author or is_noise_comment(login, body):
            continue
        if state not in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED"}:
            continue
        result.append({"login": login, "body": body, "state": state})
    return result


def collect_human_issue_comments(comments: object, *, pr_author: str | None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if not isinstance(comments, list):
        return result
    for item in comments:
        if not isinstance(item, dict):
            continue
        login = nested_login(item.get("author"))
        body = compact_whitespace(str(item.get("body") or ""))
        if not login or login == pr_author or is_noise_comment(login, body):
            continue
        result.append({"login": login, "body": body})
    return result


def collect_human_inline_comments(comments: object, *, pr_author: str | None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if not isinstance(comments, list):
        return result
    for item in comments:
        if not isinstance(item, dict):
            continue
        login = nested_login(item.get("user"))
        body = compact_whitespace(str(item.get("body") or ""))
        path = str(item.get("path") or "")
        if not login or login == pr_author or is_noise_comment(login, body):
            continue
        result.append({"login": login, "body": body, "path": path})
    return result


def is_noise_comment(login: str, body: str) -> bool:
    lowered = body.lower()
    return is_bot_login(login) or any(marker in lowered for marker in AUTO_COMMENT_MARKERS)


def classify_review_areas(body: str) -> list[str]:
    lowered = body.lower()
    hits = []
    for area, keywords in REVIEW_AREA_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            hits.append(area)
    return hits


def infer_areas_from_paths(paths: list[str]) -> list[str]:
    areas: set[str] = set()
    for path in paths:
        lowered = path.lower()
        if any(token in lowered for token in ("/docs/", "readme", ".md")):
            areas.add("documentation")
        if any(token in lowered for token in ("/test", "/tests", "_test.", ".spec.", ".test.")):
            areas.add("testing")
        if any(token in lowered for token in ("config", ".yaml", ".yml", ".toml", ".json")):
            areas.add("configuration")
        if any(token in lowered for token in ("api", "router", "server", "handler", "endpoint")):
            areas.add("api")
    return sorted(areas)


def review_weight(state: str) -> int:
    if state == "CHANGES_REQUESTED":
        return 5
    if state == "APPROVED":
        return 4
    if state == "COMMENTED":
        return 2
    return 1


def update_reviewer_stats(reviewer_stats: dict[str, dict[str, int | str]], login: str, *, review_type: str) -> None:
    stat = reviewer_stats.setdefault(
        login,
        {
            "login": login,
            "score": 0,
            "approvals": 0,
            "changes_requested": 0,
            "commented_reviews": 0,
            "issue_comments": 0,
            "inline_comments": 0,
        },
    )
    if review_type == "APPROVED":
        stat["approvals"] = int(stat["approvals"]) + 1
        stat["score"] = int(stat["score"]) + 4
    elif review_type == "CHANGES_REQUESTED":
        stat["changes_requested"] = int(stat["changes_requested"]) + 1
        stat["score"] = int(stat["score"]) + 5
    elif review_type == "COMMENTED":
        stat["commented_reviews"] = int(stat["commented_reviews"]) + 1
        stat["score"] = int(stat["score"]) + 2
    elif review_type == "ISSUE_COMMENT":
        stat["issue_comments"] = int(stat["issue_comments"]) + 1
        stat["score"] = int(stat["score"]) + 1
    elif review_type == "INLINE_COMMENT":
        stat["inline_comments"] = int(stat["inline_comments"]) + 1
        stat["score"] = int(stat["score"]) + 2


def is_blocking_review(review: dict[str, str]) -> bool:
    return str(review["state"]) == "CHANGES_REQUESTED" or is_blocking_text(review["body"])


def is_blocking_text(body: str) -> bool:
    lowered = body.lower()
    blockers = (
        "must ",
        "needs ",
        "need to ",
        "before merge",
        "block",
        "required",
        "please add",
        "please update",
        "please fix",
        "can you ",
    )
    return any(token in lowered for token in blockers)


def update_tone_stats(tone_stats: Counter[str], body: str, *, state: str) -> None:
    lowered = body.lower()
    if state == "APPROVED" and lowered in {"lgtm", "looks good", "approved", "thanks"}:
        tone_stats["approval_shorthand"] += 1
    if "please" in lowered or "can you" in lowered:
        tone_stats["polite_requests"] += 1
    if "?" in body:
        tone_stats["question_driven"] += 1
    if is_blocking_text(body):
        tone_stats["directive_requests"] += 1
    if len(body) <= 24 and body:
        tone_stats["short_comments"] += 1


def maybe_add_review_example_candidate(
    review_examples: list[dict[str, object]],
    *,
    number: int,
    author: str,
    kind: str,
    body: str,
    path: str | None,
) -> None:
    text = truncate(body, 240)
    if not text:
        return
    if len(text) < 28 and kind != "review:changes_requested":
        return
    score = review_example_score(kind=kind, body=text, path=path)
    if score < 3:
        return
    example = {
        "number": str(number),
        "author": author,
        "kind": kind,
        "excerpt": text,
        "score": score,
    }
    if path:
        example["path"] = path
    if len(review_examples) >= MAX_REVIEW_EXAMPLE_CANDIDATES:
        lowest = min(review_examples, key=lambda item: (int(item["score"]), len(str(item["excerpt"]))))
        if score <= int(lowest["score"]):
            return
        review_examples.remove(lowest)
    review_examples.append(example)


def review_example_score(*, kind: str, body: str, path: str | None) -> int:
    score = 1
    lowered = body.lower()
    if kind == "review:changes_requested":
        score += 5
    elif kind == "inline-comment":
        score += 3
    elif kind.startswith("review:commented"):
        score += 2
    if is_blocking_text(body):
        score += 3
    if "?" in body:
        score += 1
    if path:
        score += 1
    if len(body) >= 120:
        score += 2
    elif len(body) >= 80:
        score += 1
    if lowered in {"lgtm", "looks good", "approved", "thanks"}:
        score -= 4
    return score


def select_review_examples(candidates: list[dict[str, object]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    per_pr: Counter[str] = Counter()
    per_author: Counter[str] = Counter()
    ordered = sorted(
        candidates,
        key=lambda item: (-int(item["score"]), str(item["number"]), str(item["author"]), str(item["kind"])),
    )
    for item in ordered:
        pr_number = str(item["number"])
        author = str(item["author"])
        if per_pr[pr_number] >= 3:
            continue
        if per_author[author] >= 4:
            continue
        example = {
            "number": pr_number,
            "author": author,
            "kind": str(item["kind"]),
            "excerpt": str(item["excerpt"]),
        }
        if item.get("path"):
            example["path"] = str(item["path"])
        selected.append(example)
        per_pr[pr_number] += 1
        per_author[author] += 1
        if len(selected) >= MAX_REVIEW_EXAMPLES:
            break
    return selected
