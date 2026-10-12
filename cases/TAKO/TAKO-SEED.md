# TAKO seed and provenance

Takotsubo cardiomyopathy with outflow obstruction in a 68-year-old woman, presenting as an
anterior ST-elevation infarct. Drafted by a language model on 6 October 2026 at the
request of Aakash Setty. Audited by models on 6 October 2026 and corrected by a model on
7 October 2026. **No physician has reviewed this pack.** Authoring requirements section 17
applies. Read every number as a proposal.

## 0. What a person decided

Aakash Setty, 6 October 2026:

| Decision | What was decided |
|---|---|
| Handoff diagnosis | ST-elevation infarct is the correct working diagnosis. Takotsubo named first is defensible. The angiogram is revealed in the debrief |
| Norepinephrine | Left neutral and accepted, because the evidence is contested |
| Fluid | She is written with clear lungs so that a fluid bolus is right, and the debrief says wet lungs would change it |
| Catheterization lab | A button that appears in this case only |
| Cardiology | The nurse recommends cardiology whenever the pressure falls. The cardiologist gives the right treatment outright and can take over. "This is a hard case" |
| Cardiology availability | The cardiologist is busy until both an ECG and a bedside echo have been done. An earlier call is refused with the reason |
| Case map | Approved as presented: four states, a scripted fall at 180 seconds, nitrate leads to the obstructed state, the echo is not required for treatment to work |

Everything else is model output.

### 0.1 Where the audit and a recorded decision disagree

The table above was not changed on 7 October 2026. Three notes for the owner.

- **The catheterization laboratory button stays case-only.** The audit (finding 6) said
  the authoring document forbade a case-only action. Authoring 7.1 was changed in v0.24
  and now permits one by recorded decision. Its four conditions are met: the decision is
  in the table above with a name and a date, the binding row has a null catalog id with a
  placement and a narration, the action has a tag and a debrief note, and this paragraph
  states the cost. **The cost: a button unique to one case tells the learner it matters,
  and it is not in the voice table.** The second half is now covered by eleven
  `voice_phrases` on the case action, each tried in the built simulator. The first half
  cannot be fixed while the button is case-only.
- **Norepinephrine is neutral and satisfies the vasoconstrictor.** The audit (finding 25)
  asked whether it should also move the pressure. Nothing was changed. See open
  question 9.
- **Nothing is harmful and nothing ends the case except a handoff.** The brief for the
  7 October work states this as the owner's decision. It is not a row in the table above
  and should be added by the owner if it is one. Nothing in the pack conflicts with it.

The 180-second fall, the 240-second deterioration and the 90-second takeover were not
moved.

### 0.2 Model choices made on 7 October 2026, for the owner to confirm

Each of these changes what a learner sees. None was decided by a person.

1. **The catheterization laboratory cannot be activated until a twelve-lead has come
   back.** Two prerequisites on the action, written like the cardiology one. With no
   tracing the nurse says "The cath lab will want a twelve-lead before they call the team
   in. Do you want one now?" With one still printing she says "The twelve-lead is still
   printing. The cath lab will want to see it before they call the team in." A refused
   press sets no flag and earns no credit. Before this, a press with no ECG earned the
   critical action while the laboratory asked whether there was one.
2. **The fluid prompt is at 45 seconds and the vasoconstrictor prompt at 60**, down from
   60 and 80. Section 4.1 says why.
3. **A new rule at 180 seconds.** A nitrate or an inotrope given less than ten seconds
   before the scripted fall, with fluid and a vasoconstrictor already running, now meets
   the fall first and acts from the obstructed phase. Section 4.2.
4. **A nitrate on arrival costs her pressure once.** The 12-point effect is guarded off
   in the obstructed phase by name. Section 7, limit 1.
5. **An inotrope's effect in the steadied phase ends once cardiology has been called.**
   Section 7, limit 2.
6. **Push-dose epinephrine counts as the inotrope.** Section 7, limit 5.
7. **Left ventricular outflow tract obstruction is a credited additional diagnosis.**
8. **Five patient answers change once she is steadied.** Section 3.7.
9. **Both gases, the capillary glucose and the chest film are authored** from this
   pack's own numbers and notes. Section 3.6.
10. **Two abnormal flags changed**: a dry mouth, and the airway finding in worsening
    shock.
11. **The murmur is graded by phase without a comparison**: harsh on arrival, loud when
    the pressure falls, very loud in worsening shock, soft once steadied. Before, two
    findings said "than before" to a learner who might never have listened earlier.
12. **Four studies with authored results are bound as neutral case actions** so that
    each has a debrief note: the chemistry, both gases and the capillary glucose.

## 1. Learning goals and where each is acted on

| Goal | Where |
|---|---|
| Treat ST elevation as an occlusion whatever the story | Arrival. The daughter argues it is nerves. ECG, aspirin and activation are prompted only late |
| Look at the heart before treating cardiogenic shock | The murmur and the echo are available and never offered |
| Treat outflow obstruction the right way round | Nitrates and inotropes are available and show their effect. Fluid and a vasoconstrictor show theirs |

