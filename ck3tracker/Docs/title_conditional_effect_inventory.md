# Title Conditional Effect Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Scope: 74 baseline-effective opaque `effect` declarations whose sole top-level field is `if`, across 73 titles.
- Excluded: `b_lichtenfels` declaration 41541, already normalized by the date-gated capital replay.
- Raw declarations remain unchanged in `source.title_history_declarations`.

## Reviewed Families

| Family | Rows | Titles | Result |
|---|---:|---:|---|
| Exact no-Roads-to-Power government fallback | 64 | 63 | Normalized as deterministic no-op |
| Royal Court language assignment | 4 | 4 | Three normalized; `k_balhae` preserved because installed and observed values conflict |
| Royal Court language assignment plus conditional language learning | 5 | 5 | Normalized: four learned rows and one already-native no-op |
| Royal Court court-type assignment | 1 | 1 | Normalized into durable court-type state |

The normalized family has exactly this structure and ordering:

```text
if = {
    limit = {
        exists = holder
        NOT = { has_dlc_feature = roads_to_power }
    }
    holder = {
        empty_treasury_when_abandoning_landed_life_effect = yes
        change_government = feudal_government
    }
}
```

Reviewed mapping `roads_to_power -> dlc014_ep3` resolves to the valid installed Roads to Power descriptor. Therefore the negative DLC condition is false for this snapshot regardless of holder state, and the complete exact body is a no-op. Parser `1.8.0` emits `dlc_gated_conditional_noop`; changed values, ordering, or extra fields remain opaque.

Reviewed mapping `royal_court -> dlc004_ep1` resolves to the valid installed descriptor `dlc/dlc004_ep1/dlc004.dlc`, its SHA-256 manifest, and CK3 Wiki Royal Court revision `35819`. Parser `1.18.0` binds adjudicated assignments to their execution-time holder, writes durable court state, and evaluates the five exact `knows_court_language_of` branches against durable personal language knowledge. Four holders gain provenance-bearing `history_granted` rows; Tajik Nasr's Iranian branch is a proven already-native no-op.

## Declaration Inventory

