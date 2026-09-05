# EM Case Simulator

A browser-based emergency medicine case simulator. Free and open source. No backend,
no accounts, no server-side state: the whole product builds to one HTML file.

**Nothing in this repository has been reviewed by a physician.** See Status, below,
before using any of it with a learner.

## Layout

```
engine/     case-agnostic code and tools. No clinical content, no case names.
catalog/    global action and diagnosis catalogs, and their generators.
cases/      one folder per case. CHFE is the reference case; MGCA, AFRVR and DIPH follow it.
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
| `validator-tests.py` | Negative tests for the validator: break a clean case one way, assert the rule fires |
| `sim_runner.py` | Walks the authored scenarios end to end, headless |
| `engine-tests.js` | Case-agnostic engine assertions against a built file |
| `matcher_eval.mjs` | Interview matcher evaluation, all packs, against the built file. `--semantic` adds the model, `--sweep` tunes on the tuning sets only |
| `deterioration_timeline.py` | Section 14.2c's artifact for a case that uses a clock |
| `shell.html` | The page: markup, the palette, and the layout |
| `engine.js` | The fold, the condition evaluator, the resolvers |
| `ui.js` | Rendering, the panel state machine, the interview matcher |
| `semantic.js` | Optional in-browser embedding model. Loads in the background, may never load |
| `audio.js` | Heartbeat, nurse tones and the looping ward ambience |
| `room-bg.txt` | The blurred room background as a data URI |
| `hero-bg.txt` | The welcome screen photograph as a data URI |
| `avatar-male.txt`, `avatar-female.txt` | Patient silhouettes, used as CSS masks so they follow the theme |
| `nurse-avatar.txt` | The nurse's portrait, beside the line she speaks. Full colour, not a mask |
| `ambience.txt` | A 45-second ward ambience loop as base64 mp3. Optional; without it the room is silent |
| `assets/` | Sources for the derived assets above, kept so a crop or a recut can be redone |

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
| `CHFE-matcher-eval-questions.json` | authored | held-out phrasings for the interview matcher; never tuned against, always quoted |
| `CHFE-matcher-tune-questions.json` | generated | phrasings withheld from the bank by the variant expansion; thresholds are swept against these |
| `CHFE-binding.json` | generated | binding with derived statuses |
| `CHFE-review-matrix.md` | generated | the physician's review artifact |
| `CHFE-review-packet.md` | authored | what the reviewing physician reads first |

A case that uses time-guarded transitions carries one more generated file,
`<PREFIX>-deterioration-timeline.md`: every timed exit with its guard and the prompts
that precede it, the trajectory a resident sees if they do nothing at all, and every
narration line collected to be read against the vitals it introduces. The per-key matrix
cannot show any of that, because it enumerates what a key resolves to in a phase rather
than how the phase was reached. Generate it with `engine/deterioration_timeline.py`; see
`cases/MGCA/` and `cases/AFRVR/`. Run against a case with no clock it writes a one-line
stub saying so, which is a record that the artifact was checked for rather than
forgotten.

A pack may also hold the scripts that produced its files. `cases/CHFE/` keeps three
one-shot migrations; `cases/AFRVR/` and `cases/DIPH/` each keep `build_case.py` and five
`case_*.py` modules, which is how their case files were written and how they should be
edited. Nothing in
those scripts is derived from anything: they are the JSON in readable Python, so that
changing a deadline or a debrief note is a one-line edit rather than a search through
indented braces.

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
nothing. There are **three** outbound requests, to three different hosts, and the first
two are worth separating because until v0.10 this section ran them together:

- the transformers library, from `cdn.jsdelivr.net`. About 1 MB of JavaScript, and the
  URL is `LIB_URL` in `engine/semantic.js`.
- **the model weights, from `huggingface.co`**, not from jsDelivr. `all-MiniLM-L6-v2` in
  its 23 MB int8 build. `semantic.js` sets `allowRemoteModels` and never sets
  `env.remoteHost`, so the library uses its own default host, which is the Hugging Face
  hub. **A network that allows jsDelivr and blocks huggingface.co therefore fetches a
  megabyte of library and no model**, which is a different failure from the one this
  section used to describe, and a likelier one: hospital networks block model hubs more
  often than they block a general-purpose CDN. Either way the loader gives up, the
  interface says so, and the simulator runs on the lexical matcher alone. That is a
  deliberate design constraint rather than a fallback that happens to work: see
  authoring section 10.6.
- an IBM Plex stylesheet from Google Fonts, purely cosmetic. Blocked, the page falls
  back to the system sans and mono stacks and nothing else changes. Inline the two
  faces if the deployment must make no third-party requests at all.

Verified by loading the built file over http with the hosts blocked: the case renders,
the seven tabs work, and the interview answers, with the matcher chip reading
"Question matching: basic".

**The same two hosts are what `matcher_eval.mjs --semantic` needs**, for the same reason,
so an environment that cannot measure the semantic arm is also an environment where the
shipped page will not load the model. If `--semantic` dies on `getaddrinfo` or a 403 for
`huggingface.co`, that is the answer to both questions at once. Mirroring the weights
onto a host the deployment can reach, and setting `env.remoteHost` to it, is the fix for
a site behind a restrictive network, and it is not built.

**Nothing is stored server-side.** There is no analytics, no telemetry, no submission
endpoint, and no way for one learner's run to reach anyone else. The only browser
storage is the model cache.

## Time, and the five ways to use it

Five constructs touch time, move a number, or count. They are not interchangeable, and
reaching for the wrong one is the mistake this section exists to prevent. The question
that separates them is **what else in the case has to know**.

| Reach for | When | What can read it |
|---|---|---|
| A **phase** | The patient has genuinely changed clinical state | Everything |
| **`after_seconds`** on a transition | The lesson is that something had to happen sooner | Everything, since it changes the phase |
| **`flags_set_timed`** | Something is true for a while and then is not, and the case must react | Everything in the condition language |
| **`vital_effects`** | A number on the monitor moves and nothing else does | Nothing. Display and audio only |
| **`flags_set_repeat`** | The act has to be performed more than once before it works | Everything in the condition language |

An **expiring flag** is the mechanism for something that stops working. The fold removes
the flag when its duration lapses and re-checks transitions, so a case can author "when
the drug is no longer acting, and nothing else was done, deteriorate" and have it fire
with the resident sitting still. A permanent grant of the same flag absorbs a timed one
in either order, a repeat dose extends rather than replaces, and a lapse costs nothing
and appears in no timeline, because it is a thing that stopped being true while the
resident was doing something else.

A **vital effect** moves one number off the phase baseline over `[onset, duration)`, both
measured from the administration. Effects sharing a key do not stack. They are display
and audio only.

**`flags_set_repeat`** is the one exception to flags being permanent from the first dose:
it grants a flag on the Nth administration of an act, which is what a case whose lesson is
"one dose is a trial, two is a treatment" needs and which nothing else can express. The
tally is per counter rather than per button, so a case decides whether two routes to one
act count as two doses. Nothing reads the count directly and nothing ever will, for the
same reason time does not; a case reads it through the flag.

The two are designed to be used together: put the clock in the flag, guard the effect on
the flag, and there is one deadline rather than two that drift apart. Authoring section
6.4 sets out the choice with worked examples; design section 2.9 and authoring 6.5 state
what none of it can do, which is worth reading first, since each of those looks
authorable until it is tried.

## Pausing, and leaving

**A window that loses focus or is hidden pauses the case**, on `visibilitychange` or
`blur`. The clock is wall-clock time and the deadlines a case authors are claims about a
patient, so time spent in another window is subtracted rather than charged. It never
resumes on its own: a case that ran while nobody watched is worse than one that waited, so
resuming is a click on an overlay, and the sound stops and starts with it.

**Leaving is guarded as far as a page is allowed to guard it.** Keyboard refresh and the
back button are interceptable and raise the simulator's own dialog. A click on the
browser's own reload control is not: the only hook is `beforeunload`, whose wording no
browser has let a page choose for over a decade, so that path gets the native dialog
instead. The two look different because the platform makes them different.

## How a case ends, and what the debrief shows first

There are three endings and the interface treats them as three. A harmful action halts the
case immediately and shows its halt reason. A handoff completes it. A time-guarded transition
into a terminal phase, which a case has to opt into explicitly, ends it five seconds later:
the delay is there so the arrest is something the resident watches happen on the monitor
rather than something a debrief informs them of afterwards. Until v0.8 that third ending did
not end anything, and a case that arrested on the clock carried on with a dead patient and a
running timer.

The debrief then opens on a single screen carrying the verdict, *All Critical Actions
Achieved!*, *Critical Actions Missed* or *Case Failed*, the halt or arrest reason where there
is one, and the critical actions that were completed. Nothing else: the missed list, the
summary, the handoff verdict and every teaching note are the answer key, and they sit
behind **Reveal Case Answers** so a resident can replay the case without scrolling past the
answers to reach the button. A run that halted on a harmful action is grouped with the arrest
as *Case Failed* rather than being scored on its critical actions alone.

Behind the reveal, the Summary is seven scores since v0.9: History, Physical, Stabilization,
Interventions, Investigations, Consults and Handoff, each with its arithmetic printed beside
it (critical actions count two, recommended one, a discouraged action costs one, a harmful
action zeroes its tab). The handoff itself takes an ordered list of diagnoses rather than
one, the first being the primary, and the debrief gives each a verdict and lists the ones the
case considers also true of the patient that were not named. Lab panels show their numbers
and nothing else while the case runs; the case's own reading of each panel is printed in the
debrief under *Your results, read*.

## The room

A 45-second loop of ward ambience runs under everything at a very low level, from the
moment a case begins until the moment it ends. **It is the room rather than the patient or
the nurse, so it is gated on neither the monitor nor anything clinical**, and it is silent
everywhere a case is not running: the welcome screen, the splash, and the debrief. That
last one is deliberate. A debrief is reading rather than resuscitating, and a room still
humming under it is the interface not noticing the case is over. The interface says which
of the two situations it is in through `AUDIO.setScene`, at four call sites, and nothing
is inferred from anything else.

It does change one thing that used to be load-bearing: **the room is no longer silent
before the monitor is attached.** What is missing then is the monitor's sound, which is the
point being made, and a ward that was silent until somebody attached a monitor was always
the less truthful half of it.

The asset is derived from the author's recording by `engine/assets/make-ambience.py`, which
records the three decisions in it: where the loop is cut from, why the seam is an
equal-power crossfade rather than a linear one, and why it is peak-normalised, which is
what makes the gain figure in `audio.js` mean something. It is decoded once from base64 in
the page and looped as an `AudioBuffer` with the loop points set a little inside the
buffer, so mp3 encoder padding cannot click. Every failure path ends in a silent room
rather than an error: a case must never fail to start because a decoder disliked an mp3,
and a checkout with no `ambience.txt` builds a working simulator that is 360 KB smaller.

## The heartbeat, and how it is allowed to be uneven

**One beat is a soft beep**: a sine at a fixed frequency under a gated envelope, 8 ms rise,
45 ms held at full gain, 25 ms fall, with a faint octave partial on a shorter window under
it. It used to be a thump, a sine whose pitch fell a major sixth over 140 ms under an
exponential tail, and both halves of that read as percussion. The hold is what makes the
difference: a tone that sustains before it stops is heard as a tone, where one that decays
from its first instant is heard as something being hit. Fixing the pitch also made the
saturation mapping honest, since the perceived pitch of a glide sits somewhere between its
endpoints. The onset stays fast on purpose, because the same sound has to carry the rhythm
below.

The beat is a chain: each beat reads the current rate, saturation and rhythm and schedules
the next one. Exactly one is ever pending. That is what lets the tempo follow the
five-second ramp between phases continuously rather than in quantised steps, and it is
what makes an uneven rhythm expressible at all.

A phase may declare a **`rhythm`**, from a closed vocabulary in `SHARED.audio.rhythm`.
`regular` is the default and is what every phase written before this existed sounds like.
`irregularly_irregular` draws each interval independently as a shifted exponential, so
there is no period for a listener to lock onto, and varies the loudness of each beat with
the interval before it, because a long diastole fills the ventricle more. **The mean is
preserved exactly**, so the rate on the monitor is the true average rate; the spread
narrows at fast rates rather than the floor being clamped, which is what keeps that true.
The ECG trace reads the same field and draws unevenly spaced complexes with no P wave.

The engine holds no association between a rhythm and a diagnosis, exactly as the catalog
holds no appropriateness judgement about a drug. Every parameter is a teaching choice and
the provenance note beside them says so: **no case models a rhythm.** See
`docs/decisions/rhythm-and-the-heartbeat-chain.md` for what was rejected.

## The monitor, and what an action can do to a vital

Two things a resident used to get for free.

**The monitor is dark until they attach one.** Every vital cell reads a dash and there is
no heartbeat until an action carrying the catalog capability `reveals_vitals` has been
taken, which is `attach_monitor` and nothing else. The fold computes the vitals from the
first second and no rule is affected; what is gated is the display. No case can move the
gate, because the capability is a catalog field rather than a case flag. The nurse's
prompt tone is not gated: it is a person speaking rather than equipment.

**An action can move a vital off the phase baseline.** `vital_effects` on a case action
carries a delta, an optional duration, an optional guard in the ordinary condition
language, and a key that decides what does not stack. A phase is entered once and holds,
so it cannot express thirty seconds, cannot express an effect that ends when the drip is
stopped, and cannot express a drug that changes the patient without changing the number
being watched.

Vitals do not enter the condition language, for the same reason time does not. Effects
are display and audio only, exactly as the phase-boundary ramp is.

**The cost is a rebasing, and it is the mistake to expect.** Once an action supplies the
gain, a phase's authored vitals have to be the unsupported baseline or the number is
counted twice. CHFE's `stabilizing` and `improving` therefore carry the arrival
saturation of 87. Validator rule V catches the arithmetic half of that and cannot catch
the clinical half. See `docs/decisions/monitor-gating-and-vital-effects.md`.

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

## A case converted rather than authored

`cases/DIPH/` is the first pack that did not start from a seed written for this platform.
It is a conversion of a complete mannequin-based simulation case and its debriefing guide,
written by Kelly Medwid, MD, and used with her permission. Three things follow that are
worth knowing before converting another one.

**A finished case is not a seed, and a finished case can disagree with itself.** The source
document turned out to be two documents of different vintage bound together, and they
disagreed about the central teaching point: whether physostigmine is warranted in this
patient. Six other contradictions followed, including two sets of vital signs, an ECG
finding described in opposite directions four pages apart, and a chemistry panel whose
bicarbonate is arithmetically impossible beside its own blood gas. **Every one of them had
to be resolved by somebody before the case could be authored at all**, and the seed's job
in a conversion is to record which resolutions came from the author and which are drafting
assumptions. `DIPH-SEED.md` section 9 is that record and it is the first thing to read.

**The mechanics of a mannequin case do not all survive.** This one is run with a confederate
mother who is the only historian, and the engine's interview is patient-facing. It was
converted by having the mother answer in the patient's place with no engine change, which
works and has consequences: the history no longer disappears when the patient's alertness
drops, because the person answering is not the patient. Its four images could not be carried
at all, because a result payload is structured text.

**It exercised constructs no earlier pack had used, and found five gaps in the tooling.**
An unguarded time-guarded transition (authoring 5.1's scheduled natural history), a tag
gated on a study having resulted rather than on a flag, and four vital effects sharing one
key. Section 10 of `DIPH-review-packet.md` lists what each gap was. All five fixes were
verified against the other three packs, which pass unchanged.

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
python3 engine/validator-tests.py cases/PE
node    engine/matcher_eval.mjs --semantic --only PE
python3 engine/deterioration_timeline.py cases/PE
```

