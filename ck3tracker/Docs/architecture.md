# Architecture Overview

> **Authority:** This document defines durable architecture only. It does not define the current implementation sequence. `Docs/current_build.md` is the sole execution manifest and overrides roadmap or priority language below.

The CK3 Tracker is built on a provider-based architecture:

- Providers load and normalize data.
- DashboardService aggregates metrics.
- Dash pages render UI components.


The architecture has five distinct layers:

1. **Reference layer** — versioned CK3 Wiki snapshots define the domain catalog and player-facing vocabulary; installed core and DLC files supply build-specific implementation evidence.
2. **Database layer** — `ck3tracker_v2.duckdb` stores source provenance, versioned normalized reference tables, journal state, and application views.
3. **Transaction layer** — DuckDB stores mutable run state, observations, lifecycle transitions, and event history atomically.
4. **Journal layer** — dated observations, goal changes, control updates, and milestones preserve the story.
5. **Presentation layer** — Dash pages summarize current state and historical progress.

This document describes the high-level structure and relationships between components.

## Primary Database Boundary

The application database is the repository-root `ck3tracker_v2.duckdb`. The source pipeline turns wiki HTML/text and installed CK3 text data into typed, relational DuckDB tables that the application can query directly.

Recommended logical schemas:

- `source`: wiki revisions, game scans, files, DLC metadata, parser runs, and provenance
- `reference`: versioned titles, hierarchy, cultures, faiths, buildings, rules, and other normalized game concepts
- `journal`: playthroughs, observations, lifecycle transitions, plans, memories, and transaction events
- `app`: current-state and derived views consumed by providers and pages

Reference rows are immutable within a `reference_snapshot_id`. A game update creates a new snapshot rather than overwriting the prior version. Mutable journal transactions remain scoped to a playthrough and reference the snapshot used by that run.

Parquet and CSV are optional export, interchange, fixture, and archival formats. They are not the primary operational destination for parsed source data. The trial Parquet files and `data/trial/run_state.duckdb` are development fixtures, not the final database boundary.

## Current Status
The project is validating a candidate Scribe reference catalog in the root DuckDB. Landed titles, English localization, title and character history, bookmarks, and capital semantics are loaded but remain unpromoted. The read-only Reference Inspector is the temporary proof surface while promotion blockers and gate integrity are resolved. Consult `Docs/current_build.md` for exact counts and the next action.

## Workbook and Dashboard Boundary

The seed workbook, including `ck3_bambino_starts_867_dashboard.xlsx`, is a visual and workflow specification for the eventual dashboard. Its sheets, Excel tables, ranges, formulas, and cell addresses are not runtime data contracts and must not be reproduced as production storage or exposed as application identifiers.

- Preserve the workbook's visual hierarchy, grouping, questions, and player workflow as design evidence.
- Build the complete normalized item catalog in `ck3tracker_v2.duckdb` before redesigning the main dashboard around that concept.
- Read dashboard values through DuckDB-backed providers and services only.
- Do not reference workbook sheet names, Excel table names, ranges, or formulas in page callbacks, providers, database schemas, or user-facing labels.
- Replace workbook table layouts with appropriate interactive views, summaries, filters, and journal controls once the underlying catalog is complete.
- Keep the Reference Inspector separate from the final dashboard. It is a read-only engineering and visual validation tool for candidate data, not the finished player journal experience.

## Product Model: Living Run Journal

### Ruler Memory File Boundary

`Docs/ruler_memories.md` is the reusable template only. It must never be overwritten with a user's pasted memory feed or a run's imported content. Each playthrough owns a separate `run_ruler_memories.md` record, linked to its import batches and reviewed memory entries. Imported clipboard text and screenshots remain source evidence until reviewed; they do not mutate the template or become factual observations automatically.

### Evidence Archive Limits (Review)

