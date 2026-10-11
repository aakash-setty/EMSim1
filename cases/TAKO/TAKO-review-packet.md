# TAKO review packet

**Status: drafted by a language model, audited and corrected by models, not reviewed by a
physician, not for learners.** Start with `TAKO-SEED.md`.

## What to read

| File | What it is |
|---|---|
| `TAKO-SEED.md` | What a person decided, what a model chose on 7 October 2026, the seed sections 3.4 to 3.8, timing in both modes, the table of timed-rule races, sources, known limits and 20 open questions |
| `TAKO-review-matrix.md` | Every content key and tag in every state. Read it in full. It does not show prompts, prerequisites, the follow-up, transitions, vital effects or `also_satisfies` |
| `TAKO-deterioration-timeline.md` | Every clock and every nurse line beside the authored vitals of the phase it introduces. It does not add the vital effects. The table below does |
| `TAKO-binding-map.json` | 48 rows. Eight coverage rows are model judgments that several catalog entries are one act. Three rows have no catalog entry |
| `case_1_shell.py` | Phases, transitions, narration, deterioration notes |
| `case_2_actions.py` | Every tag, prompt, prerequisite, vital effect and debrief note, and the follow-up |
| `case_3_content.py` | Findings, results and what each consultant says in each state |
| `case_4_interview.py`, `case_4_variants.py` | Everything she says, and the hand-written phrasings |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points, provenance |
| `TAKO-matcher-eval-questions.json` | The held-out interview questions |
| `TAKO-tests.js`, `TAKO-scenarios.json` | What is pinned |

## Most likely to be wrong

1. The treatment the case rewards. Fluid and avoiding inotropes are in the consensus
   document. The vasoconstrictor is not.
2. The murmur's behavior, which is borrowed from hypertrophic cardiomyopathy.
3. The clocks: 180, 240 and 90 seconds.
4. Every number in the laboratory and imaging results.
5. The model choices of 7 October 2026 in SEED section 0.2, above all that the
   catheterization laboratory will not activate without a twelve-lead that is back.

## Vital effects

Every size, window and guard is a **teaching choice, not a modeled quantity.** No trial
supports any of these figures. "Pressure low" means the obstructed phase and both
worsening shock phases.

| Drug, every route | Moves | By | For how long | Acts where |
|---|---|---|---|---|
| Nitrate or nitroprusside (4 entries) | systolic | minus 12 | 120 s from the dose | every phase except arrival and obstructed |
| Catecholamine inotrope (4 entries) | systolic and rate | minus 14, plus 16 | no end | steadied only, until it is stopped or cardiology has been called |
| Stopping the inotrope (3 entries) | systolic | plus 8 | no end | the inotrope phase only |
| Loop diuretic | systolic | minus 8 | from 20 s to 240 s after the dose | every phase |
| Crystalloid bolus (4 entries) | systolic | plus 6 | 60 s from the bolus | pressure low, with no vasoconstrictor running |
| Phenylephrine or vasopressin | systolic | plus 8 | no end | pressure low, with no fluid given |
| Norepinephrine | rate | plus 6 | no end | every phase |
| Beta blocker (5 entries) | systolic and rate | minus 10, minus 10 | 180 s from the dose | every phase except steadied |
| Beta blocker (5 entries) | rate | minus 14 | no end | steadied only |

What moves nothing on purpose: aspirin, heparin, clopidogrel, the opioids, lorazepam and
thrombolysis. Norepinephrine alone moves no pressure, and its note does not say why (open
question 9). A nitrate given in the obstructed phase moves nothing there (SEED section 7,
limit 1).

How these were checked. `TAKO-tests.js` folds every timed narration on a route with each
of these drugs acting, one extra drug at a time, and compares each claim about a
direction with the monitor just before and just after the line: 140 routes. No narration
quotes a figure. The ECG report quotes no rate. No finding quotes a vital sign.

## The interview matcher

Measured on 7 October 2026 with `node engine/matcher_eval.mjs --only TAKO`, lexical stage
only, on `TAKO-matcher-eval-questions.json`: 56 in-scope questions and 30 out-of-scope.

