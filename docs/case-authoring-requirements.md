# Case authoring requirements

How to build one case that the engine runs, that says nothing false, and that a physician can sign. `docs/case-design-guide.md` says what a case is for and what we refuse. Where the two disagree, the guide governs and this document is wrong. A case must still fit the engine, and the rules here are kept to what the engine, the truth or a signed decision needs.

**How to read it.** Part One is the core. Read it in full for every case, section 0 first and then section 13, which is the route and points back into the rest. Part Two is one section per optional mechanism. Read a Part Two section only when the case uses that mechanism, and section 14 to decide which it uses.

**Every rule carries one of three labels.**

- **Engine.** The code requires it. The validator reports it, the build refuses it, or the engine behaves this way whether or not you like it. Not negotiable.
- **Truth.** Without it the case says something false to the learner. Not negotiable either, and nothing checks most of these: the person building the case does.
- **Default.** What we usually do, and why. A case may depart from it when the medicine or the goals ask, with the reason written in the SEED beside the decision.

A statement with no label is a fact about how the engine works, for you to build on.

**The field reference.** `docs/generated/field-reference.md` lists every field a case may carry, who reads it and what the learner sees. This document does not repeat it. `python3 engine/lookup.py field <name>` finds one row.

---

# Part One. The core

## 0. How the case runs

Twelve facts govern everything below.

1. **The case moves through phases.** A phase is a clinically distinct patient state with fixed vital signs. Actions, and where the case says so the clock, move the patient between phases.
2. **A clock runs. It changes the patient only where the case authored it to.** Time decides when results arrive, when the nurse prompts, and the timing feedback in the debrief. A transition rule carrying `after_seconds` fires when that many seconds have passed and its guard still holds (section 15). Vitals never drift: a timed change moves the patient from one authored phase to the next, in a step. A case that authors no such rule has a patient who waits as long as the learner does.
3. **Flags are binary, and permanent unless the case says otherwise.** An action sets a flag. Nothing is partial. Two authored exceptions: a flag granted with a duration lapses (section 17), and a flag can be granted on the Nth administration (section 18).
4. **Reads never change state.** Exams and interview questions return content for the current state and alter nothing. Ordering a study changes state, even though it feels like a read. Transitions are checked only after a state-changing action, at a deadline, and when a flag lapses. A transition whose guard turns true on an exam, a question, an observational consult or a result arriving fires at the next of those three.
5. **Every readout is resolved, not stored.** Each thing the learner can see is a key owning an ordered list of guarded alternatives. First match wins. The last alternative is unconditional.
6. **Anything the case does not author returns the catalog default, which is normal.** This is the most dangerous property of the system (9.1).
7. **Results freeze at the state in which they were ordered.** A film ordered before intubation does not show a tube.
8. **The learner sees the whole catalog, not the case's actions.** Every drug, study and maneuver in the product is on the menu whether or not the case names it.
9. **Orders on the action tabs are picked, then submitted as a batch.** The batch is logged as separate entries at one instant, in the order picked, and the fold applies them one at a time. A line picked after the drug that needs it does not help that drug. A harmful action halts the run and discards the rest of the batch. Exams, interview questions and consults fire at once. Tests that log several actions at one instant get the same ordering.
10. **The case ends** when the learner confirms a handoff, when a harmful action halts it, when a transition reaches a terminal phase the case authored, or when the learner ends it early. One authored exception: a disposition the case intercepts does not end the run (section 20).
11. **The learner is given almost nothing at the start.** A splash naming the room, the chief complaint in the patient's words and the arrival vitals as figures someone measured before they walked in. Then age, sex and weight, and a short arrival handover at the top of the History tab. There is no background paragraph. Everything else is reachable only by asking.
12. **The monitor is dark until the learner attaches it**, and vitals ramp to a new phase's numbers over five seconds. Both are display. A result ordered during the ramp still freezes at the phase's authored numbers.

Two ids are fixed. `case_complete` is the only phase that completes the run. `halted` is where a harmful action sends the patient, and it exists only in a case that has a harmful tag (section 21). The first phase in the list is the start phase.

---

## 1. Who decides what, and how that is recorded

A case is built by a model from a prompt, and the prompt may be thin. The builder's job is to work out what a competent emergency doctor must do for the condition, from several sources (guide, "Learning goals come first"), to build the case so the learner has to act on it, and to record who decided every clinical fact. A physician validates the case before any learner sees it. Nothing here is reviewed until a SEED names the decision, the person and the date.

**Truth. Every clinical fact a model wrote is unverified until a physician signs it, and the case says so.** A symptom, a finding, a value, a reference interval, a consultant's advice, a prerequisite, a deadline, an abnormal flag, a binding row that maps one catalog entry to another, a size for a vital effect. A model may draft all of them. What it may not do is present one as checked. Three places carry that:

- **`provenance`** on the case, six keys: `status`, `author`, `warning`, `author_only_fields_pending_signoff`, `reference_status`, `catalog_change_requests`. The interface reads one of them. **Engine.** While `provenance.warning` is a non-empty string the welcome card marks the case an unsigned draft. Keep it until a physician signs. Everything in the case file ships inside the built page, including every note and rationale, so write them as if a learner could read them.
- **`reference_status`** is a list with one entry per reference: the full citation, how it was read, and its status. "How read" is one of: opened in full by a named person, opened by a model, read through a summarizing tool, or from memory. A source that could not be opened is listed too, with what was written from memory in its place.
- **The SEED's section 0, "What a person decided"**: the person and the date, then a two-column table of decisions. Below it, "Everything else is model output." Every later decision gets a row. Repeat each decision where it is used in the source, as a comment or `author_note` naming the person and the date, so a reviewer meets the signature at the rule and not only in the index.

**Truth. Mark every unchecked claim that can carry a marker** (10.3 says where a marker may go). A note that cites a source the builder did not open ends "[UNVERIFIED: how it was read]".

**Default. The physician's sign-off covers these in every case:** the diagnosis, the phases and what each one claims about cause, every tag, every halt reason, the vitals of every phase, every abnormal finding and value with its flag and interval, consultant advice, the interview facts and the pertinent negatives, prerequisites and follow-ups, which actions are time-sensitive and how urgent, the disposition, every `mapped` binding row, the size of every vital effect, every deadline, `key_topics` and `key_exams`. `provenance.author_only_fields_pending_signoff` lists which of these are still open for this case.

**Default. A model may add a denial for a topic the prompt did not mention.** It marks the topic `pertinent_negative` only if the answer denies in every phase (8.3), lists the topic in the SEED as model-added, and the sign-off covers the list. A model may not add a positive finding the prompt did not supply without listing it the same way.

**Default. A builder working alone does not edit `catalog/` for a case.** Bind what exists, write the request in `provenance.catalog_change_requests`, and say in the SEED what the case does without the entry. A builder who does add the entry marks it model-proposed in the catalog generator and runs the README chain for every pack. A missing entry never becomes an invented action (6.1).

**Default. A finished case written for another platform is not a seed.** List every place the source disagrees with itself, and for each say whether the author or the builder resolved it.

---

## 2. The seed

The SEED is `cases/<PREFIX>/<PREFIX>-SEED.md`. It is the record a physician signs and the first thing the next builder reads. Copy its headings from the reference pack (section 13). Its sections, in order:

### 2.0 How this case differs from the library

**Default.** Before anything else, read `docs/generated/case-index.md` and say how this case differs on the guide's six dimensions: tempo, what is uncertain, the kind of right answer, where the danger hides, the patient and the room, how it feels. A case that matches an existing one on most of them needs a reason to exist. The same six go into `metadata.library`, which is what the index prints.

### 2.1 Learning goals

**Default.** List the core competencies of managing the condition in the emergency department, each with its source: guidelines and consensus statements, EM training standards, published simulation cases on the condition, EM education sites, the directing physician. A goal with no source is an opinion, and the SEED says so. From that list keep three to six goals that pass the guide's five tests: core, useful beyond this patient, something a learner can do, hard for a real reason, few. For each goal, write where in the case the learner has to act on it and what the patient shows. A goal acted on only in the debrief is not taught yet.

**Default.** Name the idea that travels: the one thing the learner will use on a different patient next month, and which goal carries it. It is printed from `debrief_configuration.cross_cutting_teaching_points` (10.3).

### 2.2 Identity and the public fields

- `metadata.working_title` and `metadata.final_diagnosis` (prose, for the reviewer).
- `metadata.case_number`, a whole number shown as "Case N" on the list, the splash and the learner's history. Take one more than the highest in the case index. Never change or reuse one. **Engine.** The build stops on a duplicate.
- `metadata.complaint`, three or four words in clinical register, which the welcome list prints. Optional. A case without one falls back to its title, which is usually too long for a list.
- `metadata.category`, the body system or problem class, which groups the welcome list. Optional. A case without one is grouped under "Cases".
- `metadata.target_level`, a list from `medical_student`, `intern`, `junior_resident`, `senior_resident`, lowest first. **Default.** Those four words. The welcome list prints whatever is there, and three or more read as a range.
- `metadata.estimated_runtime_seconds`, `metadata.library` (2.0), `metadata.chief_complaint_patient_voice`.
- The scored diagnosis lives in `handoff.correct_diagnosis.catalog_id` (10.1), as a diagnosis catalog id. **Engine.** An id that does not resolve means the handoff cannot be scored. The validator reports it.

**Truth. These are public.** The title, complaint, category, chief complaint, care setting label, target level, runtime, the patient's age and sex, and the pack prefix are shown to anyone who opens the site, before sign-in. None of them may name the diagnosis, and the prefix is shown with them. A prefix that abbreviates the diagnosis gives it away.

### 2.3 Patient, setting and arrival

Age, sex (`male` or `female`, which shared strings read for pronouns), weight, and the background in facts (2.8). The care setting, if it is not a quaternary center with everything on site: **Default**, because the right disposition depends on it. Adults only for now: the arrival card colors vitals by adult resting ranges.

**Engine.** `metadata.arrival.mode` is `ems` or `triage`. A walk-in, a police arrival or a transfer is `triage` unless a crew hands over to you directly. `metadata.arrival.location` is `resuscitation_bay`, `trauma_bay` or `patient_room`. The splash renders the room from it. `metadata.arrival.line` is an internal description, read only as a fallback: for the handover when `patient.arrival_handover` is missing, and for the room when `location` is missing. Never leave it as the only one.

**The handover**, `patient.arrival_handover`, is what the learner reads at the top of the History tab. It is the one piece of prose in the seed where writing it well makes the case worse, so decide it here and not after the whole history is in front of you.

- **Truth. It names no diagnosis and no word that names one.** Not "CHF exacerbation", not "fluid overloaded", not "septic". A crew may say those things. A case that says them has ended the case.
- **Truth. It is never wrong on purpose.** Vague and incomplete, as a busy handover is. A fact it states is true.
- **Truth. A vital sign in it is what was measured on the way in**, written as a past measurement, and agrees with the first phase. The validator warns when a quoted saturation disagrees.
- **Default. It carries** age and sex, the presenting problem in the speaker's register, a rough duration or tempo, and one concrete circumstance that explains why they came in today. Spoken numbers are spelled out.
- **Default. It leaves out** the past history, the medication list, allergies, pertinent negatives, the precipitant (which is usually the lesson), and treatment already given. Each of those is an interview topic. A case may put one in where a real crew would say it, and says why in the SEED: a crew that knows the patient is on warfarin would say so.
- **Default. Two sentences.** The validator warns above two and above about 45 words.
- **Default. The voice follows `mode`**: a crew who saw the scene and the family, or a triage nurse who has the patient's own account and a look at them in the waiting room. Neither has a chart.

| mode | example |
|---|---|
| `ems` | "Sixty-five year old man, breathing trouble that's been getting worse over the last few days. Family called us this morning when he couldn't manage the stairs." |
| `triage` | "Fifty-eight year old woman walked up to the desk saying her chest has felt tight since last night. She looked pale enough that I brought her straight through." |

Read cold, the handover gives the learner somewhere to start and nowhere to finish.

### 2.4 The stories, and the states

**Default. Tell the true stories first.** Before any structure, write what happens to this patient when treated well, when treated in each plausible wrong way, and when left alone, as a clinician would tell them at the bedside. Each story becomes a scenario in section 13, and the left-alone story is what the deterioration timeline is checked against.

**Default. Find the states in the stories.** A state is a moment that changes what a good doctor would do. For each phase, write its "what now?" in one line, and it must differ from the phase before. A phase whose answer is the same as the last one is cut. Use as few phases as the truth allows and as many as it needs. Most cases run around four to ten. A case with more says why in `phase_notes.count_justification`, because the review matrix grows with every phase. No phase is added because cases usually have one.

**Default. For each phase, decide what happens if the learner does nothing.** How long can this patient sit in this state without the treatment that is missing, and what does she look like afterwards. "Indefinitely, for a fifteen-minute case" is an answer, and most phases give it. A number is the seed of a timed transition, section 15, and the clock is one more tool the case may pull in to force action where that helps the case. Decide it here. A deterioration bolted on at the end fires in the part nobody played.

**Default. Decide, per wrong action, whether the patient can be got back.** A mistake the learner can recover from is a phase they can get out of. A halt is for an act with no way back in the medicine (section 21), used sparingly, so the learner is not discouraged.

### 2.5 The action spine

- **Critical actions**: what must happen for the patient to do well, in which phase each becomes critical, and which are time-sensitive.
- **Harmful actions**: what would injure or kill this patient, with a one-line reason each.
- **Discouraged actions**: wrong here but not lethal.
- **Recommended actions**: good practice, not case-determining.
- **Traps**: plausible actions that are wrong here, and why. Tag the traps the goals need, and no more: an untagged action is neutral and silent, and a tagged one costs the learner attention, so each one serves a goal.