The screenshot archive is a bounded evidence archive, not a general image bucket. A retained image must belong to a declared evidence set for a Barony, County, Duchy, or ruler-memory import and have a stated capture role. Unassigned, duplicate, unrelated, or over-limit images must not receive permanent storage. Numeric limits per set, byte limits, image-dimension limits, and retention rules remain open review decisions; do not invent them during implementation.

Evidence-set directories use six-digit zero-padded sequence IDs so a long 867-1453 run is not constrained by a four-digit namespace: `set_000000`, `set_000001`, and so on. The sequence is scoped to the playthrough and is an identifier, not a date or an observation count.

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

### Canon Law: Title Containment

The containment hierarchy is fixed and must never be inverted:

```text
Barony -> County -> Duchy -> Kingdom -> Empire
```

- A County contains Baronies.
- A Duchy contains Counties.
- A Barony never contains a County or Duchy.
- A Duchy count is derived from its Counties and their Baronies; it must not be used as the parent of a County's barony records.
- UI labels, joins, summaries, and progress calculations must preserve this direction. When in doubt, resolve parentage from CK3 title IDs and the landed-title hierarchy, not from display names.

The project has two distinct data profile classes:

- `seed`: a small synthetic map used to prove UI behavior and interaction
- promoted CK3 baselines: complete, versioned title and historical-state profiles used for real runs and goal resolution

These profiles must not be mixed. A goal such as forming Sicily must resolve against the active profile's CK3 title records. The seed profile may use simplified or imperfect names, but it must never be treated as evidence of the real CK3 hierarchy.

### Baseline Completeness Contract

Promoted CK3 baselines follow the strict complete-state policy recorded in `Docs/architecture_decision_001_baseline_completeness.md`. Every baseline-effective operation that changes supported game state must be deterministically evaluated and represented in durable typed state, whether or not the current journal UI consumes that field.

Starting court language, court type, administrative state faith, holder language knowledge, title-scoped variables, and title laws are part of historical-state completeness. Their mutability after game start does not make their initial values optional. An accepted exception is limited to a proven inactive branch, true no-op, or operation that produces no persistent state; lack of a current product consumer is not sufficient.

The application may start a journal at any CK3 location contained in a promoted reference baseline. Run creation first selects a supported baseline or bookmark date, then narrows the title hierarchy through searchable, cascading filters such as Empire, Kingdom, Duchy, County, and Barony. The final selection is persisted by stable CK3 IDs; display names are labels only. Changing an upstream filter clears incompatible descendants, and the application must preview the fully resolved hierarchy before committing the run.

A selectable baseline date is not the same as an arbitrary in-game observation date. The UI may offer only dates whose title hierarchy and historical state have been parsed, validated, and promoted for the selected reference snapshot. Later dates belong to the journal timeline unless a separate reference baseline exists for them. The current retained data proves only the 867 baseline; additional bookmarks such as 1066 or 1178 become selectable only after their source inputs and validation pass. Any baseline change must load the complete title hierarchy together so counties, duchies, kingdoms, holdings, rulers, and goals remain internally consistent.

The current supported game data contract is CK3 `1.19.0.6 (Scribe)`. Reference snapshots and persisted runs must carry `game_version`, `reference_snapshot_id`, `baseline_id`, and `start_date` metadata. Reference data from another CK3 version or baseline must be rejected or explicitly migrated rather than silently mixed into a run.

Reference updates follow `Docs/game_update_protocol.md`. Each game update creates a new candidate snapshot, compares wiki revisions and installed-file manifests, reparses affected loader groups, and promotes the snapshot only after validation. Existing runs remain pinned to their original reference snapshot.

The duchy import must include only titles from the source's `De jure duchies` section. Titles listed under `Uncreatable duchies` are exempt and must be excluded from canonical duchy records, goal population, county progress, and title-creation calculations.

The duchy metadata should retain the source's special-building information. Special buildings are metadata for the duchy/title record and must not be inferred from ordinary holding buildings.

## County Capital Changes

