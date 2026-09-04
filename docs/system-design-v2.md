# EM Case Simulator: System Design

**Version 0.8 | Supersedes v0.7**

---

## 0. What changed

**v0.8 finishes what v0.7 started, and the reason is that v0.7 was half a mechanism.** An effect with a `duration_seconds` changed a number on a screen and nothing else. Nothing in the case could react to a drug wearing off, because the condition language could not see it, so "it stopped working" was a rendering event rather than a clinical one and a case whose lesson is a closing window was still unauthorable.

A case action may now grant a flag that **lapses**: `flags_set_timed`. When it lapses the fold removes it and re-checks transitions, so a case can author "when the drug is no longer acting, and nothing else was done, deteriorate" and have it fire with the resident sitting still. Everything in the condition language reads it, which is the point: one mechanism, and tags, prompts, prerequisites, transitions, consultant tiers and content keys all see it for free. Section 2.7.

Vital effects also gained `onset_seconds`, so a drug can take time to work rather than only time to stop. Section 2.6. And section 2.8 is the part an author actually needs: four mechanisms now touch time or parameters, and choosing the wrong one is the failure mode, so they are set out side by side with the question that separates them.

The splash screen shows the arrival vitals (section 17), which is a handover artifact and not the monitor.

**v0.7 separates what the patient is from what the resident can see, and what a phase is from what an action does.** Two changes, and they are related: both take something the interface had been asserting for free and make it something the resident has to earn.

The monitor is no longer on when the case opens. Vitals and the heartbeat appear only once an action carrying the catalog's new `reveals_vitals` capability has been taken, which in the shipped catalog is `attach_monitor` and nothing else. Until then every cell reads as a dash and the room is silent. The numbers exist in the fold from the first second and every rule that reads them is unaffected; what is gated is the display.

An action may now carry `vital_effects`, which move one authored vital off the phase baseline for as long as the effect is acting. A phase is a clinical state entered once, so it cannot express "for the next thirty seconds", cannot express an effect that ends when a drip is stopped, and cannot distinguish a drug that changes the number from a drug that changes the patient without changing the number. Section 2.6.

Neither mechanism enters the condition language. Section 4's exclusion of time now covers vitals as well, for the same reason and with the same consequence: the per-key review matrix is unchanged in shape, because the matrix enumerates what a key resolves to in a phase and neither the clock nor a vital is a key.

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

**v0.5 changes what the resident is given at the start, and how the interview is matched.** Four changes, all of which came out of watching the prototype run rather than out of the design.

| v0.4 | v0.5 |
|---|---|
| Splash screen shows how the patient arrived and the handover | Splash shows one line naming the room; the handover moved into the case |
| A Patient tab holding handover, appearance and background | No Patient tab. Seven tabs. A two-sentence arrival handover sits under the History tab |
| Arrival described in prose per case | `metadata.arrival` is structured: `mode` (`ems` or `triage`), `location`, `line` |
| Vitals step instantly at a phase boundary | Vitals ramp to the new phase over five seconds, at the rendering layer only |
| Interview matching is lexical only | Lexical matcher plus an optional in-browser embedding model, fused; the lexical matcher gains a clinical lexicon, typo repair and compound-question splitting |

Sections 8, 15, 17 and 18 change. The authoring consequences are in `case-authoring-requirements.md` v0.4, sections 3.2 and 10.6.

**v0.6 adds time-guarded phase transitions.** Through v0.5 the clock governed information and
prompting and nothing else, and section 2.1 stated flatly that there are no time-driven phase
transitions. That invariant is now relaxed in one specific, bounded way: a phase transition may
carry a deadline, so that a phase can be left because the resident did not act rather than because
they did.

| v0.5 | v0.6 |
|---|---|
| No time-driven phase transitions; an untreated patient never changes | A transition rule may carry `after_seconds`; the guard is re-evaluated on a tick and fires if it still holds |
| Time excluded from the condition language, and therefore from transitions | Time still excluded from the condition language. It lives in named fields on transition rules only |
| The transition checker runs after a state-changing action | It also runs on a tick, but only while the current phase has at least one time-guarded rule |
| A nurse prompt may never imply a trajectory | Unchanged inside a phase. A time-driven phase change carries an authored narration line, which is the one place a trajectory may be described |
| A case ends by handoff or by a harmful action | Or, with an explicit per-transition opt-in, by a time-driven transition into a terminal phase |
| Two review artifacts: the per-key matrix and the path simulator | A third: the deterioration timeline, which is the only artifact that shows what happens when the resident does nothing |

Sections 2, 4, 5, 7, 10, 11, 13, 14, 15 and 17 change. The authoring consequences are in
`case-authoring-requirements.md` v0.5, sections 0, 5, 9 and 14.

**Why this was worth breaking an invariant for.** The static-patient rule bought coherence cheaply
and it bought it by making a whole category of case unauthorable. Meningococcaemia, anaphylaxis,
status epilepticus, tension pneumothorax, a tricyclic overdose and an untreated STEMI all share a
teaching point that cannot be expressed as a consequence of an action, because the point is that
nothing was done. Before v0.6 the only way to author those was to substitute a proxy: make the
patient collapse on intubation, or on some other action the resident might not take. That
misattributes the harm.

**Why it is bounded the way it is.** The v0.5 argument for excluding time from the condition
language was that time-conditional content everywhere would make the per-key review matrix
unenumerable. That argument is correct and it survives intact, because time does not enter the
condition language here. It enters one named field on one kind of rule. Content keys, clinical
tags, prerequisites, follow-up applicability and interview answers still project over phase, flags
and study state exactly as before, and the per-key matrix is unchanged in shape. What changes is
how a phase is reached, and the matrix already enumerates over phases.

**The reason for removing the Patient tab.** It held a full structured background, and a resident who opened it first was handed most of the history without asking for it. The information is still authored, because the interview answers are built from it, but it is now reachable only by asking. What replaces it is a deliberately mediocre arrival handover, two sentences, of the quality a real EMS crew or triage nurse gives when they are busy: enough to start, not enough to diagnose.

**This is a trade, not a free improvement.** A resident who cannot think of the right question now gets nothing, where before they got a paragraph. That is the intended pressure, but it puts more weight on interview matching than v0.4 did, which is why the matcher work in the same version is not a coincidence. If matching fails, the case becomes unplayable rather than merely harder. Section 15 and authoring section 10.6 carry the measured accuracy.

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

4. **Time-guarded phase transitions**, new in v0.6 and described in 2.1a. A phase may be left
   because a deadline expired with the guard still true.

The clock still does **not** change the patient continuously. Vitals do not drift, there is no
interpolation with state behind it, and nothing moves between phase boundaries. What changed in
v0.6 is that a phase boundary can now be crossed by the clock as well as by an action.

The boundary that must still hold is narrower than it was, and it is this: **the patient's state is
always a phase, and a phase always has authored numbers.** Time selects which phase; it never
produces a value nobody wrote.

### 2.1a Time-guarded transitions

A transition rule may carry `after_seconds`. The rule then matches only when its guard is true
**and** the elapsed time since a reference moment is at least that many seconds. A rule without
`after_seconds` is instantaneous and behaves exactly as it did before v0.6, so every case written
against v0.5 runs unchanged.

```json
{
  "when": "NOT flag abx_given set",
  "after_seconds": 240,
  "measured_from": "phase_entry",
  "to": "progressive_sepsis",
  "narration": "The spots on her ankles have joined up while we've been standing here.",
  "debrief_note": "The organism was never treated and the septicaemia progressed.",
  "author_rationale": "Untreated meningococcal bacteraemia progresses over minutes to hours."
}
```

**Reference moment.** `measured_from` is `phase_entry` by default, matching prompt deadlines.
The alternative is `guard_true`, meaning the clock starts when the guard first became true, which
is what a delayed consequence of an action needs.

