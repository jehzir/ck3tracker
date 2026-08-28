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

## Common Deep-Dive Progress

This is a live-install inventory of `game\common`, processed in alphabetical order. Dates are filesystem `LastWriteTime` values from the active CK3 installation. `Critical` supports structural validation or core extraction, `High` supports important rule or reference extraction, `Medium` is useful supporting game data, and `Low` is primarily presentation or peripheral metadata.

| Folder | File name | File date | Total file count within folder | Priority |
|---|---|---|---:|---|
| `accolade_icons` | `00_accolade_icons.txt` | 2026-05-09 10:35:02 -07:00 | 2 | Low |
| `accolade_icons` | `_accolade_icon.info` | 2024-03-09 16:30:35 -07:00 | 2 | Low |
| `accolade_names` | `00_accolade_names.txt` | 2026-05-09 10:34:59 -07:00 | 2 | Low |
| `accolade_names` | `_accolade_name.info` | 2024-03-09 16:30:35 -07:00 | 2 | Low |
| `accolade_types` | `00_accolade_categories.txt` | 2024-03-09 16:30:35 -07:00 | 6 | High |
| `accolade_types` | `04_ep2_common_attributes.txt` | 2026-05-09 10:34:59 -07:00 | 6 | High |
| `accolade_types` | `04_ep2_eminent_attributes.txt` | 2026-05-09 10:34:59 -07:00 | 6 | High |
| `accolade_types` | `04_ep2_maa_attributes.txt` | 2026-05-09 10:34:59 -07:00 | 6 | High |
| `accolade_types` | `04_ep2_skilled_attributes.txt` | 2026-05-09 10:34:59 -07:00 | 6 | High |
| `accolade_types` | `_accolade_type.info` | 2026-05-09 10:34:59 -07:00 | 6 | High |
| `achievements` | `ce1_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `ep1_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `ep2_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `ep3_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `ep4_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `fp1_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `fp2_achievements.txt` | 2024-10-09 04:26:02 -07:00 | 12 | Low |
| `achievements` | `fp3_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `mpo_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `msgrdk_achievements.json` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `standard_achievements.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Low |
| `achievements` | `_achievements.info` | 2025-03-29 06:45:02 -07:00 | 12 | Low |
| `activities` | `activity_group_types\_activity_group_types.info` | 2025-03-29 06:45:03 -07:00 | 68 | Critical |
| `activities` | `activity_group_types\00_activity_group_types.txt` | 2025-03-29 06:45:03 -07:00 | 68 | Critical |
| `activities` | `activity_locales\_activity_locales.info` | 2024-03-09 16:30:35 -07:00 | 68 | Critical |
| `activities` | `activity_locales\tournament_locales.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `activity_types\_activity_type.info` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `activity_types\camp_party.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `activity_types\chariot_race.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `activity_types\coronation.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\debate.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\feast.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\festival.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\funeral.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\gruesome_festival.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\hike.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\hunt.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\imperial_examination.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `activity_types\inspection.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `activity_types\local_examination.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\monument_expedition.txt` | 2026-03-16 06:57:31 -07:00 | 68 | Critical |
| `activities` | `activity_types\pilgrimage.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\playdate.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\tour.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\tournament.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `activity_types\university_visit.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\wedding.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `activity_types\witch_ritual.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `guest_invite_rules\_invite_rules.info` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `guest_invite_rules\activity_invite_rules.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `intents\_intents.info` | 2024-03-09 16:30:36 -07:00 | 68 | Critical |
| `activities` | `intents\camp_party_intents.txt` | 2024-09-24 09:02:51 -07:00 | 68 | Critical |
| `activities` | `intents\chariot_race_intents.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `intents\coronation_intents.txt` | 2025-11-15 09:19:39 -07:00 | 68 | Critical |
| `activities` | `intents\debate_intents.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `intents\education_intents.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `intents\festival_intents.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `intents\funeral_intents.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `intents\hunt_intents.txt` | 2025-05-11 14:31:09 -07:00 | 68 | Critical |
| `activities` | `intents\imperial_examination_intents.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `intents\journey_intents.txt` | 2024-11-04 10:06:28 -07:00 | 68 | Critical |
| `activities` | `intents\pilgrimage_intents.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `intents\roaming_intents.txt` | 2024-11-04 10:06:28 -07:00 | 68 | Critical |
| `activities` | `intents\shared_intents.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `intents\survey_intents.txt` | 2024-11-04 10:06:28 -07:00 | 68 | Critical |
| `activities` | `intents\tour_intents.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `intents\tournament_intents.txt` | 2024-09-24 09:02:51 -07:00 | 68 | Critical |
| `activities` | `intents\wedding_intents.txt` | 2024-09-24 09:02:51 -07:00 | 68 | Critical |
| `activities` | `intents\witch_ritual_intents.txt` | 2024-03-09 16:30:35 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\_pulse_actions.info` | 2024-03-09 16:30:36 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\camp_party_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\chariot_race_actions.txt` | 2025-03-29 06:45:02 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\coronation_pulse_actions.txt` | 2025-09-09 05:59:33 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\debate_pulse_actions.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\education_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\feast_pulse_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\feast_pulse_actions_oltner.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\festival_actions.txt` | 2025-10-28 09:58:54 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\general_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\hunt_pulse_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\imperial_examination_actions.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\journey_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\pilgrimage_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\playdate_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\roaming_actions.txt` | 2024-11-04 10:06:28 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\survey_actions.txt` | 2024-11-04 10:06:28 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\tour_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\tournament_actions.txt` | 2025-12-11 09:48:32 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\wedding_pulse_actions.txt` | 2026-05-09 10:34:59 -07:00 | 68 | Critical |
| `activities` | `pulse_actions\witch_ritual_actions.txt` | 2025-10-28 09:58:53 -07:00 | 68 | Critical |
| `ai_goaltypes` | `00_testgoals.txt` | 2024-03-09 16:30:35 -07:00 | 1 | High |
| `ai_war_stances` | `00_ai_attacker_stances.txt` | 2025-03-29 06:45:03 -07:00 | 4 | High |
| `ai_war_stances` | `00_ai_defender_stances.txt` | 2025-03-29 06:45:03 -07:00 | 4 | High |
| `ai_war_stances` | `00_ai_war_stances.txt` | 2025-03-29 06:45:02 -07:00 | 4 | High |
| `ai_war_stances` | `_ai_war_stances.info` | 2025-03-29 06:45:03 -07:00 | 4 | High |
| `artifacts` | `blueprints\00_reforge.txt` | 2025-12-11 09:48:32 -07:00 | 26 | Medium |
| `artifacts` | `blueprints\_blueprints.info` | 2024-03-09 16:30:36 -07:00 | 26 | Medium |
| `artifacts` | `features\00_features.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `features\_features.info` | 2024-03-09 16:30:35 -07:00 | 26 | Medium |
| `artifacts` | `feature_groups\00_groups.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `feature_groups\_feature_groups.info` | 2024-03-09 16:30:35 -07:00 | 26 | Medium |
| `artifacts` | `slots\00_default.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `templates\00_event_templates.txt` | 2025-11-15 09:19:39 -07:00 | 26 | Medium |
| `artifacts` | `templates\00_historical_artifacts_templates.txt` | 2026-05-09 10:34:59 -07:00 | 26 | Medium |
| `artifacts` | `templates\00_type_templates.txt` | 2025-09-09 05:59:33 -07:00 | 26 | Medium |
| `artifacts` | `templates\01_ep2_templates.txt` | 2024-03-09 17:07:48 -07:00 | 26 | Medium |
| `artifacts` | `templates\02_ep3_templates.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `templates\_templates.info` | 2024-03-09 16:30:35 -07:00 | 26 | Medium |
| `artifacts` | `types\00_types.txt` | 2025-11-15 09:19:39 -07:00 | 26 | Medium |
| `artifacts` | `types\_types.info` | 2024-03-09 16:30:35 -07:00 | 26 | Medium |
| `artifacts` | `visuals\000_placeholder.txt` | 2024-03-09 16:30:35 -07:00 | 26 | Medium |
| `artifacts` | `visuals\00_court_artifacts.txt` | 2025-11-15 09:19:39 -07:00 | 26 | Medium |
| `artifacts` | `visuals\00_historical.txt` | 2026-05-09 10:34:59 -07:00 | 26 | Medium |
| `artifacts` | `visuals\00_personal_misc.txt` | 2025-11-15 09:19:39 -07:00 | 26 | Medium |
| `artifacts` | `visuals\00_weapon_visuals.txt` | 2025-11-15 09:19:39 -07:00 | 26 | Medium |
| `artifacts` | `visuals\03_fp2_artifacts.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `visuals\04_ep2_artifacts.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `visuals\06_ce1_artifacts.txt` | 2025-10-28 09:58:53 -07:00 | 26 | Medium |
| `artifacts` | `visuals\07_ep3_artifacts.txt` | 2024-09-24 09:02:52 -07:00 | 26 | Medium |
| `artifacts` | `visuals\09_mpo_artifacts.txt` | 2025-05-11 14:31:09 -07:00 | 26 | Medium |
| `artifacts` | `visuals\_visuals.info` | 2024-03-09 16:30:36 -07:00 | 26 | Medium |
| `bookmarks` | `bookmarks\_bookmarks.info` | 2025-10-28 09:58:53 -07:00 | 6 | Medium |
| `bookmarks` | `bookmarks\00_bookmarks.txt` | 2026-05-09 10:35:02 -07:00 | 6 | Medium |
| `bookmarks` | `challenge_characters\_challenge_characters.info` | 2024-09-24 09:02:52 -07:00 | 6 | Medium |
| `bookmarks` | `challenge_characters\00_challenge_characters.txt` | 2026-05-09 10:34:59 -07:00 | 6 | Medium |
| `bookmarks` | `groups\_bookmark_groups.info` | 2024-03-09 16:30:36 -07:00 | 6 | Medium |
| `bookmarks` | `groups\00_bookmark_groups.txt` | 2024-09-24 09:02:52 -07:00 | 6 | Medium |
| `bookmark_portraits` | `[deferred: 332 files]` | Not collected | 332 | Low |
| `buildings` | `_buildings.info` | 2026-05-09 10:35:02 -07:00 | 22 | High |
| `buildings` | `00_admin_buildings.txt` | 2025-03-29 06:45:03 -07:00 | 22 | High |
| `buildings` | `00_castle_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_city_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_common_buildings.txt` | 2025-10-28 09:58:53 -07:00 | 22 | High |
| `buildings` | `00_duchy_capital_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_legendary_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_nomad_buildings.txt` | 2026-03-16 06:57:31 -07:00 | 22 | High |
| `buildings` | `00_special_buildings.txt` | 2026-05-09 10:35:00 -07:00 | 22 | High |
| `buildings` | `00_special_mines.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_standard_economy_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_standard_fortification_buildings.txt` | 2026-05-09 10:35:02 -07:00 | 22 | High |
| `buildings` | `00_standard_military_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `00_temple_buildings.txt` | 2026-05-09 10:35:00 -07:00 | 22 | High |
| `buildings` | `00_tribal_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `99_ach_buildings.txt` | 2025-10-28 09:58:53 -07:00 | 22 | High |
| `buildings` | `99_background_graphics_buildings.txt` | 2026-03-16 06:57:31 -07:00 | 22 | High |
| `buildings` | `ccp3_special_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `cp6_special_buildings.txt` | 2026-05-09 10:35:03 -07:00 | 22 | High |
| `buildings` | `cp8_special_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `temple_citadel_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `buildings` | `tgp_great_project_buildings.txt` | 2026-05-09 10:34:59 -07:00 | 22 | High |
| `casus_belli_groups` | `00_casus_belli_groups.txt` | 2025-11-15 09:19:39 -07:00 | 1 | High |
| `casus_belli_types` | `_casus_belli.info` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `00_casus_belli_types.txt` | 2025-05-11 14:31:08 -07:00 | 27 | High |
| `casus_belli_types` | `00_civil_war.txt` | 2026-01-31 02:17:48 -07:00 | 27 | High |
| `casus_belli_types` | `00_claim.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `00_conquest.txt` | 2025-10-28 09:58:53 -07:00 | 27 | High |
| `casus_belli_types` | `00_dejure_war.txt` | 2025-12-11 09:48:32 -07:00 | 27 | High |
| `casus_belli_types` | `00_event_war.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `00_invasion_war.txt` | 2025-12-11 09:48:32 -07:00 | 27 | High |
| `casus_belli_types` | `00_nomadic_conquest.txt` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `00_peasant_war_new.txt` | 2025-10-30 07:31:31 -07:00 | 27 | High |
| `casus_belli_types` | `00_religious_war.txt` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `00_struggle_war.txt` | 2025-10-28 09:58:53 -07:00 | 27 | High |
| `casus_belli_types` | `00_subjugation.txt` | 2026-05-09 10:35:01 -07:00 | 27 | High |
| `casus_belli_types` | `00_tributarize.txt` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `00_vassalization.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `01_ep1_wars.txt` | 2025-10-28 09:58:53 -07:00 | 27 | High |
| `casus_belli_types` | `01_fp1_wars.txt` | 2025-12-11 09:48:32 -07:00 | 27 | High |
| `casus_belli_types` | `03_fp2_wars.txt` | 2025-10-28 09:58:53 -07:00 | 27 | High |
| `casus_belli_types` | `05_fp3_wars.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `06_ce1_wars.txt` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `07_ep3_admin_cbs.txt` | 2025-10-28 09:58:53 -07:00 | 27 | High |
| `casus_belli_types` | `07_ep3_wars.txt` | 2026-05-09 10:35:00 -07:00 | 27 | High |
| `casus_belli_types` | `09_mpo_wars.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `10_tgp_china_wars.txt` | 2026-05-09 10:34:59 -07:00 | 27 | High |
| `casus_belli_types` | `10_tgp_faction_wars.txt` | 2026-05-09 10:35:00 -07:00 | 27 | High |
| `casus_belli_types` | `10_tgp_japan_wars.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `casus_belli_types` | `tgp_eastasia_wars.txt` | 2026-05-09 10:35:02 -07:00 | 27 | High |
| `character_backgrounds` | `00_character_backgrounds.txt` | 2024-03-09 16:30:36 -07:00 | 1 | Medium |
| `character_interactions` | `_character_interactions.info` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_adoption.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_alliance.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_artifact_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_blackmail_interactions.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_ce1_interactions.txt` | 2026-05-09 10:35:00 -07:00 | 58 | High |
| `character_interactions` | `00_character_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_choose_favorite_interaction.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_court_amenities_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_courtier_and_guest_interactions.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_culture_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_debug_interactions.txt` | 2026-05-09 10:35:03 -07:00 | 58 | High |
| `character_interactions` | `00_diarch_interactions.txt` | 2026-05-09 10:34:58 -07:00 | 58 | High |
| `character_interactions` | `00_dynast_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_education_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_faction_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_fp3_interactions.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_gift.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_grant_titles_interaction.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_heir.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_house_head_interactions.txt` | 2026-05-09 10:35:03 -07:00 | 58 | High |
| `character_interactions` | `00_invite_agent_to_scheme.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interactions` | `00_invite_to_activity.txt` | 2024-09-24 09:02:53 -07:00 | 58 | High |
| `character_interactions` | `00_lease_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_lover_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_marriage_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_modifiy_vassal_contract.txt` | 2026-05-09 10:35:03 -07:00 | 58 | High |
| `character_interactions` | `00_mongol_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_perk_interactions.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interactions` | `00_poetry_interactions.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `00_prison_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_religious_interactions.txt` | 2026-05-09 10:35:03 -07:00 | 58 | High |
| `character_interactions` | `00_revoke_title_interaction.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_scheme_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `00_test_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_tradition_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_trait_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `00_tribal_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_tributary_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_vassal_interactions.txt` | 2026-05-09 10:35:00 -07:00 | 58 | High |
| `character_interactions` | `00_war.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `00_witch_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `01_fp1_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `02_ep1_interactions.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `03_fp2_interactions.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interactions` | `04_ep2_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `05_bp2_interactions.txt` | 2025-12-11 09:48:32 -07:00 | 58 | High |
| `character_interactions` | `06_ep3_interactions.txt` | 2026-05-09 10:34:58 -07:00 | 58 | High |
| `character_interactions` | `06_ep3_laamp_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `06_ep3_scheme_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `06_ep3_test_interactions_.txt` | 2025-10-28 09:58:53 -07:00 | 58 | High |
| `character_interactions` | `09_mpo_interactions.txt` | 2026-05-09 10:34:59 -07:00 | 58 | High |
| `character_interactions` | `10_ach_interactions.txt` | 2026-05-09 10:35:03 -07:00 | 58 | High |
| `character_interactions` | `10_tgp_interactions.txt` | 2026-05-09 10:34:58 -07:00 | 58 | High |
| `character_interactions` | `10_tgp_japan_interactions.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interactions` | `10_tgp_test_interactions.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interactions` | `tgp_east_asia_interactions.txt` | 2026-05-09 10:35:02 -07:00 | 58 | High |
| `character_interactions` | `tgp_tribute_mission_interactions.txt` | 2026-05-09 10:35:01 -07:00 | 58 | High |
| `character_interaction_categories` | `00_character_interaction_categories.txt` | 2025-10-28 09:58:53 -07:00 | 1 | High |
| `character_memory_types` | `_character_memories.info` | 2026-05-09 10:35:02 -07:00 | 21 | Medium |
| `character_memory_types` | `ach_memories.txt` | 2025-11-15 09:19:39 -07:00 | 21 | Medium |
| `character_memory_types` | `bp2_hostage_memories.txt` | 2024-03-09 16:30:35 -07:00 | 21 | Medium |
| `character_memory_types` | `bp2_memories.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `character_memory_types` | `bp3_memories.txt` | 2024-11-04 10:06:28 -07:00 | 21 | Medium |
| `character_memory_types` | `ce1_memories.txt` | 2024-03-09 16:30:35 -07:00 | 21 | Medium |
| `character_memory_types` | `character_memories_1.txt` | 2025-12-11 09:48:32 -07:00 | 21 | Medium |
| `character_memory_types` | `character_memories_events.txt` | 2024-09-24 09:02:53 -07:00 | 21 | Medium |
| `character_memory_types` | `character_memories_events_jason_ep2.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `character_memory_types` | `character_memories_filippa_events.txt` | 2025-12-11 09:48:32 -07:00 | 21 | Medium |
| `character_memory_types` | `character_memories_travel_events.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `character_memory_types` | `ep2_feast_memories.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `character_memory_types` | `ep2_hunt_memories.txt` | 2025-05-11 14:31:09 -07:00 | 21 | Medium |
| `character_memory_types` | `ep2_memories_james.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `character_memory_types` | `ep2_tournament_memories.txt` | 2024-03-09 16:30:35 -07:00 | 21 | Medium |
| `character_memory_types` | `ep2_wedding_memories.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `character_memory_types` | `ep3_memories.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `character_memory_types` | `jason_first_event_ep2_memories.txt` | 2024-03-09 16:30:35 -07:00 | 21 | Medium |
| `character_memory_types` | `mpo_memories.txt` | 2025-06-27 10:17:22 -07:00 | 21 | Medium |
| `character_memory_types` | `pilgrimage_memories.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `character_memory_types` | `tgp_memories.txt` | 2025-10-28 09:58:55 -07:00 | 21 | Medium |
| `coat_of_arms` | `01_holy_order_coas.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `01_landed_titles.txt` | 2026-05-09 10:34:58 -07:00 | 21 | Medium |
| `coat_of_arms` | `01_mercenary_coas.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `coat_of_arms` | `01_random_templates.txt` | 2025-11-15 09:19:39 -07:00 | 21 | Medium |
| `coat_of_arms` | `03_religious_icons.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `90_dynasties.txt` | 2026-05-09 10:34:58 -07:00 | 21 | Medium |
| `coat_of_arms` | `91_laamp_coas.txt` | 2026-05-09 10:35:10 -07:00 | 21 | Medium |
| `coat_of_arms` | `99_coa_designer_templates.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `99_historical_character_coa.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `coat_of_arms` | `default.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `dynamic_definitions\_dynamic_definitions.info` | 2024-03-09 16:30:36 -07:00 | 21 | Low |
| `coat_of_arms` | `dynamic_definitions\00_dynamic_coas.txt` | 2025-11-15 09:19:39 -07:00 | 21 | Medium |
| `coat_of_arms` | `dynamic_definitions\00_norman_coas.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `dynamic_definitions\00_norse_coas.txt` | 2024-03-09 16:30:38 -07:00 | 21 | Medium |
| `coat_of_arms` | `options\atlases.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\coa_designer_templates.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\coa_templates.txt` | 2025-11-15 09:19:39 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\color_lists.txt` | 2025-10-28 09:58:53 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\colored_emblem_lists.txt` | 2026-05-09 10:35:02 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\pattern_lists.txt` | 2024-03-09 16:30:38 -07:00 | 21 | Medium |
| `coat_of_arms` | `template_lists\textured_emblem_lists.txt` | 2024-03-09 16:30:36 -07:00 | 21 | Medium |
| `combat_effects` | `_combat_effects.info` | 2024-09-24 09:02:53 -07:00 | 2 | High |
| `combat_effects` | `00_combat_effects.txt` | 2025-10-28 09:58:53 -07:00 | 2 | High |
| `combat_phase_events` | `_combat_phase_events.info` | 2024-03-09 16:30:36 -07:00 | 3 | High |
| `combat_phase_events` | `00_commander_phase_events.txt` | 2026-05-09 10:35:02 -07:00 | 3 | High |
| `combat_phase_events` | `00_knight_phase_events.txt` | 2026-05-09 10:35:00 -07:00 | 3 | High |
| `confederation_types` | `_confederation_types.info` | 2025-10-28 09:58:55 -07:00 | 3 | High |
| `confederation_types` | `00_confederation_types.txt` | 2025-10-28 09:58:55 -07:00 | 3 | High |
| `confederation_types` | `10_house_bloc_types.txt` | 2026-05-09 10:35:02 -07:00 | 3 | High |
| `connection_arrows` | `silk_road_arrows.txt` | 2026-05-09 10:35:03 -07:00 | 1 | Low |
| `console_groups` | `00_groups.txt` | 2024-03-09 16:30:36 -07:00 | 1 | Low |
| `council_positions` | `_council_positions.info` | 2025-11-15 09:19:39 -07:00 | 3 | High |
| `council_positions` | `00_council_positions.txt` | 2026-05-09 10:35:02 -07:00 | 3 | High |
| `council_positions` | `01_ministry_positions.txt` | 2026-05-09 10:35:03 -07:00 | 3 | High |
| `council_tasks` | `_council_tasks.info` | 2025-10-28 09:58:53 -07:00 | 10 | High |
| `council_tasks` | `00_chancellor_tasks.txt` | 2026-05-09 10:35:02 -07:00 | 10 | High |
| `council_tasks` | `00_court_chaplain_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 10 | High |
| `council_tasks` | `00_kurultai_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 10 | High |
| `council_tasks` | `00_marshal_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 10 | High |
| `council_tasks` | `00_spouse_tasks.txt` | 2024-03-09 16:30:36 -07:00 | 10 | High |
| `council_tasks` | `00_spymaster_tasks.txt` | 2026-05-09 10:35:00 -07:00 | 10 | High |
| `council_tasks` | `00_steward_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 10 | High |
| `council_tasks` | `00_vizier_tasks.txt` | 2025-05-11 14:31:09 -07:00 | 10 | High |
| `council_tasks` | `01_ministry_tasks.txt` | 2025-11-15 09:19:39 -07:00 | 10 | High |
| `courtier_guest_management` | `courtier_management.txt` | 2025-10-28 09:58:53 -07:00 | 2 | High |
| `courtier_guest_management` | `guest_management.txt` | 2026-05-09 10:35:00 -07:00 | 2 | High |
| `court_amenities` | `_court_amenities.info` | 2024-03-09 16:30:36 -07:00 | 2 | Medium |
| `court_amenities` | `00_court_amenities.txt` | 2025-10-28 09:58:53 -07:00 | 2 | Medium |
| `court_positions` | `tasks\_court_position_tasks.info` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_antiquarian_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_bookmaker_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_boyan_tasks.txt` | 2025-05-11 14:31:10 -07:00 | 47 | High |
| `court_positions` | `tasks\00_caravan_master_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_charioteer_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_cherbi_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_chief_qadi_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_chronicler_tasks.txt` | 2026-05-09 10:35:00 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_artificer_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_brahmin_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_brewmaster_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_guru_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_jester_tasks.txt` | 2025-05-11 14:31:09 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_musician_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_physician_tasks.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_poet_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_court_tutor_tasks.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `tasks\00_cupbearer_tasks.txt` | 2025-03-29 06:45:03 -07:00 | 47 | High |
| `court_positions` | `tasks\00_executioner_tasks.txt` | 2025-05-11 14:31:10 -07:00 | 47 | High |
| `court_positions` | `tasks\00_fire_dragon_engineer_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_food_taster_tasks.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `tasks\00_foreign_emissary_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_grand_guardian_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_grand_mentor_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_grand_preceptor_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_harem_manager_tasks.txt` | 2026-05-09 10:35:00 -07:00 | 47 | High |
| `court_positions` | `tasks\00_high_almoner_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_khlon_glan_tasks.txt` | 2025-10-28 09:58:55 -07:00 | 47 | High |
| `court_positions` | `tasks\00_master_of_the_horse_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_master_of_the_hunt_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_personal_champion_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_royal_architect_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_seneschal_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_siege_engineer_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `tasks\00_stargazer_tasks.txt` | 2025-05-11 14:31:09 -07:00 | 47 | High |
| `court_positions` | `tasks\00_wet_nurse_tasks.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `tasks\00_yeke_jarquchi_tasks.txt` | 2025-05-11 14:31:09 -07:00 | 47 | High |
| `court_positions` | `tasks\00_yurtchi_tasks.txt` | 2025-05-11 14:31:10 -07:00 | 47 | High |
| `court_positions` | `tasks\01_eparch_tasks.txt` | 2025-10-28 09:58:53 -07:00 | 47 | High |
| `court_positions` | `types\_court_positions.info` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `types\00_admin_court_position.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `types\00_camp_officers.txt` | 2026-05-09 10:35:03 -07:00 | 47 | High |
| `court_positions` | `types\00_celestial_court_positions.txt` | 2026-05-09 10:34:59 -07:00 | 47 | High |
| `court_positions` | `types\00_court_positions.txt` | 2026-05-09 10:34:58 -07:00 | 47 | High |
| `court_positions` | `types\00_mandala_court_positions.txt` | 2026-05-09 10:35:02 -07:00 | 47 | High |
| `court_positions` | `types\00_mpo_court_positions.txt` | 2026-05-09 10:35:00 -07:00 | 47 | High |
| `court_types` | `_court_types.info` | 2024-03-09 16:30:35 -07:00 | 2 | High |
| `court_types` | `00_court_types.txt` | 2025-05-11 14:31:09 -07:00 | 2 | High |
| `culture` | `_cultural_traits.info` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `aesthetics_bundles\_aesthetics_bundles.info` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `aesthetics_bundles\00_aesthetics.txt` | 2024-09-24 09:02:53 -07:00 | 152 | High |
| `culture` | `creation_names\_creation_names.info` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `creation_names\00_names.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `creation_names\00_names_hybrid.txt` | 2025-11-15 09:19:39 -07:00 | 152 | High |
| `culture` | `cultures\_cultures.info` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `cultures\00_akan.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_amuric.txt` | 2026-03-16 06:57:32 -07:00 | 152 | High |
| `culture` | `cultures\00_arabic.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_baltic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `cultures\00_balto_finnic.txt` | 2026-05-09 10:35:03 -07:00 | 152 | High |
| `culture` | `cultures\00_bantu.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_berber.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_brythonic.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_burman.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_byzantine.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_caucasian.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_central_african.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_central_germanic.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_cham.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_chinese.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `cultures\00_dead.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `cultures\00_dravidian.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_east_african.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_east_slavic.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_frankish.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_goidelic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `cultures\00_hmongic.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_iberian.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_indo_aryan.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_iranian.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_israelite.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_japonic.txt` | 2026-03-16 06:57:31 -07:00 | 152 | High |
| `culture` | `cultures\00_khmer.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_korean.txt` | 2026-05-09 10:35:00 -07:00 | 152 | High |
| `culture` | `cultures\00_latin.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_magyar.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_malayic.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_mongolic.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `cultures\00_nakkavaram.txt` | 2026-05-09 10:35:10 -07:00 | 152 | High |
| `culture` | `cultures\00_north_germanic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `cultures\00_qiangic.txt` | 2026-03-16 06:57:31 -07:00 | 152 | High |
| `culture` | `cultures\00_sahelian.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_sahelian_ibl.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_senegambian.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_somalian.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_south_slavic.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `cultures\00_syriac.txt` | 2025-12-11 09:48:33 -07:00 | 152 | High |
| `culture` | `cultures\00_tai.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_tibetan.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_tujia.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_tungusic.txt` | 2026-03-16 06:57:31 -07:00 | 152 | High |
| `culture` | `cultures\00_turkic.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `cultures\00_ugro_permian.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `cultures\00_viet.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_vlach.txt` | 2025-12-11 09:48:33 -07:00 | 152 | High |
| `culture` | `cultures\00_volga_finnic.txt` | 2025-10-28 09:58:54 -07:00 | 152 | High |
| `culture` | `cultures\00_west_african.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `cultures\00_west_germanic.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_west_slavic.txt` | 2026-01-31 02:17:48 -07:00 | 152 | High |
| `culture` | `cultures\00_yoruba.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `eras\_culture_eras.info` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `eras\00_culture_eras.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `innovations\_culture_innovations.info` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `innovations\00_cultural_maa_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\00_early_medieval_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\00_fp3_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\00_high_medieval_innovations.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `innovations\00_late_medieval_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\00_tribal_innovations.txt` | 2026-05-09 10:34:59 -07:00 | 152 | High |
| `culture` | `innovations\01_fp1_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\02_ce1_innovations.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `innovations\tgp_innovations.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `name_equivalency\_info.info` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_equivalency\00_names.txt` | 2026-05-09 10:35:03 -07:00 | 152 | High |
| `culture` | `name_lists\_example.info` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\_name_lists.info` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_ainu.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_akan.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_arabic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_balhae.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_baltic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_balto_finnic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_bantu.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_berber.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_brythonic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_burman.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_byzantine.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_central_african.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_central_germanic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_chinese.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `name_lists\00_dead.txt` | 2026-05-09 10:35:00 -07:00 | 152 | High |
| `culture` | `name_lists\00_dravidian.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_east_african.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_east_slavic.txt` | 2024-03-09 16:30:35 -07:00 | 152 | High |
| `culture` | `name_lists\00_frankish.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_goidelic.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `name_lists\00_iberian.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_indo_aryan.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_iranian.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_israelite.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `name_lists\00_japanese.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `name_lists\00_khmer.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_korean.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_latin.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_magyar.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `name_lists\00_malay.txt` | 2025-11-15 09:19:39 -07:00 | 152 | High |
| `culture` | `name_lists\00_mongolic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_nakkavaram.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_nivkh.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_north_germanic.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `name_lists\00_qiangic.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_ryukyuan.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_sahelian.txt` | 2024-03-09 16:30:35 -07:00 | 152 | High |
| `culture` | `name_lists\00_senegambian.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_somalian.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_south_slavic.txt` | 2024-09-24 09:02:53 -07:00 | 152 | High |
| `culture` | `name_lists\00_tai.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_tibetan.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_tungusic.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_turkic.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `name_lists\00_ugro_permian.txt` | 2025-10-28 09:58:54 -07:00 | 152 | High |
| `culture` | `name_lists\00_vietnamese.txt` | 2025-10-28 09:58:55 -07:00 | 152 | High |
| `culture` | `name_lists\00_volga_finnic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_west_african.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_west_germanic.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `name_lists\00_west_slavic.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `name_lists\00_yoruba.txt` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `pillars\_pillars.info` | 2025-05-11 14:31:09 -07:00 | 152 | High |
| `culture` | `pillars\00_ethos.txt` | 2025-05-11 14:31:10 -07:00 | 152 | High |
| `culture` | `pillars\00_head_determination.txt` | 2025-05-11 14:31:10 -07:00 | 152 | High |
| `culture` | `pillars\00_heritage.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `culture` | `pillars\00_language.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `pillars\00_martial_custom.txt` | 2024-03-09 16:30:38 -07:00 | 152 | High |
| `culture` | `traditions\_traditions.info` | 2024-03-09 16:30:36 -07:00 | 152 | High |
| `culture` | `traditions\00_combat_traditions.txt` | 2026-05-09 10:34:59 -07:00 | 152 | High |
| `culture` | `traditions\00_debug_traditions.txt` | 2024-03-09 16:30:35 -07:00 | 152 | High |
| `culture` | `traditions\00_maa_traditions.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `traditions\00_realm_traditions.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `traditions\00_regional_traditions.txt` | 2025-11-15 09:19:39 -07:00 | 152 | High |
| `culture` | `traditions\00_ritual_traditions.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `traditions\00_societal_traditions.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `traditions\01_fp1_traditions.txt` | 2025-10-28 09:58:53 -07:00 | 152 | High |
| `culture` | `traditions\03_fp2_traditions.txt` | 2026-05-09 10:35:02 -07:00 | 152 | High |
| `culture` | `traditions\03_fp3_traditions.txt` | 2025-10-28 09:58:54 -07:00 | 152 | High |
| `culture` | `traditions\04_ep2_traditions.txt` | 2025-05-11 14:31:10 -07:00 | 152 | High |
| `culture` | `traditions\06_ce1_traditions.txt` | 2025-05-11 14:31:10 -07:00 | 152 | High |
| `culture` | `traditions\07_ep3_traditions.txt` | 2025-11-15 09:19:39 -07:00 | 152 | High |
| `culture` | `traditions\09_ach_traditions.txt` | 2025-09-09 05:59:33 -07:00 | 152 | High |
| `culture` | `traditions\09_mpo_traditions.txt` | 2025-12-11 09:48:32 -07:00 | 152 | High |
| `culture` | `traditions\tgp_traditions.txt` | 2026-05-09 10:35:01 -07:00 | 152 | High |
| `customizable_localization` | `_custom_loc.info` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_activity_loc.txt` | 2026-05-09 10:35:00 -07:00 | 150 | Medium |
| `customizable_localization` | `00_adventurer_names.txt` | 2026-05-09 10:34:58 -07:00 | 150 | Medium |
| `customizable_localization` | `00_ai_value_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_animal_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_appropriate_generic_words.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_artifact_court_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_artifact_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_bad_roomate_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_board_game_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_body_part_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_bp3_wanderer_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_building_custom_localization.txt` | 2026-05-09 10:34:59 -07:00 | 150 | Medium |
| `customizable_localization` | `00_camp_party_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_casus_belli.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_character_descriptions.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_character_interaction_categories.txt` | 2025-05-11 14:31:09 -07:00 | 150 | Medium |
| `customizable_localization` | `00_childhood_custom_localization.txt` | 2024-03-09 16:30:38 -07:00 | 150 | Medium |
| `customizable_localization` | `00_compliment_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_conversation_subjects.txt` | 2026-05-09 10:34:59 -07:00 | 150 | Medium |
| `customizable_localization` | `00_councillor_custom_loc.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `00_curses_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_custom_loc_sp.txt` | 2024-03-09 16:30:35 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_body_part_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_custom_loc.txt` | 2024-03-09 16:30:38 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_mottos.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_regional_custom_localization.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_signature_weapon_custom_localization.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_single_combat_custom_loc.txt` | 2024-03-09 16:30:35 -07:00 | 150 | Medium |
| `customizable_localization` | `00_de_special_gender_cases.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_destination_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_diarchy_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_difficulty_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_disability_custom_loc.txt` | 2026-05-09 10:35:01 -07:00 | 150 | Medium |
| `customizable_localization` | `00_divinity_custom_loc.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `00_dynasty_custom_loc.txt` | 2024-03-09 16:30:38 -07:00 | 150 | Medium |
| `customizable_localization` | `00_education_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_es_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_event_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_faction_custom_loc.txt` | 2024-10-08 06:33:08 -07:00 | 150 | Medium |
| `customizable_localization` | `00_feast_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_food_custom_loc.txt` | 2025-11-15 09:19:39 -07:00 | 150 | Medium |
| `customizable_localization` | `00_friendly_custom_localization.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_friendship_custom_localization.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_generic_character_words.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `00_governance_lifestyle_custom_loc.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `00_government_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_greeting_custom_loc.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `00_health_custom_loc.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `00_historical_character_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_hold_court_custom_joe.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_incidental_details.txt` | 2025-09-09 05:59:33 -07:00 | 150 | Medium |
| `customizable_localization` | `00_insult_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_insult_poetry_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_interactions_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_interface_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_journey_focus_custom_loc.txt` | 2024-11-04 10:06:29 -07:00 | 150 | Medium |
| `customizable_localization` | `00_knight_culture.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_kr_personality_quirks_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_language_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_lifestyle_custom_localization.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_love_letter_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_lover_custom_localization.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_maa_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_magic_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_map_related_custom_loc.txt` | 2024-11-04 10:06:28 -07:00 | 150 | Medium |
| `customizable_localization` | `00_martial_lifestyle_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_mottos.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_notification_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_peasants.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_personal_details_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_personality_quirks_custom_loc.txt` | 2025-09-09 05:59:33 -07:00 | 150 | Medium |
| `customizable_localization` | `00_personality_traits_custom_loc.txt` | 2024-09-24 09:02:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pet_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pet_name_generic.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_petition_liege_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pilgrimage_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pl_custom_loc.txt` | 2024-12-01 06:01:10 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pl_custom_loc_extra.txt` | 2026-05-09 10:35:03 -07:00 | 150 | Medium |
| `customizable_localization` | `00_pl_relations.txt` | 2024-12-01 06:01:10 -07:00 | 150 | Medium |
| `customizable_localization` | `00_poetry_generation.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_poetry_theme_words.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_prison_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_reaction_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_regional_custom_localization.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_relations.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_religion_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_rich_presence_flavor_status.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_roaming_loc.txt` | 2024-11-04 10:06:29 -07:00 | 150 | Medium |
| `customizable_localization` | `00_romance_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_ruler_transition_loc.txt` | 2026-05-09 10:34:59 -07:00 | 150 | Medium |
| `customizable_localization` | `00_scheme_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_scholarship_lifestyle_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_secret_events_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_secrets_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_seduction_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_servants.txt` | 2025-09-09 05:59:33 -07:00 | 150 | Medium |
| `customizable_localization` | `00_sex_scene_custom_localisation.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_signature_weapon_custom_localization.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `00_skills_custom_loc.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `00_statecraft_lifestyle_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_suitable_title_custom_loc.txt` | 2026-05-09 10:35:00 -07:00 | 150 | Medium |
| `customizable_localization` | `00_sway_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_task_contract_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_terrain_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_test.txt` | 2025-10-28 09:58:56 -07:00 | 150 | Medium |
| `customizable_localization` | `00_title_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `00_trait_custom_loc.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `00_travel.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `00_unfriendly_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_vassal_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_visit_settlement_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_war_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `00_weird_objects.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `00_yearly_events_custom_loc.txt` | 2025-05-11 14:31:09 -07:00 | 150 | Medium |
| `customizable_localization` | `01_bp1_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `01_bp1_filippa_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `01_ep1_custom_loc.txt` | 2026-05-09 10:35:03 -07:00 | 150 | Medium |
| `customizable_localization` | `01_ep2_custom_loc.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `01_fp1_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `01_roco_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `02_court_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `03_fp2_custom_loc.txt` | 2024-09-24 09:02:53 -07:00 | 150 | Medium |
| `customizable_localization` | `04_bp2_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `04_ep2_accolade_custom_loc.txt` | 2024-03-09 16:30:39 -07:00 | 150 | Medium |
| `customizable_localization` | `04_ep2_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `04_ep2_hunt_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `05_bp2_custom_loc.txt` | 2026-05-09 10:35:03 -07:00 | 150 | Medium |
| `customizable_localization` | `06_ce1_epidemics_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `06_ce1_leg_b_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `06_ce1_legends_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `06_legitimacy_custom_loc.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `07_ep3_custom_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `08_bp3_battle_poi_custom_loc.txt` | 2025-12-11 09:48:32 -07:00 | 150 | Medium |
| `customizable_localization` | `08_bp3_experimental_brew_loc.txt` | 2024-11-04 10:06:28 -07:00 | 150 | Medium |
| `customizable_localization` | `08_bp3_survey_loc.txt` | 2025-10-28 09:58:53 -07:00 | 150 | Medium |
| `customizable_localization` | `09_de_custom_loc_suffixes.txt` | 2024-03-09 16:30:36 -07:00 | 150 | Medium |
| `customizable_localization` | `09_mpo_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `09_mpo_custom_loc_2.txt` | 2025-05-11 14:31:10 -07:00 | 150 | Medium |
| `customizable_localization` | `10_ach_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `10_tgp_custom_loc.txt` | 2026-05-09 10:35:03 -07:00 | 150 | Medium |
| `customizable_localization` | `10_tgp_japan_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |
| `customizable_localization` | `99_fr_custom_loc.txt` | 2026-05-09 10:35:00 -07:00 | 150 | Medium |
| `customizable_localization` | `99_pl_custom_loc.txt` | 2024-11-28 02:40:27 -07:00 | 150 | Medium |
| `customizable_localization` | `99_pl_relations.txt` | 2024-11-28 02:40:26 -07:00 | 150 | Medium |
| `customizable_localization` | `99_ru_custom_loc.txt` | 2025-10-28 09:58:54 -07:00 | 150 | Medium |
| `customizable_localization` | `ledger_custom_loc.txt` | 2026-05-09 10:35:10 -07:00 | 150 | Medium |
| `customizable_localization` | `tgp_custom_loc.txt` | 2026-05-09 10:35:01 -07:00 | 150 | Medium |
| `customizable_localization` | `tgp_imperial_examination_custom_loc.txt` | 2025-10-28 09:58:55 -07:00 | 150 | Medium |
| `customizable_localization` | `tgp_mandala_custom_loc.txt` | 2026-05-09 10:35:02 -07:00 | 150 | Medium |

