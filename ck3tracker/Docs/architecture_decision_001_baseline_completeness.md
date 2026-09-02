# ADR-001: Strict Baseline Historical-State Completeness

- Status: accepted
- Date: 2026-08-31
- Scope: promoted CK3 reference baselines

## Decision

A promoted baseline must project every baseline-effective operation that changes supported game state, even when the current journal UI does not yet consume that field. This includes court language, court type, administrative state faith, holder language knowledge, title-scoped variables, and title laws.

`historical_state_complete = true` means the baseline's effective historical operations have been deterministically evaluated and represented in durable typed state. Raw preservation alone is not completion. Mutable state is still required at the starting baseline because it determines the player's initial conditions.

An accepted exception is limited to an operation proven inactive for the reviewed build and baseline, a true no-op, or source behavior that cannot represent persistent state. Lack of a current UI consumer is not an accepted-exception basis.

## Consequences

- The 12 title rows in `Docs/remaining_title_history_review.md` remain blocking until their complete baseline-effective bodies are projected or proven inactive.
- Royal Court feature/package evidence must be reviewed before its conditional branches can be replayed.
- Court language and court type require durable baseline projections.
- Conditional `learn_court_language_of` results require durable character-language projections and exact branch evaluation.
- Mixed bodies such as `e_byzantium`, `e_japan`, and `k_chrysanthemum_throne` remain blocking until every active state change in the body is represented.
- `k_balhae` is complete at parser `1.22.0`: its runtime-confirmed Chinese court language retains effective-date provenance while its independently grounded Tungusic cultural language remains separate.
- Promotion readiness must report unsupported active state as blocking rather than silently narrowing completeness to current product consumption.

## Rejected Alternative

The journal-required policy would certify a baseline while known starting gameplay state remained unprojected. That would make `historical_state_complete` dependent on the current UI surface, force later semantic expansion when journal features consume court state, and weaken reproducibility across application versions.