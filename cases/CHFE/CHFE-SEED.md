# CHFE author's seed

**There is no seed for this case, and that is the defect the whole pack is built around.**

Section 3 of `docs/case-authoring-requirements.md` says the physician supplies ground
truth first and the drafting AI expands it. This case was produced the other way round:
a language model generated every AUTHOR-ONLY field, then the tooling was built to make
the result reviewable. Section 17 of the authoring document covers what to do when that
happens.

The consequence is that the reviewing physician is not checking an expansion of their
own ground truth. They are authoring the ground truth in review, one field at a time,
which is slower and needs a different frame of mind: read every number as a proposal,
not as a transcription.

Read `CHFE-review-packet.md` before anything else. It lists the fields awaiting primary
sign-off, the clinical calls most likely to be wrong, and the reference verification
status.

**When a physician does write the seed retrospectively**, replace this file with the
section 3 template that `engine/new_case.py` generates, fill it in independently of the
case file, and then diff the two. Anything in the case file that the seed does not
support is an invented fact and should be removed rather than reconciled.

## What a person decided

- 28 October 2026, Aakash Setty: only the nitroglycerin infusion and the nitroprusside drip set `nitrate_given` and move the phase. Sublingual nitroglycerin and the intravenous bolus lift the saturation by two for 60 seconds (timed flag `nitrate_bolus_acting`, one shared key, a repeat dose refreshes and does not stack), then the nurse says it has worn off and that the effect is sped up in this case. A bolus no longer holds off the four-minute tiring. The stabilizing and improving phases author a saturation of 93, which the monitor shows as 97 with the mask's four. Teaching choices, not physician reviewed.
- 27 October 2026, Aakash Setty: pressors the case does not author now move the monitor by the catalog default (`catalog/default-vital-effects.json`, display only, no change to phases, tags or scoring). Here `norepinephrine_infusion` carries `"vital_effects": []`, because it sets `pressor_running`, which moves the phase, and that phase's vitals already carry the rise. Push-dose epinephrine takes the default.

- 11 October 2026, Aakash Setty: the formal transthoracic echocardiogram (`echo_formal`)
  is removed from the case: the action, its result (no sonographer available, booked for
  the morning) and its place in the debrief's domain list. A formal echo is not used in
  this simulator. It was a neutral, uncataloged action.
- 11 October 2026, Aakash Setty: every consultant answer over 40 words is shortened to 40 or fewer (authoring 9.5), keeping what the consultant thinks, what to do now and the disposition or callback. Wording by a model. Rule order, conditions, tags and debrief notes are unchanged. Not physician reviewed. Twelve of thirteen answers changed (cardiology, critical care, nephrology). Dropped: continuing carvedilol and the repeat echocardiogram (cardiology), the quoted systolic of 188 and saturation of 85 (critical care), and nephrology's list of dialysis indications, which its debrief note still gives. Physician review question CHFE-16 quotes the old wording.
- 23 October 2026, Aakash Setty: the handover is scored on one or two major diagnoses and nothing minor. Here the primary and hypertensive emergency. Moved to `minor_diagnoses`, credited if named and never penalized if left out: cardiogenic pulmonary edema, acute hypercapnic respiratory failure and hyponatremia. Which diagnosis stayed scored was a model's pick, accepted by the author. Explanations unchanged. Not physician reviewed.
- 29 October 2026, Aakash Setty: a correct run is not marked down. Sublingual and IV
  nitroglycerin boluses and nitroprusside are neutral, and nitroprusside counts as the
  nitroglycerin infusion before the tube. The mask or a tube counts as the non-rebreather
  (catalog expectation credit). A liter of crystalloid or norepinephrine at 188/104 no longer
  halts: ten seconds later he moves to impending respiratory failure, said by the nurse, and
  the mask and a drip still bring him back. Metoprolol, diltiazem and dobutamine still halt.
  A nitroglycerin bolus lowers his pressure by 20/8 for its minute. The arterial pO2 in
  stabilizing and improving is 88, to fit a saturation of 97. The post-intubation text, the
  norepinephrine note and both consultants name the nitrate only if a drip ran. The
  crystalloid note agrees with its discouraged tag. An early diuretic takes him to improving
  the moment he stabilizes (engine). US usage in learner text. Values and wording by a
  model. Not physician reviewed.
- 30 October 2026, Aakash Setty, from playing the case: the bedside lung and cardiac
  ultrasound reads are shortened to chart lines (each under 40 words, same findings,
  numbers and severity words). The non-rebreather raises the saturation by two
  while on. It shares the positive-pressure key, so the mask and BiPAP do not stack. Values
  and wording by a model. Not physician reviewed.
- 30 October 2026, Aakash Setty: every case answers a greeting or an open question ("What's going on?") with a clear history of the present illness, the `presenting_story` topic (authoring 8.2). This case's answer was written by a model from its own onset, progression and character answers and its arrival handover, and stops short of what the case keeps behind its own questions. The wording is not physician reviewed.
