# Title History Opaque Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Starting scope: 556 baseline title states with `not evaluated:` warnings
- Current scope: zero baseline title states.
- Intermediate counts below are retained as parser-milestone audit history; the current count is 0 at parser `1.22.0` after exact Balhae court-language replay.
- Raw declarations remain preserved in `source.title_history_declarations`.
- Counts overlap when one title contains more than one opaque shape.

## Inventory

| Shape | Titles | Rows | Source paths (rows) |
|---|---:|---:|---|
| `succession_laws` | 431 | 446 | `history/titles/00_other_titles.txt` (11); `history/titles/01_admin_titles.txt` (20); `history/titles/01_admin_titles_tgp.txt` (257); `history/titles/01_laamp_titles.txt` (21); `history/titles/02_japan_noble_family.txt` (59); `history/titles/02_korea_noble_family.txt` (43); `history/titles/02_other_noble_family.txt` (18); `history/titles/e_china.txt` (9); `history/titles/k_aquitaine.txt` (1); `history/titles/k_england.txt` (4); `history/titles/k_france.txt` (1); `history/titles/k_ireland.txt` (1); `history/titles/k_scotland.txt` (1) |
| `effect: {destroy_landless_title_no_tgp_dlc_effect}` | 371 | 385 | `history/titles/01_admin_titles_tgp.txt` (257); `history/titles/02_japan_noble_family.txt` (59); `history/titles/02_korea_noble_family.txt` (42); `history/titles/02_other_noble_family.txt` (18); `history/titles/e_china.txt` (9) |
| `effect: {if}` | 73 | 74 | `history/titles/e_goryeo.txt` (1); `history/titles/e_japan.txt` (1); `history/titles/e_seasia.txt` (1); `history/titles/k_anatolia.txt` (9); `history/titles/k_balhae.txt` (1); `history/titles/k_bengal.txt` (1); `history/titles/k_bulgaria.txt` (8); `history/titles/k_cyprus.txt` (2); `history/titles/k_epirus.txt` (7); `history/titles/k_hellas.txt` (7); `history/titles/k_italy.txt` (1); `history/titles/k_lotharingia.txt` (1); `history/titles/k_nikaea.txt` (8); `history/titles/k_pontic_steppe.txt` (1); `history/titles/k_pontus.txt` (7); `history/titles/k_sicily.txt` (3); `history/titles/k_sindh.txt` (1); `history/titles/k_syria.txt` (1); `history/titles/k_thessalonika.txt` (12); `history/titles/k_transoxiana.txt` (1) |
| `tributary_of` | 23 | 23 | `history/titles/e_khmer.txt` (6); `history/titles/k_dvaravati.txt` (4); `history/titles/k_kamarupa.txt` (1); `history/titles/k_pagan.txt` (12) |
| `de_jure_liege` | 21 | 30 | `history/titles/k_aquitaine.txt` (2); `history/titles/k_aragon.txt` (3); `history/titles/k_bavaria.txt` (1); `history/titles/k_bohemia.txt` (2); `history/titles/k_denmark.txt` (2); `history/titles/k_east_francia.txt` (7); `history/titles/k_england.txt` (1); `history/titles/k_frisia.txt` (2); `history/titles/k_hungary.txt` (2); `history/titles/k_leon.txt` (2); `history/titles/k_lotharingia.txt` (3); `history/titles/k_spanish_galicia.txt` (2); `history/titles/k_valencia.txt` (1) |
| `effect: {destroy_landless_title_no_dlc_effect}` | 21 | 21 | `history/titles/01_admin_titles.txt` (20); `history/titles/01_laamp_titles.txt` (1) |
| `effect: {create_landless_adventurer_title_history_effect, set_variable, destroy_landless_title_no_dlc_effect}` | 20 | 20 | `history/titles/01_laamp_titles.txt` (20) |
| `effect: {tgp_set_minamoto_taira_dynasty_prestige_effect}` | 6 | 6 | `history/titles/02_japan_noble_family.txt` (6); normalized by parser `1.12.0` |
| `name` | 6 | 7 | `history/titles/e_seasia.txt` (1); `history/titles/k_east_francia.txt` (1); `history/titles/k_france.txt` (3); `history/titles/k_hungary.txt` (1); `history/titles/k_lotharingia.txt` (1) |
| `holder_ignore_head_of_faith_requirement` | 5 | 43 | `history/titles/00_other_titles.txt` (43) |
| `effect: {set_de_jure_liege_title}` | 2 | 2 | `history/titles/k_caspian_steppe.txt` (1); `history/titles/k_khakassia.txt` (1); normalized by parser `1.11.0` |
| `effect: {add_title_law, destroy_landless_title_no_tgp_dlc_effect}` | 1 | 1 | `history/titles/e_japan.txt` (1) |
| `effect: {create_landless_adventurer_title_history_effect, set_variable}` | 1 | 1 | `history/titles/01_laamp_titles.txt` (1); normalized by parser `1.15.0` |
| `effect: {if, if, if}` | 1 | 1 | `history/titles/00_other_titles.txt` (1) |
| `effect: {if, if}` | 1 | 1 | `history/titles/e_japan.txt` (1) |
| `effect: {set_title_name}` | 1 | 1 | `history/titles/k_aragon.txt` (1); normalized by parser `1.13.0` |
| `effect: {set_variable}` | 1 | 1 | `history/titles/e_japan.txt` (1); normalized by parser `1.16.0` |
| `effect: {while}` | 1 | 1 | `history/titles/02_japan_noble_family.txt` (1); normalized by parser `1.14.0` |
| `reset_name` | 1 | 1 | `history/titles/k_east_francia.txt` (1) |

