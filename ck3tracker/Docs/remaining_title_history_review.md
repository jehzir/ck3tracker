# Remaining Title History Review

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Review date: 2026-08-31
- Current parser: `installed_title_history` `1.18.0`
- Current readiness report: `ck3_1_19_0_6_867:readiness:8b174297-d096-4740-a8c8-4467f8223c60`
- Current unresolved count: 4 title states; the twelve-title table below is the reviewed source ledger.

## Why The Count Is 12

The readiness service currently counts every baseline title state whose `validation_note` contains `not evaluated:` and classifies the entire count as blocking. It does not distinguish product-critical title identity/hierarchy from unmodeled court state or from mixed effect bodies.

Therefore, “12 blocking titles” means 12 title rows still contain at least one baseline-effective preserved effect. It does not mean twelve title IDs are missing, invalid, unusable, or known to have incorrect holder/hierarchy state. Eleven are selectable and have otherwise resolved baseline title state. `k_chrysanthemum_throne` is nonselectable only as a geographic playthrough-start location because it has no canonical de jure chain; it is nevertheless a functional ceremonial title beneath `e_japan`.

Reviewed mapping `royal_court -> dlc004_ep1` resolves to the valid installed The Royal Court descriptor, its SHA-256 source manifest, platform IDs, and CK3 Wiki Royal Court revision `35819`. Royal Court conditional branches are deterministic as installed for this snapshot; they remain blocking where their active state lacks a durable projection.

## Title Summary

| Title | Display name | Selectable | Remaining declaration(s) | Category | Recommended disposition |
|---|---|---:|---|---|---|
| `e_byzantium` | Byzantine Empire | yes | `#1028`, `history/titles/00_other_titles.txt:3706-3733` | Orthodox administrative-state initialization, optional Royal Court Intrigue Court initialization, and an inactive no-Roads-to-Power fallback | Do not treat current government or succession as unresolved. At 867 the title is administrative with `acclamation_succession_law`; the fallback to feudal plus `single_heir_succession_law` does not run when Roads to Power is installed. Only state-faith/court initialization remains outside current projections. |
| `e_japan` | Japan | yes | `#15088`, `history/titles/e_japan.txt:18-35` | Royal Court language plus TGP administrative UI title variable | Keep blocking until the TGP variable is modeled and the court branch is scoped. |
| `k_balhae` | Bóhai | yes | `#27271`, `history/titles/k_balhae.txt:8-16` | Installed history requests Chinese; observed game UI reports Tungusic as new court-language state and exposes the five-year adoption lock | Do not waive as generic mutable presentation. Reconcile the source/runtime language difference and decide whether the initial 1,825-day lock belongs to supported baseline state. |
| `k_bengal` | Bengal | yes | `#29829`, `history/titles/k_bengal.txt:23-33` | Scholarly Court initialization for Narayanapala's Pala Kingdom | Known, screenshot-confirmed baseline court state. It may be excluded only through an explicit policy that court type is outside the supported contract, not because the declaration is unresolved. |
| `k_bulgaria` | Bulgaria | yes | `#33203`, `history/titles/k_bulgaria.txt:71-85` | Greek court language for Boris's Bulgarian kingdom; Boris learns Greek if needed | Resolved baseline court and character-language state. Any exception must explicitly exclude both dimensions; this is not an ambiguous effect. |
| `k_chrysanthemum_throne` | Chrysanthemum Throne | no geographic start | `#16413`, `history/titles/e_japan.txt:2059-2067`; `#16444`, lines 2100-2103 | Mutable Royal Court language; ceremonial-throne primogeniture plus TGP no-op | Functional kingdom-tier title under `e_japan`, held by the Tenno when imperial authority is fractured. Its lack of a canonical de jure chain excludes it from location selection but does not make it dispensable. Declaration 16444 should be replayed as proven title state, not waived as structural noise. |
| `k_italy` | Italy | yes | `#57603`, `history/titles/k_italy.txt:110-124` | High German court language for Louis II's Italy; French Louis learns High German if needed | Resolved baseline court and character-language state based on the title history's stated German ties. Any exception must explicitly exclude both dimensions. |
| `k_lotharingia` | Lotharingia | yes | `#69656`, `history/titles/k_lotharingia.txt:96-110` | High German court language standing in for Old Frankish; French Lothair II learns High German if needed | Resolved baseline court and character-language state. Any exception must explicitly exclude both dimensions and retain the source's historical substitution. |
| `k_silla` | Silla | yes | `#14481`, `history/titles/e_goryeo.txt:337-345` | Chinese court language under Silla-culture King Eung-ryeom, reflecting Chinese bureaucratic and literary influence | Resolved baseline court state. The declaration does not teach the Korean-speaking holder Chinese, so no personal language knowledge should be inferred from this effect. |
| `k_sindh` | Sindh | yes | `#94900`, `history/titles/k_sindh.txt:28-42` | Arabic court language for Umar I Habbari's Sindh; native Vrachada speaker Umar learns Arabic if needed | Resolved baseline court and character-language state. The same date's clan government is already projected and is explicitly an ahistorical bookmark convenience. |
| `k_transoxiana` | Transoxiana | yes | `#100594`, `history/titles/k_transoxiana.txt:10-24` | Iranian court language for Tajik Samanid ruler Nasr; conditional learning is a no-op because Iranian is his native language | Resolved baseline court state with no additional character-language change. Clan government is already projected separately. |
| `k_viet` | `$dai_viet$` | yes | `#17207`, `history/titles/e_seasia.txt:780-788` | Chinese court language for Gao Pian's Jinghai Circuit; the Han holder natively speaks Chinese | Resolved baseline court state with no additional character-language change. Celestial government and `h_china` liege state are already projected separately. |