**Evaluation.** The transition checker runs after every state-changing action, and additionally on
a tick while the current phase has at least one time-guarded rule. Phases with no time-guarded
rules are never ticked, so a v0.5 case is bit-identical. Both evaluations run the full ordered list
with first-match-wins, so an instantaneous rule always outranks a time-guarded rule beneath it.

**Three patterns this supports**, and authors should be able to name which one they are using:

| Pattern | Guard | `measured_from` | Example |
|---|---|---|---|
| Deterioration on inaction | negative, `NOT flag F set` | `phase_entry` | Untreated sepsis progresses |
| Delayed consequence of an action | positive, `flag F set` | `guard_true` | Peri-intubation collapse forty-five seconds after induction rather than instantly |
| Scheduled natural history | `null` | `phase_entry` | A simple febrile seizure self-terminating; a thrombolysis window closing |

The third requires an `unguarded_rationale`, because a transition that fires regardless of what the
resident does is a scripted trajectory and should be a deliberate choice rather than an oversight.

**A negative guard can only be falsified, never re-satisfied**, because flags are permanent. So once
the resident gives the drug, that deterioration is cancelled for the remainder of the case, not
merely deferred. This is the property that makes the mechanism reviewable: each time-guarded rule is
a single question, "was this done in time", with a yes or no answer.

**Terminal destinations require an explicit opt-in.** A time-guarded transition into a terminal
phase ends the case without the resident having done anything, which is the strongest statement this
system can make. It requires `allow_time_to_terminal: true` and a rationale on the rule, and the
validator errors without both. It must not be the shared `halted` phase, which carries a harmful
action's halt reason; a case that ends this way authors its own terminal phase with its own
`timeout_reason`.

### 2.2 The coherence trap this creates

### 2.2 The coherence trap this creates

If the nurse says "his sats are dropping" while the monitor shows a static saturation, the case contradicts itself.

**Requirement, unchanged inside a phase:** nurse prompt text must describe the current state or
express concern about inaction. It must never imply a trajectory, because within a phase there is
no trajectory. Acceptable: "He's still working hard to breathe. Do you want to do anything about
the airway?" Not acceptable: "He's getting worse." No validator can catch this, so it belongs on
the physician review checklist.

**v0.6 adds one exception, and exactly one.** A time-guarded transition carries a `narration`
string which is spoken at the moment the phase changes. This is the only place in the system where
a nurse line may describe a change, and it is legitimate because a change has just happened and the
monitor is about to show it. The constraint on that line is the mirror of the constraint above: it
must be true of the numbers displayed immediately after it, not of numbers that have not moved. A
narration saying the pressure has fallen, on a transition whose destination has the same systolic
pressure, is the same contradiction pointing the other way.

**A prompt in a phase with a time-guarded exit may name the consequence.** "If we don't get an
antibiotic into her she is going to get worse" is now a true statement in such a phase, where before
it was false everywhere. It is still not licence to describe the numbers as moving.

**Audio inherits this constraint.** See section 8.5. A pitch that falls as saturation falls is legitimate, because saturation genuinely changed at a phase boundary. A pitch that drifts downward while the phase is unchanged would be the audible version of the same contradiction and must not be built.

### 2.3 Compressed time

The turnaround values are pacing devices, not clinical durations. Real turnaround is roughly 30 to 60 minutes for labs and 30 to 90 for cross-sectional imaging.

Optionally display a simulated clock that advances faster than real time, so a 5-second wait reads as roughly 35 minutes elapsed. This preserves the lesson that results take time and you must act before they arrive. Low priority; the underlying values are configurable and can be calibrated later.

**On the bedside class at 0 seconds.** A point-of-care scan returning in the same instant as the order removes the order-and-wait beat entirely, which is most of what the mechanic teaches. Two to three seconds preserves the beat without pretending a scan takes as long as a send-away lab. This is a tuning decision, not a structural one, but it should be made deliberately rather than by leaving the class at zero.

### 2.4 Implementation

**Server-authoritative, client-triggered.** No websockets, no background processes, no persistent simulation loop. This keeps hosting cheap enough that free global access stays viable.

Every server response includes the current view plus a **schedule**: future events with their due times. The client sets timers and issues a request when an item comes due. The server checks its own timestamps, applies every event actually due, and returns the updated view.

**Time-guarded transitions join the schedule.** On entering a phase, the server computes the due
time of every time-guarded rule in it and adds them, exactly as it does for prompt deadlines. There
is no new transport and no new loop: the deterioration is a scheduled event like any other, and the
existing 5-second heartbeat is what catches it in a throttled or suspended tab. A resident whose
laptop slept through a deadline finds the deterioration applied on the next request, which is the
right answer and follows from the server being authoritative.

The client timer is only a trigger. The server decides what is due. This matters because browsers throttle timers in background tabs; when the tab returns, the next request catches up every overdue event at once.

Add a heartbeat roughly every 5 seconds while a case is active, as a safety net against clock drift and suspended tabs.

### 2.5 Session time

Elapsed time runs from case start to handoff confirmation or halt. Behaviour on abandonment and pause is an open decision (section 14).

**Order batching interacts with this.** See section 17.2: with batching, the log records the moment of submission rather than the moment of decision, which changes what timing feedback measures.

---

### 2.6 Vital effects

A phase authors the patient's **baseline**. An action may move one number off that baseline for as long as it is acting. What the monitor reads, and what the heartbeat is derived from, is the sum.

```json
"vital_effects": [
  {"vital": "oxygen_saturation", "delta": 3, "key": "positive_pressure_spo2",
   "while": "NOT flag intubated set"},
  {"vital": "oxygen_saturation", "delta": 5, "duration_seconds": 30, "key": "nitrate_spo2"}
]
```

Three fields govern it and there is nothing else to the mechanism.

**`duration_seconds` and `onset_seconds`, both measured from the administration.** The active window is `[t + onset, t + duration)`. Absent a duration the effect lasts as long as its guard holds; absent an onset it starts at once. One origin for both is one rule rather than two, and the cost of that choice is that an author can write a duration that does not outlast its onset and get an effect that never acts, so the validator refuses it and prints the resulting window for every effect in the case.

Neither bound is an event: nothing is scheduled, the fold simply stops counting the effect once the clock has passed it, so an effect starts and expires correctly on replay from any starting point.

**`while`, an ordinary section 4 condition.** Evaluated against the state as it now stands, not as it stood when the action was taken. This is how an effect ends when the mask comes off or the drip is stopped, without the case having to author a second action whose only job is to undo the first.

**`key`, defaulting to the action id.** Effects sharing a key do not stack; the most recent administration wins. Repeating a drug therefore repeats its effect rather than doubling it, which is the behaviour every drug in the catalog actually has and no drug in the catalog would have by summation. Two routes to the same drug must be given the same explicit key, for the same reason a harmful tag has to cover every route to the same act (3.7a): a mechanism that a sibling entry escapes is not a mechanism.

**Terminal phases are exempt.** `halted` and `case_complete` author the numbers a reader is meant to be left looking at. An effect still running when the case ends would edit the ending, and the halt card would disagree with the debrief above it.

**Effects are display and audio only, exactly as the ramp is (8.4a).** They do not enter the condition language, do not affect transitions, and do not affect result freezing: a blood gas still reports the phase's authored numbers for the moment it was ordered. This is the same accepted inconsistency the ramp already carries, now reachable in one more way, and the reason is the same one: the alternative is a state layer whose vitals move continuously, which breaks freezing and makes every rule that reads a phase read a moving target instead.

**An effect is not a clinical event.** The number moves and nothing else happens. If the case must DO something when a drug starts or stops working, the effect is the wrong tool on its own: pair it with an expiring flag (2.7) and guard the effect on that flag, so the clock lives in one place and everything can read it.

