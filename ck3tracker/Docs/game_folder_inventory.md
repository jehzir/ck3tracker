# CK3 Game Folder Inventory

## Purpose

This inventory records the live CK3 install hierarchy so the application can read reference data from the correct game folders while remaining resilient to game patches, DLC installs, and future CK3 updates.

The design goal is to treat the game install as versioned implementation evidence for the CK3 Wiki reference catalog instead of assuming a single fixed folder layout.

## Core principle

- The Steam install root can move.
- The CK3 Wiki is the primary reference catalog and each extract needs page-revision provenance.
- The game root is the anchor for all game-data reads.
- The common folder is the primary patch-sensitive rule layer.
- DLC and major patches can add or modify folders without warning.
- The app should track what it reads, when it read it, and from which install snapshot.

## Inventory table

| Layer | Path | Purpose | Read as | Patch risk | Notes |
|---|---|---|---|---|---|
| Steam install root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III | Base game install root | install metadata | Low | Can move if Steam library is relocated |
| Game root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game | Core CK3 data root | reference source | Medium | This is the primary anchor for rule and title reads |
| Common root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common | Primary game definition layer | reference source | High | Highest-risk area for mass patches and DLC overlays |
| Laws | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\laws | Succession, government, and legal rules | reference source | High | Patch-sensitive; includes succession law logic |
| Titles | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\landed_titles | Title hierarchy and title identity data | reference source | High | Critical for structural and de jure validation |
| Culture | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\culture | Cultural implementation and rules | implementation evidence | High | Important for regional vs generic behavior |
| Religion | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\religion | Faith and doctrine implementation | implementation evidence | High | Needed for legal and cultural rule context |
| Buildings | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\buildings | Building definitions | reference source | Medium | Often changed with balancing updates |
| Decisions | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\decisions | Decision and event logic | reference source | Medium | Useful broader rule context |
| History | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\history | Historical seed data and setup | reference source | High | Can shift significantly with patches and DLCs |
| Localization | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\localization | UI and text keys | reference source | Medium | Useful for reading labels and names |
| DLC overlays | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\... | DLC-specific additions | reference source | High | Must be treated as layered additions, not fixed assumptions |
| Application database | C:\Users\rodne\ck3_app\ck3tracker\ck3tracker_v2.duckdb | Typed source, reference, journal, and app-view tables | DuckDB | Low | Primary destination for parsed source blobs and application queries |

## Recommended app behavior

Use `Docs/game_update_protocol.md` for baseline capture, post-update diffing, semantic reparse, validation, and snapshot promotion. The complete manifest should be generated; this document should not grow by manually appending every file from future patches.

1. Detect the active Steam library root dynamically.
2. Resolve the CK3 game root from the discovered install.
3. Read only from the files required for the active reference model.
4. Record the exact paths and timestamps used for each scan.
5. Insert extracted reference rows into versioned tables in the root DuckDB.
6. Treat the live game directory as external, read-only, build-specific, and patch-sensitive.
7. Flag mismatches when patch or DLC drift changes expected file layouts.

## Suggested metadata to store for each scan

- Game install root
- Game root
- CK3 version or build marker
- Scan timestamp
- File list read
- DLCs detected
- Patch-sensitive directories scanned
- Extracted reference tables generated
- Drift warnings if expected files were missing or renamed

## Why this reduces risk

This approach keeps the tracker resilient to mass patches because it separates:

- live game files
- versioned DuckDB reference snapshots
- mutable app-run state

The app never has to assume that one folder layout is permanent. Instead, it can adapt to new CK3 builds and DLC combinations without silently breaking the rules model.

## Decision summary

Yes: this is the right long-term structure.

The app should pair versioned wiki snapshots with scans of the live CK3 install hierarchy, then normalize only the subset it needs into a stable internal reference model. The wiki supplies the catalog and semantics; the files verify the installed implementation and make DLC/patch drift detectable.
