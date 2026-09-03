# Changes to `engine/build_simulator.py`

Two edits, both in `main()`. Nothing else in the build changes.

### 1. Fill the background image placeholder

Find:

```python
    shell = open(os.path.join(HERE, "shell.html")).read()
```

and add the asset read after it:

```python
    shell = open(os.path.join(HERE, "shell.html")).read()
    room_bg = open(os.path.join(HERE, "room-bg.txt")).read().strip()
```

Then find:

```python
    shell = shell.replace("__TITLE__", title.replace("<", ""))
```

and add one line after it:

```python
    shell = shell.replace("__TITLE__", title.replace("<", ""))
    shell = shell.replace("__ROOM_BG__", room_bg)
```

### 2. Add `semantic.js` to the bundle

Find:

```python
    bundle = ("/*__ENGINE_START__*/\n" + open(os.path.join(HERE, "engine.js")).read() +
              "\n/*__ENGINE_END__*/\n" + open(os.path.join(HERE, "audio.js")).read() +
              "\n" + open(os.path.join(HERE, "ui.js")).read() + "\n")
```

and insert `semantic.js` **before** `ui.js`:

```python
    bundle = ("/*__ENGINE_START__*/\n" + open(os.path.join(HERE, "engine.js")).read() +
              "\n/*__ENGINE_END__*/\n" + open(os.path.join(HERE, "audio.js")).read() +
              "\n" + open(os.path.join(HERE, "semantic.js")).read() +
              "\n" + open(os.path.join(HERE, "ui.js")).read() + "\n")
```

**The order matters.** `semantic.js` declares `const SEM`, and `ui.js` registers a
listener on it at top level. If `semantic.js` comes after `ui.js` the bundle
throws `ReferenceError: SEM is not defined` before the first render and the page
is blank. There is no graceful degradation for getting this wrong, so if the
simulator goes white after applying this, check the order first.

### Failure modes if you skip these

- Skip edit 1: the build still succeeds and the simulator still runs. The
  background image is absent and the room falls back to flat colour. No error.
- Skip edit 2: `SEM` is undefined and the page does not render at all. Loud,
  which is the right way round for this one.

## Files

| File | Where it goes | New? |
|---|---|---|
| `shell.html` | `engine/shell.html` | replaces |
| `ui.js` | `engine/ui.js` | replaces |
| `semantic.js` | `engine/semantic.js` | new |
| `room-bg.txt` | `engine/room-bg.txt` | new |
| `matcher_eval.mjs` | `engine/matcher_eval.mjs` | new |
| `interview-eval-CHFE.json` | `engine/eval/interview-eval-CHFE.json` | new |

`engine.js`, `audio.js`, the catalogs and every case file are untouched.

## Running the matcher evaluation

```
python3 engine/build_simulator.py          # the harness reads build/simulator.html
node engine/matcher_eval.mjs               # lexical only, no downloads
npm install @huggingface/transformers@4.2.0
node engine/matcher_eval.mjs --semantic --sweep
```

The harness extracts the lexical matcher out of the built HTML rather than
holding a copy, as section 10.6 requires. It looks for the marker comments
`/* ---------- interview matching (section 10.6) ---------- */` and
`/* ---------- fusion of the lexical and semantic matchers ----------` in
`ui.js`. If you move or reword either, fix the markers in `matcher_eval.mjs`.
Do not paste a copy of the matcher into the harness: a second copy drifts, and
then the evaluation reports on a matcher nobody runs.

## Two operational notes about the embedding model

**Serve the simulator over http rather than opening it as a file.** The browser
caches the 23 MB model in the Cache API, which requires a secure context.
Opened as `file://`, the model may be re-fetched every session and the
embedding cache in IndexedDB is unavailable in some browsers. Any static host
works and none of them is a backend: GitHub Pages, Netlify, or a plain
`python3 -m http.server` on a teaching machine. Opened as a file it still
works, it is just slower on repeat visits.

**A sandboxed preview will stay on basic matching.** Environments that restrict
which hosts a page may contact, including published Claude artifacts, will
block the model weights on `huggingface.co`. The status line under the question
box will read "basic". That is the fallback behaving correctly, not a bug. To
see the enhanced matcher, open the built file locally or host it.

## Regenerating the background

`room-bg.txt` is derived from the source image, not authored, so it is not
stored in the project. The command that produces it is in a comment at the top
of the `.room` rule in `shell.html`.
