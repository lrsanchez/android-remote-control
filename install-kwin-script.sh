#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/kde/kwin-remote-input"

if command -v kpackagetool6 >/dev/null 2>&1; then
  kpackagetool6 --type KWin/Script --upgrade "$PACKAGE_DIR" 2>/dev/null || \
  kpackagetool6 --type KWin/Script --install "$PACKAGE_DIR"
else
  DEST="$HOME/.local/share/kwin/scripts/kwin-remote-input"
  mkdir -p "$DEST"
  cp -R "$PACKAGE_DIR"/* "$DEST"/
fi

echo "KWin script installed."
echo "Enable it in System Settings -> Window Management -> KWin Scripts."
