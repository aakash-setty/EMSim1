#!/usr/bin/env python3
"""Assemble SCOOT-case.json and SCOOT-binding-map.json from the parts in this folder.

    python3 cases/SCOOT/build_case.py cases/SCOOT

Same arrangement as cases/DKA, copied 19 October 2026. An edit made directly to SCOOT-case.json is
lost by the next run of this script.
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

# The interview bank, expanded from the shared phrasing library at build time. The
# withheld slice becomes the tuning file. Nothing is stored between builds.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "catalog"))
from interview_expand import expand_topics, apply_expansion, tune_file, report   # noqa: E402
EXPANSION = expand_topics("SCOOT", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)   # the held-out file is a source, read beside the sources
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "scoot-epidural-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (as of 19 October 2026, not opened for this case)",
   "authoring_requirements": "case-authoring-requirements.md (as of 19 October 2026)",
   "action_catalog": "action-catalog.json (0.3-draft, 305 entries). No entry added for this case",
   "diagnosis_catalog": "diagnosis-catalog.json (as of 19 October 2026)",
   "design_guide": "EMSim case design guide (repository copy of 7 October 2026)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Four live phases and two terminals. Arrival, the decline, herniation and temporized, "
     "approved as the states by Aakash Setty on 19 October 2026, plus brainstem compression "
     "(the clock's terminal) and case_complete. No halted phase."),
   "time_guarded_transitions": (
     "The decline is scheduled natural history at 240 seconds. Herniation is a deterioration "
     "on inaction at 300 seconds, guarded on the flag the neurosurgery consult sets. The "
     "consult needs a resulted head CT. In herniation, osmotherapy credited in that phase leads to "
     "temporized after 15 seconds, and without it brainstem compression follows at 300 "
     "seconds. The race table is in SCOOT-SEED.md section 2.4."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. Nothing halts this case (model default, SCOOT-SEED.md section 0).",
 },
 "flag_namespace_note": (
   "Flags are permanent. intubated is set by the tube, neurosurgery_called by the neurosurgery "
   "consult, handoff_submitted by the handoff. sedation_given and paralytic_given come from "
   "the catalog. Order and place are carried by four hidden case actions credited through "
   "also_satisfies: neuro_reexamined, neurosurgery_updated, osmotherapy_for_herniation and "
   "post_intubation_sedation."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 5,
   "rationale": (
     "Five. On arrival: the monitor at 20 and a neuro exam at 60. No neurosurgery or CT "
     "prompt on arrival (owner, 19 and 20 October 2026). In the decline: the repeat "
     "exam at 15, neurosurgery at 25 with an escalation at 35, the call back at 40 and the CT "
     "at 50. In herniation: osmotherapy at 20 with an escalation at 60, neurosurgery at 25, a "
     "tube at 30, the call back at 40 and the CT at 50. The herniation and the brainstem "
     "clocks rest on the neurosurgery and osmotherapy prompts, which come first or second in "
     "their phase, so a cap of five never suppresses them."),
 },
 "prerequisite_semantics_note": (
   "One case prerequisite: the neurosurgery consult needs a resulted head CT or CT/CTA, with "
   "the neurosurgeon's request as the failure message (authoring 9.5). The catalog's are "
   "kept: a line before every intravenous drug, "
   "central access for concentrated saline, sedation and a paralytic before the tube."),
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
 "labetalol_bolus": {"also_covers": ["labetalol_drip", "nicardipine_drip", "esmolol_drip",
                                     "nitroprusside_drip", "nitroglycerin_drip", "nitroglycerin",
                                     "nitroglycerin_sublingual", "metoprolol_bolus"],
   "note": ("Every catalog route to lowering his blood pressure. A claim about the act, not "
            "an agent. The shared note says 'the pressure', not one drug.")},
 "normal_saline_1l_bolus": {"also_covers_group": "crystalloid_bolus",
   "note": "Isotonic saline or a balanced crystalloid, either volume."},
}

# Case-only actions that nothing presses (authoring 19 and 22.2). Each needs a placement
# or the build does not create it. The handoff tab draws no button and the microphone does
# not read it. hidden keeps them out of search.
HIDDEN_TARGETS = {
 "neuro_reexamined": "Hidden target. Credited by a neuro exam in the decline phase. Not a button.",
 "neurosurgery_updated": "Hidden target. Credited by a neurosurgery call in any phase after arrival. Not a button.",
 "osmotherapy_for_herniation": (
   "Hidden target. Credited by mannitol or hypertonic saline in the herniation phase. Guards "
   "the exit and the terminal clock there. Not a button."),
 "post_intubation_sedation": (
   "Hidden target. Credited by sedation or analgesia once intubated. Discharges the "
   "follow-up. Not a button."),
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    if cid in HIDDEN_TARGETS:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": HIDDEN_TARGETS[cid],
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "Noted."})
        continue
    if cid == "handoff_submit":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": "The catalog has no handoff action; listed in its own known_gaps.",
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "I'll get the notes together for the OR."})
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
    cpath = os.path.join(PACK, "SCOOT-case.json")
    bpath = os.path.join(PACK, "SCOOT-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    tpath = os.path.join(PACK, "SCOOT-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("SCOOT", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
