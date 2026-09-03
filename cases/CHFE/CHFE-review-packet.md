# Review packet: CHFE

`cases/CHFE/`, case id `adhf-hfref-01`

**Acute decompensated HFrEF, hypertensive acute cardiogenic pulmonary oedema**
Authored against `case-authoring-requirements.md` v0.3 and `system-design-v2.md` v0.4, the
revised documents produced from this work.
Bound to `action-catalog.json` v0.1-draft and `diagnosis-catalog.json` v0.1-draft.
Status: **UNSIGNED DRAFT. Not usable with learners.** The validator currently reports
5 errors, none of them in the case content: two are catalog binding gaps that stop the
case running as written, three are grammar defects in the catalog. See section 12.

---

## 1. Read this before anything else

Section 2 of the authoring requirements draws a hard line: anything a resident could act on
clinically is AUTHOR-ONLY, and "the AI must never invent a clinical fact... not a symptom, not a
finding, not a lab value, not a consultant recommendation, not a prerequisite, not a deadline."

**This case was produced without an author seed, so a language model generated every AUTHOR-ONLY
field.** That is the exact thing section 2 calls the single most important constraint in the
document. It was done deliberately at your request, but it inverts the intended workflow, and the
consequence is that nothing here carries clinical authority until a physician has confirmed or
replaced it.

The practical effect is that the review burden is larger than it would be for a normal case. On a
seeded case you would be checking that the AI expanded your ground truth faithfully. Here you are
checking the ground truth itself: every vital sign, every laboratory value, every harmful
designation, every halt reason, every consultant recommendation, and every deadline.

The fields needing primary sign-off rather than review are listed in
`provenance.author_only_fields_pending_signoff` inside the case file.

---

## 2. What the case is

A 65 year old man with known ischaemic cardiomyopathy, LVEF 25 to 30 percent, arrives by ambulance
with four days of progressive breathlessness and an acute worsening since 04:00. He is
hypertensive at 188/104, tachycardic at 118, saturating 87 percent on 6 L nasal cannula,
respiratory rate 32, afebrile. He is warm, well perfused, orthopnoeic, has a raised jugular venous
pressure, an S3, bilateral crackles with an overlying expiratory wheeze, symmetrical pitting
oedema, and is four kilograms above his stated dry weight. He ran out of furosemide five days ago
and ate a salt load at a family event.

Nohria profile B, warm and wet. The intended path is non-invasive ventilation, then afterload
reduction with a nitrate, then diuresis, with an ECG and chest film to exclude the alternatives
and a history that identifies the precipitant. Disposition is a monitored bed that can continue
non-invasive ventilation and a titrating infusion.

**Structure**

| Component | Count |
|---|---|
| Clinical phases | 5, plus 2 terminal |
| Case actions | 65 |
| Actions that can halt the case | 6 |
| Interview topics | 34 |
| Paraphrase variants | 340 |
| Pertinent negatives authored as explicit denials | 10 |
| Exam manoeuvres authored, of the catalog's closed set of 14 | 11 |
| Content keys with state-dependent rules | 14 |
| Follow-up requirements | 4 |
| Time-sensitive critical actions with prompts | 8 |

**Deliberate design choices worth knowing before you review**

The tachycardia of 118 is set where it is to bait intravenous rate control. The wheeze is present
to bait a bronchodilator. The lactate of 2.1 is present to bait a sepsis pathway. The troponin of
62 is present to bait an acute coronary syndrome pathway. Each of those is the point of the case,
not an accident of the numbers. If you change any of them, check what trap you are removing.

---

## 3. Author sign-off checklist (section 14.3)

Every box is unticked. Status columns record what was done during drafting, not sign-off.

| # | Item | Drafting status |
|---|---|---|
| 1 | Every abnormal finding, lab and imaging result is clinically correct for this diagnosis | **Needs primary review.** All values AI-generated. |
| 2 | Every harmful action is genuinely harmful, and its halt reason is accurate | **Needs primary review.** See section 4; dobutamine is the weakest. |
| 3 | No action tagged critical is actually optional; no action tagged neutral is actually critical | Traps sit at neutral only because the vocabulary has no middle tier. See 6.1. |
| 4 | The patient never reveals the diagnosis or reports information he could not know | Checked. He describes his chronic history in lay terms and never names the current problem. Judgement call flagged in 4.6. |
| 5 | Pertinent negatives authored as denials, not left to the fallback | 10 authored. Validator lists them. |
| 5a | **Every abnormal value carries an abnormal flag, and no normal value carries one** | New. 25 payloads converted from prose. The interface renders flagged components red, so a missed flag is a value the learner reads as normal. Validator cross-checks every parseable reference interval; all agree. **Check the flags, not just the numbers.** |
| 5c | **The exam findings survived redistribution intact** | New and important. The case's own manoeuvres (general appearance, JVP, hepatojugular reflux, extremities) do not exist in the catalog, so every finding was rerouted. See section 15. |
| 5b | **Reference intervals are right for your assays** | Taken from catalog defaults where they exist, marked `verify` where not. All unverified. The BNP and troponin bind to different assays than the case wrote; see 4.9. |
| 6 | Consultant advice never references a study that was not ordered, or one still pending | **Two defects found and fixed.** See 5.2. Re-check. |
| 7 | A pending tier exists for every consultant whose advice depends on a study | Cardiology and nephrology have pending tiers. Critical care gates on flags, not studies, so it needs none. |
| 8 | Findings change appropriately after successful treatment | Exam, VBG, lactate, BMP and POCUS all trend. Chest film freezes at order state. |
| 9 | Interview answers are correct at every alertness level | Global rule covers both intubated phases. See 6.4 for the language gap. |
| 10 | Prerequisites clinically correct; catalog defaults waived where they should be | One waiver: central access before peripheral vasopressor. Confirm you agree. |
| 11 | Follow-ups triggered by the right action and apply only where indicated | 4 follow-ups. None of their conditions does discriminating work; see 6.11. |
| 12 | **No nurse prompt implies the patient is deteriorating** | Written against this constraint. **Re-read all 8 prompts yourself.** No validator can check it. |
| 13 | Prompt deadlines reflect real relative urgency | AI-assigned. Ordering: NIV 45s, nitrate 75s, ECG 90s, film 150s, adherence 210s; furosemide 60s from phase entry; stop nitrate 25s, pressor 40s. |
| 14 | Wrong dispositions and diagnoses have explanations, not verdicts | 5 dispositions and 7 diagnoses, each explained. |
| 15 | The review matrix contains no clinically wrong resolution | **Four found and fixed during drafting.** Re-read `CHFE-review-matrix.md` in full. |
| 16 | Every debrief note teaches something correct | All 65 case actions have notes. All need clinical review. |

