# CK3 Game Update Protocol

> **Authority:** This document governs snapshot refresh and promotion procedure only. It does not define the current implementation priority; use `Docs/current_build.md` for that.

## Purpose

Keep the CK3 Tracker reference model reproducible across game patches and DLC releases. The process pairs versioned CK3 Wiki pages with deterministic scans of the installed `game` tree, then reparses only the semantic source groups affected by a change.

The planned future update target is [By God Alone](https://ck3.paradoxwikis.com/By_God_Alone), a Core Expansion scheduled for September 30, 2026. It becomes active only when selected by `Docs/current_build.md`; its release patch number is not assumed in advance.

## Evidence Roles

- CK3 Wiki: primary reference catalog for mechanics, scope, terminology, and DLC features.
- Installed `game` tree: read-only evidence of the exact core and DLC implementation present in one Steam build.
- Root DuckDB: source manifests, wiki provenance, parser runs, immutable versioned reference tables, playthrough observations, and journal transactions in separate logical schemas.
- Parquet/CSV: optional exports, archives, interchange files, and test fixtures.

## Snapshot Identity

Every refresh must create a new `reference_snapshot_id` and retain:

- wiki page URL and permanent revision ID
- wiki retrieval timestamp and stated game version
- Steam app ID and build ID
- Clausewitz branch and revisions when available
- detected DLC metadata and descriptors
- normalized relative file paths, sizes, modification times, and content hashes
- scanner and parser versions
- supported baseline or bookmark dates and map profiles
- review status and drift warnings

Do not overwrite a prior snapshot or silently relabel it as a newer game version.

## Current Baseline

- Supported contract: CK3 `1.19.0.6 (Scribe)`
- Candidate baseline date: `867` (not selectable until explicit promotion)
- Steam app ID: `1158310`
- Observed Steam build ID: `23530548`
- Observed branch: `titus/release/1.19.0`
- Full installed-tree baseline: 48,350 files and 3,697 directories
- By God Alone prerelease wiki revision: `oldid=34782`
- DLC catalog wiki revision observed during planning: `oldid=34452`

These values describe the prerelease baseline only. The post-release scan must discover its own version and build identity.

## Update Workflow

### 1. Freeze The Prerelease Baseline

1. Capture the current wiki pages used by registered parsers through permanent revision links.
2. Generate a deterministic manifest for the complete installed `game` tree.
3. Record DLC metadata, package descriptors, package presence, Steam depot evidence, and launcher-enabled state as separate facts.
4. Run all registered semantic parsers and validation checks.
5. Insert normalized reference outputs into `ck3tracker_v2.duckdb` under the baseline snapshot ID.
6. Register only validated bookmark dates and complete title chains as selectable baselines.

### 2. Detect The Installed Update

After Steam installs the release:

1. Read build and branch evidence again; do not infer the new version from the calendar.
2. Generate a second full manifest without deleting the baseline.
3. Diff added, removed, changed, and moved paths by normalized path and content hash.
4. Recheck DLC metadata and descriptors for the new package ID, script code, priority, and mounted path.
5. Flag any changed registered loader group for semantic reparse.

### 3. Refresh Wiki References

1. Capture the current By God Alone, patch, DLC, and affected mechanics pages.
2. Store permanent revision IDs and retrieval timestamps.
3. Compare the prerelease feature catalog with released documentation.
4. Mark prerelease assumptions as confirmed, changed, deferred, or unsupported.
5. Never treat a timeless category label as proof that a page describes the installed build exactly.

### 4. Reparse Affected Domains

Reparse by loader group rather than filename token. Initial By God Alone candidates are:

- governments and playable theocracies
- religion, faith, doctrines, tenets, and holy sites
- situations and Great Schism progression
- landed and clerical title relationships, including archdioceses
- council, cardinal, and clerical appointment systems
- holy orders and headquarters
- character traits, modifiers, and spiritual fulfillment
- buildings and cathedrals
- decisions, interactions, triggers, effects, and events
- localization for all retained reference labels

This list is a prerelease impact hypothesis. The manifest diff and released wiki revisions decide the actual parser set.

### 5. Validate Before Promotion

A new snapshot may become supported only when:

- build identity and wiki provenance are complete
- all changed registered loader groups were reparsed
- stable IDs remain unique within their entity type
- title containment still follows `Barony -> County -> Duchy -> Kingdom -> Empire`
- every candidate baseline profile loads as one internally consistent hierarchy
- every selectable location resolves a complete stable-ID parent chain for its baseline
- bookmark, title-history, character-history, and localization inputs agree on supported starting facts or retain explicit unknowns
- deleted or renamed IDs produce explicit migration findings
- DLC-gated records retain their availability conditions
- Bronze observations remain unchanged and readable
- cross-snapshot comparison reports all known semantic drift

If validation fails, retain the new snapshot as `review_required` and continue using the last supported snapshot.

Promotion changes which `reference_snapshot_id` and baseline dates new runs may use. It does not rewrite normalized rows, mutate existing runs, or replace the DuckDB file.

## Diff Outputs

Each update comparison should produce:

- filesystem additions, removals, and content changes
- wiki revision changes by registered page
- DLC catalog and descriptor changes
- parser groups requiring rerun
- canonical records added, removed, or changed
- stable IDs renamed or no longer resolved
- validation failures and migration requirements
- an explicit promotion decision

## By God Alone Release Gate

The September 30 update is complete only when the tracker can answer:

1. Which wiki reference concepts changed between the prerelease and released revisions?
2. Which installed files and loader groups changed with the Steam update?
3. Which changes belong to the free patch, the By God Alone DLC, or shared implementation?
4. Which canonical reference tables changed semantically?
5. Can existing Scribe runs remain pinned to their original snapshot without mutation?
6. Can a new 867 run select the released snapshot only after validation?

The update process must be rerunnable for later patches without adding release-specific branches to the core journal model.