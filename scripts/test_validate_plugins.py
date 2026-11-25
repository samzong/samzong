from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("validate_plugins", HERE / "validate_plugins.py")
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def create_fixture(
    root: Path,
    *,
    marketplace_version: str = "1.5.0",
    claude_version: str = "1.5.0",
    codex_version: str | None = "1.5.0",
    plugin_name: str = "steward",
    include_agents_marketplace: bool = True,
) -> None:
    write_json(
        root / ".claude-plugin" / "marketplace.json",
        {
            "name": "samzong",
            "owner": {"name": "samzong"},
            "plugins": [
                {
                    "name": plugin_name,
                    "source": f"./plugins/{plugin_name}",
                    "description": "Plugin fixture",
                    "version": marketplace_version,
                }
            ],
        },
    )
    write_json(
        root / "plugins" / plugin_name / ".claude-plugin" / "plugin.json",
        {
            "name": plugin_name,
            "version": claude_version,
            "description": "Plugin fixture",
            "author": {"name": "samzong"},
        },
    )
    if codex_version is not None:
        write_json(
            root / "plugins" / plugin_name / ".codex-plugin" / "plugin.json",
            {
                "name": plugin_name,
                "version": codex_version,
                "description": "Plugin fixture for Codex",
                "author": {"name": "samzong"},
            },
        )
    if include_agents_marketplace:
        write_json(
            root / ".agents" / "plugins" / "marketplace.json",
            {
                "name": "samzong",
                "plugins": [
                    {
                        "name": plugin_name,
                        "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
                    }
                ],
            },
        )


class ValidatePluginsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HERE / "validate_plugins.py"), "--root", str(self.root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_parity_and_final_tag_outputs(self) -> None:
        create_fixture(self.root)
        output_file = self.root / "github_output.txt"
        result = self.run_cli("--tag", "steward--v1.5.0", "--github-output", str(output_file))
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = dict(line.split("=", 1) for line in output_file.read_text(encoding="utf-8").splitlines())
        self.assertEqual(
            outputs,
            {"plugin": "steward", "version": "1.5.0", "stage": "latest", "is_prerelease": "false"},
        )

    def test_valid_prerelease_tag_outputs(self) -> None:
        for stage in ("alpha", "beta", "rc"):
            with self.subTest(stage=stage):
                sub_root = self.root / stage
                ver = f"1.6.0-{stage}.2"
                create_fixture(sub_root, marketplace_version=ver, claude_version=ver, codex_version=ver)
                output_file = sub_root / "github_output.txt"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(HERE / "validate_plugins.py"),
                        "--root",
                        str(sub_root),
                        "--tag",
                        f"steward--v{ver}",
                        "--github-output",
                        str(output_file),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs = dict(line.split("=", 1) for line in output_file.read_text(encoding="utf-8").splitlines())
                self.assertEqual(
                    outputs,
                    {"plugin": "steward", "version": ver, "stage": stage, "is_prerelease": "true"},
                )

    def test_rejects_marketplace_plugin_version_drift(self) -> None:
        create_fixture(self.root, marketplace_version="1.4.0", claude_version="1.5.0", codex_version="1.5.0")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("1.4.0", result.stderr)
        self.assertIn("1.5.0", result.stderr)

    def test_rejects_codex_manifest_version_drift(self) -> None:
        create_fixture(self.root, marketplace_version="1.5.0", claude_version="1.5.0", codex_version="1.4.0")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".codex-plugin/plugin.json", result.stderr)

    def test_rejects_invalid_semver_versions_and_tags(self) -> None:
        create_fixture(self.root)
        invalid_tags = (
            "steward--v1.5.0-fix.1",
            "steward--v01.5.0",
            "steward--v1.5.0-rc.0",
            "steward--v1.5.0-rc1",
            "steward--v1.5.0+build.1",
            "v1.5.0",
            "steward-v1.5.0",
        )
        for tag in invalid_tags:
            with self.subTest(tag=tag):
                result = self.run_cli("--tag", tag)
                self.assertNotEqual(result.returncode, 0, f"Expected failure for {tag}")

        invalid_manifest_versions = ("01.5.0", "1.5.0-fix.1", "v1.5.0", "1.5")
        for version in invalid_manifest_versions:
            with self.subTest(version=version):
                sub_root = self.root / version.replace("/", "_")
                create_fixture(sub_root, marketplace_version=version, claude_version=version, codex_version=version)
                errors, _, _ = VALIDATOR.validate_repository(sub_root)
                self.assertTrue(errors, f"Expected errors for {version}")

    def test_rejects_tag_manifest_mismatch(self) -> None:
        create_fixture(self.root, marketplace_version="1.5.0", claude_version="1.5.0", codex_version="1.5.0")
        result = self.run_cli("--tag", "steward--v1.6.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("1.6.0", result.stderr)

    def test_rejects_unregistered_plugin_dir_and_bad_source(self) -> None:
        create_fixture(self.root)
        write_json(
            self.root / "plugins" / "extra" / ".claude-plugin" / "plugin.json",
            {"name": "extra", "version": "0.1.0"},
        )
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unregistered plugin directory: plugins/extra", result.stderr)

        bad_root = self.root / "bad_source"
        create_fixture(bad_root)
        write_json(
            bad_root / ".claude-plugin" / "marketplace.json",
            {
                "name": "samzong",
                "owner": {"name": "samzong"},
                "plugins": [
                    {
                        "name": "steward",
                        "source": "../outside",
                        "description": "Escape",
                        "version": "1.5.0",
                    }
                ],
            },
        )
        errors, _, _ = VALIDATOR.validate_repository(bad_root)
        self.assertTrue(any("escapes repository root" in err for err in errors))

    def test_rejects_symlink_and_broken_codex_symlink(self) -> None:
        outside = self.root / "outside.json"
        write_json(outside, {"name": "SECRET_NAME", "version": "9.9.9"})

        sym_manifest_root = self.root / "sym_manifest"
        create_fixture(sym_manifest_root)
        claude_manifest = sym_manifest_root / "plugins" / "steward" / ".claude-plugin" / "plugin.json"
        claude_manifest.unlink()
        claude_manifest.symlink_to(outside)
        errors, _, _ = VALIDATOR.validate_repository(sym_manifest_root)
        self.assertTrue(any("Symlink component" in err for err in errors))
        self.assertFalse(any("SECRET_NAME" in err or "9.9.9" in err for err in errors))

        broken_codex_root = self.root / "broken_codex"
        create_fixture(broken_codex_root)
        codex_manifest = broken_codex_root / "plugins" / "steward" / ".codex-plugin" / "plugin.json"
        codex_manifest.unlink()
        codex_manifest.symlink_to(self.root / "does_not_exist.json")
        errors, _, _ = VALIDATOR.validate_repository(broken_codex_root)
        self.assertTrue(any("Symlink component" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