**On item 12.** The eight prompt texts are the constraint most likely to be violated without
anyone noticing, because the failure is a contradiction between two parts of the interface rather
than an error in either. Read each one against a monitor showing static vitals and ask whether it
implies a trajectory. The drafting rule used was: describe the current state or express concern
about inaction, never a change over time. For example, "his sat is sitting at 87" rather than "his
sat is dropping."

---

## 4. Clinical calls most in need of your judgement

These are ordered by how likely I think you are to disagree.

**4.1 Dobutamine as a halting harmful action.** The physiology is defensible: an inotrope in a
hypertensive, warm, well-perfused patient with an ischaemic cardiomyopathy adds myocardial oxygen
demand and arrhythmic risk with nothing to gain. Modelling a single order as immediately fatal is
a teaching-emphasis choice, not an evidence claim. The trial evidence against routine inotropes in
decompensated heart failure concerns outcomes over an admission, not immediate arrest. Consider
whether this should instead be a deterioration path, or neutral with a strong note.

**4.2 Intubation causing hypotension with certainty.** The case transitions to
`post_intubation_hypotension` whenever the patient is intubated, in every phase. Post-intubation
hypotension is common but not universal, and this patient's pre-intubation shock index is around
0.63, which is not high-risk. The modelling argument is that he is preload-dependent, vasodilated
on a nitrate, and receiving positive pressure plus an induction agent. The engine has no
probability, so the choice is between always and never, and always teaches the anticipation
lesson. You may prefer to gate it on the nitrate infusion being running, which would be a small
change to one transition condition.

**4.3 Morphine as neutral rather than harmful.** The harm signal is consistent across registry
analyses but entirely observational, with obvious confounding by indication. Halting the case on
it would teach a stronger claim than the evidence supports. Tagging it neutral means it carries no
scoring weight at all, which teaches too little. This is a genuine dilemma created by the tag
vocabulary; see 6.1.

**4.4 Crystalloid remains harmful in the post-intubation hypotensive phase.** A fluid challenge
in post-intubation hypotension is a common and often reasonable reflex. The argument for keeping
it harmful is that this specific patient is several litres overloaded and his hypotension is
vasodilation plus reduced venous return, so the treatment is a vasopressor and stopping the
nitrate. You may consider this too absolute.

**4.5 Correct disposition is intensive care or coronary care, with step-down marked acceptable
with qualification.** This is institution-dependent and the case says so in the explanation text.
If your department routinely runs non-invasive ventilation and nitrate infusions on a step-down
unit, you should probably swap which is marked correct.

**4.6 The patient describing his own cardiomyopathy.** Section 10.4 forbids the patient from
stating or implying the diagnosis. Section 10.2 requires past medical history as a topic. He says
his heart was damaged by his infarct and does not pump properly, which is his known chronic
history stated in lay terms, and he never attributes the current episode to anything or uses the
words heart failure. I think that is the right line but it is a line, and you should confirm it.

**4.7 Norepinephrine and push-dose epinephrine tagged harmful in the hypertensive phases.** No
one is likely to do this, and if they did it would be bad. Halting for it may be more punitive
than instructive.

**4.9 Two results are attached to the wrong assay.** The case's BNP of 2840 against a
reference under 100 binds to the catalog's pro-BNP entry, and its numeric high-sensitivity
troponin I against a 99th-percentile URL of 34 binds to a qualitative troponin T. Structurally
both bind cleanly. Clinically the numbers are not transferable between those assays. Decide
which assay the case is teaching, then either rewrite the value or ask for the catalog entry.

**4.8 Every specific number.** BNP 2840, high-sensitivity troponin I 62 ng/L against a stated
reference of 34, creatinine 1.62 against a baseline of 1.4, sodium 133, pH 7.29 with pCO2 54,
lactate 2.1, D-dimer 0.94, haemoglobin 12.4. These are plausible for the presentation and none is
verified. Reference intervals in particular are assay-dependent and the troponin reference should
be set to whatever your institution uses.

---

## 5. Defects found and fixed during drafting

Recorded because they show what the tooling caught and what it did not.

### 5.1 Caught by the validator

- `bp_cycling_after_nitrate` listed `arterial_line` in `satisfied_by`, but no such action existed
  in the case. Fixed by adding the action.
- `case_complete` phase carried `temperature_c: 96.0`, a Fahrenheit value in a Celsius field. A
  plausibility range check caught it. Fixed to 36.8. Worth adding range checks to the real
  validator; this class of slip is invisible to reference checking.
- Prerequisites were initially written as block triggers (`NOT flag iv_access set`) rather than as
  requirements (`flag iv_access set`). The worked table in section 8.1 implies the requirement
  polarity. All 24 inverted. **This is worth stating explicitly in the authoring document**, since
  both readings are grammatical and the resulting behaviour is exactly opposite.

### 5.2 Caught only by reading the review matrix

None of these raised an error anywhere. This is the failure mode section 14.2 describes, and it
occurred four times in a single case.

