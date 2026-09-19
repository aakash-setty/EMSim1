#!/usr/bin/env python3
"""One-shot: teach validate_case.py about patient.avatar and content_keys.patient_visual."""
import os, sys
ROOT = sys.argv[1]
p = os.path.join(ROOT, "engine", "validate_case.py"); s = open(p).read()
def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:60])
    s = s.replace(old, new)

rep('''    if "general_status" in ck:
        out.append(("general_status", ck["general_status"]["rules"], True))
''', '''    if "general_status" in ck:
        out.append(("general_status", ck["general_status"]["rules"], True))
    if isinstance(ck.get("patient_visual"), dict) and isinstance(ck["patient_visual"].get("rules"), list):
        out.append(("patient_visual", ck["patient_visual"]["rules"], True))
''')

rep('''def _check_ecg(p, errors, warnings):''', '''# The figure in the room (engine/patient.js). Both blocks are optional and a case with
# neither draws a default patient, so nothing written before this existed changes. The
# same spelling-check stance as the rhythm and the trace: an unknown key or value would
# be ignored by the renderer and the author would be looking at a patient with open eyes
# wondering why, so it is an error. The part and colour options are read from
# engine/patient-art.json, which is their one vocabulary. The add-on names are restated
# from SHARED["patient"]["addons"] in build_simulator.py, and engine-tests.js fails if
# this list, that one and the register() calls in patient.js disagree.
PATIENT_EYES = {"open", "closed"}
PATIENT_WOB = {"normal", "increased", "severe"}
PATIENT_ADDONS = {"gaze_left", "gaze_right", "nystagmus", "nasal_cannula"}
PATIENT_VISUAL_KEYS = {"eyes", "seizure", "work_of_breathing", "expression", "addons"}
PATIENT_AVATAR_PARTS = {"topType": "top", "accessoriesType": "accessories", "facialHairType": "facialHair",
                        "clotheType": "clothes", "graphicType": "graphic", "eyeType": "eyes",
                        "eyebrowType": "eyebrow", "mouthType": "mouth"}
PATIENT_AVATAR_COLOURS = {"skinColor": "skin", "hairColor": "hair", "facialHairColor": "facialHair",
                          "hatColor": "fabric", "clotheColor": "fabric"}
_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _patient_art():
    path = os.path.join(HERE, "patient-art.json")
    return json.load(open(path)) if os.path.exists(path) else None


def _check_expression(where, e, art, errors):
    if not isinstance(e, dict):
        errors.append(f"[patient] {where}: expression must be an object"); return
    for k, v in e.items():
        if k not in ("eyeType", "eyebrowType", "mouthType"):
            errors.append(f"[patient] {where}: expression has unknown key {k!r}")
        elif art and v not in art["options"][PATIENT_AVATAR_PARTS[k]]:
            errors.append(f"[patient] {where}: expression.{k} {v!r} is not an option")


def check_patient(case, errors, warnings):
    art = _patient_art()
    av = (case.get("patient") or {}).get("avatar")
    if av is not None:
        if not isinstance(av, dict):
            errors.append("[patient] patient.avatar must be an object")
        else:
            for k, v in av.items():
                if k in ("authoring_note", "verify"):
                    continue
                if k in PATIENT_AVATAR_PARTS:
                    if art and v not in art["options"][PATIENT_AVATAR_PARTS[k]]:
                        errors.append(f"[patient] avatar.{k} {v!r} is not an option; see "
                                      f"build/patient-lab.html for the list")
                elif k in PATIENT_AVATAR_COLOURS:
                    pal = art["colors"][PATIENT_AVATAR_COLOURS[k]] if art else {}
                    if art and v not in pal and not (isinstance(v, str) and _HEX.match(v)):
                        errors.append(f"[patient] avatar.{k} {v!r} is neither a palette name nor a hex colour")
                else:
                    errors.append(f"[patient] avatar has unknown key {k!r}; a misspelt key is ignored "
                                  f"by the renderer and draws the default")
    pv = case["content_keys"].get("patient_visual")
    if pv is None:
        return
    if not isinstance(pv, dict) or not isinstance(pv.get("rules"), list) or not pv["rules"]:
        errors.append("[patient] content_keys.patient_visual needs a non-empty rules list"); return
    for i, r in enumerate(pv["rules"]):
        where = f"patient_visual[{i}]"
        v = r.get("value")
        if not isinstance(v, dict):
            errors.append(f"[patient] {where}: value must be an object"); continue
        for k in v:
            if k not in PATIENT_VISUAL_KEYS:
                errors.append(f"[patient] {where}: unknown key {k!r}; the renderer would ignore it")
        if "eyes" in v and v["eyes"] not in PATIENT_EYES:
            errors.append(f"[patient] {where}: eyes {v['eyes']!r} is not one of {sorted(PATIENT_EYES)}")
        if "work_of_breathing" in v and v["work_of_breathing"] not in PATIENT_WOB:
            errors.append(f"[patient] {where}: work_of_breathing {v['work_of_breathing']!r} is not one of "
                          f"{sorted(PATIENT_WOB)}")
        if "seizure" in v and not isinstance(v["seizure"], bool):
            errors.append(f"[patient] {where}: seizure must be true or false")
        if "addons" in v:
            if not isinstance(v["addons"], list):
                errors.append(f"[patient] {where}: addons must be a list")
            else:
                for a in v["addons"]:
                    if a not in PATIENT_ADDONS:
                        errors.append(f"[patient] {where}: addon {a!r} is not one of {sorted(PATIENT_ADDONS)}")
        if v.get("expression") is not None:
            _check_expression(where, v["expression"], art, errors)
        if "respiratory_rate" in v:
            pass  # unreachable: caught as an unknown key above, on purpose. The rate is the monitor's.


def _check_ecg(p, errors, warnings):''')

rep('''        for i, r in enumerate(gs["rules"]):
            check_finding(f"general_status[{i}]", r["value"], "general_status")
''', '''        for i, r in enumerate(gs["rules"]):
            check_finding(f"general_status[{i}]", r["value"], "general_status")

    check_patient(case, errors, warnings)
''')

rep('''    """One-line rendering of a structured result payload for the review matrix."""
''', '''    """One-line rendering of a structured result payload for the review matrix."""
    if "kind" not in v and set(v) <= PATIENT_VISUAL_KEYS:
        bits = ["eyes " + v.get("eyes", "open")]
        if v.get("seizure"):
            bits.append("SEIZURE")
        if v.get("work_of_breathing", "normal") != "normal":
            bits.append("work of breathing " + v["work_of_breathing"])
        bits += ["+" + a for a in v.get("addons", [])]
        if v.get("expression"):
            bits.append("expression " + ",".join(f"{k}={x}" for k, x in v["expression"].items()))
        return "figure: " + ", ".join(bits)
''')
open(p, "w").write(s)
print("patched engine/validate_case.py")
