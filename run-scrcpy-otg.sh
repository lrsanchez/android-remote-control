#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRCPY="$SCRIPT_DIR/tools/scrcpy-linux-x86_64-v4.1/scrcpy"
SERIAL="${ANDROID_SERIAL:-100.93.33.125:5555}"

exec "$SCRCPY" \
  --otg \
  --window-borderless \
  --window-width=1 \
  --window-height=1 \
  --window-x=0 \
  --window-y=0 \
  -s "$SERIAL" \
  "$@"