**What this asks of an author is a rebasing, and it is the mistake to expect.** Once oxygenation is action-driven, a phase's authored saturation has to be the **unsupported** one, or the phase change and the effect both fire and the number is counted twice. In CHFE this meant dropping `stabilizing` and `improving` from 93 and 96 to the arrival value of 87, so that positive pressure supplies the only durable gain and diuresis supplies none. That is not a cosmetic edit: it changes what the case teaches by making the second learning objective mechanical rather than asserted. Validator rule V catches the arithmetic half of this and cannot catch the clinical half.

### 2.7 Expiring flags

A case action may grant a flag for a fixed time:

```json
"flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 30}]
```

When the clock passes the deadline the fold removes the flag and **re-checks transitions**, which is the entire reason the mechanism exists. Without that re-check a case could author "when the drug is no longer acting, deteriorate" and it would fire only if the resident happened to press something afterwards, which is a bug that looks like flakiness.

Three rules govern grants, and all three exist because a flag is shared state that more than one action can write.

**A permanent grant is absorbing.** Once any action has set a flag through the ordinary `flags_set`, no timed grant can take it away, in either order. A drip that is running is running; a bolus of the same drug does not schedule its removal.

**A timed grant extends rather than replaces.** A second dose moves the expiry to the later of its own deadline and any deadline already standing. The earlier expiry event still arrives, sees that a later grant stands, and does nothing. So redosing refreshes, and a resident who redoses two seconds before the deadline is not overtaken by it.

**A lapse is not an action.** It appears in no timeline, produces no nurse line of its own, and costs nothing in the debrief's scoring. It is a thing that stopped being true while the resident was doing something else. If the case wants the resident told, it authors the consequence as a transition, and a transition may carry narration.

**The trap, and it is checked.** A clinical tag may read an expiring flag, and tags are re-resolved on every action, so that part works. But the set of CRITICAL actions a phase expects is computed once, on entry to that phase. An action that becomes critical because a flag lapsed mid-phase will therefore never appear in the debrief's missed list, and nothing else would ever say so. The validator warns and tells the author to put the consequence on a transition instead.

**Why a flag rather than a new predicate.** A predicate such as `drug D acting` would have been narrower, would have needed its own grammar, its own review-matrix column and its own validator rules, and would have expressed exactly one thing. A flag that expires is the existing flag, the existing predicate and the existing matrix, with a deadline attached. Section 4 is unchanged, which is the test any addition here has to pass.

### 2.8 Choosing among the five

Four mechanisms now touch time or move a number, and the failure mode is not that one of them is broken, it is that an author reaches for the wrong one. The question that separates them is **what else in the case has to know**.

| Reach for | When | What can read it |
|---|---|---|
| A **phase** | The patient has genuinely changed clinical state | Everything. It is the axis the whole case projects over |
| **`after_seconds`** on a transition | The lesson is that something had to happen sooner | It changes the phase, so everything |
| **`flags_set_timed`** | Something is true for a while and then is not, and the case must react | Everything in the condition language |
| **`vital_effects`** | A number on the monitor moves and nothing else does | Nothing. Display and audio only |
| **`flags_set_repeat`** | The act has to be performed more than once before it works | Everything in the condition language |

Read down that last column and the choice usually makes itself. Two consequences worth stating outright:

**The two bottom rows are designed to be used together.** An expiring flag holds the clock and a vital effect guarded on it holds the number:

```json
"flags_set_timed": [{"flag": "nitrate_acting", "duration_seconds": 30}],
"vital_effects": [{"vital": "oxygen_saturation", "delta": 5,
                   "key": "nitrate_spo2", "while": "flag nitrate_acting set"}]
```

The saturation rises, the case can test whether the nitrate is still acting, and there is exactly one deadline. Authoring the same 30 seconds twice, once as a duration and once as a flag, is two deadlines that will drift the first time one of them is edited.

**A phase is not expensive and is often the right answer.** It is the only construct a reviewing physician can see in the per-key matrix, and it is the only one that can change a finding, a lab, a consultant's advice or what the patient says. If the patient is genuinely worse, that is a phase, not a negative delta on a heart rate.

### 2.9 What none of them can do

Stated plainly, because each of these looks authorable until it is tried.

- **Nothing depends on dose.** Doses are not implemented anywhere in the product; `{dose}` is dropped from narration rather than faked. Two boluses are two administrations of the same thing.
- **Vitals cannot be tested.** No condition can ask whether the saturation is below 90. The condition language projects over phase, flags and study state, and that is what keeps the review matrix finite and reviewable. If a case needs to branch on a number, the number has to be a phase.
- **Effects do not reach results.** A blood gas reports the phase's authored payload for the moment it was ordered. A gas drawn while an effect is running will disagree with the monitor beside it, for up to the length of the effect. This is the inconsistency the five-second ramp already carried, and it is accepted for the same reason.
- **Effects do not compound or ramp.** They add, they clamp at physiological bounds, and they snap on and off. The renderer travels between values over five seconds, which is a display courtesy and not a model of anything.
- **Content keys cannot vary with time.** An exam finding, a lab, a consultant tier and a patient answer change with phase, flags and study state, never with the clock. A finding that must change after five minutes needs a phase, and a phase reached on a clock is exactly what 2.1a is for.

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
| `reveals_vitals` | v0.7. True on the act that puts numbers on the screen. See 8.4b |
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

### Time is deliberately excluded from this language, and stays excluded in v0.6

There is still no `elapsed > N` predicate. Timing lives only in explicit named fields: deadlines on
prompts and follow-ups, and, since v0.6, `after_seconds` on a phase transition rule.

The reason has not changed. If time entered the general condition language, authors would write
time-conditional content everywhere and the per-key review matrix would stop being enumerable. A
lab result that reads one way before four minutes and another way after cannot be reviewed by
reading a table, because the table would need a time axis with no natural granularity.

**Time-guarded transitions do not weaken this argument, and it is worth being precise about why.**
A content key resolves against phase, flags and study state. Adding a way to reach a phase does not
add a dimension to that projection: the matrix already enumerates over every phase, including the
ones only a clock can reach. The number of rows is unchanged. What is genuinely new is that a phase
can be entered with no action having been taken, which the matrix cannot show and which is why v0.6
adds a third review artifact rather than widening the second one. See 13.2a.

**The rule for a drafting AI is therefore unchanged.** A request for a time predicate in the
condition language is an architectural change and should be refused and escalated. A request for a
deterioration on a clock is now a supported feature, and should be authored as a time-guarded
transition rather than smuggled in as a condition.

---

## 5. State layer

### 5.1 The log is the source of truth

A session stores the case id, an ordered log, the start timestamp, and a status of active, halted, or complete. Nothing else is authoritative.

Each entry carries a sequence number, a timestamp relative to case start, the action id, and a type:

- **state-changing**: interventions, stabilizations, study orders, consults that unlock something, handoff
- **observational**: exams, interview questions, viewing a result, most consults
- **blocked**: an action attempted whose prerequisites were not met
- **time_transition**: a phase change caused by a time-guarded rule rather than by an action. It
  carries the rule's guard, its deadline and the phase it left, because the debrief has to be able
  to say which deadline expired and what would have prevented it

Blocked attempts are logged, because attempting intubation without sedation is a teaching moment that must reach the debrief.

**Prerequisites are evaluated during the fold, not before writing the log.** The log records what the resident attempted; the fold decides whether it succeeded. This keeps replay honest: a log replayed against a corrected case file produces the corrected outcome rather than a stale one.

### 5.2 Derived state

```
state = fold(log, case_file, catalog, current_time)
```

The fold produces: current phase, flag set, ordered studies, resulted studies, frozen result values, pending results with due times, halt status, the set of actions that were critical in any phase entered, and the set of keys answered by a default rather than by the case.

