# Fourth QMD keyword attempt: diagnostic harness compile failed

7 November 2026. **Failed; D01 did not execute.**
[Run 42387865510](https://github.com/alvarovillalbaa/findlet/actions/runs/42387865510),
job `128448999855`, tested source
[`b6e752dfb3afb017fed14f86d7d8c7d3272ceed6`](https://github.com/alvarovillalbaa/findlet/tree/b6e752dfb3afb017fed14f86d7d8c7d3272ceed6),
tree `10d4a41f54ecfc79ae6bb589b5f52f1bfdbf208b`, activation
`c15f825982e67e5b48b242d96a7a8a7190f92ff8`.

The Core compiler command exited zero. The app-less harness compiler exited one
with Swift 6.1.2, Xcode 16.4/16F6 and SDK 15.5, targeting macOS 15 ARM64 in Swift
5 language mode. Its original stderr identifies the nested `paths` expression
using array concatenation, `flatMap` and `map` at harness line 975: the compiler
was unable to type-check it in reasonable time and requested smaller expressions.
Async-context NSLock warnings also remain; this is not Swift 6 language readiness.

The outer result is `failed` with `command_exit_refused`. Collection completion,
paired updates, diagnostic acceptance, journey acceptance and product acceptance
are all false. No Node download/execution, package installation, native SQLite
admission or D01 Python/Foundation arm was reached. K01/K02 were not run; the
closed ten core cases and full application build were not repeated. This compile
failure adds no evidence about the earlier status-14 fingerprint or its cause.

All 27 command records closed normally: 26 exited zero and `compile_harness`
exited one. The 54 stdout/stderr originals verify as complete gzip records:
35,566 decoded / 15,703 compressed bytes, with matching observed lengths and
SHA256 values. The full log's unique result marker reproduces the JSON original
including its final newline. The failed compiler stderr was independently decoded.

Three guards bind the same 48 source paths / 647,806 bytes, Git modes, bodies and
index; their recomputed vector is
`3ae09f1ec838f792cc991fb95ecb6095dccb192b81b40ad89608befaa49de4bd`.
Seven owner-only source exports passed their before-compile and before-cleanup
barriers. There are 40 attributed PID/start observations, including 27 direct
commands. Every command records EOF, closed descriptors, reaping and original
process-group absence, with no forced drain or signals. No attributed process
or unknown root reference remained at the pre-delete and final barriers.

Owned cleanup verified 139 entries / 32,741,309 regular bytes and 20 directory
identities, then removed scratch. These are boundary observations, not a storage
peak, continuous host-wide attestation or strict offline proof.

Unchanged originals retained for publication:

- [JSON](qmd-keyword-integration-attempt-4.json): 68,213 bytes, SHA256
  `490ab5ee613053334be53c0827746fc9d57f00c35af957a3991fc93ee3fca8d9`.
- [Full log](qmd-keyword-integration-attempt-4.raw.log): 85,442 bytes, SHA256
  `36fa2ee1ca21e4dda8d7398cf32baa3318aa94cefb524845753eed71c280bd81`.

This local receipt does not claim a final publication commit. No local compiler,
product, model or downloaded payload was executed for this audit. A changed
typed-expression repair remains unverified here; all earlier failures and their
originals remain preserved. No QMD launch comparison or application repair is
established by this attempt.
