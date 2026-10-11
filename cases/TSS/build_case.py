#!/usr/bin/env python3
"""Assemble TSS-case.json and TSS-binding-map.json from the parts in this folder.

    python3 cases/TSS/build_case.py cases/TSS

Same arrangement as cases/AFRVR and cases/DIPH. An edit made directly to TSS-case.json is
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
EXPANSION = expand_topics("TSS", TOPICS, TOPIC_MAP, EXTRA_COVERED, HERE)   # the held-out file is a source, read beside the sources
apply_expansion(TOPICS, EXPANSION)
OUT_OF_SCOPE_BANK = EXPANSION["oos_bank"]

CASE = {
 "case_id": "toxic-shock-tampon-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (as of v0.24)",
   "authoring_requirements": (
     "case-authoring-requirements.md (v0.24). Drafted on 6 October 2026 against the v0.21 "
     "text and brought to the v0.24 rules on 7 October 2026 after the audit."),
   "action_catalog": "action-catalog.json (0.3-draft, 305 entries)",
   "diagnosis_catalog": "diagnosis-catalog.json (499 entries)",
   "design_guide": "EMSim case design guide (Claude Doc, 5 October 2026)",
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Six clinical phases, the ceiling in section 3.3, and one terminal. They are the natural "
     "history (compensated, transient response to fluid, hypotensive) crossed with what the "
     "learner has done about it (a vasopressor with the source in, the source out) plus one "
     "deterioration for a learner who does neither."),
   "no_halted_phase": (
     "Nothing in this case is tagged harmful and there is no halted phase and no arrest. "
     "Every wrong turn is recoverable. That follows the design guide ('failure is safe, "
     "visible and owned') and AFRVR's v0.20 precedent."),
   "the_intended_path_goes_through_hypotension": (
     "On the directing physician's decision the learner is expected to see the fluid "
     "response fade and then start norepinephrine. The hypotensive phase is a waypoint, "
     "not a failure."),
   "antibiotics_move_nothing": (
     "No antibiotic changes a phase or a vital sign. That is deliberate: their benefit is "
     "not visible in an emergency department stay, and showing one would be false. They are "
     "scored and prompted, and the debrief says why the monitor did not move."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "neutral"],
   "note": "Harmful is not used. See phase_notes.no_halted_phase.",
 },
 "flag_namespace_note": (
   "Flags are permanent. fluids_given is set by any crystalloid bolus and fluids_30mlkg by "
   "the second one. pressor_running is set by norepinephrine, the three infusions it covers, "
   "and dopamine. No action clears it: the stop action is refused. source_removed is set only "
   "by removing the tampon. discharge_attempted is set by the hidden action the Handoff tab "
   "logs when discharge is chosen early. A maintenance infusion sets no flag."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "prompt_cap_recommendation": {
   "per_phase": 3,
   "rationale": (
     "Three. In the arrival phase a learner who does nothing hears the monitor at 20 "
     "seconds, the line at 45 and fluid at 60, and the fluid escalation at 170 is exempt "
     "from the cap. In the hypotensive phase the vasopressor prompt at 30 and the fluid "
     "prompt at 60 are the two the 240-second deterioration rests on, and with the line at "
     "45 they are the first three. In the supported phase the source prompt at 60 is the "
     "one the 270-second deterioration rests on and it is the earliest. In the default mode "
     "every one of those is multiplied by three and still lands before its exit: 180 of "
     "300, 90 and 180 of 240, 180 of 270. The vancomycin prompt at 110 is the fourth in the "
     "two shock phases on the do-nothing path and the cap silences it there."),
 },
 "prerequisite_semantics_note": (
   "Two case prerequisites: the pelvic examination before removing a vaginal foreign body, "
   "and a running vasopressor before one can be stopped. The catalog's vascular access and "
   "intubation prerequisites are kept."),
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
   "key_topics_note": (
     "Model judgment, unreviewed. Nine of forty-three: the topics whose answers change what "
     "the learner should do. Awaiting a physician's signature."),
 },
 "handoff": HANDOFF,
 "debrief_configuration": DEBRIEF,
}

# ------------------------------------------------------------------ binding map
COVERAGE = {
 "normal_saline_1l_bolus": {
   "also_covers_group": "crystalloid_bolus",
   "note": ("The case makes a claim about volume and not about an agent, so the tag, the "
            "flags and the note cover all four crystalloid boluses."),
 },
 "norepinephrine_drip": {
   "also_covers": ["epinephrine_drip", "vasopressin_drip", "phenylephrine_drip"],
   "note": ("Any of these infusions is a running vasopressor for the purpose this case "
            "scores. The note says norepinephrine is first. Dopamine is its own action "
            "because it is discouraged."),
 },
 "stop_norepinephrine": {
   "also_covers": ["stop_epinephrine", "stop_vasopressin", "stop_phenylephrine",
                   "stop_dopamine"],
   "note": ("v0.24 audit. The stop entry of every infusion that sets pressor_running. One "
            "case action refuses all five, so no stop button is an unscored way round the "
            "lesson (authoring 3.4)."),
 },
 "normal_saline_infusion": {
   "also_covers": ["lactated_ringer_s_infusion"],
   "note": ("v0.24 audit. A maintenance infusion of either crystalloid is the same act "
            "here: not a bolus, no flag, no credit. D5 NS bolus and D5 1/2 NS infusion are "
            "left unbound and are an open question for the physician."),
 },
 "ceftriaxone": {
   "also_covers": ["cefepime", "piperacillin_tazobactam", "meropenem", "cefotaxime"],
   "note": ("Broad beta-lactam cover while the source is unknown. Accepted without penalty "
            "on the directing physician's decision, and not a substitute for vancomycin. "
            "Cefotaxime added on 7 October 2026 after the audit, as in MGCA."),
 },
 "metoprolol_bolus": {
   "also_covers": ["esmolol_drip", "labetalol_bolus", "labetalol_drip", "propranolol_bolus",
                   "diltiazem_bolus", "digoxin_bolus", "amiodarone_bolus_infusion"],
   "note": ("Every route to slowing a compensatory tachycardia carries the same tag, effect "
            "and note, so none is an unscored way round the lesson. Digoxin and amiodarone "
            "added on 7 October 2026 after the audit, under the directing physician's "
            "decision that rate control is discouraged. Adenosine is left unbound and is an "
            "open question for the physician."),
 },
 "furosemide_40_mg_iv": {
   "also_covers_group": "loop_diuretic",
   "note": ("v0.24 audit. Bound through the catalog's loop diuretic group, so the tag "
            "follows the group as the catalog grows (authoring 3.4)."),
 },
}

# Case actions that are not catalog entries and are not buttons. Each needs a row with a
# placement on the handoff tab or the build does not create it (authoring 6.9 and 8.2).
HIDDEN_ROWS = {
 "attempt_discharge": {
   "note": ("Not a catalog action and not a button. Logged by the Handoff tab when "
            "discharge is chosen in the two early phases (handoff."
            "disposition_intercepts). Hidden from every tab and from search."),
   "unmatched_narration": "I'll get her up and dressed."},
 "sedation_after_tube": {
   "note": ("Not a catalog action and not a button. Nothing presses it. A sedative or "
            "analgesic bolus given with the tube in credits it through also_satisfies, and "
            "the post-intubation sedation follow-up is discharged by it (authoring 8.2). "
            "Hidden from every tab and from search."),
   "unmatched_narration": "Sedation is running."},
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
    if cid in HIDDEN_ROWS:
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": HIDDEN_ROWS[cid]["note"],
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": HIDDEN_ROWS[cid]["unmatched_narration"]})
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
    cpath = os.path.join(PACK, "TSS-case.json")
    bpath = os.path.join(PACK, "TSS-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    tpath = os.path.join(PACK, "TSS-matcher-tune-questions.json")
    with open(tpath, "w") as f:
        json.dump(tune_file("TSS", EXPANSION), f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(report(EXPANSION, verbose=False))
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
