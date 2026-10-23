# TSS seed and provenance

Menstrual staphylococcal toxic shock syndrome in a 22-year-old woman. Drafted by a language
model on 6 October 2026 at the request of Aakash Setty. **No physician has reviewed this
pack.** Authoring requirements section 17 applies: the AUTHOR-ONLY fields were generated,
so a physician is authoring the ground truth in review. Read every number as a proposal.
On 7 October 2026 a model changed the pack after an audit against authoring requirements
v0.24. Sections 0 and 4a are a person's decisions and were not touched. Section 7 says what
changed and why. Sections 8 to 12 are new. Nothing added on that day has been read by a
physician.
## 0. What a person decided

Aakash Setty, 6 October 2026, in answer to four questions asked before drafting:

| Question | Decision |
|---|---|
| Which antibiotic orders count | Vancomycin plus clindamycin is the target. A broad agent added is accepted without penalty. Missing clindamycin is noted in the debrief only and is not scored |
| Discharge as gastroenteritis | She faints on standing and the case continues |
| Response to removing the tampon | It stops the decline. No dramatic rebound |
| When norepinephrine is expected | Once the mean pressure stays under 65 after about 30 mL/kg. More fluid without a vasopressor is allowed and she keeps sliding |

He also approved, in outline, the patient, the story and the three learning goals in the
case plan written in the same conversation. Everything else below is model output.
## 1. Learning goals, and what in the case makes the learner act on each

| Goal | What the case contains so the learner meets it by deciding |
|---|---|
| Recognize shock in a young patient who compensates | She talks, apologizes and blames a takeout meal. Only the monitor, the capillary refill and the lactate say otherwise. Discharge is available and has a consequence |
| Find the source and remove it | Nobody mentions her period. The history and the pelvic examination are available and never prompted on arrival. Her course changes only when the tampon is out |
| Resuscitate toxin-mediated shock | The first liter helps and the help fades. Further fluid buys six points for a minute. A vasopressor is what holds her |
## 2. Phases

Six clinical phases and one terminal. No halted phase, no arrest, nothing tagged harmful.

| Phase | HR | BP | RR | SpO2 | T | Reached |
|---|---|---|---|---|---|---|
| presentation | 128 | 94/58 | 22 | 97 | 39.4 | arrival |
| fluid_responsive | 114 | 104/62 | 20 | 98 | 39.2 | ten seconds after any crystalloid bolus |
| hypotensive | 138 | 78/42 | 26 | 95 | 39.6 | fluid response fades at 150 s. Or no fluid by 300 s. Or five seconds after an attempted discharge |
| supported | 124 | 92/50 | 24 | 96 | 39.5 | fluid and a vasopressor, tampon still in |
| profound_shock | 148 | 66/32 | 30 | 92 | 39.8 | hypotensive 240 s without both fluid and a vasopressor. Or supported 270 s with the source in |
| stabilizing | 116 | 98/56 | 22 | 97 | 39.1 | fluid, a vasopressor and the source out |

The intended path passes through `hypotensive`. That follows the fourth decision above.
## 3. What needs a physician's signature first

1. Every vital sign in the table above.
2. The five clocks: 300, 150, 240, 270 and 5 seconds.
3. Every laboratory value and reference interval in `case_3_content.py`.
4. That removing the tampon stops the decline within ten seconds of case clock.
5. That she always faints on an attempted discharge.
6. The tags in `case_2_actions.py`, above all: nothing harmful, rate control and a
   diuretic only discouraged, intubation discouraged until she is obtunded.
7. Every sentence in every debrief note. Notes that lean on a guideline or trial carry
   `[UNVERIFIED]`.

Added on 7 October 2026. The audit found the list above left out AUTHOR-ONLY rows of
authoring section 2. Each of these also needs a signature:

8. Consultant advice: every reply of the intensivist, infectious disease, gynecology and
   nephrology. The intensivist's tiers were rewritten and the nephrology reply is new.
9. Prompt deadlines and their relative urgency: monitor 20 seconds, vasopressor 30, line
   45, fluid 60, source 60, vancomycin 110. Escalations at 120 (vasopressor), 170 (fluid)
   and 180 (source).
10. The two follow-ups and whether they apply: a second liter 60 seconds after a bolus
    unless a vasopressor is running, and sedation 90 seconds after intubation.
11. The two case prerequisites: a pelvic examination before removal, and a running
    vasopressor before a stop.
12. Every coverage row in `TSS-binding-map.json`. Section 9 lists them.
13. The size and duration of every vital effect. The review packet has the table.
14. `key_topics` (nine topics) and `key_exams` (six examinations), which set the History
    and Physical scores.
15. Everything in section 8 under "Awaiting sign-off".
## 4. Checked, and by what

An independent model pass on 6 October 2026 opened the CDC 2011 toxic shock case
definition, the Surviving Sepsis Campaign 2021 text, the SCCM guideline page, StatPearls
and the Internet Book of Critical Care, and compared the pack against them. It was not a
physician review. It found 18 problems and the ones that could teach something false were
fixed the same day:

- The lumbar puncture note said she had no headache and cited platelets of 98 as a reason.
  She has a mild headache and 98 is not a contraindication. Rewritten.
- "A supple neck makes meningitis unlikely" and "the rash decides it" were too certain.
  Softened.
- The arterial gases were not consistent with their own pH and pCO2. Bicarbonate lowered.
- Creatinine was 2.2 against an upper limit of 1.2, which does not meet the CDC renal
  criterion of twice the upper limit. Now 2.6.
- "The indication for norepinephrine" is now "an indication", and the note no longer
  claims 30 mL/kg was given when only one bolus was.
- Six smaller contradictions between notes and authored values.

Confirmed against an opened source: the CDC criteria and thresholds, that her findings
meet a probable case once she is hypotensive, 30 mL/kg as a weak recommendation, a mean
pressure target of 65, norepinephrine first, peripheral vasopressors as acceptable short
term, blood culture yield under 5 percent, clindamycin for toxin suppression on non-trial
evidence, weak evidence for immunoglobulin, and desquamation at one to two weeks.

Not verified by anyone: the SOAP II figures behind the dopamine note, that most menstrual
toxic shock is methicillin-susceptible, lactate over 4 as a risk marker, and the CT
appearance of a tampon. The Surviving Sepsis guideline has a newer edition than the one
opened.
## 4a. Approved by Aakash Setty, 6 October 2026

After reading the summary of the finished case he approved these five as drafted:

1. The overlap with MGCA stands. The two cases are a deliberate pair.
2. The five clocks: 300, 150, 240, 270 and 5 seconds.
3. Cool hands with a four-second capillary refill in a flushed patient.
4. Rate control is discouraged and does not halt the case.
5. The dopamine note and the note that most menstrual toxic shock is
   methicillin-susceptible stay as written, with their `[UNVERIFIED]` markers.

This is approval of the design choices. It is not the section 14.3 sign-off, and the
laboratory values, tags, notes and interview are still unreviewed.
## 5. Open questions for the physician

