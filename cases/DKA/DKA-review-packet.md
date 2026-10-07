# DKA review packet

**Status: drafted by a language model, not reviewed, not for learners.** Start with
`DKA-SEED.md`.

| File | What it is |
|---|---|
| `DKA-SEED.md` | Decisions, sources and how far each was read, goals, phases, what the check changed |
| `DKA-deterioration-timeline.md` | Every timed rule and every nurse line beside the vitals it introduces |
| `DKA-review-matrix.md` | What every result and finding resolves to in every state |
| `case_2_actions.py` | Every tag and debrief note |
| `case_3_content.py` | Findings, results and what the consultants say |
| `case_4_interview.py` | Everything she says |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points |

## Most likely to be wrong

1. The potassium in each state, and that insulin at 3.1 produces weakness and ectopy at 2.6.
2. The level of care. The consensus report's table suggests less than step-down for mild
   ketoacidosis. This case argues the potassium moves her up.
3. The quotations from the consensus report, which came through a summarizing tool.
4. The two delays, 10 and 20 seconds, and what the nurse says they stand for.
5. Every number in the laboratory and ECG results.

## Tests

20 scenarios, 555 engine checks, 76 validator tests, validator 0 errors and 1 warning. One
scripted browser play-through: early subcutaneous insulin, the rescue, the restart, the
dextrose plan, handoff and debrief. Interview matcher, lexical only, on a held-out set
written by the same author: 41 of 52 in scope, 4 wrong topic, 18 of 30 out of scope refused.

Section 14.3 checklist: not started.