## Selected Family

`effect: {destroy_landless_title_no_tgp_dlc_effect}` is the only family normalized in this slice.

Installed evidence:

- `common/scripted_effects/10_dlc_tgp_scripted_effects.txt` defines destruction only when `NOT = { has_dlc_feature = all_under_heaven }` and `game_start_date = $DATE$`.
- `common/scripted_triggers/00_has_dlc_scripted_triggers.txt` defines `has_tgp_dlc_trigger` as `has_dlc_feature = all_under_heaven`.
- Reviewed feature mapping `all_under_heaven -> dlc022_ep4` resolves to the validated installed package descriptor for All Under Heaven.

Parser `1.2.0` accepts only a one-field invocation whose `DATE` equals the declaration date and only when both installed definitions match the reviewed script exactly. It records a `dlc_gated_noop` event and retains the raw declaration. Missing package evidence, changed definitions, mixed effects, or mismatched dates remain opaque.

At the 867 baseline this normalizes 385 invocations across 371 titles. It clears zero complete title warnings because every affected title also has `succession_laws`; six also have `tgp_set_minamoto_taira_dynasty_prestige_effect`, and one has `while`. The readiness count therefore remains 556 until another independently grounded family is reviewed.

## Succession-Law Normalization

Parser `1.3.0` models `succession_laws` as ordered replacement state, including meaningful empty clears, and binds every referenced ID to its installed definition. The complete evidence and replay contract are recorded in `Docs/title_law_inventory.md`.

This normalizes all 446 baseline-effective declarations across 431 titles. The materialized baseline has 431 active law rows across 430 titles, with no unresolved law IDs. The opaque-title readiness count falls from 556 to 178; the remaining warnings are 124 effect states, 23 `tributary_of` states, 21 states involving `de_jure_liege`, five `holder_ignore_head_of_faith_requirement` states, six states involving `name`, and one `reset_name` state, with overlaps between categories.

## De Jure Liege Normalization

Parser `1.4.0` models all 30 baseline-effective `de_jure_liege` declarations across 21 titles as dated replacement state in a separate table. Every nonzero target resolves in the same baseline; complete installed history also proves scalar `0` as an explicit clear. Static landed-title parentage remains unchanged. The full evidence and replay contract are recorded in `Docs/title_de_jure_inventory.md`.

