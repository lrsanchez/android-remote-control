#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if pgrep -af "$SCRIPT_DIR/tray.py" >/dev/null 2>&1; then
  exit 0
fi

nohup python3 "$SCRIPT_DIR/tray.py" >/tmp/tablet-tray.log 2>&1 &
