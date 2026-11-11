#!/usr/bin/env python3
"""Assemble ALLEY-case.json and ALLEY-binding-map.json from the parts in this folder.

    python3 cases/ALLEY/build_case.py cases/ALLEY

Same arrangement as cases/DKA. An edit made directly to ALLEY-case.json is lost by the
next run of this script.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from case_1_shell import META, PATIENT, PHASES
from case_2_actions import ACTIONS, FOLLOW_UPS
from case_3_content import EXAM, GENERAL_STATUS, PATIENT_VISUAL, PUPILS, LABS, IMAGING, CONSULTANTS
from case_4_interview import (TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES, KEY_TOPICS,
                              VOLUNTEER_SETTINGS)
from case_4_interview import TOPIC_MAP, EXTRA_COVERED
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "catalog"))
from interview_expand import expand_topics, apply_expansion, tune_file, report   # noqa: E402
EXPANSION = expand_topics("ALLEY", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "alley-intoxicated-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md",
   "authoring_requirements": "case-authoring-requirements.md (as of 11 November 2026)",
   "action_catalog": "action-catalog.json (0.3-draft, 306 entries, none added for this case)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "design_guide": "EMSim case design guide (Claude Doc, revision 28)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Seven live phases and three terminal. Three untreated tiers on a compressed clock, "
     "three held phases because a phase has one set of vitals and fomepizole freezes him at "
     "whichever tier he reached, and one improving phase. Bicarbonate without fomepizole and "
     "sedation are overlays, not phases."),
   "floor": (
     "The untreated_floor phase has no clock. The owner's design constraint is that the "
     "patient never arrests, seizes or needs a tube. The narration into it says so openly, "
     "and the debrief says what a real patient would do."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "note": ("Harmful is used for lorazepam, morphine and diphenhydramine before the patient is "
            "improving (owner, 11 November 2026)."),
 },
 "flag_namespace_note": (
   "fomepizole_given is permanent. bicarb_acting is timed: 180 seconds per bolus, 1800 for an "
   "infusion. sedated is timed, 150 seconds. reached_u1 and reached_u2 are granted by the "
   "transitions into the second and worst tiers and carry the vision tier. Two hidden "
   "targets, away_from_u0 and away_from_u1, carry 'a CT or the hallway in this phase'."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 3,
   "rationale": (
     "Three. On arrival: the gas at 40, the osmolality at 50 once the ethanol is back, the "
     "eyes at 55. All three land before the 180-second exit of the second tier in normal mode. No deterioration is guarded on a prompt: the drift is unguarded by the "
     "owner's decision."),
 },
 "prerequisite_semantics_note": (
   "Fomepizole, bicarbonate and folinic acid need a line, by the catalog's three-flag rule. "
   "Nephrology needs a gas and a chemistry resulted and a reason to suspect a toxic alcohol. "
   "Intubation is blocked by a prerequisite on a flag only a hidden, buttonless action sets, "
   "with the catalog's sedation-and-paralytic prerequisite waived so the block's message is "
   "the one spoken."),
 "content_keys": {
   "exam": EXAM,
   "general_status": GENERAL_STATUS,
   "patient_visual": PATIENT_VISUAL,
   "pupils": PUPILS,
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
   "note": "Any crystalloid bolus. A claim about fluid, not an agent."},
}

HIDDEN = {
 "attempt_discharge": ("Logged by the Handoff tab when discharge is chosen "
                       "(handoff.disposition_intercepts). Hidden.", "I'll get him up."),
 "attempt_observation": ("Logged by the Handoff tab when observation is chosen before the "
                         "antidote. Hidden.", "I'll put him in the hallway."),
 "attending_approves_intubation": ("Hidden, never credited, no button. Sets the flag the "
                                   "intubation block waits on, so the block can never be met in "
                                   "play (owner, 11 November 2026).", "Noted."),
 "gas_repeated": ("Hidden target. Credited by a gas sent while bicarbonate acts or once "
                  "improving. Read by the repeat-gas follow-up. Not a button.", "Noted."),
 "away_from_u0": ("Hidden target. Credited by a CT head or the hallway in the arrival phase. "
                  "Read by a transition. Not a button.", "Noted."),
 "away_from_u1": ("Hidden target. Credited by a CT head or the hallway in the second phase. "
                  "Read by a transition. Not a button.", "Noted."),
}
HISTORY = {
 "interview_topic_alcohol": "Satisfied by asking what he drank. The history tab draws no button.",
 "interview_topic_vision": "Satisfied by asking about his vision, or by the HEENT exam through also_satisfies.",
 "interview_topic_intent": "Satisfied by asking whether he meant to hurt himself.",
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
    if cid in HIDDEN:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None, "note": HIDDEN[cid][0],
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": HIDDEN[cid][1]})
        continue
    if cid in HISTORY:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None, "note": HISTORY[cid],
          "unmatched_placement": {"tab": "history", "group": "Not in the catalog"},
          "unmatched_narration": "Noted."})
        continue
    if cid == "folinic_acid":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": ("Case-only button, owner's decision of 11 November 2026. A catalog entry is "
                   "requested so that it does not point at the answer."),
          "unmatched_placement": {"tab": "interventions", "group": "Meds - Tox"},
          "unmatched_narration": "Giving folinic acid."})
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
    cpath = os.path.join(PACK, "ALLEY-case.json")
    bpath = os.path.join(PACK, "ALLEY-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    tpath = os.path.join(PACK, "ALLEY-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("ALLEY", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
