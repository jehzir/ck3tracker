# Roads To Power Title No-Op Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.6.0`

## Evidence Contract

Installed `common/scripted_effects/07_dlc_ep3_scripted_effects.txt` defines `destroy_landless_title_no_dlc_effect` to destroy the current title only when both `NOT = { has_dlc_feature = roads_to_power }` and `game_start_date = $DATE$` hold. The validated installed package `dlc014_ep3` is Roads to Power, and reviewed mapping `roads_to_power -> dlc014_ep3` makes that negative DLC condition false for this snapshot.

Normalization requires an effect body containing only this helper, exactly one `DATE` argument, and a date equal to the enclosing history declaration. Changed helper text, absent package evidence, mismatched dates, extra arguments, and mixed effect bodies remain opaque. Raw source text and provenance are retained.

## Baseline Inventory

| Title | Effective date | DATE argument | Source path | Declaration order |
|---|---|---|---|---:|
| d_nf_ampelas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1588 |
| d_nf_aplakes | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1594 |
| d_nf_agelastos | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1600 |
| d_nf_doukas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1606 |
| d_nf_gerontas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1626 |
| d_nf_hexavoulis | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1632 |
| d_nf_kardias | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1639 |
| d_nf_katakalitzes | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1645 |
| d_nf_kourkouas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1651 |
| d_nf_krateros | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1661 |
| d_nf_lachanodrakon | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1669 |
| d_nf_makedon | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1675 |
| d_nf_maleios | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1682 |
| d_nf_maleinos | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1692 |
| d_nf_maurikios | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1698 |
| d_nf_melissenos | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1708 |
| d_nf_pastillas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1722 |
| d_nf_ooryphas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1730 |
| d_nf_sellokalas | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1736 |
| d_nf_skleros | 0867-01-01 | 867.1.1 | history/titles/01_admin_titles.txt | 1744 |
| d_laamp_henry_of_skalitz | 0866-01-01 | 866.1.1 | history/titles/01_laamp_titles.txt | 7359 |

The complete installed history contains 94 exact date-matched invocations. All 21 effective at the 867 cutoff normalize as `dlc_gated_noop` events. Twenty title warnings clear; Henry of Skalitz retains another unsupported effect. Snapshot and baseline remain `candidate`, `historical_state_complete=false`, and `app.supported_baselines` remains empty.