| `deathreasons` | `_death_reasons.info` | 2024-03-09 16:30:36 -07:00 | 4 | Medium |
| `deathreasons` | `00_activity_deaths.txt` | 2024-09-24 09:02:54 -07:00 | 4 | Medium |
| `deathreasons` | `00_event_deaths.txt` | 2026-05-09 10:35:02 -07:00 | 4 | Medium |
| `deathreasons` | `00_natural_deaths.txt` | 2026-05-09 10:35:02 -07:00 | 4 | Medium |
| `decisions` | `_decisions.info` | 2025-10-28 09:58:53 -07:00 | 70 | High |
| `decisions` | `00_artifact_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `00_cultural_tradition_decisions.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `00_diarchy_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `00_dynasty_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `00_fp3_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `00_guest_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `00_holy_order_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `00_lifestyle_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `00_major_decisions_east_europe.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `00_major_decisions_iberia_north_africa.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `00_trait_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `00_unity_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `04_ep2_decisions.txt` | 2026-05-09 10:35:00 -07:00 | 70 | High |
| `decisions` | `06_ce1_decisions.txt` | 2026-05-09 10:35:01 -07:00 | 70 | High |
| `decisions` | `10_ach_oath_decisions.txt` | 2026-05-09 10:34:59 -07:00 | 70 | High |
| `decisions` | `10_culture_conversion_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `10_nomad_culture_and_faith_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `10_nomad_other_decisions.txt` | 2026-05-09 10:35:01 -07:00 | 70 | High |
| `decisions` | `10_religious_decisions.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `30_activity_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `30_court_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `30_mongol_invasion_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `40_japan_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_british_isles.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_central_asia.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_east_asia.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_middle_east.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_middle_europe.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_roman.txt` | 2026-05-09 10:35:00 -07:00 | 70 | High |
| `decisions` | `80_major_decisions_south_asia.txt` | 2026-05-09 10:35:01 -07:00 | 70 | High |
| `decisions` | `90_minor_decisions.txt` | 2026-05-09 10:35:01 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\03_fp2_decisions.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\bp_2\00_bp2_other_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\bp3\00_bp3_other_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ce_1\ce1_legendary_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_1\00_ep1_court_grandeur_and_amenity_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_1\00_ep1_other_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_2\00_ep2_other_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_3\06_ep3_admin_decisions.txt` | 2026-05-09 10:35:00 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_3\06_ep3_hasan_story_cycle_decisions.txt` | 2025-10-28 09:58:54 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_3\06_ep3_laamp_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep_3\06_ep3_separatist_uprising_decision.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\ep3_decisions.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_1\00_fp1_major_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_1\00_fp1_other_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_3\fp3_dynasty_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_3\fp3_islamic_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_3\fp3_minor_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_3\fp3_scholarship_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp_3\fp3_zoroastrian_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\fp3_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\mpo\09_mpo_decisions_2.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\mpo\mpo_court_astrologer_decision.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\mpo\mpo_decisions.txt` | 2026-05-09 10:35:03 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\mpo\mpo_flavor_decision.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\mpo\mpo_pax_mongolica_decision.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_china_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_culture_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_dynastic_cycle_decisions.txt` | 2026-05-09 10:35:00 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_east_asia_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_japan_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_korea_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_silk_road_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_steppe_decisions.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_tenet_decisions.txt` | 2025-11-15 09:19:39 -07:00 | 70 | High |
| `decisions` | `dlc_decisions\tgp\tgp_tribute_mission_decisions.txt` | 2026-05-09 10:35:01 -07:00 | 70 | High |
| `decisions` | `test_decision.txt` | 2025-12-11 09:48:32 -07:00 | 70 | High |
| `decisions` | `tutorial_decisions.txt` | 2026-05-09 10:35:02 -07:00 | 70 | High |
| `decision_group_types` | `_decision_group_types.info` | 2024-09-24 09:02:54 -07:00 | 2 | High |
| `decision_group_types` | `00_decision_group_types.txt` | 2025-10-28 09:58:53 -07:00 | 2 | High |
| `defines` | `00_defines.txt` | 2026-05-09 10:35:02 -07:00 | 12 | Critical |
| `defines` | `ai\00_ai.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Critical |
| `defines` | `audio\00_audio.txt` | 2025-10-28 09:58:53 -07:00 | 12 | Critical |
| `defines` | `graphic\00_coa.txt` | 2024-03-09 16:30:36 -07:00 | 12 | Critical |
| `defines` | `graphic\00_graphics.txt` | 2026-05-09 10:35:02 -07:00 | 12 | Critical |
| `defines` | `jomini\adjacencies.txt` | 2024-03-09 16:30:36 -07:00 | 12 | Critical |
| `defines` | `jomini\fog_of_war.txt` | 2025-10-28 09:58:55 -07:00 | 12 | Critical |
| `defines` | `jomini\mapeditor.txt` | 2024-03-09 16:30:36 -07:00 | 12 | Critical |
| `defines` | `jomini\portraits.txt` | 2026-05-09 10:35:11 -07:00 | 12 | Critical |
| `defines` | `jomini\rivers.txt` | 2024-03-09 16:30:36 -07:00 | 12 | Critical |
| `defines` | `jomini\text_coloring.txt` | 2024-03-09 16:30:36 -07:00 | 12 | Critical |
| `defines` | `jomini\text_formatting.txt` | 2024-03-09 16:30:39 -07:00 | 12 | Critical |
| `diarchies` | `diarchy_mandates\_mandates.info` | 2024-03-09 16:30:36 -07:00 | 6 | High |
| `diarchies` | `diarchy_mandates\00_mandates.txt` | 2026-05-09 10:35:02 -07:00 | 6 | High |
| `diarchies` | `diarchy_types\_diarchies.info` | 2024-03-09 16:30:39 -07:00 | 6 | High |
| `diarchies` | `diarchy_types\00_co_rulerships.txt` | 2026-05-09 10:35:02 -07:00 | 6 | High |
| `diarchies` | `diarchy_types\00_primeministerships.txt` | 2026-05-09 10:35:02 -07:00 | 6 | High |
| `diarchies` | `diarchy_types\00_regencies.txt` | 2026-05-09 10:35:02 -07:00 | 6 | High |
| `dna_data` | `_dna_data.info` | 2024-03-09 16:30:36 -07:00 | 9 | Low |
| `dna_data` | `00_dna.txt` | 2026-05-09 10:34:58 -07:00 | 9 | Low |
| `dna_data` | `00_ep3_dna.txt` | 2025-10-28 09:58:51 -07:00 | 9 | Low |
| `dna_data` | `00_fp3_dna.txt` | 2025-03-29 06:45:03 -07:00 | 9 | Low |
| `dna_data` | `00_mpo_dna.txt` | 2025-05-11 14:31:09 -07:00 | 9 | Low |
| `dna_data` | `00_tgp_dna.txt` | 2025-11-15 09:19:39 -07:00 | 9 | Low |
| `dna_data` | `01_easteregg_dna.txt` | 2026-05-09 10:34:58 -07:00 | 9 | Low |
| `dna_data` | `02_easteregg_dna_non_developers.txt` | 2026-05-09 10:35:02 -07:00 | 9 | Low |
| `dna_data` | `03_fp2_dna.txt` | 2024-03-09 16:30:36 -07:00 | 9 | Low |
| `domiciles` | `buildings\_domicile_buildings.info` | 2025-10-28 09:58:54 -07:00 | 9 | High |
| `domiciles` | `buildings\00_camp_buildings.txt` | 2026-05-09 10:35:01 -07:00 | 9 | High |
| `domiciles` | `buildings\00_chinese_estate_buildings.txt` | 2026-05-09 10:34:58 -07:00 | 9 | High |
| `domiciles` | `buildings\00_estate_buildings.txt` | 2026-05-09 10:34:58 -07:00 | 9 | High |
| `domiciles` | `buildings\00_yurt_buildings.txt` | 2026-05-09 10:34:58 -07:00 | 9 | High |
| `domiciles` | `buildings\10_japanese_manor_buildings.txt` | 2026-05-09 10:34:58 -07:00 | 9 | High |
| `domiciles` | `types\_domicile_types.info` | 2025-05-11 14:31:09 -07:00 | 9 | High |
| `domiciles` | `types\00_domicile_types.txt` | 2025-10-28 09:58:54 -07:00 | 9 | High |
| `domiciles` | `types\10_tgp_japan_domicile_types.txt` | 2025-10-28 09:58:56 -07:00 | 9 | High |
| `dynasties` | `00_deprecated_dynasties.txt` | 2024-03-09 16:30:39 -07:00 | 8 | High |
| `dynasties` | `00_dynasties.txt` | 2026-05-09 10:34:58 -07:00 | 8 | High |
| `dynasties` | `01_vanity_dynasties.txt` | 2026-05-09 10:35:02 -07:00 | 8 | High |
| `dynasties` | `03_fp2_dynasties.txt` | 2024-03-09 16:30:36 -07:00 | 8 | High |
| `dynasties` | `04_ep3_dynasties.txt` | 2026-05-09 10:35:03 -07:00 | 8 | High |
| `dynasties` | `05_historical_character_dynasties.txt` | 2026-05-09 10:35:02 -07:00 | 8 | High |
| `dynasties` | `05_tgp_dynasties.txt` | 2026-05-09 10:34:58 -07:00 | 8 | High |
| `dynasties` | `09_mpo_dynasties.txt` | 2025-05-11 14:31:10 -07:00 | 8 | High |
| `dynasty_houses` | `00_deprecated_dynasty_houses.txt` | 2024-03-09 16:30:36 -07:00 | 5 | High |
| `dynasty_houses` | `00_dynasty_houses.txt` | 2026-05-09 10:35:02 -07:00 | 5 | High |
| `dynasty_houses` | `99_historical_character_houses.txt` | 2026-05-09 10:35:02 -07:00 | 5 | High |
| `dynasty_houses` | `ep3_dynasty_houses.txt` | 2026-05-09 10:35:02 -07:00 | 5 | High |
| `dynasty_houses` | `tgp_dynasty_houses.txt` | 2025-10-28 09:58:56 -07:00 | 5 | High |
| `dynasty_house_mottos` | `_mottos.info` | 2024-03-09 16:30:36 -07:00 | 2 | Medium |
| `dynasty_house_mottos` | `00_mottos.txt` | 2025-10-28 09:58:53 -07:00 | 2 | Medium |
| `dynasty_house_motto_inserts` | `_inserts.info` | 2024-03-09 16:30:36 -07:00 | 2 | Medium |
| `dynasty_house_motto_inserts` | `00_inserts.txt` | 2025-10-28 09:58:53 -07:00 | 2 | Medium |
| `dynasty_legacies` | `_dynasty_legacies.info` | 2026-05-09 10:35:11 -07:00 | 10 | High |
| `dynasty_legacies` | `82_tgp_legacies.txt` | 2026-05-09 10:35:01 -07:00 | 10 | High |
| `dynasty_legacies` | `83_ep3_legacies.txt` | 2026-05-09 10:35:11 -07:00 | 10 | High |
| `dynasty_legacies` | `92_mpo_legacies.txt` | 2026-05-09 10:35:11 -07:00 | 10 | High |
| `dynasty_legacies` | `94_ce1_legacies.txt` | 2024-03-09 16:30:39 -07:00 | 10 | High |
| `dynasty_legacies` | `95_fp3_legacies.txt` | 2026-05-09 10:35:11 -07:00 | 10 | High |
| `dynasty_legacies` | `96_fp2_legacies.txt` | 2026-05-09 10:35:02 -07:00 | 10 | High |
| `dynasty_legacies` | `97_ep1_legacies.txt` | 2024-03-09 16:30:36 -07:00 | 10 | High |
| `dynasty_legacies` | `98_fp1_legacies.txt` | 2026-05-09 10:35:02 -07:00 | 10 | High |
| `dynasty_legacies` | `99_legacies.txt` | 2025-09-09 05:59:33 -07:00 | 10 | High |
| `dynasty_perks` | `_dynasty_perks.info` | 2025-05-11 14:31:09 -07:00 | 11 | High |
| `dynasty_perks` | `00_dynasty_perks.txt` | 2026-05-09 10:35:02 -07:00 | 11 | High |
| `dynasty_perks` | `01_ep1_dynasty_perks.txt` | 2025-10-28 09:58:54 -07:00 | 11 | High |
| `dynasty_perks` | `01_ep2_dynasty_perks.txt` | 2024-10-23 03:48:17 -07:00 | 11 | High |
| `dynasty_perks` | `01_fp1_dynasty_perks.txt` | 2025-05-11 14:31:09 -07:00 | 11 | High |
| `dynasty_perks` | `03_fp2_dynasty_perks.txt` | 2024-03-09 16:30:36 -07:00 | 11 | High |
| `dynasty_perks` | `03_fp3_dynasty_perks.txt` | 2024-09-24 09:02:54 -07:00 | 11 | High |
| `dynasty_perks` | `05_ce1_dynasty_perks.txt` | 2024-03-22 06:54:46 -07:00 | 11 | High |
| `dynasty_perks` | `06_ep3_dynasty_perks.txt` | 2026-05-09 10:35:02 -07:00 | 11 | High |
| `dynasty_perks` | `07_mpo_dynasty_perks.txt` | 2026-05-09 10:35:00 -07:00 | 11 | High |
| `dynasty_perks` | `08_tgp_dynasty_perks.txt` | 2026-05-09 10:35:02 -07:00 | 11 | High |
| `effect_localization` | `_effect_localization.info` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_activity_effects.txt` | 2024-09-24 09:02:54 -07:00 | 36 | Medium |
| `effect_localization` | `00_additional_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_ce1_effects.txt` | 2024-03-09 16:30:39 -07:00 | 36 | Medium |
| `effect_localization` | `00_character_effects.txt` | 2026-05-09 10:35:02 -07:00 | 36 | Medium |
| `effect_localization` | `00_council_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_county_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `00_culture_effect.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_custom_effects.txt` | 2025-10-28 09:58:54 -07:00 | 36 | Medium |
| `effect_localization` | `00_dynasty_effects.txt` | 2024-09-24 09:02:54 -07:00 | 36 | Medium |
| `effect_localization` | `00_faction_effects.txt` | 2024-09-24 09:02:54 -07:00 | 36 | Medium |
| `effect_localization` | `00_fp3_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `00_landed_title_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_legend_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `00_maa_effects.txt` | 2025-10-28 09:58:56 -07:00 | 36 | Medium |
| `effect_localization` | `00_perk_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_province_effects.txt` | 2026-05-09 10:35:00 -07:00 | 36 | Medium |
| `effect_localization` | `00_religion_effects.txt` | 2024-03-09 16:30:39 -07:00 | 36 | Medium |
| `effect_localization` | `00_scheme_effects.txt` | 2024-09-24 09:02:54 -07:00 | 36 | Medium |
| `effect_localization` | `00_secret_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `00_title_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_travel_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `00_vassal_effects.txt` | 2025-05-11 14:31:10 -07:00 | 36 | Medium |
| `effect_localization` | `00_war_effects.txt` | 2025-10-28 09:58:54 -07:00 | 36 | Medium |
| `effect_localization` | `01_ep1_effects.txt` | 2026-05-09 10:35:02 -07:00 | 36 | Medium |
| `effect_localization` | `01_fp1_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `02_ep1_effects.txt` | 2025-10-28 09:58:53 -07:00 | 36 | Medium |
| `effect_localization` | `03_fp2_effects.txt` | 2025-10-28 09:58:54 -07:00 | 36 | Medium |
| `effect_localization` | `04_ep2_diarchy_effects.txt` | 2025-05-11 14:31:09 -07:00 | 36 | Medium |
| `effect_localization` | `04_ep2_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `05_bp2_hostage_effects.txt` | 2024-03-09 16:30:36 -07:00 | 36 | Medium |
| `effect_localization` | `07_ep3_effects.txt` | 2026-05-09 10:35:02 -07:00 | 36 | Medium |
| `effect_localization` | `08_tgp_effects.txt` | 2026-05-09 10:35:01 -07:00 | 36 | Medium |
| `effect_localization` | `09_situation_effects.txt` | 2025-10-28 09:58:56 -07:00 | 36 | Medium |
| `effect_localization` | `10_ach_effects.txt` | 2025-09-09 05:59:33 -07:00 | 36 | Medium |
| `effect_localization` | `10_tgp_effects.txt` | 2025-12-11 09:48:32 -07:00 | 36 | Medium |
| `epidemics` | `_epidemics.info` | 2024-03-09 16:30:36 -07:00 | 2 | High |
| `epidemics` | `00_epidemics.txt` | 2025-10-28 09:58:53 -07:00 | 2 | High |
| `ethnicities` | `00_ethnicities_debug.txt` | 2024-09-24 09:02:54 -07:00 | 25 | Medium |
| `ethnicities` | `00_ethnicities_templates.txt` | 2025-10-28 09:58:54 -07:00 | 25 | Medium |
| `ethnicities` | `00_ethnicities_vanity_characters.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_african.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_arab.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian.txt` | 2025-10-28 09:58:53 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_ainu.txt` | 2025-10-28 09:58:55 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_austronesian.txt` | 2025-10-28 09:58:56 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_han_chinese.txt` | 2025-10-28 09:58:56 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_japanese.txt` | 2025-10-28 09:58:56 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_malay.txt` | 2025-10-28 09:58:55 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_manchu_korean.txt` | 2025-10-28 09:58:55 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_mongol.txt` | 2025-10-28 09:58:53 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_asian_tibetan.txt` | 2025-10-28 09:58:53 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_byzantine.txt` | 2024-03-09 16:30:39 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_caucasian.txt` | 2025-10-28 09:58:53 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_circumpolar.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_default_morphs.txt` | 2024-09-24 09:02:54 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_east_african.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_indian.txt` | 2025-05-11 14:31:10 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_mediterranean.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_papuan.txt` | 2025-10-28 09:58:56 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_slavic.txt` | 2024-03-09 16:30:36 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_turkic.txt` | 2025-05-11 14:31:10 -07:00 | 25 | Medium |
| `ethnicities` | `01_ethnicities_west_turkic.txt` | 2025-05-11 14:31:09 -07:00 | 25 | Medium |
| `event_2d_effects` | `_event_2d_effects.info` | 2025-10-28 09:58:53 -07:00 | 2 | Low |
| `event_2d_effects` | `event_2d_effects.txt` | 2024-09-24 09:02:54 -07:00 | 2 | Low |
| `event_backgrounds` | `_event_backgrounds.info` | 2024-03-09 16:30:36 -07:00 | 3 | Low |
| `event_backgrounds` | `01_event_backgrounds.txt` | 2026-03-16 06:57:31 -07:00 | 3 | Low |
| `event_backgrounds` | `activity_backgrounds.txt` | 2026-01-31 02:17:48 -07:00 | 3 | Low |
| `event_themes` | `_event_themes.info` | 2024-03-09 16:30:39 -07:00 | 3 | Medium |
| `event_themes` | `00_event_themes.txt` | 2025-10-28 09:58:53 -07:00 | 3 | Medium |
| `event_themes` | `ep2_tournament_themes.txt` | 2024-09-24 09:02:54 -07:00 | 3 | Medium |
| `event_transitions` | `_event_transitions.info` | 2024-03-09 16:30:36 -07:00 | 4 | High |
| `event_transitions` | `debug_test_transitions.txt` | 2024-03-09 16:30:36 -07:00 | 4 | High |
| `event_transitions` | `ep2_tournament_transitions.txt` | 2024-03-09 16:30:36 -07:00 | 4 | High |
| `event_transitions` | `ep3_chariot_race_transitions.txt` | 2025-05-11 14:31:10 -07:00 | 4 | High |
| `factions` | `_factions.info` | 2025-10-28 09:58:54 -07:00 | 7 | High |
| `factions` | `00_factions.txt` | 2026-05-09 10:35:01 -07:00 | 7 | High |
| `factions` | `00_nation_fracturing_faction.txt` | 2025-12-11 09:48:32 -07:00 | 7 | High |
| `factions` | `00_nomadic_faction.txt` | 2026-05-09 10:35:02 -07:00 | 7 | High |
| `factions` | `00_peasant_faction_new.txt` | 2026-05-09 10:35:00 -07:00 | 7 | High |
| `factions` | `00_populist_faction.txt` | 2026-05-09 10:35:00 -07:00 | 7 | High |
| `factions` | `10_tgp_factions.txt` | 2026-05-09 10:35:01 -07:00 | 7 | High |
| `flavorization` | `_flavourization.info` | 2026-05-09 10:35:02 -07:00 | 9 | Medium |
| `flavorization` | `00_flavorization.txt` | 2025-12-11 09:48:32 -07:00 | 9 | Medium |
| `flavorization` | `00_title_holders.txt` | 2026-05-09 10:35:02 -07:00 | 9 | Medium |
| `flavorization` | `01_domicile.txt` | 2024-09-24 09:02:54 -07:00 | 9 | Medium |
| `flavorization` | `02_vassal_contracts.txt` | 2024-11-04 10:06:28 -07:00 | 9 | Medium |
| `flavorization` | `10_tgp_flavorization.txt` | 2025-12-11 09:48:32 -07:00 | 9 | Medium |
| `flavorization` | `10_tgp_japan_flavorization.txt` | 2025-12-11 09:48:32 -07:00 | 9 | Medium |
| `flavorization` | `10_tgp_korea_flavorization.txt` | 2026-05-09 10:35:03 -07:00 | 9 | Medium |
| `flavorization` | `11_tgp_china_flavorization.txt` | 2026-05-09 10:35:00 -07:00 | 9 | Medium |
| `focuses` | `_focuses.info` | 2024-09-24 09:02:54 -07:00 | 4 | High |
| `focuses` | `00_education_focuses.txt` | 2025-10-28 09:58:54 -07:00 | 4 | High |
| `focuses` | `00_lifestyle_focuses.txt` | 2024-11-04 10:06:28 -07:00 | 4 | High |
| `focuses` | `00_test_focuses.txt` | 2024-09-24 09:02:54 -07:00 | 4 | High |
| `game_concepts` | `00_game_concepts.txt` | 2026-05-09 10:35:03 -07:00 | 15 | Medium |
| `game_concepts` | `01_bp1_game_concepts.txt` | 2024-09-24 09:02:54 -07:00 | 15 | Medium |
| `game_concepts` | `01_bp2_game_concepts.txt` | 2024-09-24 09:02:54 -07:00 | 15 | Medium |
| `game_concepts` | `01_bp3_game_concepts.txt` | 2024-11-04 10:06:28 -07:00 | 15 | Medium |
| `game_concepts` | `01_ep1_game_concepts.txt` | 2024-03-09 16:30:36 -07:00 | 15 | Medium |
| `game_concepts` | `01_fp1_game_concepts.txt` | 2024-03-09 16:30:37 -07:00 | 15 | Medium |
| `game_concepts` | `03_fp2_game_concepts.txt` | 2025-10-28 09:58:54 -07:00 | 15 | Medium |
| `game_concepts` | `03_fp3_game_concepts.txt` | 2025-10-28 09:58:53 -07:00 | 15 | Medium |
| `game_concepts` | `04_ep2_game_concepts.txt` | 2026-05-09 10:35:02 -07:00 | 15 | Medium |
| `game_concepts` | `05_bp2_game_concepts.txt` | 2024-03-09 16:30:39 -07:00 | 15 | Medium |
| `game_concepts` | `06_ce1_game_concepts.txt` | 2025-10-28 09:58:54 -07:00 | 15 | Medium |
| `game_concepts` | `07_ep3_game_concepts.txt` | 2026-05-09 10:35:02 -07:00 | 15 | Medium |
| `game_concepts` | `ach_game_concepts.txt` | 2025-09-09 05:59:33 -07:00 | 15 | Medium |
| `game_concepts` | `mpo_game_concepts.txt` | 2025-10-28 09:58:53 -07:00 | 15 | Medium |
| `game_concepts` | `tgp_game_concepts.txt` | 2025-12-11 09:48:32 -07:00 | 15 | Medium |
| `game_rules` | `_game_rules.info` | 2024-10-23 03:48:17 -07:00 | 2 | High |
| `game_rules` | `00_game_rules.txt` | 2026-05-09 10:35:02 -07:00 | 2 | High |
| `genes` | `_genes.info` | 2024-03-09 16:30:39 -07:00 | 12 | Medium |
| `genes` | `00_genes_color.txt` | 2024-03-09 16:30:39 -07:00 | 12 | Medium |
| `genes` | `01_genes_morph.txt` | 2026-05-09 10:34:58 -07:00 | 12 | Medium |
| `genes` | `02_genes_accessories_misc.txt` | 2025-10-28 09:58:54 -07:00 | 12 | Medium |
| `genes` | `03_genes_special_accessories_hairstyles.txt` | 2026-05-09 10:35:03 -07:00 | 12 | Medium |
| `genes` | `04_genes_special_accessories_beards.txt` | 2026-05-09 10:35:02 -07:00 | 12 | Medium |
| `genes` | `05_genes_special_accessories_clothes.txt` | 2026-03-16 06:57:31 -07:00 | 12 | Medium |
| `genes` | `06_genes_special_accessories_headgear.txt` | 2026-05-09 10:35:01 -07:00 | 12 | Medium |
| `genes` | `07_genes_special_accessories_misc.txt` | 2026-05-09 10:35:02 -07:00 | 12 | Medium |
| `genes` | `08_genes_special_visual_traits.txt` | 2025-11-15 09:19:39 -07:00 | 12 | Medium |
| `genes` | `09_genes_special_makeup.txt` | 2025-10-28 09:58:56 -07:00 | 12 | Medium |
| `genes` | `10_genes_special_misc.txt` | 2026-05-09 10:35:01 -07:00 | 12 | Medium |
| `governments` | `_governments.info` | 2025-11-15 09:19:39 -07:00 | 3 | High |
| `governments` | `00_government_types.txt` | 2026-05-09 10:35:00 -07:00 | 3 | High |
| `governments` | `01_japan_government_types.txt` | 2026-05-09 10:35:02 -07:00 | 3 | High |
| `graphical_unit_types` | `_graphical_unit_types.info` | 2025-10-28 09:58:56 -07:00 | 2 | Medium |
| `graphical_unit_types` | `00_graphical_unit_types.txt` | 2026-05-09 10:35:11 -07:00 | 2 | Medium |
| `great_projects` | `types\_great_project_types.info` | 2025-12-11 09:48:32 -07:00 | 4 | Medium |
| `great_projects` | `types\00_great_project_types.txt` | 2026-05-09 10:35:02 -07:00 | 4 | High |
| `great_projects` | `types\00_ministry_projects.txt` | 2026-05-09 10:35:02 -07:00 | 4 | High |
| `great_projects` | `types\00_natural_disasters.txt` | 2026-05-09 10:35:01 -07:00 | 4 | High |

| `guest_system` | `00_guest_system.txt` | 2024-03-09 16:30:36 -07:00 | 1 | High |

| `holdings` | `00_holdings.txt` | 2025-11-04 10:49:20 -07:00 | 2 | High |
| `holdings` | `_holdings.info` | 2025-05-11 14:31:10 -07:00 | 2 | Medium |

| `hook_types` | `_hooks.info` | 2024-03-09 16:30:36 -07:00 | 2 | Medium |
| `hook_types` | `00_hook_types.txt` | 2025-12-11 09:48:32 -07:00 | 2 | High |

| `house_aspirations` | `_house_aspiration.info` | 2025-10-28 09:58:56 -07:00 | 5 | High |
| `house_aspirations` | `00_admin_house_powers.txt` | 2025-12-11 09:48:32 -07:00 | 5 | High |
| `house_aspirations` | `10_tgp_celestial_house_powers.txt` | 2025-10-28 09:58:56 -07:00 | 5 | High |
| `house_aspirations` | `10_tgp_japan_house_aspirations.txt` | 2025-11-15 09:19:39 -07:00 | 5 | High |
| `house_aspirations` | `tgp_mandala_devaraja_aspects.txt` | 2026-05-09 10:35:02 -07:00 | 5 | High |

| `house_relation_types` | `_house_relation.info` | 2026-05-09 10:35:01 -07:00 | 2 | High |
| `house_relation_types` | `00_house_relations.txt` | 2026-05-09 10:35:02 -07:00 | 2 | High |

| `house_unities` | `_house_unities.info` | 2024-03-09 16:30:39 -07:00 | 2 | High |
| `house_unities` | `00_house_unities.txt` | 2025-10-28 09:58:54 -07:00 | 2 | High |

| `important_actions` | `_important_actions.info` | 2024-03-09 16:30:39 -07:00 | 34 | Medium |
| `important_actions` | `00_action_take_decision_or_interaction.txt` | 2025-10-28 09:58:54 -07:00 | 34 | Medium |
| `important_actions` | `00_activity_actions.txt` | 2026-05-09 10:35:02 -07:00 | 34 | Medium |
| `important_actions` | `00_artifact_actions.txt` | 2024-03-09 16:30:36 -07:00 | 34 | Medium |
| `important_actions` | `00_diarchy_actions.txt` | 2026-05-09 10:35:01 -07:00 | 34 | Medium |
| `important_actions` | `00_dynasty_actions.txt` | 2024-09-24 09:02:54 -07:00 | 34 | Medium |
| `important_actions` | `00_education_actions.txt` | 2026-05-09 10:35:02 -07:00 | 34 | Medium |
| `important_actions` | `00_inheritance_actions.txt` | 2025-10-28 09:58:53 -07:00 | 34 | Medium |
| `important_actions` | `00_lifestyle.txt` | 2024-11-04 10:06:28 -07:00 | 34 | Medium |
| `important_actions` | `00_marriage_actions.txt` | 2026-05-09 10:35:02 -07:00 | 34 | Medium |
| `important_actions` | `00_mercenaries_actions.txt` | 2024-03-09 16:30:36 -07:00 | 34 | Medium |
| `important_actions` | `00_personal_actions.txt` | 2025-10-28 09:58:53 -07:00 | 34 | Medium |
| `important_actions` | `00_raid.txt` | 2024-03-09 16:30:39 -07:00 | 34 | Medium |
| `important_actions` | `00_reactive_advice.txt` | 2025-12-11 09:48:32 -07:00 | 34 | Medium |
| `important_actions` | `00_reactive_advice_japan.txt` | 2025-10-28 09:58:56 -07:00 | 34 | Medium |
| `important_actions` | `00_reactive_advice_playtest.txt` | 2025-10-28 09:58:56 -07:00 | 34 | Medium |
| `important_actions` | `00_realm_actions.txt` | 2025-10-28 09:58:54 -07:00 | 34 | Medium |
| `important_actions` | `00_temp_actions.txt` | 2024-03-09 16:30:39 -07:00 | 34 | Medium |
| `important_actions` | `00_title_actions.txt` | 2025-10-28 09:58:54 -07:00 | 34 | Medium |
| `important_actions` | `00_war_actions.txt` | 2025-10-28 09:58:53 -07:00 | 34 | Medium |
| `important_actions` | `01_bp1_actions.txt` | 2025-10-28 09:58:56 -07:00 | 34 | Medium |
| `important_actions` | `01_ep1_actions.txt` | 2025-12-11 09:48:32 -07:00 | 34 | Medium |
| `important_actions` | `01_ep1_reactive_advice.txt` | 2025-10-28 09:58:54 -07:00 | 34 | Medium |
| `important_actions` | `01_fp1_actions.txt` | 2025-10-28 09:58:54 -07:00 | 34 | Medium |
| `important_actions` | `03_fp2_actions.txt` | 2024-03-09 16:30:37 -07:00 | 34 | Medium |
| `important_actions` | `03_fp2_reactive_advice.txt` | 2025-03-29 06:45:04 -07:00 | 34 | Medium |
| `important_actions` | `04_ep2_actions.txt` | 2026-05-09 10:35:03 -07:00 | 34 | Medium |
| `important_actions` | `05_bp2_actions.txt` | 2025-10-28 09:58:53 -07:00 | 34 | Medium |
| `important_actions` | `05_fp3_actions.txt` | 2025-03-29 06:45:03 -07:00 | 34 | Medium |
| `important_actions` | `06_ce1_actions.txt` | 2024-03-31 05:41:57 -07:00 | 34 | Medium |
| `important_actions` | `07_ep3_actions.txt` | 2025-11-15 09:19:39 -07:00 | 34 | Medium |
| `important_actions` | `09_mpo_actions.txt` | 2026-05-09 10:35:03 -07:00 | 34 | Medium |
| `important_actions` | `contract_actions.txt` | 2025-10-28 09:58:53 -07:00 | 34 | Medium |
| `important_actions` | `tgp_actions.txt` | 2026-05-09 10:35:02 -07:00 | 34 | Medium |
| `inspirations` | `_inspirations.info` | 2024-03-09 16:30:39 -07:00 | 2 | Medium |
| `inspirations` | `00_inspirations.txt` | 2025-10-28 09:58:54 -07:00 | 2 | Medium |
| `landed_titles` | `00_landed_titles.txt` | 2026-05-09 10:34:58 -07:00 | 11 | Critical |
| `landed_titles` | `01_japan.txt` | 2025-11-15 09:19:39 -07:00 | 11 | Critical |
| `landed_titles` | `01_japan_noble_family.txt` | 2026-05-09 10:35:03 -07:00 | 11 | Critical |
| `landed_titles` | `01_korea_noble_family.txt` | 2025-12-11 09:48:32 -07:00 | 11 | Critical |
| `landed_titles` | `01_other_noble_family.txt` | 2025-11-15 09:19:39 -07:00 | 11 | Critical |
| `landed_titles` | `02_china.txt` | 2026-05-09 10:35:02 -07:00 | 11 | Critical |
| `landed_titles` | `03_seasia.txt` | 2025-12-11 09:48:32 -07:00 | 11 | Critical |
| `landed_titles` | `04_china_noble_families.txt` | 2025-12-11 09:48:32 -07:00 | 11 | Critical |
| `landed_titles` | `05_goryeo.txt` | 2025-12-11 09:48:32 -07:00 | 11 | Critical |
| `landed_titles` | `06_philippines.txt` | 2025-10-28 09:58:56 -07:00 | 11 | Critical |
| `landed_titles` | `_landed_titles.info` | 2025-11-15 09:19:39 -07:00 | 11 | Critical |
| `laws` | `_laws.info` | 2026-05-09 10:35:02 -07:00 | 6 | Critical |
| `laws` | `00_realm_laws.txt` | 2026-05-09 10:35:01 -07:00 | 6 | Critical |
| `laws` | `00_succession_laws.txt` | 2026-05-09 10:35:02 -07:00 | 6 | Critical |
| `laws` | `01_title_succession_laws.txt` | 2026-05-09 10:35:02 -07:00 | 6 | Critical |
| `laws` | `02_admininistrative_laws.txt` | 2025-11-15 09:19:39 -07:00 | 6 | Critical |
| `laws` | `03_imperial_policies.txt` | 2026-05-09 10:35:00 -07:00 | 6 | Critical |
| `lease_contracts` | `_lease_contracts.info` | 2026-05-09 10:35:02 -07:00 | 2 | High |
| `lease_contracts` | `00_theocracy_lease.txt` | 2024-03-09 16:30:36 -07:00 | 2 | High |
| `legends` | `chronicles\_chronicles.info` | 2024-03-09 16:30:36 -07:00 | 6 | High |
| `legends` | `chronicles\00_chronicles.txt` | 2025-10-28 09:58:53 -07:00 | 6 | High |
| `legends` | `legend_seeds\_legend_seeds.info` | 2024-03-09 16:30:36 -07:00 | 6 | High |
| `legends` | `legend_seeds\00_legend_seeds.txt` | 2025-10-28 09:58:54 -07:00 | 6 | High |
| `legends` | `legend_types\_legends.info` | 2024-03-22 06:54:46 -07:00 | 6 | High |
| `legends` | `legend_types\00_legends.txt` | 2025-12-11 09:48:32 -07:00 | 6 | High |
| `legitimacy` | `_legitimacy.info` | 2025-10-28 09:58:53 -07:00 | 2 | High |
| `legitimacy` | `00_legitimacy.txt` | 2026-05-09 10:35:03 -07:00 | 2 | High |
| `lifestyles` | `_lifestyles.info` | 2024-03-09 16:30:37 -07:00 | 2 | High |
| `lifestyles` | `00_lifestyles.txt` | 2025-10-28 09:58:57 -07:00 | 2 | High |
| `lifestyle_perks` | `_lifestyle_perks.info` | 2024-09-24 09:02:55 -07:00 | 19 | High |
| `lifestyle_perks` | `00_diplomacy_1_foreign_affairs_tree_perks.txt` | 2025-11-15 09:19:39 -07:00 | 19 | High |
| `lifestyle_perks` | `00_diplomacy_2_majesty_tree_perks.txt` | 2025-10-28 09:58:54 -07:00 | 19 | High |
| `lifestyle_perks` | `00_diplomacy_3_family_tree_perks.txt` | 2026-05-09 10:35:02 -07:00 | 19 | High |
| `lifestyle_perks` | `00_intrigue_1_skulduggery_tree_perks.txt` | 2025-10-28 09:58:54 -07:00 | 19 | High |
| `lifestyle_perks` | `00_intrigue_2_temptation_tree_perks.txt` | 2025-10-28 09:58:54 -07:00 | 19 | High |
| `lifestyle_perks` | `00_intrigue_3_intimidation_tree_perks.txt` | 2026-05-09 10:35:03 -07:00 | 19 | High |
| `lifestyle_perks` | `00_learning_1_medicine_tree_perks.txt` | 2024-09-24 09:02:55 -07:00 | 19 | High |
| `lifestyle_perks` | `00_learning_2_scholarship_tree_perks.txt` | 2025-11-15 09:19:39 -07:00 | 19 | High |
| `lifestyle_perks` | `00_learning_3_theology_tree_perks.txt` | 2025-11-15 09:19:39 -07:00 | 19 | High |
| `lifestyle_perks` | `00_martial_1_strategy_tree_perks.txt` | 2025-10-28 09:58:53 -07:00 | 19 | High |
| `lifestyle_perks` | `00_martial_2_authority_tree_perks.txt` | 2026-05-09 10:35:02 -07:00 | 19 | High |
| `lifestyle_perks` | `00_martial_3_chivalry_tree_perks.txt` | 2026-05-09 10:35:02 -07:00 | 19 | High |
| `lifestyle_perks` | `00_stewardship_1_wealth_tree_perks.txt` | 2025-10-28 09:58:54 -07:00 | 19 | High |
| `lifestyle_perks` | `00_stewardship_2_domain_tree_perks.txt` | 2026-05-09 10:35:01 -07:00 | 19 | High |
| `lifestyle_perks` | `00_stewardship_3_duty_tree_perks.txt` | 2025-10-28 09:58:53 -07:00 | 19 | High |
| `lifestyle_perks` | `00_wanderer_1_surveyor_tree_perks.txt` | 2025-10-28 09:58:54 -07:00 | 19 | High |
| `lifestyle_perks` | `00_wanderer_2_wayfarer_tree_perks.txt` | 2025-10-28 09:58:53 -07:00 | 19 | High |
| `lifestyle_perks` | `00_wanderer_3_voyager_tree_perks.txt` | 2025-10-28 09:58:53 -07:00 | 19 | High |

| `messages` | `_messages.info` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `00_messages.txt` | 2024-10-08 06:33:07 -07:00 | 40 | Medium |
| `messages` | `01_activity_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_alliance_messages.txt` | 2025-12-11 09:48:32 -07:00 | 40 | Medium |
| `messages` | `01_artifact_messages.txt` | 2025-10-28 09:58:53 -07:00 | 40 | Medium |
| `messages` | `01_character_messages.txt` | 2026-05-09 10:35:02 -07:00 | 40 | Medium |
| `messages` | `01_childhood_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `01_council_messages.txt` | 2025-05-13 16:02:08 -07:00 | 40 | Medium |
| `messages` | `01_court_messages.txt` | 2025-03-29 06:45:03 -07:00 | 40 | Medium |
| `messages` | `01_court_position_messages.txt` | 2025-03-29 06:45:03 -07:00 | 40 | Medium |
| `messages` | `01_culture_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_currency_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `01_death_messages.txt` | 2025-12-11 09:48:32 -07:00 | 40 | Medium |
| `messages` | `01_diarch_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_domain_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_dynasty_messages.txt` | 2026-05-09 10:35:02 -07:00 | 40 | Medium |
| `messages` | `01_faction_messages.txt` | 2025-10-28 09:58:54 -07:00 | 40 | Medium |
| `messages` | `01_family_messages.txt` | 2025-10-28 09:58:53 -07:00 | 40 | Medium |
| `messages` | `01_hook_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `01_law_messages.txt` | 2025-10-28 09:58:54 -07:00 | 40 | Medium |
| `messages` | `01_marriage_messages.txt` | 2026-05-09 10:35:02 -07:00 | 40 | Medium |
| `messages` | `01_multiplayer_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_relationship_messages.txt` | 2025-10-28 09:58:53 -07:00 | 40 | Medium |
| `messages` | `01_religious_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_scheme_messages.txt` | 2025-10-28 09:58:53 -07:00 | 40 | Medium |
| `messages` | `01_secret_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_skill_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `01_struggle_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_title_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `01_travel_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `01_vassal_messages.txt` | 2025-11-15 09:19:39 -07:00 | 40 | Medium |
| `messages` | `01_war_messages.txt` | 2025-12-11 09:48:32 -07:00 | 40 | Medium |
| `messages` | `02_ep1_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `04_ep2_messages.txt` | 2026-05-09 10:35:02 -07:00 | 40 | Medium |
| `messages` | `04_fp3_messages.txt` | 2024-09-24 09:02:55 -07:00 | 40 | Medium |
| `messages` | `05_bp2_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `06_ce1_messages.txt` | 2024-09-24 09:02:54 -07:00 | 40 | Medium |
| `messages` | `07_ep3_messages.txt` | 2025-10-28 09:58:53 -07:00 | 40 | Medium |
| `messages` | `09_mpo_messages.txt` | 2025-05-13 16:02:08 -07:00 | 40 | Medium |
| `messages` | `tgp_messages.txt` | 2026-05-09 10:35:02 -07:00 | 40 | Medium |
| `message_filter_types` | `_message_filter_types.info` | 2024-10-08 06:33:08 -07:00 | 2 | High |
| `message_filter_types` | `00_message_filter_types.txt` | 2026-05-09 10:35:02 -07:00 | 2 | High |
| `message_group_types` | `_message_group_types.info` | 2026-05-09 10:35:11 -07:00 | 2 | High |
| `message_group_types` | `00_message_group_types.txt` | 2025-12-11 09:48:32 -07:00 | 2 | High |

| `modifiers` | `_modifiers.info` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_activity_feast_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_activity_hold_court_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_activity_hunt_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `00_activity_petition_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_activity_pilgrimage_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_activity_playdate_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_activity_roaming_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_activity_tour_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_activity_tournament_modifiers.txt` | 2026-05-09 10:35:00 -07:00 | 132 | High |
| `modifiers` | `00_activity_tours_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `00_activity_wedding_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_artifact_modifiers.txt` | 2025-11-15 09:19:39 -07:00 | 132 | High |
| `modifiers` | `00_basic_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_befriend_scheme_modifiers.txt` | 2025-05-11 14:31:10 -07:00 | 132 | High |
| `modifiers` | `00_bookmark_modifiers.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `00_bp1_modifiers_dan.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_bp2_yearly_4_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_chancellor_task_modifiers.txt` | 2024-03-09 16:30:39 -07:00 | 132 | High |
| `modifiers` | `00_claim_throne_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `00_councillor_spouse_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_counsel_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_county_corruption_modifiers.txt` | 2025-05-11 14:31:10 -07:00 | 132 | High |
| `modifiers` | `00_county_festival_modifiers.txt` | 2025-10-28 09:58:56 -07:00 | 132 | High |
| `modifiers` | `00_county_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_court_chaplain_task_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_court_event_modifiers_claudia.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `00_court_modifiers_james.txt` | 2024-03-09 16:30:39 -07:00 | 132 | High |
| `modifiers` | `00_court_position_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_court_scheme_modifiers.txt` | 2025-05-11 14:31:10 -07:00 | 132 | High |
| `modifiers` | `00_debug_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `00_diarchy_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_diplomacy_lifestyle_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_ep2_travel_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_event_modifiers.txt` | 2026-05-09 10:35:01 -07:00 | 132 | High |
| `modifiers` | `00_fabricate_hook_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_generic_scheme_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `00_governance_lifestyle_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_health_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_historical_artifact_modifiers.txt` | 2026-05-09 10:35:01 -07:00 | 132 | High |
| `modifiers` | `00_holy_order_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_intrigue_lifestyle_modifiers.txt` | 2024-09-24 09:02:54 -07:00 | 132 | High |
| `modifiers` | `00_intrigue_lifestyle_modifiers_2.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_intrigue_scheme_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_laamp_modifiers.txt` | 2026-05-09 10:35:01 -07:00 | 132 | High |
| `modifiers` | `00_learning_lifestyle_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_learning_lifestyle_modifiers_2.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `00_marshal_task_modifiers.txt` | 2025-05-11 14:31:11 -07:00 | 132 | High |
| `modifiers` | `00_martial_lifestyle_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_martial_lifestyle_modifiers_2.txt` | 2025-10-28 09:58:54 -07:00 | 132 | High |
| `modifiers` | `00_murder_scheme_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_nickname_modifiers.txt` | 2024-03-09 16:30:37 -07:00 | 132 | High |
| `modifiers` | `00_parent_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `00_party_baron_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_perk_modifiers.txt` | 2025-10-28 09:58:53 -07:00 | 132 | High |
| `modifiers` | `00_personal_scheme_modifiers.txt` | 2024-09-24 09:02:54 -07:00 | 132 | High |
| `modifiers` | `00_prison_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_province_modifiers.txt` | 2026-05-09 10:35:00 -07:00 | 132 | High |
| `modifiers` | `00_relationship_modifiers.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `00_religion_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_romance_character_modifiers.txt` | 2024-09-24 09:02:54 -07:00 | 132 | High |
| `modifiers` | `00_scheme_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_seduce_character_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_seduce_scheme_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `00_sibling_modifiers.txt` | 2024-03-09 16:30:37 -07:00 | 132 | High |
| `modifiers` | `00_single_combat_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_spymaster_task_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `00_steward_task_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_story_cycle_murders_at_court_modifiers.txt` | 2024-03-09 16:30:37 -07:00 | 132 | High |
| `modifiers` | `00_story_cycle_mystical_animal_modifiers.txt` | 2024-03-09 16:30:39 -07:00 | 132 | High |
| `modifiers` | `00_story_cycle_pet_animal_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_stress_effect_modifiers.txt` | 2026-05-09 10:35:01 -07:00 | 132 | High |
| `modifiers` | `00_sway_scheme_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `00_trait_modifiers.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `00_travel_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_travel_modifiers_oltner.txt` | 2025-10-28 09:58:54 -07:00 | 132 | High |
| `modifiers` | `00_tutorial_modifiers.txt` | 2025-10-28 09:58:57 -07:00 | 132 | High |
| `modifiers` | `00_unity_modifiers.txt` | 2024-03-09 16:30:39 -07:00 | 132 | High |
| `modifiers` | `00_wanderer_lifestyle_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `00_war_and_combat_modifiers.txt` | 2025-05-13 16:02:09 -07:00 | 132 | High |
| `modifiers` | `00_yearly_event_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `01_court_grandeur_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `01_dlc_bp1_filippa_modifiers.txt` | 2024-03-09 16:30:36 -07:00 | 132 | High |
| `modifiers` | `01_dlc_bp1_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `01_dlc_bp1_modifiers_chad.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `01_dlc_bp1_modifiers_claudia.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `01_dlc_bp2_yearly_1_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `01_dlc_ep1_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `01_dlc_fp1_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `01_dlc_fp3_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `01_dlc_roco_modifiers_bianca.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `01_dlc_roco_modifiers_george.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `01_dlc_roco_modifiers_joe.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `01_dlc_xp1_county_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `01_inventory_modifiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `03_dlc_fp2_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `04_bp2_modifiers_3.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `04_ep2_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `04_ep2_modifiers_james.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `04_ep2_modifiers_jason.txt` | 2024-03-09 16:30:37 -07:00 | 132 | High |
| `modifiers` | `05_bp2_modfiers.txt` | 2024-09-24 09:02:55 -07:00 | 132 | High |
| `modifiers` | `05_bp2_modifiers.txt` | 2026-05-09 10:35:01 -07:00 | 132 | High |
| `modifiers` | `06_ce1_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `07_ep3_laamp_flavor_modifiers.txt` | 2026-05-09 10:35:03 -07:00 | 132 | High |
| `modifiers` | `07_ep3_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `07_ep3_modifiers_admin.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `08_beth_nahrian_decision_modifiers.txt` | 2025-03-29 06:45:04 -07:00 | 132 | High |
| `modifiers` | `08_bp3_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `09_ce2_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `09_mpo_kurultai_modifiers.txt` | 2025-05-11 14:31:09 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers_2.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers_anna.txt` | 2025-05-11 14:31:11 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers_nerge.txt` | 2025-05-11 14:31:10 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers_settlement_issues.txt` | 2025-05-11 14:31:10 -07:00 | 132 | High |
| `modifiers` | `09_mpo_modifiers_veronica.txt` | 2025-05-11 14:31:09 -07:00 | 132 | High |
| `modifiers` | `10_ach_az_modifiers.txt` | 2025-11-15 09:19:39 -07:00 | 132 | High |
| `modifiers` | `10_ach_coronation_modifiers.txt` | 2025-09-09 05:59:33 -07:00 | 132 | High |
| `modifiers` | `10_ach_klank_modifiers.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `10_ach_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `10_ach_oath_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `10_tgp_az_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `10_tgp_japan_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `10_tgp_modifiers.txt` | 2026-05-09 10:35:02 -07:00 | 132 | High |
| `modifiers` | `10_tgp_natural_disasters_modifiers.txt` | 2025-12-11 09:48:32 -07:00 | 132 | High |
| `modifiers` | `10_tgp_tai_migration_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `11_bfj_festival_modifiers.txt` | 2025-10-28 09:58:56 -07:00 | 132 | High |
| `modifiers` | `11_tgp_mandala_scheme_modifiers.txt` | 2025-10-28 09:58:56 -07:00 | 132 | High |
| `modifiers` | `12_debug_story_cycle_modifiers.txt` | 2026-05-09 10:35:11 -07:00 | 132 | High |
| `modifiers` | `decision_modifiers.txt` | 2026-05-09 10:35:12 -07:00 | 132 | High |
| `modifiers` | `tgp_mandala_modifiers.txt` | 2025-12-11 09:48:32 -07:00 | 132 | High |
| `modifiers` | `tgp_tribute_mission_modifiers.txt` | 2025-11-15 09:19:39 -07:00 | 132 | High |

| `modifier_definition_formats` | `_definitions.info` | 2025-10-28 09:58:53 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_culture_definitions.txt` | 2024-03-09 16:30:37 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_definitions.txt` | 2026-05-09 10:35:03 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_government_definitions.txt` | 2025-10-28 09:58:54 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_holding_definitions.txt` | 2024-03-09 16:30:36 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_lifestyle_definitions.txt` | 2024-11-04 10:06:28 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_region_definitions.txt` | 2026-05-09 10:35:02 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_religion_definitions.txt` | 2025-10-28 09:58:57 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_scheme_definitions.txt` | 2025-10-28 09:58:53 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_subject_definitions.txt` | 2025-10-28 09:58:57 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_terrain_definitions.txt` | 2025-12-11 09:48:32 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_travel_definitions.txt` | 2025-12-11 09:48:32 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_unit_definitions.txt` | 2025-10-28 09:58:54 -07:00 | 14 | High |
| `modifier_definition_formats` | `00_vassal_stance_definitions.txt` | 2025-05-11 14:31:09 -07:00 | 14 | High |

| `modifier_icons` | `00_modifier_icons.txt` | 2024-03-09 16:30:36 -07:00 | 1 | Low |

| `named_colors` | `culture_colors.txt` | 2026-05-09 10:35:02 -07:00 | 2 | Low |
| `named_colors` | `default_colors.txt` | 2025-11-15 09:19:39 -07:00 | 2 | Low |
| `nicknames` | `_nicknames.info` | 2024-03-09 16:30:37 -07:00 | 11 | Medium |
| `nicknames` | `00_nicknames.txt` | 2025-10-28 09:58:54 -07:00 | 11 | Medium |
| `nicknames` | `01_bp1_nicknames.txt` | 2024-03-09 16:30:37 -07:00 | 11 | Medium |
| `nicknames` | `01_bp2_nicknames.txt` | 2024-03-09 16:30:36 -07:00 | 11 | Medium |
| `nicknames` | `01_fp3_nicknames.txt` | 2024-03-09 16:30:39 -07:00 | 11 | Medium |
| `nicknames` | `01_roco_nicknames.txt` | 2024-03-09 16:30:39 -07:00 | 11 | Medium |
| `nicknames` | `03_fp2_nicknames.txt` | 2024-03-09 16:30:36 -07:00 | 11 | Medium |
| `nicknames` | `04_ep2_nicknames.txt` | 2024-03-09 16:30:39 -07:00 | 11 | Medium |
| `nicknames` | `06_ce1_nicknames.txt` | 2024-03-09 16:30:37 -07:00 | 11 | Medium |
| `nicknames` | `07_ep3_nicknames.txt` | 2025-03-29 06:45:03 -07:00 | 11 | Medium |
| `nicknames` | `10_tgp_nicknames.txt` | 2025-12-11 09:48:33 -07:00 | 11 | Medium |

| `on_action` | `_on_actions.info` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `accolade_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `activities/activities_on_actions.txt` | 2024-03-09 17:07:42 -07:00 | 166 | Critical |
| `on_action` | `activities/coronation_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `activities/debate_on_actions.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `activities/feast_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `activities/festival_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `activities/hold_court_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `activities/hunt_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `activities/imperial_examination_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `activities/journey_on_actions.txt` | 2024-11-04 10:06:29 -07:00 | 166 | Critical |
| `on_action` | `activities/pilgrimage_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `activities/playdate_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `activities/roaming_on_actions.txt` | 2024-11-04 10:06:29 -07:00 | 166 | Critical |
| `on_action` | `activities/survey_on_actions.txt` | 2024-11-04 10:06:29 -07:00 | 166 | Critical |
| `on_action` | `alliance_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `army_on_actions.txt` | 2026-05-09 10:35:01 -07:00 | 166 | Critical |
| `on_action` | `barter_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `birthday.txt` | 2026-05-09 10:35:00 -07:00 | 166 | Critical |
| `on_action` | `bp2_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `ce1_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `character_levels.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `child_birth_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `childhood_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `clan_events_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `combat_on_actions.txt` | 2026-05-09 10:35:01 -07:00 | 166 | Critical |
| `on_action` | `confederation_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `conqueror_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `councillor_on_actions.txt` | 2025-11-15 09:19:39 -07:00 | 166 | Critical |
| `on_action` | `county_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `court_events.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `court_grandeur_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `court_maintenance_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `court_position_on_action.txt` | 2025-03-29 06:45:04 -07:00 | 166 | Critical |
| `on_action` | `court_type_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `courtier_guest_management_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `culture_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `death.txt` | 2026-05-09 10:35:01 -07:00 | 166 | Critical |
| `on_action` | `decision_on_actions.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `diarchy_on_action.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `dlc/bp2/bp2_adult_education_on_action.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `dlc/bp2/bp2_destiny_child_on_action.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `dlc/bp2/bp2_hostage_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `dlc/bp2/bp2_pet_rock_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `dlc/ce1/ce1_funeral_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep1/ep1_court_language_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep1/ep1_inspiration_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep1/ep1_pay_homage_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep1/ep1_petition_liege_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep2/ep2_tour_on_actions.txt` | 2026-05-09 10:35:00 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep2/ep2_tournament_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep2/ep2_wedding_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/camp_party_on_action.txt` | 2025-05-11 14:31:10 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/chariot_race_on_action.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/el_cid_story_cycle_on_action.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/governorship_confirmation_on_action.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/grand_ambitions_story_cycle_on_action.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/harrying_of_the_north_on_action.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/story_adventurer_ai_contract.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `dlc/ep3/violet_poet_on_action.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `dlc/fp2/fp2_other_decision_on_actions.txt` | 2026-05-09 10:35:11 -07:00 | 166 | Critical |
| `on_action` | `dlc/mpo/mpo_on_actions_2.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/mpo/mpo_season_events_on_actions.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `dlc/mpo/mpo_the_great_steppe_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_china_minister_on_action.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_china_yearly_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_japan_poetry_on_actions.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_japan_yearly_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_mandala_on_actions.txt` | 2026-05-09 10:35:03 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_mandala_yearly_on_actions.txt` | 2026-05-09 10:35:11 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_natural_disaster_on_actions.txt` | 2026-05-09 10:35:03 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_pledge_loyalty_to_liege_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_silk_road_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `dlc/tgp/tgp_tribute_mission_on_actions.txt` | 2025-11-15 09:19:39 -07:00 | 166 | Critical |
| `on_action` | `domicile_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `dynastic_cycle_on_actions.txt` | 2025-12-11 09:48:32 -07:00 | 166 | Critical |
| `on_action` | `dynasty_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `ep1_inspirations_on_actions.txt` | 2025-09-09 05:59:33 -07:00 | 166 | Critical |
| `on_action` | `ep3_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `faction_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `fp1_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `fp2_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `fp3_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `game_start.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `governance_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `health_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `holy_order_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `hook_on_actions.txt` | 2024-09-24 09:02:56 -07:00 | 166 | Critical |
| `on_action` | `inventory_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `knight_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/diplomacy_lifestyle_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/general_lifestyle_on_actions.txt` | 2024-11-04 10:06:29 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/intrigue_lifestyle_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/learning_lifestyle_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/martial_lifestyle_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/stewardship_lifestyle_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `lifestyles/wanderer_lifestyle_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `mandate_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `marriage_concubinage.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `mercenary_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `player_select_destiny_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `prison_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `province_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `realm_maintenance_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `relations/bishop_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `relations/jester_on_actions.txt` | 2025-03-29 06:45:04 -07:00 | 166 | Critical |
| `on_action` | `relations/parent_on_actions.txt` | 2024-03-09 16:30:38 -07:00 | 166 | Critical |
| `on_action` | `relations/relation_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `relations/sibling_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `relations/spouse_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `relations/vassal_on_actions.txt` | 2025-05-11 14:31:09 -07:00 | 166 | Critical |
| `on_action` | `religion_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `royal_court_acquisition.txt` | 2026-05-09 10:35:11 -07:00 | 166 | Critical |
| `on_action` | `ruler_designer.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `scheme_on_actions.txt` | 2025-12-11 09:48:32 -07:00 | 166 | Critical |
| `on_action` | `schemes/abduct_on_actions.txt` | 2026-05-09 10:35:01 -07:00 | 166 | Critical |
| `on_action` | `schemes/befriend_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `schemes/claim_throne_on_actions.txt` | 2026-05-09 10:35:03 -07:00 | 166 | Critical |
| `on_action` | `schemes/coerce_and_leverage_contribution_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `schemes/coerce_tributary_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `schemes/court_on_actions.txt` | 2025-05-11 14:31:09 -07:00 | 166 | Critical |
| `on_action` | `schemes/disbelieve_mandala_on_actions.txt` | 2025-10-28 09:58:57 -07:00 | 166 | Critical |
| `on_action` | `schemes/elope_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `schemes/fabricate_hook_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `schemes/learn_language_on_actions.txt` | 2025-10-28 09:58:53 -07:00 | 166 | Critical |
| `on_action` | `schemes/murder_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `schemes/seduce_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `schemes/steal_back_artifact_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `schemes/steal_herd_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `schemes/study_confucian_classics_on_actions.txt` | 2025-10-28 09:58:56 -07:00 | 166 | Critical |
| `on_action` | `schemes/sway_on_actions.txt` | 2024-09-24 09:02:56 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/ep3_story_cycle_admin_eunuch_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/mpo_story_cycle_temujin_flavor.txt` | 2025-05-11 14:31:10 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_cat_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_dog_on_actions.txt` | 2026-05-09 10:35:12 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_doppelganger_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_eagle_on_actions.txt` | 2025-05-11 14:31:09 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_foreign_raised_reformer_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_hostage_loyalty_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_house_feud_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_hunt_mystical_animal_on_actions.txt` | 2024-09-24 09:02:55 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_imaginary_friend_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_murders_at_court_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_party_baron_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_peasant_affair_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_roman_restoration_on_actions.txt` | 2024-09-24 09:02:56 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_statecraft_lifestyle_respected_liege_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_sycophant_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_tax_rivalry_on_actions.txt` | 2025-05-11 14:31:10 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_turkic_tribe_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_unity_decisions_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_visited_by_ghosts_on_actions.txt` | 2026-05-09 10:35:11 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_warhorse_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `story_cycles/story_cycle_witch_trial_on_actions.txt` | 2024-03-09 16:30:39 -07:00 | 166 | Critical |
| `on_action` | `stress_coping_decisions_on_actions.txt` | 2024-03-09 16:30:37 -07:00 | 166 | Critical |
| `on_action` | `stress_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `struggle_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `task_contract_on_actions.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `title_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `traits_on_actions.txt` | 2026-05-09 10:35:11 -07:00 | 166 | Critical |
| `on_action` | `travel_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `tutorial.txt` | 2025-10-28 09:58:54 -07:00 | 166 | Critical |
| `on_action` | `war_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `witch_on_actions.txt` | 2024-03-09 16:30:36 -07:00 | 166 | Critical |
| `on_action` | `yearly_groups_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |
| `on_action` | `yearly_on_actions.txt` | 2026-05-09 10:35:02 -07:00 | 166 | Critical |

