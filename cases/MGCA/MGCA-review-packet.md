# Review packet: 21-year-old woman with meningococcaemia, septic shock and adrenal crisis

**Case id:** `mgc-meningococcemia-adrenal-01`
**Prefix:** `MGCA`
**Authored against:** case-authoring-requirements.md v0.5, system-design-v2.md v0.6, action-catalog.json v0.1-draft, diagnosis-catalog.json v0.1-draft
**Revised:** rebuilt against v0.6 time-guarded transitions. Section 4 and open question OQ-1 changed materially.
**Status: UNSIGNED DRAFT. Not usable with learners.**

---

## 1. What you supplied and what the model supplied

You supplied a six-state seed: the diagnosis, the state structure, the vital signs in each state, the laboratory values in each state, the transition triggers, the five critical actions, the constraint that the lumbar puncture happens only if the patient is not hypotensive, and the patient's age and sex. That is a real seed and it covers more of section 3 than the reference case's did.

Everything else is model output and none of it has been reviewed by a physician: every clinical tag, every halt reason, every prerequisite, every exam finding, every consultant response, every interview answer, every reference interval, every abnormal flag, and all debrief text. Section 2 of the authoring requirements marks all of those AUTHOR-ONLY. The case file carries a `provenance` block recording this and listing the fields awaiting your signature.

The practical consequence: on a fully seeded case, review checks that expansion did not corrupt your ground truth. Here you are authoring roughly two thirds of the ground truth during review. Budget for reading every number rather than spot-checking.

Guideline-level claims were checked against current sources and are listed in section 9. Anything marked `[UNVERIFIED, confirm before release]` in the case file came from model memory and must be checked against the primary record. Those markers stay in the file and are stripped from the learner-facing display, per section 13.

---

## 2. What was built

| Component | Count |
|---|---|
| Clinical phases | 6, plus `halted` and `case_complete` |
| Case actions | 124 |
| Critical | 13 |
| Harmful | 11 |
| Discouraged | 28 |
| Nurse prompts | 11, six with escalations |
| Follow-up requirements | 7 |
| Time-guarded transitions | 5, one of them terminal |
| Exam keys | 14 of 14, plus the general status line |
| Laboratory keys | 26 |
| Imaging and ECG keys | 5 |
| Consultant keys | 6, each with a per-study pending tier |
| Interview topics | 41, with 492 paraphrase variants |
| Pertinent negatives authored as denials | 12 |
| Review matrix rows | 971 |

Written directly in catalog ids, so all 123 binding rows are `exact`, there are no `mapped` rows needing your signature, and there is one declared orphan (`handoff_submit`, which the reference case also treats as an orphan).

**Files**

- `MGCA-case-pack.json`: the case pack, in the same shape as the CHFE pack embedded in the built prototype.
- `MGCA-review-matrix.md`: the section 14.2 per-key review matrix. This is the artifact to read.
- `MGCA-deterioration-timeline.md`: the section 14.2c timeline. Required because this case uses time-guarded transitions, and the only artifact that shows what the patient does when the resident does nothing.
- `MGCA-matcher-eval-questions.json`: 44 held-out interview phrasings. Not yet run against anything.

---

## 3. Automated results

**Validator: 0 errors, 0 warnings.** A purpose-built implementation of the section 14.1 checks: unconditional defaults on every content key, tag, and interview topic; every referenced action, flag, study and phase exists; every phase reachable by forward search over the transition state space; every non-terminal phase has a satisfiable transition; every critical action reachable; halt reasons on every action whose tag can evaluate harmful; failure messages on every prerequisite; follow-ups complete with every `satisfied_by` id resolving in the catalog; structured payloads with `abnormal` on every payload and component, payload-level `abnormal` equal to the OR of its components, and 96 parseable reference intervals cross-checked against their flags; vital signs in physiologically possible ranges; conditions restricted to the five permitted predicates in full form; the exam set inside the closed 14; the `general_status` key present; every alertness-gated phase covered by the global interview rule; and the arrival block, including the two-sentence and 45-word limits on the handover.

