# DIPH author's seed

**Case author: Kelly Medwid, MD.** Converted to this platform with her permission, at her
request, by Aakash Setty. The source is a single Word document, `Diphenhydramine
Overdose.docx`, supplied on 5 September 2026.

Section numbers refer to `docs/case-authoring-requirements.md`.

---

## 0. What the source document is, and why that matters here

The source is **two documents in one file**, written in different registers and against
different evidence bases. This seed has to say which is authoritative wherever they
disagree, because they disagree about the central teaching point of the case.

**Part 1**, roughly the first twenty-three pages. A mannequin-based in-situ simulation
case: a two-column identity and narrative table, an Ideal Scenario Flow on a 0 / 3 / 4 /
5 / 6-10 minute clock, an Anticipated Management Mistakes list, confederate roles (RN,
EMS, mother), a mannequin and supply list, an "ABEM General Hospital" emergency admitting
form carrying triage vitals and a laboratory panel, a physical examination table, a
Teaching Points essay, and a reference list whose newest citation is 2004. Four images:
a near-normal chest radiograph, a normal non-contrast head CT, and two wide-complex
tachycardia ECGs.

**Part 2**, the remainder. A "Debriefing Guide: Diphenhydramine Overdose With QRS
Widening": case summary, eight learning objectives, reaction and analysis phases across
thirteen numbered sections with a teaching pearl under each, a Common Performance Gaps
list, Summary Pearls, and wrap-up questions. Its evidence base is materially later than
Part 1's: it cites lidocaine rescue for refractory wide-complex dysrhythmia, intravenous
lipid emulsion, and extracorporeal life support, none of which appear in Part 1.

**Which is authoritative.** Part 1 is the case. It carries the patient, the vital signs,
the laboratory values, the timing, the confederates and the mechanics, and it is what the
author wrote as a simulation. Part 2 is authoritative on **management and teaching**,
because it is later and more specific, and because the author supplied it in the same
file as the debriefing companion to the case. Where the two conflict on management, Part 2
governs and the conflict is recorded in section 9 below.

**Unresolved provenance question for the author.** Part 1's reference list cites
`acep.org/tox/case-files/15_Diphenhydramine Overdose.pdf` and
`thepoisonreview.com`. It is not clear from the document how much of the Teaching Points
essay, and which of the four images, are the author's own work and how much is reproduced
or adapted from those sources. This matters because the platform is free and open source.
**Two of the four images are now in the case pack** and are embedded in the distributed
build, so the question is live rather than sidestepped: the arrival ECG and the chest
radiograph are shown as pictures with no interpretation. The second ECG was tried and taken
out, and the head CT is unused because nothing in the case orders one. See section 9.10. Nothing from the Teaching Points essay is reproduced
verbatim in the case file. See section 10.

---

## 1. Educational framing

A resident who reaches the end of this case having recognised an anticholinergic
toxidrome, and having done nothing about the QRS, has failed the case while feeling that
they passed it. That is the case. Part 2 states it directly: "A patient with
diphenhydramine overdose and QRS widening no longer has 'just' an anticholinergic
toxidrome."

## 3.1 Case identity

- **Working title:** eighteen year old woman, confusion and fever, brought in by EMS
- **`metadata.complaint`:** Confusion and fever
- **`metadata.category`:** Toxicology
- **Chief complaint, patient's words:** the patient is delirious and does not give a
  chief complaint. The complaint as the mother states it: "She wasn't making any sense
  and she didn't know who I was."
- **Final diagnosis, as a catalog id:** `dx_diphenhydramine_overdose`, with
  `dx_sodium_channel_blocker_cardiotoxicity` first among the additional diagnoses.

  **This was a compromise when the seed was first written and it no longer is.** The
  diagnosis catalog held no entry for diphenhydramine overdose, antihistamine overdose or
  sodium-channel blockade, so the primary diagnosis had to be recorded as
  `dx_anticholinergic_toxidrome`, which is precisely the distinction Part 2 exists to
  teach. Three toxicology entries were added to the catalog on 5 September 2026 on the
  author's instruction: `dx_diphenhydramine_overdose`,
  `dx_sodium_channel_blocker_cardiotoxicity` and `dx_drug_induced_seizure`, each marked
  `source=author-supplied`. The toxidrome now appears twice in the handoff, as an
  additional diagnosis that earns credit beside the agent and as an alternative scored
  `acceptable_with_qualification` when it is offered as the primary, which is what it is:
  right as far as it goes and missing the thing that kills her.
