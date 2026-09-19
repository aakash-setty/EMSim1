#!/usr/bin/env python3
"""One-shot: changelog, README, both specifications and the four review packets."""
import os, sys
ROOT = sys.argv[1]
def ins(rel, anchor, text, before=True):
    p = os.path.join(ROOT, rel); s = open(p).read()
    assert s.count(anchor) == 1, (rel, s.count(anchor), anchor[:50])
    s = s.replace(anchor, (text + anchor) if before else (anchor + text)); open(p, "w").write(s); print("patched", rel)

ins("CHANGELOG.md", "## v0.16a: narrower panels, and the room clears the screen", """## v0.17: the patient is in the room

**A drawn patient stands in the gap between the workspace and the record.** The figure blinks,
breathes at the rate the monitor shows, opens its mouth with each breath when the case says
the work of breathing is up, closes its eyes when the case says so, and shakes when the case
says the patient is seizing. It is transparent and stands on the bottom edge of the window.
With the workspace open the face fills the gap and the shoulders run on behind the panes;
with the workspace closed it moves to the middle of the room and grows; with the record
expanded it fades. It never takes a click. It freezes while the case is paused.

**The artwork is avataaars** (Pablo Stanley, Fang-Pen Lin, MIT), extracted once into
`engine/patient-art.json` by `engine/assets/avataaars/extract.js`. Every option of the
generator is kept, plus a hospital gown and one eyebrow upstream ships and never registers.
Nothing at run time touches the generator's site, React or npm. The MIT notice is written
into `build/simulator.html` and `build/patient-lab.html`, because the licence requires it to
travel with the artwork. `package.json` still says UNLICENSED for this repository's own code;
that is a separate decision and is untouched.

**One standard man and one standard woman**, on the author's instruction: short flat hair or
long straight hair, dark brown; brown skin; a grey V-neck; default eyes, brows and mouth. They
live in `SHARED.patient.base` in `build_simulator.py` and a case draws one by `patient.sex`.
Hair, clothes and colours never change with state. A case may later author `patient.avatar`
to differ from the base key by key; none does. **The resting mouth of the base is avataaars'
`Default`, which is a smile**, as specified. On a patient in extremis that may read oddly;
`"mouthType": "Serious"` in the base is the one-word change.

**What is visible is a content key.** `content_keys.patient_visual` is a guarded rule list
resolved by the engine like any other (`patientVisual` in `engine.js`), first match wins, and
its value is the whole visible state: `eyes`, `seizure`, `work_of_breathing`, an optional
`expression`, and `addons`. The engine understands none of it. The respiratory rate is not
authorable there and the validator rejects it: the chest follows the monitor's number,
including the five-second ramp, and a rate of zero stops it. Both blocks are optional and a
case with neither draws the standard patient with open eyes.

**Built for add-ons.** `patient.js` is a rig, a pose system and one feature registry. The
built-in behaviours and every future add-on are the same kind of thing: SVG for any of eight
named slots, a per-frame tick that writes to additive channels (figure, torso, head, eyes,
brows, mouth) and to poses, and a list of layers to hide. Because channel contributions add,
features compose without knowing about each other. Four add-ons ship as worked examples, one
of each kind: `gaze_left`, `gaze_right` and `nystagmus` are motion with no artwork, and
`nasal_cannula` is artwork with no motion. **The cannula drawing is a placeholder.** Adding a
BiPAP mask or a tube is a `register()` call plus the name in two vocabularies, and
`engine-tests.js` fails if the three lists disagree. The landmarks an SVG is drawn to are in
`engine/assets/avataaars/README.md` and can be overlaid in the lab.

**`build/patient-lab.html`** is written by every build: pick an appearance, switch states,
copy the JSON for the case file.

**All four cases author a `patient_visual`, and every rule in them is model-authored.** They
are derived from each case's own phase descriptions and alertness levels and add no clinical
fact, but they are clinical depictions and each block carries a `verify` note listing the
choices to check. Three matter most. DIPH's convulsion is drawn with the eyes open. DIPH's
figure goes still with eyes closed once `airway_protected` is set, even in the seizing phase.
CHFE's nasal cannula follows the arrival phase and not the oxygen actions, which is wrong the
moment the resident changes the oxygen and should move to flags when mask artwork exists. The
rule lists appear in each review matrix as `patient_visual` rows.

**Motion.** Nothing flashes: a seizure is movement with no change in brightness. Under
`prefers-reduced-motion` amplitudes fall to about a third. The figure carries a text
description that tracks the state in observational words only.

**Not done.** At widths under 1000 px the workspace covers the room, so the figure shows only
with the workspace closed. The welcome board still uses the silhouettes. The seizure is one
pattern, with no tonic phase and no focal onset. Validator negative tests were not extended
to the new rules. Tested in headless Chromium only.

Engine checks 514 to 537. All four packs validate with 0 errors and every scenario passes.

""")