- **`labs_lactate` rule ordering.** A rule keyed on the post-intubation sedation flag was listed
  above the rule for the hypotensive phase, so a patient who was both sedated and hypotensive
  resolved to a normal lactate of 1.6. Reordered to test phase first.
- **`consult_cardiology` pending tier.** The holding response fired whenever *either* the ECG or
  the troponin had been ordered, so with the ECG resulted and no troponin sent, the consultant said
  both were in the system with nothing back. Wrong on both counts, and precisely the error item 6
  of the checklist exists to prevent. Split into four specific tiers.
- **`labs_vbg` and flag permanence.** The improved gas was keyed on `flag on_niv set`. Flags are
  permanent, so a patient who received non-invasive ventilation, was then intubated and collapsed,
  still carried `on_niv`, and a gas drawn during the hypotensive phase returned a normal pH for a
  shocked patient. Phase rules now precede the flag rule. **This is the most instructive defect in
  the set** and I would suggest adding it as a worked warning to section 15, because the permanent
  flag limitation is stated abstractly there and its practical consequence is not obvious.
- **Nitrate tags in `intubated_stabilized`.** Nitroglycerin was harmful only in
  `post_intubation_hypotension`, so in `intubated_stabilized` it fell through to "recommended". That
  patient has a systolic of 108 held up by a norepinephrine infusion. Extended the harmful
  condition to both phases. The same fallthrough affected the loop diuretics, downgraded to neutral.

The pattern in all four is identical: a rule list that is correct for the situations the author was
thinking about, and wrong for a situation reachable through a different route. Three of the four
involved the deterioration branch, which is the part of the case an author thinks about least.

---

## 6. Gaps in the schema and the authoring documents

Feedback for the design owner rather than for the clinical reviewer. Ordered by how much trouble
each is likely to cause.

**6.1 The tag vocabulary is never enumerated, and appears to have no middle tier.** Neither
document lists the permitted tag values. They can be inferred from the scoring table in section
11.2: critical, harmful, recommended, neutral. The consequence is that an action which is wrong
but not lethal, such as morphine here, a bronchodilator for cardiac asthma, steroids, antibiotics
without an indication, or an unindicated CT pulmonary angiogram, can only be tagged neutral, which
carries no scoring weight. Section 3.4 asks the author to identify traps as a distinct category
and section 7 says to tag every plausible trap, but there is nothing to tag them as. Five of this
case's traps are currently invisible to scoring and teach through the debrief note alone.
Recommend an explicit `discouraged` tier with a minor cost.

**6.2 Section 14.1 requires that no flag name collide with another case, which is incompatible
with catalog prerequisites.** Catalog-level prerequisites such as intubation requiring
`sedation_given` and `paralytic_given` must reference the same flag names in every case. Suggest
splitting the namespace: catalog-owned flags shared and reserved, case-owned flags prefixed and
checked for collisions.

**6.3 Alertness gating cannot be expressed in the condition language.** Section 10.5 asks authors
to gate interview answers on alertness level, but alertness is a phase property and there is no
alertness predicate. The workaround is to enumerate every phase whose alertness is reduced, which
means the global rule silently breaks if a phase is added later. Either add the predicate or state
the enumeration requirement in section 10.5. The validator here includes a check that every phase
with alertness 2 or 3 is covered.

**6.4 Speech limited by respiratory distress is not covered.** Section 10.5 handles alertness but
not the much more common case of a patient who is fully alert and can only speak in short bursts.
It could not be done as a global rule without suppressing all topic content, so all 34 topics in
this case carry a separate presentation-phase answer. That is a doubling of interview authoring
effort that the requirements document does not warn about.

**6.5 Whether interview topics have addressable action ids is undefined.** This case treats
"ask about medication adherence" as a critical action, which requires the `action A taken`
predicate to reach an interview topic. Section 5.1 logs interview questions as observational
entries, so the log supports it, but nothing states that topics have ids in the action namespace.
If they do not, identifying the precipitant cannot be scored at all.

**6.6 Terminal phases require a vitals block that has no meaning.** The `halted` phase has one
vitals block, but the six harmful actions in this case produce different physiology. The
`case_complete` phase logically ought to inherit the vitals of the phase handed off from, and
cannot. Suggest making vitals optional for terminal phases.

**6.7 Section 7 lists "transition triggered" as an action field while section 5 puts transitions
on phases.** Two places to express the same thing, with no statement of which wins. This case puts
them on phases only.

**6.8 Cascading transitions within a single action are undefined.** If a resident gives the
diuretic during the presentation phase and later satisfies the transition into `stabilizing`, the
`stabilizing` transition rule for `diuretic_given` is already true on arrival. Whether the engine
re-evaluates within the same step or waits for the next state-changing action is unspecified, and
it changes both the phase sequence and the prompt deadlines, which are measured from phase entry.
This is reachable in this case; scenario 10 of `engine/sim_runner.py` produces it.

**6.9 Serial testing cannot be represented.** A repeat troponin is the standard manoeuvre for
distinguishing acute from chronic myocardial injury and it is one of the things this case most
wants to teach. Because a result resolves against state and the condition language cannot express
"the second time this was ordered", a repeat in an unchanged state returns an identical value. A
delta could be faked by gating on an unrelated flag, which would be dishonest, so this case
teaches the principle in the debrief instead. Consider an ordinal predicate such as
`study S ordered at least N times`, which would stay enumerable in the review matrix.

**6.10 Turnaround classes have no bedside option.** Point-of-care ultrasound and a point-of-care
venous gas return in seconds and are performed by the treating clinician. The available classes are
labs at 5 seconds, imaging at 10, ECG at 10. This case uses a per-study override for ultrasound,
which section 8.1 says should stay unused. Recommend a `bedside` class.

**6.11 Follow-up `applies_when` conditions do no work here.** All four are trivially true once
their trigger has fired. That is honest rather than a defect, but a reviewer could mistake them for
meaningful clinical gating, and a validator cannot distinguish a meaningful condition from a
tautological one.

