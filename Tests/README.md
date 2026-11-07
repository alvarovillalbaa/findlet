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
It uses unchanged production engine, corpus, process and result-resolution code.
No fake producer or model response stands in for QMD. Authored fixtures and an
ordinary scratch-folder bookmark are never user data. Tiers 4–5, production
roles, personal folders, models and existing QMD configuration are excluded.

The [packet](../docs/proposals/qmd-keyword-integration.md) owns exact tool pins,
resources and limits. Harness and observer originals are retained; production
QMD stderr is not exported, and must not be described as captured. Two accepted
journeys require actual outcomes, unchanged originals/runtime, stable source
and normal verified cleanup. No new pass count or native UI acceptance exists yet.
