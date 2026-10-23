# DKA seed and provenance

Mild diabetic ketoacidosis with a potassium of 3.1 in a 24-year-old woman with type 1
diabetes and gastroenteritis. Drafted by a language model on 6 October 2026 at the request
of Aakash Setty, and revised by a language model on 7 October 2026 after an audit. **No
physician has reviewed this pack.** Authoring requirements section 17 applies. Read every
number as a proposal.

## 0. What a person decided

Aakash Setty, 6 October 2026:

| Decision | What was decided |
|---|---|
| The case | Mild ketoacidosis with some hypokalemia, with a correct order of steps and feedback from several interventions that could have been chosen |
| Insulin threshold | Hold insulin until the potassium is 3.5 or more (said as "3.5" on 6 October, written as "≥3.5" in the table of 7 October below) |
| Clock and death | A case with no clock that harms her and no death is acceptable. Nothing is tagged harmful |
| Catalog | Add beta-hydroxybutyrate, subcutaneous insulin and oral potassium |
| Glargine | "Add glargine as an option." Insulin glargine was added to the catalog and bound here (v0.23a) |
| Sources | Do a source pass before writing |
| Plan | The five-phase plan presented in conversation |

Everything else is model output.

Direction relayed to the model with the audit brief on 7 October 2026, in the owner's
terms. It is recorded here so that he can confirm it. It is not yet a signed decision.

| Subject | Direction |
|---|---|
| Early insulin | Any rapid insulin (infusion, subcutaneous or bolus) given before the potassium has finished running in leads to the falling potassium, whatever the gap between the two orders |
| The rescue | From the falling potassium, holding insulin with intravenous potassium given leads out. Potassium given before the fall counts, because an infusion already running is still running. The debrief says so plainly |
| The restart | After the rescue, one insulin order (infusion or subcutaneous) reaches the treated phase |

No decision above was changed by the audit fix. The audit found no rule that conflicts
with one.

Aakash Setty, 7 October 2026, with a request to re-read the case from the medical side
("use this"): a screenshot of a reference table on potassium in ketoacidosis, cited there
as [11] (the citation itself was not visible). It reads:

| Potassium | Action in the table |
|---|---|
| Under 3.5 mEq/L | Hold insulin. Aggressive repletion, 20 to 40 mEq KCl an hour IV. Recheck every 1 to 2 hours. Start insulin only after K is 3.5 or more |
| 3.5 to 5.5 | Potassium 20 to 30 mEq per liter of IV fluid. Insulin may start concurrently |
| Over 5.5 | Hold potassium. Start insulin. Recheck in 1 to 2 hours |

Its headline bullet says "Do not give insulin until K+ supplementation is underway if
K+ <3.5", which is looser than its own first row. The case follows the row: insulin
starts only once a repeat level is 3.5 or more. The 2024 consensus report, as read through
a summarizing tool, gave a lower replacement rate. The table's rate (20 to 40 mEq an hour)
is now the case's, by this decision, and the report's figure is mentioned in the debrief as
a difference between sources.

## 1. Sources, and how far each was read

| Source | How it was read | What it supplied |
|---|---|---|
| Umpierrez et al., Hyperglycaemic crises in adults with diabetes: a consensus report (ADA, EASD, JBDS, AACE, DTS), 2024 | A mirror of the Diabetologia PDF, through a summarizing tool, by the author and again by an independent checking pass. Figure 4 was not readable. The publisher's sites refused the request | Severity table, potassium threshold and rate, fluid, insulin, dextrose, bicarbonate, phosphate, resolution, level of care |
| UBC RTVS simulation case, Basic Diabetic Ketoacidosis | Opened through the same tool | What another educator's case asks for: glucose, monitor, ECG, lines, fluid, insulin, repeat labs, and a potassium decision before potassium is added |
| FDA drug safety communication on ondansetron and the QT interval | Opened by the checking pass | 6 ms at 8 mg and 20 ms at 32 mg intravenously. Correct potassium and magnesium first |
| Cleveland Clinic Journal of Medicine review of the 2024 report | Opened by the checking pass | Agreement on potassium, bicarbonate, phosphate and level of care |
| EMCrit IBCC chapter on ketoacidosis | Summary, by the checking pass | US practice that differs: a 3.3 threshold, faster potassium |
| MedEdPORTAL case (PMC5491337), 2009 ADA statement, StatPearls | Could not be opened | Nothing. Statements about the 2009 threshold of 3.3 are from memory |

Nobody in this chain has read the publisher's text of the consensus report unfiltered. A
physician should read its Table 2 and Figure 4 before this case is used.

The same list is in the case file as `provenance.reference_status`, one entry per
reference. Every action note, timed transition note and teaching point that rests on one
of these carries an `[UNVERIFIED: ...]` marker. The interface strips the marker. Follow-up
notes and handoff explanations are printed as written, so they carry none, and several of
them cite the consensus report.

## 2. Learning goals and where each is acted on