**The `--semantic` step needs two things the rest of the chain does not.** The library,
which is `npm install` against the `devDependencies` in `package.json`, and network
access to `huggingface.co` for the weights. Without the library the harness says so and
stops. Without the host it dies on a `getaddrinfo` or a 403 naming huggingface.co, and
that failure is worth reading rather than working around: it means the shipped page will
not load the model on that network either. Run the lexical arm, which needs neither, and
record that the semantic arm was not measured rather than leaving the reader to assume it
was.

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
| `docs/system-design-v2.md` | The system design. **v0.9 is current** |
| `docs/case-authoring-requirements.md` | What an author must supply. **v0.9 is current** (12.1 several diagnoses, 13.0 the seven scores) |
| `docs/spec-addendum.md` | Superseded. Its content is folded into the two above |
| `docs/decisions/` | One record per change: why it was made and what was rejected |

`docs/decisions/` holds `time-driven-transitions.md`, `welcome-integration.md`,
`ui-redesign-notes.md`, `arrival-and-history-change.md`, `interview-matching-plan.md`,
`monitor-gating-and-vital-effects.md` and `rhythm-and-the-heartbeat-chain.md`.
They are kept because they record what was rejected, which the current documents state
only as conclusions. They are not a source of truth for how the system behaves.

## Status

