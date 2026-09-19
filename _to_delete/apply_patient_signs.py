#!/usr/bin/env python3
"""One-shot: six add-ons join the vocabulary, patient_visual gains an `also` list for
things that are independent of the main state, and the cases use what their own text and
flags support."""
import json, os, re, subprocess, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
OLD = '"nasal_cannula", "nonrebreather", "bipap_mask", "intubated"'
NEW = OLD + ',\n               "bag_valve_mask", "defib_pads", "central_line", "jaundice", "sweating", "agitation"'
patch("engine/build_simulator.py", [(OLD + "],", NEW + "],")])
patch("engine/validate_case.py", [
 (OLD + "}", NEW.replace("\n               ", "\n                  ") + "}"),
 ("    for i, r in enumerate(pv[\"rules\"]):\n        where = f\"patient_visual[{i}]\"\n",
  "    # `also`: every entry whose condition holds adds its add-ons to whatever the rules chose.\n"
  "    # For things independent of the main state (pads, a line, sweat), which a first-match\n"
  "    # list could only express by multiplying every rule by every combination.\n"
  "    for i, r in enumerate(pv.get(\"also\") or []):\n"
  "        where = f\"patient_visual.also[{i}]\"\n"
  "        if not isinstance(r, dict) or set(r) - {\"when\", \"addons\", \"note\"}:\n"
  "            errors.append(f\"[patient] {where}: expected only when and addons\"); continue\n"
  "        if not r.get(\"when\"):\n"
  "            errors.append(f\"[patient] {where}: needs a condition; an unconditional add-on belongs in the default rule\")\n"
  "        else:\n"
  "            try:\n"
  "                parse_condition(r[\"when\"])\n"
  "            except ParseError as e:\n"
  "                errors.append(f\"[patient] {where}: {e}\")\n"
  "        for a in (r.get(\"addons\") or []):\n"
  "            if a not in PATIENT_ADDONS:\n"
  "                errors.append(f\"[patient] {where}: addon {a!r} is not one of {sorted(PATIENT_ADDONS)}\")\n"
  "        if not r.get(\"addons\"):\n"
  "            errors.append(f\"[patient] {where}: no addons\")\n"
  "    for i, r in enumerate(pv[\"rules\"]):\n        where = f\"patient_visual[{i}]\"\n")])
patch("engine/engine.js", [
 ("GENERAL_STATUS=null, PATIENT_VISUAL=null;", "GENERAL_STATUS=null, PATIENT_VISUAL=null, PATIENT_ALSO=[];"),
 ("  PATIENT_VISUAL = CK.patient_visual ? CK.patient_visual.rules : null;\n",
  "  PATIENT_VISUAL = CK.patient_visual ? CK.patient_visual.rules : null;\n"
  "  PATIENT_ALSO = (CK.patient_visual && CK.patient_visual.also) || [];\n"),
 ("function patientVisual(st){\n  if(PATIENT_VISUAL){\n    const v=resolve(PATIENT_VISUAL,st);\n    if(v) return {value:v,source:'case'};\n  }\n",
  "function patientVisual(st){\n"
  "  /* `also` is the one place a content key is not first-match: every entry whose condition\n"
  "     holds adds its add-ons to what the rules chose. Pads, a line and sweat are independent\n"
  "     of each other and of the airway, and a first-match list can only say that by listing\n"
  "     every combination. */\n"
  "  const extra=[];\n"
  "  for(const r of PATIENT_ALSO) if(test(r.when,st)) for(const a of (r.addons||[])) if(extra.indexOf(a)<0) extra.push(a);\n"
  "  const withExtra=v=>{ if(!extra.length) return v; const o=Object.assign({},v);\n"
  "    o.addons=(v.addons||[]).concat(extra.filter(a=>(v.addons||[]).indexOf(a)<0)); return o; };\n"
  "  if(PATIENT_VISUAL){\n    const v=resolve(PATIENT_VISUAL,st);\n    if(v) return {value:withExtra(v),source:'case'};\n  }\n"
  "  if(extra.length) return {value:withExtra((SHARED.patient&&SHARED.patient.visualDefault)||{}),source:'case'};\n")])
patch("engine/engine-tests.js", [(
 "    const bad = (rules || []).map(r => PATIENT.normalizeState(r.value).problems).flat();\n",
 "    const bad = (rules || []).map(r => PATIENT.normalizeState(r.value).problems).flat()\n"
 "      .concat(((CASE.content_keys.patient_visual || {}).also || []).map(r => PATIENT.normalizeState({ addons: r.addons }).problems).flat());\n"
 "    for (const r of ((CASE.content_keys.patient_visual || {}).also || [])) {\n"
 "      const ph = (r.when.match(/phase is (\\w+)/) || [])[1], fl = (r.when.match(/flag (\\w+) set/) || [])[1];\n"
 "      const st = { phase: ph || START_PHASE, flags: new Set(fl ? [fl] : []), ordered: new Set(), resulted: new Set(), taken: new Set() };\n"
 "      if (test(r.when, st)) chk(PACK.prefix + ': also \"' + r.when.slice(0, 40) + '\" adds ' + r.addons.join('+'),\n"
 "          r.addons.every(a => (patientVisual(st).value.addons || []).includes(a)));\n"
 "    }\n")])
