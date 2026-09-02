# Current Build

- Build ID: `B002-scribe-promotion-readiness`
- Build name: Scribe reference-catalog promotion readiness
- Status: `active — nickname storage schema bootstrapped`
- Last updated: 2026-09-02

## Objective

Produce one evidence-backed, immutable CK3 `1.19.0.6 (Scribe)` reference snapshot and 867 baseline in the repository-root DuckDB, then promote it only through an explicit atomic operation after a fresh readiness report has zero blockers.

## Authority And Scope

This file is the sole execution manifest and the only authoritative source for the current priority, next exact action, and resume instructions. Precedence is defined in `Docs/build_session_protocol.md`.

Current scope is reference ingestion, validation, and promotion safety. Imports, dashboard redesign, broader journal workflows, buildings, decisions, army, council, and other product work remain deferred until this build is complete or the user explicitly changes scope.

The workbook is a workflow and visual specification, not runtime storage. Installed CK3 files are build-specific evidence. CK3 Wiki revisions are the reference authority. Stable IDs and source provenance must be preserved, and no loader may promote as a side effect.

## Repository State

- Branch: `master`
- Checkpoint lineage: `704d80e` (`Replay Byzantine administrative state history`) is the parent checkpoint for the current title, character, and nickname sequence.
- Worktree policy: root DuckDB and backup databases remain ignored. The separate `new_version` prototype and `twelve_titles.md` are outside B002 and must not be included in this checkpoint.
- Runtime: Dash development server at `http://127.0.0.1:8051/reference` when active.
- Python: `C:\Python314\python.exe`
- DuckDB: repository-root `ck3tracker_v2.duckdb`

## Completed

