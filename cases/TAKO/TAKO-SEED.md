# TAKO seed and provenance

Takotsubo cardiomyopathy with outflow obstruction in a 68-year-old woman, presenting as an
anterior ST-elevation infarct. Drafted by a language model on 6 October 2026 at the
request of Aakash Setty. **No physician has reviewed this pack.** Authoring requirements
section 17 applies. Read every number as a proposal.

## 0. What a person decided

Aakash Setty, 6 October 2026:

| Decision | What was decided |
|---|---|
| Handoff diagnosis | ST-elevation infarct is the correct working diagnosis. Takotsubo named first is defensible. The angiogram is revealed in the debrief |
| Norepinephrine | Left neutral and accepted, because the evidence is contested |
| Fluid | She is written with clear lungs so that a fluid bolus is right, and the debrief says wet lungs would change it |
| Catheterization lab | A button that appears in this case only |
| Cardiology | The nurse recommends cardiology whenever the pressure falls. The cardiologist gives the right treatment outright and can take over. "This is a hard case" |
| Cardiology availability | The cardiologist is busy until both an ECG and a bedside echo have been done. An earlier call is refused with the reason |
| Case map | Approved as presented: four states, a scripted fall at 180 seconds, nitrate leads to the obstructed state, the echo is not required for treatment to work |

Everything else is model output.

## 1. Learning goals and where each is acted on

| Goal | Where |
|---|---|
| Treat ST elevation as an occlusion whatever the story | Arrival. The daughter argues it is nerves. ECG, aspirin and activation are prompted only late |
| Look at the heart before treating cardiogenic shock | The murmur and the echo are available and never offered |
| Treat outflow obstruction the right way round | Nitrates and inotropes are available and show their effect. Fluid and a vasoconstrictor show theirs |

## 2. Phases

| Phase | HR | BP | Reached |
|---|---|---|---|
| presentation | 115 | 96/60 | arrival |
| obstructed | 124 | 82/50 | 180 seconds, whatever is done. Or ten seconds after a nitrate |
| shock_untreated | 138 | 70/42 | obstructed for 240 seconds without both fluid and a vasoconstrictor |
| shock_worse | 138 | 70/42 | ten seconds after an inotrope, from any earlier phase |
| steadied | 104 | 100/62 | fluid and a vasoconstrictor (inotrope stopped if one was given). Or 90 seconds after cardiology is called with a low pressure |

The map showed one "worse" state. It is two phases with the same numbers because their
exits differ: the inotrope has to be stopped in one and not the other.

## 3. Changed from the approved map after the fact-check

- **Beta blocker once steadied is neutral, not recommended.** The consensus document says
  beta blockers may improve obstruction and are contraindicated in hypotension and in
  acute heart failure with a low ejection fraction. She has both.
- **The murmur is louder with Valsalva and softer with legs raised.** "Louder sitting up"
  was wrong. Sitting forward is the position for aortic regurgitation and a rub.
- **The ECG now shows elevation in V2 to V5 and II with depression in aVR.** The first
  draft authored the infarct pattern (V1 to V4, I and aVL) while claiming the opposite.
- **The troponin is no longer called modest.** An early troponin does not separate the
  two. The lower peak shows later.

## 4. Checked, and by what

An independent model pass on 6 October 2026 opened the 2018 international consensus
document part II (through a summarizing tool), a 2026 review of cardiogenic shock in
takotsubo, a 2021 case report and one emergency medicine summary. It was not a physician
review. It found 13 problems, and all of those that could teach something false were
fixed.

Confirmed against an opened source: obstruction in about one in five, treat as an acute
coronary syndrome with aspirin and heparin, no reliable ECG discriminator, avoid inotropes
and nitrates and diuretics in obstruction, cautious fluid only with clear lungs,
recovery of the ventricle in four to eight weeks, and in-hospital outcomes comparable to
acute coronary syndrome.

**Not supported by the consensus document:** phenylephrine and vasopressin. It names
neither. A 2026 review prefers phenylephrine and allows norepinephrine with careful
titration. Vasopressin is an extrapolation. The debrief says this.

Not verified by anyone: every STEMI guideline number, the figure in the consensus
document that summarizes management, and the murmur's response to maneuvers in takotsubo.
**A physician should read that figure before sign-off.**

## 5. Open questions for the physician

1. Is fluid plus a pure vasoconstrictor the plan you would teach, given that the
   consensus document names no vasoconstrictor?
2. The cardiologist takes over 90 seconds after being called. A learner who calls early,
   which is correct, is rescued 90 seconds after the pressure falls whether or not they
   act. Is that too generous?
3. Thrombolysis is only discouraged. It carries a real bleeding risk for no benefit.
4. NT-proBNP of 5200 one hour after onset is early. It usually peaks at 24 to 48 hours.
5. Lactate falls from 5.8 to 3.6 across a ten-second transition.
6. No QT prolongation, apical thrombus or anticoagulation is taught. Left out on purpose.

## 6. Engine changes made for this case (v0.22)

- Validator and timeline tool: a guard was read as negated if the text "NOT" appeared
  anywhere in it, including inside "inotrope". Now a whole-word match.
- Shared engine test: picks an unguarded vital effect when every prerequisite-free one is
  guarded off at the start.
- No engine.js or interface change. The case-only button uses the existing mechanism.
