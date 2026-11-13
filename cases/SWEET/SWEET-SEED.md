# SWEET seed and provenance

Refractory anaphylaxis to peanut in a 12-year-old boy, 40 kg, after one IM dose of
epinephrine from the ambulance crew. Case 11, the first child in the library. Drafted by a
language model (Claude) on 11 November 2026. **Not reviewed by a physician. Not for learners.**

Case map: "EMSim case map, SWEET" (Claude artifact, https://claude.ai/artifact/8Fp9iV1gSwRB4xfSCgcXhQ), revision 3 as built.

## 0. What a person decided

Aakash Setty, 11 November 2026, in conversation, from his own pasted case structure and three
rounds of questions.

| Decision | Where it is used |
|---|---|
| Case structure: 12 M, 40 kg, peanut dessert, refractory anaphylaxis, states S1 to S6, critical actions and scored errors | Whole pack. S1 to S6 are phases 1 to 6 |
| The ambulance crew gives the first IM dose (0.3 mg), not the mother's autoinjector | case_1 handover, case_4 epi_given |
| In the department the spine is one IM dose, then the infusion | case_1 transitions, case_2 tags |
| The ED IM dose acts at 10 seconds, then its effect fades, then he is still struggling (phase 2) | case_2 IM_EFFECTS, case_1 presentation |
| The learner has time to order the infusion after the dose wears off | case_1 persistent (150 and 240 seconds) |
| A second IM dose works for less time, then phase 3 | case_2 IM_EFFECTS epi2, case_1 persistent |
| A second IM dose never brings phase 3 sooner than no dose ("never sooner than no dose") | case_1 persistent guards on epi_bridge_acting |
| The engine change first: a child figure and normal ranges by age | engine (CHANGELOG, 11 November 2026) |
| No doses in the engine. Doses are taught in the debrief only | case_2 debrief notes |
| Every other default in the map accepted ("Accept all defaults"): infusion preparation 60 seconds with help and 120 without, consult_critical_care read as the PICU and senior call, a case-only "Lay him back, legs raised" button with the standing trap cut, midazolam unscored but still worsening him, the IV epinephrine bolus read as push-dose, two intubated phases, a rescue from phase 4 gated on epinephrine plus a bolus, the prefix SWEET | case_1, case_2, build_case |

Everything else is model output. The fade (full to 80 seconds, two thirds to 100, one third to
120, and for a later dose full to 40, then 50, then 60) is the model's reading of "the effect
fades away".

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
| Read his vitals against a 12-year-old's norms. A child who stops talking is getting worse | The monitor bolds by age band, the narration into phases 2 and 3, alertness 2 in phase 4 |
| Anaphylactic shock is a volume problem: two lines, a weight-based bolus repeated, lying flat with legs raised | Second line a prerequisite of the infusion, 500 mL critical, a second bolus to settle, the posture button and its prompt |
| Two IM doses without lasting response: call for help and start the infusion, bridging with IM | Infusion critical from phase 2, preparation 60 seconds with help and 120 without, IM recommended while it is mixed |
| Adjuncts in their place, no sedation for distress, the airway after the circulation | Adjuncts discouraged before epinephrine, a sedative one phase worse at once, a tube before the infusion collapses him |

## 3. The stories

1. **The intended path.** Monitor, two lines, IM on arrival, legs up, a bolus. At 10 seconds he
   looks better, then it fades. At 120 seconds after the dose he is still struggling. PICU
   called, infusion ordered, running 60 seconds later. A second bolus and he settles 180
   seconds after that. About 7 to 8 minutes.
2. **Waits on the crew's dose.** No ED epinephrine: phase 2 at 180 seconds, 3 at 330, 4 at 480,
   the terminal phase at 660.
3. **IM only, no infusion.** Phase 2 when the dose wears off, phase 3 150 seconds later, then
   the phase 3 clock.
4. **Repeats IM instead of the infusion.** A smaller lift, half as long. Phase 3 comes when it
   wears off, never sooner than with no second dose.
5. **Orders the infusion without calling for help.** It runs 120 seconds after the order in
   phases 1 and 2 (90 in phases 3 and 7). The difference is the lesson.
6. **Tubes him before the infusion.** Collapse after induction. A bridge (IM or IV push) and the
   infusion bring him to the ventilated phase. No bridge in 150 seconds ends the case.
7. **Sedates the frightened child.** Lorazepam or morphine (scored) or midazolam (not scored):
   one phase worse at once in phases 1 to 3.
8. **Stops the infusion.** Back to phase 3 120 seconds later. Restarting it brings him back 30
   seconds after.
9. **Rescue from phase 4.** Epinephrine and a bolus there bring him back to phase 3 once.

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

Eight live phases (presentation, persistent, worsening, peri_arrest, responding, stabilized,
post_induction_collapse, ventilated) and two terminal (bradycardic_arrest, case_complete).
`SWEET-deterioration-timeline.md` lists every timed rule.

| From | To | When | Measured from |
|---|---|---|---|
| presentation | responding | infusion ordered with help 60 s, without 120 s | guard true |
| presentation | persistent | ED IM dose given, 120 s | guard true |
| presentation | persistent | no ED IM dose, 180 s | phase entry |
| presentation | persistent | a sedative | at once |
| persistent | responding | as presentation | guard true |
| persistent | worsening | no infusion order and no IM acting, 150 s | phase entry |
| persistent | worsening | no IM acting, 240 s | phase entry |
| worsening | responding | ordered with help 60 s, without 90 s (not after a relapse) | guard true |
| worsening | responding | after a relapse, restarted, 30 s | guard true |
| worsening | peri_arrest | no order 150 s, no bolus 240 s, always 360 s | phase entry |
| peri_arrest | worsening | epinephrine and a bolus, once, 30 s | guard true |
| peri_arrest | bradycardic_arrest | 180 s | phase entry |
| responding | worsening | infusion stopped, 120 s | guard true |
| responding | stabilized | a second bolus, 180 s | guard true |
| any of 1 to 4 | post_induction_collapse | a tube without the infusion running | at once |
| responding, stabilized | ventilated | a tube with it running | at once |
| post_induction_collapse | ventilated | ordered, 60 s with help, 90 s without | guard true |
| post_induction_collapse | bradycardic_arrest | no bridge 150 s, always 360 s | phase entry |
| ventilated | post_induction_collapse | infusion stopped, 120 s | guard true |

Normal mode multiplies prompt deadlines by 3. The phase 1 epinephrine prompt (30 s, 90 in normal
mode) and the phase 2 infusion prompt (30 s, 90) land before the exits they warn of. The engine
tests check both.

## 5. Built differently from the owner's structure, and why

- S1 to S6 kept as phases 1 to 6 with temperature 37.1 added. Phases 7, 8 and the terminal phase
  added for the tube and the end.
- The owner's states moved on "time since epinephrine". The engine has no dose clock, so the
  first dose is a 120-second delayed consequence and the bridge a 60-second expiring flag.
- The standing trap was cut (accepted default): the figure cannot stand.
- Push-dose IV epinephrine is one catalog entry, read as a small bolus for a peri-arrest child.
- No doses are graded. The debrief teaches 0.01 mg/kg, 0.4 mg for 40 kg, and the US 0.3 mg cap
  for children, and says the two disagree for him.

## 6. Known gaps

1. An infusion ordered in one phase and still mixing at a phase change restarts its
   preparation clock in the new phase (60 or 90 s in phase 3 and 7). Found in the tests.
2. A second stop after a restart is not modeled. The relapse bookkeeping flag is once only.
3. In phase 3 the 240-second no-bolus exit only bites after a relapse: with no infusion the
   150-second exit fires first, and an ordered infusion runs within 90 seconds. Found in the
   tests. The bolus is still critical there and still prompted.
4. The drug overlay draws the infusion pump at once, before the infusion runs.
5. Midazolam cannot be scored (ungraded intubation care) but still worsens him.
6. The figure cannot show hives, lip swelling or lying flat. The exam and the nurse say them.
7. The twelve-lead tracings are adult tracings reused from other packs (media/README.md). The
   fastest is 150, shown for phases at 160 to 172. The chest film is a text report: no pediatric
   film exists in the owner's folder.
8. The monitor ramps. After the dose fades the numbers drift down over a few seconds rather
   than jump, so the phase 2 numbers appear a little after the narration.
9. The interview, lexical matcher only: in-scope 22 of 31, out-of-scope refused 21 of 30 (review
   packet).

## 7. Open questions for the physician

1. Is 0.3 mg from the crew right for 40 kg, given 0.01 mg/kg would be 0.4 mg? The debrief says
   both.
2. Are the response sizes right (first dose plus 6 heart rate, plus 12 systolic, minus 4
   respiratory rate, plus 2 saturation; a later dose about two thirds of that)?
3. Is 120 seconds of response, then a fade, the right teaching length? Real IM epinephrine
   peaks over minutes.
4. Should phase 3's bolus deadline apply on the first visit too (gap 3)?
5. Should midazolam be scored here despite the ungraded list?
6. Is an adult tracing acceptable for a 12-year-old, or should the twelve-lead be a report
   until a pediatric tracing exists?
7. The PICU fellow's lines (case_3 CONSULTANTS): right content and tone?
8. The model-added interview facts in 3.7.

## 8. Engine and catalog changes made for the case

- By the owner's instruction: a child figure and normal ranges by age (CHANGELOG, 11 November
  2026).
- `engine/engine-tests.js`: the prompt-before-deterioration check now counts a flag granted for
  a while or on a condition as the action's flag, as the validator already did.
- `engine/gen_docs.py`: a field that borrows an ancestor's note prints it once and points to it
  after, which brought the kit back under its budget with the new case index line.
- Catalog requests raised, not made: call for senior help, supine with legs raised, titrate the
  infusion, nebulized epinephrine, a pediatric chest film, tryptase.

## 9. Awaiting sign-off

Sign-off: not started.