**The same model wrote the variant bank and the held-out set**, which authoring 10.6 warns
against, so these numbers flatter the matcher. The file was written on 7 October 2026
before the bank was expanded again that day, and a script confirmed that no question
matched any bank, tuning set or shared phrasing. The pack's first expansion, on 6 October
2026, ran with no held-out file. Nothing was tuned against this set, and it must never be.

| | Result |
|---|---|
| In-scope correct | 37 of 56 (66 percent) |
| Wrong topic | 6 |
| Partial (one of two topics in a compound question) | 1 |
| Right topic plus an extra answer | 8 |
| Fell through to the fallback | 4 |
| Asked to clarify | 0 |
| Out-of-scope refused | 18 of 30 (60 percent) |
| By register, correct | paraphrase 21 of 30, shorthand 10 of 13, typed with errors 4 of 5, conversational 1 of 5, compound 1 of 3 |

**Wrong topic on a management-changing topic, by name** (the harness counts a pertinent
negative as management-changing):

| Question | Answered by | Wanted |
|---|---|---|
| Has anyone in the family passed away recently? | `family_history` | `what_she_was_doing` |
| Are you struggling to catch your breath? | `leg_swelling_and_lying_flat` | `breathing` |
| Do you take a daily aspirin? | `bleeding_risk` | `current_medications` |
| clammy/sweaty at onset? | `onset` | `sweating` |
| tearing CP to back? | `chest_pain` | `back_or_tearing_pain` |
| Okay, and before all this started, what had your day been like? | `cough_sore_throat` and `social_history` | `what_she_was_doing` |

The first and the last matter most. The emotional trigger is the frame of the case, and
two natural ways of asking for it get an answer about her father or her cough. The third
is a safety question: asked about aspirin, she answers about blood thinners and never
says she takes none.

Fell through: "What was happening right before the pain hit?" (`what_she_was_doing`),
"Can you put a finger on the spot that hurts?", "Has a doctor put you on a pill to stop
clots?" (`bleeding_risk`), "dyspneic?".

Out-of-scope questions answered anyway (12): joints, rashes, sleep apnea, a fit, hearing,
tetanus boosters, cold sores, a cat or a dog, voting, her phone number, other languages,
her car.

**The semantic stage was not run.** These are the numbers a learner gets before the
embedding model loads, or if it never does.

## Tests

Taken from the last run on 7 October 2026, not from memory.

| Tool | Result |
|---|---|
| `validate_case.py TAKO` | 0 errors, 1 warning. The warning names the three actions with no catalog entry: `chest_rechecked`, `consult_activate_cath_lab`, `handoff_submit`. It stays for good |
| `engine-tests.js` with `TAKO-tests.js` | 916 checks, all passed. 382 of them are this pack's own assertions |
| `sim_runner.py TAKO` | 32 of 32 scenarios |
| `validator-tests.py cases/TAKO` | 76 checks, all passed |
| `deterioration_timeline.py TAKO` | written |
| `matcher_eval.mjs --only TAKO` | above |
| One scripted browser play-through, Playwright, `build/simulator.html`, default mode | 35 of 35 checks, no page errors |

The play-through followed the intended path with real clicks: monitor, line, ECG, a
catheterization laboratory press refused while the tracing printed, aspirin, the
activation spoken as "code stemi" through the voice box, examinations, echo, film,
troponin, a venous gas and a capillary glucose, three interview questions, the fall at
180 seconds, the default-mode cardiology prompt at 240, the cardiology call, fluid and
phenylephrine, the steadied phase, a chest examination after the bolus, two steadied
answers, the handoff with three diagnoses, and the debrief.

## What the tests cannot cover, and what was not run

- **No physician has read anything.** Passing every check is a structural claim.
- The semantic stage of the matcher.
- The site check and the deployed build.
- The other six packs' tests. Nothing they read was changed except one line of this
  pack's own cover tags.
- A browser play-through of the wrong-drug and deterioration branches. They are folded
  in the engine tests and walked in the scenarios, and were not clicked through.
- Easy mode in the browser.
- The microphone. The eleven spoken phrases were tried through the parser and one through
  the voice text box.
- Three drugs acting at once on a narration (SEED section 7, limit 8).
- Whether the image the monitor draws matches the ECG report.

Section 14.3 checklist: not started.
