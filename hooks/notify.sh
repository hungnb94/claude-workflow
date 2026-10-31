#!/bin/sh
# Desktop alerts for Claude Code hooks. Usage: notify.sh stop|question|notification
# Reads the hook JSON on stdin. Set CLAUDE_WORKFLOW_NOTIFY=0 to disable.
# Always exits 0 and prints nothing so it can never block Claude.

kind=${1:-}

input=''
if [ ! -t 0 ]; then
  input=$(cat 2>/dev/null)
fi

[ "${CLAUDE_WORKFLOW_NOTIFY:-1}" = "0" ] && exit 0

has() {
  command -v "$1" >/dev/null 2>&1
}

run_bg() {
  "$@" </dev/null >/dev/null 2>&1 &
}

case "$kind" in
  stop)
    body='Done — ready for review'
    jq_path=''
    mac_sound=Glass
    linux_sound=complete
    ;;
  question)
    body='Claude has a question for you'
    jq_path='.tool_input.questions[0].question?'
    mac_sound=Ping
    linux_sound=message
    ;;
  notification)
    body='Claude needs permission'
    jq_path='.message?'
    mac_sound=Ping
    linux_sound=message
    ;;
  *)
    exit 0
    ;;
esac

os=$(uname -s 2>/dev/null)
case "$os" in
  Darwin | Linux) ;;
  *) exit 0 ;;
esac

is_blank() {
  [ -z "$(printf '%s' "$1" | tr -d ' ' 2>/dev/null)" ]
}

extract() {
  printf '%s' "$input" | jq -r "$1" 2>/dev/null
}

cwd=''
if [ -n "$input" ] && has jq; then
  cwd=$(extract '.cwd // empty | strings')
  if [ -n "$jq_path" ]; then
    extracted=$(extract "$jq_path"' // empty | strings | explode | map(if . < 32 or . == 127 then 32 else . end) | implode | .[0:200]')
    is_blank "$extracted" || body=$extracted
  fi
fi

dir=${cwd:-$PWD}
name=$(basename -- "$dir" 2>/dev/null | tr -d '[:cntrl:]' 2>/dev/null)
[ -n "$name" ] || name=$PWD
title="Claude Code · $name"

case "$body" in
  -*) body=" $body" ;;
esac

notify_darwin() {
  if has terminal-notifier; then
    run_bg terminal-notifier -title "$title" -message "$body" -sound "$mac_sound"
  elif has osascript; then
    run_bg osascript \
      -e 'on run argv' \
      -e 'display notification (item 1 of argv) with title (item 2 of argv) sound name (item 3 of argv)' \
      -e 'end run' \
      "$body" "$title" "$mac_sound"
  fi
}

play_linux_sound() {
  if has canberra-gtk-play; then
    run_bg canberra-gtk-play -i "$linux_sound"
  elif has paplay; then
    run_bg paplay "/usr/share/sounds/freedesktop/stereo/$linux_sound.oga"
  else
    { printf '\a' >/dev/tty; } 2>/dev/null
  fi
}

notify_linux() {
  if has notify-send; then
    run_bg notify-send -- "$title" "$body"
  fi
  play_linux_sound
}

case "$os" in
  Darwin) notify_darwin ;;
  Linux) notify_linux ;;
esac

exit 0
