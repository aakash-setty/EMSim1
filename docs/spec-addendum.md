# Spec addendum: structured results, catalog binding, and audio

Proposed against `system-design-v2.md` v0.3 and `case-authoring-requirements.md` v0.2.
**Superseded:** these changes are now folded into `system-design-v2.md` (now v0.5) and
`case-authoring-requirements.md` (now v0.4). This document is retained as the rationale record,
alongside `action-catalog.json` v0.1-draft and `diagnosis-catalog.json` v0.1-draft.

**Note on the catalog.** The `action-catalog.json` supplied in the project was stale relative
to `build_catalog.py` and `default_results.py` in the same folder: it was missing the exam
defaults, the general status default, the exam routing map and the `exam_set_is_closed`
statement, all of which the generator produces. Everything here is written against the
catalog regenerated from those sources. If the shipped JSON is the artifact of record rather
than the generator, it needs regenerating.

This is a change request, not an edit. The design documents belong to their owner; this
records what integrating the catalogs into a working case and a playable engine forced,
and what broke when it was tried.

Status of each item: **required** means something is currently broken or unrepresentable;
**recommended** means it works but silently produces a wrong result; **optional** means
it is a convenience.

---

## 1. Structured result payloads

**Required.** Design v0.3 treats a study result as a string. The action catalog does not:
its `default_result` carries `kind`, `components`, per-component `reference_range`, and a
per-component `abnormal` flag, with an explicit contract that "a case that overrides a value
must set abnormal itself; the renderer does not recompute in-range."

A case authoring results as prose cannot satisfy that contract. The two shapes cannot both
be right, and the prose shape is the one that loses information.

**Proposed.** Section 8 of the system design gains a result payload type, and section 7 of
the authoring requirements requires authored study results to use it:

```json
{"kind": "panel|value|report",
 "abnormal": true,
 "components": [{"label": "Sodium", "value": "133", "unit": "mEq/L",
                 "reference_range": "135-145", "abnormal": true}],
 "comment": "optional interpretive line",
 "verify": "optional note where the reference interval is not settled"}
```

`report` carries a `report` string instead of components. Payload-level `abnormal` must
equal the OR of its components; the validator now errors when it does not.

**Why not parse the prose.** The obvious shortcut is to look for "(high)" and "(low)" in the
authored string at render time. Do not. It is the exact recomputation the catalog contract
forbids, it fails silently the first time an author writes "raised" or "below the reference
interval" or gives a value with no marker at all, and the failure mode is a genuinely
abnormal value rendered as normal. Authoring the flag once in the file is a few minutes of
work per case and is checkable.

**Migration.** `structure_results.py` converts this case's eight lab keys and five imaging
keys, 25 payloads, preserving the original prose in a sibling `prose` key so the reviewing
physician can diff the structured payload against what was written. Reference intervals were
taken from the matching catalog default where one exists and marked `verify` where none does.
No number, unit or interpretation changed.

**Validator additions.** Payload shape; missing `abnormal` at either level; and a numeric
cross-check that parses the reference interval and warns when the flag disagrees with the
value. The renderer must not recompute, but the validator can, and a mis-set flag is
invisible everywhere else. This case currently passes the cross-check on every parseable
range.

---

## 2. The case-to-catalog binding is a first-class artifact

**Required.** The case was authored before the catalog existed and uses its own ids.
`labs_bmp` is `basic_chemistry_chem_7`; `furosemide_iv` is `furosemide_bolus`. Neither
document says how a case names a catalog action, and the catalog's own
`reference_case_id_map` is a note rather than a schema.

Resolving this by string similarity at load time is not acceptable: the near-misses are
clinically adjacent (`ketamine_bolus` and `ketamine_infusion`, `normal_saline_1l` and
`lactated_ringer_s_bolus`) and a wrong bind is silent.

**Proposed.** Either the case file references catalog ids directly, or a binding file sits
between them with an explicit status per row: `exact`, `mapped`, or `unmatched`. Mapped rows
carry an author note, because a mapping is a clinical judgement. Unmatched rows are validator
errors, not dropped rows.