The validator was mutation-tested rather than trusted. Six seeded defects were each caught: a dropped unconditional default, an unsettable flag reference, an un-flagged abnormal potassium, a harmful action with no halt reason, a handover that gained a third sentence and quoted vital signs, and an alertness-gated phase dropped from the global interview rule.

**Simulator: 28 scripted routes, all as expected.** The intended path, both deterioration branches and their rescues, five harmful halts covering both mechanisms and a second beta blocker route, four blocked prerequisites, an early handoff, the alternative antibiotic and alternative steroid paths, the crystalloid equivalence group, and the sequencing check that oral prednisone and vancomycin alone do not satisfy their respective requirements. Eight of the routes exercise the clock: doing nothing at all from arrival, treating each deficit alone and letting the clock take the other, a rescue inside the last window, a rescue one action too late, a harmful action taken after a deadline has already passed, and the fairness route in which a resident who pauses for sixty, ninety and sixty seconds while working methodically still reaches the resolution phase untouched by any deterioration.

---

## 4. Your six states, and where the engine could not follow them

| Your state | Phase id | How it is entered |
|---|---|---|
| 0, initial presentation | `presentation` | arrival |
| 1, early improvement | `improving` | antibiotic, glucocorticoid and volume all given |
| 2, adrenal crisis progression | `adrenal_crisis` | fluid or dextrose given, glucocorticoid not |
| 3, progressive meningococcaemia | `progressive_meningococcaemia` | glucocorticoid and volume given, antibiotic not |
| 4, frank septic shock | `frank_septic_shock` | intubation, **or the clock at 210s from either deterioration branch** |
| 5, stabilised septic shock | `stabilized_shock` | antibiotic, glucocorticoid and vasopressor all present |

**State 4 is now implemented as you specified it.** The previous draft of this packet recorded that
"continued progression despite inadequate or delayed treatment" could not be authored, because the
engine had no time-driven transitions, and that the phase was reachable only by intubating. That
substitution misattributed the deterioration to something the resident did rather than to something
they omitted. Time-guarded transitions were added to the engine for this, and the case now carries
five of them:

| From | At | Fires if | To |
|---|---|---|---|
| `presentation` | 240s | glucocorticoid still not given | `adrenal_crisis` |
| `presentation` | 240s | antibiotic still not given | `progressive_meningococcaemia` |
| `adrenal_crisis` | 210s | glucocorticoid still not given | `frank_septic_shock` |
| `progressive_meningococcaemia` | 210s | antibiotic still not given | `frank_septic_shock` |
| `frank_septic_shock` | 300s | any of the three still missing | `cardiac_arrest`, terminal |

Intubation still reaches `frank_septic_shock` instantly, because that physiology is real and worth
teaching, but it is no longer the only route.

**Two things about this need your decision, and they are the most consequential items in this
packet.**

*The deadlines are clinical claims.* Four minutes without hydrocortisone, four minutes without a
cephalosporin, then three and a half more, then five in refractory shock before arrest. Those numbers
are compressed against real disease tempo, in the same way the five-second laboratory turnaround is,
and they are model output. If you think a patient like this has longer or shorter, change them; they
are single integers in the phase transitions.

*This case can now kill the patient without the resident touching her.* A completely passive run
arrests at 750 seconds against an estimated runtime of 600. That required an explicit per-transition
opt-in, which exists precisely so it cannot happen by accident, and the arrest is a separate terminal
phase with its own `timeout_reason` rather than the shared `halted` phase, so the debrief attributes
it to the omission rather than to anything the resident did. It is defensible: untreated fulminant
meningococcaemia with adrenal haemorrhage kills within hours and your seed asked for progression
toward peri-arrest on failure to intervene. It is still the single thing in this case most in need of
a physician's signature.

