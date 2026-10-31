#!/usr/bin/env python3
"""Tests for hooks/notify.sh and hooks/hooks.json using fake binaries on an isolated PATH."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / "hooks" / "notify.sh"
HOOKS_JSON = ROOT_DIR / "hooks" / "hooks.json"
SH = shutil.which("sh")

DEFAULT_BODIES = {
    "stop": "Done — ready for review",
    "question": "Claude has a question for you",
    "notification": "Claude needs permission",
}
OSASCRIPT_STATEMENTS = [
    "-e", "on run argv",
    "-e", "display notification (item 1 of argv) with title (item 2 of argv) sound name (item 3 of argv)",
    "-e", "end run",
]


def question_input(text, cwd=None):
    data = {"tool_input": {"questions": [{"question": text}]}}
    if cwd:
        data["cwd"] = cwd
    return json.dumps(data)


class NotifyTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.bin = self.tmp / "bin"
        self.logs = self.tmp / "logs"
        self.proj = self.tmp / "my-proj"
        for d in (self.bin, self.logs, self.proj):
            d.mkdir()
        for tool in ("cat", "basename", "tr", "sleep"):
            real = shutil.which(tool)
            if real is None:
                self.skipTest(f"{tool} not available")
            (self.bin / tool).symlink_to(real)

    def add_jq(self):
        real = shutil.which("jq")
        if real is None:
            self.skipTest("jq not available")
        (self.bin / "jq").symlink_to(real)

    def add_uname(self):
        self._write_exec("uname", "#!/bin/sh\nprintf '%s\\n' \"$FAKE_UNAME\"\n")

    def add_fakes(self, *names, slow=False):
        delay = "sleep 5\n" if slow else ""
        for name in names:
            self._write_exec(
                name,
                f"#!/bin/sh\n{delay}printf '%s\\0' \"$@\" > \"$FAKE_LOG_DIR/${{0##*/}}.$$\"\n",
            )

    def _write_exec(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_script(self, kind, stdin="", env_extra=None, args=None):
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "FAKE_UNAME": "Darwin",
            "FAKE_LOG_DIR": str(self.logs),
            "LANG": "C.UTF-8",
        }
        env.update(env_extra or {})
        argv = [SH, str(SCRIPT)] + ([kind] if kind is not None else []) + (args or [])
        result = subprocess.run(
            argv, input=stdin.encode(), capture_output=True, timeout=15, cwd=self.proj, env=env
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")
        return result

    def calls(self, expected, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline and len(list(self.logs.iterdir())) < expected:
            time.sleep(0.05)
        out = []
        for f in sorted(self.logs.iterdir()):
            raw = f.read_bytes().decode("utf-8")
            args = raw.split("\0")[:-1] if raw else []
            out.append((f.name.rsplit(".", 1)[0], args))
        self.assertEqual(len(out), expected, out)
        return out

    def assert_no_calls(self):
        time.sleep(0.3)
        self.assertEqual(list(self.logs.iterdir()), [])


class TestNotifyScript(NotifyTestCase):
    def test_darwin_prefers_terminal_notifier_stop(self):
        self.add_uname()
        self.add_fakes("terminal-notifier", "osascript")
        self.run_script("stop")
        (name, args), = self.calls(1)
        self.assertEqual(name, "terminal-notifier")
        self.assertEqual(
            args,
            ["-title", "Claude Code · my-proj", "-message", "Done — ready for review", "-sound", "Glass"],
        )

    def test_darwin_osascript_fallback_uses_argv(self):
        self.add_uname()
        self.add_fakes("osascript")
        self.run_script("stop")
        (name, args), = self.calls(1)
        self.assertEqual(name, "osascript")
        self.assertEqual(args[:6], OSASCRIPT_STATEMENTS)
        self.assertEqual(args[6:], ["Done — ready for review", "Claude Code · my-proj", "Glass"])

    def test_darwin_question_body_from_jq(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        self.run_script("question", question_input("Which DB?"))
        (_, args), = self.calls(1)
        self.assertEqual(args[3], "Which DB?")
        self.assertEqual(args[5], "Ping")

    def test_darwin_notification_body_from_jq(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        self.run_script("notification", json.dumps({"message": "Needs permission: Bash"}))
        (_, args), = self.calls(1)
        self.assertEqual(args[3], "Needs permission: Bash")
        self.assertEqual(args[5], "Ping")

    def test_title_uses_cwd_from_json(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        self.run_script("question", question_input("Q?", cwd="/x/y/other"))
        (_, args), = self.calls(1)
        self.assertEqual(args[1], "Claude Code · other")

    def test_injection_payload_passed_verbatim_as_argv(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("osascript")
        payload = '"; do shell script "touch PWNED" -- \\ $(touch PWNED2) `touch PWNED3`\nline2'
        self.run_script("question", question_input(payload))
        (_, args), = self.calls(1)
        self.assertEqual(args[:6], OSASCRIPT_STATEMENTS)
        self.assertEqual(len(args), 9)
        self.assertEqual(args[6], payload.replace("\n", " "))
        for d in (self.proj, self.tmp):
            self.assertEqual(list(d.glob("PWNED*")), [])

    def test_leading_dash_body_guarded(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        self.run_script("question", question_input("-rm"))
        (_, args), = self.calls(1)
        self.assertEqual(args[3], " -rm")

    def test_body_truncated_200(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        self.run_script("question", question_input("é" * 500))
        (_, args), = self.calls(1)
        self.assertLessEqual(len(args[3]), 200)
        self.assertEqual(args[3], "é" * 200)

    def test_no_jq_defaults(self):
        self.add_uname()
        self.add_fakes("terminal-notifier")
        for kind, expected in DEFAULT_BODIES.items():
            with self.subTest(kind=kind):
                for f in self.logs.iterdir():
                    f.unlink()
                self.run_script(kind, question_input("ignored", cwd="/x/other"))
                (_, args), = self.calls(1)
                self.assertEqual(args[3], expected)
                self.assertEqual(args[1], "Claude Code · my-proj")

    def test_malformed_and_empty_stdin(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("terminal-notifier")
        for stdin in ("", "{not json", '{"tool_input":{"questions":"x"}}', "[]"):
            with self.subTest(stdin=stdin):
                for f in self.logs.iterdir():
                    f.unlink()
                self.run_script("question", stdin)
                (_, args), = self.calls(1)
                self.assertEqual(args[3], DEFAULT_BODIES["question"])

    def test_unknown_or_missing_kind(self):
        self.add_uname()
        self.add_fakes("terminal-notifier")
        self.run_script("bogus")
        self.run_script(None)
        self.assert_no_calls()

    def test_linux_notify_send_and_canberra(self):
        self.add_uname()
        self.add_jq()
        self.add_fakes("notify-send", "canberra-gtk-play")
        env = {"FAKE_UNAME": "Linux"}
        self.run_script("stop", env_extra=env)
        self.run_script("question", question_input("Which?"), env_extra=env)
        got = self.calls(4)
        notify = [a for n, a in got if n == "notify-send"]
        sounds = sorted(a for n, a in got if n == "canberra-gtk-play")
        self.assertIn(["--", "Claude Code · my-proj", "Done — ready for review"], notify)
        self.assertIn(["--", "Claude Code · my-proj", "Which?"], notify)
        self.assertEqual(sounds, [["-i", "complete"], ["-i", "message"]])

    def test_linux_paplay_fallback(self):
        self.add_uname()
        self.add_fakes("notify-send", "paplay")
        self.run_script("stop", env_extra={"FAKE_UNAME": "Linux"})
        got = dict(self.calls(2))
        self.assertEqual(got["paplay"], ["/usr/share/sounds/freedesktop/stereo/complete.oga"])

    def test_linux_nothing_available(self):
        self.add_uname()
        self.run_script("stop", env_extra={"FAKE_UNAME": "Linux"})
        self.assert_no_calls()

    def test_opt_out(self):
        self.add_uname()
        self.add_fakes("terminal-notifier", "notify-send", "canberra-gtk-play")
        for uname in ("Darwin", "Linux"):
            with self.subTest(uname=uname):
                self.run_script("stop", env_extra={"FAKE_UNAME": uname, "CLAUDE_WORKFLOW_NOTIFY": "0"})
                self.assert_no_calls()
        self.run_script("stop", env_extra={"CLAUDE_WORKFLOW_NOTIFY": "1"})
        self.calls(1)

    def test_unsupported_os(self):
        self.add_uname()
        self.add_fakes("terminal-notifier", "notify-send", "osascript")
        self.run_script("stop", env_extra={"FAKE_UNAME": "MINGW64_NT-10.0"})
        self.assert_no_calls()

    def test_missing_uname(self):
        self.add_fakes("terminal-notifier", "notify-send")
        self.run_script("stop")
        self.assert_no_calls()

    def test_returns_fast_with_slow_notifier(self):
        self.add_uname()
        self.add_fakes("terminal-notifier", slow=True)
        start = time.time()
        self.run_script("stop")
        self.assertLess(time.time() - start, 2)

    def test_c_locale(self):
        self.add_uname()
        self.add_fakes("terminal-notifier")
        self.run_script("stop", env_extra={"LC_ALL": "C", "LANG": "C"})
        (_, args), = self.calls(1)
        self.assertEqual(args[1], "Claude Code · my-proj")


class TestHooksConfig(unittest.TestCase):
    def test_hooks_json_structure(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(set(hooks), {"Stop", "PreToolUse", "Notification"})
        self.assertNotIn("SubagentStop", hooks)
        expected = {
            "Stop": (None, "stop"),
            "PreToolUse": ("AskUserQuestion", "question"),
            "Notification": ("permission_prompt|elicitation_dialog", "notification"),
        }
        for event, (matcher, kind) in expected.items():
            with self.subTest(event=event):
                self.assertEqual(len(hooks[event]), 1)
                entry = hooks[event][0]
                self.assertEqual(entry.get("matcher"), matcher)
                self.assertEqual(len(entry["hooks"]), 1)
                hook = entry["hooks"][0]
                self.assertEqual(hook["type"], "command")
                self.assertEqual(hook["command"], f'sh "${{CLAUDE_PLUGIN_ROOT}}/hooks/notify.sh" {kind}')
                self.assertTrue(hook["command"].endswith(" " + kind))
                self.assertIsInstance(hook["timeout"], int)
                self.assertTrue(0 < hook["timeout"] <= 10)
                self.assertNotIn("async", hook)

    def test_script_shebang_and_mode(self):
        self.assertEqual(SCRIPT.read_text(encoding="utf-8").splitlines()[0], "#!/bin/sh")
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        try:
            out = subprocess.run(
                ["git", "ls-files", "-s", "hooks/notify.sh"],
                cwd=ROOT_DIR, capture_output=True, text=True, timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        if out.strip():
            self.assertTrue(out.startswith("100755"), out)


if __name__ == "__main__":
    unittest.main()
