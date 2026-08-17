# Changelog

## 2026-08-16
- Initial project scaffold created.
- Added PROJECT_PLAN.md.
- Added docs/ folder.
- Added dark-theme Dash app with page routing and dashboard card layout.
- Added playthrough selector and dead-run placeholder state.
- Added seeded holdings provider and active holdings table to keep the app functional.
- Deferred the real new-run creation flow as an admin task until the holdings section is complete.
- Documented the county-derived duchy summary table for the dashboard: counties held, total counties, title state, and kingdom-level percentage.
- Clarified that the duchy summary is goal-driven: selecting a target title such as Form Sicily automatically populates its constituent duchies and recalculates progress.
- Documented the core product model as a living run journal, from ruler birth through the player-declared dead-run state, with history preserved after completion.
- Marked provider steps 10 and 11 as partially complete: the visual/schema scaffolding exists, while real dataclass/provider/parquet integration remains unfinished.
- Documented the map-profile boundary: the CK3 title hierarchy is authoritative, while the small seeded map remains a separate synthetic UI-test profile.
- Excluded the source page's uncreatable duchies from canonical imports and goal calculations because they are exempt titles.
- Narrowed the first real-data scope to 867 starts, CK3-defined title IDs, and source-provided duchy special-building metadata.
- Made the 867 start permanent product scope: no alternate start dates or start-date switching; the journal measures long-run survival from 867.
- Revised the plan to distinguish canonical CK3 reference data, validated duchy metadata, decision-defined goals, run-state data, and manual playthrough updates as separate layers.
- Defined CK3 `1.19.0.6 (Scribe)` as the supported game-data contract and parquet as the persistent backbone for normalized run state and journal history.
- Added separate Domain and Realm progress scopes so direct ruler holdings are not confused with holdings controlled through vassals.
- Added the refined implementation sequence: Scribe-versioned parquet backbone, Restore Carthage bridge, Domain/Realm progress, Realm/Succession state, and replay comparison across attempts.
- Corrected the capital model: `b_capital` can change during a run when valid, while lost capital bonuses and building slots must persist as historical run-state effects.
- Clarified county-screen semantics: the silver crown marks the county capital, the greyed realm arrow moves the realm capital, and Palma is the missing Mayurqa capital barony in the Mallorca proof slice.
- Documented daily county-wide versus barony additive statistics, including garrison, fort level, regular slots, and the visual true de jure duchy-building slot indicator.
- Validated the Mallorca barony proof slice: four baronies across three counties, with Palma, Ibiza, and Menorca as county capitals and Alcudia as the additional city.
- Documented the trial evidence model: complete base structure, screenshot-backed live observations, derived Domain/Realm counts, and separate CK3 source order versus UI slot order.
- Documented the Constantine acquisition bridge and corrected UI slot mapping: Tijis slot 3, Tifash slot 4, Taburshiq slot 5.
- Recorded the Kroumerie observation boundary: eight BASE baronies, two observed vassal holdings, and six remaining screenshots required for complete live daily data.
