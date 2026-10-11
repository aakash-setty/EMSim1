# Case Authoring Requirements

**Version 0.24 | Aligned to the system design as of v0.24.** Sections added after v0.7 carry their version where they appear.

What must be provided to produce one complete, playable, clinically valid case.

This document has two audiences. The **case author** is an emergency physician who supplies clinical ground truth and reviews everything. The **drafting AI** expands that ground truth into the full case file. Sections marked AUTHOR-ONLY cannot be delegated. Sections marked AI-DRAFTABLE can be generated and then reviewed.

**Changed in v0.24.** Three packs were written on 6 October 2026 (TSS v0.21, TAKO v0.22, DKA v0.23) and an audit compared them with this document and with the engine. This revision makes the document match. It describes no new mechanism apart from one new field, `voice_phrases`. What is new here:

- **Rules the audit found broken in all three packs**, each in the section where an author looks: narration and vital effects (9.5 and 6.1), what a prompt may say (9.5), the default difficulty mode (9.7), follow-ups that ask for a repeat (8.2), consultants and pending results (11.5), text on a covering action (9.1 and 3.4), result comments (11.4), the out-of-scope bank and the held-out question file (10.6), verification markers (13), and races between timed rules (5.4).
- **Fields that packs use and this document did not describe**: `short_label` (5), `expectation_label` and the action field table (7.1), `prompt_cap_recommendation.per_phase` (9.5), `pertinent_negative` (10.3), `changes_with_state` (11.4), `disposition_display_order` (12), a null `when` in `also_satisfies` (6.8), and `flags_set_repeat` used for a restart or a repeat study (6.5).
- **Case-only actions** (7.1 and 7.2), with the new `voice_phrases` field (v0.24).
- **The sign-off checklist (14.3) and the new-case sequence (16)** carry the new checks and the workflow for a pack written as Python.

**Changed from v0.2.** The global catalogs now exist, and a case is written against them rather than alongside them. Concretely: actions are named by catalog id; the exam maneuver set is closed at 14 with a fixed routing map; results are structured payloads with abnormal flags rather than prose; catalog prerequisites merge with case prerequisites rather than being replaced; there is a fifth clinical tag, `discouraged`; a case now supplies its care setting and arrival mode for the splash screen; and section 16 gives the end-to-end authoring workflow, which did not previously exist as a sequence.

**Changed from v0.6.** An action can now grant a flag that expires (`flags_set_timed`, section 6.2), which is what lets a case react to something wearing off rather than only showing it wearing off, and vital effects gained `onset_seconds` so a drug can take time to start. Read **section 6.4 first**: five mechanisms now touch time, move a number or count, and picking the wrong one is the mistake, not using them wrongly.

**Changed from v0.5.** Two things an author now has to decide that v0.5 decided for them. Oxygenation and any other vital can be moved by an action rather than only by a phase, through `vital_effects` (section 6.1), which means a phase's authored vitals have to be the **unsupported** baseline or the number is counted twice. And the resident no longer sees any vitals until they attach a monitor (section 6.7), which changes what an arrival prompt can assume the resident is looking at.

**A case is now a folder, not a file.** Everything you author for one case lives in `cases/<PREFIX>/` with a shared prefix, and every tool takes that folder as its argument. `python3 engine/new_case.py <PREFIX>` scaffolds it, including a copy of the seed template and the exam routing map. See section 16 and the repository README.

**Changed from v0.3.** One change matters more than the rest: **the resident no longer starts with a background paragraph.** The Patient tab is gone, there are seven tabs, and what the resident is handed at the start is two sentences of arrival handover, plus a splash line naming the room. Everything else about the patient must be asked for. Concretely, for the author:

- Section 3.2 now asks for a structured `arrival` block (`mode`, `location`) and a separately authored **two-sentence handover**, written to be mediocre on purpose. The old free-prose "how the patient reached you" is no longer what the runtime shows.
- The splash screen no longer shows the handover or the arrival mode. Do not write scene-setting expecting it to appear there.
- The interview now carries the weight the Patient tab used to carry, so **section 10.2 topic coverage is no longer a nicety.** A topic you did not author is a question the resident cannot get an answer to, and there is no fallback paragraph behind it.
- Vitals ramp over five seconds at phase boundaries. This changes nothing you author; section 6 notes the one consequence.
- Section 10.6 carries new measurements of the interview matcher, and the matcher itself has changed.

**Changed from v0.4. One change, and it removes a constraint rather than adding one.** A phase
transition may now carry a deadline, so a phase can be left because the resident did not act. Through
v0.4 the patient never changed unless the resident changed her, and a case whose teaching point was
the passage of time could not be authored at all.

- **Section 5** carries the mechanism: the schema, the three patterns it supports, and the six rules
  that keep it from becoming a trap.
- **Section 0 fact 2** is rewritten. It is the fact most authors build their mental model on.
- **Section 9.5** gains one exception to the no-trajectory rule, and only one.
- **Section 9.7** explains why normal mode does not slow deterioration down.
- **Section 14** adds the validator checks, a third review artifact and four checklist items.
- **Section 15** amends the limitation that said the patient does not deteriorate.

**Most cases should not use this.** It exists for the presentations whose lesson is that time itself
costs something: meningococcal sepsis, anaphylaxis, status epilepticus, tension pneumothorax, an
untreated occlusive infarct, a tricyclic overdose. If your case's teaching point is a decision rather
than a delay, author it without a clock and the case stays easier to review and fairer to play.

If you are authoring your first case, read section 0, then jump to **section 16** and follow it. The rest of this document is the reference it points into.

---

## 0. How the case runs

Understanding the runtime is necessary to author for it. Twelve facts govern everything below.

1. **The case moves through phases.** A phase is a clinically distinct patient status. Interventions move the patient between phases.
2. **A clock runs. It changes the patient only where you author it to.** Time governs when results arrive, when the nurse prompts, and timing feedback in the debrief. Since v0.5 it can also drive a phase transition, but only where the case wrote one: a transition rule carrying `after_seconds` fires when that many seconds have passed and its guard still holds. Vitals never drift; a time-driven change moves the patient from one authored phase to the next, in a step. A case that authors no such transition behaves exactly as it did before, and an untreated patient in that case does not deteriorate. See section 5.
3. **Flags are binary, and permanent unless you author otherwise.** An intervention sets a flag. Nothing is partial. Two authored exceptions exist. A flag granted with a duration lapses (6.2). A flag can be granted on the Nth administration instead of the first (6.5).
4. **Reads never change state.** Exams and interview questions return content based on current state. They do not alter it. Ordering a study does change state, even though it feels like a read.
5. **Every readout is resolved, not stored.** Each thing the resident can see is a *key* owning an ordered list of guarded alternatives. First match wins. The last alternative is unconditional.
6. **Anything the case does not author returns the catalog default, which is normal.** This is the most dangerous property of the system. See 11.1.
7. **Results freeze at the state in which they were ordered.** A film ordered before intubation does not show a tube.
8. **The resident sees the whole catalog, not your case's actions.** Every drug, study and maneuver in the product is on the menu whether or not you referenced it.
9. **Orders on the action tabs are selected then submitted as a batch.** Exams, interview questions and consults fire immediately.
10. **The case ends** when the resident confirms a handoff, when a harmful action halts it, when a transition reaches a terminal phase you authored (5.1), or when the resident ends it early. One authored exception: a disposition the case intercepts does not end the run (6.9, v0.21).
11. **The resident is given almost nothing at the start.** A splash line naming the room, then age, sex, chief complaint and a two-sentence arrival handover at the top of the History tab. There is no Patient tab and no background paragraph. Everything else is reachable only by asking.
12. **Vitals ramp to the new phase over five seconds** when a phase changes. This is display only. A result ordered during the ramp still freezes at the phase's authored numbers, so the monitor and a simultaneous blood gas can disagree for a few seconds.

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

*A mapped binding row is a clinical judgment.* Deciding that a case's high-sensitivity troponin I binds to the catalog's troponin T entry is not an id lookup, it is a claim that the two are interchangeable for this case, and here it is false. The AI proposes the mapping and records its reasoning; the author accepts or rejects each row.

*An abnormal flag is a clinical judgment.* The AI can carry a flag across from prose that already said "(high)". It cannot decide that a value is abnormal.

*A reference interval is a clinical fact.* Where the catalog supplies one, use it. Where it does not, the author supplies it, and the payload carries a `verify` note until they do.

---

## 3. The author's seed

Supplied before any AI drafting begins. For a case the author knows well this should take about an hour.

**3.1 Case identity**
- Working title and chief complaint as the patient would state it
- **A short clinical complaint**, `metadata.complaint`, three or four words in clinical
  register: "Worsening breathlessness", "Fever and a rash on her ankles". This is what
  the welcome screen lists, and it is not the chief complaint, which is the patient's
  own words and belongs on the splash. Optional; a case without one falls back to its
  working title, which is usually too long for a list
- **A category**, `metadata.category`, naming the body system or problem class:
  "Cardiovascular", "Infectious disease". It groups the welcome list and generates the
  filter chips. Optional; a case without one drops into a single unnamed group
- Final diagnosis, **as a diagnosis catalog id**. The id that is scored lives in `handoff.correct_diagnosis.catalog_id` (section 12). `metadata.final_diagnosis` is a prose line for the reviewer, for example "Mild diabetic ketoacidosis in type 1 diabetes, set off by gastroenteritis". Every pack writes it as prose and no tool reads it
- Three to six learning objectives
- Target level, `metadata.target_level`: a list drawn from `medical_student`, `intern`, `junior_resident` and `senior_resident`, lowest first. The welcome list prints it, and three or more read as a range from the first to the last

**3.2 Patient and setting**
- Age, sex, weight, relevant background
- Presenting vital signs
- Presenting appearance in one or two sentences
- **The care setting**, if it is not a quaternary Level 1 center with everything available. This is not scene-setting: the correct disposition depends on it, and a case written for a hospital with no cardiology on site has a different right answer
- **How the patient arrived**, as three separate fields, described below

**Arrival. Changed in v0.4 and this is the change most likely to catch out an author who has written a case before.**

Through v0.3 arrival was free prose, it was shown on the splash screen, and it was shown again on a Patient tab alongside a structured background. The splash section is gone and so is the Patient tab. What the runtime now uses:

```json
"metadata": {
  "arrival": {
    "mode": "ems",
    "location": "resuscitation_bay",
    "line": "Brought in by EMS. Handover given on arrival in the resuscitation bay."
  }
},
"patient": {
  "arrival_handover": "Sixty-five year old man, breathing trouble that's been getting worse over the last few days. Family called us this morning when he couldn't manage the stairs."
}
```

- **`mode`** is `ems` or `triage`, and nothing else. It decides who is speaking: an EMS crew handing over, or a triage nurse reporting what the patient told them at the desk. Legacy values (`Ambulance`, `Walk-in`, `Transfer`, `Police`) still load and produce a validator warning; convert them.
- **`location`** is `resuscitation_bay`, `trauma_bay` or `patient_room`. The splash screen renders `Patient brought to the Resuscitation Bay` from it. This is the **only** arrival information the resident sees before pressing Begin, and it is generated, not authored prose.
- **`line`** is a one-sentence internal description used in the chart header and the debrief. It is not the handover.
- **`patient.arrival_handover`** is the two sentences the resident reads at the top of the History tab.

**Rules for the handover.** The validator enforces the sentence count and warns on length. Every other rule here is a review item (14.3).

- **Two sentences at most.** More than two is an error. Roughly 45 words is the practical ceiling and the validator warns beyond it.
- **A vital sign is allowed, as what was measured on the way in** (v0.7). The monitor is dark until it is attached (6.7), so the handover may be the only number the resident has. Write it as a past measurement and make it agree with the first phase. The validator prints a note when the handover quotes one, and warns only when a quoted saturation disagrees with the first phase's.
- **No past medical history, no medication list, no allergies.** Every one of those is an interview topic. Putting it in the handover means the resident gets it without asking, which is the failure the Patient tab was removed to prevent.
- **No pertinent negatives.** "Denies chest pain" hands over the single most useful discriminator in most dyspnea cases.
- **No diagnosis, and no word that names one.** Not "CHF exacerbation", not "fluid overloaded", not "septic". A crew radioing in may say those things; a case that says them has ended the case.
- **Write it badly on purpose.** This is the hard part and it is not enforceable. A real handover from a busy crew is vague, partly wrong about timing, and organized around what was visible rather than what matters. Aim for that. The temptation is to write a competent summary, and a competent summary is worse than no handover, because it teaches that the handover can be trusted.

**What a triage handover sounds like, versus an EMS one.** The triage nurse has the patient's own account and a set of observations from the waiting room; the crew has the scene, the family and what happened in the ambulance. Neither has a chart.

| mode | example |
|---|---|
| `ems` | "Sixty-five year old man, breathing trouble that's been getting worse over the last few days. Family called us this morning when he couldn't manage the stairs." |
| `triage` | "Fifty-eight year old woman walked up to the desk saying her chest has felt tight since last night. She looked pale enough that I brought her straight through." |

**The background did not go away.** Section 3.7 interview ground truth is still required in full, and it is now the only route to any of it. Removing the tab raised the cost of an unauthored topic from "slightly less convenient" to "unanswerable", which is why section 10.2 coverage now matters more than it did.

**3.3 Phases (three to six clinical phases, plus terminals)**
For each: a label, a short label for the monitor (section 5), a one-line clinical description, and the vital signs in that phase. At least one must be a resolution phase. At least one should be a deterioration phase if deterioration is clinically plausible.

**And, for each phase, whether anything happens if the resident does nothing.** This is a clinical
question and it is yours: how long can this patient sit in this state without the treatment that is
missing, and what does she look like afterwards. If the answer is "indefinitely, for the purposes of
a fifteen-minute case", author no clock and say so. If the answer is a number, that number is the
seed for a time-guarded transition and section 5 is where it goes. Decide it here rather than later,
because a deterioration bolted onto a finished case tends to fire during the part the author never
played.

The count refers to clinical phases. The two terminal phases (halted, complete) are structural and do not count against it.

**3.4 The action spine**
- **Critical actions**: what must happen for the patient to do well, in which phase each becomes critical, and which are time-sensitive
- **Harmful actions**: what would injure or kill this patient, with a one-line clinical reason for each
- **Discouraged actions**: wrong here but not lethal
- **Recommended actions**: good practice but not case-determining
- **Traps**: plausible-looking actions that are wrong here, and why. Most traps are `discouraged`; a few are `harmful`

For each harmful and discouraged action, name **every route to it**. If a fluid bolus is harmful, say so for saline and for Ringer's and for each volume; if a bronchodilator is a trap, say so for the combination nebulizer and for each agent alone. The catalog often lists as separate entries what a clinician thinks of as one act, and an unbound sibling is an escape hatch from the lesson.

**A stop action has siblings too** (v0.21 to v0.23a audit). If stopping one infusion is discouraged or is the rescue, bind every stop entry for the same class. TSS tagged `stop_norepinephrine` discouraged and covered four vasopressors under one start action. A learner who started vasopressin and pressed Stop Vasopressin was narrated as having stopped it, was not scored, and the running flag stayed set. Check: for each start action that covers siblings, list the catalog's stop entry for each sibling and confirm one case action covers them all.

**Where the catalog declares an equivalence group, use it.** `equivalence_groups` names sets the catalog considers interchangeable, such as the four crystalloid boluses. Binding one case action to a group with `also_covers_group` on its binding-map row applies its tag, halt reason and debrief note to every member, so the coverage cannot drift as the catalog grows. `also_covers` on the row lists entries one by one where no group exists. Each entry keeps its own button and its own name. The case fields are shared, including the flags, the vital effects, the narration override and the nurse alert, so write those to be true of every member (9.1). A covered entry does not prompt on its own and does not borrow `voice_phrases`. Use it wherever the case is making a claim about **the act** rather than about one particular agent, in either direction: a harmful tag that must not be escapable, or a required action that any member should satisfy.

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

**`ordered` versus `resulted`.** These differ because studies take time to return: laboratory studies, plain films and the twelve-lead 5 seconds, CT and MRI 10, bedside 0. Use `resulted` for any content that references the finding itself. Use `ordered` for content acknowledging that something is on its way.

**`flag` versus `action taken`.** Every state-changing action sets a flag, so for those two the predicates are equivalent. Use `flag`. Reserve `action taken` for observational actions, for example a consultant who responds differently depending on whether the abdomen was examined. `action A taken` is true when A was performed, when a sibling that A covers was performed, or when another action credited A through `also_satisfies` (6.8). It means the act is accounted for, not that this button was pressed.

**There is still no time predicate, and there will not be one.** Timing is expressed only in named
deadline fields: on prompts, on follow-ups, and since v0.5 on phase transition rules. It never
appears in a condition. Requests to add a time predicate should be refused by the drafting AI and
escalated, because time-conditional *content* would make the per-key review matrix unenumerable and
the case unreviewable.

**Time-guarded transitions do not breach this, and the distinction is the thing to hold onto.** A
transition rule's `when` is an ordinary condition in this language, with no time in it. The timing
sits beside it in a separate field. So a lab result, an exam finding, a clinical tag, a prerequisite
and an interview answer still resolve against phase, flags and study state and nothing else, and the
review matrix has exactly the rows it had before. What a clock can change is which phase you are in,
and the matrix already enumerates over phases.

Concretely: `{"when": "NOT flag abx_given set", "after_seconds": 240}` is allowed on a transition.
`"elapsed > 240"` is not allowed anywhere, and `"after_seconds"` is not allowed on a content rule, a
tag, a prerequisite or a follow-up.

**Rule ordering rule of thumb: phase rules before flag rules.** Flags are permanent, so a flag set in an early phase is still set in a later one. A key that tests `flag on_niv set` above `phase is post_intubation_hypotension` returns the improved value to a patient who has since collapsed. Whenever both appear in one list, the phase rules go first. This is the single most common way a rule list is correct for the situations the author was thinking about and wrong for one they were not.

---

## 5. Phases and transitions

Each phase requires:

