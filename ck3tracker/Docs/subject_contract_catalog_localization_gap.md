# Subject-Contract Catalog Localization Gap

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Installed game: CK3 `1.19.0.6`, Steam build `23530548`
- Review date: 2026-09-02
- Intended parser: `installed_subject_contracts@1.0.0`
- Outcome: all gaps adjudicated; complete catalog ingested as `installed_subject_contracts@1.0.0`

## Complete Corpus Inventory

The installed `common/subject_contracts/contracts` corpus contains 15 UTF-8 text files, 64 unique top-level contract type blocks, and 194 direct obligation-level rows. Obligation IDs are unique within each type; 174 obligation IDs are globally unique because 20 IDs are intentionally reused under different types. The durable key therefore remains `(reference_snapshot_id, contract_type_id, obligation_id)`.

Every contract type has exactly one direct `obligation_levels` block and every direct child is a block. Source file order, type declaration order, and obligation declaration order provide deterministic zero-based indexes. There are no duplicate type IDs or duplicate obligation IDs within a type.

Two top-level scalar assignments in `special_contracts.txt`, `ai_standard_liege_desire` and `ai_standard_vassal_desire`, are shared script values rather than contract types. A future parser must recognize these exact non-type declarations or fail on changed top-level scalar shapes; it must not ingest them as contract rows.

Observed type fields are `obligation_levels`, `display_mode`, `is_shown`, `icon`, `defaults_to_highest_valid_level`, and `can_be_changed`. Obligation bodies contain broad gameplay and UI script, but catalog ingestion only needs to preserve each raw body and extract the direct `default` marker. `default` legitimately accepts both `yes` and `no`: 55 rows declare `yes`, three declare `no`, and the remainder omit it. Three types contain two `default = yes` rows, so source truth does not support a unique-default constraint.

## Localization Reconciliation

Exact English localization resolves with `valid` status for 58 of 64 type IDs and 182 of 194 obligation rows. The remaining 18 exact keys have no row in the loaded English localization catalog and no exact localization declaration anywhere in the installed game tree.

| Missing type ID | Source | Display mode | Missing obligation IDs | Installed consumers outside definition |
|---|---|---|---|---|
| `herder_government_obligations` | `common/subject_contracts/contracts/herder.txt:1-12` | implicit | none; sole level is globally localized `default` | referenced by `common/subject_contracts/groups/subject_contract_groups.txt` |
| `japan_administrative_salary` | `common/subject_contracts/contracts/japan_administrative.txt:217-299` | `tree` | none; five `salary_*` levels resolve | none found |
| `meritocratic_tribute_gold` | `common/subject_contracts/contracts/meritocratic.txt:506-571` | `tree` | `meritocratic_tributary_tax_none`, `meritocratic_tributary_tax_low`, `meritocratic_tributary_tax_normal`, `meritocratic_tributary_tax_high` | none found |
| `meritocratic_tribute_prestige` | `common/subject_contracts/contracts/meritocratic.txt:573-639` | `tree` | `meritocratic_prestige_transfer_none`, `meritocratic_prestige_transfer_low`, `meritocratic_prestige_transfer_normal`, `meritocratic_prestige_transfer_high` | none found |
| `iqta_special_rights` | `common/subject_contracts/contracts/special_contracts.txt:630-663` | `checkbox` | `iqta_special_rights_default`, `iqta_special_rights_granted` | none found |
| `ghazi_special_rights` | `common/subject_contracts/contracts/special_contracts.txt:665-704` | `checkbox` | `ghazi_special_rights_default`, `ghazi_special_rights_granted` | none found |

The 12 missing obligation IDs occur only in their definitions and same-type `parent` references. None of the 18 missing IDs occurs in loaded character history. No missing ID is used by O02, O33, or O64.

User-provided CK3 Wiki and immediate 867 in-game evidence confirms that “Iqta Grant” and “Ghazi Status,” including their displayed icons, are Tax Decrees selected for a Tax Jurisdiction. They are the active `iqta_special_rights_tax_collector` and `ghazi_special_rights_tax_collector` mechanics defined under `common/tax_slots/obligations`. They are not labels or icons for the separate `iqta_special_rights` and `ghazi_special_rights` subject-contract definitions.

The subject-contract copies have no contract-group membership, script consumer, or exact localization, while the tax-collector forms have definitions, type registration, localization, icons, and observed runtime UI. This supports classifying the six subject-contract keys (`iqta_special_rights`, `ghazi_special_rights`, and their four levels) as inactive superseded remnants in this build. Their raw definitions should remain in a complete catalog with null localization provenance; they must never inherit the active tax-decree labels or icons.

### Herder Runtime Boundary

A user-provided immediate 867 screenshot titled “Nomadic Tributary Contract” shows adjustable “Herd Tithes” and “Nomadic Prestige” rows plus “Suzerain Guarantee” and “Tributary War Support.” This screen matches the installed `tributary_steppe` group, whose four contracts are `default_tributary_taxes`, `nomad_government_prestige`, `suzerain_war_participation_guarantee`, and `tributary_war_participation_obligation`.

It does not expose `herder_government_obligations`. That type belongs only to the separate `herder_vassal` group and has one fixed `default` level with zero herd and tax values, so it cannot produce the five Herd Tithes choices visible in the screenshot. The screenshot therefore proves that “Herd Tithes” must not be assigned as the missing Herder type label.

Further user-provided immediate 867 evidence shows Herder rulers listed as tributary subjects with “Cease Tribute Chance,” while “Request Contract Change” on the player's suzerain opens the already-reviewed Nomadic Tributary Contract path. Its refusal tooltip reports only the proposed tributary trade balance and contract benefit; it is not a Herder-vassal obligation tooltip.