| Goal | Source | Where the learner acts on it |
|---|---|---|
| Recognize ketoacidosis in a vomiting patient and grade it | Consensus report diagnostic criteria and Table 2. UBC case | The triage note does not mention diabetes. Glucose, gas, chemistry and ketones are orders the learner chooses |
| Know the potassium before insulin, and replace it first when under 3.5 | Consensus report, potassium section | Insulin is available from the first second and shows what it does. Potassium first leads to a different patient |
| Fluid first, and what it does not fix | Consensus report, fluid section | Fluid moves the heart rate and the glucose. A repeat chemistry shows the gap unchanged |
| Insulin without a bolus, by either route | Consensus report, insulin section | Three insulin entries, tagged by phase |
| Plan what follows insulin | Consensus report, dextrose and resolution | A follow-up asks for the dextrose plan. Stopping insulin in the treated phase is discouraged |

## 3. The stories

- Treated well: fluid, potassium found low and replaced, level repeated, insulin, dextrose plan.
- Insulin first: potassium 2.6, weakness, a longer QT. Holding insulin and giving potassium recover her. One insulin order after that treats her.
- Insulin while the potassium is still running: the potassium finishes, and five seconds later she falls the same way. Holding insulin is then enough, because the potassium is already in.
- Bicarbonate: no change to see. A chemistry sent after it on arrival shows the potassium at 2.9.
- Fluid only, by bolus or by infusion: she looks better and the gap is unchanged.
- Left alone: nothing changes in ten minutes. The nurse prompts.

## 3a. The seed content of authoring sections 3.4 to 3.8

**Model output.** Every line below was generated on 7 October 2026 from the pack's own
`case_*.py` files, which a model wrote. It is the list a physician signs. Nothing here
came from a physician.

### 3.4 The action spine, with every route

Critical actions (the phase in which each is critical):

