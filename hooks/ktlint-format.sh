#!/bin/sh
# PostToolUse hook: runs `ktlint --format` on the Kotlin file Claude just wrote.
# Fails open (exit 0, silent) on any missing prerequisite; exits 2 with the
# remaining violations on stderr (max 20 lines) when ktlint cannot autocorrect.

MAX_REPORT_LINES=20

input=''
if [ ! -t 0 ]; then
  input=$(cat 2>/dev/null)
fi

has() {
  command -v "$1" >/dev/null 2>&1
}

json_field() {
  printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
}

is_kotlin_source() {
  case "$1" in
    *.kt | *.kts) return 0 ;;
    *) return 1 ;;
  esac
}

has_glob_chars() {
  case "$1" in
    *'*'* | *'?'* | *'['* | *']'* | *'{'* | *'}'*) return 0 ;;
    *) return 1 ;;
  esac
}

find_ktlint() {
  if has ktlint; then
    echo ktlint
  elif [ -n "$root" ] && [ -f "$root/ktlint" ] && [ -x "$root/ktlint" ]; then
    echo "$root/ktlint"
  else
    return 1
  fi
}

truncate_report() {
  awk -v max="$MAX_REPORT_LINES" '
    NR <= max { print }
    END { if (NR > max) printf "... (%d more lines truncated)\n", NR - max }
  '
}

has jq || exit 0

file=$(json_field '.tool_input.file_path')
is_kotlin_source "$file" || exit 0

root=${CLAUDE_PROJECT_DIR:-$(json_field '.cwd')}
case "$file" in
  /*) ;;
  *)
    [ -n "$root" ] || exit 0
    file="$root/$file"
    ;;
esac

has_glob_chars "$file" && exit 0
[ -f "$file" ] || exit 0

bin=$(find_ktlint) || exit 0

out=$(cd "${root:-${file%/*}}" 2>/dev/null && "$bin" --format "$file" 2>&1)
status=$?
[ "$status" -eq 0 ] && exit 0
[ -n "$out" ] || exit 0

{
  printf 'ktlint could not autocorrect %s:\n' "$file"
  printf '%s\n' "$out" | truncate_report
} >&2
exit 2