This reduces the opaque-title readiness count from 178 to 160. Eighteen title warnings clear completely, while three affected titles retain other unsupported operations.

## Tributary Normalization

Parser `1.5.0` models all 23 baseline-effective `tributary_of` blocks as dated replacement relationships in a separate table. Each block contains exactly one resolved `suzerain` title and the installed `tributary_mandala` contract group, whose definition explicitly declares `is_tributary = yes`. The full inventory and replay contract are recorded in `Docs/title_tributary_inventory.md`.

This reduces the opaque-title readiness count from 160 to 137. Liege and de-jure state remain unchanged.

## Roads To Power No-Op Normalization

Parser `1.6.0` recognizes only an effect body containing the single `destroy_landless_title_no_dlc_effect` invocation with exactly one `DATE` argument matching its enclosing declaration date. The installed helper in `common/scripted_effects/07_dlc_ep3_scripted_effects.txt` destroys the title only when `roads_to_power` is absent and the game start date matches. Reviewed mapping `roads_to_power -> dlc014_ep3` resolves to the validated installed Roads to Power package, making these exact invocations no-ops for this snapshot.

All 21 baseline-effective exact invocations normalize and remain preserved as raw declarations. Twenty title warnings clear; `d_laamp_henry_of_skalitz` retains a separate unsupported effect. Mixed adventurer-creation bodies remain opaque. The full evidence is recorded in `Docs/title_ep3_noop_inventory.md`.

## Historical Adventurer Initialization

Parser `1.7.0` recognizes only the exact three-field body containing `create_landless_adventurer_title_history_effect = yes`, `adventurer_creation_reason = flag:historical`, and a date-matched Roads to Power destruction helper. It additionally requires an effective holder and the already-declared `landless_adventurer_succession_law`, making the helper's conditional law addition idempotent.

All 20 baseline-effective bodies normalize into three provenance-linked events and 20 durable title-variable rows. Raw declarations remain preserved. The opaque-title count falls from 117 to 97. Full evidence is recorded in `Docs/title_adventurer_effect_inventory.md`.

## Conditional-Effect Review

Parser `1.8.0` inventories all 74 baseline-effective opaque bodies whose sole top-level effect field is `if`. It normalizes only the 64 exact no-Roads-to-Power government fallback bodies across 63 titles. The reviewed installed `roads_to_power -> dlc014_ep3` mapping makes their negative DLC condition false, so each complete body is a deterministic no-op.

At parser `1.8.0`, ten Royal Court language/type bodies remained opaque because no durable court-state projection existed, and five included a runtime-dependent nested language-learning condition. Mixed `e_japan` and `e_byzantium` bodies were outside this single-`if` family and opaque as a whole. The opaque-title count then fell from 97 to 34. Parser `1.17.0` supersedes this court-state limitation; the exhaustive declaration ledger is recorded in `Docs/title_conditional_effect_inventory.md`.

## Head-of-Faith Holder Override Replay

Parser `1.9.0` replays all 43 baseline-effective `holder_ignore_head_of_faith_requirement` declarations across five titles as holder assignments with an explicit assignment-time eligibility bypass. Nonzero values replace holder identity; `0` clears it. Later ordinary holder operations replace the bypass assignment normally, and a distinct holder status preserves how an effective bypass holder was assigned.

All 39 distinct nonzero character IDs resolve. Raw declarations remain unchanged and each operation emits a provenance-linked event. Five title warnings clear, reducing opaque baseline title states from 34 to 29. The complete declaration and effective-state inventory is recorded in `Docs/title_holder_head_of_faith_inventory.md`.

## Dated Title-Name Replay

Parser `1.10.0` replays seven `name` declarations and one `reset_name = yes` declaration into a separate baseline name-override projection. All six referenced localization keys resolve, including two exact localization aliases. The stable title ID and default localization remain unchanged; explicit reset state retains its source date and declaration order.

All eight raw declarations remain auditable. Six complete title warnings clear; `k_lotharingia` retains its separate Royal Court effect. Opaque baseline title states fall from 29 to 23. Full evidence is recorded in `Docs/title_name_history_inventory.md`.

