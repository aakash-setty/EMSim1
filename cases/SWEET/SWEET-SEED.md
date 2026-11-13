# SWEET seed and provenance

Refractory anaphylaxis to peanut in a 12-year-old boy, 40 kg, after one IM dose of
epinephrine from the ambulance crew. Case 11, the first child in the library. Drafted by a
language model (Claude) on 11 November 2026, revised 13 November 2026. **Not reviewed by a
physician. Not for learners.**

Case map: "EMSim case map, SWEET" (Claude artifact, https://claude.ai/artifact/8Fp9iV1gSwRB4xfSCgcXhQ), revision 4 as built.

## 0. What a person decided

Aakash Setty, in conversation, from his own pasted case structure and his answers.

| Decision | Date | Where it is used |
|---|---|---|
| Case structure: 12 M, 40 kg, peanut dessert, refractory anaphylaxis, states S1 to S6, critical actions and scored errors | 11 Nov | Whole pack. S1 to S6 are phases 1 to 6 |
| The ambulance crew gives the first IM dose (0.3 mg), not the mother's autoinjector | 11 Nov | case_1 handover, case_4 epi_given |
| In the department the spine is one IM dose, then the infusion | 11 Nov | case_1 transitions, case_2 tags |
| The ED IM dose acts at 10 seconds, then its effect fades, then he is still struggling (phase 2) | 11 Nov | case_2 IM_EFFECTS, case_1 presentation |
| The first ED IM dose lasts only 60 seconds | 13 Nov | case_2 IM_EFFECTS, case_1 presentation (60 s) |
| A second IM dose works for less time, then phase 3 | 11 Nov | case_2 IM_EFFECTS epi2, case_1 persistent |
| A second IM dose never brings phase 3 sooner than no dose | 11 Nov | case_1 persistent guards on epi_bridge_acting |
| Pharmacy makes the infusion in 10 seconds (replaces 60 s with help and 120 s without) | 13 Nov | case_1 drip_runs, every phase |
| Monitor, IV access, lying flat, the second line and the PICU call are not critical actions. New critical actions tied to the goals and the topic, case rewritten as needed | 13 Nov | case_2 tags, section 2a |
| The engine change first: a child figure and normal ranges by age | 11 Nov | engine (CHANGELOG) |
| No doses in the engine. Doses are taught in the debrief only | 11 Nov | case_2 debrief notes |
| Every other default in the map accepted: consult_critical_care read as the PICU and senior call, a case-only "Lay him back, legs raised" button with the standing trap cut, midazolam unscored but still worsening him, the IV epinephrine bolus read as push-dose, two intubated phases, a rescue from phase 4 gated on epinephrine plus a bolus, the prefix SWEET | 11 Nov | case_1, case_2, build_case |

Everything else is model output. Model choices inside the owner's decisions: the fade (full to
40 seconds, two thirds to 50, one third to 60), a later dose lasting 40 seconds (full to 25,
then 32, then 40), the two new critical actions (2a), and the two relapse phases (5).

## 1. Sources, and how far each was read

As in `provenance.reference_status` in the case file. In short: RCUK 2021 anaphylaxis and
refractory algorithms read as PDF text through search. The 2020 US practice parameter read
through two summaries. The 2023 parameter abstract only, used for nothing. Pumphrey 2003 through
BestBETs. Campbell 2015 abstract. PALS 2015 vital sign bands through a summary. None opened in
full by a person. Pediatric laboratory intervals are model output.

## 2. Learning goals and where each is acted on

| Goal | Acted on |
|---|---|
| The crew's dose is one dose. Repeat IM now, before any adjunct | Critical IM dose in phase 1, adjuncts discouraged before it, the nurse prompt at 30 seconds |
| Read his vitals against a 12-year-old's norms. A child who stops talking is getting worse | The monitor bolds by age band, the narration into phases 2 and 3, a critical second look once the dose wears off |
| Anaphylactic shock is a volume problem: a weight-based bolus repeated, lying flat with legs raised | 500 mL critical, a second bolus to settle, the posture button (recommended) and its prompt |
| Two IM doses without lasting response: start the infusion, call for help, bridge with IM | Infusion critical from phase 2, running 10 seconds after the order, PICU recommended, IM recommended in phase 2 |
| Adjuncts in their place, no sedation for distress, the airway after the circulation | Adjuncts discouraged before epinephrine, a sedative one phase worse at once, a tube before the infusion collapses him, a critical airway exam |

### 2a. The critical actions (13 November 2026)