- **Learning objectives.** The author supplied two lists. Part 1's four, verbatim in
  intent:
  1. Recognise the signs and symptoms of diphenhydramine toxicity
  2. Describe elimination techniques effective for diphenhydramine toxicity
  3. Describe the roles of therapeutic interventions in the patient with diphenhydramine
     toxicity, including indications, contraindications and efficacy
  4. Discuss the management priorities for the emergent stabilisation of the patient with
     an anticholinergic toxidrome

  Part 2's eight are narrower and more testable, and five of them are carried into the
  case file as the displayed objectives:
  - Recognise the clinical features of diphenhydramine toxicity
  - Identify ECG findings associated with sodium-channel blockade
  - Differentiate uncomplicated anticholinergic delirium from life-threatening
    cardiotoxicity
  - Administer sodium bicarbonate for QRS widening or ventricular dysrhythmias
  - Recognise when physostigmine is contraindicated

  The three not carried (treat agitation, hyperthermia and seizures appropriately;
  escalate care for refractory findings; coordinate early poison-control consultation)
  are covered by critical actions and appear in the debrief rather than in the objective
  list, which section 3.1 caps at six.
- **Target level:** not specified by the author. Drafted as junior to senior resident.
  It is not an intern case: the trap requires knowing what physostigmine is before
  knowing not to give it.

## 3.2 Patient and setting

- **Name in the source:** Tonya Jones. **Age 18. Female.** Weight not specified;
  drafted at 60 kg, which matters only for the 1 to 2 mEq/kg bicarbonate dose.
- **Background:** no past medical or surgical history. No medications. NKDA. Family
  history of hypertension. (Part 1, physical examination table.)
- **Psychosocial history, the author's own:** recently the victim of online bullying,
  recently broke up with her boyfriend, has stopped speaking to several friends, and has
  been increasingly depressed. She swallowed an entire bottle of diphenhydramine
  approximately four hours before her mother came home from work.
- **Presenting vital signs:** BP 130/75, HR 135, RR 25, SpO2 98 percent on room air,
  temperature 104.2 degrees Fahrenheit, which is **40.1 degrees Celsius** and is what the
  case file carries, since the engine's field is `temperature_c`.
- **Presenting appearance:** confused, agitated female lying in bed.
- **Care setting:** not specified by the author. Drafted as a centre with toxicology,
  critical care and psychiatry available, which is what makes the disposition question
  about level of care rather than about transfer.
- **Arrival:** `mode: ems`, `location: resuscitation_bay`. The author's Part 1 form gives
  method of transportation as EMS.
- **`patient.arrival_handover`**, two sentences, written to be vague on purpose per
  section 3.2: "Eighteen year old, her mom found her like this when she got in from work
  about an hour ago. She's been fighting us the whole way in and she's burning up."
  It carries no vital sign, no diagnosis, no past history and no pertinent negative.

**The historian is the mother, and this is a departure from the platform.** Part 1 is
explicit that the patient is confused, agitated and combative, and that the history comes
from EMS and from the mother, who is a confederate in the room. The engine's interview is
patient-facing and has no collateral-historian mechanism. On the author's instruction
(Aakash Setty, 5 September 2026) **the mother answers as the patient**: every interview
answer in this pack is the mother speaking at the bedside, with no engine change. Two
consequences the reviewer should hold onto:

1. Section 10.4's constraint that "the patient uses lay language, not clinical
   terminology" is preserved, because the mother is a lay historian. Section 10.4's
   constraint that the patient never reports what she could not know is preserved and is
   in fact easier, because the mother knows less than the patient does.
2. **The history does not disappear when the patient's alertness drops.** In every other
   pack an intubated or obtunded patient ends the interview. Here the mother is still in
   the department, so the history stays available through the post-ictal and stabilising
   phases. It is withdrawn only where the team would actually have moved her out of the
   room, which is during the seizure and during the wide-complex phases. That is authored
   as the global rule required by section 10.5.

## 3.3 Phases

Six clinical phases and three terminals. The author supplied a timed scenario rather than
phases, so the phases below are that scenario crossed with the two axes the case turns
on: whether the seizure has been treated, and whether the sodium-channel blockade has
been treated.