| Act | Catalog entries that count | Critical in | Prompt |
|---|---|---|---|
| Monitor | Attach Monitor | arrival | 20 s |
| Line | Insert IV | every phase | none |
| Bedside glucose | Fingerstick Blood Sugar | arrival | 40 s |
| Blood gas | Venous Blood Gas. An Arterial Blood Gas is accepted in its place | every phase | none |
| Chemistry | Basic Chemistry (Chem 7) | every phase | 75 s |
| Fluid | The four crystalloid boluses (saline or Ringer's, 500 mL or 1 L), by the catalog group. A saline or Ringer's infusion is accepted in its place | every phase | 100 s |
| Intravenous potassium | Potassium Chloride (KCl) | arrival and falling | 110 s once the chemistry is back, and 170 s |
| Insulin once the potassium allows | Insulin drip. Subcutaneous insulin is accepted in its place | potassium replaced and recovering | 45 s in potassium replaced |
| Hold the insulin | Stop Insulin | falling | 25 s |
| Twelve-lead | ECG | falling | 70 s |
| Insulin back on after the rescue | An insulin infusion or subcutaneous insulin ordered in the recovering phase | recovering | 45 s |

Harmful actions: none. Nothing halts the case.

Discouraged actions, with every route:

| Act | Catalog entries covered | When |
|---|---|---|
| Rapid insulin before the potassium is replaced | Insulin drip, Insulin (Subcutaneous), Insulin bolus. The catalog has no insulin group, so each is bound by itself | arrival and falling |
| An insulin bolus at any time | Insulin bolus | every phase |
| Bicarbonate | Na-Bicarbonate bolus and Na-Bicarbonate infusion | every phase |
| Concentrated dextrose | D50 bolus | every phase |
| CT of the abdomen | CT - Abdomen | every phase |
| Stopping insulin once she is treated | Stop Insulin. The catalog has one stop entry for insulin | treated |

Recommended actions: blood ketones, urinalysis, a pregnancy test (urine, or serum in its
place), a magnesium level, magnesium replacement (either catalog entry), an ECG outside the
falling phase, a monitor and a bedside glucose after arrival, intravenous potassium after
arrival, a call to endocrinology, and in the treated phase her basal insulin and
dextrose-containing fluid.

Neutral and unscored, each with a note: a second line, a central line (either entry), an
intraosseous line, an arterial gas, serum hCG, phosphate, blood count, lipase, lactate,
osmolality, chest film, cardiac ultrasound, the two crystalloid infusions, oral potassium,
a D5 bolus, ondansetron, metoclopramide, critical care.

Traps: the insulin bolus, bicarbonate, D50 and the CT.

Not bound, so neutral with a generic note: every antibiotic. See the open questions.

### 3.5 Sequencing

- Prerequisite: intravenous potassium needs a line. Peripheral, central or intraosseous
  all count. The catalog's own line rule covers every other intravenous drug. Nothing is
  waived.
- Follow-up: after intravenous potassium, a repeat potassium. Asked 50 seconds after the
  order. Discharged only by a chemistry sent once the potassium has run in.
- Follow-up: after an insulin infusion or subcutaneous insulin, a dextrose plan. Applies
  only in the treated phase. Asked 60 seconds after the order. Discharged by the D5 half
  saline infusion, or by a D5 bolus given in the treated phase.
- Order of insulin and potassium: section 4 below.

### 3.6 Key findings

Vital signs by phase are in section 4. Laboratory values, with the reference interval
each is flagged against:

| Study | Arrival | After fluid | After bicarbonate | Potassium replaced | Treated | Falling | Recovering | Interval |
|---|---|---|---|---|---|---|---|---|
| Potassium, mEq/L | 3.1 low | 3.0 low | 2.9 low | 3.6 | 3.7 | 2.6 low | 3.6 | 3.5 to 5.0 |
| Sodium, mEq/L | 133 low | 134 low | 135 | 134 low | 135 | 134 low | 134 low | 135 to 145 |
| Chloride, mEq/L | 99 | 101 | 99 | 102 | 104 | 101 | 102 | 98 to 107 |
| Bicarbonate, mEq/L | 16 low | 16 low | 18 low | 15 low | 18 low | 17 low | 17 low | 22 to 29 |
| BUN, mg/dL | 24 high | 22 high | 24 high | 22 high | 20 | 22 high | 22 high | 7 to 20 |
| Creatinine, mg/dL | 1.2 high | 1.1 | 1.2 high | 1.1 | 1.0 | 1.1 | 1.1 | 0.5 to 1.1 (F) |
| Glucose, mg/dL | 348 high | 318 high | 345 high | 320 high | 268 high | 262 high | 285 high | 70 to 140 (random) |
| Anion gap, mEq/L | 18 high | 17 high | 18 high | 17 high | 13 high | 16 high | 15 high | 8 to 12 |
| Venous pH | 7.27 low | 7.27 low | 7.30 low | 7.26 low | 7.30 low | 7.29 low | 7.28 low | 7.31 to 7.41 |
| Beta-hydroxybutyrate, mmol/L | 4.2 high | 4.1 high | 4.2 high | 4.6 high | 3.1 high | 3.4 high | 3.8 high | under 0.6 |
| Fingerstick glucose, mg/dL | 342 | 314 | 342 | 318 | 266 | 258 | 282 | 70 to 140 (random) |

After fluid and bicarbonate together on arrival: sodium 136, potassium 2.9, chloride 101,
bicarbonate 18, BUN 22, creatinine 1.1, glucose 316, pH 7.30.

One value in every state: magnesium 1.5 mg/dL low (1.7 to 2.2), and 2.1 after magnesium.
Phosphate 3.4 mg/dL (2.5 to 4.5). Lactate 1.8 mmol/L (0.5 to 2.0). Lipase 48 U/L (10 to
140). Osmolality 295 mOsm/kg (275 to 295). White count 13.4 high (4.0 to 11.0), hemoglobin
14.9, platelets 310. Urinalysis: glucose 3+, ketones large, protein trace, no leukocyte
esterase, nitrite or bacteria. Pregnancy test negative. The pCO2 on each gas is calculated
from the pH and the bicarbonate.

ECG by phase. QRS 88 ms throughout. No report quotes a rate.

| Phase | Report | QTc |
|---|---|---|
| Arrival | Sinus tachycardia, subtle T wave flattening, small U waves in V2 and V3 | about 460 |
| Potassium replaced | Sinus tachycardia, T waves fuller, small U waves | 450 |
| Treated | Sinus rhythm, T waves normal, small U waves | 445 |
| Falling | Sinus tachycardia with occasional ventricular ectopic beats, flat T waves, prominent U waves, 0.5 mm lateral ST depression | about 520 |
| Recovering | Sinus tachycardia, no ectopic beats, T waves fuller | 450 |

Ondansetron adds 5 ms to the QTc on a repeat ECG in any phase.

Exam findings that are abnormal, and how each changes:

| Maneuver | Arrival | Changes |
|---|---|---|
| General status | Tired and dry, vomit bowl, breathing deeply, alert | Falling: lying flat, arms and legs heavy, frightened. Treated: sitting up, color better, no longer retching |
| Breathing | Deep, slightly fast, no accessory muscle use | Treated: easier, rate about 20 |
| Circulation | Pulse fast, regular, low volume, refill 3 seconds, hands cool | After fluid: refill 2 seconds, hands warming. Falling: occasional dropped beats. Treated: regular, good volume, hands warm |
| Head and mouth | Lips and tongue dry, fruity breath | none |
| Heart | Fast and regular, no murmur | Falling: occasional extra beats. Treated: regular |
| Abdomen | Soft, mild diffuse tenderness, no guarding, old appendectomy scar | Treated: tenderness settling |
| Skin | Dry, reduced turgor, injection sites clean, feet intact | none |
| Neurological | Alert, power 5 of 5, reflexes normal | Falling: proximal weakness 4 of 5, reflexes reduced |
| Cardiac ultrasound | Hyperdynamic ventricle, vena cava small and collapsing | none. Derived by a model on 7 October 2026 |

Normal throughout: airway, neck (veins flat, supple), lungs, flanks, back, calves and
joints, mental state.

### 3.7 Interview ground truth

Facts she reports. Those marked (added) are not in `patient.background`. A model put them
in an answer.

- Vomiting since Sunday night, two days ago. About ten times. Yellow, no blood. Cannot keep water down.
- Watery diarrhea from a few hours after the vomiting, six or seven times a day, slowing today.
- Crampy pain all over the abdomen, in waves with the diarrhea, about four out of ten. Mostly central. Trying to drink makes her sick. Lying still helps.
- Very thirsty since yesterday and passing a lot of urine. Up four times in the night (added). Less urine this morning, and dark.
- Weak all over. She can walk.
- Heart beating fast, not irregular.
- Taking big breaths, not short of breath, no wheeze.
- Lightheaded on standing. Had to sit down in the shower this morning (added). Has not fainted.
- Felt hot and shivery the first night, temperature not taken, not since (added).
- A dull head, not a bad headache.
- Type 1 diabetes since age eleven. One admission, at diagnosis. Last clinic check fine.
- Lantus 18 units at night, Humalog with meals, both by pen. The pill. Nothing else.
- No Humalog while not eating. Half her Lantus on Sunday night, none last night.
- Meter 380 this morning and 290 last night (the 290 is added). No ketone strips.
- Appendix out at fifteen.
- A period two weeks ago. She vomited on Sunday and may have lost a pill (added).
- Roommate had three days of the same illness last week.
- Nothing solid since Sunday. Sips of water and flat soda. A cracker this morning.
- Graduate student, shares an apartment. Does not smoke. A couple of glasses of wine on weekends, none this week. No drugs.
- Mother has a thyroid problem (added). Nobody else has diabetes.
- Runs twice a week. In class on Friday.

After early insulin: weakness much worse, arms and legs heavy, heart fluttering and
missing beats. In the treated phase: nausea easing, no vomiting since treatment, breathing
easier.

Pertinent negatives she states:

- No chest pain. No cough or sore throat. No pain going to the back or the shoulder.
- No burning on passing urine, no smell, no flank pain, no discharge.
- No blood in the vomit. No blood in the stool.
- No allergies. No travel. Does not think she is pregnant.
- No other medical problems. No other surgery.
- No leg cramps (added by a model on 7 October 2026).
- Stool not black (added by a model on 7 October 2026).

Seven topics are marked `pertinent_negative`: radiation of pain, chest pain, cough and
sore throat, urinary symptoms, allergies, pregnancy and travel. Fever, headache and family
history lost the mark on 7 October 2026 because each reports something.

She never names ketoacidosis. Two answers sit near the line in authoring 10.4. She says
"they said my blood had gone acidic" about her admission at eleven, and she quotes her own
meter. Both are flagged in `interview.authoring_notes`.

Key topics for the History score, the same list as the held-out file's
`management_changing`: past medical history, diabetes history, medications, insulin taken
recently, sugar readings, thirst and urination, sick contacts, pregnancy, allergies. None
is volunteered.

### 3.8 Disposition

Correct: step-down or intermediate care with telemetry. She needs hourly glucose, an
insulin regimen being adjusted, intravenous potassium and a monitor. The potassium is what
puts her there. The consensus report's own table suggests a regular or observation unit
for mild ketoacidosis.

| Disposition | Verdict | Why |
|---|---|---|
| Intensive care | Defensible | Safe and more than she needs. Right where every insulin infusion goes to intensive care |
| Medical ward with telemetry | Defensible | The report suggests a regular unit. Right where the ward can do hourly glucose and monitored potassium |
| Observation unit | Defensible | Listed by the report for mild ketoacidosis. A poor fit for monitored potassium replacement unless set up for it |
| Discharge home | Incorrect | Still in ketoacidosis and cannot keep fluid down |
| Transfer | Incorrect | This hospital has what she needs |

Correct diagnosis: diabetic ketoacidosis (`dx_diabetic_ketoacidosis`).

Also true and credited beside it: hypokalemia, hypomagnesemia, viral gastroenteritis,
hypovolemia, and since 7 October 2026 hyponatremia and acute kidney injury.

As the primary diagnosis: hypokalemia and anion gap metabolic acidosis are defensible.
Viral gastroenteritis, infectious gastroenteritis, hypovolemia, hyperosmolar hyperglycemic
state, alcoholic ketoacidosis, acute pancreatitis, acute appendicitis, hyperemesis
gravidarum and cannabinoid hyperemesis syndrome are incorrect, each with a reason.

## 4. Phases, transitions and the race table

| Phase | Monitor chip | HR | BP | K | Reached |
|---|---|---|---|---|---|
| presentation | on arrival | 112 | 104/64 | 3.1 | arrival |
| potassium_replaced | after potassium | 112 | 104/64 | 3.6 | 20 seconds after intravenous potassium is ordered on arrival, unless insulin's rule fires first |
| treated | improving | 104 | 106/66 | 3.7 | 10 seconds after an insulin infusion or subcutaneous insulin ordered in potassium_replaced or in recovering |
| potassium_falling | weak | 118 | 102/62 | 2.6 | 10 seconds after any rapid insulin ordered on arrival. Or 5 seconds after the potassium finishes, when that insulin was ordered while it ran |
| recovering | recovering | 112 | 104/64 | 3.6 | 20 seconds after both the hold and intravenous potassium are in, from potassium_falling |

Authored rates are without fluid. A crystalloid bolus or infusion takes ten off the rate
and adds six to the pressure in every phase, for the rest of the case. No report, exam line
or nurse line quotes a rate.

Every timed rule is the delayed consequence of an action. None fires on inaction.

| From | Guard | Delay | To |
|---|---|---|---|
| presentation | `flag insulin_given set` | 10 s from the order | potassium_falling |
| presentation | `flag potassium_iv_given set` | 20 s from the order | potassium_replaced |
| potassium_replaced | `action early_insulin taken` | 5 s from entry | potassium_falling |
| potassium_replaced | `flag insulin_running set` | 10 s from the order | treated |
| potassium_falling | `flag potassium_iv_given set AND flag insulin_stopped set` | 20 s from the moment both hold | recovering |
| recovering | `action insulin_restart taken` | 10 s from the order | treated |

**How order is carried.** Flags are permanent and cannot say when. Three hidden case
actions do. Nothing presses them. Each is credited through `also_satisfies` on a real
order, judged on the phase at the moment of that order (authoring 6.8 and 8.2).

| Hidden action | Credited when | Read by |
|---|---|---|
| `early_insulin` | An insulin infusion, subcutaneous insulin or an insulin bolus is ordered in the arrival phase | The first rule of potassium_replaced |
| `insulin_restart` | An insulin infusion or subcutaneous insulin is ordered in the recovering phase | The exit of recovering. It is also tagged critical there and carries the restart prompt |
| `repeat_potassium_level` | A chemistry is sent in potassium_replaced, recovering or treated | The repeat-potassium follow-up |

The repeat-granted flags of v0.23 are gone. `insulin_restarted` counted insulin orders and
could not tell a restart from a second order. `chem_repeated` counted chemistries and
could not tell a repeat after replacement from a repeat before it. Nothing else read
either.

**The race table (authoring 5.4).** Two phases have two timed rules. Each row has a test
with fractional times in `DKA-tests.js`, section "the race table".

Arrival phase. Insulin's rule is 10 seconds and is first in the list. Potassium's is 20.

| What the learner does | Which rule fires first | Where she ends up |
|---|---|---|
| Insulin, then potassium at any gap before the fall | insulin's, at 10 seconds | falling. The potassium flag is set, so holding insulin alone then rescues her. Intended |
| Insulin, then potassium after the fall | insulin's | falling, until insulin is held |
| Potassium, then insulin less than 10 seconds later | insulin's, due first | falling, 10 seconds after the insulin |
| Potassium, then insulin exactly 10 seconds later | both due together. Insulin's is higher in the list | falling |
| Potassium, then insulin more than 10 and up to 20 seconds later | potassium's, at 20 seconds | potassium_replaced for 5 seconds, then falling by that phase's first rule. This was the gap of v0.23 |
| Potassium, then insulin more than 20 seconds later | potassium's. The insulin is ordered in potassium_replaced | potassium_replaced, then treated 10 seconds after the insulin. The intended path |

An order logged at the same instant as a deadline is applied first. So insulin ordered at
exactly 20 seconds is still early insulin.

Potassium_replaced phase. The early-insulin rule is 5 seconds and first. The insulin rule
is 10.

| State on entry | Which rule fires first | Where she ends up |
|---|---|---|
| Early insulin was an infusion or subcutaneous | both clocks start on entry. The early rule is due at 5 seconds, the other at 10 | falling |
| Early insulin was a bolus, and an infusion is ordered inside the 5 seconds | the early rule. Its clock started on entry, the other's started later | falling |
| No early insulin, then an infusion or subcutaneous dose | only the insulin rule is pending | treated |
| No early insulin, a bolus alone | neither | she stays in potassium_replaced |

The early rule can only be pending on entry. The hidden action is earned in the arrival
phase and nowhere else, so nothing a learner does in potassium_replaced can start it.

## 5. Changed after the independent check (6 October 2026)

- Ondansetron adds 5 ms to the QTc, not 20. Twenty is the figure for a 32 mg dose.
- The insulin bolus note was garbled and now follows the report's sentence.
- Phosphate is normal on arrival (3.4), and the note gives the report's cutoff as printed.
- Every blood gas is now consistent with the Henderson-Hasselbalch equation.
- Creatinine 1.2 is flagged abnormal for a 58 kg woman.
- Step-down is still the correct disposition, and the explanation now says the potassium
  is the reason. The report's own table suggests a regular or observation unit for mild
  ketoacidosis.
- Waiting for potassium now has a visible cost: ketones 4.2 to 4.6, bicarbonate 16 to 15.
- Bicarbonate lowers the potassium by 0.2, not 0.3.
- The arrival ECG is subtler, because many tracings are normal at 3.1.
- Wording softened on basal insulin, abdominal pain, lipase and the patient's weakness.

## 5a. Changed on 7 October 2026 after the audit, and why

### 5c. Potassium with the insulin (decided 7 October 2026, installed 13 October 2026)

Aakash Setty, 7 October 2026: "When the potassium goes up to 3.6, insulin should be started
but potassium should also be ordered again as in the middle row." Decided: critical. The
change was built that day and did not reach the Mac (the link dropped at the install
step). It was re-applied to the current sources and installed on 13 October 2026.

- A hidden target `potassium_maintenance`, critical in potassium_replaced, recovering and
  treated, credited when intravenous potassium is ordered again in one of those phases
  (judged on the phase at the moment of the order). The first order, and the rescue order
  in the falling phase, do not credit it. Handed over on insulin without it, it is listed
  as missed.
- The potassium order's nurse line is a rule list (engine, 13 October 2026: `nurse_alert`
  may be a list of rules). On arrival and in the falling phase: "It's on the pump. It takes
  a while to run in." Once the level is 3.5 or more: "Twenty to thirty in each liter from
  here. I'll keep it running with the insulin."
