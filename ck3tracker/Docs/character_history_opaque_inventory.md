# Character-History Opaque Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Parser observed: `installed_character_history@1.8.0`
- Inventory date: 2026-09-01
- Scope: all baseline states whose validation note contains `not evaluated: effect`

## Implementation Progress

Character-history parser `1.8.0` implements O03 and O10. All 12 complete language-only bodies normalize, producing 15 provenance-bearing `history_granted` rows for 12 characters. Every row is effective by the 867 cutoff; no post-baseline language event materializes into baseline state. Native and existing title-history knowledge remain authoritative no-ops, while all 12 mixed language declarations remain preserved.

The candidate warning count falls from 107 to 95 opaque character states. Backup `ck3tracker_v2.before-character-history-1.8.0.20260901-194743.duckdb` precedes the clean reload, and readiness report `ck3_1_19_0_6_867:readiness:4f2d5916-7cf6-40fc-b7f5-49df4d0c0201` binds the completed parser run.

The nickname evidence review resolves O01 and the nickname portions of O27-O29/O48 as scalar latest-event state. The 16 warning-linked assignments are deterministic direct children, all 15 keys resolve, and none of those characters repeats or clears a nickname. Full reconciliation also finds 104 disjoint direct baseline assignments already preserved without warnings, for 120 nickname-bearing baseline characters total. Schema and replay are not yet implemented, so counts remain unchanged; see `Docs/character_history_nickname_review.md`.

## Reconciliation

The blocker contains exactly 107 character states. Those subjects own 157 baseline-effective `effect` declarations: 36 declarations are already `normalized` as reviewed flags or relationships, while 121 declarations remain `preserved` and cause the warnings. No warning subject lacks a preserved declaration.

| Measure | Count |
|---|---:|
| Warning states | 107 |
| Total baseline-effective effect declarations on those states | 157 |
| Already normalized declarations | 36 |
| Preserved opaque declarations | 121 |
| Unique ordered structural shapes across all 157 declarations | 70 |
| Shapes represented among normalized declarations | 7 |
| Shapes represented among preserved declarations | 64 |

The shape totals overlap once: `add_character_flag` appears in both sets because 23 exact flags are reviewed non-projecting while one distinct flag remains semantically persistent. Therefore $7 + 64 - 1 = 70$ unique shapes.

Across all 157 declarations, 75 subjects have one declaration and 32 have multiple declarations. Across only the 121 preserved declarations, 96 subjects have one, eight have two, and three have three. The 11 opaque-only overlaps are `144000(2)`, `163111(3)`, `163112(2)`, `40605(2)`, `45105(2)`, `6878(2)`, `70150(2)`, `73813(3)`, `73957(2)`, `bookmark_huang_chao(3)`, and `easteregg_henry_of_skalitz(2)`.

The other 21 multi-declaration subjects combine one or more already-normalized effects with preserved effects: `1000230509`, `1230316`, `163099`, `163100`, `163101`, `163108`, `163157`, `163164`, `168137`, `251180`, `34014`, `40606`, `45107`, `45108`, `6839`, `73683`, `73857`, `90107`, `abbasid_concubines_4`, `extra_turks_0001`, and `japanese_yamato_30`.

## Already-Normalized Context

These declarations do not themselves require new work. They are included because the warning is character-level and may coexist with a separate preserved declaration. Paths are relative to `history/characters/`.

| ID | Rows | Exact ordered shape | Source distribution | Representative |
|---|---:|---|---|---|
| N01 | 23 | `add_character_flag` | `basque:1; bedouin:1; berber:1; daylamite:1; franconian:1; galician:1; han:1; levantine:1; norse:6; occitan:1; persian:2; tajik:5; turkish:1` | `73813`, `basque.txt:4733-4735` |
| N02 | 6 | `set_relation_rival{target,reason}` | `basque:1; hausa:1; norse:4` | `73813`, `basque.txt:4761-4766` |
| N03 | 2 | `set_relation_friend` | `levantine:1; tajik:1` | `abbasid_concubines_4`, `levantine.txt:12797-12799` |
| N04 | 2 | `set_relation_friend{reason,target}` | `andalusian:1; levantine:1` | `surunbaqi0001`, `andalusian.txt:5930-5932` |
| N05 | 1 | `create_betrothal` | `japanese:1` | `japanese_yamato_30`, `japanese.txt:723-725` |
| N06 | 1 | `make_concubine` | `hausa:1` | `251180`, `hausa.txt:98-100` |
| N07 | 1 | `set_primary_spouse` | `japanese:1` | `japanese_yamato_30`, `japanese.txt:729-731` |