`b_capital` identifies the county's current primary castle, but it is not permanently immutable. A county can change its capital when the game conditions allow it, including the requirement that at least two castles exist in the county. This is a run-state change and must not rewrite the selected baseline's title reference.

The journal must preserve both:

- `original_capital_barony_id`: the capital from the selected baseline hierarchy
- `current_capital_barony_id`: the capital after any in-run change

Changing the capital can have irreversible economic consequences. The former capital may lose a duchy-level capital bonus and, where applicable, lose a building slot. A new capital does not automatically regain the lost slot or bonus. The model must therefore record the capital-change event and its resulting slot/bonus state rather than deriving current capacity only from the new capital.

The domain/holding view should expose capital status, capital history, building slots, and lost-capital effects separately. In the captured Scribe `00_landed_titles.txt` source, the county block does not always contain an explicit `capital = b_*` field; the first barony listed under the county is the primary capital castle. The player's later capital decision belongs in DuckDB journal state.

## County Screen Icon Semantics

The county breakdown screen supplies behavioral evidence for the hierarchy and controls:

- The faint divider below the county-holder section and above the holding icons separates county data from barony/holding data.
- Each holding icon in the lower section represents one barony.
- The silver crown marks the county's capital barony.
- The greyed realm-up-arrow control is the move-realm-capital action; it is not an additional holding, title, or capital-barony marker.
- A selected holding's label such as `Your Castle Holding` describes the selected barony only and must not be used to count all baronies in the county.

For the Mallorca proof slice, Mayurqa contains two baronies: Alcudia as a city and Palma as the capital castle. Palma must be present in the barony breakdown even when the initially selected holding view is Alcudia.

## Daily County and Barony State

County and barony values are live run-state observations and can change on each in-game day tick. They must be stored with an observation date or timestamp rather than treated as static reference metadata.

County-wide state:

- control
- development
- popular opinion
- culture
- faith

Barony/holding state contributes additive holding-level values beneath the county section:

- tax
- loot
- levies
- supply limit
- plague resistance
- garrison
- fort level
- regular building slots
- duchy building slot

`Garrison` and `Fort level` are separate values. For example, `Garrison: 480` and `Fort level: 4` must not be confused with `Castle level: 1`, which describes the holding type/level display. The two regular building slots and the separate duchy-building slot are also distinct capacity fields.

The inward-arrow duchy building slot is a visual indicator that the holding belongs to a true de jure duchy associated with the duchy title icon in the county hierarchy. This visual evidence should be represented as a validated `is_de_jure_duchy`/duchy-building-slot state, not inferred from the holding name alone.

## Reference Source Responsibilities

