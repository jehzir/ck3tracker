# Ruler Memories

A ruler-perspective memory journal for a CK3 run.

This document is intentionally narrative. It captures what the ruler remembers, believed, feared, desired, or misunderstood. It is not a complete event log. The tracker stores exact observations and transactions separately in DuckDB; this file provides the human meaning around them.

A ruler cannot remember every decision made during a lifetime. Record the decisions that changed the direction of the run, created a relationship, caused a loss, or became part of the story.

## Run Identity

- Playthrough ID:
- Ruler:
- House:
- Culture:
- Faith:
- Start date:
- End date:
- Run status: `active` / `dead` / `completed`
- Current chapter:

## How To Use This File

Use one memory entry for a meaningful moment, not every game tick.

A good memory can be:

- a decision that changed the realm
- a person who mattered
- a war won or lost
- a title gained, lost, or restored
- a betrayal, grant, marriage, or succession choice
- an unexpected event
- a mistake that looked reasonable at the time
- a small moment that became important later
- a contradiction or strange game behavior worth investigating

When exact facts are known, include them. When the ruler is interpreting events, label that interpretation clearly.

## Memory Entry Template

### Memory: [Short title]

- Memory ID:
- Game date:
- Real-world recorded at:
- Chapter:
- Location or title:
- People involved:
- Related county/barony/title IDs:
- Source: `manual_memory` / `screenshot` / `savegame_import` / `game_file_reference` / `uncertain`
- Confidence: `confirmed` / `probable` / `uncertain`

#### What Happened

Describe the visible event or decision in plain language.

#### What I Wanted

What was the ruler trying to accomplish?

#### What I Believed At The Time

Record the information, assumptions, fears, or expectations that shaped the decision.

#### The Decision

What choice was made?

#### What I Did Not Know

Capture hidden information, missing context, or facts discovered later.

#### Immediate Consequence

What changed immediately after the decision?

#### Long-Term Consequence

What changed later because of it?

#### What The Ruler Remembers

Write this in first person from the ruler's perspective.

#### What The Records Say

Keep this factual and separate from the narrative interpretation. Link to the relevant DuckDB transaction or observation when available.

#### Later Interpretation

What does the player understand now that the ruler may not have understood then?

#### Related Memories

- 

## Major Decisions

Use this compact index for decisions that shaped the run.

| Date | Decision | Goal | Result | Confidence | Related IDs |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## People Who Matter

| Person | Role or relationship | First remembered | Last known state | Why they matter |
|---|---|---|---|---|
|  |  |  |  |  |

## Places That Matter

| Place | ID | Relationship to the ruler | Important change | Related memories |
|---|---|---|---|---|
|  |  |  |  |  |

## Wars And Turning Points

| Date | War or crisis | Cause | What was at stake | Outcome | Memory ID |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## County And Barony Memories

Use this section for places that became part of the ruler's story. Detailed status values belong in DuckDB observations; this section records meaning and narrative.

### [County or Barony]

- ID:
- First known condition:
- Loss or crisis:
- What happened while absent:
- Reclaim or restoration:
- Holder resolution:
- Grant or succession decision:
- What the place means to the ruler now:

### Inferred Period: [Date range]

- Evidence:
- Likely pressures:
- What remains unknown:
- Confidence: `probable` / `uncertain`

## Contradictions And Strange Events

Record events that appear inconsistent, impossible, bugged, or difficult to interpret. These are journal investigations, not automatically accepted facts.

| Date | Event | Why it is suspicious | Evidence | Resolution |
|---|---|---|---|---|
|  |  |  |  |  |

Examples:

- a character appears as both actor and target of a scheme
- a holder changes without a visible succession or grant
- an event repeats unexpectedly
- a county or barony state conflicts with the screenshot
- an activity appears to resolve without a clear outcome

## Chapters Of The Run

### Chapter: [Name]

- Date range:
- Opening condition:
- Main ambition:
- Main threat:
- Important people:
- Important places:
- Decisions that defined the chapter:
- How the chapter ended:
- What changed in the ruler's identity:

## Character Memory Boundary

Everything below this boundary is the ruler's actual in-game memory feed. It is not an omniscient history and must not be treated as complete run data.

The character knows only what the game has placed in that character's memory. The memory feed may omit decisions, private motives, hidden schemes, unseen events, and consequences that happened outside the ruler's knowledge. It may also contain game-generated wording that is technically true but incomplete or misleading.

Rules for this section:

