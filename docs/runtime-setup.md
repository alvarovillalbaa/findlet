# Findlet runtime setup

Findlet is a macOS 15+ menu-bar client for QMD. It does not bundle or install
Node, QMD, native bindings or models. Select only runtime files you trust:
Findlet executes that external code with your account's access.

## Existing runtime requirements

- A trusted **Node 22+** executable and an existing **`@tobilu/qmd` 2.8.3**
  package directory containing `package.json`, `dist/cli/qmd.js` and
  `dist/index.js`.
- QMD's SQLite/vector native modules must already work with your selected
  Node ABI and macOS CPU architecture. Model-backed modes also require a
  compatible existing CPU inference binding.
- Consult the [fixed QMD 2.8.3 documentation](https://github.com/tobi/qmd/blob/86d2365d17fc682e491c2c53d1e4a884aee8682a/README.md)
  and [package requirements](https://github.com/tobi/qmd/blob/86d2365d17fc682e491c2c53d1e4a884aee8682a/package.json)
  when arranging that external installation. Findlet does not verify every
  transitive dependency or provide an installation recipe.

## Start with Keyword search

1. Open Findlet's settings. Under **Existing local runtime**, select the
   **Node executable** and **QMD 2.8.3 package** directory.
2. Use **Add Folders…** to choose folders you are permitted to index. Start
   with a small local folder of UTF-8 `.md`, `.markdown` or `.txt` files.
   Hidden items, packages, symlinks, network volumes and cloud placeholders
   are excluded; unreadable or invalid eligible files can stop a rebuild.
3. Choose **Rebuild Local Index** and wait for success. Nothing is indexed
   automatically, and the original documents remain unchanged.
4. Select **Keyword** and search. This mode does not require a model.
   The default panel shortcut is **Control–Option–Space**; use the menu-bar
   item if another application owns the shortcut.

Findlet owns its generated snapshots, configuration, index and cache. It does
not use your global QMD index. Changing runtime, folder or model selections
requires another rebuild; a failed rebuild retains the last successful index.

## Prepare Semantic and Hybrid search explicitly

Provide three existing, role-compatible **GGUF** files: an embedding model,
a query-expansion model and a reranker. Obtain them legally, accept their
individual license/access terms yourself, and allow for CPU, memory and disk
costs. A GGUF header alone does not establish model compatibility.

Under **Local CPU semantic search**, select **Embedding model**,
**Expansion model** and **Reranker model**, then rebuild for the changed setup.
Enable **I understand and want to prepare these local models** and choose
**Prepare Semantic Search**. Use Semantic or Hybrid after preparation succeeds.
The CPU binding must already be installed: Findlet neither installs it nor
calls QMD's model-download command. Its CPU loader skips native downloads and
builds. These controls are not a verified strict network-offline guarantee.

## Compatibility and recovery

The accepted keyword integration covered **Node 26.13.0, QMD 2.8.3 and Darwin
ARM64** on authored small files. It does not establish compatibility with every
Node version, Intel QMD/bindings, private folders or semantic model quality.
The universal Findlet executable does not make an external runtime universal.

If setup fails, check the selected version, both compiled QMD entries and
matching native bindings before rebuilding. **Forget Findlet Index** removes
Findlet's generated search data; it retains original folders, settings and
your external runtime/model files. App notices are included as `LICENSE.txt`
and `THIRD_PARTY.md` beside this guide; external runtimes and models retain
their own terms.
