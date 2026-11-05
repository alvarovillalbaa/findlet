# Native checks v2 — prepared, unrun

5 November 2026. Standing “I approve everything” / “Do all the work” authorizes
this focused CI packet. The [old proposal](native-checks.md), example, ten tests
and build script remain unchanged. The [new example](native-checks-v2-ci.yml.example)
is inactive; there is no compilation, test or package result yet.

One public `alvarovillalbaa/findlet` job on `macos-15` is limited to 15 minutes,
scoped to `qa/findlet-native-20261105`. Pin the clean preparation SHA. Verify
preinstalled Xcode 16.4 (16F6), Swift 6.1.2 and macOS SDK 15.5; no fallback or
toolchain/dependency installation. Controller: `script/run_native_checks.py
--source-commit <SHA>`; work/cleanup/stdout bounds are 720/90/2 seconds.

1. Execute only the ten existing methods in
   [QMDContractTests.swift](../../Tests/FindletCoreTests/QMDContractTests.swift),
   class `FindletCoreTests.QMDContractTests`. Require exact unique XCTest
   identities, totals/statuses, no failure/error/skip and actual CLI exit 0.
   These are in-memory argument/JSON/manifest contracts, not QMD execution.
2. Run the actual byte-identical [build script](../../script/build_and_run.sh)
   with `--build-only`. Verify `dist/Findlet.app`: native executable/Mach-O
   architecture, `com.alvarovillalbaa.Findlet` plist, source-exact icon,
   plist validity and strict local ad-hoc signature. No sandbox entitlement
   is supplied or claimed. Do not launch, upload or release the bundle.

Full HEAD/index/path/mode/blob/working-byte guards protect the checkout.
Export only `Package.swift`, all `Sources/`, `Tests/`, `Resources/` and the actual
build script into owned scratch, at most 2 MiB. Record each tracked path/mode/
blob/size/hash and verify copied identities before/after tools. This is a bounded
native-input export, without docs/artwork/history/dependencies. Tests reuse
the export's `.build`; packaging writes `.build`/`dist` only there. Remove the
owned root after verified process-group/EOF/reaping closure; preserve uncertain
residue. System/compiler caches outside that inventory remain qualified.
Retain bounded complete command streams, hashes, toolchain, ten outcomes and
cleanup in the owning result. Local storage reserve blocks local builds;
execution is remote only.

No app launch/UI, shortcut, permission prompt, personal-folder scan, QMD/Node,
model download/inference, actual retrieval, offline-network claim, Developer ID,
notarization or distribution acceptance. Those [runtime requirements](../specs/local-search.md)
remain open; a native compile/package pass does not close them.
