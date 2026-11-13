#!/usr/bin/env python3
"""Assemble SWEET-case.json and SWEET-binding-map.json from the parts in this folder.

    python3 cases/SWEET/build_case.py cases/SWEET

Same arrangement as cases/ALLEY. An edit made directly to SWEET-case.json is lost by the
next run of this script.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from case_1_shell import META, PATIENT, PHASES
from case_2_actions import ACTIONS, FOLLOW_UPS
from case_3_content import EXAM, GENERAL_STATUS, PATIENT_VISUAL, LABS, IMAGING, CONSULTANTS
from case_4_interview import (TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES, KEY_TOPICS,
                              VOLUNTEER_SETTINGS)
from case_4_interview import TOPIC_MAP, EXTRA_COVERED
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "catalog"))
from interview_expand import expand_topics, apply_expansion, tune_file, report   # noqa: E402
EXPANSION = expand_topics("SWEET", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "sweet-anaphylaxis-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md",
   "authoring_requirements": "case-authoring-requirements.md (as of 11 November 2026, with the child figure and age-banded ranges)",
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
     "Ten live phases and two terminal. The owner's six states, plus two intubated phases "
     "because every case can be intubated (authoring 8.5) and the owner's S6 is untrue of an "
     "intubated child: after the tube without an infusion, and ventilated with one. Two more "
     "for a stopped infusion (relapse, vent_relapse), so that the infusion order can stay a "
     "positive guard everywhere else and still run in 10 seconds."),
   "refractory_by_design": (
     "IM epinephrine never ends the reaction. The first ED dose works from 10 to 60 seconds "
     "and a later dose from 10 to 40, then he is worse (owner, 11 and 13 November 2026). The "
     "epinephrine infusion is the only thing that moves him to responding."),
   "infusion_preparation": (
     "Pressing the infusion orders it. Pharmacy has it running 10 seconds later (owner, 13 "
     "November 2026), whoever has been called: one delayed-consequence rule (guard_true) in "
     "each phase a learner can order it in (drip_runs in case_1_shell.py). After a stop, "
     "only a restart in the relapse phases brings him back, in 10 seconds. The infusion's "
     "own phases (responding, stabilized, ventilated) are where it runs."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. Nothing halts this case: every mistake plays out on the patient.",
 },
 "flag_namespace_note": (
   "epi_im_ed: any ED IM dose. epi_im_2: the second (flags_set_repeat). epi_onset (10 s) and "
   "epi_bridge_acting (40 s) are timed. epi_drip_ordered and epi_drip_stopped are permanent. "
   "relapsed and relapsed_vent are granted by the stop transitions, so a stop plays once. help_called from "
   "the PICU call. second_line from the second IV. sedated_p1 to p3 by phase (flags_set_if). "
   "fluid_x2 on the second bolus. rescued_once is granted by the rescue transition. Hidden "
   "targets carry 'done in this phase': bolus_here_p3, bolus_here_p4, fluid_here_p5, "
   "epi_here_p4, bridge_here_p7."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 4,
   "rationale": (
     "Four. On arrival: epinephrine at 30, the bolus at 45, posture at 50. In phase 2: the "
     "infusion at 30, epinephrine at 30 only if none was given on arrival, the PICU call at "
     "45, the bolus at 45 if none yet. In phase 3: the infusion at 30, the bolus here at 40, "
     "the PICU call at 45. The prompts the deteriorations rest on are the earliest in each "
     "phase."),
 },
 "prerequisite_semantics_note": (
   "The infusion needs the monitor and a second line (an IV and an IO, a second IV, or a "
   "central line), as well as the catalog's line rule. Everything else keeps the catalog's "
   "rules."),
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
 "normal_saline_500ml_bolus": {"also_covers": ["lactated_ringer_s_500ml_bolus"],
   "note": ("Either crystalloid, 500 mL. The catalog's crystalloid_bolus group is split by volume "
            "here so the 1 L bag can carry its own nurse line (25 mL/kg at 40 kg).")},
 "normal_saline_1l_bolus": {"also_covers": ["lactated_ringer_s_1l_bolus"],
   "note": "Either crystalloid, 1 L."},
}

HIDDEN = {
 "bolus_here_p3": "Hidden target. Credited by a bolus given while floppy. Read by a transition.",
 "bolus_here_p4": "Hidden target. Credited by a bolus at the edge of arrest. Read by the rescue.",
 "fluid_here_p5": "Hidden target. Credited by a bolus once the infusion runs. Read by a transition.",
 "epi_here_p4": "Hidden target. Credited by IM or IV epinephrine at the edge of arrest. Read by the rescue.",
 "bridge_here_p7": "Hidden target. Credited by IM or IV epinephrine after the tube. Read by a transition.",
 "reassessed_after_epi": "Hidden target. Credited by an airway, breathing, circulation or lung exam after an ED dose.",
 "drip_restarted": "Hidden target. Credited by the infusion pressed again after a stop. Read by a transition.",
}
HISTORY = {
 "interview_topic_epi_given": "Satisfied by asking what was given before arrival.",
 "interview_topic_allergies": "Satisfied by asking about allergies.",
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    if cid == "handoff_submit":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": "The catalog has no handoff action; listed in its own known_gaps.",
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "I'll call PICU and give them the story."})
        continue
    if cid in HIDDEN:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None, "note": HIDDEN[cid],
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "Noted."})
        continue
    if cid in HISTORY:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None, "note": HISTORY[cid],
          "unmatched_placement": {"tab": "history", "group": "Not in the catalog"},
          "unmatched_narration": "Noted."})
        continue
    if cid == "lay_back_legs_raised":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": ("Case-only button, owner's defaults of 11 November 2026 (B4). A catalog entry "
                   "'Supine, legs elevated' is requested so that it does not point at the answer."),
          "unmatched_placement": {"tab": "interventions", "group": "Procedures"},
          "unmatched_narration": "Lying him back and lifting his legs."})
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
    cpath = os.path.join(PACK, "SWEET-case.json")
    bpath = os.path.join(PACK, "SWEET-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    tpath = os.path.join(PACK, "SWEET-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("SWEET", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