*The fairness guarantee, and what it does not cover.* The validator enforces that every deterioration
is preceded, in the same phase, by a nurse prompt naming the missing treatment at least twenty
seconds earlier. Here the margins are much wider than that: the antibiotic prompts at 45 and
escalates at 90 against a 240-second deadline, the hydrocortisone at 70 and 140 against the same. A
resident who acts on the second prompt has a hundred seconds to spare. What this does not cover is
hard mode, which multiplies prompt deadlines by three and deliberately does not slow deterioration
down, so in hard mode the hydrocortisone escalation at 420 seconds lands after the phase has already
ended. That is the intended behaviour of hard mode and the reasoning is in system design 17.1, but
you should confirm you accept it for this case.

**Second consequence you should decide on: the adrenal crisis branch will be entered by most good runs.** Your state 2 trigger is fluid or dextrose without hydrocortisone. Fluid resuscitation is a critical action and it will almost always precede the chemistry panel that reveals the adrenal component, so a resident doing sepsis care correctly enters the deterioration branch. The phase ordering mitigates this: if the antibiotic and the hydrocortisone are already in when the fluid finishes, the case goes straight to `improving` instead. So the branch discriminates on order rather than on competence, and a resident who sends the chemistry, reads it, gives hydrocortisone and then gives fluid avoids it entirely. Whether that is the lesson you want, or whether it unfairly penalises the conventional sequence, is your call.

---

## 5. Defects the review matrix found

None of these raised an error anywhere. All were found by reading the resolved values state by state, and all are fixed in the file you have.

1. **Cerebrospinal fluid glucose was clinically wrong on one of the two paths that can reach it.** A single authored value of 34 mg/dL is a normal ratio against the arrival serum glucose of 53 and a frankly low ratio against the improving-phase glucose of 96, which reads as bacterial meningitis in a patient whose fluid is normal. Now two rules.
2. **Platelet count rose across a transition.** The resolution phases carried a single value of 108, reachable from `progressive_meningococcaemia` at 75 and `frank_septic_shock` at 55. Split into 95 for `improving` and 58 for `stabilized_shock`.
3. **Same defect in the coagulation panel and the D-dimer.** INR fell from 1.8 to 1.3 and the D-dimer from over 20 to 8.9 across a transition measured in minutes. Split by phase.
4. **Creatinine fell from 1.9 to 1.5 across a transition.** Creatinine lags the insult by a day or more and cannot fall inside this encounter. The improving-phase value is now 1.7 with a comment saying so.
5. **Cardiac ultrasound recovered systolic function across a transition.** The frank shock phase showed septic cardiomyopathy and the stabilised phase showed a normal ventricle. The septic cardiomyopathy rule was removed rather than papered over, which also removes an addition that was beyond your seed.
6. **Lumbar puncture was permitted, and tagged recommended, in the vasopressor-dependent phase.** Your instruction was "only if not hypotensive". A patient holding a mean pressure of 65 on norepinephrine with a falling platelet count is not a patient to position for a lumbar puncture. The gate now excludes `stabilized_shock` as well as the three hypotensive phases.
7. **Four consultants quoted arrival laboratory values in phases where the values differ.** Endocrinology said "sodium 128, potassium 5.4, glucose 53" in a phase where they read 127, 5.7 and 48; nephrology and critical care did the same with the creatinine and the potassium. All numeric quotes that vary by phase are now replaced with descriptions, except drug doses.

**Residual limitation you cannot fix inside this schema.** Content keys are keyed on phase, and a phase can be reached from more than one predecessor, so a value that trends correctly on one path trends wrongly on another. The remaining instance: a patient who reaches `improving` from `progressive_meningococcaemia` sees the platelet count go from 75 to 95, which the disease does not do. The value chosen is correct for the intended path, which is arrival to improving. Section 11.4 forbids faking a delta by gating on an unrelated flag, so the alternative is to split `improving` into two phases, which takes the case to seven clinical phases and past the section 3.3 ceiling. Flagged rather than solved, and it is a spec-level point as much as a case-level one. See OQ-2.

