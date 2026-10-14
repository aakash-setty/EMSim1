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
from case_4_interview import TOPIC_MAP, EXTRA_COVERED
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

# The interview bank, expanded from the shared phrasing library at build time. The
# withheld slice becomes the tuning file. Nothing is stored between builds.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "catalog"))
from interview_expand import expand_topics, apply_expansion, tune_file, report   # noqa: E402
EXPANSION = expand_topics("DKA", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)   # the held-out file is a source, read beside the sources
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "dka-hypokalemia-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (as of v0.24)",
   "authoring_requirements": "case-authoring-requirements.md (v0.24)",
   "action_catalog": ("action-catalog.json (0.3-draft, 305 entries, four of them added for "
                      "this case: three in v0.23 and insulin glargine in v0.23a)"),
   "diagnosis_catalog": "diagnosis-catalog.json (499 entries)",
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
     "recovering from it. No halted phase and no arrest. The audit fix of 7 October 2026 "
     "added no phase."),
   "no_clock": (
     "Nothing happens to her because the learner waited. Every timed rule is the delayed "
     "consequence of an action, measured from the moment its guard became true. Approved "
     "by the directing physician on 6 October 2026."),
   "order_is_carried_by_phases": (
     "The condition language cannot express order. Insulin given in the arrival phase "
     "leads to potassium_falling. The same insulin given in potassium_replaced leads to "
     "treated. Two hidden case actions close what phases alone left open. early_insulin "
     "is credited when rapid insulin is ordered in the arrival phase, so a learner whose "
     "potassium finished first still falls, five seconds after it finishes. "
     "insulin_restart is credited when an infusion or a subcutaneous dose is ordered in "
     "the recovering phase, so one order after the rescue is the restart. The race table "
     "is in DKA-SEED.md."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. Nothing halts this case.",
 },
 "flag_namespace_note": (
   "Flags are permanent. insulin_given is set by any rapid insulin, insulin_running by "
   "an infusion or a subcutaneous dose, and insulin_stopped by the hold action. No flag "
   "says when. Four hidden case actions carry that, each credited through "
   "also_satisfies on the phase at the moment of the order: early_insulin, "
   "insulin_restart and repeat_potassium_level. The repeat-granted flags of v0.23 "
   "(insulin_restarted and chem_repeated) are gone. fluids_given is set by a crystalloid "
   "bolus or infusion."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 5,
   "rationale": (
     "Five. On arrival: the monitor at 20 seconds, a bedside glucose at 40, bloods at 75, "
     "fluid at 100 and potassium at 110 once the chemistry is back, with its escalation "
     "at 170. In the falling phase: hold insulin at 25, a twelve-lead at 70, fluid at 100 "
     "and potassium at 110. In each ready phase: insulin at 45 and fluid at 100. No "
     "deterioration depends on any of them, so the cap protects nothing here and five "
     "lets the potassium prompt be heard."),
 },
 "prerequisite_semantics_note": (
   "One case prerequisite: intravenous potassium needs a line, by the catalog's own "
   "three-flag condition (peripheral, central or intraosseous). The catalog's vascular "
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

# Case-only actions that nothing presses (authoring 19, 6.9 and 8.2). Each needs a
# placement or the build does not create it. The handoff tab draws no button and the
# microphone does not read it. hidden keeps them out of search.
HIDDEN_TARGETS = {
 "early_insulin": (
   "Hidden target. Credited through also_satisfies when rapid insulin is ordered in the "
   "arrival phase. Read by a transition in potassium_replaced. Not a button."),
 "insulin_restart": (
   "Hidden target. Credited through also_satisfies when an insulin infusion or a "
   "subcutaneous dose is ordered in the recovering phase. Read by the exit of that "
   "phase, and it carries the restart prompt. Not a button."),
 "repeat_potassium_level": (
   "Hidden target. Credited through also_satisfies when a chemistry is sent once the "
   "potassium has run in. Read by the repeat-level follow-up. Not a button."),
 "potassium_maintenance": (
   "Hidden target. Credited through also_satisfies when intravenous potassium is ordered "
   "again once the level is 3.5 or more. Critical in those phases, and it carries the "
   "prompt for potassium in the fluids. Not a button."),
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
    tpath = os.path.join(PACK, "DKA-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("DKA", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
