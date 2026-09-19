#!/usr/bin/env python3
"""One-shot: bipap_mask and intubated join the add-on vocabulary, and the four cases' visual
rules move from phases to the flags the resident's own actions set."""
import json, os, re, subprocess, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)

patch("engine/build_simulator.py", [(
 '"addons": ["gaze_left", "gaze_right", "nystagmus", "nasal_cannula"],',
 '"addons": ["gaze_left", "gaze_right", "nystagmus", "nasal_cannula", "bipap_mask", "intubated"],')])
patch("engine/validate_case.py", [(
 'PATIENT_ADDONS = {"gaze_left", "gaze_right", "nystagmus", "nasal_cannula"}',
 'PATIENT_ADDONS = {"gaze_left", "gaze_right", "nystagmus", "nasal_cannula", "bipap_mask", "intubated"}')])
patch("docs/case-authoring-requirements.md", [(
 "| `addons` | `gaze_left`, `gaze_right`, `nystagmus`, `nasal_cannula` | none |",
 "| `addons` | `gaze_left`, `gaze_right`, `nystagmus`, `nasal_cannula`, `bipap_mask`, `intubated` | none |")])

NOTE = ("MODEL-AUTHORED, NOT PHYSICIAN-AUTHORED. Drives the figure in the room (engine/patient.js). "
        "Derived from this case's own phase descriptions, alertness levels, general status lines and "
        "action flags, and adds no clinical fact of its own: eyes closed where the phase is "
        "unresponsive, sedated or arrested; work of breathing where the phase description names it; "
        "the mask and the tube where the flag the resident's own action sets is set. The respiratory "
        "rate is not authored here, the figure breathes at the monitor's rate. Verify each rule "
        "against the phase and flag it names, as for any other content key.")
TUBE = {"eyes": "closed", "addons": ["intubated"]}
def niv(wob): return {"eyes": "open", "work_of_breathing": wob, "addons": ["bipap_mask"]}
CASES = {
 "CHFE": {"rules": [
   {"when": "flag intubated set OR phase is post_intubation_hypotension OR phase is intubated_stabilized", "value": TUBE},
   {"when": "phase is halted", "value": {"eyes": "closed"}},
   {"when": "flag on_niv set AND (phase is presentation OR phase is impending_respiratory_failure)", "value": niv("severe")},
   {"when": "flag on_niv set AND (phase is niv_supported OR phase is nitrate_responding)", "value": niv("increased")},
   {"when": "flag on_niv set", "value": niv("normal")},
   {"when": "phase is impending_respiratory_failure", "value": {"eyes": "open", "work_of_breathing": "severe"}},
   {"when": "phase is presentation", "value": {"eyes": "open", "work_of_breathing": "severe", "addons": ["nasal_cannula"]}},
   {"when": "phase is niv_supported OR phase is nitrate_responding", "value": {"eyes": "open", "work_of_breathing": "increased"}},
   {"when": None, "value": {"eyes": "open", "work_of_breathing": "normal"}}],
  "verify": ("The mask follows flag on_niv and the tube follows flag intubated, so both appear when the "
             "resident's action takes effect and not when a phase happens to change. The nasal cannula "
             "is still drawn from the arrival phase alone, from the EMS handover, and does not follow "
             "the oxygen actions. Intubated is always drawn eyes closed, which assumes sedation.")},
 "MGCA": {"rules": [
   {"when": "flag intubated set OR phase is frank_septic_shock", "value": TUBE},
   {"when": "phase is cardiac_arrest OR phase is halted", "value": {"eyes": "closed"}},
   {"when": None, "value": {"eyes": "open", "work_of_breathing": "normal"}}],
  "verify": ("frank_septic_shock is drawn intubated with eyes closed because its description places it "
             "after induction and positive pressure ventilation; confirm that phase cannot be reached "
             "without intubation. Tachypnoea in this case is drawn as rate only, with no increased "
             "effort, because no phase description names respiratory effort.")},
 "AFRVR": {"rules": [
   {"when": "flag intubated set OR phase is intubated", "value": TUBE},
   {"when": "phase is halted", "value": {"eyes": "closed"}},
   {"when": "flag on_niv set AND (phase is respiratory_failure OR phase is rate_controlled_congested)", "value": niv("severe")},
   {"when": "flag on_niv set AND phase is presentation", "value": niv("increased")},
   {"when": "flag on_niv set", "value": niv("normal")},
   {"when": "phase is respiratory_failure OR phase is rate_controlled_congested", "value": {"eyes": "open", "work_of_breathing": "severe"}},
   {"when": "phase is presentation", "value": {"eyes": "open", "work_of_breathing": "increased"}},
   {"when": None, "value": {"eyes": "open", "work_of_breathing": "normal"}}],
  "verify": ("The mask follows flag on_niv and the tube follows flag intubated. presentation is drawn "
             "as increased rather than severe because he can still finish a sentence; "
             "rate_controlled_congested is drawn as severe from 'still working hard to breathe' at "
             "distress level 3. respiratory_failure is drowsy and is drawn eyes open.")},
 "DIPH": {"rules": [
   {"when": "flag airway_protected set", "value": TUBE},
   {"when": "phase is pulseless_vt OR phase is halted", "value": {"eyes": "closed"}},
   {"when": "phase is seizing", "value": {"eyes": "open", "seizure": True}},
   {"when": "phase is post_ictal", "value": {"eyes": "closed"}},
   {"when": None, "value": {"eyes": "open", "work_of_breathing": "normal"}}],
  "verify": ("Three choices to check. (1) The convulsion is drawn with the eyes OPEN, on the "
             "understanding that the eyes are usually open in a generalised tonic-clonic seizure "
             "and that closed eyes during the event point toward a functional seizure; change it "
             "if that is not what should be taught. (2) Once airway_protected is set the figure is "
             "intubated, still and eyes closed even in the seizing phase, on the assumption of "
             "induction and paralysis; a paralysed patient may still be seizing electrically and the "
             "figure cannot show that. (3) post_ictal is drawn eyes closed from 'drowsy', at alertness "
             "level 1.")},
}
def block(c): return {"authoring_note": NOTE, "verify": c["verify"], "rules": c["rules"]}
for pre in ("CHFE", "MGCA"):
    p = os.path.join(ROOT, "cases", pre, pre + "-case.json"); j = json.load(open(p))
    assert "patient_visual" in j["content_keys"]
    j["content_keys"]["patient_visual"] = block(CASES[pre])
    with open(p, "w") as f: json.dump(j, f, indent=1, ensure_ascii=False); f.write("\n")
    print("edited", p)
