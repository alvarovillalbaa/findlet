#!/usr/bin/env bash
set -euo pipefail

FINDLET_MODE="${1:-run}"
case "$FINDLET_MODE" in
  run|--build-only|--build-preview|--debug|--logs|--telemetry|--verify) ;;
  *) echo "usage: $0 [--build-only|--build-preview|--debug|--logs|--telemetry|--verify]" >&2; exit 2 ;;
esac
if [[ "$FINDLET_MODE" == --build-preview && "$#" != 1 ]]; then
  echo "--build-preview accepts no other arguments." >&2
  exit 2
fi
FINDLET_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FINDLET_ROOT"
FINDLET_DIST="$FINDLET_ROOT/dist"
FINDLET_APP="$FINDLET_DIST/Findlet.app"
FINDLET_PREVIEW_NAME="Findlet-0.1.1-macos-universal.zip"
FINDLET_PREVIEW_COMPLETE=0
if [[ "$FINDLET_MODE" == --build-preview ]]; then
  FINDLET_BUILD_FLAGS=(--configuration release --build-system native --disable-local-rpath)
  if [[ -n "${FINDLET_SWIFTPM_CACHE:-}" ]]; then
    if [[ "$FINDLET_SWIFTPM_CACHE" != /* || ! -d "$FINDLET_SWIFTPM_CACHE" || -L "$FINDLET_SWIFTPM_CACHE" ]]; then
      echo "FINDLET_SWIFTPM_CACHE must be an existing absolute directory, not a symlink." >&2
      exit 1
    fi
    FINDLET_BUILD_FLAGS+=(--cache-path "$FINDLET_SWIFTPM_CACHE")
  fi
  command -v python3 >/dev/null || { echo "Preview packaging requires Python 3's standard library." >&2; exit 1; }
  if [[ -L "$FINDLET_DIST" || ( -e "$FINDLET_DIST" && ! -d "$FINDLET_DIST" ) ]]; then
    echo "Refusing an unsafe preview output directory." >&2
    exit 1
  fi
  for FINDLET_OUTPUT in "$FINDLET_DIST/$FINDLET_PREVIEW_NAME" "$FINDLET_DIST/$FINDLET_PREVIEW_NAME.sha256"; do
    if [[ -e "$FINDLET_OUTPUT" || -L "$FINDLET_OUTPUT" ]]; then
      echo "Preview output already exists; nothing was replaced: $FINDLET_OUTPUT" >&2
      exit 1
    fi
  done
fi
if [[ -f "$HOME/.codex/storage-policy.md" ]]; then
  FINDLET_GUARD="$HOME/Library/Application Support/LocalStorageGuard/storage_guard.py"
  [[ -f "$FINDLET_GUARD" ]] || { echo "Storage Guard is required by the workspace policy." >&2; exit 1; }
  python3 "$FINDLET_GUARD" preflight --need-gib 4
fi

if pgrep -x Findlet >/dev/null; then
  if [[ "$FINDLET_MODE" == --build-only || "$FINDLET_MODE" == --build-preview ]]; then
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

if [[ "$FINDLET_MODE" == --build-preview ]]; then
  swift build --product Findlet "${FINDLET_BUILD_FLAGS[@]}" --arch arm64 --scratch-path "$FINDLET_ROOT/.build/preview-arm64"
  FINDLET_ARM64_BINARY="$(swift build "${FINDLET_BUILD_FLAGS[@]}" --arch arm64 --scratch-path "$FINDLET_ROOT/.build/preview-arm64" --show-bin-path)/Findlet"
  swift build --product Findlet "${FINDLET_BUILD_FLAGS[@]}" --arch x86_64 --scratch-path "$FINDLET_ROOT/.build/preview-x86_64"
  FINDLET_X86_64_BINARY="$(swift build "${FINDLET_BUILD_FLAGS[@]}" --arch x86_64 --scratch-path "$FINDLET_ROOT/.build/preview-x86_64" --show-bin-path)/Findlet"
else
  swift build --product Findlet
  FINDLET_BINARY="$(swift build --show-bin-path)/Findlet"
fi
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
  if [[ "$FINDLET_MODE" == --build-preview && "$FINDLET_PREVIEW_COMPLETE" == 0 ]]; then
    python3 - "$FINDLET_STAGE" "$FINDLET_DIST" "$FINDLET_PREVIEW_NAME" <<'PY'
from pathlib import Path
import stat
import sys

stage, output = map(Path, sys.argv[1:3])
for name in (sys.argv[3], sys.argv[3] + ".sha256"):
    source, target = stage / name, output / name
    try:
        left, right = source.lstat(), target.lstat()
    except FileNotFoundError:
        continue
    if (stat.S_ISREG(left.st_mode) and stat.S_ISREG(right.st_mode)
            and (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)):
        target.unlink()
PY
    if [[ -d "$FINDLET_STAGE/previous.app" ]]; then
      if [[ ! -e "$FINDLET_APP" && ! -L "$FINDLET_APP" ]]; then
        mv -n "$FINDLET_STAGE/previous.app" "$FINDLET_APP"
      fi
      if [[ -d "$FINDLET_STAGE/previous.app" ]]; then
        echo "Previous app preserved for recovery: $FINDLET_STAGE/previous.app" >&2
        return
      fi
    fi
  fi
  if [[ ! -e "$FINDLET_APP" && -d "$FINDLET_STAGE/previous.app" ]]; then mv "$FINDLET_STAGE/previous.app" "$FINDLET_APP"; fi
  rm -rf "$FINDLET_STAGE"
}
trap cleanup_findlet_stage EXIT
mkdir -p "$FINDLET_STAGE/Findlet.app/Contents/MacOS" "$FINDLET_STAGE/Findlet.app/Contents/Resources"
if [[ "$FINDLET_MODE" == --build-preview ]]; then
  /usr/bin/lipo -create "$FINDLET_ARM64_BINARY" "$FINDLET_X86_64_BINARY" -output "$FINDLET_STAGE/Findlet.app/Contents/MacOS/Findlet"
else
  cp "$FINDLET_BINARY" "$FINDLET_STAGE/Findlet.app/Contents/MacOS/Findlet"
fi
cp "$FINDLET_ROOT/Resources/Info.plist" "$FINDLET_STAGE/Findlet.app/Contents/Info.plist"
cp "$FINDLET_ROOT/Resources/AppIcon.icns" "$FINDLET_STAGE/Findlet.app/Contents/Resources/AppIcon.icns"
if [[ "$FINDLET_MODE" == --build-preview ]]; then
  cp "$FINDLET_ROOT/LICENSE" "$FINDLET_STAGE/Findlet.app/Contents/Resources/LICENSE.txt"
  cp "$FINDLET_ROOT/THIRD_PARTY.md" "$FINDLET_STAGE/Findlet.app/Contents/Resources/THIRD_PARTY.md"
  cp "$FINDLET_ROOT/docs/runtime-setup.md" "$FINDLET_STAGE/Findlet.app/Contents/Resources/SETUP.md"
fi
chmod +x "$FINDLET_STAGE/Findlet.app/Contents/MacOS/Findlet"
/usr/bin/plutil -lint "$FINDLET_STAGE/Findlet.app/Contents/Info.plist"
# Local ad-hoc signing needs no account, certificate or paid enrollment.
/usr/bin/codesign --force --sign - "$FINDLET_STAGE/Findlet.app"
/usr/bin/codesign --verify --strict "$FINDLET_STAGE/Findlet.app"
if [[ "$FINDLET_MODE" == --build-preview ]]; then
  [[ "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$FINDLET_STAGE/Findlet.app/Contents/Info.plist")" == 0.1.1 ]] || { echo "Preview archive version does not match its bundle." >&2; exit 1; }
  python3 - "$FINDLET_STAGE/Findlet.app" <<'PY'
from pathlib import Path
import stat
import sys

app = Path(sys.argv[1])
total = 0
for count, path in enumerate(app.rglob("*"), 1):
    if count > 512:
        raise SystemExit("Preview bundle exceeds 512 entries.")
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        total += path.stat().st_size
    elif not stat.S_ISDIR(mode):
        raise SystemExit("Preview bundle contains a nonregular entry.")
    if total > 32 * 1024 * 1024:
        raise SystemExit("Preview bundle exceeds 32 MiB.")
PY
  /usr/bin/ditto -c -k --rsrc --extattr --sequesterRsrc --keepParent "$FINDLET_STAGE/Findlet.app" "$FINDLET_STAGE/$FINDLET_PREVIEW_NAME"
  python3 - "$FINDLET_STAGE" "$FINDLET_DIST" "$FINDLET_PREVIEW_NAME" <<'PY'
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

stage, output = map(Path, sys.argv[1:3])
name = sys.argv[3]
archive = stage / name
if archive.stat().st_size > 8 * 1024 * 1024:
    raise SystemExit("Preview ZIP exceeds 8 MiB.")
with zipfile.ZipFile(archive) as package:
    entries = package.infolist()
    if len(entries) > 512 or sum(row.file_size for row in entries) > 32 * 1024 * 1024:
        raise SystemExit("Preview ZIP exceeds its expansion budget.")
    seen = set()
    for row in entries:
        path = PurePosixPath(row.filename)
        mode = row.external_attr >> 16
        if (row.filename in seen or path.is_absolute() or ".." in path.parts
                or not path.parts or path.parts[0] not in ("Findlet.app", "__MACOSX")
                or row.filename != path.as_posix() + ("/" if row.is_dir() else "")
                or "\\" in row.filename or any(ord(char) < 32 or ord(char) == 127 for char in row.filename)
                or row.flag_bits & 1 or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))):
            raise SystemExit("Preview ZIP contains an unsafe entry.")
        seen.add(row.filename)
        data = package.read(row)
        if path.parts[0] == "__MACOSX":
            parts = path.parts[1:]
            if not parts and row.is_dir():
                continue
            if not parts:
                raise SystemExit("Preview ZIP metadata has no bundle owner.")
            if row.is_dir():
                owner_parts = parts
            elif parts[-1].startswith("._") and len(parts[-1]) > 2:
                owner_parts = (*parts[:-1], parts[-1][2:])
                if data[:8] != b"\x00\x05\x16\x07\x00\x02\x00\x00":
                    raise SystemExit("Preview ZIP metadata is not AppleDouble.")
            else:
                raise SystemExit("Preview ZIP metadata has an unsupported name.")
            if not owner_parts or owner_parts[0] != "Findlet.app":
                raise SystemExit("Preview ZIP metadata has no bundle owner.")
            owner = stage.joinpath(*owner_parts)
            if not owner.exists() or owner.is_symlink():
                raise SystemExit("Preview ZIP metadata refers to an unknown entry.")
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
with (stage / (name + ".sha256")).open("x", encoding="ascii") as destination:
    destination.write(checksum + "  " + name + "\n")
published = []
try:
    for leaf in (name, name + ".sha256"):
        source, target = stage / leaf, output / leaf
        os.link(source, target, follow_symlinks=False)
        published.append((target, source.stat()))
except BaseException:
    for target, owned in reversed(published):
        current = target.lstat()
        if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
            target.unlink()
    raise
PY
fi
if [[ -e "$FINDLET_APP" ]]; then mv "$FINDLET_APP" "$FINDLET_STAGE/previous.app"; fi
mv "$FINDLET_STAGE/Findlet.app" "$FINDLET_APP"
if [[ "$FINDLET_MODE" == --build-preview ]]; then FINDLET_PREVIEW_COMPLETE=1; fi

case "$FINDLET_MODE" in
  --build-only) echo "Built and locally ad-hoc signed: $FINDLET_APP" ;;
  --build-preview) echo "Built a locally ad-hoc signed universal preview: $FINDLET_DIST/$FINDLET_PREVIEW_NAME" ;;
  --debug) lldb -- "$FINDLET_APP/Contents/MacOS/Findlet" ;;
  --logs|--telemetry)
    /usr/bin/open -n "$FINDLET_APP"
    /usr/bin/log stream --info --style compact --predicate 'process == "Findlet"'
    ;;
  --verify) /usr/bin/open -n "$FINDLET_APP"; sleep 1; pgrep -x Findlet >/dev/null ;;
  run) /usr/bin/open -n "$FINDLET_APP" ;;
esac