**Truth. For each harmful and discouraged action, name every route to it.** If a fluid bolus is harmful, say so for saline and for Ringer's and for each volume. The catalog lists as separate entries what a clinician thinks of as one act, and an unbound sibling is an escape from the lesson. A stop action has siblings too: if stopping one infusion is discouraged or is the rescue, bind every stop entry for the class.

**Default. Where the catalog declares an equivalence group, use it.** `also_covers_group` on the binding row applies the case action's tag, halt reason, note, flags, effects and nurse lines to every member, so coverage cannot drift as the catalog grows. `also_covers` lists entries one by one where no group exists. **Truth.** Shared fields are written to be true of every member: "the vasopressor", not "norepinephrine". A covered study returns the covering action's authored result.

Open the action index (`docs/generated/action-index.md`) before writing the spine and check that the actions the case turns on exist. This is the cheapest moment to find that the rescue is not in the product.

**Default. Where good doctors disagree, name both and say which mechanism makes the case accept both.** `also_covers_group` and `expectation_label` for one act with many agents. `also_satisfies` with a null condition for one act that credits another (section 19). `acceptable_with_qualification` for a diagnosis (10.2).

### 2.6 Sequencing

Any action that must not be performed before something else (a prerequisite). Any action that creates an obligation afterwards (a follow-up), and whether it applies here. Any catalog prerequisite to waive in this case, and why. Section 22.

### 2.7 Key findings

The abnormal exam findings, abnormal labs and abnormal imaging that define the case, and how each changes after successful treatment. **Truth.** For each abnormal value: the number, the units, the reference interval you are working to, and that it is abnormal. Say also which findings do not change in the case's minutes: a chest film and an ECG lag clinical improvement by hours, and a film that clears on the phase change teaches something false.

### 2.8 Interview ground truth

The history as a list of facts, with the pertinent negatives named (section 8).

### 2.9 Disposition and diagnosis

The correct level of care and the correct diagnosis, with the plausible wrong answers for each and why each is wrong. Diagnoses are catalog ids (10.1). The handover is scored on one or two major diagnoses and nothing minor (10.2).

### 2.10 Known gaps and open questions

Each limit the case accepts (a race between timed rules, a delay that does not survive a phase change) is a known gap in the SEED, pinned by a scenario whose name starts "Known gap:". Each question the documents did not answer is an open question, with what the builder did meanwhile. Open questions for the physician live here and in the review packet until they are answered.

---

## 3. The condition language

One language everywhere a condition appears: content rules, tags, prerequisites, follow-up applicability, prompt guards, vital effect guards, transitions. Five predicates, combined with AND, OR, NOT and one level of parentheses.

| Predicate | Meaning |
|---|---|
| `phase is X` | The case is in phase X |
| `flag F set` | A completed action set flag F |
| `study S ordered` | S has been ordered. The result may be pending |
| `study S resulted` | S has been ordered and the result has arrived |
| `action A taken` | A was performed, or a sibling A covers was, or another action credited A through `also_satisfies` |

**Engine.** No arithmetic, no comparisons, no nesting beyond one level, and no time: `after_seconds` lives beside a transition rule and never inside a condition, and it is ignored on a content rule, a tag, a prerequisite or a follow-up. Write the trailing keyword: `flag F set`, not `flag F`. The validator refuses a condition that does not parse in every field it reads, and the engine suite checks the rest (interview `facts` and `volunteer` rules).

**Engine. AND binds tighter than OR.** `A OR B OR C AND NOT D` is `A OR B OR (C AND NOT D)`. Wherever a multi-term OR is combined with AND, put the OR in parentheses. No tool reports the unparenthesized form.

**Truth. `resulted` for any content that references the finding. `ordered` for content acknowledging that something is on its way.** Studies take time: laboratory studies, plain films and the twelve-lead 5 seconds, CT and MRI 10, bedside 0.

**Default. `flag` for state-changing actions, `action taken` for observational ones.** Every state-changing action sets a flag, so the two are equivalent there. `action A taken` means the act is accounted for, not that this button was pressed.

**Truth. Phase rules before flag rules.** Flags are permanent, so a flag set early is still set late. A key that tests `flag on_niv set` above `phase is post_intubation_hypotension` returns the improved value to a patient who has since collapsed. This is the commonest way a rule list is right for the situations the builder thought of and wrong for one they did not.

---

## 4. Phases and transitions

Each phase carries `id`, `label`, `short_label`, a one-line clinical description, `vitals` (heart rate, systolic and diastolic pressure, respiratory rate, oxygen saturation, temperature), `appearance` (section 5), an ordered list of `transitions`, and `terminal`. **Engine.** The vitals, the appearance values and, for a non-terminal phase, at least one transition are required. Every phase must be reachable, counting phases reachable only by the clock.

**Engine.** Transitions are an ordered list of `{when, to}`. First match wins. They are checked after every state-changing action, at a deadline, and when a flag lapses (fact 4). One step per check: a learner who has already satisfied the next phase's exit advances to it on the next check, not at once. Two entries logged at one instant (a batch) can enter and leave a phase in one step, and that phase issues no prompts. A transition with no `after_seconds` may lead to a terminal phase the case authors, which is how a case ends on an action without the shared `halted` phase (section 21).

**Engine. Every non-terminal phase carries a transition into `case_complete`**, `{"when": "action handoff_submit taken", "to": "case_complete"}`. The engine marks a run complete only by entering `case_complete`, so a phase without the rule leaves a confirmed handoff recorded as no handoff. The validator reports a phase without one. **Default.** Put it first in the list, so a handoff wins over anything else there.

**Engine. A `narration` on a transition with no `after_seconds` is never spoken.** An instant transition says nothing. If the learner must hear something at that moment, put a `nurse_alert` on the action that causes it (7.1). The validator warns on a narration that nothing speaks.

**Truth. Every link is a claim about cause.** Moving from one phase to another says "this is what that does to this patient", and a clinician should agree with every link. A transition that exists to make the case work and not because it is true is removed. **Default.** Write the cause in `author_rationale` on every transition, timed or not. The field is required on a timed rule and is a reviewer note on the rest.

**Engine. Every deterioration branch needs an exit.** The validator requires a transition out of every non-terminal destination. **Truth.** If entering a phase takes an action, leaving it takes an action too, and that action must exist in the catalog or be a case-only action the learner can reach. Stopping an infusion is its own catalog action, not a toggle, so the rescue is gated on the flag the stop action sets.

**Truth. `short_label` names no diagnosis, mechanism, missing treatment or verdict.** The monitor prints it beside the clock from the first second. Write what a bystander could say: "on arrival", "pressure low", "after potassium". Not "septic shock", not "needs a pressor", not the drug that is running where a sibling could be running instead, and not an answer the learner is meant to reach by ordering something. **Default.** Author one on every phase, terminals included. A phase without one prints its `label`. Every pack names the first phase `presentation`, short label "on arrival".

**Default. Numbers that differ frankly.** Vitals ramp over five seconds at a boundary, so two phases a few points apart read as drift and not as an event. A phase change the learner must notice needs numbers they can see.

**Engine. Prompt deadlines are measured from phase entry.** When a phase changes, the previous phase's outstanding prompts are canceled and new deadlines start (7.2).

---

## 5. Vitals, the monitor, the sound and the figure

Builders supply numbers. The sounds and the face are computed from them, and posture is fixed.

### 5.1 Vitals and appearance

**Engine.** Per phase: the six vitals, and in `appearance` a distress level (0 to 3), an alertness level (0 alert, 1 drowsy, 2 obtunded, 3 unresponsive), pupil size (`small`, `normal`, `large`) and pupil reactivity (`reactive`, `sluggish`, `fixed`). The validator refuses values outside physiological ranges. The monitor prints a number in bold only when it is outside the adult normal range in `VITAL_NORMAL` (ui.js), so a phase value just inside a range reads as normal. Saturation drives the pitch of the heartbeat and heart rate its tempo. The respiratory rate moves the figure's chest, and the distress and alertness levels draw its face. Nothing draws skin color or perfusion. A feature outside this set is a request to extend the renderer, not something to describe in prose.

**Truth. The number is heard as well as read.** A saturation chosen loosely because it was about right is heard.

**Truth. A phase's authored vitals are what the patient shows with nothing running.** Where the case uses vital effects (section 16) the number on the monitor is the phase's number plus every effect acting, so a phase that already carries a treatment's gain counts it twice.

### 5.2 Rhythm and the trace

A phase may carry `rhythm`, `regular` (the default) or `irregularly_irregular`. **Engine.** No third value. A regularly irregular beat is a request to extend the audio module. The mean rate is preserved, so author the true average and do not compensate for the irregularity.

**Truth.** Author the rhythm wherever it is part of the finding, and state it in words in the phase's ECG report and in `exam_card`, so a learner with the sound off can find it. **Truth.** No case is described as modeling a rhythm. The intervals are authored parameters with a provenance note in `SHARED.audio.rhythm`.

A phase may carry an `ecg` block: `pattern` (`organised`, `ventricular_fibrillation`, `asystole`), `p_waves`, `pr_ms`, `qrs_ms`, `qtc_ms`, `st_mv`, `t_mv`, `verify`. The monitor draws one lead, live, from it. **Engine.** Unknown fields and patterns are errors. A unit slip (`0.12` for 120 ms) fails. A wide QRS without a `verify` note warns.

- **Truth.** Author the block from the phase's own ECG report, with the same numbers. The report and the trace are two statements of one tracing, and nothing compares a picture to a sentence.
- **Truth.** The rate cell follows `vitals.heart_rate`, not the pattern, and the beat is silent under `ventricular_fibrillation` and `asystole`. Under `asystole` author a rate of 0. Under `ventricular_fibrillation` author the rate you want the cell to show and say in `verify` that it is the counted fibrillatory rate.
- **Truth.** The monitor is not a twelve-lead and draws no ectopy, artifact, fibrillatory waves or second lead. Where the report mentions one, say in `verify` that the trace does not show it. `ecg_when`, a list of `{when, ecg}`, changes the trace within a phase: the first that holds overrides those fields. Keep the twelve-lead in step.
- **Truth.** No case is described as modeling an ECG. The shapes are stylizations with a provenance note in `SHARED.monitor.ecg`.
- **Default.** Write a block where the tracing is part of the finding, and for every terminal phase a transition can enter, since the learner spends the last five seconds of such a run looking at the monitor. The `halted` phase is never shown: a harmful action ends the run at once. Author a terminal phase's respiratory rate to match its text: 0 for no effort, a low number for agonal breathing. The shoulders move at whatever you write.

A phase with no block draws a narrow complex with P waves at the authored rate, without P waves under an irregularly irregular rhythm.

### 5.3 The figure in the room

A drawn patient sits between the panels, sitting up on a stretcher in every case. **Truth.** Avoid status lines and findings that put the patient supine or on her side. Nothing is authored for posture.

`patient.avatar` is the fixed appearance. **Default.** Leave it out. The standard man or woman is drawn by `patient.sex`, aged by `patient.age` (young under 40, middle to 59, older from 60). The one key worth authoring is `build`: `thin`, `average` or `obese`, only where the seed says so.

`content_keys.patient_visual` says what is visible now. It is a guarded rule list, first match wins, and the value is the whole visible state: `eyes` (`open`, `closed`), `seizure`, `work_of_breathing` (`normal`, `increased`, `severe`), `expression`, and `addons` from a fixed list (`gaze_left`, `gaze_right`, `nystagmus`, `nasal_cannula`, `nonrebreather`, `bipap_mask`, `intubated`, `bag_valve_mask`, `defib_pads`, `central_line`, `jaundice`, `sweating`, `agitation`, `hospital_bed`, `hospital_bed_flat`). Beside `rules` the block may carry `also`, a list of `{when, addons}` that is additive rather than first-match, for things independent of the main state such as pads or a central line. `also` is not in the review matrix.

- **Engine.** Closed keys and values. No respiratory rate or distress level here: the shoulders move at the monitor's rate and the resting face comes from the phase's distress level. The alertness level is drawn too, so `eyes` is only needed to override it (closed for a sedated patient whose phase is below level 2, or a seizure, which draws open eyes at any level).
- **Engine.** The airway device follows the last airway button pressed, not the rules. Author the arrival device in `rules`. After any airway button the figure shows the last one pressed, a tube wins over all, and nothing takes a device off. Do not author flag rules for devices the learner applies.
- **Truth.** Keep the block consistent with the general status line and the appearance values. It is clinical content, in the matrix and the sign-off like every other key. Carry a `verify` note naming the drawn choices a reviewer should check.
- **Default.** Prefer flags to phases for anything an action puts on or takes off the patient.