**6.12 Grammar inconsistency in the documents.** Section 4 specifies `flag F set`, but the worked
interview example in section 10.1 writes `"when": "flag nausea_treated"` without the trailing
keyword. This case uses the section 4 form throughout.

**6.13 Handoff and the phase machine.** Section 12 says the case completes on handoff, and section
14.1 requires every non-terminal phase to have a satisfiable transition. To satisfy both, every
non-terminal phase here carries a transition to `case_complete` on handoff, which is boilerplate
repeated five times. Cleaner would be an engine-level completion rule outside the phase graph, with
the validator's transition requirement relaxed accordingly.

---

## 7. Catalog change requests

Section 6 and section 7 both say to escalate rather than author around a missing capability. These
are the escalations.

Status updated against `action-catalog.json` v0.1-draft.

| Request | Status | Reason |
|---|---|---|
| `bedside` turnaround class | **Delivered**, at 0 seconds | See 6.10. At zero there is no order-and-wait beat for a bedside scan; 2 to 3 seconds keeps it. This case retains a 3-second override. |
| Central-access prerequisite on vasopressor entries | **Delivered** as a line-access default on 99 entries | This case waives it for peripheral norepinephrine. |
| `vent_settings_lung_protective`, `peep_reduce` | Outstanding | Needed by any case with a ventilated patient |
| A stop-action class for `persistent` infusions | **Delivered** | One stop action per persistent infusion, 20 in all. The deterioration branch now has a working exit. |
| Venous blood gas | **Delivered**, with venous reference intervals and no pO2 | See 18 |
| A critical care or intensivist consultant | **Delivered**; 17 consultants | |
| A general appearance exam | Outstanding | The finding that changes most with treatment in a respiratory case |
| Hepatojugular reflux, jugular venous pressure as discrete manoeuvres | Outstanding | Currently folded into the neck exam |
| Formal echocardiogram | Outstanding | No catalog entry |
| `bp_cycling_q5min`, `urine_output_monitoring` as stabilisation tasks | Outstanding | Both are follow-up obligations here |
| Handoff tab, disposition list, handoff action | Outstanding | The catalog lists this in its own `known_gaps` |
| A `speech_limited` appearance value, 0 to 2 | Outstanding | Would let 6.4 be handled globally instead of per topic |
| A `discouraged` tag tier | Outstanding | See 6.1; five traps in this case still carry no scoring weight |

---

## 8. Reference verification

Five references were checked against PubMed records during drafting and match on authors, journal,
year, volume and pages:

- Gray A, Goodacre S, Newby DE, Masson M, Sampson F, Nicholl J; 3CPO Trialists. N Engl J Med. 2008;359(2):142-51.
- Felker GM, Lee KL, Bull DA, et al. N Engl J Med. 2011;364(9):797-805.
- Cotter G, Metzkor E, Kaluski E, et al. Lancet. 1998;351(9100):389-93.
- Peacock WF, Hollander JE, Diercks DB, Lopatin M, Fonarow G, Emerman CL. Emerg Med J. 2008;25(4):205-9.
- Nohria A, Tsang SW, Fang JC, et al. J Am Coll Cardiol. 2003;41(10):1797-804.

**Every other reference in the case file is drawn from model memory and is unverified.** Each is
marked `[UNVERIFIED, confirm before release]` inline. Do not let any of them reach a learner
unchecked; a plausible-looking citation to a paper that does not say what is claimed is worse than
no citation.

One substantive point on the evidence rather than the citation. The non-invasive ventilation
debrief note deliberately does not claim a mortality benefit. Earlier meta-analyses reported
reductions in intubation and mortality; the largest randomised trial, 3CPO, found neither. The note
states the strongest defensible claim, which is faster physiological and symptomatic improvement,
and tells the learner the evidence is contested. If you prefer a cleaner teaching message, that is
a decision to make knowingly.

---

## 9. Known incomplete

- **Global catalog entries are assumed, not supplied.** The case references 51 catalog ids. Several
  do not exist yet; see section 7.
- **Normal defaults are assumed.** Normal exam findings, normal laboratory values for a 65 year old
  man with stage 3 chronic kidney disease, the generic unrelated-consultant response and the
  generic out-of-scope patient response are all inherited from globals that must exist.
- **Paraphrase variants sit at the floor.** Ten per topic, where section 10.1 asks for ten to
  twenty. Section 10.6 identifies matching accuracy as the highest technical risk in the system,
  because a mismatch delivers a clinically wrong answer with full confidence. The topics most worth
  expanding are the ones whose answers change management: `medication_adherence`, `chest_pain`,
  `orthopnea`, `paroxysmal_nocturnal_dyspnea`, `substance_use_stimulants`.
- **Code status and goals of care are not authored.** Defensible content for an admission for
  decompensated heart failure with an ejection fraction in the twenties, and arguably a teaching
  point in its own right.
- **Pregnancy status is not authored,** correctly, since the patient is a 65 year old man and
  section 10.2 requires it only where applicable.
- **Prompt deadlines are uncalibrated.** Section 9.6 says to prioritise relative urgency over
  absolute values and expects global recalibration. The relative ordering is the part to review.

---

## 10. Files

This case is a **case pack**: `cases/CHFE/`, every file sharing the CHFE prefix. It is
packed together with every other case into one `build/simulator.html`, which opens on a
case picker. The
engine lives in `engine/` and contains no clinical content; the catalogs live in
`catalog/`. A second case is scaffolded with `python3 engine/new_case.py <PREFIX>` and
runs through the same tools without any of them being edited. See the repository README.

