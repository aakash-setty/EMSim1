# AFRVR review packet

**Read this before anything else in the pack, and before showing this case to a learner.**

Atrial fibrillation with a rapid ventricular response, complicated by acute decompensated
heart failure on a newly recognised reduced ejection fraction and cardiogenic pulmonary
oedema. Sixty-eight year old man, EMS to the resuscitation bay.

**Nothing in this pack has been reviewed by a physician.** The clinical seed came from
one; the case file did not.

---

## 1. What came from you and what came from a model

Unlike the reference case, this one had a real seed. `AFRVR-SEED.md` holds it. The
division:

**Yours, and unchanged in the case file:**

- the diagnosis and the framing that the arrhythmia and the cardiomyopathy are each
  plausibly cause and consequence of the other
- the presenting vital signs: HR 160 irregular, BP 132/78, RR 30, SpO2 88% on room air,
  temperature 37.0
- the presenting appearance, including that he can still speak in full sentences, which
  is why the arrival phase carries full-length interview answers and only the respiratory
  failure phase carries clipped ones
- the physical findings, and the pertinent negatives among them
- the ECG: AF with RVR at about 160, no STEMI
- the laboratory values: Na 138, K 3.7, Mg 1.6, creatinine 1.0, unremarkable CBC, a
  troponin minimally elevated without a dynamic pattern, normal TSH
- the POCUS findings: EF 30 to 35 percent with global hypokinesis, no effusion, no RV
  catastrophe, diffuse bilateral B-lines
- the six critical actions, as observable behaviours
- the diltiazem nuance, including that it must not halt the case
- the accepted rate-control options and the accepted anticoagulants
- the target endpoint, including that remaining in atrial fibrillation is not a failure
- the disposition, including the conditional about weaning
- the three wrong paths and their teaching points
- the three simulation instructions: positive pressure raises the saturation over a
  minute, furosemide moves nothing, and all three anticoagulants are accepted

**A model's, and awaiting your signature:**

- every reference interval in every laboratory payload
- every debrief note and every cross-cutting teaching point
- every reference, none of which has been checked against its source
- every deadline, every vital-effect size and every phase transition delay
- the six phases and their vital signs, which are an expansion of your endpoint and your
  three wrong paths rather than something you supplied
- the arrival handover and the whole interview bank apart from the history in your seed
- the consultant scripts
- the exam findings, which expand your list of physical signs into twelve manoeuvres
- the disposition and diagnosis alternatives and their explanations

---

## 2. The five clinical claims most worth arguing with

**2.1 Four minutes without positive pressure, and he starts to tire.** Two time-guarded
transitions, both at 240 seconds, both guarded on `NOT flag on_niv set`, one from arrival
and one from the rate-controlled-but-congested phase. The claim is that a man at a
saturation of 88 percent, a respiratory rate of 30 and a ventricular rate of 160 begins to
fail inside four minutes if nothing is done for his breathing. That is compressed against
real disease tempo in the same way the five-second laboratory turnaround is, and the
honest version is that he is on a trajectory that ends in intubation and a case cannot
spend twenty minutes demonstrating it. **Each deadline is one integer in the transition.**
`AFRVR-deterioration-timeline.md` section 1 shows both with their guards and their
prompts.

The second of the two is the more debatable. A patient whose rate has been brought from
160 to 108 has better diastolic filling and might reasonably be argued to tire more slowly
than the one at 160. It is set to the same four minutes deliberately, so the case does not
teach that treating the rate buys time that has not been shown to exist. If you disagree,
lengthen it.

**2.2 Sixty seconds for rate control to work.** Both rate-control transitions carry
`after_seconds: 60, measured_from: guard_true`, so the ventricular rate falls about a
minute after the drug rather than on the click. Sixty seconds is already a compression:
intravenous metoprolol takes several minutes, amiodarone longer, and digoxin considerably
longer than either. It is the same number for all three agents even though their real
onsets differ by an order of magnitude. Representing that difference needs three separate
case actions and three separate transitions, and the cost is that the critical action can
no longer be "rate control" as one act. **That is a real trade and it is yours to make.**