| id | what it is | HR | BP | RR | SpO2 | T (C) | alertness |
|---|---|---|---|---|---|---|---|
| `presentation` | Anticholinergic delirium, hyperthermic, wide QRS present and not yet looked for | 135 | 130/75 | 25 | 98 | 40.1 | 0 |
| `seizing` | Generalised seizure | 150 | 145/90 | 8 | 84 | 40.4 | 3 |
| `post_ictal` | Seizure terminated, still hot, QRS still wide | 140 | 120/70 | 16 | 92 | 40.2 | 1 |
| `wide_complex_tachycardia` | Haemodynamically stable monomorphic wide-complex tachycardia from untreated sodium-channel blockade | 180 | 95/60 | 22 | 90 | 40.0 | 2 |
| `stabilizing` | Bicarbonate given, QRS narrowing | 115 | 115/70 | 18 | 96 | 39.6 | 1 |
| `stabilized` | Ready for the unit | 100 | 118/72 | 16 | 98 | 37.8 | 1 |

Terminals: `pulseless_vt` (reached on the clock from `wide_complex_tachycardia`),
`halted` (a harmful action), `case_complete` (handoff).

Pupils are large and reactive in every phase, including the resolution phases, because
mydriasis outlasts the cardiotoxicity. Rhythm is `regular` throughout: nothing in this
case turns on an irregular beat, and `irregularly_irregular` would be a claim the source
does not make.

**How the narrowing phase is reached, and its temperature.** Three ways, all on the same
guard and the same ten seconds: directly from arrival if the bicarbonate went in before she
convulsed (see section 9.8), from the post-ictal phase, and from the wide-complex rhythm.
Its authored vitals therefore have to be true of a patient who never seized and of one who
came within two minutes of arresting. The temperature is **39.6**, raised from 39.0 on
5 September 2026: nothing in this case cools her except active cooling, which is a vital
effect applied on top of this baseline, so a phase reached three minutes after arrival
should not already read like a treated fever.

**What happens if the resident does nothing.** The author is explicit on the one point
that matters most here: *"A seizure will occur as part of the natural process, regardless
of how well the examinee is doing."* That is an unguarded scheduled natural history in the
sense of section 5.1, and it is authored as one, with the author's sentence as its
`unguarded_rationale`. Everything after the seizure is guarded: an untreated seizure
widens the complex further, and untreated sodium-channel blockade ends in pulseless
ventricular tachycardia. The do-nothing trajectory therefore ends in a dead patient, which
is a decision this seed is making deliberately and which section 14.2c will print.

**Timing, and how it is compressed.** Part 1's clock is 0 / 3 / 4 / 5 / 6-10 minutes. The
seizure at four minutes is carried at its authored value, 240 seconds. The later
deadlines are compressed, because the engine's phase clock restarts at every phase entry
and the source's clock does not. The relative ordering is preserved and the absolute
numbers are provisional, per section 9.6.

## 3.4 The action spine