- Preserve the original first-person wording and dates.
- Do not add facts to a memory entry that the ruler could not know.
- Do not rewrite a memory because later evidence disproves the ruler's understanding.
- Store screenshots, savegame facts, and DuckDB observations separately as external evidence.
- Use later journal analysis to compare character memory with the factual record, never to overwrite the memory.
- Treat this section as the ruler's subjective continuity, not the complete history of the run.

The pasted character-memory feed begins below.

---

17 June, 916
My holy war against Touma ended in victory.

9 June, 916
I imprisoned Touma Rustamid.
My son, Achan V, was born to my wife, Gisela.
13 February, 916
I called a Priscillianist holy war for the County of Almeria against Touma Rustamid.

2 June, 915
My grandson, Achan, died from being Sickly.

17 May, 915
I became friends with Ava Zakho.

4 February, 915
My holy war against Emira Ihtizaz ended in victory.

15 June, 913
I called a Priscillianist holy war for the County of Castellon against Emira Ihtizaz of Zaragoza.

30 October, 912
My Wet Nurse, Marta, died of old age.

23 January, 911
My holy war against Touma ended in victory.

3 May, 910
I called a Priscillianist holy war for the County of Murcia against Touma Rustamid.

24 April, 909
I realized that Queen Gisela of Sardinia was my soulmate.

16 September, 908
My holy war against Sultan Ibrahim ended in victory.

16 August, 906
I called a Priscillianist holy war for the Duchy of Kroumerie against Sultan Ibrahim II of Africa.

9 October, 904
My holy war against Touma ended in victory.

25 May, 904
I defeated Touma at the battle of Ngaous.

11 May, 903
My ward, Princess Gisela II, completed her tutelage under my guidance.

9 January, 903
I called a Priscillianist holy war for the Duchy of Bejaia against Touma Rustamid.

23 October, 900
My ward, Achan II, completed his tutelage under my guidance.

8 August, 899
My twins, Gisela VI and Gisela VII, were born to my wife, Gisela.

25 January, 896
My son, Achan V, was born to my wife, Gisela.

21 January, 896
I came to King Lothaire II's defense against Mayor Adolf's attempted populist revolt of County of Aargau.

2 June, 895
I was properly crowned by Lazare as the rightful King of the Kingdom of Sardinia.

5 January, 894
My son, Achan IV, was born to my wife, Gisela.

9 October, 893
I created the Kingdom of Sardinnia.

14 June, 892
My daughter, Gisela V, was born to my wife, Gisela.

21 March, 891
My daughter, Gisela IV, was born to my wife, Gisela.

10 November, 890
I created the Duchy of Sardinia.

29 July, 889
My son, Achan III, was born to my wife, Gisela.

10 July, 888
My holy war against Captain Arzoccu ended in victory.

9 July, 888
I imprisoned Captain Arzoccu of Longbeard Band.

4 July, 888
My daughter, Gisela III, was born to my wife, Gisela.

8 May, 888
I called a Priscillianist holy war for the County of Arborea against Captain Arzoccu of Longbeard Band.

23 April, 888
My holy war against Costantzu ended in victory.

4 June, 887
I called a Priscillianist holy war for the County of Tortoli against Costantzu de Lacon.

10 May, 887
My daughter, Gisela II, was born to my wife, Gisela.

22 October, 884
My first child, Achan II, a beautiful boy, was born to my wife, Gisela.

15 January, 884
I fell in love with Queen Gisela of Sardinia.

15 January, 884
I had sex with Queen Gisela of Sardinia.

5 January, 883
I married Queen Gisela.

3 January, 883
My guardian, Tamzin, and the court of Mallorca finally acknowledged me as a full-grown man.

2 January, 883
My guardian, Marta, and the court of Mallorca finally acknowledged me as a full-grown man.

17 March, 882
My holy war against Felictu ended in victory.

9 February, 882
I became friends with Gueraua.

21 April, 881
I called a Priscillianist holy war for the County of Cagliari against Felictu de Lacon.

15 November, 878
I created the Duchy of Mallorca.

2 September, 876
I became friends with Matriarch Samee of Sardinia.

4 April, 875
I conquered the County of Gallura from Captain Arzoccu in a holy war.

3 April, 875
My holy war against Captain Arzoccu ended in victory.

2 August, 874
I called a Priscillianist holy war for the County of Gallura against Captain Arzoccu of Longbeard Band.

27 July, 869
I conquered the County of Logudoro from Captain Arzoccu in a holy war.

26 July, 869
My holy war against Captain Arzoccu ended in victory.

20 July, 868
I called a Priscillianist holy war for the County of Logudoro against Captain Arzoccu of Longbeard Band.

2 January, 867
I gained the County of Mayurqa and 2 others.

