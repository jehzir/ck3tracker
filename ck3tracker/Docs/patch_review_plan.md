# September 30 Patch Review Plan

## Purpose

Review the first CK3 build installed after Scribe build `23530548`, preserve the frozen Scribe evidence, and create a separate candidate snapshot for the released patch. This plan does not authorize pre-release parser work, promotion, or mutation of the Scribe snapshot.

## Credit Budget

Budget against observed credit consumption in the model picker or usage meter, not assumed vendor multipliers.

| Work | Model selection | Credit ceiling |
|---|---|---:|
| Pre-release checklist and synthetic diff rehearsal | Auto | 300 |
| Build identity, backup, scan, and mechanical tree diff | Auto | 450 |
| Semantic source, DLC, wiki, and warning-ledger review | GPT-5.6 Sol when prompted | 900 |
| Bounded parser and service changes | Auto; GPT-5.6 Sol only when prompted | 450 |
| Validation and promotion-readiness review | Auto for execution; GPT-5.6 Sol when prompted for final judgment | 300 |
| Unallocated contingency reserve | GPT-5.6 Sol only after an explicit escalation prompt | 600 |

Preserve at least 2,700 credits until a different Steam build is installed. Never spend the reserve merely to eliminate an unresolved finding; retain `review_required` and stop instead.

## Model Policy

Select **Auto** for the patch workflow by default. GitHub Copilot Auto with task optimization evaluates task complexity and current model health, routes straightforward work to efficient models, and can reserve stronger reasoning models for harder work. Paid Copilot plans receive the documented 10% model-cost discount while using Auto.

Keep Auto selected for exact inventory, build detection, backup, scanning, SQL reporting, path classification, deterministic diffs, documentation, test execution, scoped Python services, DuckDB schema additions, fixtures, loader routing, and straightforward parser maintenance.

Manually select GPT-5.6 Sol only after the runbook or active agent explicitly says `SWITCH TO GPT-5.6 SOL`. Use it for:

- changed Clausewitz control flow or scope semantics;
- DLC-versus-free-patch attribution;
- dependency-sensitive carry-forward of the frozen 83 declarations;
- title hierarchy or stable-ID contradictions;
- ambiguous source/wiki/runtime evidence;
- final promotion recommendation.

Do not use GPT-5.6 Sol for hashing, scans, SQL counts, ordinary test repairs, formatting, or known-pattern loader edits. Escalate only after Auto states the exact ambiguity and evidence already checked. Allow at most two Sol attempts per semantic issue; then classify it `review_required`.

Switch models at a task boundary in a new chat or clearly separated review session. GitHub documents that switching models mid-session can add cache-related cost without enough improvement in quality. After the Sol review produces a bounded decision, start or resume a separate Auto implementation session with that decision as evidence.

The agent must announce model transitions explicitly:

- `STAY ON AUTO`: continue mechanical, implementation, or validation work.
- `SWITCH TO GPT-5.6 SOL`: begin a bounded semantic or final-review task and state its credit ceiling.
- `RETURN TO AUTO`: the premium judgment is complete; perform implementation or tests in a separate Auto session.

## Pre-Release Work

The Scribe snapshot remains frozen. Allowed work is limited to read-only rehearsal against synthetic trees and temporary databases, plus documentation and checklist refinement.

Before release, prepare or verify:

1. A deterministic full-tree comparison that classifies `unchanged`, `metadata_only`, `content_changed`, `added`, `removed`, and unambiguous one-to-one `moved` files.
2. Loader ownership rules based on parser names and source roots, with unknown changed semantic paths treated as blockers.
3. Read-only checks proving frozen scan `game-tree:07f87b79-5b41-4ad6-a7f6-6c62ad32994f`, manifest SHA-256 `790a4cb6910ca603d0a5791c4380a14983a6a96e4ca426fb0f23440cc703257e`, and warning ledger SHA-256 `271d4154b1b050d2f9e302c0e5e53ce56793f5ab817d65983ccb29c818b286f9` remain unchanged.
4. A release checklist that includes `installed_subject_contracts@1.0.0` as a required readiness dependency. It is not currently included in the eleven-parser readiness gate and must be added before trusting a released candidate report.

Do not rescan the installed Scribe tree, refresh its readiness report, implement the frozen 70 states, edit the Reference Inspector, or promote data before the installed build changes.

## Release-Day Gates

### Gate 0: Detect The Build

Read Steam app manifest, launcher `rawVersion`, and `clausewitz_branch.txt`. If Steam build ID is still `23530548`, stop. The calendar does not activate the workflow.

### Gate 1: Protect The Database

