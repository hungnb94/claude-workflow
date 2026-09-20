#!/usr/bin/env python3
"""
Unit tests for scripts/bump-version.py.
Tests all parsing scenarios, SemVer calculations, manifest synchronization,
CLI arguments, and integration with scripts/verify-integrity.py.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

# Locate root directory and load bump-version module
ROOT_DIR = Path(__file__).resolve().parent.parent
BUMP_SCRIPT_PATH = ROOT_DIR / "scripts" / "bump-version.py"

spec = importlib.util.spec_from_file_location("bump_version", BUMP_SCRIPT_PATH)
bv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bv)

# Also load verify-integrity module for integration verification
VI_SCRIPT_PATH = ROOT_DIR / "scripts" / "verify-integrity.py"
vi_spec = importlib.util.spec_from_file_location("verify_integrity", VI_SCRIPT_PATH)
vi = importlib.util.module_from_spec(vi_spec)
vi_spec.loader.exec_module(vi)


class TestBumpVersion(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.test_dir)

        # Setup minimal plugin structure
        plugin_dir = self.repo_root / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        self.plugin_json_data = {
            "name": "claude-workflow",
            "version": "1.0.0",
            "description": "Six-phase structured agent workflows",
            "author": {
                "name": "Hung Nguyen",
                "email": "hungnb94@gmail.com"
            }
        }
        (plugin_dir / "plugin.json").write_text(
            json.dumps(self.plugin_json_data, indent=2) + "\n",
            encoding="utf-8"
        )

        self.marketplace_json_data = {
            "name": "claude-workflow",
            "plugins": [
                {
                    "name": "claude-workflow",
                    "source": {
                        "source": "github",
                        "repo": "hungnb94/claude-workflow"
                    },
                    "version": "1.0.0",
                    "description": "Six-phase structured agent workflows"
                }
            ]
        }
        (plugin_dir / "marketplace.json").write_text(
            json.dumps(self.marketplace_json_data, indent=2) + "\n",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Conventional Commits Parsing Tests
    # -------------------------------------------------------------------------

    def test_parse_conventional_commit_major_exclamation(self):
        bump, reason = bv.parse_conventional_commit("feat!: breaking api change")
        self.assertEqual(bump, "major")
        self.assertIn("Breaking change", reason)

    def test_parse_conventional_commit_major_scoped_exclamation(self):
        bump, reason = bv.parse_conventional_commit("fix(core)!: change parameter types")
        self.assertEqual(bump, "major")
        self.assertIn("Breaking change", reason)

    def test_parse_conventional_commit_major_body(self):
        bump, reason = bv.parse_conventional_commit(
            title="refactor: overhaul state engine",
            body="Some details.\n\nBREAKING CHANGE: config format altered"
        )
        self.assertEqual(bump, "major")
        self.assertIn("BREAKING CHANGE footer", reason)

    def test_parse_conventional_commit_major_body_dash(self):
        bump, reason = bv.parse_conventional_commit(
            title="refactor: overhaul state engine",
            body="Notes.\nBREAKING-CHANGE: protocol changed completely"
        )
        self.assertEqual(bump, "major")
        self.assertIn("BREAKING CHANGE footer", reason)

    def test_parse_conventional_commit_minor(self):
        bump, reason = bv.parse_conventional_commit("feat: add new subagent")
        self.assertEqual(bump, "minor")
        self.assertIn("minor", reason)

    def test_parse_conventional_commit_minor_scoped(self):
        bump, reason = bv.parse_conventional_commit("feat(skills): add generic task workflow")
        self.assertEqual(bump, "minor")
        self.assertIn("minor", reason)

    def test_parse_conventional_commit_patch_fix(self):
        bump, reason = bv.parse_conventional_commit("fix: resolve manifest parsing bug")
        self.assertEqual(bump, "patch")
        self.assertIn("patch", reason)

    def test_parse_conventional_commit_patch_perf(self):
        bump, reason = bv.parse_conventional_commit("perf(cache): optimize token budget check")
        self.assertEqual(bump, "patch")
        self.assertIn("patch", reason)

    def test_parse_conventional_commit_patch_refactor(self):
        bump, reason = bv.parse_conventional_commit("refactor: simplify arg parsing")
        self.assertEqual(bump, "patch")
        self.assertIn("patch", reason)

    def test_parse_conventional_commit_patch_revert(self):
        bump, reason = bv.parse_conventional_commit("revert: revert previous commit")
        self.assertEqual(bump, "patch")
        self.assertIn("patch", reason)

    def test_parse_conventional_commit_skip_types(self):
        skip_examples = [
            "docs: update readme",
            "docs(agents): document permissions",
            "chore: clean temp files",
            "chore(deps): bump actions",
            "ci: update workflow",
            "test: add unit tests",
            "style: format markdown",
            "build: update build config",
        ]
        for title in skip_examples:
            bump, reason = bv.parse_conventional_commit(title)
            self.assertEqual(bump, "skip", f"Expected skip for '{title}', got '{bump}'")
            self.assertIn("does not trigger a release", reason)

    def test_parse_conventional_commit_skip_label(self):
        # When label 'skip-release' is present, even feat should skip
        bump, reason = bv.parse_conventional_commit(
            title="feat: feature without release",
            labels=["skip-release"]
        )
        self.assertEqual(bump, "skip")
        self.assertIn("skip-release", reason)

        # When label 'no-release' is present
        bump, reason = bv.parse_conventional_commit(
            title="fix: urgent bug fix without release",
            labels=["no-release", "bug"]
        )
        self.assertEqual(bump, "skip")
        self.assertIn("no-release", reason)

    def test_parse_labels_arg_formats(self):
        self.assertEqual(bv.parse_labels_arg(None), [])
        self.assertEqual(bv.parse_labels_arg(""), [])
        self.assertEqual(bv.parse_labels_arg("a, b, c"), ["a", "b", "c"])
        self.assertEqual(bv.parse_labels_arg('["skip-release", "enhancement"]'), ["skip-release", "enhancement"])
        self.assertEqual(bv.parse_labels_arg(["label1", "label2"]), ["label1", "label2"])

    def test_parse_conventional_commit_invalid_title(self):
        with self.assertRaises(ValueError):
            bv.parse_conventional_commit("not a conventional commit title")

    def test_parse_conventional_commit_unrecognized_type(self):
        with self.assertRaises(ValueError):
            bv.parse_conventional_commit("unknown(core): something strange")

    def test_parse_conventional_commit_override(self):
        bump, reason = bv.parse_conventional_commit(bump_override="major")
        self.assertEqual(bump, "major")
        self.assertIn("override", reason)

        bump, reason = bv.parse_conventional_commit(bump_override="patch")
        self.assertEqual(bump, "patch")

        with self.assertRaises(ValueError):
            bv.parse_conventional_commit(bump_override="invalid_bump")

    # -------------------------------------------------------------------------
    # SemVer Calculation Tests
    # -------------------------------------------------------------------------

    def test_calculate_next_version(self):
        # Major
        self.assertEqual(bv.calculate_next_version("1.0.0", "major"), "2.0.0")
        self.assertEqual(bv.calculate_next_version("1.2.3", "major"), "2.0.0")
        # Minor
        self.assertEqual(bv.calculate_next_version("1.0.0", "minor"), "1.1.0")
        self.assertEqual(bv.calculate_next_version("1.2.3", "minor"), "1.3.0")
        # Patch
        self.assertEqual(bv.calculate_next_version("1.0.0", "patch"), "1.0.1")
        self.assertEqual(bv.calculate_next_version("1.2.3", "patch"), "1.2.4")
        # Skip
        self.assertEqual(bv.calculate_next_version("1.0.0", "skip"), "1.0.0")
        self.assertEqual(bv.calculate_next_version("1.2.3", "skip"), "1.2.3")

    def test_calculate_next_version_invalid_base(self):
        with self.assertRaises(ValueError):
            bv.calculate_next_version("invalid", "minor")

    def test_calculate_next_version_invalid_bump(self):
        with self.assertRaises(ValueError):
            bv.calculate_next_version("1.0.0", "super-major")

    # -------------------------------------------------------------------------
    # Base Version Resolution Tests
    # -------------------------------------------------------------------------

    def test_get_base_version_fallback(self):
        # In a repo without git tags, fallback to plugin.json
        base = bv.get_base_version(self.repo_root)
        self.assertEqual(base, "1.0.0")

    def test_get_base_version_from_git_tags(self):
        # Initialize a git repository with mock tags
        subprocess.run(["git", "init", "-b", "main"], cwd=str(self.repo_root), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "add", "."], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(self.repo_root), check=True, capture_output=True)

        subprocess.run(["git", "tag", "v1.0.0"], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "tag", "v1.2.0"], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "tag", "v1.1.5"], cwd=str(self.repo_root), check=True)

        base = bv.get_base_version(self.repo_root)
        self.assertEqual(base, "1.2.0")

    # -------------------------------------------------------------------------
    # Manifest Update Tests
    # -------------------------------------------------------------------------

    def test_update_manifests(self):
        bv.update_manifests(self.repo_root, "2.3.4")

        # Check plugin.json
        plugin_file = self.repo_root / ".claude-plugin" / "plugin.json"
        p_data = json.loads(plugin_file.read_text(encoding="utf-8"))
        self.assertEqual(p_data["version"], "2.3.4")
        self.assertEqual(p_data["name"], "claude-workflow")
        self.assertEqual(p_data["author"]["name"], "Hung Nguyen")

        # Check marketplace.json
        mp_file = self.repo_root / ".claude-plugin" / "marketplace.json"
        m_data = json.loads(mp_file.read_text(encoding="utf-8"))
        self.assertEqual(m_data["plugins"][0]["version"], "2.3.4")
        self.assertEqual(m_data["plugins"][0]["name"], "claude-workflow")
        self.assertEqual(m_data["plugins"][0]["source"]["source"], "github")

        # Check formatting: trailing newline and 2-space indent
        p_raw = plugin_file.read_text(encoding="utf-8")
        self.assertTrue(p_raw.endswith("\n"))
        self.assertIn('  "version": "2.3.4"', p_raw)

    def test_update_manifests_missing_file_raises(self):
        (self.repo_root / ".claude-plugin" / "plugin.json").unlink()
        with self.assertRaises(FileNotFoundError):
            bv.update_manifests(self.repo_root, "1.1.0")

    def test_update_manifests_fallback_with_warning(self):
        # Change plugin name in plugin.json to something not matching marketplace.json
        plugin_file = self.repo_root / ".claude-plugin" / "plugin.json"
        p_data = json.loads(plugin_file.read_text(encoding="utf-8"))
        p_data["name"] = "different-plugin-name"
        plugin_file.write_text(json.dumps(p_data, indent=2) + "\n", encoding="utf-8")

        # Capture stderr to verify warning
        import io
        from unittest.mock import patch
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            bv.update_manifests(self.repo_root, "3.0.0")

        mp_file = self.repo_root / ".claude-plugin" / "marketplace.json"
        m_data = json.loads(mp_file.read_text(encoding="utf-8"))
        self.assertEqual(m_data["plugins"][0]["version"], "3.0.0")
        self.assertIn("[WARN] Plugin 'different-plugin-name' not found by name", stderr_capture.getvalue())

    # -------------------------------------------------------------------------
    # CLI Tests
    # -------------------------------------------------------------------------

    def test_cli_dry_run(self):
        exit_code = bv.main([
            "--pr-title", "feat: add feature",
            "--repo-root", str(self.repo_root),
            "--write-manifests",
            "--dry-run"
        ])
        self.assertEqual(exit_code, 0)
        # Verify file was NOT modified
        p_data = json.loads((self.repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(p_data["version"], "1.0.0")

    def test_cli_write_manifests(self):
        exit_code = bv.main([
            "--pr-title", "feat: add feature",
            "--repo-root", str(self.repo_root),
            "--write-manifests"
        ])
        self.assertEqual(exit_code, 0)
        # Verify file WAS modified
        p_data = json.loads((self.repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(p_data["version"], "1.1.0")

    def test_cli_github_output(self):
        output_file = self.repo_root / "github_output.txt"
        exit_code = bv.main([
            "--pr-title", "feat: add feature",
            "--repo-root", str(self.repo_root),
            "--github-output", str(output_file)
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("should_release=true", content)
        self.assertIn("bump_type=minor", content)
        self.assertIn("base_version=1.0.0", content)
        self.assertIn("next_version=1.1.0", content)
        self.assertIn("release_tag=v1.1.0", content)

    def test_cli_skip_release_github_output(self):
        output_file = self.repo_root / "github_output.txt"
        exit_code = bv.main([
            "--pr-title", "docs: update readme",
            "--repo-root", str(self.repo_root),
            "--github-output", str(output_file)
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("should_release=false", content)
        self.assertIn("bump_type=skip", content)
        self.assertIn("next_version=", content)

    def test_cli_bump_type_override(self):
        exit_code = bv.main([
            "--bump-type", "major",
            "--repo-root", str(self.repo_root),
            "--write-manifests"
        ])
        self.assertEqual(exit_code, 0)
        p_data = json.loads((self.repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(p_data["version"], "2.0.0")

    def test_cli_no_args_error(self):
        exit_code = bv.main(["--repo-root", str(self.repo_root)])
        self.assertEqual(exit_code, 1)

    # -------------------------------------------------------------------------
    # Integration with verify-integrity.py
    # -------------------------------------------------------------------------

    def test_integration_bump_and_verify(self):
        # 1. Bump version to 1.1.0
        exit_code = bv.main([
            "--pr-title", "feat: new feature",
            "--repo-root", str(self.repo_root),
            "--write-manifests"
        ])
        self.assertEqual(exit_code, 0)

        # 2. Run verify-integrity version sync check with matching check-tag
        self.assertTrue(vi.check_version_sync(self.repo_root, check_tag="v1.1.0"))

        # 3. Verify that check-tag with wrong version fails
        self.assertFalse(vi.check_version_sync(self.repo_root, check_tag="v1.0.0"))


if __name__ == "__main__":
    unittest.main()
