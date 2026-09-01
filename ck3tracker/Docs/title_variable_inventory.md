# Title Variable Inventory

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Inventory date: 2026-08-29
- Parser introducing this projection: `installed_title_history` `1.16.0`; current parser: `1.21.0`

## Ceremonial Title Evidence

The one baseline-effective exact body is declaration 16411 on `k_chrysanthemum_throne` at `0500-01-01`, from `history/titles/e_japan.txt` lines 2050-2055:

```text
effect = {
    set_variable = {
        name = ceremonial_title
        value = title:e_japan
    }
}
```

`e_japan` resolves uniquely as a valid installed empire in the same baseline. Installed interactions, triggers, on-actions, events, and scripted effects test, dereference, dynamically set, and remove `var:ceremonial_title` as a title scope. The history declaration therefore establishes a durable title-scoped reference; it does not establish the future runtime lifetime of that variable. The reference links the kingdom-tier ceremonial throne back to the Japanese empire; `e_japan` separately stores the throne as its `administrative_ui_special_title`.

A second occurrence, declaration 14408 on `k_yongson_throne` at `1170-09-02`, is post-baseline and mixed with `add_title_law` and a Royal Court conditional. It remains preserved as a complete body.

## Replay Contract

Parser `1.16.0` accepts only an effect body containing one `set_variable` block with ordered fields `name` and `value`, exact name `ceremonial_title`, and a literal `title:<id>` value resolving in the installed baseline title catalog. Added, reordered, malformed, nonliteral, or unresolved fields remain opaque.

The accepted declaration creates one `reference.title_baseline_variables` row with `value_kind = title`, `text_value = e_japan`, its effective date, and source declaration order. It also emits one provenance-linked `title_variable_set` event. The raw declaration remains unchanged.

Parser `1.20.0` also certifies exact `e_japan` declaration `15088` as an ordered Chinese Royal Court branch followed by a reviewed All Under Heaven branch setting `administrative_ui_special_title=title:k_chrysanthemum_throne`. The second durable title-reference row and both court/variable events retain declaration `15088`; the body creates no personal language knowledge.

The current opaque-title count is 2 after separate exact replay of the Chrysanthemum Throne's court and law bodies and Japan's administrative UI variable. Snapshot and baseline remain candidates, `historical_state_complete` remains false, and `app.supported_baselines` remains empty.

The throne is nonselectable only under geographic start-location rules because it lacks a canonical de jure chain. It remains functional title state: installed ceremonial-liege logic uses its holder as the Tenno beneath fractured imperial authority, and observed 867 runtime evidence shows its guaranteed protection and Male Preference Primogeniture succession.
