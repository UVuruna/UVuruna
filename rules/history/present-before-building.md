# Present before building — the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="present"></a>

## Present Before Building (owner decree 2026-08-01)

Before implementing, the agent shows how it UNDERSTOOD the task. The obligation
scales with the triage class AUTOMATICALLY — the agent never asks whether a
sketch is wanted; the class decides:

| Task class | Before implementation |
|------------|----------------------|
| **Trivial** (small fix, mechanical change) | Nothing — one sentence of intent in the response |
| **Standard — new functionality / algorithm** | **Algorithm sketch**: VISUAL (box-drawing sketch in chat; rendered Artifact/HTML page when complex — see [Communication](#communication)) + detailed prose walkthrough + why this approach + how the instructions were understood + what is unclear → wait for the owner's yes |
| **Standard — new or changed GUI element** | **Layout sketch**: VISUAL wireframe (box-drawing in chat; rendered Artifact/HTML when complex) + prose explanation → wait. Mermaid source belongs only in `__flow/` doc files ([Docs Rules](../DOCS.md)), never in chat |
| **Wide** (big task, many instructions) | **Echo-brief**: ALL instructions regrouped into cohesive wholes + "this is how I understood everything" + open questions → work starts only after confirmation |

- **The approved sketch is not throwaway work:** after implementation it seeds
  the file's `__flow/` doc — written once, used twice.
- This pairs with Owner Guardrail #5 (vocabulary mix-ups): the sketch is the
  mechanism that catches a misunderstanding at the cost of one message instead
  of one implementation.
- **Pre-authorized autonomous runs** cannot wait for a yes: the sketch /
  echo-brief goes into the final report instead (same precedent as the
  MIGRATE-DOCS target map).
- Class: **GATE** — a Definition-of-Done item in every task brief.

