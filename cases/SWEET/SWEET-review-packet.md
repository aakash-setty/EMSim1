# SWEET review packet

**Status: drafted by a language model, not reviewed, not for learners. Sign-off: not started.**

Case 11, prefix SWEET, `sweet-anaphylaxis-01`. Refractory anaphylaxis to peanut in a
12-year-old boy, 40 kg, after one IM dose from the ambulance crew. Built 11 November 2026 from
Aakash Setty's case structure and his answers the same day.

## Files to read

1. `SWEET-SEED.md`: what a person decided, goals, stories, races, known gaps, open questions.
2. `SWEET-review-matrix.md`: every content key in every state. Read in full.
3. `SWEET-deterioration-timeline.md`: the clock, the prompts, the do-nothing path.
4. `case_1_shell.py` to `case_5_handoff.py`: the sources. `SWEET-case.json` is generated.
5. `media/README.md`: where each tracing came from.
6. The case map artifact, revision 3, for the design and the owner's decisions.

## Counts from the last run (11 November 2026)

- `engine/test_packs.py SWEET`: engine 638 checks, all passed. Scenarios 7 of 7. Validator 0
  errors, 2 warnings (the oxygen mask's zero delta, on purpose: it replaces the other devices'
  effects under one key; and the 11 case-only actions, expected). Validator mutation tests 145,
  all passed. Timeline written.
- `engine/test_packs.py` for the other ten packs: all pass (run after the engine-tests change).
- `engine/build_simulator.py`: all eleven packs built into `build/` and `site/`. SWEET: 68 bound
  actions, 11 case-only.
- `engine/gen_docs.py`: case index regenerated with case 11, field reference regenerated.
- `engine/kit_check.py`: 0 errors, 0 warnings, 64,724 of 65,000 tokens.
- Matcher, lexical only (`node engine/matcher_eval.mjs --only SWEET`): in-scope 22 of 31 (71%),
  wrong 4, fell through 4, extra 1, out-of-scope refused 21 of 30 (70%). Wrong on a
  management-changing topic: "How long ago was the shot in his leg?" (went to onset), "hx
  asthma?" (heart history), "Does he ever need a puffer?" (surgical history), "Was there
  anything with nuts in it?" (allergies). The other packs range from 66% to 88% in scope. The
  held-out file and the variant bank were written by the same model and the held-out file was
  not tuned against. The semantic matcher was not run.

## Teaching choices, not measurements

- The first ED IM dose: acts at 10 s, full to 80 s, two thirds to 100 s, one third to 120 s
  (heart rate +6, systolic +12, diastolic +8, respiratory rate -4, saturation +2 at full). A later
  dose: full to 40 s, fading to nothing at 60 s (+4, +8, +4, -2, +1).
- The 120-second response, the 150 and 240-second phase 2 exits, the infusion preparation (60 s
  with help, 120 without; 60 and 90 in phases 3 and 7), the phase 3 and 4 clocks, the 30-second
  rescue.
- Every other vital effect: boluses, posture (+5 systolic), IV push, albuterol, oxygen devices.
- Every phase's vitals outside S1 to S6.

## What was not run

- A physician play-through at 1x in the default mode (section 11.5).
- A scripted play-through by the builder at 8x with Playwright, actions entered through the
  engine's log rather than clicks: the child figure, the splash (BP, saturation and respiratory
  rate red for age), the 10-second response and fade on the monitor, the worn-off narration at
  120 s, the PICU reply, the infusion running 60 s after the order with help, the arrival prompt
  at 95 s in normal mode, and a smaller, shorter second dose. No page errors. The History tab,
  the exam panels and the debrief were not looked at in the browser.
- Spoken orders through the microphone.

## Physician questions

SWEET-SEED.md section 7.
