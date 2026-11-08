# Current Findlet universal Release preview — passed

8 November 2026. [Run 42472095274](https://github.com/alvarovillalbaa/findlet/actions/runs/42472095274),
job `128705023953`, passed at source
`fabe5b3d2c2bc385324f66ed34aeb442c2de19bb` under workflow
`1fc67584b42cda4658ffdcf06b5df6796f6360f5`.

## Fresh full-app build and bundle

Both current-app native SwiftPM Release builds completed, arm64 and x86_64,
with separate scratch paths, matched binary-path queries and local loader
rpaths disabled. `lipo` merged their actual binaries. The shared packaging
flow copied the source plist/icon and license/third-party/setup resources,
signed the complete app ad-hoc, then created the metadata-preserving ZIP and
checksum. Fresh `ditto` extraction matched every bundle payload/directory,
byte, mode and observed attribute; strict signatures passed before/after for
all architectures. Actual attribute maps were empty, providing no nonempty
resource-fork preservation experiment.

All **18 commands exited zero**, with 36 complete original stdout/stderr streams.
Toolchain: arm64 host, macOS 15.8.2, Xcode 16.4 / 16F6, Swift 6.1.2, SDK 15.5.
Both executable slices declare macOS 15.0 minimum; per-slice library/search-path
inspection passed. Plist identity is `com.alvarovillalbaa.Findlet`, version
0.1.0/build 1. This is an ad-hoc seal without team identity, Developer ID,
notarization or Gatekeeper acceptance.

The native source/index/body/mode vector binds 73 files / 6,835,475 bytes,
tree `2d3487a38c22170fc12587b043145d4958fefd27`, directly based on `ed5c6888`.
Of the 19 pre-existing native inputs, 18 stay unchanged; the builder intentionally
adds preview packaging and the minimal export adds three notice/setup inputs.
The service repair had changed FindletEngine and
QMDProcessRunner since the older full-app build; this run freshly compiles
the complete current app. It does not merely reuse the old app-less harness.

The ten core cases and accepted K01/K02 retain their original source/profiles.
Their relevant core/test/keyword inputs stay unchanged; neither scope was rerun.
No app launch, shortcut/bookmark/permission interaction, search, Node/QMD/native
binding or model install/invocation occurred. No private folder was indexed.

## Retained distribution assets

The bundle has seven payload files and five directories: executable, plist,
icon, source-exact LICENSE.txt, THIRD_PARTY.md, SETUP.md and signature resources.
SETUP.md is the maintained runtime guide, SHA-256
`a9de5573ba6c08bf916af2ac5e9a45197dd68e341f9e012c3f1184bf2d966e36`.
The universal executable is 3,178,048 bytes, SHA-256
`53088e6487fc590c76335d993c0e4342741746fcfe0f310bf654d3f2eeb90042`.

| Exact retained asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Findlet-0.1.0-macos-universal.zip` | 868,206 | `d905ca59173ba50011779da89a972b83a566df6924d30ef8eb6d30f265dfc4ed` |
| `Findlet-0.1.0-macos-universal.zip.sha256` | 100 | `44e0622240dad48f68ca95f3fc5f28811668dd513a8c5e7ffe97edc319d7274c` |
| `Findlet-preview-manifest.json` | 2,350 | `35a089ab418621dc49537eeea6078ec9152c9f7bc5a7e78ff7a482e48b37965e` |

The manifest explicitly keeps `externalRuntimeBundled`,
`runtimeInstalledOrInvoked`, `engineAcceptancePerformed` and
`intelEngineAcceptanceVerified` false. Compatible trusted Node 22+, QMD 2.8.3
and native bindings remain user-supplied prerequisites. The app binary's Intel
slice does not prove Intel QMD or model compatibility. Keyword needs no model;
Semantic/Hybrid still require existing compatible GGUF files and explicit setup.

Independent in-memory audit rehashed all 39 captures (36 command streams and
three retained assets), all 12 ZIP members / 3,232,824 expanded bytes, and every
payload/mode/source notice. Both raw Mach-O slices have valid bounds, 52 load
commands, macOS 15.0 targets, 35 absolute system-library links and no LC_RPATH.
Their ad-hoc CodeDirectories contain no team offset; all 755 code pages, six
special slots and four sealed resource hashes were independently verified.
This inspected bytes, without extracting/installing/launching the app or
invoking a local native tool, and supplies no publisher-trust or engine proof.

## Ownership and limits

Independent data-only audit verifies all native source blobs/tree, exact parent,
18 command identities and all 36 complete observed streams. Controller elapsed:
67.136 seconds. Sampled peaks: 165,514,928 bytes owned storage, 624,492,544 bytes
attributed-child RSS, five processes. Cleanup verified 569 removed entries,
71 process identities/54 groups, zero remaining owned processes/signals and
absent root. The final removed inventory is digest-only; RSS/process sampling
excludes unrelated Apple/Xcode services and applies no address-space limit.

Workflow `411059301` is disabled and QA1 retired at
`46b73dd8364d8c155362b260e8ce9e98093b3db1`. The older native workflow stays
disabled. Main contains no executing workflow. The unchanged passing assets
are public as `v0.1.0-preview.1`.

The [publication record](preview-package-publication.json) verifies public
prerelease `438179724`, published 10:44:55 UTC at tag/source closure
`a5d202ebe215f58e1dce3e9e52ec064d775c428a`, and all three actual server asset
sizes/SHA-256 digests. This proves GitHub artifact publication, without a fresh
anonymous installation or downloaded-app launch. Later status docs preserve
every checked app/build/controller/setup-guide input.

| Immutable original | Bytes | SHA-256 |
| --- | ---: | --- |
| [Receipt](preview-package-attempt-1.json) | 1,190,676 | `6291df5343e3984fe0e4e713d3f7d92e68e9faceaa54cd3a697566ff75859632` |
| [Full job log](preview-package-attempt-1.log) | 1,207,653 | `4318e50cc2c70cea222400f54b93fdd7940705d325d1775d1037f7444cb3bea0` |

The original build output retains 32 warning lines about existing async locking
and Binding sendability. No Swift 6 language-mode readiness or runtime-race
resolution is claimed. Native UI/settings/permissions/private-file behavior,
fresh downloaded-app/Mac launch, Gatekeeper/notarization, Intel engine operation,
semantic quality, strict offline behavior and full-product acceptance stay open.
No local app/build/test/native-library execution, new account, paid service,
provider/model call or hosted resource was needed.
