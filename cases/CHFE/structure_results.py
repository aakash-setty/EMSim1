#!/usr/bin/env python3
"""ONE-TIME MIGRATION, already applied to CHFE-case.json. Kept as the record of
what changed and why; re-running it on an already-migrated file will fail its own
assertions, which is the intended safety.

Convert the case's authored lab and imaging results from prose strings into the
structured payload the action catalog defines (kind / components / abnormal), so the
renderer can mark abnormal values without guessing.

The catalog's default_result_contract is explicit: "A case that overrides a value must
set abnormal itself; the renderer does not recompute in-range." Parsing "(high)" out of
a prose string at render time would be exactly the recomputation the contract forbids,
and it would fail silently on any value the author phrased differently. So the flags are
authored here, once, in the file.

Nothing clinical changes. Every number, unit and interpretation below is carried across
unchanged from the prose the case already contained; the reference intervals are taken
from the catalog defaults where the catalog has the same analyte, and are marked
UNVERIFIED where they are not.
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE


def C(label, value, unit, ref, abn=False):
    return {"label": label, "value": value, "unit": unit, "reference_range": ref, "abnormal": abn}


def panel(*rows, **kw):
    comps = list(rows)
    return dict(kind="panel", abnormal=any(c["abnormal"] for c in comps), components=comps, **kw)


def val(*rows, **kw):
    comps = list(rows)
    return dict(kind="value", abnormal=any(c["abnormal"] for c in comps), components=comps, **kw)


def report(text, abnormal=True, **kw):
    return dict(kind="report", abnormal=abnormal, report=text, **kw)


T = True

LABS = {
 "labs_cbc": [
   (None, panel(
     C("WBC", "8.2", "x10^9/L", "4.0-11.0"),
     C("Hemoglobin", "12.4", "g/dL", "13.5-17.5 (M)", T),
     C("Hematocrit", "37.5", "%", "41-53 (M)", T),
     C("MCV", "88", "fL", "80-100"),
     C("Platelets", "232", "x10^9/L", "150-400"),
     comment="Differential unremarkable."))],

 "labs_bmp": [
   ("flag diuretic_given set", panel(
     C("Sodium", "134", "mEq/L", "135-145", T),
     C("Potassium", "3.6", "mEq/L", "3.5-5.0"),
     C("Chloride", "97", "mEq/L", "98-107", T),
     C("Bicarbonate", "26", "mEq/L", "22-29"),
     C("BUN", "34", "mg/dL", "7-20", T),
     C("Creatinine", "1.71", "mg/dL", "0.6-1.2; stated baseline 1.4", T),
     C("Glucose", "166", "mg/dL", "70-140 (random)", T),
     C("Calcium", "8.9", "mg/dL", "8.5-10.2"),
     comment="Potassium has fallen from 4.4 and creatinine has risen from 1.62 after diuresis.")),
   (None, panel(
     C("Sodium", "133", "mEq/L", "135-145", T),
     C("Potassium", "4.4", "mEq/L", "3.5-5.0"),
     C("Chloride", "96", "mEq/L", "98-107", T),
     C("Bicarbonate", "25", "mEq/L", "22-29"),
     C("BUN", "32", "mg/dL", "7-20", T),
     C("Creatinine", "1.62", "mg/dL", "0.6-1.2; stated baseline 1.4", T),
     C("Glucose", "172", "mg/dL", "70-140 (random)", T),
     C("Calcium", "8.8", "mg/dL", "8.5-10.2")))],

 "labs_bnp": [
   (None, val(C("NT-proBNP", "9600", "pg/mL",
                "under 300 rules out; age-adjusted rule-in 900 at 50 to 75 years", T),
     verify="CONVERTED in v0.9 from the originally authored BNP 2840 (reference under 100) "
            "because the catalog entry is NT-proBNP. Approximate ratio, cut-offs cited from "
            "memory. UNVERIFIED."))],

 "labs_troponin_hs": [
   (None, val(C("High-sensitivity troponin I", "62", "ng/L", "99th percentile URL 34 (M)", T),
     verify="The catalog default for the bound entry is a qualitative troponin T. Assay, analyte "
            "and reference interval all differ. UNVERIFIED."))],

 "labs_vbg": [
   ("phase is post_intubation_hypotension", panel(
     C("pH (venous)", "7.24", "", "7.31-7.41 (venous)", T),
     C("pCO2", "46", "mmHg", "41-51 (venous)"),
     C("Bicarbonate", "19", "mEq/L", "22-26", T),
     C("Base excess", "-7", "mEq/L", "-2 to +2", T),
     C("Lactate", "3.4", "mmol/L", "under 2.0", T),
     comment="Metabolic acidosis with an inadequate respiratory response on current ventilator settings.")),
   ("phase is intubated_stabilized", panel(
     C("pH (venous)", "7.32", "", "7.31-7.41 (venous)"),
     C("pCO2", "42", "mmHg", "41-51 (venous)"),
     C("Bicarbonate", "22", "mEq/L", "22-26"),
     C("Base excess", "-3", "mEq/L", "-2 to +2", T),
     C("Lactate", "2.2", "mmol/L", "under 2.0", T),
     comment="Improving.")),
   ("flag on_niv set", panel(
     C("pH (venous)", "7.36", "", "7.31-7.41 (venous)"),
     C("pCO2", "44", "mmHg", "41-51 (venous)"),
     C("Bicarbonate", "25", "mEq/L", "22-26"),
     C("Base excess", "0", "mEq/L", "-2 to +2"),
     C("Lactate", "1.4", "mmol/L", "under 2.0"),
     comment="The respiratory acidosis has corrected.")),
   (None, panel(
     C("pH (venous)", "7.29", "", "7.31-7.41 (venous)", T),
     C("pCO2", "54", "mmHg", "41-51 (venous)", T),
     C("Bicarbonate", "25", "mEq/L", "22-26"),
     C("Base excess", "-1", "mEq/L", "-2 to +2"),
     C("Lactate", "2.1", "mmol/L", "under 2.0", T),
     comment="Acute respiratory acidosis."))],

 "labs_lactate": [
   ("phase is post_intubation_hypotension", val(C("Lactate", "3.4", "mmol/L", "under 2.0", T))),
   ("phase is intubated_stabilized", val(C("Lactate", "2.2", "mmol/L", "under 2.0", T),
     comment="Falling.")),
   ("flag on_niv set", val(C("Lactate", "1.4", "mmol/L", "under 2.0"))),
   (None, val(C("Lactate", "2.1", "mmol/L", "under 2.0", T)))],

 "labs_lft": [
   (None, panel(
     C("AST", "46", "U/L", "10-40", T),
     C("ALT", "41", "U/L", "7-40", T),
     C("Alkaline phosphatase", "132", "U/L", "40-129", T),
     C("Total bilirubin", "1.4", "mg/dL", "0.2-1.2", T),
     C("Albumin", "3.6", "g/dL", "3.5-5.0"),
     comment="Pattern consistent with hepatic congestion."))],

 "labs_dimer": [
   (None, val(C("D-dimer", "0.94", "mcg/mL FEU", "under 0.50", T)))],
}


MIGRATION_MARKER = "structure_results"


def refuse_if_already_migrated(case):
    """A one-time migration that silently re-runs destroys the thing it created.

    structure_results.py stores the original prose alongside the structured payload;
    running it twice overwrites that prose with the payload, losing the diffable record
    the reviewing physician needs. The docstring said re-running would fail its own
    assertions. It did not: the assertions checked rule counts and conditions, both of
    which still hold after migration. This checks the thing that actually changes.
    """
    if MIGRATION_MARKER in (case.get("migrations") or []):
        raise SystemExit(
            f"{MIGRATION_MARKER} has already been applied to this case file. "
            f"Re-running would overwrite migrated data. Nothing was changed.")


def mark_migrated(case):
    case.setdefault("migrations", [])
    if MIGRATION_MARKER not in case["migrations"]:
        case["migrations"].append(MIGRATION_MARKER)


def main():
    case = json.load(open(CASE))
    refuse_if_already_migrated(case)
    labs = case["content_keys"]["labs"]
    changed = 0

    for key, rules in LABS.items():
        assert key in labs, key
        existing = labs[key]["rules"]
        assert len(existing) == len(rules), (key, len(existing), len(rules))
        for old, (when, payload) in zip(existing, rules):
            assert old["when"] == when, (key, old["when"], when)
            old["prose"] = old["value"]          # keep the original for review
            old["value"] = payload
            changed += 1
        labs[key]["result_shape"] = "structured"

    # imaging: wrap the authored prose as a report payload carrying an abnormal flag
    for key, block in case["content_keys"]["imaging"].items():
        if key == "authoring_note":
            continue
        for r in block["rules"]:
            if isinstance(r["value"], str):
                r["value"] = report(r["value"], abnormal=(key != "ct_pulmonary_angiogram"))
                changed += 1
        block["result_shape"] = "structured"

    case["result_payload_contract"] = {
        "shape": "kind is panel, value or report. panel and value carry components; report carries report text.",
        "abnormal": "Set per component by the author. The renderer marks abnormal components and does not "
                    "recompute from the reference range, per the action catalog's default_result_contract.",
        "resolution_order": ["case content_keys for the resolved rule",
                             "action catalog entry.default_result",
                             "validator error if neither exists"],
        "prose_field": "Every converted rule keeps the original authored prose in a sibling 'prose' key so "
                       "the physician reviewer can diff the structured payload against what was written.",
        "unverified": "Reference intervals are assay- and institution-specific. Those taken from the "
                      "catalog defaults are themselves unverified; those the catalog does not cover are "
                      "marked with a verify field.",
    }
    mark_migrated(case)
    json.dump(case, open(OUT, "w"), indent=1)
    print("converted", changed, "result payloads")


if __name__ == "__main__":
    main()