1. Her hands are cool with a four-second capillary refill while she is flushed. Early toxic
   shock is classically warm. The case treats her as both dry and vasodilated. Is that the
   patient you want?
2. Pulse pressure is 36 to 42 in every phase. A wider one would read as more distributive.
3. Hemoglobin 14.9 on day five of a period. Plausible as hemoconcentration. Anemia is
   also described in toxic shock.
4. No calcium is authored. Hypocalcemia is described in toxic shock.
5. Would she really go to the beach with a fever of 102 and six stools a day? The beach
   exists to give her an explanation for the rash.
6. This case and MGCA are both a young woman with fever, a rash and shock. MGCA asks about
   tampons as a negative. Played in sequence they are a deliberate pair. Played back to
   back a learner may guess. Decide whether the welcome list should separate them.
7. Linezolid is not in the catalog. Some centers prefer it to vancomycin here.

Questions 8 to 31 were added on 7 October 2026. For each, the pack does what "Today" says
until a physician decides.

**Values the pack does not author.** Each study below returns the catalog's normal result
today, beside an authored picture it may not fit. A physician supplies the value or confirms
the normal.

| # | Study | What the learner sees today | Beside |
|---|---|---|---|
| 8 | ESR | 10 mm/hr, normal | CRP 238, procalcitonin 24.0 |
| 9 | LDH | 180 U/L, normal | CK 2,140, AST 148 |
| 10 | D-dimer | 0.31 mcg/mL FEU, normal | Platelets 98, PT 15.4, INR 1.3, aPTT 39 |
| 11 | Calcium, total | 9.4 mg/dL, normal | Albumin 2.9. This was question 4 |
| 12 | Calcium, ionized | 1.22 mmol/L, normal | The same |
| 13 | Phosphate | 3.5 mg/dL, normal | Creatinine 2.6, lactate up to 9.4 |
| 14 | Magnesium | 2.0 mg/dL, normal | Creatinine 2.6 |
| 15 | Troponin T | "Unremarkable" | Lactate up to 9.4, creatinine 2.6 |
| 16 | NT-proBNP | "Unremarkable" | Lactate up to 9.4, creatinine 2.6 |

**Tags and routes.**

17. Thirteen studies, the nephrology consult, the maintenance infusions, the bag valve mask,
    non-invasive ventilation, lorazepam and morphine were given a neutral tag on 7 October
    2026 so that each has a debrief note. Section 8 lists them. Options for each: neutral,
    recommended or discouraged. Two to look at first: serum hCG is neutral while urine hCG
    is recommended, and the venous gas is neutral while the lactate is recommended.
18. Adenosine is not bound. Today it is unscored, moves nothing and gets the generic note.
    Options: add it to the rate-control row (discouraged, with the same fall in rate and
    pressure), give it its own action and note, or leave it. Procainamide is in the same
    position.
19. D5 NS bolus and D5 1/2 NS infusion are not bound. Today neither counts as fluid and
    neither is scored. Options: count D5 NS bolus as a crystalloid bolus, put the D5 1/2 NS
    infusion with the maintenance infusions, or leave both.
20. A central line or an intraosseous needle as her only access is not credited as access,
    and the nurse still says "She's got no line" at 45 seconds. Options: bind the three
    entries and let them satisfy the access action, or leave it.
21. Bag valve mask and non-invasive ventilation raise the saturation by 4 in the two low
    phases, the same as a non-rebreather mask and not stacked on one. The 4 was copied from
    the mask by a model. Options: keep, change the size, or tag either route discouraged in
    a patient who is breathing for herself.
22. Ampicillin is not bound. Today it is unscored and sets no antibiotic flag. Option: add
    it to the broad beta-lactam row.

**Handoff.**

23. Five alternatives exist in the diagnosis catalog and have no authored verdict or
    explanation: bacterial meningitis, urinary tract infection, staphylococcal scalded skin
    syndrome, orthostatic hypotension and undifferentiated shock. Today each gets the
    generic "not supported" note and costs five points. Options for each: incorrect with an
    explanation, acceptable with qualification, or leave generic.
24. The additional diagnoses went from four to nine. The 20 points for them are shared pro
    rata, so each is now worth less and a learner must name nine for full marks. Options:
    keep all nine, or keep the electrolyte entries as explanations without credit.

**What the nurse and the consultants say.**

25. The source escalation at 180 seconds in the supported and profound shock phases asks
    "Has anyone asked about her period?" Section 1 says nobody mentions her period. The
    line predates the audit. It was reworded from a statement to a question and otherwise
    left. The intensivist and infectious disease also name tampons when called. Options:
    keep all three as late rescue hints, or remove the word from the nurse's line.
26. The stop line ends "Tell me again if you really want it off." A second press gets the
    same refusal. Options: keep, or drop the sentence.
27. Nephrology's reply and the intensivist's eight tiers are in `case_3_content.py`. Every
    sentence restates a debrief note. Confirm or rewrite.

**Interview.**

28. "Any black stools?" is refused with the fallback. The diarrhea answer says "No blood"
    and opens with "Yes, watery", so it was not used for this question. Options: add a
    denial, or leave it out of scope.
29. She says she is a grad student. What she studies and which year are not authored, so
    "What are you studying?" is refused. Options: author a subject, or leave it.
30. "Any nosebleeds?" and "Any nosebleeds or nasal packing?" get the wounds answer, "No. No
    cuts, no boils, nothing like that." It names neither. Nasal packing is a recognized
    source of toxic shock. Options: add "No nosebleeds, nothing in my nose" to the answer,
    or accept the general denial. [UNVERIFIED]
31. Questions still in the out-of-scope bank that touch something the case authors
    elsewhere: blood in the urine (the urinalysis shows blood), yellow skin or eyes
    (bilirubin 2.6), mouth ulcers (the Stevens-Johnson explanation says she has none),
    weakness in arms or legs, how she got here. Today each is refused. Decide which should
    be denials or answers. The drowsy answer to the confusion topic is "I feel foggy.
    Sorry.", so that topic is no longer marked a pertinent negative. Decide whether it
    should deny.
## 6. Engine and catalog changes made for this case (v0.21)

- Catalog: `remove_vaginal_foreign_body` under Procedures.
- Engine: `handoff.disposition_intercepts` and `hidden` case actions, so one disposition
  can have a consequence instead of ending the run.
- Engine fix, found by playing this case in a browser: a delayed consequence could fail to
  fire until the next click, in every pack. See CHANGELOG v0.21.
- Catalog, 7 October 2026: the diagnosis catalog gained Thrombocytopenia and Retained
  vaginal foreign body, both asked for by this pack, and the voice table sends "pelvic
  exam" to the genitourinary examination.
- This line was in the case file's `catalog_change_requests` and is an engine note, so it
  lives here now: the patient figure cannot show a rash or a flush, so the erythroderma is
  text only.
- `catalog/expand_interview_variants.py`, this pack's line only, 7 October 2026:
  `"TSS": ["character_general", "nosebleeds", "back_pain", "leg_cramps"],`. The tags
  `occupation` and `gi_bleeding` were taken off because each covers a question she cannot
  answer (questions 28 and 29).