def pylit(o):
    s = json.dumps(o, indent=1, ensure_ascii=False)
    return s.replace(": true", ": True").replace(": false", ": False").replace(": null", ": None")
for pre in ("AFRVR", "DIPH"):
    d = os.path.join(ROOT, "cases", pre); p = os.path.join(d, "case_3_content.py"); s = open(p).read()
    m = re.search(r"\nPATIENT_VISUAL = \{.*?\n\}\n\nLABS = \{", s, re.S); assert m
    s = s[:m.start()] + "\nPATIENT_VISUAL = " + pylit(block(CASES[pre])) + "\n\nLABS = {" + s[m.end():]
    open(p, "w").write(s)
    subprocess.check_call([sys.executable, os.path.join(d, "build_case.py"), d])

p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17: the patient is in the room"; assert s.count(a) == 1
s = s.replace(a, """## v0.17a: a mask and a tube

Two add-ons, registered in `engine/patient.js` exactly as its README describes and with no
other engine change. `bipap_mask` is a clear oronasal shell with four-point headgear over the
hair and a corrugated hose; the mouth shows through it, so a labouring patient is still seen
to labour, and glasses come off while it is on. `intubated` is an endotracheal tube taped at
the lips with a pilot balloon, a connector and a ventilator circuit; it hides the drawn mouth,
so no behaviour can make an intubated patient grimace or mouth-breathe. Neither decides
whether the eyes are closed; the case does. Both drawings are the model's and want a
clinician's eye.

All four cases' `patient_visual` rules now follow the flags the resident's own actions set
(`on_niv`, `intubated`, DIPH's `airway_protected`) where those exist, so the mask and the tube
appear when the action takes effect. Phase-only rules remain where a phase itself implies the
device (CHFE's two post-intubation phases, AFRVR's `intubated`, MGCA's `frank_septic_shock`).
Intubated is always drawn eyes closed, which assumes sedation. CHFE's nasal cannula is still
phase-driven. Still model-authored, still unreviewed; each block's `verify` note is updated.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