| File | Authored or generated | What it is |
|---|---|---|
| `CHFE-case.json` | authored | The case file. The deliverable. |
| `CHFE-SEED.md` | authored | Records that there is no seed, and why that matters |
| `CHFE-binding-map.json` | authored | case id to catalog id, one row per action, with the placement for anything the catalog lacks |
| `CHFE-scenarios.json` | authored | The ten end-to-end paths the simulator walks |
| `CHFE-tests.js` | authored | Case-specific engine assertions |
| `CHFE-matcher-eval.js` | authored | Interview matcher accuracy on held-out phrasings |
| `CHFE-review-packet.md` | authored | This document |
| `CHFE-binding.json` | generated | The binding with derived statuses |
| `CHFE-review-matrix.md` | generated | **The main clinical review artifact.** Section 14.2 |
| `restructure_exam.py` | one-time | Redistributed the exam findings onto the catalog's 14 manoeuvres |
| `structure_results.py` | one-time | Converted the lab and imaging results to structured payloads |
| `../../build/simulator.html` | generated | Playable single-file prototype. Open in a browser |

The engine that runs all of this lives in `engine/` and contains no clinical content.
The catalogs live in `catalog/`. A second case is scaffolded with
`python3 engine/new_case.py <PREFIX>` and runs through the same tools unedited.

Run the pipeline with:

```
python3 engine/bind_catalog.py   cases/CHFE
python3 engine/validate_case.py  cases/CHFE
python3 engine/build_simulator.py
python3 engine/sim_runner.py     cases/CHFE
node    engine/engine-tests.js   build/simulator.html cases/CHFE/CHFE-tests.js CHFE
```

Current state: validator reports 5 errors and 2 warnings, all of them about the catalog
binding rather than the case content; simulation reports 10 of 10 scenarios passing; 75
checks pass, 38 of them case-agnostic and 37 specific to this case. None of those says
anything about whether the medicine is right.

---

## 11. The prototype

the prototype runs the case in a browser: seven tabs, the phase graph, the condition evaluator
and resolver, prerequisites with their block messages, result timers with freezing, the nurse with
narration and prompts, the handoff, and the debrief. It implements the fold described in section 5
of the system design rather than mutating state directly, so log entries and derived time events are
merged chronologically and every view is recomputed from the log.

**Two engine defects surfaced by building it.**

A consult that sets a flag is state-changing, and the first implementation returned no content for
state-changing actions. Cardiology could be called and would say nothing. The requirements treat
"is it state-changing" and "does it return content" as the same question in section 7; they are not.
Consultant entries need both, and the authoring document should say so.

The ECG's turnaround class is `ecg`, which is neither `labs` nor `imaging`, so a UI that grouped
investigations by class dropped the ECG from the menu entirely. It is the second most important
study in the case. Nothing in the validator or the review matrix would catch a study the interface
never renders, because both check the case file rather than the interface.

**What the prototype makes visible that the matrix does not.** The `halted` phase's single vitals
block is displayed on every halt, so a metoprolol arrest and a fluid-bolus decompensation show
identical numbers. Section 6.6 above argues from the schema; the screen argues better.

**Interview matching, measured.** Section 10.6 of the requirements calls matching the highest
technical risk in the system. A plain bag-of-words match over the authored variants got 18 of 25
held-out phrasings right, put 5 on the wrong topic, and let 2 fall through. Two of the five errors
were clinically opposite: "any calf pain" matched the chest pain topic, and "does anything make it
better" matched aggravating factors. Weighting tokens by inverse document frequency and adding a
rare-token override raised it to 23 of 25 with 1 wrong topic, which is what ships. Out-of-scope
questions are still misrouted 2 times in 5, so a resident asking something the case does not cover
can receive a confident, specific, wrong answer.

Ten to twenty variants per topic is not enough for lexical matching, and this case sits at the floor
of ten. The number to watch is not overall accuracy but the wrong-topic rate on topics whose answers
change management, because a fallthrough is visible to the learner and a wrong topic is not.

Reproduce it with `node cases/CHFE/CHFE-matcher-eval.js`. The tool extracts the matcher
from the built prototype rather than reimplementing it, so the numbers always describe
what actually ships. **On the current build the single wrong topic is a management-changing
one**: "what medicines are you on" is matched to medication adherence rather than current
medications. Those two answers are adjacent but not the same, and a resident who asks what
he is taking and is told why he stopped taking it has been answered a question they did not
ask. Adding variants to `current_medications` is the fix.

---

## 12. Binding the case to the action catalog

The catalogs arrived after the case was written, so this section records what integrating
them broke. Detail and proposed schema changes are in `spec-addendum.md`; this is the part a
clinical reviewer needs.

**Binding: 16 exact, 41 mapped, 7 with no catalog entry, and no blocking failures.** It was
6 exact, 44 mapped and 13 unmatched with two blocking before the exam redistribution and the
catalog additions. Every mapped row is an author judgement recorded in `CHFE-binding-map.json`
with a note.

**The two blocking gaps are closed.** Stopping the nitroglycerin infusion and the venous
blood gas both exist now, so the deterioration branch has a working exit and the gas trend is
authorable. A critical care consultant exists. The exam gaps reported here previously are also
resolved. See section 18 for what changed and what to check.

Seven case actions still have no catalog entry: `bp_cycling_q5min`, `echo_formal`,
`handoff_submit`, `interview_topic_medication_adherence`, `peep_reduce`,
`urine_output_monitoring`, `vent_settings_lung_protective`. None is load-bearing for the
intended path, and each is rendered in a separate group so the gap stays visible.

**Harm that is escapable. Partly fixed.** The fluid bolus now covers all four crystalloid
entries through the catalog's `crystalloid_bolus` equivalence group, and **all four halt the
case**. That is now walked rather than asserted: `sim_runner.py` learned to resolve
`also_covers`, which it previously could not, so three scenarios walk the covered siblings
to the same halt. Two escapes remain: ipratropium alone escapes the bronchodilator trap,
and a ketamine infusion does not satisfy the post-intubation sedation follow-up. A harmful
tag has to cover every route to the harm, and at the moment it covers one route each.