- **id** and **label**. The label is printed in the debrief, in the list of what happened and in the line that says how a failed run ended
- **short_label**, the words on the monitor's phase chip for the whole time the patient is in that phase. See the rule below
- **clinical description**, one line, for author review
- **vital signs**: heart rate, systolic and diastolic blood pressure, respiratory rate, oxygen saturation, temperature
- **appearance values**: see section 6
- **transition rules**: an ordered list, each with a condition and a destination phase. Evaluated after every state-changing action. First match wins.
- **terminal flag**: whether the case ends here

Transition conditions should gate on the critical actions of that phase, so the case advances because the resident did the right things.

**The monitor prints `short_label`, so it must not name the diagnosis or the problem.** The chip sits beside the clock from the first second and changes the moment the phase does. Write what a bystander could say about how she looks: "on arrival", "pressure low", "after potassium". Do not write the diagnosis ("septic shock"), the mechanism ("outflow obstruction"), the missing treatment ("needs a pressor"), the drug that is running if a sibling could be running instead (9.1), or a verdict the learner is meant to reach by ordering something. DKA at v0.23 read "potassium replaced" before any repeat level, which answers the question its follow-up asks. "after potassium" does not. A phase with no `short_label` prints its `label` on the monitor instead, so author one on every phase, terminals included.

Harmful actions bypass transition rules entirely and move directly to a terminal halted phase carrying that action's halt reason.

**Note on prompt deadlines:** they are measured from phase entry. When a phase changes, outstanding prompts for the previous phase are canceled and new deadlines begin. Authors should therefore set deadlines relative to the start of the phase the action belongs to, not relative to case start.

**Transitions do not cascade within one action.** If the resident satisfies a later phase's transition before entering it, the phase machine advances one step per state-changing action, so the next action advances two phases at once. A phase entered and left in the same step issues no prompts. Check your simulator scenarios for orderings that produce this.

**Every deterioration branch needs a reachable exit.** If entering a phase requires an action, leaving it requires an action too, and that action must exist in the catalog. Confirm the exit exists before authoring the branch. Stopping an infusion is a case in point: every persistent infusion has a matching stop action, but stopping is a separate step rather than a toggle, so the case must author it as its own action and gate the rescue transition on the flag it sets.

**Requirement:** every phase must be reachable, and every non-terminal phase must have at least one satisfiable transition. A phase reachable only by the clock counts as reachable.

### 5.1 Time-guarded transitions

A transition rule may carry a deadline. It then fires when the deadline has passed **and** its guard
is still true. A rule without a deadline is instantaneous and behaves as it always has.

```json
{
  "when": "NOT flag abx_given set",
  "after_seconds": 240,
  "measured_from": "phase_entry",
  "to": "progressive_sepsis",
  "narration": "The spots on her ankles have joined up while we've been standing here.",
  "debrief_note": "The organism was never treated and the septicaemia progressed. Meningococcal disease is measured in hours and the rash is the clock you can see.",
  "author_rationale": "Untreated meningococcal bacteraemia progresses over minutes to hours."
}
```

| Field | Required | Meaning |
|---|---|---|
| `after_seconds` | yes, to make it time-guarded | Deadline, a whole number of seconds. Minimum 30 with a warning below 60, or minimum 5 for a delayed consequence. See 5.2 rule 1 |
| `measured_from` | no, defaults to `phase_entry` | `phase_entry` or `guard_true` |
| `narration` | yes | What the nurse says at the moment it fires. AI-DRAFTABLE. It must be true of the monitor on every route into the destination (9.5) |
| `debrief_note` | yes | What the learner is told about it afterwards. AI-DRAFTABLE from your rationale |
| `author_rationale` | yes | Why this patient deteriorates in this time. **AUTHOR-ONLY** |
| `allow_time_to_terminal` | only if the destination is terminal | Explicit opt-in to ending the case on the clock |
| `terminal_opt_in_rationale` | with the above | **AUTHOR-ONLY** |
| `unguarded_rationale` | only if `when` is null | Why this fires regardless of what the resident does. **AUTHOR-ONLY** |

**The four patterns.** Name which one you are using before you write the rule.

*Deterioration on inaction.* A negative guard, `NOT flag F set`, measured from phase entry. The
common case, and the one the feature exists for. Because flags are permanent, a negative guard can
only be falsified and never re-satisfied, so once the resident gives the drug that deterioration is
canceled for the rest of the case rather than deferred. Each rule is one question with a yes or no
answer: was this done in time.

*Delayed consequence of an action.* A positive guard, `flag F set`, with
`measured_from: "guard_true"`. Use this where an action has a consequence that is not instantaneous.
Peri-intubation collapse is the obvious one: modeling it as instant teaches that the tube caused it,
where modeling it forty-five seconds later teaches that the induction agent and the positive
pressure did, and leaves room for the resident to have a pressor ready.

*Scheduled natural history.* No guard. The illness does something regardless: a simple febrile
seizure self-terminating, a thrombolysis window closing, the second phase of a biphasic reaction.
This requires an `unguarded_rationale`, because a transition nothing can prevent is a scripted
trajectory and should be a decision rather than an oversight.

*Outcome chosen at a scheduled time* (v0.21). A positive guard, `flag F set`, measured from phase
entry, placed above an unguarded rule with the same `after_seconds`. Something happens at that
time whatever the resident does, and what is running by then decides where she lands. In TSS
the response to fluid fades at 150 seconds. With a vasopressor running she goes to the
supported phase, and with none she goes to the hypotensive one. First match decides, so the
guarded rules go above the unguarded one. The validator gives this pattern the 30 second floor
and asks for no prompt.

**How a `guard_true` clock runs** (v0.22). The clock belongs to one rule in one phase. It starts
at the first transition check in that phase that finds the guard true, or at phase entry if the
guard already holds. A check happens after a state-changing action, on a deadline and when a
flag lapses. A result coming back is not a check. The clock does not carry into the next phase.
A rule with the same guard in the next phase starts again from zero. TAKO has "cardiology takes
over 90 seconds after the call" in three phases. Cardiology called 200 seconds into a phase with
a 240 second exit arrives 90 seconds after that exit, which is 130 seconds after the call. If
the delay must survive a phase change, say so in the SEED as a known limit or put the
consequence in one phase.

### 5.2 The six rules that keep this from becoming a trap

These are enforced by the validator (14.1), and the reasoning is worth having rather than just the
rule.

1. **Thirty-second floor**, with a warning below sixty. A deterioration the resident could not
   plausibly have prevented teaches nothing about medicine and a great deal about reflexes.
   **Both the floor and the warning apply to the two patterns where something happens TO
   the resident**, which is a deterioration on inaction and an unguarded scheduled natural
   history. A delayed consequence of an action they took (`measured_from: "guard_true"`
   with a guard that negates no flag) has nothing to prevent and no reflex to test: it is
   the case saying how long a drug takes to work, and its floor is five seconds, below
   which the consequence is on the same click as the action and the drug is a button
   again. (Until v0.9 the thirty-second floor applied to this pattern too; AFRVR's rate
   control now acts at ten seconds.)

   What the validator does, exactly. A rule with no guard, or a rule whose guard contains
   the word NOT and names a flag, has the 30 second floor and warns below 60. A rule timed
   from `guard_true` that is not one of those has the 5 second floor and never warns. Any
   other rule, which is a positive guard timed from phase entry, has the 30 second floor
   and no warning. TSS uses a 5 second rule and DKA uses 10 and 20 (v0.21, v0.23).

   The test for a negated guard is the whole word NOT anywhere in the guard (v0.22). When
   it is there, every flag in the guard is treated as one the guard needs unset, including
   a flag the guard needs set. `flag fluids_given set AND NOT flag steroid_given set` asks
   for a prompt for fluid as well as for the steroid. Check a mixed guard by hand.
2. **A prompt must come first.** For every flag your guard requires to be unset, some action that
   sets that flag must prompt in that phase, at least twenty seconds before the deadline. This is
   section 1's framing made mechanical: the nurse exists to teach, and a deterioration nobody warned
   about is a trap. If you find yourself wanting a deterioration with no warning, what you actually
   want is a longer deadline and an earlier prompt.
3. **A prompt that cannot fire is an error in your case.** A prompt at 260 seconds in a phase that
   ends at 240 will never be seen. Nothing about the case looks wrong; the learner is simply never
   helped with that action. The validator warns.
4. **Terminal destinations need an explicit opt-in.** Ending a case because nothing was done is the
   strongest statement this system can make, and it must never happen because an author reused a
   phase id. It also must not use the shared `halted` phase, which carries a harmful action's halt
   reason: attributing an omission to a commission teaches the learner something false about their
   own run. Author your own terminal phase with its own `timeout_reason`.
5. **No cycle made only of time edges.** A loop with no resident involvement is a case that plays
   itself.
6. **Every destination needs an exit**, exactly as for an action-driven deterioration branch. If the
   clock can put the patient somewhere, something must be able to get her out.

### 5.3 What a time-guarded transition costs you

**Prompt deadlines and deterioration deadlines share a phase and compete for it.** Everything you
want the nurse to say has to fit before the phase can end. In a phase with a 240-second exit and
nine prompted critical actions, the last few will not be heard. This tightens the prompt cap problem
rather than creating it, and it is the most common reason to lengthen a deadline.

**The clock does not pause.** A resident reading a long consultant response, composing a batch of
orders, or thinking, is on the same clock as one who has frozen. The floor and the mandatory prompt
are the mitigations; there is no grace period. Author deadlines with a slow reader in mind.

**Normal mode does not slow it down.** See 9.7.

**Deterioration is all-or-nothing.** A drug given one second before the deadline has the same effect
as one given immediately. Graded lateness is not representable; if you need it, you need more phases,
and the section 3.3 ceiling of six clinical phases binds sooner than it used to.

**You now have to review a path nobody takes on purpose.** What the patient looks like when the
resident does nothing at all is a real trajectory in your case, and it is the one you are least
likely to have imagined. Section 14.2c generates it.

### 5.4 Two timed rules pending at once (v0.21 to v0.23a audit)

The condition language cannot express order (section 15). A case that teaches order carries it
in phases: the same drug leads somewhere different depending on the phase it is given in. That
is sound while one timed rule is pending. When two are pending, the result depends on which
fires first, and no tool checks that you meant it.

How the engine decides, so that you can work it out on paper:

- Each `guard_true` rule has its own clock (5.1).
- When any deadline arrives, the phase's rule list is read from the top. The first rule whose
  guard holds and whose time is up fires. The other rule's clock is dropped with the phase.
- Two rules due at the same instant: the one higher in the list fires.
- An action logged at the same instant as a deadline is applied first.

**Rule: for every phase with two or more timed rules, list every pair, and for each pair say
which fires first for each order and each gap, and where the patient ends up.** Put the table
in the SEED. Then test each row with fractional times, because the browser clock is not in
whole seconds and a boundary that sits between two whole seconds passes every whole-second test.

DKA's arrival phase has two delayed consequences: insulin leads to a falling potassium after
10 seconds, and potassium leads to the replaced phase after 20. Its table, confirmed in the
engine:

| What the learner does | Which rule fires first | Where she ends up |
|---|---|---|
| Insulin, then potassium at any gap | insulin's | falling potassium, as intended |
| Potassium, then insulin up to 10 seconds later | insulin's, because it is due first or is higher in the list | falling potassium, with the potassium flag already set, so holding insulin alone rescues her |
| Potassium, then insulin more than 10 and less than 20 seconds later | potassium's | replaced, then treated 10 seconds on, with no repeat level sent |
| Potassium, then insulin 20 seconds or more later | potassium's | replaced, then treated. The intended path |

Rows two and three are not what the case teaches. A table like this is how you find them
before a learner does. Fix them by changing the phases, or record each as a known gap in the
SEED with a scenario that pins the behavior. A test at 10.5 seconds finds the boundary. Tests
at 10 and 11 report a gap of "11 to 19".

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

### 6.0a The rhythm, which is authored on the phase and not in the appearance block

A phase may carry a `rhythm`, a sibling of `vitals` and `appearance` rather than a member of either, because it is neither one of the six numbers nor one of the appearance values. It is optional and it has exactly two permitted values.

| `rhythm` | What it does |
|---|---|
| `regular` | Even intervals. The default, and what a phase with no `rhythm` field sounds like |
| `irregularly_irregular` | Every R-R interval drawn independently, so there is no underlying period for the ear to lock onto |

```json
{ "id": "presentation", "vitals": { "heart_rate": 160, "...": "..." },
  "appearance": { "...": "..." },
  "rhythm": "irregularly_irregular" }
```

**Author it wherever the rhythm is part of the finding.** The heartbeat is the only channel through which a resident can perceive a rhythm before they order a tracing, and in a case that turns on recognizing one, a regular beat is the monitor telling them the wrong answer out loud. It also has to agree with everything else the case says: an ECG report describing irregularly irregular R-R intervals over a metronomic beat is the same class of contradiction as a nurse prompt describing a trajectory over static vitals, and no validator can see it either.

**The heart rate stays the heart rate.** The interval model preserves the mean exactly, so the number on the monitor is the true average rate however uneven the individual beats are. Do not compensate for the irregularity when choosing the number.

**Two things it is not.** It is not a description of a diagnosis: the engine has no idea which conditions produce which rhythm, in the same way it has no idea which drugs are harmful, and `irregularly_irregular` names a finding that atrial fibrillation is the commonest but not the only cause of. And it is not a physiological model. The interval distribution, its spread, and the beat-to-beat variation in loudness are all authored parameters in `SHARED.audio.rhythm`, with a provenance note there saying so. **No case should be described as modeling a rhythm.**

Adding a third value, for a regularly irregular beat such as bigeminy or Wenckebach, is a request to extend the global audio module. It would need its own model rather than different parameters for this one, so escalate rather than reaching for the nearest existing value.

### 6.0b The monitor trace, which is authored beside the rhythm

Since v0.16 the monitor draws one lead, live, from the same beat the heartbeat sounds (design 8.4c). A phase may carry an `ecg` block, a sibling of `rhythm`, saying what that lead looks like. The block and every field in it are optional.

| Field | Meaning | Default |
|---|---|---|
| `pattern` | `organised` draws one complex per beat from the fields below. `ventricular_fibrillation` and `asystole` draw no complexes and sound no beats | `organised` |
| `p_waves` | Whether a P wave precedes each QRS | `true`, or `false` under an `irregularly_irregular` rhythm |
| `pr_ms` | PR interval | 160 |
| `qrs_ms` | QRS duration. This is the field that makes a complex wide | 90 |
| `qtc_ms` | Corrected QT; the QT drawn follows the rate from it | 420 |
| `st_mv` | ST level at the J point in lead II, positive for elevation | 0 |
| `t_mv` | T wave amplitude in lead II from the baseline | derived: modest and upright for a narrow complex, discordant for a wide one |
| `verify`, `author_note` | Provenance for the reviewer, as elsewhere | |

```json
{ "id": "wide_complex_tachycardia", "vitals": { "heart_rate": 180, "...": "..." },
  "rhythm": "regular",
  "ecg": { "p_waves": false, "qrs_ms": 180,
           "verify": "QRS 180 ms and no P waves, as the phase's ECG report says. [UNVERIFIED]" } }
```

**Author it from the phase's own ECG report, with the same numbers.** The report and the trace are two statements of one tracing, and a monitor showing narrow complexes above a report that says the QRS is 180 ms is the contradiction 6.0a describes, seen rather than heard. The validator cannot compare a picture to a sentence, so the discipline is on you: take the QRS, the QTc and the P wave statement from the report for the phase and write them here. Where a phase has no report of its own, say in `author_note` which figures it carries and why.

**A phase with no block is not wrong.** It draws a narrow complex with P waves at the authored rate, or without P waves under an irregularly irregular rhythm, which is what every case written before this existed already showed. Write a block where the tracing is part of the finding, and where a reviewer would otherwise have to guess what the monitor is showing in a terminal phase.

**Author the terminal phases.** `halted` and `cardiac_arrest` phases carry vitals and no ECG report, and a resident spends the last five seconds of a run looking at their monitor. Say what it shows. The shipped packs draw a slow, wide, P-less idioventricular rhythm for their generic peri-arrest phases, and each says in `verify` that a reviewer who prefers asystole, or a converted sinus bradycardia, changes the block and nothing else.

**What it is not.** It is not a twelve-lead. A terminal R in aVR, lateral ST depression, anterior Q waves and reciprocal change are findings a lead II monitor does not show, and the block has no fields for them; they belong in the report. It is not a model: the amplitudes and the shape of a wide complex are stylizations with a provenance note in `SHARED.monitor.ecg`, and **no case should be described as modeling an ECG.** And it is not read by anything: no rule, tag, prerequisite or transition can see it, for the reason none can see a vital.

**A widening QRS is phases, not a parameter.** The trace cannot change within a phase. DIPH shows the QRS at 132 ms on arrival, 148 ms seizing, 180 ms in the wide-complex phase and 104 ms once bicarbonate has acted, because those are four phases; that is the same rule as for a pressure that falls.

**The validator's stance.** Unknown fields and unknown patterns are errors, because the renderer would ignore them silently. A wide QRS without a `verify` note warns, because it is a clinical claim the monitor will draw. `p_waves: true` under an irregularly irregular rhythm warns and passes, since multifocal atrial tachycardia exists. Ranges are wide, and a unit slip (`0.12` for 120 ms) fails.

**Consequence to accept:** vitals are static within a phase and change at phase boundaries. Small cosmetic variance is added by the renderer so the monitor does not look frozen, but that variance carries no clinical meaning and no rule reads it.

**Phase boundaries now ramp over five seconds.** Rather than replacing every number at once, the renderer interpolates heart rate, both pressures, saturation, respiratory rate and temperature from the previous displayed values to the new phase's authored values across five seconds, and the heartbeat audio follows. Two consequences for the author:

