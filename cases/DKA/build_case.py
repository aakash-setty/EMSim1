#!/usr/bin/env python3
"""Assemble DKA-case.json and DKA-binding-map.json from the parts in this folder.

    python3 cases/DKA/build_case.py cases/DKA

Same arrangement as cases/AFRVR, cases/DIPH and cases/TAKO. An edit made directly to DKA-case.json is
lost by the next run of this script.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from case_1_shell import META, PATIENT, PHASES
from case_2_actions import ACTIONS, FOLLOW_UPS
from case_3_content import EXAM, GENERAL_STATUS, PATIENT_VISUAL, LABS, IMAGING, CONSULTANTS
from case_4_interview import (TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES, KEY_TOPICS,
                              VOLUNTEER_SETTINGS)
try:
    from case_4_interview import OUT_OF_SCOPE_BANK
except ImportError:          # before catalog/expand_interview_variants.py has run
    OUT_OF_SCOPE_BANK = []
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

CASE = {
 "case_id": "dka-hypokalemia-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (v0.9)",
   "authoring_requirements": "case-authoring-requirements.md (v0.9, with 6.8 and 6.9)",
   "action_catalog": "action-catalog.json (0.2-draft, plus three entries added for this case in v0.23)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "design_guide": "EMSim case design guide (Claude Doc, 5 October 2026)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Five clinical phases and one terminal. Arrival, potassium replaced, treated, and "
     "the two phases of the wrong order: potassium falling after early insulin, and "
     "recovering from it. No halted phase and no arrest."),
   "no_clock": (
     "Nothing happens to her because the learner waited. Every timed rule is the delayed "
     "consequence of an action, measured from the moment its guard became true. Approved "
     "by the directing physician on 6 October 2026."),
   "order_is_carried_by_phases": (
     "The condition language cannot express order. Insulin given in the arrival phase "
     "leads to potassium_falling. The same insulin given in potassium_replaced leads to "
     "treated."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. Nothing halts this case.",
 },
 "flag_namespace_note": (
   "Flags are permanent. insulin_given is set by any insulin, insulin_running by an "
   "infusion or a subcutaneous dose, insulin_stopped by the hold action, and "
   "insulin_restarted by the second administration of an infusion or subcutaneous dose. "
   "A learner who gave both an infusion and a subcutaneous dose before the hold has "
   "already set insulin_restarted, which is a known gap."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 5,
   "rationale": (
     "Five. On arrival: the monitor at 20 seconds, a bedside glucose at 40, bloods at 75, "
     "fluid at 100 and potassium at 130 once the chemistry is back. No deterioration "
     "depends on any of them, so the cap protects nothing here and five lets the "
     "potassium prompt be heard."),
 },
 "prerequisite_semantics_note": (
   "One case prerequisite: intravenous potassium needs a line. The catalog's vascular "
   "access rule is kept for everything else."),
 "content_keys": {
   "exam": EXAM,
   "general_status": GENERAL_STATUS,
   "patient_visual": PATIENT_VISUAL,
   "labs": LABS,
   "imaging": IMAGING,
   "consultants": CONSULTANTS,
 },
 "interview": {
   "authoring_notes": AUTHORING_NOTES,
   "global_answer_rules": GLOBAL_RULES,
   "out_of_scope_fallback": OUT_OF_SCOPE,
   "out_of_scope_bank": OUT_OF_SCOPE_BANK,
   "topics": TOPICS,
   **VOLUNTEER_SETTINGS,
   "key_topics": KEY_TOPICS,
   "key_topics_note": "Model judgment, unreviewed.",
 },
 "handoff": HANDOFF,
 "debrief_configuration": DEBRIEF,
}

# ------------------------------------------------------------------ binding map
COVERAGE = {
 "normal_saline_1l_bolus": {"also_covers_group": "crystalloid_bolus",
   "note": "Isotonic saline or a balanced crystalloid, either volume. A claim about fluid, not an agent."},
 "magnesium_sulfate": {"also_covers": ["magnesium_sulfate_bolus"],
   "note": "Either catalog entry is magnesium replacement."},
 "na_bicarbonate_bolus": {"also_covers": ["na_bicarbonate_infusion"],
   "note": "Either route is bicarbonate for a pH of 7.27."},
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    if cid == "handoff_submit":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": "The catalog has no handoff action; listed in its own known_gaps.",
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "I'll get the notes together for the unit."})
        continue
    row = {"case_id": cid, "catalog_id": cid}
    row.update(COVERAGE.get(cid, {}))
    BINDING_ROWS.append(row)

BINDING = {
 "map_version": "0.1",
 "case_id": CASE["case_id"],
 "status": ("DRAFT. Every also_covers row is a model judgment that two catalog entries are "
            "the same act for this case's purposes, and needs a physician's review."),
 "how_to_read": {
   "catalog_id equals case_id": "exact; nothing to review",
   "catalog_id null": "unmatched; not in the catalog",
   "also_covers / also_covers_group": "this case action claims several catalog entries",
 },
 "rows": BINDING_ROWS,
}

if __name__ == "__main__":
    cpath = os.path.join(PACK, "DKA-case.json")
    bpath = os.path.join(PACK, "DKA-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
