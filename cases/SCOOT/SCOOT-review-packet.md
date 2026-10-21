# SCOOT review packet

**Status: drafted by a language model on 19 October 2026. Not reviewed by a physician. Not
for learners. Sign-off: not started.** Start with `SCOOT-SEED.md`.

A 22-year-old man after an e-scooter crash without a helmet arrives talking at GCS 15 with a
right temporal epidural hematoma, declines to GCS 12 at four minutes whatever is done, and
herniates if neurosurgery is not called with the scan. Four learning goals and four states
were approved by Aakash Setty on 19 October 2026. Everything else is model output.

## What to read

| File | What it is |
|---|---|
| `SCOOT-SEED.md` | What a person decided, the model defaults taken without a decision, sources and how each was read, the goals, the stories, the phases, the race tables, the action spine, key findings, the interview ground truth, known gaps and open questions |
| `SCOOT-review-matrix.md` | What every tag, finding, result, consultant line and answer resolves to in every state |
| `SCOOT-deterioration-timeline.md` | Every timed rule with the prompts before it, the do-nothing path, and every nurse line beside the vitals it introduces |
| `SCOOT-binding-map.json` | Every case action and the catalog entries it claims. Two coverage rows and five case-only rows |
| `case_1_shell.py` | Identity, the patient, the handover, the phases and every transition |
| `case_2_actions.py` | Every tag, prompt, prerequisite, hidden target, the follow-up and every debrief note |
| `case_3_content.py` | Findings, results, the tracings and what the consultants say |
| `case_4_interview.py` | Everything he says, in both voices |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points, provenance |
| `media/README.md` | How the four tracings were drawn |
| `SCOOT-tests.js`, `SCOOT-scenarios.json` | The case assertions and the walked scenarios |
| `SCOOT-matcher-eval-questions.json` | The held-out interview questions |

The review matrix does not show prompts, prerequisites, the follow-up, transitions,
`also_satisfies` or the figure's `also`. Read those in the source and the timeline.

## Most likely to be wrong

1. **The three clocks** (240 s, 120 s, 300 s). The decline cannot be prevented by design.
   The 120 s to herniation (pupil at 6:00) is the owner's choice after play. Ask whether
   300 s to brainstem compression feels right against it, and whether two minutes of
   warning in the decline is enough (SEED 2.14).
2. **The terminal clock in herniation.** A model default the owner did not choose. Remove the
   one transition if the case should never kill him.
3. **Osmotherapy tags.** Discouraged at GCS 15, neutral (accepted) in the decline, required
   only once the pupil blows. The decline is where good doctors disagree.
4. **The neurosurgery prerequisite.** The call cannot be placed before a CT has resulted. A
   heads-up call before the scan is reasonable in life.
5. **The head CT images and their read.** The images are the EDH case of the Head CT Teaching
   Cases artifact, synthetic, not reviewed by a radiologist. One series answers in every
   phase. The case's numbers were changed to match them (about 50 mL, 19 mm, 6 mm shift).
   The learner now has to read the scan.
6. **Model-added findings:** left-sided weakness in herniation, road rash, the patient's name,
   his friend Marcus, his father's blood pressure.
7. **The consultant** no longer quotes a number, and still calls it a collection with shift.
8. **The pupils drawn.** The eye view follows the exam text: right 6 mm and fixed in
   herniation, right 4 mm and sluggish after osmotherapy, both 6 mm and fixed in brainstem
   compression, 3 mm and brisk otherwise. Check that a pupil coming back that far within 15 s
   is what should be taught (SEED 2.13).
9. **No CT or neurosurgery prompt on arrival** (owner, 19 and 20 October). On arrival the
   nurse prompts only the monitor and the neuro exam (3:00 in the default mode). A learner who
   never scans him first hears about it at 5:15 (SEED 2.15). Check that this is the help a
   junior learner should get.

## Counts, from the run of 19 October 2026

