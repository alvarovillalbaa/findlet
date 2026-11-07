# Seventh QMD keyword attempt: K01 and K02 passed

7 November 2026. **Both focused Tier 3 journeys passed; product-wide acceptance
remains false.** [Run 42391877125](https://github.com/alvarovillalbaa/findlet/actions/runs/42391877125),
job `128460965390`, tested source
[`6757504d24f57cbd9ac21a392360b8fddbf3d9d4`](https://github.com/alvarovillalbaa/findlet/tree/6757504d24f57cbd9ac21a392360b8fddbf3d9d4),
tree `ffb9a627dc4e9c67387397faf39b66647cc6088f`, activation
`648651967460399639f0b75dd5964c0f11f8781f`.

The actual outer result is `passed` / `accepted:true`, with `productAccepted:false`
and no errors. This run resumed the original K01/K02 assertions after the
guarded closed-generation audit repair. D01/D02 were not rerun, no prior outcomes
were carried as passes, and the closed ten core cases/full application build
were not repeated. All six earlier failed attempts remain preserved.

**K01: actual indexing and resolution.** Its retained original report passes the
exact eight named checks: three-document rebuild without models, matching
summary, stable pointer/state across search, hidden/symlink exclusion, unchanged
authored sources and selected runtime, private handoff creation and final root
ownership. The actual engine indexed three authored UTF-8 files, including a
noncombining CJK filename, and excluded the hidden file, symlink and outside
decoy. This does not establish Unicode normalization equivalence.

**K02: graceful reopen, refusal and forget.** A different harness process opened
the persisted index. Its original report passes all 18 named checks, including
same source/runtime/pointer/state at handoff, three-document reopen, invalid-UTF-8
rebuild refusal with the full previous pointer/state preserved before another
search, removal of the failed generation, missing-original refusal, same-inode
restoration and successful resolution, then Forget Index. The independent final
observer confirms no current pointer, empty generations/cache and retained
engine lock. Sources and selected runtime remain unchanged. The exclusive
quarantine rename preserves bytes, inode, mode and mtime; the restored alpha
file's ctime changed, as allowed. Directory times are not claimed unchanged.
This is graceful process reopen/recovery, not crash, reboot or power-loss proof.

Both phase stdout originals deep-equal their stored reports; no failure
diagnostic is present. Their private 6,033-byte handoff has matching SHA256
`a34cd5c7fe015c81d8a4d35eb14d4dfe11fcf509f4eb45f0403a3bd5968131f0`.
The retained pointer and state hashes, generation and four selected runtime
roles match across sessions. The private handoff contents are not exported;
its recorded hash and source-bound validation are not a local payload rehash.

There are six successful keyword-query observations: two authored inputs across
initial indexing, fresh-process reopen and post-refusal recovery, not six
distinct query terms. Each resolves the expected authored ID and original file,
matches its byte count/SHA256, records a finite score and line 3, and retains
only snippet length/hash. The IDs were independently recomputed from folder ID
and relative UTF-8 path. Raw query strings, snippets, document bodies, bookmark
bytes and personal paths are not retained in these reports. This tiny positive
fixture does not measure general retrieval quality or relevance.

The independent immutable read-only SQL stdout contains exactly three expected
UUID `.md` rows in `findlet_documents`. Each document/content hash matches the
corresponding authored original and corpus snapshot. The recorded database is
122,880 bytes, SHA256
`e47d043443d509eb736026f2c30d1dc5d405db6551dba10a1b4fe120caf2bbc6`.
The observer's engine-tree snapshot begins before configuration inspection and
matches after the SQL read; pointer/state and private proof bindings also match.
Actual URI arguments encode the authored space and literal percent as `%20` and
`%25`. The product audit is confined to a stable owned closed generation, with
held-lock/owner identity, full hash/header and absent-or-empty sidecar fences.
It does not attest that every possible host writer is excluded.

The separate read-only YAML observer's original matches its stored result.
It used the already locked YAML 2.9.0 parser with matching manifest/entry hashes,
validated the exact curated collection and absence of hooks/extra fields, and
observed only the three exact official default model URI metadata values. The 454-byte
configuration has recorded SHA256
`18787610bfa2147c9ab0590e546ea091520141d0fa64c0205d02057d07b0fb07`.
Only metadata hashes and booleans are retained; no QMD configuration API, model
load or inference was invoked by this observer. Model URI metadata is not model
execution. Generated configuration and database payloads are not retained for
independent local rehashing.

The app-less compiles passed with Xcode 16.4/16F6, Swift 6.1.2 in Swift 5 language
mode and SDK 15.5 on macOS 15 ARM64. Six NSLock async-context warning diagnostics
remain; Swift 6 language-mode readiness is unproved. Node 26.13.0 and the frozen
scripts-off / optional-omitting runtime admitted actual Darwin bindings:
better-sqlite3's bundled SQLite 3.53.4 and sqlite-vec v0.1.9 loaded and their
in-memory database closed. No new package resolution or dependency was added.

All 55 outer commands exited zero and closed normally. All 110 command-stream
originals plus the frozen-lock original verify: 111 gzip records, 206,528 decoded
/ 59,459 compressed bytes. The log's unique result marker reproduces the JSON
original including its final newline. Parsed phase/YAML/SQL copies are not extra
executions. Independent resource auditing verifies EOF, descriptor closure,
reaping, original process-group absence and no signals or forced drain.

Six guards bind all 48 source paths / 681,726 bytes to vector
`80ab927e77ca89637c67370beb94d682c1d218294ef7662a23b7c133fc3c2155`.
Seven source exports passed five barriers; the 10,856-entry runtime vector
matched at four barriers and compiled files at three. Resource auditing recorded
69 distinct attributed PID/start observations, no remaining attributed processes
or unknown root references, and owned cleanup of 12,362 entries / 566,971,170
regular bytes with 20 directory identities. Scratch was removed. These are
boundary observations, not storage-peak, continuous host-wide or offline proof.

Unchanged originals retained through lossless publication envelopes:

- [JSON](qmd-keyword-integration.json.gz): 576,062 bytes, SHA256
  `82275feb07fbb30caa8528d50b4bce631ff9d40c323f7623acb0a6951371f6d5`.
  Decodes byte-exactly to 3,455,129 bytes, SHA256
  `5fa005b6f84578b0d3e4e8a5437741453631bfb6496d698433c9705186308181`.
- [Full log](qmd-keyword-integration.raw.log.gz): 580,194 bytes, SHA256
  `0e190da7527ce7b98f548d4b20bd3836a381d585a7e0e3e13714a7298834bd3a`.
  Decodes byte-exactly to 3,472,289 bytes, SHA256
  `337f664ca7da67a0ec4b519c0d70e082b2193e461f634dc46c94e3c490a44766`.

This local draft claims no final publication or integration commit. The audit
ran no local application/compiler, installation, new download or model. These
two new app-less integration outcomes do not prove native folder selection or
permission UI, existing user bookmarks/settings, private data, semantic quality,
accounts, signing, distribution or full-product readiness.
