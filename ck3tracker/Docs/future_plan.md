# CK3 Tracker Future Plan

## Product Direction

CK3 Tracker can grow from a safe manual journal into a progressively richer analysis product. Each tier should add capability without invalidating observations created by lower tiers.

```text
Bronze manual entry
  -> Silver read-only savegame import
  -> Gold game-file analysis
  -> Platinum isolated debug/mod service
```

The current application remains focused on the Bronze foundation and the data model required by every later tier.

## Bronze: Manual Entry

Free manual observation and run tracking.

- Record county and barony observations from screenshots or gameplay.
- Track holders, ownership, holding type, tax, levies, development, control, faith, culture, and notes.
- Record county loss, reclaim, acquisition, and holder-resolution events.
- Preserve every observation as a time-stamped DuckDB transaction.
- Validate relationships, required fields, ranges, and holding-specific fields.
- Keep historical observations instead of overwriting them.

Current implementation priority:

- Complete the basic barony status observation transaction.
- Keep County, Barony, Duchy, Summary, and lifecycle views consistent.
- Keep Editor separate from historical recovery workflows.

## Silver: Read-Only Savegame Import

Import a savegame without modifying it.

- Detect supported CK3 version and save metadata.
- Parse the save into a time-stamped import snapshot.
- Normalize save data into Parquet reference/import tables.
- Write accepted observations and provenance into DuckDB.
- Compare savegame snapshots against manual observations and prior imports.
- Never write back to the original savegame.

Sources should be labeled clearly:

- `manual_screenshot`
- `savegame_import`
- `game_file_reference`

## Gold: Game-File Analysis

Analyze CK3 game files such as the `00` and `80` data sets.

- Parse landed titles, counties, baronies, holding types, buildings, and rules.
- Resolve de jure and structural relationships.
- Detect version-specific definitions and changes.
- Validate whether observed states are structurally possible.
- Identify open barony slots separately from realized baronies.
- Enrich summaries with game-rule context without pretending it is run-state evidence.

Game-file data remains immutable/reference data in Parquet. It must not silently overwrite observations in DuckDB.

## Platinum: Isolated Debug/Mod Service

This is a separate, future commercial service, not part of the tracker core.

- Operate only through an explicit supported mod/debug workflow.
- Work on a copy of a savegame, never the original.
- Require version and compatibility checks.
- Provide a dry-run preview before any change.
- Create backups and a rollback path.
- Record a complete transaction journal.
- Verify the result after the operation.
- Warn that unsupported versions or mods may invalidate a run.

This tier must remain isolated because write-back can create checksum problems, corrupt saves, or cause a dead run. The core tracker should remain read-only with respect to authoritative game files.

## Shared Data Principles

Every tier should use stable CK3 IDs and preserve provenance.

- Parquet stores immutable game/reference and import snapshots.
- DuckDB stores mutable run state, observations, lifecycle transitions, and transaction history.
- Current views derive from the latest accepted observation.
- Historical rows remain available for comparison.
- A screenshot is an observation at a point in time, not a continuously true value.
- Volatile values such as control, tax, levies, supply, loot, and plague resistance must be time-stamped.
- Structural facts such as county/barony relationships and holding types must remain separate from observed volatile values.

## Commercial Boundaries

The tier model is designed as an upgrade path:

- Bronze is free and useful on its own.
- Silver adds convenience and read-only automation.
- Gold adds expert validation and game-rule analysis.
- Platinum is a separately isolated premium service with substantially higher operational risk.

No premium feature should require users to surrender or invalidate their existing manual history.

## Source-to-Table Registry and Patch Drift Planning

The Gold tier should not treat CK3 game files as a loose pile of scraped inputs. It should instead maintain a source-to-table registry that maps each live game file or folder to a specific canonical table or extraction pipeline.

The registry should answer three questions for every upstream source:

1. Which file or folder is authoritative?
2. What data does it yield?
3. Which internal table or validation view consumes it?

This becomes especially important when Paradox ships mass patches, DLC updates, or content changes in folders such as `common`, `history`, and `laws`.

### Working Model

The app should treat the live game install as an external source layer and the internal database as the operational layer.

- Source layer: Steam install root, CK3 game root, `common` rules folders, DLC overlays, and version-specific files.
- Extraction layer: parser or importer that turns game files into canonical tables.
- Operational layer: DuckDB-managed tables for mutable run state, historical observations, lifecycle events, and normalized reference data.
- Export layer: optional Parquet snapshots for archival use, not the primary workflow engine.

This keeps the app resilient to patch churn without splitting the data model into two jagged partial systems.

### Registry design

Each source should have a row with:

- source path
- source type (folder or file)
- CK3 version or build tag
- patch sensitivity
- extracted table name
- canonical field set
- destination database table
- validation checks
- drift warning behavior

Example structure:

```text
source_path | source_type | build | patch_risk | extract_rule | destination_table | validation |
--- | --- | --- | --- | --- | --- | ---
C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\laws | folder | build-version | high | parse law definitions | ck3_law_rules | legal_branch_consistency |
C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\landed_titles | file or folder | build-version | high | parse title hierarchy | ck3_title_hierarchy | title_relationship_checks |
C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\cultures | folder | build-version | high | parse culture metadata | ck3_culture_rules | culture_region_checks |
C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\history | folder | build-version | high | parse historical setup | ck3_history_reference | version_compatibility_checks |
```

### Why DuckDB should own the dynamic workflow

DuckDB is the better operational home for the project because it can handle:

- time-stamped observation history
- mutable lifecycle state
- validation queries against canonical reference data
- historical comparisons and audit recovery
- large table-driven analysis without forcing a split between reference and run-state workflows

Parquet remains useful for export, snapshotting, and archival comparison, but it should not be the primary engine for a dynamic tracker that must adapt to game patch drift.

### Deep-dive execution plan

The next implementation pass should be a file-by-file analysis of the CK3 game folders, with a target outcome of building the actual source-to-table registry for the project.

Priority order:

1. `game\common\laws`
2. `game\common\landed_titles`
3. `game\common\cultures`
4. `game\common\religions`
5. `game\history`
6. remaining `game\common` rule folders

This work should be treated as a compatibility and truth-grounding pass. It will likely surface areas where the app should be refactored once the direct game-file data becomes the stronger source of truth.

## Return Point

Return to the current implementation in this order:

1. Build the DuckDB transaction table for barony observations.
2. Wire the existing barony Editor save action to a validated observation transaction.
3. Add integrity checks using the Annaba screenshot truth table, including intentionally invalid test values.
4. Keep savegame import and game-file analysis deferred until the manual observation workflow is reliable.
