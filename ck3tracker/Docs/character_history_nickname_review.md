# Character-History Nickname Review

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Parser observed: `installed_character_history@1.8.0`
- Review date: 2026-09-01
- Scope: O01 and mixed shapes O27-O29/O48, reconciled with direct nickname operations already preserved by the parser

## Decision

Nickname state is one replaceable scalar per character, not an additive set. Preserve every dated set or clear as an append-only event, then derive the active baseline nickname from the latest applicable event by effective date and declaration order. A set carries one installed nickname stable ID; a clear carries no nickname ID.

The evidence supports deterministic extraction only from direct operations and direct children of an `effect` body. Never descend into `if`, `random`, scripted helpers, or other nested bodies. A mixed body's direct nickname child may be projected independently, but the declaration remains preserved and its character warning remains until every sibling operation is supported or reviewed as non-projecting.

This makes O01 fully replayable. Nickname projection also completes O27 and O48 because their sibling appearance flag and friendship are already reviewed. O28 and O29 remain blocking after nickname projection: O28 still contains unsupported gold, while O29 still contains a random witch secret-or-trait outcome.

## Blocker-Linked Ledger

All 16 baseline-effective warning-linked assignments are unconditional direct children of their enclosing `effect` bodies. The 12 O01 bodies contain only `give_nickname`; four bodies are mixed. No affected character has another `give_nickname` or `remove_nickname` anywhere in installed character history, so these 16 rows do not themselves exercise replacement chronology.

| Character | Effective date | Nickname key | Source | Shape |
|---|---|---|---|---|
| `korean_go_goguryeo_39` | `0072-01-01` | `nick_the_great` | `history/characters/korean.txt:2375` | O01 |
| `armenian_000011` | `0288-01-01` | `nick_the_illuminator` | `history/characters/armenian.txt:8338-8340` | O01 |
| `armenian_000018` | `0353-01-01` | `nick_the_great` | `history/characters/armenian.txt:8419-8421` | O01 |
| `armenian_000045` | `0641-01-01` | `nick_the_builder` | `history/characters/armenian.txt:8728-8730` | O01 |
| `armenian_000050` | `0717-01-01` | `nick_the_philosopher` | `history/characters/armenian.txt:8793-8795` | O01 |
| `161483` | `0827-01-01` | `nick_the_timid` | `history/characters/swabian.txt:6835-6837` | O01 |
| `302221` | `0833-01-01` | `nick_blue_snake` | `history/characters/norse.txt:692` | O01 |
| `302222` | `0834-01-01` | `nick_the_loyal` | `history/characters/norse.txt:710-712` | O01 |
| `70150` | `0840-01-01` | `nick_the_hairy` | `history/characters/catalan.txt:15028-15031` | O27: nickname + appearance flag |
| `163075` | `0842-01-01` | `nick_the_old` | `history/characters/lombard.txt:3594-3596` | O01 |
| `306010` | `0855-01-01` | `nick_the_truthspeaker` | `history/characters/norse.txt:4135-4138` | O48: friendship + nickname |
| `163060` | `0864-01-01` | `nick_the_terrible` | `history/characters/basque.txt:6158-6160` | O01 |
| `251180` | `0865-01-01` | `nick_the_slayer_of_the_snake` | `history/characters/hausa.txt:105-107` | O01 |
| `40605` | `0866-01-01` | `nick_troublemaker` | `history/characters/norse.txt:748-751` | O28: nickname + gold |
| `40606` | `0866-01-01` | `nick_the_seer` | `history/characters/norse.txt:813-819` | O29: nickname + nested random outcome |
| `42020` | `0866-01-30` | `nick_the_child` | `history/characters/french.txt:14604` | O01 |

## Key Resolution

All 15 distinct keys resolve exactly once in installed `common/nicknames/00_nicknames.txt` and exactly once in English localization. `is_prefix` defaults to `no` for every reviewed key. `nick_the_child`, `nick_the_old`, `nick_the_terrible`, and `nick_the_timid` set `is_bad = yes`; the other 11 default to `no`.

| Key | English label | Definition line |
|---|---|---:|
| `nick_blue_snake` | Blue Snake | 30 |
| `nick_the_builder` | the Builder | 46 |
| `nick_the_child` | the Child | 62 |
| `nick_the_great` | the Great | 108 |
| `nick_the_hairy` | the Hairy | 61 |
| `nick_the_illuminator` | the Illuminator | 45 |
| `nick_the_loyal` | the Loyal | 322 |
| `nick_the_old` | the Old | 332 |
| `nick_the_philosopher` | the Philosopher | 261 |
| `nick_the_seer` | the Seer | 32 |
| `nick_the_slayer_of_the_snake` | the Slayer of the Snake | 44 |
| `nick_the_terrible` | the Terrible | 330 |
| `nick_the_timid` | the Timid | 158 |
| `nick_the_truthspeaker` | the Truthspeaker | 159 |
| `nick_troublemaker` | Troublemaker | 31 |

