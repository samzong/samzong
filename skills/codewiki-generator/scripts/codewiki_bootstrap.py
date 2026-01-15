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
    return parser.parse_args()


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


def build_sidebar(out_dir: Path) -> list[dict]:
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
            items.append({"text": titleize(file_path.stem), "link": f"/{rel[:-3]}"})

        # Add subdirectories (recurse)
        for subdir in subdirs:
            sub_items = _build_items(subdir)
            if sub_items:
                items.append({
                    "text": titleize(subdir.name),
                    "items": sub_items,
                    "collapsed": not is_root,
                })

        return items

    items = _build_items(out_dir, is_root=True)

    # Reorder by priority
    def priority_key(item: dict) -> tuple[int, str]:
        text = item.get("text", "")
        if text == "Overview":
            return (0, text)
        for idx, name in enumerate(PRIORITY_ORDER, start=1):
            if text == titleize(name.replace(".md", "")):
                return (idx, text)
            if text.replace(" ", "-").lower() == name:
                return (idx, text)
        return (len(PRIORITY_ORDER) + 1, text)

    items.sort(key=priority_key)
    return items


def write_sidebar(out_dir: Path, sidebar: list[dict]) -> None:
    vitepress_dir = out_dir / ".vitepress"
    vitepress_dir.mkdir(parents=True, exist_ok=True)
    sidebar_path = vitepress_dir / "sidebar.mjs"
    content = "export default " + json.dumps(sidebar, indent=2) + "\n"
    sidebar_path.write_text(content, encoding="utf-8")


def replace_project_name(out_dir: Path, repo_root: Path) -> None:
    config_path = out_dir / ".vitepress" / "config.mjs"
    if not config_path.exists():
        return
    text = config_path.read_text(encoding="utf-8")
    project_name = repo_root.name
    if "__PROJECT_NAME__" in text:
        text = text.replace("__PROJECT_NAME__", project_name)
        config_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()

    if args.refresh_sidebar:
        sidebar = build_sidebar(out_dir)
        write_sidebar(out_dir, sidebar)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(out_dir, args.force)
    write_required_files(out_dir, args.force)
    if not args.no_copy_images:
        copy_referenced_images(repo_root, out_dir, args.force)
    replace_project_name(out_dir, repo_root)
    sidebar = build_sidebar(out_dir)
    write_sidebar(out_dir, sidebar)


if __name__ == "__main__":
    main()
