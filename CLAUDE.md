# Start here

This is EMSim, a browser emergency medicine case simulator. Agent tools load this file
first. It says what to read for each kind of work and what not to open. `README.md` says
how the repository is put together. Where this file and `README.md` disagree, `README.md`
is right. Both are kept short on purpose: the files they point to are the authority.

## If you are building a new case

Read, in this order, and in full:

1. `docs/case-design-guide.md`. What a case is for, and what we refuse.
2. `docs/case-authoring-requirements.md`. The rules. Section 0, then section 16, then
   the rest as section 16 points into it.
3. `README.md`, the sections "Trust", "Working on a case" and "Things that have gone
   wrong before".
4. `docs/generated/field-reference.md`. Every case field, who reads it, what the learner
   sees. Read it once; look fields up in it after that.
5. `docs/generated/action-index.md`. One line per catalog entry. What the learner can
   order, and the ids a case binds.
6. `docs/generated/case-index.md`. The library, one line per case, so you can say how
   yours differs.

Then look things up, do not read whole files:

- `python3 engine/lookup.py action <word>`, `diagnosis <word>`, `field <word>`,
  `mechanism <word>`, `prereq <id>`, `flags`. Add `--full` for the whole catalog entry.
- `docs/generated/mechanism-index.md` names one worked example per engine mechanism, by
  file and line. Open that file at that line, not the whole pack.
- The case file format: until the scaffold lands (restructure step 3), copy the layout of
  `cases/DKA` (`build_case.py` plus `case_1_shell.py` to `case_5_handoff.py`). Read its
  `case_*.py` files once. The interview bank is expanded at build time from `TOPIC_MAP`
  in `case_4_interview.py`, so nothing generated sits in those files.

Do not open, to build a case: `CHANGELOG.md`, `docs/system-design-v2.md`,
`docs/readme-reference.md`, `docs/spec-addendum.md`, `docs/decisions/`, `cases/review/`,
`engine/*.js`, `engine/validate_case.py`, `catalog/*.json` (use the index and the lookup),
or any pack's `*-case.json`, `*-binding.json`, `*-review-matrix.md` or
`*-deterioration-timeline.md` other than your own. If a question is not answered by
the files in the list above, record it in the pack's SEED as an open question rather than
reading the engine to settle it, and say so in your handoff. That gap is a defect in the
documents, and recording it is how it gets fixed.

Build chain, test duties and the interview phrasing steps: `README.md`, "Working on a
case". Run `python3 engine/kit_check.py` before you hand over.

## If you are changing the engine, the catalog or the tooling

Read `README.md` in full, then `docs/system-design-v2.md` for the part you are changing,
then `docs/decisions/` for any decision that touches it. After the change, run the tests
for every pack (README, "Working on a case"), and if the change adds or alters anything a
case author can write, update `docs/case-authoring-requirements.md` in the same delivery
and run `python3 engine/kit_check.py`.

## If you are restructuring the repository

`docs/restructure-plan.md` first. It holds the goal, the decisions taken, the steps, and
what must not be run.

## Always

- Nothing in `engine/` names a case, a drug or a diagnosis. Nothing in `cases/`
  implements behavior. A new case touches only its own folder (`engine/kit_check.py`
  checks `engine/` and `catalog/` for per-case tables).
- Nothing clinical here has been reviewed by a physician unless a SEED names the
  decision, the person and the date. Say so in anything you write.
- Plain, direct, short sentences. US spelling. No em dashes, no semicolons, and never the
  words "quiet" or "quietly".
- From a sandbox on the owner's machine: do not run `git`. The owner commits.
