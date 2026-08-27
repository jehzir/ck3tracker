# CK3 Game Folder Map

## Purpose

This document groups the CK3 install into the sections that correspond to the app’s likely responsibility boundaries. It is intentionally organized by app layer rather than by a flat file listing so the structure can absorb future patch churn and DLC additions without forcing a large refactor.

## 1. Game Reference Intake

These are the live CK3 folders the app may read directly as external source material.

| App section | Path | Why it matters | Patch risk |
|---|---|---|---|
| Steam install root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III | Root of the installed game | Low |
| Game root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game | Anchor for all reference reads | Medium |
| Common root | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common | Primary source for game rules and definitions | High |
| Laws folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\laws | Succession, government, and legal rule logic | High |
| Titles folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\landed_titles | Title hierarchy and identity | High |
| Cultures folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\cultures | Cultural rules and regional logic | High |
| Religions folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\religions | Faith and doctrine rules | High |
| Buildings folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\buildings | Building definitions | Medium |
| Decisions folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\decisions | Decision and event logic | Medium |
| History folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\history | Seeded historical setup | High |
| Localization folder | C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\localization | Labels and text keys | Medium |

## 2. Reference Normalization

These are the normalized, app-owned versions of the raw game rules after extraction and cleanup.

| App section | Example content | Why it matters | Notes |
|---|---|---|---|
| Canonical title map | Parsed title IDs, parent-child links, ranks | Structural truth model | Should be versioned by CK3 build |
| Cultural and religious mapping | Culture/faith metadata with rule context | Regional and legal filters | Must be separate from observed state |
| Rule extraction layer | Law definitions, legal branch metadata | Logic used for truth grounding | Should be explicitly tagged with source file |
| DLC / patch snapshot layer | File list, build version, detected DLCs | Detect drift and compatibility | Should be tracked as a snapshot, not assumed static |

## 3. Run-State Observation Layer

These are the mutable app states captured from gameplay or screenshots, not from the base game data.

| App section | Example content | Why it matters | Notes |
|---|---|---|---|
| Manual observations | county/barony state entries | User-observed truth | Keeps time-stamped provenance |
| Lifecycle events | acquisition, reclaim, loss, resolution | Timeline of change | Must not overwrite historical rows |
| Transaction history | DuckDB transaction rows | Durable record of accepted changes | Separate from reference files |
| Current state views | latest accepted observations | Current app truth | Derived from the latest valid record |

## 4. Validation and Truth Layer

This layer compares reference truth against observed state and flags mismatches.

| App section | Example content | Why it matters | Notes |
|---|---|---|---|
| Structural validations | title relationships, holding validity, county/barony structure | Checks if a state is possible | This is where game-file truth helps |
| Rule compatibility checks | legal branch vs culture/regional logic | Prevents false assumptions | Important for patch-sensitive rules |
| Provenance checks | source tags and timestamps | Distinguishes manual vs imported vs reference | Needed for traceability |
| Drift warnings | missing files, changed paths, changed rules | Highlights patch / DLC drift | Should be surfaced before analysis continues |

## 5. Presentation Layer

These are the app’s user-facing views.

| App section | Example content | Why it matters | Notes |
|---|---|---|---|
| Dashboard | summaries and status | High-level overview | Depends on validated source data |
| Holdings views | barony and county state | User-focused interpretation | Should not be the source of truth |
| Ruler and dynasty views | character context | Narrative context | Must remain separate from reference truth |
| Historical recovery flows | rehydration and review | Audit or correction support | Should be distinct from live editing |

## Design note

The app should not treat the live CK3 folders as the same kind of thing as the user observations. The game directories are authoritative external input. The app’s internal data model should instead be layered like this:

- source game files
- normalized extracted reference tables
- observed run-state history
- derived validation and summaries
- presentation views

This split makes future patch work much safer because it isolates the parts most likely to change when Paradox ships a big update or DLC.

## Expected refactor direction

Once direct use of the game files becomes the stronger truth source, a fair amount of the current app structure will probably be refactored to reflect this progression:

- live game data ingestion becomes a first-class pipeline
- reference normalization becomes a formal stage
- UI and run-state layers remain downstream consumers
- patch/dlc drift detection becomes a built-in capability

This is the right direction for a resilient long-term tracker.