**2.3 Diltiazem drops the systolic pressure twenty points and the diastolic ten.** Your
instruction was that a learner who gives it before knowing the ejection fraction must not
be punished with a collapse. Twenty points brings the stabilised phase from 124 to 104 and
the arrival phase from 132 to 112, which lands inside the 100 to 110 systolic range you
specified for wrong path two. It comes on over fifteen seconds and does not wear off
inside the case. **It is a teaching choice, not a modelled quantity**, and the review
matrix cannot show it because effects are invisible there.

**2.4 Positive pressure buys eight points of saturation, in four steps over a minute.**
Your instruction was that the number should climb over about a minute of game time. The
engine cannot ramp a single effect, so the case authors four separate two-point effects at
zero, twenty, forty and sixty seconds, each with its own key so they stack, all guarded on
not being intubated. Every non-terminal phase's authored saturation is therefore the
**unsupported** baseline: 88 at arrival, 88 in the breathing-supported phase, 89 in the
stabilised phase, 86 in the rate-controlled phase, 82 in respiratory failure. With the
mask on, the stabilised phase reads 97, which is inside the 94 to 97 you specified.
**If you change a phase's saturation, check whether you meant the number with the mask on
or off.** Eight points and one minute are both teaching choices.

**2.5 A crystalloid bolus halts the case, and it is the only thing that does.** Your brief
named no harmful action. Without one the halted phase is unreachable and the case can
teach nothing about an action that must not be taken, so one was added: a litre of
crystalloid in a man with an ejection fraction of 30 to 35 percent and a flooded lung. It
is tagged harmful in every phase except stabilised and intubated, where it is discouraged,
and it covers the whole crystalloid equivalence group so Ringer's and the 500 mL bag are
not escape hatches. **Halting the case is the strongest statement this system makes.** If
you think a single litre in this patient is survivable, downgrade it to discouraged and
accept that the case then has no halting action.

---

## 3. What the deterioration timeline found, and what it changed

The timeline generator (`engine/deterioration_timeline.py`, written for this case and now
case-agnostic) prints every narration line against the vitals of the phase it introduces.
Two contradictions turned up that no validator can see:

**The rate-control narration quoted a number that was wrong in one of its two
destinations.** It said "around a hundred and ten", against destinations at 108 and 104.
Rewritten to name no number.

**The respiratory failure phase read as a rate *rise* to a patient whose rate had been
controlled.** One vitals block per phase, and two routes in: an untreated patient going
from 160 to 166 as he tires, and a rate-controlled patient going from 108. The second
would have watched his rate jump to 166 on a monitor with a nodal blocker running. The fix
is a heart-rate effect of minus 35 on the rate-control action, guarded on that phase, so
the second patient reads about 131. **This is a workaround for one-vitals-block-per-phase,
not physiology**, and if you would rather see it as its own phase that is a seventh
clinical phase and puts the case over the section 3.3 ceiling.

**The do-nothing trajectory ends at respiratory failure and not in an arrest.** That was
your instruction. No transition in this case carries `allow_time_to_terminal`, and an
engine assertion enforces it. A resident who does nothing at all for twenty minutes
reaches respiratory failure at four minutes and stays there. Whether an untreated patient
should be able to sit in respiratory failure indefinitely is a teaching decision rather
than a physiological claim, and it is worth making deliberately.

---

## 4. The three places this case departs from your brief

**4.1 Magnesium replacement is tagged recommended, not critical.** Your critical action
four bundled correcting the hypomagnesaemia with the loop diuretic. The engine computes
the set of critical actions a phase expects once, on entry to that phase, so a tag that
only becomes critical after the magnesium level has resulted can never appear in the
missed list, and an unconditionally critical tag tells a resident who never had reason to
suspect hypomagnesaemia that they missed a critical action. The teaching is carried in the
debrief note and in the laboratory comment instead.

**To overturn this**, change the tag on `magnesium_sulfate_bolus` in `AFRVR-case.json`
from `recommended` to `critical` and give it a nurse prompt. Nothing else has to change.

