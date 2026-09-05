# Time-guarded phase transitions

**Status: adopted.** Folded into `system-design-v2.md` v0.6 sections 2, 4, 5, 7, 10, 11, 13, 14, 15
and 17, and into `case-authoring-requirements.md` v0.5 sections 0, 3.3, 4, 5, 9, 13, 14 and 15,
which are the source of truth for how the system behaves. This document is the rationale record: it
states why the static-patient invariant was broken, what else was considered, and what the mechanism
is expected to be used for beyond the case that prompted it.

---

## 1. The problem

Through v0.5 the clock governed three things and none of them was the patient: when results arrive,
when the nurse prompts, and timing feedback in the debrief. `system-design-v2.md` section 2.1 said
so flatly, and section 4 refused a time predicate in the condition language.

That invariant bought coherence cheaply. It also made a category of case unauthorable, and not a
marginal one. Consider what these presentations have in common:

- meningococcal septicaemia
- anaphylaxis
- status epilepticus
- tension pneumothorax
- occlusive myocardial infarction
- tricyclic antidepressant overdose
- hyperkalaemia with a widening QRS
- massive haemorrhage
- necrotising soft tissue infection

In every one of them the thing being taught is that the passage of time costs something. Not that a
particular action is wrong, and not that a particular action is right, but that a correct action
taken late is worth less than the same action taken early, and that past some point it is worth
nothing. A simulator in which an untreated patient is indistinguishable from a treated one cannot
say that. It can only say it in the debrief, afterwards, as a number.

**What authors did instead was worse.** The only available workaround was to substitute a proxy: find
an action the resident might plausibly take and hang the deterioration on it. The meningococcaemia
case reached its refractory shock phase by intubation, because intubating a vasoplegic
glucocorticoid-deficient patient genuinely does collapse her and it was the only action-shaped route
available. That is defensible physiology and it is the wrong lesson. It teaches "intubation caused
this" when the seed said "delay caused this", and it means a resident who freezes completely, which
is the failure mode most worth addressing, sees nothing at all.

---

## 2. What was considered and rejected

**An `elapsed > N` predicate in the condition language.** The obvious solution and the wrong one. The
v0.5 objection is correct: if time is available in conditions, authors put it in content, and a lab
result that reads one way before four minutes and another way after cannot be reviewed by reading a
table. The per-key review matrix is the artifact that actually finds clinical defects in this system,
and it works because every key projects over a finite set of phases, flags and study states. A time
axis has no natural granularity and the projection stops being enumerable. Rejected, and the refusal
in section 4 is retained verbatim.

**Continuous physiology, or vitals that drift within a phase.** Rejected for a different reason: it
would produce numbers no author wrote. The guarantee that every value the resident sees was authored
by a physician is the one that makes this tool safe to put in front of a learner, and interpolation
between plateaus with state behind it would break both that and result freezing. What was adopted is
a staircase, not a slope.

**Time-conditional content, meaning a study whose result changes with the clock.** Rejected for the
enumerability reason, and unnecessary besides: result freezing already answers the question these
cases actually want to ask, which is what the value was when the specimen was drawn. A rising
troponin is still not representable, and the right fix for that is the counting predicate proposed in
system design section 15, not a clock.

**Time on prerequisites, tags or follow-up applicability.** Rejected. An action that is harmful at
one moment and appropriate a minute later, with nothing else having changed, cannot be reviewed and
cannot be taught. Tags remain functions of state.

**A whole-case timer, meaning the case ends after N minutes.** Rejected. It is not a clinical claim
about anything, and it teaches clock-watching rather than medicine.

**Reusing the `halted` phase for a time-driven ending.** Rejected. `halted` carries a harmful
action's halt reason, and telling a resident "you gave metoprolol and she arrested" when in fact she
arrested because nothing was given attributes an omission to a commission. A case that can end on the
clock authors its own terminal phase with its own `timeout_reason`.

**Ticking every phase.** Rejected because it would change the behaviour of every case already
written. Section 5.6 specifies that an already-satisfied transition does not fire until the next
state-changing action, and a universal tick would silently make cascades resolve on their own.
Ticking only in phases that carry a time-guarded rule keeps every v0.5 case bit-identical.

**Scaling deterioration with difficulty mode.** Rejected after working out what it does. Hard mode
multiplies prompt deadlines by three, which makes it harder by giving less help. Multiplying
deterioration deadlines by the same factor would make it easier by giving more time. The two effects
point in opposite directions and the mode would stop meaning anything. Deterioration is unscaled, so
the physiology is identical in both modes and only the help differs, which is the property the modes
were built for.

