# CK3 Game Folder Inventory

## Purpose

This inventory records the live CK3 install hierarchy so the application can read reference data from the correct game folders while remaining resilient to game patches, DLC installs, and future CK3 updates.

The design goal is to treat the game install as a versioned external reference source instead of assuming a single fixed folder layout.

## Core principle

- The Steam install root can move.
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
| Cultures | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\cultures | Cultural definitions and rules | reference source | High | Important for regional vs generic behavior |
| Religions | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\religions | Faith and doctrine rules | reference source | High | Needed for legal and cultural rule context |
| Buildings | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\buildings | Building definitions | reference source | Medium | Often changed with balancing updates |
| Decisions | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\decisions | Decision and event logic | reference source | Medium | Useful broader rule context |
| History | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\history | Historical seed data and setup | reference source | High | Can shift significantly with patches and DLCs |
| Localization | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\localization | UI and text keys | reference source | Medium | Useful for reading labels and names |
| DLC overlays | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\... | DLC-specific additions | reference source | High | Must be treated as layered additions, not fixed assumptions |
| App cache / snapshot | Project-local reference tables | Normalized app snapshot | derived data | Low | Stores extracted or normalized versions for stable app use |

## Recommended app behavior

1. Detect the active Steam library root dynamically.
2. Resolve the CK3 game root from the discovered install.
3. Read only from the files required for the active reference model.
4. Record the exact paths and timestamps used for each scan.
5. Store a snapshot of the extracted reference data in the app’s own reference layer.
6. Treat the live game directory as external and patch-sensitive.
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
- extracted reference snapshots
- mutable app-run state

The app never has to assume that one folder layout is permanent. Instead, it can adapt to new CK3 builds and DLC combinations without silently breaking the rules model.

## Decision summary

Yes: this is the right long-term structure.

The app should continually scan and record the live CK3 install hierarchy, then normalize only the subset it needs into a stable internal reference model. That makes DLC and patch drift manageable instead of brittle.
