# Fifth QMD keyword attempt: D01 collected, both SQLite audits failed

7 November 2026. **Diagnostic failed; no K01/K02 or product acceptance.**
[Run 42388379135](https://github.com/alvarovillalbaa/findlet/actions/runs/42388379135),
job `128450525829`, tested source
[`a6ee6b2a7e030635be112da163d9480a0f60ebc6`](https://github.com/alvarovillalbaa/findlet/tree/a6ee6b2a7e030635be112da163d9480a0f60ebc6),
tree `cbe6a6307b335e682a7296bb7641c3f289f9614a`, activation
`c2b76be9c74c67a74237606bcb140986897e3793`.

`collectionComplete` is true, but `diagnosticAccepted`, `accepted` and
`productAccepted` remain false and CI failed. Both fresh, separate arms returned
zero for keyword update and SDK status, then failed the fixed read-only SQLite
audit with exit status 14. The field `pairedUpdatesSucceeded` is false because
the complete three-stage arms failed; it does not mean the update subprocesses
returned nonzero. The retained `phases` and `journeysExecuted` arrays are empty:
K01/K02 and the closed ten-test/full-application-build scope were not run.

The Python arm has actual original stdout/stderr for all three stages. Its
SQLite command returned empty stdout and 53 stderr bytes:
`Error: in prepare, unable to open database file (14)` followed by a newline,
SHA256 `5b77e976aa03a4a27e6fe41d23fcf4563efdcafba891b551be4d5ea2233df425`.
The SDK original reports three documents, three needing embedding and no vector
index. Those metadata observations do not establish an accepted Findlet index.

The Foundation arm used the actual production QMDProcessRunner. Its finite
diagnostic identifies `reason:exit`, `status:14` at `sqlite_audit`; message SHA256
`fd14685085b63c3fb18e23491bd511bb8dbb5904f7c6505bc35a05aa72fadf87`
independently matches the public error template. The two earlier stages returned
under the runner's existing success predicate. Their outputs are counts/hashes,
not retained originals; inner stderr remains discarded. The outer Swift harness
exited zero to report completed collection, which is distinct from arm success.
No signal termination is reported by these failed audit stages; the receipt does
not identify an underlying filesystem, SQLite, Node or launcher cause or a signal
sender. Earlier failed K01 fingerprints are not retroactively reclassified.

Both arms match normalized command, environment, initial configuration and
corpus roles, including the exact 526-byte production SDK program and 189-byte
SQL. Their owned absolute paths and launch settings differ; Python's new-session
and signal-restoration options are not proof of Foundation's inner spawn context.
The Foundation original matches its parsed report, including eight true checks,
11 directory identities, six unchanged corpus files and four unchanged selected
runtime roles. Initial curated configurations bind their authored hashes. Both
initial comparison configurations had different hashes by final collection;
their contents are not retained, so no exact rewrite contents are claimed.

Both compiler commands passed on macOS 15 ARM64 with Xcode 16.4/16F6, Swift 6.1.2
in Swift 5 language mode and SDK 15.5. Async-context NSLock warnings remain.
Node 26.13.0 and the frozen scripts-off / optional-omitting runtime admitted
better-sqlite3's bundled SQLite 3.53.4 and sqlite-vec v0.1.9 on Darwin and closed
the in-memory database. The system SQLite CLI version was not recorded.
The 82,521-byte lock original verifies with 179 package records and 151 installed
required-package bindings. These are runtime admissions, not product acceptance.

All 49 outer command records closed normally: 48 exited zero and the Python
SQLite audit exited 14. All 98 command-stream originals plus the lock original
verify: 99 gzip records, 192,654 decoded / 52,112 compressed bytes. Lengths,
observed digests, EOF and canonical base64 match. The log's unique result marker
reproduces the JSON file including its final newline. Privacy scans passed for
all six directly retained diagnostic streams; no authored body/query token was
published in them.

Five guards bind 48 source paths / 648,798 bytes to the recomputed vector
`42ea44d3335e3c477dd73d6f44cf4a5e9a6db01471206cc69124c638182074fe`.
Seven private source exports, four checks of the 10,856-entry runtime vector and
two compiled-file checks passed their recorded barriers. There are 62 attributed
PID/start observations, including the 49 direct commands. Every command records
reaping, EOF, descriptor closure and original process-group absence, with no
forced drain or signals. No attributed processes or unknown root references
remained at the pre-delete and final barriers. Owned cleanup verified 12,368
entries / 567,142,637 regular bytes and 31 directory identities, then removed
scratch. These are boundary observations, not a storage peak, continuous
host-wide or strict offline attestation.

Unchanged local originals, retained through lossless publication envelopes:

- [JSON](qmd-keyword-integration-attempt-5.json.gz): 573,389 bytes, SHA256
  `84a5ab63c5b9096aa3697b61cd0be5a41af36aeb5c2dfedc09bcfecd30d0c292`.
  Decodes byte-exactly to 3,438,470 bytes, SHA256
  `6549b4b9ffa857250bba7d526d0bb29d2bf74318cafff9d09f9eca3b2d1fc9d6`.
- [Full log](qmd-keyword-integration-attempt-5.raw.log.gz): 576,882 bytes, SHA256
  `ca863c5dc84f28849e82fba97f335f3aa59b26cda256ad4a8387d1c96b2992af`.
  Decodes byte-exactly to 3,455,692 bytes, SHA256
  `01ad5294b3d795690ed306f41bbd815d744c92287dfcbc92b21a66f726b9d8de`.

This local draft does not claim a final publication commit. No local product
execution, new payload download or model invocation occurred in this audit.
The diagnostic identifies the failing external stage in this attempt; it does
not prove a repair, retrieval/lifecycle behavior, private-folder or native UI
acceptance. All earlier failures remain preserved.