- A prompt at 45 seconds in the treated phase: "She's on insulin now. Do you want
  potassium in her fluids?" (135 seconds in the default mode).
- An endocrinology tier for the treated phase with no second order, asking for it by
  name, under the 40-word rule of 11 October. The existing treated tiers sit behind it.
- The intended path, the learning objectives, the debrief domain and the review packet
  name the second order.
- A model choice to confirm: a second potassium order placed in potassium_replaced before
  insulin starts also earns the credit, because "keep potassium going" is right either way.

### 5b. Changed on 7 October 2026 after the medical re-read, and why

A model re-read the whole pack against the potassium table in section 0. Changes:

- Potassium replacement rate: 20 to 40 mEq an hour with a recheck every one to two hours,
  in the potassium debrief note, the endocrinologist's plan, the potassium-replaced
  transition note and the teaching points. Was 10 mEq an hour with "up to 20 with central
  access", from the consensus report as read. The hours the twenty seconds stand for are
  now one to three, not four to six.
- The rule by level (under 3.5, 3.5 to 5.5, over 5.5) is now in the potassium note, the
  endocrinologist's plan and the first teaching point, so the learner leaves with the
  whole rule and not only the branch this patient is on.
- "Above 3.5" is "3.5 or more" in every string, to match the table's ≥3.5. The repeat
  level in the case is 3.6 either way.