`content_keys.pupils` is optional. A case that authors it gets a magnified view of the eyes when the learner hovers over the figure's face, with a penlight that makes the pupils respond. It is a guarded rule list, first match wins, with `iris` (a hex colour) beside `rules`. The value is `state` (`normal`, `pinpoint`, `dilated`, `dilated_fixed`, `blown`), an optional `size_mm` and `reaction` (`brisk`, `sluggish`, `none`) overriding the state's, and for `blown` the `side` (the patient's `left` or `right`). For `blown`, `size_mm` and `reaction` describe the unaffected eye, and the affected eye is drawn at 8 mm (or `size_mm` if larger) with no reaction unless `affected_mm` and `affected_reaction` say otherwise, for a pupil not yet at its largest or partly back after treatment. Light in either eye reaches both, so every pupil that can respond does.

- **Truth.** Keep it consistent with the HEENT exam text, phase by phase. End with an unconditional rule.

### 5.4 The monitor is dark until it is attached

Every cell reads a dash and there is no heartbeat until the learner takes the action carrying the catalog's `reveals_vitals` capability, `attach_monitor`. No case changes this. The splash shows the first phase's vitals as a handover artifact, so a handover that quotes a saturation quotes that one.

- **Truth.** An arrival prompt never assumes the learner can see a number they have not obtained. "His sat has dropped" implies a screen that may be dark. The nurse volunteering a number is fine.
- **Truth.** A prompt quotes no vital sign at all. Its text is one string for every phase the action is critical in, and any effect acting makes the number wrong.
- **Default.** Tag `attach_monitor` and give it a note. The debrief's recommended lists leave out a line and a monitor on purpose (they still count in the score), so tag it `critical` if you want it named (10.4).

---

## 6. Actions, binding and tags

### 6.1 Actions come from the catalog

The catalog defines every drug, maneuver, study, consultant and procedure, with names, tab, turnaround, narration template, default prerequisites, default flags and default results. It holds no case-specific judgment. A case references entries and supplies what is case-specific: the tag, flags, prerequisites and waivers, follow-ups, prompt, nurse lines, halt reason, debrief note, and the optional mechanisms of Part Two. `docs/generated/field-reference.md` has the full list with who reads each. **Engine.** Search and the tab filters read "drip" and "infusion" as one word (28 October 2026), so a case display name needs only one of them to be found by either.

**Engine. Fields the engine reads have exact names.** On an action, a phase or a topic, a field not in the reference is a reviewer note and changes nothing, including a misspelt one, so copy names from the reference. Inside `ecg`, `patient_visual` and `patient.avatar` an unknown key is a validator error. The validator does not check every spelling elsewhere.

**Engine. `flags_set` is merged with the catalog entry's `flags_set_default`.** Do not restate those. `python3 engine/lookup.py flags` lists them. **Default.** Set a flag only where a condition reads it. A flag nothing reads is a note.

**Engine. A consult is state-changing unless the case sets `state_changing: false`.** Its flags are granted and transitions are checked on every press. Set `false` on a consult that must not move the case. `true` is the default and changes nothing. Exams never change state. Labs, imaging and ECG always do.

**Default. A missing action is a catalog change request.** Record it in `provenance.catalog_change_requests`, bind what exists, and see section 1 for who adds the entry.

**A case-only action** is one the catalog does not have. **Engine.** Its binding row has `catalog_id: null`, an `unmatched_placement` naming the `tab` (and a `group`, which defaults to "Not in the catalog"), and an `unmatched_narration`. A row with no placement is not built: no button, no validator error, a build note listing the action as unreachable, and the engine suite fails the pack on that note. The id's prefix decides its kind: `consult_` returns consultant content, `exam_` is an exam, `labs_`, `echo_`, `cxr`, `ct_` and `pocus` are investigations, anything else is an order with no result. **Default.** A case-only button is a decision in the SEED, and the SEED says what it costs: a button unique to one case tells the learner it matters, and it is not in the voice table.

**Engine. Every pack authors `handoff_submit`** as a neutral case action, `display_name` "Submit handoff", `state_changing: true`, `flags_set: ["handoff_submitted"]`, bound with `catalog_id: null` and `unmatched_placement` `{"tab": "handoff", "group": "Not in the catalog"}`. Without it the engine drops the handoff entry and the run never completes. The reference pack and the scaffold both carry it.

**A history question can be a tagged case action.** Bind `interview_topic_<topic>` with `catalog_id: null` and a placement on the `history` tab, which draws no button. Asking the topic, or having it volunteered, satisfies it. It never changes state, and it prompts like any critical action, so **Truth.** guard its prompt off the phases where the patient cannot answer. For several questions that count only together, use `asked_all` (section 19).

**`voice_phrases`**: spoken phrases for one action in one case. **Engine.** A list of non-empty strings with a letter or digit each, normalized the way speech is, indexed ahead of the global table, on an action that sits on a tab the microphone reads (not `handoff` and not `history`), not borrowed by a covered sibling. The same phrase on two actions warns. **Engine.** The engine suite pins a list of global phrases with the case bound (`engine/engine-tests.js`, "voice"). A case phrase that captures one of them fails the suite for that pack. Run the suite after adding phrases and treat a failure there as the suite being right. Test each phrase in the built simulator.

**Engine. The catalog's narration templates drop `{dose}`**, since doses are not implemented, and a `display_name` is lowered word by word in narration. Write it as a button label and let the engine case it.

### 6.2 Binding to the catalog

**Engine.** Every case action has a row in `<PREFIX>-binding-map.json`. `engine/bind_catalog.py` derives `exact` (the case id is the catalog id), `mapped` (the row names a different catalog id) or `unmatched` (`catalog_id` null). A missing row is an error. An unmatched row warns for as long as it is unmatched, and is an error when its note starts with `BLOCKING`. A catalog entry bound by two case actions warns: the second is unreachable, so merge them into one action and put both teaching points in its note.

**Truth. Every `mapped` row is a clinical claim that two entries are interchangeable here**, and it needs the physician's signature. Look for assay mismatches (a numeric high-sensitivity troponin I does not transfer to a qualitative troponin T entry), route and formulation splits, and composite actions (a combined lung and cardiac ultrasound may be two entries, so bind to both or cover one with the other).

**Default. Use exact ids in a Python pack.** The scenario runner reads catalog defaults by the case id, so a `mapped` row has no catalog prerequisites there. A `COVERAGE` entry for an action id that no longer exists is dropped without a message, so check the row count the binder prints against the number of actions.

### 6.3 Clinical tags

**Engine. A tag is an ordered rule list, first match wins, unconditional default last**, with values from `critical`, `recommended`, `discouraged`, `harmful`, `neutral`. The validator refuses any other value and any single-value tag.

| Value | Meaning |
|---|---|
| `critical` | The patient does badly without it. Omission costs |
| `recommended` | Good practice, not case-determining. One point on offer. **Default.** A consult is recommended only where the call changes care in the department (owner, 28 October 2026) |
| `discouraged` | Wrong here but not lethal. One point lost, explained in the debrief |
| `harmful` | Halts the case. Needs a halt reason and a `halted` phase (section 21) |
| `neutral` | No effect |

**Truth. Reserve `harmful` for what the evidence supports as lethal.** A halt is the strongest claim the system makes. If the evidence is observational and confounded, `discouraged` with a good note is the honest tag.

**Truth. Check the fallthrough in every phase.** A nitrate tagged harmful only in the hypotensive phase falls through to recommended in the vasopressor-dependent phase that follows. The review matrix shows it. Read it.

**Default.** Tag the traps the goals need. Tag `recommended` what you would want said in the debrief, because forty recommended tags dilute the critical ones in the score (10.4).

**Engine. One act, any route** (owner, 29 October 2026). `catalog/expectation-credit.json` lets one device or test meet its alternatives' expectations: a mask the cannula, two IVs the IO, either gas or hCG the other. In a case, `also_satisfies` credits an adequate alternative. A recommended expectation counts only after 30 seconds in its phase. **Truth.** An alternative, second agent or symptomatic drug is `neutral` unless leaving it out is a mistake. A note agrees with its tag. Text reached by several routes is true on each.

**Engine. Intubation care is never graded** (owner, 23 October 2026). The RSI drugs and the care before and after the tube, listed in `catalog/ungraded-intubation-care.json`, are `neutral` everywhere and never in the debrief's critical actions, Critical Errors or traps. The decision to intubate is not on the list. A case-only action that is intubation care carries `"ungraded": true`. Its flags, effects, prerequisites, phase changes and note still apply. The validator refuses a non-neutral tag or a trap on one, and a hidden target credited only by intubation care that is not marked ungraded.

**Engine.** An action whose tag can resolve to `harmful` needs a `halt_reason`: one sentence saying what was done and the physiological consequence. Every tagged action needs a `debrief_note` (10.3). The validator warns on a missing note.

---

## 7. The nurse

The nurse narrates actions, announces results, speaks the prerequisite failure messages, and prompts. Only the lines and the prompts are authored.

### 7.1 Narration, overrides and alerts

The catalog template narrates each order ("Giving {name}."). Exams and interview questions are not narrated. Two case fields change it:

| Field | What it does |
|---|---|
| `narration_override` | Replaces the catalog line. **Default.** Only where the standard line would be wrong or confusing |
| `nurse_alert` | A second line, said straight after the catalog's own, colored and filed in the running chart, said again on a repeat dose, never a prompt and never counted against the cap. A string, or a rule list (`[{"when": <condition>, "value": "..."}, {"when": null, "value": "..."}]`) resolved against the state at the moment of the order, so a repeat of the same drug in a later phase can carry a different line. DKA's potassium says "it takes a while to run in" on arrival and "twenty to thirty in each liter" once the level is 3.5 or more |

**Default.** Reach for `nurse_alert` where the learner will need the words again after they have scrolled away: a drug that takes time, a repeat that is expected, a consequence that is coming.

Both fields are borrowed by every covered sibling, and both are one string said in every phase. **Truth**, three checks on each: name the class and not one drug wherever a sibling can be the thing that is running ("the vasopressor"), and search the case for every covering action's display name and read each hit as if a sibling had been ordered. Say nothing the action's prerequisites do not guarantee. Be true in every phase.

### 7.2 Prompts

A prompt is a `prompt` block on a case action: `deadline_seconds`, `text`, optional `guard`, optional `escalation` (a second deadline and text). **Engine.** It is scheduled when the run enters a phase in which the action's tag resolves to critical, at phase entry plus the deadline. At the deadline the engine checks the action is not satisfied, reads the guard once, and checks the cap. A guard false at that moment is not retried. The escalation is its own event with its own deadline. A covered sibling never prompts. A prompted action counts as done and is not penalized, only noted in the debrief.

**Default. Not every critical action needs a prompt.** Prompt where delay carries real clinical cost. A prompt trills, so prompt for fewer things and mean it.

**Default. The nurse names the problem, not the drug.** "Her pressure is still low and nothing is running" is the default form: the concern and what is visible. End on an open question: "Her mean pressure is under 65. Should we do something?" (owner, 28 October 2026). Where the case hides a source or a disclosure, the prompt cues sideways with a question whose answer leads there, and names neither the source, the exam nor the drug. TSS asks "Did someone check if she's pregnant?", and her answer mentions her period. The prompt names the treatment only where the case decides a junior would be told it, and that is a per-prompt choice recorded in the SEED. Either way the prompt is a warning that comes before the consequence (section 15), never a lecture before the learner has acted.

**Engine. The cap.** `prompt_cap_recommendation.per_phase` limits the prompts spoken per phase. It defaults to 3. An escalation is exempt. A follow-up prompt is never silenced by it but uses a slot. The prompts a deterioration rests on must be the earliest in the phase. The deterioration timeline marks the ones the cap would suppress, and the engine suite walks the do-nothing path. Put the reasoning in `rationale`.

### 7.3 What a prompt may say

Within a phase the patient does not change, so a prompt that says the patient is getting worse contradicts a static monitor. Describe the current state or express concern about inaction. In a phase with a timed exit a prompt may name the consequence ("if we don't get an antibiotic into her, she's going to get worse"), which is still not permission to describe the numbers as moving. The narration on a timed transition is the one place a trajectory is described (15.3).

**Truth**, four rules for the text. No validator checks them.

1. **True in each phase** the action is critical in and the guard can hold. A consequence counts: "she is going to drop her pressure" is false in a phase where it already has.
2. **No claim that a treatment was given** unless the guard tests its flag.
3. **No study finding** unless the guard tests `study S resulted`. Let the study's own prompt cover the learner who has no tracing.
4. **The deadline falls after the earliest moment the guard can be true**, since the guard is read once. Work out when it can first hold for a learner following the prompts. Write every escalation so it reads correctly as a first warning.

**Truth.** A prompt quotes no vital sign (5.4). Spoken numbers are spelled out.

### 7.4 Deadlines and the difficulty modes

The learner chooses normal or easy on the splash, and a case starts in normal. **Engine.** Normal multiplies every prompt deadline, escalation and follow-up deadline by three and changes nothing else: turnaround, transitions, effects and tags are identical. The physiology is the same in both modes and only the amount of help differs, which is why deterioration is not scaled.

**Default. Author deadlines for easy mode, then check the default mode.** Get the relative urgency between actions right first. The absolute numbers are provisional.

**Engine. The floors are the only hard rule on timing**: a deterioration on inaction fires no sooner than 30 seconds (warning below 60), a delayed consequence no sooner than 5, and the warning for a deterioration comes at least 20 seconds before it (section 15). Beyond the floors, how generous a deadline is belongs to the case: a learner should run out of time for indecision, not for reading. The clock does not pause for reading or thinking. It pauses when the window loses focus, during the leave dialog, and once per case at the six-minute reflection pause, which every learner meets.

**Truth. In the default mode the warning still comes first.** For every deterioration timed from phase entry, each prompt its guard rests on, times three, must land before `after_seconds`, with room to act. Equal is not enough: when a prompt and a deadline fall on the same instant the deadline wins and the prompt is canceled. The validator and the timeline read the authored deadlines, so neither sees this. Where the physician decides a deterioration should arrive unwarned in the default mode, record it in the SEED and in the rule's `author_rationale`. A deterioration timed from `guard_true` has no fixed relation to the prompt clock: play that route in the default mode.

**Truth.** Write prompts that still make sense arriving late. In normal mode many runs end with the prompt never firing.

---

## 8. The interview

A fully authored bank with intent matching. **Engine.** No model generates clinical content. A model may only match free text to an authored topic, and the authored answer is printed as written. An unauthored topic is a dead end: the learner gets the fallback and cannot tell it from a denial.

### 8.1 Topics

Each topic carries `topic`, `canonical`, `variants`, `answer` (an ordered rule list, unconditional default last), and the optional fields of section 24.

- **Default.** Ten to twenty hand-written variants. The validator warns below ten. The build adds the shared library's phrasings on top (8.6).
- **Default.** Variants are in the learner's register, not the patient's: include the abbreviations a resident types (`PND?`, `PMH?`, `meds?`, `NKDA?`). The lay-language rule is for answers.
- **Default.** Variants for a topic every case shares may be copied from an existing pack. They are questions, not facts, and need no sign-off. Say so in the topic's `authoring_note` (`variants_provenance` is overwritten by the build).

### 8.2 Topic coverage

**Truth. Every case opens with `presenting_story`.** A greeting or an open question ("Hi", "Hello", "What's going on?", "What happened?", "What brings you in today?") gets a brief history of the present illness: two to four sentences in the voice of whoever is answering, saying what happened, when, and the main complaint. It never gives away a disclosure the case holds behind its own question. Without it the first thing a resident types is answered by the fallback or by the wrong topic. Map it to the shared concept `presenting_story` in `TOPIC_MAP`, and add greetings to its variants, which the shared library does not carry. The validator warns when the topic is missing.

**Truth. Author every topic a resident would plausibly ask.** That usually means: onset, timing and progression, character, location, radiation, severity, aggravating and relieving factors, each associated symptom as its own topic, past medical and surgical history, medications, allergies, social history with substance use, family history, last oral intake, pregnancy where applicable, and code status where the presentation makes it live. Where breathlessness is the complaint, home oxygen too (owner, 28 October 2026). Author a topic even where it is clinically irrelevant here, because the denial is the teaching and the fallback reads as the software failing. This is the one list in the document whose cost of omission is friction.

### 8.3 Three response types

**Engine.** In-scope positive: the patient has this and says so. In-scope negative: the patient denies it, authored as its own topic. Out-of-scope: no topic matched and the patient gives the fallback, in this patient's voice, which the case must supply. A learner cannot distinguish a denial from a missed match if a negative falls through to the fallback, and those are clinically opposite.

**Truth. Mark a topic `pertinent_negative` only if its answer denies in every phase**, and mark nothing else. The validator prints the marked topics as explicit denials and the matcher harness counts them as management-changing. A topic that reports anything ("a bit of a dull head") is not a denial.

### 8.4 What the patient may say

- **Truth.** The patient never states or implies the diagnosis, and never reports information they could not know: no lab value, imaging result or vital sign number. Attributing today's episode to a known history is naming the problem. A known past diagnosis in lay terms is fine ("my heart doesn't pump properly").
- **Default.** Lay language. A patient who is a nurse may not.
- **Default. One or two sentences.** An answer gives the fact asked for, not the speaker's reasoning about it. A follow-up `fact` holds the detail (owner, 23 October 2026: DIPH's onset answer was too long).
- **Engine.** Answers change only through the authored rules, never through the matcher.
- **Truth.** Do not author the scaffolding into answers. "Like I said", "Sorry, do you mean", "No, that's everything" come from `interviewDefaults` and may be overridden per case under `interview`.

