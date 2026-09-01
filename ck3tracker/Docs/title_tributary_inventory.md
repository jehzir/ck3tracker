# Title Tributary Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.5.0`

## Evidence And Semantics

The complete installed history contains 94 `tributary_of` declarations, all structured blocks. At the 867 cutoff, ordered replay produces 23 effective declarations across 23 titles. Every effective block has exactly one `suzerain` and one `contract_group`; all six suzerain IDs resolve in the same baseline and every block uses `tributary_mandala`.

Installed `common/subject_contracts/groups/subject_contract_groups.txt` defines `tributary_mandala` with `is_tributary = yes`, tributary and suzerain heir succession, and explicit tributary obligations. Installed `start_tributary` consumers pass the same `suzerain` and `contract_group` pair. This establishes a durable subject relationship rather than liege or de-jure hierarchy.

## Baseline Inventory

| Title | Effective date | Suzerain | Contract group | Source path | Declaration order |
|---|---|---|---|---|---:|
| c_ava | 0846-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81626 |
| c_canasha | 0867-01-01 | d_angkor | tributary_mandala | history/titles/e_khmer.txt | 16688 |
| c_chakangrao | 0867-01-01 | k_dvaravati | tributary_mandala | history/titles/k_dvaravati.txt | 40240 |
| c_hanlan | 0867-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81686 |
| c_kauthara | 0867-01-01 | k_champa | tributary_mandala | history/titles/e_khmer.txt | 16859 |
| c_kusumi | 0860-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81887 |
| c_kyaukse | 0867-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81639 |
| c_ma_linh | 0867-01-01 | k_champa | tributary_mandala | history/titles/e_khmer.txt | 16822 |
| c_mae_hong_son | 0867-01-01 | d_haripunjaya | tributary_mandala | history/titles/k_dvaravati.txt | 40407 |
| c_manipur | 0849-01-01 | d_pagan | tributary_mandala | history/titles/k_kamarupa.txt | 61678 |
| c_panduranga | 0867-01-01 | k_champa | tributary_mandala | history/titles/e_khmer.txt | 16873 |
| c_pegu | 0861-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81848 |
| c_phetchabun | 0867-01-01 | k_dvaravati | tributary_mandala | history/titles/k_dvaravati.txt | 40250 |
| c_ramu | 0866-01-01 | d_arakan | tributary_mandala | history/titles/k_pagan.txt | 81766 |
| c_sagaing | 0846-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81658 |
| c_sriksetra | 0860-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81696 |
| c_sukhothai | 0867-01-01 | d_haripunjaya | tributary_mandala | history/titles/k_dvaravati.txt | 40259 |
| c_takon | 0867-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81676 |
| c_thabeik_taung | 0866-01-01 | d_arakan | tributary_mandala | history/titles/k_pagan.txt | 81773 |
| c_vijaya | 0867-01-01 | k_champa | tributary_mandala | history/titles/e_khmer.txt | 16835 |
| d_arakan | 0849-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81720 |
| d_ramannadesa | 0860-01-01 | d_pagan | tributary_mandala | history/titles/k_pagan.txt | 81808 |
| d_vyadhapura | 0867-01-01 | d_angkor | tributary_mandala | history/titles/e_khmer.txt | 16521 |

## Replay Contract

- A valid block replaces the title's prior dated tributary relationship.
- The suzerain must resolve to a different title in the same baseline.
- The contract group must resolve uniquely to an installed definition with `is_tributary = yes`.
- Malformed blocks, unresolved targets, self-targets, and non-tributary groups remain opaque and blocking.
- Raw declarations and definition provenance remain immutable and auditable.
- Tributary state is stored separately from ordinary liege, static hierarchy, and dated de-jure parentage.

Production materializes 23 valid relationships, reduces opaque title states from 160 to 137, and leaves snapshot/baseline status unchanged at `candidate`, `historical_state_complete=false`, with no supported baselines.