**Result for this case:** 15 exact, 39 mapped, 11 unmatched. (It was 6, 44 and 13 before the exam findings were redistributed onto the catalog manoeuvres; see section 7a.)

---

## 3. Binding failures this case exposes

### 3.1 Blocking: no stop-action

The catalog rules stop-actions out of scope and marks infusions `persistent`. This case tags
stopping the nitrate as a critical action in `post_intubation_hypotension`, and the rescue
transition requires `flag nitro_stopped`.

**With the catalog as it stands, the deterioration branch has no exit.** A resident who
intubates this patient cannot rescue him, because the action that rescues him does not exist
in the interface.

Stopping a vasoactive infusion is a distinct clinical act with its own timing and its own
teaching point. Either the catalog gains stop-actions for `persistent` entries, or every case
with a vasoactive deterioration branch needs a different rescue and the design should say so.

### 3.2 Blocking: no venous blood gas

The catalog has `arterial_blood_gas` only. This case authors a venous gas and trends it
across four states. Substituting the arterial gas changes the clinical act, and the catalog's
own note says the ABG default assumes room air, which this patient is not on.

### 3.3 Assay mismatches that render as plausible numbers

Three bindings pass structurally and are clinically wrong:

- The case's **BNP 2840, reference under 100** binds to `pro_bnp`. Different assay, different
  reference interval, and the number is not transferable.
- The case's **numeric high-sensitivity troponin I against a stated 99th-percentile URL of 34**
  binds to `troponin_t`, whose catalog default is qualitative ("Unremarkable"). Assay, analyte
  and reporting format all differ.
- The case's **combined lung-and-cardiac ultrasound** binds to `ultrasound_lung`. The catalog
  has the two scans as separate acts, so the cardiac findings in the authored report are
  unreachable by a resident who orders only the cardiac scan.

These are the dangerous class: nothing errors, and the learner reads a plausible number
attached to the wrong test.

### 3.4 Shared catalog entries shadow case actions

CPAP and BiPAP were collapsed into one catalog entry on author instruction. This case tags
them separately. The interface can only offer one button, so `niv_bipap` is unreachable.
Same shape, different consequence: `crystalloid_bolus_1l` binds to `normal_saline_1l`, so
**`lactated_ringer_s_bolus` reaches the same patient harm through an unbound action and does
not halt the case.** Ipratropium alone escapes the bronchodilator trap the same way, and
`ketamine_infusion` does not satisfy the post-intubation sedation follow-up.

**Proposed.** A case action binds to a *set* of catalog ids, not one. Harmful tags in
particular need to name every route to the same harm, and the validator should warn when a
harmful action's catalog entry has sibling entries in the same group that are unbound.

### 3.5 Eleven further unmatched actions

`bumetanide_iv`, `echo_formal`, `vent_settings_lung_protective`, `peep_reduce`,
`bp_cycling_q5min`, `urine_output_monitoring`, `consult_critical_care`,
`exam_general_appearance`, `exam_hepatojugular_reflux`, `interview_topic_medication_adherence`,
`handoff_submit`.

Two are worth singling out. **There is no intensivist among the catalog's sixteen
consultants**, and critical care advice is the most disposition-relevant consultant content
this case has. And **there is no general appearance exam**, which is the finding that changes
most with treatment in a respiratory case.

---

## 4. Catalog prerequisites do not parse

**Required. Still present after regenerating the catalog**, so this is a defect in
`build_catalog.py` or its inputs rather than a stale file. Eight catalog entries carry prerequisites written as `flag sedation_given AND
flag paralytic_given`, `flag lumbar_puncture_performed`, and `flag pacing_pads_placed`, all
omitting the trailing `set` that section 4 requires. Section 10.1 of the authoring
requirements has the same slip in its worked example, so this is a documentation defect that
has now propagated into shipped data.

Either the grammar drops the trailing keyword or the catalog is corrected. The prototype
accepts the loose form and records that it is doing so, which is a workaround, not a fix.

