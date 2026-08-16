# Architecture Overview

The CK3 Tracker is built on a provider-based architecture:

- Providers load and normalize data.
- DashboardService aggregates metrics.
- Dash pages render UI components.
- Plotly figures provide charts.

The architecture has four distinct layers:

1. **Reference layer** — CK3 Scribe files and validated wiki extracts define the title map and decision vocabulary.
2. **Parquet data layer** — normalized parquet datasets provide durable run storage, current state, and history.
3. **Journal layer** — dated observations, goal changes, control updates, and milestones preserve the story.
4. **Presentation layer** — Dash pages summarize current state and historical progress.

This document describes the high-level structure and relationships between components.

## Current Status
The project is currently in a holdings-first stabilization phase. The holdings page is functional with realistic seeded data so the app remains usable while the parquet-backed implementation is still being finalized. The new-run creation flow is intentionally deferred as an admin task until the holdings section is fully assembled.

## Product Model: Living Run Journal

The application is the living journal of a Crusader Kings III run. A run begins at the tracked ruler's birth and remains active until the player explicitly declares the run dead. The app must preserve the story of the run across that entire lifetime rather than only showing the latest snapshot.

Core lifecycle states:

- `active`: the run is ongoing and accepts new observations and updates
- `dead`: the player has ended the run; its history remains readable and becomes read-only

The seeded data and dead-run placeholder represent this lifecycle concept during development. They establish the shape of a run record that will later be backed by real playthrough data.

Architectural implications:

- Keep the run identity and ruler identity stable for the full journal lifetime.
- Preserve dated observations and goal changes as history instead of overwriting the past.
- Derive current dashboard and holdings views from the latest valid run state.
- Keep historical snapshots available for reviewing how the realm changed.
- Treat declaring a run dead as a lifecycle event, not as deletion.
- Prevent updates after death while allowing the completed journal to remain browseable.

## Map Scope and Canonical Titles

The application tracks the CK3 title hierarchy, not real-world geography. CK3 title IDs and CK3 county-to-duchy-to-kingdom relationships are authoritative. Display names are labels only and may be shared by different title levels or titles.

The project has two distinct data profiles:

- `seed`: a small synthetic map used to prove UI behavior and interaction
- `ck3_867`: the canonical game map used for real runs and goal resolution

These profiles must not be mixed. A goal such as forming Sicily must resolve against the active profile's CK3 title records. The seed profile may use simplified or imperfect names, but it must never be treated as evidence of the real CK3 hierarchy.

The application is permanently scoped to the 867 start date. There will be no start-date selector and no support for the 1066 or 1178 starts. The point of the journal is to measure how long a realm can survive from the 867 starting position as the run develops and stronger external powers begin to threaten it. All joins and goal calculations must use the title IDs defined by CK3 itself, not display-name matching. Any map-profile change must reload the complete title hierarchy together so counties, duchies, kingdoms, holdings, and goals remain internally consistent.

The supported game data contract is CK3 `1.19.0.6 (Scribe)`. Reference snapshots and persisted runs must carry `game_version` and `start_date` metadata. Reference data from another CK3 version must be rejected or explicitly migrated rather than silently mixed into a Scribe run.

The duchy import must include only titles from the source's `De jure duchies` section. Titles listed under `Uncreatable duchies` are exempt and must be excluded from canonical duchy records, goal population, county progress, and title-creation calculations.

The duchy metadata should retain the source's special-building information. Special buildings are metadata for the duchy/title record and must not be inferred from ordinary holding buildings.

## Reference Source Responsibilities

`raw/ck3_867_00_landed_titles.txt` is authoritative for title identity and hierarchy. The parser must preserve CK3 IDs and resolve empire → kingdom → duchy → county → barony relationships.

`raw/duchies_source.html` is a validated 867 reference extract for duchy-level metadata. It contributes county count, barony count, average development, capital county, and special-building information. Its `Uncreatable duchies` section is excluded.

`raw/barony_source.html` is a candidate barony source, but its records must be validated against the landed-title hierarchy before becoming canonical.

`ruler_decisions` is the source for goal definitions. A decision can describe result titles, regions, required duchies, alternative requirement groups, costs, prerequisites, and effects. It is not a source of current playthrough control.

The reference layer and parquet data layer must remain separate. Static files explain what the game allows; parquet records explain what happened in the player's run. Manual updates are writes to parquet-backed run state and journal events.

## Parquet Data Contract

Parquet is the persistence backbone, not merely an export format. Datasets should be normalized around stable keys and retain history rather than overwrite it:

- `playthroughs`: run identity, ruler identity, `game_version`, `start_date`, lifecycle state
- `holdings`: canonical holding records and latest run state
- `holding_events`: dated acquisition and metric updates
- `goals`: selected decision goals and their versioned definitions
- `goal_targets`: resolved regions, titles, counties, and baronies for each goal
- `goal_progress_events`: manual control, completion, exception, and note updates
- `journal_events`: dated observations, milestones, threats, and run lifecycle events