- Potassium in the fluids: "20 to 30 mEq in each liter with the potassium between 3.5
  and 5.5". Was "under 5.0", from the report as read.
- Recheck interval: every one to two hours while replacing and at first on insulin. Was
  "two hours after insulin starts and every four hours", from the report as read.
- Hyponatremia is no longer credited. A sodium of 133 at a glucose of 348 corrects to
  about 137 to 139 (1.6 to 2.4 per 100 mg/dL of glucose above 100), which is normal. It is
  now a defensible alternative whose explanation teaches the correction. Naming it costs
  nothing. Leaving it out costs nothing.
- Acute kidney injury is no longer credited. A single creatinine of 1.2 with no baseline
  does not meet the definition. Same handling as hyponatremia, with "repeat after fluid"
  as the handover.
- The hypokalemia handover explanation says the level is checked every one to two hours
  while it is being replaced. Was "every two to four hours".

Checked on the re-read and left alone, with the reasoning: the gases are self-consistent
by Henderson-Hasselbalch and the arterial pCO2 of 31 to 32 sits inside Winter's range for
a bicarbonate of 15. The calculated osmolality (2 × 133 + 348/18 + 24/2.8) is 294 against
the authored 295. The anion gap of 18 is correct for 133, 99 and 16. Mild ketoacidosis by
the 2024 report's bands (pH 7.25 to under 7.30, bicarbonate 15 to under 18, alert) fits
7.27, 16 and GCS 15. The ketone criterion (3.0 mmol/L or more) and the resolution criteria
(under 0.6 with pH 7.3 or bicarbonate 18 or more) match the report as read. Dextrose at a
glucose under 250 matches. Bicarbonate only under pH 7.0 matches. The insulin dose of 0.1
units per kg per hour matches.

