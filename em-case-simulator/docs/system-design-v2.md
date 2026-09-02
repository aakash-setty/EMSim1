# EM Case Simulator: System Design

**Version 0.4 | Supersedes v0.3**

---

## 0. What changed

**v0.2 reintroduced time.** The clock governs result availability, nurse prompting, and timing feedback. It does not change the patient.

**v0.3 reframed the product as educational rather than assessment.** Several v0.2 mechanisms existed to protect assessment validity and were removed or softened.

**v0.4 makes the global catalogs real.** v0.3 described the action catalog, the diagnosis catalog and the global defaults as things that would exist. They now exist, and building a case against them surfaced a set of contracts the design had left unstated. Almost every change below is a rule that was implicit, was interpreted two different ways by two different pieces of the system, and produced a plausible-looking wrong answer.

| v0.3 | v0.4 |
|---|---|
| Catalog described in the abstract | Catalog is the action surface; a case binds to it and cannot invent entries |
| Case names actions in its own ids | Explicit case-to-catalog binding, reviewable per row |
| Results are strings | Results are structured payloads with per-component abnormal flags |
| Exam maneuvers open-ended | Exam set is closed at 14, with a routing map and a general status line |
| Case prerequisites replace catalog defaults | Case prerequisites are additive; catalog defaults apply unless waived |
| No audio | Continuous heartbeat pitched by saturation, plus a prompt tone |
| Every click performs an action | Orders are selected and submitted as a batch on order tabs |
| Four tag values | Five, with `discouraged` between neutral and harmful |
| Case starts immediately | A splash screen sets the scene and the clock starts on Begin |
| One pacing for everyone | Easy and hard modes, differing only in prompt timing |
| Engine and case content interleaved | Separated: `engine/`, `catalog/`, `cases/<PREFIX>/` |

Sections 3, 4, 6, 8, 11, 13 and 15 have substantive changes. Sections 16, 17, 18 and 19 are new.

---

## 1. Educational framing

This is a teaching tool, not a certification instrument. That sets several defaults.

**Helping the learner is the goal, not a leak.** The nurse prompting a resident toward a critical action is a feature. Prompted and unprompted performance are still tracked, but for the learner's own awareness rather than as a penalty (section 7.5).

**Repeat attempts are expected and desirable.** A resident replaying a case until they run it cleanly is the tool working, not someone gaming it. This makes restart after a harmful halt something to encourage rather than ration.

**The debrief is the product.** In simulation education the debrief is generally where learning consolidates, with the scenario as the material it works on. The score exists to direct review, not to rank. Report by clinical domain rather than as a single number (section 11).

**Case content is effectively public.** In a free open-source project the case files live in a public repository, so any learner can read them. Server-side rendering still matters, because it prevents spoiling a case mid-run, but treat it as user experience rather than protection. Design nothing that depends on the learner not knowing the answer.

**What does not change.** Clinical accuracy requirements are, if anything, higher. A learner will believe what this tool teaches, and there is no examiner downstream to catch an error. Every constraint in `case-authoring-requirements.md` about physician review and the prohibition on AI-invented clinical facts holds without modification.

Harmful actions still halt the case. The consequence is the lesson, and softening it would remove the stakes that make the case matter.

---

## 2. The time model

### 2.1 What the clock does and does not do

The clock governs three things:

1. **Result availability.** Turnaround is set per class in the catalog: labs 5 seconds, imaging 10, ECG 10, bedside 0. These are configuration values and are expected to change with tuning.
2. **Nurse prompting.** Critical actions carry deadlines measured from phase entry.
3. **Timing feedback** in the debrief.

The clock does **not** change the patient. There are no time-driven phase transitions. Vitals do not drift. An untreated patient does not deteriorate. Phases advance only when the resident acts.

This boundary is deliberate and must hold, because violating it creates incoherence the resident will notice immediately.

### 2.2 The coherence trap this creates

If the nurse says "his sats are dropping" while the monitor shows a static saturation, the case contradicts itself.

**Requirement:** nurse prompt text must describe the current state or express concern about inaction. It must never imply a trajectory, because there is no trajectory. Acceptable: "He's still working hard to breathe. Do you want to do anything about the airway?" Not acceptable: "He's getting worse." No validator can catch this, so it belongs on the physician review checklist.

**Audio inherits this constraint.** See section 8.5. A pitch that falls as saturation falls is legitimate, because saturation genuinely changed at a phase boundary. A pitch that drifts downward while the phase is unchanged would be the audible version of the same contradiction and must not be built.

### 2.3 Compressed time

The turnaround values are pacing devices, not clinical durations. Real turnaround is roughly 30 to 60 minutes for labs and 30 to 90 for cross-sectional imaging.

Optionally display a simulated clock that advances faster than real time, so a 5-second wait reads as roughly 35 minutes elapsed. This preserves the lesson that results take time and you must act before they arrive. Low priority; the underlying values are configurable and can be calibrated later.

**On the bedside class at 0 seconds.** A point-of-care scan returning in the same instant as the order removes the order-and-wait beat entirely, which is most of what the mechanic teaches. Two to three seconds preserves the beat without pretending a scan takes as long as a send-away lab. This is a tuning decision, not a structural one, but it should be made deliberately rather than by leaving the class at zero.

### 2.4 Implementation

**Server-authoritative, client-triggered.** No websockets, no background processes, no persistent simulation loop. This keeps hosting cheap enough that free global access stays viable.

Every server response includes the current view plus a **schedule**: future events with their due times. The client sets timers and issues a request when an item comes due. The server checks its own timestamps, applies every event actually due, and returns the updated view.

The client timer is only a trigger. The server decides what is due. This matters because browsers throttle timers in background tabs; when the tab returns, the next request catches up every overdue event at once.

Add a heartbeat roughly every 5 seconds while a case is active, as a safety net against clock drift and suspended tabs.

### 2.5 Session time

Elapsed time runs from case start to handoff confirmation or halt. Behaviour on abandonment and pause is an open decision (section 14).

