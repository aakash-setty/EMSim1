# Changelog

Unreleased. No case has completed the section 14.3 sign-off checklist, so none of this
is usable with learners.

---

## System design v0.6, authoring requirements v0.5

**Time-guarded phase transitions.** A transition rule may carry `after_seconds` and fires
when the deadline passes with its guard still true. This removes the invariant that an
untreated patient never changes, which had made a category of case unauthorable:
meningococcal sepsis, anaphylaxis, status epilepticus, tension pneumothorax, an untreated
occlusive infarct. The previous workaround was to hang the deterioration on some action
the resident might take, which attributes an omission to a commission.

Time does not enter the condition language and will not. It lives in a named field on one
kind of rule, so content keys, tags, prerequisites and interview answers still project
over phase, flags and study state, and the per-key review matrix is unchanged in shape.
That was the design constraint, not a happy accident.

Three patterns are supported: deterioration on inaction with a negative guard, a delayed
consequence of an action through `measured_from: "guard_true"`, and scheduled natural
history with no guard at all.

Deterioration deadlines are deliberately not scaled by difficulty. Scaling them would
make hard mode more forgiving at the same time as the later prompts make it less
forgiving, and the mode would stop meaning anything.

Rationale record, including everything rejected: `docs/decisions/time-driven-transitions.md`.

Sections changed: design 0, 2, 4, 5, 7, 10, 11, 13, 14, 15, 17. Authoring 0, 3.1, 3.3, 4,
5, 9, 10.6, 13, 14, 15, 16.

## engine/

**`engine.js`: time-guarded transitions in the fold.** Two new pieces of fold state, a
`checkTransitions` that consults a deadline, deadlines scheduled as derived events
alongside prompts and results, and a `deadline` case in `applyEvent`. A rule without
`after_seconds` behaves exactly as before, so CHFE is unaffected. A new nurse utterance
kind, `deterioration`, carries the transition's narration; it is the only place in the
system where a nurse line may describe a trajectory, and putting it on its own channel
keeps the no-trajectory assertion on prompts valid. A new `timeFires` record lets the
debrief name which deadline expired rather than only that the patient ended up somewhere
bad.

**`engine.js`: a covered entry no longer prompts or is expected.** `also_covers` exists so
that a tag cannot be escaped by choosing a sibling agent. It was also handing the covered
entries the covering action's prompt and its critical expectation, so the four crystalloid
entries prompted four times for one act and consumed the whole per-phase prompt cap
between them. That was suppressing the glucocorticoid prompt in MGCA and leaving a
deterioration unwarned, which is precisely what the cap must never do. Covered entries now
keep the tag, the halt reason and the debrief note, and the covering action alone prompts
and is expected. This also removes three phantom entries from CHFE's omissions list.

**`validate_case.py`: the six time-transition rules.** A thirty-second floor, a mandatory
preceding prompt with twenty seconds of lead, an error on a prompt stranded past the exit,
an explicit opt-in before the clock may end a case, a ban on a time-driven ending reusing
the shared `halted` phase, and cycle detection over time edges. Ten seeded defects were
each caught.

**`sim_runner.py`: a clock, and equivalence groups.** A scenario step may be
`{"wait": 120}`. Steps naming a covered sibling now resolve through `also_covers`, which
they previously could not, so group coverage was untestable; CHFE gained three scenarios
walking the crystalloid siblings its harmful tag claims. A step naming an action the case
does not hold is now reported rather than silently discarded.

**`engine-tests.js`: updated for v0.6.** `mode changes only the prompts, not the phase`
asserted the phase was still the starting phase after 300 seconds of inaction, which was
only true while no case could deteriorate. It now asserts what it was for, that both modes
produce the same phase sequence. A new generic section walks the do-nothing path and
checks that every deterioration is preceded by a prompt that **actually fires**, which is
the thing the validator cannot see.

**`build_simulator.py` and `shell.html`: the welcome screen** replaces the case picker and
keeps the id `picker`, so `chooseCase`, `backToPicker` and the `[data-case]` delegation are
untouched. Seventy per cent hero, thirty per cent case board built as an ED tracking board:
aligned columns, a status bead, sticky group headers, search on `/`, chips generated from
the data, arrow keys and Enter. The splash gained a real back control at the top of the
card. Two new optional card fields, `metadata.complaint` and `metadata.category`, both
degrading. Three new build-time assets.

## cases/

**MGCA is new.** Meningococcaemia with septic shock, early DIC, acute kidney injury and
adrenal crisis from bilateral adrenal haemorrhage, in a 21-year-old woman. Six clinical
phases, 124 case actions, 41 interview topics with 492 variants, five time-guarded
transitions of which one is terminal. Written directly in catalog ids, so all 123 binding
rows are exact and none needs a clinical signature.

Seven clinically wrong resolutions were found by reading the review matrix, and none
raised an error anywhere: a cerebrospinal fluid glucose that was a normal ratio on one
path and frankly low on another, a platelet count that rose across a transition, the same
defect in the coagulation panel and the D-dimer, a creatinine that fell in minutes, a
cardiac ultrasound that recovered systolic function, a lumbar puncture permitted in the
vasopressor-dependent phase, and four consultants quoting arrival values in phases where
they differ.

**CHFE: the two non-invasive ventilation actions consolidated into `niv_bipap_cpap`.** They
both bound to one catalog entry, and because one entry resolves to one case action the
second was never in the action surface: its tag, its debrief note and its two references
were unreachable. The merged note carries both teaching points, including the one that was
lost, that bilevel and continuous pressure are equivalent here and that bilevel is often
preferred in the hypercapnic patient. This also fixed a scenario passing for the wrong
reason: it named `niv_bipap`, the engine discarded the step silently, and the scenario
reached `presentation` while expecting `stabilizing`.

## catalog/

`reference_case_id_map` still mapped both old NIV ids, in the generated catalog and in
`build_catalog.py`. Consolidated.

---

## Outstanding

- Section 14.3 sign-off on both cases. Neither is usable with learners.
- MGCA's interview matcher returns 22 of 37 held-out phrasings, with four wrong topics on
  topics that change management, and refuses only one of six out-of-scope questions. The
  fix is variant expansion written against fresh phrasings; the held-out set stays held
  out.
- The engine drops a log entry naming an action the pack does not hold without applying,
  blocking or logging it. `sim_runner.py` now reports it; the engine should refuse it.
- MGCA's `halted` phase and CHFE's are both alertness-gated terminal phases not named in
  their global interview rules. Unreachable today, a defect the moment either stops being
  terminal.
- Whether the clock should pause while a resident reads, and whether deterioration pacing
  should get a global multiplier. Design section 14, open decisions 9 and 10.