A model made every change below. The audit reports are the DKA pack audit (29 findings),
the docs audit Part 2 (findings 14 to 21) and the catalog audit (4.1, 5.11, 6.1).

Order of insulin and potassium:

- Insulin ordered 11 to 19 seconds after potassium no longer reaches treated. The
  potassium finishes, and five seconds later she falls. Why: the lesson leaked for any
  learner who gave the two close together in the right order.
- A learner whose first insulin was a bolus no longer needs two infusion orders after the
  rescue. One order placed in the recovering phase is the restart, from any history.
- Two insulin orders before the hold no longer count as a restart.
- Restarting insulin after the rescue is a critical action of its own, with its own
  prompt. Why: the insulin action could already count as done from the early order, so a
  learner who handed over with insulin still off was told every critical action was
  achieved, and the nurse never asked.
- The hold line now says "It stays off until you order it again."

Follow-ups:

- The repeat-potassium follow-up is discharged only by a chemistry sent once the potassium
  has run in. Two chemistries sent before the potassium used to discharge it, and a first
  chemistry sent after replacement did not.
- The dextrose follow-up is no longer discharged by a D5 bolus given on arrival, lists
  both insulin routes as its trigger, and its prompt no longer says the sugar "is coming
  down".

The nurse:

- The potassium line no longer says she is on the monitor or promises a call back.
- The oral potassium line no longer says she vomited it, which was false in the treated
  phase.
- The first potassium prompt moved from 45 to 110 seconds and the escalation from 130 to
  170. Why: the chemistry prompt is at 75, so a learner who needed it never heard the
  first potassium line. The escalation no longer says "still".
- The insulin prompt asks for a repeat level first, and is said in both ready phases.
- The potassium prerequisite uses the catalog's three-flag line rule. The central line and
  intraosseous entries are bound, neutral, so that the validator accepts it.
- US usage in the nurse's lines and her answers ("She doesn't have a line yet", "I have type 1 diabetes").