| Critical action | When | Why |
|---|---|---|
| IM epinephrine, anterolateral thigh | On arrival (and phase 2 if none was given), at the edge of arrest, after the tube | Goal 1. The crew's dose is one dose |
| Airway checked for swelling and stridor (exam_airway) | Phases 1 to 4 and relapse | The anaphylaxis exam that decides how soon the airway becomes the problem |
| Crystalloid bolus | Phases 1 to 4, after the tube, and a second once the infusion runs | Goal 3 |
| Examined him again after the IM dose (reassessed_after_epi) | Phase 2, once an ED dose was given. Met by the airway, breathing, circulation or lung exam after the dose. The nurse asks at 20 seconds | Goal 2. The brief response looks like recovery |
| Epinephrine infusion | Phases 2 to 4, after the tube | Goal 4 |
| Rescue targets: bolus while floppy, epinephrine and a bolus at the edge of arrest, epinephrine after the tube, restarting a stopped infusion | Only in the phase each names | The branches |

Now recommended, not critical: the monitor, IV access, the second line, lying flat with legs
raised, the PICU call. The monitor and a second line are still prerequisites of the infusion.

## 3. The stories

1. **The intended path.** IM on arrival, the airway examined, legs up, a bolus. At 10 seconds he
   looks better, it fades from 40, and at 60 seconds after the dose he is still struggling. A
   second look, the infusion (running 10 seconds later), PICU, a second bolus, and he settles
   180 seconds after that. About 4 to 5 minutes.
2. **Waits on the crew's dose.** No ED epinephrine: phase 2 at 180 seconds, 3 at 330, 4 at 480,
   the terminal phase at 660.
3. **IM only, no infusion.** Phase 2 when the dose wears off, phase 3 150 seconds later, then
   the phase 3 clock.
4. **Repeats IM instead of the infusion.** A smaller lift, gone in 40 seconds. Phase 3 comes when
   it wears off, never sooner than with no second dose.
5. **Tubes him before the infusion.** Collapse after induction. A bridge (IM or IV push) and the
   infusion bring him to the ventilated phase. No bridge in 150 seconds ends the case.
6. **Sedates the frightened child.** Lorazepam or morphine (scored) or midazolam (not scored):
   one phase worse at once in phases 1 to 3.
7. **Stops the infusion.** The relapse phase 120 seconds later. A restart brings him back 10
   seconds after. No restart: silent at 150 seconds.
8. **Rescue from phase 4.** Epinephrine and a bolus there bring him back to phase 3 once (to the
   relapse phase if the infusion had been stopped).

### 3.7 Interview ground truth

His mother answers. Positive: a piece of a dessert bar her sister brought, peanut in it; mouth
itch, hives, wheeze within minutes; lips and eyes swelled fast; chest tight "like breathing
through a straw"; dizzy on standing at home; the crew's shot about fifteen minutes before
arrival, better for a few minutes and then worse; peanut allergy known since age three; 40 kg,
weighed last month.

