# The cold-start test

The acceptance test for the restructure described in `docs/restructure-plan.md`. It
measures the one thing the restructure is for: can an AI that has never seen this
repository build a case correctly from the repository's own instructions, and how much
does it have to read to do it.

The test is run once before the restructure (the baseline) and again after each step that
changes what a builder reads. The seed, the instructions and the scoring below are frozen.
Changing any of them invalidates the comparison, so a change gets a new version of this
file and a fresh baseline.

**The seed is a test fixture, not a case.** A model wrote it in one sitting with no source
and no physician. Nothing built from it ships, and nothing built from it is kept in
`cases/`.

## How it is run

1. Copy the repository at the commit under test to an empty folder. Remove nothing.
2. Start a fresh agent with no memory of this project. Give it the instructions below and
   the path to the copy. Do not answer questions. If it asks, it is on its own.
3. When it stops, run the chain on its pack yourself and score.

## The instructions given to the agent

> You are building a new case for EMSim, a browser emergency medicine simulator, in the
> repository at PATH. Nobody is available to answer questions. Work from the repository's
> own instructions. The seed for the case is in SEED (a file). Build the case pack for
> prefix HYPK as the repository says a case should be built today, until the validator
> reports no errors and the engine tests and the scenario runner pass for your pack, or
> until you judge further effort would not help. Then stop and write REPORT.md in the pack
> folder with: every file you opened and roughly how much of it you read, in the order you
> read them; every rule or convention you were unsure about; everything you looked for and
> could not find; and anything you invented because you could not find it. Do not change
> files outside your pack folder unless the repository's instructions tell you to, and if
> you do, list each one in the report with the reason.

## The seed

