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
- The repaired native source now compiles, all ten original core cases passed
  once, and fresh ad-hoc packaging passed. Preserve the initial compiler failure
  and accepted receipt. Do not rerun this closed scope without changed inputs
  or a concrete concern. Native UI, QMD retrieval and distribution stay separate;
  the captured concurrency warnings do not establish Swift 6 language readiness.

## First actual QMD keyword integration — 7 November 2026

The owner's standing "I approve everything / Keep going / Do all the work"
covers the [separate keyword packet](docs/proposals/qmd-keyword-integration.md):
one temporary free public macOS 15 ARM64 job, capped at 20 minutes, with
explicitly pinned Node/QMD tooling and no install scripts, model downloads,
semantic preparation, app launch or private-folder access. This is new actual
engine integration, not a repeat of the closed ten core cases or app packaging.
Local Storage Guard still fails; no local install, compile or application run.

Compile the two unchanged core files and four production engine/service files
with an app-less harness. Use only task-owned authored documents, an ordinary
Foundation bookmark of their scratch folder, and app-owned configuration/index.
K01 rebuilds and searches; K02 reopens the persisted index, checks failed-rebuild
preservation and missing-source refusal, then forgets generated data. Keep all
original documents and external runtime files unchanged. Do not weaken path,
manifest, ownership or cancellation checks, or substitute fake QMD responses.

Retain bounded original harness/observer outputs, exact source/runtime hashes,
the actual outcomes and owned teardown on success or failure. Production QMD
stderr is discarded internally; an outer receipt must not claim that it retains
those inner streams. Actual macOS SQLite/vector admission is required; Linux
evidence does not transfer. Native UI, existing bookmarks, semantic quality,
strict offline behavior, permissions and trusted distribution remain separate.
Disable and retire the owned workflow after its terminal run. No account,
payment, model/provider call, application dependency or application API change.

The first attempt stopped at Node archive size admission, before Node execution
or either journey; compilation and owned teardown passed. Preserve that failed
source and original receipt. The standing approval covers one changed attempt
on the separate QA `-2` ref, with a metadata inventory before extraction and
explicit 256 MiB/member, 512 MiB/total and 20,000-member bounds for the same
hash-pinned archive. The 2 GiB scratch limit and all other gates remain. Do not
infer the rejected member or exceeded sub-limit from the first receipt.

The second attempt admitted the pinned archive and actual Darwin SQLite/vector
bindings, then failed the production rebuild before queries. Preserve its
originals. One changed diagnostic attempt on QA `-3` may add a harness-only
finite error category and SHA256 of an existing Findlet error message, with no
raw message, userInfo, document text, query, bookmark or inner stderr. Keep the
same failure exit and all journey assertions. No product repair is established
until the observed cause supports it; all source/runtime/resource gates remain.

The third attempt fingerprint matches the existing runner's status-14 template,
which omits termination reason. Preserve that failure. The QA `-4` packet is
diagnostic-only D01: compare direct Python execution and the actual production
QMDProcessRunner on fresh, separate authored indexes, covering keyword update,
SDK health and read-only SQLite metadata verification with matched runtime,
argv, corpus/configuration and environment roles. Record differing launch
settings and path roles; do not call a comparison a proven cause. K01/K02 remain
unrun in this packet. The only production change adds finite termination reason
to the existing error message; retain the same success predicate, cancellation
and output limits. No observer API, private data, model or inference is added.
Direct diagnostic streams are separate from the production runner's discarded
inner streams. Reject output containing authored document bodies or query
tokens before publishing captures. A failed arm must keep CI failed; collection
completion is separate from diagnostic success and requires normal owned closure.
After a failed stage, record later stages as unrun. QMD may rewrite its owned
configuration with default model URI metadata without downloading models;
require equal curated initial inputs, record later configuration changes, and
continue to require original corpus and runtime bytes to remain unchanged.

The QA `-4` attempt failed harness compilation at the nested directory-path
expression, before Node setup or either D01 arm. Preserve its originals. QA `-5`
may replace only that expression with explicit typed steps and rerun the same
bounded D01 scope. No assertion, outcome gate, runtime or production change.
