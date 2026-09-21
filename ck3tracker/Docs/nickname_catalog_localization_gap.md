# Nickname Catalog Localization Gap

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Installed build: CK3 `1.19.0.6`, Steam build `23530548`
- Review date: 2026-09-02
- Subject: `nick_the_bastard_rumoured`

## Finding

The installed nickname catalog contains 683 unique top-level definitions across 10 `common/nicknames/*.txt` files. Exactly 682 definition IDs resolve through the snapshot-scoped English localization catalog. The sole unresolved definition is:

```text
common/nicknames/00_nicknames.txt:338
nick_the_bastard_rumoured = { is_bad = yes }
```

The definition is structurally valid and unique. It explicitly sets `is_bad = yes` and defaults `is_prefix = no` under the installed nickname contract.

## Installed Evidence

- No `nick_the_bastard_rumoured` localization key exists in any installed localization language.
- No installed script outside `common/nicknames/00_nicknames.txt` assigns, queries, or otherwise references the key.
- No parsed character-history declaration in the candidate snapshot contains the key.
- `nick_the_bastard` is a separate adjacent definition and resolves to English label `the Bastard` at `localization/english/nicknames_l_english.yml:36`.
- No installed alias, fallback declaration, or engine contract proves that `nick_the_bastard_rumoured` inherits the `nick_the_bastard` label. Similar naming is not sufficient evidence for substitution.

## Consequence

The current ingestion acceptance contract is contradictory for this installed package: it requires all 683 definitions to load with resolved English labels while also requiring missing localization to reject the load. A loader cannot satisfy both conditions without inventing a label, silently omitting an installed definition, or weakening validation.

No such inference is accepted. Candidate catalog ingestion remains blocked before mutation. No nickname loader, parser run, source manifest, catalog row, readiness report, or character state changed during this investigation.

## Decision

Preserve `nick_the_bastard_rumoured` as an exact reviewed non-localized orphan. Its catalog row retains the stable ID, flags, raw definition, and definition provenance while localization key, display name, and localization coordinates remain null. Its validation status is `reviewed_orphan`, not `valid`.

This does not create a historical-state exception. ADR-001 requires deterministic projection of baseline-effective operations; all 63 nickname keys used by direct or reviewed effect-wrapped operations at the 867 baseline resolve exactly to English localization. The orphan has no installed consumer and no character-history operation, so it contributes no baseline state to project.

The exception is fail-closed and package-specific:

- Recognize only exact stable ID `nick_the_bastard_rumoured` with the reviewed Scribe definition provenance and `is_bad = yes`, `is_prefix = no` semantics.
- Do not alias it to `nick_the_bastard` and do not invent user-facing text.
- Show the stable ID only in diagnostic or administrative surfaces; it is not eligible for a resolved display label.
- Any installed use, baseline use, newly available localization, changed definition, duplicate declaration, or additional unresolved nickname ID invalidates the recognizer and blocks catalog replacement pending review.
- Readiness may report the exact unused orphan informationally, but every baseline-used nickname ID must remain fully localized and valid.

This policy preserves all 683 installed definitions, distinguishes 682 localized rows from one reviewed orphan, and keeps strict baseline completeness tied to the 63 active keys without silently narrowing or fabricating evidence.