**4.2 Attaching the monitor and obtaining intravenous access are scored as critical
actions.** Your six do not include them. They are critical here because the simulator
shows no vital signs at all until a monitor is attached, so in a case whose entire
management hinges on a rate and a rhythm it is the first diagnostic act rather than
housekeeping; and because every intravenous drug in the case is gated behind a line.
**The case therefore has nine critical actions rather than six**, and the debrief's
critical-action list is longer than your brief implies.

**4.3 A harmful action was added.** See 2.5.

---

## 5. Rate control and anticoagulation are each scored as one act, not as a choice of drug

Your brief accepts digoxin, an appropriately selected beta blocker or amiodarone for rate
control, and prefers a DOAC while accepting enoxaparin or a heparin infusion for
anticoagulation. The engine scores a named action, not a category, so the case uses
catalog **coverage groups**: `digoxin_bolus` covers `amiodarone_bolus_infusion` and
`metoprolol_bolus`, and `apixaban` covers `enoxaparin` and `heparin_bolus_drip`. Each entry
keeps its own button and its own name; they share one tag, one flag and one debrief note.

**What this costs, and it is the item in this packet most likely to bother you.** The
three rate-control agents are not scored differently from each other. A learner who pushes
metoprolol into a man at a saturation of 88 percent with a respiratory rate of 30, before
any positive pressure, is credited with the critical action and reads the caveat only if
they open the expander. Your own brief says aggressive beta blockade in active pulmonary
oedema is not the goal, and the case cannot express "acceptable, but the least comfortable
of the three, and worse before the breathing is supported" as a tag.

**The alternatives, none of them free.** Splitting metoprolol out as its own action with a
phase-dependent tag makes the ordering explicit and means a learner who chooses it is told
they missed the critical action, which is a false negative. Adding a sixth tag tier
between recommended and critical is an engine change and a change to every case. Leaving
it as it is means the discrimination lives in the debrief note. The note is written to do
that work and you should read it and decide whether it is enough.

Esmolol and propranolol are deliberately **not** in the group. Each is its own case action
tagged discouraged with its own reasoning, so the group is not a blanket endorsement of
beta blockade.

Two catalog entries were added for this case on your instruction and are marked
`source: author-supplied, not in screenshots` in `catalog/action-catalog.json`: **apixaban
and enoxaparin**, because the catalog's only anticoagulant was heparin. **Digoxin** was
added for the same reason on the rate-control side. Before this case the catalog offered
no rate-control agent for a patient in whom calcium channel blockade is contraindicated.
The catalog version moved from 0.1-draft to 0.2-draft. **If your real interface does not
have these three buttons, this is the thing to tell us**, because the catalog is supposed
to be a transcription of it.

---

## 6. The diltiazem decision, which is the case

Tagged `discouraged` in every phase, with a rule list that distinguishes the two situations
so the review matrix shows them:

| when | tag |
|---|---|
| the cardiac ultrasound has resulted | discouraged |
| otherwise | discouraged |

**Both rules resolve to the same value, and that is a limitation rather than a mistake.**
The five-tier vocabulary has nothing between recommended and discouraged, so "a defensible
first move that still costs you a point" and "an error of not updating" cannot be
separated by a tag. The difference is carried entirely in the debrief note, which is
written in two halves for exactly this reason, and in the blood pressure the learner
watches fall on the monitor.

The engine also cannot score the same action twice, differently. A learner who gives
diltiazem before the ultrasound and again after it has one entry in the debrief, tagged
from the second administration. **If you want the second dose to be scored as the error
your brief calls it**, the honest way to do it in the current engine is a phase, and the
case is already at the six-phase ceiling.

One engine change was made in service of this: `discouraged` actions were defined in the
specification, authored by the second case on thirty-one tag rules, recorded on the
timeline, and then **read by nothing**. The debrief surfaced critical, recommended,
harmful and the neutral traps, so a discouraged action produced no output at all. It now
has its own debrief section. That was a live defect in the reference cases as well as a
blocker for this one.

---

## 7. What the interview matcher does on this case, and it is not good

Held-out set: `AFRVR-matcher-eval-questions.json`, 47 in-scope phrasings stratified by
register, 5 excluded as genuinely ambiguous, and **30 out-of-scope questions**, which is
the floor authoring section 10.6 sets and which neither earlier pack meets. None of these
phrasings appears in any variant list. Measured on the shipped lexical matcher with the
embedding model off, which is how it will run on a hospital network.