- **Author the endpoints, not the path.** You still supply one set of numbers per phase. There is no way to author a trajectory, and the ramp is not one: it is a straight interpolation between two authored plateaus. A case that clinically requires a rise over minutes still needs an extra phase.
- **The tempo follows the ramp continuously.** The beat reads the current rate when it schedules the next beat, so a heart rate sliding from 160 to 108 over five seconds is heard sliding rather than in steps. Nothing to author; worth knowing when you choose the two endpoints.
- **A result ordered during a ramp freezes at the phase's authored numbers**, not the ramped ones, per fact 7. So a blood gas ordered one second after a transition returns the new phase's values while the monitor is still showing something in between. This is a real inconsistency, it lasts up to five seconds, and it was accepted rather than fixed, because the alternatives are ramping state (which breaks result freezing) or delaying results (which makes the clock lie). It is not worth authoring around; it is worth knowing about if a reviewer reports it as a bug.

### 6.0c The figure in the room, which is a content key and not part of the phase

A drawn patient stands between the panels. Two optional blocks control it, and a case with
neither gets the standard patient with open eyes.

`patient.avatar` is the fixed appearance, in avataaars option names. **Leave it out.** Every
case currently draws the standard man or woman by `patient.sex` (`SHARED.patient.base`), and
the appearance never changes with state. When cases come to choose their own bases, author
only the keys that differ. `build/patient-lab.html` lists every option and prints the JSON.

Two appearance keys are not avataaars options. `"build"` is `thin`, `average` or `obese`, and
is the one key worth authoring now: write it only where the seed or the presenting appearance
says so. The age group is **not authored**: the figure is drawn young under 40, middle from
40 to 59 and older from 60, from `patient.age`, with graying hair and facial lines.
`"ageGroup"` in the avatar overrules that, with a validator warning.

`content_keys.patient_visual` says what is visible now. It is a guarded rule list like
`general_status` (section 11.3), first match wins, and the value is the whole visible state:

```json
"patient_visual": { "rules": [
  { "when": "phase is seizing", "value": { "eyes": "open", "seizure": true } },
  { "when": "flag airway_protected set", "value": { "eyes": "closed" } },
  { "when": null, "value": {} }
] }
```

| Key | Values | Absent means |
|---|---|---|
| `eyes` | `open`, `closed` | `open`, blinking |
| `seizure` | `true`, `false` | `false` |
| `work_of_breathing` | `normal`, `increased`, `severe` | `normal` |
| `expression` | `{eyeType, eyebrowType, mouthType}` | the resting face |
| `addons` | `gaze_left`, `gaze_right`, `nystagmus`, `nasal_cannula`, `nonrebreather`, `bipap_mask`, `intubated`, `bag_valve_mask`, `defib_pads`, `central_line`, `jaundice`, `sweating`, `agitation` | none |

Beside `rules` the block may carry `also`, a list of `{"when": ..., "addons": [...]}`. It is
not first-match: every entry whose condition holds adds its add-ons to whatever `rules` chose.
Use it for things independent of the main state, such as pads, a central line or sweating,
which `rules` could only express by listing every combination. Keep the airway devices in
`rules`, where only one can win. **`also` does not appear in the review matrix**; read it in
the case file.

Do not author a respiratory rate or a distress level here; the validator rejects both. The
shoulders rise and drop at the rate on the monitor, and the resting face is drawn from the
phase's own `appearance.distress_level`: 0 a neutral mouth, 1 worried brows, 2 a downturned
mouth, 3 heavier brows as well. Closed eyes relax the face. An authored `expression` wins.

The phase's `appearance.alertness_level` is drawn the same way and is likewise not authored
here. 0 alert: open eyes, ordinary blinks. 1 drowsy: heavy lids, slow blinks, and now and
then the lids close and the head nods. 2 obtunded: eyes closed, opening to a sliver for a
moment every several seconds, head fallen a little to one side, jaw slack. 3 unresponsive: the
same with the eyes staying closed. So `eyes` in a rule is now only needed to override the
level: `"eyes": "closed"` for a sedated patient whose phase is not level 3, or a seizure,
which draws open eyes and a clenched jaw at any level. Keep the block consistent with the general status line and the appearance
values, since all describe the same patient. Prefer flags to phases for anything a resident's
action puts on or takes off the patient. It is clinical content: it goes through the review
matrix and the 14.3 sign-off like every other key.

### 6.1 Moving a vital with an action, not a phase

A phase is entered once and holds until something moves the case out of it. That makes it the wrong tool for three ordinary clinical facts: an effect that lasts thirty seconds and then is gone, an effect that ends when the drip is stopped or the mask comes off, and a drug that changes the patient without changing the number the resident is watching. Author those on the action:

```json
{
  "catalog_id": "niv_bipap_cpap",
  "vital_effects": [
    {"vital": "oxygen_saturation", "delta": 3,
     "key": "positive_pressure_spo2",
     "while": "NOT flag intubated set"}
  ]
}
```

| Field | Required | What it does |
|---|---|---|
| `vital` | yes | One of the six authored per phase |
| `delta` | yes | Added to the phase baseline. May be negative |
| `duration_seconds` | no | Omit for an effect that lasts as long as its guard holds |
| `while` | no | An ordinary section 4 condition, re-evaluated continuously |
| `key` | no | Defaults to the action id. Effects sharing a key do not stack |

**Rebase your phases, or the number is counted twice.** This is the mistake, it is easy to make, and the validator catches only the half of it that leaves the plausible range. If positive pressure adds three points and the phase a resident reaches by applying positive pressure also raises the saturation, the resident sees both. Every non-terminal phase's authored vitals must be what the patient would show **with nothing running**. In CHFE that meant `stabilizing` and `improving` both carry the arrival saturation of 87, and the only durable gain in the case comes from the mask.

**Decide deliberately which vitals a treatment does not move.** The reason to author this at all is usually the thing that does *not* happen. CHFE's furosemide carries no effect, so a resident who reaches for the diuretic first and watches the saturation sees nothing move, while the heart rate, pressure and respiratory rate all improve on the phase change. That is the case's second learning objective stated as behavior instead of as a sentence in the debrief. If every treatment in your case raises the number, you have authored a case in which sequencing does not matter.

**Give two routes to the same drug the same key.** DIPH's four routes to oxygen share `oxygen_support`, so a resident cannot stack a cannula, a mask and a bag into an improvement none of them would produce. This is the same obligation as covering every route with a harmful tag, and it fails the same way if you forget: the lesson has a sibling entry that walks around it.

**Sizes are teaching choices and should be labeled as such.** Four points for positive pressure in CHFE, eight for the mask in AFRVR, are authored numbers. No trial supports a specific figure, the patient in front of you is not the mean of a trial population, and the review packet should say so rather than implying the simulator is modeling physiology. Put the reasoning in a `note` on the effect; the field is carried through and printed nowhere, which is what a note to a reviewer should be.

**An effect follows the patient into the next phase, and that is where it makes text false** (v0.21 to v0.23a audit). An effect acts in every non-terminal phase its `while` allows. With no `while` it acts in all of them. With no `duration_seconds` it never ends. Everything else the case says about a number is written against the phase's authored vitals, so an effect that is acting makes that text wrong on the monitor. Three rules follow.

- **Timed narration.** A narration on a timed transition quotes no number unless you have checked every effect that can be acting in the destination phase (9.5).
- **Study reports and exam lines.** A report or a finding that quotes a vital sign is false for as long as an effect on that vital is acting. Where an effect on that vital has no end, the report and the finding quote no number for it. DKA's fluid bolus lowers the heart rate by 10 with no guard and no duration, and its ECG reports open "Sinus tachycardia at 112". After fluid the monitor reads 102 beside that report for the rest of the case. Write "Sinus tachycardia" and leave the rate to the monitor.
- **A `while` is read against the state now, not the state when the drug was given.** `while: "NOT phase is presentation"` on a drug given in the presentation phase switches on the moment she leaves it. TAKO's nitrate carried that guard with a note saying the next phase "carries the fall". The phase lowered the pressure to 82 and the effect then took off 12 more, so the nurse said 82 and the monitor read 70. If a phase already carries the change, guard the effect off in that phase by name.

Check: for each effect, write down the phases its guard allows and how long it lasts. For each of those phases, read every narration into it, every report and finding in it, and every nurse alert that quotes that vital.

**What is out of reach.** Effects add; they do not multiply, ramp, titrate, or depend on a dose, because doses are not implemented. An effect cannot read another effect. Nothing in the condition language can test a vital, so you cannot author "if the saturation is below 90, then". If your case needs any of that, it needs a phase.

### 6.2 Expiring flags: something that stops being true

An ordinary flag, once set, is set for the rest of the case. A flag granted with a duration is removed when the duration lapses, and the case can react to that:

```json
{
  "catalog_id": "nitroglycerin_sublingual",
  "flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 300}]
}
```

Then anything in the condition language can ask whether it is still acting. A transition:

```json
{"when": "action nitroglycerin_sublingual taken AND NOT flag nitrate_acting set",
 "to": "pressure_rebounds",
 "narration": "His pressure is climbing again, 178 over 98."}
```

That transition fires **on its own**, at the moment the flag lapses, with the resident sitting still. That is the whole point, and it is the thing `duration_seconds` on a vital effect cannot do.

**How grants combine.** Three rules, and you need all three because more than one action can write the same flag.

- **A permanent grant wins, in either order.** If `nitroglycerin_infusion` sets `nitrate_acting` through the ordinary `flags_set` and the sublingual dose grants it for 300 seconds, then once the drip is running the flag never expires. That is usually right, and it is the shape to reach for when a drip and a bolus are the same drug. The validator warns so that it is a decision rather than a surprise.
- **A repeat dose refreshes.** A second administration moves the deadline to the later of the two. Giving the drug again 10 seconds before it runs out buys the full duration again, not 10 seconds.
- **A lapse is not an action.** It costs nothing, appears in no timeline, and the nurse says nothing about it. If the resident should be told, author the consequence as a transition and put the words in its `narration`, which is the one place a nurse line may describe a trajectory.

**Do not put an expiring flag in a clinical tag.** It is legal, tags are re-resolved on every action, and it still will not do what you want: the set of critical actions a phase expects is computed once, when the phase is entered, so an action that becomes critical because a flag lapsed is never listed as missed in the debrief. The validator warns. Put the consequence on a transition.

**Every timed flag must be read by something.** A flag that expires and that no transition, tag, prompt guard, prerequisite or content rule tests changes nothing at all. This is the most common way the mechanism is mis-authored, and the validator warns rather than letting it look like it works.

### 6.3 Delayed onset

`onset_seconds` on a vital effect delays its start. Both it and `duration_seconds` are measured **from the administration**, so the effect acts over `[onset, duration)`:

```json
{"vital": "systolic_bp", "delta": -25, "onset_seconds": 45, "duration_seconds": 600}
```

A duration that does not outlast its onset is an effect that never acts, and the validator refuses it rather than letting you find out by playing the case. It also prints every effect's window as a note, so the arithmetic is in front of you at validation time.

### 6.4 Choosing among the five, which is the part to get right

Five constructs touch time, move a number, or count. None of them is hard to use; the mistake is reaching for the wrong one. The question that separates them is **what else in the case has to know**.

| Reach for | When | What can read it |
|---|---|---|
| A **phase** | The patient has genuinely changed clinical state | Everything |
| **`after_seconds`** on a transition (5.1) | The lesson is that something had to happen sooner | Everything, since it changes the phase |
| **`flags_set_timed`** (6.2) | Something is true for a while and then is not, and the case must react | Everything in the condition language |
| **`vital_effects`** (6.1) | A number on the monitor moves and nothing else does | Nothing. Display and audio only |
| **`flags_set_repeat`** (6.5) | The act has to be performed more than once before it works | Everything in the condition language |

Worked examples of the choice, all of them things an author will actually want:

- *"BiPAP raises the saturation while the mask is on."* One vital effect, guarded on not being intubated. Nothing else in the case needs to know, so nothing else is involved.
- *"Sublingual nitrate raises the saturation for thirty seconds."* One vital effect with a duration. No flag: nothing reacts to it running out.
- *"The nitrate wears off and the pressure rebounds, and the resident has to notice."* An expiring flag, plus a transition guarded on it, plus a `narration` on that transition. The rebound is a phase, because the patient really is different.
- *"Steroids take twenty minutes to do anything."* An onset. And be honest about whether a twenty-minute onset means anything in an eight-minute case: usually it means the case should not model it at all.
- *"The patient deteriorates if nobody gives antibiotics."* A time-guarded transition, section 5.1, with all six of its fairness rules.
- *"One dose slows him a little and two doses get him where you want him."* A vital effect for the partial response, a repeat-granted flag for the second dose, and the phase guarded on that flag. Plus a `nurse_alert` saying the drug takes time, or the resident reads the partial response as a failed drug and reaches for a different one.

**The two bottom rows are designed to be used together.** When a drug both shows on the monitor and changes what the case will do, put the clock in the flag and guard the effect on the flag:

```json
"flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 30}],
"vital_effects": [{"vital": "oxygen_saturation", "delta": 5,
                   "key": "nitrate_spo2", "while": "flag nitrate_acting set"}]
```

One deadline in one place. Writing the 30 seconds twice, once as a duration and once as a flag, gives you two deadlines that drift apart the first time either is edited.

**A phase is not expensive, and reviewers can only see phases.** It is the only construct the per-key review matrix shows, and the only one that can change an exam finding, a lab, a consultant's advice or what the patient says. If the patient is genuinely worse, that is a phase, not a negative delta on a heart rate.

### 6.5 Flags granted on the Nth administration

Section 15 says flags are binary and permanent and tells you not to build cases that depend on redosing. That holds for everything except the case whose lesson **is** the redose: an act that produces a partial response the first time and works the second. Author it on the action:

```json
{ "catalog_id": "digoxin_bolus",
  "flags_set": ["rate_control_given"],
  "flags_set_repeat": [{"flag": "rate_control_adequate",
                        "after_administrations": 2,
                        "counter": "rate_control_doses"}] }
```

| Field | Required | What it does |
|---|---|---|
| `flag` | yes | Granted permanently once the count is reached |
| `after_administrations` | yes | At least 2. One is what `flags_set` already does |
| `counter` | no, defaults to the act | The tally this administration adds to |

**The counter is the interesting field and it is a clinical judgment.** Left to default it counts the act, so a sibling covered through `also_covers` adds to the same tally and two routes to one act are two doses. Named explicitly, several separate case actions share one tally, which is what you want when four different drugs are four attempts at the same physiological maneuver. Getting it wrong is silent: two actions granting one flag at different totals means whichever tally fills first wins, and the validator warns rather than guessing which you meant.

**Two flags, not one, and both earn their place.** `flags_set` fires on every administration including the first and is what says an attempt has been made; the repeat flag is what says enough attempts have been made. A case usually needs both, the first to drive a vital effect and a follow-up obligation, the second to drive the phase.

**The partial response belongs on a vital effect, not on a phase.** A first dose that moves a number and changes nothing else is exactly what 6.1 is for, and making it a phase costs you a phase for every combination of it with everything else in the case. Guard the effect off in the phases whose authored vitals already carry the controlled number, or it is subtracted twice.

**Say so out loud.** Pair it with a `nurse_alert` (9.1). A partial response with no explanation reads as a failed drug, and what a resident does about a failed drug is reach for a different one, which in a case whose lesson is the redose is precisely the wrong move.

**Two more uses, and what each cannot see** (v0.23). DKA uses the same field for things that are not a redose.

*A restart.* No action restarts a stopped infusion, so DKA reads the second administration of insulin as the restart: `{"flag": "insulin_restarted", "after_administrations": 2, "counter": "insulin_starts"}` on the infusion and on subcutaneous insulin. The count knows nothing about what came between the two. Two orders with no hold between them set the flag. An insulin given through an action outside the counter, such as a bolus, is not counted, so a learner whose first insulin was the bolus needs two more orders to "restart". List every action that is the same act on one counter, and write a scenario for each first dose.

*A repeat study.* A study can carry the field too, and the flag is granted before that order's result is frozen, so the second order's own result can resolve against it. DKA grants `chem_repeated` on the second chemistry. The flag says the study was ordered twice. It does not say the second order came after anything. A repeat sent before the treatment sets it. Do not use it to discharge "repeat the level after replacement". Use the pattern in 8.2.

**What it still cannot do.** Nothing counts doses in the condition language and nothing ever will, for the same reason time does not: the per-key review matrix has to stay finite. A case reads the count only through the flag it grants. There is no way to make a third dose differ from the second, no way to decay a tally, and no way to make a dose count for less because it was late.

### 6.6 What none of this can do

Each of these looks authorable until you try it.

- **Nothing depends on dose.** Doses are not implemented. Two boluses are two administrations of the same thing.
- **No condition can test a vital.** You cannot author "if the saturation is below 90". The condition language sees phase, flags and study state, which is what keeps the review matrix finite. Branching on a number means the number has to be a phase.
- **A result never sees an effect.** A gas ordered while an effect is running reports the phase's authored payload and will disagree with the monitor beside it. Do not author around it; know about it when a reviewer calls it a bug.
- **Effects add, clamp and snap.** No compounding, no titration, no gradient. The five-second travel between values is a display courtesy, not a model.
- **Exams, labs, consultants and patient answers never vary with the clock.** They vary with phase, flags and study state. A finding that must change after five minutes needs a phase, reached on a clock.

### 6.7 The resident sees no vitals until they attach a monitor

The monitor is dark when the case opens: every cell reads a dash, and there is no heartbeat. Both arrive when the resident takes the action carrying the catalog's `reveals_vitals` capability, which is `attach_monitor`. Nothing you author changes this and no case can turn it off.

**The splash screen does show the arrival vitals**, read from your first phase, as figures on a pale panel. That is a handover artifact, not the monitor: it is what somebody measured before the resident walked in. What the resident still has to earn is the current number and the trend. Two things follow for you: the first phase's vitals are now read by a learner before the case starts, so they are the numbers the case is introduced by; and a handover that quotes a saturation should quote **that** one. The validator warns if the two disagree.

Two consequences for authoring, and the first is easy to get wrong:

