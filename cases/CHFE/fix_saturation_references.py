#!/usr/bin/env python3
"""ONE-TIME MIGRATION for CHFE-case.json, third of three. Re-running it fails its own
assertions.

Two loose ends from dropping the arrival saturation from 87 to 85.

1. Every place the case QUOTES the arrival saturation in prose. The validator caught the
   EMS handover, which is the one that matters most, because a resident reads the handover
   and then attaches a monitor and sees a different number thirty seconds later. It cannot
   catch the other two, which are inside a consultant's reply and a diagnosis explanation,
   because they are free text.

2. The venous gas authored for the phases either side of arrival had a payload-level
   `abnormal` of true over components that are all in range, which the payload contract
   forbids and the validator refused. It is the first result in this case that is entirely
   normal: the gas of a patient whose respiratory acidosis has corrected.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE

case = json.load(open(CASE))
assert "rewrite_findings_and_speech" in case["migrations"], "run the companions first"
assert "fix_saturation_references" not in case["migrations"], "already applied"

m = case["patient"]   # both handover strings live on the patient, not the metadata
a, b = "Sats were 84 percent on room air at the house, 87 on six litres now.", \
       "Sats were 82 percent on room air at the house, 85 on six litres now."
assert a in m["ems_handover_text"]
m["ems_handover_text"] = m["ems_handover_text"].replace(a, b)

a, b = "he's still only holding 87% on six litres by nasal cannula.", \
       "he's still only holding 85% on six litres by nasal cannula."
assert a in m["arrival_handover"]
m["arrival_handover"] = m["arrival_handover"].replace(a, b)

cc = case["content_keys"]["consultants"]["consult_critical_care"]
rules = cc if isinstance(cc, list) else cc["rules"]
hits = [r for r in rules if "87 percent on a cannula" in json.dumps(r.get("value"))]
assert len(hits) == 1
hits[0]["value"] = hits[0]["value"].replace("at 87 percent on a cannula",
                                            "at 85 percent on a cannula")

for d in case["handoff"].get("additional_diagnoses", []):
    if "a saturation of 87 percent" in d.get("explanation", ""):
        d["explanation"] = d["explanation"].replace("a saturation of 87 percent",
                                                    "a saturation of 85 percent")
        break
else:
    raise AssertionError("the additional diagnosis quoting 87 percent has moved")

vbg = case["content_keys"]["labs"]["labs_vbg"]
hit = [r for r in vbg["rules"] if r["when"] == "phase is stabilizing OR phase is improving"]
assert len(hit) == 1
v = hit[0]["value"]
assert v["abnormal"] is True and not any(c["abnormal"] for c in v["components"])
v["abnormal"] = False

case["migrations"].append("fix_saturation_references")
json.dump(case, open(OUT, "w"), indent=1, ensure_ascii=False)
open(OUT, "a").write("\n")
print("wrote", OUT)
