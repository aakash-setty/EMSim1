# Case Authoring Requirements

**Version 0.3 | Aligned to System Design v0.4**

What must be provided to produce one complete, playable, clinically valid case.

This document has two audiences. The **case author** is an emergency physician who supplies clinical ground truth and reviews everything. The **drafting AI** expands that ground truth into the full case file. Sections marked AUTHOR-ONLY cannot be delegated. Sections marked AI-DRAFTABLE can be generated and then reviewed.

**Changed from v0.2.** The global catalogs now exist, and a case is written against them rather than alongside them. Concretely: actions are named by catalog id; the exam maneuver set is closed at 14 with a fixed routing map; results are structured payloads with abnormal flags rather than prose; catalog prerequisites merge with case prerequisites rather than being replaced; there is a fifth clinical tag, `discouraged`; a case now supplies its care setting and arrival mode for the splash screen; and section 16 gives the end-to-end authoring workflow, which did not previously exist as a sequence.

**A case is now a folder, not a file.** Everything you author for one case lives in `cases/<PREFIX>/` with a shared prefix, and every tool takes that folder as its argument. `python3 engine/new_case.py <PREFIX>` scaffolds it, including a copy of the seed template and the exam routing map. See section 16 and the repository README.

If you are authoring your first case, read section 0, then jump to **section 16** and follow it. The rest of this document is the reference it points into.

---

## 0. How the case runs

Understanding the runtime is necessary to author for it. Ten facts govern everything below.

1. **The case moves through phases.** A phase is a clinically distinct patient status. Interventions move the patient between phases.
2. **A clock runs, but it does not change the patient.** Time governs when results arrive, when the nurse prompts, and timing feedback in the debrief. There are no time-driven phase transitions and vitals do not drift. An untreated patient does not deteriorate.
3. **Flags are binary and permanent.** An intervention sets a flag. Nothing wears off, and nothing is partial.
4. **Reads never change state.** Exams and interview questions return content based on current state. They do not alter it. Ordering a study does change state, even though it feels like a read.
5. **Every readout is resolved, not stored.** Each thing the resident can see is a *key* owning an ordered list of guarded alternatives. First match wins. The last alternative is unconditional.
6. **Anything the case does not author returns the catalog default, which is normal.** This is the most dangerous property of the system. See 11.1.
7. **Results freeze at the state in which they were ordered.** A film ordered before intubation does not show a tube.
8. **The resident sees the whole catalog, not your case's actions.** Every drug, study and maneuver in the product is on the menu whether or not you referenced it.
9. **Orders on the action tabs are selected then submitted as a batch.** Exams, interview questions and consults fire immediately.
10. **The case ends** when the resident confirms a handoff, when a harmful action halts it, or when the resident ends it early.

---

## 1. Educational framing

This is a teaching tool, not a certification instrument. Three consequences for authoring.

**Write prompts and messages to help.** The nurse exists to teach. A prompt that names the needed intervention is doing its job. A blocked-action message that states the missing prerequisite is doing its job. Do not write them to be cryptic.

**Write debrief notes that teach, not that judge.** Every note should leave the learner knowing something they did not know. "Wrong drug" is useless. State what the drug does, why it was wrong here, and what was indicated instead.

**Explain the wrong answers.** Incorrect handoff dispositions and diagnoses need explanations, because a learner who picks one has revealed a specific misunderstanding worth correcting.

**What does not change.** Clinical accuracy requirements are higher, not lower, than they would be for an assessment tool. There is no examiner downstream to catch an error, and the learner will believe what this tool teaches. Every constraint below about physician review and AI-invented facts holds without modification.

---

## 2. Division of labor

| Component | Who supplies it |
|---|---|
| Diagnosis, phases, critical actions, harmful actions | AUTHOR-ONLY |
| Clinical tags on every action | AUTHOR-ONLY |
| Harm halt reasons | AUTHOR-ONLY |
| Vital sign values per phase | AUTHOR-ONLY |
| Abnormal exam findings and their resolution | AUTHOR-ONLY |
| Abnormal lab and imaging values | AUTHOR-ONLY |
| **The abnormal flag on every authored component** | AUTHOR-ONLY |
| **Which reference interval applies, where the catalog has none** | AUTHOR-ONLY |
| Consultant clinical advice content | AUTHOR-ONLY |
| Interview ground truth facts and pertinent negatives | AUTHOR-ONLY |
| Case-specific prerequisites and any catalog overrides | AUTHOR-ONLY |
| Follow-up requirements and whether they apply here | AUTHOR-ONLY |
| Which critical actions are time-sensitive, and their urgency | AUTHOR-ONLY |
| Correct disposition and diagnosis | AUTHOR-ONLY |
| **Every mapped row in the catalog binding** | AUTHOR-ONLY |
| Normal exam findings, normal labs | AI-DRAFTABLE |
| Paraphrase variants for interview matching | AI-DRAFTABLE |
| Patient-voice phrasing of authored facts | AI-DRAFTABLE |
| Nurse narration and prompt phrasing | AI-DRAFTABLE |
| Debrief explanatory text | AI-DRAFTABLE |
| Condition logic scaffolding | AI-DRAFTABLE |
| Routing a finding to a maneuver, where the map is unambiguous | AI-DRAFTABLE |

The dividing line: anything a resident could act on clinically is author-only. Anything that is phrasing, formatting, or a restatement of an author-supplied fact is AI-draftable.

**The AI must never invent a clinical fact.** Not a symptom, not a finding, not a lab value, not a consultant recommendation, not a prerequisite, not a deadline. If the author has not specified it, the correct AI output is a normal finding, an explicit denial, or a flag that the author must supply it. This is the single most important constraint in this document, because an invented symptom changes the correct workup and silently makes the case wrong.

**Three additions to that rule in v0.3.**