### 5.3 Replay must interleave actions and time events

This is the most likely place to introduce a defect.

Derived time events, meaning result arrivals, prompt deadlines, follow-up deadlines and, since
v0.6, time-guarded transition deadlines, are computed from log entries plus case data. The fold
merges log entries and derived events into one chronological sequence and processes them in
timestamp order.

**Time-guarded transitions make this materially harder and the ordering rule matters more than it
did.** A deterioration due at t=240 and a drug given at t=240 produce opposite outcomes depending
on which is processed first. The existing tiebreak already answers it: at identical timestamps, log
entries before derived events. The resident who gets the drug in on the deadline is credited with
having got it in. That is the right way round for a teaching tool, and it should be stated rather
than left to be discovered.

**A deterioration also invalidates the schedule that follows it.** On a time-driven phase change,
outstanding prompt and time-transition deadlines for the old phase are dropped and the new phase's
are computed from the moment of entry, exactly as for an action-driven change.

Order a lab at t=2, give a drug at t=5, lab results at t=7. The replay must process all three in that order. Processing all actions first and then all time events produces wrong state.

**Tiebreak:** at identical timestamps, process log entries before derived events, then by sequence number. Determinism requires an explicit rule.

**Batched orders arrive at one timestamp** (section 19). They are separate log entries in selection order, so the tiebreak applies and they are processed in sequence. Prerequisites, transitions and harmful tags evaluate exactly as they would one at a time.

### 5.4 Result freezing

A result resolves against the state at the moment it was **ordered**, not when it arrives. The specimen was drawn then and the image was acquired then. A chest film ordered before intubation does not show an endotracheal tube.

Store each result as its value plus the ordering state. Reordering creates a separate result with its own order and due times. If a case needs a result to reflect post-intervention state, the author must require a repeat order.

### 5.5 Nurse prompts are derived, not stored

A prompt for critical action A in phase P with deadline D is due at (phase P entry time) + D, and fires only if A was not completed before that moment.

This is fully derivable from the log, so nothing extra is stored and no read writes to state. The debrief determines prompted versus unprompted by comparing timestamps.

Deadlines are measured from phase entry. On a phase change, whether caused by an action or by the
clock, outstanding prompts for the previous phase are cancelled and new deadlines begin.

**This creates a defect a case can have and no reviewer will notice by reading.** A prompt at 260
seconds in a phase with a time-guarded exit at 240 can never fire. The validator checks for it (13.1)
because the failure is silent: the case looks complete, the prompt exists, and the learner is simply
never helped with that action. The same applies to an escalation deadline that lands past the exit.

**The set of expected actions is collected at the same moment.** On entering a phase, the fold records which actions resolve to `critical` against the state at entry. That set drives both prompt scheduling and the omissions section of the debrief, so the two cannot drift apart.

### 5.6 Cascading transitions

After a state-changing action the transition checker evaluates the current phase's rules once. If the destination phase's own rules are already satisfied on arrival, they do **not** fire until the next evaluation.

**In v0.6 the next evaluation is not necessarily the next action.** In a phase carrying at least one
time-guarded rule the checker also runs on a tick, so an already-satisfied instantaneous rule fires
within one tick rather than waiting for the resident. This is a behaviour change and it is confined
to phases that have a time-guarded rule, which means no case written before v0.6 is affected. Inside
such a phase the cascade resolves promptly, which is the more coherent behaviour: a patient should
not sit in a phase whose exit condition is already met while a deterioration clock runs against her.

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

**8.3 The running chart.** Every output the case produces goes to a panel that is on screen at all times: results as they return, exam findings, consultant replies, what the patient said, what the nurse asked for, and every action performed or blocked. A result enters the chart when it **results**, not when it was ordered, so the chart is a record of what was known and when.

**Newest first** (v0.8). The chart is read while the case is running, to answer "what just happened", and the answer to that is at one end of the list. Oldest-first put it at the far end of a scroller that grows all case, and in the expanded multi-column layout it put the newest entry at the bottom of the LAST column, which is the hardest place on the panel to find. Reversed, what a resident is looking for is at the top of the first column and the expanded panel needs no scrolling to answer that question at all. Ties are broken so that several things landing in the same second still read newest-first rather than in an arbitrary order.

**The nurse is in the chart, but not everything she says** (v0.8). Her line is the only thing in the interface that is overwritten rather than added to: the header holds one utterance and the next replaces it, so a resident working in a tab loses every prompt they were not looking at. That was the one kind of information in the product with nowhere to be read back.

Four of her six utterance kinds stay out, each for its own reason, and the reasoning is the 8.3 duplicate rule applied consistently rather than a preference. `narration` echoes an action that is already a row. `result` echoes a result that is already a row, with its payload. `blocked` is folded into the blocked row, which now carries the prerequisite message as its body rather than only the words "Blocked: X"; the reason is the teaching, and it used to live only in a header line that scrolls away. `halt` is said at the instant the case ends, which is the instant the panel is hidden, so it would be written somewhere nobody can look; its reason is on the halt card and in the debrief.

What is left is the two that have no other home: a **prompt**, which appears nowhere else at all, and a **deterioration narration**, which is the one place a nurse line may describe a trajectory (2.2) and is narrating a change the resident may not have been watching for. The two are styled apart, because being asked for something and being told the patient is worse are not the same utterance and the second should not be skimmed past as if it were.

**This removes the unread state, and with it a measurement.** An earlier design tracked whether each result had been read, warned at handoff about unread results, and reported them in the debrief. That was meaningful when a finding was visible only on the tab that produced it. With a chart that cannot be scrolled away from, a returned result has been shown to the resident whether or not they attended to it, and asserting otherwise would be a claim the interface cannot support. What remains measurable is a study that never came back, and that is still reported.

Two interface requirements, both learned by getting them wrong:

- **A study appears twice**, once when sent and once when it returns. Under the same name that reads as a duplicate, so the order entry is labelled as an order.
- **Auto-scroll only on change.** Following the newest entry every render pulls a reader who has scrolled away through earlier results back repeatedly. Scroll when the item count changes, not every tick. With newest-first that means scrolling to zero rather than to the full height.
- **A question the patient did not understand is not a chart entry.** v0.7. When the matcher finds no topic, the case's `out_of_scope_fallback` answers and the patient says they do not follow. That is feedback about the phrasing, not something learned about the patient, and a chart of "I don't know what you mean" three times over buries the history that was actually taken. The exchange stays on the History tab, where the resident can see which of their questions did not land and rephrase, and it does not enter the chart. The readout records the matched topic and is `null` exactly when the fallback answered, so this is one test and not a string comparison against the fallback text.

**8.4 The dead monitor problem.** Vitals are static within a phase, so with a clock running the monitor will look frozen and broken. Add small cosmetic variance at the rendering layer only, on the order of a beat or two of heart rate and a point of saturation. This must live in the client renderer and never enter state, or it will corrupt result freezing and rule evaluation.

**8.4a The phase-boundary ramp.** A phase transition replaces every vital at once, and an instantaneous jump from 128 to 96 reads as a rendering fault rather than as a patient responding. The renderer interpolates from the previous phase's displayed numbers to the new phase's authored numbers over **five seconds**, using a smoothstep curve so the movement eases in and out rather than sliding linearly.

Six values ramp: heart rate, systolic and diastolic pressure, saturation, respiratory rate, temperature. Everything else switches at the boundary.

**The same constraint as the cosmetic variance applies, and it is the one that matters here.** The ramp is a display value. It is computed on each render from the phase's authored vitals and never written to state, never folded, and never read by a condition. `study S resulted` freezing (5.4) captures the authored numbers, not the ramped ones, so a saturation captured during a ramp is the phase's value and not an intermediate. A resident who orders a blood gas one second into a ramp gets the phase's authored gas, and the monitor beside it will disagree with that gas for four more seconds. That is a real inconsistency and it is accepted deliberately: the alternative is either ramping the state, which breaks freezing and rule evaluation, or holding results until the ramp ends, which makes the clock lie.