```
HYPK: severe hyperkalemia in a dialysis patient who missed a session

Identity. Working title "Missed dialysis, weak legs". Complaint for the case list:
"Weakness and a slow pulse". Chief complaint in the patient's words: "My legs have gone
heavy and I feel sick." Diagnosis: the catalog's hyperkalemia entry. Level: intern and
junior resident. Category: Renal and electrolytes.

Patient and arrival. 58-year-old man, 82 kg, on hemodialysis three times a week through a
left arm fistula. Missed his last two sessions because his ride fell through. Arrived by
EMS to a patient room. Handover is from the crew. He is alert, pale, slow to speak, with
diffuse weakness worse in the legs. He denies chest pain. Presenting vitals: HR 48 regular,
BP 118/70, RR 18, SpO2 96% on air, temperature 36.6.

Learning goals. (1) Treat the ECG, not the number: calcium goes in as soon as the tracing
shows widening or peaked T waves, before any result is back. (2) Shifting potassium into
cells buys time and nothing else: the patient is not treated until the potassium leaves the
body, which here means dialysis. (3) Every shift has a cost the learner must cover: insulin
needs glucose, and bicarbonate does little in a patient who is not acidotic.

Phases.
- arrival: as above. ECG shows peaked T waves, QRS 128 ms, PR 220 ms, HR 48.
- stabilized: after IV calcium. HR 56, QRS 104, PR 200. T waves still peaked. Potassium
  unchanged. Lasts as long as the case needs; the learner has to go on to shift and remove.
- shifted: after calcium AND an insulin bolus (or nebulized albuterol if that is all they
  give; count albuterol as a partial shift that does not reach this phase on its own).
  HR 62, QRS 98, T waves less peaked. Potassium on a repeat level 5.9. Glucose falling if
  no dextrose was given with the insulin, see follow-up.
- worsening: if the learner gives insulin, bicarbonate or albuterol with NO calcium, the
  ECG widens further: QRS 160, HR 40, BP 96/60. Calcium rescues this to stabilized.
- dialysis_arranged: after nephrology has been called with a potassium result back and the
  learner asks for dialysis. This is the exit. Vitals as in shifted.
No time-driven deterioration. He does not arrest in this case. Nothing halts the case
except the one harmful action below.

Actions.
- Critical: 12-lead ECG, attach monitor, IV access, IV calcium (chloride or gluconate;
  the catalog may hold only one, bind what exists and request the other), IV insulin
  bolus WITH glucose, nephrology consult once a potassium is back, dialysis as the
  disposition.
- Recommended: nebulized albuterol, repeat potassium after shifting, basic metabolic
  panel, venous blood gas.
- Discouraged: sodium bicarbonate bolus (he is not acidotic; gas pH 7.36), IV fluid bolus
  (he is anuric and already volume-up; mild cost, not harmful), furosemide.
- Harmful: succinylcholine, by any route the catalog offers. Reason: it raises serum
  potassium and in this patient precipitates arrest. If the learner intubates, the halt
  reason says what happened. Rocuronium is neutral.
- Trap: insulin without dextrose. Author a follow-up: after an insulin bolus, dextrose is
  due within 60 seconds; if not given, a fingerstick at 2.9 appears when next checked and
  the nurse says he is sweaty and confused. The catalog may have no dextrose entry; if so,
  request it and author the follow-up against the request.

Sequencing. Calcium has no prerequisite beyond IV access. Insulin requires IV access.
Nephrology gives no plan until a potassium result exists; before that they ask for one.
Dialysis as a disposition requires nephrology to have been consulted with a result back.

Key findings. Potassium 7.4 (ref 3.5-5.0, abnormal), creatinine 9.8, BUN 92, bicarbonate 20,
glucose 142, calcium 8.6, pH 7.36 on venous gas. After shifting: potassium 5.9 (still
abnormal). Exam: regular slow pulse, fistula with a thrill, mild bibasal crackles, 2+ leg
edema, power 4/5 in both legs, reflexes reduced, no chest pain on questioning.

Interview ground truth. Missed two dialysis sessions (transport). Dialysis Mon/Wed/Fri.
Weakness started this morning, worse in the legs, now hard to stand. Nausea, no vomiting.
Ate a large meal yesterday with oranges and a banana. Medications: amlodipine, sevelamer,
a renal vitamin, and he takes a potassium supplement his cousin gave him "for cramps" (he
will only mention this if asked about anything else he takes). Allergies: none. Past
history: diabetes, hypertension, end-stage kidney disease. No chest pain. No palpitations.
No fever. No shortness of breath at rest. Social: lives alone, does not drive, no alcohol,
quit smoking ten years ago. Code status: full.

Disposition. Correct: ICU or dialysis unit with telemetry, for urgent dialysis. Acceptable
with qualification: step-down with telemetry if dialysis is happening within the hour.
Wrong: ward (no telemetry for a widened QRS), discharge. Diagnosis: hyperkalemia. Also
true: end-stage kidney disease, missed dialysis, volume overload. Plausible wrong
primaries: acute kidney injury, bradycardia from a conduction block, hypothermia.

Nurse. Prompt for calcium at 45 seconds in arrival if the ECG has resulted and no calcium
has been given. Prompt for dextrose as the follow-up above. Prompt for nephrology at 120
seconds in shifted.
```

## Scoring

Score from the files the agent leaves, not from its report, except where noted.

**A. Validator errors.** Run `python3 engine/validate_case.py cases/HYPK`. Count errors and
warnings. If the pack does not build, record that and score the rest from the sources.

**B. Traps.** One point for each avoided, zero for each hit, not scored if the seed did not
exercise it. The list is the audit's known traps, fixed on 8 October 2026.

1. Every condition uses the trailing keyword (`flag F set`, `study S resulted`).
2. Phase rules precede flag rules in every rule list that has both.
3. Every content key ends in an unconditional default.
4. `short_label` on every phase, and none names the diagnosis or the drug.
5. The handover is two sentences, names no diagnosis, no history, no medications and no
   pertinent negative.
