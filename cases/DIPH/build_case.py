#!/usr/bin/env python3
"""Assemble DIPH-case.json and DIPH-binding-map.json from the parts in this folder.

    python3 cases/DIPH/build_case.py cases/DIPH

Same arrangement as cases/AFRVR. Nothing here is derived from anything: every clinical
fact in case_1 through case_5 is either Dr Medwid's source document or model output
awaiting her signature, and the split is recorded in DIPH-SEED.md and in PROVENANCE.
The script exists so that changing a deadline or a debrief note is a one-line edit in
readable Python rather than a search through indented JSON.

An edit made directly to DIPH-case.json is lost by the next run of this script.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from case_1_shell import META, PATIENT, PHASES
from case_2_actions import ACTIONS, FOLLOW_UPS
from case_3_content import EXAM, GENERAL_STATUS, LABS, IMAGING, CONSULTANTS
from case_4_interview import TOPICS, GLOBAL_RULES, OUT_OF_SCOPE, AUTHORING_NOTES, KEY_TOPICS
try:
    from case_4_interview import OUT_OF_SCOPE_BANK
except ImportError:          # before the expansion script has run
    OUT_OF_SCOPE_BANK = []
from case_5_handoff import HANDOFF, DEBRIEF, PROVENANCE

PACK = sys.argv[1] if len(sys.argv) > 1 else HERE

CASE = {
 "case_id": "diphenhydramine-overdose-qrs-01",
 "schema_version": "0.3",
 "authored_against": {
   "system_design": "system-design-v2.md (v0.9)",
   "authoring_requirements": "case-authoring-requirements.md (v0.9)",
   "action_catalog": "action-catalog.json (0.2-draft, plus physostigmine added for this case)",
   "diagnosis_catalog": "diagnosis-catalog.json",
   "conformance_note": (
     "Five-tier tags as ordered rule lists, structured result payloads with author-set abnormal "
     "flags, the closed set of fourteen exam manoeuvres with the catalog routing map, the "
     "two-sentence arrival handover, time-guarded phase transitions including one terminal one "
     "with an explicit opt-in, vital effects rebased so that no phase double-counts a gain an "
     "action supplies, flags granted on the Nth administration, the seven-score summary with "
     "key_topics and key_exams, and an ordered handoff diagnosis list."),
 },
 "provenance": PROVENANCE,
 "catalog_change_requests": PROVENANCE["catalog_change_requests"],
 "metadata": META,
 "patient": PATIENT,
 "phase_notes": {
   "count_justification": (
     "Six clinical phases, which is the ceiling in section 3.3, and three terminals. The six are "
     "the author's timed scenario crossed with the two axes the case turns on: whether the "
     "seizure has been treated and whether the sodium-channel blockade has been treated. "
     "Arrival, seizing, post-ictal, the wide-complex branch for a blockade nobody treated, and "
     "the two resolution phases.\n\n"
     "There is deliberately no intubated phase, which every other pack has. Two reasons. The six "
     "slots are spent on the axes above. And an intubated phase would sit at alertness 3 and end "
     "the interview, which would be wrong here: the historian is the patient's mother and she is "
     "not the one who has been intubated. Intubation instead sets a flag, moves the saturation "
     "through a vital effect, and changes the airway and general-status content."),
   "the_seizure": (
     "The one transition in this case with no guard. The author writes that a seizure occurs as "
     "part of the natural process regardless of how well the examinee is doing, so it is "
     "authored as a scheduled natural history at her own four minutes. Section 5.1 requires an "
     "unguarded_rationale for exactly this construct, and hers is quoted in it.\n\n"
     "It is unguarded and, since 5 September 2026, not unavoidable. The rule listed above it "
     "moves a patient who has received sodium bicarbonate out of the arrival phase after ten "
     "seconds, so a resident who treats the conduction before about 230 seconds never reaches "
     "the seizure rule. Nothing about the seizure rule changed; it was given an escape, on "
     "instruction, and the rationale on the escape sets out why the pharmacology behind it is "
     "weak and what deleting it would restore."),
   "three_ways_into_the_narrowing_phase": (
     "The stabilising phase is reached from the arrival phase, from the post-ictal phase and "
     "from the wide-complex rhythm, on the same guard and the same ten seconds each time. Its "
     "authored vitals therefore have to be true of a patient who never convulsed and of one "
     "who came within two minutes of arresting, which is why the temperature sits at 39.6 "
     "rather than at a number that assumes a particular history: nothing in this case cools "
     "her except active cooling, which is a vital effect applied on top of this baseline."),
   "the_deterioration_path": (
     "Three guarded deteriorations, all negative guards measured from phase entry: an untreated "
     "seizure at 120 seconds, untreated sodium-channel blockade from the post-ictal phase at 180 "
     "seconds, and untreated stable ventricular tachycardia at 120 seconds. The last one is "
     "terminal and carries allow_time_to_terminal. A resident who does nothing at all in this "
     "case reaches cardiac arrest, and that is a decision the seed records rather than an "
     "oversight. Sodium bicarbonate is prompted for in every phase on that path."),
   "the_two_delayed_consequences": (
     "Bicarbonate narrows the QRS ten seconds after it is given rather than on the click, and "
     "physostigmine produces its seizure ten seconds after it is given. Both are delayed "
     "consequences of the resident's own action in the sense of section 5.1, so the five-second "
     "floor applies rather than the thirty-second one. The bicarbonate delay is paired with a "
     "nurse_alert said the instant the drug goes in, because a delay with no explanation reads "
     "as a drug that has failed."),
 },
 "phases": PHASES,
 "tag_vocabulary": {
   "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "values_used_by_this_case": ["critical", "recommended", "discouraged", "harmful", "neutral"],
   "note": (
     "All five. Harmful is used four times, which is more than any other pack, and each is a "
     "drug: physostigmine given before the ECG, flumazenil, a further dose of diphenhydramine, "
     "and procainamide in an established wide-complex rhythm. Discouraged carries the rest of "
     "the weight and there are sixteen traps, because in a toxicology case most of the wrong "
     "answers are things you give rather than things you omit."),
 },
 "flag_namespace_note": (
   "Flags are case-scoped and permanent, with two exceptions that are not expiring flags but "
   "repeat grants. benzo_given is set by lorazepam and by the midazolam entry it covers. "
   "bicarb_given is set by the bolus and by the infusion, so a resident who reaches only for the "
   "drip is not treated as having withheld bicarbonate. bicarb_titrated is granted on the second "
   "bolus and ecg_repeated on the second tracing, and both exist to drive follow-up obligations "
   "the case cannot express as set membership. No flag in this case expires."),
 "case_actions": ACTIONS,
 "follow_ups": FOLLOW_UPS,
 "follow_up_condition_note": (
   "Three. Post-intubation sedation applies only if she has been intubated. The two bicarbonate "
   "obligations apply only once bicarbonate has been given, and both use satisfied_when rather "
   "than satisfied_by, because each is an obligation to do something again and a repeat of the "
   "triggering action cannot be expressed as set membership (authoring 8.2). They are discharged "
   "by the flags that the second administration grants."),
 "prompt_cap_recommendation": {
   "per_phase": 4,
   "rationale": (
     "Four slots, and the ordering matters more than the number. In the arrival phase the nurse "
     "can say four new things before the seizure at 240 seconds: the monitor at 20, the glucose "
     "at 55, the tracing at 75 and cooling at 140. The ECG escalation at 150 is exempt from the "
     "cap since v0.9, which matters because the ECG is the action this whole case is about.\n\n"
     "In the seizing phase, which ends at 120 seconds if nothing is given, the prompts are the "
     "benzodiazepine at 15, bicarbonate at 25 and the tube at 70. The benzodiazepine prompt is "
     "the one the 120-second deterioration's fairness guarantee rests on and it is the earliest, "
     "so the cap cannot suppress it.\n\n"
     "Every prompt in this case is guarded to the phases it makes sense in, because an action "
     "carries one deadline and it applies in every phase the guard admits."),
 },
 "prerequisite_semantics_note": (
   "A prerequisite is a requirement that must already hold, not a condition that blocks. This "
   "case authors none of its own and waives none of the catalog's. That is deliberate and it is "
   "about one action: physostigmine must be reachable. Gating it behind the ECG as a "
   "prerequisite would block the attempt and teach the lesson by refusing it, which teaches "
   "nothing about why. The case lets the resident give it and then shows them what it does."),
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
   "out_of_scope_bank": OUT_OF_SCOPE_BANK,
   "out_of_scope_bank_note": (
     "Questions this case has no authored answer to, generated into case_4_interview.py by "
     "catalog/expand_interview_variants.py from catalog/interview_out_of_scope.py, filtered to "
     "the concepts this case does not cover. The matcher embeds them beside the topic bank."),
   "topics": TOPICS,
   "key_topics": KEY_TOPICS,
   "key_topics_note": (
     "Author judgement, unreviewed. Read by the summary's History score, asked over listed. "
     "Twelve of forty-one, and they are the ones whose answers change what happens: what was "
     "found by the bed, what she took, what else is in the house, when she was last well, the "
     "absence of any medical history or medication that could explain this, the mental health "
     "history that makes a deliberate ingestion likely, the absence of any prior seizure, and "
     "the pregnancy question. Every other topic is answerable and charted and does not count."),
 },
 "handoff": HANDOFF,
 "debrief_configuration": DEBRIEF,
 "result_payload_contract": {
   "shape": "kind is panel, value or report; components carry label, value, unit, reference_range and abnormal",
   "abnormal": (
     "Set by the author of the case file, never computed by the renderer. The validator "
     "cross-checks every parseable interval against its flag and reports disagreements."),
   "resolution_order": ["case content", "catalog default", "error"],
   "prose_field": "Not used. Every authored result is a structured payload.",
   "unverified": (
     "Every laboratory value in this case is Dr Medwid's. Not one reference interval is: the "
     "source document contains no intervals at all, so every one is model output, and the "
     "abnormal flags follow from intervals nobody has signed. Three panels carry a verify note "
     "naming a specific problem: the corrected bicarbonate, the female haemoglobin and "
     "haematocrit, and the invented magnesium."),
 },
 "phases_note": (
   "Read the transition lists in order, because first match wins. The handoff rule is first in "
   "every list so that submitting a handover is never overtaken by a clinical rule in the same "
   "step. In the arrival phase the physostigmine rule is checked before the unguarded seizure "
   "rule, which matters only for a resident who gives physostigmine at around the four-minute "
   "mark; both land in the same phase either way.\n\n"
   "A harmful action bypasses every rule here and goes straight to the halted phase, so the "
   "physostigmine transition in the arrival phase is reachable only when the tag has evaluated "
   "to discouraged, which means the ECG had already resulted.\n\n"
   "The seizing phase is reachable from arrival by two routes and from nowhere else. The "
   "wide-complex phase is reachable from the seizing phase and from the post-ictal phase, both "
   "on the clock. Every one of those has an exit that an action can take, except the arrest, "
   "which is terminal by design."),
}

# ------------------------------------------------------------------ binding map
COVERAGE = {
 "lorazepam_bolus": {
   "also_covers": ["midazolam_bolus"],
   "note": (
     "Lorazepam and midazolam are one decision for the purpose this case scores, which is "
     "whether the seizure and the agitation were treated with a benzodiazepine. Coverage gives "
     "both the same tag, the same flag and the same note, so neither is an unscored route around "
     "the critical action.\n\n"
     "The cost is real and is recorded here rather than hidden. The catalog places midazolam "
     "under the intubation drugs, where it is an induction agent, so a resident who induces with "
     "midazolam sets the benzodiazepine flag and terminates the seizure without having chosen an "
     "anticonvulsant. That is clinically true, and it means this case cannot distinguish a "
     "deliberate anticonvulsant from an induction agent that happened to be one. Diazepam is not "
     "in the catalog."),
 },
 "normal_saline_1l_bolus": {
   "also_covers_group": "crystalloid_bolus",
   "note": (
     "The case is making a claim about volume rather than about an agent, so the recommended tag "
     "and the note cover all four crystalloid boluses. Nothing here is harmful, so the group is "
     "being used to stop the credit being agent-specific rather than to close an escape hatch."),
 },
 "ceftriaxone": {
   "also_covers": ["vancomycin", "cefepime"],
   "note": (
     "This case scores the act of starting empirical antimicrobial cover for a febrile confused "
     "adolescent, not a regimen, and it makes no claim about which regimen is right for "
     "suspected bacterial meningitis in this age group. Coverage means a resident who reaches "
     "for vancomycin and cefepime gets the same recommended tag on arrival and the same "
     "discouraged tag once the toxicology screen has resulted. Acyclovir is deliberately NOT in "
     "this group: it is a different question and is authored as its own action."),
 },
 "magnesium_sulfate": {
   "also_covers": ["magnesium_sulfate_bolus"],
   "note": (
     "The catalog carries magnesium twice, as a plain entry placed under four groups and as a "
     "bolus. Repleting through either is the same act here, so the tag, the flag and the note "
     "cover both."),
 },
}

BINDING_ROWS = []
for a in ACTIONS:
    cid = a["catalog_id"]
    if cid == "handoff_submit":
        BINDING_ROWS.append({
          "case_id": cid, "catalog_id": None,
          "note": ("The catalog has no handoff tab and no handoff action; it is listed in the "
                   "catalog's own known_gaps. Rendered anyway so the case is playable."),
          "unmatched_placement": {"tab": "handoff", "group": "Not in the catalog"},
          "unmatched_narration": "I'll get the notes together for the unit."})
        continue
    row = {"case_id": cid, "catalog_id": cid}
    row.update(COVERAGE.get(cid, {}))
    BINDING_ROWS.append(row)

BINDING = {
 "map_version": "0.1",
 "case_id": CASE["case_id"],
 "status": ("DRAFT. Every also_covers row is an author judgement about two catalog entries being "
            "the same act for this case's purposes, and needs review. Every other row binds a "
            "case id to the identical catalog id."),
 "how_to_read": {
   "catalog_id equals case_id": "exact; nothing to review",
   "catalog_id null": "unmatched; a catalog change request",
   "also_covers / also_covers_group": (
     "this case action claims several catalog entries, so its tag, flags, halt reason and "
     "debrief note apply to every route to the same act. Every one of these is a clinical claim "
     "that the entries are the same act for this case's purposes."),
 },
 "rows": BINDING_ROWS,
}

if __name__ == "__main__":
    cpath = os.path.join(PACK, "DIPH-case.json")
    bpath = os.path.join(PACK, "DIPH-binding-map.json")
    with open(cpath, "w") as f:
        json.dump(CASE, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(bpath, "w") as f:
        json.dump(BINDING, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", cpath, os.path.getsize(cpath), "bytes")
    print("wrote", bpath, len(BINDING_ROWS), "rows")