Current-state views may be derived from the latest parquet records, but historical rows must remain available for the living journal.

## Replay and Version Comparison

A challenge may be attempted repeatedly across game updates. A `challenge_id` groups attempts of the same goal, while each `playthrough_id` remains an independent run. Comparisons should use the immutable run metadata and journal history to show how outcomes changed between Scribe versions or future versions.

The comparison layer must not merge runs into one current state. It should compare survival duration, goal progress, succession outcomes, major milestones, failure points, and completion/death results.

## Realm and Succession State

Realm state is distinct from House state. Realm/Succession records capture the current political structure and the consequences of the current succession law: primary title, realm size, government, player heir, designated heir, partition type, inherited titles, titles lost, and title recipients. A succession forecast is current state; the actual succession is a dated journal event that remains in history.

# Providers

## HoldingsProvider
Loads baseline + playthrough holdings, joins them, and returns enriched Holding objects. At the moment, it uses seeded sample rows to keep the UI stable while the final parquet-backed logic is being built.

## CountiesProvider
Loads county metadata.

## DuchiesProvider
Loads duchy metadata.

## CharacterProvider
Loads character/domain limit data.

## DashboardService
Aggregates all provider data into dashboard metrics.

# Dashboard Requirements

The dashboard displays:

- Counties Owned
- Domain Limit
- Duchies Held
- Domain Size
- Total Tax
- Total Levies
- Low Control Count
- Average Development
- Terrain Distribution

### Duchy Summary Table

The duchy summary is driven by the selected playthrough goal. A goal such as `Form Kingdom of Sicily` supplies a target title. `DashboardService` resolves that title's constituent duchies, then derives progress from county ownership and duchy membership. The table is therefore an automatically populated goal worklist, not a fixed list of duchies.

The summary is rendered as one row per target duchy with these fields:

- `duchy_name`: displayed as `Duchy`
- `counties_held`: number of counties currently held, displayed as `Have`
- `county_count`: total counties in the duchy, displayed as `Count`
- `title_state`: current source title marker, displayed as `Title`

The table also has a summary row for the selected target title. Its `Have` value is the total held counties within the goal scope, its `Count` value is the total counties in that scope, and its percentage is calculated as:

`counties_held_percent = counties_held / county_count * 100`

Changing the goal must replace the target title, repopulate the target duchies, and recalculate all rows. This summary is a read-only aggregation. It should be computed from the goal, county, duchy, and title providers rather than maintained as independent mutable data.

## Goal Progress Bridge

The goal workflow is intentionally a bridge between static CK3 rules and lived run state:

1. Select a ruler decision such as Restore Old Vasconia or Restore Carthage.
2. Read the decision's requirements and effects.
3. Resolve named regions, kingdoms, duchies, counties, and baronies through canonical CK3 IDs.
4. Present the resulting worklist to the player.
5. Let the player manually record control, completion, exceptions, and notes.
6. Calculate progress without overwriting the underlying decision definition.
7. Record when a target or decision was achieved in the living journal.

Requirement groups must be preserved. For example, "completely control at least four of the following duchies" is not equivalent to requiring every listed duchy. The UI should show both the candidate list and the threshold.

## Domain and Realm Conditions

Goal progress must preserve two distinct ownership scopes:

- **Domain** — counties or holdings personally held by the player character.
- **Realm** — counties or holdings held by the player or by vassals within the player's realm.

These scopes must never be collapsed into one `Have` value. A goal may require realm control while a planning view may separately show how much is in the ruler's direct domain. Progress records should identify the scope they measure, for example `domain_count`, `realm_count`, `domain_complete`, and `realm_complete`.

The decision definition is authoritative for which scope applies. The UI may show both scopes when useful, but it must not imply that direct domain ownership is required when the game only requires realm control.

All metrics come from DashboardService.

# Data Flow

Reference files → Reference parsers → Canonical title/decision records

Run-state files + manual journal updates → Providers/services → Current run state

Canonical reference records + current run state → DashboardService → Dash UI

DashboardService calls:
- get_holdings()
- get_counties()
- get_duchies()
- get_character()
- get_goal()
- get_title_hierarchy()

Then computes metrics and returns a dictionary consumed by the UI.

# Roadmap

## Phase 1 — Core Providers
- HoldingsProvider
- CountiesProvider
- DuchiesProvider
- CharacterProvider

## Phase 2 — Dashboard Metrics
- Implement DashboardService
- Bind metrics to UI

## Phase 3 — Visualizations
- Terrain chart
- Development histogram
- Levies/tax charts

## Phase 4 — Tabs
- Holdings
- Counties
- Duchies
- Ruler

## Phase 5 — Advanced Features
- Realm composition
- Council
- Goals
- Dynasty
- Wars

## Priority Note
The next engineering priority is to complete the holdings layer cleanly before reintroducing the new-run/admin creation workflow.