The [Crusader Kings III Wiki](https://ck3.paradoxwikis.com/Crusader_Kings_III_Wiki) is the project's primary reference catalog for mechanics, titles, decisions, buildings, cultures, faiths, warfare, DLC scope, and player-facing vocabulary. Every retained wiki extract must record its page URL, revision or permanent-link ID when available, retrieval timestamp, stated game version, and review status. A wiki page is reference evidence, not a live-run observation, and community-maintained content must not be assumed current without version review.

The installed CK3 `game` tree is read-only build evidence. It supplies stable script IDs, hierarchy declarations, trigger/effect implementation, localization keys, history, map relationships, and the exact core/DLC content present in the inspected build. Game-file evidence validates and specializes the wiki model for a supported version; it does not replace the wiki as the reference catalog.

`raw/ck3_867_00_landed_titles.txt` is a captured game-file extract used to verify title IDs and hierarchy for the supported build. The parser must preserve CK3 IDs and resolve empire → kingdom → duchy → county → barony relationships.

`raw/duchies_source.html` is a validated 867 wiki extract for duchy-level metadata. It contributes county count, barony count, average development, capital county, and special-building information. Its `Uncreatable duchies` section is excluded.

`raw/barony_source.html` is a candidate barony source, but its records must be validated against the landed-title hierarchy before becoming canonical.

`ruler_decisions` is the source for goal definitions. A decision can describe result titles, regions, required duchies, alternative requirement groups, costs, prerequisites, and effects. It is not a source of current playthrough control.

Reference evidence and run-state evidence must remain logically separate inside DuckDB. Wiki snapshots and installed game files explain the documented and build-specific game model. Versioned reference tables preserve normalized source facts; journal tables record what happened in the player's run through observations, transactions, and events. Parquet may export either layer without becoming its source of truth.

## Trial Evidence Model

The current trial proves the model with two contrasting cases:

- `d_mallorca`: three Domain counties and four directly held baronies
- `d_kroumerie`: two Realm counties and two observed vassal holdings, with eight canonical base baronies

The trial distinguishes three kinds of data:

- **Base data**: the complete canonical title/slot structure for the 867 map
- **Observed run data**: values visible in screenshots for a specific dead run snapshot
- **Derived data**: Domain/Realm counts, title progress, and validation results calculated from the first two layers

Missing screenshots do not invalidate the base structure. They only mean the corresponding live holding values remain unobserved until the player supplies them.

## Source Order and UI Slot Order

The order of barony declarations in `00_landed_titles.txt` is not guaranteed to be the order shown in the in-game holding slots. Both values must be preserved separately:

- `source_order`: canonical declaration order from CK3 files
- `ui_slot_number`: observed in-game slot position

UI slot mappings are evidence-backed run/reference metadata. They must not be inferred from source order alone. The Constantine trial mapping is:

```text
1 b_constantine  castle/county capital
2 b_qasr-al-ifriqi city
3 b_tijis        open
4 b_tifash       temple
5 b_taburshiq    open
```

## County Acquisition Bridge

When a county enters a run, the acquisition workflow resolves the complete base barony set, applies any validated UI slot mapping, and creates one acquisition event plus one run-state row per barony. This allows a county with only partial screenshot evidence to retain a complete structural record without fabricating unseen daily stats.

For the current Kroumerie trial, `c_constantine` has five UI slots and `c_annaba` has three BASE baronies. The acquisition bridge creates all structural rows immediately, while live daily fields remain unknown until observed. The current vassal proof contains two observed city holdings and six remaining barony observations are still outstanding.

## Data Contract

The root DuckDB stores immutable versioned reference rows and transactional playthrough history in separate logical schemas. Tables should be normalized around stable keys and retain history rather than overwrite it:

- `playthroughs`: run identity, ruler identity, `game_version`, `start_date`, lifecycle state
- `holdings`: canonical holding records and latest run state
- `holding_events`: dated acquisition and metric updates
- `goals`: selected decision goals and their versioned definitions
- `goal_targets`: resolved regions, titles, counties, and baronies for each goal
- `goal_progress_events`: manual control, completion, exception, and note updates
- `journal_events`: dated observations, milestones, threats, and run lifecycle events

The current trial state database stores lifecycle transitions, acquisition events, and mutable barony snapshots in `data/trial/run_state.duckdb`, with static fixtures in Parquet. These are development fixtures to migrate into the root DuckDB; they do not define the final storage boundary. Historical rows must remain available throughout migration and in the living journal.

### Bronze Transaction Boundary

The first complete editor transaction is a barony observation. It validates the target against immutable reference data, appends a dated observation and transaction event in DuckDB, and refreshes affected views. The application records what the player observed; it does not claim continuous game-tick synchronization and does not modify savegames.

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

The workbook concept guides the eventual composition and information hierarchy of this page, but the implementation is deferred until the full reference item catalog is available. Every metric and item shown here must come from `DashboardService` or another DuckDB-backed read model; no spreadsheet table or cell reference may survive into the production UI contract.

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

# Historical Implementation Roadmap

This roadmap records the original application sequence. It is not a resume point and does not override `Docs/current_build.md`.

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
Historical note: holdings completion preceded the current reference-catalog work. The active engineering priority is defined only in `Docs/current_build.md`.