## 2. Phases

| Phase | HR | BP | Reached | If nothing is done |
|---|---|---|---|---|
| presentation | 115 | 96/60 | arrival | The pressure falls at 180 seconds whatever is done |
| obstructed | 124 | 82/50 | 180 seconds, whatever is done. Or ten seconds after a nitrate | Worsening shock after 240 seconds without both fluid and a vasoconstrictor |
| shock_untreated | 138 | 70/42 | obstructed for 240 seconds without both fluid and a vasoconstrictor | Nothing. No clock leaves it |
| shock_worse | 138 | 70/42 | ten seconds after an inotrope, from any earlier phase | Nothing. No clock leaves it |
| steadied | 104 | 100/62 | fluid and a vasoconstrictor (inotrope stopped if one was given). Or 90 seconds after cardiology is called with a low pressure | Nothing |

The map showed one "worse" state. It is two phases with the same numbers because their
exits differ: the inotrope has to be stopped in one and not the other.

## 3. The seed, sections 3.4 to 3.8

**Model output.** Generated on 7 October 2026 from `case_1_shell.py` to `case_5_handoff.py`
and `build_case.py`, because the audit (finding 15) found these sections missing. A
physician signs this list. The sources are the authority if the two disagree.

### 3.4 The action spine, with every route

**Critical**

| Act | When it is critical | Catalog entries that count | Prompt, easy mode |
|---|---|---|---|
| Attach the monitor | on arrival | `attach_monitor` | 15 s |
| Vascular access | always | `insert_iv` | none |
| Twelve-lead ECG | on arrival | `ecg_12_lead` | 40 s |
| Aspirin | always | `aspirin` | 90 s, on arrival and once steadied, only when the ECG is back |
| Activate the catheterization laboratory | always | `consult_activate_cath_lab` (case-only) | 130 s, only when the ECG is back |
| Bedside cardiac ultrasound | always | `ultrasound_cardiac` | none, on purpose |
| Small crystalloid bolus | pressure low | the `crystalloid_bolus` group: saline and Ringer's, 500 mL and one liter | 45 s |
| Vasoconstrictor with no inotropic effect | pressure low | `phenylephrine_drip`, `vasopressin_drip`. `norepinephrine_drip` satisfies it and keeps its own neutral tag | 60 s |
| Call cardiology | pressure low | `consult_cardiology` | 20 s |
| Stop the inotrope | in the inotrope phase | `stop_dobutamine`, `stop_epinephrine`, `stop_dopamine` | 25 s |

**Discouraged.** Nothing is harmful.

| Act | Every route | What it does |
|---|---|---|
| Nitrate or other vasodilator | `nitroglycerin`, `nitroglycerin_sublingual`, `nitroglycerin_drip`, `nitroprusside_drip` | On arrival she is obstructed ten seconds later. Later it costs 12 points of systolic pressure for two minutes, except in the obstructed phase |
| Catecholamine inotrope | `dobutamine_drip`, `epinephrine_drip`, `dopamine_drip`, `epinephrine_bolus` | Worsening shock ten seconds later, from any phase but steadied. Once steadied it costs 14 points and adds 16 to the rate |
| Loop diuretic | the `loop_diuretic` group, which is `furosemide_40_mg_iv` | 8 points, from 20 to 240 seconds after the dose |
| Thrombolysis | `tenecteplase_tnk_bolus`, `alteplase_tpa` | Nothing on the monitor |
| Beta blocker before the pressure is supported | `esmolol_drip`, `metoprolol_bolus`, `labetalol_bolus`, `labetalol_drip`, `propranolol_bolus` | 10 points and 10 beats for three minutes. Neutral once steadied, where it slows her by 14 |

**Recommended.** A second line. Troponin. Chest film. The monitor and the ECG after
arrival. Cardiology on arrival. Stopping an inotrope outside the inotrope phase.

**Neutral, with a note.** Heparin, clopidogrel, fentanyl, morphine, lorazepam,
norepinephrine, NT-proBNP, lung ultrasound, lactate, chemistry, both gases, capillary
glucose, intensive care consult, and all 14 examinations.

**Traps.** `trap_actions` is empty. Lorazepam was listed, and the debrief printed it under
"Things that looked reasonable and were not" while its own note says a small dose is not
wrong (audit finding 20).

**Routes not bound, by decision pending.** `phenylephrine_bolus` and `vasopressin_bolus`.
See open question 7.

### 3.5 Sequencing

