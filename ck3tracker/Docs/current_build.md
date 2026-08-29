# Current Build

- Build ID: `B002-scribe-promotion-readiness`
- Build name: Scribe reference-catalog promotion readiness
- Status: `active`
- Last updated: 2026-08-29

## Objective

Produce one evidence-backed, immutable CK3 `1.19.0.6 (Scribe)` reference snapshot and 867 baseline in the repository-root DuckDB, then promote it only through an explicit atomic operation after a fresh readiness report has zero blockers.

## Authority And Scope

This file is the sole execution manifest and the only authoritative source for the current priority, next exact action, and resume instructions. Precedence is defined in `Docs/build_session_protocol.md`.

Current scope is reference ingestion, validation, and promotion safety. Imports, dashboard redesign, broader journal workflows, buildings, decisions, army, council, and other product work remain deferred until this build is complete or the user explicitly changes scope.

The workbook is a workflow and visual specification, not runtime storage. Installed CK3 files are build-specific evidence. CK3 Wiki revisions are the reference authority. Stable IDs and source provenance must be preserved, and no loader may promote as a side effect.

## Repository State

- Branch: `master`
- HEAD at handoff refresh: `fa10740`
- Worktree: intentionally dirty with the uncommitted Scribe reference pipeline, documentation updates, tests, root DuckDB, and backup databases. Do not revert unrelated changes.
- Runtime: Dash development server at `http://127.0.0.1:8051/reference` when active.
- Python: `C:\Python314\python.exe`
- DuckDB: repository-root `ck3tracker_v2.duckdb`

## Completed

- Root `source`, `reference`, `journal`, and `app` schemas and promoted-only selector views.
- Candidate Scribe snapshot `ck3_1_19_0_6_build_23530548` and candidate 867 baseline `ck3_1_19_0_6_867`.
- Installed landed titles, English localization, title history, character history, bookmarks, and static/dynamic capital ingestion with provenance.
- Seven 867 bookmark collections and 35 direct featured rulers validated.
- Capital semantics resolved for all selectable 867 titles.
- Immutable promotion-readiness reports shown in the read-only Reference Inspector.
- Duplicate title blocks classified by baseline impact; all 21 same-date singleton conflicts are resolved by reviewed vanilla source order while every raw block remains preserved.
- Duplicate character blocks classified: 18 semantically identical IDs and two baseline conflicts remain.
- Character parser `1.3.0` normalizes top-level `set_culture`, two proven non-projecting flag values, and pure relationship effects while preserving mixed effects.
- Character review reduced to 109 subjects: two duplicate conflicts and 107 opaque states.
- Grounded government catalog loaded from 18 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Government` revision `35874`; all 14 baseline-used government IDs resolve.
- Grounded culture catalog loaded from 244 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Culture` revision `35845`; all 228 baseline-used culture IDs resolve.
- Grounded faith catalog loaded from 140 installed definitions nested under 49 parent religions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Faith` revision `35751`; all 111 baseline-used faith IDs resolve.
- Grounded dynasty catalog loaded from 10,338 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Dynasty` revision `35828`; all 10,180 baseline-used dynasty IDs resolve.
- Grounded house catalog loaded from 558 installed definitions with the internal wiki path `Dynasty` revision `35828` to its versioned `Houses` section; all 459 baseline-used dynasty-house IDs resolve and all 235 parent dynasty IDs resolve.
- Readiness now requires the deterministic latest run for each of ten parser groups to be completed at its explicit expected version; older successful runs cannot mask newer failures or obsolete versions.
- All 1,698 source-file manifests are bound to the exact latest parser runs that produced them; readiness blocks missing, detached, and stale run bindings.
- All nine installed bookmark DLC gates resolve through reviewed feature mappings to canonical installed package descriptors: `landless_adventurer -> dlc014_ep3`, `khans_of_the_steppe -> dlc020_ce2`, and `all_under_heaven -> dlc022_ep4`.
- Raw feature flags remain preserved beside package identity, descriptor hashes, platform IDs, and permanent wiki-revision evidence; unknown feature flags remain unresolved and block readiness.
- Bookmark parser is `1.1.0`, title-history parser is `1.4.0`, character history is `1.4.0`, and the other seven required parsers remain `1.0.0`.
- Every readiness report now stores an immutable ten-row evidence ledger containing the exact latest parser-run ID, parser version/status, manifest count, and deterministic SHA-256 digest evaluated for each required source group.
- Readiness retrieval compares stored bindings with current evidence and labels legacy or superseded reports stale without rewriting the persisted report, findings, or evidence ledger.
- All 1,709 current source manifests are covered by the latest report evidence ledger; title history also binds installed TGP and law-definition evidence.
- Title-history blocks now record explicit `winner`, `superseded`, or `unresolved` status and expose their source block order, path, conflicting fields, and resolution in the Reference Inspector.
- The permanent `Modding` revision `35725` grounds the engine rule that later ASCII filenames override earlier top-level declarations; this evidence defines vanilla parsing behavior only and adds no mod support.
- All 556 opaque title states are grouped into 19 operation/script shapes with complete source-path counts in `Docs/title_history_opaque_inventory.md`.
- The exact `destroy_landless_title_no_tgp_dlc_effect` family is normalized as a no-op only when its invocation date matches, both installed definitions retain reviewed semantics, and validated package mapping `all_under_heaven -> dlc022_ep4` is present.
- At 867 this records 385 no-op events across 371 titles while preserving every raw declaration. All 371 also contain unsupported `succession_laws`, so the opaque-title count correctly remains 556.
- All 446 baseline-effective `succession_laws` declarations across 431 titles are preserved and normalized as ordered replacement state, including empty clears.
- Fourteen law IDs used across complete installed title history resolve uniquely to bound definitions; the 867 cutoff uses 11 IDs and materializes 431 active rows across 430 titles with no unresolved IDs.
- Active title laws and their definition provenance are visible in the Reference Inspector. Law normalization reduces opaque title states from 556 to 178 without changing unrelated title fields.
- All 30 baseline-effective `de_jure_liege` declarations across 21 titles are preserved and normalized into separate dated parent state; all 14 targets resolve in the same baseline.
- Static landed-title parentage remains immutable while the Reference Inspector displays it beside the 867-effective de-jure parent, date, and source declaration order.
- De-jure normalization reduces opaque title states from 178 to 160; three affected titles retain unrelated unsupported operations.
- The immediate unmodded `Sheikh_Lubb_of_Najera_867_01_01.ck3` save proves `b_logrono` is a city barony in Lubb's domain, distinct from his county `c_najera`; reviewed evidence adjudicates its 867 holder from deceased `73812` to living `73813` while preserving installed history.
- All 44 repository tests pass; changed modules compile and editor diagnostics are clean.

