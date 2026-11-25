#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(alpha|beta|rc)\.([1-9][0-9]*))?$"
)
TAG_RE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)--v(.+)$")


def load_json_object(path: Path, label: str, errors: list[str]) -> dict[str, object] | None:
    if not path.is_file():
        errors.append(f"Missing {label}: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON in {label} ({path}): {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"Expected JSON object in {label}: {path}")
        return None
    return data


def validate_semver(value: object, label: str, errors: list[str]) -> re.Match[str] | None:
    if not isinstance(value, str) or not value:
        errors.append(f"Missing or non-string version in {label}")
        return None
    match = SEMVER_RE.fullmatch(value)
    if not match:
        errors.append(f"Invalid SemVer version in {label}: {value!r}")
        return None
    return match


def resolve_within_root(root: Path, raw_source: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_source, str) or not raw_source:
        errors.append(f"Missing or invalid source in {label}")
        return None
    resolved = (root / raw_source).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        errors.append(f"Source path escapes repository root in {label}: {raw_source!r}")
        return None
    return resolved


def validate_marketplace(root: Path, errors: list[str]) -> dict[str, dict[str, object]]:
    registered: dict[str, dict[str, object]] = {}
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    marketplace = load_json_object(marketplace_path, ".claude-plugin/marketplace.json", errors)
    if marketplace is None:
        return registered

    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or not entries:
        errors.append(".claude-plugin/marketplace.json must contain a non-empty plugins list")
        return registered

    for idx, entry in enumerate(entries):
        entry_label = f".claude-plugin/marketplace.json plugins[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label} must be a JSON object")
            continue

        name = entry.get("name")
        if not isinstance(name, str) or not PLUGIN_NAME_RE.fullmatch(name):
            errors.append(f"Invalid plugin name in {entry_label}: {name!r}")
            continue
        if name in registered:
            errors.append(f"Duplicate plugin entry in .claude-plugin/marketplace.json: {name}")
            continue

        marketplace_version = entry.get("version")
        validate_semver(marketplace_version, f".claude-plugin/marketplace.json ({name})", errors)

        expected_dir = (root / "plugins" / name).resolve()
        source_dir = resolve_within_root(root, entry.get("source"), f".claude-plugin/marketplace.json ({name})", errors)
        if source_dir is not None and source_dir != expected_dir:
            errors.append(
                f"Marketplace source for {name} resolves to {source_dir}, expected {expected_dir}"
            )
        if not expected_dir.is_dir():
            errors.append(f"Plugin directory does not exist for {name}: {expected_dir}")
            registered[name] = {
                "marketplace_version": marketplace_version,
                "claude_version": None,
                "codex_version": None,
                "has_codex": False,
            }
            continue

        claude_rel = f"plugins/{name}/.claude-plugin/plugin.json"
        claude_manifest = load_json_object(expected_dir / ".claude-plugin" / "plugin.json", claude_rel, errors)
        claude_version: object = None
        if claude_manifest is not None:
            if claude_manifest.get("name") != name:
                errors.append(
                    f"Plugin name mismatch in {claude_rel}: {claude_manifest.get('name')!r} != {name!r}"
                )
            claude_version = claude_manifest.get("version")
            if validate_semver(claude_version, claude_rel, errors) is not None:
                if isinstance(marketplace_version, str) and claude_version != marketplace_version:
                    errors.append(
                        f"Version mismatch for {name}: .claude-plugin/marketplace.json has {marketplace_version!r}, {claude_rel} has {claude_version!r}"
                    )

        codex_path = expected_dir / ".codex-plugin" / "plugin.json"
        codex_rel = f"plugins/{name}/.codex-plugin/plugin.json"
        codex_version: object = None
        has_codex = codex_path.exists()
        if has_codex:
            codex_manifest = load_json_object(codex_path, codex_rel, errors)
            if codex_manifest is not None:
                if codex_manifest.get("name") != name:
                    errors.append(
                        f"Plugin name mismatch in {codex_rel}: {codex_manifest.get('name')!r} != {name!r}"
                    )
                codex_version = codex_manifest.get("version")
                if validate_semver(codex_version, codex_rel, errors) is not None:
                    if isinstance(claude_version, str) and codex_version != claude_version:
                        errors.append(
                            f"Version mismatch for {name}: {claude_rel} has {claude_version!r}, {codex_rel} has {codex_version!r}"
                        )
                    elif isinstance(marketplace_version, str) and codex_version != marketplace_version:
                        errors.append(
                            f"Version mismatch for {name}: .claude-plugin/marketplace.json has {marketplace_version!r}, {codex_rel} has {codex_version!r}"
                        )

        registered[name] = {
            "marketplace_version": marketplace_version,
            "claude_version": claude_version,
            "codex_version": codex_version,
            "has_codex": has_codex,
        }

    return registered