**Order batching interacts with this.** See section 17.2: with batching, the log records the moment of submission rather than the moment of decision, which changes what timing feedback measures.

---

## 3. Data layer

### 3.1 Global action catalog

Every drug, exam maneuver, lab, imaging study, ECG, consultant, stabilization task, and procedure in the product. Each entry defines:

| Field | Purpose |
|---|---|
| `id` | Referenced by cases and by the binding |
| `display_name` | What the resident sees, unless the case overrides it |
| `placements` | Tab and group; drives the entire action surface |
| `category` | exam, investigation, medication, stabilization, procedure, consultant, blood_product |
| `state_changing` | Whether performing it can change state |
| `turnaround_class` | For investigations: lab, imaging, ecg, bedside |
| `narration_template` | Nurse line, for example "Giving {dose} of {name}." |
| `default_prerequisites` | Standard gating, applied to every case unless waived |
| `flags_set_default` | Flags the action sets everywhere, for example `insert_iv` sets `iv_access` |
| `default_result` | For investigations and exams: the normal finding, see 3.2 |
| `persistent`, `repeatable`, `dose_required` | Display and behaviour hints |

No clinical judgment lives here, because appropriateness is case-dependent. Every value that is not transcribed from the interface should record its provenance, because a field derived by convention and a field taken from a real menu need different levels of scrutiny.

**The catalog is the action surface.** A case does not add buttons. The resident sees the catalog, filtered by tab, whether or not this case has anything to say about a given entry. This is not a convenience: a menu that shows only the actions relevant to this case tells the resident the answer before they start.

**Consequence:** if a case needs an action the catalog does not have, that is a catalog change request, not something to author around. The alternative is content no learner can reach.

### 3.2 The default result contract

Resolution order for any study or exam:

1. Case content for the current state, if authored
2. `entry.default_result` in the catalog
3. If neither exists, the study returns nothing and the validator errors

Every component of a default is in range and carries `abnormal: false` explicitly.

**The renderer does not recompute in-range.** A case that overrides a value must set `abnormal` itself. Two reasons. First, reference intervals are assay- and institution-specific and a renderer that decides for itself will disagree with the laboratory the case is modelling. Second, the interpretation is often not the number: a pO2 of 95 is normal on room air and alarming on a non-rebreather, and no renderer can know which.

**A normal default is not a neutral default.** If an author forgets the troponin in a myocardial infarction case, the resident is shown a normal troponin and is taught the wrong thing, with no error raised anywhere. Section 13 requires a warning for this, and section 11.1 requires the debrief to list what was answered by a default rather than by the case.

### 3.3 Result payload shape

```json
{"kind": "panel|value|report|exam_findings|general_status",
 "abnormal": true,
 "components": [{"label": "Sodium", "value": "133", "unit": "mEq/L",
                 "reference_range": "135-145", "abnormal": true}],
 "comment": "optional interpretive line",
 "verify": "optional note where the reference interval is not settled"}
```

`panel` and `value` carry components. `report` carries a `report` string. `exam_findings` and `general_status` carry a `findings` string.

Payload-level `abnormal` must equal the OR of its components. The interface renders abnormal components distinctly, currently in red.

**Do not parse prose.** The tempting shortcut is to look for "(high)" in an authored string at render time. It is the exact recomputation this section forbids, it fails silently the first time an author writes "raised" or gives a bare number, and the failure mode is a genuinely abnormal value displayed as normal.

### 3.4 The exam set is closed

The catalog defines exactly 14 exam maneuvers. There is no fifteenth. Each carries a default finding, so a maneuver a case does not author still returns something.

Because 14 maneuvers cannot cover every anatomic region, the catalog also supplies **`exam_finding_routing`**: a fixed map from findings that do not fit cleanly to the maneuver that owns them. Peripheral oedema belongs to the cardiovascular exam, jugular venous distension to the neck exam, capillary refill to the circulation exam, and so on.

**The map is not a convenience, it is the point.** Without a fixed routing an author puts pedal oedema under cardiac in one case and musculoskeletal in another, and the resident concludes the tool is arbitrary rather than learning where to look. Authors follow the map even where they would have chosen differently.

Findings routed to "no available maneuver" cannot be examined for and must not be a case's teaching point.

### 3.5 The general status line

A short line rendered above the exam maneuvers. It is **not clickable and cannot be skipped**, which makes it the one exam finding every resident sees.

It has a catalog default ("No acute distress. GCS 15.") and should be overridden per phase by any case whose patient is not that. A case that makes its patient critically unwell and forgets this key displays a reassuring line above a comatose neurological exam. The validator requires the key to exist.

### 3.6 Global diagnosis catalog

A large searchable list used at handoff, matched on display name and synonyms so a resident typing STEMI, DKA or AAA finds the entry. See section 9.

**Cases reference catalog ids, not free-text labels.** A correct diagnosis resolved by string matching is a correct diagnosis that can silently stop matching.

### 3.7 Case file

Metadata, patient definition, phases, case actions, content rules, interview bank, prompts, and handoff definition. Detailed in `case-authoring-requirements.md`.

The client receives only resolved content for the current state, so a case is not spoiled mid-run. As noted in section 1, this is not a protection mechanism in an open-source project.

### 3.7a Equivalence groups

