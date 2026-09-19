#!/usr/bin/env python3
"""One-shot: the non-rebreather joins the vocabulary; CHFE and MGCA draw it (and MGCA its
nasal cannula) from the oxygen flags their own actions set."""
import json, os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
OLD = '"nasal_cannula", "bipap_mask", "intubated"'
NEW = '"nasal_cannula", "nonrebreather", "bipap_mask", "intubated"'
patch("engine/build_simulator.py", [(OLD + "],", NEW + "],")])
patch("engine/validate_case.py", [(OLD + "}", NEW + "}")])
patch("docs/case-authoring-requirements.md", [("`nasal_cannula`, `bipap_mask`, `intubated`", "`nasal_cannula`, `nonrebreather`, `bipap_mask`, `intubated`")])

def nrb(w): return {"eyes": "open", "work_of_breathing": w, "addons": ["nonrebreather"]}
def edit(pre, fn):
    p = os.path.join(ROOT, "cases", pre, pre + "-case.json"); j = json.load(open(p))
    fn(j["content_keys"]["patient_visual"])
    with open(p, "w") as f: json.dump(j, f, indent=1, ensure_ascii=False); f.write("\n")
    print("edited", p)
def chfe(pv):
    r = pv["rules"]; i = next(k for k, x in enumerate(r) if x["when"] == "flag on_niv set") + 1
    r[i:i] = [
     {"when": "flag oxygen_nrb set AND (phase is presentation OR phase is impending_respiratory_failure)", "value": nrb("severe")},
     {"when": "flag oxygen_nrb set AND (phase is niv_supported OR phase is nitrate_responding)", "value": nrb("increased")},
     {"when": "flag oxygen_nrb set", "value": nrb("normal")}]
    pv["verify"] = pv["verify"].replace(
     "The nasal cannula is still drawn from the arrival phase alone, from the EMS handover, and does not follow the oxygen actions.",
     "The non-rebreather follows flag oxygen_nrb and replaces the cannula; NIV replaces both. The nasal cannula itself is still drawn from the arrival phase alone, from the EMS handover.")
    assert "oxygen_nrb" in pv["verify"]
def mgca(pv):
    r = pv["rules"]; i = len(r) - 1
    r[i:i] = [{"when": "flag oxygen_nrb set", "value": nrb("normal")},
              {"when": "flag oxygen_nc set", "value": {"eyes": "open", "work_of_breathing": "normal", "addons": ["nasal_cannula"]}}]
    pv["verify"] += " The non-rebreather and the nasal cannula follow flags oxygen_nrb and oxygen_nc; if both are set the non-rebreather is drawn."
edit("CHFE", chfe); edit("MGCA", mgca)

p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17a: a mask and a tube"; assert s.count(a) == 1
s = s.replace(a, """## v0.17b: a non-rebreather, and shoulders that breathe

`nonrebreather` is a third device add-on: a soft clear mask with side ports, a thin elastic
strap, a reservoir bag that sags on inspiration and refills on expiration, and narrow green
oxygen tubing. The mouth shows through it. CHFE and MGCA draw it from `oxygen_nrb`, the flag
their own action sets, and MGCA now also draws its nasal cannula from `oxygen_nc`. AFRVR's
`supplemental_o2` and DIPH's `oxygen_applied` do not say which device, so those cases draw
none; splitting those flags by device is a case-authoring decision.

**Breathing is now visible at rest.** On the author's instruction the shoulders rise and drop
once per breath at the monitor's rate: 3.2 units of travel at normal effort, 5 at increased,
6.5 at severe, against 1.1, 2.6 and 4 before, which at the size the figure is drawn in the gap
was under two pixels at rest. It is a stretch of the torso about the drawing's bottom edge, so
that edge never lifts off the window. The head does not move at normal effort.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