**CPAP and BiPAP are one catalog entry. Fixed.** The case used to tag them as two actions
bound to the same entry, and because one catalog entry resolves to one case action the
second was never in the action surface at all: its tag, its debrief note and its two
references were unreachable, and a scenario step naming it was silently discarded rather
than blocked, so that scenario had been passing for the wrong reason. They are now a
single action, `niv_bipap_cpap`, whose note carries both teaching points including the one
previously lost, that bilevel and continuous pressure are equivalent here and that bilevel
is often preferred in the hypercapnic patient this one is. See `consolidate_niv.py` in
this folder. If the catalog ever splits the two modes into separate entries, the fix is to
add them to the `non_invasive_ventilation` equivalence group and bind this action to the
group, not to reintroduce two case actions.

**Diagnoses: fixed, and worth knowing how it was found.** The case named its diagnoses in
its own ids, and the builder had a fallback that guessed the correct one by looking for
"reduced ejection" or "hfref" in the catalog. The guess worked, so nothing looked wrong.
Separating the engine from the case content exposed it, because a guess keyed on a specific
diagnosis is case content sitting in engine code.

Removing the guess broke the handoff immediately, which is what should have happened: the
correct answer had never resolved to a catalog id. All eight diagnoses, the correct one and
the seven alternatives, are now bound to real ids and verified scoring correctly in the
interface.

**Check the eight bindings.** In particular, the case's correct answer carries a longer label
than the catalog's ("...with cardiogenic pulmonary oedema" against plain "...reduced ejection
fraction"), and the resident now sees the catalog's shorter name. Confirm that is acceptable,
or ask for a more specific catalog entry.

---

## 13. Abnormal values, and why the flags are authored

The interface renders abnormal lab components in red. The flag is authored per component in
the case file, not computed at display time, because the catalog's contract says the renderer
must not recompute and because parsing "(high)" out of prose fails silently the first time an
author writes "raised" or gives a bare number.

Twenty-five payloads were converted from prose to structured panels. Every number, unit and
interpretive comment carried across unchanged, and the original prose is kept alongside each
converted rule so you can diff them. Verified in a browser: on a full metabolic panel, sodium
133, chloride 96, BUN 32, creatinine 1.62 and glucose 172 render red while potassium 4.4,
bicarbonate 25 and calcium 8.8 render black.

**What this asks of you that the old prose did not.** You are now signing off two things per
value: that the number is right, and that the flag is right. A number you consider abnormal
that carries no flag is displayed to the learner as normal, and no other check will catch it.
The validator cross-checks every parseable reference interval against its flag and currently
reports no disagreement, but it can only check ranges it can parse, and the ranges themselves
are unverified.

---

## 14. Sound

The prototype plays a continuous heartbeat and a trill on nurse prompts. Two decisions need
your view.

**The pitch mapping is more dramatic than a real oximeter.** A5 at 100% saturation, one
semitone lower per percent below, so 415 Hz at this patient's presenting 87% and 698 Hz once
he is at 96%. A real pulse oximeter's pitch drop is neither linear in semitones nor anchored
at 100%. This makes desaturation more salient in the simulator and less like the sound a
resident will actually work with. If transfer matters more than salience, it should match the
device convention instead.

**The trill may undercut section 9.** Nurse prompts must not imply deterioration. A distinct
alert sound attached only to prompts teaches the resident that the trill means "you have
missed something", which is exactly the information the prompt text is forbidden to carry.
If that is unacceptable, the fix is to sound every nurse utterance rather than prompts alone.

Nothing in the interface depends on sound alone; the monitor carries the same information
visually, and that has to stay true.

---

## 15. The exam rework

The action catalog states that its 14 exam manoeuvres are the complete set, supplies a
default finding for each, and supplies `exam_finding_routing`, a map that fixes where a
finding belongs when its anatomy does not match a manoeuvre. It also defines a general status
line rendered above the manoeuvres, which is not clickable and therefore cannot be skipped.

The case predated all of that and used four manoeuvres that do not exist in the interface:
general appearance, jugular venous pressure, hepatojugular reflux, and extremities. Those
findings were unreachable. `restructure_exam.py` redistributes them.

**Where the findings went, and why.** The routing map decided this, not the author:

| Finding | Now lives under | Note |
|---|---|---|
| End-of-bed impression, GCS | General appearance line | Always visible, above the manoeuvres |
| Speech in short bursts, airway patency | Airway | Newly written during redistribution |
| Accessory muscle use, work of breathing, posture | Breathing | Newly written during redistribution |
| Capillary refill, peripheral temperature, pulse quality | Circulation | From the old extremities manoeuvre |
| Jugular venous pressure, hepatojugular reflux, trachea | Neck | Two old manoeuvres merged into one |
| Third heart sound, murmur, apex beat, **pitting oedema** | Cardiovascular | The map puts oedema here, not under musculoskeletal or circulation |
| Crackles, wheeze, air entry | Pulmonary | Unchanged content |
| Tender liver, distension | Abdominal | Unchanged content |
| Calf tenderness, asymmetry, cords | Musculoskeletal | The deep vein thrombosis pertinent negative |
| Sweating, temperature, rash | Skin | Unchanged content |
| Orientation, GCS, focal deficit | Neurological | Unchanged content |
| Anxiety, cooperativeness | Psychological | Newly written; moved out of the neuro finding |

HEENT, genitourinary and back are not authored and inherit the catalog default.

**Three things to check specifically.**

*The three newly written categories.* Airway, breathing and psychological had no prior
authored content. Each restates something the case already asserted elsewhere, but they are
new sentences and need reading as such. They are listed in the case file under
`provenance.exam_redistribution.newly_authored_during_redistribution`.

*The hepatojugular reflux is no longer a discrete act.* The case tagged it as a separate
confirmatory manoeuvre with its own teaching note, and a learner could choose to perform it or
not. It is now part of the neck exam and happens automatically whenever the neck is examined.
The teaching note is folded in. Whether that is an acceptable loss is your call; the
alternative is asking for a catalog entry.