Results, findings and consultants:

- Result comments are gone, apart from one caption on the chemistry. Each sentence moved
  to the debrief note of that study.
- No ECG report or exam line quotes a heart rate. The treated ECG says sinus rhythm. The
  falling ECG says QRS 88 ms, as the monitor draws.
- The treated status line is no longer flagged abnormal, and the treated heart exam no
  longer says fast. Derived from the pack's own treated findings.
- Neither consultant names a laboratory value. Each has a tier per study state. The
  falling-phase lines read no result.
- The cardiac ultrasound is authored, so it no longer reports a normal vena cava in a dry
  patient.
- The two crystalloid infusions count as her fluid and move the monitor like a bolus.

Interview:

- The out-of-scope bank no longer refuses weakness, leg cramps, night urination, blood in
  the stool, black stools, what she studies or back pain. Each now reaches a topic.
- Two denials were added so those questions have an answer: no leg cramps, stool not
  black.
- Three topics lost the pertinent-negative mark. Two wrong phrasings left the chest pain
  topic. The insulin topic no longer draws phrasings about tablets. The sick-contact topic
  no longer draws phrasings about her own recent illness.
- One volunteer line is left, reworded. Past medical history, the diabetes history and
  thirst are must-ask. The diabetes history is a key topic.
- Six topics carry facts.

Handoff and provenance:

- Hyponatremia and acute kidney injury are additional diagnoses.
- Markers on 48 action notes, 4 timed transition notes and 3 teaching points.
- The provenance block lists each reference with how it was read, and the sign-off list
  follows the section 2 table.
- The monitor chip for potassium_replaced reads "after potassium".

## 6. Known gaps

- Doses are not modeled, so the rate of potassium cannot be taught by doing.
- A hold pressed before any insulin was given still counts as the hold. A learner who
  holds, gives potassium and then gives insulin early falls and recovers 20 seconds later
  with no further action. A test and a scenario pin it.
- Insulin reordered during the rescue wait is ignored. She recovers, and the reorder is
  not the restart. No nurse line says the insulin is on hold at that point, so none is
  made false. A test and a scenario pin it.
- On the route where the potassium finishes before early insulin acts, she spends five
  seconds in potassium_replaced. A chemistry sent in that window reads 3.6 and counts as
  the repeat level. Five seconds later she falls.
- The scenario runner does not implement `also_satisfies`. Scenarios that depend on a
  hidden action name it as a step. The engine tests fold the real routes.
- The restart prompt asks for a repeat level whether or not one was sent.
- The first potassium prompt has one deadline for two phases. In the falling phase it
  comes at 110 seconds, after the hold prompt at 25 and the ECG prompt at 70.
- The fluid effect never ends, and phase rules come before flag rules, so the trace of
  fluid or bicarbonate on a chemistry disappears when the phase changes.
- The falling phase describes extra and dropped beats over a regular beat and a regular
  trace. The rhythm field has no value for it.
- A spoken "insulin" offers the bolus or the infusion and not the subcutaneous entry.
- Glargine is recommended once she is treated and unscored before that. It never lowers
  the potassium.
- The potassium threshold in many US protocols is 3.3. This case uses 3.5 by decision.
- The held-out interview questions were written by the same author as the variant bank.
  Two management-changing questions go to the wrong topic (review packet).
- The chest film and the abdominal CT are the catalog defaults, which are normal. Intended.

## 7. Open questions for the physician

Each says what the pack does today.

1. **Should intravenous potassium require the monitor first?** Today it needs a line only,
   and the nurse no longer says she is on the monitor. Option: a case prerequisite with
   the message "She's not on a monitor. I'd want her on one before potassium runs."
2. **Does a crystalloid infusion earn the same credit as a bolus?** Today yes. It sets the
   fluid flag, moves the monitor the same way and satisfies the fluid expectation. The
   infusion's own tag is neutral. Option: leave infusions unscored and keep asking for a
   bolus.
3. **Does potassium given before the fall count toward the rescue?** Today yes, as
   directed on 7 October 2026. Holding insulin alone then rescues her, and the debrief
   says why. Confirm the direction and the wording.
4. **Is restarting insulin after the rescue a critical action?** Today yes, in the
   recovering phase, shown in the debrief as "Insulin back on, once the potassium is above
   3.5". Option: leave it unscored and keep only the phase exit.
5. **Diagnoses that need a verdict.** Sepsis, urinary tract infection, euglycemic diabetic
   ketoacidosis and starvation ketosis are plausible wrong answers with no authored
   explanation. Each costs five points with a generic note. All four ids exist.
6. **True statements that still cost points.** Type 1 diabetes mellitus, hyperglycemia and
   acquired long QT are now in the catalog. Named beside the ketoacidosis, each is "not
   supported" and costs five points. Options for each: an additional diagnosis (the 20
   points are then shared among more entries), a defensible alternative (no cost beside
   the primary, half credit as the primary), or leave it.
7. **Hyponatremia and acute kidney injury.** Since the medical re-read of 7 October 2026
   both are defensible alternatives, not credited and not penalized. The hyponatremia
   explanation teaches the glucose correction (133 corrects to about 137 to 139). The
   kidney explanation says a single creatinine of 1.2 with no baseline is not an acute
   kidney injury and should be repeated after fluid. Confirm both explanations.
