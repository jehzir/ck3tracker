# Duplicate Character 71419 Adjudication

- Snapshot: `ck3_1_19_0_6_build_23530548`
- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Character: `71419`, Lope
- Decision date: 2026-09-01
- Decision: use `castilian` culture; preserve both raw blocks
- Implemented: character-history parser `1.6.0`

## Conflict

The installed files contain two otherwise identical blocks for Lope:

| Source block | Source | Culture | Shared identity |
|---:|---|---|---|
| 2920 | `history/characters/basque.txt:1-14` | `basque` | Lope, dynasty 681, Catholic, parents 71410/71411, born 1208-01-01, died 1235-01-01 |
| 9008 | `history/characters/castilian.txt:1682-1695` | `castilian` | Lope, dynasty 681, Catholic, parents 71410/71411, born 1208-01-01, died 1235-01-01 |

Only `culture_id` conflicts. Lope is not born at the 867 baseline and is neither an 867 title holder nor a featured ruler, but strict source identity still requires an explicit winner.

## Internal Evidence

The Castilian block belongs to one contiguous paternal family sequence. Father `71410`, Sancho, is Castilian, belongs to dynasty 681, and holds Leonese titles from 1188 until his death in 1220. Lope's siblings `71412` (Diego) and `71418` (Maria) are also children of Sancho and Teresa and are both Castilian. The following descendants in the same Ivrea sequence are Castilian as well.

Dynasty 681 is the valid installed `dynn_Ivrea` definition. The title-history comments identify Sancho and his heirs as the Borgona line in Leon. Lope's Castilian block is therefore structurally owned by the same source that owns his father, siblings, dynasty sequence, and paternal title succession.

The Basque placement has a real genealogical basis but weaker character ownership. Mother `71411`, Teresa, is Basque and belongs to dynasty 778; her father is in the Basque file. Lope's block is isolated at the beginning of that file, while his mother appears much later in her own maternal family sequence. No sibling is duplicated there and no Basque title-history row names Lope as holder.

## External Evidence

Permanent Wikipedia revision `1369933120` for Diego Lopez II de Haro records Teresa Diaz de Haro as a daughter of the Haro lord of Biscay and the wife of Infante Sancho of Leon. This corroborates the mixed parental context: Teresa supplies the Haro/Biscay maternal link, while Lope belongs to Sancho's Leonese household. It does not directly assign Lope a culture and is supporting rather than controlling evidence.

Evidence URL: `https://en.wikipedia.org/w/index.php?title=Diego_L%C3%B3pez_II_de_Haro&oldid=1369933120`

## Decision

Adjudicate `castilian` as Lope's culture. The decision is not based on later filename precedence. It follows source ownership and family consistency: the Castilian block is embedded in Lope's paternal household and sibling sequence, whereas the Basque block is an isolated maternal-file duplicate.

Parser `1.6.0` preserves both source blocks and declarations, marks the Castilian block as `reviewed_winner`, marks the Basque block as `reviewed_superseded`, and materializes only the winner's culture. All seven consensus identity/lifecycle fields remain unchanged. Exact altered blocks fall back to unresolved conflict handling; no general duplicate precedence was added. `bobo0050` and opaque character effects remain outside this adjudication.