The catalog declares sets of entries it considers interchangeable, such as the four crystalloid boluses (normal saline and lactated Ringer's, at two volumes each).

They exist because splitting a generic entry into explicit ones is usually right for the resident and dangerous for the author. A generic "crystalloid bolus" hides the choice a clinician actually makes; four explicit entries expose it, and simultaneously create three unguarded routes to the same harm the moment a case tags only one of them. A group lets one case action claim all four, so coverage cannot drift as the catalog grows.

Each member keeps its own id, button and display name. Only the case-specific fields (tag, halt reason, debrief note) are shared. The mechanism works in both directions: a harmful tag that must not be escapable, and a required action that any member should satisfy.

### 3.8 The case-to-catalog binding

A case authored before the catalog existed, or authored by someone thinking in clinical rather than catalog terms, will not use catalog ids. Resolving this by string similarity at load time is not acceptable: the near-misses are clinically adjacent (`ketamine_bolus` against `ketamine_infusion`, `normal_saline_1l` against `lactated_ringer_s_bolus`) and a wrong bind is silent.

Either the case references catalog ids directly, or a **binding file** sits between them with an explicit status per row:

- `exact` the case id is already a catalog id
- `mapped` a different id for the same action; the mapping is an author judgement and carries a note
- `unmatched` the catalog has no entry; this is a validator error and a catalog change request

**One case action may bind to several catalog entries**, and for harmful actions it usually must. If the case tags a one litre crystalloid bolus as harmful and binds it only to normal saline, a resident who reaches for lactated Ringer's causes the same harm and the case does not halt. A harmful tag has to cover every route to the harm.

Where two case actions bind to one catalog entry the interface can offer only one button, and the second case action is unreachable. The build must report this rather than dropping it.

---

## 4. Condition language

One language everywhere: content rules, clinical tags, prerequisites, and phase transitions. Five predicates combined with AND, OR, NOT.

| Predicate | Meaning |
|---|---|
| `phase is X` | Current phase is X |
| `flag F set` | A completed action set flag F |
| `study S ordered` | S has been ordered, result may still be pending |
| `study S resulted` | S has been ordered and its result has arrived |
| `action A taken` | Action A was performed |

`ordered` and `resulted` were one predicate before timers existed. The split is justified by the pending state being real.

Use `flag` rather than `action taken` for state-changing actions, since every one of them sets a flag. Reserve `action taken` for observational actions, for example a consultant who responds differently depending on whether the abdomen was examined.

**The trailing keywords are mandatory.** `flag F set`, not `flag F`. `study S ordered`, not `study S`. The short form is grammatical to a human reader and unparseable to the engine, and it has already reached shipped data through an example in an earlier version of the authoring document. The parser must reject the short form rather than accepting it, so the defect surfaces at build time rather than at runtime.

**This applies to catalog conditions too.** Default prerequisites in the catalog use the same language and must satisfy the same grammar. The validator checks the catalog, not only the case.

### Time is deliberately excluded from this language

There is no `elapsed > N` predicate. Timing lives only in explicit deadline fields on prompts and follow-ups.

If time entered the general condition language, authors would write time-conditional content everywhere and the per-key review matrix would stop being enumerable. Confining timing to named fields keeps every case reviewable by a physician. Treat requests to add a time predicate as an architectural change, not a convenience.

---

## 5. State layer

### 5.1 The log is the source of truth

A session stores the case id, an ordered log, the start timestamp, and a status of active, halted, or complete. Nothing else is authoritative.

Each entry carries a sequence number, a timestamp relative to case start, the action id, and a type:

- **state-changing**: interventions, stabilizations, study orders, consults that unlock something, handoff
- **observational**: exams, interview questions, viewing a result, most consults
- **blocked**: an action attempted whose prerequisites were not met

Blocked attempts are logged, because attempting intubation without sedation is a teaching moment that must reach the debrief.

**Prerequisites are evaluated during the fold, not before writing the log.** The log records what the resident attempted; the fold decides whether it succeeded. This keeps replay honest: a log replayed against a corrected case file produces the corrected outcome rather than a stale one.

### 5.2 Derived state

```
state = fold(log, case_file, catalog, current_time)
```

The fold produces: current phase, flag set, ordered studies, resulted studies, frozen result values, pending results with due times, halt status, the set of actions that were critical in any phase entered, and the set of keys answered by a default rather than by the case.

### 5.3 Replay must interleave actions and time events

This is the most likely place to introduce a defect.

Derived time events, meaning result arrivals, prompt deadlines and follow-up deadlines, are computed from log entries plus case data. The fold merges log entries and derived events into one chronological sequence and processes them in timestamp order.

Order a lab at t=2, give a drug at t=5, lab results at t=7. The replay must process all three in that order. Processing all actions first and then all time events produces wrong state.

**Tiebreak:** at identical timestamps, process log entries before derived events, then by sequence number. Determinism requires an explicit rule.

**Batched orders arrive at one timestamp** (section 19). They are separate log entries in selection order, so the tiebreak applies and they are processed in sequence. Prerequisites, transitions and harmful tags evaluate exactly as they would one at a time.

### 5.4 Result freezing

A result resolves against the state at the moment it was **ordered**, not when it arrives. The specimen was drawn then and the image was acquired then. A chest film ordered before intubation does not show an endotracheal tube.

Store each result as its value plus the ordering state. Reordering creates a separate result with its own order and due times. If a case needs a result to reflect post-intervention state, the author must require a repeat order.

### 5.5 Nurse prompts are derived, not stored

A prompt for critical action A in phase P with deadline D is due at (phase P entry time) + D, and fires only if A was not completed before that moment.

This is fully derivable from the log, so nothing extra is stored and no read writes to state. The debrief determines prompted versus unprompted by comparing timestamps.

Deadlines are measured from phase entry. On a phase change, outstanding prompts for the previous phase are cancelled and new deadlines begin.

**The set of expected actions is collected at the same moment.** On entering a phase, the fold records which actions resolve to `critical` against the state at entry. That set drives both prompt scheduling and the omissions section of the debrief, so the two cannot drift apart.

### 5.6 Cascading transitions

After a state-changing action the transition checker evaluates the current phase's rules once. If the destination phase's own rules are already satisfied on arrival, they do **not** fire until the next state-changing action.

This is reachable in practice: a resident who gives the diuretic early can satisfy the improving-phase transition before ever entering the stabilizing phase, and the next action then advances two phases in one step. Single-step evaluation is the specified behaviour. Authors should be aware that prompt deadlines are measured from phase entry, so a phase entered and left in the same step issues no prompts.

---

## 6. Prerequisites and follow-ups

These are different mechanisms and are easy to conflate. Keep them separate.

### 6.1 Prerequisites

Each action may carry an ordered list of prerequisite rules, each with a condition and a failure message.

**The condition is a requirement that must be TRUE**, not a block trigger. Write `flag iv_access set`, meaning the line must already be in, not `NOT flag iv_access set`. Both readings are grammatical and the resulting behaviour is exactly opposite, so this must be stated rather than inferred.

When the resident selects an action, the server evaluates the prerequisites. On failure it returns the message, logs a blocked entry, and does not change state.

**Actions remain visible and selectable.** Hiding or greying out a blocked action teaches nothing. Letting the resident attempt it and receive "the patient is not sedated or paralyzed; give induction and paralytic agents before attempting intubation" teaches the sequence. This is the pedagogical point of the mechanism.

**Do not print prerequisites on the button either.** Annotating an entry with "needs a line" is the same information delivered as a label rather than as a lesson, and it makes the gated actions visibly different from the ungated ones, which leaks structure.

In scope for catalog defaults:
- Intubation requires sedation and paralysis
- Transcutaneous pacing requires pacing pads placed
- CSF studies require lumbar puncture performed
- Any intravenous drug requires intravenous, central or intraosseous access

The last two mean investigations and medications can be gated by interventions, so both menus need a blocked state.

### 6.2 Merge semantics

**Catalog defaults apply unless the case explicitly waives them. Case prerequisites are additional, not a replacement.**

This must be stated because the natural implementation is wrong. If a case supplying its own prerequisite list overwrites the catalog defaults, then a case that adds "needs a monitor" to a drug silently loses "needs a line". The merge is a union, deduplicated by condition, and each merged prerequisite retains its origin so the debrief can say whether a block came from the case or the catalog.

Waiving is explicit, through a `prerequisite_overrides` entry naming what is waived and why. A crash airway in a patient already in arrest does not require sedation and paralysis; a case that needs that says so.

### 6.3 Follow-ups

An action may declare follow-up requirements, each with a condition determining whether it applies to this case, a deadline measured from the triggering action, a nurse prompt, and a debrief note.

Post-intubation analgesia and sedation are the canonical example. **They cannot be prerequisites of intubation, because they come after it.** A requirement that must be satisfied before an action is a prerequisite; one triggered by an action is a follow-up, enforced by prompting and surfaced as an omission. Conflating the two makes post-intubation medication unreachable.

**`satisfied_by` must list every catalog entry that discharges the obligation.** If sedation can be propofol or ketamine and the list names only propofol, a resident who chose ketamine is told they failed to sedate a paralysed patient.

### 6.4 Validator obligations

- Every prerequisite flag is settable by some reachable action
- No circular prerequisite chains
- Every prerequisite has a failure message
- Every follow-up has a deadline, a prompt, and a debrief note
- Every `satisfied_by` id exists in the catalog

---

## 7. The nurse

A persistent character at top center with four functions.

**7.1 Action narration.** After each state-changing action, a line describing what was done, generated from the catalog template with case-specific overrides. Do not narrate exams or interview questions; those are the resident's own actions and narrating them is noise.

**7.2 Result announcements.** "Labs are back." "ECG is up." Fired when a result becomes available.

**7.3 Blocked-action feedback.** The prerequisite failure message is delivered in the nurse's voice, which is more natural than a system error and matches how this happens in a real department.

**7.4 Critical action prompts.** Each critical action in a phase may carry a deadline and prompt text, optionally with a second more urgent prompt later. Prompts are guarded by the standard condition language so they never fire for something already done or no longer appropriate.

### 7.5 Prompts are a teaching affordance

A nurse who says "do you want to intubate?" has given the learner the answer. In an assessment tool that would be a problem to engineer around. Here it is the tool working: a real nurse does exactly this, and a learner who did not know what to do next has now learned it.

**Recommended handling:** a prompted action counts as done. It is flagged in the debrief so the learner can see where they needed help, but it is not penalized. Only genuine omissions cost anything.

| Outcome | Debrief treatment |
|---|---|
| Done before the prompt deadline | Credited, noted as independent |
| Done after a prompt | Credited, noted as prompted |
| Not done | Omission |

Reporting these separately gives the learner useful self-knowledge without turning the nurse into a trap. Whether prompted actions eventually carry reduced weight is a tuning choice, not a structural one.

**Two extensions worth considering later.** An explicit hint control, so a stuck learner can ask rather than wait, which is more honest than making them sit through a deadline. And difficulty modes, where a beginner setting prompts earlier and more specifically while an advanced setting prompts late or not at all. Both fit the existing prompt schema without structural change.

A cap on prompts per phase avoids nagging and should be configurable.

---

## 8. Results, monitor rendering and audio

**8.1 Turnaround** is set by class in the catalog: labs 5 seconds, imaging 10, ECG 10, bedside 0. Per-study overrides should exist but stay unused by default. All values are expected to change with tuning. See 2.3 on the bedside class.

**8.2 Pending display.** Ordered studies appear in Investigations as pending with a visible countdown. Pending is a real state and consultant rules may reference it.

**Do not print the turnaround value on the button.** It tells the resident the simulator's clock rather than anything clinical and invites ordering in an order that games the timer. Pending and resulted state carry the information a resident actually needs.

**8.3 The running chart.** Every output the case produces goes to a panel that is on screen at all times: results as they return, exam findings, consultant replies, what the patient said, and every action performed or blocked, in the order the resident learned them. A result enters the chart when it **results**, not when it was ordered, so the chart is a record of what was known and when.

**This removes the unread state, and with it a measurement.** An earlier design tracked whether each result had been read, warned at handoff about unread results, and reported them in the debrief. That was meaningful when a finding was visible only on the tab that produced it. With a chart that cannot be scrolled away from, a returned result has been shown to the resident whether or not they attended to it, and asserting otherwise would be a claim the interface cannot support. What remains measurable is a study that never came back, and that is still reported.

Two interface requirements, both learned by getting them wrong:

- **A study appears twice**, once when sent and once when it returns. Under the same name that reads as a duplicate, so the order entry is labelled as an order.
- **Auto-scroll only on change.** Following the newest entry every render pulls a reader scrolled back through earlier results to the bottom repeatedly. Scroll when the item count changes, not every tick.

**8.4 The dead monitor problem.** Vitals are static within a phase, so with a clock running the monitor will look frozen and broken. Add small cosmetic variance at the rendering layer only, on the order of a beat or two of heart rate and a point of saturation. This must live in the client renderer and never enter state, or it will corrupt result freezing and rule evaluation.

### 8.5 Audio

Two channels, both derived from the current phase's authored vitals and neither stored.

**Continuous heartbeat.** A two-thump beat at an interval of `60 / heart_rate` seconds, pitched by oxygen saturation:

```
frequency = BASE_HZ * 2 ^ (-(SPO2_REFERENCE - saturation) / SEMITONES_PER_PERCENT_DIVISOR)
```

The shipped configuration is A5 (880 Hz) at 100 percent saturation, one semitone lower per percent below. At 87 percent that is 13 semitones down, about 415 Hz.

**The reference point and the step size are configuration, and both are teaching decisions.** A real pulse oximeter's pitch drop is neither linear in semitones nor anchored at 100 percent. The shipped mapping is more dramatic than the bedside sound a resident will actually work with, which makes it a better alarm and a worse simulation. If transfer to real practice matters more than in-simulator salience, match the device convention instead. Whichever is chosen, the interface should state the mapping rather than hide it.

**Prompt tone.** A short two-note trill on nurse prompts and follow-up prompts, timbrally distinct from the heartbeat.

**This partly undercuts section 2.2 and the decision should be conscious.** Prompt text is forbidden from implying the patient is deteriorating. A distinct alert sound attached only to prompts teaches the resident that the tone means "you have missed something", which is the information the text is not allowed to carry. If that is unacceptable, sound every nurse utterance rather than prompts alone.

**Constraints.** Browsers will not start audio without a user gesture, so the context is created on the first interaction and the control reports actual state rather than intent. Muting must persist across subsequent interactions. Nothing in the interface may depend on sound alone; the monitor carries the same information visually and must continue to.

---

## 9. Completion and handoff

The case completes when the resident submits a handoff and confirms.

The handoff requires:
- **Level of care and disposition** from a case-supplied list including plausible alternatives
- **Working diagnosis** from the global diagnosis catalog, referenced by catalog id
- **Explicit confirmation**, with a warning if any study is still pending

**Diagnosis entry method.** Use a searchable global catalog rather than a short case-supplied list. Committing to a diagnosis from a wide field is the actual cognitive task being taught; picking from four options is a different and much easier task. This also avoids putting a language model in the critical path.

**Author must supply:** the correct disposition, the correct diagnosis as a catalog id, and for each plausible alternative a short explanation for the debrief. Incorrect selections are teaching opportunities and should be explained, not just marked wrong.

**A case cannot pre-explain every wrong answer.** With several hundred diagnoses in the catalog most selections will land outside the authored alternatives and receive a generic note. That is acceptable for the long tail and is not acceptable for the common misdiagnoses of the presentation, which is why the validator checks that each authored alternative resolves to a real catalog id.

**Abandonment.** A resident who cannot proceed needs an exit. Provide an end-case option that terminates the run and generates a debrief marked incomplete. Without it, sessions with no handoff never resolve.

---

## 10. Harmful actions and halting

A harmful action bypasses all transition rules and moves directly to a terminal halted phase carrying that action's halt reason.

On halt:
1. The case ends and the clock stops
2. The halt reason is displayed, stating what was done and the physiological consequence
3. **A full debrief is generated for the entire run**, including everything done correctly beforehand
4. A restart is offered

Termination and restart are separate decisions. **Restart should be offered, not forced.** Forcing an immediate restart discards the debrief the learner most needs to read at precisely the moment they are most receptive to it. Let them read, then replay.

Clinical tags are rule lists, not fixed values, so the same action can be harmful in one phase and appropriate in another. The tag is evaluated against current state at the moment of the action.

**A batch that contains a harmful action halts on it** and discards everything selected after it. Actions before it in the batch are applied normally. This is correct and will surprise learners who expected a submitted set to go through as a set. Warning before submission would leak the answer, so the behaviour stands.

**The halted phase has one vitals block for every halt reason.** A metoprolol arrest and a fluid-overload decompensation display identical numbers. This is a known limitation; see section 15.

---

## 11. Debrief

The debrief is the product. Design it explanation-first, score second.

### 11.1 Contents

**Order matters.** The harmful action, if there was one, comes first, then the critical actions. A resident reading top to bottom should meet the medicine before the scoreboard; a debrief that opens with a domain table invites them to read the score and stop.

1. **Harmful actions** and their consequence
2. **Critical actions**, those done and those missed together, each with its teaching note
3. **Recommended actions** that were done
4. **Summary**, the domain table and the score
5. **Discouraged actions**, meaning traps that were wrong but not lethal
6. **Blocked attempts**, framed as sequence teaching, naming whether the block was a case or catalog prerequisite
7. **Handoff accuracy**, with an explanation for an incorrect disposition or diagnosis
8. **Answered by a default**, listing every study, exam or consultant that returned the catalog normal because this case authors nothing for it
9. **Studies still pending** at completion
10. **Independent versus prompted**, as self-knowledge
11. **References** per teaching note, optional per author

**Item 8 matters more than it looks.** It is the only place a normal-by-omission becomes visible. A resident reading "your lipase and your orthopaedics consult were answered by a default" learns that the case had nothing to say about them, which is different from learning that they were normal.

**Teaching notes are collapsed by default**, each behind its own expander next to the action. The notes are the most valuable content in the debrief and also the longest; printed in full for every action they become a wall of text that gets skimmed, and the list of what was done and what was missed stops being readable at a glance. Use a native disclosure element rather than a scripted toggle, so the open state survives a re-render.

**Two sections were removed rather than kept.** A timeline of the run duplicated the running chart from 8.3, which is on screen throughout play and already ordered by time. A path map through the phase graph showed the case's internal structure, which is an authoring artifact: the resident did not choose phases, they chose actions, and the actions are already listed. Both were cheap to generate, which is not the same as being worth reading.

### 11.2 Scoring

Points exist to direct review, not to rank. Report by clinical domain, for example airway, circulation, diagnostics, disposition, so the learner knows what to study. A single percentage tells them nothing actionable.

| Dimension | Treatment |
|---|---|
| Critical actions | Credited whether prompted or not; omission costs |
| Harmful actions | Halt, with explanation |
| Discouraged actions | Minor cost, with explanation. Wrong but not lethal |
| Recommended actions | Minor credit; minor cost for omission |
| Follow-up requirements | Credit or omission |
| Blocked attempts | Surfaced as teaching, not penalized. The system already corrected the learner in the moment |
| Neutral actions | No effect |
| Handoff accuracy | Disposition and diagnosis scored separately |
| Studies never resulted | Flagged |
| Timeliness | Reported, weighted lightly until the cadence is calibrated |

**The `discouraged` tier is new in v0.4.** v0.3 offered critical, harmful, recommended and neutral. An action that is wrong but not lethal, such as morphine in acute pulmonary oedema, a bronchodilator for cardiac asthma, steroids or antibiotics without an indication, or an unindicated CT pulmonary angiogram, could only be tagged neutral and therefore carried no weight at all. Section 3.4 of the authoring document asks authors to identify traps as a category; without this tier there was nothing to tag them as.

### 11.3 Attempt history

Sessions are logs, so tracking improvement across repeat attempts of the same case is close to free and is educationally motivating. Worth building once the debrief itself is working.

---

## 12. Engine components

Case-agnostic. No clinical knowledge, no case names, no drug behavior. An `if` statement about a specific drug in engine code means that logic belongs in a case file.

| Component | Responsibility |
|---|---|
| **Scheduler** | Computes due times for pending results, prompts, and follow-ups; produces the client schedule |
| **Folder** | Replays log entries and derived time events chronologically; calls the resolver, prerequisite checker and transition checker during the walk |
| **Condition evaluator** | Evaluates the five predicates and their boolean combinations |
| **Resolver** | Walks a key's rule list, returns the first match |
| **Result resolver** | Case content, then catalog default, then error |
| **Transition checker** | Evaluates the current phase's transition rules after each state-changing action |
| **Prerequisite checker** | Merges catalog and case prerequisites, evaluates them, returns the failure message |
| **Debrief generator** | Folds the log against case data to produce narrative, teaching points, and score |

**The folder is not independent of the resolver and transition checker.** Phase changes come from transition rules, and results freeze at order-time state, both computed during the chronological walk. Implementing fold-then-resolve produces a system that appears correct while silently breaking result freezing, showing an early gas with the improved value. Build it as one ordered replay.

---

## 13. Tooling

### 13.1 Validator

**Structure.** Every content key ends in an unconditional default. Every referenced action, flag, study, and phase exists. Every phase is reachable and every non-terminal phase has a satisfiable transition. Every critical action is reachable. Every action whose tag can evaluate to harmful has a halt reason. Every prerequisite is satisfiable and non-circular, with a failure message. Every follow-up has a deadline, prompt, and note. Every critical action with a deadline has prompt text. No condition uses an unpermitted predicate.

**Payloads.** Every authored result is a structured payload, not a prose string. Every payload carries `abnormal` at both levels, and the payload level equals the OR of its components. Every component carries a label, value and reference range.

**Plausibility.** Vital sign values fall in physiologically possible ranges. This catches transcription slips such as a Fahrenheit value in a Celsius field, which no reference check will find.

**Abnormal flag cross-check.** Parse each reference interval and compare it against the value. The renderer must not recompute, but the validator can, and a mis-set flag is invisible everywhere else. Warn rather than error, since not every range is parseable.

**Catalog binding.** Every case action has a binding row. Unmatched rows error. Mapped targets exist in the catalog. A catalog entry bound by more than one case action warns. A harmful action whose catalog entry has unbound siblings in the same group warns.

**Catalog integrity.** Every catalog condition parses in the section 4 grammar. Every investigation and every exam carries a default result. The case authors no exam maneuver outside the closed set. The general status key exists.

**Silent normals.** A study named in a condition or tagged critical but with no authored result warns, naming the catalog default that will be served in its place.

**Handoff.** The correct diagnosis and every authored alternative resolve to a real diagnosis catalog id.

**Flag namespace.** Catalog-owned flags are shared and reserved; case-owned flags are prefixed and checked for collisions. A blanket rule forbidding all cross-case flag collisions is incompatible with catalog prerequisites, which must reference the same flag names everywhere.

### 13.2 Per-key review matrix

For each key, enumerate every combination of the flags, studies, and phases appearing in *that key's own rule list*, and show what it resolves to in each. Study predicates take three values (not ordered, pending, resulted), which widens the projection slightly but keeps it enumerable.

For lab, imaging and exam keys, render the resolved payload inline with abnormal components marked. A component that reads abnormal to the reviewing physician but is not marked is a display defect that no other check will catch.

Do not attempt to enumerate the full reachable state space. With fifteen interventions and twenty studies it runs to billions of states. Per-key projection is the tractable version and produces the artifact the physician actually reviews.

Per-key projection can generate combinations unreachable in the real case, for example two mutually exclusive interventions both set. Either filter these with a reachability pass or label them in the output.

### 13.3 Path simulator

A scripted replay of a dozen or so end-to-end routes through the case: the intended path, each harmful halt, each blocked prerequisite, the deterioration branch and its rescue, and any ordering the author considers likely.

Reachability is a weak claim. The validator says a phase *can* be reached; the simulator confirms that a plausible sequence of clinical actions actually gets there. It is also where ordering ambiguities such as cascading transitions (5.6) surface.

### 13.4 What the tooling cannot check

Two categories, both belonging on the human checklist:

**Anything requiring clinical knowledge.** Whether a value is right, whether a harmful action is genuinely harmful, whether a prompt implies deterioration.

**Anything about the interface rather than the file.** A study the interface never renders raises no error, because both the validator and the matrix read the case file. This has already happened: an ECG whose turnaround class was neither lab nor imaging was dropped from a menu that grouped by class, and it was the second most important study in the case. Build a case and play it before signing it off.

---

## 14. Open decisions

1. **Session time on abandonment.** Whether the clock continues if the browser closes, and whether a session can be paused or resumed.
2. **Timing under batching.** Whether timing feedback should measure from first selection or from submission. See 19.2.
3. **Bedside turnaround.** Zero seconds as shipped, or two to three to preserve the order-and-wait beat.
4. **Audio mapping.** Device-realistic against simulator-salient, and whether the prompt tone should apply to all nurse utterances.
5. **Prompt cap** per phase, and prompt specificity.
6. **Scoring weights** across the dimensions in section 11.2, including the new discouraged tier.
7. **Simulated clock display** for compressed time. Low priority.
8. **Difficulty modes** and an explicit hint control. Deferred, fits the existing schema.

---

## 15. Limitations carried forward

- **Flags are binary and permanent.** A single dose fixes something for the rest of the case. Cases cannot depend on redosing or titration, and partial response cannot be represented. Stopping an infusion sets its own flag rather than clearing the running flag, so a case can tell that a drip was started and then stopped, but not that it is currently running.
- **Permanent flags can shadow phase-correct content.** A patient who received non-invasive ventilation, then deteriorated, still carries the `on_niv` flag. A key keyed on that flag returns the improved value in the deteriorated phase. **Phase rules must precede flag rules in any list where both appear.** This is the most easily missed consequence of flag permanence and has already produced a wrong result in review.
- **Vitals are static within a phase.** The monitor steps at phase boundaries. Cosmetic variance disguises this but does not fix it.
- **The patient does not deteriorate.** Time affects information availability and prompting only. A resident who ignores every prompt reaches the same patient state as one who acts immediately, and sees the difference only in the debrief.
- **Order cannot be expressed in conditions,** beyond what prerequisites enforce.
- **Serial testing cannot be represented.** A repeat study in an unchanged state returns an identical value, so a rising troponin cannot be taught without gating on an unrelated flag, which would be dishonest. A predicate such as `study S ordered at least N times` would fix this and would stay enumerable in the review matrix.
- **Stopping an infusion is a separate action, not a toggle.** Every persistent infusion has a matching stop entry, so a rescue that depends on withdrawing a drip is now authorable, but the case must author the stop as its own step and gate the transition on the flag it sets. Restarting the same infusion afterwards is not represented.
- **One vitals block per terminal phase.** Every halt displays the same numbers regardless of the mechanism. Making vitals optional per halt reason would fix it.
- **Turnaround times are compressed** and teach a false tempo unless a simulated clock is displayed.
- **Interview matching is lexical.** See `case-authoring-requirements.md` section 10.6 for measured accuracy.

Each is a deliberate trade for version one. The rule structure migrates cleanly when continuous variables are added, because rule lists keep their shape and only the predicate set becomes richer.

---

## 16. Repository layout

The engine and the case content are separate trees, and nothing crosses between them.

```
engine/     case-agnostic code and tools. No clinical content, no case names.
catalog/    global action and diagnosis catalogs, and their generators.
cases/      one folder per case, each a case pack.
docs/       this document and the authoring requirements.
build/      generated prototypes.
```

**The test for whether something is in the right tree.** An `if` about a specific drug
in `engine/` belongs in a case file. Condition parsing or fold logic in `cases/` belongs
in the engine. Section 12 already required this of the runtime; this extends it to the
tooling, which had been accumulating case data without anyone noticing.

**Applying that test found a live defect.** The builder carried a fallback that resolved a
case's correct diagnosis by searching the catalog for "reduced ejection" or "hfref". It is
obviously case content in engine code, and it was also masking the fact that the case had
never named a real catalog id. Removing the fallback broke the handoff at once, which is
the correct behaviour and the reason section 9 now requires ids rather than labels.

The general lesson: a fallback that guesses on behalf of a case will hide the very defect
the fallback exists to work around, and it will hide it for as long as the guess happens
to be right.

### 16.1 One build, many cases

`engine/build_simulator.py` packs every case pack into a single `build/simulator.html`
that opens on a case picker. With one pack the picker is skipped, because choosing from
a list of one teaches nothing.

**The catalog merge happens at runtime, not at build time.** An earlier build emitted
each case's finished action table, which was 227 KB and 95 percent catalog data, so the
file grew by roughly 370 KB per case. The catalog is now emitted once and the engine
merges it with the case bindings on selection. Per-case cost falls to the size of the
case file. It is also the right home for the merge: section 6.2 describes catalog-default
and case-prerequisite merging as engine behaviour, and it had been living in the build.

**The picker names what is wrong with a case rather than hiding it.** A case whose build
produced notes, such as a diagnosis that does not resolve or an action with no placement,
is listed with those problems counted. A skeleton mid-authoring should be playable, and
the interface must survive null vitals rather than white-screening.

### 16.2 A case pack

A folder under `cases/` whose files share a prefix. Authored: the seed, the case file,
the binding map, the scenario list, the case assertions, the review packet. Generated:
the resolved binding and the review matrix.

Every tool takes a case pack as its argument and defaults to the only one present. None
of them needs editing to accept a new case:

```
python3 engine/new_case.py       PE "Acute pulmonary embolism"
python3 engine/bind_catalog.py   cases/PE
python3 engine/validate_case.py  cases/PE
python3 engine/build_simulator.py
python3 engine/sim_runner.py     cases/PE
node    engine/engine-tests.js   build/simulator.html cases/PE/PE-tests.js PE
```

### 16.3 The scaffold fails on purpose

`new_case.py` writes a skeleton whose clinical fields are placeholders, so the validator
rejects it. The error list is the authoring to-do list, and a skeleton that passed would
be a skeleton that taught nothing.

This puts a load on the validator that it did not previously carry: it now runs against
half-authored files, so every check must report rather than crash. Four crashes on null
values were found and fixed the first time a skeleton was passed through it. Anything
added to the validator later should be tested against a fresh skeleton, not only against
a finished case.

### 16.4 Splitting the test suite

Engine assertions and case assertions are different artifacts. `engine/engine-tests.js`
is a harness plus the checks that hold for any case; it discovers ids from the loaded
data rather than naming them. The case pack's `<PREFIX>-tests.js` holds everything that
names a drug, study or phase.

Some checks resist being made generic, and the honest resolution is to weaken the
generic version rather than fake it. "Every harmful action halts" cannot be tested
without knowing how to reach the state in which it is harmful. The generic suite checks
instead that every harmful tag is reachable from some authored phase and carries a halt
reason; walking there is a case assertion.

---

## 17. The splash screen

The case does not start on load. A splash screen sets the scene and the clock starts
when the resident presses Begin.

It shows, all from the case file:

- the care setting, as a header
- the working title and the chief complaint in the patient's words
- how the patient reached the department, and the handover
- the difficulty toggle
- the provenance warning, if the case carries one

**Care setting is authored per case, not per deployment.** It reads as a property of the
institution, but the correct disposition depends on it: a case written for a critical
access hospital with no cardiology on site has a different right answer. Default is a
quaternary Level 1 centre with everything available.

**The clock reads zero until Begin.** Reading the scene is not part of the resuscitation
and should not be timed.

### 17.1 Difficulty

Two modes, differing in one number:

| Mode | Prompt multiplier | Intent |
|---|---|---|
| Easy | 1 | The nurse prompts at the authored deadlines |
| Hard | 3 | The nurse waits three times as long, and often the case ends first |

The multiplier scales prompt deadlines, prompt escalations and follow-up prompt
deadlines. **It scales nothing else.** Result turnaround, phase transitions and clinical
tags are identical, so the medicine is the same in both modes and only the amount of
help changes. This is what makes the two modes comparable in the debrief.

Hard mode is the honest test of whether a resident would have acted unaided, which is
the question the prompted-versus-independent report in section 11.2 exists to answer and
could not previously answer well, because in easy mode the prompt usually arrives before
the resident has finished thinking.

The mode is displayed on the monitor throughout and named in the debrief, so a run is
never compared against one taken under different pacing.

---

## 18. The action surface

The tabs are defined by catalog `placements`, not by the engine. The current set:

| Tab | Contents | Behaviour |
|---|---|---|
| Patient | Handover, appearance, background | Read only |
| History | Free-text interview | Fires on submit |
| Exam | General status line, then the 14 maneuvers | Fires on click |
| Stabilization | Access, airway, oxygen, intubation, fluids, pacing | Order batch |
| Investigations | Bedside, labs, imaging | Order batch |
| Interventions | All medications, procedures, blood products | Order batch |
| Consults | All consultants | Fires on click |
| Handoff | Disposition, diagnosis, confirm | Terminal |

**Every catalog entry in a tab is rendered**, whether or not this case references it. An entry with no case content is inert, neutral, and returns the catalog default. A resident must choose from the real menu, not from a menu of the answers.

Each action tab carries a filter box with a clear control. Filters are held per tab so switching away and back preserves them.

**Tabs with many groups render collapsed.** Interventions, Investigations and Stabilization
all carry more entries than read as a flat list. Their group headers render closed, showing
the name, the entry count and the number selected, and open on click. Expanded state is held
per tab like the filter and the basket, and a selection made inside one group survives
collapsing it, so an order set can be assembled across several groups before submitting.
Typing a filter opens every group that still has hits, because a filter the resident cannot
see the results of is worse than no filter.

**Exams and Consults stay flat.** Both are a single group of fourteen and seventeen entries,
where an accordion would add a click and hide nothing. Collapsing is worth it when the tab has
several groups and a long list; it is a cost when it has one.

This is presentation only. It changes nothing about what is orderable, what any action does,
or what the engine sees. Which tabs collapse is configuration.

**Case actions with no catalog entry** should not exist. Where they do, during migration, render them in a separately labelled group so the case remains playable while the gap stays visible, and error in the validator.

---

## 19. Order batching

On the Stabilization, Investigations and Interventions tabs, clicking an action selects it rather than performing it. Nothing enters the log until Submit Order. Selections are held per tab and survive switching tabs, so an order set can be assembled across tabs and submitted in pieces.

Exams and consults are excluded. They are reads, not orders, and batching a read would only add a step.

### 19.1 What it does not change

Submitting writes one log entry per action at the same timestamp in selection order. Section 5.3 governs the rest: the fold applies them in sequence and every mechanism behaves as it would one at a time.

### 19.2 What it does change

**Timing.** Prompt deadlines run from phase entry and are unaffected, but the log now records the moment of submission rather than the moment of decision. A resident can sit past a deadline while composing an order set, receive the prompt, and then submit something they had already selected, and be scored as prompted.

If that matters, time from first selection in the batch. This is open decision 2.

**Realism, in both directions.** Clicking an action and having it happen instantly is not how ordering works; assembling a set and submitting it is. But a resuscitation case often wants to teach that hesitation costs something, and batching hides hesitation.

### 19.3 Interface requirements

Two defects that any implementation will hit, stated as requirements rather than left to each build:

- **Selecting must not move anything.** If the pending-order bar or a Clear control appears on the first selection, the grid shifts under the cursor and the next click lands on the wrong item. Render the bar and the controls unconditionally, disabled when empty.
- **The selected marker must not change the button's height**, for the same reason. Use an absolutely positioned marker rather than a label in flow.
