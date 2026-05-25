#!/usr/bin/env python3
"""Analyze a repository and generate deep codewiki docs + metadata.

This script is designed to augment the codewiki-generator skill with a
stronger, evidence-driven planning and writing pipeline.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
EVIDENCE_RULES_PATH = REFERENCES_DIR / "evidence-rules.json"

EXCLUDE_DIRS = {".git", ".vitepress", "node_modules", ".venv", "dist", "build", "target", "codewiki"}

CODE_EXTS = {".py", ".go", ".rs", ".swift", ".js", ".ts", ".tsx", ".jsx", ".kt", ".java"}
TEXT_EXTS = CODE_EXTS | {".md", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}

REQUIRED_PAGES = [
    {"path": "overview.md", "title": "Overview", "template": "overview"},
    {"path": "getting-started/quickstart.md", "title": "Quickstart", "template": "quickstart"},
    {"path": "architecture/overview.md", "title": "Architecture Overview", "template": "architecture"},
    {"path": "core-components/overview.md", "title": "Core Components Overview", "template": "components"},
    {"path": "development/overview.md", "title": "Development Overview", "template": "development"},
]

MODULE_PAGES = {
    "ui-app": [
        {"path": "application-lifecycle/bootstrap.md", "title": "Application Bootstrap", "template": "bootstrap"},
        {"path": "user-inference/ux-model.md", "title": "UX Model", "template": "ux"},
    ],
    "api": [
        {"path": "api-reference/overview.md", "title": "API Overview", "template": "api"},
    ],
    "plugins": [
        {"path": "plugins/overview.md", "title": "Plugins Overview", "template": "plugins"},
    ],
    "build-and-release": [
        {"path": "build-and-release/ci-cd.md", "title": "CI/CD", "template": "ci"},
        {"path": "build-and-release/release-process.md", "title": "Release Process", "template": "release"},
    ],
    "data": [
        {"path": "data/domain-model.md", "title": "Domain Model", "template": "domain"},
        {"path": "data/storage-layout.md", "title": "Storage Layout", "template": "storage"},
    ],
    "security": [
        {"path": "security/auth-authz.md", "title": "Auth & Authz", "template": "auth"},
        {"path": "security/threat-model.md", "title": "Threat Model", "template": "threat"},
    ],
    "observability": [
        {"path": "observability/logging-metrics-tracing.md", "title": "Observability", "template": "observability"},
        {"path": "observability/runbook.md", "title": "Runbook", "template": "runbook"},
    ],
    "performance": [
        {"path": "performance/bottlenecks.md", "title": "Bottlenecks", "template": "bottlenecks"},
        {"path": "performance/scaling-strategy.md", "title": "Scaling Strategy", "template": "scaling"},
    ],
    "integrations": [
        {"path": "integrations/external-services.md", "title": "External Services", "template": "integrations"},
    ],
    "troubleshooting": [
        {"path": "troubleshooting/common-issues.md", "title": "Common Issues", "template": "troubleshooting"},
    ],
    "glossary": [
        {"path": "glossary.md", "title": "Glossary", "template": "glossary"},
    ],
}


@dataclass
class RepoMeta:
    root: Path
    files: list[Path]
    rel_files: list[str]
    languages: list[str]
    deps: set[str]
    commands: list[str]
    entrypoints: list[str]
    top_dirs: list[str]
    tech_stack: list[str]
    symbols: list[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze repo and generate deep codewiki docs")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Repo root path")
    parser.add_argument("--out-dir", default="codewiki", help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing docs")
    parser.add_argument("--no-bootstrap", action="store_true", help="Skip bootstrap step")
    parser.add_argument("--analyze-only", action="store_true", help="Only write metadata outputs")
    parser.add_argument("--no-write-docs", action="store_true", help="Skip doc generation")
    parser.add_argument("--refresh-sidebar", action="store_true", help="Refresh sidebar after generation")
    parser.add_argument("--language", default="en", help="Language code passed to bootstrap/sidebar")
    return parser.parse_args()


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def _iter_repo_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in filenames:
            files.append(Path(root) / name)
    return files


def _detect_languages(files: list[Path]) -> list[str]:
    langs: set[str] = set()
    for path in files:
        if path.name == "go.mod":
            langs.add("Go")
        if path.name == "Cargo.toml":
            langs.add("Rust")
        if path.name == "Package.swift":
            langs.add("Swift")
        if path.name == "pyproject.toml" or path.name == "requirements.txt":
            langs.add("Python")
        if path.name == "package.json":
            langs.add("JavaScript/TypeScript")
        if path.suffix == ".py":
            langs.add("Python")
        if path.suffix == ".go":
            langs.add("Go")
        if path.suffix == ".rs":
            langs.add("Rust")
        if path.suffix == ".swift":
            langs.add("Swift")
        if path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            langs.add("JavaScript/TypeScript")
    return sorted(langs)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _load_toml(path: Path) -> dict[str, Any] | None:
    if tomllib is None:
        return None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def _extract_deps_from_package_json(path: Path) -> set[str]:
    data = _load_json(path)
    if not data:
        return set()
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        for dep in (data.get(key) or {}).keys():
            deps.add(dep.lower())
    return deps


def _extract_deps_from_pyproject(path: Path) -> set[str]:
    data = _load_toml(path)
    if not data:
        return set()
    deps = set()
    project = data.get("project") or {}
    for dep in project.get("dependencies") or []:
        deps.add(dep.split()[0].lower())
    for extra in (project.get("optional-dependencies") or {}).values():
        for dep in extra:
            deps.add(dep.split()[0].lower())
    poetry = (data.get("tool") or {}).get("poetry") or {}
    for dep in (poetry.get("dependencies") or {}).keys():
        if dep != "python":
            deps.add(dep.lower())
    return deps


def _extract_deps_from_requirements(path: Path) -> set[str]:
    deps = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[<=>]", line)[0].strip()
            if pkg:
                deps.add(pkg.lower())
    except UnicodeDecodeError:
        return deps
    return deps


def _extract_deps_from_cargo(path: Path) -> set[str]:
    data = _load_toml(path)
    if not data:
        return set()
    deps = set()
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        for dep in (data.get(section) or {}).keys():
            deps.add(dep.lower())
    return deps


def _extract_deps_from_go_mod(path: Path) -> set[str]:
    deps = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("require "):
                parts = line.split()
                if len(parts) >= 2:
                    deps.add(parts[1].lower())
            elif line and not line.startswith("module") and not line.startswith("//"):
                if re.match(r"^[\w\.-]+\.[\w\.-/]+", line):
                    deps.add(line.split()[0].lower())
    except UnicodeDecodeError:
        return deps
    return deps


def _extract_deps_from_metadata(repo_root: Path) -> set[str]:
    deps = set()
    # Go
    if (repo_root / "go.mod").exists():
        code, output = _run(["go", "list", "-deps", "-f", "{{.Path}}", "./..."], cwd=repo_root)
        if code == 0:
            for line in output.splitlines():
                deps.add(line.strip().lower())
    # Rust
    if (repo_root / "Cargo.toml").exists():
        code, output = _run(["cargo", "metadata", "--no-deps", "--format-version=1"], cwd=repo_root)
        if code == 0:
            try:
                data = json.loads(output)
                for pkg in data.get("packages") or []:
                    deps.add(pkg.get("name", "").lower())
            except json.JSONDecodeError:
                pass
    # Swift
    if (repo_root / "Package.swift").exists():
        code, output = _run(["swift", "package", "dump-package"], cwd=repo_root)
        if code == 0:
            try:
                data = json.loads(output)
                for dep in data.get("dependencies") or []:
                    if "name" in dep:
                        deps.add(str(dep["name"]).lower())
            except json.JSONDecodeError:
                pass
    return deps


def _detect_commands(repo_root: Path) -> list[str]:
    commands: list[str] = []
    pkg = repo_root / "package.json"
    if pkg.exists():
        data = _load_json(pkg) or {}
        scripts = data.get("scripts") or {}
        if scripts:
            commands.append("npm install")
        for key in ("dev", "start", "test", "build", "lint"):
            if key in scripts:
                commands.append(f"npm run {key}")
    makefile = repo_root / "Makefile"
    if makefile.exists():
        targets = []
        try:
            for line in makefile.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("\t") or line.startswith("#"):
                    continue
                if ":" in line and not line.startswith("."):
                    target = line.split(":", 1)[0].strip()
                    if target and " " not in target:
                        targets.append(target)
        except UnicodeDecodeError:
            targets = []
        for target in sorted(set(targets))[:6]:
            commands.append(f"make {target}")
    if (repo_root / "go.mod").exists():
        commands.extend(["go test ./...", "go vet ./..."])
    if (repo_root / "Cargo.toml").exists():
        commands.extend(["cargo build", "cargo test", "cargo run"])
    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        commands.extend(["python -m pytest", "python -m pip install -r requirements.txt"])
    if (repo_root / "Package.swift").exists():
        commands.extend(["swift build", "swift test"])
    return _dedupe(commands)


def _detect_entrypoints(files: list[Path], repo_root: Path) -> list[str]:
    entrypoints = []
    candidates = [
        "main.go",
        "main.rs",
        "main.py",
        "__main__.py",
        "app.py",
        "server.py",
        "index.js",
        "main.ts",
        "App.tsx",
        "App.jsx",
        "Package.swift",
    ]
    for path in files:
        if path.name in candidates:
            entrypoints.append(str(path.relative_to(repo_root)))
    cmd_dir = repo_root / "cmd"
    if cmd_dir.exists():
        for sub in cmd_dir.iterdir():
            if sub.is_dir():
                entrypoints.append(str(sub.relative_to(repo_root)))
    return _dedupe(entrypoints)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _top_level_dirs(repo_root: Path) -> list[str]:
    dirs = []
    for p in repo_root.iterdir():
        if p.is_dir() and p.name not in EXCLUDE_DIRS:
            dirs.append(p.name)
    return sorted(dirs)


def _tech_stack(meta: RepoMeta) -> list[str]:
    stack = []
    for lang in meta.languages:
        stack.append(lang)
    # Add key deps as hints
    for dep in sorted(meta.deps):
        if dep in {"react", "vue", "svelte", "next", "nuxt", "fastapi", "flask", "gin", "echo", "axum", "actix", "tokio", "sqlalchemy", "gorm", "diesel", "prisma", "opentelemetry", "prometheus"}:
            stack.append(dep)
    return _dedupe(stack)[:12]


def _extract_symbols_ctags(repo_root: Path) -> list[dict[str, Any]]:
    if not _has_cmd("ctags"):
        return []
    cmd = [
        "ctags",
        "--output-format=json",
        "--fields=+n",
        "--extras=+q",
        "--sort=no",
        "--languages=Python,Go,Rust,JavaScript,TypeScript,Swift",
        "--exclude=.git",
        "--exclude=node_modules",
        "--exclude=dist",
        "--exclude=build",
        "--exclude=target",
        "--exclude=codewiki",
        "-R",
        ".",
    ]
    code, output = _run(cmd, cwd=repo_root)
    if code != 0 or not output:
        return []
    symbols: list[dict[str, Any]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        path = data.get("path")
        if not path:
            continue
        symbol = {
            "name": data.get("name"),
            "kind": data.get("kind"),
            "path": path,
            "line": data.get("line"),
        }
        symbols.append(symbol)
        if len(symbols) >= 3000:
            break
    return symbols


def _load_evidence_rules() -> dict[str, Any]:
    data = _load_json(EVIDENCE_RULES_PATH)
    if not data:
        raise RuntimeError(f"Missing evidence rules at {EVIDENCE_RULES_PATH}")
    return data


def _should_exclude(path: Path, repo_root: Path) -> bool:
    """Check if any path component is in EXCLUDE_DIRS."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def _matches_path_glob(repo_root: Path, pattern: str) -> list[str]:
    matches = []
    for path in repo_root.glob(pattern):
        if _should_exclude(path, repo_root):
            continue
        if path.is_file() or path.is_dir():
            try:
                matches.append(str(path.relative_to(repo_root)))
            except ValueError:
                continue
    return matches