---

## 5. Prerequisite merge semantics

**Required.** Section 3.5 allows a case to override catalog prerequisites, and section 8.1
shows the requirement polarity, but neither says what happens when a case *adds*
prerequisites to an action that already has catalog defaults.

The first implementation had case prerequisites replace catalog defaults. That silently drops
a real gate: a case that adds "needs a monitor" to a drug would lose "needs a line".

**Proposed, and implemented here:** catalog defaults apply unless explicitly waived through
`prerequisite_overrides`; case prerequisites are additional. Each merged prerequisite carries
its origin, and the debrief tells the learner whether a block came from the case or the
catalog.

---

## 6. Handoff diagnoses must reference catalog ids

**Recommended.** The case names its correct diagnosis as a free-text label. That label does
not appear verbatim in the 488-entry diagnosis catalog, so the binding fell back to a synonym
match. A case whose correct answer is resolved by fuzzy matching cannot be scored reliably.

Three of the seven authored alternative diagnoses also have no catalog entry: COPD
exacerbation, acute pulmonary embolism, and sepsis of unclear source. A resident who selects
the catalog's nearest equivalent gets the generic "not anticipated" note instead of the
authored teaching explanation, which is the wrong outcome for the three commonest wrong
answers to this presentation.

**Proposed.** `handoff.correct_diagnosis.catalog_id` and each alternative must be a diagnosis
catalog id, and the validator errors when one is not found.

---

## 7. Default results need an authoring warning, not just a contract note

**Recommended.** The catalog states the risk correctly in `default_result_contract`: "If an
author forgets to write the troponin in an MI case, the resident is shown a normal troponin
and taught the wrong thing."

That belongs in the authoring requirements as a numbered constraint, not only in the catalog,
because the author reads the authoring requirements. The prototype now surfaces it at the
point where it matters: the debrief has a section listing everything answered by a default
rather than by the case, so a learner and a reviewer can both see which normals were real
findings and which were the absence of authoring.

The catalog's own recommended validator rule is implemented: a study named in a condition or
tagged critical but with no authored result raises a warning that names which catalog default
will be served in its place.

---

## 7a. The exam set is closed, and the case must fit it

**Required, and now satisfied.** The catalog states that its 14 exam manoeuvres are the
complete set, supplies a default finding for each, supplies a `general_status` line rendered
above them, and supplies `exam_finding_routing`, a map fixing where a finding belongs when its
anatomy does not match a manoeuvre.

None of that is in either design document. Section 6 of the system design describes appearance
and vitals; nothing says the exam surface is closed, and nothing tells an author that inventing
a manoeuvre produces content no learner can reach.

This case had four such manoeuvres: general appearance, jugular venous pressure, hepatojugular
reflux, and extremities. Every finding in them was unreachable in the interface.

**Proposed.** Section 7 of the authoring requirements states that the exam set is closed,
reproduces the routing map or points at it, and requires authors to follow it. The reason the
catalog gives for the map is the right one and belongs in the authoring document: without a
fixed routing an author puts pedal oedema under cardiac in one case and musculoskeletal in
another, and the learner concludes the tool is arbitrary rather than learning where to look.

**Payload.** Exam findings take the same treatment as study results, with `kind` of
`exam_findings` and an `abnormal` flag, so the interface can mark an abnormal exam without
recomputing anything. The general status line uses `kind` of `general_status`.

**The general status line needs a case rule list, not just a default.** The catalog default is
"No acute distress. GCS 15." A case that makes its patient critically unwell and forgets this
key displays that line above a patient in severe respiratory distress, and it is the one exam
finding the learner cannot choose to skip. The catalog flags this risk in its own `verify`
note; the validator now errors when the key is missing.

**Validator additions:** the case may not author findings for a manoeuvre outside the catalog
set; every catalog exam must carry a default; the general status key must exist; exam and
general status payloads must carry `abnormal` and findings text.