**Deterioration proportional to how late the resident was.** Rejected: it needs continuous state.
A guard is true or false, so a drug given one second before the deadline has the same effect as one
given at once. An author who needs graded lateness needs graded phases.

**A grace period, or pausing the clock while a modal is open.** Deferred rather than rejected, and
recorded as open decision 9 in the system design. A resident reading a long consultant response is on
the same clock as one who has frozen, which is unfair in a way a prompt firing is not. The shipped
answer is that there is one clock with one set of semantics, and the mitigations are the 30-second
floor and the mandatory preceding prompt. This should be revisited against a real learner rather than
argued about.

---

## 3. What was adopted

A transition rule may carry `after_seconds`. It fires when the deadline has passed and its guard is
still true. A rule without `after_seconds` is instantaneous and unchanged.

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

**The key property is that time never enters the condition language.** The guard is an ordinary
condition with no time in it; the timing sits beside it in a named field. Content keys, tags,
prerequisites, follow-up applicability and interview answers still resolve against phase, flags and
study state, so the per-key review matrix has exactly the rows it had before. What a clock changes is
which phase you are in, and the matrix already enumerates over phases. This is the whole argument for
why the v0.5 refusal survives intact.

**What the matrix cannot show** is that a phase can now be entered with nobody having done anything.
That is why a third review artifact was added rather than the second one being widened. See section 6.

### Three patterns

| Pattern | Guard | `measured_from` | What it models |
|---|---|---|---|
| Deterioration on inaction | `NOT flag F set` | `phase_entry` | The illness progresses because the treatment was not given |
| Delayed consequence of an action | `flag F set` | `guard_true` | An action whose effect is not instantaneous |
| Scheduled natural history | `null` | `phase_entry` | The illness does something regardless |

The second is worth dwelling on, because it improves cases that have nothing to do with delay. Modelling
peri-intubation collapse as instantaneous teaches that the tube caused it. Modelling it forty-five
seconds after induction teaches that the induction agent and the positive pressure caused it, and
leaves a window in which a resident who anticipated it can have a pressor running. The clinical
lesson is in the window.

The third requires an `unguarded_rationale`, because a transition nothing can prevent is a scripted
trajectory rather than a response to the resident, and should be a decision an author remembers
making.

### Six safety rules

Enforced by the validator, and each of them is a lesson from a way this could go wrong.

1. **Thirty-second floor**, warning below sixty. A deterioration nobody could have prevented tests
   reflexes, not medicine.
2. **A prompt must precede it**, at least twenty seconds before the deadline, from an action that
   sets a flag the guard requires unset. This is the framing in section 1 of the authoring
   requirements made mechanical: the nurse exists to teach, so a deterioration nobody was warned
   about is a trap rather than a lesson.
3. **A prompt stranded past the exit is a defect.** A prompt at 260 seconds in a phase that ends at
   240 never fires. Nothing looks wrong; the learner is simply never helped.
4. **Terminal destinations need an explicit opt-in** plus a rationale, and must not reuse `halted`.
5. **No cycle made only of time edges**, which would be a case that plays itself.
6. **Every destination needs an exit**, as for any deterioration branch.

Rule 2 is the one that matters most and it is the one most likely to be argued with. It is what
keeps this feature inside the educational framing rather than turning the simulator into a reaction
test.

---

## 4. How other cases should use it

The mechanism was built for one case and it is worth being explicit about the general shape, because
the risk with a feature like this is that every subsequent case reaches for it.

**The test to apply.** Is the passage of time itself part of what you are teaching? If the lesson is
"this decision is wrong", author it as a tag. If the lesson is "this action has a consequence",
author it as an ordinary transition. Only if the lesson is "this had to happen sooner than it did"
does a clock belong in the case. Most cases fail this test and should not use the feature at all.

Worked examples, each of which the mechanism supports without extension:

| Case | Rule | Reads as |
|---|---|---|
| Anaphylaxis | `NOT flag epinephrine_im_given set`, 120s, → airway edema | Delay to adrenaline is the single determinant of outcome, and antihistamines and steroids do not stop the clock |
| Status epilepticus | `NOT flag benzodiazepine_given set`, 180s, → refractory status | Seizure duration is the variable; the second-line agent is a different phase again |
| Occlusive infarction | `NOT flag reperfusion_activated set`, 300s, → cardiogenic shock | Time is muscle, expressed as physiology rather than as a debrief line |
| Tension pneumothorax | `NOT flag needle_decompression set`, 90s, → arrest, terminal, opt-in | The one presentation where a very short deadline is defensible |
| Tricyclic overdose | `NOT flag bicarbonate_given set`, 240s, → wide-complex arrhythmia | The QRS is the clock, and the case can show it widening as a step |
| Hyperkalaemia | `NOT flag calcium_given set`, 180s, → sine wave | Membrane stabilisation is time-critical in a way potassium shifting is not |
| Massive haemorrhage | `NOT flag blood_products_given set`, 180s, → coagulopathic shock | Crystalloid does not satisfy the guard, which is the lesson |
| Simple febrile seizure | no guard, 90s, → postictal | Natural history: it stops on its own, and the teaching is that nothing needed doing |
| Biphasic anaphylaxis | no guard, 400s, → recurrence | The reason the patient is observed rather than discharged |
| Any case with an airway | `flag intubated set`, 45s, `guard_true` → peri-intubation hypotension | Improves cases that have no time pressure at all |