def _search_content_regex(files: list[Path], repo_root: Path, pattern: str) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []
    for path in files:
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except UnicodeDecodeError:
            continue
        if regex.search(text):
            matches.append(str(path.relative_to(repo_root)))
    return matches


def analyze_repo(repo_root: Path) -> RepoMeta:
    files = _iter_repo_files(repo_root)
    rel_files = [str(p.relative_to(repo_root)) for p in files]
    languages = _detect_languages(files)

    deps = set()
    if (repo_root / "package.json").exists():
        deps |= _extract_deps_from_package_json(repo_root / "package.json")
    if (repo_root / "pyproject.toml").exists():
        deps |= _extract_deps_from_pyproject(repo_root / "pyproject.toml")
    if (repo_root / "requirements.txt").exists():
        deps |= _extract_deps_from_requirements(repo_root / "requirements.txt")
    if (repo_root / "Cargo.toml").exists():
        deps |= _extract_deps_from_cargo(repo_root / "Cargo.toml")
    if (repo_root / "go.mod").exists():
        deps |= _extract_deps_from_go_mod(repo_root / "go.mod")
    deps |= _extract_deps_from_metadata(repo_root)

    commands = _detect_commands(repo_root)
    entrypoints = _detect_entrypoints(files, repo_root)
    top_dirs = _top_level_dirs(repo_root)
    symbols = _extract_symbols_ctags(repo_root)
    tech_stack = _tech_stack(
        RepoMeta(
            repo_root,
            files,
            rel_files,
            languages,
            deps,
            commands,
            entrypoints,
            top_dirs,
            [],
            symbols,
        )
    )
    return RepoMeta(
        repo_root,
        files,
        rel_files,
        languages,
        deps,
        commands,
        entrypoints,
        top_dirs,
        tech_stack,
        symbols,
    )


