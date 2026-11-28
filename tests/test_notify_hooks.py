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
                # notify.sh probes terminal-notifier with -help before using it; the probe is not logged.
                f"#!/bin/sh\n[ \"$1\" = -help ] && exit 0\n{delay}printf '%s\\0' \"$@\" > \"$FAKE_LOG_DIR/${{0##*/}}.$$\"\n",
            )

    def _write_exec(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def add_focus(self):
        (self.bin / "sh").symlink_to(SH)
        # notify.sh runs as a direct child of this test process, so its $PPID is our pid.
        self._write_exec(
            "ps",
            "#!/bin/sh\n"
            f"[ \"$3\" = -p ] && [ \"$4\" = {os.getpid()} ] || exit 0\n"
            "case \"$2\" in\n  tty=) printf '%s\\n' \"$FAKE_TTY\" ;;\n  ppid=) echo 1 ;;\nesac\n",
        )

    def run_script(self, kind, stdin="", env_extra=None, args=None, script=SCRIPT):
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "FAKE_UNAME": "Darwin",
            "FAKE_LOG_DIR": str(self.logs),
            "LANG": "C.UTF-8",
        }
        env.update(env_extra or {})
        argv = [SH, str(script)] + ([kind] if kind is not None else []) + (args or [])
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

    def test_darwin_skips_terminal_notifier_that_cannot_run(self):
        self.add_uname()
        broken = self.tmp / "broken"
        broken.mkdir()
        (broken / "terminal-notifier").write_text("#!/bin/sh\nexit 1\n")
        (broken / "terminal-notifier").chmod(0o755)
        self.add_fakes("terminal-notifier")
        self.run_script("stop", env_extra={"PATH": f"{broken}:{self.bin}"})
        (name, args), = self.calls(1)
        self.assertEqual(name, "terminal-notifier")
        self.assertEqual(args[:2], ["-title", "Claude Code · my-proj"])

    def test_darwin_falls_back_to_osascript_when_no_notifier_runs(self):
        self.add_uname()
        self._write_exec("terminal-notifier", "#!/bin/sh\nexit 1\n")
        self.add_fakes("osascript")
        self.run_script("stop")
        (name, _), = self.calls(1)
        self.assertEqual(name, "osascript")

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