### 8.5 Alertness and distress

**Engine.** A patient at alertness 2 or 3 cannot give a history. Author it once as a global rule in `interview.global_answer_rules`, which precedes every topic. There is no alertness predicate, so the rule enumerates the phases, and the validator checks that every non-terminal phase at level 2 or 3 is covered. The list may be empty in a case with no such phase.

**Truth. Speech limited by distress is a second, shorter answer with the same fact**, not a suppressed one. Author it on every topic the distressed phase can reach.

**Default. A relative may answer instead of the patient.** Write every answer in that voice, including the alertness rule. The tab heading cannot change.

### 8.6 Matching, the shared library and the held-out file

Two stages, fused per topic. The lexical stage always runs: IDF-weighted overlap with a clinical abbreviation lexicon, typo repair against the case's own vocabulary, and compound-question splitting. The embedding model is optional and may never load. **Default.** Author as though it will never load.

**The bank is expanded at build time.** `TOPIC_MAP` in `case_4_interview.py` gives each topic the shared concepts in `catalog/interview_phrasings.py` it draws phrasings from, `EXTRA_COVERED` names what the answers cover without drawing phrasings, and `build_case.py` calls `catalog/interview_expand.py` on every build. The expansion is deterministic and never stored in the sources. Every sixth new phrasing per topic and every sixth out-of-scope entry is withheld into `<PREFIX>-matcher-tune-questions.json`, the tuning set.

**Engine. The out-of-scope bank** (`interview.out_of_scope_bank`) is generated from `catalog/interview_out_of_scope.py`, filtered to the concepts the case does not cover, and both stages score it like a topic. **Truth. It must hold no question the case answers.** A topic special to the case needs a concept in `TOPIC_MAP` (add one to the shared library if none fits) and the tags its answers cover in `EXTRA_COVERED`. List a tag only when an authored answer really covers the question. Editing an existing entry's `covers` changes every later pack's bank and is a shared-file change worth a line in the handoff. After the build, read the bank from top to bottom beside the topic list, and ask the built simulator each question that looks answerable.

**The held-out file**, `<PREFIX>-matcher-eval-questions.json`, is what gets quoted. **Truth.** Write it before the first build, so held-out questions stay out of the bank. Write it in the register you expect, not the one you write variants in, and have a different person or a separate model pass write it from the one that wrote the variants, or say in `authoring_note` that the same hand wrote both. Keep `management_changing` and `interview.key_topics` the same list. **Default.** At least thirty questions with `expect` null. **Truth.** Never tune against the held-out set and then quote it. A pack with no held-out file is unmeasured, and its review packet says so in those words. The number to watch is the wrong-topic rate on management-changing topics. `node engine/matcher_eval.mjs --only <PREFIX>` measures the shipped matcher.

---

## 9. Exam, status, results and consultants

All use one structure: a key owning an ordered rule list, unconditional default last. **Engine.** Inside `content_keys.labs` and `content_keys.imaging` every key except `authoring_note` is a study block with `rules` and `changes_with_state`.

### 9.1 The default is normal

Resolution is the case's content, then the catalog default, then an error. A study the case forgot returns a normal result with full confidence. Three defenses: the validator refuses a condition that names a study the case has not authored and warns on a critical-tagged study with no authored result, the debrief lists everything answered by a default, and the sign-off asks. None catches a study nobody thought about.

**Default. Where the diagnosis makes the catalog normal wrong** (a clear film in florid pulmonary edema), author the abnormal, mark the payload's `verify` as derived from the diagnosis, and list it in the SEED. Where the prompt is silent and the diagnosis does not force it, leave the default and name the study in the SEED.

### 9.2 Exams

**Engine.** Fourteen maneuvers and no more: `exam_airway`, `exam_breath`, `exam_circ`, `exam_heent`, `exam_neck`, `exam_card`, `exam_pulm`, `exam_abd`, `exam_gu`, `exam_back`, `exam_msk`, `exam_skin`, `exam_neuro`, `exam_psych`. The catalog's `exam_finding_routing` says which owns a finding that does not fit cleanly: jugular venous distension and tracheal position under `exam_neck`, peripheral edema under `exam_card`, capillary refill and pulse quality under `exam_circ`, work of breathing under `exam_breath`, consciousness and GCS under `exam_neuro`, rash and diaphoresis under `exam_skin`. **Default.** Follow the map even where you would have chosen differently, so a learner learns where to look. Findings the map sends to no maneuver cannot be examined for and cannot be a teaching point. **Airway, breathing and circulation.** The learner examines these three together, with one button on Stabilization (`exam_abc`), which logs `exam_airway`, `exam_breath` and `exam_circ` in its place. Author findings, tags and expectations on those three as before. Never bind or tag `exam_abc`: it is never logged, so anything on it never fires.

**Default.** Author only maneuvers whose findings are abnormal or change with treatment. Keep a finding to a chart line, about 15 words, abnormal first. **Truth.** Interpretation belongs in the debrief note, not the finding. A finding that quotes a vital sign is false while an effect on it is acting (section 16). Exams show what can be seen: a paralyzed patient does not convulse. Describe a sign without naming it where recognizing it is the lesson.

### 9.3 The general status line

**Engine.** `content_keys.general_status` must exist. It sits above the maneuvers, cannot be skipped, and defaults to "No acute distress. GCS 15." above whatever exam you authored. **Truth.** Author it per phase for any other patient, consistent with the neurological exam, the appearance values and the figure.

### 9.4 Results

**Engine.** Results are structured: `kind` is `panel`, `value`, `report` or `image` (section 23). A payload and each component carry `abnormal`, and each component a label, a value and a reference interval. The validator warns where a parseable lab interval disagrees with the flag (imaging components are not checked). **Truth.** You set the flag. The renderer does not compute it, so sign-off is two things per value: the number and the flag.

- **Default.** Author only abnormal values and values that trend with treatment. Use the catalog's units (US conventional: mg/dL, mEq/L, lactate and gases as the catalog default shows). Convert a value given in another unit and say so in `verify`. Where the catalog has a default for the analyte, use its interval. Where you are unsure of an interval, write a `verify` note instead of guessing.
- `changes_with_state` is a reviewer aid read by no tool: `true` when the rules give different values in different states. Keep it honest.
- **Engine.** A result freezes at order. Serial testing cannot be represented: a repeat in an unchanged state returns the same value. A result may be keyed on a related flag inside one phase, with phase rules first. **Truth.** Any text that quotes a value is then true for every variant the learner may have on the chart.
- **Truth.** A report that quotes a vital sign is false while an effect on it is acting. Leave the rate out of an ECG report where an effect on it has no end.
- **Truth. Author findings, not conclusions.** A report that ends "interpretation: cardiogenic pulmonary edema" has done the work the case was setting. The reasoning goes in the study's debrief note. Cut the views obtained and the secondary measures that merely agree.
- **Truth.** A gas agrees with the monitor and with Henderson-Hasselbalch, and moves with the dose where the case titrates to a pH.
- **Truth. A culture cannot be the teaching point.** Results arrive in seconds and the catalog returns "Cultures pending".
- **Engine. Turnaround by catalog class:** labs, plain films and the ECG 5 seconds, ultrasounds and cross-sectional imaging 10 (ultrasounds since 28 October 2026), other bedside tests at once. A scenario, test or prerequisite that waits on an ultrasound waits 10 seconds for it.

**`comment`** is printed in the debrief only, under the numbers of a `panel`, `value` or `image`, and nowhere for a `report`. **Truth.** It holds what those numbers show and nothing else: not the diagnosis, nothing from another result or the history, nothing to the reviewer (that goes in `verify`, which is never shown). **Default.** Not the lesson either: that is the action's note. **Engine.** A study with an authored abnormal result needs a case action, or it has no note and no tag.

### 9.5 Consultants

The most state-dependent key. **Engine.** First match wins, so order rules from most specific to least. Unrelated consultants inherit the global "does not know why they were called" reply.

- **Truth.** Every tier that names a finding or a value tests `study S resulted` for the study it came from, the deteriorated-phase tiers included. Split a phase tier in two: one on the phase and the study, which may quote the value, and one on the phase alone, which says what is visible and asks for the study. Search every consultant value for a digit and check its rule.
- **Truth.** A quoted value is the value on the chart, so a result that varies with a flag inside the phase is quoted as a direction, not a number.
- **Truth.** A tier that says a treatment was given tests its flag.
- **Truth.** A consultant who declines must not give credit. A state-changing consult satisfies its expectation whatever the reply says. If the consult needs a study first, make that a prerequisite on the action with the request as its failure message.
- **Default.** Author a pending tier per study, not per group: with a 5 to 10 second turnaround there is a window in which a study is ordered and not resulted, and "either study ordered" fires when one has resulted and the other was never sent.
- **Default. 40 words or fewer, in about three short sentences:** what the consultant thinks, what to do now, and where the patient goes or when to call back. The learner reads the reply in the middle of the case, and a long one hides the instruction. The reasoning and the teaching go in the action's `debrief_note`. The validator warns above 40 words.

One workable order, an example and not a template: deteriorated-phase advice, then definitive advice once the key studies have resulted, then a holding reply while they are pending, then a default asking for the workup that has not happened.

---

## 10. Handoff, diagnoses and the debrief

### 10.1 Handoff

The case completes when the learner submits the handoff, one click. Supply the correct disposition and level of care, plausible alternative dispositions each with an explanation (or marked defensible with qualification), the correct diagnosis as a catalog id, at most one additional major diagnosis, the minor diagnoses that are also true, plausible alternative diagnoses as catalog ids with explanations, and `disposition_display_order`.

- **Engine.** Diagnosis ids resolve against the diagnosis catalog. The validator reports one that does not. `python3 engine/lookup.py diagnosis <word>` finds them. A common misdiagnosis that is not in the catalog is a catalog change request.
- **Default.** Disposition ids are the case's own strings. No catalog holds them. Reuse the ids the newest pack uses (`icu`, `stepdown_telemetry`, `medical_floor_telemetry`, `observation_unit`, `discharge_home`, `transfer_tertiary`) and add one only for a disposition the case needs.
- **Default.** One fixed display order, least intensive first, so position says nothing about the answer. An id left out is appended with a build note.
- **Truth.** Wrong dispositions and diagnoses have explanations, not verdicts. A learner who picks one has revealed a specific misunderstanding.