def score_modules(meta: RepoMeta, rules: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    modules = rules.get("modules") or {}
    for module, config in modules.items():
        signals = config.get("signals") or []
        score = 0
        evidence = []
        for signal in signals:
            kind = signal.get("type")
            weight = int(signal.get("weight", 0))
            pattern = signal.get("pattern")
            matches: list[str] = []
            if kind == "path_glob" and pattern:
                matches = _matches_path_glob(meta.root, pattern)
            elif kind == "content_regex" and pattern:
                matches = _search_content_regex(meta.files, meta.root, pattern)
            elif kind == "dependency" and pattern:
                if pattern.lower() in meta.deps:
                    matches = [pattern]
            if matches:
                score += weight
                evidence.append({"type": kind, "pattern": pattern, "weight": weight, "matches": matches[:10]})
        threshold = int(config.get("threshold", 60))
        candidate_threshold = int(config.get("candidate_threshold", 40))
        if score >= threshold:
            status = "included"
        elif score >= candidate_threshold:
            status = "candidate"
        else:
            status = "excluded"
        confidence = "low"
        if score >= 80:
            confidence = "high"
        elif score >= 60:
            confidence = "medium"
        result[module] = {
            "score": score,
            "threshold": threshold,
            "candidate_threshold": candidate_threshold,
            "status": status,
            "confidence": confidence,
            "evidence": evidence,
        }
    return result


def build_doc_plan(meta: RepoMeta, module_scores: dict[str, Any]) -> dict[str, Any]:
    pages = []
    for page in REQUIRED_PAGES:
        pages.append({**page, "status": "required", "module": "core"})
    for module, pages_list in MODULE_PAGES.items():
        status = module_scores.get(module, {}).get("status", "excluded")
        if status in {"included", "candidate"}:
            for page in pages_list:
                pages.append({**page, "status": status, "module": module})
    return {
        "repo": meta.root.name,
        "languages": meta.languages,
        "entrypoints": meta.entrypoints,
        "commands": meta.commands,
        "top_dirs": meta.top_dirs,
        "tech_stack": meta.tech_stack,
        "symbol_count": len(meta.symbols),
        "module_scores": module_scores,
        "pages": pages,
    }


def _render_related_code(paths: list[str]) -> str:
    if not paths:
        paths = ["path/to/file"]
    lines = ["```text", "# Related Code"]
    for path in paths[:8]:
        lines.append(f"- `{path}`")
    lines.append("```")
    return "\n".join(lines)


def _render_mermaid_context(project: str, externals: list[str]) -> str:
    nodes = [f"user[User]", f"system[{project}]" ]
    edges = ["user --> system"]
    for idx, ext in enumerate(externals[:3], start=1):
        key = f"ext{idx}"
        nodes.append(f"{key}[{ext}]")
        edges.append(f"system --> {key}")
    lines = ["```mermaid", "graph TD"]
    lines.extend(nodes)
    lines.extend(edges)
    lines.append("```")
    return "\n".join(lines)


def _render_component_graph(project: str, components: list[str]) -> str:
    lines = ["```mermaid", "graph TD", f"core[{project}]" ]
    for comp in components[:8]:
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", comp)
        lines.append(f"{safe}[{comp}]")
        lines.append(f"core --> {safe}")
    lines.append("```")
    return "\n".join(lines)


def _render_sequence(title: str) -> str:
    return "\n".join([
        "```mermaid",
        "sequenceDiagram",
        f"participant User as {title}",
        "participant System",
        "User->>System: Start",
        "System-->>User: Ready",
        "```",
    ])


def _page_intro(status: str) -> str:
    if status == "candidate":
        return "**Confidence: candidate (evidence incomplete). Please verify against code.**"
    return ""


def _write_page(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def generate_docs(out_dir: Path, plan: dict[str, Any], meta: RepoMeta, force: bool) -> None:
    project = plan["repo"]
    externals = [d for d in sorted(meta.deps) if d in {"redis", "postgres", "mysql", "kafka", "s3", "stripe"}]
    components = meta.top_dirs or ["src", "app", "core"]
    key_symbols = [
        s for s in meta.symbols
        if s.get("kind") in {"class", "function", "method", "struct", "interface"}
    ]

    for page in plan["pages"]:
        page_path = out_dir / page["path"]
        status = page.get("status", "required")
        module = page.get("module")
        evidence = []
        if module and module != "core":
            evidence = [m for ev in plan["module_scores"].get(module, {}).get("evidence", []) for m in ev.get("matches", [])]
        related = _render_related_code(evidence)
        intro = _page_intro(status)
        title = page.get("title", "Untitled")

        if page["template"] == "overview":
            content = f"# {title}\n\n{related}\n\n## One-Line Definition\n{intro}\n- {project} is a [type] system that [primary goal].\n\n## Tech Stack Radar\n- " + "\n- ".join(plan["tech_stack"] or ["[fill stack]"]) + "\n\n## System Context Diagram\n" + _render_mermaid_context(project, externals) + "\n\n## Architecture Highlights\n- [Highlight 1]\n- [Highlight 2]\n- [Highlight 3]\n\n## Key Risks / Tech Debt\n- [Risk 1]\n- [Risk 2]\n"
        elif page["template"] == "architecture":
            content = f"# {title}\n\n{related}\n\n## Design Rationale\n{intro}\n- [Why this architecture exists]\n\n## Component Diagram\n" + _render_component_graph(project, components) + "\n\n## Data Flow\n" + _render_mermaid_context(project, externals) + "\n\n## Tech Debt Notes\n- [Debt 1]\n"
        elif page["template"] == "components":
            symbol_lines = []
            for sym in key_symbols[:12]:
                name = sym.get("name") or "[symbol]"
                path = sym.get("path") or "path/to/file"
                line = sym.get("line")
                if line:
                    symbol_lines.append(f"- `{name}` ({path}:{line})")
                else:
                    symbol_lines.append(f"- `{name}` ({path})")
            content = f"# {title}\n\n{related}\n\n## Component Dictionary\n{intro}\n- {project}: [responsibility]\n" + "\n".join(f"- {comp}: [responsibility]" for comp in components[:8]) + "\n\n## Relationship Graph\n" + _render_component_graph(project, components) + "\n"
            if symbol_lines:
                content += "\n## Key Symbols\n" + "\n".join(symbol_lines) + "\n"
        elif page["template"] == "quickstart":
            steps = plan.get("commands") or ["[command]"]
            content = f"# {title}\n\n{related}\n\n## Prerequisites\n{intro}\n- [toolchain]\n\n## Steps\n" + "\n".join(f"1. `{cmd}`" for cmd in steps[:6]) + "\n\n## Expected Output\n- [what success looks like]\n"
        elif page["template"] == "development":
            content = f"# {title}\n\n{related}\n\n## Local Workflow\n{intro}\n" + "\n".join(f"- `{cmd}`" for cmd in (plan.get("commands") or ["[command]"])[:6]) + "\n\n## Debugging Tips\n- [Tip 1]\n\n## Test Strategy\n- [Unit/Integration/E2E]\n"
        elif page["template"] == "api":
            content = f"# {title}\n\n{related}\n\n## API Surface Map\n{intro}\n- [List services/endpoints]\n\n## Authn/Authz\n- [Mechanism]\n\n## Example Request\n```bash\ncurl -X GET https://example.com\n```\n"
        elif page["template"] == "ci":
            content = f"# {title}\n\n{related}\n\n## Pipeline Stages\n{intro}\n- [build]\n- [test]\n- [deploy]\n\n## Artifacts\n- [artifact list]\n"
        elif page["template"] == "release":
            content = f"# {title}\n\n{related}\n\n## Release Steps\n{intro}\n- [step 1]\n- [step 2]\n\n## Release Risks\n- [risk]\n"
        elif page["template"] == "domain":
            content = f"# {title}\n\n{related}\n\n## Domain Entities\n{intro}\n- [Entity A]\n- [Entity B]\n\n## Relationships\n" + _render_component_graph("Domain", components[:4]) + "\n"
        elif page["template"] == "storage":
            content = f"# {title}\n\n{related}\n\n## Storage Layout\n{intro}\n- [Database]\n- [Tables/Collections]\n"
        elif page["template"] == "auth":
            content = f"# {title}\n\n{related}\n\n## Auth Flow\n{intro}\n" + _render_sequence("Client") + "\n\n## Roles & Permissions\n- [Role]\n"
        elif page["template"] == "threat":
            content = f"# {title}\n\n{related}\n\n## Threat Model\n{intro}\n- [Threat]\n- [Mitigation]\n"
        elif page["template"] == "observability":
            content = f"# {title}\n\n{related}\n\n## Signals\n{intro}\n- Logs\n- Metrics\n- Traces\n\n## Dashboards\n- [dashboard]\n"
        elif page["template"] == "runbook":
            content = f"# {title}\n\n{related}\n\n## Operational Playbooks\n{intro}\n- [Scenario]\n- [Action]\n"
        elif page["template"] == "bottlenecks":
            content = f"# {title}\n\n{related}\n\n## Known Bottlenecks\n{intro}\n- [Bottleneck]\n"
        elif page["template"] == "scaling":
            content = f"# {title}\n\n{related}\n\n## Scaling Strategy\n{intro}\n- [Horizontal]\n- [Vertical]\n"
        elif page["template"] == "integrations":
            content = f"# {title}\n\n{related}\n\n## External Services\n{intro}\n- [Service]\n"
        elif page["template"] == "troubleshooting":
            content = f"# {title}\n\n{related}\n\n## Common Issues\n{intro}\n- [Issue]\n- [Fix]\n"
        elif page["template"] == "glossary":
            terms = [t for t in meta.top_dirs if t.isalpha()]
            glossary = "\n".join(f"- **{term}**: [definition]" for term in terms[:12])
            content = f"# {title}\n\n{related}\n\n## Terms\n{intro}\n" + (glossary or "- [Term]: [definition]") + "\n"
        elif page["template"] == "bootstrap":
            content = f"# {title}\n\n{related}\n\n## Startup Sequence\n{intro}\n" + _render_sequence("User") + "\n\n## Key Initialization Steps\n- [Step]\n"
        elif page["template"] == "ux":
            content = f"# {title}\n\n{related}\n\n## UX Model\n{intro}\n- [Persona]\n- [Flow]\n"
        elif page["template"] == "plugins":
            content = f"# {title}\n\n{related}\n\n## Plugin Lifecycle\n{intro}\n- [Load]\n- [Execute]\n- [Unload]\n\n## Extension Points\n- [Hook]\n"
        else:
            content = f"# {title}\n\n{related}\n\n## Notes\n{intro}\n- [Details]\n"

        _write_page(page_path, content, force=force)


def write_meta(out_dir: Path, meta: RepoMeta, plan: dict[str, Any]) -> None:
    meta_dir = out_dir / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "symbols.json").write_text(json.dumps(meta.symbols, indent=2) + "\n", encoding="utf-8")
    (meta_dir / "deps.json").write_text(json.dumps(sorted(meta.deps), indent=2) + "\n", encoding="utf-8")
    (meta_dir / "entrypoints.json").write_text(json.dumps(meta.entrypoints, indent=2) + "\n", encoding="utf-8")
    (meta_dir / "evidence.json").write_text(json.dumps(plan.get("module_scores"), indent=2) + "\n", encoding="utf-8")
    (meta_dir / "doc_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")


def write_quality_report(out_dir: Path, plan: dict[str, Any]) -> None:
    lines = ["# Quality Report", ""]
    lines.append(f"## Symbols\n- Extracted symbols: {plan.get('symbol_count', 0)}")
    lines.append("\n## Module Coverage")
    for module, score in plan["module_scores"].items():
        lines.append(f"- **{module}**: {score['status']} (score {score['score']}, confidence {score['confidence']})")
    lines.append("\n## Low-Confidence Pages")
    for page in plan["pages"]:
        if page.get("status") == "candidate":
            lines.append(f"- {page['path']} (candidate)")
    lines.append("\n## Missing Evidence")
    for module, score in plan["module_scores"].items():
        if score["status"] == "excluded":
            lines.append(f"- {module}: no strong evidence")
    (out_dir / "quality-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_bootstrap(repo_root: Path, out_dir: Path, force: bool, language: str) -> None:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "codewiki_bootstrap.py"),
        "--repo-root",
        str(repo_root),
        "--out-dir",
        str(out_dir),
        "--language",
        language,
    ]
    if force:
        cmd.append("--force")
    subprocess.run(cmd, check=False)


def refresh_sidebar(repo_root: Path, out_dir: Path, language: str) -> None:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "codewiki_bootstrap.py"),
        "--repo-root",
        str(repo_root),
        "--out-dir",
        str(out_dir),
        "--refresh-sidebar",
        "--language",
        language,
    ]
    subprocess.run(cmd, check=False)


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()

    if not args.no_bootstrap:
        run_bootstrap(repo_root, out_dir, force=args.force, language=args.language)

    meta = analyze_repo(repo_root)
    rules = _load_evidence_rules()
    module_scores = score_modules(meta, rules)
    plan = build_doc_plan(meta, module_scores)

    write_meta(out_dir, meta, plan)

    if not args.analyze_only and not args.no_write_docs:
        generate_docs(out_dir, plan, meta, force=args.force)
        write_quality_report(out_dir, plan)

    if args.refresh_sidebar:
        refresh_sidebar(repo_root, out_dir, language=args.language)


if __name__ == "__main__":
    main()
