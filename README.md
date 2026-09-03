# EM Case Simulator

A browser-based emergency medicine case simulator. Free and open source. No backend,
no accounts, no server-side state: the whole product builds to one HTML file.

**Nothing in this repository has been reviewed by a physician.** See Status, below,
before using any of it with a learner.

## Layout

```
engine/     case-agnostic code and tools. No clinical content, no case names.
catalog/    global action and diagnosis catalogs, and their generators.
cases/      one folder per case. CHFE is the reference case; MGCA is the second.
docs/       specification, and decisions/ holding one rationale record per change.
build/      generated. simulator.html and an identical index.html.
```

Nothing in `engine/` names a case. Nothing in `cases/` implements engine behaviour.
If you find an `if` about a specific drug in `engine/`, it belongs in a case file. If
you find condition-parsing or fold logic in `cases/`, it belongs in the engine.

### What is in engine/

| File | What it is |
|---|---|
| `paths.py` | The canonical layout. Every tool resolves a case pack through this |
| `build_simulator.py` | Packs the shell, the catalogs and every case pack into one HTML file |
| `new_case.py` | Scaffolds `cases/<PREFIX>/`, including the seed template |
| `bind_catalog.py` | Resolves a case's binding map against the action catalog |
| `validate_case.py` | Structural and conformance checks. Runs against half-authored cases |
| `sim_runner.py` | Walks the authored scenarios end to end, headless |
| `engine-tests.js` | Case-agnostic engine assertions against a built file |
| `matcher_eval.mjs` | Interview matcher evaluation, with `--semantic --sweep` for thresholds |
| `eval/` | Evaluation sets. Read the `provenance` field in each before quoting a number |
| `shell.html` | The page: markup, the palette, and the layout |
| `engine.js` | The fold, the condition evaluator, the resolvers |
| `ui.js` | Rendering, the panel state machine, the interview matcher |
| `semantic.js` | Optional in-browser embedding model. Loads in the background, may never load |
| `audio.js` | Heartbeat and prompt tones |
| `room-bg.txt` | The blurred room background as a data URI |
| `hero-bg.txt` | The welcome screen photograph as a data URI |
| `avatar-male.txt`, `avatar-female.txt` | Patient silhouettes, used as CSS masks so they follow the theme |

The bundle order in `build_simulator.py` is load-bearing: `semantic.js` declares `SEM`
and `ui.js` registers on it at top level, so reversing them produces a blank page.

## A case pack

A folder under `cases/` whose files share a prefix. For the reference case the prefix
is `CHFE` (congestive heart failure exacerbation):

| File | Authored or generated | What it is |
|---|---|---|
| `CHFE-SEED.md` | authored | The physician's ground truth, authoring section 3 |
| `CHFE-case.json` | authored | The case file |
| `CHFE-binding-map.json` | authored | case id to catalog id, one row per action |
| `CHFE-scenarios.json` | authored | end-to-end paths the simulator walks |
| `CHFE-tests.js` | authored | case-specific engine assertions |
| `CHFE-matcher-eval.js` | authored | interview matcher accuracy on held-out phrasings |
| `CHFE-binding.json` | generated | binding with derived statuses |
| `CHFE-review-matrix.md` | generated | the physician's review artifact |
| `CHFE-review-packet.md` | authored | what the reviewing physician reads first |

A case that uses time-guarded transitions carries one more generated file,
`<PREFIX>-deterioration-timeline.md`: every timed exit with its guard and the prompts
that precede it, the trajectory a resident sees if they do nothing at all, and every
narration line collected to be read against the vitals it introduces. The per-key matrix
cannot show any of that, because it enumerates what a key resolves to in a phase rather
than how the phase was reached. See `cases/MGCA/`.

Migration scripts that were run once against this case live in the pack too, since
their content is case-specific: `restructure_exam.py`, `structure_results.py`.

## Building

```
python3 engine/build_simulator.py
```

Packs **every** case in `cases/` into `build/simulator.html`, and writes the same bytes
to `build/index.html` so `build/` can be served as a site root. Opening it shows a case
picker; with a single case the picker is skipped. Cases share one copy of the catalog,
so a second case costs only the size of its own case file. A case that still has
unresolved build problems is listed and flagged rather than hidden, so a half-authored
case is playable while it is being written.

## Running it as a website

The build is a single self-contained file, so hosting is deployment of one static file.
Two things make that less trivial than it sounds.

