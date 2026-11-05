# TIDE seed and provenance

Severe community-acquired pneumonia with septic shock in a 58-year-old man, who tires on
high-flow oxygen once his pressure is held and needs a tube. Drafted by a language model on
4 November 2026 at the request of Aakash Setty, from a case structure he supplied and his
answers to two rounds of questions. **No physician has reviewed this pack.** Read every
number as a proposal.

The prefix TIDE is a model choice. It names nothing clinical: the fluid response in this
case comes in and goes out like a tide. Case number 9.

## 0. What a person decided

Aakash Setty, 4 November 2026, in conversation:

| Decision | What was decided |
|---|---|
| The case | Build it from the pasted structure (severe CAP, sepsis-induced hypoperfusion, failure of noninvasive support, the physiologically difficult airway). "The pasted content is important but does not need to be perfectly followed" |
| Intubation care | Stays ungraded, by the rule of 23 October 2026, "for now". Its physiology still plays |
| High-flow nasal cannula | "Build it in." Added to the catalog the same day (CHANGELOG, 4 November 2026) |
| Ventilator settings | No ventilator panel in this version. Lung-protective ventilation is taught in the debrief only |
| Structure | One phase web, as drawn in the case map (revision 1) |
| Time | Remove the two-hour time jump |
| Length | 10 to 12 minutes |
| Clinical corrections | Agreed: hydrocortisone recommended once on a vasopressor, the corrected citations (CAPE COD, ED-AWARENESS), the awareness question as a nurse line with no vital change, the no-oxygen arrest path cut, gases made Henderson-Hasselbalch consistent |
| Honest time (B1) | "Follow your suggestion": the narration into the failing phase says the clock is moving faster, and the debrief gives the real timescale |
| B2 to B6 | Agreed as drafted: the antibiotic is scored and prompted but changes nothing visible, a late pressor costs a higher lactate, any intubation without a running drip collapses him, the same failure clock on every device, a learner who never starts a pressor never meets the intubation decision |
| Open questions | "Build the entire case now... ask any other questions as needed." The model took its drafted default for each smaller question (case map, section 8) and lists them in section 7 below for confirmation |

Everything else is model output. The case map the decisions refer to is the private
artifact "EMSim draft case map" (revision 2) and `Claude outputs/casemaps-draft/`.

## 1. Sources, and how far each was read

| Source | How read | Used for |
|---|---|---|
| The owner's pasted case structure, 4 November 2026 | In full, by the model | Patient, findings, states, critical actions, debrief anchors |
| Surviving Sepsis Campaign 2026 (Prescott, Antonelli et al., Crit Care Med 2026) | SCCM guideline page and summaries through web search. The guideline was not opened | Antibiotics within an hour in shock, at least 30 mL/kg crystalloid suggested (low certainty), adjusted or ideal weight in obesity, lactate suggested, cultures before antibiotics, corticosteroids suggested in septic shock |
| ATS CAP guideline update (Jones BE, Ramirez JA et al., AJRCCM 2025) | Summaries through web search. Not opened | Corticosteroids suggested in severe CAP (conditional, low quality), not in influenza. IDSA did not endorse |
| IDSA/ATS CAP guideline 2019 (Metlay et al.) | From memory | Severe CAP regimens, minor criteria, MRSA and Pseudomonas risk factors |
| Dequin PF et al., CAPE COD, NEJM 2023 | PubMed abstract and The Bottom Line summary | Hydrocortisone in severe CAP. Septic shock excluded, by the summary |
| Pappal RD et al., ED-AWARENESS, Ann Emerg Med 2021, and Fuller BM et al., Crit Care Med 2022 | Summaries (REBEL EM, JournalFeed) | Awareness with paralysis 2.6% and 3.4%, associated with rocuronium |
| Maia IS et al., RENOVATE, JAMA 2025 | Summaries | HFNC noninferior to NIV in nonimmunocompromised hypoxemia |
| ACEP clinical policy, endotracheal intubation | ACEP page through search | NIV over conventional oxygen for preoxygenation (Level B), HFNC when NIV is not feasible (Level C), consider video laryngoscopy, avoid fentanyl, midazolam or propofol induction in patients at risk of post-intubation hypotension |
| Gibbs KW et al., PREOXI, NEJM 2024 | Citation seen in reference lists. Percentages from the owner's structure, not checked | NIV preoxygenation |
| Roca O et al., ROX index, AJRCCM 2019 | From memory and the owner's structure | ROX thresholds and timepoints |
| Published simulation cases on severe pneumonia | Not searched | Gap. Goals rest on guidelines and the owner's structure |

