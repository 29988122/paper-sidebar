#!/bin/zsh
# Close the throwaway Chrome started by run.sh; with --wipe also delete its profile.
set -uo pipefail
: ${VT_UDD:?set VT_UDD}
HERE=${0:A:h}
PATTERN="--user-data-dir=$VT_UDD"

node "$HERE/cdp.mjs" close 2>/dev/null
for _ in {1..40}; do
  pgrep -f -- "$PATTERN" >/dev/null || break
  node -e 'setTimeout(()=>{}, 250)'
done
if pgrep -f -- "$PATTERN" >/dev/null; then
  pkill -TERM -f -- "$PATTERN"
fi

if [[ "${1:-}" == "--wipe" ]]; then
  case "$VT_UDD" in
    /private/tmp/*|/tmp/*|${TMPDIR:-/nonexistent}*) rm -rf -- "$VT_UDD" && print "wiped $VT_UDD" ;;
    *) print -u2 "not wiping $VT_UDD: only temp-dir profiles are deleted" ;;
  esac
fi
