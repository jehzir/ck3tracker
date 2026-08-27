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

**Stopping point:** `artifacts` completed. Continue with `bookmarks`.