## 2. How this case differs from the library

| Dimension | This case | Closest |
|---|---|---|
| Tempo | Minutes. Shock on a clock, then respiratory failure on an openly compressed clock | MGCA, CHFE |
| What is uncertain | When fluid has stopped working, and when noninvasive support has failed | MGCA, CHFE |
| Kind of right answer | Do more at the right moment, and support the circulation before taking away the patient's own drive | CHFE, AFRVR |
| Where the danger hides | Behind a reassuring saturation on high flow, then created by induction | CHFE, TAKO |
| Patient and room | 58 M, walked in with his wife, triage to the resuscitation bay. His wife answers most questions | CHFE 65 M by EMS |
| How it feels | Urgent, then a slow dread as the numbers stay "fine" | MGCA, CHFE |

It overlaps MGCA and CHFE more than most. What it alone teaches is the reassuring
saturation on high flow and the drip before induction. The first play-through should check
that phase 7 plays as its own decision.

## 2.1 Learning goals and where each is acted on

| Goal | Source | Where the learner acts | Status |
|---|---|---|---|
| 1. Recognize severe CAP with sepsis and hypoperfusion | IDSA/ATS 2019 minor criteria (memory), SSC 2026 | Antibiotic, cultures, lactate and fluid in phase 1. ICU and both diagnoses at handoff | Taught |
| 2. Escalate oxygen stepwise, and a better saturation is not resolution | Owner's structure, RENOVATE, Roca 2019 | Device choice in phase 1. The decision to intubate in phase 7 at a saturation of 88 | Taught |
| 3. Early antibiotic, fluid, and a vasopressor when the fluid fails | SSC 2026 | Phases 1 to 6. The antibiotic is scored and changes nothing visible (B2) | Taught, antibiotic by score |
| 4. Recognize failing noninvasive support and intubate before the crash | Owner's structure, observational data cited there | Phase 7, graded, clock to phase 8 | Taught |
| 5. Prepare the physiology before induction | ACEP policy, owner's structure | A drip running before the tube, graded through the pressor. Preoxygenation shown, not graded (owner rule) | Partly |
| 6. Lung-protective ventilation and prompt analgosedation | Owner's structure, SSC 2021 | Debrief. Sedation is an ungraded follow-up | Not taught by play (no ventilator panel) |

The idea that travels: a better number on the monitor is not a better patient. Judge
support by the work of breathing and the trend, and judge fluid by whether the pressure stays.

## 3. The stories

**Treated well.** Monitor, line, high flow at sixty percent. Cultures, lactate, a gas,
ceftriaxone and azithromycin. A liter of crystalloid lifts his pressure for a few minutes and
it drifts back below a mean of 65. Peripheral norepinephrine holds it. The ICU is called and
hydrocortisone is given. His saturation on high flow is 92, but he keeps working. He tires:
confused, paradoxical breathing, 88 percent on a hundred percent. The team preoxygenates on
BiPAP with the drip running and intubates. His saturation holds near ninety, his pressure dips
and recovers. Sedation goes in, a film shows the tube, he goes to the ICU.

**Never decides to intubate.** As above, until the learner reads 88 on high flow as acceptable.
His breathing slows, his heart rate falls, he arrests.

**Fluid without a pressor.** Each bolus helps less. His knees mottle, then his thighs, and his
mental state slips. Without a vasopressor he arrests. Fluid beyond two boluses puts more water
in his lungs.

**A late pressor.** Started once he is mottled to the thighs, it holds his pressure. His
lactate is higher from then on, and the debrief names the delay.

**Intubated with nothing running.** Induction and positive pressure take away the tone he was
living on. His pressure falls fast. A drip started then rescues him, and without one he
arrests.