*A mapped binding row is a clinical judgement.* Deciding that a case's high-sensitivity troponin I binds to the catalog's troponin T entry is not an id lookup, it is a claim that the two are interchangeable for this case, and here it is false. The AI proposes the mapping and records its reasoning; the author accepts or rejects each row.

*An abnormal flag is a clinical judgement.* The AI can carry a flag across from prose that already said "(high)". It cannot decide that a value is abnormal.

*A reference interval is a clinical fact.* Where the catalog supplies one, use it. Where it does not, the author supplies it, and the payload carries a `verify` note until they do.

---

## 3. The author's seed

Supplied before any AI drafting begins. For a case the author knows well this should take about an hour.

**3.1 Case identity**
- Working title and chief complaint as the patient would state it
- Final diagnosis, **as a diagnosis catalog id**
- Three to six learning objectives
- Target level (intern, junior resident, senior resident)

**3.2 Patient and setting**
- Age, sex, weight, relevant background
- Presenting vital signs
- Presenting appearance in one or two sentences
- **How the patient reached you**: ambulance, walk-in, transfer, police, and the handover as it would be given
- **The care setting**, if it is not a quaternary Level 1 centre with everything available. This is not scene-setting: the correct disposition depends on it, and a case written for a hospital with no cardiology on site has a different right answer

**3.3 Phases (three to six clinical phases, plus terminals)**
For each: a short label, a one-line clinical description, and the vital signs in that phase. At least one must be a resolution phase. At least one should be a deterioration phase if deterioration is clinically plausible.

The count refers to clinical phases. The two terminal phases (halted, complete) are structural and do not count against it.

**3.4 The action spine**
- **Critical actions**: what must happen for the patient to do well, in which phase each becomes critical, and which are time-sensitive
- **Harmful actions**: what would injure or kill this patient, with a one-line clinical reason for each
- **Discouraged actions**: wrong here but not lethal
- **Recommended actions**: good practice but not case-determining
- **Traps**: plausible-looking actions that are wrong here, and why. Most traps are `discouraged`; a few are `harmful`

For each harmful and discouraged action, name **every route to it**. If a fluid bolus is harmful, say so for saline and for Ringer's and for each volume; if a bronchodilator is a trap, say so for the combination nebuliser and for each agent alone. The catalog often lists as separate entries what a clinician thinks of as one act, and an unbound sibling is an escape hatch from the lesson.

**Where the catalog declares an equivalence group, use it.** `equivalence_groups` names sets the catalog considers interchangeable, such as the four crystalloid boluses. Binding one case action to a group with `also_covers_group` applies its tag, halt reason and debrief note to every member, so the coverage cannot drift as the catalog grows. Each entry keeps its own button and its own name; only the case-specific fields are shared. Use it wherever the case is making a claim about **the act** rather than about one particular agent, in either direction: a harmful tag that must not be escapable, or a required action that any member should satisfy.

**3.5 Sequencing**
- Any action in this case that must not be performed before something else (prerequisites)
- Any action that creates an obligation afterwards (follow-ups), and whether it applies here
- Any standard catalog prerequisite that should be waived in this case, and why

**3.6 Key findings**
The abnormal exam findings, abnormal labs, and abnormal imaging that define this case, plus how each changes after successful treatment.

For each abnormal value give the number, the units, the reference interval you are working to, and confirm it is abnormal. For each exam finding, name the finding; section 11.2 will tell you which of the 14 maneuvers owns it.

**3.7 Interview ground truth**
The history as a list of facts, with pertinent negatives listed explicitly. See section 10.

**3.8 Disposition**
The correct level of care and the correct diagnosis, plus the plausible wrong answers for each and why each is wrong. Diagnoses are catalog ids.

Everything else in this document is expansion of the seed.

---

## 4. The condition language

One language is used everywhere a condition appears: content rules, clinical tags, prerequisites, follow-up applicability, nurse prompts, and phase transitions. Five predicates, combined with AND, OR, NOT.

| Predicate | Meaning |
|---|---|
| `phase is X` | The case is currently in phase X |
| `flag F set` | A completed action set flag F |
| `study S ordered` | S has been ordered; the result may still be pending |
| `study S resulted` | S has been ordered and the result has arrived |
| `action A taken` | Action A was performed |

No arithmetic. No comparisons. No nesting beyond one level of grouping.

**Write the trailing keyword.** `flag F set`, not `flag F`. `study S ordered`, not `study S`. The short form reads correctly to a human and is unparseable to the engine. An earlier version of this document used the short form in its own worked example, and that example propagated into shipped catalog data.

**`ordered` versus `resulted`.** These differ because studies take time to return: labs 5 seconds, imaging 10, ECG 10, bedside 0. Use `resulted` for any content that references the finding itself. Use `ordered` for content acknowledging that something is on its way.

**`flag` versus `action taken`.** Every state-changing action sets a flag, so for those two the predicates are equivalent. Use `flag`. Reserve `action taken` for observational actions, for example a consultant who responds differently depending on whether the abdomen was examined.

**There is no time predicate.** Timing is expressed only in the deadline fields on prompts and follow-ups, never in conditions. Requests to add a time predicate should be refused by the drafting AI and escalated, because time-conditional content everywhere would make the per-key review matrix unenumerable and the case unreviewable.

**Rule ordering rule of thumb: phase rules before flag rules.** Flags are permanent, so a flag set in an early phase is still set in a later one. A key that tests `flag on_niv set` above `phase is post_intubation_hypotension` returns the improved value to a patient who has since collapsed. Whenever both appear in one list, the phase rules go first. This is the single most common way a rule list is correct for the situations the author was thinking about and wrong for one they were not.

---

## 5. Phases and transitions

Each phase requires:

- **id** and **label** (label appears in the debrief only)
- **clinical description**, one line, for author review
- **vital signs**: heart rate, systolic and diastolic blood pressure, respiratory rate, oxygen saturation, temperature
- **appearance values**: see section 6
- **transition rules**: an ordered list, each with a condition and a destination phase. Evaluated after every state-changing action. First match wins.
- **terminal flag**: whether the case ends here