ins("README.md", "| `audio.js` |", """| `patient.js` | The patient figure in the room: the rig, the poses, and one registry for behaviours and add-ons. Fenced for the tests. How to add an add-on is in `assets/avataaars/README.md` |
| `patient-art.json` | The avataaars artwork as loose parts with colour slots. Derived by `assets/avataaars/extract.js`, not authored |
| `patient-lab.html` | Template for `build/patient-lab.html`, a workbench for choosing an appearance and previewing states |
""")

ins("docs/case-authoring-requirements.md", "### 6.1 Moving a vital with an action, not a phase", """### 6.0c The figure in the room, which is a content key and not part of the phase

A drawn patient stands between the panels. Two optional blocks control it, and a case with
neither gets the standard patient with open eyes.

`patient.avatar` is the fixed appearance, in avataaars option names. **Leave it out.** Every
case currently draws the standard man or woman by `patient.sex` (`SHARED.patient.base`), and
the appearance never changes with state. When cases come to choose their own bases, author
only the keys that differ. `build/patient-lab.html` lists every option and prints the JSON.

`content_keys.patient_visual` says what is visible now. It is a guarded rule list like
`general_status` (section 11.3), first match wins, and the value is the whole visible state:

```json
"patient_visual": { "rules": [
  { "when": "phase is seizing", "value": { "eyes": "open", "seizure": true } },
  { "when": "flag airway_protected set", "value": { "eyes": "closed" } },
  { "when": null, "value": {} }
] }
```

| Key | Values | Absent means |
|---|---|---|
| `eyes` | `open`, `closed` | `open`, blinking |
| `seizure` | `true`, `false` | `false` |
| `work_of_breathing` | `normal`, `increased`, `severe` | `normal` |
| `expression` | `{eyeType, eyebrowType, mouthType}` | the resting face |
| `addons` | `gaze_left`, `gaze_right`, `nystagmus`, `nasal_cannula` | none |

Do not author a respiratory rate here; the validator rejects it. The chest moves at the rate
on the monitor. Keep the block consistent with the general status line and the appearance
values, since all describe the same patient. Prefer flags to phases for anything a resident's
action puts on or takes off the patient. It is clinical content: it goes through the review
matrix and the 14.3 sign-off like every other key.

""")

ins("docs/system-design-v2.md", "### 8.5 Audio", """**8.4d The patient figure.** v0.17. `engine/patient.js` draws a person in the gap between the
workspace and the record and moves them. It holds no clinical knowledge. The engine resolves
`content_keys.patient_visual` through the ordinary resolver (`patientVisual`, beside
`generalStatus`) and the interface hands the value to the figure every frame, adding the
respiratory rate the monitor last showed so that the chest and the number cannot disagree.
The figure is drawn whether or not the monitor is attached, because a resident can see a
patient breathe without one. It freezes when the case is paused or over.

The module is a rig (nested groups: figure, torso, head, eyes, brows, mouth, each with an
additive channel), a pose system (eyes, brows and mouth each hold several drawings and show
one) and a single feature registry. Built-in behaviours and add-ons are the same kind of
object and run in priority order each frame. Rejected: one SVG per state, which cannot
compose (a seizing patient on a cannula would need its own drawing) and multiplies with every
add-on; CSS keyframes, which cannot follow a respiratory rate that ramps; and deriving the
visible state from vitals or alertness inside the engine, which would put a clinical
association in code that is meant to hold none. Vocabulary lives in `SHARED.patient`; part and
colour options live in `engine/patient-art.json` and are read, not restated.

""")

PACKET = """

## The figure in the room (v0.17, model-authored, not yet reviewed)

`content_keys.patient_visual` drives the drawn patient: eyes open or closed, seizure, work of
breathing, add-ons. Every rule was written by the model from this case's own phase
descriptions and alertness levels. Read the `verify` note inside the block, then the
`patient_visual` rows of the review matrix, and check each against the phase it names and
against the general status line.
"""
for pre in ("CHFE", "MGCA", "AFRVR", "DIPH"):
    p = os.path.join(ROOT, "cases", pre, pre + "-review-packet.md")
    s = open(p).read().rstrip("\n") + PACKET; open(p, "w").write(s); print("patched", p)