**Audio follows the ramp.** The heartbeat interval and pitch are derived from the ramped values, because a beat that jumps while the number slides is worse than either alone.

**Five seconds is a guess.** It was chosen to be long enough to read as movement and short enough not to delay the resident. It has not been tested against residents and should be treated as configuration, not as a finding.

**8.4b No monitor, no numbers.** The simulator opens with every vital cell reading a dash and with no heartbeat. Both appear the moment an action carrying `reveals_vitals` is taken, which in the shipped catalog is `attach_monitor` alone.

This is display gating and only display gating. `st.vitals` is computed by the fold from the first second whether or not anyone is watching, every transition and every result behaves identically, and a case cannot switch the gate off or move it to another action: the capability is a catalog field, so no case names it.

**Why it is worth the friction.** Attaching a monitor was previously a recommended action that changed nothing a resident could perceive, which is the definition of an action a learner is entitled to skip. The numbers were on screen before anyone had done anything to obtain them, which taught that vitals are a property of arriving in a room. They are a property of putting equipment on a patient, and a resident who has not done it should be looking at a patient rather than at a monitor.

**Two things this deliberately does not do.** It does not distinguish "no monitor" from "unauthored vitals": both read as a dash, because the dash is already the interface's word for "no number here" and a reader is not helped by two kinds of nothing. And it does not silence the nurse's prompt trill, which is a person speaking rather than equipment and fires from the first prompt whether or not anything is attached. The sound control says which of the two is missing rather than reading "Sound on" over silence.

**The debrief is not gated.** A resident who never attached a monitor still sees, in the debrief, everything the case recorded. Withholding the debrief would punish the omission twice and would remove the only place the omission can be explained.

### 8.5 Audio

Three channels. The heartbeat and the nurse's tones are derived from the current phase's authored vitals with any active vital effect applied (2.6), and neither is stored. The heartbeat is additionally gated on the monitor (8.4b); the nurse's tones are not, because she is a person rather than equipment. The third is the room, and it is gated on neither.

**Continuous heartbeat.** A two-thump beat at a mean interval of `60 / heart_rate` seconds, pitched by oxygen saturation:

```
frequency = BASE_HZ * 2 ^ (-(SPO2_REFERENCE - saturation) / SEMITONES_PER_PERCENT_DIVISOR)
```

The shipped configuration is A5 (880 Hz) at 100 percent saturation, one semitone lower per percent below. At 87 percent that is 13 semitones down, about 415 Hz.

**The reference point and the step size are configuration, and both are teaching decisions.** A real pulse oximeter's pitch drop is neither linear in semitones nor anchored at 100 percent. The shipped mapping is more dramatic than the bedside sound a resident will actually work with, which makes it a better alarm and a worse simulation. If transfer to real practice matters more than in-simulator salience, match the device convention instead. Whichever is chosen, the interface should state the mapping rather than hide it.

**The beat is a self-rescheduling chain, not a fixed interval.** Each beat reads the current rate, saturation and rhythm when it schedules its successor. That is what lets the tempo follow the five-second ramp continuously instead of being restarted whenever a quantised rate crosses a step, and it is what makes an uneven rhythm expressible at all. Exactly one beat is ever pending; the render loop starts the chain and stops it and does nothing else.

**Rhythm.** A phase may declare `rhythm`, from a closed vocabulary held in `SHARED.audio.rhythm`. `regular` is the default and is bit-identical to the behaviour before this existed. `irregularly_irregular` draws each interval independently as a shifted exponential:

```
interval = mean * (s + (1 - s) * Exp(1))
```

A fraction `s` of the mean is refractory and the remainder is exponentially distributed, which is right-skewed and therefore produces the occasional long pause that makes such a rhythm recognisable. Two properties are enforced and asserted:

- **The mean is preserved exactly.** `E[Exp(1)] = 1`, so the expected interval is the authored one. The rate on the monitor and the average rate in the ear are the same number.
- **The spread narrows as the rate rises.** `s` is raised wherever a fixed refractory floor would otherwise be breached, rather than clamping the draw, which would push a third of the beats at 220 bpm onto the floor and move the mean off the authored rate. The coefficient of variation is `1 - s`. The floor also guarantees that one beat's second sound can never land on the next beat's first.

An uneven rhythm additionally varies the loudness of each beat with the length of the interval preceding it, because a long diastole fills the ventricle more. Without it the ear hears mistimed identical beats rather than a heart.

**Every one of those parameters is a teaching choice and none is measured.** They live in `SHARED.audio.rhythm` with a provenance note saying so. The engine holds no association between a rhythm and a diagnosis, exactly as it holds no appropriateness judgement about a drug.

**The ECG trace follows the same field.** The trace is decorative and its path does not encode rate, but a monitor drawing evenly spaced complexes with P waves beside an audibly uneven beat is a contradiction on one screen. Under an irregular rhythm the six complexes are unevenly spaced, deterministically per rate so the picture does not shimmer, and the P wave is omitted. It remains decorative: the beats on screen are not the beats being heard.

**Prompt tone.** A short two-note trill on nurse prompts and follow-up prompts, timbrally distinct from the heartbeat.

**Utterance cue.** Every other nurse line makes a shorter, softer sound: an action narrating, a result landing, a blocked attempt, a `nurse_alert`. A line nobody was looking at is a line nobody read, and the nurse's banner is not where a resident's eyes are. The design constraint is that it fires far more often than the trill and therefore must not be noticeable enough to irritate: it is brief, about half the trill's amplitude, and repeats inside 250 ms are dropped, because a submitted basket narrates several lines at one instant and a burst of clicks reads as a fault. **The two are exclusive.** A prompt trills and does not cue, because two sounds on one line would be worse than either.

**Levels are relative and are set by ear.** The three sounds share one gain block in the audio module and are exposed on the module for inspection, because the balance between them is a decision and a decision nothing can check is a decision that drifts. Peak gain is not perceived loudness and the figures should not be read as a ranking: the beat is a long low thump with a falling pitch, the cue two very short components an octave up, the trill two sustained tones higher still. What the figures are good for is the invariants the suite asserts, which are that the second heart sound stays under the first, that a cue cannot be masked by a beat landing at the same instant, and that nothing dominates. **The heartbeat is the one that has to be right**, because it is the only sound that never stops: pitched to be noticeable on the first beat, it is unbearable by the two hundredth.

**This partly undercuts section 2.2 and the decision should be conscious.** Prompt text is forbidden from implying the patient is deteriorating. A distinct alert sound attached only to prompts teaches the resident that the tone means "you have missed something", which is the information the text is not allowed to carry. If that is unacceptable, sound every nurse utterance rather than prompts alone.

**Ward ambience.** A 45-second loop under everything at a very low level, running from the moment a case begins until the moment it ends and silent everywhere else, which means the welcome screen, the splash of a case that has been chosen and not started, and the debrief. The interface declares which of the two situations it is in; nothing about the room is inferred from the patient, the monitor or the clock.

**The debrief being silent is the part worth stating as a rule.** A debrief is reading rather than resuscitating, and continuing to play a room under a learner reading about what they missed is the interface failing to notice the case is over. The same applies to a case that has ended in a halt.

**It changes 8.4b, and the change is an improvement.** The room is no longer silent before a monitor is attached: what is missing then is the monitor's sound, which is the whole of the point being made, and a ward that fell silent until somebody attached a monitor was the less truthful half of it. Nothing else about 8.4b moves.