## 7. What changed on 7 October 2026, and why

A model made every change below. The finding numbers are the audit's. No clock, phase, vital
sign or laboratory value from 6 October was changed.

| Finding | What was wrong | What the pack does now |
|---|---|---|
| 1 | Timed narrations quoted figures the monitor did not show while a vital effect was acting | No narration quotes a figure. Each keeps the direction. The test folds each effect-bearing route and compares with the monitor |
| 2 | The source prompt said fluid and norepinephrine had been given, and fired in profound shock on the do-nothing path | "She's a young woman in shock and no source has been dealt with. Has anyone examined her from head to toe, including a pelvic exam?" |
| 3 | Two escalations named a consequence that had already happened or could not happen | Fluid: "She still hasn't had a fluid bolus. She is dry and she needs volume. Can I hang a liter?" Vasopressor: "Her mean pressure is still under 65. Can I start norepinephrine?" |
| 4 | "Norepinephrine" was said when vasopressin, epinephrine, phenylephrine or dopamine was running | The alert, seven narrations, two status lines, the monitor chip, two phase labels and the intensivist say "the vasopressor" |
| 5 | Stop Norepinephrine did not cover the other stop buttons, and spoke when nothing was running | One action covers five stop entries. Discouraged only while a vasopressor runs. Blocked with "There's no vasopressor running to stop." when none is |
| 6 | Unbound routes | Digoxin and amiodarone are rate control. Cefotaxime is broad cover. Furosemide is bound through the loop diuretic group. The two maintenance infusions are their own neutral action. Four oxygen routes share one effect key |
| 7 | Result comments named the diagnosis, her period and the reviewer | Removed or cut to what the numbers show. The reviewer sentence is in `verify` |
| 8 | Twelve authored studies had no case action | Each has a neutral tag and a debrief note built from the removed comments |
| 9 | Catalog normals contradicted the authored picture | FAST agrees with the CT. The skin biopsy says it was taken. Nine studies are questions 8 to 16 |
| 10 | The intensivist said "Fluid in" without testing it, and "Good" in profound shock | Eight tiers. A profound shock tier first. Every claim of a treatment tests its flag |
| 11 | Markers missing | Cefazolin, lactate, CT, immunoglobulin, hydrocortisone, clindamycin and urinalysis notes carry one. None sits in a field the interface prints |
| 12 | One sentence of reference status that contradicted this file | A list of eight entries, each with how it was read |
| 13 | Sign-off list left out AUTHOR-ONLY rows | Section 3, items 8 to 15, and the case file's list |
| 14 | The packet did not show vital effects as teaching choices | It has the table |
| 15 | This file lacked authoring sections 3.1 to 3.8 | Section 12 |
| 16 | The fade has no warning | Left as it is, and recorded in section 10 |
| 17 | In the default mode the fluid warning landed on the instant the hypotensive phase ends | Fluid and source prompts moved from 80 and 75 to 60. Section 10 has the arithmetic |
| 18 | Three volunteer lines repeated the answer they ride on | Replaced |
| 19 | The out-of-scope bank refused questions she can answer | Eleven hand variants, the bank regenerated, two cover tags removed |
| 20 | "My back is the worst" against "not in my back" | Thighs and calves are worst. The drowsy abdominal answer adds "Not my back." |
| 21 | Three topics had facts, and the background left out the ibuprofen | Six topics have facts. The background has the ibuprofen, the wisdom teeth and the 102 reading |
| 22 | True statements cost points at handover | Five additional diagnoses credited |
| 23 | Change requests incomplete | Linezolid and a liver injury diagnosis are requested. Calcium and the engine line moved out |
| 24 | Sedation follow-up left out satisfiers | Midazolam, lorazepam and morphine count |
| 25 | Small items | Oxygen is recommended in both low phases. The trace has PR 140. The arterial saturation is the phase's. Six notes reworded. The psychiatric finding in the two vasopressor phases no longer has her asking to go home |
| Docs 5 | A sedative given before the tube discharged the follow-up | A bolus counts only with the tube in. An infusion counts whenever it was started |
| Catalog 3.6 | "pelvic exam" ordered a pelvis film | Fixed in the catalog. The pack now says "pelvic exam" wherever it says the word aloud, and a test checks it |

Three changes went beyond the audit, each for the same rule as a finding:

- The line prompt says "She's got no line", so its guard now tests the access flag. Before,
  a learner who pressed Second IV first heard it.
- The discharge line said "Her rate is still fast". After a liter and rate control the
  monitor reads 98. It now says "She still has a fever."
- The confusion topic lost its pertinent negative mark (question 31).

## 8. Awaiting sign-off: what a model wrote or decided on 7 October 2026

**Neutral tags given as placeholders.** Each action had no case action or was unbound, and
neutral is what the catalog would have served. None is a verdict.

- `venous_blood_gas`
- `arterial_blood_gas`
- `liver_function_tests_lfts`
- `creatine_kinase_ck`
- `coagulation_panel`
- `plasma_procalcitonin`
- `c_reactive_protein_crp`
- `urinalysis`
- `serum_hcg_quantitative`
- `peripheral_smear`
- `ecg_12_lead`
- `ultrasound_cardiac`
- `ultrasound_fast`
- `consult_renal`
- `normal_saline_infusion`
- `bag_valve_mask`
- `non_invasive_positive_pressure_ventilation`
- `lorazepam_bolus`
- `morphine_bolus`

**A hidden action that is not a button.** `sedation_after_tube` is a case-only action added
by a model under authoring 8.2, so that a sedative given before the tube does not discharge
the sedation follow-up. It is on no tab, is not in search and has no spoken phrase, so it
gives the learner nothing. Authoring 7.1 asks that a case-only action be a physician's
recorded decision. This one is not yet. Options: keep it, or go back to counting any dose
given at any time.

**Patient answers a model wrote or edited.**

- `location_of_pain`: "My thighs and calves are the worst." It said thighs and back.
- `abdominal_pain`, drowsy answer: "Crampy. All over. Not my back."
- Volunteer lines: fever "It was 102 when I took it yesterday." Vomiting "I can't even keep
  water down now." Diarrhea "And I've had watery diarrhea, no blood."
- Facts on `fever_and_chills`, `nausea_vomiting` and `current_medications`. Every word of
  each is in the topic's own answer, and a test checks that.
- American usage: "throwing up" for "being sick" in three places, "in the hospital", "A lot"
  for "Loads", "never sick" for "never ill".
- Eleven hand variants in `EXTRA_VARIANTS`, each under the topic whose answer covers it.

**Other text a model wrote.** All of it restates sentences the pack already had.

- Thirteen study notes and the nephrology note, in `case_2_actions.py`.
- The intensivist's eight tiers and nephrology's three, in `case_3_content.py`.
- The five new additional diagnosis explanations, in `case_5_handoff.py`.
- The maintenance infusion alert and note, and the two notes for the bag and non-invasive
  ventilation.
- The psychiatric finding for the two vasopressor phases: "Awake, cooperative, tired. No
  longer asking to go home."

