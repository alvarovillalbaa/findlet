# First native attempt — compiler failure

5 November 2026. **Failed; zero tests or packages accepted.** Preserve this
result before source repair. The ten existing XCTest cases, application
packaging and signature verification were not reached.

Checked source `507f025929f18ab509ad36b8765190c610cab255`, tree
`3d3e83b856a5fa47a093c57c1575ec20208717cd`: 37 tracked files / 261,594 bytes.
[Run 42122974426](https://github.com/alvarovillalbaa/findlet/actions/runs/42122974426),
job `127579814618`, ran **22:36:55–22:37:38 UTC**, 43 seconds. Actual runner:
macOS 15, arm64, Xcode 16.4 (16F6), Swift 6.1.2 and macOS SDK 15.5.

The actual unchanged `--build-only` script compiled FindletCore, then application
compilation failed at `Sources/Findlet/Services/HotKeyController.swift:20`:
`cannot find 'ByteCount' in scope`. That was the only distinct compiler error
in the complete 32,868-byte build stdout. The unavailable type wraps the hotkey
event buffer length. This is an actual compiler result, separate from earlier
syntax-only checks. No weaker check or removed test substitutes for compilation.

The [raw JSON](native-checks-attempt-1.json) is **46,609 bytes**, SHA256
`e895f94e4dc113abebee2b109fec48de35f095ec4da40205bfb823b816aac2b1`.
All 34 original command streams were independently decompressed and checked
against byte counts/SHA256. Sixteen commands exited zero; the build exited 1.
All 17 children were reaped, both streams reached EOF and original process
groups disappeared without a stop reason or forced drain.

Two full canonical source guards passed before execution and after cleanup.
The exact 19-file / 167,283-byte native-input subset had matching pre-tool and
pre-cleanup export guards. The generated `.build` and owned scratch were removed;
canonical ignored output was empty. This does not inventory detached sessions
or compiler/system caches outside the owned tree.

No app launch, QMD/Node/model, indexing, user folder, account, paid service or
distribution operation occurred. The original test/build-script bytes remain
unchanged. Repair only the SDK API type, then rerun the same ten-case/native
package scope against a new immutable source. Native UI, actual retrieval and
distribution remain separate requirements.
