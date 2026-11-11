# ALLEY review packet

**Status: drafted by a language model, not reviewed, not for learners. Sign-off: not started.**

Case 10, prefix ALLEY, `alley-intoxicated-01`. Methanol poisoning from windshield washer fluid
in a 52-year-old man brought in to sleep it off. Built 11 November 2026 from Aakash Setty's case
structure and his answers the same day.

## Files to read

1. `ALLEY-SEED.md`: what a person decided, goals, stories, races, known gaps, open questions.
2. `ALLEY-review-matrix.md`: every content key in every state. Read in full.
3. `ALLEY-deterioration-timeline.md`: the clock, the prompts, the do-nothing path.
4. `case_1_shell.py` to `case_5_handoff.py`: the sources. `ALLEY-case.json` is generated.
5. `media/README.md`: where each picture came from.
6. The case map artifact, revision 2, for the design and the owner's decisions.

## Counts from the last run (11 November 2026)

- `engine/test_packs.py ALLEY`: engine 606 checks, all passed. Scenarios 11 of 11. Validator 0
  errors, 1 warning (the 11 case-only actions, expected). Validator mutation tests 145, all
  passed. Timeline written.
- `engine/build_simulator.py`: all ten packs built into `build/` and `site/`. ALLEY: 54 bound
  actions, 11 case-only.
- `engine/gen_docs.py`: case index regenerated with case 10.
- `engine/kit_check.py`: 0 errors, 0 warnings. The case-building kit is at 64,995 of its 65,000
  token budget.
- Matcher, lexical only (`node engine/matcher_eval.mjs --only ALLEY`): in-scope 27 of 32 (84%),
  wrong 3, fell through 2, out-of-scope refused 6 of 6. Wrong on a management-changing topic:
  "Did you drink something other than booze?" went to last oral intake, and "What exactly was
  in the jug?" went to location of pain, both wanted the drink topic. The held-out file and the
  variant bank were written by the same model. The semantic matcher was not run.

## Teaching choices, not measurements

- The tier clock (360 seconds, then 180), the 180-second bicarbonate window, the 150-second sedation overlay, the
  5-second "time away" move.
- Every vital effect: bicarbonate (to HR 104, BP 130/82, RR 24), fluid (HR minus 5), sedation
  (RR minus 6, systolic minus 8, diastolic minus 4, saturation minus 2).
- The fixed buffered and improving gases.

## What was not run

- A physician play-through at 1x in the default mode (section 11.5).
- A scripted play-through of the treatment path in the interface. The builder checked the case
  list, the splash, the room and the History tab in the built simulator with Playwright: no page
  errors, and the drink, blue-stuff, vision and intent answers came back as authored.
- `engine/test_packs.py` for the other nine packs. Nothing in `engine/` or `catalog/` changed.
- `CHANGELOG.md` was not given a line for the case: section 13 says nothing outside the pack is
  edited for a case. The owner may add one.

## Physician questions

ALLEY-SEED.md section 7.