**Values derived from the pack's own numbers.** Each carries a `verify` note.

- The FAST report, from the CT's "Small volume of free pelvic fluid".
- The arterial saturation in each phase, from that phase's monitor saturation.
- The anion gap of 17 in the chemistry comment: 131 minus 97 minus 17.
- The saturation effect of 4 for the bag and non-invasive ventilation, from the mask.
- The skin biopsy line, which states that a biopsy was taken and gives no result.

## 9. The action spine, with every route (authoring 3.4 and 3.5)

Generated from `case_2_actions.py` and `TSS-binding-map.json` on 7 October 2026. A model
wrote every tag except where section 0 or 4a records a decision. The first id on each line
is the case action. The rest are catalog entries it covers.

**Critical**

- `attach_monitor`. critical when phase is presentation / recommended otherwise
- `insert_iv`. critical in every state
- `normal_saline_1l_bolus`, `group crystalloid_bolus`. neutral when phase is stabilizing / critical otherwise
- `remove_vaginal_foreign_body`. critical in every state
- `norepinephrine_drip`, `epinephrine_drip`, `vasopressin_drip`, `phenylephrine_drip`. critical when phase is hypotensive OR phase is profound_shock / recommended when phase is fluid_responsive OR phase is supported OR phase is stabilizing / neutral otherwise
- `vancomycin`. critical in every state

**Recommended**

- `attach_monitor`. critical when phase is presentation / recommended otherwise
- `second_iv`. recommended in every state
- `nasal_cannula_oxygen`. recommended when phase is hypotensive OR phase is profound_shock / neutral otherwise
- `non_rebreather_mask`. recommended when phase is hypotensive OR phase is profound_shock / neutral otherwise
- `norepinephrine_drip`, `epinephrine_drip`, `vasopressin_drip`, `phenylephrine_drip`. critical when phase is hypotensive OR phase is profound_shock / recommended when phase is fluid_responsive OR phase is supported OR phase is stabilizing / neutral otherwise
- `insert_foley_catheter`. recommended in every state
- `lactate`. recommended in every state
- `blood_culture_x_2`. recommended in every state
- `basic_chemistry_chem_7`. recommended in every state
- `complete_blood_count_cbc`. recommended in every state
- `urine_hcg_qualitative`. recommended in every state
- `consult_critical_care`. recommended in every state

**Discouraged**

- `propofol_bolus`. discouraged in every state
- `midazolam_bolus`. discouraged in every state
- `intubate_rapid_sequence`. neutral when phase is profound_shock / discouraged otherwise
- `dopamine_drip`. discouraged in every state
- `stop_norepinephrine`, `stop_epinephrine`, `stop_vasopressin`, `stop_phenylephrine`, `stop_dopamine`. discouraged when flag pressor_running set / neutral otherwise
- `ibuprofen`. discouraged in every state
- `metoprolol_bolus`, `esmolol_drip`, `labetalol_bolus`, `labetalol_drip`, `propranolol_bolus`, `diltiazem_bolus`, `digoxin_bolus`, `amiodarone_bolus_infusion`. discouraged in every state
- `furosemide_40_mg_iv`, `group loop_diuretic`. discouraged in every state
- `lumbar_puncture`. discouraged in every state
- `attempt_discharge`. discouraged in every state

**Harmful.** None. The pack cannot end in death and nothing halts it.

**Neutral with a note or a flag.** `normal_saline_infusion`, `lactated_ringer_s_infusion`, `bag_valve_mask`, `non_invasive_positive_pressure_ventilation`, `etomidate_bolus`, `ketamine_bolus`, `rocuronium_bolus`, `succinylcholine_bolus`, `fentanyl_bolus`, `lorazepam_bolus`, `morphine_bolus`, `ketamine_infusion`, `propofol_infusion`, `sedation_after_tube`, `phenylephrine_bolus`, `clindamycin`, `ceftriaxone`, `cefepime`, `piperacillin_tazobactam`, `meropenem`, `cefotaxime`, `cefazolin`, `intravenous_immunoglobulin`, `hydrocortisone_bolus`, `acetaminophen`, `ondansetron`, `ct_abdomen`, `venous_blood_gas`, `arterial_blood_gas`, `liver_function_tests_lfts`, `creatine_kinase_ck`, `coagulation_panel`, `plasma_procalcitonin`, `c_reactive_protein_crp`, `urinalysis`, `serum_hcg_quantitative`, `peripheral_smear`, `ecg_12_lead`, `ultrasound_cardiac`, `ultrasound_fast`, `consult_infectious_disease`, `consult_ob_gyn`, `consult_renal`, `handoff_submit`.

**Traps.** Discharge as gastroenteritis, rate control, ibuprofen, a diuretic, a lumbar
puncture, early intubation, dopamine and stopping the vasopressor are the discouraged ones
above. Ondansetron, acetaminophen and the CT are neutral traps with a note.

**Sequencing.**

- Prerequisite on `remove_vaginal_foreign_body`: `action exam_gu taken`. "I can set up a speculum, but nobody has examined her down there yet. Do you want to do the pelvic exam first?"
- Prerequisite on `stop_norepinephrine`: `flag pressor_running set`. "There's no vasopressor running to stop."
- Follow-up `second_liter`: 60 seconds after `normal_saline_1l_bolus`, applies when `flag fluids_given set AND NOT flag pressor_running set`, discharged by `flag fluids_30mlkg set OR flag pressor_running set`.
- Follow-up `post_intubation_sedation`: 90 seconds after `intubate_rapid_sequence`, applies when `flag intubated set`, discharged by `propofol_infusion`, `ketamine_infusion`, `sedation_after_tube`.
- No catalog prerequisite is waived.
- `also_satisfies`: fentanyl, midazolam, lorazepam and morphine credit `sedation_after_tube`
  when `flag intubated set`.

## 10. Time: the default mode, pending rule pairs, and what is deliberately unwarned

**The fade is not warned about, on purpose.** In the fluid-responsive phase the response to
fluid ends at 150 seconds whatever the learner does. No prompt names a vasopressor there, in
either mode. This follows decision 4 in section 0: norepinephrine is expected once the mean
pressure stays under 65 after fluid, so the learner is meant to see the pressure fall first.
The hypotensive phase it leads to is recoverable with one order and its prompts start at 30
seconds. Authoring 5.2 rule 2 asks for a prompt before a deterioration. This is the recorded
exception.

**Default mode (authoring 9.7).** The mode a learner starts in multiplies prompt, escalation
and follow-up deadlines by three and leaves the clocks alone.

| Clock | Prompt it rests on | Authored | Default mode | Time left to act |
|---|---|---|---|---|
| 300 s, no fluid | Fluid | 60 | 180 | 120 s |
| 240 s, hypotensive | Vasopressor | 30 | 90 | 150 s |
| 240 s, hypotensive | Fluid, if none given | 60 | 180 | 60 s |
| 270 s, source in | Source | 60 | 180 | 90 s |

The fluid prompt was 80 and the source prompt was 75. At 80 the default-mode fluid warning
fell on second 240 of the hypotensive phase, the same instant as its exit, and was never
said. The owner's clocks were not moved.