---

## 6. Catalog change requests

**6.1 There is no serum cortisol, ACTH or cosyntropin entry.** This is the significant one. The case's second diagnosis cannot be confirmed by any test in the product, so it has to be made entirely on the pattern of sodium, potassium, glucose and catecholamine-resistant shock. That is defensible teaching, because treatment does precede confirmation in a suspected crisis and a cortisol assay would not return inside a real resuscitation either. It is still a gap: a resident who orders the correct test should be told it has been sent and will not return in time, not discover the test does not exist.

**6.2 There is no fibrinogen orderable.** The catalog's coagulation panel carries PT, INR and aPTT. Your seed specifies fibrinogen, and it is the analyte that distinguishes early from established consumptive coagulopathy, so it is authored here as a fourth component of the coagulation panel payload. Confirm you are content with a case payload carrying a component the catalog default does not.

**6.3 There is no 10 percent dextrose.** Only D50 and D5. D10 titrated to effect is increasingly preferred in an alert patient.

**6.4 Notify Public Health already exists and needed no change.** You asked for it to be added to the Consults tab. `consult_public_health_authorities` is already there, already carries `state_changing_overridable: true`, and this case overrides it to state-changing and has it set a flag, which is what that marker is for. It is a critical action with its own prompt, its own follow-up chain from the isolation order, and three tiers of authored response.

---

## 7. Decisions where a physician should overrule me if I got it wrong

**7.1 Creatinine of 1.6 is not a mild acute kidney injury in this patient.** You wrote 1.6 and I kept it. In a 21-year-old woman the expected baseline is 0.6 to 0.8, so 1.6 is a two-fold or greater rise, which is KDIGO stage 2. The case is authored and taught as stage 2. If you want mild, the value is about 1.1, and the nephrology consultant text and two debrief notes change with it.

**7.2 Eleven harmful actions, in three groups.** Six beta and calcium channel blockade routes, covering metoprolol, propranolol, esmolol, labetalol bolus and infusion, and diltiazem, all for rate control of a compensatory sinus tachycardia. Two insulin routes, for shifting a potassium of 5.4 in a patient whose glucose is 53 and who has no counter-regulatory cortisol. Potassium replacement in mineralocorticoid deficiency. Two hypertonic saline routes for a sodium of 128 that is about to correct on its own with volume and glucocorticoid. The hypertonic saline pair is the one I am least sure of: the mechanism is right and osmotic demyelination is real, but calling a single order immediately lethal is a modelling choice for teaching emphasis. Consider downgrading it to discouraged.

**7.3 Etomidate is discouraged, not harmful.** It inhibits 11-beta-hydroxylase and a single induction dose suppresses cortisol synthesis for 24 to 48 hours, which in a patient whose adrenals have infarcted is blocking a pathway that has already failed. The pharmacology is not in doubt; the outcome evidence in septic shock is contested. Section 7.3 says to be honest about evidence strength, so it is discouraged with a long note. If you think the specific case of established adrenal insufficiency justifies a halt, say so.

**7.4 Therapeutic heparin for the coagulopathy is discouraged, not harmful.** Guidance genuinely differs between the ISTH, Japanese and North American positions. Same reasoning.

**7.5 Oral prednisone does not satisfy the glucocorticoid requirement, and vancomycin does not satisfy the antibiotic requirement.** Both are deliberate. Prednisone in a shocked vomiting patient cannot be assumed absorbed; vancomycin has no activity against Neisseria meningitidis. Both are the kind of decision that will feel harsh to a learner and both are, I think, correct. Seven antibiotics do satisfy the requirement, so a resident who chooses any reasonable agent is not stranded.

**7.6 The skin biopsy hands over the organism, and so does the peripheral smear.** The biopsy reports Gram-negative diplococci, which is real, fast and the only route to the organism inside an encounter this short given that cultures cannot return. The smear additionally reports intracellular diplococci on the buffy coat, which is a genuine finding in fulminant meningococcaemia and is a very specific thing to make available on a routine film. Decide whether you want both.

