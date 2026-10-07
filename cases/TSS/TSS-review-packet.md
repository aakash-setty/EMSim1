# TSS review packet

For the reviewing physician. Start with `TSS-SEED.md`, which says what a person decided
and what a model wrote. This packet lists what to read and in what order.

**Status: drafted by a language model, not reviewed, not for learners.**

## What to read

| File | What it is | Time |
|---|---|---|
| `TSS-SEED.md` | Decisions, phases, open questions | 5 min |
| `TSS-deterioration-timeline.md` | Every clock, the do-nothing path, every nurse line beside the vitals it introduces | 5 min |
| `case_2_actions.py` | Every tag and debrief note | 20 min |
| `case_3_content.py` | Every finding and laboratory value | 10 min |
| `case_4_interview.py` | Everything she says | 10 min |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points | 10 min |
| `TSS-review-matrix.md` | What each key resolves to in each state. Generated | as needed |

Then play it once in the browser, including a discharge on arrival and a run with fluid
and a vasopressor and no pelvic examination.

## The four things most likely to be wrong

1. **The clocks.** 300 seconds without fluid, 150 seconds of fluid response, 240 seconds
   hypotensive, 270 seconds supported with the source in. All four are drafting judgments.
2. **Source removal working in ten seconds.** The direction was chosen by the directing
   physician. The speed is a compression the debrief note admits to.
3. **The laboratory picture.** Values were chosen to meet the CDC criteria for a probable
   case. No physician chose them.
4. **Nothing is harmful.** A beta blocker in compensated shock costs a point and twelve
   points of pressure for three minutes. MGCA halts the case for the same act.

## What the tests cover

- 22 scenarios in `TSS-scenarios.json`, all passing in `engine/sim_runner.py`.
- 587 checks in `engine/engine-tests.js` with `TSS-tests.js`, all passing.
- Validator: 0 errors, 1 warning (two actions are not in the catalog by design).
- One browser play-through by script: discharge on arrival, the faint, recovery, removal,
  handoff, debrief. This is what found the engine timing fault recorded in the CHANGELOG.

## What the tests cannot cover

Whether any of it is good medicine, and whether it is any good to sit through. No learner
and no physician has played it.

## Interview matcher, held-out set, lexical stage only

28 of 38 in-scope questions correct, 3 sent to a wrong topic, 15 of 30 out-of-scope
questions refused. That is in line with the other packs. The embedding stage could not be
run here. The three wrong answers were on management-changing topics (two on the rash, one
on urine output). The tampon topic matched every held-out phrasing.

## Section 14.3 checklist

Not started. Every box is open.