Known limits in the default mode. The first two are pinned by tests:

- No escalation is heard before the exit it warns about. They fall at 360, 510 and 540.
- The second-liter follow-up comes 180 seconds after the bolus, which is after the fade.
- The vancomycin prompt comes at 330 seconds of a phase and is heard only in a phase that
  lasts that long.

**Two timed rules pending at once (authoring 5.4).** Confirmed in the engine with fractional
times. "Faint" is the 5-second rule after an attempted discharge.

| Phase | What the learner does | Which rule fires first | Where she ends up |
|---|---|---|---|
| presentation | Bolus, then discharge less than 5 s later | The faint | Hypotensive, with fluid given |
| presentation | Bolus, then discharge exactly 5 s later | Both due together. The faint is higher in the list | Hypotensive |
| presentation | Bolus, then discharge more than 5 s later | The fluid response | Fluid-responsive, then the faint 5 s after she enters it |
| presentation | Discharge more than 5 s before second 300 | The faint | Hypotensive |
| presentation | Discharge in the last 5 s before second 300 | The 300 s clock | Hypotensive. The faint is never narrated. Known limit |
| presentation | Bolus any time before second 300 | The fluid response, 10 s after the bolus | Fluid-responsive |
| presentation | Bolus after second 300 | The 300 s clock already fired | Hypotensive. One action too late |
| fluid_responsive | Discharge more than 5 s before the fade | The faint | Hypotensive |
| fluid_responsive | Discharge in the last 5 s before the fade, no vasopressor | The fade | Hypotensive, with the fade's narration |
| fluid_responsive | Discharge in the last 5 s before the fade, vasopressor running | The fade | Supported. She never faints and the discharge is spent. Known limit |
| fluid_responsive | Vasopressor before the fade | The fade, to supported or stabilizing | Never hypotensive |
| fluid_responsive | Vasopressor after the fade | The fade, to hypotensive | Supported 10 s after the order |
| hypotensive | The second of fluid and vasopressor before second 240 | The 10 s rule | Supported or stabilizing |
| hypotensive | The second of the two after second 240 | The 240 s clock | Profound shock. One action too late |
| hypotensive | Source out during the 10 s wait | The 10 s rule to supported | Supported, then stabilizing 10 s later |
| supported | Source out before second 270 | The 10 s rule | Stabilizing |
| supported | Source out after second 270 | The 270 s clock | Profound shock, then stabilizing 15 s after the removal |

**Narration and the monitor.** No narration quotes a figure. "Pressure" in a narration is
judged on the mean arterial pressure. One known limit, pinned by a test: a vasopressor
infusion with no fluid plus a push dose inside 90 seconds lifts the systolic above the
arrival figure, 98 over 42 against 94 over 58, while the nurse says her pressure has
dropped. The mean and the diastolic have fallen. The systolic has not.

## 11. Known gaps

- Two 500 mL boluses count as 30 mL/kg. The four crystalloid boluses are one catalog group
  and one counter, and the simulator has no doses. The second-liter note says so. Splitting
  the half-liter entries would need a second counter for the same flag, which the engine
  resolves by whichever fills first, so a liter plus two half liters would not count.
- The ECG report gives the phase's heart rate. For 60 seconds after a bolus in a low phase,
  and for 180 seconds after rate control, the monitor reads lower than the report. Authoring
  11.4 requires the rate to come out only where an effect has no end. Option: drop the rate.
- A gas or a lactate never sees a vital effect. Oxygen in the two low phases shows on the
  monitor and not on the arterial gas.
- Debrief notes on three timed transitions quote arrival figures. Rate control taken
  earlier makes the monitor differ from them.
- The handover says "something she ate". Authoring 14.3 says the handover names no
  diagnosis in clinical or lay words. This is the patient's own wrong explanation, repeated
  by the triage nurse, and it is the trap the case is built on. Recorded as an exception.
- The nurse's source prompt says "head to toe". Said into the microphone, "head" orders the
  head and neck examination. "pelvic exam" orders the genitourinary examination. A bare
  "pelvic" is offered as a choice between that examination and a pelvis film.
- The interview matcher was measured on the lexical stage only. The embedding stage was not
  run.
- `cases/review/` has no question bank for this pack, so its open questions live here.

## 12. Authoring sections 3.1 to 3.8, as a list a physician can sign

Copied on 7 October 2026 from the `case_*.py` files. A model wrote all of it on 6 October
2026 except what sections 0 and 4a record. Read every number as a proposal.

### 3.1 Identity

- Working title: 22-year-old woman, vomiting and diarrhea for two days, walked in with her roommate
- Chief complaint, her words: "I think I've got food poisoning. I can't keep anything down."
- Clinical complaint: Vomiting and diarrhea. Category: Infectious disease
- Scored diagnosis: `dx_toxic_shock_syndrome`
- Final diagnosis, prose: Menstrual staphylococcal toxic shock syndrome from a tampon retained for about four days, with septic shock, acute kidney injury, thrombocytopenia, transaminitis and early rhabdomyolysis. Blood cultures are expected to stay negative, as they usually do in staphylococcal toxic shock.
- Target level: medical_student, intern, junior_resident
- Learning objectives:
  - Recognize shock in a young, talking patient from the heart rate, the blood pressure, the capillary refill and the lactate, and do not let a plausible story of gastroenteritis explain them away.
  - In fever, rash and hypotension with no clear source, ask about menstruation and tampon use and do a pelvic examination.
  - Remove the source. A retained tampon is found and removed at the bedside, and nothing else in the resuscitation replaces that.
  - Give about 30 mL/kg of crystalloid, reassess, and start norepinephrine when the mean arterial pressure stays under 65 after fluid.
  - Start antibiotics early that cover staphylococci including MRSA, and know why clindamycin is added in toxin-mediated disease.
  - Admit to intensive care, and name the organ injuries at handover.

### 3.2 Patient and setting

- 22-year-old female, 62 kg.
- Graduate student, lives with one roommate. No past medical history. Wisdom teeth removed at eighteen and no other surgery. Takes a combined oral contraceptive pill. She took ibuprofen yesterday, two tablets a couple of times, and nothing else. No allergies. Does not smoke, drinks socially, uses no drugs.
- Her period started five days ago. She uses super-absorbency tampons. Four days ago she put one in before an evening out, came home late, and did not take it out. She believes her period has ended and has not thought about the tampon since. Two days ago she developed fever, muscle aches, vomiting and watery diarrhea, which she puts down to a takeout meal. Yesterday she took her temperature and it was 102. The same day she spent an hour at the beach and blames her red skin on that. This morning she nearly fainted in the shower and her roommate drove her in.
- Appearance: A young woman sitting up on the bed, talking in full sentences and apologizing for coming in. She is flushed all over, her lips are dry, and she keeps a vomit bag in her lap. She does not look as sick as her numbers.
- Care setting: Urban academic emergency department. Adult emergency department with an intensive care unit, infectious disease and gynecology on call, and a full laboratory and imaging service. Nothing in this case is limited by resources.
- Arrival: mode `triage`, location `patient_room`.
- Handover, two sentences, 32 words: "Twenty-two year old, two days of vomiting and diarrhea, says she thinks it was something she ate. Her roommate drove her in after she nearly passed out in the shower this morning."

