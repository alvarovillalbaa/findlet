# Findlet

Your documents. One small search bar.

A native macOS menu-bar utility for explicitly selected Markdown and text folders, powered by actual [QMD](https://github.com/tobi/qmd). Open the panel with **Control–Option–Space**, type a query, then open or reveal a matching original file.

**Status: initial source release.** Syntax/configuration checks passed; native compilation, the ten authored core cases, QMD execution and runtime acceptance have not run. There is no downloadable, notarized app release. See the [receipt](docs/results/2026/10-27/initial-source.md) and [inactive native-check proposal](docs/proposals/native-checks.md).

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

No QMD runtime, native binding or model was installed during development. External setup/downloads and model terms are separate; see [third-party notices](THIRD_PARTY.md). No cloud search, account, Vercel or Supabase service is required.

## Data and limits

The app reads regular, locally present UTF-8 `.md`, `.markdown`, and `.txt` files from up to 32 selected folders. Hidden items, packages, symlinks, network volumes and cloud placeholders are excluded. Each rebuild allows 2,000 documents, 2 MiB per file, 100 MiB combined, 100,000 visited entries and 64 directory levels. Exceeding a limit, unreadable/invalid UTF-8 input, or an eligible empty/whitespace-only file fails the rebuild with an explanation.

Snapshots and indexes remain under the app's private `com.alvarovillalbaa.Findlet` Application Support directory. Search uses the last successful snapshot until another explicit rebuild. Source text and queries are not logged. **Forget Findlet Index** removes Findlet-owned generated data; original folders, settings and external runtime/model installations remain. Generation directories without valid ownership markers are preserved and require attention before deletion.

Results resolve through the manifest and revalidate the current original file before handing its URL to macOS. That external handoff cannot prevent a later filesystem replacement by another process. The application uses a direct external executable and is **not App Sandbox enforcement**. It requests no Accessibility or Full Disk Access permission and is not a Finder Sync extension.

## Verification

The [contract](docs/specs/local-search.md) records the implementation and proof boundaries. No app launch, shortcut registration, permission prompt, private-folder scan, QMD command, model inference or download was performed while producing this source. The [proposed temporary CI](docs/proposals/native-checks.md) compiles/packages without launching and executes ten pure-core cases; it remains inactive pending approval. Native interaction and actual retrieval need a separate authored-folder acceptance run.