**The asset is derived, normalised and optional.** It is peak-normalised at build time so the gain figure means something against a known reference rather than against whatever a particular recording happened to be; it is crossfaded so it repeats without a seam; it is decoded once from base64 in the page and looped as a buffer with loop points set inside the encoder padding. Every failure path ends in a silent room rather than an error, and a build made without the asset is a working simulator that is smaller. **No case should depend on it**, which is the same rule as nothing depending on sound at all.

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

## 10. Harmful actions, halting, and ending on the clock

A harmful action bypasses all transition rules and moves directly to a terminal halted phase carrying that action's halt reason.

**A time-driven ending is a different thing and must look different.** Since v0.6 a case can also
end because a time-guarded transition reached a terminal phase. The two are not interchangeable and
should never share a phase:

| | Harmful halt | Time-driven ending |
|---|---|---|
| Cause | Something the resident did | Something the resident did not do |
| Phase | The shared `halted` phase | A phase the case authors, with its own vitals |
| Text shown | The action's `halt_reason` | The phase's `timeout_reason` |
| Authored per | Action | Transition |
| Opt-in required | No | Yes: `allow_time_to_terminal` plus a rationale |

Attributing an omission to a commission is the specific error this separation prevents. A resident
who is told "you gave metoprolol and she arrested" when in fact she arrested because nothing was
given has been taught something false about their own run.

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
1a. **Deteriorations that happened on the clock**, if any: which deadline expired, in which phase,
    what the guard was, and which action would have prevented it, with the transition's own
    teaching note. This sits with the harmful actions rather than with the omissions because it is
    the strongest thing that happened in the run, and a resident who arrested a patient by doing
    nothing needs to meet that before the scoreboard
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

**Item 1a is the reason the log needs a `time_transition` entry type.** Without it the debrief can
say the patient ended up in a bad phase but not why, and "you missed the antibiotic" and "she
deteriorated at four minutes because the antibiotic had not been given" are different sentences with
different teaching in them.

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
| **Interview matcher** | Maps a typed question to an authored topic, or to nothing; lexical, with an optional embedding stage fused on top |
| **Vital effect resolver** | v0.7. Reduces the recorded administrations to the effects acting now, one per key, and adds them to the phase baseline. Nothing schedules an expiry; the resolver is a function of the clock |
| **Flag grant ledger** | v0.8. Records, per flag, whether an action has granted it permanently and the latest deadline any timed grant runs to. A lapse is a scheduled event that removes the flag and re-checks transitions, so a case can react to something wearing off |

**The folder is not independent of the resolver and transition checker.** Phase changes come from transition rules, and results freeze at order-time state, both computed during the chronological walk. Implementing fold-then-resolve produces a system that appears correct while silently breaking result freezing, showing an early gas with the improved value. Build it as one ordered replay.

---

## 13. Tooling

### 13.1 Validator

**Structure.** Every content key ends in an unconditional default. Every referenced action, flag, study, and phase exists. Every phase is reachable and every non-terminal phase has a satisfiable transition. Reachability traverses time-guarded edges as well as action-driven ones, since a phase reachable only by the clock is still reachable. Every critical action is reachable. Every action whose tag can evaluate to harmful has a halt reason. Every prerequisite is satisfiable and non-circular, with a failure message. Every follow-up has a deadline, prompt, and note. Every critical action with a deadline has prompt text. No condition uses an unpermitted predicate.

**Time-guarded transitions.** `after_seconds` is an integer at or above the floor, currently 30,
with a warning below 60. `measured_from` is `phase_entry` or `guard_true`, and `guard_true` requires
a guard. An unguarded time transition requires an `unguarded_rationale`. Every time-guarded rule
carries a narration, a debrief note and an author rationale. Every flag named in a guard is settable
by some reachable action. A terminal destination requires `allow_time_to_terminal` and a rationale.
A non-terminal destination must itself have an exit. No cycle may be composed only of time edges,
since it would loop with no resident involvement.

**The fairness check.** For every flag a guard requires to be unset, some action that sets that flag
must prompt in that phase, at a deadline at least 20 seconds before the transition fires. A
deterioration the resident was never warned about is a trap rather than a lesson, and this is the
one check that enforces section 1's framing mechanically rather than leaving it to review. The
converse is also checked: a prompt or escalation whose deadline lands at or after the phase's
earliest time-guarded exit can never fire, and warns.

**Payloads.** Every authored result is a structured payload, not a prose string. Every payload carries `abnormal` at both levels, and the payload level equals the OR of its components. Every component carries a label, value and reference range.

**Plausibility.** Vital sign values fall in physiologically possible ranges. This catches transcription slips such as a Fahrenheit value in a Celsius field, which no reference check will find.

**Abnormal flag cross-check.** Parse each reference interval and compare it against the value. The renderer must not recompute, but the validator can, and a mis-set flag is invisible everywhere else. Warn rather than error, since not every range is parseable.

**Catalog binding.** Every case action has a binding row. Unmatched rows error. Mapped targets exist in the catalog. A catalog entry bound by more than one case action warns. A harmful action whose catalog entry has unbound siblings in the same group warns.

**Catalog integrity.** Every catalog condition parses in the section 4 grammar. Every investigation and every exam carries a default result. The case authors no exam maneuver outside the closed set. The general status key exists.

**Silent normals.** A study named in a condition or tagged critical but with no authored result warns, naming the catalog default that will be served in its place.

**Handoff.** The correct diagnosis and every authored alternative resolve to a real diagnosis catalog id.

**Flag namespace.** Catalog-owned flags are shared and reserved; case-owned flags are prefixed and checked for collisions. A blanket rule forbidding all cross-case flag collisions is incompatible with catalog prerequisites, which must reference the same flag names everywhere.

**Vital effects (rule V, v0.7).** The vital named is one of the six authored per phase. The delta is a number, and a zero delta warns rather than errors, since it is more often a half-finished edit than a deliberate no-op. A duration is positive. A `while` condition parses. Two effects sharing a key must name the same vital, or one of them is silently discarded. An effect on an action the case marks `state_changing: false` errors, because the fold returns before it would record one.

**The rebasing check is a warning and is only made for unguarded effects.** If a phase's baseline plus the delta leaves the plausible range, the phase was almost certainly never rebased when the effect was added. A guarded effect is skipped and reported as a note saying the check was not made, because deciding whether a guard makes a phase unreachable is deciding reachability, which this validator does not attempt anywhere else. CHFE's nitrate effect is guarded on `NOT flag intubated set` and cannot reach either ventilator phase; warning about it would have been wrong on the first case that used the feature, and a rule that cries wolf on its first outing is a rule nobody reads afterwards.

**Expiring flags (rule W, v0.8).** The flag is a bare identifier, since the condition grammar splits on whitespace and could not name anything else. The duration is positive. The same action does not also grant the flag permanently, which would absorb the timed grant and make the duration dead. The action is state-changing, or the flag is never granted at all. **Something in the case reads the flag**: a flag that expires and that no transition, tag, prompt guard, prerequisite or content rule tests changes nothing, and that is the most likely way this mechanism is mis-authored. A flag granted with a duration by one action and permanently by another warns, because taking the second one silently stops the first from ever expiring. And a clinical tag that reads an expiring flag warns, for the reason in 2.7: the expectation set is fixed at phase entry and will not follow the tag.

**What rule V cannot check.** Whether the delta is the right size, whether the duration matches the drug, and whether the rebased baseline is still the patient the case describes. None of that is decidable without clinical knowledge, and the per-key review matrix cannot show any of it either, because the matrix enumerates what a key resolves to in a phase and an effect is neither a key nor a phase. It is a human review item, listed in authoring 14.3.

### 13.1a Negative tests for the validator

`engine/validator-tests.py`. The validator is the only thing standing between a future case author and a mechanic that fails silently, and a rule that has never fired is a rule nobody has run. The harness loads a real case that passes cleanly, breaks it in one specific way, and asserts that the rule meant to catch it says so, then throws the mutated copy away. Nothing on disk is touched.

