#!/usr/bin/env python3
"""Tests for hooks/focus-terminal.sh using fake ps, uname, osascript and open on an isolated PATH."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_DIR / "hooks" / "focus-terminal.sh"
SH = shutil.which("sh")

FAKE_PS = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_LOG_DIR/ps.log"
field=$2
pid=$4
printf '%s\\n' "$FAKE_PS_TABLE" | while read -r p pp t; do
  [ "$p" = "$pid" ] || continue
  case "$field" in
    tty=) printf '%s   \\n' "$t" ;;
    ppid=) printf '%5s\\n' "$pp" ;;
  esac
done
"""

TERMINAL_CHAIN = "500 400 ??\n400 300 ttys003\n300 1 ttys003\n"
MALICIOUS = [
    "com.apple.Terminal; touch PWNED",
    'com.apple.Terminal"',
    "com.apple.Terminal'",
    "$(touch PWNED)",
    "com.apple Terminal",
    "-com.apple.Terminal",
    "com.äpple.Terminal",
    "a" * 256,
]


class FocusTerminalCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.bin = self.tmp / "bin"
        self.logs = self.tmp / "logs"
        for d in (self.bin, self.logs):
            d.mkdir()
        self._write_exec("uname", "#!/bin/sh\nprintf '%s\\n' \"$FAKE_UNAME\"\n")
        self._write_exec("ps", FAKE_PS)
        for name in ("osascript", "open"):
            self._write_exec(
                name,
                "#!/bin/sh\nprintf '%s\\0' \"$@\" > \"$FAKE_LOG_DIR/${0##*/}.$$\"\n"
                "exit \"${FAKE_EXIT:-0}\"\n",
            )

    def _write_exec(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_script(self, *args, env_extra=None):
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "FAKE_UNAME": "Darwin",
            "FAKE_LOG_DIR": str(self.logs),
            "FAKE_PS_TABLE": TERMINAL_CHAIN,
            "LANG": "C.UTF-8",
        }
        env.update(env_extra or {})
        result = subprocess.run(
            [SH, str(SCRIPT), *args], capture_output=True, timeout=15, cwd=self.tmp, env=env
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        return result.stdout.decode("utf-8")

    def resolve(self, pid="500", **env):
        out = self.run_script("resolve", pid, env_extra=env)
        lines = out.split("\n")
        self.assertEqual(len(lines), 4, out)
        self.assertEqual(lines[3], "")
        return lines[:3]

    def calls(self, name):
        out = []
        for f in sorted(self.logs.glob(f"{name}.*")):
            if f.name == "ps.log":
                continue
            raw = f.read_bytes().decode("utf-8")
            out.append(raw.split("\0")[:-1] if raw else [])
        return out

    def ps_calls(self):
        log = self.logs / "ps.log"
        return log.read_text().splitlines() if log.exists() else []


class TestResolve(FocusTerminalCase):
    def test_terminal_app_walks_up_to_first_tty(self):
        got = self.resolve(TERM_PROGRAM="Apple_Terminal", __CFBundleIdentifier="com.apple.Terminal")
        self.assertEqual(got, ["/dev/ttys003", "Apple_Terminal", "com.apple.Terminal"])

    def test_iterm(self):
        got = self.resolve(TERM_PROGRAM="iTerm.app", __CFBundleIdentifier="com.googlecode.iterm2")
        self.assertEqual(got, ["/dev/ttys003", "iTerm.app", "com.googlecode.iterm2"])

    def test_tmux_drops_tty_and_terminal_keeps_bundle(self):
        got = self.resolve(
            TERM_PROGRAM="Apple_Terminal", __CFBundleIdentifier="com.apple.Terminal", TMUX="/tmp/tmux,1,0"
        )
        self.assertEqual(got, ["", "", "com.apple.Terminal"])

    def test_other_terminal_keeps_tty_and_bundle_only(self):
        got = self.resolve(TERM_PROGRAM="ghostty", __CFBundleIdentifier="com.mitchellh.ghostty")
        self.assertEqual(got, ["/dev/ttys003", "", "com.mitchellh.ghostty"])

    def test_not_darwin_prints_three_empty_lines(self):
        got = self.resolve(
            FAKE_UNAME="Linux", TERM_PROGRAM="Apple_Terminal", __CFBundleIdentifier="com.apple.Terminal"
        )
        self.assertEqual(got, ["", "", ""])
        self.assertEqual(self.ps_calls(), [])

    def test_no_tty_stops_at_init(self):
        got = self.resolve(FAKE_PS_TABLE="500 400 ??\n400 1 ??\n", TERM_PROGRAM="Apple_Terminal")
        self.assertEqual(got, ["", "Apple_Terminal", ""])
        self.assertNotIn("-o tty= -p 1", self.ps_calls())

    def test_ancestor_limit(self):
        rows = [f"{100 + i} {101 + i} ??" for i in range(12)] + ["112 1 ttys009"]
        got = self.resolve(pid="100", FAKE_PS_TABLE="\n".join(rows) + "\n", TERM_PROGRAM="Apple_Terminal")
        self.assertEqual(got[0], "")
        tty_lookups = [c for c in self.ps_calls() if c.startswith("-o tty=")]
        self.assertEqual(len(tty_lookups), 9)

    def test_malformed_tty_is_skipped(self):
        for bad in ("ttys", "ttys00a", "console", "ttys1$(x)", "ttys1;x", "tty003"):
            with self.subTest(tty=bad):
                got = self.resolve(FAKE_PS_TABLE=f"500 1 {bad}\n", TERM_PROGRAM="Apple_Terminal")
                self.assertEqual(got[0], "")

    def test_invalid_pid(self):
        for pid in ("", "abc", "0", "1"):
            with self.subTest(pid=pid):
                self.assertEqual(self.resolve(pid=pid)[0], "")

    def test_missing_ps(self):
        (self.bin / "ps").unlink()
        got = self.resolve(TERM_PROGRAM="Apple_Terminal")
        self.assertEqual(got, ["", "Apple_Terminal", ""])

    def test_malicious_bundle_dropped(self):
        for bad in MALICIOUS:
            with self.subTest(bundle=bad):
                self.assertEqual(self.resolve(__CFBundleIdentifier=bad)[2], "")
        self.assertEqual(list(self.tmp.glob("PWNED*")), [])

    def test_bundle_max_length(self):
        self.assertEqual(self.resolve(__CFBundleIdentifier="a" * 255)[2], "a" * 255)


class TestFocus(FocusTerminalCase):
    def assert_tty_only_in_argv(self, args, tty):
        self.assertEqual(args[-1], tty)
        statements = args[:-1]
        self.assertEqual(statements[0::2], ["-e"] * (len(statements) // 2))
        self.assertEqual(statements[1], "on run argv")
        self.assertEqual(statements[-1], "end run")
        self.assertFalse(any(tty in s for s in statements))

    def test_terminal_app_selects_tab_by_tty(self):
        out = self.run_script("focus", "/dev/ttys003", "Apple_Terminal", "com.apple.Terminal")
        self.assertEqual(out, "")
        (args,) = self.calls("osascript")
        self.assert_tty_only_in_argv(args, "/dev/ttys003")
        self.assertIn('tell application "Terminal"', args)
        self.assertIn("if tty of t is targetTty then", args)
        self.assertIn("set selected of t to true", args)
        self.assertIn("set index of w to 1", args)
        self.assertIn("activate", args)
        self.assertEqual(self.calls("open"), [])

    def test_iterm_selects_session_by_tty(self):
        self.run_script("focus", "/dev/ttys012", "iTerm.app", "com.googlecode.iterm2")
        (args,) = self.calls("osascript")
        self.assert_tty_only_in_argv(args, "/dev/ttys012")
        self.assertIn('tell application "iTerm2"', args)
        self.assertIn("if tty of s is targetTty then", args)
        for stmt in ("select w", "tell t to select", "tell s to select", "activate"):
            self.assertIn(stmt, args)
        self.assertEqual(self.calls("open"), [])

    def test_no_tty_activates_bundle(self):
        self.run_script("focus", "", "Apple_Terminal", "com.apple.Terminal")
        self.assertEqual(self.calls("osascript"), [])
        self.assertEqual(self.calls("open"), [["-b", "com.apple.Terminal"]])

    def test_unknown_terminal_activates_bundle(self):
        self.run_script("focus", "/dev/ttys003", "ghostty", "com.mitchellh.ghostty")
        self.assertEqual(self.calls("osascript"), [])
        self.assertEqual(self.calls("open"), [["-b", "com.mitchellh.ghostty"]])

    def test_osascript_failure_falls_back_to_bundle(self):
        self.run_script(
            "focus", "/dev/ttys003", "Apple_Terminal", "com.apple.Terminal", env_extra={"FAKE_EXIT": "1"}
        )
        self.assertEqual(len(self.calls("osascript")), 1)
        self.assertEqual(self.calls("open"), [["-b", "com.apple.Terminal"]])

    def test_malicious_tty_not_passed(self):
        for bad in ("/dev/ttys003; touch PWNED", "/dev/ttys$(touch PWNED)", "/dev/tty003", "ttys003"):
            with self.subTest(tty=bad):
                self.run_script("focus", bad, "Apple_Terminal", "")
        self.assertEqual(self.calls("osascript"), [])
        self.assertEqual(self.calls("open"), [])
        self.assertEqual(list(self.tmp.glob("PWNED*")), [])

    def test_malicious_bundle_not_opened(self):
        for bad in MALICIOUS:
            with self.subTest(bundle=bad):
                self.run_script("focus", "", "", bad)
        self.assertEqual(self.calls("open"), [])
        self.assertEqual(list(self.tmp.glob("PWNED*")), [])

    def test_nothing_valid_does_nothing(self):
        self.run_script("focus")
        self.run_script("bogus", "/dev/ttys003")
        self.run_script()
        self.assertEqual(self.calls("osascript"), [])
        self.assertEqual(self.calls("open"), [])


class TestScriptFile(unittest.TestCase):
    def test_shebang_and_mode(self):
        self.assertEqual(SCRIPT.read_text(encoding="utf-8").splitlines()[0], "#!/bin/sh")
        self.assertTrue(os.access(SCRIPT, os.X_OK))
        try:
            out = subprocess.run(
                ["git", "ls-files", "-s", "hooks/focus-terminal.sh"],
                cwd=ROOT_DIR, capture_output=True, text=True, timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        if out.strip():
            self.assertTrue(out.startswith("100755"), out)


if __name__ == "__main__":
    unittest.main()
