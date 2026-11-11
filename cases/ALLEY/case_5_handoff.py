"""ALLEY part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "icu",
   "label": "Intensive care unit",
   "level_of_care": "critical_care",
   "explanation": (
     "He goes to intensive care for emergent hemodialysis, a bicarbonate infusion, a gas "
     "every few hours and fomepizole every four hours while he is on dialysis.\n\n"
     "What the receiving team needs to hear: what he drank and that the level is a send-out, "
     "the anion gap and the osmolar gap with the ethanol, his vision, when fomepizole and "
     "bicarbonate went in, that nephrology has accepted him, and that the poison center is "
     "involved.")},

 # Owner, 11 November 2026. Observation before the antidote is the hallway: one tier of
 # untreated time, then the case continues. Discharge from any phase ends the run in the
 # authored terminal phase 'discharged'.
 "disposition_intercepts": [
   {"disposition": "observation_unit",
    "when": "(phase is presentation OR phase is drifting OR phase is untreated_floor) AND NOT flag observation_attempted set",
    "action": "attempt_observation",
    "author_note": "Owner's structure I12, 11 November 2026: the hallway costs time and the case continues."},
   {"disposition": "discharge_home",
    "when": "NOT flag discharge_attempted set",
    "action": "attempt_discharge",
    "author_note": "Owner, 11 November 2026: discharge is a case failure, ending on 'He was brought back four hours later, unresponsive.'"},
 ],

 "alternative_dispositions": [
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care with telemetry",
    "verdict": "incorrect",
    "explanation": (
      "He needs emergent dialysis, frequent gases and a bicarbonate infusion in a man whose "
      "pH is under 7.2. That is intensive care.")},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "incorrect",
    "explanation": "A ward cannot dialyze him tonight or run the gases this needs."},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": (
      "Observation to sleep it off is the plan the triage note offered. His respiratory rate "
      "and his ethanol level never supported it.")},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": "He has a severe metabolic acidosis and is losing his sight. He came back unresponsive."},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": (
      "This hospital has dialysis and intensive care. Without them, transfer after "
      "fomepizole and bicarbonate would be right.")}],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_methanol_toxicity",
   "label": "Methanol toxicity",
   "explanation": (
     "Washer fluid after the vodka ran out, an anion gap of 30 that lactate and ketones do not "
     "explain, an osmolar gap of 38 that his ethanol of 28 does not explain, and snowstorm "
     "vision. The send-out methanol level, back the next day, was 96 mg/dL. None of that "
     "level was needed to make the diagnosis or start treatment.")},

 "additional_diagnoses": [
   {"catalog_id": "dx_anion_gap_metabolic_acidosis", "label": "Anion gap metabolic acidosis",
    "explanation": (
      "The mechanism, and the number that makes him a dialysis patient: an anion gap above "
      "24, a pH at or under 7.15 as he drifted, with the breathing doing all it can.")}],

 "minor_diagnoses": [
   {"catalog_id": "dx_acute_alcohol_intoxication", "label": "Acute alcohol intoxication",
    "explanation": "True, and the label that hid everything else. Ethanol 28 mg/dL."},
   {"catalog_id": "dx_lactic_acidosis", "label": "Lactic acidosis",
    "explanation": "A lactate of 3.6 to 4.6, a small part of a gap of 30."}],

 "alternative_diagnoses": [
   {"catalog_id": "dx_ethylene_glycol_toxicity", "label": "Ethylene glycol toxicity",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "The other toxic alcohol with both gaps, and treated the same way at first: "
      "fomepizole, bicarbonate, dialysis. His vision points to methanol and his kidneys are "
      "normal. Send both levels.")},
   {"catalog_id": "dx_acute_alcohol_intoxication", "label": "Acute alcohol intoxication",
    "verdict": "incorrect",
    "explanation": (
      "He is intoxicated, and an ethanol of 28 does not explain how he looks, his breathing, "
      "his gap or his eyes. This is the diagnosis that sends him to the hallway.")},
   {"catalog_id": "dx_alcoholic_ketoacidosis", "label": "Alcoholic ketoacidosis",
    "verdict": "incorrect",
    "explanation": (
      "The classic trap: a drinker who has not eaten for days with an anion gap. His "
      "beta-hydroxybutyrate is 0.5, so ketones cannot explain a gap of 30, and ketoacidosis "
      "does not explain an osmolar gap or his vision.")},
   {"catalog_id": "dx_lactic_acidosis", "label": "Lactic acidosis",
    "verdict": "incorrect",
    "explanation": "His lactate is 3.6. It explains a few points of a gap of 30."},
   {"catalog_id": "dx_alcohol_withdrawal", "label": "Alcohol withdrawal",
    "verdict": "incorrect",
    "explanation": (
      "His tachycardia invites it. He has no tremor, no sweating and no hallucinations, and "
      "withdrawal does not cause a gap of 30.")},
   {"catalog_id": "dx_diabetic_ketoacidosis", "label": "Diabetic ketoacidosis",
    "verdict": "incorrect",
    "explanation": "His glucose is 90 and his ketones are low."},
   {"catalog_id": "dx_optic_neuritis", "label": "Optic neuritis",
    "verdict": "incorrect",
    "explanation": (
      "His optic nerves are injured, by formate, not by inflammation. Name the poisoning that "
      "is doing it.")}],

 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "recognition", "label": "Not just drunk",
    "actions": ["attach_monitor", "venous_blood_gas", "arterial_blood_gas", "basic_chemistry_chem_7",
                "ethanol_level_etoh", "lactate", "beta_hydroxybutyrate", "salicylate_aspirin_level",
                "acetaminophen_level", "fingerstick_blood_sugar"]},
   {"id": "two_gaps", "label": "Both gaps",
    "actions": ["osmolality", "urinalysis"]},
   {"id": "history", "label": "What he drank, his eyes, his intent",
    "actions": ["interview_topic_alcohol", "interview_topic_vision", "interview_topic_intent", "exam_heent"]},
   {"id": "trauma", "label": "Looking for injury",
    "actions": ["exam_neuro", "exam_abd"]},
   {"id": "treatment", "label": "Stop it, buffer it, remove it",
    "actions": ["insert_iv", "fomepizole", "na_bicarbonate_bolus", "na_bicarbonate_infusion",
                "folinic_acid", "thiamine", "normal_saline_1l_bolus", "activated_charcoal"]},
   {"id": "harm", "label": "What made it worse",
    "actions": ["lorazepam_bolus", "morphine_bolus", "diphenhydramine", "midazolam_bolus",
                "haloperidol", "ct_head", "attempt_observation", "intubate_rapid_sequence"]},
   {"id": "people", "label": "Calling for help and disposition",
    "actions": ["consult_toxicology", "consult_renal", "consult_critical_care", "attempt_discharge",
                "handoff_submit"]},
 ],
 "key_exams": ["exam_breath", "exam_pulm", "exam_heent", "exam_neuro", "exam_abd"],
 "key_exams_note": (
   "The Physical score reads the tagged exams: the trauma survey (head, neurological, "
   "abdominal) is critical (owner, 11 November 2026), and the breathing and lung exams are "
   "recommended. This list matches them. Model judgment beyond the owner's decision."),
 "intended_path": ["presentation", "held_early", "improving", "case_complete"],
 "intended_path_note": (
   "Gas, chemistry, ethanol and osmolality, the drink and the eyes asked about, fomepizole, "
   "bicarbonate, the poison center and nephrology, ICU. Bicarbonate before fomepizole reaches "
   "improving directly if fomepizole follows while it is still acting."),
 "trap_actions": ["attempt_observation", "lorazepam_bolus", "activated_charcoal", "haloperidol"],
 "cross_cutting_teaching_points": [
   ("A diagnosis has to explain the numbers. 'Just drunk' did not explain a respiratory rate "
    "of 27 with clear lungs, or an ethanol of 28 in a man who looked this drunk. When the "
    "obvious label leaves a number unexplained, chase the number."),
   ("Work both gaps. When lactate and ketones do not explain an anion gap, order a measured "
    "osmolality and subtract the calculated one with the ethanol in it. The osmolar gap is "
    "highest early and falls as the anion gap rises, so a normal one late does not exclude a "
    "toxic alcohol. [UNVERIFIED: Kraut and Mullins, N Engl J Med 2018, not opened]"),
   ("Ask an intoxicated patient about his eyes. He will not volunteer that everything looks "
    "like a snowstorm, and a new vision deficit is both a clue and a dialysis indication. "
    "[UNVERIFIED: Roberts et al. 2015 (EXTRIP), read through an abstract page and a summary]"),
   ("Stop it, buffer it, remove it. Fomepizole stops formate being made and changes nothing "
    "you can see. Bicarbonate buffers the acid and wears off if production continues. "
    "Dialysis removes it. None of the three waits for a methanol level. [UNVERIFIED: "
    "fomepizole prescribing information, read through search]"),
   ("His breathing was the only thing defending his pH. A sedative, or a ventilator on "
    "ordinary settings, takes that defense away."),
   ("He never crashed in this case. That was a design choice. Untreated methanol poisoning "
    "progresses to coma, seizures and death, and the simulator compresses hours into minutes."),
 ],
 "attempt_history_note": "Blocked attempts (intubation, an early call to nephrology) are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 11 November 2026, from his "
            "case structure and his answers to two rounds of questions the same day. "
            "Authoring requirements section 1 applies."),
 "warning": (
   "A physician decided the things listed in ALLEY-SEED.md section 0. Everything else is "
   "model output and awaits sign-off: every vital sign, finding, laboratory value, delay, "
   "tag, debrief note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase, the heart rates moved to 112, 114, 116 and 96 to fit the borrowed tracings, and the tier clock (360 seconds to the second tier, 180 more to the worst).",
   "Every laboratory value: the five gas states and their sedated variants, the chemistry with the sodium rise after bicarbonate, the osmolality ladder (328, 327, 326, and 332 to 334 after bicarbonate), lactate 3.6 to 4.6.",
   "Every abnormal flag on every result, finding and status line.",
   "The vital effects of bicarbonate, fluid and sedation. Teaching choices, not measurements.",
   "The halt reason on lorazepam, morphine and diphenhydramine in the untreated and held phases.",
   "That fomepizole freezes the patient with no improvement inside the case.",
   "That bicarbonate alone lasts 180 seconds and that an infusion lasts the case.",
   "That a CT or the hallway before fomepizole costs one tier, once.",
   "Every clinical tag, every prompt deadline (40, 60, 70, 120, 150 and the escalation at 150 in the worst tier) and their texts.",
   "Nephrology's two prerequisites and every consultant line.",
   "The ECG tracings borrowed from TSS and SCOOT, and the chest film.",
   "The interview in full, including every model-added fact and denial (ALLEY-SEED.md 3.7).",
   "interview.key_topics, interview.must_ask and debrief_configuration.key_exams.",
   "Both diagnosis lists and every disposition explanation.",
   "Every debrief note.",
 ],
 "reference_status": [
   {"reference": ("Roberts DM, et al. Recommendations for the role of extracorporeal treatments in the "
                  "management of acute methanol poisoning: a systematic review and consensus statement "
                  "(EXTRIP). Crit Care Med 2015;43(2):461-472"),
    "how_read": "Abstract page (Mount Sinai scholars) and a UMEM summary, read by a model through search on 11 November 2026",
    "status": "Supplies the dialysis indications. Full text not opened. Not checked by a physician"},
   {"reference": "Kraut JA, Mullins ME. Toxic alcohols. N Engl J Med 2018;378(3):270-280",
    "how_read": "Citation confirmed through the Washington University repository. Not opened",
    "status": "The 100 mg/dL ethanol figure, the bicarbonate threshold and the osmolar gap teaching attributed to it are from the owner's structure and a model's memory. Unverified"},
   {"reference": "Cranmer et al., N Engl J Med 2026 (cited in the owner's structure)",
    "how_read": "Could not be found. The NEJM page for Kraut and Mullins lists Cranmer, Erickson and Beach as a citing article",
    "status": "Not used in the case. Unverified"},
   {"reference": ("Barceloux DG, et al. American Academy of Clinical Toxicology practice guidelines on the "
                  "treatment of methanol poisoning. J Toxicol Clin Toxicol 2002;40(4):415-446"),
    "how_read": "Not opened. Criteria read through AMBOSS, the Austin Health guideline and a SESLHD guideline via search",
    "status": "Fomepizole criteria as reported secondhand. Unverified"},
   {"reference": "Fomepizole injection prescribing information",
    "how_read": "Label text via ndclist and Prescriberpoint, read through search",
    "status": "Begin on suspicion. Dosing every four hours during dialysis. Not checked by a physician"},
   {"reference": "Utah Poison Control Center, fomepizole antidote page, 2023",
    "how_read": "Read through search",
    "status": "Methanol half-life up to 71 hours under fomepizole. Not checked by a physician"},
   {"reference": "Emergency Care BC methanol ingestion summary, and Austin Health methanol guideline 2023",
    "how_read": "Read through search",
    "status": "Bicarbonate below pH 7.25 to 7.3, reduced tissue penetration of formate. Not checked by a physician"},
   {"reference": "Wittler M, O'Brien MC, Masneri DA. Toxic alcohol ingestion/methanol ingestion. MedEdPORTAL 2018;14:10740",
    "how_read": "Abstract read through search. Case materials not opened",
    "status": "Used as a published simulation source for goal 1. Not checked by a physician"},
   {"reference": "Winter's formula, venous-arterial gas differences, ethanol contribution to the osmolar gap, and the withdrawal and sedation teaching",
    "how_read": "From memory. No source opened",
    "status": "Written by a model. Unverified. Marked where the field allows"},
 ],
 "reference_status_note": (
   "Markers sit only where the interface strips them: action debrief notes, timed "
   "transition notes and the cross-cutting teaching points."),
 "catalog_change_requests": [
   "Methanol and ethylene glycol levels as send-out studies, so the learner can send them and see 'pending at the reference lab'. Not added: a case-only button would point at the answer.",
   "A 'search belongings' action for toxicology cases. Until then the empty jug reaches the learner through the drink history and the nurse's escalation in the worst tier.",
   "An ophthalmology consult.",
   "Folinic acid is a case-only button in this pack (owner, 11 November 2026). A catalog entry would stop it pointing at the answer.",
   "The ungraded intubation-care list makes midazolam, propofol and fentanyl unscorable when given as sedatives with no tube to follow. Lorazepam halts here and midazolam does not.",
   "A conditional outcome line on case_complete, to show the owner's epilogues and vision outcomes at the end of the run.",
   "A way to block a catalog action in one case with a message. This pack blocks intubation with a prerequisite on a flag only a hidden, buttonless action sets.",
 ],
}
