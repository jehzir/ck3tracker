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
- Related observation IDs:
- Related transaction IDs:

## Unseen Decisions

There were many decisions that will never be reconstructed exactly. Use this section for inferred context rather than inventing false precision.

### Inferred Period: [Date range]

- What was probably happening:
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

## Closing Memory

When the run ends, write the final memory from the ruler's perspective.

- What did the ruler believe they had accomplished?
- What did they fail to understand?
- Who inherited the consequences?
- Which place, person, or decision outlived the ruler?
- What should the next ruler remember?
