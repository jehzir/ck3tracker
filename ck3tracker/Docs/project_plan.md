---

# 📘 CK3 Tracker — Project Blueprint  
*A clean, structured, GitHub‑ready plan for the CK3 Tracker Dash App.*

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
- Treat the current small seeded map as a synthetic UI-test profile only.
- Keep the seed profile separate from the full CK3 map; never combine their records.
- Resolve goals and duchy membership by stable IDs, never by familiar display names.
- Load one internally consistent map profile for a run before calculating dashboard progress.
- Import only de jure duchies; exclude all uncreatable duchies because they are exempt from the goal workflow.
- Permanently limit the application to 867 starts; do not add start-date switching or support for 1066/1178.
- Preserve CK3-defined title IDs exactly as the canonical keys.
- Preserve the source special-building list on duchy metadata records.

### Survival Journal Objective
The central question of the run is: how long can the realm survive from the 867 start before larger external powers overwhelm it? Features should support recording the realm's growth, goals, pressures, threats, and eventual survival or death across that timeline. Alternate start dates are outside the product scope.

---

## 📂 Data Sources

### Canonical Reference Sources
- `raw/ck3_867_00_landed_titles.txt` — installed CK3 title hierarchy and canonical title IDs
- `raw/duchies_source.html` — validated 867 de jure duchy metadata, counts, development summary, capitals, and special buildings
- `raw/barony_source.html` — candidate barony reference source; unverified until checked against `00_landed_titles.txt`
- CK3 `ruler_decisions` — goal definitions, requirements, required regions/titles, costs, and effects

Reference snapshot metadata:
- game version: `1.19.0.6 (Scribe)`
- start date: `867`
- title hierarchy source: installed CK3 game files
- wiki metadata source: CK3 Wiki pages captured for the matching game data

### Run-State Sources
- `holdings.parquet`
- `playthrough_holdings.parquet`
- `counties.parquet`
- `duchies.parquet`
- `characters.parquet`

Reference sources define what exists in CK3. Parquet is the durable application data layer for run state, persistence, and historical journal observations. Manual updates write into that run-state layer rather than replacing the reference sources.

### Parquet Backbone
All persistent application records should be normalized into parquet datasets keyed by `playthrough_id`, stable CK3 IDs, and observation/event dates where applicable. The parquet layer is the backbone for:
- run identity and lifecycle
- ruler history
- current and historical holdings
- county and duchy progress
- selected goals and requirement status
- manual control updates
- journal observations, milestones, threats, and completion events

Every persisted run must record the reference snapshot it was created against, including `game_version` and `start_date`. A Scribe run must not silently load reference data from another game version.

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
The next implementation pass should remain narrow and use Restore Carthage as the proving example.

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

### **Phase 2: Dashboard Service**
- [ ] Step 28 — Implement DashboardService `get_dashboard_metrics()`

### **Phase 3: Dashboard UI**
- [ ] Step 29 — Update dashboard page layout
- [ ] Step 30 — Bind metrics to dashboard cards
- [ ] Step 31 — Add first Plotly chart (terrain distribution)
- [ ] Step 32 — Add filters/dropdowns
- [ ] Step 33 — Update holdings page with data table
- [ ] Step 34 — Add counties tab
- [ ] Step 35 — Add duchies tab

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
