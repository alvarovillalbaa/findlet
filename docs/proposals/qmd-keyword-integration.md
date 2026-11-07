# First actual QMD keyword pipeline

PREPARATION; no K01/K02 journey pass is claimed. The [owning contract](../specs/local-search.md)
requires real QMD retrieval, private generations and manifest-bound original
files. The accepted native build and ten core cases do not prove this path.
Standing owner approval covers this named, free-only integration scope.

The [first attempt](https://github.com/alvarovillalbaa/findlet/actions/runs/42383731437)
stopped at `node_archive_size_bound` before Node execution or either journey.
The [frozen first source](https://github.com/alvarovillalbaa/findlet/commit/36ace0d39aa8f77648d7fb694fe068a2c3b4ff7f)
and original outputs remain evidence. Compilation and owned teardown passed;
the receipt does not identify the rejected member or exceeded sub-limit.
This revised packet permits one changed attempt with an explicit archive
inventory before extraction, bounded at 256 MiB/member, 512 MiB total and
20,000 members. The archive hash, 2 GiB scratch ceiling and other gates stay
unchanged. No QMD pass is carried forward from the failed attempt.

The [second attempt](https://github.com/alvarovillalbaa/findlet/actions/runs/42384616852)
passed archive/native admission, then failed K01's production rebuild before
queries. Its generic failure code does not identify the underlying exception.
This diagnostic revision adds only a finite failure category and an error-message
SHA256 in the harness, keeping raw messages, userInfo and inner process streams
private. It keeps the generic failure code, failing exit and all assertions.
K02 runs only after an actual K01 pass. No production code repair is inferred.
The second inventory retrospectively explains the old archive failure: the
147,346,864-byte Node binary exceeds the old 128 MiB member cap; total bytes and
entry counts fit the old limits. This was not identified in the first receipt.

## Exact boundary

Use one public macOS 15 ARM64 job, at most 20 minutes. Compile an app-less
Swift harness against the two exact `FindletCore` files and four exact production
services: `FindletEngine`, `CorpusBuilder`, `SourceFileAccess` and
`QMDProcessRunner`. No app entry point, views, Settings store, shortcut, signing,
package dependency or production API is changed. Two direct Swift compiler
commands use owned exports, output and module/Clang caches, with HOME preserved.
The closed ten-test/full-app packaging scope is not rerun.

Use the pinned Node 26.13.0 Darwin ARM64 archive and QMD 2.8.3 dependency lock,
with archive/SRI checks and install scripts disabled. Admit the actual Darwin
SQLite/vector binary and load/close it before native execution. A prior Linux
ELF load is not macOS proof. No model file, inference, embed/vsearch/query mode,
model download/build fallback, provider, account or paid plan belongs here.

The single runner profile is macOS 15 ARM64, fixed Xcode 16.4/16F6 at
`/Applications/Xcode_16.4.app/Contents/Developer`, SDK 15.5 and deployment target
`arm64-apple-macosx15.0`; no toolchain fallback. The independent metadata review
used the [official ARM64 image inventory](https://github.com/actions/runner-images/blob/main/images/macos/macos-15-arm64-Readme.md).
Node's [official 26.13.0 release](https://nodejs.org/en/blog/release/v26.13.0)
pins `node-v26.13.0-darwin-arm64.tar.gz` SHA256
`d38bd5e5a2ddce6bbb5ce45e46e208337da4d51fffe611e567fd32073d6439f6`.

The [Darwin runtime fixture](../../Tests/fixtures/qmd-darwin-arm64-package-lock.json)
derives from the retained vAFS lock (82,512 bytes / SHA256
`98697aea8ca592674d254ca791b355a27549388451e1d2a7ba9c9366294e98a7`).
Only root identity/platform-dependency and the two platform optional flags may
change; every dependency version, resolved URL and integrity stays exact.
The resulting 82,521-byte fixture has SHA256
`c7fbb1cb91ac025f79861db970aab98eb4604ec91f8115fcd67d09e9b9176df2`;
all 179 package paths and their version/resolved/integrity values match the seed.
Root dependencies are QMD 2.8.3, better-sqlite3 13.0.3, sqlite-vec 0.1.9 and
sqlite-vec-darwin-arm64 0.1.9; node-llama-cpp 3.20 remains transitive and unused
for model inference. Derive package.json from the frozen root and use only
`npm ci --ignore-scripts --omit=optional`; no new dependency resolution.
Preserve the complete lock before/after and verify installed identities/SRIs.
The [pinned QMD producer](https://github.com/tobi/qmd/tree/86d2365d17fc682e491c2c53d1e4a884aee8682a)
defines the CLI/SDK contract; a version string alone is not a native-load proof.

## Two journeys

- **K01 — index/search:** create three tiny authored UTF-8 Markdown/text files,
  Unicode names/content, and owned hidden/symlink/outside-folder decoys. An
  ordinary Foundation bookmark points only to that scratch folder. Invoke the
  actual engine's rebuild, summary, keyword searches and original-file resolver.
  Bind returned IDs/labels to the manifest and exact authored originals. Keep
  its index after normal exit for independent read-only SQLite/filesystem checks.
- **K02 — reopen/recovery/forget:** a new process opens the same index and
  searches it. An authored invalid-UTF-8 rebuild must fail while the prior
  pointer/generation and search remain usable. A deliberately missing authored
  original must be refused by the resolver, then restored exactly. Forget Index
  must empty generated state while preserving authored originals and runtime.

The missing-source probe uses an exclusive rename into owned quarantine and
back. Bytes, inode, mode and modification time must survive; change times and
directory timestamps may change. Do not claim those timestamps remain exact.
Failed-rebuild pointer/state preservation is checked before another search can
perform a legitimate QMD configuration/index update.

This is integration **Tier 3**: an owned, disposable real SQLite index created
through QMD's own schema, backed by authored files. No production database,
existing QMD configuration/index, user folder or user bookmark is available.
The ordinary authored bookmark is a necessary engine input; it does not prove
native folder selection, user bookmark behavior or security-scoped permission UI.

## Admission and evidence

The selected source remains on a separate work branch. Default branch contains
only an inert registration stub; the active workflow exists only on the exact
reviewed `qa/findlet-qmd-keyword-20261107-3` ref. Manual dispatch exposes no inputs
and pins one reviewed preparation commit. Verify the complete source tree,
index and file hashes before/after setup, execution and cleanup. Keep a 900-second
work budget, 120-second cleanup reserve and 30-second margin inside the earliest
20-minute job clock. Bound downloads, output, scratch storage and every process.

Capture the actual outer harness/observer streams before interpreting them.
Store counts, IDs, relative authored labels and hashes, excluding document text,
query strings, bookmark bytes and personal paths. Inner QMD streams are private
to the production runner and are not original outputs retained by this observer.
Record that boundary explicitly. Runtime/package closure and SQLite checks are
separate from retrieval quality, native UI, cancellation and strict offline proof.

Require normal child/group closure and verified owned file/directory teardown.
Unexpected files, replacement inodes, signals or incomplete evidence keep the
packet failed; preserve original failures before any changed repair. Delete only
proved owned disposable resources, and retire the CI control after termination.
No local runtime exception is granted by this remote packet.
