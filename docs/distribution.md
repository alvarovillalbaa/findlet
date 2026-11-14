# Findlet preview distribution

The current release is **`v0.1.1-preview.1`**, containing app version **0.1.1**
(build 2) for macOS 15+. Fresh universal Release compilation, packaging and
CI acceptance [passed](results/2026/11-13/panel-preview-package.md).
The [unchanged passing assets are public](https://github.com/alvarovillalbaa/findlet/releases/tag/v0.1.1-preview.1);
native installation/runtime acceptance remains separate.

## Assets and trust

- `Findlet-0.1.1-macos-universal.zip`
- `Findlet-0.1.1-macos-universal.zip.sha256`
- `Findlet-preview-manifest.json`

The app executable targets **arm64 and x86_64**. Node, QMD, native bindings and
models are not included. Their architecture/ABI compatibility is separate;
a universal app does not prove an Intel QMD runtime works. See the
[runtime setup guide](runtime-setup.md), also bundled verbatim as
`Findlet.app/Contents/Resources/SETUP.md`.

The preview uses an **ad-hoc signature**, with no Developer ID identity or
TeamIdentifier. It is **not notarized**. Signature integrity and a checksum do
not establish publisher identity, Gatekeeper acceptance, fresh-Mac installation
or full-product acceptance. Apple describes these separate boundaries in its
[code-signing](https://developer.apple.com/documentation/security/seccodesignatureflags/adhoc)
and [notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
documentation.

## Inspecting a published preview

Download the ZIP, checksum and manifest from the preview release above. Compare the
archive's digest with both records before extracting:

```sh
shasum -a 256 Findlet-0.1.1-macos-universal.zip
```

Extract with Finder's Archive Utility. The archive contains `Findlet.app`;
the runtime setup and license notices are inside its Resources directory.
If macOS refuses the download, stop and inspect the source or wait for a
trusted distribution. No quarantine-removal or security-bypass step is part
of this preview. Apple's [macOS code-signing overview](https://support.apple.com/en-ca/guide/security/sec3ad8e6e53/web)
explains the default Gatekeeper requirements.

## Building the preview from source

Use a reviewed source checkout on macOS 15+ with a compatible Swift toolchain
and macOS 15+ SDK, Apple's command-line packaging tools, and **Python 3's
standard library**. Meet the repository's Storage Guard reserve before building.
Close any running Findlet yourself, then run:

```sh
./script/build_and_run.sh --build-preview
```

This mode builds without launching or quitting the app. It compiles native
SwiftPM Release slices separately for arm64 and x86_64, disables local build
rpaths, and joins them with `lipo`. The complete bundle receives `LICENSE.txt`
from root `LICENSE`, root `THIRD_PARTY.md`, and the exact runtime setup guide
before ad-hoc signing. See Apple's [universal-binary guidance](https://developer.apple.com/documentation/apple-silicon/building-a-universal-macos-binary).

Outputs are `dist/Findlet.app`, the ZIP and its `.zip.sha256` sidecar. Existing
archive/sidecar paths are refused. The separate CI controller produces the
manifest. Packaging uses metadata-preserving `ditto` ZIP options, bounded to
8 MiB archived, 32 MiB expanded and 512 members. The passing CI checks include fresh
extraction and matching bundle bytes, modes, xattrs and signature; nonempty
resource-fork preservation is not established merely by empty-xattr results.

The older ten native/core checks and accepted K01/K02 keyword integration
remain their own evidence; this packaging scope does not rerun them. The
separate [native Debug journey](results/2026/11-13/native-search-ui.md) now passed
setup/search/Finder/shortcut/normal Quit/reopen/confirmed Forget on authored
files. User permissions/private folders, general semantic quality, strict
network-offline operation and trusted distribution remain separate.

The [publication record](results/2026/11-13/panel-preview-publication.json)
verifies the exact public tag and server asset digests. Direct anonymous shell
asset downloads failed DNS; no anonymous body match or fresh downloaded-app
launch is claimed. The prior0.1.0 assets remain unchanged.