Transition conditions should gate on the critical actions of that phase, so the case advances because the resident did the right things.

Harmful actions bypass transition rules entirely and move directly to a terminal halted phase carrying that action's halt reason.

**Note on prompt deadlines:** they are measured from phase entry. When a phase changes, outstanding prompts for the previous phase are cancelled and new deadlines begin. Authors should therefore set deadlines relative to the start of the phase the action belongs to, not relative to case start.

**Transitions do not cascade within one action.** If the resident satisfies a later phase's transition before entering it, the phase machine advances one step per state-changing action, so the next action advances two phases at once. A phase entered and left in the same step issues no prompts. Check your simulator scenarios for orderings that produce this.

**Every deterioration branch needs a reachable exit.** If entering a phase requires an action, leaving it requires an action too, and that action must exist in the catalog. Confirm the exit exists before authoring the branch. Stopping an infusion is a case in point: every persistent infusion has a matching stop action, but stopping is a separate step rather than a toggle, so the case must author it as its own action and gate the rescue transition on the flag it sets.

**Requirement:** every phase must be reachable, and every non-terminal phase must have at least one satisfiable transition.

---

## 6. Vitals and appearance

Authors supply numbers. Authors do not describe the patient's skin, face, or posture.

Appearance is computed globally from a fixed set of values, so every case animates without new artwork or new authoring. Supply these per phase:

| Value | Range | Drives |
|---|---|---|
| Oxygen saturation | 0-100 | Cyanosis, **and the audio pitch** |
| Systolic blood pressure | numeric | Pallor, perfusion |
| Heart rate | numeric | Pallor, perfusion, **and the audio tempo** |
| Distress level | 0-3 | Diaphoresis, facial expression, posture |
| Alertness level | 0-3 (alert, drowsy, obtunded, unresponsive) | Eye state, responsiveness, ability to give history |
| Pupil size | small, normal, large | Pupils |
| Pupil reactivity | reactive, sluggish, fixed | Pupils |

If a case needs an appearance feature outside this list, that is a request to extend the global renderer. Escalate rather than authoring a one-off description.

**Saturation and heart rate are now audible.** The heartbeat runs at the authored rate and its pitch falls with the authored saturation. A saturation chosen loosely because it was "about right" will be heard, not just read. Choose the numbers as deliberately as you would for the monitor.

**Consequence to accept:** vitals are static within a phase and change at phase boundaries. Small cosmetic variance is added by the renderer so the monitor does not look frozen, but that variance carries no clinical meaning and no rule reads it.

---

## 7. Actions and clinical tags

### 7.1 Actions come from the catalog and only from the catalog

The global catalog defines every drug, exam maneuver, lab, imaging study, ECG, consultant, stabilization task and procedure across the product, with names, tab placement, turnaround class, narration templates, default prerequisites and default results. It holds no case-specific clinical judgment.

**The resident sees the whole catalog.** Actions your case never mentions are still on the menu, are inert and neutral, and return the catalog default. This is deliberate: a menu showing only the relevant actions gives away the answer.

**A case cannot add an entry.** If the action you need is not there, that is a catalog change request. Authoring around it produces content no learner can reach.

A case references catalog entries and supplies only what is case-specific:

- **catalog id** (see 7.2)
- **clinical tag**: an ordered rule list (see 7.3)
- **display name override**, only where the catalog name would be wrong or ambiguous here
- **prerequisite additions or waivers** (section 8)
- **follow-ups triggered**, if any (section 8)
- **flags set**
- **prompt deadline and text**, for time-sensitive critical actions (section 9)
- **halt reason**, required if the tag can ever evaluate to harmful: one sentence stating what was done, plus the physiological consequence
- **debrief note**: why this action is right or wrong here, the teaching point, and optionally a reference

Transitions live on phases, not on actions. Section 5 is authoritative.

### 7.2 Binding to the catalog

If you write the case in catalog ids, nothing further is needed. If you write it in your own ids, a binding file records one row per case action with a status of `exact`, `mapped` or `unmatched`.

**Every `mapped` row is a clinical judgement and needs your signature.** Look particularly for:

- **Assay mismatches.** A numeric high-sensitivity troponin I does not transfer to a qualitative troponin T entry. A BNP does not transfer to a pro-BNP entry. Same analyte family, different reference intervals, different numbers.
- **Route and formulation splits.** A bolus and an infusion are different catalog entries and often different clinical acts.
- **Composite actions.** A combined lung and cardiac ultrasound may be two catalog entries. A combination nebuliser may be two drugs. Bind to both or the unbound half is unreachable.
- **Collapsed entries.** Where the catalog collapses two acts you score separately, the interface can offer only one button and the second is unreachable. Decide which one it should be.

**`unmatched` is an error, not a warning.** Fix it by requesting the catalog entry or by changing the case. A case that cannot bind cannot run.

### 7.3 Clinical tags

**Tags must be rule lists, not single values.** The same drug can be indicated in one phase and harmful in another. A tag is an ordered list of conditions and tag values, first match wins, unconditional default last.

```json
"tag": [
  { "when": "phase is post_intubation_hypotension OR phase is intubated_stabilized",
    "value": "harmful" },
  { "when": "phase is presentation", "value": "critical" },
  { "when": null, "value": "recommended" }
]
```

The five values:

| Value | Meaning |
|---|---|
| `critical` | The patient does badly without it. Omission costs |
| `recommended` | Good practice, not case-determining |
| `discouraged` | Wrong here but not lethal. Minor cost, explained in the debrief |
| `harmful` | Halts the case. Requires a halt reason |
| `neutral` | No effect |

