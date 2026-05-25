#!/usr/bin/env python3
"""Bootstrap a codewiki/ folder with VitePress config, skeleton, and sidebar."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path
import json


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_DIR / "assets" / "vitepress"

REQUIRED_DIRS = [
    "getting-started",
    "architecture",
    "core-components",
    "development",
]

REQUIRED_FILES = {
    "overview.md": """# Overview\n\n```text\n# Related Code:\n- path/to/file\n```\n\n## One-Line Definition\n<!-- Replace with a one-sentence definition of the system. -->\n\n## Tech Stack Radar\n<!-- List core language, framework, infra, and key deps. -->\n\n## System Context Diagram\n<!-- Use Mermaid. -->\n""",
    "architecture/overview.md": """# Architecture Overview\n\n```text\n# Related Code:\n- path/to/file\n```\n\n## Design Rationale\n<!-- Explain why this architecture exists. -->\n""",
    "core-components/overview.md": """# Core Components Overview\n\n```text\n# Related Code:\n- path/to/file\n```\n\n## Component Map\n<!-- Summarize major components and why they exist. -->\n""",
    "development/overview.md": """# Development Overview\n\n```text\n# Related Code:\n- path/to/file\n```\n\n## Local Workflow\n<!-- Describe how to develop locally. -->\n""",
    "getting-started/quickstart.md": """# Quickstart\n\n```text\n# Related Code:\n- path/to/file\n```\n\n## Steps\n<!-- Minimal steps to run the project. -->\n""",
}

EXCLUDE_DIRS = {".vitepress", "assets", "node_modules", ".git", "dist"}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

PRIORITY_ORDER = [
    "overview.md",
    "getting-started",
    "architecture",
    "core-components",
    "development",
    "application-lifecycle",
    "user-inference",
    "api-reference",
    "plugins",
    "build-and-release",
    "data",
    "security",
    "observability",
    "performance",
    "integrations",
    "troubleshooting",
    "glossary.md",
]

LANGUAGE_ALIASES = {
    "en": "en",
    "en-us": "en",
    "english": "en",
    "zh": "zh",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "cn": "zh",
    "chinese": "zh",
}

TRANSLATIONS = {
    "overview": {"zh": "\u6982\u89c8"},
    "getting-started": {"zh": "\u5feb\u901f\u5f00\u59cb"},
    "getting-started/quickstart": {"zh": "\u5feb\u901f\u4e0a\u624b"},
    "architecture": {"zh": "\u67b6\u6784"},
    "architecture/overview": {"zh": "\u67b6\u6784\u6982\u89c8"},
    "core-components": {"zh": "\u6838\u5fc3\u7ec4\u4ef6"},
    "core-components/overview": {"zh": "\u7ec4\u4ef6\u603b\u89c8"},
    "development": {"zh": "\u5f00\u53d1"},
    "development/overview": {"zh": "\u5f00\u53d1\u6307\u5357"},
    "getting-started/overview": {"zh": "\u5f00\u59cb\u603b\u89c8"},
    "application-lifecycle": {"zh": "\u5e94\u7528\u751f\u547d\u5468\u671f"},
    "application-lifecycle/bootstrap": {"zh": "\u542f\u52a8\u6d41\u7a0b"},
    "user-inference": {"zh": "\u7528\u6237\u7406\u89e3"},
    "user-inference/ux-model": {"zh": "UX \u6a21\u578b"},
    "api-reference": {"zh": "API \u53c2\u8003"},
    "api-reference/overview": {"zh": "API \u603b\u89c8"},
    "plugins": {"zh": "\u63d2\u4ef6"},
    "plugins/overview": {"zh": "\u63d2\u4ef6\u6982\u89c8"},
    "build-and-release": {"zh": "\u6784\u5efa\u4e0e\u53d1\u5e03"},
    "build-and-release/ci-cd": {"zh": "CI/CD"},
    "build-and-release/release-process": {"zh": "\u53d1\u5e03\u6d41\u7a0b"},
    "data": {"zh": "\u6570\u636e"},
    "data/domain-model": {"zh": "\u9886\u57df\u6a21\u578b"},
    "data/storage-layout": {"zh": "\u5b58\u50a8\u5e03\u5c40"},
    "security": {"zh": "\u5b89\u5168"},
    "security/auth-authz": {"zh": "\u8ba4\u8bc1\u4e0e\u6388\u6743"},
    "security/threat-model": {"zh": "\u5a01\u80c1\u6a21\u578b"},
    "observability": {"zh": "\u53ef\u89c2\u6d4b\u6027"},
    "observability/logging-metrics-tracing": {"zh": "\u65e5\u5fd7\u3001\u6307\u6807\u4e0e\u8ffd\u8e2a"},
    "observability/runbook": {"zh": "\u8fd0\u8425\u624b\u518c"},
    "performance": {"zh": "\u6027\u80fd"},
    "performance/bottlenecks": {"zh": "\u74f6\u9888\u5206\u6790"},
    "performance/scaling-strategy": {"zh": "\u62c9\u5e73\u7b56\u7565"},
    "integrations": {"zh": "\u96c6\u6210"},
    "integrations/external-services": {"zh": "\u5916\u90e8\u670d\u52a1"},
    "troubleshooting": {"zh": "\u6545\u969c\u6392\u67e5"},
    "troubleshooting/common-issues": {"zh": "\u5e38\u89c1\u95ee\u9898"},
    "glossary": {"zh": "\u672f\u8bed\u8868"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap codewiki output")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Repo root path")
    parser.add_argument("--out-dir", default="codewiki", help="Output directory")
    parser.add_argument("--no-copy-images", action="store_true", help="Skip copying image assets")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--refresh-sidebar",
        action="store_true",
        help="Only regenerate sidebar from current codewiki",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code for sidebar/nav labels (e.g. en, zh, zh-CN)",
    )
    return parser.parse_args()


