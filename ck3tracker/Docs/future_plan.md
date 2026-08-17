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

## Return Point

Return to the current implementation in this order:

1. Build the DuckDB transaction table for barony observations.
2. Wire the existing barony Editor save action to a validated observation transaction.
3. Add integrity checks using the Annaba screenshot truth table, including intentionally invalid test values.
4. Keep savegame import and game-file analysis deferred until the manual observation workflow is reliable.
