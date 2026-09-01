# Title Name History Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Scope: seven baseline-effective `name` declarations, one `reset_name` declaration, and one exact `set_title_name` effect across eight titles.
- Raw declarations remain unchanged in `source.title_history_declarations`.

## Replay Contract

`name = KEY` is a dated replacement of a title's display-name localization key. The key must resolve through the snapshot's reviewed English localization catalog; exact whole-value aliases such as `$k_east_francia$` are followed with cycle and missing-key rejection. `reset_name = yes` explicitly restores the title's default localization.

Parser `1.13.0` also accepts an effect body containing exactly one scalar `set_title_name = KEY` command. Installed title-scoped usage establishes that the command changes the current title's name, while `title:d_aragon = { reset_title_name = yes }` demonstrates its explicit reversal. Mixed bodies and unresolved localization keys remain opaque.

The effective state is stored separately in `reference.title_baseline_name_overrides`. It does not alter `reference.titles.title_id`, `localization_key`, or `display_name`. A reset is retained as `explicit_default` with its date and declaration order rather than represented as missing history.

Title Modding revision `32469` documents title localization keys and dated title-history execution. Installed history supplies the exact `name` and `reset_name` declarations.

## Declaration Inventory

| Title | Date | Operation | Value | Source | Line | Order |
|---|---|---|---|---|---:|---:|
| `k_dali` | `0728-01-01` | `name` | `NAME_NANZHAO` | `history/titles/e_seasia.txt` | 18 | 16900 |
| `k_east_francia` | `0769-01-01` | `name` | `EAST_FRANCIA` | `history/titles/k_east_francia.txt` | 7 | 40970 |
| `d_swabia` | `0865-01-01` | `reset_name` | `yes` | `history/titles/k_east_francia.txt` | 3333 | 42027 |
| `k_france` | `0481-01-01` | `name` | `WEST_FRANCIA` | `history/titles/k_france.txt` | 9 | 47024 |
| `k_france` | `0768-09-24` | `name` | `WEST_FRANCIA` | `history/titles/k_france.txt` | 73 | 47046 |
| `d_normandy` | `0001-01-01` | `name` | `NEUSTRIA` | `history/titles/k_france.txt` | 1378 | 47452 |
| `k_hungary` | `0797-01-01` | `name` | `KINGDOM_PANNONIA` | `history/titles/k_hungary.txt` | 58 | 54892 |
| `k_lotharingia` | `0855-08-22` | `name` | `LOTHARINGIA` | `history/titles/k_lotharingia.txt` | 95 | 69655 |
| `d_aragon` | `0711-01-01` | `effect: set_title_name` | `d_zaragoza` | `history/titles/k_aragon.txt` | 1095 | 25635 |

## Effective 867 State

| Title | Key | Display value | Status |
|---|---|---|---|
| `d_normandy` | `NEUSTRIA` | Neustria | `declared` |
| `d_swabia` | none | default title localization | `explicit_default` |
| `k_dali` | `NAME_NANZHAO` | Nanzhao | `declared` |
| `k_east_francia` | `EAST_FRANCIA` | East Francia | `declared` |
| `k_france` | `WEST_FRANCIA` | West Francia | `declared` |
| `k_hungary` | `KINGDOM_PANNONIA` | Pannonia | `declared` |
| `k_lotharingia` | `LOTHARINGIA` | Lotharingia | `declared` |
| `d_aragon` | `d_zaragoza` | Zaragoza | `declared` |

All nine declarations normalize. The direct-operation slice clears six complete title warnings, while `k_lotharingia` retains a separate opaque Royal Court effect. Exact effect-form replay clears `d_aragon`, reducing opaque baseline title states from 15 to 14. Snapshot and baseline remain candidates, `historical_state_complete=false`, and `app.supported_baselines` remains empty.