Model-added (the owner's structure did not supply): she could not find his EpiPen and called
911; sixth grade, lives with his mother and little sister; weighed last month; dizzy on
standing; and every denial below.

Pertinent negatives: asthma or inhaler use, medicine allergies, medications, other medical
history, surgeries, heart history, fever, cough, vomiting, abdominal pain, passing out, family
history. Immunizations up to date.

## 4. Phases, transitions and the race table

Ten live phases (presentation, persistent, worsening, peri_arrest, responding, stabilized,
post_induction_collapse, ventilated, relapse, vent_relapse) and two terminal
(bradycardic_arrest, case_complete). `SWEET-deterioration-timeline.md` lists every timed rule.

| From | To | When | Measured from |
|---|---|---|---|
| presentation, persistent, worsening | responding | infusion ordered, 10 s | guard true |
| presentation | persistent | ED IM dose given, 60 s | guard true |
| presentation | persistent | no ED IM dose, 180 s | phase entry |
| presentation, persistent, worsening, relapse | one phase worse | a sedative | at once |
| persistent | worsening | no infusion order and no IM acting, 150 s | phase entry |
| persistent | worsening | no IM acting, 240 s | phase entry |
| worsening | peri_arrest | no order 150 s, no bolus 240 s, always 360 s | phase entry |
| peri_arrest | relapse | after a relapse: epinephrine and a bolus, once, 30 s | guard true |
| peri_arrest | worsening | epinephrine and a bolus, once, 30 s | guard true |
| peri_arrest | bradycardic_arrest | 180 s | phase entry |
| responding, stabilized | relapse | infusion stopped, 120 s | guard true |
| responding | stabilized | a second bolus, 180 s | guard true |
| relapse | responding | infusion restarted, 10 s | guard true |
| relapse | peri_arrest | not restarted 150 s, no bolus 240 s, always 360 s | phase entry |
| relapse | vent_relapse | a tube | at once |
| presentation to peri_arrest | post_induction_collapse | a tube without the infusion running | at once |
| responding, stabilized | ventilated | a tube with it running | at once |
| post_induction_collapse | ventilated | infusion ordered, 10 s | guard true |
| post_induction_collapse | bradycardic_arrest | no bridge 150 s, always 360 s | phase entry |
| ventilated | vent_relapse | infusion stopped, 120 s | guard true |
| vent_relapse | ventilated | infusion restarted, 10 s | guard true |
| vent_relapse | bradycardic_arrest | not restarted 150 s, always 360 s | phase entry |

Normal mode multiplies prompt deadlines by 3. The phase 1 epinephrine prompt (30 s, 90 in normal
mode), the phase 2 infusion prompt (30 s, 90) and the restart prompt (20 s, 60) land before the
exits they warn of. The engine tests check the first two.

## 5. Built differently from the owner's structure, and why

- S1 to S6 kept as phases 1 to 6 with temperature 37.1 added. Phases 7, 8 and the terminal phase
  added for the tube and the end.
- The owner's states moved on "time since epinephrine". The engine has no dose clock, so the
  first dose is a 60-second delayed consequence and the bridge a 40-second expiring flag.
- Two relapse phases (13 November 2026). The infusion has to run 10 seconds after the order in
  phases 3 and 7 as well. A rule that also has to say "and it was not stopped" needs a NOT in its
  guard, and the validator then floors it at 30 seconds. So a stopped infusion moves him to a
  phase of its own (relapse, or vent_relapse when intubated) where only a restart helps, and the
  order stays a plain positive guard everywhere else. They show what phases 3 and 7 show
  (case_3 copies those rules atom for atom).
- The standing trap was cut (accepted default): the figure cannot stand.
- Push-dose IV epinephrine is one catalog entry, read as a small bolus for a peri-arrest child.
- No doses are graded. The debrief teaches 0.01 mg/kg, 0.4 mg for 40 kg, and the US 0.3 mg cap
  for children, and says the two disagree for him.

## 6. Known gaps

1. A restart given before the relapse still lets the relapse play at 120 seconds, and he comes
   back 10 seconds after it. Preventing the relapse would need a negated restart in the stop
   rule, which the validator can only warn for with a prompt that fires on a phase alone.
2. A second stop after a restart is not modeled. The relapse bookkeeping flag is once only.
3. In phase 3 the 240-second no-bolus exit only bites in the relapse phase: with no infusion the
   150-second exit fires first, and an ordered infusion runs in 10 seconds.
4. The drug overlay draws the infusion pump at once. With a 10-second preparation this now
   matters little.
5. Midazolam cannot be scored (ungraded intubation care) but still worsens him.
6. The figure cannot show hives, lip swelling or lying flat. The exam and the nurse say them.
7. The twelve-lead tracings are adult tracings reused from other packs (media/README.md). The
   fastest is 150, shown for phases at 160 to 172. The chest film is a text report.
8. The monitor ramps. After the dose fades the numbers drift down over a few seconds.
9. The interview, lexical matcher only: in-scope 22 of 31, out-of-scope refused 21 of 30 (review
   packet).
10. The second look (reassessed_after_epi) is met by any of four exams after the dose,
    including one done while the dose is still working.

## 7. Open questions for the physician

1. Is 0.3 mg from the crew right for 40 kg, given 0.01 mg/kg would be 0.4 mg? The debrief says
   both.
2. Are the response sizes right (first dose plus 6 heart rate, plus 12 systolic, minus 4
   respiratory rate, plus 2 saturation; a later dose about two thirds of that)?
3. Real IM epinephrine peaks over minutes and an infusion takes minutes to mix. 60 seconds and
   10 seconds are teaching compressions (owner's decision). Should the debrief say so more
   plainly?
4. Are the two new critical actions (airway exam, second look after the dose) the right ones?
   Candidates not chosen: asking what the crew gave (the handover already says it), nebulized
   epinephrine for stridor (not in the catalog), the disposition (scored at handoff).
5. Should midazolam be scored here despite the ungraded list?
6. Is an adult tracing acceptable for a 12-year-old?
7. The PICU fellow's lines (case_3 CONSULTANTS): right content and tone?
8. The model-added interview facts in 3.7.

## 8. Engine and catalog changes made for the case

- By the owner's instruction: a child figure and normal ranges by age (CHANGELOG, 11 November
  2026).
- `engine/engine-tests.js`: the prompt-before-deterioration check counts a flag granted for a
  while or on a condition as the action's flag, as the validator already did.
- `engine/gen_docs.py`: a field that borrows an ancestor's note prints it once and points to it
  after, which brought the kit back under its budget with the new case index line.
- Catalog requests raised, not made: call for senior help, supine with legs raised, titrate the
  infusion, nebulized epinephrine, a pediatric chest film, tryptase.

## 9. Awaiting sign-off

Sign-off: not started.