- **An arrival-phase prompt must not assume the resident can see a number they have not obtained.** A prompt reading "his sat has dropped" implies the resident is watching a trend on a screen that may still be dark. The nurse volunteering a number outright is fine and does more work than it looks like it does.
- **A prompt that quotes a number is bound to the phase whose number it quotes, and nothing checks that.** Prompts are scheduled per phase, for every action that is critical in the phase being entered, and the text is one string for all of them. CHFE's mask and nitrate prompts each quoted an arrival vital sign, and when the case was restructured they began firing in three phases with three different saturations and two different pressures. Both had the figure taken out of them, which is a real loss. If you want the figure, the action needs a prompt per phase, and the schema does not have one: this is a gap rather than a rule.
- **Attaching the monitor is worth tagging.** It was previously an action with no perceptible consequence, which is an action a learner is entitled to skip. It now gates the whole monitor, so give it a tag and a debrief note rather than leaving it neutral.

---

### 6.8 Credit that depends on when, and a handover that shows the truth (v0.20)

Two optional fields, both added for AFRVR on a physician's decision.

**`also_satisfies` on a case action.** A list of `{"id": <case action>, "when": <condition>}`.
When the action is taken and the condition holds at that moment, the named action counts as
satisfied: its critical expectation is met, its prompt stops and follow-ups that name it are
discharged. The action keeps its own tag, flags and note. Use it when the same drug is right
at one point and wrong at another and the order is the lesson. AFRVR's metoprolol is
discouraged before positive pressure and satisfies critical rate control after it. Do not use
it where two entries are simply the same act. That is `also_covers`. The condition is judged
before the action's own flags are granted, so an action cannot satisfy its own condition.

A `when` of null always holds (v0.22). Use that form for an act that discharges another action's
expectation and still needs its own tag, result or vital effect. TAKO's norepinephrine satisfies
the vasoconstrictor and keeps its own heart rate effect. DKA's arterial gas satisfies the venous
gas and keeps its own result. `also_covers` would lend it the other action's fields instead.

What the condition can see: the phase, the flags, and the studies ordered and resulted at the
moment the button is pressed. What it cannot see: the clock, a vital, or what happens next. The
target must be a case action and cannot be the action itself. The validator checks both.

**`inherit_vitals: true` on a terminal phase.** The phase shows the vitals of the phase the
run came from, with the effects acting at that moment, instead of its own authored numbers.
Use it on `case_complete` so a learner who hands over a patient they never treated is not
shown a better patient. The authored vitals stay as a fallback and are still validated.

### 6.9 A disposition that has a consequence instead of ending the case (v0.21)

Confirming a handoff ends the run. A case may say that one disposition, chosen in a state
it names, does not:

```json
"handoff": { "disposition_intercepts": [
  {"disposition": "discharge_home",
   "when": "(phase is presentation OR phase is fluid_responsive) AND NOT flag discharge_attempted set",
   "action": "attempt_discharge"} ] }
```

When the resident confirms that disposition and `when` holds, the interface logs `action`
in place of `handoff_submit`, clears the chosen disposition and returns to the Stabilization
tab. The diagnoses already listed are kept. The first matching rule wins.

The action is a case-only action (7.1). Give it a tag (`discouraged`), a flag, a
`narration_override` and a debrief note. Give it a binding-map row with `catalog_id: null`
and an `unmatched_placement` on the `handoff` tab, which draws no buttons and is not read by
the microphone. **The placement is required.** Without it the build does not create the
action, the engine skips the rule with no error, and the disposition ends the run as if you
had authored nothing. Mark the action `"hidden": true` to keep it out of search. `hidden`
does not remove a button from an action tab, so do not rely on it for an action placed
anywhere else. Put the consequence on a transition guarded on the flag, timed from
`guard_true`, so the nurse can say what happened. Include `NOT flag <the flag> set` in
`when`, or the resident can never hand that disposition over at all.

Use it for a discharge the patient does not survive leaving on, where ending the run would
teach the verdict and letting it play out teaches the reason. Do not use it to block a
disposition you simply disagree with. The payload is never visible to the condition
language, so the review matrix is unchanged.

## 7. Actions and clinical tags

### 7.1 Actions come from the catalog, with one recorded exception

The global catalog defines every drug, exam maneuver, lab, imaging study, ECG, consultant, stabilization task and procedure across the product, with names, tab placement, turnaround class, narration templates, default prerequisites and default results. It holds no case-specific clinical judgment.

**The resident sees the whole catalog.** Actions your case never mentions are still on the menu, are inert and neutral, and return the catalog default. This is deliberate: a menu showing only the relevant actions gives away the answer.

**The rule: a missing action is a catalog change request first.** Add the entry in `catalog/build_catalog.py`, marked author-supplied, regenerate, and bind it. Every pack then shows the button, so it gives nothing away, and it gets rows in the voice table. TSS, DIPH and DKA each got their missing action this way. Record the request in the case file's `catalog_change_requests` either way.

**The exception: a case-only action** (v0.22). A case may carry an action the catalog does not have when the directing physician decides the act belongs to that case alone. Four conditions, all required:

1. The decision is recorded in the SEED with the person's name and the date.
2. The binding-map row has `catalog_id: null`, an `unmatched_placement` naming the `tab` and the `group`, and an `unmatched_narration`, which is the nurse line when the action carries no `narration_override`.
3. The case action is authored like any other, with a tag and a debrief note. The start of its id decides its category. `consult_` is a consultant and returns content from `content_keys.consultants`. `exam_` is an exam. `labs_`, `echo_`, `cxr`, `ct_` and `pocus` are investigations. Any other id is an order with no result. A case-only consultant that sets a flag needs `state_changing: true`, like any consult that does (11.5).
4. The SEED says what the button costs, in these words or better: a button unique to one case tells the learner it matters, and it is not in the voice table.

```json
{"case_id": "consult_activate_cath_lab", "catalog_id": null,
 "note": "Case-only button on the Consults tab, on the directing physician's instruction of 6 October 2026.",
 "unmatched_placement": {"tab": "consultations", "group": "Consultations"},
 "unmatched_narration": "Calling the cath lab activation now."}
```

A placement in an existing group draws an ordinary button there. A placement with no group, or in the group `Not in the catalog`, draws it under that heading with a note saying a resident would not see it in the real product. A row with no `unmatched_placement` is not built at all: no button, no error, and the build notes list the action as unreachable. The validator warns for every case-only action and names them. It errors only when the row's note starts with `BLOCKING`.

Two case-only actions exist beside TAKO's button, and neither is a button. `handoff_submit` is in every pack, placed on the `handoff` tab. TSS's `attempt_discharge` is the action a disposition intercept logs (6.9).

**`voice_phrases`: spoken phrases for one action in one case** (v0.24). The voice table is keyed by catalog id, so a case-only action has no row in it. The microphone knows it by its display name and its id and by nothing else. At v0.22 TAKO's Activate Catheterization Lab answered to "activate catheterization lab" and not to "cath lab", "call the cath lab" or "stemi alert". A case action may carry `voice_phrases` to fix that:

```json
{"catalog_id": "consult_activate_cath_lab",
 "voice_phrases": ["activate the cath lab", "cath lab", "call the cath lab", "stemi alert"]}
```

The contract:

- A list of non-empty strings, each with at least one letter or digit. Anything else is a validator error.
- Each phrase is normalized the way speech is: lower case, punctuation dropped, filler words and bare numbers removed. Write it the way a resident says it.
- The phrases are indexed when the case is bound, ahead of the global table. In that case they win over a table row with the same words. Check that you are not taking a phrase from a catalog entry the learner still needs.
- Any case action may carry the field, not only a case-only one. The action must sit on a tab the microphone reads: Investigations, Stabilization, Interventions, Exam or Consults. Phrases on an action on the `handoff` tab do nothing.
- A covered sibling does not borrow the phrases. They name the action that authors them.
- The same phrase on two actions is offered to the learner as a choice, and the validator warns.
- A phrase that normalizes to nothing, or to a bare qualifier such as "bolus", "drip", "oral" or "repeat", is dropped without an error. Test each phrase in the built simulator.

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

The field names, for reference. Every one is read by the engine. A field not in this table is a note to the reviewer and changes nothing.

| Field | What it does | Section |
|---|---|---|
| `catalog_id` | The case action's id. A catalog id, or the case's own id where a binding row maps it | 7.2 |
| `tag` | Ordered rule list of clinical tags | 7.3 |
| `display_name` | Replaces the catalog name on the button. Not borrowed by a covered sibling | 7.1 |
| `expectation_label` | The name the debrief uses for this act in the critical action lists. Use it when the action covers several entries, so a learner who gave amiodarone is not told they completed "Digoxin bolus". The button keeps its own name | 7.1 |
| `flags_set`, `flags_set_timed`, `flags_set_repeat` | Flags granted for good, for a time, or on the Nth administration | 6.2, 6.5 |
| `vital_effects` | Numbers the action moves on the monitor | 6.1 |
| `prerequisites`, `prerequisite_overrides` | Added gates, and catalog gates waived | 8.1 |
| `follow_ups_triggered` | Follow-up ids this action starts. This list is what schedules them | 8.2 |
| `also_satisfies` | Credit for another action, with a condition | 6.8 |
| `prompt` | `deadline_seconds`, `text`, optional `guard`, optional `escalation` | 9.4 |
| `narration_override`, `nurse_alert` | The nurse's line, replaced or added to | 9.1 |
| `halt_reason` | Shown when the tag resolves to harmful | 7.1 |
| `debrief_note`, `references` | The teaching note and its sources | 13 |
| `state_changing` | `true` makes a consult state-changing, so it sets its flags and transitions are checked. A consult is observational without it. Exams never change state | 11.5 |
| `turnaround_override_seconds` | A study's turnaround in this case. Leave unused | 4 |
| `hidden` | Keeps the action out of search. It does not remove a button | 6.9 |
| `voice_phrases` | Spoken phrases for this action in this case (v0.24) | 7.1 |

Transitions live on phases, not on actions. Section 5 is authoritative.

### 7.2 Binding to the catalog

Every case action has a row in the pack's binding map, `<PREFIX>-binding-map.json`. `engine/bind_catalog.py` derives a status for each row: `exact` when the case id is the catalog id, `mapped` when the row names a different catalog id, and `unmatched` when the row's `catalog_id` is null. A row may also carry `also_covers` or `also_covers_group` (3.4), and a case-only row carries `unmatched_placement` and `unmatched_narration` (7.1).

**Every `mapped` row is a clinical judgment and needs your signature.** Look particularly for:

- **Assay mismatches.** A numeric high-sensitivity troponin I does not transfer to a qualitative troponin T entry. A BNP does not transfer to an NT-proBNP entry (the catalog carries NT-proBNP, `nt_probnp`, and no BNP). Same analyte family, different reference intervals, different numbers.
- **Route and formulation splits.** A bolus and an infusion are different catalog entries and often different clinical acts.
- **Composite actions.** A combined lung and cardiac ultrasound may be two catalog entries. A combination nebulizer may be two drugs. Bind to both or the unbound half is unreachable.
- **Collapsed entries.** Where the catalog collapses two acts you score separately, the interface can offer only one button and the second is unreachable. Decide which one it should be.

**`unmatched` is a decision, and the validator warns until someone has made it.** An unmatched row means the case has an action the catalog does not. There are three ways to settle it, in this order of preference.

1. Request the catalog entry and bind to it. This is the rule (7.1).
2. Change the case so it does not need the action.
3. Keep it as a case-only action, by the directing physician's decision recorded in the SEED, with all four conditions in 7.1 met.

The validator prints one warning naming every unmatched action, and that warning stays for as long as the action is case-only. It is an error when the row's note starts with `BLOCKING`, which is how an author marks an action the case cannot run without and the catalog must supply. An unmatched row with no `unmatched_placement` is the dangerous state: the validator still only warns, and the action is unreachable. A case action with no row at all is an error.

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

**Use `discouraged` for traps.** Before v0.3 a trap that was wrong but survivable could only be neutral, which meant it carried no weight and taught only through a note the learner might not read. Morphine in acute pulmonary edema, a bronchodilator for cardiac asthma, unindicated steroids or antibiotics, an unnecessary CT: these are `discouraged`.

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

**Blocked actions stay visible and selectable, and unannotated.** Hiding or graying out teaches nothing. Neither does printing "needs a line" on the button: that turns a lesson into a label and makes gated actions visibly different from ungated ones. Let the resident attempt it and read why it failed.

### 8.2 Follow-ups create an obligation afterwards

A follow-up is triggered by an action and becomes due after it. It cannot gate the triggering action, because the triggering action must happen first.

Post-intubation analgesia and sedation are the canonical example. They cannot be prerequisites of intubation. They are enforced by nurse prompting and surfaced as omissions in the debrief.

Each follow-up requires:
- **condition** determining whether it applies in this case, since not every intubated patient needs the same follow-up
- **deadline** measured from the triggering action
- **nurse prompt text**
- **debrief note**
- **`satisfied_by`**: every case action that discharges the obligation, or
- **`satisfied_when`**: a condition that discharges it, where a list of actions cannot

The field names are `applies_when`, `deadline_seconds`, `nurse_prompt`, `debrief_note`, `triggered_by`, `satisfied_by` and `satisfied_when`. The validator requires the first four, so a follow-up that always applies still needs an `applies_when`, usually the flag its trigger sets.

**One of the two is mandatory.** A follow-up with neither is an obligation the debrief reports as left open however the resident plays, and the validator refuses it.

**`satisfied_when` exists because `satisfied_by` is set membership and cannot express "again".** An obligation to repeat a dose is created by the first dose and would be discharged by it, because the action that would satisfy it is already in the taken set. Author it against the flag the repeat grants instead (6.5). Anything the condition language can say is available, so the same field also covers "unless they intubated instead".

**List every satisfier.** If sedation may be propofol or ketamine and you name only propofol, a resident who chose ketamine is told they left a paralyzed patient unsedated. Each id in the list must be a case action, so bind every satisfier. An entry covered through `also_covers` satisfies its covering action, so name the covering action once.

**How a follow-up runs** (v0.21 to v0.23a audit). Four facts, each of which a pack has got wrong.

- The engine schedules a follow-up from the triggering action's `follow_ups_triggered` list. The follow-up's own `triggered_by` is checked for unknown ids and is not read when the case runs. Keep the two in step by hand. If two actions trigger it, both carry it in `follow_ups_triggered` and `triggered_by` lists both.
- Each administration of the trigger schedules its own check, `deadline_seconds` later. The difficulty mode multiplies that deadline (9.7).
- `applies_when`, `satisfied_by` and `satisfied_when` are all read when the deadline arrives, not when the action is taken. So `applies_when` can name a phase the action leads to. DKA's dextrose follow-up is triggered by insulin and applies only in the treated phase that insulin produces ten seconds later.
- `satisfied_by` asks whether a listed action has ever been satisfied in the run.

**`satisfied_by` cannot say "again" or "after".** An act done before the trigger discharges the follow-up before it exists. TAKO asked the learner to listen to the chest again after a fluid bolus and listed the chest exam, the lung ultrasound and the chest film. A learner who examined the chest on arrival, as most do, was never asked. A learner who never examined it was asked to listen "again". Check: for each id in `satisfied_by`, ask whether a learner could reasonably have done it before the trigger. If so, `satisfied_by` is the wrong field.

Two tools express it, and each sees something different.

| Use | It can see | It cannot see |
|---|---|---|
| `satisfied_when` with a flag from `flags_set_repeat` (6.5) | That the act has been done N times in the run | Whether the Nth time came after the trigger. A repeat sent before the trigger counts. Right for "give a second dose", where the first dose is the trigger. Wrong for "repeat the level after replacement" |
| `satisfied_when` with a phase or an ordinary flag | The state at the deadline | What was done to reach it, or when |
| A target action that nothing presses, credited through `also_satisfies` with a `when` (6.8) | The state at the moment the satisfying act was taken. With `when` set to the flag the trigger sets, or the phase the trigger leads to, that is "after the trigger" | A second round. Once credited, the target stays satisfied, so a later trigger is already discharged |

The third is the one for "do it again after". Author a case action whose only job is to be the target, for example `chest_rechecked`. Give it a neutral tag, a binding-map row with `catalog_id: null`, a placement on the `handoff` tab and `hidden: true`, as for the action in 6.9. On each real satisfier add `"also_satisfies": [{"id": "chest_rechecked", "when": "flag fluids_given set"}]`. Set the follow-up's `satisfied_by` to `["chest_rechecked"]`. An exam can carry `also_satisfies`, because credit is given before the engine checks whether the action changes state. This was confirmed in the engine on TAKO's follow-up: a chest exam before the bolus no longer discharged it, and one after the bolus did. No pack ships this form yet, so test it in yours.

### 8.3 Validator obligations

- Every prerequisite flag is settable by some reachable action
- No circular prerequisite chains
- Every prerequisite has a failure message
- Every follow-up has a condition, deadline, prompt, and debrief note
- Every follow-up has `satisfied_by` or `satisfied_when`
- Every `satisfied_by` id and every `triggered_by` id is a case action

---

## 9. The nurse

The nurse sits at top center and has four functions. Three are largely automatic; one needs authoring.

**9.1 Action narration.** Generated from the catalog template, for example "Giving {dose} of {name}." Exams and interview questions are not narrated. Two case fields change it, and the difference between them is which of the two things you want.

| Field | What it does |
|---|---|
| `narration_override` | Replaces the catalog line entirely. Use it only where the standard line would be wrong or confusing |
| `nurse_alert` | A second line, said straight after the catalog's own, **colored and filed in the running chart**. Use it where the standard line is correct and there is something the resident will need again later |

A `nurse_alert` is the one to reach for when a case has authored a delay or a repeat. A resident who pushes a rate-controlling drug and watches an incompletely controlled rate will reasonably conclude the drug failed; the nurse saying "these agents can take a bit of time to kick in" costs one line and prevents it. **The reason it goes in the chart is that it is needed after it has scrolled away**: the moment it matters is half a minute later, when the resident is deciding whether the drug worked, and by then the nurse's banner has moved on.

It is emitted on its own kind, so it is not a prompt: it does not consume a prompt slot, it does not trill, it is said the instant the action is taken rather than on a deadline, and it is said again on a repeat dose. Section 9.5's rule that prompt text must not imply a trajectory does not reach it, but it must still be true of what the monitor is about to show.