Installed engine-facing script completes the distinction. `herder_government` assigns `vassal_contract_group = herder_vassal`, so the fixed type is active structural data. Both ordinary vassal-contract editor entry points require `vassal_contract_has_modifiable_obligations = yes`; the Herder group cannot satisfy that requirement because its sole type has only one level. The suzerain-side tributary editor also explicitly excludes `government_is_herder`, while the subject-side tributary request remains available for the separate modifiable `tributary_steppe` group observed at runtime.

Classify `herder_government_obligations` as an active, fixed, engine-structural contract type that is intentionally unavailable in the editable contract interface. Preserve its raw definition, active group membership, and null type-label provenance. The installed broader UI key `herder_government_vassals_label = "Herder obligations cannot be adjusted"` documents the government-wide rule but is not an alias for the missing type ID.

### Japanese Administrative Salary

`japan_administrative_salary` defines five otherwise localized `salary_*` levels and declares `is_shown = { scope:subject.primary_title.tier >= tier_duchy }`, but the installed `japan_administrative_vassal` group contains only `japan_administrative_obligations` and `japan_administrative_provinces`. No installed group, script, or UI consumer adds the salary type.

User-provided immediate 867 runtime evidence shows the Japanese administrative hierarchy consists of Kuni governors directly beneath the empire, with no intermediate duchy-tier or higher Japanese administrative vassal class that could satisfy the salary definition's visibility gate. Group omission already makes the definition unreachable; the impossible society-specific tier condition independently confirms it is not a hidden live row. Classify the missing `japan_administrative_salary` type key as an inactive superseded remnant in this build. Preserve its raw definition and null type-label provenance without inventing “Salary” or borrowing another contract type's label; its five level labels retain their own exact localization provenance.

### Meritocratic Tribute Families

`meritocratic_tribute_gold` defines four tree levels at 0%, 5%, 10%, and 25% gold tribute. The levels range from +5 to -25 subject opinion and from +0.1 to +0.5 monthly legitimacy; `meritocratic_tributary_tax_low` is the sole declared default.

`meritocratic_tribute_prestige` mirrors the same four transfer rates, opinion values, and legitimacy modifiers for prestige. Its source is internally inconsistent because both `meritocratic_prestige_transfer_low` and `meritocratic_prestige_transfer_normal` declare `default = yes`.

One exact whole-game occurrence inventory finds each type ID only at its declaration and each level ID only at its declaration plus same-family `parent` link where applicable. None of the ten IDs has localization, group membership, UI usage, history usage, or another script consumer. Registered East Asian tributary groups instead use distinct `celestial_tribute_*` and related types.

There is no runtime route capable of instantiating either meritocratic family, so further in-game searching cannot discriminate their behavior. Classify both types and all eight levels as inactive superseded remnants in this build. Preserve their raw definitions, numeric mechanics, declaration order, duplicate prestige defaults, and null localization provenance; do not normalize the source defect or borrow labels from active celestial tribute contracts.

## Fail-Closed Decision

The current manifest requires separate English localization provenance for every loaded type and obligation and rejects unresolved required localization before replacement. The 18 exact gaps violate that contract. No evidence yet establishes whether these definitions are intentionally hidden, unreachable remnants, engine-labeled through an undocumented fallback, or source defects.

Accordingly:

- no `subject_contract_catalog_loader.py` is created;
- no `installed_subject_contracts` parser run or source manifest is written;
- no catalog, event, or baseline-state row is written;
- no backup is needed because no database mutation occurs;
- no alias, fallback text, synthetic label, partial catalog, or reviewed exception is invented;
- the 64 types and 194 obligation rows remain the complete ingestion denominator.

The O02/O33/O64 mappings remain independently supported because `administrative_themes`, `religious_rights`, `title_revocation_rights`, `special_contract`, and all referenced level IDs have exact valid English localization.

## Adjudication Complete

All 18 original localization gaps now have exact build-bound classifications. Six Iqta/Ghazi keys, one Japanese salary type, and ten meritocratic tribute keys are inactive superseded remnants. `herder_government_obligations` is active fixed engine-structural data hidden from editable contract paths. None receives an invented or borrowed label.

Catalog ingestion may preserve all 64 types and 194 obligation rows without narrowing the complete denominator. Reviewed non-localized rows must retain null localization/display provenance. Every exception must reject newly added localization, changed definitions, changed group membership, changed editor gates, new consumers, or newly reachable Japanese administrative title tiers. The meritocratic prestige double default is source truth and must not be normalized.

## Ingestion Outcome

Parser `installed_subject_contracts@1.0.0` transactionally loaded all 194 obligation rows across 64 types from 15 source files. Exactly 182 obligation rows retain valid exact English localization and 18 rows carry a reviewed non-localized classification because their type, obligation, or both lack labels. All 15 manifests bind the latest completed parser run `ck3_1_19_0_6_build_23530548:installed_subject_contracts:8c2cc990-38b7-4ce8-9355-05c8e28468af`.

Backup `ck3tracker_v2.before-subject-contract-catalog-1.0.0.20260902-150026.duckdb` precedes mutation and matches the source database at 822,358,016 bytes with SHA-256 `302513E9397F1AF206ACF719B4499AD1F9EE0D187BA0488676445B5E4D03ACD3`. Two production loads are idempotent, all 89 tests pass, and event/state tables remain empty. Character parser `1.9.0`, 82 opaque states, readiness, candidate status, and zero supported baselines remain unchanged.