def normalize_language(value: str | None) -> str:
    if not value:
        return "en"
    key = value.strip().lower()
    return LANGUAGE_ALIASES.get(key, key or "en")


def _normalize_slug(value: str) -> str:
    return value.strip("/").lower()


def display_text(slug: str, raw_name: str, language: str) -> str:
    slug_key = _normalize_slug(slug)
    raw_key = _normalize_slug(raw_name)
    if slug_key:
        lang_map = TRANSLATIONS.get(slug_key)
        if lang_map:
            translated = lang_map.get(language)
            if translated:
                return translated
    lang_map = TRANSLATIONS.get(raw_key)
    if lang_map:
        translated = lang_map.get(language)
        if translated:
            return translated
    return titleize(raw_name)


def safe_copy_file(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_assets(out_dir: Path, force: bool) -> None:
    if not ASSETS_DIR.exists():
        return
    for item in ASSETS_DIR.rglob("*"):
        rel = item.relative_to(ASSETS_DIR)
        target = out_dir / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            safe_copy_file(item, target, force)


def write_required_files(out_dir: Path, force: bool) -> None:
    for rel_dir in REQUIRED_DIRS:
        (out_dir / rel_dir).mkdir(parents=True, exist_ok=True)
    for rel_file, content in REQUIRED_FILES.items():
        target = out_dir / rel_file
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")



def _iter_markdown_files(repo_root: Path) -> list[Path]:
    md_files: list[Path] = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            if name.lower().endswith(".md"):
                md_files.append(Path(root) / name)
    return md_files


def _extract_image_paths(md_text: str) -> list[str]:
    pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    matches = []
    for match in pattern.findall(md_text):
        raw = match.strip().strip("<>")
        if not raw:
            continue
        if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("data:"):
            continue
        # Strip title or fragment.
        raw = raw.split()[0]
        raw = raw.split("#")[0]
        matches.append(raw)
    return matches


def copy_referenced_images(repo_root: Path, out_dir: Path, force: bool) -> None:
    assets_root = out_dir / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    seen: set[Path] = set()
    for md_file in _iter_markdown_files(repo_root):
        try:
            text = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rel in _extract_image_paths(text):
            if rel.startswith("/"):
                candidate = (repo_root / rel.lstrip("/")).resolve()
            else:
                candidate = (md_file.parent / rel).resolve()
            if not candidate.exists() or not candidate.is_file():
                continue
            if candidate.suffix.lower() not in IMAGE_EXTS:
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                rel_to_repo = candidate.relative_to(repo_root)
            except ValueError:
                continue
            target = assets_root / rel_to_repo
            safe_copy_file(candidate, target, force)


def titleize(name: str) -> str:
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in name.split())