**Use `discouraged` for traps.** Before v0.3 a trap that was wrong but survivable could only be neutral, which meant it carried no weight and taught only through a note the learner might not read. Morphine in acute pulmonary oedema, a bronchodilator for cardiac asthma, unindicated steroids or antibiotics, an unnecessary CT: these are `discouraged`.

**Reserve `harmful` for genuine lethality**, and be honest about the strength of the evidence. Halting the case on an action teaches the strongest possible claim. If the evidence is observational and confounded, `discouraged` with a good note is the honest tag.

**Check the fallthrough in every phase.** The commonest tag defect is a rule list that is right for the phases the author was thinking about and wrong for one they were not. A nitrate tagged harmful only in the hypotensive phase falls through to "recommended" in the vasopressor-dependent phase that follows it. The review matrix exists to catch this; read it.

Actions not referenced by the case inherit a neutral tag and a generic debrief note. Tag every plausible trap.

**Labs, imaging, and ECG are state-changing**, because ordering them changes what consultants say and what other rules see.

---

## 8. Prerequisites and follow-ups

These are different mechanisms. Conflating them is the most consequential authoring error available.

### 8.1 Prerequisites gate an action

A prerequisite is a condition that **must already be true**. Failing it blocks the action, shows a message, logs the attempt, and changes nothing.

**Write the requirement, not the block.** `flag iv_access set` means the line must be in. `NOT flag iv_access set` means the opposite and will block every action that should have been allowed. Both parse; only one is right.

Each prerequisite has a **condition** and a **failure message** written in the nurse's voice, stating what must happen first.

| Action | Condition | Failure message |
|---|---|---|
| Intubation | `flag sedation_given set AND flag paralytic_given set` | "He isn't sedated or paralyzed yet. We need induction and a paralytic before we tube him." |
| Transcutaneous pacing | `flag pacing_pads_placed set` | "Pads aren't on him yet. Want me to get them on?" |
| CSF studies | `flag lumbar_puncture_performed set` | "We haven't done the LP, so there's no CSF to send." |
| Any IV drug | `flag iv_access set OR flag central_access set OR flag io_access set` | "He doesn't have a line yet. Do you want me to get IV access first?" |

**Most prerequisites belong in the catalog, not the case.** Intubation requires sedation and paralysis in almost every case, so authoring it per case is duplicated work and invites inconsistency.

**Case prerequisites are additive.** A prerequisite you write is added to the catalog defaults, not substituted for them. If you want a catalog default gone, waive it explicitly through `prerequisite_overrides`, naming what is waived and giving the clinical reason. A crash airway in a patient already in arrest does not require sedation and paralysis; say so.

**Blocked actions stay visible and selectable, and unannotated.** Hiding or greying out teaches nothing. Neither does printing "needs a line" on the button: that turns a lesson into a label and makes gated actions visibly different from ungated ones. Let the resident attempt it and read why it failed.

### 8.2 Follow-ups create an obligation afterwards

A follow-up is triggered by an action and becomes due after it. It cannot gate the triggering action, because the triggering action must happen first.

Post-intubation analgesia and sedation are the canonical example. They cannot be prerequisites of intubation. They are enforced by nurse prompting and surfaced as omissions in the debrief.

Each follow-up requires:
- **condition** determining whether it applies in this case, since not every intubated patient needs the same follow-up
- **deadline** measured from the triggering action
- **nurse prompt text**
- **debrief note**
- **`satisfied_by`**: every catalog action that discharges the obligation

**List every satisfier.** If sedation may be propofol or ketamine and you name only propofol, a resident who chose ketamine is told they left a paralysed patient unsedated.

### 8.3 Validator obligations

- Every prerequisite flag is settable by some reachable action
- No circular prerequisite chains
- Every prerequisite has a failure message
- Every follow-up has a condition, deadline, prompt, and debrief note
- Every `satisfied_by` id exists in the catalog

---

## 9. The nurse

The nurse sits at top center and has four functions. Three are largely automatic; one needs authoring.

**9.1 Action narration.** Generated from the catalog template, for example "Giving {dose} of {name}." Supply a case-specific override only where the standard line would be wrong or confusing. Exams and interview questions are not narrated.

**9.2 Result announcements.** Automatic. No authoring.

**9.3 Blocked-action feedback.** Uses the prerequisite failure message from section 8.1.

**9.4 Critical action prompts.** This is the authored part.

For each time-sensitive critical action, supply:
- **deadline**, measured from entry to the phase in which the action is critical
- **prompt text**
- optionally a **second deadline and escalated prompt**
- optionally a **guard condition**, if the prompt should only appear in certain circumstances

Not every critical action needs a prompt. Prompt for the ones where delay carries real clinical cost.

### 9.5 Two hard constraints on prompt text

**Prompts must not imply a trajectory.** The patient does not deteriorate, so a prompt saying the patient is getting worse contradicts a monitor showing static vitals. Describe the current state or express concern about inaction.

- Acceptable: "He's still working hard to breathe. Do you want to do anything about the airway?"
- Acceptable: "His sat is sitting at 87 on six litres."
- Not acceptable: "He's crashing." / "His pressure is dropping."

No validator can catch this. It is a review checklist item, and it is the constraint most likely to be violated without anyone noticing, because the failure is a contradiction between the text and the monitor rather than an error in either.

**Prompts must be helpful.** This is a teaching tool. A prompted action counts as done and is not penalized; it is only noted in the debrief so the learner can see where they needed help. Write prompts that would actually rescue a stuck learner.

### 9.6 On deadline values

Author deadlines in seconds, but expect global recalibration once the pacing is tuned. Prioritize getting the **relative** urgency right between actions in a case over any absolute number.

### 9.7 Difficulty modes change when prompts fire

The resident chooses easy or hard on the splash screen. Hard multiplies every prompt deadline, escalation and follow-up deadline by three. It changes nothing else: turnaround, transitions and tags are identical, so the medicine is the same either way.

**Author for easy mode.** Get the relative urgency right at the authored deadlines, per 9.6. Hard mode is derived from those numbers and needs no separate authoring.

