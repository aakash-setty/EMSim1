# AFRVR author's seed

Unlike CHFE, this case had a real seed. The physician author supplied the ground truth
below before any drafting: the diagnosis, the presenting vital signs, the physical
findings, the initial ECG and laboratory results, the POCUS findings that are the pivot
of the case, the six critical actions, the three ways the case can go wrong, the
diltiazem nuance, the accepted rate-control and anticoagulation options, the target
endpoint and the disposition.

Everything else in `AFRVR-case.json` was expanded by a language model and is unsigned.
The division is recorded in `AFRVR-review-packet.md` section 1, and the three places
where the expansion departs from this seed are in section 4 of that packet.

Section numbers below refer to `docs/case-authoring-requirements.md`.

---

## 3.1 Case identity

- **Working title:** sixty-eight year old man, palpitations and breathlessness, brought
  in by EMS
- **Chief complaint, patient's words:** "My heart won't stop racing and I can't get my
  breath."
- **Final diagnosis:** atrial fibrillation with rapid ventricular response complicated by
  acute decompensated HFrEF and cardiogenic pulmonary oedema. The author's note: "the
  learner should also recognise that the AF may be both a consequence of acute
  physiologic stress and a potential contributor to the patient's LV dysfunction."
- **Learning objectives** (author's list, verbatim in intent):
  - recognise atrial fibrillation with rapid ventricular response
  - identify acute decompensated heart failure and cardiogenic pulmonary oedema
  - use cardiac and lung POCUS to identify previously undiagnosed HFrEF
  - select appropriate rate-control therapy in the setting of reduced LV systolic
    function
  - initiate appropriate respiratory and heart-failure treatment
  - recognise the need for anticoagulation
  - reassess response to treatment and determine appropriate disposition
- **Target level:** not specified in the seed. Drafted as intern to senior resident.

## 3.2 Patient and setting

- **Age, sex:** 68, male. Weight not specified in the seed; drafted at 84 kg.
- **Background:** hypertension; type 2 diabetes; coronary artery disease without known
  prior MI; **no known history of atrial fibrillation**; **no known history of heart
  failure**. Medications: lisinopril, atorvastatin, metformin. **Not on an
  anticoagulant.**
- **Presenting vital signs:** HR 160 irregular, BP 132/78, RR 30, SpO2 88% on room air,
  temperature 37.0 degrees Celsius.
- **Presenting appearance:** awake, anxious, and visibly dyspnoeic but able to speak in
  full sentences.
- **History:** approximately one day of worsening palpitations, shortness of breath and
  fatigue. Heart has felt "racing" since yesterday. Dyspnoea progressively worse, now
  breathless walking across the room. **Denies syncope. No severe chest pain.**
- **Arrival, room, handover:** not specified in the seed. Drafted as EMS to the
  resuscitation bay, with the two-sentence handover written to be vague on purpose.
- **Care setting:** not specified. Drafted as a quaternary centre with everything
  available, which is what makes the disposition question about capability rather than
  about resources.

## 3.3 Phases

The seed did not supply phases. It supplied a target endpoint and three wrong paths, and
the six clinical phases in the case file are those crossed with the two axes the seed is
organised around, whether the breathing is supported and whether the rate is controlled.

**The author's target endpoint,** verbatim in substance: over 20 to 30 minutes with
correct management, SpO2 rises to about 94 to 97 percent, respiratory rate falls toward
the low twenties, work of breathing improves, diuresis begins, heart rate falls toward
100 to 110, blood pressure remains stable, dyspnoea substantially improved. Repeat POCUS
may show persistent but improving pulmonary oedema. **The patient remains in AF, and this
is not a failure.**

**The author's instruction on the simulation mechanics,** verbatim in substance:

- BiPAP should increase the oxygen saturation over the course of one minute of game time.
- Furosemide should not change the oxygen saturation.
- For anticoagulation: a heparin drip is acceptable, a DOAC is preferred, enoxaparin is
  acceptable if it exists in the interventions list.

## 3.4 The action spine

**The six critical actions, written by the author as observable learner behaviours:**

1. Obtain and interpret a 12-lead ECG, and recognise AF with RVR.
2. Perform cardiac and lung POCUS and use the findings to identify reduced LV systolic
   function and pulmonary oedema.
3. Initiate non-invasive positive pressure ventilation (BiPAP or CPAP).
4. Treat acute decompensated heart failure: IV loop diuretic, and address relevant
   contributors such as hypomagnesaemia.
5. Initiate and reassess appropriate rate-control therapy. Acceptable approaches include
   digoxin, appropriately selected beta blockade when physiologically tolerated, or IV
   amiodarone.
6. Assess thromboembolic and bleeding risk and initiate anticoagulation where there is no
   contraindication.

**The diltiazem nuance, which is the author's central teaching point.** Diltiazem before
the learner knows the EF is *not* an automatic failure. The simulation must not produce a
dramatic hypotensive collapse. Instead the heart rate falls, the blood pressure falls
modestly or remains acceptable, POCUS then reveals an EF of 30 to 35 percent, and the
learner should recognise that continued diltiazem is inappropriate and change strategy.
**Once moderate to severe LV systolic dysfunction is known, continued IV diltiazem is a
management error.** Giving it before that is a performance deduction rather than a
failure.

**Harmful actions:** none named in the seed. See review packet section 4.

## 3.5 Sequencing

Not specified in the seed beyond the ordering implied by the wrong paths: respiratory
support is an immediate priority and not something to defer until the arrhythmia is
controlled.

## 3.6 Key findings

**Physical examination, author's list:** irregular tachycardia; elevated JVP; bibasilar
crackles; bilateral lower-extremity oedema; increased work of breathing; no obvious
unilateral leg swelling; no severe chest pain; no altered mental status; no clinical
shock.

**ECG:** atrial fibrillation with rapid ventricular response, ventricular rate
approximately 160. No STEMI.

**Laboratory, author's values:** Na 138, K 3.7, **Mg 1.6**, creatinine 1.0, CBC
unremarkable, initial troponin negative or minimally elevated without a dynamic ischaemic
pattern, TSH normal. The author's note: "the low magnesium should prompt replacement."

**Cardiac POCUS:** globally reduced LV systolic function, estimated EF approximately
**30 to 35 percent**, no large pericardial effusion, no obvious RV catastrophe.

**Lung POCUS:** diffuse bilateral B-lines consistent with pulmonary interstitial oedema.

Reference intervals were not supplied and every one in the case file is model output.

## 3.7 Interview ground truth

The seed supplied the history above. The remaining thirty-eight interview topics, the
pertinent negatives beyond syncope and chest pain, and all 570 paraphrase variants are
model output.

## 3.8 Disposition

**Admit.** If he remains dependent on BiPAP or CPAP, to a setting capable of continuous
cardiac monitoring, ongoing non-invasive ventilation, frequent reassessment and rapid
escalation to invasive ventilation. Depending on institutional capability this could be
an ICU, a step-down or intermediate-care unit, or another appropriately equipped
monitored unit. If he improves rapidly and is weaned from NIV, telemetry-level admission
may subsequently be appropriate. **Discharge from the ED is not an appropriate
endpoint.**

He **does not need to convert to sinus rhythm in the ED** to be considered successfully
managed.

---

## The three wrong paths, as the author wrote them

**Wrong path 1: treats the heart rate and misses the heart failure.** Identifies AF with
RVR and focuses exclusively on the rate. May give diltiazem and reach a heart rate of 105
to 110 but fails to perform POCUS, recognise pulmonary oedema, initiate NIV or treat the
decompensated heart failure. Evolution: the heart rate improves, the respiratory rate
stays around 32, SpO2 stays around 86 to 89 percent, the patient remains markedly
dyspnoeic, and the B-lines persist. **Teaching point: a lower heart rate does not equal
successful resuscitation.**

**Wrong path 2: continues diltiazem after HFrEF is identified.** Sees EF 30 to 35 percent
and continues IV diltiazem because it lowered the rate. The patient does not necessarily
crash. Instead: heart rate 95 to 105, systolic pressure 100 to 110, persistent pulmonary
oedema, ongoing oxygen or NIV requirement, possible worsening heart failure symptoms.
**Teaching point: a medication can produce the desired physiologic effect while still
being an inappropriate treatment in the patient's underlying disease state.**

**Wrong path 3: fails to treat the pulmonary oedema.** Recognises AF and HFrEF but delays
or fails to initiate NIV despite SpO2 88 percent, RR 30, increased work of breathing and
diffuse B-lines. Evolution: respiratory distress persists or worsens, increasing oxygen
requirement, RR above 30, increasing fatigue, persistent hypoxaemia, and ultimately the
patient may require intubation. **Teaching point: in acute cardiogenic pulmonary oedema
with respiratory failure, respiratory support is an immediate treatment priority, not
something to defer until the arrhythmia is completely controlled.**
