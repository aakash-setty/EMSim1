# Welcome screen, and v0.6 time transitions in the engine

**Applied.** These edits are in `engine/` and `build/simulator.html` is generated from
them, so this document is now the rationale record rather than a to-do list. It was
originally written the other way round, against a patched build, because the engine
sources had not been shared at the time.

Three things were found only once the real sources were in hand, and they are recorded
in section 6 rather than here: the prompt cap silently suppressing the prompts that a
deterioration depends on, the equivalence group duplicating a prompt across every
covered entry, and a generic engine assertion that encoded the pre-v0.6 invariant.

## What changed, in one paragraph

The case picker became the welcome screen. It keeps the id `picker`, which means
`chooseCase()`, `backToPicker()` and the `[data-case]` click delegation all work
unchanged: selecting a case still hides `#picker` and shows `#splash`, and the
splash's existing `#backtopicker` control still comes back. The engine also gained
time-guarded transitions, because the MGCA pack uses them and a v0.5 engine reads
`after_seconds` rules as instantaneous, which would fire MGCA's first deterioration
on the resident's first action.

## Files

| File | Change |
|---|---|
| `engine/shell.html` | font link, welcome CSS, `#picker` markup, splash back control |
| `engine/ui.js` | `renderPicker()` replaced, `backToPicker()` amended |
| `engine/engine.js` | time-guarded transitions in the fold |
| `engine/hero-bg.txt` | new, base64 of the hospital illustration |
| `engine/avatar-male.txt`, `engine/avatar-female.txt` | new, base64 silhouette masks |
| `cases/CHFE/CHFE-case.json` | two new card fields |
| `cases/MGCA/` | new pack |

---

## 1. engine.js: time-guarded transitions

Four edits in `fold()`. This is the only part of the change that touches case
behaviour, and it is the part to review closely.

**1.1 Two new pieces of fold state.** Find the `st` initialiser and add:

```js
guardTrue:{}, timeFires:[]
```

`guardTrue` records when a `measured_from: "guard_true"` rule first became true.
`timeFires` is what the debrief reads to say which deadline expired.

**1.2 Replace `checkTransitions`:**

```js
function transitionDue(tr,idx,t){
  if(tr.after_seconds===undefined) return true;
  if((tr.measured_from||'phase_entry')==='guard_true'){
    const k=st.phase+'|'+idx;
    if(st.guardTrue[k]===undefined) st.guardTrue[k]=t;
    return t-st.guardTrue[k] >= tr.after_seconds;
  }
  return t-(st.phaseEntry[st.phase]||0) >= tr.after_seconds;
}
function checkTransitions(t){
  const p=PHASE[st.phase];
  if(!p||!p.transitions) return;
  for(let i=0;i<p.transitions.length;i++){
    const tr=p.transitions[i];
    if(!test(tr.when,st)) continue;
    if(!transitionDue(tr,i,t)) continue;
    if(tr.to!==st.phase){
      if(tr.after_seconds!==undefined && tr.narration) narrate(t,tr.narration,'deterioration');
      if(tr.after_seconds!==undefined) st.timeFires.push({t,from:st.phase,to:tr.to,
        after:tr.after_seconds,when:tr.when,note:tr.debrief_note||''});
      enterPhase(tr.to,t);
    }
    return;
  }
}
```

The ordered list and first-match-wins are unchanged. A rule without
`after_seconds` behaves exactly as before, so a case that authors none is
bit-identical.

**1.3 Schedule the deadlines.** Extend `cancelPromptsFor` and add
`scheduleDeadlines` next to it:

```js
function cancelPromptsFor(phase){
  for(const e of ev) if((e.kind==='prompt'||e.kind==='deadline')&&e.phase===phase&&!e.done)
    e.done=true;
}
function scheduleDeadlines(phase,t){
  const p=PHASE[phase];
  if(!p||!p.transitions) return;
  for(const tr of p.transitions)
    if(tr.after_seconds!==undefined) push({t:t+tr.after_seconds,kind:'deadline',phase});
}
```

Call it on the first line of `onPhaseEntry(phase,t)`.

**1.4 Handle the event.** First line of `applyEvent`'s tail:

```js
if(e.kind==='deadline'){ checkTransitions(t); return; }
```

**Why this is the right shape.** A deadline is a derived event exactly like a
prompt deadline or a result arrival, so it joins the schedule the fold already
merges in timestamp order, and the existing tiebreak (log entries before derived
events at equal timestamps) means a resident who gets the drug in *on* the
deadline is credited. Replay stays honest because nothing is stored. Deadlines are
cancelled on any phase change, including a time-driven one.

**Difficulty is deliberately not applied.** `DM` scales prompt deadlines only. See
system design 17.1 for why scaling deterioration would make hard mode more
forgiving and less forgiving at the same time.

### Verification

```
fold([],800) on MGCA  ->  presentation@0, adrenal_crisis@240,
                          frank_septic_shock@450, cardiac_arrest@750
fold([],800) on CHFE  ->  presentation@0            (unchanged)
```

Treating both deficits before 240s never fires a deadline. Treating them at 250s
fires the first deadline and then recovers to `improving`. All three match the
offline path simulator in `cases/MGCA/`.

---

## 2. shell.html

**2.1** Add IBM Plex Serif to the font link, weight 600 only. It is used for one
element.

