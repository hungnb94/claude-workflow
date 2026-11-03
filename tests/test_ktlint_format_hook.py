#!/usr/bin/env python3
"""Tests for hooks/ktlint-format.sh and its hooks.json entry using a fake ktlint on an isolated PATH."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / "hooks" / "ktlint-format.sh"
HOOKS_JSON = ROOT_DIR / "hooks" / "hooks.json"
SH = shutil.which("sh")
TOOLS = ("jq", "cat", "awk")
HEADER = "ktlint could not autocorrect {}:\n"


class KtlintHookCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.bin = self.tmp / "bin"
        self.proj = self.tmp / "project"
        self.log = self.tmp / "calls.log"
        self.bin.mkdir()
        self.proj.mkdir()
        for tool in TOOLS:
            real = shutil.which(tool)
            if real is None:
                self.skipTest(f"{tool} not available")
            (self.bin / tool).symlink_to(real)

    def fake_ktlint(self, where, exit_code=0, lines=0):
        body = (
            "#!/bin/sh\n"
            f'printf \'%s\\n\' "$0 $*" >> "{self.log}"\n'
            f"i=1\nwhile [ \"$i\" -le {lines} ]; do echo \"violation $i\"; i=$((i + 1)); done\n"
            f"exit {exit_code}\n"
        )
        where.write_text(body, encoding="utf-8")
        where.chmod(0o755)
        return where

    def make_file(self, name, content="fun main() {}\n"):
        path = self.proj / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def run_hook(self, payload, project_dir=True, drop_tools=()):
        env = {"PATH": str(self.bin)}
        if project_dir:
            env["CLAUDE_PROJECT_DIR"] = str(self.proj)
        for tool in drop_tools:
            (self.bin / tool).unlink()
        stdin = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(
            [SH, str(SCRIPT)], input=stdin, env=env,
            capture_output=True, text=True, timeout=10,
        )

    def payload(self, file_path, **extra):
        return {"tool_input": {"file_path": str(file_path)}, **extra}

    def assertSilent(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))


class TestFiltering(KtlintHookCase):
    def test_non_kotlin_file_is_ignored(self):
        self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("Main.java")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [])

    def test_kt_file_is_formatted_once_without_extra_flags(self):
        ktlint = self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [f"{ktlint} --format {path}"])

    def test_relative_kts_resolves_against_project_dir(self):
        ktlint = self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("build.gradle.kts")
        self.assertSilent(self.run_hook(self.payload("build.gradle.kts")))
        self.assertEqual(self.calls(), [f"{ktlint} --format {path}"])

    def test_leading_dash_name_is_passed_as_absolute_path(self):
        ktlint = self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("-Weird.kt")
        self.assertSilent(self.run_hook(self.payload("-Weird.kt")))
        self.assertEqual(self.calls(), [f"{ktlint} --format {path}"])

    def test_glob_characters_in_path_are_ignored(self):
        self.fake_ktlint(self.bin / "ktlint")
        for name in ("Foo[1].kt", "Foo*.kt", "Foo?.kt", "Foo{a}.kt"):
            with self.subTest(name=name):
                path = self.make_file(name)
                self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [])


class TestBinaryLookup(KtlintHookCase):
    def test_path_wins_over_project_binary(self):
        on_path = self.fake_ktlint(self.bin / "ktlint")
        self.fake_ktlint(self.proj / "ktlint")
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [f"{on_path} --format {path}"])

    def test_project_binary_is_used_when_not_on_path(self):
        local = self.fake_ktlint(self.proj / "ktlint")
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [f"{local} --format {path}"])

    def test_project_dir_falls_back_to_cwd_in_input(self):
        local = self.fake_ktlint(self.proj / "ktlint")
        path = self.make_file("App.kt")
        result = self.run_hook(self.payload("App.kt", cwd=str(self.proj)), project_dir=False)
        self.assertSilent(result)
        self.assertEqual(self.calls(), [f"{local} --format {path}"])

    def test_relative_path_resolves_against_input_cwd(self):
        ktlint = self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("sub/App.kt")
        result = self.run_hook(self.payload("App.kt", cwd=str(self.proj / "sub")))
        self.assertSilent(result)
        self.assertEqual(self.calls(), [f"{ktlint} --format {path}"])

    def test_missing_project_dir_falls_back_to_file_dir(self):
        ktlint = self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("App.kt")
        env_proj, self.proj = self.proj, self.tmp / "gone"
        try:
            result = self.run_hook(self.payload(path))
        finally:
            self.proj = env_proj
        self.assertSilent(result)
        self.assertEqual(self.calls(), [f"{ktlint} --format {path}"])

    def test_directory_named_ktlint_is_skipped(self):
        (self.proj / "ktlint").mkdir()
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))

    def test_non_executable_project_binary_is_skipped(self):
        self.fake_ktlint(self.proj / "ktlint").chmod(0o644)
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(self.calls(), [])

    def test_no_binary_is_silent(self):
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))


class TestFailOpen(KtlintHookCase):
    def test_missing_jq_is_silent(self):
        self.fake_ktlint(self.bin / "ktlint")
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path), drop_tools=("jq",)))
        self.assertEqual(self.calls(), [])

    def test_invalid_json_is_silent(self):
        self.fake_ktlint(self.bin / "ktlint")
        self.assertSilent(self.run_hook("{not json"))
        self.assertEqual(self.calls(), [])

    def test_missing_file_path_is_silent(self):
        self.fake_ktlint(self.bin / "ktlint")
        self.assertSilent(self.run_hook({"tool_input": {}}))
        self.assertEqual(self.calls(), [])

    def test_nonexistent_file_is_silent(self):
        self.fake_ktlint(self.bin / "ktlint")
        self.assertSilent(self.run_hook(self.payload(self.proj / "Missing.kt")))
        self.assertEqual(self.calls(), [])

    def test_nonzero_status_with_empty_output_is_silent(self):
        self.fake_ktlint(self.bin / "ktlint", exit_code=1, lines=0)
        path = self.make_file("App.kt")
        self.assertSilent(self.run_hook(self.payload(path)))
        self.assertEqual(len(self.calls()), 1)


class TestReport(KtlintHookCase):
    def run_failing(self, exit_code, lines):
        self.fake_ktlint(self.bin / "ktlint", exit_code=exit_code, lines=lines)
        path = self.make_file("App.kt")
        return path, self.run_hook(self.payload(path))

    def test_long_report_is_truncated_to_20_lines(self):
        path, result = self.run_failing(1, 25)
        expected = HEADER.format(path) + "".join(f"violation {i}\n" for i in range(1, 21))
        expected += "... (5 more lines truncated)\n"
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertEqual(result.stderr, expected)
        self.assertNotIn("violation 21", result.stderr)

    def test_report_of_exactly_20_lines_is_not_truncated(self):
        _, result = self.run_failing(1, 20)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("truncated", result.stderr)
        self.assertIn("violation 20", result.stderr)

    def test_any_nonzero_status_with_output_is_reported(self):
        _, result = self.run_failing(3, 1)
        self.assertEqual(result.returncode, 2)
        self.assertIn("violation 1", result.stderr)


class TestHooksConfig(unittest.TestCase):
    def test_post_tool_use_entry(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        entries = hooks["PostToolUse"]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.get("matcher"), "Edit|Write|MultiEdit")
        self.assertEqual(len(entry["hooks"]), 1)
        hook = entry["hooks"][0]
        self.assertEqual(hook["type"], "command")
        self.assertEqual(hook["command"], 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/ktlint-format.sh"')
        self.assertIsInstance(hook["timeout"], int)
        self.assertTrue(10 < hook["timeout"] <= 60)
        self.assertNotIn("async", hook)

    def test_script_shebang_and_mode(self):
        self.assertEqual(SCRIPT.read_text(encoding="utf-8").splitlines()[0], "#!/bin/sh")
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        try:
            out = subprocess.run(
                ["git", "ls-files", "-s", "hooks/ktlint-format.sh"],
                cwd=ROOT_DIR, capture_output=True, text=True, timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        if out.strip():
            self.assertTrue(out.startswith("100755"), out)


if __name__ == "__main__":
    unittest.main()
