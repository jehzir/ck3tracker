---

# 📘 CK3 Tracker — Project Blueprint  
*A clean, structured, GitHub‑ready plan for the CK3 Tracker Dash App.*

> **Historical blueprint:** This checklist preserves early project intent and completed scaffolding history. It is not authoritative for current status, storage contracts, or implementation order. Use `Docs/current_build.md` for the sole current path and `Docs/architecture.md` for durable boundaries.

---

## ✅ Overview
The **CK3 Tracker** is a Dash application that visualizes Crusader Kings III realm data extracted from parquet files.  
This document defines the architecture, providers, data flow, dashboard requirements, and implementation steps.

Use this file as a **project map**.  
Check off items as you complete them.

## 📖 Living Journal Goal
The app is the living journal of a run, beginning with the tracked ruler's birth and continuing until the player decides the run is dead. It must retain the run's history, goals, realm changes, and observations so the current dashboard is only the latest view of a longer story.

The run lifecycle is:

- `active`: accepts observations, goal changes, and holdings updates
- `dead`: player-declared end state; history remains visible but updates are blocked

The existing seeded data and dead-run placeholder are the initial implementation of this lifecycle and should remain useful while real parquet integration is developed.

### Journal Requirements
- stable playthrough and ruler identity from birth through death
- dated run observations and state changes
- historical goal records, including the duchies populated for each goal
- current-state views derived from the latest journal state
- readable completed journals after a run is declared dead
- no destructive deletion when a run ends

### Map Profile Boundary
- Use CK3 title IDs and the CK3 title hierarchy as the canonical source.
- Canon law: `Barony -> County -> Duchy -> Kingdom -> Empire`. A County contains Baronies, and a Duchy contains Counties; never reverse these relationships in data models, UI labels, joins, or counts.
- Treat the current small seeded map as a synthetic UI-test profile only.
- Keep the seed profile separate from the full CK3 map; never combine their records.
- Resolve goals and duchy membership by stable IDs, never by familiar display names.
- Load one internally consistent map profile for a run before calculating dashboard progress.
- Import only de jure duchies; exclude all uncreatable duchies because they are exempt from the goal workflow.
- Allow a run to start at any location in a promoted CK3 baseline by filtering the canonical hierarchy and persisting stable title IDs.
- Offer only baseline or bookmark dates that have complete parsed history and have passed promotion validation for the selected reference snapshot.
- Preserve CK3-defined title IDs exactly as the canonical keys.
- Preserve the source special-building list on duchy metadata records.

### Survival Journal Objective
The central question of a run is: how does this ruler and realm develop from the selected CK3 baseline until the player declares the journal complete or dead? Features should support recording the realm's growth, goals, pressures, threats, and eventual outcome across that timeline. The current retained reference data supports 867; additional bookmarks become available only after their historical state is parsed and promoted.

---

## 📂 Data Sources

### Canonical Reference Sources
- `raw/ck3_867_00_landed_titles.txt` — installed CK3 title hierarchy and canonical title IDs
- `raw/duchies_source.html` — validated 867 de jure duchy metadata, counts, development summary, capitals, and special buildings
- `raw/barony_source.html` — candidate barony reference source; unverified until checked against `00_landed_titles.txt`
- CK3 `ruler_decisions` — goal definitions, requirements, required regions/titles, costs, and effects

Reference snapshot metadata:
- game version: `1.19.0.6 (Scribe)`
- candidate baseline date under promotion review: `867` (not selectable until explicit promotion)
- title hierarchy source: installed CK3 game files
- wiki metadata source: CK3 Wiki pages captured for the matching game data

### Reference and Run-State Sources
Current development fixtures:

- `holdings.parquet`
- `playthrough_holdings.parquet`
- `counties.parquet`
- `duchies.parquet`
- `characters.parquet`
- `data/trial/run_state.duckdb`

The final application database is the repository-root `ck3tracker_v2.duckdb`. It stores source provenance, immutable versioned reference tables, imports, mutable run state, observations, lifecycle transitions, journal events, and application views in separate logical schemas. The files above are fixtures used by the current trial and must be migrated without losing history.