Both fields are borrowed by a covered sibling, so a line authored on a coverage group speaks for every route to the act. Write it so that it does: "these agents" rather than "this drug".

**Three checks on both fields** (v0.21 to v0.23a audit). Each is one string, said in every phase and for every covered sibling.

- **Name the class, not one drug, wherever a sibling can be the thing that is running.** TSS covered epinephrine, vasopressin and phenylephrine under its norepinephrine action. A learner who ordered vasopressin heard "Starting vasopressin drip." and then "Norepinephrine is running through the peripheral line". The same word was in seven transition narrations, the general status line, the monitor's `short_label` and a consultant's reply. Write "the vasopressor". Check: search the whole case for the display name of every covering action, and read each hit as if a sibling had been ordered.
- **Say nothing the action's prerequisites do not guarantee.** DKA's potassium alert said "she's on the monitor" and the action required only a line. Either add the prerequisite or cut the clause.
- **Be true in every phase.** DKA's oral potassium override said she had vomited it straight back, and in the treated phase her status line said she was no longer retching. A `narration_override` cannot vary by phase. Write a line that holds in all of them.

**Neither of these existed until v0.9**, despite this section having promised the override since v0.2. A case that authored one got the catalog line and no error.

**9.2 Result announcements.** Automatic. No authoring.

**9.3 Blocked-action feedback.** Uses the prerequisite failure message from section 8.1.

**9.4 Critical action prompts.** This is the authored part.

For each time-sensitive critical action, supply:
- **deadline**, measured from entry to the phase in which the action is critical
- **prompt text**
- optionally a **second deadline and escalated prompt**
- optionally a **guard condition**, if the prompt should only appear in certain circumstances

Not every critical action needs a prompt. Prompt for the ones where delay carries real clinical cost.

**How a prompt runs.** It is scheduled when the run enters a phase in which the action's tag resolves to critical, at that phase's entry plus the deadline. At the deadline the engine checks that the action is not yet satisfied, reads the guard once, and checks the cap. If the guard is false at that moment the prompt does not fire in that visit to the phase, and it is not retried when the guard later becomes true. The escalation is a separate event with its own deadline and the same checks. The text is one string for every phase. A covered sibling never prompts.

### 9.5 Two hard constraints on prompt text

**Prompts must not imply a trajectory.** Within a phase the patient does not change, so a prompt saying the patient is getting worse contradicts a monitor showing static vitals. Describe the current state or express concern about inaction.

**Two amendments in v0.5, both narrow.**

*The narration on a time-guarded transition is the one place a trajectory may be described*, because
one has just happened and the monitor is about to show it. "She's harder to rouse than she was ten
minutes ago and her pressure's come down" is correct there and nowhere else. The constraint on that
line is the mirror image of the constraint above: it must be true of the numbers displayed
immediately afterwards. A narration saying the pressure has fallen, on a transition whose
destination has the same systolic pressure, is the same contradiction pointing the other way. Check
each one against the destination phase's vitals; the deterioration timeline (14.2c) prints them
side by side for exactly this.

**The numbers displayed are the destination's authored vitals plus every vital effect acting
there** (v0.21 to v0.23a audit). The timeline prints the authored vitals only, and so does a
test that compares a narration with the phase. All three packs written in v0.21 to v0.23 quoted
numbers the monitor did not show. In TSS a learner who gave norepinephrine and a first bolus
heard "The norepinephrine has brought her up to 92 over 50" while the monitor read 98 over 50,
because the bolus adds 6 for 60 seconds in that phase. The rule:

- **A narration into a phase that a vital effect can reach quotes no number, unless you have
  checked every effect.** Checked means this. List every effect whose `while` allows the
  destination phase (6.1). For each one, either show that it cannot be acting when this
  transition fires, or confirm the line is true with it and without it. If you cannot do both
  for every effect, take the number out and keep the direction: "That fluid isn't holding. Her
  pressure is down again and she's getting drowsy."
- **Write the test against the monitor.** Fold a log that contains each effect-bearing action on
  the route, and compare the line with the folded vitals, not with the phase's authored ones.
- **A line that says a number fell needs a phase in which it was higher.** TAKO's "Her pressure
  dipped for a minute" introduced a phase whose pressure had only risen.

*In a phase that has a time-guarded exit, a prompt may name the consequence.* "If we don't get an
antibiotic into her, she's going to get worse" is a true statement in such a phase where it was
false everywhere before. It is still not permission to describe the numbers as moving.

- Acceptable: "He's still working hard to breathe. Do you want to do anything about the airway?"
- Acceptable: "His sat is sitting at 87 on six liters."
- Not acceptable: "He's crashing." / "His pressure is dropping."

No validator can catch this. It is a review checklist item, and it is the constraint most likely to be violated without anyone noticing, because the failure is a contradiction between the text and the monitor rather than an error in either.

**Four rules for prompt text** (v0.21 to v0.23a audit). They follow from 9.4: one string,
spoken in every phase the guard allows, with the guard read once at the deadline. No validator
checks any of them.

1. **True in each phase.** List the phases in which the action is critical and the guard can
   hold, and read the text against each one. TSS's source prompt was guarded on two phases and
   said "We've given her fluid and she's on norepinephrine". On the do-nothing path it was
   spoken in the second of them to a patient who had been given neither. A consequence counts
   too: "she is going to drop her pressure" is false in a phase where it has already dropped.
2. **No claim that a treatment was given, unless the guard tests its flag.** Either add the
   flags to the guard, or write a line that does not depend on them: "Has anyone examined her
   from head to toe?"
3. **No study finding unless the guard tests `study S resulted`.** TAKO's aspirin prompt said
   "She's got ST elevation" and fired with no ECG ordered. Add
   `study ecg_12_lead resulted` to the guard, and let the ECG prompt cover the learner who
   has no tracing.
4. **The deadline falls after the earliest moment the guard can be true.** The guard is read
   once. DKA's potassium prompt had a 45 second deadline and a guard that needed the chemistry
   back, and the nurse asks for the chemistry at 75. A learner who needed that prompt never
   heard the potassium one. The first thing said about potassium was the escalation, "Her
   potassium still hasn't been replaced". Work out when the guard can first hold for a learner
   following the prompts, and set the deadline after it. Write every escalation so that it also
   reads correctly as a first warning.

**The prompt cap can suppress a prompt a deterioration depends on, and no static check
sees it.** The validator enforces that a time-guarded deterioration is preceded by a
prompt naming the missing treatment, but it checks the deadline you authored, not
whether that prompt survives the per-phase cap. Author nine prompts into a phase with a
cap of three and the fourth onwards never fire, so the deterioration arrives unwarned.
Count the prompts in every phase that has a time-guarded exit, and make sure the ones
your guards depend on are the earliest. `engine-tests.js` checks this at runtime by
walking the do-nothing path; the validator cannot. Since v0.9 an escalation is exempt
from the cap: it neither consumes a slot nor is silenced by one, because it repeats a
warning the nurse has already given rather than raising a new one. The first warning
still has to be inside the cap.

**The cap is a case field, `prompt_cap_recommendation.per_phase`.** The engine reads it, and
the deterioration timeline marks the prompts it would suppress. It defaults to 3 when the
case authors none. Packs use 3, 4 and 5. Put the reasoning beside it in `rationale`: which
prompts fire in each timed phase, in order, and which of them the deterioration rests on. A
follow-up prompt is never silenced by the cap, and it does use a slot in the phase it fires in.

**Prompts must be helpful.** This is a teaching tool. A prompted action counts as done and is not penalized; it is only noted in the debrief so the learner can see where they needed help. Write prompts that would actually rescue a stuck learner.

### 9.6 On deadline values

Author deadlines in seconds, but expect global recalibration once the pacing is tuned. Prioritize getting the **relative** urgency right between actions in a case over any absolute number.

This applies to time-guarded transition deadlines too, with one difference: a prompt deadline that
is slightly wrong produces a prompt at a slightly odd moment, and a transition deadline that is
slightly wrong changes the outcome of the case. Get the ordering right first, meaning that every
prompt in a phase lands before the phase can end, and treat the absolute numbers as provisional. A
global multiplier for deterioration pacing is proposed but not built; see system design open
decision 10.

### 9.7 Difficulty modes change when prompts fire

The resident chooses normal or easy on the splash screen, and a case starts in normal. Normal multiplies every prompt deadline, escalation and follow-up deadline by three. It changes nothing else: turnaround, transitions and tags are identical, so the medicine is the same either way.

**Author for easy mode, then check the default mode.** The deadlines you write are easy mode's. Get the relative urgency right there, per 9.6. The default mode is normal, and its multiplier is 3. It multiplies prompt deadlines, escalation deadlines and follow-up deadlines. It does not multiply `after_seconds` on a transition, a study's turnaround or a vital effect's window.

**Rule: in the default mode, the warning for each deterioration still comes first** (v0.21 to v0.23a audit). For every deterioration timed from phase entry, take each prompt its guard rests on and multiply the deadline by 3. The result must be less than the transition's `after_seconds`, with enough left over to act on it. Equal is not enough. When a prompt and a deadline fall on the same instant, the deadline is processed first, the phase changes, and the prompt is canceled. The validator's fairness check and the deterioration timeline both use the authored deadlines, so neither sees this.

TSS and TAKO each authored a prompt at 80 seconds in a phase with a 240 second exit. Both pass the validator, with 160 seconds of lead. In the mode a learner starts in, 80 times 3 is 240, and the nurse never says it. Fix it by moving the prompt earlier (60 gives 180) or by lengthening the transition. Count the cap at the same time: the prompts that come first in the default mode must be the ones the deterioration rests on. If the physician decides a deterioration should arrive unwarned in the default mode, record that decision in the SEED and in the transition's `author_rationale`.

A deterioration timed from `guard_true` has no fixed relation to the prompt clock, which runs from phase entry. Play that route in the default mode.

**Normal mode does not slow deterioration down, and you should understand why before relying on it.**
The multiplier scales prompts only. If it also scaled time-guarded transitions, the patient would
take three times as long to deteriorate in normal mode, which would make it more forgiving at the same
time as the later prompts make it less forgiving, and the mode would stop meaning anything. Leaving
deterioration unscaled preserves the property the modes exist for: the physiology is identical in
both and only the amount of help differs. The consequence is that in normal mode a resident can
deteriorate a patient before the prompt that would have warned them has fired. That is the honest
version of the question normal mode asks, and it is the strongest argument for setting your deadlines
generously.

**What normal mode is for.** In easy mode the prompt often arrives before the resident has finished thinking, so the prompted-versus-independent report in the debrief measures reading speed as much as knowledge. Normal mode is the honest version of that question, and it means many runs will end with the prompt never firing at all. Write prompts that still make sense arriving late.

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

**This list stopped being a minimum and became the case.** Through v0.3 a resident who could not get an interview answer still had the Patient tab's background paragraph. That is gone (section 3.2). An unauthored topic is now a dead end, and a resident who hits three of them in a row concludes the simulator is broken rather than that they asked the wrong questions. Author the full list even where a topic is clinically irrelevant here, because the denial is itself the teaching (10.3).

### 10.3 Three distinct response types

Mandatory, and a common failure point.

1. **In-scope positive**: the patient has this and reports it.
2. **In-scope negative**: the patient does not have this and denies it. Pertinent negatives must be authored as their own topics with denial answers. A resident asking about chest pain in an abdominal case should hear a clear denial, not a fallback.
3. **Out-of-scope**: no topic matched. The patient gives a non-committal response revealing nothing.

A learner cannot distinguish "the patient denies it" from "the system did not understand me" if a pertinent negative falls through to the fallback, and those are clinically opposite. Authors must list the pertinent negatives explicitly. The drafting AI must not decide on its own that something is a negative rather than out of scope.

**Mark each denial topic with `"pertinent_negative": true`, and mark nothing else.** The field sits on the topic beside `answer`. Two tools read it. The validator counts the marked topics and prints them as "pertinent negatives authored as explicit denials". The matcher harness adds them to the management-changing topics, so a wrong match on one is reported with the misses that matter most (10.6). The engine does not read it. So the only check on it is you. Set it only on a topic whose answer is a denial in every phase:

```json
{"topic": "chest_pain", "pertinent_negative": true,
 "answer": [{"when": null, "value": "'No. No pain in my chest at all.'"}]}
```

DKA marked `fever_and_chills`, `headache` and `family_history`, whose answers were "I felt hot and shivery the first night", "A bit of a dull head" and "My mom has a thyroid problem". TAKO marked a surgical history that reports a gallbladder operation. The validator then reported all of them as explicit denials. Check: read the answer of every marked topic. If the patient reports anything, remove the mark.

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

#### What the matcher is, as of v0.8

Two stages, fused per topic. The architecture is in system design section 20; what an author needs to know:

**Stage one, lexical, always runs.** IDF-weighted overlap between the typed question and the variants, with a clinical abbreviation lexicon (`pnd`, `orthopnea`, `pmh`, `nkda`, `hx`, `n/v`, `lmp`, `cp`, roughly a hundred and twenty entries) rewritten into lay words **only** where the case has not itself authored that word, single-edit typo repair against the case's own vocabulary, and compound-question splitting.

**Stage two, an embedding model, is optional and may never load.** all-MiniLM-L6-v2, about 23 MB, fetched from a CDN and cached in the browser. When it is ready the two stages are combined per topic (0.6 on the model, 0.4 on the lexical score) and the best combined score wins if it clears 0.45, with two rescue branches for evidence only one stage can see. **Author as though it will never load.**

**The out-of-scope bank is part of the case.** `interview.out_of_scope_bank` is a list of questions the case has no answer to, and both stages score it like a topic under a reserved id. A question that lands closest to it gets the fallback. Do not hand-write this list: it is generated per case from `catalog/interview_out_of_scope.py` by the build (`catalog/interview_expand.py`), filtered to the concepts the case does not cover, so a case that authors a rash never has "any rash?" in its out-of-scope bank.

**The bank must not contain a question the case answers** (v0.21 to v0.23a audit). A banked question the patient can answer is refused with the fallback, and the learner is told nothing where the case has a fact. All three packs written in v0.21 to v0.23 had some. DKA's bank refused "Any weakness in your arms or legs?" and "Do you get up at night to pass water?" in a case whose clues are weakness and being up four times in the night. The filter only knows what you tell it, in two files:

- **`TOPIC_MAP` and `EXTRA_COVERED` in the pack's own `case_4_interview.py`.** `TOPIC_MAP` gives each topic the shared concepts it draws phrasings from. Every concept in the map counts as covered. `EXTRA_COVERED` lists what the pack's answers cover without drawing phrasings. (The four frozen packs keep these in `catalog/expand_interview_variants.py`.)
- **`catalog/interview_out_of_scope.py`.** Each question carries `covers`, a list of concepts or of tags from `BANK_ONLY_TAGS`. A question is dropped from a pack's bank when the pack covers any name in that list. A question with an empty list goes into every bank.

**A topic that is special to the case needs both a map entry and cover tags.** A topic left out of `TOPIC_MAP` gets no expanded phrasings and filters nothing. DKA's `weakness`, `thirst_and_urination`, `diabetes_history` and `glucose_monitoring` were the topics the case turns on, and they were the ones left out. For each such topic: add or choose a concept in `catalog/interview_phrasings.py`, map the topic to it, and then read the whole out-of-scope list against the pack's answers. For every question the patient can answer, give the entry a concept or a tag in `covers` and put that name in the pack's `EXTRA_COVERED`. List a name only when an authored answer really covers the question. The build stops on a concept, tag or topic name it does not know.

Check after expanding: read the generated bank from top to bottom beside the topic list, and ask the built simulator each question that looks answerable.

#### Variants: hand-written, expanded, and withheld

Your `variants` are yours and are never touched by tooling. Beside them, the build sets `expanded_variants` on each topic from the shared library `catalog/interview_phrasings.py`, which is keyed by concept (`onset`, `pmh`, `allergies`, `anticoag`, sixty-odd) and mixes lay paraphrase, clinical shorthand and conversational openers. Each pack maps its topics onto concepts in `TOPIC_MAP` in its own `case_4_interview.py`, and `build_case.py` calls `catalog/interview_expand.py` on every build, so the expansion is never stored in the sources and nothing per pack is added to any shared file. A new pack needs `TOPIC_MAP`, `EXTRA_COVERED` and the tagging described above. The two lists are merged into `variants` by `engine/build_simulator.py`. The four frozen packs keep their committed expansion and `catalog/expand_interview_variants.py` for it.

Every sixth generated phrasing per topic is diverted into `<PREFIX>-matcher-tune-questions.json` instead of the bank, which the build writes too. That file is the TUNING set: thresholds are swept against it. The held-out set, `<PREFIX>-matcher-eval-questions.json`, is what gets quoted, and the expansion refuses to add any phrasing that matches a held-out question. The expansion is deterministic: the same sources give the same bank.

**A held-out file is required for every pack, and it is written before the first expansion** (v0.21 to v0.23a audit). The generator can only keep a held-out question out of the banks if the file exists when it runs. With no file its check passes with nothing to check. A pack with no held-out file has not been measured, and its review packet must say so in those words. Do not describe the interview of such a pack as tested, and do not quote a number from the tuning file in its place. TAKO shipped at v0.22 with none, and its packet says so.

The file's shape, from the packs that have one:

```json
{"case_prefix": "DKA",
 "status": "HELD OUT. This set is quoted, never tuned against.",
 "authoring_note": "who wrote it, when, and in which registers",
 "management_changing": ["past_medical_history", "diabetes_history"],
 "questions": [
   {"register": "shorthand", "q": "home BGs?", "expect": "glucose_monitoring"},
   {"register": "out_of_scope_clinical", "q": "Do you get migraines with flashing lights?", "expect": null}]}
```

The two rows are there to show the shape. Keep `management_changing` and `interview.key_topics` (13.0) the same list. Include at least thirty questions with `expect` null. Write questions for the topics that are special to the case, in shorthand as well as in lay sentences. Then run `node engine/matcher_eval.mjs --only <PREFIX>`, and put the counts and every wrong-topic miss on a management-changing topic in the review packet by name.

