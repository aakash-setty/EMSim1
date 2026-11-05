# TIDE review packet

For the reviewing physician. Start with `TIDE-SEED.md`, which says what a person decided
and what a model wrote. This packet lists what to read and in what order.

**Status: drafted by a language model on 4 November 2026, not reviewed, not for learners.
Sign-off: not started.**

## What to read

| File | What it is | Time |
|---|---|---|
| `TIDE-SEED.md` | Decisions (section 0), sources, stories, phases and clocks, gaps, 18 open questions with the model's defaults | 25 min |
| `TIDE-deterioration-timeline.md` | Every clock, the do-nothing path, every nurse line beside the vitals it introduces. It prints authored vitals only. Add the effects below by hand | 5 min |
| `TIDE-binding-map.json` | Every coverage row: which catalog entries each case action speaks for | 5 min |
| `case_1_shell.py` | Phases, vitals, transitions, narrations, the compressed-clock lines | 15 min |
| `case_2_actions.py` | Every tag, prompt, vital effect and debrief note | 25 min |
| `case_3_content.py` | Every finding, gas, laboratory value, image and consultant reply | 15 min |
| `case_4_interview.py` | Everything his wife and he say | 10 min |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points, provenance | 10 min |
| `TIDE-discussion.html` | The case discussion beside the debrief, from `Claude outputs/tide-discussion/tide_discussion_v1.py` | 10 min |
| `media/README.md` | Where each picture came from | 3 min |
| `TIDE-review-matrix.md` | What each key resolves to in each state. Generated | as needed |

Then play it in the browser in the default mode: once as intended, once without ever
intubating, and once intubating with nothing running.

## The six things most likely to be wrong

1. **The clocks.** A silent 120 s arrival phase with only the oxygen question (owner, 5
   November 2026), then 240 s to hypotension without fluid, 150 s of fluid response, 150 s to
   worsening shock, 150 s to arrest, 180 s from a held pressure to failing support, 150 s to
   fatigue, 120 s to arrest, 120 s after an unsupported tube. No source supports a figure.
   The owner set the 10 to 12 minute target, asked for the quiet start, and accepted that the
   case can kill a patient left alone.
2. **The failing phase is scripted.** It arrives at 180 s on a vasopressor whatever the
   device (owner B5), and the narration says the clock is compressed (owner B1).
3. **Any intubation without a running drip collapses him** (owner B4). In real patients
   post-intubation hypotension is common, not certain. The debrief says so.
4. **The gases.** Every arterial and venous gas is Henderson-Hasselbalch consistent by
   assertion in the script, and the PaO2 follows the monitor saturation through a lookup
   table. The values themselves are model choices.
5. **The borrowed ECG tracings.** Four come from TSS and one from SCOOT (media/README.md),
   because the ECG generator could not be built in the model's workspace. To fit them, the
   ventilated heart rate moved from 106 to 112 and the tiring heart rate from 52 to 56.
6. **Nothing is harmful.** A third bolus costs saturation and adds rate. Furosemide,
   beta-blockers, nitroglycerin, dopamine, bicarbonate and CT are discouraged. Nothing halts
   the case.

## Vital effects, all teaching choices

None of these is a measured quantity. Each is a number a model chose so that the monitor
shows a lesson. A physician may change any of them.

| Action | Vital | Change | Lasts | Acts | What it is meant to show |
|---|---|---|---|---|---|
| Nasal cannula, nonrebreather, high flow, BiPAP | Saturation | +3, +6, +7, +8 | while on | not intubated, not tiring | Each step buys a little. One key, so the last device shown wins |
| The same | Rate | 0, -2, -2, -4 | the same | the same | Support eases the work a little. The 0 replaces an earlier device's effect under the same key (validator warning, by design) |
| Third crystalloid bolus onward | Saturation, rate | -3, +4 | from then on | not intubated | Fluid that has stopped working goes to the lungs |
| Intubation | Saturation | -3, -10 or -18 | 30 s | by preoxygenation (positive pressure, high flow, none) | Preoxygenation decides the desaturation |
| Intubation with a drip running | Systolic, diastolic | -14, -8 | 60 s | drip running | Induction dips him even with support |
| Propofol infusion | Systolic, diastolic | -8, -4 | while on | every phase | Sedation lowers pressure |
| Stopping a vasopressor | Systolic, diastolic | -24, -14 | until restarted | every phase | The drip was holding him |
| Vasopressor drips | none | `vital_effects: []` | | | The phases carry the rise |

