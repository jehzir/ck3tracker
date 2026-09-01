# Title De Jure Liege Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser: `installed_title_history` `1.4.0`

## Baseline Evidence

The 867 cutoff contains 30 `de_jure_liege` declarations across 21 titles and 14 target IDs. Every declaration is a scalar title ID and remains preserved in `source.title_history_declarations` with effective date, raw value, source path, line range, and global declaration order.

All 14 target IDs resolve to titles in the same baseline. Ordered date and declaration replay produces 21 rows in `reference.title_baseline_de_jure_lieges`. No baseline-effective declaration is an explicit clear.

The complete installed history contains 95 declarations. Its only explicit clear is `k_asturias = 0` on `0910-12-20`, which establishes the clear representation even though it is after the 867 cutoff.

## Replay Contract

- A valid scalar title ID replaces the prior dated de-jure parent for that title.
- Scalar `0` replaces the prior value with an explicit null parent.
- Nonzero targets must resolve to a title in the same baseline; self-targets and malformed or unresolved values remain unsupported.
- `reference.titles.parent_title_id` remains the immutable installed landed-title hierarchy.
- Dated state, effective date, declaration order, and validation are stored separately in `reference.title_baseline_de_jure_lieges`.
- The Reference Inspector displays static and dated parentage side by side.

This normalization reduces the opaque-title readiness finding from 178 to 160 states. Three of the 21 affected titles retain other unsupported operations. Snapshot and baseline remain `candidate`, `historical_state_complete` remains false, and `app.supported_baselines` remains empty.

## Exact Effect-Form Replacements

Parser `1.11.0` additionally recognizes two baseline-effective title-scope effect bodies:

| Title | Date | Target | Source | Lines | Declaration order |
|---|---|---|---|---:|---:|
| `k_caspian_steppe` | `0864-01-01` | `e_caspian-pontic_steppe` | `history/titles/k_caspian_steppe.txt` | 12-14 | 35220 |
| `k_khakassia` | `0840-01-02` | `e_kirghiz_khanate` | `history/titles/k_khakassia.txt` | 9-11 | 62832 |

Each complete body contains exactly one scalar `set_de_jure_liege_title = title:<id>` command. Installed scripted effects repeatedly place this command inside an explicit `title:<id> = { ... }` scope, proving that it changes the current title's de-jure liege to the supplied title scope. The later `1066-01-01` declaration on `k_khakassia` uses the same command to replace its target with `e_mongolia`, confirming ordinary dated replacement semantics.

Both 867 targets resolve as empire-rank titles in the same baseline. The parser accepts only the exact one-command body, a literal `title:` scope, a resolved non-self target, and a title-history effect executed in the enclosing title scope. Mixed bodies, malformed scopes, dynamic scopes, unresolved targets, and self-targets remain opaque. Raw effect bodies and source provenance remain unchanged.

The two operations feed the existing `reference.title_baseline_de_jure_lieges` projection and emit `de_jure_liege_replaced` events; no generic effect interpreter or alternate parentage model is introduced. Opaque title states fall from 23 to 21. Snapshot and baseline remain candidates, `historical_state_complete` remains false, and `app.supported_baselines` remains empty.