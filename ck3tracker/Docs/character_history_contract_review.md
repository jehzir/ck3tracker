# Character-History Vassal-Contract Review

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Installed game: CK3 `1.19.0.6`, Steam build `23530548`
- Review date: 2026-09-02
- Scope: opaque character-history shapes O02, O33, and O64 only
- Outcome: durable contract defined; schema and replay remain unimplemented

## Decision

`vassal_contract_set_obligation_level` writes one obligation level on the current character's subject contract. The durable owner is the subject character and, when deterministically resolvable, that subject's effective liege character. A title can prove the relationship and contract applicability, but is not the identity of the contract.

The numeric `level` is an ordered index into the named contract type's installed `obligation_levels`; durable state must store the resolved stable obligation ID as well as the source numeric index. Different obligation types coexist. A later executable write for the same subject and obligation type replaces the materialized scalar value, while every write remains an append-only event.

Eleven baseline-effective writes are executable: ten O02 administrative-theme writes and O64's March write. O33 contains two syntactically valid writes, but its `has_mpo_dlc_trigger = no` branch is false for this snapshot and therefore emits no contract event or state.

## Declaration Ledger

Paths are relative to `history/characters/`. Declaration order is the preserved global source order.

| Shape | Subject | Effective date | Declaration | Source | Branch | Resolved write | Liege evidence |
|---|---|---|---:|---|---|---|---|
| O02 | `145116` | `0867-01-01` | `202775` | `greek.txt:16760-16770` | active | `administrative_themes[2] -> admin_theme_military` | `d_nf_lachanodrakon -> e_byzantium -> 1700` |
| O02 | `145123` | `0867-01-01` | `202818` | `greek.txt:16871-16881` | active | `administrative_themes[3] -> admin_theme_frontier` | `d_chaldia -> e_byzantium -> 1700` |
| O02 | `145137` | `0867-01-01` | `202922` | `greek.txt:17092-17102` | active | `administrative_themes[2] -> admin_theme_military` | `d_anatolia -> e_byzantium -> 1700` |
| O02 | `145144` | `0867-01-01` | `202974` | `greek.txt:17205-17215` | active | `administrative_themes[2] -> admin_theme_military` | `d_charsianon -> e_byzantium -> 1700` |
| O02 | `145185` | `0867-01-01` | `203293` | `greek.txt:17838-17848` | active | `administrative_themes[3] -> admin_theme_frontier` | `d_nf_aplakes -> e_byzantium -> 1700` |
| O02 | `145194` | `0867-01-01` | `203350` | `greek.txt:17972-17982` | active | `administrative_themes[5] -> admin_theme_naval` | `d_ephese -> e_byzantium -> 1700` |
| O02 | `145196` | `0867-01-01` | `203363` | `greek.txt:18011-18021` | active | `administrative_themes[5] -> admin_theme_naval` | `d_cibyrrhaeot -> e_byzantium -> 1700` |
| O02 | `145931` | `0867-01-01` | `204749` | `greek.txt:21299-21309` | active | `administrative_themes[5] -> admin_theme_naval` | `d_aegean_islands -> e_byzantium -> 1700` |
| O02 | `302342` | `0867-01-01` | `204867` | `greek.txt:21562-21572` | active | `administrative_themes[2] -> admin_theme_military` | `d_cappadocia -> e_byzantium -> 1700` |
| O02 | `302355` | `0867-01-01` | `204968` | `greek.txt:21776-21786` | active | `administrative_themes[3] -> admin_theme_frontier` | `d_nf_kardias -> e_byzantium -> 1700` |
| O33 | `3022740` | `0845-01-02` | `408467` | `khazar.txt:1046-1058` | inactive | no event; enclosed `religious_rights[1]` and `title_revocation_rights[1]` do not execute | `c_tmutarakan -> d_azov`; no baseline liege holder, immaterial to inactive branch |
| O64 | `168137` | `0865-01-01` | `476349` | `occitan.txt:12973-12981` | active | `special_contract[2] -> special_contract_march` | `d_barcelona -> k_aquitaine -> 90104` |

No subject has more than one contract-writing declaration anywhere in the installed character-history timeline. Supersession is consequently part of the durable API contract, but is not exercised by these source rows.