**7.7 The urine antigen test is authored as negative in a patient who has the organism.** That is what the test does: antigen detection for this organism performs poorly, particularly on urine. The teaching value is the trap. The risk is a learner concluding the simulator is broken.

**7.8 Vaccination history sits close to the section 10.4 line.** She says she had "two of the meningitis ones", at 11 and before high school, without naming a serogroup and without connecting them to today. That is what a 21-year-old could actually tell you, and it sets up the point that the routine conjugate vaccine covers A, C, W and Y and not B. Judgement call, flagged as the requirements instruct.

**7.9 Family history is authored as non-contributory.** A mother with autoimmune hypothyroidism would be realistic and would raise autoimmune polyglandular adrenal insufficiency as an alternative mechanism. I left it out because the mechanism here is haemorrhage and the addition risks teaching the wrong disease. Add it if you disagree.

---

## 8. Open questions for the spec owner

**OQ-1. RESOLVED.** This was the observation that no time-driven transition existed and that a whole
class of seed therefore could not be authored. The mechanism was built. See
`time-driven-transitions.md` for the rationale record, including what was rejected, and system design
v0.6 sections 2.1a, 5 and 13.2a for the specification. Two consequences remain open rather than
resolved, and are recorded as open decisions 9 and 10 in the system design: whether the clock should
pause while a resident is reading, and whether deterioration pacing should get a global multiplier so
the library can be tuned without editing cases.

**OQ-2. Phase-keyed content cannot express path-dependent trajectories.** Defect 2 in section 5 above. When a phase has more than one predecessor, a single authored value for a consumptive marker is right for one path and wrong for another, and section 11.4 correctly forbids the obvious workaround. Either content keys need to be able to reference the previous phase, or section 11.4 should tell authors to design phase graphs so that resolution phases have a single predecessor, which would have changed this case's structure.

**OQ-3. Prompt cap versus the number of genuinely time-critical actions.** The presentation phase carries nine prompts. The recommended cap is three. The three I would keep are the antibiotic, the crystalloid and the hydrocortisone, which means the isolation order goes unprompted, and the isolation order is the one action in this case that protects people other than the patient. Either the cap needs to be per-category rather than global, or this case needs to accept more than three.

**OQ-4. The handoff takes one diagnosis and the honest answer to this case is two.** Meningococcaemia and adrenal crisis are both correct and neither is complete. Both are graded `acceptable_with_qualification` and the explanations do the work, which is a workaround rather than a fix.

**OQ-5. Shared catalog flags versus the no-collision rule.** Unchanged from the reference case and recorded again in the file: catalog prerequisites reference `iv_access`, `sedation_given`, `paralytic_given`, `intubated` and `lumbar_puncture_performed` across all cases, which is incompatible with section 14.1's requirement that no flag name collide with another case.

---

## 9. Sources consulted, and what each supports

- **Surviving Sepsis Campaign 2021** (Evans et al.): at least 30 mL/kg crystalloid within three hours, a weak recommendation on low-certainty evidence; norepinephrine as first-line vasopressor over dopamine, epinephrine and vasopressin, with a mean arterial pressure target of 65; antimicrobials immediately and ideally within one hour for possible septic shock; hydrocortisone 200 mg per day for shock with an ongoing vasopressor requirement.
- **IDSA bacterial meningitis guidelines 2004** (Tunkel et al.): empiric regimen; empiric therapy is not delayed pending Gram stain or other diagnostic tests; adjunctive dexamethasone for suspected or proven pneumococcal meningitis specifically.
- **CDC, Manual for the Surveillance of Vaccine-Preventable Diseases, chapter 8**: definition of a close contact, including exposure to oral secretions in the seven days before onset and airway management; chemoprophylaxis regardless of vaccination status, as soon as possible, of little or no benefit beyond 14 days; ceftriaxone treatment eradicates carriage so the index patient needs no separate course.
- **MMWR 2024, Berry et al.**: selection of prophylaxis where ciprofloxacin-resistant strains are circulating; rifampin, ceftriaxone or azithromycin preferred.
- **CDC health advisory on meningococcal disease**: case fatality of 10 to 15 percent with appropriate treatment.

