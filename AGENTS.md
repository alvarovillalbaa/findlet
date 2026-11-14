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

## Current-app preview distribution — 8 November 2026

The current all-project delivery instruction and standing owner approval cover
Findlet's own [universal preview scope](docs/proposals/preview-package-checks.md):
current full-app native Release builds for arm64/x86_64, one bounded free Mac
CI packaging run, metadata/signature/ZIP round-trip checks, source-exact bundled
license/runtime notes and publication of unchanged GitHub preview assets.
This uses applicable standing Findlet authority, not another project's tests.

Preserve the closed ten-case and K01/K02 evidence; do not repeat it. Keep app/
engine/package/resource/test behavior and runtime policy unchanged. The preview
requires existing compatible external Node/QMD/bindings; no runtime/model
redistribution, installation, invocation, retrieval, native app launch, private
folder, permission, trusted-signing or network-offline proof belongs to this scope.

Storage Guard currently fails at 9.0 GiB free/34.0 GiB required. No local build,
install, app/test/CLI/native-library execution. Only source/static checks and
bounded data-only evidence handling. Own and verify CI scratch/caches/children,
preserve failures and retire temporary controls. A universal binary is not
Intel-engine compatibility, Gatekeeper, native UI or whole-product acceptance.

The [first preview invocation](docs/results/2026/11-08/preview-package-attempt-1.md)
now passed full current-app universal Release compilation, packaging/round-trip,
source-bound notices/setup and owned cleanup. Do not rerun this accepted scope
or the old core/keyword cases. Publish only unchanged retained artifacts and
record actual public tag/server digests. The archived controller guards its
original source; later status docs do not create another checked profile.
Keep external runtime/Intel engine/native/trust/model/offline gates explicit.

The [preview is public](docs/results/2026/11-08/preview-package-publication.json)
at `v0.1.0-preview.1`; exact source tag and three unchanged server asset
digests verify. Main has no workflow file; both provider workflows are disabled
and QA retired. Keep bundled `docs/runtime-setup.md` byte-exact to this build
unless a changed guide/package scope is intended. Public release metadata does
not establish downloaded-app launch, external Intel engine or native UI proof.
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

The fifth attempt completed D01 collection: both arms passed update and SDK
status, then the system SQLite audit exited 14. Preserve those failed outcomes.
QA `-6` adds only D02 read-only compatibility probes on those fresh owned closed
databases: explicit empty shell init, escaped URI mode=ro, then immutable=1 only
after stable owned database/header/hash checks, no observed live writers and
absent or zero-byte journal/WAL/SHM files. Record CLI identity/version, parent
and temp permissions, and sidecar state before/after each probe. Ineligible
immutable probes stay unrun. Require exact three-document metadata and unchanged
database/corpus/runtime bytes; no chmod, checkpoint, write open, new dependency
or model. Candidate observations do not repair the application or accept
K01/K02; failed original arms keep CI failed. No production or harness change.

The sixth attempt preserved the failed ordinary audits and verified the guarded
immutable candidate: both closed databases returned the exact three expected
metadata rows with unchanged hashes and absent sidecars. QA `-7` resumes the
original K01/K02 journeys after applying that guarded path inside the engine.
Require private generation/owner/held-lock identity, no-follow regular database
and stable streaming hash/header snapshots, absent or zero-byte sidecars, and
matching snapshots after the read-only URI query. Any pending journal or changed
identity/content must retain the previous generation. No checkpoint, chmod,
write-mode audit, schema, model or public API change. Immutable is confined to
the closed staged generation; these observations do not attest all host writers.
Use an authored scratch name containing a space and literal percent to exercise
actual URI encoding. Keep original journey assertions unchanged. The observer
may parse generated YAML through the already pinned parser to validate only the
curated collection and official default model metadata, without exporting config
contents or performing inference. D01/D02 controls remain preserved and unrun.

The [accepted keyword receipt](docs/results/2026/11-07/qmd-keyword-integration.md)
records fresh K01/K02 passes at source `6757504d24f57cbd9ac21a392360b8fddbf3d9d4`:
26 named checks, six keyword query proofs and independent YAML/raw-table audits.
Rebuild/search/original resolution, persistent reopen, failed UTF-8 rebuild
preservation, missing-original refusal/restoration and Forget passed on authored
fixtures. Preserve all six prior failures. This scope is closed; do not rerun
unchanged accepted journeys or the older ten core/package scope without changed
inputs or a concrete concern. App UI, private folders, user permission/bookmark
flows, models/inference/semantic quality, strict offline behavior and trusted
distribution remain separate. The existing Swift 6 language-mode warnings remain.

## Actual local-model semantic integration — 11 November 2026

The current all-project instruction and standing owner approval apply to this
separate [real-model scope](docs/proposals/qmd-semantic-integration.md). Use one
free public macOS15 ARM64/Xcode16.4 job, capped20minutes, with6GiB owned scratch,
900seconds maximum work and120seconds cleanup plus30seconds margin. Preserve
HOME; all config/cache/corpus/index/model/runtime work stays in that scratch.
Local Storage Guard now fails at0.8GiB free/38required; no local install, model,
compile, native library or application execution. Syntax parsing remains allowed.

S01/S02 use the actual unchanged two core/four service files, three authored
documents and three exact public model revisions with full size/hash admission.
Require native SQLite/vec and QMD force-CPU backend admission, actual complete
embeddings, expected top hits for six semantic/hybrid probes, persisted reopen,
failed-native-preparation preservation, observed owned-query cancellation,
successful subsequent retrieval and Forget. Independently audit closed vectors
and unchanged original/model/runtime/source bytes. Never replace inference with
fixtures, weaken ranking or safety assertions, change the production whitelist,
or count prior accepted keyword/core/package checks again.