## Exact Effect-Form De Jure Replay

Parser `1.11.0` recognizes the two complete effect bodies containing only `set_de_jure_liege_title = title:<id>`. Both targets resolve as empires, and installed title-scoped usages establish that the command replaces the current title's de-jure liege. The operations feed the existing dated de-jure projection while preserving their raw effect bodies.

Bodies with additional fields, non-literal or malformed scopes, unresolved targets, and self-targets remain opaque. Both affected title warnings clear, reducing opaque baseline title states from 23 to 21. Full evidence is recorded in `Docs/title_de_jure_inventory.md`.

## Dynasty Prestige Floor Replay

Parser `1.12.0` recognizes six exact `tgp_set_minamoto_taira_dynasty_prestige_effect = yes` bodies after binding the complete installed helper definition and its hash. The helper loops on the resolved holder dynasty until `dynasty_prestige_level >= 5`, so replay records a lower-bound constraint rather than an inferred exact level.

All six execution-time holders and dynasties resolve. Mixed bodies, changed helper definitions, and unresolved scopes remain opaque. Six title warnings clear, reducing opaque baseline title states from 21 to 15. Full evidence is recorded in `Docs/title_dynasty_prestige_inventory.md`.

## Exact Effect-Form Title Name Replay

Parser `1.13.0` recognizes the complete `d_aragon` effect body containing only `set_title_name = d_zaragoza`. The localization key resolves to “Zaragoza,” and the operation feeds the existing dated name-override projection without changing stable title identity or default localization.

Mixed bodies and unresolved keys remain opaque. The `d_aragon` warning clears, reducing opaque baseline title states from 15 to 14. Full evidence is recorded in `Docs/title_name_history_inventory.md`.

## Exact Direct Dynasty Prestige Floor Replay

Parser `1.14.0` recognizes only the complete `c_nf_yamato` body that scopes to `holder.dynasty` and increments until `dynasty_prestige_level >= 9`. Its execution-time holder `japanese_yamato_30` has the explicit, unique, valid installed dynasty `japanese_yamato`; an unrelated character-effect warning does not invalidate that field-specific dependency.

The declaration reuses the dynasty prestige lower-bound projection with `minimum_prestige_level = 9` and no inferred exact level. Mixed or structurally changed bodies and unresolved holder/dynasty scopes remain opaque. The Yamato warning clears, reducing opaque baseline title states from 14 to 13. Full evidence is recorded in `Docs/title_dynasty_prestige_inventory.md`.

## Exact Two-Field Historical Adventurer Replay

Parser `1.15.0` recognizes the complete `d_laamp_henry_of_skalitz` body containing only `create_landless_adventurer_title_history_effect = yes` and `adventurer_creation_reason = flag:historical`. Its effective nonzero holder and explicit `landless_adventurer_succession_law` make the reviewed creation helper idempotent, as in the established three-field family.

Replay emits only initialization and title-variable events. It does not synthesize the omitted destruction-helper effect; Henry's separate date-matched declaration remains the source of that no-op. Mixed or changed bodies remain opaque. The warning clears, reducing opaque baseline title states from 13 to 12. Full evidence is recorded in `Docs/title_adventurer_effect_inventory.md`.

## Exact Ceremonial-Title Variable Replay

Parser `1.16.0` recognizes only the complete `k_chrysanthemum_throne` effect body containing one `set_variable` with exact name `ceremonial_title` and resolved literal value `title:e_japan`. Installed consumers establish that this variable stores a title scope; replay records `value_kind = title` without predicting later runtime mutation or removal.

Mixed, reordered, malformed, nonliteral, and unresolved bodies remain opaque. The raw declaration is retained and the resolved variable is visible in the Reference Inspector. The overall opaque-title count remains 12 because `k_chrysanthemum_throne` retains separate Royal Court and law-plus-destruction bodies. Full evidence is recorded in `Docs/title_variable_inventory.md`.
