# TSS review packet

For the reviewing physician. Start with `TSS-SEED.md`, which says what a person decided
and what a model wrote. This packet lists what to read and in what order.

**Status: drafted by a language model on 6 October 2026, changed by a model on 7 October
2026 after an audit, not reviewed, not for learners.**

## What to read

| File | What it is | Time |
|---|---|---|
| `TSS-SEED.md` | Decisions, phases, what changed, open questions, and sections 3.1 to 3.8 as lists to sign | 20 min |
| `TSS-deterioration-timeline.md` | Every clock, the do-nothing path, every nurse line beside the vitals it introduces. It prints authored vitals only. Add the effects in the table below by hand | 5 min |
| `TSS-binding-map.json` | Every coverage row: which catalog entries each case action speaks for | 5 min |
| `case_2_actions.py` | Every tag, prompt and debrief note | 25 min |
| `case_3_content.py` | Every finding, laboratory value and consultant reply | 15 min |
| `case_4_interview.py` | Everything she says | 10 min |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points, provenance | 10 min |
| `TSS-review-matrix.md` | What each key resolves to in each state. Generated. It does not show prompts, transitions, vital effects, facts or volunteer lines | as needed |

Then play it once in the browser in the default mode, including a discharge on arrival and
a run with fluid and a vasopressor and no pelvic examination.

## The five things most likely to be wrong

1. **The clocks.** 300 seconds without fluid, 150 seconds of fluid response, 240 seconds
   hypotensive, 270 seconds supported with the source in. The owner approved them as design
   choices. No source supports a figure.
2. **Source removal working in ten seconds.** The direction was chosen by the directing
   physician. The speed is a compression the debrief note admits to.
3. **The laboratory picture.** Values were chosen to meet the CDC criteria for a probable
   case. No physician chose them. Nine studies still return a catalog normal beside them
   (SEED questions 8 to 16).
4. **Nothing is harmful.** A beta blocker in compensated shock costs a point and twelve
   points of pressure for three minutes. MGCA halts the case for the same act.
5. **Twenty neutral tags given as placeholders on 7 October 2026.** Thirteen studies, the
   nephrology consult, the maintenance infusions, two oxygen routes, lorazepam and
   morphine, and a hidden action that is not a button. SEED section 8 lists them.

## Vital effects, all teaching choices

None of these is a measured or modeled quantity. Each is a number a model chose so that the
monitor shows a lesson. A physician may change any of them.

| Action, and what it covers | Vital | Change | Lasts | Acts in | What it is meant to show |
|---|---|---|---|---|---|
| Crystalloid bolus, four entries | Systolic | +6 | 60 s | hypotensive, supported, profound shock | A further bolus buys a little, briefly |
| The same | Heart rate | -6 | 60 s | the same | The same |
| Vasopressor infusion, four entries | Systolic | +8 | while no fluid has been given | hypotensive, profound shock | A vasopressor without fluid is not enough |
| Phenylephrine push | Systolic | +12 | 90 s | hypotensive, supported, profound shock | A push dose is a bridge |
| Rate control, eight entries | Heart rate | -16 | 180 s | every phase | Slowing her takes away her compensation |
| The same | Systolic | -12 | 180 s | every phase | The same |
| Nasal cannula | Saturation | +2 | while on | hypotensive, profound shock, not intubated | Oxygen adds little until she is hypotensive |
| Mask, bag or non-invasive ventilation | Saturation | +4 | while on | the same | The same. One key, so the four routes do not stack. The +4 for the bag and for non-invasive ventilation was copied from the mask on 7 October 2026 |
| Acetaminophen | Temperature | -0.6 | from 30 s, no end | every phase | It lowers the number and treats nothing |

What moves nothing on purpose: every antibiotic, ondansetron, removal of the tampon without
fluid and a vasopressor, and a maintenance infusion.

Because rate control acts in every phase, every phase can carry an effect. For that reason
no nurse narration quotes a figure. One stack is a known limit: a vasopressor with no fluid
plus a push dose lifts the systolic to 98 while the nurse says her pressure has dropped.
The mean and the diastolic have fallen (SEED section 10).

## What the tests cover

Counts from the last run, on 7 October 2026.

- 31 scenarios in `TSS-scenarios.json`, all passing in `engine/sim_runner.py`. Nine are
  new: paired "inside the last window" and "one action too late" routes for the 300 and
  240 second clocks, a last-window rescue for the 270 second clock, a maintenance infusion,
  the two stop routes and the two new rate-control routes.
- 1,024 checks in `engine/engine-tests.js` with `TSS-tests.js`, all passing. The new ones
  fold 44 effect-bearing routes and compare each nurse line with the monitor before and
  after it, fold each one-treatment-missing path in the default mode, test each pair of
  pending timed rules with fractional times, and test the sedation follow-up both ways.
- Validator: 0 errors, 1 warning. Three actions are not in the catalog by design:
  `handoff_submit`, `attempt_discharge` and `sedation_after_tube`. None is a button.
- `engine/validator-tests.py`: 76 checks, all passing.
- One browser play-through by script, in the default mode: history, examination, a
  maintenance infusion, a bolus, removal, antibiotics, the fade, vasopressin, a refused
  stop, stabilizing, two consults, the spoken phrase "pelvic exam" typed into the voice
  box, handoff with four diagnoses and the debrief. Then a discharge on arrival and the
  faint. 42 checks passed and the page raised no error. The browser could not reach the
  network, so the two requests the page makes for outside resources failed.

## What the tests cannot cover, and what was not run

Whether any of it is good medicine, and whether it is any good to sit through. No learner
and no physician has played it.

Not run: the embedding stage of the interview matcher. The microphone, which was tested
only through the text box. Any other pack's suites, since nothing outside this pack changed
except this pack's own line in `catalog/expand_interview_variants.py`. The harmful halt in
the checklist does not apply, because this pack has none.

## Interview matcher, held-out set, lexical stage only

68 held-out questions, written before the bank was expanded and never tuned against.

| | 6 October | 7 October |
|---|---|---|
| In-scope correct | 28 of 38 | 28 of 38 |
| Sent to a wrong topic | 3 | 3 |
| Extra answer | 6 | 6 |
| Fell through | 1 | 1 |
| Out-of-scope refused | 15 of 30 | 13 of 30 |

Wrong topic on a management-changing topic, the same three as before:

- "How come your skin is that color?" went to `urine_output`. Wanted `rash`.
- "How much have you peed today?" went to `last_oral_intake`. Wanted `urine_output`.
- "how long have you had the rahs" went to `onset`. Wanted `rash`.

Two out-of-scope questions that were refused on 6 October are answered now, and neither
change was made to chase this set:

- "Do you have trouble hearing?" goes to `breathing`. The regenerated bank moved "Any
  problems with your hearing?" into the tuning file, because every sixth entry goes there
  and the list is shorter.
- "What is your favorite restaurant?" goes to `suspect_meal`. That topic gained shared
  phrasings about restaurants when the catalog mapped it.

The tampon topic matched every held-out phrasing. The embedding stage could not be run here.

## Section 14.3 checklist

Not started by a physician. Every box is open. The structural items a tool can check were
checked on 7 October 2026 and are listed under "What the tests cover".
