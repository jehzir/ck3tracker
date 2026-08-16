# Architecture Overview

The CK3 Tracker is built on a provider-based architecture:

- Providers load and normalize data.
- DashboardService aggregates metrics.
- Dash pages render UI components.
- Plotly figures provide charts.

This document describes the high-level structure and relationships between components.

## Current Status
The project is currently in a holdings-first stabilization phase. The holdings page is functional with realistic seeded data so the app remains usable while the parquet-backed implementation is still being finalized. The new-run creation flow is intentionally deferred as an admin task until the holdings section is fully assembled.

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

