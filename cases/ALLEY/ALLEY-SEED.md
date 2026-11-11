# ALLEY seed and provenance

Methanol poisoning from windshield washer fluid in a 52-year-old man brought in to sleep it
off. Case 10. Drafted by a language model (Claude) on 11 November 2026. **Not reviewed by a
physician. Not for learners.**

Case map: "EMSim case map, ALLEY revision 2" (Claude artifact, https://claude.ai/artifact/XM7Ep2Tw5dqhTBUWVNEG9j).

## 0. What a person decided

Aakash Setty, 11 November 2026, in conversation, from his own pasted case structure and two
rounds of questions.

| Decision | Where it is used |
|---|---|
| Case structure: PGY-1, washer fluid, never arrests, seizes or needs a tube, sparse history because he is drunk | Whole pack |
| Arrival pH 7.19, then 7.15, then 7.12. His answer was "okay, return the pH to how you had it" after first asking for 7.10, read by the model as restoring this ladder | case_1 phases, case_3 GAS |
| Venous and arterial gases show the same numbers | case_3 gas_rules, gas debrief note |
| Vision at arrival counts fingers (V0) | case_3 VISION_EXAM, case_4 vision |
| Thiamine not penalized (neutral) | case_2 thiamine |
| Folinic acid added for this case, as a case-only button | case_2 folinic_acid, build_case binding |
| Poison center (consult_toxicology) critical | case_2 consult_toxicology |
| Bicarbonate alone does not pause the clock (his rule T4 changed) | case_2 na_bicarbonate_*, case_1 transitions |
| No prompt warns of the untreated drift by naming the antidote | case_1 CLOCK_RATIONALE |
| The worst tier is a floor, stated openly | case_1 untreated_floor, narration |
| Nephrology gated on the chart, no dialogue | case_2 RENAL_PREREQS, case_3 consultants |
| Intubation blocked | case_2 intubate_rapid_sequence |
| Six learning goals | section 2 |
| Discharge is a case failure, ending "He was brought back four hours later, unresponsive." | case_1 discharged, case_5 intercepts |
| Sedation ends the case before both fomepizole and bicarbonate are in, and is a 150-second overlay after. His answer "okay" to the default, as read by the model | case_2 SEDATION |
| An engine change may be made if the intubation block needed one | Not needed in the end: see section 8 |
| A trauma survey (head, neurological and abdominal exams) is critical, for a man with an unclear cause of delirium | case_2 exams, all live phases |
| The first drift takes 360 seconds, the second 180 | case_1 transitions |

Everything else is model output.

## 1. Sources, and how far each was read

As in `provenance.reference_status` in the case file. In short: EXTRIP (Roberts 2015) and the
fomepizole label read through abstract pages and summaries via search. AACT 2002 not opened,
criteria read secondhand. Kraut and Mullins 2018 not opened. Cranmer et al. 2026, cited in the
owner's structure, could not be found. Wittler et al., MedEdPORTAL 2018 (a methanol simulation
for EM residents) read as an abstract only.

## 2. Learning goals and where each is acted on

| Goal | Source | Where the learner acts |
|---|---|---|
| 1. When "just drunk" does not explain the respiratory rate and the ethanol, get a gas and a chemistry, and look for injury | Owner. Wittler 2018 (abstract) | Gas, chemistry and ethanol critical on arrival. Head, neurological and abdominal exams critical throughout. Nurse cue at 40 s. The hallway and discharge intercepts |
| 2. Work both gaps, with ethanol in the osmolar gap | Owner. Ontario Poison Centre resource (via search) | Osmolality critical. Cue at 50 s once the ethanol is back. Additional diagnosis at handoff |
| 3. Ask about vision | Owner. EXTRIP | Vision target critical, HEENT exam counts. Cue at 55 s. The tier the learner locks in |
| 4. Fomepizole on suspicion, and it stops production and removes nothing | Owner. Fomepizole label | Fomepizole critical in the untreated tiers. Held phases look unchanged |
| 5. Bicarbonate alongside the antidote, not instead of it | Owner. Emergency Care BC, Austin | Bicarbonate critical until improving. The overlay wears off |
| 6. Dialysis on the indications, without a level | Owner. EXTRIP | Nephrology critical, with two chart prerequisites |

Idea that travels: a diagnosis has to explain the numbers. When the obvious label leaves one
unexplained, chase the number.

How it differs from the library: `metadata.library` in case_1. Closest are DIPH (toxicology)
and DKA (acid-base reading). First unhoused patient and first known "regular".

## 3. The stories

- Treated well: gas, chemistry, ethanol, osmolality, the drink and the eyes asked about,
  fomepizole, bicarbonate, poison center, nephrology, ICU. Presentation, held_early,
  improving, case_complete. About 70 to 140 seconds of clock.
