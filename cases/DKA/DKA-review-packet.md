# DKA review packet

**Status: drafted by a language model on 6 October 2026, revised by a language model on 7
October 2026 after an audit. Not reviewed by a physician. Not for learners.** Start with
`DKA-SEED.md`.

## What to read

| File | What it is |
|---|---|
| `DKA-SEED.md` | What a person decided. Sources and how each was read. The seed content of sections 3.4 to 3.8. Phases, transitions and the race table. What the audit fix changed. Known gaps. Open questions for the physician |
| `DKA-review-matrix.md` | What every tag, result, finding, consultant line and answer resolves to in every state |
| `DKA-deterioration-timeline.md` | Every timed rule and every nurse line beside the vitals it introduces |
| `DKA-binding-map.json` | Every case action and the catalog entries it claims. Three coverage rows and four case-only rows |
| `case_1_shell.py` | Identity, the patient, the handover, the phases and every transition |
| `case_2_actions.py` | Every tag, flag, prompt, vital effect, follow-up and debrief note |
| `case_3_content.py` | Findings, results and what the consultants say |
| `case_4_interview.py` | Everything she says, the facts, the volunteer line, and the generated phrasings and out-of-scope bank |
| `case_4_variants.py` | The hand-written question phrasings shared with other packs |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points, and the provenance block |
| `DKA-tests.js`, `DKA-scenarios.json` | The case assertions and the walked scenarios |
| `DKA-matcher-eval-questions.json` | The held-out interview questions |

The review matrix does not show prompts, prerequisites, follow-ups, transitions, vital
effects, `also_satisfies`, facts or volunteer lines (authoring 14.2a). Read those in the
sources.

## Changed on 7 October 2026 by a medical re-read against the owner's potassium table

The potassium rule by level (hold insulin under 3.5, 20 to 40 mEq an hour, recheck every
one to two hours, insulin at 3.5 or more, 20 to 30 mEq per liter between 3.5 and 5.5, hold
potassium over 5.5) replaced the rate and the intervals read from the consensus report.
Hyponatremia and acute kidney injury are no longer credited diagnoses. DKA-SEED.md
section 5b has the list and the reasoning.

## Changed on 13 October 2026

A second potassium order once the level is 3.5 or more (potassium in the fluids with the
insulin) is a critical action with its own nurse line, a prompt and an endocrinology tier,
by the owner's decision of 7 October. DKA-SEED.md section 5c.

## Most likely to be wrong

1. The potassium in each state, and that insulin at 3.1 produces weakness and ectopy at 2.6.
2. The level of care. The consensus report's table suggests less than step-down for mild
   ketoacidosis. This case argues the potassium moves her up.
3. Every sentence that cites the consensus report. It was read through a summarizing tool.
   Follow-up notes and handoff explanations cite it too and cannot carry a marker.
4. The three delays, 10, 20 and 5 seconds, and what the nurse says they stand for.
5. Every number in the laboratory and ECG results, and two chemistry values that do not
   trend the way the notes say (SEED open question 10).
6. The order rules as revised on 7 October 2026: any rapid insulin before the potassium
   has finished leads to the fall, potassium given before the fall counts toward the
   rescue, and one insulin order after the rescue is the restart.
7. Two denials a model added to her answers: no leg cramps and no black stools.

## Counts, from the run of 7 October 2026

| What | Count |
|---|---|
| Phases | 5 clinical and 1 terminal |
| Timed transitions | 6, every one the delayed consequence of an action |
| Case actions | 62: 43 orders, studies and consults, 14 exams, 4 hidden targets and the handoff |
| Actions that can be critical | 12 |
| Prompts | 10 actions prompt. One has an escalation |
| Follow-ups | 2 |
| Case-only actions | 5: the handoff and the four hidden targets |
| Interview topics | 35, with 439 hand-written phrasings and 1067 in all. 71 out-of-scope bank entries. 6 topics carry facts |
| Additional diagnoses | 4 |
| Scenarios | 37 of 37 pass |
| Engine checks | 767 pass on the one-pack build of 13 October 2026 |
| Validator tests | 76 pass |
| Validator | 0 errors and 1 warning. The warning names the five case-only actions and stays for good |

