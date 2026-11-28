#!/bin/sh
# Finds and focuses the terminal tab of a Claude session. Used by notify.sh.
#   focus-terminal.sh resolve <pid>
#     Prints three lines: tty (/dev/ttysNNN), terminal (Apple_Terminal or iTerm.app), bundle id.
#     A line is empty when the value is unknown or fails validation.
#   focus-terminal.sh focus <tty> <terminal> <bundle>
#     Runs on notification click: selects the tab with that tty, or brings the app forward.
# Always exits 0 and never writes to stderr.

MAX_ANCESTORS=8

is_valid_tty() {
  case "$1" in
    /dev/ttys[0-9]*) ;;
    *) return 1 ;;
  esac
  case "${1#/dev/ttys}" in
    *[!0-9]*) return 1 ;;
  esac
}

is_valid_terminal() {
  case "$1" in
    Apple_Terminal | iTerm.app) return 0 ;;
    *) return 1 ;;
  esac
}

# Letters are listed explicitly because [A-Z] ranges depend on the locale.
is_valid_bundle() {
  case "$1" in
    '' | -* | *[!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-]*) return 1 ;;
  esac
  [ "${#1}" -le 255 ]
}

ps_field() {
  read -r value _rest <<EOF
$(ps -o "$1=" -p "$2" 2>/dev/null)
EOF
  printf '%s' "$value"
}

session_tty() {
  pid=$1
  hops=0
  while [ "$hops" -le "$MAX_ANCESTORS" ]; do
    case "$pid" in
      '' | *[!0-9]* | 0 | 1) return ;;
    esac
    tty_name=$(ps_field tty "$pid")
    if is_valid_tty "/dev/$tty_name"; then
      printf '/dev/%s' "$tty_name"
      return
    fi
    pid=$(ps_field ppid "$pid")
    hops=$((hops + 1))
  done
}

resolve() {
  tty=''
  terminal=''
  bundle=''
  if [ "$(uname -s 2>/dev/null)" = Darwin ]; then
    if [ -z "${TMUX:-}" ]; then
      tty=$(session_tty "$1")
      is_valid_terminal "${TERM_PROGRAM:-}" && terminal=$TERM_PROGRAM
    fi
    is_valid_bundle "${__CFBundleIdentifier:-}" && bundle=$__CFBundleIdentifier
  fi
  printf '%s\n%s\n%s\n' "$tty" "$terminal" "$bundle"
}

focus_terminal_app() {
  osascript \
    -e 'on run argv' \
    -e 'set targetTty to item 1 of argv' \
    -e 'tell application "Terminal"' \
    -e 'repeat with w in windows' \
    -e 'repeat with t in tabs of w' \
    -e 'if tty of t is targetTty then' \
    -e 'set selected of t to true' \
    -e 'set index of w to 1' \
    -e 'activate' \
    -e 'return' \
    -e 'end if' \
    -e 'end repeat' \
    -e 'end repeat' \
    -e 'activate' \
    -e 'end tell' \
    -e 'end run' \
    "$1"
}

focus_iterm() {
  osascript \
    -e 'on run argv' \
    -e 'set targetTty to item 1 of argv' \
    -e 'tell application "iTerm2"' \
    -e 'repeat with w in windows' \
    -e 'repeat with t in tabs of w' \
    -e 'repeat with s in sessions of t' \
    -e 'if tty of s is targetTty then' \
    -e 'select w' \
    -e 'tell t to select' \
    -e 'tell s to select' \
    -e 'activate' \
    -e 'return' \
    -e 'end if' \
    -e 'end repeat' \
    -e 'end repeat' \
    -e 'end repeat' \
    -e 'activate' \
    -e 'end tell' \
    -e 'end run' \
    "$1"
}

activate_bundle() {
  [ -n "$1" ] && open -b "$1"
}

focus() {
  tty=$1
  terminal=$2
  bundle=$3
  is_valid_tty "$tty" || tty=''
  is_valid_terminal "$terminal" || terminal=''
  is_valid_bundle "$bundle" || bundle=''
  if [ -z "$tty" ] || [ -z "$terminal" ]; then
    activate_bundle "$bundle"
    return
  fi
  case "$terminal" in
    Apple_Terminal) focus_terminal_app "$tty" ;;
    iTerm.app) focus_iterm "$tty" ;;
  esac || activate_bundle "$bundle"
}

case "${1:-}" in
  resolve) resolve "${2:-}" 2>/dev/null ;;
  focus) focus "${2:-}" "${3:-}" "${4:-}" </dev/null >/dev/null 2>&1 ;;
esac

exit 0
