#!/usr/bin/env bash
set -euo pipefail

FINDLET_MODE="${1:-run}"
case "$FINDLET_MODE" in
  run|--build-only|--debug|--logs|--telemetry|--verify) ;;
  *) echo "usage: $0 [--build-only|--debug|--logs|--telemetry|--verify]" >&2; exit 2 ;;
esac
FINDLET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FINDLET_ROOT"
if [[ -f "$HOME/.codex/storage-policy.md" ]]; then
  FINDLET_GUARD="$HOME/Library/Application Support/LocalStorageGuard/storage_guard.py"
  [[ -f "$FINDLET_GUARD" ]] || { echo "Storage Guard is required by the workspace policy." >&2; exit 1; }
  python3 "$FINDLET_GUARD" preflight --need-gib 4
fi

if pgrep -x Findlet >/dev/null; then
  if [[ "$FINDLET_MODE" == --build-only ]]; then
    echo "Close Findlet before replacing its bundle. An active operation has been left alone." >&2
    exit 1
  fi
  /usr/bin/osascript -e 'tell application id "com.alvarovillalbaa.Findlet" to quit'
  for FINDLET_ATTEMPT in {1..20}; do
    pgrep -x Findlet >/dev/null || break
    sleep 0.25
  done
  if pgrep -x Findlet >/dev/null; then
    echo "Findlet stayed open. Finish or cancel its operation and quit before rebuilding." >&2
    exit 1
  fi
fi

swift build --product Findlet
FINDLET_BINARY="$(swift build --show-bin-path)/Findlet"
FINDLET_DIST="$FINDLET_ROOT/dist"
FINDLET_APP="$FINDLET_DIST/Findlet.app"
mkdir -p "$FINDLET_DIST"
if [[ -L "$FINDLET_DIST" || -L "$FINDLET_APP" ]]; then
  echo "Refusing a symbolic-link output path." >&2; exit 1
fi
if [[ -e "$FINDLET_APP" ]]; then
  FINDLET_OLD_ID="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$FINDLET_APP/Contents/Info.plist")"
  [[ "$FINDLET_OLD_ID" == com.alvarovillalbaa.Findlet ]] || { echo "Output belongs to another app." >&2; exit 1; }
fi
FINDLET_STAGE="$(mktemp -d "$FINDLET_DIST/.findlet-stage.XXXXXX")"
cleanup_findlet_stage() {
  if [[ ! -e "$FINDLET_APP" && -d "$FINDLET_STAGE/previous.app" ]]; then mv "$FINDLET_STAGE/previous.app" "$FINDLET_APP"; fi
  rm -rf "$FINDLET_STAGE"
}
trap cleanup_findlet_stage EXIT
mkdir -p "$FINDLET_STAGE/Findlet.app/Contents/MacOS"
cp "$FINDLET_BINARY" "$FINDLET_STAGE/Findlet.app/Contents/MacOS/Findlet"
cp "$FINDLET_ROOT/Resources/Info.plist" "$FINDLET_STAGE/Findlet.app/Contents/Info.plist"
chmod +x "$FINDLET_STAGE/Findlet.app/Contents/MacOS/Findlet"
/usr/bin/plutil -lint "$FINDLET_STAGE/Findlet.app/Contents/Info.plist"
# Local ad-hoc signing needs no account, certificate or paid enrollment.
/usr/bin/codesign --force --sign - "$FINDLET_STAGE/Findlet.app"
/usr/bin/codesign --verify --strict "$FINDLET_STAGE/Findlet.app"
if [[ -e "$FINDLET_APP" ]]; then mv "$FINDLET_APP" "$FINDLET_STAGE/previous.app"; fi
mv "$FINDLET_STAGE/Findlet.app" "$FINDLET_APP"

case "$FINDLET_MODE" in
  --build-only) echo "Built and locally ad-hoc signed: $FINDLET_APP" ;;
  --debug) lldb -- "$FINDLET_APP/Contents/MacOS/Findlet" ;;
  --logs|--telemetry)
    /usr/bin/open -n "$FINDLET_APP"
    /usr/bin/log stream --info --style compact --predicate 'process == "Findlet"'
    ;;
  --verify) /usr/bin/open -n "$FINDLET_APP"; sleep 1; pgrep -x Findlet >/dev/null ;;
  run) /usr/bin/open -n "$FINDLET_APP" ;;
esac