The labels are in `localization/english/nicknames_l_english.yml`; the nickname stable ID is also the localization key. The definition contract documents `is_prefix`, `is_bad`, `has_nickname`, singular `has_any_nickname`, and `give_nickname`.

## Scalar-State Evidence

- Installed `_nicknames.info` defines `has_any_nickname` as whether a character has a nickname and `give_nickname` as giving the scoped character the specified nickname. The API is singular throughout.
- Harald Fairhair receives `nick_tanglehair` on `0850-01-01` and later receives `nick_fairhair` on `0872-01-01` without an intervening clear (`norse.txt:2997-3018`).
- William the Conqueror receives `nick_the_bastard` on `1035-07-03` and later receives `nick_the_conqueror` on `1066-12-25` without an intervening clear (`norman.txt:1033-1035`, `1130-1133`).
- Rodrigo Diaz de Vivar's history explicitly executes `remove_nickname = yes` before a later `give_nickname = nick_el_cid`, proving a distinct clear operation rather than an empty additive collection update.
- Installed nickname helper logic tests `has_any_nickname` before assignment and deliberately permits replacement of a bad nickname. That behavior requires one active value.

Together, later set events replace earlier active values; clear events remove the active value. History remains additive only at the event/provenance layer.

## Full Baseline Reconciliation

The warning ledger is not the full state surface. The parser already preserves 104 baseline-effective direct `give_nickname` declarations on 104 other characters but does not project them and does not warn for them. They span 25 source files and 50 keys. Combined with the 16 effect-wrapped assignments, the 867 baseline has 120 nickname-bearing characters and 63 distinct keys; the two character sets do not overlap. Every one of the 63 keys resolves to an installed definition and English localization. There are no baseline-effective clears.

Across the complete installed direct-operation timeline there are 505 sets on 500 characters and one explicit clear. Of those direct operations, 401 sets and the clear occur after the 867 cutoff. Across `effect` bodies there are 33 deterministic direct-child sets: 16 at or before the cutoff and 17 after it. Nested nickname outcomes are not included in these counts.

The direct baseline source distribution is: `andalusian:1; armenian:10; basque:1; bedouin:2; breton:2; cumbrian:6; czech:1; easteregg_non_developers:1; ethiopian:1; franconian:3; frankish:6; french:6; georgian:1; german:1; greek:3; irish:5; korean:1; levantine:20; norse:12; persian:3; roman:2; saka:2; turkish:1; visigothic:2; welsh:11`.

Implementation must therefore replay both the direct and effect-wrapped event forms. Supporting only O01 would clear visible warnings while leaving 104 known baseline nickname states absent.

## Durable Contract

Use three separate ownership layers:

1. `reference.nicknames`: one snapshot-scoped catalog row per installed nickname definition, keyed by `(reference_snapshot_id, nickname_id)`, with `is_bad`, `is_prefix`, resolved English label, definition and localization source coordinates, raw definition, and validation status.
2. `reference.character_nickname_events`: append-only set/clear events keyed independently of current state, with snapshot, character, effective date, declaration order, event kind, nullable nickname ID, source group, source declaration ID, exact source coordinates, and validation status. A set requires a valid nickname ID; a clear forbids one.
3. `reference.character_baseline_nickname_states`: sparse latest-event state keyed by `(baseline_id, character_id)`, with nullable active nickname ID, last event kind/date/order, source group/declaration ID, and validation status. No row means no known nickname event by the cutoff; a clear-derived row records proven absence and clear provenance.

The event identity must prevent duplicate materialization on reload while allowing multiple events for one character. Catalog and state foreign keys must remain snapshot-consistent. Character-history reload replaces only character-history-owned nickname events/states and never deletes another source group's rows.

## Exact Parser Boundary

- Normalize top-level direct `give_nickname = <key>` and `remove_nickname = yes` declarations after key/value validation.
- In an `effect` declaration, inspect only top-level children. Extract direct `give_nickname = <key>` and `remove_nickname = yes`; never recursively discover nested assignments.
- Fully normalize a complete nickname-only body after catalog resolution.
- In a mixed body, emit the proven nickname event but leave the raw declaration `preserved` until all direct siblings and nested bodies are supported or explicitly reviewed.
- Resolve every set key before transaction mutation. Unknown keys, invalid clear values, malformed bodies, or unresolved character identity fail closed.
- Materialize all events for provenance, but derive baseline state using only events effective on or before the baseline cutoff, ordered by canonical game date and declaration order.
- Apply direct and effect-wrapped events in one chronology so a later event wins regardless of syntax form.

## Outcome

The reviewed contract is implemented in character-history parser `1.9.0`. All 539 installed direct or direct-effect-child operations materialize as 538 sets and one clear; nested outcomes remain excluded. The 867 projection contains 120 characters across 63 active nickname IDs, with complete source-operation provenance and source-group-scoped replacement.

O01 and O48 are fully resolved. O27's nickname/appearance declaration is normalized, but character `70150` remains warning because a separate same-day prestige body is unresolved. O28 and O29 retain warnings for gold and random witch state. Opaque character subjects fall from 95 to 82 without changing candidate or promotion status.