class TestNotifyFocusTab(NotifyTestCase):
    BASE_ARGS = ["-title", "Claude Code · my-proj", "-message", "Done — ready for review", "-sound", "Glass"]

    def setUp(self):
        super().setUp()
        self.add_uname()
        self.add_focus()
        self.add_fakes("terminal-notifier", "osascript", "open")

    def notifier_args(self, env, script=SCRIPT):
        for f in self.logs.iterdir():
            f.unlink()
        self.run_script("stop", env_extra=env, script=script)
        (name, args), = self.calls(1)
        self.assertEqual(name, "terminal-notifier")
        self.assertEqual(args[:6], self.BASE_ARGS)
        return args[6:]

    def focus_cmd(self, tty, terminal, bundle):
        focus = ROOT_DIR / "hooks" / "focus-terminal.sh"
        command = f"[ -f '{focus}' ] && sh '{focus}' focus '{tty}' '{terminal}' '{bundle}'"
        return f"{command} || open -b '{bundle}'" if bundle else command

    def run_click(self, command):
        for f in self.logs.iterdir():
            f.unlink()
        env = {"PATH": str(self.bin), "FAKE_LOG_DIR": str(self.logs)}
        subprocess.run([SH, "-c", command], capture_output=True, timeout=15, cwd=self.tmp, env=env)
        return self.calls(1)

    def test_terminal_app_group_and_execute(self):
        env = {"FAKE_TTY": "ttys003", "TERM_PROGRAM": "Apple_Terminal", "__CFBundleIdentifier": "com.apple.Terminal"}
        extra = self.notifier_args(env)
        command = self.focus_cmd("/dev/ttys003", "Apple_Terminal", "com.apple.Terminal")
        self.assertEqual(extra, ["-group", "claude-workflow-ttys003", "-execute", command])
        (name, args), = self.run_click(command)
        self.assertEqual(name, "osascript")
        self.assertIn('tell application "Terminal"', args)
        self.assertEqual(args[-1], "/dev/ttys003")

    def test_iterm_group_and_execute(self):
        env = {"FAKE_TTY": "ttys012", "TERM_PROGRAM": "iTerm.app", "__CFBundleIdentifier": "com.googlecode.iterm2"}
        extra = self.notifier_args(env)
        command = self.focus_cmd("/dev/ttys012", "iTerm.app", "com.googlecode.iterm2")
        self.assertEqual(extra, ["-group", "claude-workflow-ttys012", "-execute", command])
        (name, args), = self.run_click(command)
        self.assertEqual(name, "osascript")
        self.assertIn('tell application "iTerm2"', args)
        self.assertEqual(args[-1], "/dev/ttys012")

    def test_execute_without_bundle_has_no_open_fallback(self):
        extra = self.notifier_args({"FAKE_TTY": "ttys003", "TERM_PROGRAM": "Apple_Terminal"})
        command = self.focus_cmd("/dev/ttys003", "Apple_Terminal", "")
        self.assertEqual(extra, ["-group", "claude-workflow-ttys003", "-execute", command])
        self.assertNotIn("open -b", command)

    def test_click_after_script_removed_opens_bundle(self):
        hooks = self.tmp / "5.11.0" / "hooks"
        hooks.mkdir(parents=True)
        for name in ("notify.sh", "focus-terminal.sh"):
            shutil.copy2(ROOT_DIR / "hooks" / name, hooks / name)
        env = {"FAKE_TTY": "ttys003", "TERM_PROGRAM": "Apple_Terminal", "__CFBundleIdentifier": "com.apple.Terminal"}
        extra = self.notifier_args(env, script=hooks / "notify.sh")
        focus = hooks / "focus-terminal.sh"
        command = (
            f"[ -f '{focus}' ] && sh '{focus}' focus '/dev/ttys003' 'Apple_Terminal' 'com.apple.Terminal'"
            " || open -b 'com.apple.Terminal'"
        )
        self.assertEqual(extra, ["-group", "claude-workflow-ttys003", "-execute", command])
        shutil.rmtree(self.tmp / "5.11.0")
        (name, args), = self.run_click(command)
        self.assertEqual(name, "open")
        self.assertEqual(args, ["-b", "com.apple.Terminal"])

    def test_resolve_starts_from_notify_parent_pid(self):
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "FAKE_UNAME": "Darwin",
            "FAKE_LOG_DIR": str(self.logs),
            "FAKE_TTY": "ttys003",
            "TERM_PROGRAM": "Apple_Terminal",
        }
        result = subprocess.run(
            [SH, "-c", f"sh '{SCRIPT}' stop; :"], capture_output=True, timeout=15, cwd=self.proj, env=env
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        (name, args), = self.calls(1)
        self.assertEqual(name, "terminal-notifier")
        self.assertEqual(args, self.BASE_ARGS)

    def test_group_id_per_tty(self):
        def group(tty):
            extra = self.notifier_args({"FAKE_TTY": tty, "TERM_PROGRAM": "Apple_Terminal"})
            return extra[extra.index("-group") + 1]

        self.assertEqual(group("ttys003"), group("ttys003"))
        self.assertNotEqual(group("ttys003"), group("ttys004"))

    def test_other_terminal_activates_bundle(self):
        env = {"FAKE_TTY": "ttys003", "TERM_PROGRAM": "ghostty", "__CFBundleIdentifier": "com.mitchellh.ghostty"}
        extra = self.notifier_args(env)
        self.assertEqual(extra, ["-group", "claude-workflow-ttys003", "-activate", "com.mitchellh.ghostty"])

    def test_tmux_only_activates_app(self):
        env = {
            "FAKE_TTY": "ttys003",
            "TERM_PROGRAM": "Apple_Terminal",
            "__CFBundleIdentifier": "com.apple.Terminal",
            "TMUX": "/tmp/tmux-501/default,1,0",
        }
        self.assertEqual(self.notifier_args(env), ["-activate", "com.apple.Terminal"])

    def test_no_tty_only_activates_app(self):
        env = {"FAKE_TTY": "??", "TERM_PROGRAM": "Apple_Terminal", "__CFBundleIdentifier": "com.apple.Terminal"}
        self.assertEqual(self.notifier_args(env), ["-activate", "com.apple.Terminal"])

    def test_nothing_resolved_keeps_old_command(self):
        self.assertEqual(self.notifier_args({"FAKE_TTY": "??"}), [])

    def test_injection_values_never_reach_command(self):
        payloads = ["x;touch PWNED", 'x"y', "x'y", "$(touch PWNED)", "a b"]
        for bad in payloads:
            with self.subTest(bad=bad):
                extra = self.notifier_args(
                    {"FAKE_TTY": "ttys" + bad, "TERM_PROGRAM": "Apple_Terminal", "__CFBundleIdentifier": bad}
                )
                self.assertEqual(extra, [])
                extra = self.notifier_args(
                    {"FAKE_TTY": "ttys003", "TERM_PROGRAM": bad, "__CFBundleIdentifier": "com.apple" + bad}
                )
                self.assertEqual(extra, ["-group", "claude-workflow-ttys003"])
        for d in (self.proj, self.tmp):
            self.assertEqual(list(d.glob("PWNED*")), [])

    def test_quote_in_script_path_falls_back_to_activate(self):
        hooks = self.tmp / "it's" / "hooks"
        hooks.mkdir(parents=True)
        for name in ("notify.sh", "focus-terminal.sh"):
            shutil.copy2(ROOT_DIR / "hooks" / name, hooks / name)
        env = {"FAKE_TTY": "ttys003", "TERM_PROGRAM": "Apple_Terminal", "__CFBundleIdentifier": "com.apple.Terminal"}
        extra = self.notifier_args(env, script=hooks / "notify.sh")
        self.assertEqual(extra, ["-group", "claude-workflow-ttys003", "-activate", "com.apple.Terminal"])

    def test_returns_fast_with_slow_notifier(self):
        (self.bin / "terminal-notifier").unlink()
        self.add_fakes("terminal-notifier", slow=True)
        start = time.time()
        self.run_script("stop", env_extra={"FAKE_TTY": "ttys003", "TERM_PROGRAM": "Apple_Terminal"})
        self.assertLess(time.time() - start, 1)


class TestHooksConfig(unittest.TestCase):
    def test_hooks_json_structure(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(set(hooks), {"Stop", "PreToolUse", "Notification", "PostToolUse"})
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