## Review Resume Boundary

The original twelve-title summary was interrupted when credits ran out. Subsequent evidence review is complete through the Pala/Bengal clarification above; the repeated Bengal prompt was caused by that handoff desynchronization.

All 12 titles and 13 declarations now have title-by-title dispositions. Domain or in-game clarification was added for `e_byzantium`, `k_chrysanthemum_throne`, `k_balhae`, `k_bengal`, `k_bulgaria`, `k_italy`, `k_lotharingia`, `k_silla`, `k_sindh`, `k_transoxiana`, and `k_viet`. The `e_japan` row retains its linked ceremonial-title evidence and current blocking disposition.

The evidence-review sequence is complete. The next action is the strict complete-state versus journal-required baseline policy decision; there is no next title to inspect in this twelve-title set.

These reviews refine the eventual policy decision; they do not alter the current 12-title readiness count, parser behavior, candidate statuses, or production database.

## Baseline Completeness Decision

The strict complete-state policy is accepted in `Docs/architecture_decision_001_baseline_completeness.md`. All 12 rows remain blocking until every active baseline-effective operation is represented in durable typed state or proven inactive for this build and baseline.

Court language, court type, administrative state faith, holder language knowledge, title-scoped variables, and title laws belong to `historical_state_complete`. Mutable state still defines the player's starting conditions. Raw preservation and lack of a current journal consumer do not qualify as completeness or as accepted-exception grounds.

The rejected journal-required policy would make baseline truth depend on the application's current display surface and require semantic expansion when later journal features consume already-known game state.

## Byzantine Effect Clarification

Declaration 1028 is one mixed initialization body, but its branches do not describe four simultaneous uncertain states:

1. Because the effective holder is administrative, `set_state_faith = faith:orthodox` initializes the administrative empire's state faith as Orthodox. This is separate from the holder's personal faith, although Basileios is also Orthodox at the baseline.
2. When Royal Court is available, `set_court_type = court_intrigue` initializes the holder's court as Intrigue Court. Court type remains player-changeable and should not be treated as an immutable title attribute.
3. Only when Roads to Power is absent does the holder change to `feudal_government` and receive `single_heir_succession_law`. Roads to Power is present in the reviewed build, so this fallback is inactive.
4. The effective title succession row is `acclamation_succession_law`, declared separately in declaration 1027. Its installed definition uses administrative appointment succession and permits heir designation. The displayed male-preference rule is the separate gender law.