### 3.3 Phases

Section 2 has the table. What happens if the learner does nothing: hypotensive at 300
seconds, profound shock 240 seconds later, and she stays there. The pack cannot end in
death.

### 3.4 and 3.5 The action spine and sequencing

Section 9.

### 3.6 Key findings

**Laboratory values that are flagged abnormal.** One value per study unless a phase is named.

| Study | Component | Value | Unit | Reference interval |
|---|---|---|---|---|
| `lactate` | Lactate | presentation 4.6, fluid_responsive 4.0, hypotensive 6.8, supported 5.6, profound_shock 9.4, stabilizing 3.8 | mmol/L | 0.5-2.0 |
| `venous_blood_gas` | pH | presentation 7.30, fluid_responsive 7.31 (not flagged), hypotensive 7.24, supported 7.27, profound_shock 7.16, stabilizing 7.31 (not flagged) |  | 7.31-7.41 |
| `venous_blood_gas` | pCO2 | presentation 34, fluid_responsive 35, hypotensive 31, supported 32, profound_shock 28, stabilizing 34 | mmHg | 41-51 |
| `venous_blood_gas` | HCO3 | presentation 17, fluid_responsive 18, hypotensive 14, supported 15, profound_shock 11, stabilizing 17 | mEq/L | 22-26 |
| `venous_blood_gas` | Base excess | presentation -8, fluid_responsive -7, hypotensive -12, supported -10, profound_shock -16, stabilizing -8 | mEq/L | -2 to +2 |
| `venous_blood_gas` | Lactate | presentation 4.6, fluid_responsive 4.0, hypotensive 6.8, supported 5.6, profound_shock 9.4, stabilizing 3.8 | mmol/L | 0.5-2.0 |
| `arterial_blood_gas` | pH | presentation 7.33, fluid_responsive 7.34, hypotensive 7.27, supported 7.30, profound_shock 7.19, stabilizing 7.34 |  | 7.35-7.45 |
| `arterial_blood_gas` | pCO2 | presentation 29, fluid_responsive 30, hypotensive 26, supported 27, profound_shock 23, stabilizing 29 | mmHg | 35-45 |
| `arterial_blood_gas` | pO2 | presentation 92 (not flagged), fluid_responsive 92 (not flagged), hypotensive 78, supported 92 (not flagged), profound_shock 64, stabilizing 92 (not flagged) | mmHg | 80-100 on room air |
| `arterial_blood_gas` | HCO3 | presentation 15, fluid_responsive 16, hypotensive 12, supported 13, profound_shock 9, stabilizing 15 | mEq/L | 22-26 |
| `arterial_blood_gas` | Base excess | presentation -8, fluid_responsive -7, hypotensive -12, supported -10, profound_shock -16, stabilizing -8 | mEq/L | -2 to +2 |
| `arterial_blood_gas` | O2 saturation | presentation 97 (not flagged), fluid_responsive 98 (not flagged), hypotensive 95 (not flagged), supported 96 (not flagged), profound_shock 92, stabilizing 97 (not flagged) | % | 95-100 |
| `basic_chemistry_chem_7` | Sodium | 131 | mEq/L | 135-145 |
| `basic_chemistry_chem_7` | Potassium | 3.3 | mEq/L | 3.5-5.0 |
| `basic_chemistry_chem_7` | Chloride | 97 | mEq/L | 98-107 |
| `basic_chemistry_chem_7` | Bicarbonate | 17 | mEq/L | 22-29 |
| `basic_chemistry_chem_7` | BUN | 41 | mg/dL | 7-20 |
| `basic_chemistry_chem_7` | Creatinine | 2.6 | mg/dL | 0.6-1.2 |
| `complete_blood_count_cbc` | WBC | 17.4 | x10^9/L | 4.0-11.0 |
| `complete_blood_count_cbc` | Platelets | 98 | x10^9/L | 150-400 |
| `liver_function_tests_lfts` | AST | 148 | U/L | 10-40 |
| `liver_function_tests_lfts` | ALT | 121 | U/L | 7-56 |
| `liver_function_tests_lfts` | Total bilirubin | 2.6 | mg/dL | 0.1-1.2 |
| `liver_function_tests_lfts` | Direct bilirubin | 1.4 | mg/dL | 0.0-0.3 |
| `liver_function_tests_lfts` | Albumin | 2.9 | g/dL | 3.5-5.0 |
| `liver_function_tests_lfts` | Total protein | 5.8 | g/dL | 6.0-8.3 |
| `creatine_kinase_ck` | Creatine kinase | 2140 | U/L | 30-200 |
| `coagulation_panel` | PT | 15.4 | sec | 11.0-13.5 |
| `coagulation_panel` | INR | 1.3 |  | 0.8-1.1 |
| `coagulation_panel` | aPTT | 39 | sec | 25-35 |
| `plasma_procalcitonin` | Procalcitonin | 24.0 | ng/mL | < 0.10 |
| `c_reactive_protein_crp` | CRP | 238 | mg/L | < 5 |
| `urinalysis` | Color | Dark amber |  | yellow |
| `urinalysis` | Clarity | Slightly cloudy |  | clear |
| `urinalysis` | Protein | 1+ |  | negative |
| `urinalysis` | Ketones | 2+ |  | negative |
| `urinalysis` | Blood | 2+ |  | negative |
| `urinalysis` | Leukocyte esterase | 1+ |  | negative |
| `urinalysis` | WBC | 10-20 | /hpf | 0-5 |
| `urinalysis` | RBC | 10-20 | /hpf | 0-2 |
| `peripheral_smear` | report | Neutrophilia with a left shift and toxic granulation. Platelets reduced. No schistocytes. No blasts. | | |

Authored and not flagged: urine hCG negative, serum hCG under 5, blood cultures with no
growth to report, hemoglobin 14.9, hematocrit 45, glucose 104, alkaline phosphatase 118.

**Imaging and ECG.**

- `ecg_12_lead`: Sinus tachycardia at the phase heart rate. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST elevation or depression.
- `ultrasound_cardiac`: Hyperdynamic left ventricle. No pericardial effusion. Right ventricle not dilated. Inferior vena cava small and collapsing with each breath.
- `ultrasound_fast`: No free fluid in Morison's pouch or the splenorenal recess. Small volume of free fluid in the pelvis. No pericardial effusion.
- `ct_abdomen` when `flag source_removed set`: Mild diffuse small bowel wall thickening. Small volume of free pelvic fluid. No abscess. Normal appendix. No hydronephrosis.
- `ct_abdomen`: Cylindrical air-containing object in the vaginal canal. Mild diffuse small bowel wall thickening. Small volume of free pelvic fluid. No abscess. Normal appendix. No hydronephrosis.
- Chest film: left to the catalog default, which is normal, on purpose.