### Unified DuckDB Backbone
All persistent application records should be normalized in the root DuckDB around `reference_snapshot_id`, `playthrough_id`, stable CK3 IDs, observation/event dates, and provenance. Parquet and CSV are optional export, archival interchange, and fixture formats. DuckDB-backed records include:

- wiki revisions, installed-file scans, DLC metadata, and parser runs
- versioned normalized CK3 reference tables
- run identity and lifecycle
- ruler history
- current and historical holdings
- county and duchy progress
- selected goals and requirement status
- manual control updates
- journal observations, milestones, threats, and completion events

Every persisted run must record the reference snapshot it was created against, including `game_version` and `start_date`. A Scribe run must not silently load reference data from another game version.

### Playthrough Baseline Selector
Run creation establishes an immutable starting context before observations begin:

1. Select a supported game reference snapshot and promoted baseline or bookmark date.
2. Search and filter the title hierarchy using stable parent relationships: Empire, Kingdom, Duchy, County, then Barony where applicable.
3. Select or enter the tracked ruler identity supported by the baseline evidence.
4. Preview the resolved location chain, baseline date, ruler, culture, faith, holder, and capital facts; unknown values remain explicitly unknown.
5. Atomically create the playthrough, its baseline selection, and a `playthrough_created` transaction event.
6. Load Dashboard, Holdings, and journal views from one shared playthrough context.

The selectors display localized names but persist `reference_snapshot_id`, `baseline_id`, and stable CK3 title IDs. Changing an upstream selector clears incompatible descendants. Unsupported dates, incomplete title chains, and titles marked non-selectable by validation must be rejected before commit.

### Bronze MVP: Barony Observation Editor
The first functioning editor milestone is a manual barony observation workflow:

1. Select an active county and realized barony.
2. Load the latest accepted observation as a preset.
3. Enter basic status values such as holding type, holder type, tax, levies, plague resistance, and notes.
4. Validate stable IDs, holding-specific fields, required values, and numeric ranges.
5. Commit one DuckDB transaction containing the event and barony observation.
6. Refresh Summary, Barony, County, and Duchy views from the new state.

The editor records a time-stamped observation; it does not attempt to synchronize every game tick or modify the savegame.

### Trial Holdings State Model
The trial Holdings view uses two explicit states to separate acquisition from ongoing observation:

- `New / Conquered`: starts from the canonical county and barony structure. Recording the acquisition persists one acquisition event and one base state row for every barony slot, including empty slots.
- `Update / Realm`: reads the observed county-wide and barony-level state for an existing county. Empty slots remain visible as open slots, while occupied baronies display their observed holder and daily values.

This is a visual proof model for the manual bridge between static CK3 reference data and lived run state. It is trial-scoped until the Bronze DuckDB observation workflow is complete.

### Holdings Navigation Model
`Holdings` is the summary surface for the current realm snapshot. Detailed updates are separated by ownership scope:

- `Barony`: holding-level values such as holder, tax, levies, fort level, buildings, and notes
- `County`: county-wide values such as control, development, popular opinion, culture, faith, and county holder
- `Duchy`: title progress, observed counties, base barony structure, and goal status

The editing workflow is a separate `Editor` scope. It first asks what is being edited (`Barony`, `County`, or `Duchy`), then presents only the fields and update mode appropriate to that scope.

Updates are event-point snapshots. The tracker records meaningful run changes rather than attempting to reproduce every game-day tick.

---

## 🧱 Schemas  
### Barony  
- `barony_id`  
- `barony_name`  
- `terrain`  
- `buildings`  

### County  
- `county_id`  
- `county_name`  
- `duchy_id`  
- `terrain`  
- `development`  

### Duchy  
- `duchy_id`  
- `duchy_name`  
- `capital_county_id`  
- `kingdom_name_867`
- `empire_name_867`
- `county_count_867`
- `barony_count_867`
- `average_development_867`
- `special_buildings`
- `start_date` (always `867`)
- `source_revision`