**Migration.** `restructure_exam.py` performs the redistribution for this case, following the
routing map exactly. Three categories had no prior authored content and were written during
the move from findings the case already asserted elsewhere (airway, breathing, psychological);
they are recorded in `provenance.exam_redistribution` so a reviewer knows which sentences are
new. The hepatojugular reflux ceases to be a discrete act, which is a real loss of a
separately scorable manoeuvre.

**One remaining request.** A hepatojugular reflux entry, if the design owner agrees it is a
distinct act rather than part of the neck exam. Everything else this case needed from the exam
surface is now present.

---

## 7b. Order batching

**New.** Not covered by either document. Implemented in the prototype at the author's request;
specified here because it changes what the timing measures.

### 7b.1 Mechanic

On the investigations, stabilization and interventions tabs, clicking an action selects it
rather than performing it. Nothing enters the log until Submit Order. Selections are held per
tab and survive switching tabs, so an order set can be assembled across tabs and submitted in
pieces. Exams and consults are excluded: they are reads, not orders, and batching a read would
only add a step.

### 7b.2 What it does not change

Submitting a batch writes one log entry per action at the same timestamp, in the order they
were picked. The fold applies them in sequence, so prerequisites, transitions, follow-ups and
harmful tags evaluate exactly as they would one at a time. Verified: a batch containing a
harmful action halts on that action and discards everything selected after it, and the actions
before it are applied normally.

That behaviour is correct and will surprise learners, who tend to expect a submitted set to go
through as a set. Whether the interface should warn before submitting a batch that will halt is
a design decision; warning would leak the answer, so the current behaviour is probably right.

### 7b.3 What it does change

**Timing.** Prompt deadlines run from phase entry and are unaffected. But a resident can now
select five things, deliberate, and submit them at once, and the log records the moment of
submission rather than the moment of decision. Section 9.6 treats prompt deadlines as a measure
of relative urgency, and section 11 reports whether a critical action was independent or
prompted. Batching lets a resident sit past a deadline while composing, receive the prompt, and
then submit an order they had already selected, which will be scored as prompted.

If that matters, time from first selection in the batch rather than from submission. This case
does not currently do so.

**Realism.** Clicking an action and having it happen instantly is not how ordering works;
assembling a set and submitting is. But a resuscitation case often wants to teach that
hesitation costs something, and batching hides hesitation. The two goals conflict and the
design should say which wins.

### 7b.4 Interface details the design should fix rather than leave to each build

Two defects appeared while building this and are worth stating as requirements, because any
implementation will hit them:

- **Selecting must not move anything.** The first build revealed the pending-order bar and a
  Clear button on the first pick, which shifted the grid under the cursor and turned the next
  click into a misclick. The bar is now always rendered and Clear is always present but
  disabled; measured layout shift on selection is zero.
- **The selected marker must not change the button's height**, for the same reason. It is an
  absolutely positioned tick rather than a label in flow.

---

## 7c. Action buttons carry the name only

**Recommended.** The prototype previously printed each action's prerequisites and turnaround
class underneath its button. Both are removed.

Prerequisites are system detail. A real order menu does not annotate metoprolol with "needs a
line", and a blocked attempt with the nurse's message teaches the sequencing better than a
label does, which is the point section 6.1 makes about prerequisites being teaching devices
rather than validation. Printing them also makes the trap actions visibly different from the
safe ones, which leaks information.

Turnaround times are worse: showing "5s" next to a laboratory test tells the resident the
simulator's clock rather than anything clinical, and it invites gaming the order in which
studies are sent. Pending and resulted state is still visible through colour and the pending
rail, which is the information a resident actually needs.

---

## 8. Turnaround classes

**Optional.** The catalog adds `bedside` at 0 seconds, which resolves the change request in
section 7 of the review packet and makes the case's per-study override for ultrasound
unnecessary. One consequence worth a decision: at 0 seconds there is no order-and-wait beat
for a bedside scan, and the result appears in the same instant as the order. Two to three
seconds preserves the beat without pretending a scan takes as long as a lab. This case keeps
its 3-second override, which section 8.1 says should stay unused.

---

## 9. Audio

