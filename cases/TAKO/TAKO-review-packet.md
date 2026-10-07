# TAKO review packet

**Status: drafted by a language model, not reviewed, not for learners.** Start with
`TAKO-SEED.md`.

| File | What it is |
|---|---|
| `TAKO-SEED.md` | Decisions, phases, what the fact-check changed, open questions |
| `TAKO-deterioration-timeline.md` | Every clock and every nurse line beside the vitals it introduces |
| `case_2_actions.py` | Every tag and debrief note |
| `case_3_content.py` | Findings, results and what the cardiologist says in each state |
| `case_4_interview.py` | Everything she says |
| `case_5_handoff.py` | Dispositions, diagnoses, teaching points |

## Most likely to be wrong

1. The treatment the case rewards. Fluid and avoiding inotropes are in the consensus
   document. The vasoconstrictor is not.
2. The murmur's behavior, which is borrowed from hypertrophic cardiomyopathy.
3. The clocks: 180, 240 and 90 seconds.
4. Every number in the laboratory and imaging results.

## Tests

23 scenarios, 560 engine checks, 76 validator tests, validator 0 errors. One scripted
browser play-through: the case-only button, an inotrope, the fall, a cardiology call,
handoff and debrief. No interview matcher evaluation was written for this pack.

Section 14.3 checklist: not started.
