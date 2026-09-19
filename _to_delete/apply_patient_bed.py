#!/usr/bin/env python3
"""One-shot: the stretcher trial. Registered as an add-on so a case could use it, and
switched on everywhere by adding ?bed=1 to the address, so it can be judged on the real
screen without touching any case."""
import os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
patch("engine/build_simulator.py", [('"jaundice", "sweating", "agitation"],', '"jaundice", "sweating", "agitation",\n               "hospital_bed", "hospital_bed_flat"],')])
patch("engine/validate_case.py", [('"jaundice", "sweating", "agitation"}', '"jaundice", "sweating", "agitation",\n                  "hospital_bed", "hospital_bed_flat"}')])
patch("engine/ui.js", [(
 "  PT.setState(v);\n",
 "  /* TRIAL. ?bed=1 (or ?bed=flat) on the address draws the stretcher behind every patient, so\n"
 "     it can be judged on the real screen before any case is asked to author it. */\n"
 "  if(BED_TRIAL) v.addons=(v.addons||[]).concat(BED_TRIAL);\n"
 "  PT.setState(v);\n"),
 ("let PT=null, PT_CASE=null;\n",
  "let PT=null, PT_CASE=null;\n"
  "const BED_TRIAL=(function(){ try{ const m=/[?&]bed=(\\w+)/.exec(location.search); return m?(m[1]==='flat'?'hospital_bed_flat':'hospital_bed'):null; }catch(e){ return null; } })();\n")])
p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17g: build and age"; assert s.count(a) == 1
s = s.replace(a, """## v0.17h: a stretcher behind the patient (trial)

On the author's request, to see how it looks on the main screen. A stretcher with the head up,
drawn behind the bust in the backdrop slot: backrest and mattress, a headboard above it, a
pillow behind the head and a side rail either side. It is outside the figure rig, so it stays
still while the patient breathes, nods or seizes against it. It is drawn well beyond the
viewBox on purpose and runs on behind the panels and off the bottom of the window. Built in
two stages, both kept: `hospital_bed_flat` is the shapes alone; `hospital_bed` adds gradients
on the mattress and pillow, fitted-sheet folds as soft blurred bands, pillow creases running
out from under the head, a piped seam, and blurred contact shadows where the head presses the
pillow, the pillow presses the mattress and the shoulders press the sheet.

**No case uses it.** `?bed=1` on the address draws it behind every patient and `?bed=flat`
draws the first stage. Open questions if it stays: the patient's white shirt on a white sheet
relies entirely on the contact shadow for separation; the room photograph already contains a
bed, so there are now two; and an upright bust against a backrest reads as sitting up at
about 45 degrees, which is right for CHFE and wrong for a patient the text says is supine or
curled on her side.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