Half the checks are the inverse: a rule must NOT fire on correct authoring. That half is the one that matters over time. A validator that shouts at a legitimate case teaches authors to ignore it, after which it protects nothing, and the guarded-effect range check in rule V would have shipped doing exactly that if it had not been written down as a test.

It found a real defect on its first run, though not in the validator: the engine test harness captured its action map once, while `selectCase` rebuilds that map on every call and the suite binds every packed case in turn. Every read off the stale map happened to agree with the live one, so nothing failed and the staleness was invisible until a test tried to write to it.

### 13.2 Per-key review matrix

For each key, enumerate every combination of the flags, studies, and phases appearing in *that key's own rule list*, and show what it resolves to in each. Study predicates take three values (not ordered, pending, resulted), which widens the projection slightly but keeps it enumerable.

For lab, imaging and exam keys, render the resolved payload inline with abnormal components marked. A component that reads abnormal to the reviewing physician but is not marked is a display defect that no other check will catch.

Do not attempt to enumerate the full reachable state space. With fifteen interventions and twenty studies it runs to billions of states. Per-key projection is the tractable version and produces the artifact the physician actually reviews.

Per-key projection can generate combinations unreachable in the real case, for example two mutually exclusive interventions both set. Either filter these with a reachability pass or label them in the output.

### 13.2a Deterioration timeline

New in v0.6, and required for any case that uses a time-guarded transition.

The per-key matrix cannot show these. It enumerates what a key resolves to in a phase, not how the
phase was reached, and the whole point of a time-guarded transition is that it is reached by nobody
doing anything. So the tooling emits a third artifact with three parts:

1. **Every time-guarded exit, by phase**: the deadline, the guard, the destination, whether the
   destination is terminal, and the prompts that precede it with their deadlines. A physician reads
   this asking two questions: would this patient really deteriorate in that time if that treatment
   were withheld, and was the resident warned early enough to act.
2. **The do-nothing trajectory**: the sequence of phases and vitals a resident sees if they perform
   no state-changing action at all, with the elapsed clock at each hop. This is the path an author
   is least likely to have imagined and the one a frozen or overwhelmed learner will actually see.
3. **Every narration line**, collected together, because these are the only lines in the system
   permitted to describe a trajectory and they should be read as a set against the vitals they
   precede.

### 13.3 Path simulator

A scripted replay of a dozen or so end-to-end routes through the case: the intended path, each harmful halt, each blocked prerequisite, the deterioration branch and its rescue, and any ordering the author considers likely.

**A case with time-guarded transitions needs waits in its scripts,** and at least four more routes:
doing nothing at all from arrival to the end; treating each deficit alone and letting the clock take
the other; a rescue inside the last window; and a rescue one action too late. The fourth is the one
worth writing carefully, because the difference between it and the third is the entire lesson and it
is easy to author a window nobody can hit.

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
9. **Whether the clock pauses.** Time-guarded transitions make this consequential where it was
   cosmetic. A resident reading a long consultant response or composing a batch of orders is on the
   same clock as one who is stuck, and a deterioration that fires while they are reading is unfair in
   a way a prompt firing is not. Shipped behaviour is that the clock does not pause, on the grounds
   that one clock with one set of semantics is worth more than the fairness it costs, and that the
   30-second floor and the mandatory preceding prompt are the mitigations. Revisit with a real
   learner.
10. **A global `time_pressure_multiplier`.** Time-guarded deadlines are authored in seconds and are
    subject to the same expectation of global recalibration as prompt deadlines. A single multiplier
    applied to every time-guarded deadline, defaulting to 1, would let pacing be tuned across the
    library without editing cases. Not built.

---

## 15. Limitations carried forward

- **Flags are binary and permanent.** A single dose fixes something for the rest of the case. Cases cannot depend on redosing or titration, and partial response cannot be represented. Stopping an infusion sets its own flag rather than clearing the running flag, so a case can tell that a drip was started and then stopped, but not that it is currently running.
- **Permanent flags can shadow phase-correct content.** A patient who received non-invasive ventilation, then deteriorated, still carries the `on_niv` flag. A key keyed on that flag returns the improved value in the deteriorated phase. **Phase rules must precede flag rules in any list where both appear.** This is the most easily missed consequence of flag permanence and has already produced a wrong result in review.
- **Vitals are static within a phase.** The monitor holds one authored set per phase. Cosmetic variance and the five-second boundary ramp (8.4a) disguise this but do not fix it: between boundaries nothing moves, and the ramp is a rendering effect with no state behind it. A case cannot author a trajectory, only a sequence of plateaus. Time-guarded transitions let those plateaus be chained on a clock, which is a staircase rather than a slope; a case that needs a genuine gradient still needs more phases, and the section 3.3 ceiling of six clinical phases binds sooner than it used to.
- **The patient deteriorates only where a case authored it, and only in steps.** v0.6 removed the
  blanket rule that an untreated patient never changes, but what replaced it is a staircase, not a
  slope: a time-guarded transition moves the patient from one authored plateau to the next. A case
  that authors no time-guarded transitions behaves exactly as it did in v0.5, and a resident who
  ignores every prompt in such a case still reaches the same patient state as one who acts
  immediately. Most cases should stay that way. The mechanism is for the presentations whose
  teaching point is the passage of time, and using it where the point is something else buys
  unfairness for nothing.
- **Deterioration is all-or-nothing per rule.** A guard is true or false, so a treatment given at
  the deadline minus one second has the same effect as one given at the start. Partial credit for
  partial delay is not representable, and neither is a dose-response between how late you were and
  how sick she becomes. Authors wanting graded lateness need graded phases.
- **Order cannot be expressed in conditions,** beyond what prerequisites enforce.
- **Serial testing cannot be represented.** A repeat study in an unchanged state returns an identical value, so a rising troponin cannot be taught without gating on an unrelated flag, which would be dishonest. A predicate such as `study S ordered at least N times` would fix this and would stay enumerable in the review matrix.
- **Stopping an infusion is a separate action, not a toggle.** Every persistent infusion has a matching stop entry, so a rescue that depends on withdrawing a drip is now authorable, but the case must author the stop as its own step and gate the transition on the flag it sets. Restarting the same infusion afterwards is not represented.
- **One vitals block per terminal phase.** Every halt displays the same numbers regardless of the mechanism. Making vitals optional per halt reason would fix it.
- **Turnaround times are compressed** and teach a false tempo unless a simulated clock is displayed.
- **Interview matching is bounded by what the case anticipated.** The shipped matcher is an IDF-weighted lexical matcher, extended in v0.5 with a clinical abbreviation lexicon, single-edit typo repair against the case's own vocabulary, and compound-question splitting. An optional embedding model (all-MiniLM-L6-v2, roughly 23 MB, loaded from a CDN and cached in IndexedDB) fuses with it when it loads and is skipped entirely when it does not, so the case is playable either way. None of this creates an answer the author did not write: an unanticipated question still falls through. See `case-authoring-requirements.md` section 10.6 for measured accuracy and for what the measurements do and do not cover.
- **The arrival handover carries almost nothing.** Removing the Patient tab means the resident starts from two authored sentences. This is intended, but it means a matcher failure is no longer a nuisance, it is a stall. The failure mode to watch for is a resident who asks reasonable questions, gets nothing back, and concludes the case is broken rather than that their phrasing missed.

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
- one line naming where the patient was brought: `Patient brought to the Resuscitation Bay`, `the Trauma Bay`, or `the Patient Room`
- **the arrival vitals** (v0.8), read from the first authored phase
- the difficulty toggle
- the provenance warning, if the case carries one