The last two rows are the ones worth noticing. This is not only a deterioration mechanism. Scheduled
natural history and delayed consequences are both better modelled with it than without, and neither
punishes the resident for being slow.

**A convention worth adopting across the library:** where a case uses deterioration on inaction, the
deadline should be roughly three times the prompt deadline for the action that prevents it. That puts
the escalation prompt comfortably inside the window and leaves a resident who acts on the second
prompt with time to spare. The meningococcaemia case runs at 240 seconds against a 45-second
antibiotic prompt and a 90-second escalation, which is a ratio of about five and is on the generous
side deliberately, because it is the first case to use the feature.

---

## 5. Engine notes

**Scheduling.** A time-guarded deadline is a scheduled event exactly like a prompt deadline or a
result arrival. On phase entry the server computes the due time of each time-guarded rule in the
phase and adds it to the schedule it already returns. No new transport, no new loop, no persistent
process. The existing five-second heartbeat is what catches a throttled or suspended tab, and a
laptop that slept through a deadline finds the deterioration applied on the next request, which
follows from the server being authoritative.

**Evaluation.** The transition checker runs after every state-changing action, and additionally on a
tick while the current phase has at least one time-guarded rule. Both evaluations run the full
ordered list with first-match-wins, so an instantaneous rule always outranks a time-guarded rule
beneath it. Phases without time-guarded rules are never ticked.

**The ordering rule now decides outcomes.** A deterioration due at t=240 and a drug given at t=240
produce opposite results depending on which is processed first. The existing tiebreak in section 5.3,
log entries before derived events at equal timestamps, already answers it: the resident who gets the
drug in on the deadline is credited. That was a determinism rule; it is now also a fairness rule, and
it should be stated as one.

**Replay.** Time-guarded transitions are derived from the log plus case data, like every other time
event, so nothing extra is stored and a log replayed against a corrected case file produces the
corrected outcome. A `time_transition` log entry type was added so the debrief can name which
deadline expired, in which phase, and what would have prevented it.

**Backwards compatibility is total.** A rule without `after_seconds` behaves exactly as before, no
phase without a time-guarded rule is ticked, and the difficulty multiplier is unchanged. The
reference heart failure case runs identically.

---

## 6. Review consequences

**The per-key matrix is unchanged in shape.** Same projection, same rows, one more phase to enumerate
over in any key that mentions phases. This was the design constraint, not a happy accident.

**A third artifact was added: the deterioration timeline** (authoring section 14.2c). Three parts:
every time-guarded exit with its guard, deadline, destination and preceding prompts; the do-nothing
trajectory from arrival to whatever the end is, with the clock at each hop; and every narration line
collected together to be read against the vitals it introduces. The second part is the one that earns
the artifact. It is the path a frozen learner sees, it is the path an author is least likely to have
imagined, and if its last row is a terminal phase then the case can kill the patient without the
resident touching her, which should be a decision somebody remembers making.

**The path simulator needs waits**, and four routes it did not need before: doing nothing at all;
treating each deficit alone and letting the clock take the other; a rescue inside the last window;
and a rescue one action too late. The last two should be written together, because the difference
between them is the entire lesson and it is easy to author a window nobody can hit.

**Four new checklist items** in authoring section 14.3, of which the substantive one is that every
deadline is a clinical claim the author is willing to defend: this patient, without this treatment,
deteriorates in about this long. That is not a number a model can supply.

---

## 7. What this still does not do

- No gradient. The patient moves between authored plateaus, and a case needing a genuine slope needs
  more phases, against a ceiling of six that now binds sooner.
- No partial credit for partial delay. A guard is true or false.
- No time in content, tags, prerequisites or follow-up applicability, and this is permanent rather
  than pending.
- No pause. The clock runs while the resident reads.
- No recovery on a clock in the sense of a drug wearing off, because flags are permanent. A
  transition can move the patient to a phase whose numbers represent a worn-off state, but the flag
  saying the drug was given stays set, and any content keyed on that flag will still return the
  treated value. Phase rules before flag rules, as always.