patch("docs/case-authoring-requirements.md", [
 ("`nasal_cannula`, `nonrebreather`, `bipap_mask`, `intubated`",
  "`nasal_cannula`, `nonrebreather`, `bipap_mask`, `intubated`, `bag_valve_mask`, `defib_pads`, `central_line`, `jaundice`, `sweating`, `agitation`"),
 ("Do not author a respiratory rate or a distress level here;",
  "Beside `rules` the block may carry `also`, a list of `{\"when\": ..., \"addons\": [...]}`. It is\n"
  "not first-match: every entry whose condition holds adds its add-ons to whatever `rules` chose.\n"
  "Use it for things independent of the main state, such as pads, a central line or sweating,\n"
  "which `rules` could only express by listing every combination. Keep the airway devices in\n"
  "`rules`, where only one can win. **`also` does not appear in the review matrix**; read it in\n"
  "the case file.\n\n"
  "Do not author a respiratory rate or a distress level here;")])

ALSO = {
 "CHFE": [{"when": "phase is presentation OR phase is impending_respiratory_failure", "addons": ["sweating"]}],
 "AFRVR": [{"when": "phase is respiratory_failure", "addons": ["sweating"]},
           {"when": "flag pacing_pads_placed set", "addons": ["defib_pads"]},
           {"when": "flag central_access set", "addons": ["central_line"]}],
 "MGCA": [{"when": "phase is presentation OR phase is adrenal_crisis", "addons": ["sweating"]},
          {"when": "flag central_access set", "addons": ["central_line"]}],
 "DIPH": [{"when": "phase is presentation AND NOT flag airway_protected set", "addons": ["agitation"]}],
}
VER = {
 "CHFE": " Sweating is drawn in the two phases whose general status line says so.",
 "AFRVR": " Sweating is drawn in respiratory_failure, from 'grey and sweaty'. The pads and the central line follow flags pacing_pads_placed and central_access; the line is drawn in the right internal jugular, which the case does not specify.",
 "MGCA": " Sweating is drawn in presentation and adrenal_crisis, from the general status lines. The central line follows flag central_access and is drawn in the right internal jugular, which the case does not specify.",
 "DIPH": " Agitation is drawn on arrival, from 'agitated ... plucking at the leads', until the airway is protected. She is 'hot and dry', so she is never drawn sweating.",
}
def apply(pv, pre):
    pv["also"] = ALSO[pre]; pv["verify"] = pv["verify"] + VER[pre]
    out = {}
    for k in ("authoring_note", "verify", "rules", "also"): out[k] = pv[k]
    return out
for pre in ("CHFE", "MGCA"):
    p = os.path.join(ROOT, "cases", pre, pre + "-case.json"); j = json.load(open(p))
    j["content_keys"]["patient_visual"] = apply(j["content_keys"]["patient_visual"], pre)
    with open(p, "w") as f: json.dump(j, f, indent=1, ensure_ascii=False); f.write("\n")
    print("edited", p)
def pylit(o):
    s = json.dumps(o, indent=1, ensure_ascii=False)
    return s.replace(": true", ": True").replace(": false", ": False").replace(": null", ": None")
for pre in ("AFRVR", "DIPH"):
    d = os.path.join(ROOT, "cases", pre); p = os.path.join(d, "case_3_content.py"); s = open(p).read()
    m = re.search(r"\nPATIENT_VISUAL = (\{.*?\n\})\n\nLABS = \{", s, re.S); assert m
    pv = eval(m.group(1))
    s = s[:m.start()] + "\nPATIENT_VISUAL = " + pylit(apply(pv, pre)) + "\n\nLABS = {" + s[m.end():]
    open(p, "w").write(s); subprocess.check_call([sys.executable, os.path.join(d, "build_case.py"), d])

p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17d: four faces for four levels of alertness"; assert s.count(a) == 1
s = s.replace(a, """## v0.17e: three signs, three devices, and add-ons that stack

**Signs.** `jaundice` recolours the skin itself toward yellow, on the fills and not as an
overlay, so the neck and the chest inside a collar change with the face and the cloth never
does; it also gives the eyes a yellowed sclera, which the stock eyes lack entirely. On the
darker skins of the palette the skin change is slight and the sclera carries the sign.
`sweating` is a forehead sheen and ten beads that form, run and fade on separate clocks.
`agitation` is motion only: the head turns and will not settle, the eyes dart and hold, the
body shifts and the mouth works. It is built from unrelated slow sines and held random
targets so that it is never rhythmic, which is what separates it from the seizure.

**Devices.** `defib_pads` anterolateral, over the clothes, the apical pad mostly below the
frame. `central_line` in the patient's right internal jugular with a clear dressing and three
lumens. `bag_valve_mask` with a gloved hand in a C-E grip; the bag is squeezed as the chest
rises.

**`patient_visual.also`.** A first-match list cannot say "pads, and also a line, and also
sweating" without listing every combination against every airway state. `also` is a list of
`{when, addons}` in which every matching entry contributes; the engine unions them onto what
`rules` chose. Airway devices stay in `rules`, where only one can win. `also` is validated but
**does not appear in the review matrix**, which is a gap in the review artifact.

**Wired from the cases' own text and flags:** sweating in CHFE (arrival, impending failure),
AFRVR (respiratory failure) and MGCA (arrival, adrenal crisis); agitation on DIPH's arrival
until the airway is protected; pads from AFRVR's `pacing_pads_placed`; the line from
`central_access` in AFRVR and MGCA. **Not wired:** jaundice, which no case has, and the
bag-valve mask, because AFRVR's `preoxygenated` does not say by what, and no case has a flag
for bagging. The internal jugular site is the model's assumption; no case names one.

All six drawings are the model's and want a clinician's eye, the hand on the mask most of all.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
