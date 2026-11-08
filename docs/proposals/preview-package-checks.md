# Findlet current-app universal preview

8 November 2026. Alvaro's current all-project delivery instruction and standing
“I approve everything / Keep going / Do all the work” authorize this concrete
Findlet build/package/GitHub-preview scope. This is its own bounded scope;
another project's native-test approval is not being transferred.

Current clean main `ed5c688894035d3a10b59ac808b154b46fd01d2f` includes the
accepted QMD keyword repair, but the last full-app build preceded changes to
FindletEngine/QMDProcessRunner. A fresh complete app build and downloadable
developer preview close that integration/distribution gap. They do not establish
new retrieval, native interaction or trusted installation acceptance.

## Source and distribution

Add `--build-preview` to the existing builder. Preserve all ordinary modes;
preview refuses a running Findlet without quitting it and publishes ZIP/checksum
leaves exclusively. Build Release arm64 and x86_64 separately with native
SwiftPM, distinct scratch paths, matched binary-path queries, scoped caches and
local loader rpath disabled. Merge the actual binaries with `lipo` into the
existing staged app, then use its plist/icon/ad-hoc signing path. Preserve
previous output on failure and roll back only inode-bound partial artifacts.

Bundle source-exact LICENSE.txt, THIRD_PARTY.md and SETUP.md as readable resources
before signing. SETUP.md comes from the maintained runtime guide. Keep QMD,
Node, native bindings, models, configurations, indexes and user documents outside
the archive. The established product contract requires a compatible trusted
external runtime; universal app slices do not prove Intel QMD compatibility.
This is a developer preview with external setup, not self-contained search.

App source, Package.swift, existing resources, old tests and dependency/permission
policy stay unchanged. Preserve all prior failed and accepted native/keyword
evidence. Do not rerun the ten core cases or K01/K02 without changed inputs or
a concrete concern; no test/provider/model acceptance carries into this scope.

## One free native packaging invocation

Use one temporary public macOS 15 job, capped at 20 minutes, fixed reviewed
source and `qa/findlet-preview-20261108-1`. No arbitrary dispatch inputs. The
push-only QA workflow checks out the exact preparation commit with its source
parent available; main has no executing workflow. Disable/retire the temporary
control after terminal evidence. Preserve any failure before a changed control.

Export only tracked native package/app/core-test layout, current builder,
resources and the three notice/setup source files. Include old test sources
only for SwiftPM target discovery; do not execute them. Exclude histories,
older evidence, QMD harnesses, dependency locks, runtime tools and private data.
Keep HOME intact and all owned export/build/cache/temp paths private and bounded.

Verify source/index/body/modes; actual toolchain/SDK; source plist identity,
0.1.0/build 1 and macOS 15.0 minimum; both real executable slices/deployment
targets; each slice's system libraries/search paths; ad-hoc identity/strict
signature; source-exact icon/notices/setup; and bounded archive paths/payloads.
Extract the actual ZIP with metadata-preserving `ditto` into fresh owned scratch;
compare every bundle file/directory byte/mode/attribute and verify signatures
again. Preserve quarantine/metadata; use bounded read-only Darwin attribute APIs.

Bounds: 8 MiB ZIP, 32 MiB expanded, 512 archive members; 4 GiB owned scratch and
sampled attributed-child RSS, 64 processes, 900-second work and 150-second cleanup
budgets within the 20-minute job. Retain complete bounded command originals,
ZIP/checksum/manifest bytes and finite errors. Attribute child processes/groups,
verify their absence, then delete only verified owned output. Late failure or
forced signals keep the result failed. Unrelated system services are outside it.

Publish unchanged passing assets as GitHub prerelease `v0.1.0-preview.1`:
`Findlet-0.1.0-macos-universal.zip`, its `.zip.sha256`, and
`Findlet-preview-manifest.json`. Verify actual server asset digests and source
tag. No app launch, shortcut/bookmark/permission interaction, private folders,
Node/QMD/bindings/model install or invocation, search, inference, dependency
upgrade, account, payment, notarization or hosted provisioning. App signing is
ad-hoc; native runtime/Gatekeeper/fresh-Mac/semantic/offline gates remain open.

Local Storage Guard reports 9.0 GiB free against 34.0 GiB required. No local
build/install/app/test/native-call exception. Source/Bash/Python syntax checks
and bounded data-only evidence handling are allowed; native execution stays in
the owned public CI. The source/build/service/distribution boundaries remain
separate in canonical results and the [distribution guide](../distribution.md).

## Terminal packaging acceptance

The [first invocation](../results/2026/11-08/preview-package-attempt-1.md)
passed the current full-app universal Release build, all 18 commands, strict
signatures, source-exact bundled notices/setup and fresh ZIP round-trip.
Owned cleanup passed. This packaging scope is closed; do not repeat it or
the older core/keyword scopes as routine follow-up. Publish only the exact
retained assets and record actual public tag/digests. External runtime, Intel
engine/native UI/Gatekeeper/model/offline acceptance remains separate.
