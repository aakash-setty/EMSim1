"""TAKO part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "cath_lab",
   "label": "Cardiac catheterization laboratory",
   "level_of_care": "critical_care",
   "explanation": (
     "She goes to the catheterization laboratory. She has ST elevation with chest pain, "
     "and nothing done in the emergency department can tell an occluded artery from "
     "takotsubo. The angiogram is both the treatment for one and the diagnosis of the "
     "other.\n\n"
     "What happened next: her coronary arteries had no obstruction, and the ventriculogram "
     "showed the apex ballooning with a vigorous base. That is takotsubo cardiomyopathy. "
     "She went to cardiac intensive care on a vasoconstrictor and her ventricle recovered "
     "over the following weeks, as it usually does. It is not a benign illness: rates of "
     "shock and death in hospital are similar to those of a heart attack.\n\n"
     "What the receiving team needs: the ECG, the murmur and the echo, what her pressure "
     "did, and which drugs helped and which made her worse.")},

 "alternative_dispositions": [
   {"id": "icu", "label": "Intensive care unit",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "She needs intensive care and she will get it, after the angiogram. Sending her "
      "there first leaves ST elevation with chest pain uninvestigated. Defensible only as "
      "the bed she goes to from the laboratory.")},
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care with telemetry",
    "verdict": "incorrect",
    "explanation": (
      "She is on a vasoconstrictor with ST elevation and an ejection fraction of 30 "
      "percent. She needs an angiogram and then intensive care.")},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "incorrect",
    "explanation": "Telemetry watches a rhythm. It does not open an artery or run a vasoactive infusion."},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": (
      "Observation with serial troponins is for chest pain with a normal ECG. Hers shows "
      "ST elevation.")},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": (
      "This is the outcome her daughter's explanation leads to. Grief does not cause ST "
      "elevation that can safely be sent home. Even when the cause turns out to be "
      "takotsubo, she has a failing ventricle and was in shock.")},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": "This hospital has a catheterization laboratory and cardiac intensive care."}],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu", "cath_lab", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_st_elevation_myocardial_infarction",
   "label": "ST-elevation myocardial infarction",
   "explanation": (
     "This is the right working diagnosis to hand over, and it is not what she had. Chest "
     "pain with anterior ST elevation is treated as an occluded coronary artery until an "
     "angiogram shows otherwise.\n\n"
     "Her angiogram showed no obstruction and an apex that ballooned in systole: takotsubo "
     "cardiomyopathy, brought on by the death of her husband. Nothing available to you "
     "could have told the two apart. The emotional trigger, the very "
     "high natriuretic peptide and wall motion that crossed arterial territories all "
     "point toward takotsubo, and none of them is reliable enough to keep a patient out of "
     "the laboratory.\n\n"
     "This case scores the working diagnosis you should have acted on. Naming takotsubo "
     "first is scored as defensible, because it turned out to be true and could only have "
     "been a guess. Decided by the directing physician.")},

 "additional_diagnoses": [
   {"catalog_id": "dx_cardiogenic_shock", "label": "Cardiogenic shock",
    "explanation": (
      "Her pressure fell with cold hands, a rising lactate and an ejection fraction of 30 "
      "percent. Saying so tells the laboratory to expect an unstable patient. Say with it "
      "that the shock was from outflow obstruction and got worse with inotropes, because "
      "that changes what they reach for.")},
   {"catalog_id": "dx_takotsubo_cardiomyopathy", "label": "Takotsubo cardiomyopathy",
    "explanation": (
      "Worth naming as a possibility beside the infarct. The trigger, the echo and the "
      "murmur all suggest it, and a team that has it in mind will do a ventriculogram and "
      "will not be surprised by clean arteries.")}],

 "alternative_diagnoses": [
   {"catalog_id": "dx_takotsubo_cardiomyopathy", "label": "Takotsubo cardiomyopathy",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "This is what she had. As the primary diagnosis at handover it is a guess that "
      "happened to be right. It cannot be made before angiography, and a doctor who "
      "commits to it early may hold aspirin or delay the laboratory for a patient who has "
      "an occluded artery. Hand over the infarct and name this beside it.")},
   {"catalog_id": "dx_cardiogenic_shock", "label": "Cardiogenic shock",
    "verdict": "acceptable_with_qualification",
    "explanation": "True, and it describes her circulation without saying why. Name the cause first."},
   {"catalog_id": "dx_acute_coronary_syndrome_unspecified", "label": "Acute coronary syndrome, unspecified",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Right family, too vague. ST elevation is the finding that sends her to the "
      "laboratory now, and the handover should say it.")},
   {"catalog_id": "dx_non_st_elevation_myocardial_infarction", "label": "Non-ST-elevation myocardial infarction",
    "verdict": "incorrect",
    "explanation": "Her ECG shows ST elevation in V2 to V5. That changes the urgency from hours to minutes."},
   {"catalog_id": "dx_panic_attack", "label": "Panic attack",
    "verdict": "incorrect",
    "explanation": (
      "This is her daughter's diagnosis. A panic attack does not cause ST elevation, a "
      "raised troponin, a new murmur or a ventricle that does not contract. Distress and "
      "serious disease often arrive together, and the first never excludes the second.")},
   {"catalog_id": "dx_hypertrophic_cardiomyopathy", "label": "Hypertrophic cardiomyopathy",
    "verdict": "incorrect",
    "explanation": (
      "A good thought, because her murmur behaves like the murmur of hypertrophic "
      "obstruction and the treatment of the obstruction is the same. Her echo shows an "
      "apex that does not move, not a thick septum, and she has never had a murmur before.")},
   {"catalog_id": "dx_aortic_dissection", "label": "Aortic dissection",
    "verdict": "incorrect",
    "explanation": (
      "Worth a thought in any chest pain with a new murmur. Her pain is crushing and not "
      "tearing, her arm pulses are equal, her mediastinum is normal and the murmur is "
      "systolic. Most dissections have no murmur, and when one is present it is the "
      "diastolic murmur of aortic regurgitation.")},
   {"catalog_id": "dx_severe_aortic_stenosis", "label": "Severe aortic stenosis",
    "verdict": "incorrect",
    "explanation": (
      "A harsh systolic murmur with a low pressure makes this reasonable. The murmur of a "
      "fixed stenosis does not change with a Valsalva strain the way hers does. The "
      "echo settles it.")},
   {"catalog_id": "dx_pulmonary_embolism", "label": "Pulmonary embolism",
    "verdict": "incorrect",
    "explanation": "Her right ventricle is normal on echo and her ECG shows precordial ST elevation with a left ventricle that is not contracting."},
   {"catalog_id": "dx_myocarditis", "label": "Myocarditis",
    "verdict": "incorrect",
    "explanation": (
      "It can mimic an infarct and it can look like takotsubo. Angiography excludes "
      "coronary disease and does not separate the two. Cardiac MRI does, later. Either "
      "way she goes to the laboratory first.")},
   {"catalog_id": "dx_acute_pericarditis", "label": "Acute pericarditis",
    "verdict": "incorrect",
    "explanation": "Pericarditis gives widespread ST elevation with PR depression and a rub, and it does not weaken the ventricle."}],

 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "infarct_pathway", "label": "Treating ST elevation as an occlusion",
    "actions": ["attach_monitor", "insert_iv", "ecg_12_lead", "aspirin",
                "consult_activate_cath_lab", "heparin_bolus_drip", "clopidogrel",
                "troponin_t", "tenecteplase_tnk_bolus"]},
   {"id": "look_at_the_heart", "label": "Looking at the heart before treating shock",
    "actions": ["exam_card", "exam_neck", "exam_pulm", "ultrasound_cardiac",
                "ultrasound_lung", "xr_chest", "nt_probnp"]},
   {"id": "obstruction", "label": "Treating outflow obstruction",
    "actions": ["normal_saline_1l_bolus", "phenylephrine_drip", "norepinephrine_drip",
                "esmolol_drip", "nitroglycerin", "dobutamine_drip", "stop_dobutamine",
                "furosemide_40_mg_iv", "consult_cardiology"]},
   {"id": "comfort", "label": "Pain and distress",
    "actions": ["fentanyl_bolus", "morphine_bolus", "lorazepam_bolus"]},
   {"id": "disposition", "label": "Disposition",
    "actions": ["consult_critical_care", "handoff_submit"]},
 ],
 "key_exams": ["exam_card", "exam_pulm", "exam_neck", "exam_circ"],
 "key_exams_note": (
   "Every exam is tagged neutral, so the Physical score reads this list: the murmur, the "
   "clear lungs, the flat neck veins and the perfusion. Model judgment."),
 "intended_path": ["presentation", "obstructed", "steadied", "case_complete"],
 "intended_path_note": (
   "The intended path passes through the obstructed phase, which arrives on a clock for "
   "every learner. A learner who has fluid and a vasoconstrictor running before it arrives "
   "goes straight to steadied."),
 "trap_actions": ["lorazepam_bolus"],
 "cross_cutting_teaching_points": [
   ("Chest pain with ST elevation is an occluded artery until an angiogram says otherwise. "
    "A funeral, a panic and a family's explanation do not change the pathway."),
   ("Before treating a low pressure in a weak heart, listen to it and look at it. A new "
    "systolic murmur can mean the usual treatment will make the patient worse."),
   ("In outflow obstruction the plan runs backwards: no nitrates, no inotropes, no "
    "diuretics. A small fluid bolus if the lungs are clear, and a vasoconstrictor that "
    "does not drive the heart. Avoiding those drugs and giving fluid is in the consensus "
    "document. The choice of vasoconstrictor is physiology and expert opinion."),
   ("When a treatment makes the patient worse, stop it. That is a decision, and it is "
    "often the hardest one in the room."),
   ("Call cardiology the moment the pressure falls in a patient with ST elevation. Asking "
    "for help early in a patient you do not fully understand is good practice."),
   ("Takotsubo cannot be diagnosed in the emergency department. The clues are an emotional "
    "or physical trigger, a very high natriuretic peptide and wall motion that crosses "
    "arterial territories. None of them keeps a "
    "patient out of the laboratory."),
   ("Outflow obstruction happens in a minority of patients with takotsubo. This case makes "
    "it happen every time so that you meet it."),
 ],
 "attempt_history_note": "Blocked attempts are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 14.3 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 6 October 2026, from a "
            "plan, a case map and a set of decisions made in the same conversation. "
            "Authoring requirements section 17 applies."),
 "warning": (
   "A physician decided the things listed in TAKO-SEED.md section 0. Everything else is "
   "model output and awaits sign-off: every vital sign, finding, laboratory value, "
   "deadline, tag, debrief note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase (shock_worse and shock_untreated share one set), and the four clocks: 180, 240, 90 and 10 seconds.",
   "Every laboratory value and reference interval, above all the troponin of 186 ng/L.",
   "The ECG and echo reports.",
   "The murmur's response to posture, which is taught for hypertrophic obstruction and "
   "assumed to carry over.",
   "That fluid plus a pure vasoconstrictor relieves the obstruction in ten seconds.",
   "That norepinephrine is accepted as the vasoconstrictor and tagged neutral.",
   "That a beta blocker is discouraged before a vasoconstrictor and neutral after.",
   "That nothing is harmful, including thrombolysis.",
   "That the cardiologist takes over ninety seconds after being called.",
   "The interview in full and both diagnosis lists.",
 ],
 "reference_status": "No reference has been checked by a physician. Notes carry [UNVERIFIED] markers.",
 "catalog_change_requests": [
   "'Activate Catheterization Lab' is a case-only action, not in the catalog, placed on the "
   "Consults tab on the directing physician's instruction. A global entry would give "
   "nothing away and would serve any future infarct case.",
   "The catalog offers crystalloid only as 500 mL and one liter. The dose this case teaches "
   "is 250 to 500 mL.",
   "The catalog's troponin T and NT-proBNP defaults are qualitative. This case authors "
   "numbers.",
   "There is no diagnosis entry for left ventricular outflow tract obstruction.",
 ],
}