What moves nothing on purpose: every antibiotic (owner B2), hydrocortisone, the cultures and
every study.

## What the tests cover

Counts from the last run, on 5 November 2026, in the owner's folder. The same counts came
from a copy of the repository in the model's workspace the day before. The source files and
the built case file were checked byte for byte between the two.

- 24 scenarios in `TIDE-scenarios.json`, all passing in `engine/sim_runner.py`: the intended
  path, never intubating, fluid only, left alone, a late pressor, pressor without fluid,
  fluid late, the three collapse routes, early intubation, mask only, no antibiotic,
  vasopressin alone, dopamine, a tube in the tiring phase, and an immediate handoff.
- 596 checks in `engine/engine-tests.js` with `TIDE-tests.js`, all passing.
- Validator: 0 errors, 2 warnings. Eight actions are not in the catalog by design: seven
  hidden targets and `handoff_submit`. The nasal cannula's rate effect of 0 is deliberate
  (above).
- `engine/validator-tests.py`: 138 checks, all passing.
- `engine/test_packs.py` for every pack, one at a time: 9 packs, 0 failed.
- `engine/build_simulator.py` and `engine/gen_docs.py` ran. TIDE binds 113 actions, 8
  unbound by design.
- `engine/kit_check.py`: 0 errors, 0 warnings, 64,553 tokens against 65,000.
- Browser play-throughs by script, in Chromium, in the workspace copy: the case opens, high flow goes on with the
  nurse line and the cannula drawn on the figure, the monitor attaches, the ECG returns its
  tracing image with its caption. A do-nothing run in the default mode reached the
  six-minute pause, then arrest, with the case's timeout reason. Ending early opened the
  debrief, and the discussion rendered with all four figures. The page raised no error. The
  only failed request was the page's call to an outside font or script host, which the
  workspace blocks.

## Interview matcher, held-out set, lexical stage only

77 held-out questions, 31 of them out of scope, written before the first build by the same
model that wrote the variants (said in the file's note). Two were reworded after the first
run because they appeared word for word in the generated bank, which the harness refuses.
Nothing was tuned against this set.

| | 4 November |
|---|---|
| In-scope correct | 40 of 46 (87%) |
| Sent to a wrong topic | 4 |
| Extra answer | 1 |
| Fell through | 1 |
| Out-of-scope refused | 20 of 31 |

Wrong topic on a management-changing topic:

- "Since when has he had the fever?" went to `fever_and_chills`. Wanted `onset`.
- "Did this come on over days or all at once?" went to `onset`. Wanted `timing_progression`.
- "Can he talk in full sentences normally?" went to `code_status`. Wanted `breathing`.

Also wrong: "What's brought you in today?" went to `nausea_vomiting`. Wanted
`presenting_story`. This is likely the most common opening question. A fix should be made
in the shared phrasings and then measured on fresh questions, not on this set.

Fell through: "Does it hurt when he takes a deep breath?" Wanted `chest_pain`.

Answered when out of scope, 11: hearing, tetanus shot (to `vaccinations`, arguably fair),
joint pains, swallowing, snoring, memory before this, prostate, favorite food, back pain,
eye problems, hair loss.

The embedding stage was not run: the workspace cannot reach huggingface.co.

## What the tests cannot cover, and what was not run

Whether any of it is good medicine, and whether it is any good to sit through. No learner
and no physician has played it.

Not run: the embedding stage of the matcher. The microphone. A full intended-path
play-through by hand in the browser (the scenarios cover the logic, the script covered the
screens listed above). The matcher was run in both places with the same result.

## Section 11.5 checklist

Not started by a physician. Every box is open.
