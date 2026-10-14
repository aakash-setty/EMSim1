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
      "checking every one to two hours while it is being replaced.")},
   {"catalog_id": "dx_hypomagnesemia", "label": "Hypomagnesemia",
    "explanation": "A low magnesium makes a low potassium harder to correct. Worth naming so it is replaced and rechecked."},
   {"catalog_id": "dx_viral_gastroenteritis", "label": "Viral gastroenteritis",
    "explanation": (
      "The trigger. Naming it tells the next team that the search for a cause was made "
      "and that no other source was found on examination or in the urine.")},
   {"catalog_id": "dx_hypovolemia", "label": "Hypovolemia",
    "explanation": "She was dry from vomiting, diarrhea and the glucose in her urine. True, and treated with the first fluid."},
   ],
 # Hyponatremia and acute kidney injury were additional diagnoses for one day (7 October
 # 2026). The medical re-read the same day moved them to defensible alternatives: a sodium
 # of 133 at a glucose of 348 corrects to normal, and a single creatinine of 1.2 with no
 # baseline does not meet the definition of acute kidney injury. Naming either beside the
 # ketoacidosis costs nothing, and the explanation teaches the correction.

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
   {"catalog_id": "dx_hyponatremia", "label": "Hyponatremia",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Her measured sodium was 133 at a glucose of 348. Corrected for the glucose, by "
      "adding 1.6 to 2.4 for every 100 mg/dL above 100, it is about 137 to 139, which is "
      "normal. Glucose draws water into the blood and dilutes the sodium, and the number "
      "rises on its own as the glucose falls. Report the corrected value, and expect the "
      "measured one to climb.")},
   {"catalog_id": "dx_acute_kidney_injury", "label": "Acute kidney injury",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Her creatinine was 1.2 with a BUN of 24, in a woman who was dry, and no earlier "
      "value is known. A single creatinine does not meet the definition of acute kidney "
      "injury, which needs a rise against a baseline or a fall in urine output. The "
      "likely reading is a kidney short of volume, and the handover is to repeat the "
      "creatinine after fluid.")},
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
    "actions": ["insert_iv", "normal_saline_1l_bolus", "normal_saline_infusion",
                "lactated_ringer_s_infusion"]},
   {"id": "potassium_first", "label": "Potassium before insulin, and with it",
    "actions": ["potassium_chloride_kcl", "potassium_maintenance", "potassium_chloride_oral",
                "magnesium_level", "magnesium_sulfate", "ecg_12_lead", "stop_insulin"]},
   {"id": "insulin", "label": "Insulin and what follows it",
    "actions": ["insulin_drip", "insulin_subcutaneous", "insulin_bolus", "insulin_restart",
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
   "Fluid, the chemistry, potassium, a repeat level, then insulin with potassium in the "
   "fluids. A learner who gives "
   "rapid insulin at any point before the potassium has run in passes through "
   "potassium_falling and recovering and reaches the same end."),
 "trap_actions": ["insulin_bolus", "na_bicarbonate_bolus", "d50_bolus", "ct_abdomen"],
 "cross_cutting_teaching_points": [
   ("Know the potassium before you give insulin. Under 3.5, hold insulin and replace it "
    "at 20 to 40 mEq an hour, rechecking every one to two hours, and start insulin once "
    "the level is 3.5 or more. Between 3.5 and 5.5, insulin runs with 20 to 30 mEq of "
    "potassium in each liter. Over 5.5, hold the potassium and start insulin. Insulin, "
    "bicarbonate and fluid all push potassium down. "
    "[Potassium rule from the reference table supplied by the directing physician, "
    "7 October 2026] [UNVERIFIED: Umpierrez et al. 2024, read through a summarizing tool]"),
   ("A vomiting adult who looks dry or is breathing deeply gets a bedside glucose. "
    "Ketoacidosis often arrives looking like a stomach bug."),
   ("Fluid treats the dehydration and insulin treats the ketoacidosis. When the glucose "
    "falls under 250, add dextrose and keep the insulin going until the ketones clear. "
    "[UNVERIFIED: Umpierrez et al. 2024, read through a summarizing tool]"),
   ("Mild describes the pH. It does not describe the risk. The most dangerous number in "
    "this patient was not the glucose."),
   ("Patients who stop eating often stop their insulin. In type 1 diabetes basal insulin "
    "is not stopped during illness, even when not eating, and that teaching is part of "
    "the discharge. [UNVERIFIED: general teaching written by a model from memory]"),
   ("The simulator compresses hours into seconds and does not model doses. The order of "
    "the steps is the lesson, and the timings are not."),
 ],
 "attempt_history_note": "Blocked attempts are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 6 October 2026, from a "
            "plan and four decisions made in the same conversation. Authoring "
            "requirements section 1 applies."),
 "warning": (
   "A physician decided the things listed in DKA-SEED.md section 0. Everything else is "
   "model output and awaits sign-off: every vital sign, finding, laboratory value, delay, "
   "tag, debrief note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase, and the three delays: 10 seconds for insulin to act, 20 seconds for potassium to run in, and 5 seconds for insulin given during the potassium infusion to act once it finishes.",
   "Every laboratory value and reference interval, above all the potassium in each state (3.1, 3.0, 2.9, 3.6, 3.7, 2.6).",
   "Every abnormal flag on every result, finding and status line.",
   "Every exam finding, its routing to a maneuver, and how it changes by phase.",
   "That insulin at a potassium of 3.1 produces weakness, ectopy and a potassium of 2.6.",
   "That any rapid insulin ordered before the potassium infusion has finished produces the same fall, whatever the gap.",
   "That potassium given before the fall counts toward the rescue once insulin is held.",
   "That bicarbonate lowers the potassium from 3.1 to 2.9.",
   "That oral potassium has no effect at any point in the case.",
   "That ondansetron adds 5 ms to the QTc on a repeat ECG, and that the wait for potassium raises the ketones from 4.2 to 4.6.",
   "That magnesium is recommended and is not required for the potassium to correct.",
   "That nothing is harmful, including an insulin bolus at a potassium of 3.1.",
   "Every clinical tag, including the critical tag on restarting insulin in the recovering phase, the critical tag on potassium continued with the insulin (a second potassium order once the level is 3.5 or more, decided by the directing physician on 7 October 2026) and the neutral tags on the two crystalloid infusions, the central lines and the intraosseous line.",
   "That a crystalloid infusion earns the same credit as a bolus.",
   "The two vital effects of fluid: heart rate down 10 and systolic pressure up 6, with no end. Teaching choices, not measurements.",
   "Every prompt deadline (20, 25, 40, 45, 70, 75, 100, 110 and the escalation at 170 seconds, and 45 seconds for potassium in the fluids once treated) and both follow-up deadlines (50 and 60 seconds).",
   "The one case prerequisite (a line before intravenous potassium), and that the monitor is not required first.",
   "Both follow-ups, what triggers each and what discharges each.",
   "Everything the endocrinologist and the intensivist say.",
   "The three coverage rows in the binding map: the crystalloid bolus group, the two magnesium entries and the two bicarbonate entries.",
   "That step-down is the correct disposition and three others are defensible.",
   "The ECG reports and the monitor blocks.",
   "The cardiac ultrasound report, derived by a model on 7 October 2026 from the pack's other findings.",
   "The interview in full, including the two denials added on 7 October 2026 (no leg cramps, no black stools) and the facts on four topics.",
   "interview.key_topics, interview.must_ask and debrief_configuration.key_exams.",
   "Both diagnosis lists, including hyponatremia and acute kidney injury as defensible alternatives since 7 October 2026, with the corrected-sodium arithmetic (1.6 to 2.4 per 100 mg/dL of glucose above 100) in the hyponatremia explanation.",
   "The potassium rule by level and its numbers (hold insulin under 3.5, 20 to 40 mEq an hour, recheck every one to two hours, insulin once 3.5 or more, 20 to 30 mEq per liter between 3.5 and 5.5, hold potassium over 5.5), taken from the reference table the directing physician supplied on 7 October 2026 and applied by a model.",
   "Every debrief note and every handoff explanation. Handoff explanations and follow-up notes cannot carry a marker, and several cite the 2024 consensus report.",
 ],
 "reference_status": [
   {"reference": ("Umpierrez GE, et al. Hyperglycaemic crises in adults with diabetes: a consensus "
                  "report (ADA, EASD, JBDS, AACE, DTS). Diabetologia and Diabetes Care, 2024"),
    "how_read": ("A mirror of the Diabetologia PDF, read through a summarizing tool by a model on "
                 "6 October 2026, and again by an independent checking pass. Figure 4 was not "
                 "readable. The publisher's sites refused the request"),
    "status": ("Quotations and figures in the notes are the tool's and were not checked against "
               "the publisher's text. Not checked by a physician. The verbatim quotation about "
               "basal insulin was replaced with a paraphrase on 7 October 2026. The potassium "
               "replacement rate as read from it (lower than 20 mEq an hour) was superseded on "
               "7 October 2026 by the table the directing physician supplied")},
   {"reference": ("Potassium repletion table supplied by the directing physician, Aakash Setty, "
                  "on 7 October 2026, as a screenshot of a reference whose own citation "
                  "(marked [11]) was not visible"),
    "how_read": "Read by a model from the screenshot",
    "status": ("Sets the case's potassium rule: hold insulin under 3.5, 20 to 40 mEq KCl an hour "
               "intravenously, recheck every 1 to 2 hours, start insulin only at 3.5 or more, 20 to "
               "30 mEq per liter of fluid between 3.5 and 5.5 with insulin concurrently, hold "
               "potassium over 5.5 and recheck in 1 to 2 hours. Its bullet also says insulin may "
               "wait only until supplementation is underway when the level is under 3.5, which is "
               "looser than its own table row. The case follows the row. Not checked beyond that")},
   {"reference": "UBC RTVS simulation case, Basic Diabetic Ketoacidosis",
    "how_read": "Opened through the same summarizing tool by a model on 6 October 2026",
    "status": "Used for the shape of the case only. Nothing is quoted. Not checked by a physician"},
   {"reference": "FDA drug safety communication on ondansetron and the QT interval",
    "how_read": "Opened by a model in the checking pass on 6 October 2026",
    "status": ("Supplies 6 ms at 8 mg and 20 ms at 32 mg intravenously, and the advice to correct "
               "potassium and magnesium first. Not checked by a physician")},
   {"reference": "Cleveland Clinic Journal of Medicine review of the 2024 consensus report",
    "how_read": "Opened by a model in the checking pass on 6 October 2026",
    "status": "Used to cross-check potassium, bicarbonate, phosphate and level of care. Not checked by a physician"},
   {"reference": "EMCrit Internet Book of Critical Care, chapter on diabetic ketoacidosis",
    "how_read": "A summary, read by a model in the checking pass on 6 October 2026",
    "status": "Used only to note that US practice often differs (a 3.3 threshold, faster potassium). Not checked by a physician"},
   {"reference": "Kitabchi AE, et al. Hyperglycemic crises in adult patients with diabetes. ADA consensus statement, Diabetes Care 2009",
    "how_read": "Could not be opened. From memory",
    "status": "The statement that the 2009 threshold was 3.3 is from a model's memory. Unverified"},
   {"reference": "MedEdPORTAL simulation case (PMC5491337) and the StatPearls chapter on diabetic ketoacidosis",
    "how_read": "Could not be opened",
    "status": "Supplied nothing"},
   {"reference": "Teaching on hypomagnesemia with hypokalemia, the ECG of a low potassium, oral potassium, urine and pregnancy testing, and sick-day rules",
    "how_read": "From memory. No source opened",
    "status": "Written by a model. Unverified. Each such note carries a marker where the field allows one"},
 ],
 "reference_status_note": (
   "Markers sit only where the interface strips them: action debrief notes, timed "
   "transition notes and the cross-cutting teaching points. Follow-up notes and handoff "
   "explanations are printed as written, so they carry none. Those that cite the "
   "consensus report rest on the first entry above."),
 "audit_fix": (
   "Revised by a language model on 7 October 2026 after the audit of 6 October 2026. "
   "DKA-SEED.md section 5a lists what changed and why. No physician has reviewed the "
   "revision."),
 "catalog_change_requests": [
   "Done in v0.23 and v0.23a, on the directing physician's instruction: Beta-Hydroxybutyrate, "
   "Insulin (Subcutaneous), Potassium Chloride (oral) and Insulin Glargine (Subcutaneous) "
   "were added to the global catalog.",
   "Done on 7 October 2026: the diagnosis catalog gained euglycemic diabetic ketoacidosis, "
   "starvation ketosis, hyperglycemia, type 1 diabetes mellitus and acquired long QT. This "
   "case does not use them yet. Each needs a physician's verdict first (DKA-SEED.md, open "
   "questions).",
   "The existing potassium entry has no route. This case shows it as 'Potassium Chloride "
   "(KCl) IV' and adds a vascular access prerequisite. A global rename would be cleaner.",
   "There is no action for restarting a stopped infusion. This case reads an insulin "
   "order placed in the recovering phase as the restart, through a hidden case action.",
   "The catalog has no dose, so the rate of potassium replacement cannot be taught by "
   "doing.",
   "The rhythm field has two values, regular and irregularly irregular. The falling "
   "phase describes extra beats, dropped beats and ectopy in the exam, the interview and "
   "the ECG report, over a regular beat and a regular trace. A third value for occasional "
   "ectopy would let the monitor agree (authoring 5.2).",
   "A spoken 'insulin' offers the bolus or the infusion and not the subcutaneous entry. "
   "The bolus is the discouraged one in this case. The fix is in "
   "catalog/build_voice_aliases.py.",
   "The scenario runner does not implement also_satisfies. Scenarios that depend on a "
   "hidden target name it as a step. DKA-tests.js folds the real routes.",
 ],
}