The current warning survives because the parser preserves the mixed body as a whole and has no state-faith or court-state projection. It is not evidence that Byzantium's 867 government or succession is unknown.

## Balhae Court-Language Clarification

Declaration 27271 runs on `0867-01-01` when the title has a holder and Royal Court is available. Its installed source explicitly calls `holder = { set_court_language = language_chinese }`, with the comment “Chinese influence on bureaucracy and literature.”

The observed game UI instead reports Tungusic Language as new court-language state and warns that it cannot be changed for five years. The installed define `NRoyalCourt.COURT_LANGUAGE_ADOPTION_COOLDOWN` is 1,825 days, confirming that adopting a new court language carries a five-year restriction.

Until the source/runtime difference is explained, Balhae must not be reduced to an inconsequential “court language” exception. The supported-baseline decision must account for both the effective language and any adoption-date/cooldown state affecting the first five years of play.

## Bengal Court-Type Clarification

Declaration 29829 is dated `0855-01-01`, assigns Narayanapala Pala as holder, and, when Royal Court is available, executes `set_court_type = court_scholarly`. The observed 867 Royal Court screen confirms that the Pala Kingdom starts with a Scholarly Court.

This is resolved initial gameplay state rather than an unknown effect. Court type remains mutable during play, but it controls Royal Court mechanics and should be projected under a strict complete-state policy. A journal-required policy may exclude it only by explicitly placing court state outside the supported baseline contract while retaining the declaration and screenshot evidence.

## Bulgaria Court-Language Clarification

Declaration 33203 is dated `0852-01-01`, assigns Boris as holder, and, when Royal Court is available, sets his court language to Greek. The source explains that much of Bulgaria's clergy and nobility spoke Greek before the later Old Bulgarian transition.

Boris's culture is Bulgarian, whose installed native language is Slavonic, and his character history contains no earlier Greek-language acquisition. After setting the Greek court language, the declaration checks `knows_court_language_of = this` and calls `learn_court_language_of = this` when false. The effective 867 interpretation is therefore a Greek-speaking court whose Bulgarian ruler has learned Greek in addition to his native language.

The title history later sets Simeon's court language to South Slavic in 893, outside the 867 baseline. Both the initial Greek court language and Boris's personal language knowledge are resolved gameplay state; they remain opaque only because the database has no durable court-language or character-language projection.

## Italy Court-Language Clarification

Declaration 57603 is dated `0855-09-20`, assigns Louis II as holder, and, when Royal Court is available, sets his court language to High German. The source notes that the precise historical court language is difficult to establish and uses Italy's close German ties as the basis for this assignment.

Louis II is French at the 867 baseline, and French culture's installed native language is French rather than High German. His character history contains no earlier language acquisition. After setting the court language, the declaration conditionally calls `learn_court_language_of = this`; the effective interpretation is therefore a High German-speaking Italian court whose French ruler learns High German as an additional language.

The court-language assignment and Louis's resulting language knowledge are resolved gameplay state, while the source comment preserves the historical uncertainty behind Paradox's chosen initialization. They remain unprojected because the database has no durable court-language or character-language state.

## Lotharingia Court-Language Clarification

Declaration 69656 is dated `0855-08-22`, assigns Lothair II as holder, renames the title Lotharingia, and, when Royal Court is available, sets his court language to High German. The source identifies Old Frankish as the historically intended language but uses High German because Old Frankish is dead by 867.

Lothair II is French at the baseline, and French culture's installed native language is French. His character history contains no earlier language acquisition. The declaration's conditional `learn_court_language_of = this` therefore gives Lothair High German as an additional learned language after establishing the High German court.

This is resolved court and character-language state with an explicit historical substitution, not an unknown operation. It remains unprojected because the database has no durable court-language or character-language state.