def build_sidebar(out_dir: Path, language: str) -> list[dict]:
    def _build_items(dir_path: Path, is_root: bool = False) -> list[dict]:
        """Recursively build sidebar items for a directory."""
        items: list[dict] = []
        files = sorted(p for p in dir_path.iterdir() if p.is_file() and p.suffix == ".md")
        subdirs = sorted(
            p for p in dir_path.iterdir() if p.is_dir() and p.name not in EXCLUDE_DIRS
        )

        # Add files
        for file_path in files:
            if file_path.name == "index.md":
                continue
            rel = file_path.relative_to(out_dir).as_posix()
            slug = rel[:-3]
            items.append({
                "text": display_text(slug, file_path.stem, language),
                "link": f"/{slug}",
                "_slug": slug,
            })

        # Add subdirectories (recurse)
        for subdir in subdirs:
            sub_items = _build_items(subdir)
            if not sub_items:
                continue
            if len(sub_items) == 1 and "items" not in sub_items[0]:
                items.append(sub_items[0])
                continue
            slug = subdir.relative_to(out_dir).as_posix()
            items.append({
                "text": display_text(slug, subdir.name, language),
                "items": sub_items,
                "collapsed": not is_root,
                "_slug": slug,
            })

        return items

    items = _build_items(out_dir, is_root=True)

    # Reorder by priority
    def priority_key(item: dict) -> tuple[int, str]:
        slug = _normalize_slug(item.get("_slug") or item.get("link", "").lstrip("/"))
        text = item.get("text", "")
        if slug == "overview":
            return (0, slug)
        for idx, name in enumerate(PRIORITY_ORDER, start=1):
            normalized = _normalize_slug(name.replace(".md", ""))
            if slug == normalized or slug == _normalize_slug(name):
                return (idx, slug)
        return (len(PRIORITY_ORDER) + 1, slug or text)

    items.sort(key=priority_key)

    def _strip_meta(entries: list[dict]) -> list[dict]:
        for entry in entries:
            entry.pop("_slug", None)
            if "items" in entry:
                _strip_meta(entry["items"])
        return entries

    return _strip_meta(items)


def write_sidebar(out_dir: Path, sidebar: list[dict]) -> None:
    vitepress_dir = out_dir / ".vitepress"
    vitepress_dir.mkdir(parents=True, exist_ok=True)
    sidebar_path = vitepress_dir / "sidebar.mjs"
    content = "export default " + json.dumps(sidebar, indent=2) + "\n"
    sidebar_path.write_text(content, encoding="utf-8")


def replace_project_name(out_dir: Path, repo_root: Path, language: str) -> None:
    config_path = out_dir / ".vitepress" / "config.mjs"
    if not config_path.exists():
        return
    text = config_path.read_text(encoding="utf-8")
    project_name = repo_root.name
    if "__PROJECT_NAME__" in text:
        text = text.replace("__PROJECT_NAME__", project_name)
    nav_label = display_text("overview", "Overview", language)
    text = re.sub(r'text:\s*"Overview"', f'text: "{nav_label}"', text)
    config_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    language = normalize_language(args.language)
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()

    if args.refresh_sidebar:
        sidebar = build_sidebar(out_dir, language)
        write_sidebar(out_dir, sidebar)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(out_dir, args.force)
    write_required_files(out_dir, args.force)
    if not args.no_copy_images:
        copy_referenced_images(repo_root, out_dir, args.force)
    replace_project_name(out_dir, repo_root, language)
    sidebar = build_sidebar(out_dir, language)
    write_sidebar(out_dir, sidebar)


if __name__ == "__main__":
    main()