*The oedema placement will look wrong to some readers.* Peripheral oedema under the
cardiovascular exam rather than the extremities is the catalog's decision, and the reason it
gives is sound: without a fixed routing an author puts pedal oedema under cardiac in one case
and musculoskeletal in another, and the learner concludes the tool is arbitrary. The
musculoskeletal exam carries a cross-reference so a learner who looks there is not stranded.

**The validator now enforces the closure.** It errors if the case authors findings for a
manoeuvre the catalog does not have, errors if a catalog exam has no default, and reports how
many of the 14 are authored. It also requires the general status line to exist, because
without it the learner sees the catalog's generic "No acute distress. GCS 15." above a patient
in severe respiratory distress.

---

## 16. Interface changes in this pass

Recorded because two of them change what the resident is measured on.

**Orders are now batched.** On the investigations, stabilization and interventions tabs a
click selects an item rather than performing it; nothing happens until Submit Order. Selections
persist across tab switches, so a resident can assemble an order set across tabs. Exams and
consults are unchanged and still fire on click, because they are reads rather than orders.

Two consequences worth deciding on deliberately:

- **Batching changes what the timing measures.** Prompt deadlines run from phase entry and are
  unchanged, but a resident who selects five things and submits them together produces five log
  entries at one instant. The fold still applies them in sequence, so prerequisites, transitions
  and harmful tags all evaluate exactly as they would one at a time. Verified: a batch
  containing metoprolol halts on the metoprolol and discards everything selected after it,
  which is correct and may surprise a learner who expected the whole set to go through.
- **It removes a small amount of realism and adds a different kind.** Clicking an action and
  having it happen instantly is not how ordering works; assembling a set and submitting it is.
  But it also lets a resident sit and think without the clock reflecting hesitation, which is
  the opposite of what a resuscitation case usually wants to teach. If the timing pressure
  matters, consider timing from first selection rather than from submission.

**Buttons carry the name and nothing else.** The prerequisite hints ("needs: iv access") and
turnaround times underneath each button are gone. They were system detail a resident does not
read off a real order menu, and a blocked attempt with its nurse message teaches the
prerequisite better than a label does. Pending and resulted states are still shown by colour
and in the pending rail.

**Two fields moved out of the build and into this case file**, where a reviewer can see
them: `handoff.disposition_display_order`, which orders the level-of-care list from least
to most intensive rather than in authoring order, and `debrief_configuration.trap_actions`,
which names the seven plausible-looking wrong actions. Both were previously hard-coded in
the builder, which meant a second case would have silently inherited this case's answers.
Check the trap list is complete: an action missing from it gets no debrief section.

**Each phase now carries both a `label` and a `short_label`.** The full label is what the
debrief shows; the short label is what fits on the monitor beside the vitals. The short
forms were previously maintained in the builder, which meant they were invisible to a
reviewer and a second case would have had none. Read the short labels: the resident sees
them for the whole run.

**Renames.** "Place two large-bore peripheral IVs" is now "Insert IV", matching the catalog.
CPAP is now "Positive pressure ventilation (BiPAP/CPAP)". That resolved the display half of
the shadowing problem in section 12 at the time; the scoring half is resolved too now that
the two actions have been merged into one.

**Stabilization ordering.** The ungrouped stabilization entries (monitor, IV, compressions)
now sort to the top of that tab, ahead of vascular access, oxygen, intubation and the rest.
The Stabilization tab itself now sits directly after Exam, so the tab order is Patient,
History, Exam, Stabilization, Investigations, Interventions, Consults, Handoff. That puts the
tab a resident reaches for first in a sick patient next to the assessment that tells them the
patient is sick, rather than behind the investigations menu.

**Each filter box has a clear button.** It appears only when the box has text and is
absolutely positioned inside the input, so showing and hiding it does not move the toolbar or
the grid beneath. Clearing returns focus to the box. Filters remain per tab: clearing one does
not touch another, and a selection made while a filter was active survives the filter being
cleared.

**The suggested opening questions are gone** from the History tab. A resident now types a
question with no prompting, which is a better test of history-taking and a worse experience for
anyone who has not used the interface before. It also removes the only path that guaranteed a
clean match, so the matcher's error rate in section 11 now applies to every question asked.

---

## 17. The splash screen, difficulty modes and the collapsed menu

Three interface changes since the last revision. Two of them change what the case
measures, so they need your view rather than just your notice.

**The splash screen sets the scene before the clock starts.** It shows the care setting,
the working title, the chief complaint in the patient's words, how he reached you and the
EMS handover, and the provenance warning. The clock reads zero until Begin, so reading
the scene is not timed.

Care setting is authored in this case file rather than fixed by the deployment, and this
case declares a quaternary Level 1 centre with cardiology, critical care and
interventional cardiology in house at all hours. **Check that this is the setting you
want**, because the correct disposition depends on it. If the teaching point were about
managing this patient where the nearest cardiology service is two hours away, both the
disposition answer and several of the alternatives would change.

**Two difficulty modes.** Easy prompts at your authored deadlines. Hard waits three times
as long: 135 seconds for non-invasive ventilation rather than 45, 225 for the nitrate
rather than 75. It scales prompt deadlines, escalations and follow-up prompts and nothing
else, so turnaround, transitions and tags are identical and the medicine is the same
either way.

**What this asks of your prompt text.** In hard mode many runs will end before a prompt
ever fires, which is the intent: it is the honest test of whether the resident would have
acted unaided, and easy mode cannot answer that question because the prompt usually
arrives before the resident has finished thinking. But it also means the prompts have to
read sensibly arriving very late. Re-read the eight prompts against the idea that the
patient has now been in severe respiratory distress for over two minutes with nothing
done. Section 9.5 forbids implying a trajectory, and a prompt that was fine at 45 seconds
may read as implying one at 135.