**The library is clinical content and belongs on the review list.** A phrasing that maps a question to the wrong concept produces a confident wrong answer for every case that uses the concept.

#### Measured accuracy, v0.8

One harness, `engine/matcher_eval.mjs`, runs every pack against the built prototype. It runs the shipped `matchQuestion`, so compound questions, clause splitting, clarification and the fusion are all measured as they ship, once with the model absent and once with it present. The table below is the v0.8 measurement of the three packs that existed then, AFRVR, CHFE and MGCA. Each of those three carries thirty out-of-scope questions, the floor this section set and which none of them met before. It says nothing about a later pack. Each later pack's own figures are in its review packet, and a pack with no held-out file has none. Before and after the v0.8 work, on the held-out sets, model present:

| pack | in-scope correct | wrong topic | fell through | asked to clarify | out-of-scope refused |
|---|---|---|---|---|---|
| AFRVR | 39/52 → 46/52 | 6 → 2 | 5 → 1 | 0 → 4 | 11/30 → 24/30 |
| CHFE | 40/46 → 39/46 | 5 → 4 | 0 → 2 | 0 → 1 | 11/30 → 23/30 |
| MGCA | 23/37 → 26/37 | 6 → 3 | 5 → 3 | 0 → 3 | 9/30 → 21/30 |

Read the columns separately, because they are not equally bad. **Wrong topic** is the number this section has always said matters most, and it roughly halved. **Asked to clarify** is new: the patient names the two topics the matcher could not choose between and commits to neither, which costs the learner a turn and is visible, where a wrong topic is neither. Of the eight clarifications on the held-out sets, four had the right topic in the pair, two replaced a wrong answer, two replaced an out-of-scope false accept. **Out-of-scope refused** doubled, and that is almost entirely the bank.

CHFE moved least because its held-out set was already mostly well-formed lay sentences, which is the register this section warns an author's own set over-represents; its three remaining wrong answers are genuine ambiguities ("does lying flat make it worse" sits between orthopnea and aggravating factors for both stages).

**What is still unmeasured.** Nothing here was collected from residents. The held-out sets were written by an AI assistant and a case author, and the tuning sets are the library's own withheld phrasings, so they measure the matcher against the registers the library anticipated. An opt-in export of real question logs remains the best evaluation source that exists and does not yet exist here.

#### The rules that follow from this

**The number to watch is the wrong-topic rate on topics whose answers change management.** Each held-out file lists those topics under `management_changing`; the harness reports them separately.

**Measure it, and measure the shipped matcher.** `node engine/matcher_eval.mjs --semantic` quotes the held-out sets. `--sweep` reads only the tuning sets and refuses to run without one. Do not tune against the held-out set and then quote it; that measures memorization rather than coverage.

**The extraction contract.** The harness slices two regions out of the built file by marker comment (system design 20.3) and evaluates them with a shim for the model. Anything placed in those regions is measured; anything after `bindCase()` is not.

**Write held-out questions in the register you expect, not the register you write variants in.** If every question in your held-out set is a well-formed lay sentence, your set will report that the matcher is fine no matter what you do to it.

### 10.7 The patient's side of the conversation

New in v0.8, and the reason "natural" is now partly an authoring property. Each topic may carry two more fields; system design 20.4 has the mechanics.

**`echo`**: a short phrase in the patient's voice naming the topic ("my tablets", "when it started", "the spots"). Used as a prefix when the matcher's confidence was marginal, so a wrong match is visible at once, and inside the clarifying question ("Sorry, do you mean when it started, or whether it's getting worse?"). Every topic should have one; the phrase should read after "do you mean".

**`facts`**: the atomic pieces of the answer, each with its own phrasings and a phase-conditional value, so a follow-up is answered by the piece asked about. The rule that keeps facts and paragraph consistent: **a fact restates part of the paragraph and adds nothing to it.** Mark one fact `restate` to be the short form the patient gives when asked the topic again. Author facts where sub-questions matter: onset (when versus how), medications (what versus dose versus adherence), the presenting complaint's character, anything with a time course. Facts are optional and packs differ (v0.21 to v0.23). `catalog/author_interview_facts.py` writes them for AFRVR, CHFE and MGCA, eight topics each, and knows no other pack. DIPH and TSS author three topics each in their own `case_4_interview.py`. TAKO and DKA author none, so a follow-up such as "what dose?" gets the whole paragraph again. A new pack authors its facts in its own sources.

Without facts a topic still gains repeat handling, "anything else?", and the echo. With them it gains follow-ups and partial answers.

**`adjacent` and `volunteer`** (v0.18a): a real patient answering "when did this start?" says how it has gone since. A topic may list up to two `adjacent` topics. When it is first asked, the `volunteer` line of each adjacent topic that has not been spoken about is added to the answer in the same voice, and the adjacent topic counts as asked, for the History score and for any `interview_topic_` action. Rules:

1. A volunteer line is one short clause, under 25 words, restating part of that topic's own answer. It adds nothing, and it does not repeat what the answer it rides on has just said. It may be phase-conditional like an answer; a rule whose value is null volunteers nothing in that phase.
2. Safety screens go in `interview.must_ask` and are never volunteered: allergies, recreational drugs, pregnancy, sexual and menstrual history, self-harm and intent, anticoagulant and bleeding history, goals of care, and anything the case is built around the learner discovering. The validator refuses a must-ask topic that carries a volunteer line or is listed as adjacent.
3. Nothing is volunteered while a global rule speaks for the patient, or while `interview.volunteer_blocked_when` holds. Use it for a patient too confused or too breathless to say more than was asked.

`catalog/author_interview_volunteers.py` holds the lines for AFRVR, CHFE, DIPH and MGCA. TSS, TAKO and DKA author `adjacent`, `volunteer`, `must_ask` and `volunteer_blocked_when` by hand in their own `case_4_interview.py` (v0.21 to v0.23). Do not run either script on a pack it does not list. A new pack authors these fields in its own sources.

**Do not author the scaffolding into answers.** "Like I said", "Sorry, do you mean", "No, that's everything" come from `interviewDefaults` and may be overridden per case under `interview` (`repeat_prefixes`, `clarify_template`, `nothing_more`). An answer that begins "As I said" will read wrongly the first time it is given.

---

## 11. Content rules for exam, labs, imaging and consultants

All use the same structure: a key owning an ordered rule list, unconditional default last. What changed in v0.3 is the shape of the value.

### 11.1 The default rule, and why it is dangerous

Resolution order is: **your case content, then the catalog default, then an error.**

The catalog default is normal. So a study you forget to author does not fail; it returns a normal result, confidently, and teaches the resident the wrong thing with no error raised anywhere.

Three defenses, all of which should be used:

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
| **Peripheral or pedal edema** | `exam_card` |
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

**Spelling** (v0.18c): US spelling everywhere a learner reads (hemoglobin, edema, color, liter, maneuver). Interview variants may keep a British alternate beside the US one so that either matches.

**Keep a finding to a chart line** (v0.18a): about 15 words, abnormal findings first, pertinent negatives only where they carry the case (no neck stiffness in a febrile patient, no calf asymmetry with leg swelling). Clipped phrases are fine. Interpretation ("this is carbon dioxide, not a neurological event") belongs in the debrief note, not in the finding. The catalog defaults follow the same rule, so an authored abnormal finding stands out against them.

**A finding that quotes a vital sign must survive the vital effects** (v0.21 to v0.23a audit). The monitor shows the phase's number plus any effect acting (6.1). DKA's circulation exam said "Pulse about 100" in a phase where the fluid effect, which never ends, left the monitor at 94. Where an effect on a vital has no end, findings quote no number for that vital. Write "Pulse fast".

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

`kind` is `panel` for multi-analyte results, `value` for single ones, `report` for imaging and ECG narrative, and `image` for a study shown as a picture. Two more kinds belong to the exam keys and are not study results: `exam_findings` on each maneuver (11.2) and `general_status` on the status line (11.3). Each carries `abnormal` and a `findings` string, and the validator requires both.

**Each lab and imaging key is a block with `rules` and `changes_with_state`.** `rules` is the list the engine resolves. `changes_with_state` is `true` when the rules give different values in different states and `false` when one value serves every state. Every pack sets it on every key. No tool reads it. It tells the reviewer which keys to read across phases in the matrix, so keep it honest when you add or remove a rule.

```json
"lactate": {"changes_with_state": false,
            "rules": [{"when": null, "value": {"kind": "value", "abnormal": false, "components": ["..."]}}]}
```

**Showing the study instead of describing it.** Put the file in `media/` inside the pack, named for the id the payload uses, and author:

```json
{"kind": "image", "abnormal": true,
 "image": "diph-ecg-arrival", "caption": "Twelve-lead ECG"}
```

Formats are `.jpg`, `.jpeg`, `.png`, `.webp` and `.gif`. Every file in `media/` is inlined into the build as a data URI whether or not a payload refers to it, so it costs build size permanently: put a file there when the case shows it and not before. Resize and recompress first; a twelve-lead scanned at full resolution is several megabytes and reads no better at 1400 pixels wide.

**An image payload may not also carry `report` text or `components`**, and the validator rejects one that does. Decide which the study is. A `caption` is required in practice, since the viewer has nothing to title itself with otherwise, and the validator warns when it is missing.

**A caption is a caption, not a reading.** The findings-not-conclusions rule below applies with more force here, because the whole point of showing a tracing is that the resident reads it. "Twelve-lead ECG" is a caption. So are the machine measurements a real tracing prints along its top, which a resident would have in front of them at the bedside. "Wide-complex tachycardia with a terminal R in aVR" is the answer to the question the case is asking.

**Nothing in this tool chain can check what an image shows.** The validator confirms the file exists and the payload is well formed. It cannot see that the tracing contradicts the sentence beside it, and neither can the scenario runner or the engine assertions, because to every one of them the payload is valid and the study resulted. An image is the only authored content in a case whose correctness rests entirely on a person having looked at it.

**So decide three things before you use one, and write the answers down.** Whether the picture matches the phase it is assigned to, because a tracing that contradicts what the nurse says is worse than no tracing, and worse in a way no test will report. Whether removing the report text takes a number out of the interface that the case needs a resident to be able to read, in which case it belongs in the caption. And whether some studies in the case describing themselves in text while others do not is a choice you can defend, since the asymmetry is what a learner will notice. DIPH hit all three: it shipped a wide-complex tracing under a line saying the complexes had narrowed, passed every check, and was caught by a person reading the picture and the sentence together. Section 2.9 of its review packet is the worked example.

**A file in `media/` that no payload names still costs build size**, because the build inlines the directory rather than the references. Keep source images the case does not show outside it.

**Provenance is yours to establish.** An image is embedded in a build that gets distributed as one file. Do not put anything in `media/` whose source you cannot account for.

**Author findings, not conclusions, and keep them short.** A report that ends "interpretation: cardiogenic pulmonary edema", or a tracing that explains that the ST depression is rate-related, has done the work the case was setting. Put that reasoning in the study's debrief note instead, where the learner meets it after committing to an answer rather than before. Length is the same problem in a less obvious form: a resident who reads eight sentences to find the ejection fraction is spending attention on comprehension rather than on management, and because length reads as importance, a long report about a negative study misleads. Cut the views obtained, the secondary measures that merely agree with the primary one, and the negatives nobody asked about.

**Where `comment` is shown, by kind** (the behavior since v0.9, read from `engine/ui.js`).

| Payload kind | While the case runs | In the debrief |
|---|---|---|
| `panel`, `value` | Not shown. The result is its numbers | Printed once per order under "Your results, read", below the numbers |
| `image` | Not shown | Printed the same way, below the picture |
| `report` | Not shown | **Not shown anywhere.** That debrief section skips reports |
| `exam_findings`, `general_status` | Not shown | Not shown |

`verify` is never shown to the learner, on any kind. A note addressed to the reviewing physician goes in `verify`, alongside the reference interval you are unsure of.

**What a comment may hold** (v0.21 to v0.23a audit). The learner reads it after the case, under the numbers of one result. It holds what those numbers show and nothing else. Four rules, each broken in at least one of the three packs written in v0.21 to v0.23.

- **Not the diagnosis.** DKA's gas comment read "A pH above 7.25 with a bicarbonate of 15 to 18 in an alert patient is mild ketoacidosis", which is one of its learning objectives stated for the learner. TSS's urinalysis comment named toxic shock.
- **Not the lesson.** "Potassium 3.1 is low before any insulin, which is unusual in ketoacidosis and changes the order of treatment" belongs in the potassium action's debrief note.
- **Nothing from another result or from the history.** "the potassium has fallen from 3.1 to 2.9" is printed even when the learner never sent the first sample. TSS's blood count comment mentioned day five of her period in a case where nobody mentions her period.
- **Nothing to the reviewer.** "The case shows the same picture in every phase, which is a simplification" goes in `verify`.

A comment that passes, for example: "Anion gap 18, calculated without potassium." Put everything else in the debrief note of the study's case action. A study with an authored abnormal result and no case action has no note and no tag, so bind it as a case action. And never put text you need the learner to read in the `comment` of a report. TAKO's echo comment "With the murmur this is outflow obstruction" was never displayed.

**You set the abnormal flag; the renderer does not compute it.** Flagged components display distinctly, currently in red. Two reasons the renderer stays out of it: reference intervals are assay- and institution-specific, and the interpretation is often not the number, since a pO2 of 95 is normal on room air and alarming on a non-rebreather.

**This means sign-off is now two things per value**: the number is right, and the flag is right. A value you consider abnormal that carries no flag displays to the learner as normal, and no other check will find it. The validator cross-checks parseable reference intervals against the flags and will tell you where they disagree, but it can only check ranges it can parse.

Where you are not certain of the reference interval, add a `verify` note rather than guessing. Where the catalog has a default for the same analyte, use its interval so the case and the default agree.

A result **freezes at the state in which it was ordered**, not when it arrives. Confirm that any study likely to be repeated has authored values across the phases where it might be drawn. If a case needs a result to reflect post-intervention state, require a repeat order.

**Serial testing cannot be represented.** A repeat study in an unchanged state returns an identical value, so a rising troponin cannot be taught mechanically. Teach it in the debrief note instead; do not fake a delta by gating on an unrelated flag.

A result may be keyed on a flag that is related, inside one phase (v0.23). DKA's chemistry reads differently once fluid or bicarbonate has been given, so a repeat sent after either shows what it did. Two limits. Phase rules go before flag rules (section 4), so that trace disappears when the phase changes. And any text that quotes a value, such as a consultant's line or a debrief note, has to be true for every variant the learner may have on the chart (11.5).

**A report that quotes a vital sign must survive the vital effects.** The same rule as for a finding in 11.2. An ECG report that opens with a rate is false whenever an effect on the heart rate is acting. Leave the rate out of the report where an effect on it has no end.

### 11.5 Consultants

The most state-dependent key in the case.

- Content referencing a finding must gate on `study S resulted`. A consultant must never discuss imaging that was never obtained, and must not discuss a result that has not come back yet.
- **Every tier that names a value tests `study S resulted` for the study it came from, and that includes the deteriorated-phase tiers** (v0.21 to v0.23a audit). A phase rule goes first in the list, so it is the tier most often written with no study guard. DKA's intensivist said "A potassium of 2.6 with ectopy needs a monitored bed" in the falling phase to a learner who had sent no chemistry. Split each such tier in two: one guarded on the phase and the study, which may quote the value, and one on the phase alone, which describes what is visible and asks for the study. Check: search every consultant value for a digit, and for each hit confirm the rule's `when` tests the study.
- **A quoted value must be the value on the chart.** If the result varies with a flag inside the phase, the consultant cannot quote one variant. DKA's endocrinologist said "A potassium of 3.1" to a learner whose only chemistry, sent after fluid, read 3.0. Say "A potassium that low".
- **A tier that says a treatment was given tests its flag.** TSS's intensivist said "Fluid in, norepinephrine running, source out" on a rule that tested only the last two.
- **A consultant who declines must not give credit.** A state-changing consult sets its flags and satisfies its expectation whatever the reply says. TAKO's catheterization laboratory asked whether there was a twelve-lead, and the press still counted as the critical action. If the consult needs a study first, make that a prerequisite on the action, with the request as its failure message.
- **Author a pending tier.** With a 5 to 10 second turnaround there is a real window in which a study is ordered but not resulted. A consultant asked during that window should acknowledge it. The window is 5 seconds for a twelve-lead, a plain film and any laboratory study, and 10 for CT and MRI, so a rule that depends on the window being noticed has less room than it looks.
- Order rules from most specific to least specific.
- Unrelated consultants inherit the global "does not know why they were called" response. Do not author these.
- Where a consult unlocks a disposition or intervention, it sets a flag and is state-changing. Author `state_changing: true` on the case action, because a catalog consult is observational and its flags are not granted without it. **A state-changing consult still returns content**: the two questions are independent.

A workable rule order: deteriorated-phase advice, then definitive advice once the key studies have resulted, then a holding response while they are pending, then a default asking for the workup that has not happened.

**Write the pending tier per study, not per group.** A rule reading "either study ordered" will fire when the ECG has resulted and the troponin was never sent, and the consultant will say both are in the system with nothing back, which is wrong on both counts. Enumerate the states.

---

## 12. Handoff and completion

The case completes when the resident submits a handoff and confirms. One exception: a disposition the case intercepts logs an action and the run goes on (6.9, v0.21).

Supply:

- **Correct disposition** and level of care
- **Plausible alternative dispositions**, each with an explanation of why it is wrong here, or why it is defensible with qualification
- **Correct diagnosis, as a diagnosis catalog id**
- **Plausible alternative diagnoses, as catalog ids**, meaning the common misdiagnoses for this presentation, each with an explanation
- **`disposition_display_order`**, the disposition ids in the order the Handoff tab lists them. Use one fixed order, least intensive first, so that position says nothing about the answer. An id you leave out is added at the end, with a build note

**Use catalog ids, not labels.** A free-text label that does not appear verbatim in the catalog has to be resolved by fuzzy matching, and a correct answer resolved by fuzzy matching can silently stop matching. The validator errors when an id does not resolve.