Everything else, including the Endocrine Society adrenal insufficiency guideline, the etomidate literature, the DIC anticoagulation literature, the hyponatraemia correction literature and the CT-before-lumbar-puncture rule, is cited from model memory, is marked `[UNVERIFIED, confirm before release]` in the file, and must be checked.

---

## 10. Outstanding before this can be signed off

- The section 14.3 checklist, reproduced below, is untouched.
- Step 10 of section 16 has not happened: the case has not been played in the interface. Neither the validator nor the matrix can see a study the interface never renders or a rescue the resident cannot reach.
- The matcher evaluation has now been run. See section 10 below. The result is poor and the outstanding work is variant expansion on the topics that changed management, done against new phrasings rather than against the held-out set.
- Paraphrase coverage is 12 variants per topic. Ten is the floor and section 10.1 says to write toward twenty. The topics where a wrong match changes management, and therefore where expansion matters most, are `neck_stiffness`, `photophobia`, `menstrual_and_tampon`, `tick_and_outdoor_exposure`, `current_medications` and `vaccinations`.

---

## 11. Section 14.3 sign-off checklist

**Clinical content**
- [ ] Every abnormal finding, lab and imaging result is clinically correct for this diagnosis
- [ ] Every abnormal value carries an abnormal flag, and no normal value carries one
- [ ] Reference intervals are right for the assays this case is modelling, including the authored fibrinogen interval and the female-specific haemoglobin, haematocrit and creatinine ranges
- [ ] Every harmful action is genuinely harmful, and its halt reason is accurate
- [ ] Nothing tagged harmful should have been discouraged, and nothing discouraged should have been harmful. Attend particularly to hypertonic saline, etomidate and heparin
- [ ] No action tagged critical is actually optional; no action tagged neutral is actually critical
- [ ] Findings change appropriately after successful treatment
- [ ] Every debrief note teaches something correct, and every reference has been checked

**Catalog conformance**
- [ ] Every harmful and discouraged action covers every catalog route to the same act. Six beta and calcium channel routes, two insulin routes, two hypertonic saline routes, and the crystalloid equivalence group are the four places this matters
- [ ] Exam findings sit where the routing map puts them, and the general status line matches the patient in all six clinical phases
- [ ] Every diagnosis, correct and alternative, is a real catalog id

**Arrival handover**
- [ ] It names no diagnosis, in clinical or lay words
- [ ] It contains no past history, no medication, no allergy, no pertinent negative, no vital sign
- [ ] It is vague and incomplete in the way a real busy handover is. It deliberately overstates her mental state as "really out of it" when she is GCS 15 on arrival
- [ ] It is in the right voice for an EMS crew
- [ ] Read cold, it gives a resident somewhere to start and nowhere to finish

**Interview**
- [ ] Every topic in the 10.2 minimum list is authored, including the ones this case does not turn on
- [ ] The case has been played through the History tab alone, asking only what a resident would think to ask
- [ ] The patient never reveals the diagnosis or reports information she could not know. Check the vaccination and rash topics specifically
- [ ] Pertinent negatives are authored as denials rather than left to the fallback. Twelve are marked in the file
- [ ] Interview answers are correct at every alertness level, and every topic has a drowsy-phase answer where the case needs one
- [ ] Paraphrase coverage is adequate on every topic whose answer changes management