**The Interventions tab now renders collapsed.** 131 entries across 15 groups was
unreadable as a flat list. Group headers show the name, the entry count and the number
selected, and open on click. This is presentation only and changes nothing about what is
orderable or what anything does.

One consequence worth knowing: a resident must now open a category before they can see
what is in it, which makes reaching for a drug slightly more deliberate. For the traps in
this case that probably helps, since morphine and the bronchodilator are no longer sitting
in the resident's peripheral vision. Whether that is a fair change or one that hides the
temptation the case is built around is a judgement I cannot make for you.

---

## 18. Catalog additions and the interface clean-up

### 18.1 The two blocking gaps are closed

**Stop actions.** Rather than adding a single stop button for nitroglycerin, the generator now
derives one stop action for **every persistent infusion**, twenty in all. A single hand-added
entry would have left the same defect waiting for the next case that needs a drip withdrawn.
Verified: after intubation, stopping the nitrate and starting a pressor reaches
`intubated_stabilized`, so the deterioration branch has a working exit for the first time.

**Venous blood gas.** Added with **venous reference intervals rather than the arterial ones**,
which is the error to watch for: a venous pH runs about 0.03 to 0.05 lower and a venous pCO2
about 4 to 6 mmHg higher than arterial, and reporting a venous gas against arterial ranges makes
a normal gas look acidotic. **It reports no pO2**, because a venous pO2 says nothing about
oxygenation and printing one invites it to be read as though it did. Check both decisions.

**Critical care consultant** added; seventeen consultants.

**Catalog prerequisite grammar** fixed on all three defective conditions. They parse now, which
matters for the next case rather than for this one: they gate intubation, pacing and CSF studies,
none of which this case relied on.

### 18.2 The crystalloid change, and a new mechanism

The generic crystalloid bolus is gone, replaced by four explicit entries: normal saline and
lactated Ringer's, at 1 L and 500 mL. That is closer to the choice a resident actually makes, and
it also removes a hiding place: a single generic entry concealed which agent and which volume
were being given.

It created a problem worth understanding. **Four entries means a harmful tag on one leaves three
unguarded routes to the same harm.** The catalog now declares `equivalence_groups`, and the
binding map has `also_covers_group`, so one case action claims all four. Each keeps its own button
and its own catalog name; only the tag, halt reason and debrief note are shared. **Verified: all
four halt the case.**

The same mechanism is what a future case should use when crystalloid is *indicated* rather than
harmful, so that any of the four counts as correct.

**Furosemide** carries its dose in the catalog name, so the case no longer overrides it.
**Bumetanide is gone** from both the catalog and the case, including from the diuretic follow-up
that used to trigger on either drug.

### 18.3 What changed in the interface

**A running chart sits on the right and is always visible.** It carries results as they return,
exam findings, consultant replies, what the patient said, and every action performed or blocked,
in the order the resident learned them. Results enter the chart at the moment they **result**, not
when they were ordered. Abnormal components render red inline.

This changes what the case can measure. Previously a result could be returned and never read, and
both the handoff warning and the debrief reported that as a finding. **With a chart that is always
on screen there is no unread state**, so the "mark reviewed" control, the unread warnings and the
`view` log entry have all been removed. What can still be missed is a study that never came back,
and that is still reported.

**The debrief now opens with the medicine.** Order is: the harmful action if there was one, then
critical actions with the misses folded in, then also-worth-doing, then the summary and score.
A resident reading top to bottom meets the case before the scoreboard.

**Each teaching note is collapsed behind a "Why" expander** next to its action. Your notes are the
best content in this case and also the longest; printed in full for every action the section became
a wall of text that invites skimming, and the list of what was done and missed stopped being
readable at a glance. Nothing is lost, but **the note now has to be worth opening on the strength
of the action name alone**, which is worth a pass through them with that in mind.

**Two debrief sections were removed:** the timeline of the run, which duplicated the running chart
that is on screen throughout play, and the route through the phase graph. The route map showed the
case's internal structure rather than anything the resident chose; they chose actions, and the
actions are already listed. Both were cheap to generate, which is not the same as worth reading. If
you want either back, say so: the data for both is still in the fold.

**Investigations and Stabilization now collapse into categories** like Interventions, with larger
category headings. Exams and Consults stay flat, since each is a single group where an accordion
would add a click and hide nothing. A selection made inside one group survives collapsing it, so an
order set can still be assembled across several groups before submitting.

**Editorial content is gone from the interface.** The physician-review banner, the prototype notes
on appearance and action surface, the sound assumption, the matched-topic line under each patient
reply, the catalog-default annotations on findings, and the closing provenance section. The heart
rate and frequency readout beside the sound control is gone. The splash lost the care-setting
detail and the difficulty explainer.

**This is a presentation decision with a cost, and it is worth stating plainly.** Those notes were
the interface telling a reader which content was unverified and which findings came from a default
rather than from the case. Removing them makes the tool look finished. It is not: nothing in this
case has been signed off, and the diagnosis catalog remains unreviewed. That information now lives
only in this packet and in the case file's provenance block, so **the packet is the only place a
reader will encounter it.**

Actions with no catalog entry are still shown in their own labelled group, as requested.


---

## Addendum: what changed when the engine moved to v0.6

This case authors no time-guarded transitions and is unaffected by the mechanism. Three
things did change for it, none clinical.

**Three phantom entries left its omissions list.** `also_covers` was handing every covered
crystalloid entry the covering action's critical expectation as well as its tag, so the
debrief counted four expected actions where the resident performs one act. Covered entries
now inherit the tag, the halt reason and the debrief note only.

**Its NIV actions were consolidated**, recorded in section 12 above and in
`consolidate_niv.py`.

**Its scenario list grew from ten to thirteen**, and one of the original ten had been
passing for the wrong reason. Two of the three new ones walk crystalloid siblings; the
third walks the last.

Nothing in the clinical content of this case was reviewed or changed as part of that work,
so the sign-off checklist stands exactly where it did.