Results still pending at handoff are recorded automatically. An early exit produces a debrief marked incomplete.

### 10.2 Several diagnoses

The learner lists as many diagnoses as apply, in order, and the first is the primary.

**Truth. The handover is scored on the one or two major diagnoses only** (case author's instruction, 23 October 2026). The primary is one. `additional_diagnoses` holds at most one more, `{catalog_id, label, explanation}`: a second diagnosis that changes what the receiving team does. It earns credit when listed, and when not named it is printed under "Also true of this patient, and not named". Everything else true of the patient goes in `minor_diagnoses`, the same shape: an electrolyte value (hypomagnesemia, hyponatremia), a complication the primary implies (lactic acidosis, AKI), the trigger, the syndrome around the agent. A minor diagnosis is never scored. Named, it is marked "also true" and costs nothing. Left out, it costs nothing and is printed under "Also true of this patient, not scored". Test: would a senior correct a handover that left it out? If not, it is minor.

**Engine.** The validator refuses a second additional diagnosis, and an additional or minor diagnosis that is not in the catalog or repeats the correct one or each other. It warns on one with no explanation. `correct_diagnosis` scores the primary. `alternative_diagnoses` carry the verdicts for a primary that is not it (`acceptable_with_qualification` is defensible, anything else incorrect). A diagnosis may sit in both lists. For a poisoning, name the agent as the primary, the mechanism among the additional diagnoses and the syndrome as a defensible alternative, so a learner who names any level is credited.

### 10.3 Debrief notes

The debrief is where the words go. The patient's response is the first feedback (guide, belief 2). **Truth.** Every tagged action, every timed transition, every follow-up, every wrong disposition and diagnosis, and every exam maneuver the case authors has a note. A note states what the action does, why it was right or wrong in this case, and what should have happened instead, in the voice of one doctor talking to another. Each is collapsed behind the action's display name, so the note has to be worth opening on that name alone. A prerequisite has no note field: its `failure_message`, spoken at the time, is the only teaching a blocked attempt gets, and the debrief timeline shows the attempt as "did not happen".

**Default.** `debrief_configuration.cross_cutting_teaching_points`: three to six, most important first. The first three print under the critical actions, the rest at the end.

**Engine. Markers are stripped from four fields only**: an action's `debrief_note` and `references`, a timed transition's `debrief_note`, and `cross_cutting_teaching_points`. A marker is text in square brackets starting `UNVERIFIED`, `PubMed`, `VERIFY` or `MODEL OUTPUT`. Everywhere else it is printed to the learner as written: a follow-up's note, every handoff explanation, a `halt_reason`, a `timeout_reason`, a `comment`, and everything the nurse, the patient and a consultant say. Put no marker in those. If a sentence there rests on an unchecked source, record it in `provenance.reference_status` and keep the sentence to what you will print.

**Engine.** An action's `references` are shown behind a "Sources" button at the end of its note. **Truth.** References are optional and an unverified one is worse than none. Mark anything unchecked. Where the evidence is contested, say so in the note.

**Style, for everything a learner reads.** Plain, direct, short sentences. US spelling and US words: "seizing", not "fitting", and no "registrar", "trolley", "half seven" or "paracetamol" (owner, 23 October 2026). Interview variants may keep British forms so either matches. No em dashes, no semicolons. Spoken text spells numbers out, titles and chart lines use numerals. Findings in results, interpretation in the debrief. The nurse and the debrief speak as one doctor to another.

### 10.4 The seven scores

The Summary prints one score per category and the arithmetic beside it. **Engine.** History is key topics asked over `interview.key_topics`: author it, or every topic counts and a thorough learner scores 40 percent. Physical is regions examined over the exams tagged critical or recommended, or `debrief_configuration.key_exams` where none is, or every authored exam failing that. The four ordering tabs score critical at two points and recommended at one over what was expected in the phases visited, a discouraged action costs one, a harmful halt zeroes its tab. A recommended line or monitor is left out of the debrief's recommended lists on purpose and still counts in the score. Handoff is level of care (40), the primary diagnosis (40, or 60 with no additional diagnosis) and the additional diagnosis (20), a defensible answer earns half, and a wrong primary or an unsupported diagnosis costs five. Minor diagnoses add and cost nothing. **Engine.** The overall score on the second dial is critical actions (85) plus the recommended actions and the handoff (15 between them). The history and the examination keep their Summary rows and are not in it (owner, 28 October 2026). The validator checks that `key_topics` and `key_exams` name things in the case.

### 10.5 The case discussion

The left column of the revealed debrief. **Engine.** `cases/<PREFIX>/<PREFIX>-discussion.html`, read at build time, with no scripts and no `on*` attributes. Markers are stripped as in 10.3. Generate it from a script in `Claude outputs/` and edit the script, not the HTML. AFRVR and TSS are the models (`Claude outputs/dbv2/afrvr_discussion_v2.py`, `dbv3/tss_discussion_v1.py`).

**Default, the form the owner settled on (23 and 28 October 2026)**, for a reader short on attention:

- A learning-goals box of up to six short lines, then "The patient" with one bold line and three or four sentences.
- Four to seven numbered sections. Each opens with one bold line (`p.cd-key`) and then short bullets that lead with a bold phrase. A reader who reads only the bold lines gets the case.
- Three or four figures. Each has its point in bold above it (`p.cd-point`), few elements, labels of 14 to 16 px, and numbers taken from the case's own phases and results. Say in the caption when a number is illustrative.
- A "Traps" list, then the references folded away (`details.cd-refs`).
- About 3,000 px tall at 620 px wide.

**Truth.** The discussion agrees with the case's own debrief notes (the antibiotic regimen, which treatments score). A definition is read in its source, not recalled. Mark anything unchecked `[UNVERIFIED]` and list it for sign-off. Render it after ending a case and look at every figure before handing over.

---

## 11. Checks, review artifacts and the sign-off

### 11.1 What the validator enforces

`python3 engine/validate_case.py <PREFIX>` reports errors and warnings and writes the review matrix. It is a structural claim. It enforces, as errors unless marked:

- Every rule list ends in an unconditional default, every condition parses, every referenced action, flag, study and phase exists.
- Every phase is reachable and every non-terminal phase has a transition and a rule into `case_complete`. Every critical action is reachable. Vitals and appearance are present and in range. `halted` exists only when a tag can be harmful, and then it must.
- Every tag is a rule list of the five values. A harmful-capable action has a halt reason. A missing debrief note warns.
- Every prerequisite flag is settable, chains are not circular, every prerequisite has a failure message, and a `waived` string that names no catalog prerequisite of the entry warns.
- Every follow-up has `applies_when`, `deadline_seconds`, `nurse_prompt`, `debrief_note` and one of `satisfied_by` or `satisfied_when`. Every id in them is a case action. Something fires each follow-up, and `triggered_by` agrees with `follow_ups_triggered`.
- A `prompt` block has a deadline and text, and an escalation that is complete and later than the first. A prompt that lands at or after a phase's earliest timed exit warns.
- Timed rules: the floors and the warning below 60, `measured_from` values, a rationale on an unguarded rule, narration, note and rationale on every timed rule, an opt-in and rationale on a terminal destination, an exit on every non-terminal destination, no cycle of time edges that can repeat, and the prompt-first rule: every flag or action a guard negates is prompted for in that phase at least 20 seconds before the deadline (a negated study gets the floor only). A narration on an instant rule warns.
- Payloads are structured with `abnormal` on each level, a label, value and interval on each component, and parseable intervals agree with the flags (warning). An image payload has a file and no report text.
- Every case action has a binding row. Unmatched rows warn, `BLOCKING` rows error, two case actions on one catalog entry warn. No exam outside the fourteen. `general_status` exists. Every alertness-gated non-terminal phase is covered by a global rule.
- A study named in a condition or tagged critical but unauthored warns, naming the default.
- Arrival: `mode` and `location` values, the handover present and not the scaffold text, a note on its sentence and word count, a warning above two sentences, a warning when a quoted saturation disagrees with the first phase.
- Handoff: the correct and alternative diagnosis ids resolve, at most one additional diagnosis, additional and minor diagnoses resolve and repeat neither the correct one nor each other, intercepts name a disposition the case offers and a case action other than `handoff_submit`.
- Mechanisms: `also_satisfies` targets a case action other than itself, `inherit_vitals` sits on a terminal phase only, `flags_set_repeat` needs at least 2 and its flag is not in `flags_set`, a flag nothing reads warns, `voice_phrases` are non-empty strings and a duplicate warns.
- A consultant line over 40 words warns (9.5).
- A shape fault the checks cannot read (a missing required key) prints one `[crash]` error naming the line instead of a traceback. Fix it and run again: the list is not complete until the validator runs through.

**What it does not check**, each of which a pack has shipped with: that a narration, report or finding is true of the monitor with effects counted (section 16), that a prompt's text is true in every phase its guard allows (7.3), that a warning comes before its deterioration in the default mode (7.4), that a `satisfied_by` action could not have been done before the trigger (22.2), that a consultant tier quoting a value tests the study (9.5), what a `comment` says, whether a `pertinent_negative` topic denies, that the out-of-scope bank holds no answerable question, which of two pending timed rules fires first (15.4), and what an image shows (section 23). Those are sign-off items.

### 11.2 The review matrix

`<PREFIX>-review-matrix.md`, rewritten on every validator run. For each key it enumerates every combination of the flags, studies and phases in that key's own rule list and shows what the key resolves to. **Truth. Read it in full.** On the first case, four clinically wrong resolutions raised no error anywhere and were found only here, three of them on the deterioration branch. What it has found since: an exam still abnormal after the treatment that fixes it, a lab that improves across a deterioration, a creatinine that falls in minutes, a bladder still full after a catheter, a lactate normal in a rhythm with no output, a procedure permitted in a phase that contraindicates it, consultants quoting arrival values in later phases.

What it leaves out: prompts, prerequisites, follow-ups, transitions and their narration, vital effects, `also_satisfies`, interview `facts`, `volunteer` lines and the figure's `also`. It stops at 96 rows per key. Its "reachable?" column reads the case's own `review_hints.implausible` pairs (`[{flag, requires, why}]`) and calls every other row plausible, which means nobody checked. It shows a key in a phase, never how the phase was reached and never the monitor with an effect acting.

### 11.3 The scenarios and the case tests

Two artifacts walk the case. They are not equal.

**`<PREFIX>-scenarios.json`**, run by `engine/sim_runner.py`: `{scenarios_version, case_id, note, scenarios: [{name, steps, expect_phase, note}]}`, a step being an action id or `{"wait": n}`. The runner is a second implementation of the phase machine. It charges 8 whole seconds per action step (a wait step advances its own seconds), asserts the final phase only, reads catalog defaults by the case id, and ignores timed flags, effects, prompts, follow-ups and `also_satisfies` (a scenario through a hidden target names the target as a step). A runner pass is weaker than an engine test pass. Every story from the seed is a scenario, and a known gap is a scenario named "Known gap:".

**`<PREFIX>-tests.js`**, run by `engine/engine-tests.js` against a built simulator, folds a real log through the shipped engine and is the authority. It is evaluated inside the harness with these globals: `chk(name, cond, extra)`, `section(name)`, `mk(steps)` (steps are `[t, actionId]` pairs), the id lists `EXAMS`, `STUDIES`, `HARMFUL`, `CRITICAL`, `START_PHASE`, `CASE` and `ACT`, and the engine's own `fold(log, now, difficultyMultiplier)`, `tagOf(id, st)`, `generalStatus(st)` and `patientVisual(st)`. The folded state exposes `phase`, `phaseSeq`, `nurse`, `promptFires`, `timeFires`, `blocked`, `satisfied`, `expected`, `fuOutstanding`, `discouragedTaken`, `orders`, `readouts` and `monitoring`. **Engine.** A log entry for an id the pack does not build is ignored with no error, so assert that the action was taken as well as the phase reached. Fractional times, the folded vitals with effects, every nurse line and a multiplier of 3 are all available here and nowhere else.

**Engine. The shared suite walks the do-nothing path.** If any timed rule can fire on its own, one must fire from the start phase with nothing taken. If none can, nothing may change. Every deterioration narration arrives on the deterioration channel. **Truth.** Test coverage is never a reason to edit clinical content: do not change a deadline, a dose or a finding to make a test easier to write. Change the test.

### 11.4 The deterioration timeline

`python3 engine/deterioration_timeline.py <PREFIX>` writes three parts: every timed exit by phase with the prompts before it, the do-nothing trajectory with the clock at each hop, and every narration line beside the vitals of the phase it introduces. The do-nothing part walks `phase_entry` rules only. Delayed consequences (`guard_true`) are in part one and absent from part two by design. Read each exit asking two things: would this patient really deteriorate in that time without that treatment, and was the learner warned early enough to act. If the last row is a terminal phase, the case can kill the patient without the learner touching her, and that is a decision to remember making.

### 11.5 The sign-off

The release gate. Every line, by the physician named in the SEED.

**Goals and structure**
- [ ] The seed says how this case differs from the library on the six dimensions, and the web does not repeat one already built unless the medicine demands it.
- [ ] Every goal names its source or is labeled an opinion. Every goal is acted on somewhere other than the debrief. Every phase, finding and branch names the goal it serves.
- [ ] Each phase's "what now?" differs from the phase before. A clinician would agree with every transition as a statement of cause.
- [ ] The idea that travels is stated in the debrief and acted on in the case.
- [ ] Played badly on purpose, the run ends with the learner blaming a decision of their own, and the debrief names that decision.

**Clinical content**
- [ ] Every abnormal finding, lab and imaging result is correct for this diagnosis, carries its flag, and no normal value carries one. Intervals are right for the assays modeled. Derived findings are listed in the SEED.
- [ ] Every harmful action is lethal on the evidence and its halt reason is accurate. Nothing harmful should have been discouraged and nothing discouraged harmful. No critical action is optional and no neutral action is critical.
- [ ] Findings change after successful treatment where the medicine says they do, and not where it says they do not.
- [ ] Every debrief note teaches something correct and every reference has been checked. Markers sit only in the fields the interface strips, every unchecked claim there has one, and the provenance block lists each reference with how it was read.
- [ ] After any change to a vital, a lab or a deadline, the sources have been searched for the old figure. Consultant replies, diagnosis explanations and debrief notes quote numbers no rule can reach.

**Catalog**
- [ ] Every mapped row is clinically sound. Every harmful and discouraged action covers every route to the act, and a discouraged or rescuing stop covers every sibling stop.
- [ ] Every case-only action is a decision in the SEED, has a placement, and its spoken phrases have been tried. No `short_label` names the diagnosis, mechanism or missing treatment.
- [ ] Exam findings sit where the routing map puts them, and the status line matches the patient.

**Handover and interview**
- [ ] The handover names no diagnosis, is never wrong, and any vital in it is a past measurement that agrees with the first phase. Read cold, it gives somewhere to start and nowhere to finish. Anything it carries beyond the default list has its reason in the SEED.
- [ ] Every topic a resident would ask is authored. The case has been played through the History tab alone. The patient never reveals the diagnosis or anything they could not know.
- [ ] Every `pertinent_negative` topic denies in every phase. Model-added denials are listed in the SEED.
- [ ] Every topic the distressed phase can reach has a shorter answer. Paraphrase coverage is adequate on every management-changing topic.
- [ ] The held-out file exists, was written before the first build, and its results are in the review packet with each management-changing miss named, or the packet says the interview is unmeasured. The out-of-scope bank has been read against the topic list.

**Prompts and the nurse**
- [ ] No prompt implies the patient is deteriorating, quotes a vital sign, claims a treatment or cites a study its guard does not test, or has a deadline its guard cannot meet. Each is true in every phase its guard allows and names the drug only where the SEED says so.
- [ ] Every `nurse_alert`, `narration_override`, narration, status line and consultant line on a covering action names the class and not one drug, and claims nothing the prerequisites do not guarantee.
- [ ] Relative urgency between prompts is right. In the default mode, with prompt deadlines times 3, the warning for each deterioration still comes first, or the exception is a recorded decision.

**Results and consultants**
- [ ] No consultant line references a study not ordered or still pending. Every line with a number sits on a rule that tests `study S resulted`, deteriorated tiers included, and is true for every variant on the chart. No consultant declines while the press earns credit. A pending tier exists per study.
- [ ] Every consultant line is 40 words or fewer and gives the impression, the next step and the disposition or callback. Its reasoning is in the debrief note.
- [ ] No `comment` names the diagnosis, quotes another result or speaks to the reviewer. No report carries a comment the learner needs.
- [ ] No report, finding or alert quotes a vital an endless effect can move.

**Sequencing**
- [ ] Prerequisites are clinically correct and every waiver is deliberate. Follow-ups are triggered by the right action, apply only where indicated, list every satisfier, and none that asks for "again" or "after" relies on `satisfied_by` for an act the learner could have done first.
- [ ] Every deterioration branch has an exit that exists, and the exit is not satisfiable by what the patient had on the way in.

**Each mechanism the case uses** (Part Two): the items its section lists.

**The play**
- [ ] The review matrix contains no clinically wrong resolution, read in full, with the deterioration timeline, every prompt against each phase, and every consultant line and comment with a number read in the same sitting.
- [ ] The case has been played start to finish in the interface at 1x in the default mode, including each halt and each deterioration branch the case has, with each case-specific order spoken into the microphone. The builder's scripted play-through is a tool check and not this item.

---

## 12. What the engine cannot do

Design around these. Each is a deliberate trade.

- **Flags are binary and permanent** unless granted with a duration (section 17) or on the Nth administration (section 18). No titration, no third dose that differs from the second, no reading a count in a condition.
- **Order cannot be expressed in a condition.** A prerequisite carries it (22.1), `also_satisfies` credits only in a named state (section 19), and a phase can stand for what has already happened. The third opens a race wherever two timed rules are pending (15.4).
- **"Again" and "after" are not in the language.** `satisfied_by` and `action A taken` mean ever in the run. 22.2 has the one pattern for "after".
- **Serial testing cannot be represented.** A repeat in an unchanged state returns the same value. A culture cannot be the point.
- **Nothing depends on dose.** Two boluses are two administrations of one thing.
- **No condition can test a vital.** Branching on a number means the number is a phase.
- **A vital effect moves the monitor and nothing else**, and a result never sees an effect (section 16).
- **Deterioration is all-or-nothing per rule** and in steps. There is no gradient and no graded lateness. One vitals block per terminal phase.
- **Turnaround is compressed** to seconds, and the splash says so to the learner.
- **Adults only** for now: the arrival card colors vitals by adult ranges.
- **The interview returns only what is authored.** An unauthored topic is a dead end.

---

## 13. The route: building a case end to end

A Python pack is `build_case.py` plus `case_1_shell.py` (`META, PATIENT, PHASES`), `case_2_actions.py` (`ACTIONS, FOLLOW_UPS`), `case_3_content.py` (`EXAM, GENERAL_STATUS, PATIENT_VISUAL, LABS, IMAGING, CONSULTANTS`), `case_4_interview.py` (`TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES, KEY_TOPICS, VOLUNTEER_SETTINGS, TOPIC_MAP, EXTRA_COVERED`), `case_4_variants.py` (`SHARED`) and `case_5_handoff.py` (`HANDOFF, DEBRIEF, PROVENANCE`). **Engine.** Edit the Python and never the JSON. The next build overwrites it.

**Step 1. Scaffold.** `python3 engine/new_case.py <PREFIX> "Title"` writes the folder, a JSON skeleton, the binding map, and the test and scenario stubs. Its SEED template is older than section 2. Until restructure step 3 replaces it, keep the folder and the stubs, discard the JSON, and copy the Python layout and the SEED headings of the reference pack named in `CLAUDE.md`.

**Step 2. The seed** (section 2), in the SEED's order. Read the case index first. Record every decision with a name and a date, and repeat it where it is used.

**Step 3. Bind** (6.2). The rows are written in `build_case.py`. Run `python3 engine/bind_catalog.py cases/<PREFIX>` and read the counts.

**Step 4. Draft the case** against the seed: phases, transitions, tags, prerequisites, follow-ups, content keys, interview, prompts, handoff, notes. Everything a model adds beyond the seed is listed as model-added. Route each finding to its maneuver (9.2) and structure each result (9.4).

**Step 5. The interview files.** Write `<PREFIX>-matcher-eval-questions.json` by hand first (8.6). Fill `TOPIC_MAP` and `EXTRA_COVERED`, adding a concept to `catalog/interview_phrasings.py` where a topic has none. Build, read what was dropped, then read the generated bank against the topic list. Repeat whenever a topic changes.

**Step 6. Test.** In this order, from the repository root:

```
python3 cases/XX/build_case.py cases/XX        # expands the interview, writes the case, binding map and tuning file
python3 engine/bind_catalog.py cases/XX
python3 engine/test_packs.py XX                # one-pack build in a scratch folder, then the engine tests, the
                                               # scenarios, the validator (which writes the review matrix), its
                                               # negative tests and the deterioration timeline
node    engine/matcher_eval.mjs --only XX      # add --semantic if huggingface.co is reachable
python3 engine/build_simulator.py              # every case, into build/ and site/, for the play-through
python3 engine/gen_docs.py                     # the generated indexes
python3 engine/kit_check.py                    # before any handover
```

Run the validator until it is clean or every remaining error is a catalog change request you have raised. One warning stays for good: the case-only actions, which always include `handoff_submit`. Read the names each time. A full `build_simulator.py` rewrites `build/`, `site/`, `private-packs/` and `vercel.json`, and the validator rewrites the review matrix: list those in the handoff as regenerated, not edited. Never pass a pack name to `build_simulator.py` before running tests by hand against `build/`: a named build leaves `build/` holding only that pack. `validator-tests.py` mutates the pack to prove the validator catches faults and needs one follow-up, one authored imaging study and two topics. A pack without those cannot run it: say so in the handoff rather than adding content to satisfy it.

**Step 7. Scenarios and tests** (11.3). A scenario for every story in the seed: treated well, each wrong way, left alone, each halt, each blocked prerequisite, the rescue inside the last window and one action too late. Case assertions for each mechanism the case uses, as its Part Two section lists, and property assertions over every phase ("no clock reaches a terminal phase", "no prompt quotes a number"). Two runs that differ by one action find precedence faults.

**Step 8. Read** (11.2, 11.4): the matrix in full, the timeline with each effect's delta added by hand to the rows it can reach, every prompt against each phase, every consultant line and comment with a number.

**Step 9. Play.** The builder scripts a play-through with Playwright against `build/simulator.html` for anything a learner would see, and records what it saw. The local build's speed control (`[` and `]`, up to 16x) is for the long waits, and the debrief says when it was used. Then the physician plays it at 1x (11.5).

**Step 10. Hand over.** Write the review packet: status line ("drafted by a language model, not reviewed, not for learners"), the files to read, the counts from the last run and not from memory, every vital effect labeled a teaching choice, the matcher results or "unmeasured", what was not run, and "sign-off: not started". Optional review questions for the physician go in `<PREFIX>-review-questions.json`, which the review page merges at build time. Record in the SEED every question these documents did not answer. Add the case to the Case Maps artifact with `Claude outputs/casemaps-gen/v2/` (a config of paths, each with the ending it must reach). Nothing outside `cases/<PREFIX>/` is edited for a case, and `engine/kit_check.py` checks that.

---

# Part Two. The mechanisms

Each section is read only when the case uses the mechanism. Each ends with its sign-off items.

## 14. Choosing a mechanism

Six constructs touch time, move a number, or count. None is hard to use. The mistake is reaching for the wrong one, and the question that separates them is what else in the case has to know.

| Reach for | When | What can read it |
|---|---|---|
| A **phase** | The patient has changed clinical state | Everything |
| A **timed transition** (15) | Something has to happen, or a consequence arrives after a delay | Everything, since it changes the phase |
| An **expiring flag** (17) | Something is true for a while and then is not, and the case must react | Everything in the condition language |
| A **vital effect** (16) | A number on the monitor moves and nothing else does | Nothing. Display and sound only |
| A **repeat-granted flag** (18) | The act has to be performed more than once before it works | Everything in the condition language |
| **Credit by state** (19) | The same act is right at one point and wrong at another, and order is the lesson | The expectation it satisfies |

Worked choices: "BiPAP raises the saturation while the mask is on" is one effect guarded on not being intubated. "The nitrate wears off and the pressure rebounds, and the learner has to notice" is an expiring flag, a transition guarded on it, and a narration, because the patient really is different. "Steroids take twenty minutes" is an onset, and usually means the case should not model it. "The patient deteriorates if nobody gives antibiotics" is a timed transition with its fairness rules. "One dose slows him a little and two get him there" is an effect for the partial response, a repeat-granted flag for the second dose, a phase guarded on the flag, and a `nurse_alert` saying the drug takes time. "A consultant takes over" is a `guard_true` transition on the consult's flag with a narration naming who acted, and nothing the learner pressed is credited, which is the point.

**Default.** When a drug both shows on the monitor and changes what the case does, put the clock in the flag and guard the effect on the flag. One deadline in one place. **Default.** A phase is not expensive, and reviewers can only see phases. If the patient is worse, that is a phase and not a negative delta.

## 15. The clock: timed transitions

A transition rule may carry `after_seconds`. It then fires when that many seconds have passed and its guard still holds. The clock is used seldom, and it is one more tool the case may pull in to force action where that helps the case. From anywhere, something happens if the learner does nothing, and in most phases that something is nothing.

```json
{"when": "NOT flag abx_given set", "after_seconds": 240, "measured_from": "phase_entry",
 "to": "progressive_sepsis",
 "narration": "The spots on her ankles have joined up while we've been standing here.",
 "debrief_note": "The organism was never treated and the bacteremia progressed. Meningococcal disease is measured in hours and the rash is the clock you can see.",
 "author_rationale": "Deterioration on inaction. Untreated meningococcal bacteremia progresses over minutes to hours. Model output."}
```

### 15.1 The fields and the four shapes

**Engine.** `after_seconds`, a whole number. `measured_from`, `phase_entry` (the default) or `guard_true`, and `guard_true` needs a guard. `narration`, `debrief_note` and `author_rationale` on every timed rule. `allow_time_to_terminal` and `terminal_opt_in_rationale` when the destination is terminal. `unguarded_rationale` when `when` is null. **Default.** Start `author_rationale` with the shape's name and end it with who decided it, or "Model output".

- **Deterioration on inaction.** `NOT flag F set`, from phase entry. A negative guard can only be falsified, so once the drug is given the deterioration is canceled, not deferred. **Default.** Guard it on a flag, as every pack does. A guard on `NOT action X taken` is held to the same floor and prompt rule. A guard on `NOT study S resulted` gets the 30 second floor and no prompt check, so a deterioration for a study not sent needs a flag.
- **Delayed consequence of an action.** `flag F set`, `measured_from: "guard_true"`. Peri-intubation collapse forty-five seconds after the tube teaches that the induction agent and the positive pressure did it, and leaves room for a pressor.
- **Scheduled natural history.** No guard. A febrile seizure self-terminating, a thrombolysis window closing, the second phase of a biphasic reaction. **Engine.** Needs `unguarded_rationale`, because a transition nothing can prevent is a decision and not an oversight.
- **Outcome chosen at a scheduled time.** A positive guard from phase entry placed above an unguarded rule with the same `after_seconds`: what is running by then decides where she lands. **Engine.** The guarded rule goes above the unguarded one.

Shapes the library has used, each a teaching choice and not a measurement: anaphylaxis `NOT flag epinephrine_im_given set` 120 s, status epilepticus 180 s, tension pneumothorax 90 s to a terminal phase with opt-in, febrile seizure unguarded 90 s, biphasic anaphylaxis unguarded 400 s, peri-intubation `flag intubated set` 45 s from `guard_true`.

**How a `guard_true` clock runs.** It belongs to one rule in one phase. It starts at the first transition check in that phase that finds the guard true, or at entry if it already holds. It does not carry into the next phase: a rule with the same guard there starts from zero. If the delay must survive a phase change, record it as a known gap or put the consequence in one phase. **Engine, known limit.** If the run returns to a phase, a `guard_true` rule there keeps its first start time and can fire on arrival. Avoid a `guard_true` rule in any phase the case can re-enter, or record the gap.

**Engine. A transition can grant flags** (owner, 27 October 2026). `flags_set` on a transition rule grants those flags for good as it fires, before the new phase is entered. Use it to make a timed event happen once: a rule whose guard needs the flag unset, and which grants it, fires at most once. A flag only a transition grants is bookkeeping, not an obligation, so the fairness rules in 15.2 ask for no warning for it, and the loop check counts it as set after the edge. Where a case can re-enter a phase, give the rules that apply after the event their own guards, so each has its own `guard_true` clock. DIPH's one-time relapse does this (`seizure_relapsed`).

### 15.2 The fairness rules

**Engine.** The validator enforces each.

1. **Floors.** A rule with no guard, or with NOT anywhere in its guard, fires no sooner than 30 seconds and warns below 60. A `guard_true` rule with a positive guard fires no sooner than 5. Any other rule, 30 with no warning. In a mixed guard only the atoms under the NOT count as needing a prompt, and the deterioration timeline treats every flag in such a guard as unset, so check a mixed guard by hand.
2. **A warning comes first.** For every flag the guard needs unset, some action that sets it prompts in that phase at least 20 seconds before the deadline. A deterioration nobody warned about is a trap the learner could not have seen. The warning names the problem by default (7.2).
3. **A prompt that cannot fire warns.** A prompt at 260 seconds in a phase that ends at 240 is never heard.
4. **A terminal destination needs the opt-in**, and never the shared `halted` phase, which carries a harmful action's halt reason: attributing an omission to a commission teaches something false. Author your own terminal phase with its own `timeout_reason`. A terminal phase reachable by clock and by action has a `timeout_reason` that names both.
5. **No cycle of time edges that can repeat.** A loop that needs a permanent flag, an action or a study both absent and present runs once and is a note.
6. **Every destination has an exit**, and **Truth.** the exit is not satisfiable by what the patient had on the way in. A phase entered for lacking B, with an exit guarded on A OR B, sends a patient who had A straight back and restarts the clock. Guard the exit on what was missing.

### 15.3 What it costs

Prompts and the deadline share the phase. Everything the nurse must say has to land before the phase can end, and in the default mode prompt deadlines are tripled (7.4). This is the usual reason to lengthen a deadline.

**Truth. The narration is the one place a trajectory is described**, because one has just happened. It must be true of the numbers shown immediately afterwards: the destination's authored vitals plus every effect acting there. A narration into a phase an effect can reach quotes no number unless every such effect has been checked (section 16). A line that says a number fell needs a phase in which it was higher. The timeline prints authored vitals only, so fold a log with each effect-bearing action and compare the line with the folded vitals.

Deterioration is all-or-nothing. A rescue timed from `guard_true` has to be due before the deterioration is: subtract its `after_seconds` from the deterioration's and treat that as the real deadline. You now review a path nobody takes on purpose: the do-nothing trajectory (11.4).

### 15.4 Two timed rules pending at once

The condition language cannot express order. A case that teaches order carries it in phases, and that is sound while one timed rule is pending. When two are pending, which fires first decides the outcome and no tool checks that you meant it. Each `guard_true` rule has its own clock. At any deadline the phase's list is read from the top and the first rule whose guard holds and whose time is up fires. Two rules due at the same instant: the higher one. An action logged at the same instant as a deadline is applied first.

**Truth.** For every phase with two or more timed rules, list every pair in the SEED, and for each say which fires first for each order and gap and where the patient ends up. Test each row with fractional times, because a boundary between two whole seconds passes every whole-second test. Fix the rows the case does not teach by changing the phases, or record each as a known gap pinned by a scenario.

**Sign-off.** Every deadline is a claim you will defend: this patient, without this treatment, deteriorates in about this long. Every deterioration has a warning early enough to act on, in both modes, and the timeline confirms it. Every narration is true of the monitor with every reachable effect acting. Every pair of pending rules has its line in the SEED and a fractional-time test. The do-nothing trajectory is right end to end. If the clock can end the case, you meant it, and the `timeout_reason` names the omission. No prompt in a timed phase is stranded past the exit.

## 16. Moving a vital with an action

A phase holds until something moves the case out of it, which makes it the wrong tool for an effect that lasts thirty seconds and is gone, an effect that ends when the drip is stopped, or a drug that changes the patient without changing the number the learner is watching. Author those on the action:

```json
{"catalog_id": "niv_bipap_cpap",
 "vital_effects": [{"vital": "oxygen_saturation", "delta": 3, "key": "positive_pressure_spo2",
                    "while": "NOT flag intubated set"}]}
```

**Engine.** `vital` (one of the six) and `delta` (added to the phase baseline, may be negative) are required. `duration_seconds` is omitted for an effect that lasts as long as its guard holds. `while` is an ordinary condition, re-evaluated continuously, read against the state now and not the state when the drug was given. `key` defaults to the action id, and effects sharing a key replace rather than stack. Effects add, clamp and snap. They do not multiply, ramp, titrate or depend on dose, an effect cannot read another, and a result never sees an effect. Effects are ignored in a terminal phase.

- **Truth. Rebase the phases.** Every non-terminal phase's authored vitals are what the patient shows with nothing running, or the number is counted twice. The validator catches only the half that leaves the plausible range.
- **Engine. Give two routes to the same drug the same key**, or a cannula, a mask and a bag stack into an improvement none would produce.
- **Truth. Sizes are teaching choices.** No trial supports a specific figure. Put the reasoning in a `note` on the effect and say "teaching choice" in the review packet.
- **Truth. An effect follows the patient into every phase its guard allows and makes text false there.** A report or finding that quotes a vital is false while an effect on it is acting, so where an effect has no end, quote no number for that vital anywhere ("Sinus tachycardia", "Pulse fast"). A `while` of `NOT phase is presentation` on a drug given in the presentation phase switches on the moment she leaves it, so if a phase already carries the change, guard the effect off in that phase by name. Check: for each effect, write down the phases its guard allows and how long it lasts, then read every narration into, and every report, finding and alert in, each of those phases.
- **Engine. "Stop the drip" is a `while` guard** on a flag the stop action sets: `NOT flag <stop flag> set`. Nothing stops an effect you author on its own.
- **Engine. Pressors have a default** (owner, 27 October 2026). A pressor with no `vital_effects` of its own takes the catalog default in `catalog/default-vital-effects.json` (norepinephrine, epinephrine, vasopressin, phenylephrine and dopamine drips, and push-dose epinephrine, phenylephrine and vasopressin boluses), so the monitor answers a pressor in any case. Display only: it changes no phase, tag, flag or score. A default drip ends when its stop order is given and resumes if restarted. Your own `vital_effects` replace the default whole. `"vital_effects": []` means none: use it where the pressor's flag moves the phase and that phase's vitals already carry the rise. The validator warns on exactly that pattern.
- **Default.** Decide which vitals a treatment does not move. The thing that does not happen is usually the lesson, and a case where every treatment raises the number is a case where sequencing does not matter.

### 16.1 Delayed onset and a climbing number

**Engine. The drug overlay.** In every case (`medOverlayCases` is `"all"` in `engine/build_simulator.py`, 28 October 2026), every drug and fluid is drawn above the patient with a countdown, and a drip as a pump until it is stopped. With a timed effect (an onset, a duration or a timed flag) the countdown ends when the effect is complete. With none, it is display only: 10 s for a syringe, 60 s for a fluid bag (`MEDVIS_DEFAULT` in ui.js). The overlay is not evidence of timing, so a drug whose timing matters needs its own timed effect.

`onset_seconds` delays the start. Both it and `duration_seconds` are measured from the administration, so the effect acts over `[onset, duration)`. **Engine.** A duration that does not outlast its onset never acts and the validator refuses it. It prints every window as a note. To make a number climb rather than jump, author several small effects on one action with rising `onset_seconds` and a different `key` each.

**Sign-off.** Every non-terminal phase's vitals are the unsupported baseline. You have played the case with each effect-bearing action alone and read the number off the monitor. Every route to a drug shares one key and no two keys name one act. Every pressor whose flag moves a phase authors its effect or carries `[]`. Every delta and duration is labeled a teaching choice. The treatments that move nothing do so on purpose and the debrief says why. No report, finding or alert quotes a vital an endless effect can move. No `while` switches an effect on in a phase that already carries the change. Every window in the validator's note is the one you meant.

## 17. Expiring flags

A flag granted with a duration is removed when it lapses, and the case can react:

```json
{"catalog_id": "nitroglycerin_sublingual",
 "flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 300}]}
```

A transition guarded on `action nitroglycerin_sublingual taken AND NOT flag nitrate_acting set` fires on its own at the moment the flag lapses, with the learner sitting still, which is what `duration_seconds` on an effect cannot do.

- **Engine. A permanent grant wins, in either order.** If the infusion sets the flag through `flags_set` and the bolus grants it for 300 seconds, once the drip is running the flag never expires. The validator warns so it is a decision. A repeat dose moves the deadline to the later of the two.
- **Engine. A lapse is not an action.** It costs nothing and appears in no timeline. If the lapse fires a transition, put the words in that transition's `narration`.
- **Engine. A lapse can speak** (28 October 2026). `lapse_note` on the grant is what the nurse says, as an alert, when the flag lapses. The latest grant's line is said, once. Use it for a short-acting drug whose effect ends with no phase change: `{"flag": "nitrate_bolus_acting", "duration_seconds": 60, "lapse_note": "The nitro has worn off..."}` with a `vital_effects` entry guarded `while: flag nitrate_bolus_acting set`. If the duration is shortened for teaching, the line says so. No reviewer markers, since the nurse says it aloud. The validator refuses an empty note.
- **Default. A bolus and an infusion of one drug need not do the same thing.** If only the infusion should move the phase, keep the shared phase flag off the bolus and give the bolus a timed effect instead (CHFE, 28 October 2026).
- **Engine. Do not put an expiring flag in a tag.** The critical set of a phase is computed at entry, so an action that becomes critical on a lapse is never listed as missed. The validator warns.
- **Engine. Every timed flag is read by something**: a transition, tag, prompt guard, prerequisite, content rule or an effect's `while`. The validator warns otherwise.

**Sign-off.** Every expiring flag is read, and by a transition rather than a tag. Every effect that ends with no phase change has a `lapse_note` or a reason it has none. A drug that both moves a number and changes the case holds its clock in one place. You have played the case doing nothing after the drug and watched the consequence arrive. Every duration is a claim you will defend. Where a drip and a bolus both grant the flag, you meant the drip to stop it expiring.

## 18. Flags granted on the Nth administration

For the case whose lesson is the redose, a restart, or a repeat study:

```json
{"catalog_id": "digoxin_bolus", "flags_set": ["rate_control_given"],
 "flags_set_repeat": [{"flag": "rate_control_adequate", "after_administrations": 2, "counter": "rate_control_doses"}]}
```

**Engine.** `after_administrations` is at least 2. The flag is not also in `flags_set`. `counter` defaults to the act, so a covered sibling adds to the same tally. Named, several actions share one tally. Two actions granting one flag at different totals warn. The count knows nothing about what came between two administrations, so two orders with no hold between them set a restart flag, and a repeat study sent before the treatment sets the repeat flag. Use the pattern in 22.2 for "after".

- **Default.** Two flags: `flags_set` says an attempt was made and drives the effect and the follow-up, the repeat flag says enough attempts were made and drives the phase.
- **Default.** The partial response is an effect, not a phase, guarded off the phases whose vitals already carry the controlled number, with a `nurse_alert` saying the drug takes time, or the learner reads a failed drug and reaches for another.
- **Truth.** List every action that is the same act on one counter, and write a scenario for each first dose.

**`flags_set_if`** (owner, 27 October 2026): a list of `{"flag": ..., "when": ...}` on a case action. Each flag is granted for good, but only if its condition holds as the act is taken, judged before the act's own flags are granted. It tells a dose given after some event from the doses before it, which neither a permanent flag nor a count can: DIPH's bicarbonate grants `bicarb_after_relapse` only once `seizure_relapsed` is set. **Engine.** A flag name and a condition are both required. An unconditional grant belongs in `flags_set`.

**Sign-off.** A scenario for each first dose and each early repeat, and the limits in the SEED.

## 19. Credit by state, and a handover that shows the truth

**`also_satisfies`** on a case action: a list of `{"id": <case action>, "when": <condition>}`. When the action is taken and the condition holds at that moment, the named action counts as satisfied: its expectation is met, its prompt stops, follow-ups naming it are discharged. The action keeps its own tag, flags and note. Use it when the same drug is right at one point and wrong at another and the order is the lesson. A null `when` always holds: use it for an act that discharges another's expectation and still needs its own tag, result or effect, where `also_covers` would lend it the other's fields instead. **Engine.** The condition is judged before the action's own flags are granted, so an action cannot satisfy its own condition. The target is a case action and not the action itself. An exam can carry it.

**`asked_all`** on a case action: a list of interview topic ids. The action is satisfied once every topic in the list has been asked or volunteered, in any order and in any phase. Use it for questions that are one clinical act only as a set, such as the questions a decision rule turns on (SCOOT's `cchr_history`, 29 October 2026). **Engine.** Every id is a topic in the case's interview. **Default.** Make it a hidden target with a placement on the `history` tab and a `display_name`, as for `interview_topic_<topic>` (section 6.1). **Truth.** A question asked of a patient who cannot answer still counts as asked, as it does for an `interview_topic_` action, so tag it critical only in the phases where the patient can answer.

**`inherit_vitals: true`** on a terminal phase shows the vitals of the phase the run came from with the effects acting then. **Engine.** Terminal phases only. **Truth.** Use it on `case_complete`, so a learner who hands over a patient they never treated is not shown a better patient.

**Sign-off.** Each credit condition is the state the medicine means, and a scenario covers the act before and after it.

## 20. A disposition that has a consequence

Confirming a handoff ends the run. A case may say that one disposition, chosen in a state it names, does not:

```json
"handoff": {"disposition_intercepts": [
  {"disposition": "discharge_home",
   "when": "(phase is presentation OR phase is fluid_responsive) AND NOT flag discharge_attempted set",
   "action": "attempt_discharge"}]}
```

The interface logs `action` in place of `handoff_submit`, clears the disposition and returns to the Stabilization tab. **Engine.** The action is a case-only action with a row carrying `catalog_id: null` and an `unmatched_placement` on the `handoff` tab, which draws no buttons. Without the placement the rule is skipped with no error and the disposition ends the run. `when` includes `NOT flag <its flag> set`, or the learner can never hand that disposition over. **Default.** Tag it `discouraged`, give it a flag, a `narration_override`, a note and `hidden: true`, and put the consequence on a `guard_true` transition so the nurse can say what happened.

**Default.** Use it wherever letting the disposition play out teaches the reason and ending the run would only teach the verdict. A case may make "do less" or "send home" the right answer. The one lever for scoring restraint today is a `discouraged` tag on the tempting act.

**Sign-off.** The intercepted disposition can still be handed over once the consequence has played, and the learner is told what the attempt did.

## 21. Harmful actions that halt the case

**Engine.** An action whose tag resolves to `harmful` bypasses transitions and moves the patient to the `halted` phase, carrying the action's `halt_reason`. A case with any harmful tag authors `halted`, with vitals and appearance, although the learner never sees it: the run ends at once and the debrief opens. A case with none does not author it: the validator reports it unreachable. The engine throws on a harmful tag with no `halted`.

**Default.** A halt is used sparingly, where the act is lethal and the lesson is the verdict. Where the lesson is the consequence, the alternative is an instant transition into a terminal phase the case authors (shown with the case's own vitals and a `timeout_reason`), or better, a deterioration phase the learner can get out of (section 4). The action keeps a `discouraged` or `neutral` tag either way. The seed says per wrong action which it is (2.4). **Truth.** Do not halt what only makes him worse (29 October 2026).

**Sign-off.** Every halt is lethal on the evidence, its reason is accurate and names the commission, and each halt has been played.

## 22. Prerequisites and follow-ups

Different mechanisms. Conflating them is the most consequential authoring error available: a prerequisite gates an act on what must already be true, a follow-up creates an obligation after an act.

### 22.1 Prerequisites

**Engine.** A prerequisite is `{when, failure_message}`. Failing it blocks the action, speaks the message, logs the attempt and changes nothing. Write the requirement, not the block: `flag iv_access set` means the line must be in, and `NOT flag iv_access set` blocks every action that should have been allowed. Both parse. Case prerequisites are added to the catalog's, and a case prerequisite identical to a catalog one is deduplicated by its `when` string. **Engine.** To waive a catalog prerequisite, `prerequisite_overrides` is `[{"waived": <the catalog prerequisite's when string, character for character>}]`. `python3 engine/lookup.py prereq <id>` prints it to copy. A string that matches nothing waives nothing, and the validator warns.

- **Default.** Most prerequisites belong in the catalog. Author one per case only where this case differs (a crash airway in arrest needs no induction).
- **Engine.** Catalog failure messages take the pronoun from `patient.sex`. An override waives a gate, never fixes a pronoun.
- **Truth.** The failure message is the only teaching a blocked attempt gets and the only place the control explains itself, so it names what must happen first, in the nurse's voice. Blocked actions stay visible and unannotated on purpose.

### 22.2 Follow-ups

**Engine.** Each follow-up carries `applies_when`, `deadline_seconds`, `nurse_prompt`, `debrief_note`, `triggered_by`, and one of `satisfied_by` (a list of case actions) or `satisfied_when` (a condition). It is scheduled from the triggering action's `follow_ups_triggered` list, one check per administration, the deadline multiplied by the mode. `applies_when`, `satisfied_by` and `satisfied_when` are read at the deadline, not at the trigger, so `applies_when` may name a phase the action leads to. `satisfied_by` asks whether a listed action has ever been satisfied in the run. `triggered_by` must list the actions that trigger it, and the validator checks that something fires each follow-up.

- **Engine. Post-intubation follow-ups are not graded.** A follow-up triggered by the intubation action (the catalog's `intubation_actions`, in `catalog/ungraded-intubation-care.json`) carries `"graded": false`. The nurse still asks at the deadline. The debrief does not list it as an obligation left open. The validator refuses one without it. `graded` defaults to true for every other follow-up.
- **Truth. List every satisfier.** If sedation may be propofol or ketamine and you name only propofol, a learner who chose ketamine is told they left a paralyzed patient unsedated. A covered entry satisfies its covering action, so name that once.
- **Truth. `satisfied_by` cannot say "again" or "after".** An act done before the trigger discharges the follow-up before it exists. For each id, ask whether a learner could reasonably have done it first. If so, use one of the three below.

| Use | It can see | It cannot see |
|---|---|---|
| `satisfied_when` with a repeat-granted flag (18) | That the act was done N times | Whether the Nth time came after the trigger |
| `satisfied_when` with a phase or ordinary flag | The state at the deadline | How it was reached, or when |
| A hidden target action credited through `also_satisfies` with a `when` (19) | The state at the moment of the satisfying act, so with `when` set to the trigger's flag or phase, "after the trigger" | A second round: once credited the target stays satisfied |

The third is "do it again after". Author a case action whose only job is to be the target (`chest_rechecked`): neutral tag, a row with `catalog_id: null`, a placement on the `handoff` tab, `hidden: true`. On each real satisfier add `"also_satisfies": [{"id": "chest_rechecked", "when": "flag fluids_given set"}]`, and set the follow-up's `satisfied_by` to `["chest_rechecked"]`.

**Sign-off.** Prerequisites are clinically right and each waiver is deliberate. Follow-ups are triggered by the right action, apply where indicated, list every satisfier, and have a scenario with the satisfying act before the trigger and after it.

## 23. Showing a study as a picture

```json
{"kind": "image", "abnormal": true, "image": "diph-ecg-arrival", "caption": "Twelve-lead ECG"}
```

**Engine.** The file lives in `media/` inside the pack, named for the id, as `.jpg`, `.jpeg`, `.png`, `.webp` or `.gif`. Every file in `media/` is inlined into the build whether or not a payload names it, so put a file there when the case shows it and not before, resized and recompressed. An image payload carries no `report` text or `components`. A missing `caption` warns. The image opens full size the moment it results and the clock keeps running.

- **Truth. A caption is a caption, not a reading.** "Twelve-lead ECG", or the machine measurements a real tracing prints, which a learner would have at the bedside. "Wide-complex tachycardia with a terminal R in aVR" is the answer.
- **Truth.** Nothing in the tool chain can see what an image shows. It is the only authored content whose correctness rests entirely on a person having looked at it. Before using one, write down: that the picture matches the phase, that no number the case needs the learner to read has been lost from the interface (if so, it belongs in the caption), and that some studies showing themselves in text while others do not is a choice you can defend.
- **Truth.** Do not put anything in `media/` whose source you cannot account for.

- **Default (13 October 2026). A twelve-lead is a generated tracing.** Draw it with the ECG generator from the case's own read, as WebP 1800 pixels wide, and record in `media/README.md` the script, the date and anything the read left open that the drawing had to choose. Put the read in `comment`, which the debrief prints under the tracing. The caption is `Twelve-lead ECG.` followed by the machine measurements in the case's own numbers (ventricular rate, PR, QRS, QTc), with no closing period because the chart adds one, less any the case holds back: DIPH prints none, and DKA and TAKO print no rate because vital effects move it. Where the read leaves an interval open, take it from the phase's monitor block, so the caption and the monitor agree.
- **Default (29 October 2026). A chest film is a picture from the owner's folder "Images Manual - Chest XRay"**, chosen for the patient's sex and findings (`Normal/Normal_Male.png` or `Normal/Normal_Female.png` for a normal film), converted to WebP (quality 82, 1024 pixels, greyscale), with the read in `comment`. Every pack that can order a chest film shows one. Record in `media/README.md` the folder path and the date. Where the case can intubate, give the intubated state its own film with a tube drawn in (`Claude outputs/ett_v1/cxr_ett_draw.py`, used for MGCA, CHFE and SCOOT) and a read that mentions the tube, or the picture contradicts the state. **Truth.** The folder records no original source or licence for its films. Find and record it before release.
- **Truth. A tracing has a rate, and a read need not.** Where one rule covers states with different heart rates, give each rate its own rule and picture (TAKO since 13 October 2026), or the picture contradicts the monitor. Where a vital effect moves the rate within a state, draw the rate on the likely path and say which in the README (DKA: with fluid after arrival).

**A scan the resident scrolls (19 October 2026).** An image payload may add `series`, the stem of two files in `media/`: `<stem>.series.json` (format `emsim-ct-1`: `n`, `w`, `h`, `pixel_mm`, `thickness_mm`, `z_mm`, `start_image`, `windows` as `{name, w, l}`, `label`, `title`, `synthetic`, `notice`) and `<stem>.series.gz` (Hounsfield units plus 1024 as unsigned 16-bit, gzipped as two byte planes, all low bytes then all high bytes). The `image` is the series' still and is the thumbnail. Opening it opens the CT viewer: scroll, window presets and right-drag, zoom, a 5 cm bar and the HU under the pointer, with a small drawn guide to scrolling on the left of the images. The image slider stands on the right, image 1 at the top, and the window and zoom buttons sit on the image's bottom right corner. The header reads "Interactive PACS Viewer: " and the series' `title`, the study's name as a clinician would say it ("CT Head without contrast"), or the caption when there is no title. **Engine.** The validator checks both files, the geometry and the voxel count. **Truth.** A series is one acquisition: every rule that names it is a state those images are true of. The still and `start_image` are picked by a rule that does not point at the lesion. Carry the image source's licence or notice in `notice`. It travels in the pack with the images. Since 20 October 2026 the viewer no longer prints it, so where a licence requires a visible notice, show it another way. **Default.** One series per case: a head CT costs about 4 MB in the build.

**Sign-off.** A named person has looked at each picture beside the sentences the case says about it, in the phase it is assigned to.

## 24. Facts, echoes and volunteered history

Three optional interview fields, with the mechanics in the system design.

**`echo`**: a short phrase in the patient's voice naming the topic ("my tablets", "when it started"), used as a prefix when the match was marginal and inside the clarifying question. **Default.** Every topic has one, reading after "do you mean".

**`facts`**: the atomic pieces of an answer, each with its own phrasings and a phase-conditional value, so a follow-up is answered by the piece asked about. **Truth.** A fact restates part of the paragraph and adds nothing. Mark one `restate` for the short form on a repeat. Author facts where sub-questions matter: onset (when versus how), medications (what versus dose versus adherence), anything with a time course. Without facts a topic still gains repeat handling and the echo. A pack authors its facts in its own sources. `catalog/author_interview_facts.py` serves the frozen packs only.

**`adjacent` and `volunteer`**: a topic lists adjacent topics (more than two warns). When it is first asked, the `volunteer` line of each adjacent topic not yet spoken about is added to the answer, and the adjacent topic counts as asked, for the History score and for any `interview_topic_` action, while still giving its full answer when asked directly.

- **Default.** A volunteer line is one clause under 25 words restating part of its own topic's answer. The validator warns above that. It may be phase-conditional, and a null value volunteers nothing in that phase.
- **Engine.** A topic in `interview.must_ask` can neither carry a volunteer line nor be adjacent. **Default.** The safety screens go there: allergies, drugs, pregnancy, sexual and menstrual history, self-harm, anticoagulation and bleeding, goals of care, and anything the case is built around the learner discovering.
- **Engine.** Nothing is volunteered while a global rule speaks for the patient or while `interview.volunteer_blocked_when` holds.

**Sign-off.** Every fact restates its paragraph. No must-ask topic is volunteered. Each volunteered line has been heard in the built simulator.
