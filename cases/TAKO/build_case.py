#!/usr/bin/env python3
"""Assemble TAKO-case.json and TAKO-binding-map.json from the parts in this folder.

    python3 cases/TAKO/build_case.py cases/TAKO

Same arrangement as cases/AFRVR and cases/DIPH. An edit made directly to TAKO-case.json is
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
 "case_id": "takotsubo-lvoto-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (v0.9)",
   "authoring_requirements": "case-authoring-requirements.md (v0.9, with 6.8 and the v0.21 note)",
   "action_catalog": "action-catalog.json (0.2-draft, plus no entries added for this case)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "design_guide": "EMSim case design guide (Claude Doc, 5 October 2026)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Four clinical phases and one terminal: arrival, the obstruction declaring itself, "
     "worse on the wrong treatment or none, and steadied. No halted phase and no arrest."),
   "the_scripted_drop": (
     "The arrival phase ends at 180 seconds whatever is done, so every learner meets "
     "outflow obstruction. A learner with fluid and a vasoconstrictor already running "
     "goes straight to steadied."),
   "the_cardiologist": (
     "On the directing physician's instruction the nurse recommends cardiology twenty "
     "seconds after the pressure falls, the cardiologist gives the plan outright, and "
     "ninety seconds after being called takes over and steadies her."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. See phase_notes.no_halted_phase.",
 },
 "flag_namespace_note": (
   "Flags are permanent. An inotrope that has been stopped is inotrope_given with "
   "inotrope_stopped, and 'active' is the first without the second. Restarting a stopped "
   "inotrope has no further effect, which is a limit of the tool. vasoconstrictor_running "
   "is set by phenylephrine, vasopressin and norepinephrine."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 4,
   "rationale": (
     "Four. On arrival: the monitor at 15 seconds, the ECG at 40, aspirin at 90 and the "
     "catheterization laboratory at 130. With a low pressure: cardiology at 20, fluid at "
     "60 and a vasoconstrictor at 80, which are the three the 240-second deterioration "
     "rests on and are the earliest."),
 },
 "prerequisite_semantics_note": "No case prerequisites. The catalog's vascular access rule is kept.",
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
   "note": "A claim about volume, not an agent."},
 "phenylephrine_drip": {"also_covers": ["vasopressin_drip"],
   "note": "Either is a vasoconstrictor with no inotropic effect."},
 "nitroglycerin": {"also_covers": ["nitroglycerin_sublingual", "nitroglycerin_drip", "nitroprusside_drip"],
   "note": "Every route to lowering preload and afterload carries the same tag and effect."},
 "dobutamine_drip": {"also_covers": ["epinephrine_drip", "dopamine_drip"],
   "note": "Every catecholamine inotrope is the same act here."},
 "stop_dobutamine": {"also_covers": ["stop_epinephrine", "stop_dopamine"],
   "note": "Stopping any of them is the same rescue."},
 "esmolol_drip": {"also_covers": ["metoprolol_bolus", "labetalol_bolus", "labetalol_drip", "propranolol_bolus"],
   "note": "Every beta blocker carries the same timing rule. Esmolol is the one to prefer because it is short-acting."},
 "tenecteplase_tnk_bolus": {"also_covers": ["alteplase_tpa"],
   "note": "Either thrombolytic is the same decision."},
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
    if cid == "consult_activate_cath_lab":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": ("Case-only button on the Consults tab, on the directing physician's "
                   "instruction of 6 October 2026. Not in the catalog."),
          "unmatched_placement": {"tab": "consultations", "group": "Consultations"},
          "unmatched_narration": "Calling the cath lab activation now."})
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
    cpath = os.path.join(PACK, "TAKO-case.json")
    bpath = os.path.join(PACK, "TAKO-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