## Preserved Shape Ledger

`S` means a complete single-purpose body; `M` means a mixed body spanning multiple projections or semantics. `Replay` requires durable projection with declaration provenance. `Non-projecting` requires exact reviewed evidence. `Inactive` is acceptable only for the proven installed package branch. `Block` means the shape remains unresolved.

| ID | Rows | Kind | Exact ordered shape | Source distribution and representative | Affected state; proposed disposition |
|---|---:|---|---|---|---|
| O01 | 12 | S | `give_nickname` | `armenian:4; basque:1; french:1; hausa:1; korean:1; lombard:1; norse:2; swabian:1`; `armenian_000011`, `armenian.txt:8338-8340` | Nickname; reviewed scalar replacement, replay after nickname schema |
| O02 | 10 | S | `if{government_allows,vassal_contract_set_obligation_level{type,level}}` | `greek:10`; `145116`, `greek.txt:16760-16770` | Contract; Replay after contract/scope model |
| O03 | 9 | S | `learn_language_of_culture` | `karluk:4; persian:1; tajik:4`; `extra_karluks_4`, `karluk.txt:3384-3386` | Language knowledge; Implemented in parser `1.8.0` |
| O04 | 7 | S | `add_trait+add_trait_xp{trait,value{integer_range{min,max}}}` | `asturleonese:1; basque:1; bedouin:1; hungarian:1; norse:3`; `70017`, `asturleonese.txt:131-142` | Trait and random XP; Block pending random-state policy |
| O05 | 6 | S | `make_character_crypto_religionist_effect{CRYPTO_RELIGION}` | `afghan:2; andalusian:1; daylamite:2; levantine:1`; `188713`, `afghan.txt:380-382` | Secret faith and secret; Replay installed helper |
| O06 | 5 | S | `add_gold` | `bodpa:1; cisalpine:1; greek:1; norse:2`; `247105`, `bodpa.txt:1092-1114` | Starting gold; Replay after resource projection |
| O07 | 3 | S | `if{has_fp3_dlc_trigger,add_trait}` | `bedouin:1; sogdian:2`; `163166`, `bedouin.txt:6803-6808` | Conditional trait; Block until FP3 package evidence |
| O08 | 3 | S | `if{has_realm_law,add_realm_law}` | `egyptian:1; franconian:1; greek:1`; `163115`, `egyptian.txt:1489-1494` | Realm law; Replay after law/scope lookup |
| O09 | 3 | S | `if{liege-or-court-owner-differs,set_employer}` | `japanese:3`; `japanese_lowborn_1`, `japanese.txt:103098-103103` | Employer; Replay after scope resolution |
| O10 | 3 | S | `learn_language_of_culture+learn_language_of_culture` | `karluk:2; turkish:1`; `extra_karluks_6`, `karluk.txt:3434-3437` | Two ordered languages; Implemented in parser `1.8.0` |
| O11 | 2 | S/M | `add_character_flag+add_character_flag` | `andalusian:1; easteregg_non_developers:1`; `surunbaqi0001`, `andalusian.txt:5923-5926` | Appearance flags may be non-projecting; independence flag remains blocking |
| O12 | 2 | S | `add_pressed_claim` | `berber:1; catalan:1`; `danis0004`, `berber.txt:7317-7319` | Claims; Replay after claim projection |
| O13 | 2 | S | `add_prestige` | `norse:2`; `144000`, `norse.txt:3012-3014` | Prestige; Replay after resource projection |
| O14 | 2 | S | `create_character_memory{type}` | `han:2`; `bookmark_huang_chao`, `han.txt:141923-141927` | Memory; Replay through journal-independent history projection |
| O15 | 2 | S | `set_realm_capital` | `bedouin:1; sogdian:1`; `163098`, `bedouin.txt:6331-6333` | Realm capital; Replay after character/title scope model |
| O16 | 2 | S | `spawn_army{name,levies,location,origin}` x4 | `norse:2`; `163111`, `norse.txt:3902-3927` | Starting armies; Replay after army projection |
| O17 | 1 | S | `add_character_flag` | `japanese:1`; `japanese_yamato_30`, `japanese.txt:734-736` | Ceremonial-liege flag; Replay persistent flag |
| O18 | 1 | M | `add_character_flag+if{not has_perk,add_perk}` x7 | `norse:1`; `6878`, `norse.txt:514-545` | Appearance/perks; Block mixed body |
| O19 | 1 | M | `flag+relations+claim+gold+spawn_army` | `levantine:1`; `azariqa_0009`, `levantine.txt:12690-12708` | Six dimensions; Block mixed body |
| O20 | 1 | S | `add_character_modifier` | `norse:1`; `144000`, `norse.txt:3005-3008` | Modifier; Replay after modifier projection |
| O21 | 1 | M | `add_gold+FP1-conditional spawn_army` | `norse:1`; `6811`, `norse.txt:4219-4253` | Gold and army; Block pending FP1 and projections |
| O22 | 1 | M | `add_gold+set_relation_rival{target,reason}` | `basque:1`; `73813`, `basque.txt:4774-4782` | Gold and relationship; Block mixed body |
| O23 | 1 | M | `add_gold+spawn_army+conditional realm law` | `levantine:1`; `34014`, `levantine.txt:8558-8583` | Gold, army, law; Block mixed body |
| O24 | 1 | M | `claim+gold+friend+realm capital+primary title` | `galician:1`; `73857`, `galician.txt:5317-5323` | Five dimensions; Block mixed body |
| O25 | 1 | S | `add_unpressed_claim` | `turkish:1`; `163132`, `turkish.txt:7437-7439` | Claim; Replay after claim projection |
| O26 | 1 | S | `create_character_memory{type}+every_memory{set_variable{name,value}}` | `han:1`; `bookmark_huang_chao`, `han.txt:141937-141944` | Memory and location metadata; Replay together |
| O27 | 1 | M | `give_nickname+add_character_flag` | `catalan:1`; `70150`, `catalan.txt:15028-15031` | Nickname reviewed; full support after nickname projection because appearance flag is already reviewed |
| O28 | 1 | M | `give_nickname+add_gold` | `norse:1`; `40605`, `norse.txt:748-751` | Nickname reviewed; gold remains blocking after partial projection |
| O29 | 1 | M | `give_nickname+random{chance,give_witch_secret_or_trait_effect}` | `norse:1`; `40606`, `norse.txt:813-819` | Nickname reviewed; random trait/secret remains blocking after partial projection |
| O30 | 1 | M | `if{not roads_to_power,set_employer}+add_character_flag` | `norse:1`; `242`, `norse.txt:23-31` | Employer branch inactive under reviewed installed package; family flag non-projecting |
| O31 | 1 | M | `if{roads_to_power,change_government}+flags+global-list/scopes+create_artifact_weapon_effect` | `easteregg_non_developers:1`; `easteregg_henry_of_skalitz`, `easteregg_non_developers.txt:247-275` | Government, flags, scopes, artifact; Block |
| O32 | 1 | S | `if{has_fp1_dlc_trigger,spawn_army}+else{spawn_army}` | `norse:1`; `40605`, `norse.txt:754-786` | Starting army; Block until FP1 package evidence |
| O33 | 1 | S | `if{has_mpo_dlc_trigger,contract-write,contract-write}` | `khazar:1`; `3022740`, `khazar.txt:1046-1058` | Installed MPO branch is deterministic; Replay selected contract write |
| O34 | 1 | S | `imprison{target,type}` | `levantine:1`; `73683`, `levantine.txt:9467-9472` | Imprisonment; Replay after relationship/status projection |
| O35 | 1 | M | `language+pressed claims` x2 `+crypto helper` | `daylamite:1`; `45107`, `daylamite.txt:16-21` | Language, claims, secrets; Block mixed body |
| O36 | 1 | M | `language+unpressed claim` | `tajik:1`; `163161`, `tajik.txt:780-783` | Language and claim; Block mixed body |
| O37 | 1 | M | `language+claim+capital+modifier+FP3 trait` | `tajik:1`; `1000230509`, `tajik.txt:933-942` | Five dimensions; Block mixed body |
| O38 | 1 | M | `language+language+unpressed claim` | `turkish:1`; `extra_turks_0002`, `turkish.txt:12372-12376` | Languages and claim; Block mixed body |
| O39 | 1 | M | `language+reverse_add_opinion` | `turkish:1`; `extra_turks_0001`, `turkish.txt:12343-12350` | Language and opinion; Block mixed body |
| O40 | 1 | M | `language+set_relation_nemesis` | `tajik:1`; `extra_tahirids_15`, `tajik.txt:1188-1191` | Language and relationship; Block mixed body |
| O41 | 1 | M | `crypto helper+language` | `levantine:1`; `163133`, `levantine.txt:8112-8115` | Secrets and language; Block mixed body |
| O42 | 1 | M | `set_realm_capital+FP3-conditional trait` | `khwarezmian:1`; `188598`, `khwarezmian.txt:265-273` | Capital and trait; Block mixed body |
| O43 | 1 | M | `set_relation_best_friend+language` | `karluk:1`; `extra_karluks_3`, `karluk.txt:3359-3362` | Relationship and language; Block mixed body |
| O44 | 1 | M | `best friend+potential rival+language` | `tajik:1`; `1230316`, `tajik.txt:1930-1934` | Relationships and language; Block mixed body |
| O45 | 1 | M | `set_relation_friend+set_realm_capital` | `tajik:1`; `163099`, `tajik.txt:33-36` | Relationship and capital; Block mixed body |
| O46 | 1 | M | `friend+gold+prestige+prestige XP+FP1 armies` | `norse:1`; `6878`, `norse.txt:548-615` | Resources, relationship, armies; Block |
| O47 | 1 | M | `friend+claim+rival+FP3 trait` | `bedouin:1`; `45108`, `bedouin.txt:40-52` | Relationship, claim, trait; Block |
| O48 | 1 | M | `friend+give_nickname` | `norse:1`; `306010`, `norse.txt:4135-4138` | Nickname reviewed; full support after nickname projection because friendship is already reviewed |
| O49 | 1 | M | `friend+set_realm_capital` | `basque:1`; `73813`, `basque.txt:4744-4747` | Relationship and capital; Block |
| O50 | 1 | M | `friend+add_character_flag` | `japanese:1`; `japanese_fujiwara_530`, `japanese.txt:15988-15991` | Relationship and ceremonial-regent flag; Block |
| O51 | 1 | M | `lover+rival+claims` x2 `+trait/random XP` | `andalusian:1`; `73957`, `andalusian.txt:1892-1908` | Relationship, claims, trait; Block |
| O52 | 1 | M | `nemesis+crypto helper` | `afghan:1`; `188712`, `afghan.txt:359-362` | Relationship and secrets; Block |
| O53 | 1 | M | `nemesis+friend+rival+capital+language+opinion` | `berber:1`; `danis0005`, `berber.txt:7364-7381` | Relationship, capital, language, opinion; Block |
| O54 | 1 | M | `relations+claims` x2 `+language+opinion` | `tajik:1`; `163100`, `tajik.txt:688-700` | Relationship, claims, language; Block |
| O55 | 1 | M | `potential rival+pressed claims` x2 | `afghan:1`; `175060`, `afghan.txt:10-14` | Relationship and claims; Block |
| O56 | 1 | M | `potential rival+set_realm_capital` | `daylamite:1`; `45105`, `daylamite.txt:372-375` | Relationship and capital; Block |
| O57 | 1 | M | `relations+prestige+gold+army+FP3 trait` | `persian:1`; `163101`, `persian.txt:1763-1784` | Relationship, resources, army, trait; Block |
| O58 | 1 | M | `potential rivals` x2 `+rival+language` | `tajik:1`; `163157`, `tajik.txt:135-140` | Relationship and language; Block |
| O59 | 1 | M | `rival+conditional perks` x4 `+armies` x4 `+capital` | `kurdish:1`; `extra_kurds_0010`, `kurdish.txt:1845-1944` | Relationship, perks, armies, capital; Block |
| O60 | 1 | M | `rival+friend+prestige XP+prestige` | `catalan:1`; `70150`, `catalan.txt:15034-15044` | Relationship and prestige; Block |
| O61 | 1 | S | `spawn_army{name,levies,location,origin}` | `basque:1`; `73813`, `basque.txt:4750-4758` | Starting army; Replay after army projection |
| O62 | 1 | S | `spawn_army{name,levies,men_at_arms,location,origin,inheritable}` x4 | `levantine:1`; `azariqa_0006`, `levantine.txt:12611-12656` | Starting armies; Replay after army projection |
| O63 | 1 | S | `spawn_army{name,levies,men_at_arms,location,origin,war_keep_on_attacker_victory}` x3 | `bedouin:1`; `163096`, `bedouin.txt:5650-5696` | Starting armies and war retention; Replay after army projection |
| O64 | 1 | M | `vassal_contract_set_obligation_level+set_relation_friend` | `occitan:1`; `168137`, `occitan.txt:12973-12981` | Contract and relationship; Block mixed body |

