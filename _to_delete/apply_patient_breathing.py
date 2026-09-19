#!/usr/bin/env python3
"""One-shot: the resting face follows the phase's distress level, the base stops smiling,
and the tests follow the new breathing curve."""
import os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new, n in pairs:
        assert s.count(old) == n, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
patch("engine/ui.js", [(
 "  if(typeof shown.respiratory_rate==='number') v.respiratory_rate=shown.respiratory_rate;\n",
 "  if(typeof shown.respiratory_rate==='number') v.respiratory_rate=shown.respiratory_rate;\n"
 "  /* The resting face is drawn from the distress level the phase already authors, the same\n"
 "     way the chest is drawn from the rate: passed in here, never authored a second time. */\n"
 "  const ap=(PHASE[ST.phase]||{}).appearance||{};\n"
 "  if(typeof ap.distress_level==='number') v.distress=ap.distress_level;\n", 1)])
patch("engine/build_simulator.py", [
 ('"eyeType": "Default", "eyebrowType": "Default", "mouthType": "Default",',
  '"eyeType": "Default", "eyebrowType": "Default", "mouthType": "Serious",', 2),
 ("    # patient beyond their sex. A case's patient.avatar overrides these key by key.\n",
  "    # patient beyond their sex. A case's patient.avatar overrides these key by key.\n"
  "    # The mouth is Serious and not avataaars' Default, which is a smile: nobody arriving in a\n"
  "    # resuscitation bay is smiling. The resting mouth and brows then follow the phase's own\n"
  "    # appearance.distress_level (DISTRESS_FACE in patient.js).\n", 1)])
patch("engine/engine-tests.js", [(
 "  chk('breathing is 0 at end-expiration and 1 at end-inspiration',\n"
 "      PATIENT._breathCurve(0, 16) === 0 && Math.abs(PATIENT._breathCurve(0.38, 16) - 1) < 1e-9);\n",
 "  {\n"
 "    const curve = rr => Array.from({ length: 1000 }, (_, i) => PATIENT._breathCurve(i / 1000, rr));\n"
 "    const rest = curve(14), fast = curve(34);\n"
 "    chk('a breath starts at 0, peaks at 1 and stays inside 0 to 1',\n"
 "        rest[0] === 0 && Math.max(...rest) > 0.999 && rest.every(x => x >= 0 && x <= 1));\n"
 "    chk('a resting breath ends in a pause and a fast one does not',\n"
 "        rest.slice(900).every(x => x === 0) && fast[990] > 0);\n"
 "    chk('expiration lets go quickly and then tails off',\n"
 "        (() => { const p = rest.indexOf(Math.max(...rest)), end = rest.findIndex((x, i) => i > p && x === 0);\n"
 "                 return rest[Math.round(p + (end - p) / 2)] < 0.35; })());\n"
 "    const d = [0, 1, 2, 3].map(n => PATIENT.normalizeState({ distress: n }).state.distress);\n"
 "    chk('distress is accepted from the interface and clamped', d.join() === '0,1,2,3' &&\n"
 "        PATIENT.normalizeState({ distress: 9 }).state.distress === 3);\n"
 "    chk('the standard patient is not smiling', ['male', 'female'].every(s => PATIENT.baseFor(s).mouthType === 'Serious'));\n"
 "  }\n", 1)])
patch("engine/validate_case.py", [(
 "        if \"respiratory_rate\" in v:\n            pass  # unreachable: caught as an unknown key above, on purpose. The rate is the monitor's.\n",
 "        # respiratory_rate and distress are caught as unknown keys above, on purpose. The rate is\n"
 "        # the monitor's and the distress level is the phase's; the interface passes both in.\n", 1)])
patch("docs/case-authoring-requirements.md", [(
 "Do not author a respiratory rate here; the validator rejects it. The chest moves at the rate\non the monitor.",
 "Do not author a respiratory rate or a distress level here; the validator rejects both. The\n"
 "shoulders rise and drop at the rate on the monitor, and the resting face is drawn from the\n"
 "phase's own `appearance.distress_level`: 0 a neutral mouth, 1 worried brows, 2 a downturned\n"
 "mouth, 3 heavier brows as well. Closed eyes relax the face. An authored `expression` wins.", 1)])
p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17b: a non-rebreather, and shoulders that breathe"; assert s.count(a) == 1
s = s.replace(a, """## v0.17c: nobody ill is smiling, and breathing that looks like breathing

**The standard patient's mouth is `Serious`, not avataaars' `Default`, which is a smile.** On
the author's instruction, reversing the earlier one to copy the generator's defaults. The
resting face then follows the distress level each phase already authors: 0 a neutral mouth, 1
worried brows, 2 a downturned mouth, 3 heavier brows as well. Closed eyes relax the face to
level 0. The interface passes `appearance.distress_level` to the figure the way it passes the
respiratory rate, so nothing is authored twice and the validator rejects `distress` inside
`patient_visual`. An authored `expression` still wins. CHFE, AFRVR and DIPH arrive at distress
3 or 2 and now look it; MGCA arrives at 2.

**Breathing was a stretch of the whole torso and read as a shirt being pulled.** The torso is
now drawn once whole and still, with a left and a right half on top, each turning outward
about the base of the neck. The shoulder tips travel 3, 5 and 7 units at normal, increased and
severe effort while the collar stays put. The chest widens slightly, the head rides up a
touch even at rest, and the nostrils flare on inspiration at increased and severe effort. The
halves are cut with masks, not clip paths, and stop a hair above the hem, because a clip is
applied per child and the art's layered edges bled a hairline along every cut.

**The breath has three parts.** Inspiration is eased at both ends. Expiration lets go quickly
and tails off. At resting rates a pause follows, shrinking as the rate climbs and gone by 28,
while inspiration takes a growing share of the cycle. Engine tests assert the shape.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
