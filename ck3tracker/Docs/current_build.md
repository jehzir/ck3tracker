# Current Build

- Build ID: `B001-ruler-memory-ingestion`
- Build name: Ruler memory event-stream groundwork
- Status: `suspended`
- Last updated: 2026-08-17

## Objective

Establish the CK3 Game Journal as a durable memory and event model. Treat pasted ruler memories as incomplete, character-bound summaries and preserve the dropped details as separately sourced Holdings, House, relationship, title, and consequence records.

## User Decisions

- The current application is Bronze-level manual data building, not a game-runtime mechanism.
- The app must not write back to savegames or use Debug/mod mode.
- Parquet is for immutable/reference/import snapshots.
- DuckDB is for mutable run state, observations, lifecycle transitions, and transactions.
- The ruler memory feed contains only what the character knows; it is not omniscient history.
- A memory sentence is a compressed completed puzzle; detailed facts are the dropped puzzle pieces.
- The first memory entry, `2 January, 867`, is the Holdings-tree starting point.
- The likely initial counties are Mayurqa, Ibiza, and Menorca, but unnamed counties must retain confidence/provenance.

## Repository State

- Branch: `master`
- HEAD: `52d6934 docs: preserve ruler memory history`
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
- Latest completed checkpoint: `52d6934`.
- `git diff --check` passes.

## Known Issues

- The ruler feed has at least one paste ambiguity near `9 June, 916`, where a birth entry appears without its own date.
- The memory feed is not yet parsed into structured DuckDB journal events.
- The Bronze barony observation transaction is planned but not implemented.
- The exact identities of the two counties in “Mayurqa and 2 others” require external resolution; probable trial mapping is Ibiza and Menorca.

## Next Exact Action

Design and implement the Bronze barony observation transaction in DuckDB, using the Annaba screenshot truth table for validation. Keep the user-pasted ruler memory separate from factual observations.

## Resume Note

Start the next chat with:

```text
start build
```

Read this file first. Verify git state and the current ruler memory file before editing. Treat the character-memory feed as source content: do not rewrite its meaning or merge it with omniscient factual history.