**2.2** Add the welcome CSS block immediately before
`/* ---------- splash and picker ---------- */`. It is namespaced `wl-` throughout
except for `#picker.welcome` itself, which has to override the `.splash` overlay
rules. Two base64 assets are substituted at build time, the same way `__ROOM_BG__`
already is:

```python
shell = shell.replace("__HERO_BG__", open("engine/hero-bg.txt").read().strip())
shell = shell.replace("__AVATAR_M__", open("engine/avatar-male.txt").read().strip())
shell = shell.replace("__AVATAR_F__", open("engine/avatar-female.txt").read().strip())
```

**2.3** Replace the `#picker` block. Keep the id. Keep `#pk-list` and `#pk-warn`,
because `renderPicker` and `boot` both reference them.

**2.4** Splash back control. Move it to the top of `.splashcard`, above the setting
line, and drop the ghost button from `.splashactions` so Begin is the only thing in
the actions row:

```html
<div class="splashcard">
  <button class="splashback" id="backtopicker">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>All cases</button>
  <div class="setting" id="sp-setting"></div>
```

The id is unchanged, so both the click delegation and `boot()`'s single-case
hiding still find it.

---

## 3. ui.js

`renderPicker()` is replaced wholesale. It derives its list from `CASES` rather
than holding its own data, so adding a case stays a data change.

`backToPicker()` gains two lines, resetting the selection and blurring the search
box so returning from a case does not land on a stale highlight.

Everything else in ui.js is untouched. In particular `chooseCase`, the
`[data-case]` delegation, `renderSplash`, `begin` and `boot` are unchanged.

**Keyboard handling is scoped.** The welcome binds one `keydown` listener that
returns immediately unless `#picker` is visible, so `/`, the arrow keys and Enter
never reach a running case.

---

## 4. Case pack: two new optional card fields

```json
"card": {
  "complaint": "Worsening breathlessness",
  "category":  "Cardiovascular"
}
```

`complaint` is the short clinical phrase the welcome row shows. It is not
`chief_complaint`, which is the patient's own words and belongs on the splash.
`category` drives the group headers and the filter chips.

Both are optional and both degrade: a pack without `complaint` falls back to
`card.title`, and a pack without `category` drops into a single unnamed group with
the chips hidden. Age and sex come from `case.patient`, which every pack already
has, so no new field is needed for them.

These should be added to `case-authoring-requirements.md` section 3.1 the next time
that document is opened. They are not there yet.

---

## 5. Known issues found while doing this

**A CHFE scenario references an action id that does not exist in the build.**
`CHFE-scenarios.json`, "Every phase is reachable in some run: improving reached
without NIV first", uses `niv_bipap`. The binding shadows `niv_bipap` onto
`niv_cpap`, so the built pack has no such action, and the step is silently a no-op:
not applied, not blocked, not logged. The scenario expects `stabilizing` and
reaches `presentation`.

This predates the change here. It was confirmed by running the same scenario
against the unpatched `simulator.html`, which fails identically. Two things follow.
The scenario should use `niv_cpap` or the shadowing should be removed. And the
engine should log an unknown action id as a blocked attempt with a reason rather
than dropping it, because a silently ignored step in a test file is a test that
passes for the wrong reason.

**The provenance notice is gone from the entry screen.** It was removed on request.
The only remaining signal that no case has completed sign-off is the amber bead on
each row, which carries a `title` of "Unsigned draft". If that is too quiet, the
splash card is the natural home for it, one line under the setting.


---

## 6. Found when the edits moved from the build into the sources

**The prompt cap defeated the fairness guarantee.** The validator enforces that every
time-guarded deterioration is preceded by a prompt naming the missing treatment. It
checks the authored deadline. At runtime the per-phase prompt cap suppressed those
prompts: MGCA's presentation phase authored nine prompts against a cap of three, so the
antibiotic was fifth and the glucocorticoid seventh, and the 240 second deterioration
fired with neither warned. A static check on authored deadlines cannot see this. The
case now authors prompts only on the three actions its own `prompt_cap_recommendation`
always named, and `engine-tests.js` gained a runtime check that walks the do-nothing
path and asserts a prompt for each guard flag actually fires before its deadline.

**`also_covers` duplicated the prompt.** A covered entry borrows the covering action's
case fields so that a tag cannot be escaped by choosing a sibling. It was borrowing the
prompt and the critical expectation too, so the four crystalloid entries prompted four
times for one act and consumed the whole cap between them. `onPhaseEntry` now skips
covered entries: they keep the tag, the halt reason and the debrief note, which is the
point of the mechanism, and the covering action alone prompts and is expected. This
also removes three phantom entries from CHFE's omissions list.

**A generic engine assertion encoded the old invariant.** `mode changes only the
prompts, not the phase` asserted that after 300 seconds of inaction the phase was still
the starting phase, which was true only while no case could deteriorate. It now asserts
what it was really for: that easy and hard produce the same phase sequence, because
prompt deadlines scale and deterioration deadlines do not.

**`sim_runner.py` could not resolve equivalence groups.** A scenario step naming a
covered sibling read as an unknown action, so group coverage was untestable and CHFE
had no scenario walking the three crystalloids its harmful tag claims. The runner now
reads `also_covers` from the binding, and CHFE gained three scenarios that walk them.