def validate_plugins_dir(root: Path, registered: dict[str, dict[str, object]], errors: list[str]) -> None:
    plugins_dir = root / "plugins"
    if not plugins_dir.is_dir():
        errors.append(f"Missing plugins directory: {plugins_dir}")
        return
    for child in sorted(plugins_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name not in registered:
            errors.append(f"Unregistered plugin directory: plugins/{child.name}")


def validate_agents_marketplace(root: Path, registered: dict[str, dict[str, object]], errors: list[str]) -> None:
    agents_path = root / ".agents" / "plugins" / "marketplace.json"
    if not agents_path.exists():
        return
    agents_marketplace = load_json_object(agents_path, ".agents/plugins/marketplace.json", errors)
    if agents_marketplace is None:
        return
    entries = agents_marketplace.get("plugins")
    if not isinstance(entries, list):
        errors.append(".agents/plugins/marketplace.json must contain a plugins list")
        return

    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        entry_label = f".agents/plugins/marketplace.json plugins[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label} must be a JSON object")
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not PLUGIN_NAME_RE.fullmatch(name):
            errors.append(f"Invalid plugin name in {entry_label}: {name!r}")
            continue
        if name in seen:
            errors.append(f"Duplicate plugin entry in .agents/plugins/marketplace.json: {name}")
            continue
        seen.add(name)
        if name not in registered:
            errors.append(f"Plugin {name} in .agents/plugins/marketplace.json is missing from .claude-plugin/marketplace.json")
            continue

        raw_source = entry.get("source")
        raw_path: object = None
        if isinstance(raw_source, dict):
            if raw_source.get("source") != "local":
                errors.append(f"Expected local source in {entry_label} for {name}")
            raw_path = raw_source.get("path")
        elif isinstance(raw_source, str):
            raw_path = raw_source
        source_dir = resolve_within_root(root, raw_path, f".agents/plugins/marketplace.json ({name})", errors)
        expected_dir = (root / "plugins" / name).resolve()
        if source_dir is not None and source_dir != expected_dir:
            errors.append(
                f"Agents marketplace source for {name} resolves to {source_dir}, expected {expected_dir}"
            )

    for name, info in registered.items():
        if info["has_codex"] and name not in seen:
            errors.append(f"Codex plugin {name} is missing from .agents/plugins/marketplace.json")


def validate_release_tag(
    tag: str, registered: dict[str, dict[str, object]], errors: list[str]
) -> dict[str, str] | None:
    tag_match = TAG_RE.fullmatch(tag)
    if not tag_match:
        errors.append(f"Invalid plugin release tag format {tag!r}; expected <plugin>--v<semver>")
        return None
    plugin, tag_version = tag_match.groups()
    semver_match = SEMVER_RE.fullmatch(tag_version)
    if not semver_match:
        errors.append(f"Invalid SemVer version in release tag {tag!r}: {tag_version!r}")
        return None
    if plugin not in registered:
        errors.append(f"Release tag plugin {plugin!r} is not registered in .claude-plugin/marketplace.json")
        return None

    info = registered[plugin]
    if info["marketplace_version"] != tag_version:
        errors.append(
            f"Tag {tag!r} version {tag_version!r} does not match .claude-plugin/marketplace.json version {info['marketplace_version']!r}"
        )
    if info["claude_version"] != tag_version:
        errors.append(
            f"Tag {tag!r} version {tag_version!r} does not match plugins/{plugin}/.claude-plugin/plugin.json version {info['claude_version']!r}"
        )
    if info["has_codex"] and info["codex_version"] != tag_version:
        errors.append(
            f"Tag {tag!r} version {tag_version!r} does not match plugins/{plugin}/.codex-plugin/plugin.json version {info['codex_version']!r}"
        )

    stage = semver_match.group(4) or "latest"
    is_prerelease = "true" if semver_match.group(4) else "false"
    return {
        "plugin": plugin,
        "version": tag_version,
        "stage": stage,
        "is_prerelease": is_prerelease,
    }


def validate_repository(root: Path, tag: str | None = None) -> tuple[list[str], dict[str, str] | None, int]:
    root = root.resolve()
    errors: list[str] = []
    registered = validate_marketplace(root, errors)
    validate_plugins_dir(root, registered, errors)
    validate_agents_marketplace(root, registered, errors)
    tag_meta = validate_release_tag(tag, registered, errors) if tag is not None else None
    return errors, tag_meta, len(registered)


def write_github_output(output_path: Path, tag_meta: dict[str, str]) -> None:
    lines = [
        f"plugin={tag_meta['plugin']}",
        f"version={tag_meta['version']}",
        f"stage={tag_meta['stage']}",
        f"is_prerelease={tag_meta['is_prerelease']}",
    ]
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate plugin manifest parity and SemVer tags.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tag")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)

    if args.github_output is not None and args.tag is None:
        parser.error("--github-output requires --tag")

    errors, tag_meta, plugin_count = validate_repository(args.root, args.tag)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.github_output is not None and tag_meta is not None:
        write_github_output(args.github_output, tag_meta)

    if tag_meta is not None:
        print(
            f"OK: {plugin_count} plugin(s) validated; tag {args.tag} matches {tag_meta['plugin']} {tag_meta['version']} (stage={tag_meta['stage']}, prerelease={tag_meta['is_prerelease']})"
        )
    else:
        print(f"OK: {plugin_count} plugin(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
