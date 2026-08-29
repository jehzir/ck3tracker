# Title History Opaque Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Starting scope: 556 baseline title states with `not evaluated:` warnings
- Current scope: 178 baseline title states after succession-law normalization
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
| `effect: {tgp_set_minamoto_taira_dynasty_prestige_effect}` | 6 | 6 | `history/titles/02_japan_noble_family.txt` (6) |
| `name` | 6 | 7 | `history/titles/e_seasia.txt` (1); `history/titles/k_east_francia.txt` (1); `history/titles/k_france.txt` (3); `history/titles/k_hungary.txt` (1); `history/titles/k_lotharingia.txt` (1) |
| `holder_ignore_head_of_faith_requirement` | 5 | 43 | `history/titles/00_other_titles.txt` (43) |
| `effect: {set_de_jure_liege_title}` | 2 | 2 | `history/titles/k_caspian_steppe.txt` (1); `history/titles/k_khakassia.txt` (1) |
| `effect: {add_title_law, destroy_landless_title_no_tgp_dlc_effect}` | 1 | 1 | `history/titles/e_japan.txt` (1) |
| `effect: {create_landless_adventurer_title_history_effect, set_variable}` | 1 | 1 | `history/titles/01_laamp_titles.txt` (1) |
| `effect: {if, if, if}` | 1 | 1 | `history/titles/00_other_titles.txt` (1) |
| `effect: {if, if}` | 1 | 1 | `history/titles/e_japan.txt` (1) |
| `effect: {set_title_name}` | 1 | 1 | `history/titles/k_aragon.txt` (1) |
| `effect: {set_variable}` | 1 | 1 | `history/titles/e_japan.txt` (1) |
| `effect: {while}` | 1 | 1 | `history/titles/02_japan_noble_family.txt` (1) |
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