**Check that your alternatives exist.** The common misdiagnoses for your presentation are exactly the wrong answers most worth explaining, and if one is missing from the catalog a resident who picks the nearest equivalent gets a generic note instead of your teaching. That is a catalog change request.

Diagnosis is entered by searching the global catalog rather than choosing from a short case-supplied list, because committing to a diagnosis from a wide field is the cognitive task being taught. With several hundred entries most wrong answers will fall outside your authored alternatives and receive a generic note; that is acceptable for the long tail and not for the common ones.

### 12.1 Several diagnoses (v0.9)

A handover names one working diagnosis and, nearly always, the other things that are true of the patient. Since v0.9 the resident lists as many diagnoses as apply, in order; the first is the primary. Supply:

- **`additional_diagnoses`**, a list of `{catalog_id, label, explanation}`: what is also true of this patient and appropriate to name beside the primary. For an atrial fibrillation case with a flooded lung that is the heart failure, the pulmonary edema, the respiratory failure and the low magnesium. Each earns credit when listed beside the primary, and each one the resident did not name is printed in the debrief under "Also true of this patient, and not named", with your explanation, so write the explanation as the sentence you would say at the bedside about why it belongs in the handover.
- The existing **`correct_diagnosis`** is still the one the primary is scored against, and the existing **`alternative_diagnoses`** still carry the verdicts for a primary that is not it (`acceptable_with_qualification` is scored as defensible; anything else as incorrect).

A diagnosis may sit in both lists. AFRVR lists acute decompensated heart failure as a defensible alternative (the verdict when it is named as the primary) and as an additional diagnosis (the credit when it is named beside the arrhythmia). A finding the case marks "not a diagnosis on its own" as an alternative, such as MGCA's disseminated intravascular coagulation, is exactly the kind of thing that belongs in the additional list.

How the debrief reads the list: the first entry gets `correct`, `defensible` or `incorrect`; the case's diagnosis listed anywhere but first gets its own flag; every other entry is `appropriate` (in your additional list), `defensible` (an acceptable alternative) or `not supported` (anything else, with your alternative's explanation if you wrote one, or the generic note). The case's own diagnosis is printed at the end whenever the resident did not name it. The validator errors on an additional diagnosis that is not in the diagnosis catalog or that repeats the correct diagnosis, and warns on one with no explanation.

Pending or unviewed results at the moment of handoff are recorded automatically and surfaced in the debrief. No authoring required.

An early-exit option exists for a resident who cannot proceed. It produces a debrief marked incomplete.

---

## 13. Debrief notes

The debrief is the product, so these notes carry most of the teaching load. Every action referenced by the case needs one.

### 13.0 The summary's seven scores (v0.9)

The debrief's Summary prints one score per category: History, Physical, Stabilization, Interventions, Investigations, Consults and Handoff. The engine computes them from what you authored and nothing else, and it prints the arithmetic beside each one. The `clinical_domains` table is no longer printed (the field is still read by the review tooling).

- **History** is key topics asked over key topics listed. Author **`interview.key_topics`**, the topics whose answers change management in your case; without it every topic counts, which makes a thorough resident score 40 percent. AFRVR, CHFE and MGCA seed theirs from the `management_changing` list in their held-out matcher evaluation file.
- **Physical** is regions examined over the exams your case tags critical or recommended. If none is tagged (CHFE and MGCA tag every exam neutral), author **`debrief_configuration.key_exams`**; failing that every exam you author findings for counts.
- **The four ordering tabs** score critical actions at two points and recommended at one, over the critical and recommended actions that were expected on that tab in the phases the run visited. A discouraged action taken on the tab costs one point; a harmful action that halted the case zeroes its tab. A recommended tag therefore now carries weight it did not before: it is a point on offer, and a case that tags forty things recommended has diluted its critical actions. Tag recommended what you would actually want said in the debrief.
- **Handoff** is level of care (40), the primary diagnosis (40, or 60 when the case authors no additional diagnoses), and additional diagnoses named (20, pro rata); a defensible answer earns half, the case's diagnosis listed but not first earns half, and every unsupported diagnosis costs five.

The validator checks that `key_topics` name topics in the bank and `key_exams` name exams in the case. Nothing here is a claim about how residents should be ranked; the text under the table says so.

A good note states what the action does, why it was right or wrong **in this case**, and what should have happened instead. Optionally add a reference.

**Each note is collapsed behind its own expander in the debrief**, so length is not the constraint it would be if every note were printed at once. Write the note you would give at the bedside rather than a line the learner will skim. What the expander does constrain is the **first line the learner sees**, which is the action's own display name: the note has to be worth opening on the strength of that name alone.

**Reference verification markers stay in the case file and are stripped from the display.** A note ending "[UNVERIFIED, confirm before release]" is addressed to the reviewing physician, and printing it in a teaching note tells a learner to distrust the sentence they just read. Keep the markers; the interface removes them.

**The interface removes them from four fields only** (read from `engine/ui.js`, v0.18a). A marker is text in square brackets that starts with `UNVERIFIED`, `PubMed`, `VERIFY` or `MODEL OUTPUT`.

| A marker may go in | Why |
|---|---|
| An action's `debrief_note` | Stripped before display |
| An action's `references` entries | Stripped, and any bracket at the end of an entry is removed too |
| A timed transition's `debrief_note` | Stripped |
| `debrief_configuration.cross_cutting_teaching_points` | Stripped |
| Any `verify`, `author_note` or other note field | Never displayed |

**Everywhere else a marker is printed to the learner as written.** That means a follow-up's `debrief_note`, every handoff explanation (dispositions and diagnoses, correct, alternative and additional), a `halt_reason`, a `timeout_reason`, a result `comment`, and everything the nurse, the patient and a consultant say. Do not put a marker in any of them. If a sentence in one of those fields rests on an unchecked source, record that in the provenance block (section 17) and keep the sentence to what you are willing to print.

**Mark every unchecked claim that can carry a marker** (v0.21 to v0.23a audit). DKA shipped 25 learner-facing strings that cite its sources, with no marker on any of them, while its provenance block said the quotations had not been checked against the publisher's text. A reviewer reading the case file could not tell which sentences were checked. Put one marker at the end of each note that can carry one, saying what was not checked: "[UNVERIFIED: Umpierrez et al. 2024, read through a summarizing tool]".

Notes are needed for:
- Every time-guarded transition, explaining what deteriorated, why it deteriorated in that time, and which action would have prevented it. This is the note a learner reads at the worst moment of their run, so it should teach the physiology rather than restate the deadline
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
- Every phase is reachable, counting phases reachable only by the clock; every non-terminal phase has a satisfiable transition
- Every critical action is reachable
- Every action whose tag can evaluate to harmful has a halt reason
- Every prerequisite is satisfiable, non-circular, and has a failure message
- Every follow-up has a condition, deadline, prompt, and note, and has `satisfied_by` or `satisfied_when`
- Every time-sensitive critical action has a deadline and prompt text
- No condition uses a predicate outside the five permitted, in the full grammar
- Vital sign values fall in physiologically possible ranges

**Time-guarded transitions**
- `after_seconds` is an integer. A rule with no guard, or with a guard that contains the word NOT and names a flag, needs at least 30 and warns below 60. A rule timed from `guard_true` that is neither needs at least 5 and never warns. Any other rule needs at least 30 and does not warn (5.2 rule 1)
- `measured_from` is `phase_entry` or `guard_true`; `guard_true` requires a guard
- An unguarded time transition has an `unguarded_rationale`
- Every time-guarded rule carries a narration, a debrief note and an author rationale
- Every flag named in a guard is settable by a reachable action
- A terminal destination has `allow_time_to_terminal` and a rationale
- A non-terminal destination has an exit of its own
- No cycle is composed only of time edges
- **Every flag a guard requires to be unset is prompted for in that phase, at least 20 seconds before the deadline** (error)
- No prompt or escalation deadline lands at or after the phase's earliest time-guarded exit (warning)

**Payloads**
- Every authored result is a structured payload, not a prose string
- Every payload and every component carries `abnormal`
- Payload-level `abnormal` equals the OR of its components
- Every component carries a label, value and reference range
- Parseable reference intervals agree with their abnormal flags (warning)

**Catalog conformance**
- Every case action has a binding row, and a missing row is an error
- An `unmatched` row warns, and is an error when its note starts with `BLOCKING` (7.2)
- Mapped targets exist in the catalog
- A catalog entry bound by more than one case action warns
- Every catalog condition parses in the section 4 grammar
- Every catalog investigation and exam carries a default result
- The case authors no exam maneuver outside the closed set of 14
- The `general_status` key exists
- Every alertness-gated phase is covered by the global interview rule

**Silent normals**
- A study named in a condition or tagged critical but unauthored warns, naming the default that will be served

**Arrival**
- `metadata.arrival.mode` is `ems` or `triage`; a legacy prose value warns
- `metadata.arrival.location` is `resuscitation_bay`, `trauma_bay` or `patient_room`
- `patient.arrival_handover` exists and is not still the scaffold TODO
- The handover is at most two sentences (error) and about 45 words (warning)
- A handover that quotes a vital sign gets a note. A quoted saturation that disagrees with the first phase warns
- The validator prints an arrival note giving the mode, the room, the sentence count and the word count

What the validator **cannot** check is everything that matters most about the handover: whether it names a diagnosis in lay words, whether it contains a pertinent negative, and whether it is too competent. Those are review-checklist items (14.3).

**Handoff**
- The correct diagnosis and every authored alternative resolve to real catalog ids
- Every disposition intercept names a disposition the case offers and a case action other than `handoff_submit`, and its condition parses (v0.21)

**Mechanisms added since v0.9**
- `also_satisfies`: the target is a case action, is not the action itself, and the condition parses (v0.20)
- `inherit_vitals` is on a terminal phase only (v0.20)
- `flags_set_repeat`: `after_administrations` is an integer of at least 2, the flag is not also in the same action's `flags_set`, a flag nothing reads warns, and one flag granted on different counters or totals warns
- `voice_phrases` is a list of non-empty strings, each with a letter or a digit. The same phrase on two actions warns (v0.24)

**What it does not check, from the audit of v0.21 to v0.23a.** None of these is checked, and most were found in a pack that passed the validator with no errors. They are on the 14.3 checklist.
- That a narration, a report or a finding is true of the monitor once vital effects are counted (9.5, 6.1)
- That a prompt's text is true in every phase its guard allows, or that its guard can be true at its deadline (9.5)
- That a warning comes before its deterioration in the default mode (9.7)
- That a `satisfied_by` action could not have been done before the trigger (8.2), or that `triggered_by` agrees with `follow_ups_triggered`
- That a consultant tier which quotes a value tests the study (11.5)
- What a `comment` says (11.4), and whether a `pertinent_negative` topic denies anything (10.3)
- That the out-of-scope bank holds no question the case answers, or that a held-out file exists (10.6)
- That an unmatched action has an `unmatched_placement` (7.2, 6.9)
- Which of two pending timed rules fires first (5.4)

### 14.2 The review artifact

Before release, the tooling generates a **per-key review matrix**. For each key it enumerates every combination of the flags, studies, and phases appearing in *that key's own rule list*, and shows what the key resolves to in each. Study predicates take three values: not ordered, pending, resulted. For lab, imaging and exam keys the resolved payload is shown inline with abnormal components marked.

This is what the physician author reviews. It surfaces the failure mode this system is most vulnerable to: a missing rule falling through to a default that is clinically wrong in that situation, with no error raised anywhere.

**Read it in full.** On the reference case, four clinically wrong resolutions raised no error anywhere and were found only by reading the matrix. Three of the four were on the deterioration branch, which is the part of the case an author thinks about least.

Per-key enumeration can produce combinations unreachable in the real case, for example two mutually exclusive interventions both set. These are labeled rather than trusted.

### 14.2a What the matrix leaves out

Read from `engine/validate_case.py`. Know these before you treat a clean read of the matrix as a clean case.

- **It covers content keys and tags.** That is action tags, exam findings, the general status line, the figure's `rules`, labs, imaging, consultants and interview answers. It does not show prompts, prerequisites, follow-ups, transitions and their narration, vital effects, `also_satisfies`, interview `facts` or `volunteer` lines. Those are read in the case sources and tested in scenarios.
- **It stops at 96 rows per key.** A key whose rule list names more flags, studies and phases than that prints the count, the axes and the first 96 rows. Read that key's rule list directly.
- **The "reachable?" column knows two combinations.** Both were written into the tool for the first case. Every other row reads "plausible", including rows that cannot happen. "Plausible" means nobody checked.
- **It shows a key in a phase, never how the phase was reached** (14.2c), and never the monitor with an effect acting (6.1).

### 14.2b The walked scenarios and the case assertions

Two artifacts walk the case instead of reading it. They are not equal.

- **`<PREFIX>-scenarios.json`**, run by `engine/sim_runner.py`. Each scenario is a name, a list of steps and an `expect_phase`. A step is an action id or `{"wait": 120}`. The runner is a second implementation of the phase machine. It charges a fixed 8 seconds per action and waits in whole seconds, so it cannot express a gap shorter than that. A scenario asserts the final phase and nothing else. The runner can agree with itself and disagree with the engine.
- **`<PREFIX>-tests.js`**, run by `engine/engine-tests.js` against the built simulator. This folds a real log through the shipped engine. It is the authority. It can log fractional times, read the folded vitals with effects applied, read every nurse line, and fold in the default mode by passing a multiplier of 3.

Anything in 5.4, 9.5 and 9.7 that needs a test needs it in the second file.

### 14.2c The deterioration timeline

Required for any case using a time-guarded transition, and generated by the same tooling.

The per-key matrix cannot show these, because it enumerates what a key resolves to in a phase rather
than how the phase was reached, and the whole point of a time-guarded transition is that it is
reached by nobody doing anything. The timeline has three parts:

1. **Every time-guarded exit, by phase**: deadline, guard, destination, whether the destination is
   terminal, and the prompts that precede it with their own deadlines. Read each row asking two
   questions. Would this patient really deteriorate in that time if that treatment were withheld.
   And was the resident warned early enough to act on it.
2. **The do-nothing trajectory**: the phases and vitals a resident sees from arrival to the end if
   they perform no state-changing action at all, with the clock at each hop. This is the path an
   author is least likely to have imagined and the one a frozen learner will actually see. If the
   last row of it is a terminal phase, you have written a case that can kill the patient without the
   resident touching her, and that should be a decision you remember making.
3. **Every narration line**, collected together, to be read against the vitals of the phase each one
   introduces.

### 14.3 Author sign-off checklist

**Clinical content**
- [ ] Every abnormal finding, lab, and imaging result is clinically correct for this diagnosis
- [ ] Every abnormal value carries an abnormal flag, and no normal value carries one
- [ ] Reference intervals are right for the assays this case is modeling
- [ ] Every harmful action is genuinely harmful, and its halt reason is accurate
- [ ] Nothing tagged harmful should have been discouraged, and nothing discouraged should have been harmful
- [ ] No action tagged critical is actually optional; no action tagged neutral is actually critical
- [ ] Findings change appropriately after successful treatment
- [ ] Every debrief note teaches something correct, and every reference has been checked

**Catalog conformance**
- [ ] Every mapped binding row is clinically sound, with particular attention to assays, routes and composites
- [ ] Every harmful and discouraged action covers every catalog route to the same act, and a discouraged or rescuing stop action covers every sibling stop entry (3.4)
- [ ] Every case-only action is a decision in the SEED with a name and a date, has an `unmatched_placement`, and the SEED says what the button costs (7.1). Its spoken phrases have been tried in the built simulator
- [ ] No `short_label` names the diagnosis, the mechanism or the missing treatment, and every phase has one (5)
- [ ] Exam findings sit where the routing map puts them, and the general status line matches the patient
- [ ] Every diagnosis, correct and alternative, is a real catalog id

**Arrival handover**
- [ ] It names no diagnosis, in clinical or lay words
- [ ] It contains no past history, no medication, no allergy and no pertinent negative
- [ ] Any vital sign in it is what was measured on the way in, is written that way, and agrees with the first phase. It is no longer forbidden: since the monitor is dark until it is attached, the handover may be the only number the resident has, which is what a real handover is
- [ ] It is vague and incomplete in the way a real busy handover is, rather than a competent summary
- [ ] It is in the right voice for `mode`: a crew who saw the scene, or a triage nurse who saw the waiting room
- [ ] Read cold, it gives a resident somewhere to start and nowhere to finish

**Interview**
- [ ] Every topic in the 10.2 minimum list is authored, including the ones this case does not turn on
- [ ] The case has been played through the History tab alone, asking only what a resident would think to ask, to check that the case opens at all without the old background paragraph
- [ ] The patient never reveals the diagnosis or reports information they could not know
- [ ] Pertinent negatives are authored as denials, not left to the out-of-scope fallback
- [ ] Interview answers are correct at every alertness level, and every topic has a distressed-phase answer where the case needs one
- [ ] Paraphrase coverage is adequate on every topic whose answer changes management
- [ ] A held-out question file exists, was written before the bank was expanded, and its results are in the review packet with each management-changing miss named. If there is none, the packet says the interview is unmeasured (10.6)
- [ ] The generated out-of-scope bank has been read against the topic list and holds no question this patient can answer. Every topic special to the case is in `MAP` and has cover tags (10.6)
- [ ] Every topic marked `pertinent_negative` denies, in every phase (10.3)

**Time-guarded transitions**, where the case uses them
- [ ] Every deadline is a clinical claim you are willing to defend: this patient, without this treatment, deteriorates in about this long
- [ ] Every deterioration is preceded by a prompt naming the missing treatment, early enough to act on, and you have read the deterioration timeline to confirm it
- [ ] Every narration line is true of the vital signs shown immediately after it fires, on the monitor and not only against the phase's authored numbers. For each destination phase, every vital effect that can be acting there has been listed, and a narration that quotes a number has been tested with each one acting (9.5)
- [ ] In the default mode, with prompt deadlines times 3, the warning for each deterioration still fires before it. Where it does not, that is a recorded decision (9.7)
- [ ] In every phase with two or more timed rules, each pair has a line in the SEED saying which fires first and where the patient lands, and each line has a test with fractional times (5.4)
- [ ] The do-nothing trajectory is clinically right from end to end, not only at the first hop
- [ ] If the clock can end the case, you intended that, and the `timeout_reason` attributes it to the omission rather than to anything the resident did
- [ ] No prompt in a timed phase is stranded past the exit

