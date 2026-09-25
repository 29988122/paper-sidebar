#!/bin/zsh
# Launch a separate, throwaway Google Chrome for visual tests.
#   VT_UDD=/private/tmp/.../vt-udd harness/run.sh          (EXTRA_FLAGS="--force-dark-mode" optional)
# Headful on purpose: headless Chrome has no browser UI, so the tab strip can't be seen.
# Never points at the real profile; everything is driven over CDP by harness/cdp.mjs.
set -euo pipefail
: ${VT_UDD:?set VT_UDD to a throwaway profile directory}
case "$VT_UDD" in
  *"/Library/Application Support/Google/Chrome"*) print -u2 "refusing to use the real Chrome profile"; exit 1 ;;
esac
HERE=${0:A:h}

if [[ ! -e "$VT_UDD/Default/Preferences" ]]; then
  mkdir -p "$VT_UDD/Default"
  cp "$HERE/prefs.seed.json" "$VT_UDD/Default/Preferences"
fi
rm -f "$VT_UDD/DevToolsActivePort"

open -na "Google Chrome" --args \
  --user-data-dir="$VT_UDD" --remote-debugging-port=0 \
  --no-first-run --no-default-browser-check --use-mock-keychain --disable-sync \
  --disable-background-networking --disable-component-update \
  --window-position=48,28 --window-size=1216,760 \
  ${=EXTRA_FLAGS:-} about:blank

node "$HERE/cdp.mjs" wait