**What hard mode is for.** In easy mode the prompt often arrives before the resident has finished thinking, so the prompted-versus-independent report in the debrief measures reading speed as much as knowledge. Hard mode is the honest version of that question, and it means many runs will end with the prompt never firing at all. Write prompts that still make sense arriving late.

### 9.8 Prompts now make a sound

A trill plays with each nurse prompt. This is worth knowing when writing them, because the tone tells the resident that a prompt has fired before they read the words, which is close to telling them they have missed something. Nothing about the text changes, but the prompt is louder in every sense than it was in v0.2, so prompt for fewer things and mean it.

---

## 10. The interview

A fully authored question-and-answer bank with intent matching. No model generates clinical content. A model may be used only to match free text to an authored topic and optionally to phrase an authored answer in the patient's voice.

### 10.1 Topics

- **topic id**
- **canonical question**
- **paraphrase variants**, ten to twenty per topic (AI-DRAFTABLE, author spot-checks)
- **answer**: an ordered rule list using the section 4 condition language, unconditional default last

```json
{
  "topic": "nausea",
  "canonical": "Are you feeling nauseated?",
  "variants": ["Do you feel sick?", "Any nausea?", "Do you feel like throwing up?"],
  "answer": [
    { "when": "flag nausea_treated set", "value": "The sick feeling has settled down a lot." },
    { "when": null, "value": "Yes, really nauseated. I keep feeling like I'm going to be sick." }
  ]
}
```

**Write toward twenty variants, not ten.** Ten is the floor and the measured error rate at the floor is not comfortable. See 10.6.

### 10.2 Required topic coverage

At minimum: onset, timing and progression, character, location, radiation, severity, aggravating and relieving factors, associated symptoms (each as its own topic), past medical history, past surgical history, current medications, allergies, social history including substance use, family history where relevant, last oral intake, and pregnancy status where applicable.

Consider also code status and goals of care where the presentation makes them live.

### 10.3 Three distinct response types

Mandatory, and a common failure point.

1. **In-scope positive**: the patient has this and reports it.
2. **In-scope negative**: the patient does not have this and denies it. Pertinent negatives must be authored as their own topics with denial answers. A resident asking about chest pain in an abdominal case should hear a clear denial, not a fallback.
3. **Out-of-scope**: no topic matched. The patient gives a non-committal response revealing nothing.

A learner cannot distinguish "the patient denies it" from "the system did not understand me" if a pertinent negative falls through to the fallback, and those are clinically opposite. Authors must list the pertinent negatives explicitly. The drafting AI must not decide on its own that something is a negative rather than out of scope.

### 10.4 Hard constraints on patient answers

- The patient never states or implies the diagnosis.
- The patient never reports information they could not know, including any lab value, imaging result, or vital sign number.
- The patient uses lay language, not clinical terminology.
- Answers change only through the authored condition rules, never through the matcher.

**The line on chronic history.** A patient may describe a known past diagnosis in lay terms, because it is his history and he knows it. "My heart was damaged by the attack and it doesn't pump properly" is acceptable. Attributing today's episode to it is not, and naming the current problem is not. Where a case sits close to this line, flag it for the reviewer rather than deciding silently.

### 10.5 Speech and alertness gating

Two separate gates, and v0.2 only described one.

**Alertness.** Where the alertness level is obtunded or unresponsive, the patient cannot give a history. Author this once as a global rule preceding all topic rules.

There is no alertness predicate in the condition language, so the global rule must enumerate the phases whose alertness is 2 or 3. That means it breaks silently if a phase is added later. The validator checks that every such phase is covered; do not remove that check.

**Speech limited by distress.** Much more common than reduced alertness, and not covered by a global rule, because a patient in severe respiratory distress can answer but only in short bursts. Suppressing the content globally would delete the answer; the answer has to be the same fact, shorter.

This means **every topic needs a second answer for the distressed phase**, which roughly doubles interview authoring effort for any respiratory or shocked case. Budget for it.

### 10.6 Matching failure

Specify the out-of-scope fallback in this patient's voice.

**Matching accuracy is the highest technical risk in the case system**, because a mismatch delivers a clinically wrong answer with full confidence, and unlike a fallthrough it is invisible to the learner.

Measured on one case with 34 topics at ten variants each, using inverse-document-frequency weighted matching with a rare-token override: **23 of 25 held-out phrasings matched correctly, 1 matched the wrong topic, 1 fell through. Out-of-scope questions were misrouted 2 times in 5.** A plain bag-of-words matcher on the same bank scored 18 of 25 with 5 wrong topics, two of them clinically opposite: "any calf pain" matched the chest pain topic, and "does anything make it better" matched aggravating factors.

Two things follow.

**The number to watch is the wrong-topic rate on topics whose answers change management**, not overall accuracy. A fallthrough is visible to the learner; a wrong topic is not. Expand variants first on the topics where a wrong answer changes the workup.

**Measure it, and measure the shipped matcher.** Each case pack should carry a `<PREFIX>-matcher-eval.js` holding held-out phrasings that appear in no variant list, and it should extract the matcher from the built prototype rather than reimplementing it. A second copy of the matching logic drifts, and then the evaluation reports on a matcher nobody runs. Do not tune the matcher against the held-out set and then quote the result; that measures memorisation rather than coverage.

**Out-of-scope handling is the weakest part.** Two in five unrelated questions receive a confident, specific, wrong answer. Until that improves, assume any question your case does not cover may be answered as though it were a different question.

---

## 11. Content rules for exam, labs, imaging and consultants

All use the same structure: a key owning an ordered rule list, unconditional default last. What changed in v0.3 is the shape of the value.

### 11.1 The default rule, and why it is dangerous

Resolution order is: **your case content, then the catalog default, then an error.**

The catalog default is normal. So a study you forget to author does not fail; it returns a normal result, confidently, and teaches the resident the wrong thing with no error raised anywhere.