**Open it over http, not by double-clicking it.** From a `file://` URL the page renders
and every case is playable, but the browser gives the page an opaque origin, IndexedDB
is unavailable, and the optional embedding model cannot be cached. It will attempt to
download roughly 23 MB on every single page load, or fail outright. Locally:

```
python3 -m http.server 8000 --directory build
# then open http://localhost:8000/
```

**Prefer https for anything beyond localhost.** The model loader caches through the
Cache API, which browsers restrict to secure contexts. `localhost` counts as secure;
a bare LAN address such as `http://192.168.1.20:8000` does not, so the model will work
but re-download on every load. Any static host that terminates TLS solves this:
GitHub Pages, Netlify, Cloudflare Pages, S3 with CloudFront, or an nginx block serving
the directory. There is no build step to configure and nothing to install on the host.

**What needs network access at runtime, and what does not.** The case, the catalogs,
the interface and the lexical interview matcher are all inside the file and need
nothing. There are exactly two outbound requests:

- the optional embedding model (`all-MiniLM-L6-v2`, about 23 MB, from jsDelivr). On a
  network that blocks it the loader gives up, the interface says so, and the simulator
  runs on the lexical matcher alone. This is a deliberate design constraint, not a
  fallback that happens to work: see authoring section 10.6.
- an IBM Plex stylesheet from Google Fonts, purely cosmetic. Blocked, the page falls
  back to the system sans and mono stacks and nothing else changes. Inline the two
  faces if the deployment must make no third-party requests at all.

Verified by loading the built file over http with both hosts blocked: the case renders,
the seven tabs work, and the interview answers, with the matcher chip reading
"Question matching: basic".

**Nothing is stored server-side.** There is no analytics, no telemetry, no submission
endpoint, and no way for one learner's run to reach anyone else. The only browser
storage is the model cache.

## The clock

Through v0.5 the clock governed information and prompting and nothing else, and an
untreated patient never changed. A transition rule may now carry `after_seconds` and
fires when that deadline passes with its guard still true, which is what makes a case
whose lesson is delay authorable at all. Time does not enter the condition language, so
the per-key review matrix is unchanged in shape.

Most cases should not use it. If the lesson is a decision, author it as a tag; if it is
the consequence of an action, author an ordinary transition. Only when the lesson is that
something had to happen sooner does a clock belong in the case. Six validator rules keep
it from becoming a trap, of which the one that matters is that every deterioration must
be preceded by a prompt naming the missing treatment. See
`docs/decisions/time-driven-transitions.md` for what was rejected and why.

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
node    cases/PE/PE-matcher-eval.js
```

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

## Documents

| File | What it is |
|---|---|
| `docs/system-design-v2.md` | The system design. **v0.6 is current** |
| `docs/case-authoring-requirements.md` | What an author must supply. **v0.5 is current** |
| `docs/spec-addendum.md` | Superseded. Its content is folded into the two above |
| `docs/decisions/` | One record per change: why it was made and what was rejected |

`docs/decisions/` holds `time-driven-transitions.md`, `welcome-integration.md`,
`ui-redesign-notes.md`, `arrival-and-history-change.md` and `interview-matching-plan.md`.
They are kept because they record what was rejected, which the current documents state
only as conclusions. They are not a source of truth for how the system behaves.

## Status

Both cases pass the validator with no errors. CHFE walks 13 authored scenarios and passes
91 engine assertions; MGCA walks 26 and passes 118. Each carries one warning, in both
cases about actions the catalog does not hold, which the prototype renders anyway so the
gap stays visible. Those are catalog change requests rather than defects.

That is a structural claim only.

**Nothing here has been reviewed by a physician**: not the reference case, not the
290-entry action catalog, and not the 488-entry diagnosis catalog, which was generated
from model memory with no source consulted. The interface no longer displays that
warning, so `cases/CHFE/CHFE-review-packet.md` is the only place a reader will
encounter it. Read it before using any of this with a learner.

**The interview matcher's accuracy is measured on small sets and the second case scores
badly.** CHFE returns 23 of 25 held-out phrasings correctly; MGCA returns 22 of 37, with
four wrong topics on topics that change management. The two are not comparable, because
CHFE's set is 25 well-formed lay sentences and MGCA's was written deliberately in the
registers that section 10.6 says an author's own set misses. Neither was collected from
residents, so neither characterises how they actually type. Authoring section 10.6 and
`cases/MGCA/MGCA-review-packet.md` section 10 state what the numbers do and do not
support.