## Exact Grammar And Branches

O02 has exactly one conditional child in each body:

```text
if = {
    limit = { government_allows = administrative }
    vassal_contract_set_obligation_level = {
        type = administrative_themes
        level = <2|3|5>
    }
}
```

All ten subjects are alive at the baseline and hold an administrative duchy directly under `e_byzantium`; the branch is active. `administrative_themes.is_shown` independently requires the subject's primary title to be at least duchy tier. Family-title IDs remain valid relationship evidence and must not be discarded merely because they are not geographic selection titles.

O33 is one conditional body with two ordered writes:

```text
if = {
    limit = { has_mpo_dlc_trigger = no }
    vassal_contract_set_obligation_level = {
        type = religious_rights
        level = 1
    }
    vassal_contract_set_obligation_level = {
        type = title_revocation_rights
        level = 1
    }
}
```

Installed `common/scripted_triggers/00_has_dlc_scripted_triggers.txt` maps `has_mpo_dlc_trigger` to feature `khans_of_the_steppe`. Reviewed snapshot mapping `khans_of_the_steppe -> dlc020_ce2` and the valid installed “Khans of the Steppe” descriptor make the negated condition false. This is an audited inactive branch, not an event with an absent value.

O64 has two ordered top-level children:

```text
vassal_contract_set_obligation_level = {
    type = special_contract
    level = 2
}
set_relation_friend = {
    reason = friend_generic_history
    target = character:127007
}
```

The contract write is unconditional. The friendship child is already supported by parser `1.9.0`; once contract projection exists, both direct children are understood and the complete declaration can normalize without broadening relationship grammar.

## Installed Contract Mapping

Installed definitions use `scope:subject` and `scope:liege`, confirming character-to-character contract context. Read-side script queries the singular scalar `vassal_contract_obligation_level:<type>`. The reviewed numeric order and English labels are:

| Type ID | Type label | Level | Obligation ID | Obligation label | Definition evidence |
|---|---|---:|---|---|---|
| `administrative_themes` | Available Administration Types | 0 | `admin_theme_balanced` | Balanced Administration | `common/subject_contracts/contracts/administrative.txt:26` |
| `administrative_themes` | Available Administration Types | 1 | `admin_theme_civilian` | Civilian Administration | `common/subject_contracts/contracts/administrative.txt:54` |
| `administrative_themes` | Available Administration Types | 2 | `admin_theme_military` | Military Administration | `common/subject_contracts/contracts/administrative.txt:107` |
| `administrative_themes` | Available Administration Types | 3 | `admin_theme_frontier` | Frontier Administration | `common/subject_contracts/contracts/administrative.txt:160` |
| `administrative_themes` | Available Administration Types | 4 | `admin_theme_imperial` | Imperial Administration | `common/subject_contracts/contracts/administrative.txt:216` |
| `administrative_themes` | Available Administration Types | 5 | `admin_theme_naval` | Naval Administration | `common/subject_contracts/contracts/administrative.txt:294` |
| `religious_rights` | Religious Rights | 0 | `religious_rights_none` | default/no protected rights | `common/subject_contracts/contracts/special_contracts.txt:325` |
| `religious_rights` | Religious Rights | 1 | `religious_rights_protected` | Religiously Protected | `common/subject_contracts/contracts/special_contracts.txt:332` |
| `title_revocation_rights` | Title Revocation | 0 | `title_revocation_rights_default` | default revocation | `common/subject_contracts/contracts/special_contracts.txt:535` |
| `title_revocation_rights` | Title Revocation | 1 | `title_revocation_rights_protected` | Protected Title Revocation | `common/subject_contracts/contracts/special_contracts.txt:542` |
| `special_contract` | Special Contract | 0 | `special_contract_none` | No Special Contract | `common/subject_contracts/contracts/special_contracts.txt:11` |
| `special_contract` | Special Contract | 1 | `special_contract_scutage` | Scutage Contract | `common/subject_contracts/contracts/special_contracts.txt:89` |
| `special_contract` | Special Contract | 2 | `special_contract_march` | March Contract | `common/subject_contracts/contracts/special_contracts.txt:140` |
| `special_contract` | Special Contract | 3 | `special_contract_castellan` | Castellan Contract | `common/subject_contracts/contracts/special_contracts.txt:201` |
| `special_contract` | Special Contract | 4 | `special_contract_palatinate` | Palatinate Contract | `common/subject_contracts/contracts/special_contracts.txt:250` |

