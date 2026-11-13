# SWEET review packet

**Status: drafted by a language model, not reviewed, not for learners. Sign-off: not started.**

Case 11, prefix SWEET, `sweet-anaphylaxis-01`. Refractory anaphylaxis to peanut in a
12-year-old boy, 40 kg, after one IM dose from the ambulance crew. Built 11 November 2026 from
Aakash Setty's case structure and his answers. Revised 13 November 2026 on his instruction: the
infusion runs 10 seconds after the order, the first ED IM dose lasts 60 seconds, and the
critical actions were rewritten.

## Files to read

1. `SWEET-SEED.md`: what a person decided, the critical actions (2a), stories, races, known
   gaps, open questions.
2. `SWEET-review-matrix.md`: every content key in every state. Read in full.
3. `SWEET-deterioration-timeline.md`: the clock, the prompts, the do-nothing path.
4. `case_1_shell.py` to `case_5_handoff.py`: the sources. `SWEET-case.json` is generated.
5. `media/README.md`: where each tracing came from.
6. The case map artifact, revision 4, for the design and the owner's decisions.

## Counts from the last run (13 November 2026)

- `engine/test_packs.py SWEET`: engine 650 checks, all passed. Scenarios 7 of 7. Validator 0
  errors, 2 warnings (the oxygen mask's zero delta, on purpose, and the 11 case-only actions,
  expected). Validator mutation tests 145, all passed. Timeline written.
- `engine/build_simulator.py`: all eleven packs built into `build/` and `site/`. SWEET: 68 bound
  actions, 11 case-only.
- `engine/gen_docs.py`: case index regenerated. `engine/kit_check.py`: 0 errors, 64,725 of
  65,000 tokens.
- Matcher, lexical only, last run 11 November 2026 (the interview has not changed since except
  one answer rule's phase list): in-scope 22 of 31 (71%), out-of-scope refused 21 of 30 (70%).
  Wrong on a management-changing topic: "How long ago was the shot in his leg?", "hx asthma?",
  "Does he ever need a puffer?", "Was there anything with nuts in it?". The semantic matcher was
  not run.

## Teaching choices, not measurements

- The first ED IM dose: full 10 to 40 s, two thirds to 50 s, one third to 60 s (heart rate +6,
  systolic +12, diastolic +8, respiratory rate -4, saturation +2 at full). A later dose: full to
  25 s, gone at 40 s (+4, +8, +4, -2, +1).
- The 60-second response and the 10-second infusion (owner's), the 150 and 240-second phase 2
  exits, the phase 3, relapse and phase 4 clocks, the 30-second rescue, the 120-second relapse
  after a stop.
- Every other vital effect: boluses, posture (+5 systolic), IV push, albuterol, oxygen devices.
- Every phase's vitals outside S1 to S6.

## What was not run

- A physician play-through at 1x in the default mode (section 11.5).
- The builder's scripted browser run at 4x (13 November 2026): the dose acting at 10 s and
  fading, the worn-off narration at 60 s, the infusion running 10 s after the order, no page
  errors. The History tab, the exam panels and the debrief were not looked at in the browser.
- `engine/test_packs.py` for the other ten packs after this revision. Nothing in `engine/` or
  `catalog/` changed in it.
- Spoken orders through the microphone.

## Physician questions

SWEET-SEED.md section 7.
