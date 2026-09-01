# Historical Adventurer Effect Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.15.0`

## Evidence Contract

Twenty baseline-effective bodies have the same ordered fields:

1. `create_landless_adventurer_title_history_effect = yes`
2. `set_variable = { name = adventurer_creation_reason value = flag:historical }`
3. `destroy_landless_title_no_dlc_effect = { DATE = 867.1.1 }`

The installed creation helper conditionally adds `landless_adventurer_succession_law` to the holder's realm. Every affected title has an effective holder and explicitly declares that law before the effect, so the helper is idempotent. The second operation creates durable title-scoped state consumed by installed title on-actions and memory logic. The third operation is a proven no-op under reviewed `roads_to_power -> dlc014_ep3` evidence.

Normalization requires the exact field order and values, matching declaration and helper dates, an effective nonzero holder, the explicit installed succession law, exact installed helper definitions, and validated DLC evidence. Any deviation remains opaque; partial normalization is rejected.

One additional baseline-effective body has exactly the first two fields and no destruction invocation:

```text
effect = {
	create_landless_adventurer_title_history_effect = yes
	set_variable = { name = adventurer_creation_reason value = flag:historical }
}
```

`d_laamp_henry_of_skalitz` declares holder `easteregg_henry_of_skalitz` and `landless_adventurer_succession_law` before this body at `0866-01-01`. The body is declaration 7358 at `history/titles/01_laamp_titles.txt:1159-1162`. A separate declaration 7359 invokes the date-gated destruction helper, so declaration 7358 proves only adventurer initialization and the historical variable.

Parser `1.15.0` accepts this exact two-field sequence under the same holder, law, installed-helper, and DLC prerequisites. It emits no synthetic destruction event. Added, reordered, or changed fields remain opaque as a complete body.

## Baseline Inventory

| Title | Date | Field order | Source path | Declaration order |
|---|---|---|---|---:|
| d_laamp_xuanji | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6963 |
| d_laamp_guttorm | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6969 |
| d_laamp_ahwazi | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6975 |
| d_laamp_ziyar | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6981 |
| d_laamp_anangapida | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6987 |
| d_laamp_hrolfr | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6993 |
| d_laamp_ubbe | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 6999 |
| d_laamp_enian | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7005 |
| d_laamp_sevener_caliph | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7011 |
| d_laamp_twelver_caliph | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7017 |
| d_laamp_qutid | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7023 |
| d_laamp_takaoka | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7029 |
| d_laamp_ding_hui | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7035 |
| d_laamp_zhu_quanzhong | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7041 |
| d_laamp_miyoshi_kiyotsura | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7047 |
| d_laamp_hidden_valley_banner | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7053 |
| d_laamp_way_of_the_mountains | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7059 |
| d_laamp_pongyi_thaing_fellowship | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7065 |
| d_laamp_ravine_lords | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7071 |
| d_laamp_sirafi_mariners | 0867-01-01 | create, variable, destroy | history/titles/01_laamp_titles.txt | 7077 |

Production materializes 21 valid `adventurer_creation_reason=flag:historical` rows. The 20 three-field bodies emit three provenance-linked events each; Henry's two-field body emits only initialization and variable events. Its warning clears, reducing the later opaque-title count from 13 to 12. Snapshot and baseline remain `candidate`, `historical_state_complete=false`, and no supported baseline exists.