- Just drunk: the hallway or a CT before the antidote costs one tier, once per tier.
- Bicarbonate alone: the monitor and gas look better for 180 seconds, the clock runs on.
- Antidote alone: frozen at the tier, bicarbonate prompted at 120 seconds in the held phase.
- Left alone: second tier at 360 seconds, worst tier at 540, then the floor. Prompts on the
  floor for the antidote at 60 seconds and an escalation naming the backpack and poison
  control at 150.
- Sedated for "withdrawal": lorazepam, morphine or diphenhydramine halts the run before he is
  improving. Midazolam, propofol and fentanyl are ungraded by the catalog rule and play a
  150-second overlay instead.
- Discharged: ends in the terminal phase `discharged`.

### 3.7 Interview ground truth

Positive: drank vodka, then "the blue stuff" ("window stuff, for the car"), most of the jug,
cannot say when. Vision by tier (V0 snowstorm, V1 cannot make out faces, V2 light and shapes),
since he woke. Nausea (vomited from the second tier), epigastric pain, pounding headache,
little dizzy, tired. Heavy drinker, gets the shakes when he stops, not now. No medical
history, no medications, no allergies. Lives outside. Smokes. Has not eaten for a couple of
days.

Model-added (owner's structure did not supply): the timing he cannot give, how much he drank,
the intent denial, the withdrawal history, the last meal, the housing wording, the dizziness,
and every denial (chest pain, palpitations, fever, cough, diarrhea, urinary symptoms, fall or
head injury, seizures, other drugs, allergies).

Pertinent negatives: intent, chest pain, palpitations, fever, cough, diarrhea, urinary
symptoms, fall or head injury, seizures, allergies, other drugs.

## 4. Phases, transitions and the race table

Seven live phases (presentation, drifting, untreated_floor, held_early, held_mid, held_late,
improving) and three terminal (discharged, halted, case_complete). The deterioration timeline
lists every timed rule.

Pairs of pending timed rules:

| Phase | Rules | Which fires first | Result |
|---|---|---|---|
| presentation | away (5 s after a CT or the hallway) and the 360 s clock | Whichever is due first. A CT at 356 to 360 s: the clock fires at 360 and the away credit was for this phase, so no second move | One tier in every order |
| drifting | away and the 180 s clock | As above | One tier |
| presentation | bicarbonate lapse at t and the 360 s clock | A bolus at 180 s lapses at 360, the same instant | Drift either way. Tested at fractional times |

## 5. Built differently from the owner's structure, and why

See the case map's table "What changed from your structure". Main items: seconds not sim
minutes, three held phases, overlays for bicarbonate and sedation, the hallway as an
intercepted disposition, heart rates moved to 112, 114, 116 and 96 to match borrowed ECG
tracings, Winter's formula noted as arterial, fomepizole criteria corrected to "suspicion plus
two of", timing of the drink made vague, the T+7 vision cue reworded, a self-harm question
added, a repeat-gas follow-up added from the owner's bonus list.

## 6. Known gaps

- No arrest, seizure or coma on the clock. The floor is a design choice, stated in the
  narration and the debrief.
- Bicarbonate overlay values are fixed whatever the tier.
- Stopping a bicarbonate infusion does not end its buffering inside the case.
- Midazolam, propofol and fentanyl cannot be scored here (ungraded intubation-care rule), so
  they do not halt where lorazepam does.
- The held phases do not slowly improve.
- No conditional epilogue at the end of the run. The vision outcome is in the debrief notes.
- The methanol level, "search belongings" and ophthalmology are not orderable.
- The ECG tracings are borrowed and show the phase rate, not the rate an effect moves.
- Lexical matcher: "how much of it?" after the drink question routes to severity, and "since
  when?" after the vision question routes to last oral intake. Two held-out questions on the
  drink topic route elsewhere (review packet).

## 7. Open questions for the physician

1. Is harmful (halt) right for lorazepam, morphine and diphenhydramine before treatment, given
   the ungraded midazolam plays only an overlay?
2. Are the dialysis prerequisites right: a gas and a chemistry, plus an osmolality or the drink
   or the vision asked?
3. Should the improving phase keep the tier's osmolality and anion gap more precisely?
4. Is thiamine better recommended than neutral for a malnourished drinker?
5. Should the floor eventually end in coma, against the no-crash constraint?

## 8. Engine and catalog changes made for the case

None. An edit to `engine/engine-tests.js` to let a case declare intubation blocked was refused
by the session's permission check as a shared-file change. The block was built inside the case
instead: a prerequisite on a flag set only by a hidden, buttonless case action
(`attending_approves_intubation`). Catalog change requests are in the case file's provenance.

## 9. Awaiting sign-off

Everything in `provenance.author_only_fields_pending_signoff`, and the section 11.5 checklist
in full, including a play-through at 1x in the default mode.
