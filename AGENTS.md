# Findlet agent instructions

- Read `README.md` and `docs/specs/local-search.md` before implementation.
- Keep the app a compact native menu-bar search utility. QMD owns retrieval; do not substitute sample results or claim Spotlight parity.
- Source inspection and Swift syntax parsing are allowed. Run Storage Guard before installs, builds, models, or test databases; preserve its 30 GiB reserve.
- Native UI checks, private-folder indexing, model downloads, backend checks, temporary CI, dependencies, and distribution require the user's applicable approval. Other projects' approvals do not transfer.
- Never run QMD against the user's existing configuration or index while developing. Use authored fixtures and an app-owned configuration when checks are approved.
- Use explicit folder selection, reject symlinks/cloud placeholders during corpus creation, and preserve originals. Search output is untrusted data.
- Do not include source text, search queries, bookmarks, absolute personal paths, models, indexes, or credentials in logs or commits.
- Keep the source/build/runtime/distribution proof boundaries explicit in `docs/results/`.