### Holding  
- `holding_id`  
- `barony_name`  
- `holding_type`  
- `county_id`  
- `duchy_id`  
- `terrain`  
- `buildings`  
- `levies`  
- `taxes`  
- `development`  
- `control`  
- `owned_by_character_id`  
- `owned_by_realm_id`  
- `acquired_at`  
- `acquisition_method`  

---

## 🏗 Provider Architecture  
### HoldingsProvider  
- `__init__(data_path, enable_cache=True)`  
- `_load_baseline()`  
- `_load_playthrough()`  
- `_join_holdings(baseline_df, play_df)`  
- `_to_schema_objects(df)`  
- `get_holdings(playthrough_id)`  

### CountiesProvider  
- `get_counties(playthrough_id)`  

### DuchiesProvider  
- `get_duchies(playthrough_id)`  

### CharacterProvider  
- `get_character(playthrough_id)`  

### DashboardService  
- `get_dashboard_metrics(playthrough_id)`  

---

## 🔗 Join Logic (HoldingsProvider)
The enriched holdings row must contain:

- structural fields (barony, county, duchy, terrain)  
- ownership fields  
- acquisition fields  
- numeric fields (levies, taxes, development, control)  
- lists (buildings, modifiers)  

Missing fields → filled with `None` or empty lists.  
Numeric fields → default to `0`.

---

## 🧪 Validation Rules  
### Baseline  
- required columns exist  
- correct types  
- no duplicate `holding_id`  
- no null `holding_id`  

### Playthrough  
- required columns exist  
- no null `playthrough_id`  
- no duplicate `(holding_id, playthrough_id)`  

### Post‑Join  
- holding_id required  
- playthrough_id required  
- structural fields filled  
- ownership fields filled  
- acquisition fields filled  
- lists normalized  
- numeric fields normalized  

---

## 🛡 Error Handling  
### File-Level  
- missing file → `FileNotFoundError`  
- corrupted file → `ValueError`  
- empty file → warn + continue  

### Column-Level  
- missing columns → `KeyError`  
- wrong types → coerce or warn  
- extra columns → ignore + log  

### Join-Level  
- missing baseline → warn + fill None  
- duplicate keys → warn + keep first  
- join failure → `RuntimeError`  

### Schema-Level  
- missing fields → skip row  
- invalid types → default + warn  
- object creation failure → skip row  

---

## ⚡ Caching Strategy  
### Baseline  
- cache once  
- invalidate only when baseline changes  

### Playthrough  
- cache per playthrough_id  

### Enriched Holdings  
- cache per playthrough_id  
- invalidate when baseline or playthrough changes  

---

## 📊 Dashboard Requirements  
The dashboard needs:

- `counties_owned`  
- `domain_limit`  
- `duchies_owned`  
- `domain_size`  
- `total_tax`  
- `total_levies`  
- `low_control_count`  
- `avg_development`  
- `terrain_distribution`  

### Goal-Driven Duchy Summary Table
The dashboard includes a goal-driven, county-derived duchy summary table. The user first selects a playthrough goal, such as forming the Kingdom of Sicily. The selected goal identifies the target title and automatically populates the duchies that contribute toward that title.

The table is a worklist for achieving the goal. It answers the practical question: how many counties are held in each target duchy, how many counties exist in that duchy, and how close is the player to satisfying the duchy title requirement?

| Column | Meaning |
| --- | --- |
| `Duchy` | Target duchy name, automatically populated from the selected goal title |
| `Have` | Counties currently held by the player in that duchy |
| `Count` | Total counties belonging to the duchy |
| `Title` | Current title-state or availability marker for the duchy |

The table includes a final target-title summary row with the total counties held, total counties in the selected goal scope, and the held percentage. The sample table is illustrative only; its duchies must change when the user selects a different goal. The `Title` marker is presentation data and must retain the source value until title-state codes are formalized.