All four cases pass the validator with no errors. CHFE walks 13 authored scenarios,
MGCA 26, AFRVR 31 and DIPH 33. CHFE passes 309 engine assertions, MGCA 319, AFRVR 393 and
DIPH 367, which is the same case-agnostic suite plus each pack's own; each passes 49
validator negative tests. Each carries one warning, in every case about actions the catalog does not
hold, which the prototype renders anyway so the gap stays visible. Those are catalog change
requests rather than defects.

That is a structural claim only.

**Nothing here has been reviewed by a physician**: not the reference case, not the
300-entry action catalog, and not the 488-entry diagnosis catalog, which was generated
from model memory with no source consulted. AFRVR and DIPH are the closest to exceptions
and neither is one: a physician supplied AFRVR's clinical seed, and DIPH is a conversion of
a complete simulation case written by a physician and used with her permission. Everything
expanded from either, including every reference interval and every reference, is unsigned.
DIPH's source document also contradicts itself in seven places, of which three are resolved
by a drafting assumption rather than by its author; they are in `cases/DIPH/DIPH-SEED.md`
section 9 and in section 2 of its review packet. The interface no
longer displays the warning, so the review packets are the only place a reader will
encounter it. Read the one for whichever case you are about to use.

**The interview matcher was measured properly for the first time in v0.8, and then
changed.** On the held-out sets with the embedding model present, in-scope answers went
from 39 to 46 of 52 on AFRVR, 40 to 39 of 46 on CHFE, and 23 to 26 of 37 on MGCA; wrong
topics went from 6, 5 and 6 to 2, 4 and 3; and out-of-scope questions correctly refused
went from 11, 11 and 9 of 30 to 24, 23 and 21. The banks were expanded from a shared
phrasing library, the case gained an out-of-scope bank that both matchers score as a
topic, two lexical precision defects were fixed, and the threshold ladder was replaced by
a per-topic sum whose weights were chosen on withheld tuning sets. Authoring section 10.6
carries the table and what it does not support: none of the questions was collected from
residents.

**v0.9 changed what the debrief scores and what the handoff accepts**, and neither has been
put in front of a resident. The seven category scores are arithmetic over authored tags, so a
case that tags fifteen things recommended on one tab (AFRVR's Stabilization) has diluted its
own critical actions there; the additional-diagnosis lists in all three packs were written by
an AI assistant from the cases' own findings and approved by the author, with the explanations
under them still unsigned; and CHFE's NT-proBNP is a
converted number, marked as such in the case file, that a physician should replace.

**The patient now holds a conversation rather than returning paragraphs.** A follow-up is
answered by the fact it asked about, "anything else?" returns what is untold, a repeated
question gets a short restatement, a marginal match is prefixed with the topic so a wrong
guess is visible, and a question the matcher cannot choose between produces a clarifying
question rather than a coin toss. Facts are authored for eight topics per pack; system
design 20.4 and authoring 10.7 describe the mechanism and its limits.
