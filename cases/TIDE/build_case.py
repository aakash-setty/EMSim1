#!/usr/bin/env python3
"""Assemble TIDE-case.json and TIDE-binding-map.json from the parts in this folder.

    python3 cases/TIDE/build_case.py cases/TIDE

Same arrangement as cases/DKA. An edit made directly to TIDE-case.json is lost by the next run.
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
EXPANSION = expand_topics("TIDE", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "tide-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md",
   "authoring_requirements": "case-authoring-requirements.md (as of 4 November 2026)",
   "action_catalog": "action-catalog.json (0.3-draft, with High-Flow Nasal Cannula added 4 November 2026)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "design_guide": "EMSim case design guide (Claude Doc, 5 October 2026)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "ventilation": {"when": "flag intubated set", "respiratory_rate": 24,
                 "note": "The ventilator rate a learner would set for a high carbon dioxide on low tidal volumes. Model output."},
 "phase_notes": {
   "count_justification": (
     "Ten live phases and two terminal. Two problems in sequence, each with its own turning "
     "points: the shock (arrival, transient response, low before fluid, low after fluid, very "
     "low, held) and the breathing (failing, tiring), plus the two outcomes of the tube "
     "(collapse, ventilated). Agreed with the owner in the case map on 4 November 2026."),
   "severe_shock_flag": (
     "Every timed rule into worsening_shock grants severe_shock. The lactate, the gases and the "
     "chemistry read it from then on, so a late vasopressor leaves a visible mark (owner B3)."),
   "no_time_jump": "Owner decision of 4 November 2026: no two-hour jump. Phase 7 arrives on an openly compressed clock.",
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. Nothing halts this case.",
 },
 "flag_namespace_note": (
   "Device flags o2_nc, o2_nrb, o2_hfnc and o2_niv are permanent, so the highest device used "
   "is assumed for the gas and for preoxygenation (known gap 3). fluid_given, fluid_twice and "
   "fluid_stacked come from the crystalloid count. pressor_running is set by any vasopressor "
   "drip, pressor_stopped and pressor_restarted only move the monitor. preox_pp marks "
   "positive-pressure preoxygenation. severe_shock is granted by a transition."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 4,
   "rationale": (
     "Four. On arrival: oxygen at 20, fluid at 40, high flow or NIV at 45 and the antibiotic at "
     "50. The fluid prompt, which the 180 s deterioration rests on, comes before the last two. "
     "In every later phase the prompt a deterioration rests on is the earliest."),
 },
 "content_keys": {
   "exam": EXAM,
   "general_status": GENERAL_STATUS,
   "patient_visual": PATIENT_VISUAL,
   "labs": LABS,
   "imaging": IMAGING,
   "consultants": CONSULTANTS,
 },
 "review_hints": {
   "note": "Pairs the review matrix would otherwise call plausible.",
   "implausible": [
     {"flag": "preox_pp", "requires": "flag o2_niv set", "why": "Granted only by NIV or a bag in the failing phases, or preoxygenation after NIV."},
     {"flag": "fluid_stacked", "requires": "flag fluid_given set", "why": "The third bolus implies the first."},
     {"flag": "pressor_restarted", "requires": "flag pressor_stopped set", "why": "Granted only after a stop."},
   ],
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

COVERAGE = {
 "normal_saline_1l_bolus": {"also_covers_group": "crystalloid_bolus",
   "note": "Saline or a balanced crystalloid, either volume. One count per bolus (known gap 9)."},
}

HIDDEN_TARGETS = {
 "hidden_oxygen": "Credited by any oxygen device. Critical on arrival, with the oxygen prompt.",
 "hidden_support": "Credited by high flow or NIV. Critical in phases 1 to 6, with its prompt.",
 "hidden_reassessed": "Credited by a circulation exam, an ultrasound or a lactate after fluid.",
 "hidden_beta_lactam": "Credited by ceftriaxone, cefotaxime, ampicillin or a broader beta-lactam. Carries the antibiotic prompt.",
 "hidden_atypical": "Credited by azithromycin, levofloxacin or moxifloxacin.",
 "hidden_push_dose": "Credited by a push-dose vasopressor bolus. Recommended after an unsupported tube.",
 "hidden_sedation": "Credited by a sedative or analgesic after the tube. Ungraded intubation care.",
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    if cid in HIDDEN_TARGETS:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": "Hidden target. " + HIDDEN_TARGETS[cid] + " Not a button.",
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "Noted."})
        continue
    if cid == "handoff_submit":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": "The catalog has no handoff action.",
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "I'll get the notes together for the ICU."})
        continue
    row = {"case_id": cid, "catalog_id": cid}
    row.update(COVERAGE.get(cid, {}))
    BINDING_ROWS.append(row)

BINDING = {
 "map_version": "0.1",
 "case_id": CASE["case_id"],
 "status": ("DRAFT. The coverage row is a model judgment that the four crystalloid boluses are "
            "one act here, and needs a physician's review."),
 "how_to_read": {
   "catalog_id equals case_id": "exact; nothing to review",
   "catalog_id null": "unmatched; not in the catalog",
   "also_covers / also_covers_group": "this case action claims several catalog entries",
 },
 "rows": BINDING_ROWS,
}

if __name__ == "__main__":
    cpath = os.path.join(PACK, "TIDE-case.json")
    bpath = os.path.join(PACK, "TIDE-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    tpath = os.path.join(PACK, "TIDE-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("TIDE", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