- **Prerequisites.** Cardiology needs a resulted twelve-lead and a resulted bedside echo
  (owner's decision). The catheterization laboratory needs a twelve-lead ordered and then
  resulted (model choice, section 0.2). The catalog's vascular access rule is kept for
  every intravenous drug. Nothing is waived.
- **Follow-up.** One. After any crystalloid bolus the nurse asks at 60 seconds (180 in
  the default mode) whether to listen to the chest. A chest examination, a lung ultrasound
  or a chest film taken after the bolus discharges it. One taken before does not. This
  uses the hidden target in authoring 8.2: each of the three credits a case action named
  `chest_rechecked`, which nothing presses, when `fluids_given` is already set.
- **Order.** The same drug leads to different places in different phases. Fluid and a
  vasoconstrictor do nothing to the phase on arrival and steady her afterwards. An
  inotrope has to be stopped before the pair works.
- **A null `when` in `also_satisfies`.** Norepinephrine credits the vasoconstrictor with
  `"when": null`, which always holds (authoring 6.8, described since v0.22). It keeps its
  own tag, note and heart rate effect.

### 3.6 Key findings

Every number here is model output. Intervals are the ones in the case file.

| Finding | Arrival | Pressure low | Worsening shock | Steadied |
|---|---|---|---|---|
| Heart rate | 115 | 124 | 138 | 104 |
| Blood pressure | 96/60 | 82/50 | 70/42 | 100/62 |
| Respiratory rate | 22 | 24 | 28 | 20 |
| Saturation | 96 | 95 | 93 | 97 |
| General status | Pale and sweating, fist on her chest, daughter at the bedside | Gray and sweating, feels faint | Gray, cold, confused, barely speaking, GCS 14 | Color better, pain easing |
| Murmur (`exam_card`) | Harsh systolic, left sternal edge, louder with Valsalva, softer with legs raised | Loud | Very loud | Soft |
| Capillary refill (`exam_circ`) | 3 s | 4 s | 5 s | 2 s |
| Lungs (`exam_pulm`) | Clear | Clear | Clear | Clear |
| Neck veins (`exam_neck`) | Flat | Flat | Flat | Flat |
| Mouth (`exam_heent`) | Dry, flagged abnormal | same | same | same |
| Lactate, mmol/L (0.5 to 2.0) | 2.6 | 3.4 | 5.8 | 3.6 |

| Study | Result | Abnormal |
|---|---|---|
| Troponin T, high sensitivity | 186 ng/L (under 14) | yes |
| NT-proBNP | 5200 pg/mL (under 125) | yes |
| Chemistry | Sodium 141, potassium 3.9, chloride 104, bicarbonate 22, BUN 29 (7 to 20), creatinine 1.1, glucose 148 (70 to 140) | BUN and glucose |
| ECG | Sinus tachycardia. ST elevation 2 to 3 mm in V2 to V5 and 1 mm in II. ST depression in aVR. None in V1. QRS 92 ms, QTc 470 ms. The report quotes no rate | yes |
| Bedside echo | Apex and mid ventricle do not contract and bulge in systole. Base contracts vigorously. Ejection fraction about 30 percent. Anterior mitral leaflet moves toward the septum in systole (only slightly once steadied). Inferior vena cava small | yes |
| Lung ultrasound | A-lines, no B-lines, no effusion | no |
| Chest film | Lungs clear. Mediastinum not widened. Heart size normal | no |
| Venous and arterial gas | Bicarbonate 22. Lactate as the lactate key in the same phase. Nothing else | lactate |
| Capillary glucose | 148 mg/dL | yes |

**Derived on 7 October 2026, not new claims.** The gas rows repeat the chemistry
bicarbonate and the lactate key. The capillary glucose repeats the chemistry glucose. The
chest film restates this pack's own notes, which cited a normal mediastinum that the
catalog default did not mention. Each carries a `verify` note saying so.

**Not authored, and needed from a physician.** A pH, a pCO2, a base excess, and for the
arterial gas a pO2 and a saturation. No pH could be written without inventing one, so
none was, and the gases show two rows. See open question 12.

### 3.7 Interview ground truth

Every fact is model output.

- 68, retired schoolteacher, widowed five days ago after 41 years. Lives alone now.
  Daughter twenty minutes away and at the bedside. Three children, and grandchildren.
- Crushing central chest pressure for about an hour, at the reception after his funeral.
  Came on all at once while she was standing and talking. Eight out of ten.
- Goes to the left arm and the jaw. Not to the back. Not tearing.
- Nothing changes it: not position, not breathing in, not pressing on it.
- Sweating, cold and clammy. Nauseated, has not vomited. Short of breath, not wheezy.
  Heart racing, regular. Lightheaded when stood up, has not passed out.
- Has barely eaten or drunk for five days. Nothing today.
- High blood pressure and high cholesterol. No diabetes. Amlodipine and atorvastatin,
  taken this morning. No aspirin and nothing for her nerves.
- Gallbladder removed twenty years ago.
- Never smoked. A glass of wine at Christmas. No drugs.
- Father had a heart attack at 70. Mother lived to 90.
- Walks two miles a day and does her own garden. A checkup in the spring found nothing.
- Wants everything done.
- Her daughter says it is her nerves. That is a relative's opinion and the case does not
  endorse it.

**Pertinent negatives, authored as denials in every phase (10 topics).**
No tearing pain and no back pain. No ankle swelling, sleeps flat on one pillow, never
wakes breathless. No fever. No cough. No abdominal pain. No headache. No prior heart
attack, angina or murmur. No blood thinners, stroke, bleed, ulcer, recent operation or
head injury. No allergies, and she can take aspirin. No recent travel.

`past_surgical_history` was marked as a denial and is not one. The mark was removed.

**Answers that change with state.** With a low pressure every topic has a short answer
with the same fact. After an opioid, the character and the severity of the pain ease.
Once steadied, five answers change. **These five were written by a model on 7 October
2026 and await sign-off.** They restate the status line ("pain easing") and the skin
examination ("Sweating has settled") and add nothing else:

| Topic | Once steadied she says |
|---|---|
| `timing_progression` | "It's easing. Not gone, but better than it was." |
| `chest_pain` | "Yes, in the middle of my chest. It's still there, but it's easing." |
| `severity` | "Less than it was. It's easing." |
| `aggravating_relieving` | "It's easing now. Sitting up or lying back makes no difference, and breathing in doesn't change it." |
| `sweating` | "I was drenched. It's settled now." |

The audit proposed a number for the severity ("Maybe a four") and a new answer about
faintness. Neither was taken, because neither restates anything the pack already says.

**Negatives that fall to the fallback today and need a ruling.** See open question 11.

### 3.8 Disposition

- **Correct level of care:** the catheterization laboratory. Intensive care is defensible
  only as the bed she goes to afterwards. Step-down, a ward, observation, discharge and
  transfer are wrong, each with its reason in `case_5_handoff.py`.
- **Correct primary diagnosis:** `dx_st_elevation_myocardial_infarction` (owner's
  decision).
- **Defensible as primary:** takotsubo cardiomyopathy (owner's decision), cardiogenic
  shock, acute coronary syndrome unspecified.
- **Credited beside the primary:** cardiogenic shock, takotsubo cardiomyopathy, and since
  7 October 2026 `dx_left_ventricular_outflow_tract_obstruction`.
- **Wrong, each with an explanation:** non-ST-elevation infarct, panic attack,
  hypertrophic cardiomyopathy, aortic dissection, severe aortic stenosis, pulmonary
  embolism, myocarditis, acute pericarditis.

## 4. Timing

### 4.1 Prompts in both modes

The deadlines in the case file are easy mode's. A case starts in normal mode, which
multiplies every prompt and follow-up deadline by 3 and leaves the clocks alone (authoring
9.7). Counted from the start of the phase:

| Prompt | Easy mode | Default mode | Fires when |
|---|---|---|---|
| Monitor | 15 s | 45 s | on arrival |
| Twelve-lead | 40 s | 120 s | on arrival |
| Aspirin | 90 s | 270 s | on arrival or once steadied, and only if the ECG is back |
| Catheterization laboratory | 130 s | 390 s | any phase, only if the ECG is back |
| Cardiology | 20 s | 60 s | pressure low |
| Stop the inotrope | 25 s | 75 s | inotrope phase |
| Fluid | 45 s | 135 s | pressure low |
| Vasoconstrictor | 60 s | 180 s | pressure low |
| Recheck the chest (follow-up) | 60 s after the bolus | 180 s after it | fluid given, no recheck since |

**What that means for the 240-second deterioration.** Its guard rests on the fluid and
the vasoconstrictor. In easy mode the nurse has asked for cardiology, fluid and a
vasoconstrictor by 60 seconds. In the default mode she has asked for all three by 180
seconds, which leaves 60 seconds to act. Before 7 October 2026 the vasoconstrictor prompt
was at 80 seconds, which is 240 in the default mode, the same instant as the
deterioration, and the nurse never said it (audit finding 27). The owner's 240 seconds
was not moved. `TAKO-tests.js` folds the do-nothing path, the infarct pathway alone,
fluid alone and a vasoconstrictor alone with a multiplier of 3 and checks each warning is
spoken first.

**What it means on arrival.** The fall at 180 seconds is unguarded, so no rule requires a
prompt before it. In easy mode the nurse offers the monitor, the ECG, aspirin and the
catheterization laboratory before the fall. In the default mode only the monitor (45 s)
and the ECG (120 s) can come before it. Aspirin and the laboratory are not prompted on
arrival in the default mode at all. They are next offered once she is steadied, or in
untreated shock (the laboratory, 390 seconds after she enters it). That fits learning
goal 1 as written ("prompted only late") and is open question 16.

The cap is four prompts per phase. With a low pressure the order is cardiology, fluid,
vasoconstrictor, then the laboratory. On an inotrope it is cardiology, stop, fluid,
vasoconstrictor, and the laboratory prompt is the one the cap drops.

### 4.2 Two timed rules pending at once (authoring 5.4)

Model output, worked out from the engine and each row tested in `TAKO-tests.js` with
fractional times. "The pair" is fluid and a vasoconstrictor. A rule timed from its guard
starts its ten or ninety seconds again in each phase.

**On arrival.** Rules in order: inotrope (10 s from the drug), nitrate (10 s from the
drug), a nitrate or inotrope at 180 s, the pair at 180 s, the unguarded fall at 180 s.

| What the learner does | Which rule fires first | Where she ends up |
|---|---|---|
| Inotrope 10 s or more before the fall | the inotrope's | worsening shock on an inotrope |
| Inotrope less than 10 s before the fall, with or without the pair | the 180-second rule | obstructed at 180, worse on the inotrope 10 s later |
| Nitrate 10 s or more before the fall | the nitrate's | obstructed |
| Nitrate less than 10 s before the fall | the 180-second rule | obstructed at 180. With the pair running, steadied 10 s later |
| Inotrope and nitrate at the same instant | the inotrope's, higher in the list | worse on the inotrope |
| Nitrate, then an inotrope inside 10 s | the nitrate's | obstructed, then worse on the inotrope 10 s after that |
| Inotrope started and stopped inside 10 s | the inotrope's still fires | worse on the inotrope, with the stop already counted. Limit 3 |
| Cardiology called on arrival | no rule here | cardiology arrives 90 s after the fall. Limit 4 |

The second and fourth rows are new on 7 October 2026. Before, the pair's rule fired and she
went straight to steadied with the wrong drug acting, 86 over 62 with a rate of 120,
while the nurse said her pressure was holding.

**Pressure low (obstructed).** Rules in order: inotrope (10 s), the pair (10 s), cardiology
(90 s), not treated by 240 s.

| What the learner does | Which rule fires first | Where she ends up |
|---|---|---|
| Inotrope, then the pair inside 10 s | the inotrope's | worse on the inotrope |
| The pair completed and an inotrope at the same instant | the inotrope's, higher in the list | worse on the inotrope |
| The pair, then an inotrope inside 10 s | the pair's | steadied with the inotrope acting. Limit 6 |
| The pair completed less than 10 s before 240 | the pair's. The 240 rule's guard is already false | steadied. She never enters untreated shock |
| The second drug after 240 | the 240-second rule | untreated shock, then steadied 10 s after the drug |
| Inotrope less than 10 s before 240 | the 240-second rule | untreated shock, then worse on the inotrope 10 s later |
| Cardiology called 90 s or more before 240 | cardiology's | steadied by cardiology |
| Cardiology called less than 90 s before 240 | the 240-second rule | untreated shock. Cardiology arrives 90 s after that. Limit 4 |
| Cardiology called, the pair 10 s or more before they arrive | the pair's | steadied by the learner. Cardiology does not take over |
| Cardiology called, the pair less than 10 s before they arrive | cardiology's | steadied, and the nurse says cardiology took over |
| Cardiology called, inotrope 10 s or more before they arrive | the inotrope's | worse on the inotrope. Cardiology arrives 90 s after that |
| Cardiology called, inotrope less than 10 s before they arrive | cardiology's | steadied. The inotrope shows nothing. Limit 2 |

**Untreated shock.** The same rules without the 240-second one, and the same rows.

**Worse on an inotrope.** Rules in order: stopped and the pair (10 s), cardiology (90 s).
Whichever is due first fires. A learner who stops the inotrope and gives the pair less
than 10 s before cardiology arrives is told that cardiology took over.

## 5. Sources and checks

### 5.1 Sources, and how far each was read

| Reference | How it was read | Status |
|---|---|---|
| Ghadri JR, et al. International Expert Consensus Document on Takotsubo Syndrome (Part II): Diagnostic Workup, Outcome, and Management. Eur Heart J 2018 | Through a summarizing tool, by a model, on 6 October 2026. Not opened in full | Its management figure was not read. Quotations not checked against the publisher's text. Not checked by a physician |
| A 2026 review of cardiogenic shock in takotsubo | Opened by a model on 6 October 2026 | **Authors, title and journal were not recorded.** It is the source for preferring phenylephrine. It cannot be checked until the citation is recovered |
| A 2021 case report | Opened by a model on 6 October 2026 | **Citation not recorded** |
| One emergency medicine summary | Opened by a model on 6 October 2026 | **Site and title not recorded** |
| STEMI guidelines, no edition recorded | From memory, by a model. Not opened | Four figures rest on it: a twelve-lead within ten minutes, the artery open within 90 minutes, nitrates held under a systolic of 90, thrombolysis for a delay over about two hours |

The audit (finding 13) asked for full citations. Three could not be supplied, because the
first draft did not record them, and inventing one would be worse than the gap. The case
file's `provenance.reference_status` carries the same list.

**Markers.** Each debrief note that rests on an unchecked source ends with an
`[UNVERIFIED: ...]` marker saying what was not checked. The interface strips these from
action notes, references, timed transition notes and the teaching points. It prints
handoff explanations, follow-up notes, and everything the nurse, the patient and a
consultant say exactly as written, so those carry no marker. Two handoff explanations and
the cardiologist's lines rest on the same sources.

### 5.2 Changed from the approved map after the fact-check (6 October 2026)

- **Beta blocker once steadied is neutral, not recommended.** The consensus document says
  beta blockers may improve obstruction and are contraindicated in hypotension and in
  acute heart failure with a low ejection fraction. She has both.
- **The murmur is louder with Valsalva and softer with legs raised.** "Louder sitting up"
  was wrong. Sitting forward is the position for aortic regurgitation and a rub.
- **The ECG now shows elevation in V2 to V5 and II with depression in aVR.** The first
  draft authored the infarct pattern (V1 to V4, I and aVL) while claiming the opposite.
- **The troponin is no longer called modest.** An early troponin does not separate the
  two. The lower peak shows later.

### 5.3 Checked, and by what

An independent model pass on 6 October 2026 opened the sources above. It was not a
physician review. It found 13 problems, and all of those that could teach something false
were fixed.

Confirmed against an opened source: obstruction in about one in five, treat as an acute
coronary syndrome with aspirin and heparin, no reliable ECG discriminator, avoid inotropes
and nitrates and diuretics in obstruction, cautious fluid only with clear lungs,
recovery of the ventricle in four to eight weeks, and in-hospital outcomes comparable to
acute coronary syndrome.

**Not supported by the consensus document:** phenylephrine and vasopressin. It names
neither. A 2026 review prefers phenylephrine and allows norepinephrine with careful
titration. Vasopressin is an extrapolation. The debrief says this.

Not verified by anyone: every STEMI guideline number, the figure in the consensus
document that summarizes management, and the murmur's response to maneuvers in takotsubo.
**A physician should read that figure before sign-off.**

A second set of model audits on 6 October 2026 compared the pack with the authoring
document, the engine and the catalog. It found 29 problems in the pack and more in the
shared files. Section 6 is what was done about them.

## 6. What changed on 7 October 2026, and why

A model made these changes. No clinical fact was added. Section 0.2 lists the ones a
learner would notice.

| Audit finding | What was wrong | What was done |
|---|---|---|
| 1, 18 | The nurse quoted numbers the monitor did not show, because a vital effect was acting when the line was spoken. One line described a dip that never happened | No timed narration quotes a figure. Each keeps the direction. The nitrate's effect is guarded off in the obstructed phase. The test now folds each line with each effect-bearing drug and reads the monitor |
| 2 | After cardiology took over from an inotrope the monitor read 86 over 62 for the rest of the case | The inotrope's two effects end once cardiology has been called |
| 3 | Two prompts said she had worsened when she had not | Both describe the state: "Her pressure is low" and "That inotrope is not helping her" |
| 4 | Two prompts cited an ECG nobody had ordered | Both are guarded on the twelve-lead having resulted |
| 5 | A chest exam before the bolus discharged the recheck | The hidden target in authoring 8.2. Tested both ways |
| 6 | Case-only button against the old rule | Kept, by the owner's decision. Section 0.1 |
| 7 | A sentence about phenylephrine read as if about the balloon pump | Reordered |
| 8 | The out-of-scope bank refused questions she can answer | Stroke, back pain and blood in the stool are no longer refused. "Any sweats?" belongs to sweating |
| 9 | No held-out questions and no measurement | Written before expansion, measured, in the review packet |
| 10 | She said the pain had not let up while her status line said it was easing | Five steadied answers |
| 11 | Push-dose epinephrine and the diuretic group were unbound | Bound. Push-dose phenylephrine and vasopressin are open question 7 |
| 12 | Two deterioration notes restated the deadline | Both now teach the physiology and name the treatment |
| 13 | Unmarked guideline figures, one blanket reference sentence | Markers on each note, a list per reference, section 5.1 |
| 14 | Missing step 8 routes | Eight scenarios and matching tests |
| 15 | SEED and packet lacked required sections | This file and the packet |
| 16 | The laboratory credited an activation with no ECG and had no pending tier | Two prerequisites. Section 0.2 item 1 |
| 17 | Negatives that fall to the fallback | Open question 11 |
| 19 | The inotrope guard cannot see a stop | Recorded, limit 3, and the line quotes no figure |
| 20 | Lorazepam listed as a trap against its own note | `trap_actions` is empty |
| 21 | "Decided by the directing physician" printed to the learner | Moved to a note field |
| 22 | A reported operation marked as a denial. Four facts missing from the background | Mark removed. Facts added to the background and to 3.7 |
| 23 | Comments on reports are never shown | Removed. The debrief notes hold the interpretation. Two lab comments that named the diagnosis or another result were removed as well |
| 24 | The chest film was a catalog default that two notes misquoted | Authored from those notes |
| 25, 26 | Verdicts | Open questions 9 and 10 |
| 27 | The default mode | Section 4.1 |
| 28 | Stale notes and counts | Corrected |
| 29 | Small inconsistencies | Airway finding by phase, dry mouth flagged, no "than before", BUN not urea, the chemistry bound, US usage, the stop note says part of the pressure returns |

From the catalog audit: the gases and the capillary glucose (5.1 to 5.3), the spoken
phrases (3.8), the diagnosis (4.1), the misplaced variants (6.2) and the held-out file
(6.7). The ECG report no longer opens with a rate, because three effects on the heart
rate have no end (authoring 11.4).

Also on 7 October 2026: the nurse says "that inotrope" and "a vasoconstrictor" where she
used to say "that infusion" and "phenylephrine", because one case action speaks for
several drugs (authoring 9.1). And the handoff explanation for cardiogenic shock no longer
says the shock "got worse with inotropes" to a learner who gave none.

## 7. Known gaps and limits

Each of the first seven is pinned by a test in `TAKO-tests.js` so that it cannot change
unnoticed.

1. **A nitrate given while she is obstructed shows nothing more on the monitor there.**
   An effect's guard is read against the state now and cannot see where the drug was
   given. The obstructed phase's own numbers are the fall a nitrate on arrival causes, so
   the effect is off in that phase by name. The tag and the note still apply. In worsening
   shock or once steadied the 12 points show.
2. **After a cardiology call, an inotrope in the steadied phase shows nothing.** A
   takeover stops the inotrope, and a timed transition can set no flag, so the effect is
   guarded on the call instead. Two side effects. An inotrope started after a call shows
   no cost once she is steadied. And a call made in the steadied phase with an inotrope
   running takes its effect off the monitor without the learner stopping it.
3. **An inotrope stopped inside its ten seconds still makes her worse.** The guard is
   positive only, because the validator reads a negated flag in a timed guard as a
   deterioration on inaction. The stop is already counted, so she then needs only the
   pair.
4. **Cardiology's ninety seconds starts again in each phase** (authoring 5.1). Called on
   arrival, they arrive 90 seconds after the fall. Called less than 90 seconds before the
   240-second deterioration, they arrive 90 seconds after it, up to 180 seconds after the
   call.
5. **A push dose of epinephrine is modeled like the infusion.** It moves her to the
   inotrope phase and has to be "stopped" with one of the three stop actions. The nurse's
   lines say "that inotrope", not "that infusion", so they are true of both. A real push
   dose wears off on its own. Open question 8.
6. **An inotrope started in the ten seconds after the pair is complete does not prevent
   the steadied phase.** She is steadied with the inotrope's cost on the monitor, which
   is the same as giving it once steadied. The nurse's line stays true: the pressure is
   up and the rate is down from the phase before.
7. **Once the chest has been rechecked after fluid, a second bolus asks for nothing.**
   The hidden target stays satisfied.
8. **The narration test acts one extra drug at a time.** Three wrong drugs together (a
   nitrate, then the pair, then an inotrope inside ten seconds) can make "her pressure is
   up" false by a few points. Not tested and not fixed.
9. **The gases have two rows.** See 3.6.
10. **The interview matcher.** Six wrong-topic misses on management-changing topics in the
    held-out set. They are named in the review packet. Nothing was tuned against them.
11. **"Has it been getting better or worse?" is split at "or" by the matcher** and answered
    by two topics. This is the engine's compound-question handling, on a canonical
    question. Not a pack fault, and reported.
12. **"Do you have a garden?" is refused**, although she says elsewhere that she does her
    own garden. The bank entry carries a tag about tick exposure, which this pack cannot
    honestly claim. It needs a tag of its own in the shared file.
13. **The cardiologist mentions the murmur** to a learner who may not have listened to the
    heart. Open question 17.
14. **Handoff explanations are one string each.** "her mediastinum is normal" is printed
    to a learner who never ordered the film.
15. **Her answer about dizziness does not change once steadied.** Open question 14.
16. **No interview facts are authored**, so a follow-up such as "what dose?" gets the whole
    answer again.

## 8. Open questions for the physician

The first six are from 6 October 2026. Each later one gives the options and what the pack
does today.

1. Is fluid plus a pure vasoconstrictor the plan you would teach, given that the
   consensus document names no vasoconstrictor?
2. The cardiologist takes over 90 seconds after being called. A learner who calls early,
   which is correct, is rescued 90 seconds after the pressure falls whether or not they
   act. Is that too generous?
3. Thrombolysis is only discouraged. It carries a real bleeding risk for no benefit.
4. NT-proBNP of 5200 one hour after onset is early. It usually peaks at 24 to 48 hours.
5. Lactate falls from 5.8 to 3.6 across a ten-second transition.
6. No QT prolongation, apical thrombus or anticoagulation is taught. Left out on purpose.
   The catalog now has `dx_acquired_long_qt` if you want it. Her QTc is authored as 470.
7. **Push-dose phenylephrine and vasopressin.** Today both are unbound: neutral, no
   note, no effect. Fluid plus a phenylephrine bolus leaves her obstructed with nothing
   said. Options: (a) cover them under the infusion, so a push dose steadies her for
   good. (b) Give them their own action with a short pressure effect and a nurse line such
   as "That bolus will wear off in a few minutes. Do you want an infusion running?" (c)
   Leave them.
8. **Push-dose epinephrine.** Today it is the inotrope and has to be stopped (limit 5).
   Options: keep, or a short effect that wears off with no stop needed.
9. **Norepinephrine alone moves no pressure.** Today it adds 6 to the rate and nothing
   else, while phenylephrine alone adds 8 points. Options: give it the same 8 points, or
   keep it and say why in its note.
10. **Fluid and a vasoconstrictor before the fall are tagged neutral**, while the debrief
    calls that path the best version of the case. Options: recommended on arrival once
    the echo has resulted, or neutral as today.
11. **Pertinent negatives.** Each of these gets "I'm sorry, I don't follow" today. Rule
    each as a denial topic, an answered topic or out of scope.
    - Heartburn or indigestion. The audit's candidate: "No, it's not like heartburn. I
      don't get that."
    - Anxiety, panic attacks, low mood. The case's central frame is the daughter's
      "nerves", and panic attack is an authored wrong diagnosis. Candidate: "I've never
      had panic attacks. I've never been a nervous person."
    - Weakness in the arms or legs, trouble with speech. She has a thrombolysis decision.
      Candidate: "No weakness. I can speak fine."
    - Who is with her, family in the waiting room, children. Her daughter is at the
      bedside and she mentions three children in another answer.
    - What she did before she retired. The background says schoolteacher. No answer says
      so.

    None of the candidates was adopted.
12. **The gas.** Supply a pH for each phase and the pCO2 follows from it and the
    bicarbonate. Today the gases show bicarbonate and lactate only. Related: the
    chemistry bicarbonate is 22 in every phase, beside a lactate of 5.8 in shock. Should
    it fall?
13. **The catheterization laboratory prerequisite.** Options: a resulted twelve-lead
    (today), an ordered one, or none.
14. **Dizziness once steadied.** She still says she was lightheaded when stood up for the
    ambulance. Should she say the faint feeling has gone?
15. **Outflow obstruction named as the primary diagnosis.** Today it is scored incorrect
    with the generic note. Should it be defensible, like cardiogenic shock?
16. **Default mode on arrival.** Aspirin and the laboratory are not prompted before the
    fall (section 4.1). Options: leave it, which fits "prompted only late", or move both
    under 60 seconds so the default mode hears them.
17. **The cardiologist and the murmur.** Options: require the cardiac examination before
    the call, split the reply on whether the heart was examined, or leave it.
18. **A nitrate in the obstructed phase shows nothing** (limit 1). Acceptable? The
    alternative is a second hidden action that records a nitrate given after arrival.
19. **"Any night sweats?"** is answered by the fever topic ("No fever. I've not been
    ill"). The audit proposed moving it to sweating, where she would say she is drenched.
    It was left.
20. **A dry mouth is now flagged abnormal**, and so is "Barely speaking" in worsening
    shock. Confirm both flags.

## 9. Engine and catalog changes

Made for this case in v0.22:

- Validator and timeline tool: a guard was read as negated if the text "NOT" appeared
  anywhere in it, including inside "inotrope". Now a whole-word match.
- Shared engine test: picks an unguarded vital effect when every prerequisite-free one is
  guarded off at the start.
- No engine.js or interface change. The case-only button uses the existing mechanism.

On 7 October 2026 nothing outside `cases/TAKO/` was changed for this pack except one
line. In `catalog/expand_interview_variants.py` this pack's cover tags are now:

```python
"TAKO": ["character_general", "cough_sputum", "prior_hf", "stroke_history", "gi_bleeding"],
```

`mood_stress` and `companion` were removed because no answer covers those questions (open
question 11). `gi_bleeding` was added because the bleeding topic answers it.

## What a person decided

- 11 October 2026, Aakash Setty: every consultant answer over 40 words is shortened to 40 or fewer (authoring 9.5), keeping what the consultant thinks, what to do now and the disposition or callback. Wording by a model. Rule order, conditions, tags and debrief notes are unchanged. Not physician reviewed. Six of nine answers changed, all cardiology. The arrival-and-takeover line is now "I'm coming down to take over" and the takeover itself is unchanged. Dropped: an Impella rather than a balloon pump if she fails on a vasoconstrictor, which the phenylephrine note still gives, the angiogram and ventriculogram plan, the mechanism sentences (a fuller ventricle obstructs less, squeeze the vessels without driving the heart), and "whatever happened at the funeral".