## Silla Court-Language Clarification

Declaration 14481 is effective on `0867-01-01`, assigns King Eung-ryeom as holder, and, when Royal Court is available, sets his court language to Chinese. The source attributes the choice to Chinese influence on Silla's bureaucracy and literature.

Eung-ryeom has Silla culture, whose installed native language is Korean. His character history contains no Chinese-language acquisition, and this declaration does not include the conditional `learn_court_language_of` operation used by Bulgaria, Italy, and Lotharingia. The evidence therefore establishes a Chinese-speaking court but does not establish that Eung-ryeom personally knows Chinese.

Silla's court language is resolved baseline gameplay state. Any future character-language projection must preserve the absence of a learning effect instead of inferring language knowledge from court membership.

## Sindh Court-Language Clarification

Declaration 94900 is effective on `0866-01-01` and, when Royal Court is available, sets Umar I Habbari's court language to Arabic. It then conditionally calls `learn_court_language_of = this` when the holder does not know that court language.

Umar I has Sindhi culture, whose installed native language is Vrachada, and his character history contains no earlier Arabic-language acquisition. The effective 867 interpretation is therefore an Arabic-speaking court whose native Vrachada-speaking ruler has learned Arabic as an additional language.

The same 866 title-history block sets `clan_government`, explicitly described in the installed source as ahistorical and included for bookmark usability. That government state is already projected separately; declaration 94900 remains opaque only for its court-language and character-language effects.

## Transoxiana Court-Language Clarification

Declaration 100594 is effective on `0864-01-01`, assigns Samanid ruler Nasr as holder, and, when Royal Court is available, sets his court language to Iranian. It conditionally calls `learn_court_language_of = this` only when the holder does not already know the court language.

Nasr has Tajik culture, whose installed native language is Iranian. Once his court is set to Iranian, the knowledge condition is already satisfied, so the learning branch adds no new personal language. The effective 867 state is an Iranian-speaking court under a native Iranian-speaking ruler.

The same title-history block sets `clan_government`, which is already projected separately. Declaration 100594 remains opaque only because court language lacks a durable projection, not because Nasr's character-language outcome is unresolved.

## Viet Court-Language Clarification

Declaration 17207 is effective on `0866-01-01`, assigns Gao Pian (`han_3310`) as holder of the Jinghai Circuit, and, when Royal Court is available, sets his court language to Chinese. The source attributes the court language to Chinese influence on bureaucracy and literature.

Gao Pian has Han culture, whose installed native language is Chinese. The declaration contains no holder-language learning operation, and none is needed: the court language matches his native language. The effective 867 state is a Chinese-speaking court under a native Chinese-speaking ruler.

The same title-history block assigns celestial government and `h_china` as liege, both already projected separately. Declaration 17207 remains opaque only because court language has no durable projection.

## Chrysanthemum Throne Clarification

`k_chrysanthemum_throne` is the functional ceremonial title beneath `e_japan` when Japanese imperial authority is fractured. At the baseline it is held by `japanese_yamato_30`, has `e_japan` as its liege, uses `japan_administrative_government`, and has Yamashiro as its capital.

The installed scripts maintain a two-way semantic link: the throne's `ceremonial_title` variable points to `e_japan`, while Japan's `administrative_ui_special_title` variable points to the throne. Ceremonial-liege triggers identify its holder as the Tenno, restrict hostile/revocation actions against that holder, and support restoration or destruction of the ceremonial arrangement as imperial authority changes.

The observed 867 title screen confirms that the throne is a kingdom-tier province title with guaranteed protection and Male Preference Primogeniture. This agrees with declaration 16444's `add_title_law = single_heir_succession_law`; the date-matched TGP destruction helper is inactive with All Under Heaven installed. The Royal Court language assignment remains mutable presentation state.

Its `selectable = false` status means only that it is not a canonical geographic start location. It must not be described as an irrelevant placeholder or accepted merely because it has no de jure titles beneath it.