| register | correct |
|---|---|
| paraphrase | 16/20 |
| shorthand | 6/12 |
| typo | 6/6 |
| conversational | 2/8 |
| compound | 1/1 |
| **in scope, total** | **31/47** |
| wrong topic | 9 |
| fell through | 7 |
| **wrong topic on a management-changing topic** | **9** |
| **out-of-scope correctly refused** | **11/30** |

**The out-of-scope number is the finding.** Nineteen of thirty questions this case does
not cover received a confident, specific and wrong answer. "Have you noticed any blood in
your stool" returns the leg-swelling answer. "What is your favourite colour" returns the
cough answer. "Have you ever had a blood transfusion" returns the anticoagulant history.
This is the known behaviour described in section 10.6, made worse here by a large variant
space: 570 variants across 38 topics is more than either earlier case, and more surface
for a spurious lexical match to land on. It is the strongest evidence yet for the
proposition in section 10.6 that variant expansion trades out-of-scope rejection for
recall, and it is a reason to consider re-enabling the semantic veto rule for this case.

**Nine wrong topics on management-changing topics is also bad**, and a wrong topic is
invisible to the learner in a way a fallthrough is not. The conversational register is
where it concentrates: "I just want to check, are you allergic to anything?" returns the
code-status answer.

**This set has not been used to tune anything.** The obvious next step is to expand every
topic's variant list into clinical shorthand, because the case's 570 variants are written
almost entirely in lay register and the shorthand arm scores 6 of 12. Doing that will
improve these numbers and will also spend this set: a new held-out set has to be written
before any number is quoted again. Section 10.6 is explicit that tuning against a held-out
set and then quoting the result measures memorisation rather than coverage.

**Neither this set nor its expected topics was written by a resident or by the case
author.** The expected topic on each row is a drafting judgement. Review the rows before
quoting any of these numbers outside this pack.

---

## 8. The per-key review matrix

`AFRVR-review-matrix.md`, 148 keys. **Read it in full.** On the reference case, four
clinically wrong resolutions raised no error anywhere and were found only by reading it.
Pay closest attention to:

- the four keys whose rule lists mix a phase rule with a flag rule: `exam_pulm`,
  `ultrasound_lung`, `magnesium_level`, and the consultants. A permanent flag set in an
  early phase is still set in a later one, and a flag rule above a phase rule returns the
  improved value to a patient who has since deteriorated.
- everything in the `respiratory_failure` column, which is the branch nobody plays on
  purpose.
- the consultant tiers. Cardiology has five, keyed on whether the ECG and the cardiac
  ultrasound have been ordered, are pending, or have resulted. The rule that fires when
  the ultrasound has resulted but the ECG has not is the one most likely to be wrong.

Two things the matrix cannot show and you have to check by hand: the vital effects, which
depend on when a drug was given rather than on which phase you are in, and the narration
lines, which are in the deterioration timeline instead.

---

## 9. Reference verification: none

Every reference in this pack carries `[UNVERIFIED in this pack, confirm before release]`.
The interface strips the marker before display; the case file and this packet keep it. The
citations are 3CPO, the Cochrane review of non-invasive ventilation in cardiogenic
pulmonary oedema, DOSE, RACE II, LOMAGHI, and the 2023 ACC/AHA/ACCP/HRS atrial fibrillation
guideline. **A plausible-looking citation to a paper that does not say what is claimed will
be believed by a learner.** Check them.

Claims in the debrief notes that rest on contested or thin evidence, and that say so in
the note rather than presenting a clean message:

- non-invasive ventilation reduces intubation and mortality: meta-analytic support,
  contradicted by 3CPO, the largest single trial. The note claims only faster
  physiological improvement.
- intravenous magnesium as an adjunct to nodal blockade in rapid atrial fibrillation:
  small randomised trials and a meta-analysis of them, not a definitive trial.
- the lenient rate target of under 110: RACE II enrolled patients with permanent atrial
  fibrillation, not acutely decompensated ones, and the note says the optimal target in
  acute decompensated HFrEF is less certain.
