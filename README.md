# Findlet

Your documents. One small search bar.

A native macOS menu-bar utility for explicitly selected Markdown and text folders, powered by actual [QMD](https://github.com/tobi/qmd). Open the panel with **Control–Option–Space**, type a query, then open or reveal a matching original file.

**Status: focused keyword and real-model service journeys verified.** The
[keyword result](docs/results/2026/11-07/qmd-keyword-integration.md) records fresh
app-less production-service checks with actual QMD. The earlier
[native result](docs/results/2026/11-05/native-checks.md) records the app build,
ten core cases and ad-hoc package; that closed scope was not rerun. The current
services compiled for those checks. A [fresh complete universal Release build
and archive check](docs/results/2026/11-08/preview-package-attempt-1.md) now passed;
no native app launch occurred. The preview is now downloadable; it is
not notarized and requires separately installed compatible Node/QMD/bindings.

The separate [real-model result](docs/results/2026/11-11/qmd-semantic-integration.md)
now verifies explicit model preparation, semantic/hybrid retrieval, persistent
reopen, failed-preparation recovery, cancellation and Forget on authored files.
It changes no production app code or published preview asset.

## Download the developer preview

[Findlet for Apple silicon and Intel Macs](https://github.com/alvarovillalbaa/findlet/releases/download/v0.1.0-preview.1/Findlet-0.1.0-macos-universal.zip)
(macOS 15+), with [SHA-256 checksum](https://github.com/alvarovillalbaa/findlet/releases/download/v0.1.0-preview.1/Findlet-0.1.0-macos-universal.zip.sha256)
and [source/toolchain manifest](https://github.com/alvarovillalbaa/findlet/releases/download/v0.1.0-preview.1/Findlet-preview-manifest.json).
These are the unchanged passing artifacts, with [public tag/digest readback](docs/results/2026/11-08/preview-package-publication.json).

**Requires existing trusted Node 22+, QMD 2.8.3 and compatible native bindings.**
The signed app includes setup/license notices, with no engine or models bundled.
Universal app slices do not prove Intel QMD operation. See the
[runtime guide](docs/runtime-setup.md) and [installation/trust limits](docs/distribution.md).

## Included in the source

- A compact native panel with keyboard navigation, excerpts, Open/Reveal, progress, Cancel, setup and error states. No large document-management interface.
- Keyword (BM25), expanded semantic, and hybrid/reranked search through QMD's actual commands. Semantic preparation is explicit and uses local CPU inference.
- Selected-folder bookmarks, a configurable shortcut and local runtime/model selection in Settings.
- Private, bounded snapshots with exact manifest-to-result mapping. A successful generation replaces the previous index only after indexing/embedding metadata checks. A failed rebuild preserves the previous complete generation.
- Direct process argument arrays, bounded output, serialized work, owned-process cancellation and stale-query protection. Invalid or externally changed settings are preserved.

## Build and set up

Requires macOS 15+, the Swift toolchain, and sufficient free disk space. The build script honors an installed workspace Storage Guard policy; it does not install dependencies or free disk space.

```sh
./script/build_and_run.sh --build-only
open dist/Findlet.app
```

To build the current app as a Release preview for both Apple silicon and Intel,
with Python 3 available for bounded archive staging:

```sh
./script/build_and_run.sh --build-preview
```

This mode builds/packages without launching or quitting Findlet and refuses
existing preview ZIP/checksum leaves. It emits
`dist/Findlet-0.1.0-macos-universal.zip` and its `.zip.sha256`, with source-exact
license, third-party and setup notes in the signed app bundle. Fresh universal
packaging passed, and the unchanged download is public under the
[Findlet preview scope](docs/proposals/preview-package-checks.md). The
[runtime guide](docs/runtime-setup.md) explains required external setup; the app
archive contains no Node, QMD, native bindings or models.

The default `./script/build_and_run.sh` builds, locally ad-hoc signs, and opens the real app bundle. Codex's Run action calls that script. `--debug`, `--logs`, `--telemetry`, and `--verify` are explicit diagnostic/launch modes. The app itself emits no document/query telemetry; the telemetry option only opens the local process log stream.

Original icon artwork is editable in `artwork/app-icon.svg`. Its PNG reference
and ten-representation `Resources/AppIcon.icns` are prepared, and the packaging
source copies the icon before its existing signing step. To regenerate using
Python's standard library, run
`bash script/render_app_icon.sh`; add `--check` to compare fresh exports on the
current toolchain. PNG compression bytes can vary across Python/zlib versions.
The [icon receipt](docs/results/2026/10-28/app-icon.md) records source checks;
actual app-bundle icon loading and Finder appearance remain unverified.

In Settings:

1. Select an existing **Node 22+** executable and a trusted installed **`@tobilu/qmd` 2.8.3** package directory containing `dist/cli/qmd.js` and `dist/index.js`. Findlet checks package metadata and entry fingerprints; it does not attest every dependency or install QMD.
2. Select document folders, then click **Rebuild Local Index**. Nothing is indexed automatically. Choose document folders narrower than your whole home directory, outside Findlet's own data folder.
3. Use Keyword search. For Semantic/Hybrid, select compatible existing embedding, query-expansion and reranker **GGUF** files, rebuild for the updated setup, then explicitly accept and run **Prepare Semantic Search**. The QMD CPU binding must already be installed. Findlet never calls QMD's model-download command and configures its CPU loader to skip native downloads/builds. Strict network-offline behavior remains unverified.

The app does not bundle or install Node, QMD, native bindings or models. The
approved service checks installed pinned Node/QMD and native bindings only in
owned disposable CI scratch; the semantic packet also used three hash-pinned
public models, then removed all owned scratch. No local runtime installation
or model setup was performed. External setup/downloads and model terms remain
separate; see [third-party notices](THIRD_PARTY.md). No cloud search, account,
Vercel or Supabase service is required.

## Data and limits

The app reads regular, locally present UTF-8 `.md`, `.markdown`, and `.txt` files from up to 32 selected folders. Hidden items, packages, symlinks, network volumes and cloud placeholders are excluded. Each rebuild allows 2,000 documents, 2 MiB per file, 100 MiB combined, 100,000 visited entries and 64 directory levels. Exceeding a limit, unreadable/invalid UTF-8 input, or an eligible empty/whitespace-only file fails the rebuild with an explanation.

Snapshots and indexes remain under the app's private `com.alvarovillalbaa.Findlet` Application Support directory. Search uses the last successful snapshot until another explicit rebuild. Source text and queries are not logged. **Forget Findlet Index** removes Findlet-owned generated data; original folders, settings and external runtime/model installations remain. Generation directories without valid ownership markers are preserved and require attention before deletion.

Results resolve through the manifest and revalidate the current original file before handing its URL to macOS. That external handoff cannot prevent a later filesystem replacement by another process. The application uses a direct external executable and is **not App Sandbox enforcement**. It requests no Accessibility or Full Disk Access permission and is not a Finder Sync extension.

## Verification

The [contract](docs/specs/local-search.md) records the implementation and proof
boundaries. On 7 November, the
[keyword result](docs/results/2026/11-07/qmd-keyword-integration.md) passed two
fresh journeys with 26 named harness checks and six actual keyword queries:
rebuild/search/original resolution, then reopen, invalid-UTF-8 rebuild refusal,
missing-original refusal, same-inode restoration and Forget. Three authored
UTF-8 files (197 bytes), including a Unicode filename, matched the independent
SQLite document/content rows. An owned parent path containing a space and a
literal percent exercised actual URI escaping. The checked source uses a
guarded closed-generation metadata audit and a read-only observer through the
already locked YAML parser; official default-model URI metadata is not model
execution. No prior passes were carried.

Earlier failed CI attempts remain preserved:
[1](docs/results/2026/11-07/qmd-keyword-integration-attempt-1.md),
[2](docs/results/2026/11-07/qmd-keyword-integration-attempt-2.md),
[3](docs/results/2026/11-07/qmd-keyword-integration-attempt-3.md),
[4](docs/results/2026/11-07/qmd-keyword-integration-attempt-4.md),
[5](docs/results/2026/11-07/qmd-keyword-integration-attempt-5.md),
[6](docs/results/2026/11-07/qmd-keyword-integration-attempt-6.md).
The dated native build/ten-case/package proof stays separate and was not rerun.

On 11 November, the [real-model result](docs/results/2026/11-11/qmd-semantic-integration.md)
passed two new journeys with18named preparation/lifecycle checks and eight real
searches. Three authored topics ranked first in Semantic and Hybrid modes;
fresh-process reopen, failed native preparation, observed child cancellation,
subsequent search and Forget passed. An independent immutable audit verified
three finite nonzero1024D vectors, real expansion and nonconstant rerank-cache
metadata, unchanged index bytes/sidecars and exact snapshot mapping. Six source
guards and owned teardown passed. Four prior invocations remain preserved; this
small fixture check does not establish general retrieval quality.

Swift 6 language-mode warnings remain unresolved. Native UI, shortcut and
permission interaction, private folders/file providers, general semantic quality,
strict offline behavior, Developer ID/notarization and fresh downloaded-app/
Gatekeeper acceptance remain pending. The current full-app build and ad-hoc
preview delivery have their separate evidence above. These service checks do not establish whole-product release readiness
or continuous protection against every external filesystem writer.
