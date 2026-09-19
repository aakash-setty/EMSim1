#!/usr/bin/env python3
"""One-shot: the figure's face follows the phase's alertness level."""
import os, re, subprocess, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
patch("engine/ui.js", [(
 "  if(typeof ap.distress_level==='number') v.distress=ap.distress_level;\n",
 "  if(typeof ap.distress_level==='number') v.distress=ap.distress_level;\n"
 "  if(typeof ap.alertness_level==='number') v.alertness=ap.alertness_level;\n")])
patch("engine/engine-tests.js", [
 ("voc.parts.graphicType.length === 11 && voc.parts.eyeType.length === 12 &&",
  "voc.parts.graphicType.length === 11 && voc.parts.eyeType.length === 14 &&"),
 ("    chk('the standard patient is not smiling',",
  "    chk('alertness is accepted from the interface and clamped',\n"
  "        [0, 1, 2, 3].map(n => PATIENT.normalizeState({ alertness: n }).state.alertness).join() === '0,1,2,3' &&\n"
  "        PATIENT.normalizeState({ alertness: -2 }).state.alertness === 0);\n"
  "    chk('the two reduced-alertness eye drawings exist', ['Drowsy', 'Heavy'].every(e => voc.parts.eyeType.includes(e)));\n"
  "    chk('the standard patient is not smiling',")])
patch("engine/validate_case.py", [(
 "        # respiratory_rate and distress are caught as unknown keys above, on purpose. The rate is\n"
 "        # the monitor's and the distress level is the phase's; the interface passes both in.\n",
 "        # respiratory_rate, distress and alertness are caught as unknown keys above, on purpose.\n"
 "        # The rate is the monitor's and the two levels are the phase's; the interface passes all\n"
 "        # three in.\n")])
patch("docs/case-authoring-requirements.md", [(
 "Closed eyes relax the face. An authored `expression` wins.",
 "Closed eyes relax the face. An authored `expression` wins.\n\n"
 "The phase's `appearance.alertness_level` is drawn the same way and is likewise not authored\n"
 "here. 0 alert: open eyes, ordinary blinks. 1 drowsy: heavy lids, slow blinks, and now and\n"
 "then the lids close and the head nods. 2 obtunded: eyes closed, opening to a sliver for a\n"
 "moment every several seconds, head fallen a little to one side, jaw slack. 3 unresponsive: the\n"
 "same with the eyes staying closed. So `eyes` in a rule is now only needed to override the\n"
 "level: `\"eyes\": \"closed\"` for a sedated patient whose phase is not level 3, or a seizure,\n"
 "which draws open eyes and a clenched jaw at any level.")])
patch("engine/assets/avataaars/README.md", [(
 "- `eyebrowType: \"FrownNatural\"`. Upstream ships the drawing and never registers it.",
 "- `eyebrowType: \"FrownNatural\"`. Upstream ships the drawing and never registers it.\n"
 "- `eyeType: \"Drowsy\"` and `\"Heavy\"`. The default eye under a heavy lid, and under a lid so low\n"
 "  only a sliver shows. Drawn for reduced alertness; the figure picks them itself from the\n"
 "  phase's alertness level.")])

# DIPH: post_ictal was drawn eyes closed for want of a drowsy face. It has one now.
d = os.path.join(ROOT, "cases", "DIPH"); p = os.path.join(d, "case_3_content.py"); s = open(p).read()
m = re.search(r'  \{\n   "when": "phase is post_ictal",\n   "value": \{\n    "eyes": "closed"\n   \}\n  \},\n', s); assert m, "post_ictal rule not found"
s = s[:m.start()] + s[m.end():]
old = ("(3) post_ictal is drawn eyes closed from 'drowsy', at alertness level 1.")
assert s.count(old) == 1
s = s.replace(old, "(3) post_ictal has no rule of its own: it is alertness level 1 and is drawn drowsy, with heavy lids and a nodding head, by the figure itself.")
open(p, "w").write(s); subprocess.check_call([sys.executable, os.path.join(d, "build_case.py"), d])

p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17c: nobody ill is smiling"; assert s.count(a) == 1
s = s.replace(a, """## v0.17d: four faces for four levels of alertness

Authoring section 6 has always said the alertness level governs "eye state, responsiveness".
The figure now draws it, from `appearance.alertness_level`, passed in by the interface like
the distress level and rejected by the validator inside `patient_visual`.

- **0 alert.** Open eyes, ordinary blinks.
- **1 drowsy.** Heavy upper lids, slow blinks, and every six to thirteen seconds the lids close
  for about a second while the head nods forward and comes back.
- **2 obtunded.** Eyes closed, opening to a sliver for about a second every five to ten
  seconds. Head fallen a little to one side, jaw slack, brows and mouth relaxed whatever the
  distress level was.
- **3 unresponsive.** The same, with the eyes staying closed and the head further over.

Two eye drawings were added to the art file for this, `Drowsy` and `Heavy`; avataaars has
nothing between open and shut. A seizure still draws open eyes and a clenched jaw at any
level, so DIPH's seizing phase (level 3) is unchanged. The slack jaw takes the larger of
itself and the breathing mouth, so CHFE's obtunded, exhausted phase still mouth-breathes. An
authored `"eyes": "closed"` still closes the eyes at any level.

**DIPH's `post_ictal` rule is removed.** It drew closed eyes at level 1 only because there was
no drowsy face. The phase now draws as drowsy. MGCA's two level 1 phases and AFRVR's
`respiratory_failure` change the same way with no edit.

The torso copy under the head is now clipped to the neck's width above the shoulders. A
tilted head was showing a second jaw line from the copy beneath it.

The timings and the tilt are the model's choices and want a clinician's eye, as does whether
level 2 should open its eyes at all without a stimulus.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