| Check | Result |
|---|---|
| `engine/test_packs.py`, all eight packs | All pass |
| SCOOT engine checks | 574, all passed |
| SCOOT scenarios | 12 of 12 |
| Validator | 0 errors, 1 warning (the five case-only actions, including `handoff_submit`) |
| Validator negative tests | 111, all passed |
| `engine/kit_check.py` | 0 errors, 0 warnings |

## Vital effects

None. Every number on the monitor is a phase's authored number, and the ECG captions and
consultant lines may quote them. The nurse narrations were read against the destination
vitals in the timeline.

## The interview matcher

Lexical only. In scope 40 of 52 (77 percent). Six wrong, all six on management-changing
topics:

| Question | Matched | Wanted |
|---|---|---|
| Walk me through how you came off the scooter | onset | mechanism_of_injury |
| Your friend said you went out for a bit, is that right? | orientation | loss_of_consciousness |
| How bad is your head hurting? | chest_pain | headache |
| Is anything wrong with your eyesight? | onset | vision_changes |
| Did you hurt yourself anywhere besides your head? | seizure | other_injuries |
| Do you take any medicines regularly? | past_medical_history | current_medications |

Out of scope refused 17 of 32 (53 percent). Several of the unrefused are answered correctly by
the past medical history topic, which says he has no medical problems. The semantic stage was
not run: huggingface.co was unreachable. The same model wrote the variants and the held-out
file. Nothing was tuned against the held-out file after this run.

## What was run, and what was not

Run, in this order: `build_case.py`, `bind_catalog.py`, `test_packs.py` (SCOOT, then all eight
packs), `matcher_eval.mjs --only SCOOT` (lexical), `build_simulator.py` (full),
`gen_docs.py`, `kit_check.py`. A scripted Playwright play-through against
`build/simulator.html` in the default mode: the intended path, the concussion path through
herniation and rescue, and the do-nothing path. Scripts and screenshots in
`Claude outputs/scoot-playthrough/`.

Regenerated, not edited: `build/`, `site/`, `private-packs/`, `vercel.json`,
`docs/generated/case-index.md`, `SCOOT-case.json`, `SCOOT-binding-map.json`,
`SCOOT-binding.json`, `SCOOT-review-matrix.md`, `SCOOT-deterioration-timeline.md`,
`SCOOT-matcher-tune-questions.json`.

Outside the pack: four tracings were drawn with the ECG generator (read only) by a script in
`Claude outputs/scoot-ecg/`. No shared file was edited. No line was added to `CHANGELOG.md`,
which CLAUDE.md asks a case builder not to open. The owner may add the one line README asks
for.

Not run: the semantic matcher. Not done: the physician's play at 1x, voice orders spoken into
the microphone (the case adds no voice phrases), a named person looking at each tracing
beside its read (authoring 23). At 16x, the end screen shows the herniation vitals still
ramping, because the run ends five simulated seconds after the terminal phase. At 1x the
terminal vitals show for the full five seconds.

## Section 11.5 checklist

Not started. Every line is open.

## Added 19 October 2026: the head CT as images

The head CT result is now the EDH case of the owner's Head CT Teaching Cases artifact, shown
as a still in the record and as a 31-image stack in a new CT viewer (SCOOT-SEED.md 2.12,
authoring 23). The case's numbers were changed to match the images. Run after the change:
`test_packs.py` for all eight packs (all pass, SCOOT 570 engine checks, 103 validator
negative tests), the full build, `gen_docs.py`, `kit_check.py` (0 errors), and a Playwright
check of the viewer: it opens itself when the scan results, the thumbnail and the debrief
thumbnail reopen it, the wheel moves one image a notch, the arrow, Home, End and number keys,
right-drag windowing, zoom, the slider, Escape and the backdrop all work, the twelve-lead still
opens the plain image viewer, there are no console errors, and with the site's
Content-Security-Policy applied there are no violations, at desktop and phone widths. Not run:
`engine/site-check` (Deno is not installed on this machine), and the upload of the larger
private pack. SCOOT's private pack is now about 4.6 MB.
