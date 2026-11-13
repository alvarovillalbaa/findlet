# Findlet focused integration checks

The existing `Tests/FindletCoreTests` suite is grandfathered. Its ten accepted
cases and full native package build remain closed and are not repeated here.
New checks keep the existing capitalized `Tests/` root and use the integration,
scripts and fixtures child directories; no case-colliding sibling is introduced.

| Deliberate entry | Layer / data tier | Boundary |
| --- | --- | --- |
| `integration/KeywordPipelineHarness.swift` | Native service integration / Tier 3 | K01 actual QMD keyword indexing/search; K02 persistent reopen, recovery and Forget Index; real owned SQLite plus authored files |
| `scripts/run-keyword-integration.py` | Operational supervisor / same Tier 3 | Exact source/tool/runtime admission, two compiler invocations, original capture, independent file/SQLite observations and owned teardown |
| `fixtures/qmd-darwin-arm64-package-lock.json` | Frozen runtime support / same Tier 3 | Explicit Darwin adaptation of the retained lock, with all versions/resolved URLs/integrities preserved; scripts-off frozen installation |

The harness is a separately compiled CLI, not a new SwiftPM/XCTest collection.
It uses the production engine, corpus, process and result-resolution code.
D01 changes only the process runner's existing failure message to retain its
finite termination reason; the success predicate and limits remain unchanged.
No fake producer or model response stands in for QMD. Authored fixtures and an
ordinary scratch-folder bookmark are never user data. Tiers 4–5, production
roles, personal folders, models and existing QMD configuration are excluded.

The [packet](../docs/proposals/qmd-keyword-integration.md) owns exact tool pins,
resources and limits. Harness and observer originals are retained; production
QMD stderr is not exported, and must not be described as captured. Two accepted
journeys require actual outcomes, unchanged originals/runtime, stable source
and normal verified cleanup. The accepted journeys are recorded in the
[keyword receipt](../docs/results/2026/11-07/qmd-keyword-integration.md); native UI
acceptance remains separate.

D01 is a separate diagnostic-only phase in the same harness/controller. It
compares direct Python and the actual production process runner using fresh
authored keyword indexes and matched runtime/configuration/environment roles
through keyword update, SDK health and read-only SQLite metadata verification.
Its collection and per-arm outcomes do not accept K01/K02. Those original
journey bodies remain unchanged and are not repeated by the D01 packet.

D02 adds guarded read-only SQLite connection variants to the same fresh owned
diagnostic databases. It records file/header/sidecar and CLI observations,
requires exact metadata rows and unchanged database/corpus/runtime bytes, and
leaves an ineligible immutable probe unrun. It does not waive D01 failures or
accept an application repair or either original journey.

QA `-7` returns to the unchanged K01/K02 assertions after the engine's guarded
closed-generation audit repair. The authored parent path includes space/percent
characters. Observer-only YAML validation uses the existing pinned parser and
retains hashes rather than configuration contents. D01/D02 remain historical
observations and are not rerun by this packet.

K01/K02 now passed once on the repaired source: 26 unchanged named checks and six
keyword query proofs. Preserve the six failed receipts and the accepted original
outputs. The scope is closed; no unchanged retry or broader product acceptance
is implied. Models, private folders, UI and trusted distribution remain unverified.

## Actual local-model integration

The separate [semantic packet](../docs/proposals/qmd-semantic-integration.md)
uses `integration/SemanticPipelineHarness.swift` and
`scripts/run-semantic-integration.py` for S01/S02. These are actual production
preparation, vsearch/query, reopen, failed-preparation, cancellation/recovery and
Forget journeys with three authored documents and three pinned external models.
The semantic fixture lock adds only the existing pinned ARM64 native backend.

The new supervisor reuses the immutable keyword supervisor's generic owned
file/process/archive helpers by its full SHA256; it never calls the old
preflight, installer, main or keyword/diagnostic cases. The semantic profile
owns its source guards, model/CPU admission, independent closed-vector audit,
privacy scan, resource bounds and teardown. No older accepted case is repeated.
Weights, indexes, document bodies, query text and bookmarks stay in owned CI
scratch and never enter published captures. Actual outcomes determine acceptance.

S01/S02 now passed at `b2979cb8b8a9228975683a87f2b7c0861d4a9198`:
18named checks, eight actual queries, independent immutable vector/cache audit,
six identical source guards and owned teardown. The [accepted result](../docs/results/2026/11-11/qmd-semantic-integration.md)
retains all originals and four prior invocations. This scope is closed; do not
repeat its accepted cases unchanged. Native UI/private/general-quality/offline/
trusted-distribution gates remain separate. The production six files and bundled
runtime guide were unchanged; no new preview package was necessary.

## Native search-bar journey

`e2e/FindletAcceptance.swift` is NUI01, a T3 actual app/QMD/owned SQLite
journey under the separate [native UI scope](../docs/proposals/native-search-ui.md).
It uses the normal Xcode UI runner and real picker/search/shortcut/reopen/Forget
actions. The host controller owns fixtures and verifies filesystem state; the
UI runner injects no application state. Old core/service/model/package cases
remain closed. Only empty-query panel images and finite observations are public;
native activity streams have an explicit redaction boundary.
