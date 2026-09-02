# EM Case Simulator

Case-agnostic engine, global catalogs, and one case pack per case.

## Layout

```
engine/     case-agnostic code and tools. No clinical content, no case names.
catalog/    global action and diagnosis catalogs, and their generators.
cases/      one folder per case. CHFE is the reference case.
docs/       specification.
build/      generated prototypes.
```

Nothing in `engine/` names a case. Nothing in `cases/` implements engine behaviour.
If you find an `if` about a specific drug in `engine/`, it belongs in a case file. If
you find condition-parsing or fold logic in `cases/`, it belongs in the engine.

## A case pack

A folder under `cases/` whose files share a prefix. For the reference case the prefix
is `CHFE` (congestive heart failure exacerbation):

| File | Authored or generated | What it is |
|---|---|---|
| `CHFE-SEED.md` | authored | The physician's ground truth, section 3 |
| `CHFE-case.json` | authored | The case file |
| `CHFE-binding-map.json` | authored | case id to catalog id, one row per action |
| `CHFE-scenarios.json` | authored | end-to-end paths the simulator walks |
| `CHFE-tests.js` | authored | case-specific engine assertions |
| `CHFE-matcher-eval.js` | authored | interview matcher accuracy on held-out phrasings |
| `CHFE-binding.json` | generated | binding with derived statuses |
| `CHFE-review-matrix.md` | generated | the physician's review artifact |
| `CHFE-review-packet.md` | authored | what the reviewing physician reads first |

Migration scripts that were run once against this case live in the pack too, since
their content is case-specific: `restructure_exam.py`, `structure_results.py`.

## Adding a case

```
python3 engine/new_case.py PE "Acute pulmonary embolism"
```

That writes `cases/PE/` with a skeleton and a seed template listing the 14 exam
maneuvers and the finding-routing map. The skeleton deliberately fails the validator;
the error list is the authoring to-do list.

Then, in order:

```
python3 engine/bind_catalog.py   cases/PE
python3 engine/validate_case.py  cases/PE
python3 engine/build_simulator.py
python3 engine/sim_runner.py     cases/PE
node    engine/engine-tests.js   build/simulator.html cases/PE/PE-tests.js PE
```

`build_simulator.py` packs **every** case in `cases/` into one `build/simulator.html`.
Opening it shows a case picker; with a single case the picker is skipped. Cases share
one copy of the catalog, so a second case costs only the size of its own case file.
A case that still has unresolved build problems is listed and flagged rather than
hidden, so you can play a half-authored case while you write it.

Every tool takes a case pack and defaults to the only one present. None of them
needs editing to accept a new case.

Then read `PE-review-matrix.md` in full, play the case start to finish, and complete
the sign-off checklist in `docs/case-authoring-requirements.md` section 14.3.

## Regenerating the catalogs

```
python3 catalog/build_catalog.py   > catalog/action-catalog.json
python3 catalog/build_diagnoses.py > catalog/diagnosis-catalog.json
```

The action catalog checked in here was regenerated from `build_catalog.py`; an earlier
copy was stale and missing the exam defaults and the routing map.

## Status

The reference case passes the validator with no errors. That is a structural claim only.

**Nothing here has been reviewed by a physician**: not the reference case, not the 290-entry
action catalog, and not the 488-entry diagnosis catalog, which was generated from model memory
with no source consulted. The interface no longer displays that warning, so
`cases/CHFE/CHFE-review-packet.md` is the only place a reader will encounter it. Read it before
using any of this with a learner.
