# Sixth QMD keyword attempt: immutable-read candidate observed

7 November 2026. **Collection complete; diagnostic and product acceptance false.**
[Run 42390052907](https://github.com/alvarovillalbaa/findlet/actions/runs/42390052907),
job `128455549686`, tested source
[`d40b7b4f5136802faa9d33fe3d0fac6d93095a70`](https://github.com/alvarovillalbaa/findlet/tree/d40b7b4f5136802faa9d33fe3d0fac6d93095a70),
tree `5290a9061178ba67acf86941ac95f4875ed0fe75`, activation
`dc19366703f645b5e674c2216ddeab549e1c93d3`.

D02 retained fresh D01 Python/Foundation controls, then compared read-only
SQLite connections to each lane's owned database. Both controls returned zero
for keyword update and SDK status, then their original SQLite audit (M0) failed
with exit status 14. The matrix produced these actual outcomes in both lanes:

M1–M3 were direct Python-managed CLI probes on the Python-produced and
Foundation-produced databases, not extra Foundation-runner invocations.

| Probe | Connection form | Python / Foundation database lane result |
| --- | --- | --- |
| M0 | Original `-readonly` path | Exit 14 / exit 14; retained failure |
| M1 | `-init /dev/null`, ordinary read-only path | Exit 14 / exit 14 |
| M2 | Empty init, escaped file URI `mode=ro` | Exit 14 / exit 14 |
| M3 | Empty init, escaped URI `mode=ro&immutable=1` | Exit 0 / exit 0; exact expected rows |

Both M3 stdout originals parse to the exact three authored UUID `.md` paths in
`findlet_documents`, each with integer `content_present:1`, with no extra rows
or fields and empty stderr. The direct failed SQLite commands retain the same
53-byte inability-to-open-database stderr observed in attempt five. Foundation's
M0 reports finite `reason:exit`, `status:14`; discarded inner stderr is not
reconstructed. No signal termination was reported for these failed stages.

`candidateProof.m3` is true, M1/M2 are false, and `allProbesPassed` is false.
The overall `collectionComplete` is true but `diagnosticAccepted`, `accepted`
and `productAccepted` remain false; CI remained failed. Both original failed
arms are preserved. K01/K02 were unrun (`phases` and `journeysExecuted` are empty),
and the closed ten core cases/full application build were not repeated.

The actual system SQLite CLI reports 3.43.2. Its before/after binary identity and
SHA256 match `d6a8ca0c2013c6d1204875960ce270e0f155ab8d0af289408421820592dd0a20`.
Separately, native admission loaded better-sqlite3's bundled SQLite 3.53.4 and
sqlite-vec v0.1.9, then closed its in-memory database. These distinct version
observations and connection results do not establish a unique OS, SQLite, Node,
filesystem or launcher cause, or prove how the earlier K01 failures arose.

Each database was 122,880 bytes. Eight observations per lane retain the same
full-file hash and identity, including final checks after all probes:

- Python: `b8800180872b8f5edbe3ebc3d768e860dda1498428bc9fdb524347238d78b593`.
- Foundation: `869d6339d883e6a20e16b1987cd17e0850f2668a08f1a6882605228ce4bf529b`.

All 16 validated 100-byte SQLite header originals verify their base64, byte
count and SHA256. Independently decoded fields match the report: page size
4,096, read/write version bytes 2/2, 30 pages, and last-writer version field
3,053,004. All 48 sidecar observations report absent journal/WAL/SHM files.
Each observation reports zero observed attributed processes and unknown root references,
with direct children reaped/groups absent and owner-only parent/temp directories.
M3 additionally passed its immediate eligibility recheck and unchanged after-state.
These are bounded observations, not a continuous or host-wide writer attestation.
Immutable mode skips normal locking/change detection; this result applies only
to these stable, quiescent owned files. No chmod, checkpoint, database copy or
write-mode repair was performed.

Both compiler commands passed with Xcode 16.4/16F6, Swift 6.1.2 in Swift 5
language mode and SDK 15.5 on macOS 15 ARM64; async-context NSLock warnings remain.
Node 26.13.0 and the frozen scripts-off / optional-omitting runtime admitted.
The retained 82,521-byte lock verifies with 179 package records and 151 installed
required-package bindings. The Foundation report matches its actual stdout;
its eight checks and both arms' normalized semantic vectors match. Configuration
rewrites remain metadata-only observations; corpus/runtime continuity stays strict.

All 56 outer commands closed normally: 51 exited zero and five direct SQLite
commands exited 14. The Foundation outer harness's zero means completed
collection, not successful M0. All 112 command-stream originals plus the lock
original verify: 113 gzip records, 193,599 decoded / 52,994 compressed bytes.
The 16 plain header originals add 1,600 bytes. The unique full-log result marker
reproduces the JSON file including its final newline. Counts do not treat parsed
report copies as extra executions. Privacy scans passed for the directly retained
diagnostic streams; no raw database payload, document text or bookmark was exported.

Five guards bind 48 source paths / 664,186 bytes to vector
`ca82c1f3aabea3759399c0111d4ab94b053fb45e3082b45276f2509c5fd2d5ba`.
Seven source files passed their export barriers; ten 10,856-entry runtime checks
and two compiled-file checks passed. There are 73 attributed PID/start observations, including 56 direct
commands, with no signals, forced drain, remaining attributed processes or unknown
root references at final barriers. Cleanup verified 12,368 entries / 567,142,726
regular bytes and 31 directory identities, then removed scratch. EOF, descriptor,
reaping and original process-group checks passed; this is not a storage-peak,
continuous host-wide or strict offline claim.

Unchanged originals retained through lossless publication envelopes:

- [JSON](qmd-keyword-integration-attempt-6.json.gz): 577,002 bytes, SHA256
  `ffd6798820ec2941987046eee5465327c2c8dda2a1adf59a5e51d24162bd3182`.
  Decodes byte-exactly to 3,479,336 bytes, SHA256
  `cf5878595c3e7176bb7e89dd861e2a619e5e753e9d4c4997f4338098b203fc5f`.
- [Full log](qmd-keyword-integration-attempt-6.raw.log.gz): 580,591 bytes, SHA256
  `ae087e6e27cbdc71880ba51da8ff33aab76be73fbe73daf5d6ca5defd9d33ccd`.
  Decodes byte-exactly to 3,496,572 bytes, SHA256
  `f29207bbe8a90d4305f147c0c6b2e5d63d63234035ce8a566ef9295af66df60d`.

This local draft claims no final publication commit or implemented product fix.
Raw database payloads were not retained for local rehashing; their recorded CI
hashes, structural headers and exact metadata rows are the available evidence.
The audit ran no local product/compiler, download or model. Retrieval/lifecycle,
private-folder, semantic/model, native UI and distribution acceptance remain open;
all earlier failures remain preserved.