- Root `source`, `reference`, `journal`, and `app` schemas and promoted-only selector views.
- Candidate Scribe snapshot `ck3_1_19_0_6_build_23530548` and candidate 867 baseline `ck3_1_19_0_6_867`.
- Installed landed titles, English localization, title history, character history, bookmarks, and static/dynamic capital ingestion with provenance.
- Seven 867 bookmark collections and 35 direct featured rulers validated.
- Capital semantics resolved for all selectable 867 titles.
- Immutable promotion-readiness reports shown in the read-only Reference Inspector.
- Duplicate title blocks classified by baseline impact; all 21 same-date singleton conflicts are resolved by reviewed vanilla source order while every raw block remains preserved.
- Duplicate character blocks classified: 18 semantically identical IDs and two baseline conflicts remain.
- Character parser `1.3.0` normalizes top-level `set_culture`, two proven non-projecting flag values, and pure relationship effects while preserving mixed effects.
- Character review reduced to 95 subjects: zero duplicate conflicts and 95 opaque states.
- Grounded government catalog loaded from 18 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Government` revision `35874`; all 14 baseline-used government IDs resolve.
- Grounded culture catalog loaded from 244 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Culture` revision `35845`; all 228 baseline-used culture IDs resolve. Parser `1.1.0` also loads all 91 installed language definitions and resolves one native language for every culture.
- Grounded faith catalog loaded from 140 installed definitions nested under 49 parent religions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Faith` revision `35751`; all 111 baseline-used faith IDs resolve.
- Grounded dynasty catalog loaded from 10,338 installed definitions with the internal wiki path `Crusader_Kings_III_Wiki` revision `32094` to `Dynasty` revision `35828`; all 10,180 baseline-used dynasty IDs resolve.
- Grounded house catalog loaded from 558 installed definitions with the internal wiki path `Dynasty` revision `35828` to its versioned `Houses` section; all 459 baseline-used dynasty-house IDs resolve and all 235 parent dynasty IDs resolve.
- Readiness now requires the deterministic latest run for each of ten parser groups to be completed at its explicit expected version; older successful runs cannot mask newer failures or obsolete versions.
- All 1,714 source-file manifests are bound to the exact latest parser runs that produced them; readiness blocks missing, detached, and stale run bindings.
- All nine installed bookmark DLC gates resolve through reviewed feature mappings to canonical installed package descriptors: `landless_adventurer -> dlc014_ep3`, `khans_of_the_steppe -> dlc020_ce2`, and `all_under_heaven -> dlc022_ep4`.
- Required snapshot evidence now also resolves `royal_court -> dlc004_ep1` independently of bookmark requirements, binding the valid installed The Royal Court descriptor, platform IDs, SHA-256 manifest, and CK3 Wiki revision `35819`.
- Raw feature flags remain preserved beside package identity, descriptor hashes, platform IDs, and permanent wiki-revision evidence; unknown feature flags remain unresolved and block readiness.
- Bookmark parser is `1.2.0`, title-history parser is `1.22.0`, culture parser is `1.1.0`, character history is `1.8.0`, and the other six required parsers remain `1.0.0`.
- Every readiness report now stores an immutable ten-row evidence ledger containing the exact latest parser-run ID, parser version/status, manifest count, and deterministic SHA-256 digest evaluated for each required source group.
- Readiness retrieval compares stored bindings with current evidence and labels legacy or superseded reports stale without rewriting the persisted report, findings, or evidence ledger.
- All 1,714 current source manifests are covered by the latest report evidence ledger; culture evidence includes the installed language pillar and title history binds installed TGP and law-definition evidence.
- Title-history blocks now record explicit `winner`, `superseded`, or `unresolved` status and expose their source block order, path, conflicting fields, and resolution in the Reference Inspector.
- The permanent `Modding` revision `35725` grounds the engine rule that later ASCII filenames override earlier top-level declarations; this evidence defines vanilla parsing behavior only and adds no mod support.
- All 556 opaque title states are grouped into 19 operation/script shapes with complete source-path counts in `Docs/title_history_opaque_inventory.md`.
- The exact `destroy_landless_title_no_tgp_dlc_effect` family is normalized as a no-op only when its invocation date matches, both installed definitions retain reviewed semantics, and validated package mapping `all_under_heaven -> dlc022_ep4` is present.
- At 867 this records 385 no-op events across 371 titles while preserving every raw declaration. All 371 also contain unsupported `succession_laws`, so the opaque-title count correctly remains 556.
- All 446 baseline-effective `succession_laws` declarations across 431 titles are preserved and normalized as ordered replacement state, including empty clears.
- Fourteen law IDs used across complete installed title history resolve uniquely to bound definitions; the 867 cutoff uses 11 IDs and materializes 431 active rows across 430 titles with no unresolved IDs.
- Active title laws and their definition provenance are visible in the Reference Inspector. Law normalization reduces opaque title states from 556 to 178 without changing unrelated title fields.
- All 30 baseline-effective `de_jure_liege` declarations across 21 titles are preserved and normalized into separate dated parent state; all 14 targets resolve in the same baseline.
- Static landed-title parentage remains immutable while the Reference Inspector displays it beside the 867-effective de-jure parent, date, and source declaration order.
- De-jure normalization reduces opaque title states from 178 to 160; three affected titles retain unrelated unsupported operations.
- The immediate unmodded `Sheikh_Lubb_of_Najera_867_01_01.ck3` save proves `b_logrono` is a city barony in Lubb's domain, distinct from his county `c_najera`; reviewed evidence adjudicates its 867 holder from deceased `73812` to living `73813` while preserving installed history.
- All 23 baseline-effective `tributary_of` declarations are preserved and normalized as dated replacement relationships; all six suzerain IDs resolve and `tributary_mandala` resolves to an installed contract group marked `is_tributary = yes`.
- Tributary state remains separate from liege and de-jure parentage and is visible in the Reference Inspector. Normalization reduces opaque title states from 160 to 137.
- All 21 exact baseline-effective `destroy_landless_title_no_dlc_effect` invocations have matching declaration dates and normalize as no-ops through reviewed `roads_to_power -> dlc014_ep3` evidence; mixed effect bodies remain opaque.
- This Roads to Power normalization reduces opaque title states from 137 to 117; `d_laamp_henry_of_skalitz` retains a separate unsupported effect.
- All 20 exact historical adventurer bodies are fully replayed as an idempotent law check, a durable `adventurer_creation_reason=flag:historical` title variable, and a Roads to Power no-op.
- Historical adventurer normalization reduces opaque title states from 117 to 97; title variables are visible in the Reference Inspector.
- All 74 baseline-effective opaque single-`if` title effects are inventoried by shape and source. The 64 exact no-Roads-to-Power government fallback bodies across 63 titles normalize as deterministic no-ops; parser `1.17.0` also normalizes four complete court-only bodies and preserves the other six after projecting only their proven court state.
- Conditional normalization reduces opaque title states from 97 to 34 while preserving raw declarations and emitting provenance-linked audit events.
- All 43 baseline-effective `holder_ignore_head_of_faith_requirement` declarations across five titles replay as holder replacement/clear operations with a distinct assignment-mode status and provenance events.
- All 39 referenced nonzero character IDs resolve; later ordinary holder declarations supersede bypass assignments normally. Opaque title states fall from 34 to 29.
- Seven dated `name` declarations and one `reset_name` declaration replay into a separate title-name override projection; all localization keys and aliases resolve without changing stable title identity or default labels.
- Name replay clears six complete title warnings and exposes effective override/default state in the Reference Inspector, reducing opaque title states from 29 to 23.
- Both baseline-effective exact `set_de_jure_liege_title = title:<id>` effect bodies replay through the existing dated de-jure projection after resolving their empire targets and proving title-scope semantics from installed usage.
- Effect-form de-jure replay preserves both raw bodies, rejects mixed or unresolved bodies, and reduces opaque title states from 23 to 21 without changing static hierarchy.
- Six exact Minamoto/Taira prestige helper bodies replay as provenance-bearing dynasty minimum-level constraints after resolving each execution-time holder and dynasty and binding the complete installed helper definition.
- Prestige replay records only the proven `dynasty_prestige_level >= 5` postcondition, exposes it in the Reference Inspector, and reduces opaque title states from 21 to 15 without inferring exact runtime levels.
- The exact `d_aragon` `set_title_name = d_zaragoza` effect reuses the dated title-name projection after resolving “Zaragoza”; mixed bodies and unresolved localization keys remain opaque.
- Effect-form title-name replay reduces opaque title states from 15 to 14 without changing stable title identity or default localization.
- The exact direct `c_nf_yamato` prestige loop reuses the dynasty lower-bound projection after resolving execution-time holder `japanese_yamato_30` and its explicit valid dynasty `japanese_yamato`.
- Direct prestige replay records only `dynasty_prestige_level >= 9`, preserves the complete raw body, and reduces opaque title states from 14 to 13 without generalizing arbitrary `while` execution or certifying an unrelated character warning.
- The exact two-field `d_laamp_henry_of_skalitz` historical-adventurer body reuses the existing initialization and `adventurer_creation_reason=flag:historical` projections after proving its holder, law, helper, and package dependencies.
- Henry replay emits no synthetic destruction event because that field is absent; its separate declaration remains authoritative. The warning clears, reducing opaque title states from 13 to 12.
- The Yamato prestige audit event now carries its actual minimum level 9 rather than the helper-family floor 5.
- The exact `k_chrysanthemum_throne` `ceremonial_title = title:e_japan` body reuses the title-variable projection with `value_kind=title` after resolving the target and installed title-scope consumers.
- Mixed and unresolved ceremonial-title bodies remain opaque. At parser `1.16.0`, the overall opaque-title count stayed 12 because `k_chrysanthemum_throne` retained separate Royal Court and law-plus-destruction effects.
- All 58 repository tests pass. The Reference Inspector displays `ceremonial_title=title:e_japan` from declaration 16411 while retaining the title's unrelated history warning.
- All 12 remaining title rows and 13 declarations are classified in `Docs/remaining_title_history_review.md`; strict historical-state completeness is accepted in `Docs/architecture_decision_001_baseline_completeness.md`.
- Durable `reference.character_baseline_court_states` storage now owns one court-state row per baseline character, with independently nullable court-language and court-type IDs, effective dates, and source declaration orders.
- Durable `reference.character_baseline_languages` storage now owns one row per baseline character and language, with explicit knowledge kind, effective date, source group/declaration provenance, and validation state.
- Snapshot-scoped `reference.languages` and `reference.culture_native_languages` catalogs preserve all 91 installed language definitions and all 244 culture-native references with source coordinates; zero native references are unresolved.
- Character parser `1.5.0` materializes 71,121 native-language rows for all 71,121 baseline characters with non-null culture IDs. Every row resolves through the grounded culture mapping, and native-only replacement preserves separately owned history-granted knowledge.
- Title-history parser `1.17.0` materializes 11 adjudicated court-state rows at 867, including proven court fields embedded in mixed bodies, while binding every field to its execution-time holder, effective date, and declaration order.
- Four complete court-only declarations normalize; mixed and holder-language-learning bodies retain warnings after their proven court fields are projected. `k_balhae` remains wholly excluded at this parser milestone pending the later culture-versus-court evidence reconciliation.
- Opaque title states fall from 12 to 9. All 62 repository tests pass, and the candidate remains unpromoted with `historical_state_complete=false`.
- Title-history parser `1.18.0` replays all five exact conditional `learn_court_language_of = this` branches against durable baseline language knowledge. Boris learns Greek, Louis II and Lothair II learn High German, Umar I Habbari learns Arabic, and Tajik Nasr's Iranian branch records an already-native no-op.
- Four `history_granted` rows retain their effective dates and title-declaration provenance; reload ignores and replaces stale title-history-owned learned rows idempotently. Opaque title states fall from 9 to 4 while `k_balhae` remains excluded.
- Title-history parser `1.19.0` fully replays `k_chrysanthemum_throne` declaration `16444` as an additive `single_heir_succession_law` operation plus a date-matched All Under Heaven no-op. Both events and the active law retain declaration provenance.
- The raw declaration remains preserved, two reloads are idempotent, and altered title/body order remains opaque. Opaque title states fall from 4 to 3; all 63 repository tests pass without promotion.
- Title-history parser `1.20.0` fully replays `e_japan` declaration `15088` as its holder-bound Chinese court assignment plus `administrative_ui_special_title=title:k_chrysanthemum_throne` under reviewed Royal Court and All Under Heaven evidence.
- Both events and the durable title variable retain declaration provenance; no personal Chinese knowledge is inferred. Wrong-title and reordered bodies remain opaque, two reloads are idempotent, and opaque title states fall from 3 to 2 with all 64 tests passing.
- Durable `reference.title_baseline_state_faiths` storage now owns one administrative state-faith row per baseline title, with explicit snapshot/faith identity, effective date, source group/declaration provenance, validation state, and enforced title/faith foreign keys.
- The candidate database is bootstrapped with zero state-faith rows. Parser `1.20.0`, readiness report `3e00ddd4-b439-4a00-b1dd-c84be7d31102`, both opaque title warnings, candidate statuses, false historical completeness, and zero supported baselines remain unchanged; all 65 tests pass.
- Title-history parser `1.21.0` fully replays exact `e_byzantium` declaration `1028`: resolved holder `70490` retains Intrigue Court, the title gains durable Orthodox administrative state faith, and the no-Roads-to-Power feudal/law fallback is recorded as inactive under the reviewed installed package.
- State faith remains separate from holder `70490`'s source-derived personal faith. Exact wrong-title and non-administrative cases remain opaque, two reloads are idempotent, and opaque title states fall from 2 to only `k_balhae`; all 66 repository tests pass.
- Title-history parser `1.22.0` replays exact `k_balhae` declaration `27271` as holder `balhae_dae_12`'s Chinese court language effective `0867-01-01`, preserving the effective date required by the observed five-year adoption lock while leaving Tungusic cultural language and personal language knowledge unchanged.
- Same-source wrong-title, wrong-date, altered-language, unresolved-language, holder-missing, and package-missing cases remain opaque. Two reloads are idempotent; declaration `27271` normalizes, title warnings fall from 1 to 0, and all 67 repository tests pass.
- Character-history parser `1.6.0` implements the reviewed Lope adjudication without a general precedence rule. It preserves both exact blocks and all 16 declarations, labels the Castilian copy `reviewed_winner` and the Basque copy `reviewed_superseded`, and materializes Castilian with all consensus identity/lifecycle fields intact.
- Exact altered blocks return to unresolved conflict handling and unrelated duplicates remain untouched. Character review falls from 109 to 108 subjects, holder validations remain warning-free, and all 68 repository tests pass.
- Duplicate character `bobo0050` is internally deterministic: Yama of `bobodyn005` owns `bobo0050` and completes the `c_loropeni` succession, while Labidiedo of `bobodyn006` is the missing `bobo0060` already named by the `c_nyene` succession.
- Character-history parser `1.7.0` preserves both installed `bobo0050` blocks and all 14 declarations, labels Yama `reviewed_winner`, labels Labidiedo `reviewed_corrected`, and materializes valid canonical states for both `bobo0050` and `bobo0060`.
- Exact operation/path/order certification and the absence of an independent `bobo0060` are required. Altered or competing evidence fails closed; all 4,434 holder validations remain valid, character review falls from 108 to 107 opaque-only subjects, and all 69 repository tests pass.
- The 107 opaque character states reconcile to 157 baseline-effective effect declarations: 36 already-normalized declarations and 121 preserved declarations across 64 opaque structural shapes. Every warning subject and all multi-declaration overlaps are accounted for in `Docs/character_history_opaque_inventory.md`.
- No blanket exception is supportable. Complete language-only bodies are the smallest replayable family because durable provenance-bearing character-language storage and culture-native-language mappings already exist; mixed language bodies remain blocking.
- Character-history parser `1.8.0` normalizes all 12 complete language-only bodies from shapes O03 and O10, resolving their culture targets through grounded native-language mappings and materializing 15 `history_granted` rows for 12 characters.
- Character-history grants replace only their own source rows, preserve native and title-history knowledge, and obey the baseline cutoff. Mixed language bodies remain wholly preserved; opaque character states fall from 107 to 95, all 4,434 holder validations remain valid, and all 71 repository tests pass.
- Nickname semantics are resolved as scalar latest-event state: later sets replace the active nickname and `remove_nickname = yes` clears it, while every set/clear remains append-only provenance. All 15 warning-linked keys resolve uniquely to installed definitions and English localization.
- The 16 warning-linked direct-child assignments are disjoint from 104 baseline-effective direct assignments already preserved without warnings. A complete replay must cover all 120 baseline characters, use one chronology across both syntax forms, and never descend into conditional or random bodies.
- The nickname review is evidence-only in `Docs/character_history_nickname_review.md`; parser `1.8.0`, the 95 warnings, current readiness report, candidate statuses, false historical completeness, and zero supported baselines remain unchanged.
- Durable nickname storage now separates snapshot-scoped definitions, append-only character set/clear events, and sparse scalar baseline state. Composite keys retain source operation identity, set/clear checks enforce nullable nickname semantics, and same-schema foreign keys bind localization, nickname, baseline character, and exact event provenance.
- The candidate schema bootstrap created zero nickname catalog, event, and state rows. Backup `ck3tracker_v2.before-nickname-schema.20260901-201938.duckdb` precedes the additive bootstrap; all 72 repository tests pass without changing parser `1.8.0`, the 95 warnings, readiness, or promotion state.
- `k_chrysanthemum_throne` is a functional ceremonial kingdom beneath `e_japan` during fractured imperial authority, not disposable structural noise. Nonselectability applies only to geographic start selection; observed 867 evidence confirms its protected Tenno role and Male Preference Primogeniture succession.
- A full documentation consistency pass found no broken relative Markdown links or stale current parser, readiness-report, and opaque-count claims; archived B001 and deferred design tasks are explicitly non-authoritative.

## Current Evidence

- Latest readiness report: `ck3_1_19_0_6_867:readiness:4f2d5916-7cf6-40fc-b7f5-49df4d0c0201`.
- Report evidence status: `current`, with ten parser bindings and both installed EP3 helper definitions bound to title-history evidence.
- Report status: blocked, with 1 blocking, 2 accepted-exception, 1 informational, and 21 passed findings.
- Snapshot status: `candidate`.
- Baseline status: `candidate`.
- `historical_state_complete`: `false`.
- `app.supported_baselines`: zero rows.
- Holder validation: all 4,434 rows valid, including one reviewed runtime adjudication.
- Root backups exist before each destructive candidate reload.

## Known Blockers

- Title history has zero baseline warning states; its readiness finding passes.
- 95 character states contain baseline-effective opaque effects.
- No production atomic promotion service exists.

## Deferred And Superseded Work

- B001 ruler-memory ingestion is preserved at `Docs/build_history/B001-ruler-memory-ingestion.md`; its Imports next action is suspended, not current.
- Holdings, Bronze observation, dashboard, and tier roadmaps in architecture and planning documents are historical or long-range guidance unless activated here.
- The old permanent 867-only product decision is superseded. 867 is the first candidate date profile, not a permanent product limit.
- Do not promote or resume product feature work from an older document.

## Next Exact Action

Implement only candidate nickname-catalog ingestion. Parse every top-level installed definition under `common/nicknames/*.txt`, applying documented `is_bad = no` and `is_prefix = no` defaults, and resolve each nickname ID through the existing snapshot-scoped English localization catalog. Preserve raw definitions, definition coordinates/order, localization coordinates, source hashes/manifests, parser version, and validation status in `reference.nicknames`.

Use a dedicated `installed_nicknames@1.0.0` parser run and make it an explicit required readiness evidence group. Reject duplicate IDs, missing or duplicate resolved English localization, malformed boolean fields, unknown snapshots, and promoted snapshots before replacement. Replace only the target candidate snapshot's nickname rows and manifests in one transaction; rollback must preserve the prior catalog.

Add focused exact/default/explicit-flag, unresolved-localization, duplicate-ID, promoted-snapshot, rollback, provenance, and repeated-load tests. Back up the root database, load the complete installed catalog, audit all 683 definitions and the 63 baseline-used keys, then refresh readiness without changing character parser `1.8.0`, character declarations/states, warning count, candidate status, or promotion state.

Target files:

- `logic/nickname_catalog_loader.py`
- `logic/promotion_readiness_service.py`
- `tests/test_nickname_catalog_loader.py`
- `tests/test_promotion_readiness_service.py`
- `Docs/current_build.md`
- `Docs/changelog.md`

Do not combine character nickname event replay, baseline nickname materialization, warning reduction, Reference Inspector UI, or promotion into this slice.

`k_balhae` is reconciled semantically. Installed culture defines Balhae with Tungusic language from its year-700 creation; installed title history separately assigns Chinese to King Geon-hwang's court on `0867-01-01`; and the observed Royal Court screen confirms Chinese at the exact baseline. The culture-panel tooltip blocks `Adopt Tungusic Court Language` until `0872-01-01`, proving the initial Chinese-to-potential-Tungusic direction and the standard 1,825-day adoption cooldown. The game-start tributary setup independently makes Balhae a tributary of Tang. The court row's effective date therefore remains supported baseline state; developer-reported post-start complexity does not change these two distinct baseline language dimensions.

`k_bengal` is resolved semantically: its 855 history initializes Narayanapala's Pala Kingdom with `court_scholarly`, and the observed 867 Royal Court screen confirms a Scholarly Court. Whether to project it remains a baseline-scope decision, not a parser-meaning ambiguity.

`k_bulgaria` is resolved semantically: its 852 history gives Boris's court Greek as its language and teaches Boris that court language when he does not already know it. Bulgarian culture's native language is Slavonic; the scripted transition to South Slavic occurs later under Simeon in 893.

`k_italy` is resolved semantically: its 855 history gives Louis II's court High German as its language and teaches the French ruler High German when needed. The source explicitly presents close German ties as the basis for this historically uncertain assignment.

`k_lotharingia` is resolved semantically: its 855 history uses High German as the living substitute for Old Frankish and teaches it to French Lothair II when needed.

`k_silla` is resolved semantically: its baseline-date history gives King Eung-ryeom's court Chinese as its language because of Chinese bureaucratic and literary influence. Eung-ryeom is a native Korean speaker, and this effect contains no holder-language learning operation.

`k_sindh` is resolved semantically: its 866 history gives Umar I Habbari's court Arabic as its language and teaches the native Vrachada-speaking ruler Arabic when needed. The same block's ahistorical clan government is already projected separately.

`k_transoxiana` is resolved semantically: its 864 history gives Nasr's court Iranian as its language. Nasr is Tajik and natively speaks Iranian, so the conditional holder-learning branch is a no-op; clan government is already projected separately.

`k_viet` is resolved semantically: its 866 history gives Gao Pian's Jinghai Circuit a Chinese court language. Gao Pian is Han and natively speaks Chinese; celestial government and the `h_china` liege are already projected separately.

Do not combine character replay, opaque-effect reclassification, promotion, dashboard work, or journal work into this slice.

## Acceptance Checks

- All installed nickname definitions load exactly once with defaulted or explicit flags, English labels, raw definitions, source coordinates, and bound manifests.
- Every nickname key used by baseline direct and reviewed effect-wrapped assignments resolves in the catalog.
- Invalid input and promoted-snapshot attempts roll back without partial replacement.
- Repeated candidate load is idempotent and the fresh readiness report binds `installed_nicknames@1.0.0` with all manifests current.
- Character parser remains `1.8.0`, character nickname event/state tables remain empty, and opaque character warnings remain 95.
- `app.supported_baselines` remains empty.
- Snapshot and baseline remain candidate with `historical_state_complete=false`.

## Resume Note

Start a future chat with:

```text
start build
```

Read this file first, verify its repository and database claims, and execute only `Next Exact Action` unless the user changes scope.
