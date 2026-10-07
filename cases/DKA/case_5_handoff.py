"""DKA part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "stepdown_telemetry",
   "label": "Step-down or intermediate care with telemetry",
   "level_of_care": "intermediate",
   "explanation": (
     "She needs hourly glucose checks, an insulin regimen that is being adjusted, "
     "intravenous potassium and a monitor. A step-down or intermediate unit does all of "
     "that.\n\n"
     "The grade of ketoacidosis is not what puts her there. The 2024 consensus report "
     "suggests a regular or observation unit for mild ketoacidosis, and says the level "
     "of care is a clinical decision. Her potassium of 3.1 and the intravenous "
     "replacement on a monitor are what make step-down the better fit.\n\n"
     "What the receiving team needs: the potassium before and after replacement, when "
     "insulin started and by which route, the plan for dextrose when the glucose is "
     "under 250, and that she reduced and then stopped her own insulin because she was "
     "not eating. She needs her long-acting insulin restarted, and sick-day teaching "
     "before she goes home: basal insulin is not stopped during illness, even when not "
     "eating, and ketones are checked.")},

 "alternative_dispositions": [
   {"id": "icu", "label": "Intensive care unit",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Safe, and more than she needs. She is alert with mild ketoacidosis. Some hospitals "
      "send every insulin infusion to intensive care, and in those hospitals this is the "
      "right answer.")},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "The consensus report suggests a regular unit for mild ketoacidosis, so this is "
      "defensible where the unit can check a glucose every hour, run intravenous "
      "potassium on a monitor and follow a subcutaneous insulin protocol. Many cannot, "
      "and her potassium is the reason to ask.")},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "The consensus report lists an observation unit for mild ketoacidosis, and some "
      "departments run a subcutaneous insulin protocol there. A potassium that started at "
      "3.1 and needs intravenous replacement on a monitor makes her a poor fit unless the "
      "unit is set up for it.")},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": (
      "She is still in ketoacidosis. It takes hours of insulin for the ketones to clear, "
      "and she cannot yet keep fluid down. This is the outcome the triage story leads to "
      "if nobody checks a sugar.")},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": "This hospital has everything she needs."}],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_diabetic_ketoacidosis",
   "label": "Diabetic ketoacidosis",
   "explanation": (
     "A glucose of 348, blood ketones of 4.2 mmol/L and a pH of 7.27 with a bicarbonate "
     "of 16 in a patient with type 1 diabetes. All three parts of the definition are "
     "present. With a pH above 7.25, a bicarbonate of 15 to 18 and a clear head it is "
     "mild.\n\n"
     "Mild describes the acidosis. It does not describe the risk. Her potassium was low "
     "before treatment, and the usual first drug would have made it dangerous.")},

 "additional_diagnoses": [
   {"catalog_id": "dx_hypokalemia", "label": "Hypokalemia",
    "explanation": (
      "The finding that changed the order of treatment. The receiving team needs to know "
      "it was 3.1 on arrival, because insulin will keep pushing it down and it needs "
      "checking every two to four hours.")},
   {"catalog_id": "dx_hypomagnesemia", "label": "Hypomagnesemia",
    "explanation": "A low magnesium makes a low potassium harder to correct. Worth naming so it is replaced and rechecked."},
   {"catalog_id": "dx_viral_gastroenteritis", "label": "Viral gastroenteritis",
    "explanation": (
      "The trigger. Naming it tells the next team that the search for a cause was made "
      "and that no other source was found on examination or in the urine.")},
   {"catalog_id": "dx_hypovolemia", "label": "Hypovolemia",
    "explanation": "She was dry from vomiting, diarrhea and the glucose in her urine. True, and treated with the first bolus."}],

 "alternative_diagnoses": [
   {"catalog_id": "dx_viral_gastroenteritis", "label": "Viral gastroenteritis",
    "verdict": "incorrect",
    "explanation": (
      "She has it, and as the main diagnosis it stops one step short. Gastroenteritis "
      "explains the vomiting. It does not explain a glucose of 348, deep breathing or a "
      "bicarbonate of 16. This is the diagnosis that sends her home. Name it beside the "
      "ketoacidosis as the trigger.")},
   {"catalog_id": "dx_infectious_gastroenteritis", "label": "Infectious gastroenteritis",
    "verdict": "incorrect",
    "explanation": (
      "The trigger and not the problem that needs a hospital bed. The glucose, the "
      "ketones and the gas make the diagnosis.")},
   {"catalog_id": "dx_hypokalemia", "label": "Hypokalemia",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "True, and the most dangerous number she has. It is a complication. The diagnosis "
      "that explains the admission is the ketoacidosis. Name this beside it.")},
   {"catalog_id": "dx_anion_gap_metabolic_acidosis", "label": "Anion gap metabolic acidosis",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Correct as a description of the gas and the chemistry. With a high glucose and "
      "ketones of 4.2 the cause is known, and the handover should say it.")},
   {"catalog_id": "dx_hypovolemia", "label": "Hypovolemia",
    "verdict": "incorrect",
    "explanation": "True and incomplete. Fluid alone left her bicarbonate and anion gap where they were."},
   {"catalog_id": "dx_hyperosmolar_hyperglycemic_state", "label": "Hyperosmolar hyperglycemic state",
    "verdict": "incorrect",
    "explanation": (
      "That is a much higher glucose and osmolality with little ketosis, usually in an "
      "older patient with type 2 diabetes. Her glucose is 348, her osmolality is normal "
      "and her ketones are high.")},
   {"catalog_id": "dx_alcoholic_ketoacidosis", "label": "Alcoholic ketoacidosis",
    "verdict": "incorrect",
    "explanation": (
      "Ketoacidosis after heavy drinking and poor intake, usually with a normal or low "
      "glucose. She drinks little, had none this week, and has type 1 diabetes with a "
      "glucose of 348.")},
   {"catalog_id": "dx_acute_pancreatitis", "label": "Acute pancreatitis",
    "verdict": "incorrect",
    "explanation": (
      "Worth a thought with vomiting and abdominal pain, and it can trigger "
      "ketoacidosis. Her pain is crampy and diffuse, her abdomen is soft and her lipase "
      "is normal.")},
   {"catalog_id": "dx_acute_appendicitis", "label": "Acute appendicitis",
    "verdict": "incorrect",
    "explanation": "Her appendix was removed when she was fifteen, and her abdomen has no localized tenderness."},
   {"catalog_id": "dx_hyperemesis_gravidarum", "label": "Hyperemesis gravidarum",
    "verdict": "incorrect",
    "explanation": "Her pregnancy test is negative. It was right to check."},
   {"catalog_id": "dx_cannabinoid_hyperemesis_syndrome", "label": "Cannabinoid hyperemesis syndrome",
    "verdict": "incorrect",
    "explanation": "She does not use cannabis, and it does not cause a high glucose with ketones."}],

 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "recognition", "label": "Recognizing and grading ketoacidosis",
    "actions": ["attach_monitor", "fingerstick_blood_sugar", "venous_blood_gas",
                "arterial_blood_gas", "basic_chemistry_chem_7", "beta_hydroxybutyrate"]},
   {"id": "fluid", "label": "Fluid",
    "actions": ["insert_iv", "normal_saline_1l_bolus"]},
   {"id": "potassium_first", "label": "Potassium before insulin",
    "actions": ["potassium_chloride_kcl", "potassium_chloride_oral", "magnesium_level",
                "magnesium_sulfate", "ecg_12_lead", "stop_insulin"]},
   {"id": "insulin", "label": "Insulin and what follows it",
    "actions": ["insulin_drip", "insulin_subcutaneous", "insulin_bolus",
                "insulin_glargine_subcutaneous",
                "d5_1_2_ns_infusion", "na_bicarbonate_bolus"]},
   {"id": "trigger", "label": "Looking for a trigger",
    "actions": ["urinalysis", "urine_hcg_qualitative", "lipase", "xr_chest", "ct_abdomen"]},
   {"id": "disposition", "label": "Disposition",
    "actions": ["consult_endocrinology", "consult_critical_care", "handoff_submit"]},
 ],
 "key_exams": ["exam_breath", "exam_circ", "exam_heent", "exam_abd", "exam_neuro"],
 "key_exams_note": (
   "Every exam is tagged neutral, so the Physical score reads this list: the deep "
   "breathing, the perfusion, the dry mouth, the abdomen and the mental state. Model "
   "judgment."),
 "intended_path": ["presentation", "potassium_replaced", "treated", "case_complete"],
 "intended_path_note": (
   "Fluid, the chemistry, potassium, a repeat level, then insulin. A learner who gives "
   "insulin first passes through potassium_falling and recovering and reaches the same "
   "end."),
 "trap_actions": ["insulin_bolus", "na_bicarbonate_bolus", "d50_bolus", "ct_abdomen"],
 "cross_cutting_teaching_points": [
   ("Know the potassium before you give insulin. Under 3.5, replace it and hold insulin "
    "until it is back above 3.5. Insulin, bicarbonate and fluid all push potassium down."),
   ("A vomiting adult who looks dry or is breathing deeply gets a bedside glucose. "
    "Ketoacidosis often arrives looking like a stomach bug."),
   ("Fluid treats the dehydration and insulin treats the ketoacidosis. When the glucose "
    "falls under 250, add dextrose and keep the insulin going until the ketones clear."),
   ("Mild describes the pH. It does not describe the risk. The most dangerous number in "
    "this patient was not the glucose."),
   ("Patients who stop eating often stop their insulin. In type 1 diabetes basal insulin "
    "is not stopped during illness, even when not eating, and that teaching is part of "
    "the discharge."),
   ("The simulator compresses hours into seconds and does not model doses. The order of "
    "the steps is the lesson, and the timings are not."),
 ],
 "attempt_history_note": "Blocked attempts are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 14.3 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 6 October 2026, from a "
            "plan and four decisions made in the same conversation. Authoring "
            "requirements section 17 applies."),
 "warning": (
   "A physician decided the things listed in DKA-SEED.md section 0. Everything else is "
   "model output and awaits sign-off: every vital sign, finding, laboratory value, delay, "
   "tag, debrief note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase, and the two delays: 10 seconds for insulin to act and 20 seconds for potassium to run in.",
   "Every laboratory value and reference interval, above all the potassium in each state (3.1, 3.0, 2.9, 3.6, 3.7, 2.6).",
   "That insulin at a potassium of 3.1 produces weakness, ectopy and a potassium of 2.6.",
   "That bicarbonate lowers the potassium from 3.1 to 2.9.",
   "That oral potassium is vomited and has no effect.",
   "That ondansetron adds 5 ms to the QTc on a repeat ECG, and that the wait for potassium raises the ketones from 4.2 to 4.6.",
   "That magnesium is recommended and is not required for the potassium to correct.",
   "That nothing is harmful, including an insulin bolus at a potassium of 3.1.",
   "That step-down is the correct disposition and three others are defensible.",
   "The ECG reports and the monitor blocks.",
   "The interview in full and both diagnosis lists.",
 ],
 "reference_status": (
   "The 2024 consensus report was read through a summarizing tool on 6 October 2026, from "
   "a mirror of the Diabetologia version. Quotations in the notes are that tool's and "
   "have not been checked against the publisher's text. No reference has been checked by "
   "a physician."),
 "catalog_change_requests": [
   "Beta-Hydroxybutyrate, Insulin (Subcutaneous) and Potassium Chloride (oral) were added "
   "to the global catalog for this case on the directing physician's instruction (v0.23).",
   "The existing potassium entry has no route. This case shows it as 'Potassium Chloride "
   "(KCl) IV' and adds a vascular access prerequisite. A global rename would be cleaner.",
   "There is no action for restarting a stopped infusion. This case reads a second "
   "administration of insulin as the restart.",
   "Insulin Glargine (Subcutaneous) was added to the global catalog on the directing "
   "physician's instruction (v0.23a), so the basal dose she missed can be ordered.",
   "The catalog has no dose, so the rate of potassium replacement cannot be taught by "
   "doing.",
 ],
}