**Left alone.** His pressure falls on its own after three minutes, falls further, and he
arrests at eight. The case can kill him without the learner touching him: a decision the owner
made by accepting the clocks.

## 3.4 The action spine, with every route

Critical (phase): oxygen, any device (1). HFNC or NIV (1 to 6). Crystalloid bolus (1, 3).
A beta-lactam with pneumococcal activity (1 to 7, 10). Atypical cover (1 to 7, 10). A
vasopressor drip (4, 5, 9). The decision to intubate (7, 8). The monitor (1).

Recommended: IV, the ABC exam, lactate, blood cultures, a gas, CBC, chemistry, influenza test,
chest film, lung and cardiac ultrasound, reassessment after fluid, a second bolus in phase 2,
hydrocortisone (6 to 10), consult critical care, push-dose vasopressor (9), ABG (7, 10).

Discouraged, every route bound: a third crystalloid bolus or more, furosemide (loop diuretic
group), beta-blockers and diltiazem, nitroglycerin (three entries), dopamine, CT of the chest
(either entry), sodium bicarbonate (both entries), stopping a vasopressor (each stop entry).

Ungraded (owner rule): preoxygenation, BVM, positioning, induction agents, paralytics, the
sedation after the tube.

Harmful: none. Nothing halts the case.

Accepted alternatives: any crystalloid bolus; vasopressin, epinephrine or phenylephrine drip
for the vasopressor (norepinephrine is first line, the others are credited); a broadened
beta-lactam (piperacillin-tazobactam, cefepime, meropenem) meets the beta-lactam
expectation; levofloxacin or moxifloxacin meets atypical cover; methylprednisolone meets
the steroid; an arterial or venous gas.

## 3.5 Sequencing

Catalog prerequisites only: a line before every intravenous drug and fluid, induction and a
paralytic before the tube. No case prerequisite and no waiver. One follow-up: sedation after
a rocuronium tube, ungraded, discharged by a sedative or analgesic given after intubation.

## 3.6 Key findings

Exam: tripoding, accessory muscles, three or four words a breath, coarse crackles at both
bases worse on the right, bronchial breathing and egophony at the right base, warm and flushed
on arrival, then mottled knees, then thighs. Confusion and paradoxical breathing in phase 7.

Results (units and intervals from the catalog defaults; every value model output):

| Study | Value | Flag |
|---|---|---|
| VBG on arrival | pH 7.33, pCO2 33, HCO3 17, lactate 3.8 | pCO2, HCO3, lactate abnormal. pH inside the venous interval |
| VBG after severe shock | pH 7.27, pCO2 30, HCO3 13.5, lactate 5.4 | abnormal |
| VBG failing support | pH 7.18, pCO2 56, HCO3 20 (severe-shock branch 7.11, 56, 17) | abnormal |
| ABG | by phase and device, PaO2 and SaO2 matching the monitor. Ventilated on FiO2 0.7: PaO2 78 at SpO2 95, P/F about 111 | abnormal |
| Chemistry | Na 133, K 4.1, Cl 99, HCO3 18, BUN 34, Cr 1.7, glucose 244 | Na, HCO3, BUN, Cr, glucose |
| CBC | WBC 18.6, bands 14%, Hb 13.8, Plt 168 | WBC, bands |
| Procalcitonin | 18.4 ng/mL | abnormal |
| Urine pneumococcal antigen | positive | abnormal |
| Influenza, COVID-19 | negative | normal |
| Chest film | bilateral patchy airspace opacities, right mid and lower zones and left lower zone | abnormal. The picture is `Pneumonia/Multifocal_Male.png` from the owner's folder |

Unchanged in the case's minutes: the film, the CBC, the chemistry, the procalcitonin and the
lactate (no clearance in ten minutes). The lactate rises only on the severe-shock branch.
The ECG is a generated tracing per phase, reused from TSS and SCOOT (gap 6.4, media/README.md).
The ventilated heart rate is 112 and the tiring heart rate 56, set to match the tracings.

## 3.7 Interview ground truth

His wife answers. He manages a few words in phases 1 to 6, and none from phase 7.