8. **Antibiotics.** Ceftriaxone and piperacillin-tazobactam are unbound, so neutral with a
   generic note. The blood count note says a white count of 13 does not on its own mean
   she needs antibiotics. Should they be discouraged?
9. **Glargine before she is treated.** Unscored today, and it never lowers the potassium.
   Should a basal dose at a potassium of 3.1 be discouraged?
10. **Two chemistry values.** In potassium_replaced the anion gap reads 17 against 18 on
    arrival, while the bicarbonate falls from 16 to 15 and the ketones rise from 4.2 to
    4.6. A chloride of 101 would give 18. In recovering the gap reads 15 after 16 in the
    falling phase while the ketones rise from 3.4 to 3.8. New numbers are needed.
11. **Two denials a model added.** "No cramps" in the weakness answer, on arrival and
    after early insulin. Should she have cramps at a potassium of 2.6? And "it isn't
    black" in the diarrhea answer.
12. **Facts in her answers that the background does not hold.** The seven marked (added)
    in 3.7.
13. **The pregnancy topic is marked a pertinent negative.** Her answer is "I don't think
    so", with a period two weeks ago and a pill she may have lost. Keep the mark?
14. **The hold before any insulin.** Today it counts (known gaps). Option: a prerequisite
    on Stop Insulin, "She hasn't had any insulin."
15. **A second insulin order while one is running.** Today it is accepted and changes
    nothing. Option: a prerequisite that refuses it. It would also close the reorder gap.
16. **The potassium prompt in the falling phase.** 110 seconds in the easy mode and 330 in
    the default mode. Is that too late for the rescue?
17. **Derived on 7 October 2026 from the pack's own findings.** The cardiac ultrasound
    report. The treated ECG as "sinus rhythm". The treated heart exam as "Regular". The
    treated status line as not abnormal. Each needs a signature.
18. **Central and intraosseous lines.** Bound neutral so the line rule validates. Should
    either be discouraged in a patient with a working peripheral line?
19. **The level of care.** The report's table suggests less than step-down for mild
    ketoacidosis. This case argues the potassium moves her up.
20. **The five seconds in potassium_replaced before she falls.** A level sent then reads
    3.6. Acceptable?

## 8. Engine and catalog changes made for the case

- v0.23, on the directing physician's instruction: catalog entries for beta-hydroxybutyrate,
  subcutaneous insulin and oral potassium, with default results and voice phrases.
- v0.23a, on the directing physician's instruction: a catalog entry for insulin glargine.
- 7 October 2026, by the catalog fix that preceded this one: diagnosis ids for euglycemic
  diabetic ketoacidosis, starvation ketosis, hyperglycemia, type 1 diabetes mellitus and
  acquired long QT. Cover tags in the out-of-scope list. Four topics added to this pack's
  map.
- 7 October 2026, by this fix, in `catalog/expand_interview_variants.py`, this pack's
  entries only: `back_pain` added to `EXTRA_COVERED`. `insulin_taken_recently` removed
  from `MAP` (its `adherence` phrasings name tablets). `recent_illness_sick_contacts`
  removed from the `sick_contacts` entry in `MAP`.
- No engine change. The three hidden case actions use `also_satisfies` and `hidden`, which
  the engine already had.

## 9. Awaiting sign-off beyond the list in the case file

Model-written text added on 7 October 2026:

- Patient answers: "No cramps" (twice), "it isn't black", and the short forms on six
  topics' facts.
- Consultant lines: every line of both consultants was rewritten. The advice is the same.
  The pending and default tiers are new.
- Nurse lines: the potassium alert, the oral potassium line, the hold line, the potassium
  escalation, both insulin prompts, the dextrose follow-up prompt, and the narration into
  recovering.
- Debrief notes: the notes on the two infusions, the restart, the three line entries and
  the cardiac ultrasound are new. The chemistry, gas, ECG and blood count notes took in
  the sentences that used to be result comments.
- Handoff: the two explanations for hyponatremia and acute kidney injury.

## What a person decided

- 11 October 2026, Aakash Setty: every consultant answer over 40 words is shortened to 40 or fewer (authoring 9.5), keeping what the consultant thinks, what to do now and the disposition or callback. Wording by a model. Rule order, conditions, tags and debrief notes are unchanged. Not physician reviewed. Six of fourteen answers changed, all endocrinology. Dropped: the potassium infusion rate and the line it needs, the 20 to 30 per liter figure (now "potassium in every liter"), and "don't stop insulin because the sugar looks better" (now "keep the insulin going"). The falling-phase answer says palpitations where the narration says fluttering. Mild on the gas now says subcutaneous rapid-acting insulin works too, and the infusion rate is in the answer after replacement.
- 23 October 2026, Aakash Setty: the handover is scored on one or two major diagnoses and nothing minor. Here the primary and hypokalemia. Moved to `minor_diagnoses`, credited if named and never penalized if left out: hypomagnesemia, viral gastroenteritis and hypovolemia. Which diagnosis stayed scored was a model's pick, accepted by the author. Explanations unchanged. Not physician reviewed.
