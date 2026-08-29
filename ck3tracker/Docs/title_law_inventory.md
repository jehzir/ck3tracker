# Title Succession-Law Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.3.0`

## Baseline Evidence

The 867 cutoff contains 446 `succession_laws` replacement declarations across 431 titles and 12 ordered declaration shapes. Every declaration remains queryable in `source.title_history_declarations` with its effective date, raw block, source path, line range, and global declaration order. The corresponding `succession_laws_replaced` event records the ordered law IDs, including an empty value for an explicit clear.

The 11 IDs present by the 867 cutoff are:

- `acclamation_succession_law`
- `celestial_grand_marshal_appointment_succession_law`
- `celestial_ministry_appointment_succession_law`
- `feudal_elective_succession_law`
- `gaelic_elective_succession_law`
- `landless_adventurer_succession_law`
- `male_only_law`
- `noble_family_succession_law`
- `princely_elective_succession_law`
- `saxon_elective_succession_law`
- `temporal_head_of_faith_succession_law`

## Definition Binding

The complete installed title-history corpus references 14 law IDs. All 14 resolve uniquely to definitions in `common/laws/00_succession_laws.txt` or `common/laws/01_title_succession_laws.txt`; their raw definition blocks, hashes, groups, line ranges, and source order are stored in `reference.law_definitions`. The three IDs used only after the 867 cutoff are `equal_law`, `male_preference_law`, and `scandinavian_elective_succession_law`.

The baseline materialization contains 431 active law rows across 430 titles and 10 distinct law IDs in `reference.title_baseline_laws`. All active IDs resolve to the snapshot-scoped definition catalog. `k_asturias` has no active explicit law because its 843 empty block replaces and clears its 718 elective-law block.

## Replay Contract

- A syntactically valid `succession_laws` block replaces the title's prior explicit law set at its effective date and declaration order.
- An empty block is a valid replacement with an empty set.
- Ordered IDs are preserved; duplicate, malformed, or unresolved IDs are not normalized.
- Law replay changes no holder, liege, government, development, capital, or hierarchy field.
- Snapshot and baseline remain `candidate`, `historical_state_complete` remains false, and `app.supported_baselines` remains empty.

After this normalization, the opaque-title readiness finding is 178 states, down from 556. The immutable report is `ck3_1_19_0_6_867:readiness:e799523e-a95c-4c5d-a3e8-79172e9ccb0c`.