**New.** Not covered by either document. Implemented in the prototype; specified here so the
behaviour is reviewable rather than incidental.

### 9.1 Continuous heartbeat

A soft beep, pitched, at an interval of `60 / heart_rate` seconds, taken from the current
phase's authored vitals. Rate and pitch are derived, never stored; changing phase changes
the sound because it changes the vitals. One beat is a fixed-frequency sine under a gated
envelope, 8 ms rise, 45 ms hold, 25 ms fall, with a faint octave partial on a shorter
window; design 8.5 carries the reasoning and what it replaced.

### 9.2 Pitch mapping

`frequency = 880 * 2 ^ (-(reference - SpO2) / 12)`, with `reference = 100`.

A5 at full saturation, one semitone lower per percent below. At the presenting saturation of
87 that is 13 semitones below A5, about 415 Hz. At 96 it is 698 Hz.

**Assumption flagged.** The brief specified A5 and half a step per percent "below" without
naming the anchor. 100% is the only defensible anchor for "A5 at full saturation", and "half
step" is read as one semitone in the standard musical sense. Both are single named constants
(`spo2Reference`, `semitonesPerPercent`) and the interface displays the current mapping on
screen rather than hiding it.

**Clinical caveat for the reviewer.** A real pulse oximeter's pitch drop is not linear in
semitones and does not begin at 100%. This mapping is more dramatic than the bedside sound
residents will actually hear, which makes it a better alarm and a worse simulation. If the
goal is transfer to real practice rather than in-simulator salience, it should be matched to
the device convention instead.

### 9.3 Prompt trill

A rising two-note trill, 1318.5 Hz then 1760 Hz, 90 ms apart, on triangle waves so it is
timbrally distinct from the heartbeat. It fires on nurse prompts and follow-up prompts only,
not on narration, results, or block messages.

**Design constraint this inherits.** Section 9 forbids a nurse prompt from implying
deterioration. A distinct alert sound attached only to prompts partly undermines that: the
resident learns that the trill means "you have missed something", which is information the
prompt text is not allowed to carry explicitly. Whether that is acceptable is a pedagogical
decision. If it is not, the trill should fire on every nurse utterance rather than on prompts
alone.

### 9.4 Controls and browser constraints

Audio cannot start without a user gesture, so the context is created on the first click and
the toggle reports actual state (`Enable sound` / `Sound on` / `Sound off`) rather than
intent. Muting persists across subsequent interactions. Sound stops when the case ends.

**Accessibility.** Nothing in the interface currently depends on sound alone; the monitor
carries the same information visually. That must remain true.

---

## 10. Validator changes in this pass

Added to `validate_case.py`:

- result payload shape, and `abnormal` present at both levels
- payload-level `abnormal` must equal the OR of its components
- numeric cross-check of every parseable reference interval against its flag
- every case action has a binding row; unmatched rows error; blocking unmatched rows error
  with the reason
- binding targets must exist in the catalog
- catalog entries bound by more than one case action warn
- every catalog condition must parse in the section 4 grammar
- every catalog investigation must carry a `default_result`
- a study named in a condition or tagged critical but unauthored warns, naming the default
  that will be served
- exam and general status payloads carry `abnormal` and findings text
- the case authors no exam manoeuvre outside the catalog's closed set of 14
- every catalog exam carries a default finding
- the `general_status` content key exists, so the learner does not see the catalog's generic
  "No acute distress" line above a critically unwell patient

Current state on this case: **5 errors, 2 warnings.** Two errors are the blocking binding
gaps in section 3; three are the catalog grammar defects in section 4. None is a defect in
the case content. The validator is doing its job by refusing to pass a case that cannot
actually run against the shipped catalog.

The exam gaps reported in earlier revisions of this document are resolved. `exam_general_appearance`
and `exam_hepatojugular_reflux` are no longer unmatched case actions, because the exam findings
now bind one-to-one onto the catalog set: the binding is 15 exact, 39 mapped, 11 unmatched,
improved from 6 exact, 44 mapped, 13 unmatched.