- the CHA2DS2-VASc score itself: the note gives four and says a reviewer who counts three
  reaches the same decision, because whether the vascular disease point applies turns on
  how the coronary disease is documented.

---

## 10. Sign-off checklist

Section 14.3 of the authoring requirements. The structural half is done; the clinical half
is yours.

**Structural, done and reproducible:**

- [x] validator clean: 0 errors, 1 warning, the same warning both earlier cases carry
      (`handoff_submit` has no catalog entry)
- [x] 30 authored scenarios walk end to end, including the do-nothing path, both
      deterioration branches, each rescue, every blocked prerequisite, every route to the
      halting action, and both coverage groups
- [x] 196 engine assertions pass, including the four-step saturation ramp read off the
      monitor at each step, the diuretic moving nothing, and the sixty-second rate-control
      delay firing with no further action taken
- [x] 26 validator negative tests pass
- [x] abnormal flags agree with every parseable reference interval
- [x] every phase reachable, every non-terminal phase has a satisfiable exit, no cycle of
      time edges, no transition ends the case on the clock
- [x] arrival handover: two sentences, 34 words, no vitals, no past history, no
      medications, no allergies, no pertinent negatives, no word naming a diagnosis

**Clinical, and none of it is done:**

- [ ] every reference interval is right for the assays you are modelling
- [ ] the two 240-second deadlines are claims you will defend
- [ ] the 60-second rate-control delay is a claim you will defend
- [ ] the eight-point saturation gain and its one-minute tempo are what you meant
- [ ] the twenty-point systolic fall on diltiazem is what you meant
- [ ] a crystalloid bolus in this patient is genuinely lethal, or it is not and the tag
      should change
- [ ] the coverage groups are clinically sound, particularly binding metoprolol to the
      same tag as digoxin
- [ ] magnesium replacement is correctly recommended rather than critical, or it is not
- [ ] every debrief note teaches something correct
- [ ] every reference has been checked against its source
- [ ] the review matrix contains no clinically wrong resolution
- [ ] **the case has been played start to finish in the interface**, including the
      harmful halt and both deterioration branches. This is the only step that can catch
      an interface defect, and it is also the only thing that will tell you whether the
      case is any good to sit through.

---

## 11. Engine changes this case required

Recorded here because they affect the other two packs. All are in `engine/` and none names
a case.

1. **`discouraged` was scored by nothing.** Defined in the spec, authored by MGCA on 31 tag
   rules, and absent from the debrief. It now has its own section.
2. **A covered sibling did not satisfy the covering action's critical expectation.** Taking
   Ringer's when saline is the covering action set the flag, advanced the phase and
   borrowed the tag, but left the debrief reporting the critical action as missed. This
   affected MGCA's fluid group as well.
3. **`expectation_label`** was added so the debrief can name an act rather than one of its
   routes. Without it a resident who gave amiodarone was told they had completed "Digoxin
   bolus".
4. **A `guard_true` transition scheduled no deadline of its own**, so it could only ever
   fire on the resident's next action. A case authoring "this takes a minute to work" left
   a resident who gave the drug and then waited watching nothing happen. Fixed in the
   engine and, separately, in `sim_runner.py`, which measured guard_true deadlines from
   phase entry.
5. **The validator warned that a prompt was stranded** whenever a phase had any timed exit,
   including a `guard_true` one whose clock has a different origin. It fired nine times on
   this case, all wrong.
6. **The case-agnostic engine suite hard-coded a case id** (`iv_access_peripheral`) in its
   equivalence-group assertion, so the assertion failed in any pack that names its line
   differently. The action is now discovered from the loaded pack.
7. **`alternative_diagnoses` gained a `verdict` of `acceptable_with_qualification`**,
   mirroring the dispositions, because this case's formulation has two halves and the
   engine scores one id. Selecting acute decompensated heart failure with reduced ejection
   fraction now reads "defensible" rather than "incorrect".
8. **`engine/deterioration_timeline.py`** is new. Section 14.2c required the artifact and
   there was no tool; MGCA's was written by hand. Both packs are now generated.
