# Native checks v2 — verified and retired

5 November 2026. Standing “I approve everything” / “Do all the work” authorizes
this focused CI packet. The [old proposal](native-checks.md), example, ten tests
and build script remain unchanged. The [new example](native-checks-v2-ci.yml.example)
is inactive. The [accepted result](../results/2026/11-05/native-checks.md)
records native compilation, all ten original cases and fresh ad-hoc packaging.
The [first actual attempt](../results/2026/11-05/native-checks-attempt-1.md)
failed before tests or packaging; its raw failure was published before repair.
The preparation and rerun instructions below are retained history.

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

## Compiler repair and same-scope rerun

The actual SDK rejected the unavailable `ByteCount` alias in hotkey handling.
The [primary Swift importer map](https://github.com/swiftlang/swift/blob/main/lib/ClangImporter/MappedTypes.def#L62)
maps that C type to `Int` without exporting its alias. Pass the existing
`MemoryLayout<EventHotKeyID>.size` value directly. This one-expression change
still needs the actual selected-toolchain compile; no integer-width guess or
shortcut behavior change is proposed. Tests, build script and controller stay
unchanged. All 34 first-attempt command streams and owned cleanup passed;
there was no xUnit or package result to carry forward.

The next job has a 14-minute ceiling. The first 43 seconds plus 840 seconds is
883, below the original 900-second allowance. Controller work/cleanup/stdout
remain 720/90/2 seconds, with the same ten cases and package assertions.

The repaired-source run `42123792452` / job `127582625371` passed once at
`b59af255b48581bb9fd250a96d7e8f7a9f7759d9`, 22:42:55–22:43:57 UTC. The two
jobs used 105 seconds total. All three source/export guards and scoped cleanup
passed; the temporary workflow is disabled and its active file removed. QMD,
native UI and distribution were not exercised.
