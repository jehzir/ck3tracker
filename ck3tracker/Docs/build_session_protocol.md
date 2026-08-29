# Build Session Protocol

This project is developed across multiple AI chat sessions and agents. Chat context is temporary; this file-based protocol is the durable handoff.

## Session Commands

Use these phrases literally in chat:

```text
start build
```

The agent must:

1. Read `Docs/current_build.md` before exploring broadly.
2. Inspect `git status`, the latest commit, and the listed handoff files.
3. Confirm the current build ID and objective.
4. State the immediate next action and the cheapest validation check.
5. Work only on the current build objective unless the user changes scope.

```text
end build
```

The agent must:

1. Stop implementation work unless the user explicitly asks to continue.
2. Run the narrowest available validation for the completed slice.
3. Record changed files, tests, commits, unresolved issues, and the next exact action in `Docs/current_build.md`.
4. Record any dirty user files without reverting them.
5. Leave the repository in a resumable state.

## Current Build File

`Docs/current_build.md` is the canonical handoff document. It is not a diary of every chat message. It contains only the information needed to resume safely.

### Authority And Precedence

Use this order when instructions or status claims disagree:

1. The user's explicit instruction in the current session.
2. Observable worktree, database, source-manifest, and executable-validation state.
3. `Docs/current_build.md` for the sole current objective and next exact action.
4. `Docs/game_update_protocol.md` for snapshot, update, validation, and promotion procedure.
5. `Docs/architecture.md` for durable system boundaries and invariants.
6. `Docs/future_plan.md` for product tiers and long-range sequencing.
7. Changelog, project plan, decisions, inventories, registries, build history, and prior transcripts as historical or advisory evidence.

No document other than `Docs/current_build.md` may define an authoritative current priority, return point, resume prompt, or next action. Imperative roadmap language in lower-precedence documents is historical unless the current build explicitly activates it.

The word `manifest` has three distinct meanings in this repository:

- `Docs/current_build.md`: the execution manifest and sole resumable path.
- `source.source_files` in the root DuckDB: generated installed-file evidence manifests.
- `Docs/source_table.json`: an advisory source-to-table planning registry.

Never use the planning registry or an older roadmap as a substitute for the execution manifest.

Every build checkpoint must include:

- build ID
- build name
- status
- objective
- user decisions
- repository commit
- working-tree changes
- files touched
- validation performed
- known defects
- unresolved decisions
- next exact action
- resume instructions

## Build IDs

Use a monotonic ID with a short name:

```text
B001-ruler-memory-ingestion
B002-bronze-barony-observation
B003-county-recovery
```

The build name should describe the implementation slice, not the chat title. Chat titles may be long, accidental, or unavailable after compaction.

## Suspension And Agent Changes

A session is resumable when `Docs/current_build.md` contains:

- a committed checkpoint or an explicit uncommitted state
- the exact files that matter
- a passing or failing validation result
- one next action

A new agent must not infer completion from the last assistant message alone. It must trust, in order:

1. Current working tree and actual files
2. `Docs/current_build.md`
3. Git commit history
4. Validation output recorded in the handoff
5. Prior chat transcript, only for additional context

If the working tree disagrees with the handoff, the new agent must report the discrepancy before editing.

## Commit Rules

- Commit after each coherent, validated slice.
- Do not commit user-pasted source or memory content without explicit permission.
- Never revert dirty files that are not part of the current agent's work.
- Use the commit hash in the handoff.
- A clean worktree is preferred, but a dirty user file is a valid suspended state when documented.

## Checkpoint Format

Use this compact structure in `Docs/current_build.md`:

```markdown
# Current Build

- Build ID:
- Build name:
- Status: `active` / `suspended` / `complete` / `blocked`
- Last updated:

## Objective

## User Decisions

## Repository State

- Branch:
- HEAD:
- Worktree:

## Completed

## Files That Matter

## Validation

## Known Issues

## Next Exact Action

## Resume Note
```

## Compaction Rule

When a chat becomes large, do not try to preserve the whole conversation in the next prompt. End the build first, update `Docs/current_build.md`, and start the next chat with:

```text
start build
```

The next agent should resume from the handoff and verify the repository rather than reconstructing the entire conversation.

## Scope Changes

If the user changes direction mid-build:

1. Mark the current build `suspended`.
2. Record what is complete and what remains.
3. Create a new build ID for the new objective.
4. Do not silently replace the old next action.

This preserves multiple unfinished threads without confusing them.