## Vital effects are teaching choices

No trial supports either number. The simulator is not modeling physiology.

| Action | Vital | Change | Lasts | Key |
|---|---|---|---|---|
| Any crystalloid bolus (four catalog entries) | heart rate | down 10 | the rest of the case | `fluid_hr` |
| Any crystalloid bolus | systolic pressure | up 6 | the rest of the case | `fluid_bp` |
| Normal saline infusion or Ringer's infusion | heart rate | down 10 | the rest of the case | `fluid_hr` |
| Normal saline infusion or Ringer's infusion | systolic pressure | up 6 | the rest of the case | `fluid_bp` |

The keys are shared, so nothing stacks. Every phase's authored rate is the rate without
fluid. The effect has no end, so no ECG report, exam line or nurse line quotes a heart
rate. The treated phase reads 104 without fluid and 94 with it. Its ECG says sinus rhythm
and its exam does not say fast. Every nurse line that gives a direction ("her rate has
gone up") was folded through the engine with a bolus, with an infusion and with no fluid,
and compared with the monitor.

No treatment other than fluid moves a number by an effect. Potassium, insulin and
magnesium change her through phases.

## The interview matcher

Lexical stage only, on the held-out set of 82 questions written by the same author as the
bank. The semantic stage was not run.

| | Before the fix | After |
|---|---|---|
| In scope correct | 41 of 52 | 41 of 52 |
| Wrong topic | 4 | 3 |
| Fell through | 1 | 2 |
| Extra answer | 6 | 6 |
| Out of scope refused | 18 of 30 | 17 of 30 |

Wrong topic on a management-changing topic, both before and after:

- "Did you give yourself your insulin yesterday?" goes to severity. It should reach
  insulin_taken_recently.
- "home BGs?" goes to current_medications. It should reach glucose_monitoring.

The other misses after the fix: "Whereabouts in your belly is the pain?" goes to
abdominal_pain and not location_of_pain. "Roughly how often have you been throwing up?"
and "T1DM?" fall through.

Nothing was tuned against the held-out set. The two management-changing misses need new
phrasings in the shared library, which is outside this pack.

Two answers sit near the limits in authoring 10.4 and are flagged in
`interview.authoring_notes`: "they said my blood had gone acidic" about her admission at
eleven, and her home meter readings of 380 and 290.

The generated out-of-scope bank was read against the topic list on 7 October 2026. Seven
questions it used to refuse were asked in the built simulator and each reached a topic:
night urination, weakness in the arms or legs, leg cramps, blood in the stool, black
stools, what she studies, and back pain.

## What was run, and what was not

Run on 7 October 2026, in this order: the interview expansion for this pack,
`build_case.py`, `bind_catalog.py`, `validate_case.py`, `deterioration_timeline.py`,
`build_simulator.py`, `engine-tests.js` with `DKA-tests.js`, `sim_runner.py`,
`validator-tests.py`, and `matcher_eval.mjs --only DKA`.

One scripted browser play-through with Playwright against `build/simulator.html` on 7
October 2026, in the default mode, two runs, 51 checks, no page errors. Run one: the
intended path with fluid by infusion, twelve interview questions, both consultants, the
handoff with five diagnoses, and the debrief with every note opened. Run two: insulin 13
seconds after potassium, the fall five seconds after the potassium finished, the hold
alone, one subcutaneous restart, the handoff and the debrief. It supersedes the
play-through of 6 October 2026, which predated glargine.

Not run:

- The semantic stage of the matcher.
- Any play by a person. Nobody has sat through the case.
- Voice orders by microphone. The generic voice checks in `engine-tests.js` passed.
- The restart prompt in the browser. It comes at 135 seconds in the default mode. The
  engine tests cover it in both modes.
- The tests of the other six packs. The only change outside this folder is three of this
  pack's own entries in `catalog/expand_interview_variants.py`.
- No physician has read any of it.

## Section 14.3 checklist

Every box is open. No physician has started it.

**Clinical content**
- [ ] Every abnormal finding, lab, and imaging result is clinically correct for this diagnosis
- [ ] Every abnormal value carries an abnormal flag, and no normal value carries one
- [ ] Reference intervals are right for the assays this case is modeling
- [ ] Every harmful action is genuinely harmful, and its halt reason is accurate
- [ ] Nothing tagged harmful should have been discouraged, and nothing discouraged should have been harmful
- [ ] No action tagged critical is actually optional. No action tagged neutral is actually critical
- [ ] Findings change appropriately after successful treatment
- [ ] Every debrief note teaches something correct, and every reference has been checked

**Catalog conformance**
- [ ] Every mapped binding row is clinically sound, with particular attention to assays, routes and composites
- [ ] Every harmful and discouraged action covers every catalog route to the same act, and a discouraged or rescuing stop action covers every sibling stop entry (3.4)
- [ ] Every case-only action is a decision in the SEED with a name and a date, has an `unmatched_placement`, and the SEED says what the button costs (7.1). Its spoken phrases have been tried in the built simulator
- [ ] No `short_label` names the diagnosis, the mechanism or the missing treatment, and every phase has one (5)
- [ ] Exam findings sit where the routing map puts them, and the general status line matches the patient
- [ ] Every diagnosis, correct and alternative, is a real catalog id

**Arrival handover**
- [ ] It names no diagnosis, in clinical or lay words
- [ ] It contains no past history, no medication, no allergy and no pertinent negative
- [ ] Any vital sign in it is what was measured on the way in, is written that way, and agrees with the first phase. It is no longer forbidden: since the monitor is dark until it is attached, the handover may be the only number the resident has, which is what a real handover is
- [ ] It is vague and incomplete in the way a real busy handover is, rather than a competent summary
- [ ] It is in the right voice for `mode`: a crew who saw the scene, or a triage nurse who saw the waiting room
- [ ] Read cold, it gives a resident somewhere to start and nowhere to finish

**Interview**
- [ ] Every topic in the 10.2 minimum list is authored, including the ones this case does not turn on
- [ ] The case has been played through the History tab alone, asking only what a resident would think to ask, to check that the case opens at all without the old background paragraph
- [ ] The patient never reveals the diagnosis or reports information they could not know
- [ ] Pertinent negatives are authored as denials, not left to the out-of-scope fallback
- [ ] Interview answers are correct at every alertness level, and every topic has a distressed-phase answer where the case needs one
- [ ] Paraphrase coverage is adequate on every topic whose answer changes management
- [ ] A held-out question file exists, was written before the bank was expanded, and its results are in the review packet with each management-changing miss named. If there is none, the packet says the interview is unmeasured (10.6)
- [ ] The generated out-of-scope bank has been read against the topic list and holds no question this patient can answer. Every topic special to the case is in `MAP` and has cover tags (10.6)
- [ ] Every topic marked `pertinent_negative` denies, in every phase (10.3)

**Time-guarded transitions**, where the case uses them
- [ ] Every deadline is a clinical claim you are willing to defend: this patient, without this treatment, deteriorates in about this long
- [ ] Every deterioration is preceded by a prompt naming the missing treatment, early enough to act on, and you have read the deterioration timeline to confirm it
- [ ] Every narration line is true of the vital signs shown immediately after it fires, on the monitor and not only against the phase's authored numbers. For each destination phase, every vital effect that can be acting there has been listed, and a narration that quotes a number has been tested with each one acting (9.5)
- [ ] In the default mode, with prompt deadlines times 3, the warning for each deterioration still fires before it. Where it does not, that is a recorded decision (9.7)
- [ ] In every phase with two or more timed rules, each pair has a line in the SEED saying which fires first and where the patient lands, and each line has a test with fractional times (5.4)
- [ ] The do-nothing trajectory is clinically right from end to end, not only at the first hop
- [ ] If the clock can end the case, you intended that, and the `timeout_reason` attributes it to the omission rather than to anything the resident did
- [ ] No prompt in a timed phase is stranded past the exit

**Timed mechanics**, where the case uses them
- [ ] For each one you have asked "what else has to know", and the answer picked the construct (6.4)
- [ ] Every expiring flag is read by something, and the thing that reads it is a transition rather than a tag
- [ ] A drug that both moves a number and changes the case holds its clock in ONE place, not in a duration and a flag both
- [ ] You have played the case doing nothing after the drug, and watched the consequence of it wearing off actually arrive
- [ ] Every duration is a clinical claim you will defend: this drug, this patient, acts about this long
- [ ] Where a drip and a bolus of the same drug both grant the flag, you intended the drip to stop it expiring

**Vital effects**, where the case uses them
- [ ] Every non-terminal phase's authored vitals are the **unsupported** baseline, so nothing is counted twice
- [ ] You have played the case with each effect-bearing action alone and read the number off the monitor, rather than trusting the arithmetic
- [ ] Every route to the same drug shares one key, and no two keys name the same act
- [ ] Every delta and duration is a teaching choice you are willing to have called a teaching choice in the review packet, and none of them is presented as a modeled quantity
- [ ] The treatments that move nothing move nothing on purpose, and the debrief says why
- [ ] The terminal phases read correctly, remembering that they ignore every effect
- [ ] No study report, exam finding or nurse alert quotes a vital sign that an effect with no end can move (6.1)
- [ ] No `while` guard switches an effect on in the phase that already carries the change (6.1)
- [ ] Every onset and duration window in the validator's note is the window you meant

**Structure and sequencing**
- [ ] Consultant advice never references a study that was not ordered, or one still pending. Every consultant line containing a number sits on a rule that tests `study S resulted`, the deteriorated-phase tiers included, and the number is true for every variant of that result (11.5)
- [ ] No consultant reply declines while the press still earns credit (11.5)
- [ ] A pending tier exists for every consultant whose advice depends on a study
- [ ] Prerequisites are clinically correct, and any catalog default that should be waived here has been
- [ ] Follow-ups are triggered by the right action, apply only where clinically indicated, and list every satisfier
- [ ] No follow-up that asks for something "again" or "after" relies on `satisfied_by` for an act the learner could have done before the trigger. `triggered_by` matches the actions that list it in `follow_ups_triggered` (8.2)
- [ ] A `flags_set_repeat` flag used as a restart or a repeat study has a scenario for each first dose and each early repeat, and its limits are in the SEED (6.5)
- [ ] Every deterioration branch has an exit that exists in the catalog

**Presentation**
- [ ] **No nurse prompt implies the patient is deteriorating**
- [ ] Every prompt and escalation is true in each phase its guard allows, claims no treatment and cites no study that its guard does not test, and has a deadline its guard can meet (9.5)
- [ ] Every `nurse_alert`, `narration_override`, narration, status line and consultant line on a covering action names the class and not one drug, and claims nothing the prerequisites do not guarantee (9.1)
- [ ] No result `comment` names the diagnosis, states the lesson, quotes another result or speaks to the reviewer, and no report carries a comment the learner needs (11.4)
- [ ] `[UNVERIFIED]` markers sit only in the fields the interface strips, every unchecked claim in those fields has one, and the provenance block lists each reference with how it was read (13, 17)
- [ ] Prompt deadlines reflect real relative urgency
- [ ] Wrong dispositions and diagnoses have explanations, not just verdicts
- [ ] The review matrix contains no clinically wrong resolution
- [ ] **The case has been played start to finish in the interface**, in the default mode, including at least one harmful halt and the deterioration branch
