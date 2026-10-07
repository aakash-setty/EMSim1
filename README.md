# EMSim

A browser-based emergency medicine case simulator. The learner is the doctor, the patient
responds to what they do, and a debrief explains it afterwards. Proprietary and freemium.
See `LICENSE`.

**This file is written for an AI agent picking up the repository cold.** It says how the
project is put together, what must stay true, and how to work in it. It deliberately holds
no case list, no counts and no version history, because those go stale. Where it and
another file disagree, the other file is right:

| Question | Where the answer is |
|---|---|
| What changed, and when | `CHANGELOG.md` |
| How the engine behaves | `docs/system-design-v2.md` |
| What a case must contain, and the rules for writing one | `docs/case-authoring-requirements.md` |
| What makes a case worth building | the "EMSim case design guide" (a Claude Doc in the project, not in this repository) |
| Why a past decision was made and what was rejected | `docs/decisions/` |
| How the site is deployed and who can see what | `docs/deployment.md` |
| Detail on the room, audio, monitor trace, hosting and network requests | `docs/readme-reference.md` (the previous README, kept as reference and not maintained) |
| What a specific case is, and who wrote which part of it | `cases/<PREFIX>/<PREFIX>-SEED.md` and its review packet |

## Trust

Assume nothing clinical here has been reviewed by a physician unless a case's SEED file
names the decision, the person and the date. The catalogs and most case content were
written by language models. Passing every test is a structural claim only. Do not describe
any case as validated, and do not use one with learners until its sign-off checklist
(authoring requirements 14.3) is complete.

When you write clinical content: say in the case's provenance block that a model wrote it,
mark unchecked references `[UNVERIFIED]`, and list what needs a physician's signature. Never
present a teaching choice (a deadline, the size of a vital sign change) as a measured
quantity.

## Layout

```
engine/         case-agnostic code and tools. No clinical content, no case names.
catalog/        global action and diagnosis catalogs, and the scripts that generate them.
cases/          one folder per case (a "case pack"), files sharing an upper-case prefix.
docs/           specification, decisions, deployment.
build/          generated. Local build with every case inlined. Committed, never deployed.
site/           generated. Deployed build: engine and case list only.
private-packs/  generated, not committed. One JSON per case for the private bucket.
supabase/       SQL and the edge function for access control.
```

Two rules hold the design together:

- **Nothing in `engine/` names a case, a drug or a diagnosis.** If the engine needs a new
  behavior, add a general mechanism that a case opts into, and document it.
- **Nothing in `cases/` implements behavior.** A case is data.

List what exists instead of trusting any list written down: `ls cases`, `ls engine`,
`python3 engine/paths.py`.

## How a case runs, in five lines

1. A case moves through authored **phases**. Each has fixed vital signs.
2. Actions come from one global **catalog**. A case binds the ones it cares about and gives
   each a tag (critical, recommended, discouraged, harmful, neutral), flags and a note.
3. One **condition language** (phase, flag, study, action) decides every transition, tag,
   finding, result and patient answer. There is no arithmetic and no time predicate.
4. Time acts only through deadlines authored on transitions, prompts and follow-ups.
5. The whole state is recomputed from the action log on every tick (a fold). Nothing is
   stored between ticks.

Read authoring requirements section 0 before touching a case, and section 6.4 before using
anything that involves time.

## Working on a case

Some packs keep their case file as Python sources (`build_case.py` plus `case_*.py`) and
generate the JSON. **If a pack has a `build_case.py`, edit the Python and never the JSON.**
Otherwise edit the JSON.

The chain, in order, for a pack `XX`:

```
python3 cases/XX/build_case.py cases/XX        # only if the pack has one
python3 engine/bind_catalog.py cases/XX
python3 engine/validate_case.py XX             # also writes the review matrix
python3 engine/build_simulator.py              # every case, into build/ and site/
node    engine/engine-tests.js build/simulator.html cases/XX/XX-tests.js XX
python3 engine/sim_runner.py XX
python3 engine/validator-tests.py cases/XX
python3 engine/deterioration_timeline.py XX
node    engine/matcher_eval.mjs                # add --semantic if huggingface.co is reachable
```

After any change to `engine/` or `catalog/`, run the tests for **every** pack, not only
the one you were working on.

New case: `python3 engine/new_case.py XX "Title"` scaffolds a pack that fails validation
on purpose. The error list is the to-do list. Authoring requirements section 16 is the
full sequence. Add the pack's topic map to `catalog/expand_interview_variants.py` and run
it to generate interview phrasings.

Catalogs are generated. Edit the generator and regenerate:

```
python3 catalog/build_catalog.py   > catalog/action-catalog.json
python3 catalog/build_diagnoses.py > catalog/diagnosis-catalog.json
python3 catalog/build_voice_aliases.py
```

## Things that have gone wrong before

- **Tests log whole seconds. The browser clock does not.** A timing fault that only shows
  with fractional times passed every suite. Use fractional times in new timing tests.
- **Only playing a case in a browser finds interface faults.** The validator, the scenario
  runner and the engine tests all read data. Script a play-through with Playwright against
  `build/simulator.html` for any change a learner would see.
- **Anything a case does not author returns a normal default, with no error.** A forgotten
  study teaches the wrong thing confidently. Check the review matrix.
- **Flags are permanent and rule lists are first-match.** Put phase rules before flag rules.
- **A prompt's text is one string used in every phase it fires in.** Do not quote a vital
  sign in it.
- **Nurse narration on a timed transition must match the destination phase's numbers.**
- **Instant transitions are re-checked only after a state-changing action or a clock
  event.** Exams and interview questions do not trigger them.
- **Held-out matcher questions are never tuned against.**
- **The scenario runner (`sim_runner.py`) is a second implementation.** It can agree with
  itself and disagree with the engine. The engine tests are the authority.

## Working from a sandbox on the owner's machine

- Do not run `git` there. It can leave a lock file it cannot remove. The owner commits.
- Files cannot be deleted, and `tar` cannot overwrite. Write over a file with
  `cat new > old`.
- `Claude outputs/` is ignored by git and is the place for scratch files.
- State what you ran and what you did not. Unrun checks are listed, not implied.

## Writing style for anything a learner or the owner reads

Plain, direct, short sentences. US spelling. No em dashes, no semicolons, and never the
words "quiet" or "quietly". The nurse and the debrief speak as one doctor to another.
Findings in results, interpretation in the debrief.