**Timed mechanics**, where the case uses them
- [ ] For each one you have asked "what else has to know", and the answer picked the construct (6.4)
- [ ] Every expiring flag is read by something, and the thing that reads it is a transition rather than a tag
- [ ] A drug that both moves a number and changes the case holds its clock in ONE place, not in a duration and a flag both
- [ ] You have played the case doing nothing after the drug, and watched the consequence of it wearing off actually arrive
- [ ] Every duration is a clinical claim you will defend: this drug, this patient, acts about this long
- [ ] Where a drip and a bolus of the same drug both grant the flag, you intended the drip to stop it expiring

**Vital effects**, where the case uses them
- [ ] Every non-terminal phase's authored vitals are the **unsupported** baseline, so nothing is counted twice
- [ ] You have played the case with each effect-bearing action alone and read the number off the monitor, rather than trusting the arithmetic
- [ ] Every route to the same drug shares one key, and no two keys name the same act
- [ ] Every delta and duration is a teaching choice you are willing to have called a teaching choice in the review packet, and none of them is presented as a modeled quantity
- [ ] The treatments that move nothing move nothing on purpose, and the debrief says why
- [ ] The terminal phases read correctly, remembering that they ignore every effect
- [ ] No study report, exam finding or nurse alert quotes a vital sign that an effect with no end can move (6.1)
- [ ] No `while` guard switches an effect on in the phase that already carries the change (6.1)
- [ ] Every onset and duration window in the validator's note is the window you meant

**Structure and sequencing**
- [ ] Consultant advice never references a study that was not ordered, or one still pending. Every consultant line containing a number sits on a rule that tests `study S resulted`, the deteriorated-phase tiers included, and the number is true for every variant of that result (11.5)
- [ ] No consultant reply declines while the press still earns credit (11.5)
- [ ] A pending tier exists for every consultant whose advice depends on a study
- [ ] Prerequisites are clinically correct, and any catalog default that should be waived here has been
- [ ] Follow-ups are triggered by the right action, apply only where clinically indicated, and list every satisfier
- [ ] No follow-up that asks for something "again" or "after" relies on `satisfied_by` for an act the learner could have done before the trigger. `triggered_by` matches the actions that list it in `follow_ups_triggered` (8.2)
- [ ] A `flags_set_repeat` flag used as a restart or a repeat study has a scenario for each first dose and each early repeat, and its limits are in the SEED (6.5)
- [ ] Every deterioration branch has an exit that exists in the catalog

**Presentation**
- [ ] **No nurse prompt implies the patient is deteriorating**
- [ ] Every prompt and escalation is true in each phase its guard allows, claims no treatment and cites no study that its guard does not test, and has a deadline its guard can meet (9.5)
- [ ] Every `nurse_alert`, `narration_override`, narration, status line and consultant line on a covering action names the class and not one drug, and claims nothing the prerequisites do not guarantee (9.1)
- [ ] No result `comment` names the diagnosis, states the lesson, quotes another result or speaks to the reviewer, and no report carries a comment the learner needs (11.4)
- [ ] `[UNVERIFIED]` markers sit only in the fields the interface strips, every unchecked claim in those fields has one, and the provenance block lists each reference with how it was read (13, 17)
- [ ] Prompt deadlines reflect real relative urgency
- [ ] Wrong dispositions and diagnoses have explanations, not just verdicts
- [ ] The review matrix contains no clinically wrong resolution
- [ ] **The case has been played start to finish in the interface**, in the default mode, including at least one harmful halt and the deterioration branch

The last item is not ceremonial. Both the validator and the review matrix read the case file, so neither can see a study the interface never renders or a rescue action the resident cannot reach.

**Where the open questions go.** `cases/review/` holds a physician review question bank and the page reviewers answer it on. It covers AFRVR, CHFE, DIPH and MGCA and nothing later. A pack outside the bank keeps its open questions for the physician in its SEED and its review packet until the bank is extended to it.

---

## 15. Limitations authors must design around

- **Flags are permanent unless you author otherwise, and there are two ways to.** A single dose fixes something for the remainder of the case. A flag granted with `flags_set_timed` lapses (6.2). A flag granted with `flags_set_repeat` (6.5) arrives on the Nth administration of an act. That covers "it takes two doses", a restart read as a second start, and a second order of a study (v0.23). It covers nothing else: there is no titration, no third dose that differs from the second, no way for the condition language to read a count directly, and no way to know what happened between two administrations.
- **Permanent flags can shadow phase-correct content.** Put phase rules before flag rules in any list where both appear. See section 4.
- **Flags are binary.** Symptoms and findings switch rather than grade. Partial response cannot be represented.
- **The patient deteriorates only where the case authored it, and only in steps.** A time-guarded transition moves her from one authored plateau to the next; there is no gradient and no partial deterioration. In a case that authors none, ignoring every nurse prompt still produces the same patient as acting immediately, and most cases should stay that way.
- **Deterioration is all-or-nothing per rule.** A treatment given one second before the deadline has the same effect as one given at once, and how late you were does not affect how sick she becomes.
- **Order cannot be expressed in conditions.** Three things carry it instead. A prerequisite blocks an act until another is done (8.1). `also_satisfies` gives credit only in a named state (6.8). And a phase can stand for what has already happened, so the same drug leads to different places in different phases (DKA, v0.23). The third opens a race wherever two timed rules are pending (5.4).
- **Serial testing cannot be represented.** A repeat study in an unchanged state returns the same value. A result can be keyed on a related flag inside a phase (11.4), and a second order can grant a flag (6.5). Neither knows when the sample was sent.
- **"Again" and "after" are not in the language.** `satisfied_by` and `action A taken` mean ever in the run. 8.2 has the one pattern that expresses "after".
- **Prompts are multiplied by the difficulty mode and deteriorations are not.** The validator checks the authored deadlines only (9.7).
- **A vital effect moves the monitor and nothing else.** Every sentence in the case that quotes a number is written against the phase and can be made false by an effect (6.1).
- **One vitals block per terminal phase.** Every halt shows the same numbers whatever the mechanism.
- **Turnaround times are compressed** and do not reflect real clinical waits.
- **Vitals are static within a phase.** The monitor holds one authored set per phase and ramps to the next over five seconds. You author plateaus, not trajectories.
- **The interview matcher can only return what you authored.** No stage of it invents an answer. With the Patient tab gone, an unauthored topic is a dead end rather than an inconvenience. Error rates in section 10.6.
- **There is no background paragraph.** Two sentences of arrival handover is everything the resident is given. See section 3.2.

Each is a deliberate trade for version one. The rule structure migrates cleanly when continuous variables are added, because rule lists keep the same shape and only the predicate set becomes richer.

---

## 16. Authoring a new case, end to end

The sequence, with the reference section for each step and the artifact each produces.

### Step 1. Scaffold the pack.

```
python3 engine/new_case.py PE "Acute pulmonary embolism"
```

Writes `cases/PE/` with a skeleton case file, a seed template, an empty binding map, an empty scenario list and an empty test file. The seed template lists the 14 exam maneuvers and the routing map, so you have them in front of you while writing step 2.

The skeleton deliberately fails the validator. The error list is your to-do list.

**The scaffold is a JSON pack. Most packs are written as Python** (the five most recent, as of v0.23). In a Python pack the case lives in `case_1_shell.py` (metadata, patient, phases), `case_2_actions.py` (actions and follow-ups), `case_3_content.py` (exam, results, consultants), `case_4_interview.py` (topics, with the hand-written variants in `case_4_variants.py` in the three newest packs) and `case_5_handoff.py` (handoff, debrief, provenance). `build_case.py` assembles them and writes both `<PREFIX>-case.json` and `<PREFIX>-binding-map.json`. To start one, scaffold as above for the seed template, then copy `build_case.py` and the module layout from the newest pack that has them. **In a Python pack, edit the Python and never the JSON.** The next build overwrites the JSON.

Two things in the scaffold are older than this document. Its seed template says the handover carries no vitals, and 3.2 now allows one. Its skeleton asks for a catalog id in `metadata.final_diagnosis`, and 3.1 puts the scored id in the handoff block.

### Step 2. Write the seed (section 3). AUTHOR-ONLY.
About an hour for a case you know well. Nothing downstream can be right if this is wrong or thin.

**Before you write the action spine, open the catalog** and check that the actions your case turns on actually exist. This is the cheapest possible moment to discover that the rescue for your deterioration branch is not in the product.

**Record who decided what.** A case is reviewed only where its SEED names the decision, the person and the date. Give the SEED a first section for that, and put every later decision in it: a case-only button (7.1), a deterioration left unwarned in the default mode (9.7), a known gap from a race between timed rules (5.4). If a model drafted the AUTHOR-ONLY fields, section 17 lists what else the SEED carries.

**Write the arrival block and the two-sentence handover here, not later.** Section 3.2. The handover is the only thing the resident has before they start asking, so it is a clinical decision about how hard the case opens, and it is the one piece of prose in the seed where writing it well makes the case worse. Deciding it at the end, after you have the full history in front of you, reliably produces a handover that summarizes the case.

### Step 3. Bind to the catalog (section 7.2). AUTHOR-ONLY sign-off.
Produce a binding row per action. The AI proposes and you accept each `mapped` row. Any `unmatched` row is a decision: request a catalog entry, change the case, or keep a case-only action on the directing physician's recorded decision (7.2). In a Python pack the rows are written in `build_case.py`.

A new catalog entry is a change to `catalog/`, not to the pack: the entry in `build_catalog.py`, a default result if it is an investigation, voice phrases in `build_voice_aliases.py`, then all three catalog files regenerated and every pack rebound, rebuilt and retested. The repository README has the list.

Run the binding tool. It reports counts and flags anything blocking.

### Step 4. Route the exam findings (section 11.2). AI-DRAFTABLE, author reviews.
Take the findings from seed 3.6 and place each on one of the 14 maneuvers using the routing map. Write the general status line per phase.

### Step 5. Draft the case file. AI-DRAFTABLE against the seed.
Phases, transitions, tags, prerequisites, follow-ups, content keys, interview bank, prompts, handoff, debrief notes. Everything here is expansion of steps 1 to 3, and the AI must flag rather than invent anything the seed did not supply.

### Step 5a. Write the held-out questions, then expand the interview bank (section 10.6).
The order matters, and it is the order three packs got wrong.

1. Write `<PREFIX>-matcher-eval-questions.json` by hand, before anything is generated. Cover the topics that are special to the case, in shorthand as well as in lay sentences, and include at least thirty out-of-scope questions.
2. Fill `TOPIC_MAP` in the pack's `case_4_interview.py`, with every topic the shared library has a concept for. Add a concept to `catalog/interview_phrasings.py` for each topic that has none.
3. Read `catalog/interview_out_of_scope.py` from top to bottom against the pack's answers. Tag every question this patient can answer, and list the tags in the pack's `EXTRA_COVERED`.
4. Run `build_case.py`. It expands the bank, writes the tuning file, and prints what it added and dropped. Read the dropped list.
5. Read the generated out-of-scope bank (`interview.out_of_scope_bank` in the case file) against the topic list.

```
python3 cases/PE/build_case.py cases/PE
```

Run step 5a again whenever a topic is added, removed or renamed. Do not run the expansion on another pack on the way: it rewrites that pack's sources.

### Step 6. Structure the results (section 11.4). AI-DRAFTABLE, author signs the flags.
Convert every authored lab and imaging result into the payload shape, with reference intervals and abnormal flags. Where the catalog has a default for the same analyte, use its interval.

### Step 7. Validate (section 14.1).
Run the chain, in this order, for a pack `PE`:

```
python3 cases/PE/build_case.py cases/PE        # only if the pack has one
python3 engine/bind_catalog.py cases/PE
python3 engine/validate_case.py PE             # also writes the review matrix
python3 engine/build_simulator.py              # every case, into build/ and site/
node    engine/engine-tests.js build/simulator.html cases/PE/PE-tests.js PE
python3 engine/sim_runner.py PE
python3 engine/validator-tests.py cases/PE
python3 engine/deterioration_timeline.py PE
node    engine/matcher_eval.mjs --only PE      # add --semantic if huggingface.co is reachable
```

Run the validator until it is clean, or until every remaining error is a catalog change request you have raised rather than a defect in the case. One warning stays for good in every pack: the case actions with no catalog entry, which always include `handoff_submit`. Read the names in it each time. A clean validator is a structural claim. The list at the end of 14.1 is what it did not look at.

Expect the first run to find things. On the reference case it found a phantom action reference, a Fahrenheit value in a Celsius field, and 24 prerequisites written in the wrong polarity.

### Step 8. Simulate (system design 13.3).
Script a dozen end-to-end routes: the intended path, each harmful halt, each blocked prerequisite, the deterioration branch and its rescue, and any ordering you think a resident might produce. Reachability is a weak claim; a walked path is a strong one.

If the case uses time-guarded transitions, the scripts need waits, and four more routes: doing
nothing at all from arrival to the end, treating each deficit alone and letting the clock take the
other, a rescue inside the last window, and a rescue one action too late. Write the last two
together, because the difference between them is the lesson and it is easy to author a window nobody
can hit.

**Five more kinds of route, from the audit of v0.21 to v0.23a.** Write them as case assertions in `<PREFIX>-tests.js`, because the scenario runner cannot express them (14.2b).

- *Each narration with each effect acting.* For every timed transition whose narration quotes a number or a direction, fold a route on which each effect that can reach the destination is acting, and compare the line with the folded vitals (9.5).
- *The default mode.* Fold the do-nothing path, and each one-treatment-missing path, with a multiplier of 3. Assert that the warning for each deterioration is among the nurse's lines before the deterioration fires (9.7).
- *Each pair of pending timed rules.* One test per row of the 5.4 table, with fractional times on both sides of every boundary.
- *Every first dose.* Where a count or a phase stands for order (6.5), one route for each action a learner could reasonably give first, including the siblings and the discouraged route.
- *Every follow-up, both ways round.* The satisfying act before the trigger, and after it (8.2).

### Step 9. Read the review matrix in full (section 14.2). AUTHOR-ONLY.
This is where the clinically wrong resolutions are, and they raise no error. Pay closest attention to the deterioration branch and to any key where a flag rule and a phase rule appear in the same list.

Read three more things in the same sitting, because the matrix does not hold them (14.2a). The deterioration timeline, with each effect's delta added by hand to the destination rows it can reach. Every prompt and escalation, against each phase its guard allows. And every consultant line and result comment that contains a number or names a condition.

### Step 10. Play the case (section 14.3, final item). AUTHOR-ONLY.
Start to finish in the interface, in the default mode, including a harmful halt and the deterioration branch. Say each case-specific order into the microphone or its text box, in the words the nurse and the consultants use. This is the only step that can catch an interface defect, and it will also tell you whether the case is any good to sit through, which nothing else measures.

### Step 11. Sign off (section 14.3).
Every box. The checklist is the release gate.

Write the review packet before you ask for the signature. It lists the files to read, including the review matrix and the binding map. It gives the current counts of scenarios and engine checks, taken from the last run and not from memory. It has a table of every vital effect, each labeled a teaching choice. It gives the matcher results from the held-out file, or says the interview is unmeasured. And it says what was not run.

---

## 17. If the case was drafted before the seed

Section 2 assumes the author supplies ground truth and the AI expands it. A case produced the other way round, with a model generating the AUTHOR-ONLY fields, inverts the most important constraint in this document.

That is sometimes the practical starting point. Where it happens, the case file must carry a provenance block recording:

- that the AUTHOR-ONLY fields were AI-generated
- the list of fields awaiting primary sign-off
- reference verification status, per reference

**Per reference means a list, with how each one was read** (v0.21 to v0.23a audit). All three packs written in v0.21 to v0.23 carried one sentence for every source, and one of those sentences contradicted its own SEED. Write `provenance.reference_status` as a list with one entry per reference: the full citation, how it was read, and its status.

```json
"reference_status": [
  {"reference": "Umpierrez et al., Hyperglycaemic crises in adults with diabetes: a consensus report, 2024",
   "how_read": "A mirror of the journal PDF, through a summarizing tool, by a model, on 6 October 2026",
   "status": "Quotations not checked against the publisher's text. Not checked by a physician"}]
```

"How read" is one of: opened in full by a named person, opened by a model, read through a summarizing tool, or from memory. A source that could not be opened is listed too, with what was written from memory in its place. No tool reads this field. Its reader is the physician deciding what to check first.

**The list of fields awaiting sign-off is the section 2 table applied to this case.** Go down that table row by row. The packs written in v0.21 to v0.23 left out consultant advice, prompt and follow-up deadlines, coverage rows, the sizes of vital effects, `key_topics` and `key_exams`. Each is AUTHOR-ONLY or a clinical claim, and each needs a line.

**What the SEED of such a pack carries.** The headings TSS, TAKO and DKA use are the right ones: what a person decided, with the name and the date. The sources and how far each was read. The learning goals and where each is acted on. The phases. What an independent check changed. Known gaps. Open questions for the physician. Engine and catalog changes made for the case. That record does not replace sections 3.1 to 3.8. The physician signs a list of facts: every route to each harmful and discouraged act, the key findings with their numbers and intervals, the interview ground truth with the pertinent negatives named, and the disposition reasoning. Where that content was drafted in a `case_*.py` file, copy it into the SEED as a list and say that a model wrote it.

And the review burden changes shape. On a seeded case the physician checks that the AI expanded ground truth faithfully. Here they are authoring the ground truth in review, which is slower and needs a different frame of mind: read every number as a proposal, not as a transcription.

Such a case is not usable with learners until the section 14.3 checklist is complete, and the file should say so in a field the interface displays.