Positive: fever and shaking chills since Saturday (four days), cough with rusty brown phlegm,
sharp right-sided chest pain on breathing in, breathless since last night and worse today,
lightheaded on standing this morning, little urine today, poor intake. Home thermometer 102
last night. Hypertension and type 2 diabetes, lisinopril and metformin taken this morning.
Smokes about three quarters of a pack a day since eighteen. A couple of beers at weekends.
Lives with his wife, works for the city water department (model-added). Missed his flu shot
this year, unsure about the pneumonia vaccine (model-added). Full code. Father had a heart
attack at seventy (model-added). A knee scope years ago (model-added).

Pertinent negatives (deny in every phase): allergies, no hospital stay or antibiotics in the
last three months, no home oxygen, no leg swelling or calf pain, no travel or hotel stay, no
sick contacts, no abdominal pain, no diarrhea, no steroids or immune problems. All
model-added except the allergies and the antibiotic and hospital history, which the owner's
structure states.

## 3.8 Disposition and diagnoses

ICU. Primary community-acquired pneumonia. Additional septic shock. Minor: acute hypoxemic
respiratory failure, AKI, lactic acidosis, ARDS. Defensible: sepsis, ARDS, acute hypoxemic
respiratory failure. Incorrect: aspiration pneumonia, influenza, hospital-acquired pneumonia,
empyema, decompensated heart failure (both entries), pulmonary embolism, COPD exacerbation.

## 4. Phases and clocks

| Phase | Short label | What now | Leaves by |
|---|---|---|---|
| presentation | on arrival | Oxygen up to high flow, line, cultures, antibiotic, first fluid | fluid → fluid_response. 180 s without fluid → low_pressure (with a drip already running → on_pressor) |
| fluid_response | after fluid | Reassess, expect it not to last, line up a pressor | 150 s → low_after_fluid always, or on_pressor if a drip is running |
| low_pressure | pressure low | Fluid now | fluid → fluid_response, drip → on_pressor, 150 s → worsening_shock |
| low_after_fluid | pressure low again | Start the vasopressor | drip → on_pressor, 150 s → worsening_shock |
| worsening_shock | pressure very low | Vasopressor now | drip → on_pressor, 150 s → arrest |
| on_pressor | pressure holding | Antibiotic if missing, steroid, ICU | 180 s → failing_support always (compressed) |
| failing_support | working harder | Decide to intubate | 150 s → tiring |
| tiring | breathing slowing | Intubate now | 120 s → arrest |
| post_induction_collapse | after the tube | Vasopressor drip | drip → ventilated, 120 s → arrest |
| ventilated | on the ventilator | Sedation, film, gas, ICU, handoff | handoff |

Intubation from any live phase: a drip running → ventilated, otherwise →
post_induction_collapse. Every timed rule into worsening_shock grants `severe_shock`, which
keys the lactate and the gases from then on.

Two timed rules pending at once: presentation, fluid_response and on_pressor each carry
guarded rules above a fallback at the same second (outcome chosen at a scheduled time). No
phase has two independent clocks, so there is no race table.

Do-nothing: presentation 180 s → low_pressure 150 s → worsening_shock 150 s → arrest at 480 s.
Treated well reaches handoff at about 520 s of scenario clock.

Prompt cap per phase: 4, for presentation, which has four prompts (oxygen 20 s, more support
35 s, fluid 40 s, antibiotic 50 s). Each deterioration's prompt is the earliest in its phase.
Normal mode (deadlines × 3): every warning still lands at least 30 s before its deterioration.

## 5. Vital effects (teaching choices, not measurements)

| Action | Vital | Delta | Guard | Key |
|---|---|---|---|---|
| Nasal cannula, nonrebreather, HFNC, NIV | SpO2 | +3, +6, +7, +8 | not intubated, not in tiring | resp_spo2 |
| same | RR | 0, −2, −2, −4 | same | resp_rr |
| Third crystalloid bolus onward | SpO2, RR | −3, +4 | fluid_stacked set, not intubated | fluid_spo2, fluid_rr |
| Intubation | SpO2 | −3, −10 or −18 for 30 s by preoxygenation | by flag | tube_spo2 |
| Intubation with a drip running | SBP, DBP | −14, −8 for 60 s | pressor_running | tube_sbp, tube_dbp |
| Propofol infusion | SBP, DBP | −8, −4 | not stopped | propofol_sbp, propofol_dbp |
| Stopping a vasopressor | SBP, DBP | −24, −14 | not restarted | stop_sbp, stop_dbp |
| Vasopressor drips | none | `vital_effects: []` | the phases carry the rise | |
| Push-dose boluses | catalog default | | | |