| `opinion_modifiers` | `_opinions.info` | 2025-05-11 14:31:10 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_feast_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_festival_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_hunt_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_pilgrimage_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_playdate_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_activity_system_opinons.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_birth_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_childhood_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_claim_throne_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_council_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_council_task_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_court_events_opinions_linnea.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_crime_and_prison_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_decision_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_doctrinal_crime_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_dynasty_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_education_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_election_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_fabricate_hook_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_friendship_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_holy_order_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_intrigue_scheme_opinions.txt` | 2026-05-09 10:35:00 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lifestyle_governance_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lifestyle_intrigue_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lifestyle_medicine_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lifestyle_statecraft_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lifestyle_wanderer_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_lover_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_marriage_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_martial_lifestyle_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_opinion_modifiers.txt` | 2026-05-09 10:35:00 -07:00 | 71 | High |
| `opinion_modifiers` | `00_peasant_affair_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_poetry_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_prison_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_regional_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_religious_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_rival_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_romance_and_adultery_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_scheme_befriend_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_scheme_seduce_opinion.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_scheme_sway_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_sibling_opinions.txt` | 2026-05-09 10:35:01 -07:00 | 71 | High |
| `opinion_modifiers` | `00_spouse_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_stress_effect_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_struggle_opinions.ola.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `00_title_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `00_travel_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `00_vassal_promise_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `00_war_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_bp1_filippa_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_bp1_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_bp2_yearly_1_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_ep1_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_fp1_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `01_dlc_fp3_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `01_roco_opinions.txt` | 2026-05-09 10:35:00 -07:00 | 71 | High |
| `opinion_modifiers` | `02_dlc_bp1_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `03_dlc_fp2_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `04_dlc_ep2_filippa_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `04_dlc_ep2_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `05_dlc_bp2_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `06_dlc_ep3_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `09_mpo_opinions.txt` | 2026-05-09 10:35:03 -07:00 | 71 | High |
| `opinion_modifiers` | `10_ach_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |
| `opinion_modifiers` | `10_dlc_tgp_japan_opinions.txt` | 2026-05-09 10:35:00 -07:00 | 71 | High |
| `opinion_modifiers` | `10_dlc_tgp_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `tgp_imperial_examination_opinions.txt` | 2026-05-09 10:35:12 -07:00 | 71 | High |
| `opinion_modifiers` | `tgp_mandala_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `tgp_treasury_opinions.txt` | 2026-05-09 10:35:02 -07:00 | 71 | High |
| `opinion_modifiers` | `tgp_tribute_mission_opinions.txt` | 2026-05-09 10:35:11 -07:00 | 71 | High |

**Current stopping point:** `opinion_modifiers` completed at 71 of 71 files. Continue with `playable_difficulty_infos`.