| Title | Date | Source | Order | Family | Resolution |
|---|---|---|---:|---|---|
| `k_silla` | `0867-01-01` | `history/titles/e_goryeo.txt` | 14481 | Royal Court language | Normalized |
| `k_chrysanthemum_throne` | `0503-03-03` | `history/titles/e_japan.txt` | 16413 | Royal Court language | Normalized |
| `k_viet` | `0866-01-01` | `history/titles/e_seasia.txt` | 17207 | Royal Court language | Normalized |
| `c_seleucia` | `0638-01-01` | `history/titles/k_anatolia.txt` | 20865 | Roads to Power no-op | Normalized |
| `c_lycandus` | `0330-01-01` | `history/titles/k_anatolia.txt` | 20893 | Roads to Power no-op | Normalized |
| `d_cibyrrhaeot` | `0330-01-01` | `history/titles/k_anatolia.txt` | 20977 | Roads to Power no-op | Normalized |
| `c_lycia` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21009 | Roads to Power no-op | Normalized |
| `d_anatolia` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21096 | Roads to Power no-op | Normalized |
| `c_lycaonia` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21112 | Roads to Power no-op | Normalized |
| `c_pacatiana` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21142 | Roads to Power no-op | Normalized |
| `c_selge` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21195 | Roads to Power no-op | Normalized |
| `d_cappadocia` | `0330-01-01` | `history/titles/k_anatolia.txt` | 21306 | Roads to Power no-op | Normalized |
| `k_balhae` | `0867-01-01` | `history/titles/k_balhae.txt` | 27271 | Royal Court language | Preserved |
| `k_bengal` | `0855-01-01` | `history/titles/k_bengal.txt` | 29829 | Royal Court court type | Normalized |
| `k_bulgaria` | `0852-01-01` | `history/titles/k_bulgaria.txt` | 33203 | Royal Court language and learning | Preserved |
| `d_turnovo` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 33344 | Roads to Power no-op | Normalized |
| `c_sredets` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 33456 | Roads to Power no-op | Normalized |
| `d_bulgaria` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 33840 | Roads to Power no-op | Normalized |
| `c_naissus` | `0681-01-01` | `history/titles/k_bulgaria.txt` | 33876 | Roads to Power no-op | Normalized |
| `c_pomoravlje` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 33915 | Roads to Power no-op | Normalized |
| `c_pirin` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 33986 | Roads to Power no-op | Normalized |
| `d_philippopolis` | `0330-01-01` | `history/titles/k_bulgaria.txt` | 34116 | Roads to Power no-op | Normalized |
| `d_cyprus` | `0330-01-01` | `history/titles/k_cyprus.txt` | 37535 | Roads to Power no-op | Normalized |
| `c_nicosia` | `0688-01-01` | `history/titles/k_cyprus.txt` | 37566 | Roads to Power no-op | Normalized |
| `d_epirus` | `0330-01-01` | `history/titles/k_epirus.txt` | 45680 | Roads to Power no-op | Normalized |
| `c_nicopolis` | `0330-01-01` | `history/titles/k_epirus.txt` | 45703 | Roads to Power no-op | Normalized |
| `c_aetolia` | `0330-01-01` | `history/titles/k_epirus.txt` | 45742 | Roads to Power no-op | Normalized |
| `d_dyrrachion` | `0330-01-01` | `history/titles/k_epirus.txt` | 45784 | Roads to Power no-op | Normalized |
| `d_dyrrachion` | `0865-01-01` | `history/titles/k_epirus.txt` | 45791 | Roads to Power no-op | Normalized |
| `c_dyrrachion` | `0330-01-01` | `history/titles/k_epirus.txt` | 45823 | Roads to Power no-op | Normalized |
| `c_cephalonia` | `0330-01-01` | `history/titles/k_epirus.txt` | 45990 | Roads to Power no-op | Normalized |
| `d_athens` | `0330-01-01` | `history/titles/k_hellas.txt` | 53660 | Roads to Power no-op | Normalized |
| `c_euboea` | `0330-01-01` | `history/titles/k_hellas.txt` | 53730 | Roads to Power no-op | Normalized |
| `d_achaia` | `0330-01-01` | `history/titles/k_hellas.txt` | 53756 | Roads to Power no-op | Normalized |
| `c_achaia` | `0330-01-01` | `history/titles/k_hellas.txt` | 53788 | Roads to Power no-op | Normalized |
| `c_korinthos` | `0330-01-01` | `history/titles/k_hellas.txt` | 53817 | Roads to Power no-op | Normalized |
| `c_messenia` | `0330-01-01` | `history/titles/k_hellas.txt` | 53848 | Roads to Power no-op | Normalized |
| `c_laconia` | `0330-01-01` | `history/titles/k_hellas.txt` | 53877 | Roads to Power no-op | Normalized |
| `k_italy` | `0855-09-20` | `history/titles/k_italy.txt` | 57603 | Royal Court language and learning | Preserved |
| `k_lotharingia` | `0855-08-22` | `history/titles/k_lotharingia.txt` | 69656 | Royal Court language and learning | Preserved |
| `d_opsikion` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76416 | Roads to Power no-op | Normalized |
| `c_prusa` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76473 | Roads to Power no-op | Normalized |
| `d_ephese` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76516 | Roads to Power no-op | Normalized |
| `c_aeolis` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76554 | Roads to Power no-op | Normalized |
| `d_thracesia` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76568 | Roads to Power no-op | Normalized |
| `c_chonae` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76662 | Roads to Power no-op | Normalized |
| `d_optimatoi` | `0330-01-01` | `history/titles/k_nikaea.txt` | 76686 | Roads to Power no-op | Normalized |
| `d_bucellaria` | `0753-01-01` | `history/titles/k_nikaea.txt` | 76727 | Roads to Power no-op | Normalized |
| `c_kerch` | `0839-01-01` | `history/titles/k_pontic_steppe.txt` | 85432 | Roads to Power no-op | Normalized |
| `d_paphlagonia` | `0330-01-01` | `history/titles/k_pontus.txt` | 85537 | Roads to Power no-op | Normalized |
| `d_armeniac` | `0330-01-01` | `history/titles/k_pontus.txt` | 85619 | Roads to Power no-op | Normalized |
| `c_sinope` | `0330-01-01` | `history/titles/k_pontus.txt` | 85674 | Roads to Power no-op | Normalized |
| `d_sebasteia` | `0750-01-01` | `history/titles/k_pontus.txt` | 85745 | Roads to Power no-op | Normalized |
| `d_charsianon` | `0330-01-01` | `history/titles/k_pontus.txt` | 85858 | Roads to Power no-op | Normalized |
| `d_chaldia` | `0330-01-01` | `history/titles/k_pontus.txt` | 85971 | Roads to Power no-op | Normalized |
| `c_colonea` | `0855-01-01` | `history/titles/k_pontus.txt` | 86050 | Roads to Power no-op | Normalized |
| `c_siracusa` | `0536-01-01` | `history/titles/k_sicily.txt` | 93989 | Roads to Power no-op | Normalized |
| `c_malta` | `0536-01-01` | `history/titles/k_sicily.txt` | 94065 | Roads to Power no-op | Normalized |
| `c_lecce` | `0536-01-01` | `history/titles/k_sicily.txt` | 94668 | Roads to Power no-op | Normalized |
| `k_sindh` | `0866-01-01` | `history/titles/k_sindh.txt` | 94900 | Royal Court language and learning | Preserved |
| `d_antioch` | `0330-01-01` | `history/titles/k_syria.txt` | 97717 | Roads to Power no-op | Normalized |
| `c_kalliopolis` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100090 | Roads to Power no-op | Normalized |
| `d_strymon` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100137 | Roads to Power no-op | Normalized |
| `c_mosynopolis` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100157 | Roads to Power no-op | Normalized |
| `d_aegean_islands` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100208 | Roads to Power no-op | Normalized |
| `c_naxos` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100231 | Roads to Power no-op | Normalized |
| `c_abydos` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100252 | Roads to Power no-op | Normalized |
| `c_lesbos` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100280 | Roads to Power no-op | Normalized |
| `c_chios` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100311 | Roads to Power no-op | Normalized |
| `c_rhodos` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100346 | Roads to Power no-op | Normalized |
| `d_thessalonika` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100375 | Roads to Power no-op | Normalized |
| `c_thessalia` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100493 | Roads to Power no-op | Normalized |
| `c_demetrias` | `0330-01-01` | `history/titles/k_thessalonika.txt` | 100521 | Roads to Power no-op | Normalized |
| `k_transoxiana` | `0864-01-01` | `history/titles/k_transoxiana.txt` | 100594 | Royal Court language and learning | Preserved |

## Outcome

- 64 declarations across 63 titles normalize as no-ops.
- Four complete court-only declarations normalize into durable court state.
- Six Royal Court declarations remain preserved: five pending character-language projection and `k_balhae` pending evidence reconciliation.
- Current opaque baseline title states are 9 after all later parser milestones.
- Snapshot and baseline remain `candidate`; `historical_state_complete=false`; `app.supported_baselines` remains empty.