Three defences, all of which should be used:

1. The validator warns when a study is named in a condition or tagged critical but has no authored result, naming the default that will be served instead.
2. The debrief lists everything answered by a default rather than by the case, so the omission is visible after the fact.
3. Section 14.3 asks you to check it directly.

None of the three catches a study you never thought about. That one is on the review.

### 11.2 Exams: a closed set of 14, and a routing map

The catalog defines exactly 14 maneuvers and no more:

`exam_airway`, `exam_breath`, `exam_circ`, `exam_heent`, `exam_neck`, `exam_card`, `exam_pulm`, `exam_abd`, `exam_gu`, `exam_back`, `exam_msk`, `exam_skin`, `exam_neuro`, `exam_psych`

**You cannot add a maneuver.** A case that authors "hepatojugular reflux" or "general appearance" as its own key produces findings no resident can reach.

Because 14 maneuvers cannot cover every region, the catalog supplies **`exam_finding_routing`**, a fixed map for findings that do not fit cleanly. Follow it even where you would have chosen differently. Some placements will feel wrong:

| Finding | Owned by |
|---|---|
| Jugular venous distension, tracheal position | `exam_neck` |
| **Peripheral or pedal oedema** | `exam_card` |
| Capillary refill, skin temperature, pulse quality | `exam_circ` |
| Extremity findings, distal neurovascular status | `exam_msk` |
| Accessory muscle use, work of breathing | `exam_breath` |
| Lung auscultation | `exam_pulm` |
| Level of consciousness and GCS | `exam_neuro` |
| Agitation, cooperativeness, thought content | `exam_psych` |
| Rash, wounds, cellulitis, diaphoresis | `exam_skin` |

The map exists so that a resident learns where to look rather than learning that the tool is arbitrary. Findings the map sends to "no available maneuver" cannot be examined for and must not be a case's teaching point.

**Where a maneuver absorbs a finding that used to be its own act**, put the teaching note there too. A hepatojugular reflux folded into the neck exam should still teach the hepatojugular reflux.

Author only maneuvers whose findings are abnormal or change with treatment. The rest inherit the catalog default. Exams may be repeated freely and return current state each time.

### 11.3 The general status line

A short line above the maneuvers. **Not clickable, so the resident cannot skip it**, which makes it the one exam finding everyone sees.

Author it per phase for any patient who is not "No acute distress. GCS 15." A case that forgets this key displays that reassuring default above a comatose neurological exam. The validator requires the key to exist.

Keep it short and keep it consistent with the neurological exam and the appearance values, since all three describe the same patient.

### 11.4 Labs, imaging and ECG: structured payloads

Author only abnormal values and any value that trends with treatment. Everything else inherits the catalog default.

Results are structured, not prose:

```json
{"kind": "panel",
 "abnormal": true,
 "components": [
   {"label": "Sodium", "value": "133", "unit": "mEq/L",
    "reference_range": "135-145", "abnormal": true},
   {"label": "Potassium", "value": "4.4", "unit": "mEq/L",
    "reference_range": "3.5-5.0", "abnormal": false}],
 "comment": "optional interpretive line"}
```

`kind` is `panel` for multi-analyte results, `value` for single ones, `report` for imaging and ECG narrative.

**You set the abnormal flag; the renderer does not compute it.** Flagged components display distinctly, currently in red. Two reasons the renderer stays out of it: reference intervals are assay- and institution-specific, and the interpretation is often not the number, since a pO2 of 95 is normal on room air and alarming on a non-rebreather.

**This means sign-off is now two things per value**: the number is right, and the flag is right. A value you consider abnormal that carries no flag displays to the learner as normal, and no other check will find it. The validator cross-checks parseable reference intervals against the flags and will tell you where they disagree, but it can only check ranges it can parse.

Where you are not certain of the reference interval, add a `verify` note rather than guessing. Where the catalog has a default for the same analyte, use its interval so the case and the default agree.

A result **freezes at the state in which it was ordered**, not when it arrives. Confirm that any study likely to be repeated has authored values across the phases where it might be drawn. If a case needs a result to reflect post-intervention state, require a repeat order.

**Serial testing cannot be represented.** A repeat study in an unchanged state returns an identical value, so a rising troponin cannot be taught mechanically. Teach it in the debrief note instead; do not fake a delta by gating on an unrelated flag.

### 11.5 Consultants

The most state-dependent key in the case.

- Content referencing a finding must gate on `study S resulted`. A consultant must never discuss imaging that was never obtained, and must not discuss a result that has not come back yet.
- **Author a pending tier.** With a 5 to 10 second turnaround there is a real window in which a study is ordered but not resulted. A consultant asked during that window should acknowledge it.
- Order rules from most specific to least specific.
- Unrelated consultants inherit the global "does not know why they were called" response. Do not author these.
- Where a consult unlocks a disposition or intervention, it sets a flag and is state-changing. **A state-changing consult still returns content**: the two questions are independent.

A workable rule order: deteriorated-phase advice, then definitive advice once the key studies have resulted, then a holding response while they are pending, then a default asking for the workup that has not happened.

**Write the pending tier per study, not per group.** A rule reading "either study ordered" will fire when the ECG has resulted and the troponin was never sent, and the consultant will say both are in the system with nothing back, which is wrong on both counts. Enumerate the states.

---

## 12. Handoff and completion

The case completes when the resident submits a handoff and confirms.

Supply:

- **Correct disposition** and level of care
- **Plausible alternative dispositions**, each with an explanation of why it is wrong here, or why it is defensible with qualification
- **Correct diagnosis, as a diagnosis catalog id**
- **Plausible alternative diagnoses, as catalog ids**, meaning the common misdiagnoses for this presentation, each with an explanation

**Use catalog ids, not labels.** A free-text label that does not appear verbatim in the catalog has to be resolved by fuzzy matching, and a correct answer resolved by fuzzy matching can silently stop matching. The validator errors when an id does not resolve.