The hash-pinned keyword supervisor supplies only generic owned process/file/tar
helpers; its old execution paths stay unrun. Keep original bounded outer outputs
and failures, scan out authored bodies/query text and retain opaque failure hashes
instead of private error details. Production QMD stderr remains discarded. No
weights/index/bookmarks are artifacts. Disable/retire the exact owned QA workflow
after its terminal run. No app UI, private corpus, external account/provider API,
paid plan, redistribution, general semantic quality or strict offline proof.

The first semantic invocation was cancelled while queued, with no runner steps:
source review caught an8GiB RAM/14GiB free-disk draft floor that exceeds the
documented free runner. Preserve that unexecuted invocation. A changed QA-2
profile may use measured6GiB RAM/8GiB free disk with the same6GiB scratch cap,
2GiB remote disk reserve, exact weights and unchanged assertions. No paid runner,
local reserve reduction, source model substitution or inference acceptance.

QA-2's executed receipt passed real S01 preparation/six searches, compilation,
native CPU admission and full model pins, then failed the independent observer's
newer-schema assumption. Cleanup passed; S02 was unrun and overall scope failed.
Preserve originals. QA-3 may correct only that observer to locked npm2.8.3's
`vectors_vec` schema (registry gitHead facd35e), correct upstream citations and
require nonempty expansion/nonconstant rerank-cache metadata without values.
Fresh S01 is necessary for the changed audit; prior observations are not extra
cases. Keep all existing assertions/model/runtime pins and execute S02 once.

QA-3's native observer returned exact vector/cache metadata, then failed its
combined integrity predicate. Preserve the failure; do not infer which part
failed. QA-4 may replace only the observer connection with guarded immutable
system SQLite plus the pinned admitted vec extension, retaining exact file/hash/
sidecar/path predicates and recording them separately. SQL-only finite/norm/
cache metadata must expose no vectors or cache values. All assertions remain;
no checkpoint, write open, chmod, app/runtime/model change or old-case rerun.

QA-4's system shell rejected `.load`, so its observer/S02 were unrun; retain the
failed originals and passed teardown. QA-5 may use the existing isolated Python
sqlite3 binding with explicit URI and extension APIs, admitting the pinned vec
library/JSON in memory before weights. No install or implicit loader fallback.
Keep immutable file/sidecar guards and SQL finite/norm/cache assertions, with
missing expansion-query fields rejected. App/QMD/model/runtime pins stay exact.

The [accepted real-model receipt](docs/results/2026/11-11/qmd-semantic-integration.md)
now records fresh S01/S02 passes at b2979cb8b8a9228975683a87f2b7c0861d4a9198:
18named checks/eight real queries, exact vector/cache metadata, all six identical
source guards and owned cleanup. All prior invocations remain preserved. This
scope is CLOSED; do not repeat it unchanged. App source and published preview/
bundled runtime guide stayed exact. Retire only the five owned QA refs and this
temporary disabled workflow after publication. Native UI, private folders,
general semantic quality, strict offline and trusted distribution remain open.

## Native search-bar UI — 13 November 2026

The same standing owner delegation covers the concrete new
[NUI01 scope](docs/proposals/native-search-ui.md), one bounded free public Mac
runner and its pinned existing-runtime installation. It does not reopen the
closed ten core, K01/K02, S01/S02 or preview packaging scopes. Use actual app,
native picker/shortcut/reopen/Forget actions and real QMD, without production
test hooks or fake results. Preserve the real HOME; use the fixed app-support
directory only after proving it absent on the disposable account and creating
an owner marker. Authored fixture constants belong only in reviewed test source.
Keep runtime query/body/bookmark/picker values out of public logs and images;
retain only explicit empty-query screenshots and finite
observations, with activity redaction declared. Preserve failed originals and
owned cleanup limits. The local1.7/34GiB Guard refusal still applies.

NUI01 now passed once at66cb4806061fe0b4e5407b740185fd0ff2f87087:
one real native journey/nine phases,30commands/60complete retained streams,
five identical full-source guards and owned teardown. The accepted
[receipt](docs/results/2026/11-13/native-search-ui.md) preserves nine failed
originals, including original3's unverified scratch removal. This UI scope is
closed; do not rerun it or the old service/model/core scopes unchanged.

Standing approval covers the separate [0.1.1 preview scope](docs/proposals/panel-preview-package.md):
one fixed free public Mac job for changed full-app universal Release packaging
and unchanged-asset GitHub publication. Bind the accepted native source as
parent; only app0.1.1/build2 metadata, builder archive-version constants and
the new versioned package controller may change compiled/build inputs.
The original package controller and bundled runtime guide stay unchanged.
Require the source/mode/index,18command/archive/signature/round-trip and owned
cleanup gates; preserve every failure. No app launch, engine/model or old test
execution belongs to packaging. The local Guard still forbids heavy execution;
remote6GiB admission/2GiB reserve and4GiB owned limits apply. Trusted downloaded-
app/Intel-engine/private-folder/offline gates remain separate.

The0.1.1 [package/publication receipt](docs/results/2026/11-13/panel-preview-package.md)
now passed at1dc21d0b67a2ecc976549e5322d7bde6ff460f94:18commands/36complete
streams, both slices, metadata/strict signature/fresh ZIP round-trip and owned
cleanup. Exact assets are public at `v0.1.1-preview.1`; tag/server digests match.
Workflow417865018 is disabled and checked package QA absent; all ten native
controls are also retired. The scope is closed, not a prompt to rerun old checks.
Keep anonymous shell download's DNS failure and fresh downloaded Release/
Gatekeeper/Developer ID/Intel-engine/private-folder/offline limits explicit.