## 6. Known gaps

1. **The antibiotic changes nothing visible (B2).** Owner decision. MGCA does the opposite
   and the library is inconsistent.
2. **Time is compressed in phase 7.** Said in the narration and the debrief (B1).
3. **Permanent device flags.** A learner who used NIV and then switched to HFNC is treated as
   on NIV for the gas and for preoxygenation. The monitor follows the last device.
4. **Borrowed ECG pictures.** The generator could not be built in the workspace, so each
   phase shows the TSS or SCOOT tracing nearest its rate, with that tracing's read
   (media/README.md). A learner who has played TSS may recognize them. Draw tracings for this
   case when the generator can be run.
5. **Stopping a vasopressor** moves the monitor and changes no phase. A second stop after a
   restart is not modeled.
6. **Restarting a vasopressor after a stop** in post_induction_collapse is not distinguished.
7. **Ventilator settings, laryngoscope choice and capnography** are not in the product.
8. **An infusion is not a bolus.** NS and LR infusions do not move the phase.
9. **A crystalloid count is not a volume.** A 500 mL bolus counts as one, like a liter.
10. **The second preoxygenation route.** BVM given in phase 7 or 8 counts as positive pressure,
    as if it had a PEEP valve.

## 7. Open questions for the physician

Model defaults taken under the owner's instruction of 4 November 2026. Each awaits a "yes"
or a change.

1. Antibiotics: beta-lactam critical and atypical cover critical. Fluoroquinolone monotherapy
   meets atypical cover only. Broadened cover is neutral with a stewardship note.
   Doxycycline is neutral.
2. Fluid critical on arrival (MAP 75, lactate 3.8), with the debrief explaining why.
3. The third bolus is the harm threshold.
4. Septic shock is the additional diagnosis, ARDS minor.
5. Lactate, cultures and the ICU consult recommended, the ICU disposition scored.
6. NIV in phase 7 is neutral, does not stop the clock, and counts as preoxygenation. No
   aspiration branch.
7. Deterministic consequences of probabilistic risks, said so by the nurse and the debrief.
8. Arrest is terminal, no ROSC.
9. ABG variants by device, highest device assumed.
10. The pressor prompt says "under sixty-five" in phases 4 and 5 only.
11. Prompt cap 4.
12. His wife answers. He manages a few words until phase 7.
13. Catalog requests: titrate a vasopressor, MRSA nares PCR, sputum culture, Legionella
    antigen, respiratory viral PCR, passive leg raise.
14. Public fields: complaint "Fever, cough and breathlessness", category "Respiratory".
15. Published simulation sources not searched.
16. Dexamethasone is neutral, methylprednisolone meets the steroid expectation.
17. Vasopressin, epinephrine and phenylephrine drips meet the vasopressor expectation.
    Dopamine is discouraged and still holds his pressure.
18. Sodium bicarbonate discouraged at pH 7.18 with a respiratory component.

## 8. Engine and catalog changes made for the case

- High-Flow Nasal Cannula added to the catalog, its voice phrases, expectation credit and a
  figure add-on (CHANGELOG, 4 November 2026).
- `engine/gen_docs.py` equivalence-group notes fixed (same entry).

Engine behavior found while building, not changed (for the owner):

- `flags_set_repeat` counts once per entry, not once per action. Two entries on one action
  that share a counter advance it twice per bolus. The crystalloid bolus therefore uses a
  separate named counter for each threshold (`crystalloid_two`, `crystalloid_three`). The
  authoring requirements do not say this. Recorded here as a gap in the documents.

## 9. Awaiting sign-off

Everything in `provenance.author_only_fields_pending_signoff` in the case file.

## What a person decided

See section 0. Aakash Setty, 4 November 2026.
