# CK3 Tracker Daily Design Tracker

## Current Checkpoint

- Holdings opens as a realm summary.
- Holdings includes read-only Summary, Barony, County, and Duchy scopes.
- Editor is a separate scope for recording major updates.
- Editor flow is:
  1. County filter
  2. What are you editing? Barony, County, or Duchy
  3. Update style where applicable: New / Conquered or Update / Realm
  4. Target selector
  5. Scope-specific editor fields
- Barony target is shown beside the editor choice cards.
- Selected barony context appears beside `Record a major update`.
- Dark mode is preserved with DHS/USWDS-inspired accessibility patterns.
- Updates are event-point snapshots, not daily game-tick tracking.
- Current UI remains trial-backed and marked `[VALIDATED]`.

## Next Design Tasks

### 1. Extract Render Functions

Create a `render.py` layer for reusable presentation functions:

- Holdings summary
- Barony summary
- County summary
- Duchy summary
- Barony editor
- County editor
- Duchy editor
- Radio choice cards
- County and target selectors
- Summary and detail tables

Keep callbacks and data access separate from render composition.

### 2. Complete the County Editor

The County editor should support major event-point updates for:

- Control
- Development
- Popular opinion
- Culture
- Faith
- County holder
- Ownership scope
- Event date
- Event type
- Event note

The selected county should appear beside the editor heading.

### 3. Complete the Duchy Editor

The Duchy editor should support:

- Duchy selection
- Selected duchy context
- Counties held
- Required counties
- Base barony progress
- Title status
- Creation requirements
- Goal or event note
- Event date
- Event type

### 4. Make Event-Point Updates Explicit

Every editor should communicate:

```text
What changed?
When did it change?
Why did it change?
```

Do not model continuous daily updates unless the player records them.

### 5. Connect Save Actions to Trial Parquet

Persist the current trial editor values with:

- `playthrough_id`
- Scope
- Target ID
- Observed values
- Observation date
- Event type
- Notes
- Source or manual-entry marker

Preserve canonical reference data separately from observed run state.

### 6. Improve Summary-to-Editor Navigation

A summary row should open the correct editor context:

```text
Ibiza row
  -> Editor
  -> County
  -> Ibiza selected
```

The same pattern should work for a specific barony or duchy.

### 7. Accessibility and Responsive Review

Check each scope at desktop and narrow widths:

- Radio labels do not wrap unnecessarily.
- Scope choices remain understandable on one line when space permits.
- Barony target choices remain vertical and readable.
- Keyboard focus is visible.
- Dark-mode contrast remains strong.
- Tables do not create avoidable horizontal scrolling.
- Mobile layout collapses predictably.
- Controls retain stable dimensions.

## Design Rules

- Holdings summarizes.
- Editor records changes.
- Barony fields stay separate from County fields.
- Duchy fields stay separate from County and Barony fields.
- Use one clear target context at the top of an editor.
- Avoid repeating scope labels in multiple consecutive headings.
- Prefer compact aligned work surfaces over stacked cards.
- Keep the DHS/USWDS accessibility influence while preserving dark mode.
- Do not mix synthetic trial data with canonical CK3 reference data.
- Keep the current trial proof visible until the production persistence workflow is validated.

## Current Visual Reference

The Holdings Editor should read in this order:

```text
Record a major update | Selected target
County filter
What are you editing? | Update style | Target selector
Observed or base state table
Scope-specific editor
```
