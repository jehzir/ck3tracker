# Current Build

- Build ID: `B001-ruler-memory-ingestion`
- Build name: Ruler memory event-stream groundwork
- Status: `suspended`
- Last updated: 2026-08-18

## Objective

Establish the CK3 Game Journal as a durable memory and event model. Treat pasted ruler memories as incomplete, character-bound summaries and preserve the dropped details as separately sourced Holdings, House, relationship, title, and consequence records.

## User Decisions

- The current application is Bronze-level manual data building, not a game-runtime mechanism.
- The app must not write back to savegames or use Debug/mod mode.
- Canon law: `Barony -> County -> Duchy -> Kingdom -> Empire`. Counties contain baronies; duchies contain counties. Never invert this hierarchy in views, joins, or counts.
- Parquet is for immutable/reference/import snapshots.
- DuckDB is for mutable run state, observations, lifecycle transitions, and transactions.
- The ruler memory feed contains only what the character knows; it is not omniscient history.
- `Docs/ruler_memories.md` is a template only; each run gets its own `run_ruler_memories.md`, and imported source content must not overwrite the template.
- A memory sentence is a compressed completed puzzle; detailed facts are the dropped puzzle pieces.
- The first memory entry, `2 January, 867`, is the Holdings-tree starting point.
- The likely initial counties are Mayurqa, Ibiza, and Menorca, but unnamed counties must retain confidence/provenance.

## Repository State

- Branch: `master`
- HEAD: `24dd967 feat: add screenshot OCR review draft`
- Worktree: clean

## Completed

- County inactive/reclaim lifecycle is implemented and tested with Annaba.
- DuckDB run-state database is in place.
- Active Barony, County, Duchy, and Summary views are lifecycle-aware.
- Open barony slots are excluded from realized barony counts.
- Duchy coverage separates base/observed counties and realized baronies.
- Future Bronze/Silver/Gold/Platinum plan is documented.
- Project plan and architecture are aligned around Bronze plus DuckDB.
- Ruler memory template exists at `Docs/ruler_memories.md`.
- Character-memory boundary was added above the pasted feed.
- The pasted ruler feed contains 53 dated memory ticks from 867 through 916.
- The user-pasted ruler memory history is committed and must remain separate from factual observations.
- The 867-01-02 "Mayurqa and 2 others" memory is treated as a county-level bootstrap that fans out to attached barony structure, with unresolved details retaining provenance.
- Bronze barony observation transactions are now implemented in DuckDB.
- The Barony Editor validates open slots, active county state, holder type, and non-negative numeric fields.
- Valid observations write one `transaction_events` row and one `barony_observations` row atomically.
- Current Barony views project the latest DuckDB observation over immutable Parquet without rewriting the source.
- County observation transactions are implemented with explicit game-date/source inputs and current-state projection.
- Duchy views preserve `Barony -> County -> Duchy` order and display aligned Barony and County tables.
- The active Imports page accepts pasted ruler-memory text and screenshot evidence as review-pending client-side imports.
- Screenshot OCR is implemented with Pillow, pytesseract, and the configured Tesseract executable at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- OCR review preserves the screenshot's actual detected subject; a wrong screenshot is evidence to review, not a target to coerce.

## Files That Matter

- `Docs/ruler_memories.md` - user-pasted character memory feed and template; preserve user content.
- `Docs/project_plan.md` - Bronze MVP and implementation order.
- `Docs/architecture.md` - Parquet snapshot and DuckDB transaction boundary.
- `Docs/future_plan.md` - product tiers and deferred read-only import/analysis.
- `logic/run_state_store.py` - DuckDB state access.
- `logic/acquisition_service.py` - county lifecycle transactions.
- `pages/holdings/page.py` - Holdings views and callbacks.
- `data/trial/run_state.duckdb` - mutable trial state.

## Validation

- Lifecycle, reclaim, callback propagation, Barony filtering, and Duchy coverage were verified in the live Dash browser.
- Latest completed checkpoint: `fe8d574`.
- `git diff --check` passes.
- Current DuckDB test state has Annaba and Constantine active with loss/reclaim events retained.
- Current DuckDB test state includes one valid `b_annaba` barony observation and its transaction event.
- Latest completed checkpoint: `ab3b6ae`.
- Latest completed checkpoint: `24dd967`.
- OCR was verified in the live Imports page with an Annaba/Izan screenshot and the intended Murcia Barony screenshot; identity and core Barony fields were detected, with icon-related noise retained for review.
- All touched Python modules compile with the configured Python 3.14 interpreter; `git diff --check` passes.

## Known Issues

- The ruler feed has at least one paste ambiguity near `9 June, 916`, where a birth entry appears without its own date.
- The memory feed is not yet parsed into structured DuckDB journal events.
- The Bronze barony observation transaction is implemented; broader journal event parsing remains future work.
- The exact identities of the two counties in “Mayurqa and 2 others” require external resolution; probable trial mapping is Ibiza and Menorca.
- Imports currently remain client-side review artifacts; they are not yet persisted as import batches or pending acquisition records.
- Screenshot archive limits are intentionally unresolved: record the bounded evidence-set rule for review, but do not choose numeric quotas yet.
- Evidence-set scaffolding uses six-digit playthrough-local IDs such as `set_000000`; four digits are insufficient for a full 867-1453 run.
- OCR dependencies and the screenshot OCR page are committed; native Tesseract is installed outside the repository and configured by path.

## Next Exact Action

Build the first Imports review workflow: persist a pasted ruler-memory import batch and linked screenshot evidence with provenance, then create reviewed pending acquisition candidates without inventing exact game dates or modifying the character-memory feed.

## Resume Note

Start the next chat with:

```text
start build
```

Then use this exact next-action prompt:

```text
Implement the Imports review-to-queue slice. Persist the pasted ruler-memory text and screenshot evidence as a provenance-preserving import batch, allow review without rewriting Docs/ruler_memories.md, and create pending acquisition candidates with nullable/uncertain event dates. Keep Barony -> County -> Duchy ordering and validate the Murcia screenshot path without fabricating observations.
```

Read this file first. Verify git state and the current ruler memory file before editing. Treat the character-memory feed as source content: do not rewrite its meaning or merge it with omniscient factual history.
