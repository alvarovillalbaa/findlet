# Third QMD keyword attempt: bounded failure fingerprint

7 November 2026. **Failed; no K01 or K02 journey acceptance.**
[Run 42385493265](https://github.com/alvarovillalbaa/findlet/actions/runs/42385493265),
job `128441877594`, tested source
[`d5ced91197ff819ee491209f97b008c7ca5cc8d0`](https://github.com/alvarovillalbaa/findlet/tree/d5ced91197ff819ee491209f97b008c7ca5cc8d0),
tree `18d498e105519b6dfb758fad638b3b6b83b1955f`, with activation
`7939881dfb5d68c8c7e7a110a5f7f8f36f38dd73`.

This attempt added harness-only classification to the existing failure path.
The outer result remains `failed` / `accepted:false`, with
`harness_phase_failed`. K01 created the authored fixture and entered
`production_rebuild`, then returned `production_production_rebuild_refused`.
Its checks and query proofs are empty; no pointer/state or private handoff was
retained as accepted evidence. The independent index audit was not reached.
K02 did not run. The closed ten core cases and full application build were not
repeated.

The actual diagnostic is `kind:findlet_message`, `stage:production_rebuild`, and
message SHA256
`2df4754c8c2f98a00a6813c6abee313cbaca12bfa793f89f2dbbc3a5f812e4dd`.
An independent local comparison binds the unchanged
[public QMDProcessRunner template](https://github.com/alvarovillalbaa/findlet/blob/d5ced91197ff819ee491209f97b008c7ca5cc8d0/Sources/Findlet/Services/QMDProcessRunner.swift#L89)
to this hash when its status interpolation is `14`; the source file itself
matches the receipt's SHA256
`b44f8e08b2e8268c9687442b4b7d4cf733186f114b124727c43ecf724251bc30`.
That guard combines termination reason and status, but the diagnostic does not
retain `terminationReason`. It establishes neither a normal exit code nor a
signal interpretation, nor which inner operation or underlying cause failed.
No raw error message, userInfo or inner QMD stdout/stderr was added to the
diagnostic. Production QMD stderr is discarded internally; the retained outer
streams cannot reconstruct it.

Both app-less compile commands passed with Xcode 16.4/16F6, Swift 6.1.2 in
Swift 5 language mode, and SDK 15.5 on macOS 15 ARM64. Async-context NSLock
warnings remain; this is not Swift 6 language-mode readiness.
The hash-pinned 58,334,661-byte Node archive passed inventory and extraction:
5,828 logical entries, 4,743 regular files / 221,464,747 bytes, and two symlinks.
Both passes matched decoded structural-header hashes; original tar headers
were not retained. The first archive-bound failure remains preserved.

Node 26.13.0, the frozen scripts-off / optional-omitting install, and actual
Darwin ARM64 native admission passed. SQLite 3.53.4 and sqlite-vec v0.1.9 loaded
in an in-memory database, which closed. The 82,521-byte lock original verifies,
with 179 package records and 151 installed required-package bindings.
The 10,856-entry runtime vector matched after admission and before cleanup;
compiled-file continuity passed before K01. These admissions do not establish
successful application indexing.

All 40 command records closed normally: 39 exited zero and K01 exited one.
All 80 command-stream originals and the lock original verify: 81 gzip records,
175,489 decoded / 46,483 compressed bytes, with complete observed lengths and
hashes. The log's unique report marker reproduces the JSON file including its
final newline. Native-admission, resolved-tree and failed-harness parsed values
match their actual stdout originals.

Four guards bind all 48 source paths / 603,796 bytes with one unchanged vector;
all seven private source exports also passed their recorded barriers. There
are 56 attributed PID/start observations, including 40 direct commands. No
signals, remaining attributed processes or unknown root references were
recorded; EOF, descriptor closure, reaping and original process-group absence
passed for every command. Cleanup verified 12,361 entries / 566,653,250 regular
bytes and 20 directory identities, then removed scratch. These are boundary
observations, not a storage peak, continuous host-wide or offline attestation.

Lossless publication envelopes retain the unchanged local originals:

- [JSON](qmd-keyword-integration-attempt-3.json.gz): 569,479 bytes, SHA256
  `1e10ca1f5977e24bbd78d1a2449e190480bfb4341f729f4bca44462e9bc78e78`.
  Decodes byte-exactly to 3,403,229 bytes, SHA256
  `ef3b7112a7f91d7c91c0ec7b19e83a99b0539cacc86061c80fb98ebceba730b9`.
- [Full log](qmd-keyword-integration-attempt-3.raw.log.gz): 573,562 bytes, SHA256
  `374d7f0940361d5fe2bbc09dce8f044529f1e229e61cc156c79ecfd7ea3d1bc8`.
  Decodes byte-exactly to 3,420,452 bytes, SHA256
  `c97cf701452f874ad4b597c5166cd45757b101e387b342da9dd6c8dd7149e95d`.

Original files were retained before further changes. Final publication metadata
is recorded separately from these immutable observations.
The audit executed no local product code or new download. No product repair,
retrieval, lifecycle, private-folder, semantic/model, native UI or distribution
acceptance follows from the fingerprint. All earlier failures remain preserved.