**The arrival vitals are a handover artifact, not the monitor, and that distinction is
the whole reason showing them does not undo 8.4b.** A crew hands over the numbers they
measured; that is what a handover is, and the two sentences of it on the History tab are
the same thing in prose. What the resident still does not have is the current number and
the trend, which is what a monitor is for and what attaching one buys them.

So the strip is styled as figures on a pale panel rather than in the monitor's dark, the
numbers are static, and they carry none of the cosmetic variance the monitor adds. There
is no caption saying they are not live: the heading is past tense and the empty monitor a
few seconds later says the rest. A resident who has to be told in a sentence that a
number from before they walked in is not a live reading has been handed the lesson
instead of learning it.

A case whose first phase has no authored vitals hides the section rather than printing a
row of dashes. The picker offers half-authored cases on purpose and an empty panel
teaches nothing.

**What it deliberately does not show.** Through v0.4 the splash carried a section headed
"How they got to you" holding the arrival mode and the full handover. It was removed in
v0.5. It told the resident, before the clock started and without their asking, a large
part of what the interview is for. What remains is the room, because the room is scene
rather than history: it sets the expected acuity and it is the one thing a clinician
walking in genuinely knows before speaking to anyone.

**The room line is generated, not authored prose.** `metadata.arrival.location` takes one
of `resuscitation_bay`, `trauma_bay`, `patient_room`, and the engine renders the sentence.
An author cannot write a different sentence there, which is the point: the moment it is
free text it accumulates clinical detail again.

**The handover did not disappear, it moved.** It is now `patient.arrival_handover`,
displayed at the top of the History tab under the History heading, and it is capped at two
sentences. See section 18 and authoring section 3.2.

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

**Time-guarded transition deadlines are not scaled, and the reason is worth stating** because it
looks like an omission. Scaling them by the same multiplier would make hard mode *more* forgiving,
since the patient would take three times as long to deteriorate, while the prompts arriving later
makes it less forgiving. The two effects point in opposite directions and the mode would stop
meaning anything. Leaving deterioration unscaled keeps the property the modes were built for: the
patient's physiology is identical in both, and the only difference is how much help the nurse gives.
The consequence is real and should be understood before a case leans on it heavily: in hard mode a
resident may deteriorate a patient before the prompt that would have warned them has fired. That is
the honest version of the question hard mode exists to ask, and it is also the strongest argument
for the 30-second floor and the mandatory preceding prompt in 13.1. If deterioration pacing needs
tuning it should move through the global multiplier in open decision 10, not through difficulty.

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
| History | Demographics, the arrival handover, then the free-text interview | Fires on submit |
| Exam | General status line, then the 14 maneuvers | Fires on click |
| Stabilization | Access, airway, oxygen, intubation, fluids, pacing | Order batch |
| Investigations | Bedside, labs, imaging | Order batch |
| Interventions | All medications, procedures, blood products | Order batch |
| Consults | All consultants | Fires on click |
| Handoff | Disposition, diagnosis, confirm | Terminal |

**Seven tabs, not eight.** v0.4 opened on a Patient tab holding the handover, the
appearance and a structured background. It is gone. The engine keeps a `HIDDEN_TABS` set
containing `patient`, so a catalog placement pointing at it resolves without error and
renders nowhere, which lets existing catalog rows stay valid through the change. New
placements should not target it.

**What the History tab shows before the first question.** Age, sex, and the chief complaint
in the patient's words, then the arrival handover: two sentences attributed either to the
EMS crew or to the triage nurse, depending on `metadata.arrival.mode`. Nothing else. The
appearance and background that used to sit on the Patient tab are still authored and are
still what the interview answers are built from, but they are reachable only by asking.

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

---

## 20. Interview matching

New in v0.5. The clinical rules for authoring against this are in
`case-authoring-requirements.md` section 10.6; this section is the architecture.

The problem: the resident types free text, the case holds a fixed list of topics each with
an authored answer and a list of phrasings, and something has to choose one topic or none.
Choosing wrongly is worse than choosing nothing, because a wrong topic returns a
confidently worded clinical answer to a question the resident did not ask, and nothing on
screen marks it as a substitution.

### 20.1 Two stages, either of which can run alone

**Stage one is lexical and always present.** IDF-weighted Dice overlap between the query's
tokens and each authored variant, with the per-case weight table built when the case is
selected. It runs in about a millisecond and needs nothing from the network.

Three extensions were added in v0.5, all of them aimed at the same gap: residents type
clinical shorthand, and the authored variants are in lay register because they are what
the patient would recognise.

- **A clinical lexicon**, roughly ninety entries, rewriting abbreviations and clinical
  terms into the words the banks actually contain: `pnd` to `wake night gasping breath`,
  `orthopnea` to `lie flat pillows sleep lying down prop`, `pmh` to `medical problems
  history conditions diagnosed`. The rewrite is applied per token and **only where the
  case's own vocabulary does not already contain that token**, so a case that authored
  `orthopnea` as a variant is not rewritten out of its own match.
- **Single-edit typo repair** against the case's vocabulary, using optimal string
  alignment so a transposition costs one rather than two. Words shorter than five
  characters are never repaired, because at four characters a one-edit neighbourhood
  contains most of the short English vocabulary. Ties break lexicographically so the
  result is deterministic.
- **Compound splitting.** A question is split on `and`, `or`, `also`, `plus`, commas,
  semicolons and ampersands, and each clause matched separately. The whole question is
  matched first and its score sets the bar: a clause is only accepted if it clears that
  score times a tolerance. Without that gate, splitting produced spurious second answers
  on ordinary single questions that happen to contain the word "and".

**Stage two is an embedding model and is optional.** all-MiniLM-L6-v2, int8, roughly
23 MB, fetched from a CDN and cached in IndexedDB. It loads in the background after the
case starts. The state machine is `idle` to `loading` to either `ready` or `unavailable`,
and `unavailable` is terminal with no retry, because a model that failed once on a given
network will usually fail again and a retry loop is worse than a missing feature.

**The case is fully playable while stage two is loading or after it has failed.** This is
the reason the two stages are ordered this way rather than the model being a prerequisite.

### 20.2 The fusion rule

```
lex = lexical(q)
if the model is not ready:            return lex
sem = semantic(q)
if sem.score >= ACCEPT:               return sem      (0.62)
if sem.score >= AGREE and sem.topic == lex.topic:  return sem   (0.45)
return lex
```

A veto branch exists, where a very low semantic score suppresses a lexical match, and it
is **disabled in the shipped configuration** (`VETO = 0`). It was disabled deliberately:
the brief for this simulator is that the resident should get as many answers as the case
can honestly give, because no context is available anywhere else, and a veto trades
recall for precision in the wrong direction for that brief. A deployment that cares more
about false answers than about stalls should raise it.

**The thresholds are not measured.** 0.62 and 0.45 were chosen by inspection of a small
sweep and have not been validated against resident-typed questions. Treat them as
configuration with a plausible starting value, not as findings. The sweep tooling is in
`engine/matcher_eval.mjs` under `--semantic --sweep`.

### 20.3 The extraction contract, which has broken twice

Both evaluation harnesses read the shipped matcher out of `build/simulator.html` rather
than reimplementing it, so that the numbers describe the matcher that actually runs. They
locate it by marker comments:

```
start:  const STOP=new Set(
end:    /* ---------- fusion of the lexical and semantic matchers ----------
```

**Anything placed between those markers is evaluated by the harnesses**, in a context
where `semantic.js` is not loaded. A top-level `SEM.init(...)` inside that region throws
`ReferenceError: SEM is not defined` and the harness dies. This has now happened twice,
once in each harness, and the fix both times was to move the semantic wiring out of the
region rather than to change the markers. Engine-side semantic wiring lives in
`bindCase()`, after the fusion marker.

This is exactly the drift failure that authoring section 10.6 warns about, arriving from
the opposite direction: not a second copy of the matcher going stale, but the extraction
boundary silently moving.
