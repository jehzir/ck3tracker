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

---

## 📂 Data Sources
- `holdings.parquet`
- `playthrough_holdings.parquet`
- `counties.parquet`
- `duchies.parquet`
- `characters.parquet`

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
- [x] Step 10 — Create Holding dataclass
- [ ] Step 11 — Create County dataclass
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
- [x] Holdings provider seeded with realistic dummy rows so the UI renders and remains functional.
- [x] Holdings table is active and displays a working dark-theme grid.
- [x] Dead-run placeholder playthroughs are visible as explicit "dead" entries.
- [ ] New-run creation is deferred as an admin task until the holdings section is assembled.
- [ ] Real parquet-backed provider replacement is next once the UI shell is stable.

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