**Examination findings.** Each line is one maneuver. Where a finding changes, the phases are named.

- `exam_airway`: [flag intubated set] Endotracheal tube in place and secured. / [phase is profound_shock] Patent. Not speaking, moans to pain. Gag present. / [otherwise] Patent. Speaking in full sentences. Lips dry.
- `exam_breath`: [flag intubated set] Ventilated. Chest rising equally. / [phase is profound_shock] Rapid shallow breathing. No accessory muscle use. / [phase is hypotensive] Tachypneic. Short sentences. No accessory muscle use. / [otherwise] Mildly tachypneic. Full sentences. No accessory muscle use.
- `exam_circ`: [phase is profound_shock] Capillary refill over 6 seconds. Radial pulse barely palpable. Mottled to the thighs. / [phase is hypotensive] Capillary refill 5 seconds. Radial pulse weak and fast. Hands and feet cold. / [phase is supported] Capillary refill 4 seconds. Radial pulse weak. Hands cool. / [phase is stabilizing] Capillary refill 3 seconds. Pulses fuller. Hands warming. / [phase is fluid_responsive] Capillary refill 3 seconds. Pulse fast, fuller than before. Hands cool. / [otherwise] Capillary refill 4 seconds. Pulse fast and thready. Hands cool.
- `exam_heent`: Both conjunctivae red, no discharge. Tongue red, lips cracked, mouth dry. Pupils equal, reactive.
- `exam_neck`: Supple, no meningism. Neck veins flat. Trachea central.
- `exam_card`: [phase is profound_shock] Regular tachycardia, heart sounds soft. No rub. No edema. / [otherwise] Regular tachycardia. Soft systolic flow murmur. No rub. No edema.
- `exam_pulm`: Clear, equal air entry. No crackles or wheeze.
- `exam_abd`: Soft. Mild diffuse tenderness, no guarding or rebound. Bowel sounds active.
- `exam_gu`: [flag source_removed set] Tampon removed. Vaginal walls red, no tear or ulcer. No cervical motion tenderness. / [otherwise] Retained tampon in the vaginal vault, dark and foul-smelling. Vaginal walls red.
- `exam_back`: No costovertebral angle tenderness. Spine non-tender. Rash continues over the back.
- `exam_msk`: Diffuse muscle tenderness, thighs and calves. No joint swelling. Calves soft.
- `exam_skin`: [phase is profound_shock] Diffuse blanching red rash. Knees and thighs mottled. No petechiae, no wounds. / [otherwise] Diffuse blanching red rash, trunk, limbs, palms, under clothing. No petechiae, no wounds.
- `exam_neuro`: [flag intubated set] Sedated. Pupils equal and reactive. / [phase is profound_shock] Opens eyes to pain, confused words. GCS 10. Moves all limbs. / [phase is hypotensive] Drowsy, rouses to voice, oriented when roused. GCS 14. No focal deficit. / [otherwise] Alert, oriented. GCS 15. No focal deficit. No photophobia.
- `exam_psych`: [phase is profound_shock] Cannot be assessed. Not answering questions. / [phase is hypotensive] Drowsy and slow to answer. No longer asking to go home. / [phase is supported OR phase is stabilizing] Awake, cooperative, tired. No longer asking to go home. / [otherwise] Calm, cooperative, apologetic. Asks when she can go home.

**General status line.**

- flag intubated set: Intubated and sedated. Flushed.
- phase is profound_shock: Obtunded, gray and mottled, responds only to pain. GCS 10.
- phase is hypotensive: Gray and drowsy, rouses to voice. Flushed skin. GCS 14.
- phase is supported: Awake, washed out, flushed. Vasopressor running. GCS 15.
- phase is stabilizing: Awake, tired, flushed. Vasopressor running. GCS 15.
- phase is fluid_responsive: Sitting up, flushed, says she feels a bit better. GCS 15.
- otherwise: Sitting up, talking, flushed all over, dry lips, vomit bag in her lap. GCS 15.

**How findings change after treatment.** Capillary refill, pulse, level of consciousness,
lactate and the gases follow the phase. Kidney, liver, platelet and muscle values do not
change within the case. The pelvic examination and the CT change once the tampon is out.

### 3.7 Interview ground truth

Her answers when alert, word for word. Each topic also has a shorter drowsy answer with
the same fact.

- `onset`: 'Two days ago. Thursday night I started shivering and aching, and by the early hours I was throwing up. The diarrhea started Friday morning.'
- `timing_progression`: 'Worse. Yesterday I could get up and about for a bit. Today I can't stand without everything going gray.'
- `character_of_symptoms`: 'Like the worst flu I've ever had. Everything aches, I'm hot and cold, and my stomach keeps turning over.'
- `location_of_pain`: 'All over, really. My thighs and calves are the worst. My stomach is crampy but it's not one spot.'
- `radiation_of_pain` (pertinent negative): 'No, it doesn't go anywhere. It's just a general ache.'
- `severity`: 'The aching is maybe a six. It's more that I feel so weak. I've never felt this ill.'
- `aggravating_relieving`: 'Standing up makes everything worse. I get dizzy and my heart pounds. I took some ibuprofen yesterday and it brought the fever down for a couple of hours. Nothing has stayed down today.'
- `rash`: 'Oh, the red? I went to the beach for an hour yesterday because I thought the air would help. I figured I'd burned. It doesn't sting like sunburn, though, and it's on my stomach, where I had a shirt on.'
- `fever_and_chills`: 'Yes. I've been shivering and then burning up since Thursday night. I took my temperature yesterday and it was 102.'
- `headache`: 'A bit of one, across my forehead. It's not the main thing.'
- `neck_stiffness` (pertinent negative): 'No. My neck's fine, I can move it.'
- `photophobia` (pertinent negative): 'No, the lights are okay.'
- `nausea_vomiting`: 'Constantly. I've thrown up maybe eight or ten times since Friday. No blood in it. I can't even keep water down now.'
- `diarrhea`: 'Yes, watery. Maybe six times yesterday and a few today. No blood.'
- `abdominal_pain`: 'Crampy, all over, and it comes with the diarrhea. It's not a sharp pain anywhere, and not in my sides or my back.'
- `chest_pain` (pertinent negative): 'No chest pain. My heart's racing, though. I can feel it when I stand up.'
- `breathing`: 'I'm not short of breath exactly. I just feel like I'm breathing fast.'
- `cough_sore_throat`: 'No cough, no cold. My throat's sore, I thought from throwing up so much.'
- `urine_output`: 'Hardly at all. I think I went once yesterday and it was really dark. Nothing today. It doesn't burn.'
- `dizziness_syncope`: 'Yes. This morning in the shower everything went gray and I had to sit down on the floor. I didn't black out. My roommate found me and made me come in.'
- `confusion`: 'No, I know where I am. I'm just exhausted.'
- `cold_extremities`: 'My hands and feet are freezing, which is weird, because the rest of me is burning.'
- `joint_pain`: 'It's not my joints, it's the muscles. My thighs and calves feel like I ran a marathon. Nothing's swollen.'
- `dysuria_gu_symptoms`: 'No burning, no pain down there. There's been a bit of a smell the last day or two. I thought it was just the end of my period.'
- `menstrual_and_tampon`: 'It started five days ago, so it's pretty much done. I use tampons, the super ones.' She stops. 'I put one in on Wednesday before I went out. I honestly can't remember taking it out. I've been so sick I haven't thought about it.'
- `pregnancy` (pertinent negative): 'I don't think so. I'm on the pill and I've just had my period.'
- `sexual_history`: 'I have a boyfriend, we've been together about a year. Nobody else. He's fine.'
- `past_medical_history` (pertinent negative): 'Nothing. I'm never sick. I've never been in the hospital.'
- `past_surgical_history`: 'I had my wisdom teeth out at eighteen. That's it, nothing else removed.'
- `current_medications`: 'Just the pill. I took ibuprofen yesterday, two tablets a couple of times. Nothing else, no supplements.'
- `allergies` (pertinent negative): 'None that I know of. I've had penicillin before and it was fine.'
- `social_history`: 'I don't smoke or vape. I drink at weekends, a few drinks. No drugs, and I've never injected anything. I'm a grad student and I share an apartment with my roommate.'
- `family_history`: 'My dad has high blood pressure. Nothing else I know of, and nothing like this.'
- `last_oral_intake`: 'I had a few sips of water this morning and brought them back up. I haven't eaten since Thursday.'
- `vaccinations`: 'I think so. I had everything for college, including the meningitis ones. I had a flu shot last fall.'
- `sick_contacts`: 'No. My roommate had the same takeout I did on Thursday and she's completely fine. My boyfriend's fine too. Nobody I know is sick.'
- `suspect_meal`: 'Thai takeout on Thursday, about seven. I started feeling ill a few hours later. My roommate ate the same dishes and she's fine, which is the part I don't get.'
- `travel_history` (pertinent negative): 'No, I haven't been anywhere. Just the beach yesterday, twenty minutes away.'
- `tick_and_outdoor_exposure` (pertinent negative): 'No bites that I've seen. No hiking or camping, no pets. I sat on the beach for an hour yesterday, that's all.'
- `recent_antibiotics_healthcare` (pertinent negative): 'No. No antibiotics, no doctors, no dentist. I haven't seen anyone about this.'
- `wounds_and_skin` (pertinent negative): 'No. No cuts, no boils, nothing like that. No new piercings or tattoos.'
- `functional_baseline`: 'I'm healthy. I run three times a week. I was completely fine on Wednesday.'
- `code_status_goals`: 'What? Do whatever you need to. My mom's number is in my phone.' She looks at you. 'Is it that bad?'

