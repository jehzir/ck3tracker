# Title Dynasty Prestige Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.14.0`
- Installed helper: `common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt`
- Helper SHA-256: `e62ce9f628ef5b52cbd57be17a9f81f355d901a8488a04dc79fe3c5f0ffbbf78`

## Baseline Evidence

All six baseline-effective bodies contain exactly one scalar invocation:

```text
effect = { tgp_set_minamoto_taira_dynasty_prestige_effect = yes }
```

| Source title | Date | Holder at invocation | Dynasty | Source lines | Declaration order |
|---|---|---|---|---:|---:|
| `c_nf_minamoto_montoku` | `0867-01-01` | `japanese_yamato_165` | `japanese_minamoto_montoku` | 972-975 | 7714 |
| `c_nf_minamoto_ninmyo` | `0867-01-01` | `japanese_minamoto_ninmyo_9` | `japanese_minamoto_ninmyo` | 1049-1052 | 7741 |
| `c_nf_minamoto_saga` | `0867-01-01` | `japanese_minamoto_saga_28` | `japanese_minamoto_saga` | 1088-1091 | 7755 |
| `c_nf_taira_kanmu` | `0867-01-01` | `japanese_taira_kanmu_4` | `japanese_taira_kanmu` | 1574-1577 | 7923 |
| `c_nf_tachibana` | `0867-01-01` | `japanese_tachibana_76` | `japanese_tachibana` | 2955-2958 | 8430 |
| `c_nf_takashina` | `0867-01-01` | `japanese_takashina_1` | `japanese_takashina` | 3043-3046 | 8461 |

Every holder declaration precedes its helper invocation in the same dated title block. Every holder resolves to one valid baseline character and one valid installed dynasty. Eight additional exact invocations occur only after 867 and remain preserved without producing 867 state.

One additional baseline-effective declaration directly contains the complete prestige loop:

```text
effect = {
    holder.dynasty ?= {
        while = {
            limit = { dynasty_prestige_level < 9 }
            add_dynasty_prestige_level = 1
        }
    }
}
```

| Source title | Date | Holder at invocation | Dynasty | Source path | Source lines | Declaration order |
|---|---|---|---|---|---:|---:|
| `c_nf_yamato` | `0867-01-01` | `japanese_yamato_30` | `japanese_yamato` | `history/titles/02_japan_noble_family.txt` | 11-18 | 7379 |

The holder's character state carries a warning for an unrelated character effect, but its explicit dynasty field is non-null, unique, and resolves to one valid installed dynasty. Replay depends only on that field and does not certify the unrelated character effect.

## Helper Contract

The complete installed helper is:

```text
tgp_set_minamoto_taira_dynasty_prestige_effect = {
    holder.dynasty ?= {
        while = {
            limit = { dynasty_prestige_level < 5 }
            add_dynasty_prestige_level = 1
        }
    }
}
```

For a resolved holder dynasty with prior level $L$, its deterministic postcondition is:

$$
L_{after} = \max(L_{before}, 5)
$$

The helper therefore proves only `dynasty_prestige_level >= 5`. It does not prove an exact level or the number of loop iterations.

## Replay Contract

Parser `1.14.0` accepts either an effect body containing the single exact helper invocation with scalar `yes`, while the installed helper definition exactly matches the reviewed body, or the single exact direct floor-9 body shown above. It resolves the title holder at the invocation's date and declaration order, then requires a non-null dynasty field resolving to one valid installed dynasty in the same baseline.

Each accepted declaration creates a `reference.dynasty_baseline_prestige_constraints` row with `value_status = lower_bound_only`, plus a provenance-linked `dynasty_prestige_minimum_established` event. Helper invocations record floor 5 and the helper file hash; the direct declaration records floor 9 and its title-history source path without inventing a helper hash. Raw title declarations remain preserved.

Mixed or structurally changed bodies, changed helper definitions, missing or cleared holders, and unresolved dynasties remain opaque. Constraints are independent evidence rows keyed by source declaration; they are not additive and never become exact levels.

The six helper title warnings reduce opaque baseline title states from 21 to 15. The direct Yamato warning reduces the later count from 14 to 13. Snapshot and baseline remain candidates, `historical_state_complete` remains false, and `app.supported_baselines` remains empty.