**Check that your alternatives exist.** The common misdiagnoses for your presentation are exactly the wrong answers most worth explaining, and if one is missing from the catalog a resident who picks the nearest equivalent gets a generic note instead of your teaching. That is a catalog change request.

Diagnosis is entered by searching the global catalog rather than choosing from a short case-supplied list, because committing to a diagnosis from a wide field is the cognitive task being taught. With several hundred entries most wrong answers will fall outside your authored alternatives and receive a generic note; that is acceptable for the long tail and not for the common ones.

Pending or unviewed results at the moment of handoff are recorded automatically and surfaced in the debrief. No authoring required.

An early-exit option exists for a resident who cannot proceed. It produces a debrief marked incomplete.

---

## 13. Debrief notes

The debrief is the product, so these notes carry most of the teaching load. Every action referenced by the case needs one.

A good note states what the action does, why it was right or wrong **in this case**, and what should have happened instead. Optionally add a reference.

**Each note is collapsed behind its own expander in the debrief**, so length is not the constraint it would be if every note were printed at once. Write the note you would give at the bedside rather than a line the learner will skim. What the expander does constrain is the **first line the learner sees**, which is the action's own display name: the note has to be worth opening on the strength of that name alone.

**Reference verification markers stay in the case file and are stripped from the display.** A note ending "[UNVERIFIED, confirm before release]" is addressed to the reviewing physician, and printing it in a teaching note tells a learner to distrust the sentence they just read. Keep the markers; the interface removes them.

Notes are needed for:
- Every critical, recommended, discouraged and harmful action
- Every trap
- Every follow-up requirement
- Every plausible wrong disposition and diagnosis
- Every prerequisite, so a blocked attempt teaches the sequence rather than just refusing
- Every exam maneuver the case authors

Blocked attempts are surfaced in the debrief but not penalized, since the system already corrected the learner in the moment.

**On references.** They are optional, and an unverified one is worse than none. A plausible-looking citation to a paper that does not say what is claimed will be believed. Mark anything unchecked as unverified in the file and check it before release.

**Be honest about contested evidence.** Where a teaching point rests on evidence that is disputed, say so in the note. A learner who is told the strongest defensible claim and told that the evidence is contested has learned more than one given a clean message that does not survive contact with the literature.

---

## 14. Completeness and review

### 14.1 Structural requirements the validator enforces

**Case structure**
- Every content key ends in an unconditional default
- Every referenced action, flag, study, and phase exists
- Every phase is reachable; every non-terminal phase has a satisfiable transition
- Every critical action is reachable
- Every action whose tag can evaluate to harmful has a halt reason
- Every prerequisite is satisfiable, non-circular, and has a failure message
- Every follow-up has a condition, deadline, prompt, and note
- Every time-sensitive critical action has a deadline and prompt text
- No condition uses a predicate outside the five permitted, in the full grammar
- Vital sign values fall in physiologically possible ranges

**Payloads**
- Every authored result is a structured payload, not a prose string
- Every payload and every component carries `abnormal`
- Payload-level `abnormal` equals the OR of its components
- Every component carries a label, value and reference range
- Parseable reference intervals agree with their abnormal flags (warning)

**Catalog conformance**
- Every case action has a binding row; `unmatched` is an error
- Mapped targets exist in the catalog
- A catalog entry bound by more than one case action warns
- Every catalog condition parses in the section 4 grammar
- Every catalog investigation and exam carries a default result
- The case authors no exam maneuver outside the closed set of 14
- The `general_status` key exists
- Every alertness-gated phase is covered by the global interview rule

**Silent normals**
- A study named in a condition or tagged critical but unauthored warns, naming the default that will be served

**Handoff**
- The correct diagnosis and every authored alternative resolve to real catalog ids

### 14.2 The review artifact

Before release, the tooling generates a **per-key review matrix**. For each key it enumerates every combination of the flags, studies, and phases appearing in *that key's own rule list*, and shows what the key resolves to in each. Study predicates take three values: not ordered, pending, resulted. For lab, imaging and exam keys the resolved payload is shown inline with abnormal components marked.

This is what the physician author reviews. It surfaces the failure mode this system is most vulnerable to: a missing rule falling through to a default that is clinically wrong in that situation, with no error raised anywhere.

**Read it in full.** On the reference case, four clinically wrong resolutions raised no error anywhere and were found only by reading the matrix. Three of the four were on the deterioration branch, which is the part of the case an author thinks about least.

Per-key enumeration can produce combinations unreachable in the real case, for example two mutually exclusive interventions both set. These are labeled rather than trusted.

### 14.3 Author sign-off checklist

**Clinical content**
- [ ] Every abnormal finding, lab, and imaging result is clinically correct for this diagnosis
- [ ] Every abnormal value carries an abnormal flag, and no normal value carries one
- [ ] Reference intervals are right for the assays this case is modelling
- [ ] Every harmful action is genuinely harmful, and its halt reason is accurate
- [ ] Nothing tagged harmful should have been discouraged, and nothing discouraged should have been harmful
- [ ] No action tagged critical is actually optional; no action tagged neutral is actually critical
- [ ] Findings change appropriately after successful treatment
- [ ] Every debrief note teaches something correct, and every reference has been checked

**Catalog conformance**
- [ ] Every mapped binding row is clinically sound, with particular attention to assays, routes and composites
- [ ] Every harmful and discouraged action covers every catalog route to the same act
- [ ] Exam findings sit where the routing map puts them, and the general status line matches the patient
- [ ] Every diagnosis, correct and alternative, is a real catalog id

**Interview**
- [ ] The patient never reveals the diagnosis or reports information they could not know
- [ ] Pertinent negatives are authored as denials, not left to the out-of-scope fallback
- [ ] Interview answers are correct at every alertness level, and every topic has a distressed-phase answer where the case needs one
- [ ] Paraphrase coverage is adequate on every topic whose answer changes management

