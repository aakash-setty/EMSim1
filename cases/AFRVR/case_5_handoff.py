"""AFRVR part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "icu_or_ccu",
   "label": "Intensive care or coronary care unit",
   "level_of_care": "critical_care",
   "explanation": (
     "He is on non-invasive ventilation, he has a newly recognised ejection fraction of 30 to 35 "
     "percent, and he has just had a rate-controlling drug. The unit that takes him has to be able "
     "to continue positive pressure, run continuous cardiac monitoring, reassess him frequently in "
     "the next few hours, and intubate him without moving him if the mask fails. In most "
     "institutions that is an intensive care or coronary care bed. If he was intubated during the "
     "case, the answer is unambiguously intensive care.\n\n"
     "The reasoning is what is being scored, not the name of the ward. The question to be able to "
     "answer is what the receiving unit must be able to do, and this case is written for a hospital "
     "where every option exists.")},

 "alternative_dispositions": [
  {"id": "stepdown_telemetry",
   "label": "Step-down or intermediate care unit with telemetry",
   "verdict": "acceptable_with_qualification",
   "explanation": (
     "Defensible, and at many hospitals this is where this patient actually goes. It turns entirely "
     "on local capability: a step-down unit that can maintain non-invasive ventilation, monitor "
     "continuously and escalate quickly is an appropriate destination, and one that cannot is not. "
     "A learner who chose this and can say what the unit needs to be able to do has answered the "
     "question. If he was intubated, this becomes wrong.")},
  {"id": "medical_floor_telemetry",
   "label": "General medical ward with telemetry",
   "verdict": "incorrect",
   "explanation": (
     "Not while he is on a mask. A general ward with telemetry can monitor the rhythm and cannot "
     "run non-invasive ventilation, and the nursing ratio does not support the frequency of "
     "reassessment the next few hours need. There is a version of this patient for whom this is "
     "the right answer, and it is the version who has been weaned off positive pressure, is "
     "comfortable on room air or a cannula, and has a stable rate: that is a reasonable "
     "twelve-hour destination and not a reasonable one from the department. The judgement error "
     "here is treating improvement as resolution. He looks much better than he did on arrival "
     "because of two things a general ward cannot continue.")},
  {"id": "observation_unit",
   "label": "Emergency department observation unit",
   "verdict": "incorrect",
   "explanation": (
     "Observation pathways exist for both atrial fibrillation and heart failure and both have "
     "narrow entry criteria that this patient fails. The atrial fibrillation pathways are for "
     "recent-onset arrhythmia in patients without heart failure, without hypoxaemia and without "
     "haemodynamic consequence, with a plan for cardioversion or rate control and discharge. The "
     "heart failure pathways are for mild congestion without ventilatory support and with a prompt "
     "response to a single diuretic dose. He required positive pressure ventilation, he has newly "
     "recognised moderate to severe systolic dysfunction, and his arrhythmia has no established "
     "onset time.")},
  {"id": "discharge_home",
   "label": "Discharge home on rate control and anticoagulation with cardiology follow-up",
   "verdict": "incorrect",
   "explanation": (
     "Unsafe. There is a real population of patients with new atrial fibrillation who are "
     "discharged from the emergency department on rate control and anticoagulation, and every one "
     "of them is well, oxygenating, and has no heart failure. This man presented in hypoxaemic "
     "respiratory failure, required ventilatory support, and has an ejection fraction nobody knew "
     "about an hour ago. That he improved quickly does not undo any of it. Early mortality after "
     "a first admission for decompensated heart failure is substantial, and the newly discovered "
     "cardiomyopathy is by itself a reason for an inpatient workup.")},
  {"id": "cardiac_catheterization_lab",
   "label": "Direct to the cardiac catheterisation laboratory",
   "verdict": "incorrect",
   "explanation": (
     "Choosing this almost always means the troponin of 38 or the lateral ST depression was read "
     "as an acute coronary occlusion. Neither is. The ST depression is rate-related "
     "repolarisation change in a patient at 160 and it improves when the rate comes down, which is "
     "why the repeat tracing is worth taking. The troponin is a demand pattern. Acute coronary "
     "syndrome is a real precipitant of new atrial fibrillation and of decompensation and deserves "
     "inpatient consideration and a repeat troponin, but nothing here justifies emergent "
     "revascularisation, and taking a hypoxaemic patient on non-invasive ventilation to the "
     "laboratory has its own cost.")},
 ],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu_or_ccu", "cardiac_catheterization_lab"],
 "disposition_display_order_note": (
   "Least to most intensive, with the catheterisation laboratory last because it is a different "
   "axis rather than a more intensive ward."),

 "correct_diagnosis": {
   "catalog_id": "dx_atrial_fibrillation_with_rapid_ventricular_response",
   "label": "Atrial fibrillation with rapid ventricular response, with acute decompensated heart "
            "failure and cardiogenic pulmonary oedema on a newly recognised reduced ejection "
            "fraction",
   "explanation": (
     "New atrial fibrillation with a rapid ventricular response in a man with previously "
     "undiagnosed moderately to severely reduced left ventricular systolic function, presenting as "
     "acute decompensated heart failure with cardiogenic pulmonary oedema. Whether the arrhythmia "
     "caused the cardiomyopathy or the cardiomyopathy precipitated the arrhythmia cannot be "
     "settled in the department and does not need to be: a sustained rapid ventricular response "
     "can produce a tachycardia-induced cardiomyopathy, and a dilated left atrium in an existing "
     "cardiomyopathy readily produces atrial fibrillation. The complete formulation names both "
     "halves, and the plan that follows from it treats both."),
   "label_note": "Retained for the review packet. The interface shows the diagnosis catalog's own "
                 "display name, which is shorter."},

 "alternative_diagnoses": [
  {"catalog_id": "dx_acute_decompensated_heart_failure_with_reduced_ejection_fraction",
   "label": "Acute decompensated heart failure with reduced ejection fraction",
   "verdict": "acceptable_with_qualification",
   "explanation": (
     "This is the other half of the same answer and it is marked defensible rather than wrong. A "
     "learner who selected it has recognised the pulmonary oedema and the reduced ejection "
     "fraction, which is the harder half of the case. What it leaves out is the arrhythmia driving "
     "it, and the reason that matters is that it is the half that generates the rate-control and "
     "anticoagulation decisions. The full formulation names both, and if you can only choose one "
     "id, name the one the treatment turns on. The simulator scores a single catalog id, which is "
     "a limitation of the tool rather than a claim that this answer is wrong.")},
  {"catalog_id": "dx_cardiogenic_pulmonary_edema",
   "label": "Cardiogenic pulmonary oedema",
   "explanation": (
     "True and incomplete. It describes the radiographic and ultrasonographic finding and names "
     "neither the arrhythmia nor the ventricular dysfunction underneath it, so it generates no "
     "plan beyond positive pressure and a diuretic. A formulation you cannot write a treatment "
     "plan from is not finished.")},
  {"catalog_id": "dx_non_st_elevation_myocardial_infarction",
   "label": "Non-ST-elevation myocardial infarction",
   "explanation": (
     "The commonest wrong answer here, and it is reached honestly: there is a raised troponin and "
     "there is lateral ST depression. Both have a better explanation. The ST depression is "
     "rate-related and improves with rate control, and the troponin is a demand pattern in a "
     "ventricle running at 160 with an ejection fraction of 30 to 35 percent, which is type 2 "
     "myocardial injury rather than plaque rupture. Distinguishing type 1 from type 2 injury is "
     "the skill this alternative is testing, and the discriminators are the trajectory of the "
     "troponin, the presence or absence of an occlusion pattern on the tracing, and whether there "
     "is a better explanation for the demand. Here there is.")},
  {"catalog_id": "dx_pulmonary_embolism",
   "label": "Acute pulmonary embolism",
   "explanation": (
     "Usually selected downstream of a D-dimer that should not have been sent. The pretest "
     "probability is low: gradual onset over more than a day, symmetrical bilateral leg oedema "
     "with no calf tenderness or asymmetry, no immobilisation, travel, surgery or malignancy, and "
     "a complete alternative explanation for every symptom. The bedside ultrasound settles it: "
     "diffuse bilateral B-lines with a poorly contracting left ventricle and a plethoric inferior "
     "vena cava is left heart failure, and pulmonary embolism large enough to cause this degree of "
     "hypoxaemia would show a dilated hypokinetic right ventricle with clear lung fields. Atrial "
     "fibrillation does raise the D-dimer on its own.")},
  {"catalog_id": "dx_community_acquired_pneumonia",
   "label": "Community-acquired pneumonia",
   "explanation": (
     "Reasonable to consider and excluded by the data. He is afebrile with a normal white cell "
     "count, no sick contacts, no preceding illness, a dry cough with no sputum, and imaging "
     "showing a symmetrical interstitial pattern with effusions rather than focal consolidation. "
     "The mildly raised lactate is the finding most likely to mislead and is explained by the work "
     "of breathing. Infection is a common precipitant of decompensation, so looking for it is "
     "right and concluding it is not.")},
  {"catalog_id": "dx_supraventricular_tachycardia",
   "label": "Supraventricular tachycardia",
   "explanation": (
     "A rhythm error, and it is the one that leads to adenosine. The R-R intervals are irregularly "
     "irregular and there is no organised atrial activity, which is not compatible with a "
     "re-entrant supraventricular tachycardia. Atrial flutter with variable block is the harder "
     "distinction and is excluded by the absence of flutter waves and by the irregularity being "
     "random rather than patterned. Reading the rhythm strip properly is the whole of the "
     "difference.")},
  {"catalog_id": "dx_thyroid_storm",
   "label": "Thyroid storm",
   "explanation": (
     "Worth thinking of and not this. Hyperthyroidism is a genuine and treatable precipitant of "
     "new atrial fibrillation, which is exactly why the thyroid function test is worth sending, "
     "but thyroid storm is a different clinical picture: fever, agitation or delirium, "
     "gastrointestinal symptoms, and usually a known or clinically obvious thyroid problem. He is "
     "afebrile, oriented, has no goitre and no eye signs, and his TSH is normal.")},
 ],

 "diagnosis_entry_method": (
   "The learner searches the whole diagnosis catalog rather than choosing from a list this case "
   "supplies, because committing to a diagnosis from a wide field is the cognitive task being "
   "taught. Wrong answers outside the seven anticipated here receive the generic note."),
 "pending_result_warning": (
   "Results ordered and never read are recorded automatically and surfaced in the debrief. In this "
   "case the study most often ordered and never looked at is the repeat ECG after rate control."),
 "early_exit": {
   "available": True,
   "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
  {"id": "airway_breathing", "label": "Oxygenation and ventilation",
   "actions": ["non_invasive_positive_pressure_ventilation", "nasal_cannula_oxygen",
               "non_rebreather_mask", "intubate_rapid_sequence", "preoxygenate_for_intubation",
               "position_for_intubation", "propofol_infusion", "ketamine_infusion",
               "fentanyl_bolus", "etomidate_bolus", "ketamine_bolus", "midazolam_bolus",
               "propofol_bolus", "rocuronium_bolus", "succinylcholine_bolus"]},
  {"id": "rate_and_rhythm", "label": "Rate and rhythm control",
   "actions": ["digoxin_bolus", "diltiazem_bolus", "esmolol_drip", "propranolol_bolus",
               "adenosine_bolus", "procainamide_drip", "synchronized_cardioversion",
               "unsynchronized_cardioversion", "place_pads_for_monitoring"]},
  {"id": "decongestion", "label": "Decongestion and volume",
   "actions": ["furosemide_40_mg_iv", "magnesium_sulfate_bolus", "potassium_chloride_kcl",
               "normal_saline_1l_bolus", "insert_foley_catheter", "nitroglycerin_drip",
               "nitroglycerin_sublingual", "dobutamine_drip", "norepinephrine_drip"]},
  {"id": "thromboembolic_risk", "label": "Stroke prevention",
   "actions": ["apixaban", "aspirin", "clopidogrel", "coagulation_panel"]},
  {"id": "diagnostics", "label": "Diagnostic reasoning and test selection",
   "actions": ["ecg_12_lead", "ultrasound_cardiac", "ultrasound_lung", "xr_chest", "troponin_t",
               "pro_bnp", "basic_chemistry_chem_7", "magnesium_level",
               "complete_blood_count_cbc", "tsh", "venous_blood_gas", "lactate", "d_dimer",
               "ct_pulmonary_embolus", "ultrasound_lower_extremity_venous", "urinalysis",
               "liver_function_tests_lfts"]},
  {"id": "examination", "label": "Physical examination",
   "actions": ["exam_airway", "exam_breath", "exam_circ", "exam_neck", "exam_card", "exam_pulm",
               "exam_abd", "exam_msk", "exam_skin", "exam_neuro", "exam_psych", "exam_heent"]},
  {"id": "disposition_and_communication", "label": "Disposition and communication",
   "actions": ["attach_monitor", "insert_iv", "consult_cardiology", "consult_critical_care",
               "consult_pulmonology", "handoff_submit"]},
 ],
 "intended_path": ["presentation", "breathing_supported", "stabilized", "case_complete"],
 "trap_actions": ["d_dimer", "ct_pulmonary_embolus", "adenosine_bolus", "aspirin", "clopidogrel",
                  "ultrasound_lower_extremity_venous", "nitroglycerin_sublingual",
                  "nitroglycerin_drip", "dobutamine_drip", "urinalysis"],
 "trap_actions_note": (
   "Actions that look reasonable and are not. Most of them are tagged discouraged and appear in "
   "their own debrief section; the ones tagged neutral appear under things that looked reasonable. "
   "The D-dimer and the computed tomography are listed together because they are one error with "
   "two steps, and the second step is the expensive one."),
 "cross_cutting_teaching_points": [
  "The organising question in this case is not what the rhythm is. It is what the ventricle is "
  "doing, because that is what decides the drug. Atrial fibrillation with a rapid ventricular "
  "response has a standard answer, and this patient is the exception to it, and the only thing "
  "standing between a learner and the exception is a minute with an ultrasound probe. Getting into "
  "the habit of asking what the ejection fraction is before choosing a rate-control agent is the "
  "single most transferable thing in this case.",
  "A lower heart rate is not a resuscitated patient. It is possible to run this case, treat the "
  "arrhythmia competently, reach a ventricular rate of 108, and hand over a man who is still at a "
  "saturation of 86 percent breathing 32 times a minute with a lung full of water. The number that "
  "was easiest to fix was not the number that was going to kill him. Ask what you have actually "
  "changed, not what you have treated.",
  "A drug can do exactly what you asked of it and still be the wrong drug. Diltiazem lowers the "
  "ventricular rate in this patient and it is contraindicated in his ventricle, and the feedback "
  "the monitor gives you is reassuring while the treatment is wrong. This generalises well beyond "
  "atrial fibrillation and is worth naming explicitly when you teach it.",
  "New information should change the plan. Reaching for diltiazem on arrival, before the ejection "
  "fraction is known, is defensible. Continuing it after the ultrasound is the error, and it is an "
  "error of not updating rather than an error of knowledge. Most residents know the "
  "contraindication; fewer revisit a decision they have already made and watched work.",
  "Two problems presenting as one. The rate and the pump are both abnormal, each is making the "
  "other worse, and the emergency department does not have to determine which came first. It has "
  "to treat both. A formulation that names only one of them generates a plan that is missing half "
  "of the treatment.",
 ],
 "attempt_history_note": (
   "This case rewards replay in a specific way. A learner who gives diltiazem on the first run, "
   "watches the pressure drift down after the ultrasound, and then runs it again choosing "
   "differently has learned the thing the case exists to teach, and the second run should feel "
   "different rather than merely faster."),
}

PROVENANCE = {
 "status": "DRAFTED FROM AN AUTHOR SEED. Not reviewed by a physician. Not for use with learners.",
 "warning": (
   "The physician author supplied the clinical ground truth for this case: the diagnosis, the "
   "presenting vital signs, the physical findings, the laboratory and ultrasound results, the six "
   "critical actions, the three wrong paths, the diltiazem nuance, the accepted rate-control and "
   "anticoagulation options, and the disposition. A language model expanded that seed into this "
   "case file. Everything below the seed, including every reference interval, every debrief note, "
   "every reference, every deadline and every vital-effect size, is model output and awaits "
   "primary sign-off. Nothing here has been reviewed by a physician."),
 "author_only_fields_pending_signoff": [
   "Every reference interval in content_keys.labs, none of which came from a laboratory reference.",
   "The two 240-second deterioration deadlines, which are clinical claims about how long this "
   "patient tolerates untreated respiratory failure.",
   "The 30-second delay on the rate-control transitions, which compresses agents whose real "
   "onsets differ by an order of magnitude into one number, and the nurse line that goes with "
   "it.",
   "The four two-point steps of the positive-pressure saturation effect, both the total of eight "
   "points and the one-minute tempo.",
   "The 20 mmHg systolic and 10 mmHg diastolic fall attributed to diltiazem.",
   "The decision to bind digoxin, amiodarone and metoprolol as one act, which means a learner who "
   "gives metoprolol to a man in active pulmonary oedema is credited with the critical action and "
   "reads the caveat only in the expander.",
   "The decision to tag magnesium replacement recommended rather than critical, against the "
   "author's brief. See the note on that action and section 4 of the review packet.",
   "The decision that a crystalloid bolus is the only halting action in this case.",
   "The decision that every non-terminal phase carries an irregularly irregular heartbeat, "
   "and the shape and spread of the interval model that sounds it. The parameters are "
   "global rather than case-level, so changing them changes every future case that uses "
   "the same rhythm.",
   "The choice of a single correct diagnosis catalog id where the formulation has two halves.",
   "Every reference, all of which are marked unverified in the case file.",
 ],
 "reference_verification": (
   "No reference in this pack has been checked against its source. Every one carries an "
   "[UNVERIFIED in this pack, confirm before release] marker, which the interface strips before "
   "display and the review packet retains. A plausible-looking citation to a paper that does not "
   "say what is claimed will be believed, so these must be checked before the case is used."),
 "seed_fidelity_note": (
   "Three places where this file departs from the author's brief, each deliberate and each flagged "
   "in the review packet: magnesium replacement is recommended rather than critical; attaching a "
   "monitor and obtaining intravenous access are scored as critical actions in addition to the "
   "author's six; and a crystalloid bolus was added as a halting action, which the brief did not "
   "name, because without one the halted phase is unreachable and the case can teach nothing about "
   "an action that must not be taken."),
}
