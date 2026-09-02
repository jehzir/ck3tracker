# Duplicate Character bobo0050 Adjudication

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Raw duplicate ID: `bobo0050`
- Decision date: 2026-09-01
- Decision: Yama owns `bobo0050`; Labidiedo's block has the mistyped identifier and is intended to define `bobo0060`
- Implemented: character-history parser `1.7.0`

## Conflict

The installed `history/characters/bobo.txt` file contains two different fictional characters under `bobo0050`:

| Source block | Source lines | Name | Dynasty | Faith | Father | Life |
|---:|---:|---|---|---|---|---|
| 6148 | 647-659 | Yama | `bobodyn005` (`dynn_Boura`) | `west_african_pagan` | `bobo0049` | 1186-1244 |
| 6158 | 781-793 | Labidiedo | `bobodyn006` (`dynn_Wule`) | `ashari` | `bobo0059` | 1193-1254 |

Only culture agrees. Display name, dynasty, faith, father, birth date, and death date describe separate people, so source position cannot identify a winner.

## Internal Evidence

The first block completes the contiguous `bobodyn005` ruler sequence for `c_loropeni`. Characters `bobo0041` through `bobo0049` all belong to that dynasty, and Yama is explicitly the son of `bobo0049`. Title history transfers `c_loropeni` from `bobo0049` to `bobo0050` on `1210-01-01`, exactly the father's death date. Yama therefore owns stable ID `bobo0050`.

The second block completes the immediately following `bobodyn006` ruler sequence for `c_nyene`. Characters `bobo0051` through `bobo0059` form an uninterrupted parent chain, and Labidiedo is explicitly the son of `bobo0059`. Title history transfers `c_nyene` from `bobo0059` to `bobo0060` on `1216-01-01`, exactly the father's death date. The character file has no `bobo0060` definition, and the numeric sequence jumps directly from the second raw `bobo0050` block to `bobo0061`, which begins `bobodyn007` and the next county chain.

Repository-wide installed-source search finds `bobo0060` only in the `c_nyene` holder declaration and finds no other reference that competes with this interpretation. The two matching parent-to-successor transitions, dynasty boundaries, and consecutive stable-ID ranges make the intended identifier deterministic.

## Decision

Adjudicate Yama of `bobodyn005` as canonical `bobo0050`. Treat the exact Labidiedo block from source block 6158 as a source typo whose intended canonical identity is `bobo0060`.

Parser `1.7.0` preserves both raw source blocks and all 14 declarations under their installed source identifier. Source block 6148 is `reviewed_winner`; source block 6158 is `reviewed_corrected` and alone materializes as canonical `bobo0060`. Both canonical states are valid, while raw block order, lines, scripts, hashes, and operation provenance remain unchanged.

Certification requires the complete exact operation signatures in their installed path and order plus the absence of an independent `bobo0060` definition. Any altered identity, relationship, lifecycle, source path, block order, or competing `bobo0060` definition restores unresolved duplicate handling. This is a one-record correction, not a general numeric-sequence or later-position precedence rule.

Backup `ck3tracker_v2.before-character-history-1.7.0.20260901-192150.duckdb` precedes the candidate-only reload. Fresh readiness report `ck3_1_19_0_6_867:readiness:4dcc0a9a-515e-465f-9658-1ee8c6cc368f` confirms zero duplicate IDs and 107 baseline-effective opaque character states. No promotion state changed.