The ledger accounts for all 121 preserved declarations exactly once. The 16 repeated-shape rows contribute 73 declarations and the 48 singleton-shape rows contribute 48, totaling 121.

## Installed Dependency Evidence

- `common/scripted_triggers/00_has_dlc_scripted_triggers.txt:70-92` maps FP1 to `the_northern_lords`, FP3 to `legacy_of_persia`, and MPO to `khans_of_the_steppe`. The snapshot has reviewed MPO package evidence, but FP1 and FP3 are not yet bound, so their branch outcomes remain unresolved.
- The same trigger file maps EP3 and playable-adventurer checks to `roads_to_power`; that package is reviewed and installed, making O30's no-Roads-to-Power employer branch inactive.
- `common/scripted_effects/00_religious_interaction_effects.txt:1250` defines `make_character_crypto_religionist_effect` as persistent secret-faith and crypto-religionist-secret state unless already established.
- `common/scripted_effects/00_secret_effects.txt:116` defines the witch helper as a runtime-dependent witch secret or trait. The random caller in O29 cannot be collapsed to one deterministic value.
- `common/scripted_effects/00_ep1_artifact_creation_effects.txt:9553` constructs Henry's typed weapon artifact with owner, creator, quality, wealth, type, history, and modifiers.
- `common/character_memory_types/tgp_memories.txt:80` defines Huang Chao's failed-examination memory; `localization/english/memories_l_english.yml:1557` resolves its label, and installed event/dynasty logic queries that memory.
- Installed nickname localization resolves every key used by O01, O27-O29, and O48. Installed modifiers resolve Harald's vow and the Baghdad police-chief modifier. Installed contract definitions resolve the obligation types and levels used by O02, O33, and O64.
- `learn_language_of_culture` is persistent character language knowledge. Its target culture can be resolved through `reference.culture_native_languages`, and the existing `reference.character_baseline_languages` projection already owns provenance-bearing `history_granted` rows.
- Army names used by the complete bodies resolve through installed localization, including Azariqa Fanatics, Ayyar Loyalists, and the character-titled default host. Army composition and retention still require a dedicated projection.
- Ceremonial-liege and ceremonial-regent flags are consumed by installed TGP title/on-action logic. `should_become_independent` is consumed by installed civil-war logic. They cannot be treated as cosmetic appearance flags.

## Decision

The 107 states remain blocking as a group. No evidence supports a blanket exception: the preserved bodies contain persistent languages, claims, resources, traits, secrets, contracts, capitals, memories, modifiers, armies, flags, employment, imprisonment, government, artifacts, and title state.

Parser `1.8.0` now covers O03 and O10. Mixed language bodies O35-O41, O43-O44, O53-O54, and O58 remain blocking until every operation in each body is supported.

Nickname semantics and storage boundaries are resolved in `Docs/character_history_nickname_review.md`. O01 is the next unresolved complete family. Its 12 bodies must be implemented together with the 104 direct baseline assignments that currently do not warn; otherwise warning reduction would overstate baseline completeness. O27/O48 can become fully supported after nickname projection, while O28/O29 must retain warnings for gold and random witch outcomes.