Required derived fields:
- `goal_title_id`
- `goal_title_name`
- `target_duchy_ids`
- `duchy_name`
- `counties_held`
- `county_count`
- `title_state`
- `counties_held_percent` for the target-title summary row

### Goal Progress Bridge
The goal workflow connects static CK3 decision rules to the player's lived run:

1. Select a ruler decision such as Restore Old Vasconia or Restore Carthage.
2. Populate the decision's regions, target titles, and requirement groups.
3. Resolve duchies into canonical counties and baronies through CK3 title IDs.
4. Let the player manually record control, completion, exceptions, and notes.
5. Calculate current progress without changing the source decision definition.
6. Record target and decision completion dates in the living journal.

The implementation must preserve threshold logic such as "completely control at least four of the following duchies" rather than flattening it into an all-target requirement.

### Domain vs Realm Progress
Goal and duchy progress must distinguish two conditions:

- `domain`: directly held by the player character
- `realm`: held anywhere inside the player's realm, including vassal holdings

The app must retain separate counts and completion states for both. A manually entered `Have` value must identify whether it represents Domain or Realm progress; it must not silently combine the two.

### Trial Evidence Boundary
- Treat `base_baronies.parquet` as complete structural evidence for the trial map.
- Treat `holding_observations.parquet` and `county_observations.parquet` as screenshot-backed live observations only.
- Do not fill unseen daily values with guesses.
- Preserve CK3 source order separately from observed UI slot order.
- Use the acquisition bridge to create complete barony state rows when a county is acquired.
- Mark the trial `[VALIDATED]` only when its executable assertions pass.

Current Constantine UI slot mapping:
- slot 1: `b_constantine`, capital castle
- slot 2: `b_qasr-al-ifriqi`, city
- slot 3: `b_tijis`, open
- slot 4: `b_tifash`, temple
- slot 5: `b_taburshiq`, open

### Vassal Observation Follow-Up
The Kroumerie trial has complete BASE structure for eight baronies but only two live screenshot observations (`b_qasr-al-ifriqi` and `b_qalama`). Six remaining vassal barony screenshots are needed to complete the daily run-state values. The missing screenshots must not be fabricated from BASE data.

### County Capital Changes
- Treat the primary castle from the 867 title map as the original canonical capital; in the captured Scribe source this is the first barony listed in the county block when no explicit capital field exists.
- Allow a run-state capital change only when the game permits it, including two or more castles in the county.
- Preserve original and current capital barony IDs separately.
- Record lost capital bonuses and building slots as irreversible run-state effects.
- Do not restore a lost slot or bonus merely because the new capital becomes `b_capital`.

### County Breakdown Interpretation
- Use the faint divider to separate county-holder data from the barony/holding section.
- Count lower-section holding icons as baronies.
- Treat the silver crown as the county-capital marker.
- Treat the greyed realm-up-arrow as the move-realm-capital action.
- In the Mallorca proof slice, include Palma as Mayurqa's capital barony even when Alcudia is the selected city holding.

### Live Daily State
County and barony statistics are daily observations and may change on every game tick.

County-wide fields:
- `control`
- `development`
- `popular_opinion`
- `culture`
- `faith`

Barony/holding additive fields:
- `tax`
- `loot`
- `levies`
- `supply_limit`
- `plague_resistance`
- `garrison`
- `fort_level`
- `regular_building_slots`
- `duchy_building_slots`

Keep `fort_level` separate from `castle_level`. A duchy building slot with inward arrows, together with the duchy title icon in the county hierarchy, is evidence of a true de jure duchy relationship.

---

## 🔄 Dashboard Data Flow  
Dashboard → Providers → Aggregation → UI

### Providers Called:
- `holdings_provider.get_holdings()`  
- `counties_provider.get_counties()`  
- `duchies_provider.get_duchies()`  
- `character_provider.get_character()`  

### Aggregation:
`get_dashboard_metrics(playthrough_id)` returns a dictionary with all metrics.

### UI Binding:
Dashboard reads the dictionary and updates:

- text fields  
- charts  
- filters  

---

## 🧩 Implementation Steps (Checklist)

This checklist is historical and must not be used as a current resume sequence unless `Docs/current_build.md` explicitly activates a step.

### **Phase 0: Scaffolding & Setup** ✅ COMPLETE
- [x] Step 1 — Create project structure
- [x] Step 2 — Initialize Dash app
- [x] Step 3 — Register pages (dashboard, holdings)
- [x] Step 4 — Define schemas (holdings, dashboard)
- [x] Step 5 — Setup theme/styling
- [x] Step 6 — Git init & first commit
- [x] Step 7 — Add .gitignore
- [x] Step 8 — Add project_plan.md & architecture.md
- [x] Step 9 — Create changelog.md

### **Phase 0.5: Scaffolding Reorganization** ✅ COMPLETE
- [x] Step 9.5 — Create logic/ folder with all providers
- [x] Step 9.6 — Create all schema dataclass files
- [x] Step 9.7 — Update imports to match scaffolding
- [x] Step 9.8 — Verify dashboard runs successfully

### **Phase 1: Provider Implementation** — IN PROGRESS
- [~] Step 10 — Create Holding dataclass (visual/schema scaffold exists; provider and parquet integration remain)
- [~] Step 11 — Create County dataclass (county column mapping exists; dataclass and provider integration remain)
- [ ] Step 12 — Create Duchy dataclass
- [ ] Step 13 — Create Character dataclass
- [ ] Step 14 — Add validation utilities (check required columns, types)
- [ ] Step 15 — Add error handling utilities
- [ ] Step 16 — Add caching utilities
- [ ] Step 17 — Add logging setup
- [ ] Step 18 — Stub all provider classes
- [ ] Step 19 — Implement HoldingsProvider `__init__()`
- [ ] Step 20 — Implement HoldingsProvider `_load_baseline()`  
- [ ] Step 21 — Implement HoldingsProvider `_load_playthrough()`  
- [ ] Step 22 — Implement HoldingsProvider `_join_holdings()`  
- [ ] Step 23 — Implement HoldingsProvider `_to_schema_objects()`  
- [ ] Step 24 — Implement HoldingsProvider `get_holdings(playthrough_id)`  
- [ ] Step 25 — Implement CountiesProvider `get_counties()`
- [ ] Step 26 — Implement DuchiesProvider `get_duchies()`
- [ ] Step 27 — Implement CharacterProvider `get_character()`

### **Current Working State (Holdings First Build)**
- `[~]` Steps 10–11 are visually represented enough to support the current seeded dashboard/holdings experience, but neither is functionally complete against real parquet data.
- [x] Holdings provider seeded with realistic dummy rows so the UI renders and remains functional.
- [x] Holdings table is active and displays a working dark-theme grid.
- [x] Dead-run placeholder playthroughs are visible as explicit "dead" entries.
- [ ] New-run creation is deferred as an admin task until the holdings section is assembled.
- [ ] Real parquet-backed provider replacement is next once the UI shell is stable.

### **Refined Next Session Plan**
Historical proposal: a narrow decision-model pass could use Restore Carthage as the proving example if activated by `Docs/current_build.md`.

1. **Freeze the Scribe reference contract**
    - Record `1.19.0.6 (Scribe)` and `867` as required run metadata.
    - Keep `00_landed_titles.txt`, `80_major_decisions.txt`, and validated duchy metadata in the raw/reference layer.

2. **Define the parquet run backbone**
    - Establish `playthroughs`, `goals`, `goal_targets`, `holdings`, and event/history records.
    - Key all records by `playthrough_id`, CK3 title IDs, game version, and observation date.

3. **Build the Restore Carthage bridge**
    - Use `restore_carthage_decision` as the source goal.
    - Resolve its custom regions into the human-readable Area groups: `CN`, `M`, `T`, and `CAR`.
    - Populate the duchy worklist from the interpreted summary structure.
    - Preserve shortened display names while storing canonical CK3 IDs.

