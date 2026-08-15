#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRCPY="$SCRIPT_DIR/tools/scrcpy-linux-x86_64-v4.1/scrcpy"
SERIAL="${ANDROID_SERIAL:-100.93.33.125:5555}"

exec "$SCRCPY" \
  -s "$SERIAL" \
  --no-audio \
  --keyboard=uhid \
  --mouse=uhid \
  --window-title="Tablet Portal" \
  --window-borderless \
  --always-on-top \
  --window-x=1700 \
  --window-y=900 \
  --window-width=154 \
  --window-height=294 \
  --max-size=336 \
  "$@"