**Critical.** Attach a monitor. Obtain IV access. Obtain a point-of-care glucose (the
author's value is 110, and the point of it is that it is normal). **Obtain a 12-lead ECG,
which is the pivot of the case.** Terminate the seizure with a benzodiazepine. **Give
sodium bicarbonate for the wide QRS.** Begin active cooling. Consult toxicology or poison
control. Admit to critical care.

**Harmful, in the engine's sense, which is that the case halts.**

| action | when | why |
|---|---|---|
| `physostigmine` | before the ECG has resulted | See section 9. Given blind to a patient whose QRS is already 132 ms |
| `flumazenil` | always | Precipitates seizure in an undifferentiated overdose, in a patient who is going to seize anyway |
| `diphenhydramine` | always | More of the drug she overdosed on. The catalog carries it under Meds - Allergy and a resident treating a presumed allergic reaction can reach it |
| `procainamide_drip` | `wide_complex_tachycardia` and `pulseless_vt` | A class IA antiarrhythmic in established sodium-channel blockade. Part 2 section 9 names the class explicitly |

**Discouraged.**

| action | why |
|---|---|
| `physostigmine` after the ECG has resulted | See section 9 |
| `fos_phenytoin` | The author writes "Dilantin should be avoided since it also prolongs sodium channels." Tagged discouraged rather than harmful: see section 9 |
| `haloperidol`, `olanzapine`, `ziprasidone` | Antipsychotics for the agitation. Anticholinergic, QT-prolonging, and not the first-line agent. Part 2 section 8 |
| `acetaminophen` | Antipyretic for a temperature of 40.1. Part 2 section 12: "Antipyretics are not useful because the elevated temperature is caused by impaired heat dissipation and muscle activity rather than a hypothalamic fever response" |
| `activated_charcoal` before the airway is protected | Part 2 section 11: "Charcoal should not be given to a severely agitated, seizing, or obtunded patient without a protected airway." Recommended once intubated |
| `naloxone_bolus` | Defensible reflex in undifferentiated altered mental status, wrong here: the pupils are large |
| antibiotics and `lumbar_puncture` after the toxicology screen has resulted | Reasonable before, not after |

**Recommended, and this is where Part 1 and Part 2 differ in emphasis.** Part 1's Ideal
Scenario Flow says at time zero: "Sepsis bundle should be be initiated with IV fluid bolus
and possible antibiotics" [the doubled "be" is the source's] and "The team may also want to
isolate the patient. (if thinking meningitis)". Part 2 never mentions sepsis. Both are right for the moment they describe.
**Antibiotics and isolation are tagged `recommended` in `presentation` and `discouraged`
once the urine toxicology screen has resulted**, which is the case saying that an empirical
sepsis workup in an undifferentiated hyperthermic delirious eighteen year old is good
practice, and that continuing down it after the toxidrome is established is not.

Also recommended: crystalloid (bound to the whole `crystalloid_bolus` equivalence group,
for the rhabdomyolysis the CK of 540 is the beginning of), a urinary catheter (she has a
palpable bladder and needs urine output measured), CK, chemistry, CBC, lactate, blood gas,
acetaminophen, salicylate, ethanol, urine and serum toxicology, urine hCG, magnesium,
ionised calcium, chest radiograph, head CT, psychiatry, and critical care.

**Refractory rescue, from Part 2 section 10**, each recommended only in
`wide_complex_tachycardia` and only once bicarbonate has been given, and discouraged
before that, because reaching for lipid emulsion before bicarbonate is the error the
section warns about: `lidocaine_bolus`, `hypertonic_saline_25_bolus`, `intralipid`. The
author should note that Part 2 itself says the evidence for all three "is limited and
largely based on case reports, toxicology experience, and extrapolation from other
sodium-channel blockers," and the debrief notes say so.

**Not authorable.** Gastric lavage, which Part 1's Teaching Points discusses, has no
catalog entry. Core temperature measurement has no catalog entry: the temperature appears
on the monitor once one is attached and cannot be ordered as an act, so Part 2's "check
rectal temps in patients with significant agitation" cannot be taught mechanically and is
carried in a debrief note instead. Defibrillation of the pulseless rhythm is out of scope
because the arrest phase is terminal and the engine ends the case there.

## 3.5 Sequencing

The only prerequisite the case adds is the one the whole case is about: **physostigmine
is not blocked**. It must be reachable, because a blocked action teaches nothing and the
lesson here is what happens when it is given. Catalog defaults (a line before an
intravenous drug, sedation and paralysis before intubation) stand unmodified.

One follow-up: intubation creates an obligation to sedate, satisfied by propofol,
midazolam, ketamine or fentanyl.

## 3.6 Key findings

**Physical examination, the author's table verbatim in substance.** General: confused,
agitated female lying in bed. HEENT: pupils equal and enlarged, with opsoclonus, dry
mucous membranes. Neck: supple, no meningismus. Lungs: clear breath sounds bilaterally.
Cardiovascular: sinus tachycardia, no murmurs. Abdomen: soft, non-tender, non-distended,
decreased bowel sounds, palpable large bladder. Neurological: confused, agitated. GU:
palpable enlarged bladder. Skin: hot, dry. Musculoskeletal: no oedema, full range of
motion, no trauma. Psychiatric: agitated.

Routed to the closed set of fourteen maneuvers per section 11.2. Two routings are worth
naming because they are not obvious: the dry hot skin and the absent sweat go to
`exam_skin`, and the agitation and thought content go to `exam_psych` rather than to
`exam_neuro`, which owns the level of consciousness.

**The ECG. This is the finding the case exists for**, and the source contradicts itself
about it. See section 9. As authored: rate 135, sinus tachycardia, **QRS 132 ms**,
**terminal R wave in aVR 5 mm with an R to S ratio in aVR above 0.7**, rightward terminal
QRS axis, QTc 495 ms, no ST elevation. Findings and not conclusions, per section 11.4:
the words "sodium-channel blockade" appear in the debrief note and not in the report.

**Laboratory, the author's values.** Arterial blood gas pH 7.28, pCO2 34 mmHg, pO2 94
mmHg, HCO3 13 mEq/L, lactate 3.1. hCG negative. Salicylate 0 mg/dL. Ethanol under 10
mg/dL. Acetaminophen 0. CK 540. WBC 16. Haematocrit 47.2 percent. Haemoglobin 16.9 g/dL.
Platelets 250. Chemistry: sodium 135, potassium 3.8, chloride 109, **bicarbonate 13**,
BUN 12, creatinine 0.8, glucose 120. Point-of-care glucose 110.

Four notes on those values, all of which need the author's signature:

1. **The source's chemistry panel gives CO2 as 34 mEq/L and its blood gas gives HCO3 as
   13 mEq/L, and both cannot be true.** With sodium 135 and chloride 109, a bicarbonate of
   13 gives an anion gap of 13, which fits a pH of 7.28 with a lactate of 3.1 and a
   seizure. A bicarbonate of 34 gives an anion gap of negative 8, which is not a number a
   patient can have. **The case authors 13 and treats the 34 as a transcription error.**
2. **Haemoglobin 16.9 g/dL and haematocrit 47.2 percent are above the usual female
   reference interval** and are flagged abnormal, with a `verify` note. Haemoconcentration
   in a hyperthermic patient who has not drunk for hours is a plausible reading, but it is
   a reading, not the author's statement.
3. **WBC is written "16 L/ul" in the source.** Taken as 16 K/microlitre.
4. **CK 540 carries no reference interval in the source.** Authored against 30 to 200
   U/L, flagged abnormal, with a `verify` note. It is the beginning of rhabdomyolysis
   rather than established rhabdomyolysis, and the debrief note says so.

**The urine toxicology screen is positive for tricyclic antidepressants, and it is a false
positive.** Part 1's Teaching Points: "The urine toxicology screen may be falsely positive
for tricyclic antidepressants." Authored as a positive result with the false-positive
teaching in the debrief note and not in the result comment, so that a resident who anchors
on it does so and then reads why they should not have.

**Imaging is normal and that is the point.** Chest radiograph normal, non-contrast head CT
normal. Both are authored rather than left to the catalog default, because a resident who
orders them should get a short normal report from this case rather than a default from the
catalog.

## 3.7 Interview ground truth

In the mother's voice throughout. The positives: found confused and not making sense when
the mother came home from work about an hour ago; well that morning; increasingly
withdrawn and low for months; bullied online; a recent breakup; stopped speaking to
several friends; no past medical or surgical history; no regular medications; no
allergies; hypertension in the family.

**The disclosure.** The mother does not volunteer the empty bottle. Asked whether there
was anything near the bed, or whether anything is missing from the house, she says she did
not look, and then that she will call her son to look. The bottle is found. If nobody asks,
the nurse delivers it in the post-ictal phase, which is Part 1's five-minute rule
compressed into the phase structure.

The pertinent negatives, each its own topic with its own denial per section 10.3: no
fever or infectious symptoms before today, no headache, no neck stiffness, no rash, no
head injury or fall, no alcohol, no recreational drugs that the mother knows of, no
seizure history, no diabetes, no recent travel, no sick contacts, not pregnant as far as
the mother knows, no prescription medicines in the house.

**`interview.key_topics`**, the topics whose answers change management here: the bottle
and what is missing from the house, what she took and when, the timeline of the last four
hours, past medical history, medications in the house, and the psychiatric history.

## 3.8 Disposition

**Admit to critical care.** Part 1: "Toxicology should be consulted and the patient should
be intubated and admitted to the ICU." Part 2 section 13 lists nine indications for
critical-care admission and this patient meets at least six of them: QRS widening, seizure,
persistent delirium, hyperthermia, need for a bicarbonate infusion, and significant
metabolic abnormality.

Wrong dispositions worth explaining: telemetry or a monitored ward bed (defensible only
after the QRS has narrowed and stayed narrow, and not from the ED), the psychiatric unit
(medical clearance is not achieved in a patient with an unresolved wide QRS, and this is
the disposition error the case is most likely to produce), observation, and discharge.

**Primary diagnosis:** `dx_diphenhydramine_overdose`.

**Additional diagnoses**, in the order they are authored:
`dx_sodium_channel_blocker_cardiotoxicity` (first, because it is what decides the
management), `dx_anticholinergic_toxidrome`, `dx_rhabdomyolysis`,
`dx_drug_induced_seizure` and `dx_suicide_attempt`. The deliberate nature of the ingestion
belongs in the handover and the catalog already held an entry for it.

**Plausible wrong primary diagnoses, each of which the case explains:**
`dx_tricyclic_antidepressant_overdose` (defensible with qualification: the ECG is the same
picture and the urine screen says TCA, and the immediate management is identical, which is
worth telling a resident who names it), `dx_sympathomimetic_toxicity` (the discriminator is
the skin, which is hot and dry rather than hot and wet), `dx_serotonin_syndrome` (the
discriminator is clonus and hyperreflexia, absent here), `dx_neuroleptic_malignant_syndrome`
(rigidity, absent, and the time course is wrong), `dx_bacterial_meningitis` (the neck is
supple and there is no rash, but it is the right thing to have thought about at time zero),
`dx_heat_stroke`, and `dx_thyroid_storm`.

---

## 9. Where the source contradicts itself, and what this pack does about it

Seven conflicts in the source, plus one departure from it that is not a conflict at all
and is recorded here because it belongs in the same list. Four of the seven are resolved on
the author's instruction of 5 September 2026 and three are drafting assumptions; all four of
those, and the departure in 9.8, **need the author's signature before release**.

### 9.1 Physostigmine. RESOLVED BY THE AUTHOR, with one mechanical caveat.

Part 1: *"The use of physostigmine is warranted, however, the examinee needs to first
discover that diphenhydramine was the causative agent and discuss with the poison center.
If the learner administers physostigmine before either checking an ECG for the QRS
interval, or having obtained a clear history of diphenhydramine ingestion, then the patient
will become hemodynamically unstable (severe bradycardia) and seize."*

Part 2 section 7: *"Physostigmine Is Not Appropriate When the QRS Is Wide... Anticholinergic
delirium plus a wide QRS is a bicarbonate case, not a physostigmine case."*

**The author's instruction:** physostigmine is harmful, and it leads back to a seizure
requiring bicarbonate.

**The mechanical caveat, which is the one thing in this seed the author has not seen.**
The engine's `harmful` tag halts the case immediately into a terminal phase and bypasses
every transition rule (system design 10, authoring 7.3). It therefore cannot lead
anywhere, and "harmful, and it leads back to a seizure" is not expressible as one tag. The
instruction is split along the line Part 1 itself draws:

- **Physostigmine before the ECG has resulted is `harmful` and halts the case.** This is
  the unambiguous case and it is what Part 1 describes: the drug given blind to a patient
  whose QRS is already 132 ms.
- **Physostigmine after the ECG has resulted is `discouraged`, and transitions the patient
  into `seizing` ten seconds later.** This is the author's "leads back to seizure requiring
  bicarb", and it is the only way to author a consequence the resident then has to treat.

Both routes end with the resident being told that physostigmine was the wrong drug and
that the wide QRS was the reason. What differs is the score: the harmful route zeroes the
Interventions tab and ends the run, and the discouraged route costs one point and leaves
the case running. **If the author wants physostigmine to halt the case in every
circumstance, that is a one-line change to the tag rule list and this seed should be
amended rather than the case patched.**

Part 1's harm mechanism for the blind route is "severe bradycardia and seize"; its own
Ideal Scenario Flow four pages later says "the patient will progress to v-tach and / or
v-fib and arrest." **The halt reason uses the bradycardia-and-seizure mechanism**, because
it is the one in the author's narrative description rather than in the timing outline, and
because cholinergic bradycardia is the pharmacologically specific consequence of
physostigmine. Flagged for signature.

### 9.2 The aVR finding. DRAFTING ASSUMPTION. NEEDS SIGNATURE.

Part 1's narrative: *"The examinee should recognize **the lack of** a significant R wave in
lead aVR and should also note a wide complex rhythm."*

Part 1's own Teaching Points, four pages later: *"There may be a large terminal R in lead
AVR."* And: physostigmine is recommended only after checking *"a patient's ECG for signs of
TCA drug effect (>3mm R in AVR, widened QRS)."*

Part 2 section 3 lists among the findings of sodium-channel blockade: *"Terminal R wave in
lead aVR. Increased R-to-S ratio in aVR."*

Three of the four statements say the R wave is present and is the finding. **The case
authors it present, at 5 mm, with an R to S ratio above 0.7**, and treats "the lack of" as
an error in the narrative. This is the assumption most likely to be wrong in a way that
matters, because the whole ECG teaching rests on it.

### 9.3 The two sets of vital signs. DRAFTING ASSUMPTION.

The narrative table and the initial-presentation table both give BP 130/75, HR 135, RR 25,
SpO2 98 percent, T 104.2 F. The ABEM admitting form gives BP 134/74, P 120, R 21, O2 99
percent, and no temperature at all. **The case uses the first set**, because it appears
twice, because it carries the temperature that half the case turns on, and because a
triage form filled in at the desk and a resuscitation-bay monitor are two different
moments. The admitting form's numbers appear nowhere in the pack.

### 9.4 The chemistry panel. DRAFTING ASSUMPTION. See section 3.6 note 1.

### 9.5 Who gives the history. RESOLVED BY THE AUTHOR. See section 3.2.

The admitting form says "Person giving information: Patient and EMS." The narrative and
the physical examination table say the patient is confused, agitated and combative and
that the mother is the historian. The mother answers.

### 9.6 The obligatory seizure. RESOLVED, from the author's own sentence.

*"A seizure will occur as part of the natural process, regardless of how well the examinee
is doing."* Authored as an unguarded time-guarded transition at 240 seconds, which is
exactly the construct section 5.1 calls a scheduled natural history and exactly the
construct it says must be a decision rather than an oversight. It is a decision, and it is
the author's.

### 9.7 Sepsis and antibiotics. RESOLVED, by tagging for the moment rather than the case.

See section 3.4.

### 9.8 The seizure is escapable. NOT A CONTRADICTION IN THE SOURCE. A DEPARTURE FROM IT.

Recorded here because it belongs in the same list, though its origin is different from the
other seven: the source does not contradict itself about this. It is unambiguous, and the
conversion departs from it.

**What she wrote:** *"A seizure will occur as part of the natural process, regardless of how
well the examinee is doing."*

**What the case now does:** the arrival phase carries an arrow, added on Aakash Setty's
instruction, that moves a patient who has received **both a benzodiazepine and sodium
bicarbonate** into the narrowing phase ten seconds later. A resident who sedates her and
treats the conduction before about 230 seconds therefore never convulses. The seizure rule
is untouched and still carries no guard; it has been given an escape.

**The guard is a conjunction, and that is what makes it defensible.** The first draft of the
arrow, on 5 September 2026, required sodium bicarbonate alone, and that was a weak claim
dressed as a mechanism. Bicarbonate is not an anticonvulsant. It treats the cardiac
sodium-channel blockade and, by correcting the acidaemia, reduces the un-ionised fraction of
drug available to that channel, which is an indirect argument at best, and the agent that
lowered her seizure threshold is still on board and still being absorbed from a gut its own
antimuscarinic effect has slowed down. **What prevents a drug-induced seizure is a
benzodiazepine**, and the guard now says so. Requiring both also states something the case
wanted to teach anyway: in the first four minutes the two things that matter are sedating
the agitation, which is generating the heat and the acid and is itself worsening the
cardiotoxicity, and treating the conduction. Neither alone is enough, and the case now
scores it that way.

**What remains a teaching choice rather than a physiological certainty** is that the pair
*prevents* the seizure rather than making it less likely. A patient who has swallowed a gram
of diphenhydramine may seize through an adequate benzodiazepine dose.

**Two further consequences to sign off.**

1. **The intended path changed.** It used to run through the convulsion. It now runs around
   it: arrival, narrowing, stabilised. The seizure teaching is roughly a third of the
   clinical content of this case, and a strong resident may never meet it. A resident who
   seized has not necessarily done anything wrong: the escape needs the ECG ordered,
   resulted, read and acted on, and a benzodiazepine given, inside 230 seconds.
2. **There is a ten-second dead zone.** The escape needs its ten seconds to mature before the
   240-second deadline, so the boundary is about 230 seconds. A resident who completes the
   pair at 235 seconds convulses anyway, and then leaves the seizure and the post-ictal phase
   on the flags already set. Same resident, ten seconds later, very different debrief.

**Deleting the arrow restores her sentence exactly**, and nothing else in the pack depends
on it.

### 9.9 Amiodarone arrests her. NOT IN THE SOURCE AT ALL.

Added on Aakash Setty's instruction, 5 September 2026. The wide-complex phase carries an
instantaneous transition to the arrest phase guarded on `flag amiodarone_given set`.

**The source does not mention amiodarone anywhere.** Part 2 says to avoid class IA and IC
antiarrhythmics and says to treat the toxicologic mechanism rather than reflexively applying
a standard antiarrhythmic to every wide-complex rhythm, which is the principle this
implements, but the specific claim that amiodarone kills this patient is not hers.

**The clinical reasoning, and its strength.** Amiodarone blocks sodium channels among several
other actions and prolongs the QT, which is already 495 milliseconds here in a patient whose
potassium channels are also affected. Given into a wide-complex rhythm that is itself the
product of sodium-channel blockade, it adds to the block that produced the rhythm. That is
mechanistic reasoning and toxicology practice rather than trial evidence, and it is weaker
than the case against procainamide, which is why the action's tag remains `discouraged` while
its consequence in that phase is death. **Those two disagree, and the reviewer should decide
which to move**: soften the consequence to match the tag, or harden the tag to match the
consequence.

**Two mechanical notes.** The tag cannot be `harmful`, because a harmful tag halts the case
into the shared halted phase and bypasses every transition, so the arrest phase would never
be reached and she would end on generic bradycardic peri-arrest numbers rather than in the
fast wide rhythm the case authors. The cost is that the action scores as one point off its
tab rather than zeroing it; the run is still recorded as failed, which is what the learner
sees. And the arrest phase is now reachable two ways, so its `timeout_reason` names the
outcome they share and both causes.

**The arrow exists only in the wide-complex phase.** Amiodarone given at any other point is
discouraged and does nothing, which is arguable: it is a sodium-channel blocker added to a
sodium-channel-blocker overdose whenever it is given. That is the same shape as the
physostigmine gap in section 2.0 of the review packet and the same decision to make about it.

### 9.10 The images. RESOLVED, EXCEPT WHICH TRACING IS WHICH.

Added on Aakash Setty's instruction, 5 September 2026, after the engine gained a result
payload that is a picture; narrowed the same day.

**What is in the pack.** `media/diph-ecg-arrival.jpg` and `media/diph-cxr.jpg`, resized and
recompressed from the source document. The arrival twelve-lead and the chest radiograph
resolve to those files and to no text at all. Every other ECG in the case, and the radiograph
of the intubated patient, report in words.

**No interpretation is supplied with either**, on instruction. A resident who orders one gets
a thumbnail in the chart, opens it, and reads it. Cardiology will read a tracing aloud if
called, and calling cardiology is not prompted anywhere.

**The second tracing was tried in the narrowing phase and taken out.** Section 0 records the
source as carrying "two wide-complex tachycardia ECGs", and that is what both files are.
Neither is narrow, so the twelve-lead assigned to the narrowing phase showed a broad tracing
under a nurse line saying the complexes had narrowed. That phase reports in text again.
`diph-ecg-post-bicarb.jpg` is kept in `cases/DIPH/assets/` with a note saying how to put it
back, and is out of `media/` because the build inlines that directory whole.

**The restored report is new text.** The original string was overwritten when the image went
in and the repository is not under version control, so it was rewritten to agree with the
numbers the case states elsewhere: 115 per minute, which is the phase's own authored heart
rate, a QRS of 104 ms and a terminal R in aVR of 2 mm, which are what `consult_cardiology`
reads aloud on the repeat tracing, and a QTc of 470. It is model output like every other
number in every tracing in this case. See section 9.2.

**What is still a drafting assumption.** That the remaining image is the arrival tracing
rather than the repeat. The source document does not label them, both are wide-complex, and a
QRS cannot be measured off a scan whose calibration is not readable.

**Second-order effect of removing the report text.** The arrival ECG used to report a QRS of
132 ms in words. It no longer does, so on the likeliest path that number reaches a resident
only through the cardiology consult or the debrief. Putting the machine measurements in the
caption would restore it without supplying an interpretation, and is what a real tracing
prints along its top.

**Provenance is unresolved and now matters more.** Section 0's question about which of the
four images are the author's own work was previously academic, because none was used. Two are
now embedded in a build distributed as a single file.