4. **Add separate Domain and Realm progress**
    - Track direct holdings separately from realm-wide control through vassals.
    - Keep `Have`, completion, and notes scope-aware.

5. **Add Realm/Succession state**
    - Capture primary title, realm size, heir, partition law, inherited titles, titles lost, and recipient sons.
    - Treat succession forecasts as current state and actual succession as a dated journal event.

6. **Add replay comparison after one run is stable**
    - Group attempts by the same goal.
    - Compare game version, survival length, milestones, failures, succession outcomes, and completion/death state.

Do not build the full goal catalog, barony import, or broad dashboard redesign until this vertical slice is validated visually and against the manual bridge.

The attached 867 dashboard workbook is the visual concept for the eventual player dashboard, not an import format or runtime dependency. Complete the normalized DuckDB reference item catalog first. When dashboard work resumes, translate its visual grouping and player questions into provider-backed components and remove all Excel sheet, table, range, formula, and cell-reference terminology from the implementation.

The read-only Reference Inspector may evolve during catalog construction because it exists to make candidate data visually reviewable. It must remain visibly marked as candidate tooling and must not bypass promotion gates for playthrough creation.

### **Phase 2: Dashboard Service**
- [ ] Step 28 — Complete the normalized reference item catalog and promotion report
- [ ] Step 29 — Implement DashboardService `get_dashboard_metrics()` from DuckDB-backed providers

### **Phase 3: Dashboard UI**
- [ ] Step 30 — Translate the workbook's visual concept into the dashboard page layout
- [ ] Step 31 — Bind dashboard components to service fields without spreadsheet references
- [ ] Step 32 — Add the first evidence-backed visualization
- [ ] Step 33 — Add filters and dropdowns
- [ ] Step 34 — Update the holdings page with provider-backed records
- [ ] Step 35 — Add counties and duchies views

### **Phase 4: Polish & Advanced Features**
- [ ] Step 36 — Add development trend chart
- [ ] Step 37 — Add levies/tax charts
- [ ] Step 38 — Add ruler tab
- [ ] Step 39 — Add realm composition visualization
- [ ] Step 40 — Style refinements & dark mode tweaks  

---

## 🚀 Future Features  
- Holdings tab  
- County detail view  
- Duchy summary  
- Realm composition  
- Council tab  
- Goals tab  
- Dynasty tab  
- Wars tab  
- Building slot visualization  
- Terrain heatmaps  
- Development trend charts  

---

## 📝 Notes  
This file is meant to be updated as you progress.  
Check off items.  
Add notes.  
Extend sections.  
Treat it like your project’s living blueprint.

---

This `.md` file is **ready to paste into VS Code and commit to GitHub**.  

---

## Project Scaffolding

ck3tracker/
│
├── app.py
├── requirements.txt
├── README.md
├── PROJECT_PLAN.md
│
├── data/
│   ├── holdings.parquet
│   ├── playthrough_holdings.parquet
│   ├── counties.parquet
│   ├── duchies.parquet
│   └── characters.parquet
│
├── logic/
│   ├── __init__.py
│   ├── holdings_provider.py
│   ├── counties_provider.py
│   ├── duchies_provider.py
│   ├── character_provider.py
│   └── dashboard_service.py
│
├── schemas/
│   ├── __init__.py
│   ├── barony_schema.py
│   ├── county_schema.py
│   ├── duchy_schema.py
│   └── holdings_schema.py
│
├── pages/
│   ├── __init__.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── page.py
│   ├── holdings/
│   │   ├── __init__.py
│   │   └── page.py
│   ├── counties/
│   │   ├── __init__.py
│   │   └── page.py
│   ├── duchies/
│   │   ├── __init__.py
│   │   └── page.py
│   └── ruler/
│       ├── __init__.py
│       └── page.py
│
└── docs/
    ├── architecture.md
    ├── providers.md
    ├── dashboard.md
    ├── data_flow.md
    ├── roadmap.md
    └── changelog.md
