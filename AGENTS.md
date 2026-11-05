# Findlet agent instructions

- Read `README.md` and `docs/specs/local-search.md` before implementation.
- Keep the app a compact native menu-bar search utility. QMD owns retrieval; do not substitute sample results or claim Spotlight parity.
- Source inspection and Swift syntax parsing are allowed. Run Storage Guard before installs, builds, models, or test databases; preserve its 30 GiB reserve.
- Native UI checks, private-folder indexing, model downloads, backend checks, temporary CI, dependencies, and distribution require the user's applicable approval. Other projects' approvals do not transfer.
- Never run QMD against the user's existing configuration or index while developing. Use authored fixtures and an app-owned configuration when checks are approved.
- Use explicit folder selection, reject symlinks/cloud placeholders during corpus creation, and preserve originals. Search output is untrusted data.
- Do not include source text, search queries, bookmarks, absolute personal paths, models, indexes, or credentials in logs or commits.
- Keep the source/build/runtime/distribution proof boundaries explicit in `docs/results/`.
- Alvaro's standing "I approve everything / Keep going / Do all the work"
  authorization covers the first native compile/package and ten existing
  pure-core cases in `docs/proposals/native-checks-v2.md`, including its bounded
  temporary public CI. It does not require another approval question. Preserve
  every failed receipt before repair; do not repeat accepted cases unchanged.
- Storage Guard on 5 November reports 18.6 GiB free versus 34 GiB required.
  No local build/install/native execution. CI builds only an exact bounded
  tracked-source export under owned scratch; never copy Git history or use
  private folders. No app launch, QMD, model setup or distribution is implied.