**Structure and sequencing**
- [ ] Consultant advice never references a study that was not ordered, or one still pending
- [ ] A pending tier exists for every consultant whose advice depends on a study
- [ ] Prerequisites are clinically correct, and any catalog default that should be waived here has been
- [ ] Follow-ups are triggered by the right action, apply only where clinically indicated, and list every satisfier
- [ ] Every deterioration branch has an exit that exists in the catalog

**Presentation**
- [ ] **No nurse prompt implies the patient is deteriorating**
- [ ] Prompt deadlines reflect real relative urgency
- [ ] Wrong dispositions and diagnoses have explanations, not just verdicts
- [ ] The review matrix contains no clinically wrong resolution
- [ ] **The case has been played start to finish in the interface**, including at least one harmful halt and the deterioration branch

The last item is not ceremonial. Both the validator and the review matrix read the case file, so neither can see a study the interface never renders or a rescue action the resident cannot reach.

---

## 15. Limitations authors must design around

- **Flags are permanent.** A single dose fixes something for the remainder of the case. Do not build cases that depend on redosing or titration.
- **Permanent flags can shadow phase-correct content.** Put phase rules before flag rules in any list where both appear. See section 4.
- **Flags are binary.** Symptoms and findings switch rather than grade. Partial response cannot be represented.
- **The patient does not deteriorate.** Ignoring every nurse prompt produces the same patient as acting immediately. The difference appears only in the debrief.
- **Order cannot be expressed in conditions**, beyond what prerequisites enforce.
- **Serial testing cannot be represented.** A repeat study in an unchanged state returns the same value.
- **One vitals block per terminal phase.** Every halt shows the same numbers whatever the mechanism.
- **Turnaround times are compressed** and do not reflect real clinical waits.
- **Vitals are static within a phase.** The monitor steps at phase boundaries.
- **The interview matcher is lexical**, with the error rates in section 10.6.

Each is a deliberate trade for version one. The rule structure migrates cleanly when continuous variables are added, because rule lists keep the same shape and only the predicate set becomes richer.

---

## 16. Authoring a new case, end to end

The sequence, with the reference section for each step and the artifact each produces.

### Step 1. Scaffold the pack.

```
python3 engine/new_case.py PE "Acute pulmonary embolism"
```

Writes `cases/PE/` with a skeleton case file, a seed template, an empty binding map, an empty scenario list and an empty test file. The seed template lists the 14 exam maneuvers and the routing map, so you have them in front of you while writing step 1.

The skeleton deliberately fails the validator. The error list is your to-do list.

### Step 2. Write the seed (section 3). AUTHOR-ONLY.
About an hour for a case you know well. Nothing downstream can be right if this is wrong or thin.

**Before you write the action spine, open the catalog** and check that the actions your case turns on actually exist. This is the cheapest possible moment to discover that the rescue for your deterioration branch is not in the product.

### Step 3. Bind to the catalog (section 7.2). AUTHOR-ONLY sign-off.
Produce a binding row per action. The AI proposes; you accept each `mapped` row. Any `unmatched` row is a decision: request a catalog entry, or change the case.

Run the binding tool. It reports counts and flags anything blocking.

### Step 4. Route the exam findings (section 11.2). AI-DRAFTABLE, author reviews.
Take the findings from seed 3.6 and place each on one of the 14 maneuvers using the routing map. Write the general status line per phase.

### Step 5. Draft the case file. AI-DRAFTABLE against the seed.
Phases, transitions, tags, prerequisites, follow-ups, content keys, interview bank, prompts, handoff, debrief notes. Everything here is expansion of steps 1 to 3, and the AI must flag rather than invent anything the seed did not supply.

### Step 6. Structure the results (section 11.4). AI-DRAFTABLE, author signs the flags.
Convert every authored lab and imaging result into the payload shape, with reference intervals and abnormal flags. Where the catalog has a default for the same analyte, use its interval.

### Step 7. Validate (section 14.1).
Run the validator until it is clean, or until every remaining error is a catalog change request you have raised rather than a defect in the case.

Expect the first run to find things. On the reference case it found a phantom action reference, a Fahrenheit value in a Celsius field, and 24 prerequisites written in the wrong polarity.

### Step 8. Simulate (system design 13.3).
Script a dozen end-to-end routes: the intended path, each harmful halt, each blocked prerequisite, the deterioration branch and its rescue, and any ordering you think a resident might produce. Reachability is a weak claim; a walked path is a strong one.

### Step 9. Read the review matrix in full (section 14.2). AUTHOR-ONLY.
This is where the clinically wrong resolutions are, and they raise no error. Pay closest attention to the deterioration branch and to any key where a flag rule and a phase rule appear in the same list.

### Step 10. Play the case (section 14.3, final item). AUTHOR-ONLY.
Start to finish in the interface, including a harmful halt and the deterioration branch. This is the only step that can catch an interface defect, and it will also tell you whether the case is any good to sit through, which nothing else measures.

### Step 11. Sign off (section 14.3).
Every box. The checklist is the release gate.

---

## 17. If the case was drafted before the seed

Section 2 assumes the author supplies ground truth and the AI expands it. A case produced the other way round, with a model generating the AUTHOR-ONLY fields, inverts the most important constraint in this document.

That is sometimes the practical starting point. Where it happens, the case file must carry a provenance block recording:

- that the AUTHOR-ONLY fields were AI-generated
- the list of fields awaiting primary sign-off
- reference verification status, per reference

And the review burden changes shape. On a seeded case the physician checks that the AI expanded ground truth faithfully. Here they are authoring the ground truth in review, which is slower and needs a different frame of mind: read every number as a proposal, not as a transcription.

Such a case is not usable with learners until the section 14.3 checklist is complete, and the file should say so in a field the interface displays.
