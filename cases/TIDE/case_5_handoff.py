"""TIDE part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "icu",
   "label": "Intensive care unit",
   "level_of_care": "intensive",
   "explanation": (
     "He met the definition of severe pneumonia on arrival, and the major criteria once he "
     "needed a vasopressor and a tube. Septic shock on a vasopressor and mechanical ventilation "
     "are intensive care.\n\n"
     "What the receiving team needs: the antibiotics and when they went in, how much fluid he "
     "had and what it did, when the vasopressor started and how his pressure has held, the "
     "intubation and how he tolerated it, his sedation, his metformin and lisinopril to hold, "
     "and the results pending: blood cultures.")},
 "alternative_dispositions": [
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care with telemetry",
    "verdict": "incorrect",
    "explanation": "He needs a vasopressor and, by the end, a ventilator. Step-down cannot provide either here."},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "incorrect",
    "explanation": "Patients with severe pneumonia who deteriorate after admission to a ward do worst. He was already in shock."},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": "He is far too sick for observation."},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": "He is in septic shock and respiratory failure."},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": "This hospital has an intensive care unit, and a transfer in shock and failing support is a risk he does not need."}],
 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_community_acquired_pneumonia",
   "label": "Community-acquired pneumonia",
   "explanation": (
     "Four days of fever, rigors, a productive cough with rusty sputum and right-sided pleuritic "
     "pain, crackles and bronchial breathing at the bases, multilobar opacities on the film, a "
     "high white count and procalcitonin, and a positive pneumococcal urine antigen. It is "
     "severe: a respiratory rate over 30, a P/F under 250, multilobar infiltrates, a high BUN, "
     "hypotension needing fluid, then confusion, and finally a vasopressor and a ventilator.")},
 "additional_diagnoses": [
   {"catalog_id": "dx_septic_shock", "label": "Septic shock",
    "explanation": (
      "His pressure needed a vasopressor after fluid, with a lactate over 2. The receiving team "
      "manages the vasopressor, the steroid decision and the fluid balance.")}],
 "minor_diagnoses": [
   {"catalog_id": "dx_acute_hypoxemic_respiratory_failure", "label": "Acute hypoxemic respiratory failure",
    "explanation": "True, and the reason for the tube. The pneumonia is the cause."},
   {"catalog_id": "dx_acute_respiratory_distress_syndrome", "label": "Acute respiratory distress syndrome",
    "explanation": (
      "After intubation he has bilateral opacities and a P/F near 111 on PEEP 12 from pneumonia, "
      "which meets a moderate ARDS definition. Worth naming for the ventilator plan.")},
   {"catalog_id": "dx_acute_kidney_injury", "label": "Acute kidney injury",
    "explanation": "A creatinine of 1.7 with little urine. Hold the metformin and the lisinopril."},
   {"catalog_id": "dx_lactic_acidosis", "label": "Lactic acidosis",
    "explanation": "Part of the shock, and it follows the shock."}],
 "alternative_diagnoses": [
   {"catalog_id": "dx_sepsis", "label": "Sepsis", "verdict": "acceptable_with_qualification",
    "explanation": "True, and incomplete. Name the source, and once he needed a vasopressor, it was septic shock."},
   {"catalog_id": "dx_acute_respiratory_distress_syndrome", "label": "Acute respiratory distress syndrome",
    "verdict": "acceptable_with_qualification",
    "explanation": "Defensible after the tube, and the pneumonia is the cause that the antibiotic treats. Name the pneumonia first."},
   {"catalog_id": "dx_acute_hypoxemic_respiratory_failure", "label": "Acute hypoxemic respiratory failure",
    "verdict": "acceptable_with_qualification",
    "explanation": "True, and it names what happened, not why. Name the pneumonia."},
   {"catalog_id": "dx_aspiration_pneumonia", "label": "Aspiration pneumonia", "verdict": "incorrect",
    "explanation": "No vomiting, no reduced consciousness before the illness, and a pneumococcal antigen."},
   {"catalog_id": "dx_hospital_acquired_pneumonia", "label": "Hospital-acquired pneumonia", "verdict": "incorrect",
    "explanation": "He has not been in hospital in years. This began at home."},
   {"catalog_id": "dx_influenza", "label": "Influenza", "verdict": "incorrect",
    "explanation": "His influenza test is negative, and the picture is a bacterial pneumonia."},
   {"catalog_id": "dx_empyema", "label": "Empyema", "verdict": "incorrect",
    "explanation": "No effusion on the film or the ultrasound."},
   {"catalog_id": "dx_acute_decompensated_heart_failure_with_reduced_ejection_fraction",
    "label": "Acute decompensated heart failure with reduced ejection fraction", "verdict": "incorrect",
    "explanation": "A hyperdynamic heart, flat neck veins, a small vena cava and no edema. The crackles are pneumonia."},
   {"catalog_id": "dx_acute_decompensated_heart_failure_with_preserved_ejection_fraction",
    "label": "Acute decompensated heart failure with preserved ejection fraction", "verdict": "incorrect",
    "explanation": "Fever, rigors and rusty sputum with a small vena cava. Fluid was what he needed, not a diuretic."},
   {"catalog_id": "dx_pulmonary_embolism", "label": "Pulmonary embolism", "verdict": "incorrect",
    "explanation": "Fever, productive cough and focal consolidation, a normal right ventricle and no leg findings."},
   {"catalog_id": "dx_copd_exacerbation", "label": "COPD exacerbation", "verdict": "incorrect",
    "explanation": "A smoker, but never diagnosed with COPD, no wheeze, and his carbon dioxide was low until he tired."}],
 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "recognition", "label": "Recognizing severe pneumonia with sepsis",
    "actions": ["attach_monitor", "lactate", "blood_culture_x_2", "venous_blood_gas", "xr_chest",
                "complete_blood_count_cbc", "basic_chemistry_chem_7", "influenza_a_and_b_antigen_test"]},
   {"id": "oxygen", "label": "Oxygen and noninvasive support",
    "actions": ["hidden_oxygen", "hidden_support", "high_flow_nasal_cannula",
                "non_invasive_positive_pressure_ventilation", "non_rebreather_mask", "nasal_cannula_oxygen"]},
   {"id": "infection", "label": "Antibiotics and the steroid",
    "actions": ["hidden_beta_lactam", "hidden_atypical", "hydrocortisone_bolus"]},
   {"id": "circulation", "label": "Fluid, then a vasopressor",
    "actions": ["insert_iv", "normal_saline_1l_bolus", "hidden_reassessed", "ultrasound_cardiac",
                "ultrasound_lung", "norepinephrine_drip", "hidden_push_dose"]},
   {"id": "airway", "label": "The decision to intubate, and the physiology around it",
    "actions": ["intubate_rapid_sequence", "arterial_blood_gas"]},
   {"id": "disposition", "label": "Disposition",
    "actions": ["consult_critical_care", "handoff_submit"]},
 ],
 "key_exams": ["exam_breath", "exam_pulm", "exam_circ", "exam_skin", "exam_neuro"],
 "key_exams_note": (
   "Every exam is neutral, so the Physical score reads this list: the work of breathing, the "
   "lungs, the perfusion, the mottling and the mental state. Model judgment."),
 "intended_path": ["arrival", "fluid_response", "low_after_fluid", "on_pressor",
                   "failing_support", "ventilated", "case_complete"],
 "intended_path_note": (
   "Oxygen to high flow, cultures, antibiotics, a bolus, the drift, norepinephrine, the ICU, "
   "hydrocortisone, then the failing phase and a tube with the drip running and BiPAP "
   "preoxygenation. Intubating from on_pressor also reaches ventilated."),
 "trap_actions": ["furosemide_40_mg_iv", "metoprolol_bolus", "ct_chest", "dopamine_drip"],
 "cross_cutting_teaching_points": [
   ("A better number on the monitor is not a better patient. On high flow his saturation was "
    "88, and he was confused, breathing near 40 and paradoxically, with a rising carbon "
    "dioxide. Judge support by the work of breathing, the mental state and the trend. "
    "[UNVERIFIED: Roca et al. 2019, from memory]"),
   ("Fluid that lifts the pressure for a few minutes and lets it drift back has stopped "
    "working. The next step is a vasopressor, and a peripheral line is enough to start "
    "norepinephrine. [UNVERIFIED: SSC 2026, read through summaries]"),
   ("Have a vasopressor running before induction in a patient in shock. Induction and "
    "positive pressure take away the tone and the venous return he is living on. Preoxygenate "
    "with positive pressure. [UNVERIFIED: ACEP clinical policy, read through its web page]"),
   ("Severe pneumonia without MRSA or Pseudomonas risk gets a beta-lactam with a macrolide or "
    "a respiratory fluoroquinolone, within the hour in shock. The antibiotic changes nothing in "
    "the simulator's minutes. It changes the next days. [UNVERIFIED: IDSA/ATS 2019, from "
    "memory, and SSC 2026, read through summaries]"),
   ("Once intubated, ventilate from predicted body weight: about 6 mL/kg, near 440 mL for him, "
    "not from his actual 95 kg, with a plateau pressure of 30 or less. Start analgesia and "
    "sedation as soon as the tube is in, especially after rocuronium. The simulator has no "
    "ventilator panel. [UNVERIFIED: SSC 2021 and ED-AWARENESS, from the owner's structure and "
    "summaries]"),
   ("The simulator compresses hours into minutes. Failure on high flow develops over hours, and "
    "the ROX index was validated at two, six and twelve hours. He failed because this patient "
    "fails, not because of anything you did."),
 ],
 "attempt_history_note": "Blocked attempts are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 4 November 2026, from his case "
            "structure and his answers of the same day. Authoring requirements section 1 applies."),
 "warning": (
   "A physician decided the things in TIDE-SEED.md section 0. Everything else is model output "
   "and awaits sign-off."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase and every clock: 120 s of arrival with only the oxygen question, then 240 s to hypotension without fluid, 150 s for the fluid response to fade, 150 s to progressive shock, 150 s to arrest, 180 s from a held pressure to failing support, 150 s to fatigue, 120 s to arrest, 120 s after an unsupported tube.",
   "That failing support is scripted and arrives whatever the device (owner B5) and that the narration says the clock is compressed (owner B1).",
   "That the antibiotic moves nothing (owner B2).",
   "That any intubation without a running vasopressor drip collapses him (owner B4), and that with one he dips and recovers.",
   "Every laboratory value and interval, every gas, the lactate of 3.8 and 5.4, and the device variants of the arterial gas.",
   "Every abnormal flag on every result, finding and status line.",
   "Every exam finding and its routing.",
   "Every tag, including the critical tags on oxygen, high flow or NIV, fluid, the two antibiotic classes, the vasopressor and the decision to intubate, and every discouraged act.",
   "Every vital effect and its size: the four oxygen devices, fluid overload from the third bolus, the intubation dips, propofol, stopping a vasopressor.",
   "Every prompt deadline (oxygen 20, fluid 40 with an escalation at 70, high flow or NIV 45, antibiotic 50, vasopressor 30 with an escalation at 45, intubation 30) and the prompt cap of 4.",
   "The sedation follow-up after rocuronium (120 s, ungraded).",
   "Everything the intensivist, the pulmonologist and the infectious disease consultant say.",
   "The coverage row in the binding map: the crystalloid bolus group.",
   "The ICU disposition and the diagnosis lists.",
   "The interview in full, including every model-added fact in TIDE-SEED.md section 3.7.",
   "interview.key_topics, interview.must_ask and debrief_configuration.key_exams.",
   "The chest film and its read, and the tube drawn on it.",
   "The twelve-lead tracings borrowed from TSS and SCOOT, their reads, and the heart rates of the ventilated (112) and tiring (56) phases set to match them.",
   "Every debrief note and every handoff explanation.",
 ],
 "reference_status": [
   {"reference": "Owner's case structure, pasted 4 November 2026",
    "how_read": "In full by the model", "status": "The basis of the case. Its citations were checked only as listed below"},
   {"reference": "Prescott H, Antonelli M, Alhazzani W, et al. Surviving Sepsis Campaign: international guidelines for management of sepsis and septic shock 2026. Crit Care Med 2026",
    "how_read": "SCCM guideline page and published summaries, through web search on 4 November 2026",
    "status": "Not opened. Recommendations quoted in notes are from the summaries"},
   {"reference": "Jones BE, Ramirez JA, Oren E, et al. Diagnosis and management of community-acquired pneumonia. An official ATS clinical practice guideline. Am J Respir Crit Care Med 2025",
    "how_read": "Summaries through web search", "status": "Not opened"},
   {"reference": "Metlay JP, et al. Diagnosis and treatment of adults with community-acquired pneumonia. Am J Respir Crit Care Med 2019",
    "how_read": "From memory", "status": "Unverified"},
   {"reference": "Dequin PF, et al. Hydrocortisone in severe community-acquired pneumonia (CAPE COD). N Engl J Med 2023;388:1931-41",
    "how_read": "PubMed abstract and The Bottom Line summary through web search",
    "status": "Mortality figures from the abstract. The septic shock exclusion from the summary only"},
   {"reference": "Pappal RD, et al. The ED-AWARENESS study. Ann Emerg Med 2021. Fuller BM, et al. Awareness with paralysis among critically ill ED patients. Crit Care Med 2022",
    "how_read": "Summaries through web search", "status": "Not opened"},
   {"reference": "Maia IS, et al. RENOVATE. JAMA 2025;333(10):875",
    "how_read": "Summaries through web search", "status": "Not opened"},
   {"reference": "ACEP clinical policy: critical issues in the management of adult patients requiring endotracheal intubation in the ED",
    "how_read": "ACEP web page through web search", "status": "Policy text not opened. Author and year not confirmed"},
   {"reference": "Gibbs KW, et al. Noninvasive ventilation for preoxygenation during emergency intubation (PREOXI). N Engl J Med 2024",
    "how_read": "Citation seen in reference lists", "status": "Percentages from the owner's structure, unverified"},
   {"reference": "Roca O, et al. ROX index. Am J Respir Crit Care Med 2019",
    "how_read": "From memory and the owner's structure", "status": "Unverified"},
   {"reference": "Munroe ES, et al. AJRCCM 2023. File TM and Ramirez JA, NEJM 2023. Martin-Loeches I, et al. ERS/ESICM/ESCMID/ALAT 2023. Evans L, et al. SSC 2021",
    "how_read": "Cited from the owner's structure", "status": "Not opened"},
   {"reference": "Twelve-lead tracings copied from TSS (four) and SCOOT (one), media/README.md",
    "how_read": "Each looked at by the model beside its read on 4 November 2026",
    "status": "Generated, synthetic. A named person must look at each beside its read, in its phase, before release"},
   {"reference": "Chest film Pneumonia/Multifocal_Male.png, from the owner's folder 'Images Manual - Chest XRay'",
    "how_read": "Looked at by the model on 4 November 2026 beside its read",
    "status": "Source and license of the folder not recorded. A named person must look at both films before release"},
 ],
 "catalog_change_requests": [
   "Done 4 November 2026 on the owner's instruction: High-Flow Nasal Cannula added to the catalog, with voice phrases, expectation credit and a figure add-on.",
   "No titrate action for a vasopressor. A second agent stands in where one is needed.",
   "No ventilator settings, laryngoscope choice, bougie or capnography (owner: not in this version).",
   "No MRSA nares PCR, sputum culture and Gram stain, Legionella urine antigen, respiratory viral PCR or passive leg raise.",
   "No diagnosis entry for influenza pneumonia or Legionella pneumonia.",
   "Twelve-lead tracings for this case need the ECG generator built. Until then the ECG shows the TSS or SCOOT tracing nearest each phase's rate (media/README.md).",
 ],
}