Stop database readers. Create a repository-root DuckDB backup and verify byte length and SHA-256 equality before mutation. Any mismatch stops the run.

### Gate 2: Capture Identity

Capture the new Steam app/build ID, launcher version, branch, DLC descriptors, package presence, and released wiki permanent revisions. Conflicting or missing identity evidence stops the run.

### Gate 3: Create A New Snapshot

Create a unique candidate `reference_snapshot_id`. Never reuse, update, or relabel the Scribe snapshot.

### Gate 4: Scan And Diff

Append a second complete installed-tree scan. Retain the frozen scan unchanged. Full-outer-join normalized paths and classify every old/new entry exactly once. Content hash controls semantic change; modification time alone does not.

### Gate 5: Route Changed Sources

Map changed files to owning parser groups. Added files under semantic source roots that map to no loader are blockers. Recheck DLC metadata and descriptors before parsing gated behavior.

### Gate 6: Refresh Released Evidence

Capture permanent wiki revisions for the patch, By God Alone, DLC catalog, and changed mechanics. Mark prerelease claims `confirmed`, `changed`, `deferred`, or `unsupported`.

### Gate 7: Reparse Dependencies

Reparse only changed groups, but preserve dependency order:

1. DLC packages and feature mappings.
2. Landed titles and localization.
3. Government, culture/language, faith, dynasty, house, nickname, and subject-contract catalogs.
4. Character history and title history.
5. Bookmarks.

Add `installed_subject_contracts` to required readiness parser evidence before candidate readiness is evaluated.

### Gate 8: Compare Semantics

Compare canonical rows, stable IDs, hierarchy, and the frozen warning ledger across snapshots. Carry one of the 83 declarations forward only when character ID, effective date, operation key, raw-script hash, source dependency hashes, DLC branch evidence, and catalog dependencies remain compatible.

A structural-shape match alone is insufficient because scalar values may have changed. Classify old declarations as `exact_unchanged`, `relocated_exact`, `modified`, `removed`, or `dependency_invalidated`; classify unmatched candidate declarations as `new`.

The released candidate is not required to retain exactly 70 warning subjects or 83 declarations. Count changes are findings requiring explanation, not automatic parser defects.

### Gate 9: Validate Candidate Readiness

Generate readiness only after every changed required group has a current completed run and bound manifests. Verify title containment, stable-ID uniqueness, complete selectable title chains, holder lifecycle, DLC conditions, Bronze/journal invariance, and cross-snapshot drift.

### Gate 10: Decide, Do Not Imply, Promotion

Promotion requires zero blockers, complete provenance, `historical_state_complete=true`, an atomic promotion service, and explicit human approval. A patch review may end with `review_required`; it must not promote as a side effect.

## Model Assignment By Phase

| Phase | Selection | Required instruction |
|---|---|---|
| Gates 0-5 | Auto | `STAY ON AUTO`; prompt for Sol only if identity evidence or path ownership is genuinely ambiguous |
| Gate 6 | Auto first | `SWITCH TO GPT-5.6 SOL` only when released wiki and installed semantics disagree |
| Gate 7 | Auto | `SWITCH TO GPT-5.6 SOL` only when parser grammar or scope semantics changed materially |
| Gate 8 | Auto for exact carry-forward and tabulation; GPT-5.6 Sol for changed semantic clusters | Open a bounded Sol review session for each related cluster, then `RETURN TO AUTO` |
| Gate 9 | Auto | Run tests, audits, and readiness generation without manual premium selection |
| Gate 10 | GPT-5.6 Sol | `SWITCH TO GPT-5.6 SOL` for the final evidence and promotion recommendation only |

## Stop Conditions

Stop immediately when:

- Steam build remains `23530548`;
- backup verification fails;
- build, version, branch, DLC, or wiki evidence conflicts;
- the scanner detects links, path collisions, or files changing during hashing;
- a candidate snapshot ID collides;
- a changed semantic path has no owning loader;
- parser manifests and full-tree hashes disagree;
- required subject-contract evidence is absent from readiness;
- stable IDs, hierarchy, or selectable chains fail validation;
- Bronze or journal data changes unexpectedly;
- any candidate blocker remains unresolved;
- promotion would require bypassing the atomic service or explicit approval.

## Release Validation

Run focused comparison and changed-loader tests first, then:

```powershell
C:\Python314\python.exe -m unittest tests.test_game_tree_scanner tests.test_game_update_service
C:\Python314\python.exe -m unittest tests.test_promotion_readiness_service
C:\Python314\python.exe -m unittest discover -s tests
```

The final review must state the credits used by phase, unresolved findings, evidence retained from Scribe, evidence reopened for the new build, and an explicit `promote`, `review_required`, or `reject` recommendation.