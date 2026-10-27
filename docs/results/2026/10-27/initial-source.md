# Findlet initial source

Status: source published and statically checked; native compilation and runtime acceptance remain pending. The overall multi-project goal remains active.

## Intent and scope

The [owning Notion list](https://app.notion.com/p/311a1ee8bd06805caa21c5306dd315ac), fetched 2026-10-27, contains the complete inline local-search entry: a small macOS search bar with displayed items, like QMD by Tobi. This receipt covers that entry; the parent response was truncated elsewhere and does not establish a complete audit of all embedded projects.

Findlet is a separate native repository under the user's personal GitHub account. Its [contract](../../../specs/local-search.md) interprets the requested extension as a menu-bar utility, with a floating AppKit panel hosting SwiftUI, ordinary persistent folder bookmarks, a configurable Carbon hotkey, settings, result navigation and original-file Open/Reveal. It is not a Finder Sync extension. Vercel and Supabase are unnecessary for this native local application.

The actual external QMD CLI/SDK were reviewed at [86d2365d17fc682e491c2c53d1e4a884aee8682a](https://github.com/tobi/qmd/commit/86d2365d17fc682e491c2c53d1e4a884aee8682a), declaring package 2.8.3. No installed artifact was available or verified. Keyword, expanded semantic and hybrid/reranked modes call those actual commands; no heuristic, sample-result or Spotlight replacement is presented as QMD.

## Source behavior

- Explicit selected local folders yield bounded private UTF-8 snapshots; originals remain untouched. Descriptor-relative no-follow traversal, identity checks, placeholder flags, overlap rejection and cancellation checks constrain ingestion. Limits and empty-file errors are explicit in the README.
- A staged generation owns a corpus, curated config, SQLite index and manifest. QMD uses direct Node execution, named index/config/cache paths, an owned cwd, argument arrays and explicit collection selection. No existing global/project config, shell update hook or blanket trust is used.
- QMD output is bounded and untrusted. A returned path must map to a known snapshot ID. Labels come from the manifest. The original file is revalidated when opened; the later macOS opener handoff retains a documented replacement race.
- Node/QMD and all three compatible GGUF files must already be installed outside Findlet's data tree. CPU mode selects the no-build/no-native-download loader. There is no pull/install command. Runtime offline behavior is unverified; package metadata/entry fingerprints are not a full dependency attestation.
- Semantic preparation builds a fresh generation. QMD exit zero alone cannot mark it ready: a fixed SDK metadata probe, exact active SQLite file/content rows, pending-embedding state and explicit successful embedding output are checked. These checks do not establish actual vector-payload readability or semantic quality.
- A generation publishes through a private atomically renamed current pointer. Fallible cleanup cannot cause a committed generation to be removed. Failed/cancelled staging retains the previous complete index. Marker checks protect unexpected generation directories; one engine holds an exclusive process lock. Settings use bounded reads, private atomic writes and guards against unreadable/concurrently changed content.
- The native model debounces/cancels superseded searches, rejects stale results, invalidates changed-folder/runtime state, and requires explicit rebuild/preparation. Revoking model consent also hides stale semantic results. Quit stays open while cancellation/process exit is pending.

## Verification

Storage Guard returned **23.4 GiB free / 34.0 GiB required**, exit 2. No install, build, typecheck, native launch, QMD execution, folder indexing, model loading/download, browser automation, permission prompt, account operation or provider mutation followed.

Swift frontend syntax parsing accepted **16 Swift files**, including the package manifest and ten authored XCTest cases. This does not load imported modules, typecheck APIs, compile/link, or execute the cases. All **28 owned text files** passed trailing-whitespace/final-newline checks, all **8 local Markdown targets** resolved, and plist, Bash script, Codex Run action and inactive CI YAML checks passed. Node's parse-only check accepted the fixed SDK probe without loading QMD. Staged `git diff --cached --check` passed before the source commit; no test case was executed.

Independent source reviews covered the process/engine/QMD contracts and native/corpus boundaries. They caught the exit-zero embedding issue, fallible work after pointer publication, consent/readiness mismatch and descriptor inheritance; the source addresses those findings. A review without execution is not native/runtime proof.

The [temporary native-check proposal](../../../proposals/native-checks.md) is inactive outside GitHub workflow discovery. It proposes native compilation, ten pure-core cases, real bundle packaging and local ad-hoc signing verification, without launching the app or installing QMD/models. Separate authored-folder and native interaction acceptance remains necessary.

### Later read-only storage audit

A bounded audit on 2026-10-27 at 19:15 UTC measured **23.31 GiB free**, leaving a **10.69 GiB shortfall** against the 34.0 GiB requirement. The entire SIDE folder occupied 1.80 GiB; readable temporary data under /tmp occupied 68.8 MiB. These totals include protected files and do not represent reclaimable space. Even their combined size cannot close the gap.

Protected dependencies, source and evidence were retained. An unclassified generated cache was also retained because current-goal ownership and inactivity were not established. Process inspection and access to a Codex daemon directory under /tmp were denied; no alternate access path was attempted. No verified disposable current-goal artifact was found, and nothing was deleted. The audit made no product, dependency or configuration changes. Native checks remain blocked; the temporary workflow remains inactive.

## Remaining work

Compile/typecheck/package and execute the authored cases after approval; resolve any compiler/API failures. Then prepare an explicitly approved disposable QMD runtime/corpus/model scope and check real retrieval, cancellation, file access and native interactions. Developer ID signing, notarization and downloadable distribution need their own account/approval and exact runtime/license review. No performance, strict-offline, App Sandbox, notarization or end-to-end completion claim is made.

## Publication

Public repository: [alvarovillalbaa/findlet](https://github.com/alvarovillalbaa/findlet), default branch `main`. Source commit [57b36f9346c262a350554c6128166fae19db9fc3](https://github.com/alvarovillalbaa/findlet/commit/57b36f9346c262a350554c6128166fae19db9fc3) contains 28 files / 2,657 inserted lines. Connected GitHub metadata confirmed personal ownership, public visibility and `main`; `git ls-remote` matched that SHA. An immutable connected read of [Package.swift](https://github.com/alvarovillalbaa/findlet/blob/57b36f9346c262a350554c6128166fae19db9fc3/Package.swift) returned blob `de314aa54dbdc1ee2ae90f710e00756176b05520`, matching the local Git blob.

The new repository had **zero GitHub Actions runs** at readback; the proposed job remains outside `.github/workflows`. The local tree was clean after the source publication. This receipt-only follow-up does not change the reviewed product/test/proposal bytes. No app binary or native release was published.
