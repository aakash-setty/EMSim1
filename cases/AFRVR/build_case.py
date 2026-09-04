#!/usr/bin/env python3
"""Assemble AFRVR-case.json and AFRVR-binding-map.json from the parts in this folder.

    python3 cases/AFRVR/build_case.py cases/AFRVR

The case file is 190 KB of JSON and was written through this script rather than by hand,
so it lives in the pack the way CHFE's migration scripts do. It is not a generator in the
sense that the catalog builders are: nothing here is derived from anything, and every
clinical fact in case_1 through case_5 is either the author's seed or model output
awaiting the author's signature. It is here so that a change to a debrief note or a
deadline is a one-line edit in readable Python rather than a search through indented JSON,
and so that the whole file can be regenerated after such an edit.

Two edits made directly to the JSON after the last run of this script would be lost by the
next one, so if you edit AFRVR-case.json by hand, mirror the change here.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from case_1_shell import META, PATIENT, PHASES
from case_2_actions import ACTIONS, FOLLOW_UPS
from case_3_content import EXAM, GENERAL_STATUS, LABS, IMAGING, CONSULTANTS
from case_4_interview import TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

# The saline bolus keeps the catalog's own button name; only the tag is shared.
for a in ACTIONS:
    if a["catalog_id"] == "normal_saline_1l_bolus":
        a.pop("display_name", None)

CASE = {
 "case_id": "afib-rvr-hfref-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (v0.8)",
   "authoring_requirements": "case-authoring-requirements.md (v0.7)",
   "action_catalog": "action-catalog.json (0.2-draft)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "conformance_note": (
     "Written against v0.7 of the authoring requirements, so it uses the five-tier tag vocabulary "
     "including discouraged, structured result payloads with author-set abnormal flags, the closed "
     "set of fourteen exam manoeuvres with the catalog routing map, the two-sentence arrival "
     "handover with no background paragraph behind it, time-guarded phase transitions, and vital "
     "effects rebased so that no phase double-counts a gain an action supplies."),
 },
 "provenance": PROVENANCE,
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Six clinical phases, which is the ceiling in section 3.3, and each one is a state a learner "
     "can actually reach and a reviewer has to read. They are the two axes of this case crossed: "
     "whether the breathing is supported and whether the rate is controlled, giving arrival, "
     "breathing supported alone, rate controlled alone, and both; plus the deterioration branch "
     "for a patient whose breathing was never supported, and the ventilated phase."),
   "deterioration_path": (
     "Two time-guarded transitions, both at 240 seconds and both guarded on positive pressure not "
     "having been applied, one from arrival and one from the rate-controlled-but-congested phase. "
     "Both land in respiratory failure, which has exits and is not terminal. The clock cannot end "
     "this case: a learner who does nothing at all reaches respiratory failure and stays there. "
     "That was the author's explicit instruction and it is the reason no transition in this case "
     "carries allow_time_to_terminal."),
   "rate_control_delay": (
     "The two transitions that follow rate control carry a 30-second guard_true delay, so the "
     "ventricular rate falls about half a minute after the drug rather than on the click. Without "
     "it the case teaches that rate control is instantaneous. The delay is paired with a nurse "
     "line said the moment the drug goes in, because a delay on its own reads as the drug having "
     "failed and invites a second dose; the line is what carries the lesson and the delay is what "
     "stops the number being a button. Thirty seconds sits on the validator's hard floor, which is "
     "deliberate and is recorded in the transition rationale."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "note": (
     "All five tiers are used. Discouraged carries the weight in this case, because the central "
     "error, continuing a calcium channel blocker in a patient with reduced systolic function, is "
     "explicitly not to halt the case: the author's instruction was that a drug producing the "
     "effect you asked for while being the wrong drug is more instructive than a collapse."),
 },
 "flag_namespace_note": (
   "Flags are case-scoped and permanent. rate_control_given is set by any of the four "
   "rate-controlling routes this case authors, including the two it discourages, so the phase "
   "advances whether or not the choice was a good one. anticoagulated is set by any of the three "
   "anticoagulants. Nothing in this case uses an expiring flag."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "follow_up_condition_note": (
   "The post-intubation obligations apply only when the patient has been intubated, and the "
   "post-cardioversion anticoagulation obligation only when he has been cardioverted, so all three "
   "are guarded rather than unconditional. Every satisfier is listed: a covered sibling records "
   "the covering action as taken, so enoxaparin and a heparin infusion discharge the "
   "anticoagulation obligation as well as apixaban."),
 "prompt_cap_recommendation": {
   "per_phase": 4,
   "rationale": (
     "Four slots per phase, and the ordering matters more than the number. In the arrival phase "
     "the nurse can say four things before the 240-second deterioration: attach the monitor at 20 "
     "seconds, apply positive pressure at 40, escalate that at 100, and put the probe on the heart "
     "at 130. The escalation has to be inside the cap, because it is the warning the "
     "deterioration's fairness guarantee rests on, and a cap that suppresses a fairness guarantee "
     "is worse than no cap. The diuretic at 160, rate control at 190 and anticoagulation at 215 "
     "therefore do not fire on arrival and do fire in the later phases, where the earlier prompts "
     "have been satisfied and their guards suppress them without consuming a slot."),
 },
 "prerequisite_semantics_note": (
   "A prerequisite is a requirement that must already hold, not a condition that blocks. Two are "
   "authored here beyond the catalog defaults: positive pressure requires that the patient is not "
   "already intubated, and synchronised cardioversion requires that he has been given something "
   "for sedation, because he is awake and talking."),
 "content_keys": {
   "exam": EXAM,
   "general_status": GENERAL_STATUS,
   "labs": LABS,
   "imaging": IMAGING,
   "consultants": CONSULTANTS,
 },
 "interview": {
   "authoring_notes": AUTHORING_NOTES,
   "global_answer_rules": GLOBAL_RULES,
   "out_of_scope_fallback": OUT_OF_SCOPE,
   "topics": TOPICS,
 },
 "handoff": HANDOFF,
 "debrief_configuration": DEBRIEF,
 "result_payload_contract": {
   "shape": "kind is panel, value or report; components carry label, value, unit, reference_range and abnormal",
   "abnormal": ("Set by the author, never computed by the renderer, because reference intervals "
     "are assay-specific and interpretation is often not the number. The validator cross-checks "
     "every parseable interval against its flag and reports disagreements."),
   "resolution_order": ["case content", "catalog default", "error"],
   "prose_field": "Not used in this case. Every authored result is a structured payload.",
   "unverified": ("Reference intervals in this pack are model output. Where the catalog carries a "
     "default for the same analyte the case uses the catalog's interval so the two agree."),
 },
 "phases_note": (
   "Read the transition lists in order, because first match wins and two of the rules in the "
   "arrival phase are timed. Intubation is checked first everywhere, so a learner who intubates "
   "from any state reaches the ventilated phase rather than an improvement phase. Positive "
   "pressure is checked before rate control in the arrival phase, so a learner who gives both in "
   "one batch of orders moves to the breathing-supported phase immediately and then to stabilised "
   "thirty seconds later, rather than waiting thirty seconds for either.\n\n"
   "The respiratory failure phase deliberately has no rate-control exit. A learner who arrives "
   "there and responds by giving a rate-controlling drug has the flag recorded and the credit "
   "given and sees no improvement, because the problem in that phase is the lung. Applying "
   "positive pressure afterwards goes straight to the stabilised phase, since the rate control is "
   "already in and has had time to work."),
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    row = {"case_id": cid, "catalog_id": cid}
    if cid == "handoff_submit":
        row = {"case_id": cid, "catalog_id": None,
               "note": "The catalog has no handoff tab and no handoff action; it is listed in the "
                       "catalog's own known_gaps. Rendered anyway so the case is playable.",
               "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
               "unmatched_narration": "I'll put the notes together for the unit."}
    elif cid == "digoxin_bolus":
        row["also_covers"] = ["amiodarone_bolus_infusion", "metoprolol_bolus"]
        row["note"] = (
          "This case scores the act of rate control rather than one agent, because the author's "
          "brief accepts digoxin, amiodarone or an appropriately selected beta blocker and says "
          "the choice should follow the patient's physiology. Coverage gives all three the same "
          "tag, the same flag and the same teaching note, so any of them satisfies the critical "
          "action and none of them is an unscored route around it. The cost is that the three are "
          "not scored differently from each other, and the differences between them are real; "
          "they are carried in the shared debrief note instead, and the debrief names the act "
          "rather than the drug through expectation_label. Esmolol and propranolol are "
          "deliberately NOT in this group: each is authored as its own discouraged action with "
          "its own reasoning.")
    elif cid == "apixaban":
        row["also_covers"] = ["enoxaparin", "heparin_bolus_drip"]
        row["note"] = (
          "Same reasoning as the rate-control group. The author's brief prefers a direct oral "
          "anticoagulant and accepts enoxaparin or a heparin infusion, so all three satisfy the "
          "critical action and the shared note carries the choice between them. Apixaban and "
          "enoxaparin were added to the action catalog for this case on the author's instruction "
          "and are marked source=author-supplied there; before this case the catalog's only "
          "anticoagulant was heparin.")
    elif cid == "normal_saline_1l_bolus":
        row["also_covers_group"] = "crystalloid_bolus"
        row["note"] = (
          "Harmful here. The catalog offers four crystalloid boluses and every one of them reaches "
          "the same harm in a patient with an ejection fraction of 30 to 35 percent and a flooded "
          "lung, so the tag covers the whole equivalence group rather than one entry. A harmful "
          "tag on saline alone would leave Ringer's as an unguarded route to the same death.")
    elif cid == "furosemide_40_mg_iv":
        row["also_covers_group"] = "loop_diuretic"
        row["note"] = ("Bound to the group so that if the catalog ever gains a second loop "
                       "diuretic the critical action does not silently stop covering it. The group "
                       "currently holds only this entry.")
    elif cid == "non_invasive_positive_pressure_ventilation":
        row["note"] = ("Continuous and bilevel positive pressure are one catalog entry and one "
                       "decision. The display name is overridden because the catalog's name is too "
                       "long for a button and does not say CPAP or BiPAP, which is what a resident "
                       "is looking for.")
    BINDING_ROWS.append(row)

BINDING = {
 "map_version": "0.1",
 "case_id": CASE["case_id"],
 "status": "DRAFT. Every row whose catalog_id differs from case_id, and every also_covers row, is "
           "an author judgement and needs review.",
 "how_to_read": {
   "catalog_id equals case_id": "exact; nothing to review",
   "catalog_id null": "unmatched; a catalog change request",
   "also_covers / also_covers_group": "this case action claims several catalog entries, so its "
     "tag, flags, halt reason and debrief note apply to every route to the same act. Every one of "
     "these is a clinical claim that the entries are the same act for this case's purposes.",
 },
 "rows": BINDING_ROWS,
}

json.dump(CASE, open(os.path.join(PACK, "AFRVR-case.json"), "w"), indent=1, ensure_ascii=False)
json.dump(BINDING, open(os.path.join(PACK, "AFRVR-binding-map.json"), "w"), indent=1,
          ensure_ascii=False)
print("case actions:", len(ACTIONS), "| phases:", len(PHASES), "| topics:", len(TOPICS),
      "| variants:", sum(len(t["variants"]) for t in TOPICS))