**Time-guarded transitions**
- [ ] Each of the five deadlines is a claim you are willing to defend: this patient, without this treatment, deteriorates in about this long
- [ ] The do-nothing trajectory in `MGCA-deterioration-timeline.md` is clinically right from end to end, not only at the first hop
- [ ] Each of the five narration lines is true of the vital signs shown immediately after it fires
- [ ] You intend this case to be able to arrest the patient on the clock, and the `timeout_reason` attributes it to the omission
- [ ] You accept the hard-mode behaviour in which the hydrocortisone escalation lands after the phase has ended

**Structure and sequencing**
- [ ] Consultant advice never references a study that was not ordered, or one still pending
- [ ] A pending tier exists for every consultant whose advice depends on a study
- [ ] Prerequisites are clinically correct. The lumbar puncture gate is the one that carries a clinical claim
- [ ] Follow-ups are triggered by the right action, apply only where clinically indicated, and list every satisfier
- [ ] Every deterioration branch has an exit that exists in the catalog

**Presentation**
- [ ] **No nurse prompt implies the patient is deteriorating.** Read all eleven prompts and all six escalations. No validator can catch this
- [ ] Prompt deadlines reflect real relative urgency
- [ ] Wrong dispositions and diagnoses have explanations, not just verdicts
- [ ] The review matrix contains no clinically wrong resolution
- [ ] **The case has been played start to finish in the interface**, including at least one harmful halt and both deterioration branches


---

## 10. Interview matching, measured

**Superseded in v0.8.** `MGCA-matcher-eval.js` is retired; `engine/matcher_eval.mjs` runs every pack. The current held-out numbers, model present, are 26 of 37 in scope correct, 3 wrong topics, 3 fallthroughs, 3 clarifying questions, and 21 of 30 out-of-scope questions refused, on a set brought up to the thirty-question out-of-scope floor. The figures below are the lexical matcher before the v0.8 work.

`MGCA-matcher-eval.js` extracts the shipped lexical matcher from the build and runs 37
held-out in-scope phrasings plus 6 out-of-scope, stratified by register. None of them
appears in any variant list. The embedding model is off, as it is on a hospital network.

| Register | Correct |
|---|---|
| compound | 5/5 |
| typo | 4/5 |
| shorthand | 9/12 |
| paraphrase | 4/12 |
| conversational | 0/3 |
| **in scope, total** | **22/37** |
| out-of-scope correctly refused | 1/6 |

**Wrong topic on a management-changing topic: 4.** That is the number section 10.6 says
to watch, because a fallthrough is visible to the learner and a wrong topic is not. The
four: a pregnancy question answered as photophobia, a contraception question answered as
confusion, a preceding-illness question answered as radiation of pain, and a mistyped
rash question answered as onset.

**Do not compare this to CHFE's 23 of 25.** The two sets are not comparable. CHFE's is 25
well-formed lay sentences, which section 10.6 itself names as the cautionary example: it
is a good test that measures a part of the system nothing has changed. This set was
written deliberately in the registers that document says an author-written set misses,
so a lower score is partly the set being harder and partly the matcher being worse. The
honest reading is that neither number characterises how residents actually type, because
neither set was collected from residents.

**One controlled comparison was run**, because the out-of-scope arm looked alarming. The
same twelve unrelated questions were put to both cases: CHFE rejected 7 of 12 and MGCA
rejected 5 of 12. That is directionally consistent with a larger variant space accepting
more of what it should refuse, MGCA having 492 variants across 41 topics against CHFE's
340 across 34. At n equals 12 and a difference of two it is far too small to conclude
anything, and it is recorded as a hypothesis worth testing properly rather than as a
finding. If it holds, it means variant expansion trades out-of-scope rejection for
recall, and section 10.6's note that the veto rule is deliberately switched off in favour
of recall becomes a decision each case should make rather than a global default.

**What was deliberately not done.** No variant was added to the case in response to any
of these failures, and the matcher was not touched. Section 10.6 forbids tuning against
the held-out set and then quoting the result. The set stays held out. The fix for the
paraphrase and conversational arms is variant expansion written against fresh phrasings,
starting with the topics in `CRITICAL_TOPICS` in the harness.