**Pertinent negatives, authored as denials (11).** radiation of pain, neck stiffness, photophobia, chest pain, pregnancy, past medical history, allergies, travel history, tick and outdoor exposure, recent antibiotics healthcare, wounds and skin.

Denials inside other answers, not their own topics: no blood in the vomit or the stool, no
flank or back pain, no burning on passing urine, no cough, no joint swelling, no loss of
consciousness, no tick bite, no new drug apart from ibuprofen, no injected drugs.

**Must ask, never volunteered.** allergies, pregnancy, sexual history, menstrual and tampon, dysuria gu symptoms, social history, code status goals.

**Key topics for the History score.** menstrual and tampon, rash, sick contacts, urine output, dizziness syncope, fever and chills, pregnancy, allergies, current medications.

### 3.8 Disposition and diagnosis

- Correct disposition: Intensive care unit.
- Step-down or intermediate care with telemetry: incorrect. A step-down unit can watch her and cannot run this resuscitation.
- General medical ward with telemetry: incorrect. Telemetry watches a rhythm.
- Emergency department observation unit: incorrect. Observation is for patients expected to go home within a day.
- Discharge home: incorrect. She is in shock.
- Transfer to another hospital: incorrect. Everything she needs is in this hospital.
- Discharge chosen in the first two phases does not end the case. She faints five seconds
  later (section 0).
- Correct diagnosis: Toxic shock syndrome.
- Additional diagnoses credited (9): Septic shock, Acute kidney injury, Lactic acidosis, Rhabdomyolysis, Retained vaginal foreign body, Thrombocytopenia, Anion gap metabolic acidosis, Hyponatremia, Hypokalemia.
- Alternatives with a verdict and an explanation (15): Septic shock (acceptable with qualification), Sepsis (incorrect), Viral gastroenteritis (incorrect), Infectious gastroenteritis (incorrect), Hypovolemia (incorrect), Meningococcemia (incorrect), Urosepsis (incorrect), Pyelonephritis (incorrect), Scarlet fever (incorrect), Heat stroke (incorrect), Heat exhaustion (incorrect), Pelvic inflammatory disease (incorrect), Stevens-Johnson syndrome (incorrect), Kawasaki disease (incorrect), Rocky Mountain spotted fever (incorrect).
- Alternatives with no verdict yet: question 23.

## What a person decided

- 11 October 2026, Aakash Setty: the skin biopsy of the rash is removed from the simulator,
  so the authored "biopsy taken, no result" line and its test are gone.
- 11 October 2026, Aakash Setty: the presentation is fainting, fever and a rash, not
  vomiting and diarrhea. She now has no gut symptoms and believes it is the flu; the beach
  still explains the rash to her. She fainted (out for a few seconds, no head strike).
  Rewritten by a model the same evening: the title, complaint, chief complaint, handovers,
  background, appearance, interview answers (onset, character, pain, aggravating, nausea,
  diarrhea, abdominal pain, throat, syncope, oral intake, contacts, suspected cause), and the
  debrief and diagnosis notes that relied on the gut story. The handover no longer carries
  "something she ate", so that recorded exception to section 11.5 is closed.
- Same day, Aakash Setty: make the source slightly easier to find. Two changes, both model
  wording: asked about the faint, she says she wondered whether it was her period on top of
  the flu; and the nurse's first source prompt now asks whether anyone has asked about her
  period as well as examined her. Deadlines, phases, vitals and scoring are unchanged.
  Not physician reviewed.

- 11 October 2026, Aakash Setty: every consultant answer over 40 words is shortened to 40 or fewer (authoring 9.5), keeping what the consultant thinks, what to do now and the disposition or callback. Wording by a model. Rule order, conditions, tags and debrief notes are unchanged. Not physician reviewed. Four of sixteen answers changed (critical care after fluid and a vasopressor, nephrology with the chemistry back, both infectious disease answers). Dropped: the intensivist's summary of her, "send the swab and blood cultures" and the immunoglobulin sentence, which the immunoglobulin action's own note covers.
- 23 October 2026, Aakash Setty: the handover is scored on one or two major diagnoses and nothing minor. Here the primary and retained vaginal foreign body. Moved to `minor_diagnoses`, credited if named and never penalized if left out: septic shock, acute kidney injury, lactic acidosis, rhabdomyolysis, thrombocytopenia, anion gap metabolic acidosis, hyponatremia and hypokalemia. Which diagnosis stayed scored was a model's pick, accepted by the author. Explanations unchanged. Not physician reviewed.