## Current Evidence

- Latest readiness report: `ck3_1_19_0_6_867:readiness:c4194efd-a8ee-42cd-b067-11ea2062b714`.
- Report evidence status: `current`, with ten parser bindings and 1,709 manifests represented by group digests.
- Report status: blocked, with 2 blocking, 2 accepted-exception, 1 informational, and 20 passed findings.
- Snapshot status: `candidate`.
- Baseline status: `candidate`.
- `historical_state_complete`: `false`.
- `app.supported_baselines`: zero rows.
- Holder validation: all 4,434 rows valid, including one reviewed runtime adjudication.
- Root backups exist before each destructive candidate reload.

## Known Blockers

- 160 title states contain baseline-effective opaque history.
- Two character IDs have baseline-conflicting duplicate declarations.
- 107 character states contain baseline-effective opaque effects.
- No production atomic promotion service exists.

## Deferred And Superseded Work

- B001 ruler-memory ingestion is preserved at `Docs/build_history/B001-ruler-memory-ingestion.md`; its Imports next action is suspended, not current.
- Holdings, Bronze observation, dashboard, and tier roadmaps in architecture and planning documents are historical or long-range guidance unless activated here.
- The old permanent 867-only product decision is superseded. 867 is the first candidate date profile, not a permanent product limit.
- Do not promote or resume product feature work from an older document.

## Next Exact Action

Review the 23 baseline-effective `tributary_of` declarations across 23 titles. Inventory their target IDs and installed script consumers, establish whether they represent durable dated title relationships at 867, and model only the evidence-supported projection.

Target files:

- `logic/root_database.py`
- `logic/title_history_loader.py` and its tributary normalization boundary
- `logic/promotion_readiness_service.py`
- `logic/reference_inspector_provider.py`
- focused title-history/readiness tests under `tests/`

Preserve raw declarations and unsupported effects. Keep tributary state separate from liege and de-jure parentage, and keep any unresolved target or unsupported relationship semantics blocking.

Do not combine opaque-effect classification, promotion, dashboard work, or journal work into this slice.

## Acceptance Checks

- All 23 declarations are inventoried by title, effective date, target ID, source path, and declaration order.
- Installed definitions or script consumers establish the relationship semantics before any state is materialized.
- Every materialized target resolves in the same snapshot or baseline, with deterministic replay covered by a focused test.
- Raw `tributary_of` declarations and unsupported operations remain unchanged and auditable.
- Readiness counts only title states that still contain baseline-effective unsupported operations after tributary normalization.
- Report generation does not change snapshot status, baseline status, or `historical_state_complete`.
- `app.supported_baselines` remains empty.
- Focused readiness tests and the full repository suite pass.

## Resume Note

Start a future chat with:

```text
start build
```

Read this file first, verify its repository and database claims, and execute only `Next Exact Action` unless the user changes scope.