The stable obligation ID is authoritative after resolution. A future source reorder must not silently reinterpret a historical numeric level; ingestion must bind the index and ID from the same snapshot catalog or fail.

## Durable Storage Contract

The minimum model has three layers:

1. A snapshot-scoped contract catalog preserves contract type ID, obligation ID, numeric level index, order, default status where declared, labels/localization provenance, raw definition, definition source path/range, and source-manifest identity. Identity is `(reference_snapshot_id, contract_type_id, obligation_id)`, with a unique `(reference_snapshot_id, contract_type_id, level_index)` mapping.
2. Append-only subject-contract events preserve snapshot, subject character ID, optional resolved liege character ID, source group, declaration order, operation order, effective game date, contract type ID, obligation ID, source level index, branch status/evidence, and exact source coordinates. Event identity includes declaration and operation order so O33's two writes could coexist if its branch were active.
3. Sparse baseline subject-contract state stores one active row per `(baseline_id, subject_character_id, contract_type_id)`, the resolved obligation ID/index, optional liege character ID, effective date, and exact winning event provenance. Defaults are not synthesized into sparse state.

Catalog, event, and state rows must use enforceable same-snapshot/baseline foreign keys. Liege is denormalized evidence on the event/state, not part of scalar obligation identity; a later liege change does not rewrite historical events.

For each executable write, chronology is `(effective_date, declaration_order, operation_order)`. Later writes for the same subject and type replace state. Writes to different types coexist. Equal-date source order is retained rather than collapsed. Inactive branches produce no contract event or state; their source declaration and branch audit remain in existing raw history evidence.

## Parser Boundary

A future parser may recognize only:

- O02's exact single `if` body, exact `government_allows = administrative` limit, and one exact two-field contract write in `type, level` order;
- O33's exact single `if` body, exact `has_mpo_dlc_trigger = no` limit, and two exact ordered contract writes shown above;
- O64's exact ordered contract write plus already-supported exact friendship child;
- direct contract writes only when the same exact two-field grammar and execution scope are independently proven.

It must not recurse into arbitrary nested effects, generalize other conditions, reorder children, accept unknown fields, treat numeric levels as stable IDs, infer defaults, or infer a title-owned contract. Every referenced type/index/obligation, subject, applicable branch dependency, and active relationship must resolve before candidate replacement.

If a branch is active but no valid subject contract or deterministic liege can be proven at that event's effective date, retain the raw declaration as unresolved and emit no materialized state. Do not use a baseline liege for an earlier event without chronology-valid relationship evidence. An inactive branch requires package/trigger evidence but does not require a hypothetical contract target.

## Evidence Limits

No local `script_docs` `effects.log` or `triggers.log` exists. The CK3 Wiki documents that code effects have predetermined syntax and scope and that `if` children execute only when their `limit` is true, but its public effect page does not expose this effect's generated engine description. Installed definitions, call sites, scalar read-side syntax, and baseline relationship state support the owner and replacement contract above; exact engine behavior for calling the effect without a valid subject contract remains unproven and is deliberately fail-closed.

This review does not claim that `is_shown` or `is_valid` UI rules are the engine write effect's runtime preconditions. They are applicability evidence only. It also does not project O33's inactive values, infer Benjamin's absent liege, or certify contract families outside O02/O33/O64.

## Implementation And Rollback Requirements

Schema bootstrap, catalog ingestion, and character replay are separate actions. Before any candidate database mutation, create and verify a root DuckDB backup. Each loader must reject promoted or unknown snapshots, validate all source and catalog dependencies before destructive replacement, replace only its own source-group rows in one transaction, preserve other snapshots/baselines/source groups, and leave prior rows and parser-run evidence unchanged on failure.

The evidence-only review changes no schema, parser, database row, readiness report, warning count, candidate status, historical-completeness flag, or supported baseline.