6. Pertinent negatives (chest pain, palpitations, fever, dyspnea) are authored as denials,
   not left to the out-of-scope fallback.
7. Every topic in the required coverage list is authored, including irrelevant ones.
8. The harmful action covers every catalog route to the act, has a `halt_reason`, and the
   pack has a `halted` phase.
9. Tags are rule lists, with the fallthrough checked in every phase (succinylcholine is
   harmful everywhere, not only on arrival).
10. The follow-up names a satisfier (`satisfied_by` or `satisfied_when`) and is attached on
    the action through the field the engine reads.
11. The nephrology consultant has a pending tier and gates on `study ... resulted`.
12. A missing catalog entry (dextrose, calcium gluconate, nephrology, dialysis) is recorded
    as a catalog change request, not invented as an action, and not silently dropped.
13. `general_status` is authored per phase.
14. Abnormal flags are set on every abnormal value and the payload flag equals the OR.
15. The ECG report states findings (peaked T, QRS width) and no conclusion.
16. No prompt text quotes a vital sign or implies a trajectory.
17. `key_topics` and `must_ask` are authored.
18. The out-of-scope bank is generated, not hand-written, and the held-out questions were
    written before expansion.
19. The pack is in the Python-source layout with a `build_case.py`, matching the newest
    pack's conventions.
20. The provenance block says a model wrote it and lists what needs a physician.
21. Phase vitals are the unsupported baseline (no vital effect double-counts).
22. Diagnoses are catalog ids, including the alternatives and the additional list.
23. The worsening branch has an authored exit (calcium) that exists in the catalog.
24. Nothing in `engine/` or `catalog/` was edited except as the README instructs.
25. The debrief has a note for every tagged action, the follow-up and the wrong
    dispositions.

**C. Dead fields.** Count fields the pack authored that no engine or tool reads (list in
the audit note B2, and after step 1 in `docs/generated/field-reference.md`).

**D. Reading cost.** From REPORT.md: sum the tokens (bytes over 4) of every file read, pro
rata for partial reads, and count the files opened. Record which generated files, other
packs, the changelog and the system design it opened.

**E. Time.** Wall-clock minutes and the agent's tool-call count, as the harness reports them.

## Results

| Run | Commit | A errors / warnings | B avoided / scored | C dead fields | D tokens / files | E minutes / calls |
|---|---|---|---|---|---|---|
| Baseline, 9 Oct 2026 | 557b1c7 (v0.24 as on the Mac on 8 Oct) | 0 / 1 | 23 / 24 | 16 | about 162,000 / 55 | 35 / 111 |

Baseline notes. Pack built in the Python layout copying DKA, passing every tool. Trap hit:
number 2, `general_status` has a flag rule above a phase rule. Not scored: 21 (no vital
effects). Dead fields written: 16 (`clinical_description`, `pupil_size`,
`pupil_reactivity`, `intended_path`, `ems_handover_text`, `background`,
`changes_with_state`, `clinical_domains`, `presenting_appearance`, `phase_notes`,
`flag_namespace_note`, `prerequisite_semantics_note`, `tag_vocabulary`,
`authored_against`, `teaching_frame`, `level_of_care`). Reading: the whole authoring
document (48,700 tokens) and the whole validator (22,800) were the two largest items;
seven DKA source files, parts of three other packs, four engine files and the catalogs by
script made up the rest. Not opened: the changelog, the system design beyond ten lines,
the decision records. The builder's own report lists sixteen uncertainties, and these are
gaps in what it was given: instant transitions carry no spoken narration (found only in
`engine.js`), the shape of `prerequisite_overrides` (learned from CHFE), the test helpers
and state fields (learned from `DKA-tests.js`), that disposition ids are case-defined, and
that the engine suite's device check takes the first catalog paralytic. The builder's
subagent run used about 509,000 tokens in total. The pack and the report are kept in
`Claude outputs/cold-start-baseline-HYPK.tgz`; the pack is not in `cases/`.
