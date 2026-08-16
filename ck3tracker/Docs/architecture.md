# Architecture Overview

The CK3 Tracker is built on a provider-based architecture:

- Providers load and normalize data.
- DashboardService aggregates metrics.
- Dash pages render UI components.
- Plotly figures provide charts.

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

All metrics come from DashboardService.

# Data Flow

Dashboard → DashboardService → Providers → Parquet Files

DashboardService calls:
- get_holdings()
- get_counties()
- get_duchies()
- get_character()

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

