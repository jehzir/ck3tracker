# Head-of-Faith Holder Override Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Scope: 43 baseline-effective `holder_ignore_head_of_faith_requirement` declarations across five titles.
- Source: `history/titles/00_other_titles.txt`.
- Raw declarations remain unchanged in `source.title_history_declarations`.

## Semantics And Boundary

The installed operation accepts the same scalar character IDs and `0` clear value as ordinary `holder`. It appears in the same dated holder sequences, and later ordinary `holder` declarations replace it. Its name records the assignment-time exception: the named character is installed as holder without enforcing the normal head-of-faith eligibility requirement.

All 39 distinct nonzero IDs resolve to valid baseline character records. The single baseline-effective `0` is an explicit clear. Title Modding revision `32469` documents dated title-history execution, character-ID holder values, and `0` holder clears, but does not document this bypass variant; its command-specific evidence is therefore the complete installed history usage rather than an inferred wiki table.

Parser `1.9.0` replays the operation into the existing holder field, emits a provenance-linked event, and distinguishes a live bypass assignment with `holder_status=declared_ignore_head_of_faith_requirement`. A `0` value uses `holder_status=explicit_unheld`. This does not create a second holder or persist an eligibility flag after a later ordinary holder assignment.

## Declaration Inventory

| Title | Date | Value | Source line | Order |
|---|---|---|---:|---:|
| `k_orthodox` | `0427-12-24` | `145053` | 735 | 243 |
| `k_orthodox` | `0535-06-05` | `70581` | 774 | 256 |
| `k_orthodox` | `0730-01-22` | `70562` | 846 | 280 |
| `k_orthodox` | `0766-11-16` | `70560` | 852 | 282 |
| `k_orthodox` | `0769-01-02` | `70560` | 858 | 284 |
| `k_orthodox` | `0780-02-07` | `70559` | 861 | 285 |
| `k_orthodox` | `0815-04-01` | `145042` | 870 | 288 |
| `k_orthodox` | `0821-01-01` | `70557` | 873 | 289 |
| `k_orthodox` | `0837-01-21` | `70556` | 876 | 290 |
| `d_patriarchate_in_the_east` | `0035-01-01` | `166236` | 1097 | 361 |
| `d_patriarchate_in_the_east` | `0052-01-01` | `166237` | 1100 | 362 |
| `d_patriarchate_in_the_east` | `0070-01-01` | `166238` | 1103 | 363 |
| `d_patriarchate_in_the_east` | `0077-01-01` | `166239` | 1106 | 364 |
| `d_patriarchate_in_the_east` | `0087-01-01` | `166240` | 1109 | 365 |
| `d_patriarchate_in_the_east` | `0120-01-01` | `166241` | 1112 | 366 |
| `d_patriarchate_in_the_east` | `0159-01-01` | `166242` | 1115 | 367 |
| `d_patriarchate_in_the_east` | `0171-01-01` | `166243` | 1118 | 368 |
| `d_patriarchate_in_the_east` | `0204-01-01` | `166244` | 1121 | 369 |
| `d_patriarchate_in_the_east` | `0220-01-01` | `166245` | 1124 | 370 |
| `d_patriarchate_in_the_east` | `0280-01-01` | `166246` | 1127 | 371 |
| `d_patriarchate_in_the_east` | `0329-01-01` | `166247` | 1130 | 372 |
| `d_patriarchate_in_the_east` | `0341-01-01` | `166248` | 1133 | 373 |
| `d_patriarchate_in_the_east` | `0343-01-01` | `166249` | 1136 | 374 |
| `d_patriarchate_in_the_east` | `0363-01-01` | `166250` | 1139 | 375 |
| `d_patriarchate_in_the_east` | `0377-01-01` | `166251` | 1142 | 376 |
| `d_patriarchate_in_the_east` | `0400-01-01` | `166252` | 1145 | 377 |
| `d_patriarchate_in_the_east` | `0410-01-01` | `166253` | 1148 | 378 |
| `d_patriarchate_in_the_east` | `0415-01-01` | `166254` | 1151 | 379 |
| `d_patriarchate_in_the_east` | `0420-01-01` | `166255` | 1154 | 380 |
| `d_patriarchate_in_the_east` | `0420-06-01` | `166256` | 1157 | 381 |
| `d_patriarchate_in_the_east` | `0421-01-01` | `166257` | 1160 | 382 |
| `d_patriarchate_in_the_east` | `0457-01-01` | `166258` | 1163 | 383 |
| `d_patriarchate_in_the_east` | `0485-01-01` | `166260` | 1169 | 385 |
| `d_patriarchate_in_the_east` | `0609-01-01` | `166272` | 1208 | 398 |
| `d_sunni` | `0610-01-01` | `33922` | 1716 | 555 |
| `d_sunni` | `0656-07-17` | `33911` | 1731 | 560 |
| `d_shiite` | `0610-01-01` | `33922` | 1908 | 618 |
| `d_shiite` | `0632-06-08` | `33911` | 1914 | 620 |
| `d_imami` | `0765-12-14` | `163022` | 5434 | 1520 |
| `d_imami` | `0799-09-01` | `163023` | 5437 | 1521 |
| `d_imami` | `0818-08-23` | `163024` | 5440 | 1522 |
| `d_imami` | `0835-11-24` | `163025` | 5443 | 1523 |
| `d_imami` | `0866-12-30` | `0` | 5446 | 1524 |

## Effective 867 Holder State

| Title | Final operation | Effective holder | Status |
|---|---|---|---|
| `d_imami` | bypass clear, 0866-12-30 | none | `explicit_unheld` |
| `d_patriarchate_in_the_east` | ordinary holder, 0860-01-01 | `166294` | `declared` |
| `d_shiite` | ordinary clear, 0867-01-01 | none | `explicit_unheld` |
| `d_sunni` | ordinary holder, 0866-01-01 | `34014` | `declared` |
| `k_orthodox` | ordinary holder, 0866-11-23 | `70555` | `declared` |

All 43 declarations normalize. Five complete title warnings clear, reducing opaque baseline title states from 34 to 29. Snapshot and baseline remain candidates, `historical_state_complete=false`, and `app.supported_baselines` remains empty.