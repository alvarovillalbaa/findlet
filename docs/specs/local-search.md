# Local-search contract

Intent: the [owning project list](https://app.notion.com/p/311a1ee8bd06805caa21c5306dd315ac), fetched 2026-10-27, requests “local search (like QMD by toby)” with a macOS extension/search bar and displayed results rather than a large app. Findlet interprets this as a menu-bar utility with a compact native panel and configurable global shortcut. It is not packaged as a Finder Sync extension.

## Retrieval and ownership

- Actual QMD 2.8.3, reviewed at [86d2365d](https://github.com/tobi/qmd/commit/86d2365d17fc682e491c2c53d1e4a884aee8682a), supplies keyword (`search`), expanded semantic (`vsearch`), and hybrid/reranked (`query`) retrieval.
- The user selects an existing Node runtime and QMD package. Findlet does not install dependencies or redistribute QMD/model assets.
- User-selected folders supply regular UTF-8 `.md`, `.markdown`, and `.txt` files. Limits are 32 folders, 2,000 documents, 2 MiB/file, 100 MiB total, 100,000 visited entries and 64 directory levels; exceeding them fails the rebuild rather than silently truncating the corpus. Empty/whitespace-only or invalid UTF-8 documents also fail explicitly. Symlinks, hidden files, packages, network volumes and nonlocal cloud placeholders are excluded. Original files are never edited.
- A generation owns a private corpus, QMD configuration, SQLite index and document manifest. Search output maps only to manifest IDs; arbitrary returned paths are never opened. A failed rebuild retains the previous complete generation.
- QMD executes directly through the selected Node runtime, with argument arrays, separate bounded stdout/stderr and app-owned configuration/cache/cwd. Existing global/project indexes, shell update hooks and blanket config trust are not used.
- Semantic modes require all three existing local GGUF model files and a separate initialization action. `QMD_FORCE_CPU=1` selects QMD's `build: "never", skipDownload: true` loader. A compatible CPU binding must already be installed. No model-download command, native install/build fallback, background download or automatic semantic setup is allowed. Strict offline behavior still needs runtime proof.
- Removal of a selected folder invalidates the current search index until an explicit successful rebuild. Forget index removes only Findlet-owned generated data. Runtime/model installations and original folders are retained.

## Native behavior

The panel supports search focus, keyboard result selection, Return to open, Reveal in Finder, Escape to dismiss, loading/empty/error/setup states, and native semantic colors. Queries are debounced and operations serialized; stale results cannot replace a newer query. Settings hold ordinary persistent folder bookmarks and local runtime selection. Bookmark scope is balanced when available, without claiming sandbox entitlement. No query/document analytics, cloud search, paid provider, Full Disk Access request or login is included.

The app uses read-only descriptor-relative source traversal with no-follow flags, file identity/change checks and local-presence checks. Its Application Support tree is private. Generations have explicit ownership markers; the current-pointer publication is atomic and has no fallible cleanup afterward. QMD exit zero alone is insufficient: staged metadata must contain exactly the manifest snapshot names, all content rows, the expected single collection, and (for semantic readiness) no pending embeddings plus explicit successful embed completion. SDK status opens/syncs only the owned database; a second read-only SQLite query checks normal file/content metadata. These are completion checks, not vector-payload or search-quality proof.

The first implementation uses direct native process execution and is not App Sandbox enforcement. Read scope is enforced in the corpus builder and result resolver. Developer ID signing/notarization and distribution require their own account, entitlement and runtime review.

## Acceptance boundaries

Source parsing is not compilation. Authored pure-core cases do not prove Node/QMD compatibility, macOS bookmarks, shortcut conflicts, file-provider behavior, subprocess cancellation, semantic quality, or runtime offline behavior. Native packaging/tests and disposable authored-folder QMD checks require separate recorded approval and resources. Do not index personal folders while developing.
