#!/usr/bin/env bash
set -euo pipefail

FINDLET_ICON_MODE="${1:-export}"
case "$FINDLET_ICON_MODE" in
  export|--check) ;;
  *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac
FINDLET_ICON_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINDLET_ICON_SOURCE="$FINDLET_ICON_ROOT/artwork/app-icon.svg"
FINDLET_ICON_STAGE="$(mktemp -d "${TMPDIR:-/tmp}/findlet-icon.XXXXXX")"
trap 'rm -rf "$FINDLET_ICON_STAGE"' EXIT
FINDLET_ICON_SET="$FINDLET_ICON_STAGE/AppIcon.iconset"
python3 "$FINDLET_ICON_ROOT/script/render_app_icon.py" "$FINDLET_ICON_SOURCE" "$FINDLET_ICON_SET" "$FINDLET_ICON_STAGE/AppIcon.icns"
if [[ "$FINDLET_ICON_MODE" == --check ]]; then
  if ! /usr/bin/cmp -s "$FINDLET_ICON_SET/icon_512x512@2x.png" "$FINDLET_ICON_ROOT/artwork/app-icon.png" \
    || ! /usr/bin/cmp -s "$FINDLET_ICON_STAGE/AppIcon.icns" "$FINDLET_ICON_ROOT/Resources/AppIcon.icns"; then
    echo "Icon exports differ. Regenerate on the reviewed macOS toolchain and inspect the artwork." >&2
    exit 1
  fi
  echo "Findlet PNG and ICNS exports match the current SVG/toolchain."
else
  cp "$FINDLET_ICON_SET/icon_512x512@2x.png" "$FINDLET_ICON_ROOT/artwork/app-icon.png"
  cp "$FINDLET_ICON_STAGE/AppIcon.icns" "$FINDLET_ICON_ROOT/Resources/AppIcon.icns"
  echo "Exported artwork/app-icon.png and Resources/AppIcon.icns."
fi
