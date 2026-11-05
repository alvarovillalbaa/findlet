# Findlet native build, ten core cases and package verified

5 November 2026. **Passed within the compile/core/package scope.** Findlet is
not yet a released or fully accepted Mac application. No app launch or QMD
execution is implied.

Checked source [`b59af255`](https://github.com/alvarovillalbaa/findlet/tree/b59af255b48581bb9fd250a96d7e8f7a9f7759d9),
tree `73da9938f52a48fdaa75ddc21b4ab49181a89b06`: 39 tracked files / 311,507 bytes,
matched across clean native HEAD/index/working bytes and the immutable GitHub
tree before activation. [Run 42123792452](https://github.com/alvarovillalbaa/findlet/actions/runs/42123792452),
job `127582625371`, ran **22:42:55–22:43:57 UTC**; controller work was
**22:43:02–22:43:52 UTC**. Actual runner: macOS 15.8.2/arm64, Xcode 16.4
(16F6), Swift 6.1.2, macOS SDK 15.5 and Python 3.15.2. No toolchain, dependency,
QMD runtime, Node or model was installed.

## Actual repair and result

The [first attempt](native-checks-attempt-1.md) failed compilation at
`HotKeyController.swift:20`, before tests or packaging. Its full raw result was
published before repair. The code attempted to construct the unavailable Swift
alias `ByteCount`. Swift's [primary importer map](https://github.com/swiftlang/swift/blob/main/lib/ClangImporter/MappedTypes.def#L62)
maps that C type to `Int` without preserving the alias. Passing the existing
`MemoryLayout<EventHotKeyID>.size` directly removes the unnecessary wrapper.
The actual selected-toolchain build then accepted this one-expression change.
Hotkey registration and runtime behavior were not exercised.

The original test file, all ten names/assertions, actual build script and reviewed
controller remain unchanged. All **ten exact XCTest identities passed once**:
CLI exit zero, one worker, no retry, and emitted XML with ten tests and zero
failures/errors/skips. The cases cover literal arguments and UTF-8 limits,
manifest identity, duplicate chunks/manifests, accepted owned paths, rejected
outside/virtual paths, malformed/oversized output and real empty results.
They use in-memory values and lexical URL strings; no folder or QMD corpus is created.

The unchanged `script/build_and_run.sh --build-only` compiled the real app and
created `Findlet.app` before test execution, without launching it. Actual strict
signature verification and ad-hoc identity checks passed, including another
strict check after tests. Effective entitlements were empty: this does not
establish App Sandbox enforcement, Developer ID or notarization.

Source-exact Info.plist and icon bytes passed. The bundle identifier was
`com.alvarovillalbaa.Findlet`, version 0.1.0/1, minimum macOS 15.0; all ten ICNS
representation tags were checked. Built/signed arm64 Mach-O UUIDs matched:
`b5f7bd29-7a3b-304e-84d4-50389150a16c`. Signing rewrites signature bytes, so
their distinct SHA256 observations are preserved rather than claimed equal:

- Built executable: `728c0fd30acbfb657c797bce904cdcf0b8aa82556f90195da59312a608fdf6a7`.
- Signed package executable: `50ba54c1f126a77d83f03f5c211cfcd3b7f3732ea52e4ae9f7a55f76f9508cab`.

## Source, evidence and cleanup

The [JSON receipt](native-checks.json) is **76,689 bytes**, SHA256
`0f1ef825ce5e8ada7625423b9d7db119ddb2835521fd604c2b7547b067747cac`.
It is the exact emitted JSON plus one LF; emitted JSON was 76,688 bytes,
SHA256 `bc0813652a131f82805dc675d884b5edb903817940e14cab9110e826dcb21bbf`.
All **60 complete original command streams** were independently decompressed
and checked for compressed size, original byte counts and SHA256. All 30 commands
exited zero, with child reaping, pipe EOF, closed streams and original process
groups absent, without a stop reason or forced drain. The emitted 1,611-byte
xUnit XML, SHA256 `d149a5bb59201b9096a5099c057eda18af0970bcaa81087ec36d867a018d979b`,
independently matched the original ten class/method identities.

Three full canonical source guards protected every path/mode/Git blob/working
byte and rejected ignored/untracked output. The bounded native-input export was
**19 files / 167,272 bytes**: Package.swift, all Sources/Tests/Resources and the
actual build script. Each copied path/mode/blob/length/SHA was recorded and
verified before tools, after work and before cleanup. No Git history,
dependencies, docs or earlier evidence was copied. This is an exact native-input
export build, not a full-repository fresh-install claim.

Generated `.build`, `dist` and the unique scratch root were verified owned and
removed only after process release. Final canonical ignored output was empty.
Separately detached sessions and compiler/system caches outside the owned paths
are not independently inventoried. GitHub owns final runner teardown.

Standing approval covered the bounded native scope and temporary public CI.
The two actual jobs used **43 + 62 = 105 seconds**; the final 14-minute ceiling
plus the first 43 seconds stayed below the original 15-minute allowance.
Temporary workflow `408719568` was verified `disabled_manually`, and its active
file was removed. Four later status documents and the two new receipts leave
**35 of 39 checked inputs unchanged**, including all 19 native build inputs,
the actual checker, original tests and build script. Final publication metadata
is recorded separately in the portfolio handoff.

## Remaining acceptance

The actual build/test streams retain 32 concurrency warning lines, representing
four distinct messages about NSLock calls from async contexts and Binding
sendability. The package remains in its existing Swift language mode; this pass
does not establish Swift 6 language-mode readiness or diagnose a runtime race.

No app launch, global shortcut, settings/bookmarks, Open/Reveal, file-provider
behavior, process cancellation, indexing/retrieval, semantic quality or strict
network-offline behavior was exercised. QMD/models, original folders and account
resources were untouched. Ad-hoc signing is not Gatekeeper/install acceptance,
Developer ID, notarization or a downloadable/store release. No paid service,
Vercel or Supabase resource is needed for this native local app. These remain
separate work under the active portfolio goal.
