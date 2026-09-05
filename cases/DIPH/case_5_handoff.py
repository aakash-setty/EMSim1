"""DIPH part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "icu",
   "label": "Intensive care unit",
   "level_of_care": "critical_care",
   "explanation": (
     "She goes to a critical care bed. The author says so in her scenario, and her debriefing "
     "guide lists nine indications for critical-care admission after this poisoning: QRS "
     "widening, dysrhythmia, seizure, persistent delirium, hyperthermia, hypotension, the need "
     "for a bicarbonate infusion, the need for intubation, and significant metabolic or "
     "electrolyte abnormality. This patient meets at least six of them, and every one of them "
     "was present before she left the department.\n\n"
     "What the receiving unit has to be able to do, which is the question actually being asked: "
     "continuous cardiac monitoring with somebody watching it, serial ECGs and serial gases, a "
     "bicarbonate infusion titrated against the QRS, active cooling, management of a recurrent "
     "seizure, and intubation without moving her. Add continuous observation for the "
     "self-harm risk. In most hospitals that is an intensive care bed.\n\n"
     "The trap in this disposition is not choosing the ward. It is treating the improvement in "
     "her agitation as evidence that the poisoning has resolved. Diphenhydramine has a long "
     "duration of action, absorption from a gut slowed by its own antimuscarinic effect "
     "continues for hours, and a QRS that has narrowed on bicarbonate can widen again when the "
     "bicarbonate stops. Clinical improvement in the delirium says nothing about the "
     "conduction.")},

 "alternative_dispositions": [
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care with telemetry",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Defensible in some hospitals and only for the version of this patient who has been "
      "watched for several hours with a normal QRS, a normal temperature and no recurrent "
      "seizure. It is not defensible from the department on the day. The unit has to be able to "
      "run a bicarbonate infusion, repeat tracings, and escalate fast, and a resident who chose "
      "this and can say what the unit must be able to do has answered the question even if the "
      "answer is a level too low. If she was intubated, this is wrong.")},
   {"id": "psychiatric_unit", "label": "Psychiatric inpatient unit",
    "verdict": "incorrect",
    "explanation": (
      "The most instructive wrong answer available in this case, and the reason psychiatry is "
      "tagged discouraged as an early consultation.\n\n"
      "Medical clearance is not a status conferred by recognising that an overdose was "
      "deliberate. It means the medical problem has been treated and the patient can engage. "
      "This patient has a conduction abnormality that has not been normal for long, a "
      "temperature that has been over 40, a seizure a few minutes ago and a delirium she cannot "
      "be assessed through. A psychiatric unit has no cardiac monitor, no capacity to run a "
      "bicarbonate infusion and no way to manage a recurrent seizure.\n\n"
      "She does need psychiatry, urgently, and the way to get it is a monitored medical bed with "
      "psychiatry consulting and continuous observation. The pathway is not blocked by admitting "
      "her medically; it is made possible by it.")},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "incorrect",
    "explanation": (
      "Telemetry watches the rhythm and that is all it does. It will not titrate a bicarbonate "
      "infusion against serial tracings, it does not have the nursing ratio for a patient who is "
      "still delirious and still hot, and it cannot manage a recurrent seizure or an airway "
      "without a transfer. There is a version of this patient for whom a monitored ward bed is "
      "right and it is the version who has been stable for many hours.")},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": (
      "Observation pathways exist for low-risk ingestions with a normal ECG, a normal mental "
      "state and a short expected course. This patient failed the entry criteria at the moment "
      "her QRS came back at 132 milliseconds, and she failed them again when she seized. A "
      "deliberate ingestion of unknown quantity in a depressed adolescent is not an observation "
      "problem either.")},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": (
      "Wrong on two independent grounds, and either one is sufficient. Medically she has "
      "cardiotoxicity from a drug that is still being absorbed and still has hours of duration "
      "left. Psychiatrically she has taken an entire bottle of a medication alone in the house "
      "after months of low mood and social withdrawal, which is a planned act during a period of "
      "isolation. Neither problem has been treated to a point where anything happens at home "
      "except a repeat.")},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": (
      "Nothing this patient needs is unavailable here. This case is written for a hospital with "
      "toxicology, critical care and psychiatry on site. In a hospital without an intensive care "
      "bed or without paediatric or adolescent psychiatric provision, transfer would be a "
      "reasonable answer to a different question, and the thing to be able to say is which "
      "capability is missing.")}],

 "disposition_display_order": ["discharge_home", "observation_unit", "psychiatric_unit",
                               "medical_floor_telemetry", "stepdown_telemetry", "icu",
                               "transfer_tertiary"],
 "disposition_display_order_note": (
   "Ordered from least to most intensive, with the psychiatric unit placed among the low-acuity "
   "options because that is what it is medically, whatever it is administratively."),

 "correct_diagnosis": {
   "catalog_id": "dx_diphenhydramine_overdose",
   "label": "Diphenhydramine overdose",
   "explanation": (
     "The agent, which is what a handover names. Diphenhydramine overdose covers both "
     "halves of this patient, and the second half is the one that decides her management: "
     "an anticholinergic toxidrome with hyperthermia, delirium and rhabdomyolysis, and "
     "cardiac sodium-channel blockade with a QRS of 132 milliseconds and a seizure.\n\n"
     "Naming the agent rather than the syndrome matters here for three practical reasons "
     "and not for tidiness. It tells the receiving team the duration to expect, which for "
     "diphenhydramine is long and is extended further by the antimuscarinic slowing of her "
     "own gut. It tells them what the wide QRS is, which is why she is on a bicarbonate "
     "infusion and why she needs serial tracings rather than one reassuring one. And it "
     "tells them what the positive tricyclic urine screen is, which is a cross-reaction and "
     "not a second drug.\n\n"
     "Until 5 September 2026 this entry did not exist in the diagnosis catalog and the "
     "correct answer had to be recorded as the toxidrome, which is the thing this case "
     "exists to say is not the whole story. It exists now, along with an entry for the "
     "cardiotoxicity itself.")},

 "additional_diagnoses": [
   {"catalog_id": "dx_sodium_channel_blocker_cardiotoxicity",
    "label": "Sodium channel blocker cardiotoxicity",
    "explanation": (
      "The most important thing about this patient and the one to say out loud. Her QRS was "
      "132 milliseconds with a terminal R wave in aVR, which is cardiac sodium-channel "
      "blockade, and it is the reason she is on bicarbonate rather than being watched. A "
      "handover that says antihistamine overdose and stops leaves the receiving team to "
      "discover the conduction abnormality themselves, and the thing about this poisoning "
      "is that the patient looks better long before the channel does.\n\n"
      "The catalog entry is deliberately a mechanism rather than an agent, because that is "
      "how it is handed over and because the same sentence and the same treatment serve "
      "tricyclic, cocaine, bupropion, flecainide and local anaesthetic poisoning.")},
   {"catalog_id": "dx_anticholinergic_toxidrome", "label": "Anticholinergic toxidrome",
    "explanation": (
      "True, and worth naming beside the agent because it is what the nursing staff will be "
      "managing for the next twelve hours: the delirium, the retention, the absent bowel "
      "sounds and the hyperthermia she cannot sweat off. It is also the half of the "
      "diagnosis a resident reaches first, which is why this case scores it as a component "
      "rather than as the answer.")},
   {"catalog_id": "dx_rhabdomyolysis", "label": "Rhabdomyolysis",
    "explanation": (
      "Her creatine kinase is 540 after hours of agitation, a temperature over 40 and a "
      "convulsion, and it is going to keep rising. Naming it is what makes the receiving "
      "team measure the urine output, keep her filled and repeat the creatine kinase and "
      "the creatinine overnight. It is also a reason the sedation and the cooling matter "
      "beyond comfort.")},
   {"catalog_id": "dx_drug_induced_seizure", "label": "Drug-induced seizure",
    "explanation": (
      "She convulsed, and the receiving team needs to know both that it happened and that "
      "it was toxic rather than epileptic, because it changes what they do if it recurs: "
      "benzodiazepines and correction of the acidaemia, the temperature and the "
      "oxygenation, and not phenytoin. A recurrent seizure in this poisoning is also a "
      "cardiac event, because the acidaemia it produces frees more drug to block the "
      "sodium channel.")},
   {"catalog_id": "dx_suicide_attempt", "label": "Suicide attempt",
    "explanation": (
      "This was a deliberate ingestion of an entire bottle, taken alone in the house after "
      "months of low mood and social withdrawal, and the handover has to say so. It is what "
      "determines that she needs continuous observation on the ward rather than a side "
      "room, that psychiatry sees her before any discussion of discharge, and that somebody "
      "asks what else is in the house before she goes home. Leaving it out because the "
      "medical problem is more urgent is the commonest way it gets lost.")}],
 "additional_diagnoses_note": (
   "Five, and the first of them used to be unsayable. Before 5 September 2026 the diagnosis "
   "catalog had no entry for the agent, for sodium-channel blockade or for a drug-induced "
   "seizure, so this list read rhabdomyolysis, status epilepticus (which claims something "
   "about duration that a single toxic convulsion does not) and delirium, with the "
   "cardiotoxicity carried nowhere at all.\n\n"
   "The list was drafted by an AI assistant from the case's own findings and is unsigned. "
   "Delirium came out of it when the toxidrome moved in, because the two were saying the "
   "same thing twice."),

 "alternative_diagnoses": [
   {"catalog_id": "dx_anticholinergic_toxidrome", "label": "Anticholinergic toxidrome",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "This is the case, and it is now possible to score it as what it is: defensible and "
      "incomplete.\n\n"
      "A resident who names the toxidrome has read the patient correctly. The pupils, the "
      "dry hot skin, the absent bowel sounds, the retained urine and the delirium are all "
      "there and they are all antimuscarinic, and every one of them was available at the "
      "bedside in ninety seconds. What it leaves out is the thing that was going to kill "
      "her, which was on a tracing.\n\n"
      "The distinction is not academic and it is not about vocabulary. A patient handed over "
      "as an anticholinergic toxidrome gets watched until the delirium clears. A patient "
      "handed over as a diphenhydramine overdose with sodium-channel blockade gets a "
      "bicarbonate infusion, serial ECGs and a monitored bed, and is not moved to psychiatry "
      "when she wakes up. Same patient, same findings, different night.\n\n"
      "Scored as defensible rather than wrong because the reasoning is sound as far as it "
      "goes, and because a resident who names it and then names the cardiotoxicity beside "
      "it, in either order, has the whole answer.")},
   {"catalog_id": "dx_tricyclic_antidepressant_overdose",
    "label": "Tricyclic antidepressant overdose",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "Marked defensible rather than wrong, and it is worth saying why to a resident who chose "
      "it. The electrocardiographic picture is the same picture, the urine screen came back "
      "positive for tricyclics, and the immediate management is identical: sodium bicarbonate "
      "for the wide QRS, benzodiazepines for the seizure, and no physostigmine. A resident who "
      "named this has got the management right for the right mechanical reason.\n\n"
      "What is wrong with it: the urine immunoassay is cross-reacting with the diphenhydramine "
      "and there is an empty Benadryl bottle at home. It matters for the conversation with "
      "toxicology, for what is watched over the next day, and for what the psychiatric team is "
      "told about access to medication in the house. It does not matter for the next ten "
      "minutes, and that is the more useful half of the lesson.")},
   {"catalog_id": "dx_sympathomimetic_toxicity", "label": "Sympathomimetic toxicity",
    "verdict": "incorrect",
    "explanation": (
      "The closest clinical mimic and the discriminator is the skin. A sympathomimetic patient "
      "is hyperthermic, agitated, tachycardic, mydriatic and wet: the sweat glands are driven "
      "rather than blocked. This patient is bone dry at 40.1 degrees, has absent bowel sounds "
      "and a distended bladder, all of which are antimuscarinic and none of which is "
      "sympathomimetic. If you take one discriminator out of this case, take the skin.")},
   {"catalog_id": "dx_serotonin_syndrome", "label": "Serotonin syndrome",
    "verdict": "incorrect",
    "explanation": (
      "Reasonable to consider in a hyperthermic agitated patient on the differential, and the "
      "examination excludes it. Serotonin syndrome is a neuromuscular diagnosis: clonus, "
      "especially inducible and ocular clonus, hyperreflexia greatest in the lower limbs, and "
      "rigidity. She has none of those, her reflexes are symmetrical and normal and her plantars "
      "are down. It also usually needs a serotonergic drug, and she is on nothing.")},
   {"catalog_id": "dx_neuroleptic_malignant_syndrome", "label": "Neuroleptic malignant syndrome",
    "verdict": "incorrect",
    "explanation": (
      "Wrong on the exposure, the tempo and the examination. She takes no antipsychotic. "
      "Neuroleptic malignant syndrome evolves over days rather than hours. And its defining sign "
      "is lead-pipe rigidity, which she does not have. The raised creatine kinase is common to "
      "both and is the one thing that would point you here.")},
   {"catalog_id": "dx_bacterial_meningitis", "label": "Bacterial meningitis",
    "verdict": "incorrect",
    "explanation": (
      "The right thing to have thought about at time zero, and this case does not penalise "
      "empirical antibiotics for it. It is the wrong final answer. The neck is supple with no "
      "meningism, there is no rash, there is no headache today, and the pupils, the dry skin, "
      "the absent bowel sounds and the palpable bladder together are a toxidrome. And a "
      "meningitis does not widen a QRS.")},
   {"catalog_id": "dx_heat_stroke", "label": "Heat stroke",
    "verdict": "incorrect",
    "explanation": (
      "The temperature and the delirium fit and nothing else does. Classical heat stroke needs an "
      "environmental exposure and exertional heat stroke needs exertion, and she has been indoors "
      "at home all day. Anticholinergic hyperthermia is heat stroke's mechanism arrived at "
      "pharmacologically: heat generated by muscle activity in a patient who cannot sweat. The "
      "cooling you would do for either is the same, and the sodium bicarbonate is not.")},
   {"catalog_id": "dx_thyroid_storm", "label": "Thyroid storm",
    "verdict": "incorrect",
    "explanation": (
      "On the differential for a hyperthermic tachycardic agitated young woman and excluded by "
      "the examination and the TSH. No goitre, no eye signs, no preceding history, and a normal "
      "TSH. It is also the wrong tempo: thyroid storm has a precipitant and a prodrome.")},
   {"catalog_id": "dx_first_time_generalized_seizure", "label": "First seizure",
    "verdict": "incorrect",
    "explanation": (
      "The seizure is a feature of this presentation rather than the diagnosis, and calling it a "
      "first seizure is what leads to a head CT, an EEG request and a neurology referral instead "
      "of sodium bicarbonate. The provocation is in front of you: a toxic ingestion, a "
      "temperature over 40 and a pH of 7.28.")}],

 "diagnosis_entry_method": (
   "The learner searches the whole diagnosis catalog rather than choosing from a list this case "
   "supplies. Since v0.9 they list as many diagnoses as apply, the first being the primary. Wrong "
   "answers outside the authored alternatives receive a generic note, which is acceptable for the "
   "long tail and is a real limitation here, because the single most important thing about this "
   "patient has no id to select."),
 "pending_result_warning": (
   "Results ordered and never read are recorded automatically and surfaced in the debrief. In "
   "this case the study most often ordered and never looked at is the repeat ECG after "
   "bicarbonate, which is the one that tells you whether the treatment worked."),
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

# ==================================================================== debrief
DEBRIEF = {
 "clinical_domains": [
   {"id": "recognition", "label": "Recognising the toxidrome",
    "actions": ["exam_heent", "exam_skin", "exam_abd", "exam_gu", "exam_neuro", "exam_psych",
                "exam_neck", "exam_card", "exam_pulm", "fingerstick_blood_sugar"]},
   {"id": "conduction", "label": "Finding and treating the sodium-channel blockade",
    "actions": ["ecg_12_lead", "na_bicarbonate_bolus", "na_bicarbonate_infusion",
                "stop_na_bicarbonate", "arterial_blood_gas", "venous_blood_gas",
                "calcium_ionized", "potassium_chloride_kcl", "magnesium_sulfate",
                "magnesium_level", "lidocaine_bolus", "hypertonic_saline_25_bolus",
                "intralipid", "procainamide_drip", "amiodarone_bolus_infusion",
                "defibrillate", "synchronized_cardioversion", "place_pads_for_monitoring",
                "norepinephrine_drip"]},
   {"id": "the_antidote_question", "label": "The physostigmine decision",
    "actions": ["physostigmine", "atropine_bolus"]},
   {"id": "seizure_and_agitation", "label": "Seizure, agitation and sedation",
    "actions": ["lorazepam_bolus", "levetiracetam_bolus", "fos_phenytoin", "propofol_infusion",
                "propofol_bolus", "haloperidol", "olanzapine", "ziprasidone", "flumazenil",
                "ketamine_infusion", "fentanyl_bolus", "morphine_bolus"]},
   {"id": "temperature", "label": "Hyperthermia and rhabdomyolysis",
    "actions": ["cooling_measures", "warming_measures", "acetaminophen", "ibuprofen",
                "creatine_kinase_ck", "urinalysis", "insert_foley_catheter",
                "normal_saline_1l_bolus", "lactate"]},
   {"id": "airway", "label": "Airway and ventilation",
    "actions": ["intubate_rapid_sequence", "preoxygenate_for_intubation",
                "position_for_intubation", "etomidate_bolus", "ketamine_bolus",
                "rocuronium_bolus", "succinylcholine_bolus", "midazolam_bolus",
                "nasal_cannula_oxygen", "non_rebreather_mask", "bag_valve_mask", "suction"]},
   {"id": "decontamination", "label": "Decontamination",
    "actions": ["activated_charcoal", "whole_bowel_irrigation_by_ng_tube",
                "place_orogastric_tube", "place_nasogastric_tube"]},
   {"id": "co_ingestion", "label": "Co-ingestion and the wider workup",
    "actions": ["acetaminophen_level", "salicylate_aspirin_level", "ethanol_level_etoh",
                "urine_tox_screen", "urine_hcg_qualitative", "serum_hcg_quantitative",
                "basic_chemistry_chem_7", "complete_blood_count_cbc",
                "liver_function_tests_lfts", "coagulation_panel", "troponin_t", "tsh",
                "xr_chest", "ct_head", "ultrasound_cardiac"]},
   {"id": "the_other_road", "label": "The infectious differential",
    "actions": ["ceftriaxone", "acyclovir", "lumbar_puncture", "blood_culture_x_2",
                "place_patient_on_isolation_precautions"]},
   {"id": "consults_and_disposition", "label": "Consultation and disposition",
    "actions": ["consult_toxicology", "consult_critical_care", "consult_psychiatry",
                "consult_neurology", "consult_cardiology", "consult_renal", "handoff_submit"]},
 ],

 "key_exams": ["exam_skin", "exam_heent", "exam_abd", "exam_neuro", "exam_psych", "exam_neck"],
 "key_exams_note": (
   "Section 13.0. Every exam in this case is tagged neutral, so without this list the Physical "
   "score would count all thirteen authored maneuvers equally and a resident who examined the "
   "six that make the diagnosis would score under fifty percent. These six are the ones that "
   "distinguish an anticholinergic toxidrome from its mimics: the dry skin, the pupils and dry "
   "mucosa, the silent abdomen and full bladder, the absence of clonus and focal signs, the "
   "delirium, and the supple neck. Author judgement, unreviewed."),

 "intended_path": ["presentation", "stabilizing", "stabilized", "case_complete"],
 "intended_path_note": (
   "Changed on 5 September 2026, and the change is the largest single departure from the "
   "source in this pack.\n\n"
   "It used to read presentation, seizing, post-ictal, stabilising, stabilised: the intended "
   "path went through the convulsion, because the case author writes that a seizure occurs "
   "regardless of how well the examinee is doing, so there was no path that avoided it and a "
   "resident who reached the post-ictal phase had not failed at anything. The arrival phase "
   "now carries an arrow that takes a patient who has received sodium bicarbonate straight to "
   "the narrowing phase, so the best run no longer convulses and the intended path is the one "
   "that does not.\n\n"
   "Two consequences for reading a debrief. A resident who seized has not necessarily done "
   "anything wrong, because the escape needs the ECG ordered, resulted, read and acted on "
   "inside about 230 seconds, and most runs will not manage it. And the seizure teaching, "
   "which is a third of the clinical content of this case, is no longer on the intended path "
   "at all, so a strong resident may never meet it."),

 "trap_actions": ["physostigmine", "fos_phenytoin", "haloperidol", "olanzapine", "ziprasidone",
                  "acetaminophen", "ibuprofen", "flumazenil", "diphenhydramine",
                  "procainamide_drip", "amiodarone_bolus_infusion", "naloxone_bolus",
                  "lumbar_puncture", "defibrillate", "succinylcholine_bolus", "d50_bolus"],
 "trap_actions_note": (
   "Sixteen, which is more than any other pack, and that is what a toxicology case is: the "
   "differential is a list of drugs and most of the wrong answers are things you give rather "
   "than things you fail to give. Four of them halt the case and the rest cost a point and a "
   "note. The three that matter most are physostigmine, which is the case's central question; "
   "phenytoin, because it is the reflex for a seizure and it is the wrong reflex here; and the "
   "antipsychotics, because the agitation is the loudest thing in the room and haloperidol is "
   "what an agitated patient usually gets."),

 "cross_cutting_teaching_points": [
   ("Treat the ECG, not the ingestion history. A wide QRS after any exposure is an indication "
    "for sodium bicarbonate, and you do not need to know what was taken to give it. Waiting to "
    "find out is what the arrest branch of this case is made of."),
   ("The satisfying diagnosis arrives before the dangerous one. The toxidrome is visible on "
    "examination in ninety seconds. The conduction abnormality is on a tracing nobody has "
    "ordered. Any case where the easy answer is also the incomplete one rewards asking what "
    "else is true."),
   ("Anticholinergic hyperthermia is not a fever, so antipyretics do nothing. The set point is "
    "normal. The heat comes from muscle activity and stays because the sweat glands are "
    "blocked, which is why the treatment is sedation, cooling and, if necessary, paralysis."),
   ("Hot and dry versus hot and wet is the single most useful discriminator on the "
    "hyperthermic-agitated differential, and it takes one second to check."),
   ("Acidaemia and sodium-channel blockade feed each other. A seizure produces acid, acid frees "
    "more drug to block the channel, and a wider QRS makes the next seizure more likely. "
    "Terminating the seizure and ventilating the patient are cardiac interventions here."),
   ("QRS widening and QT prolongation are different electrophysiological problems, they coexist "
    "in this poisoning, and they have different treatments. Bicarbonate for the QRS, magnesium "
    "for torsades. One does not cover the other."),
   ("A qualitative urine drug screen reports exposure, not causation, and it has known "
    "cross-reactants. Hers says tricyclic and she has not taken one. It did not change the "
    "right management, which is the most useful thing about it."),
   ("Medical clearance is not a form and it is not conferred by recognising that an overdose was "
    "deliberate. A patient with an unresolved wide QRS is not medically cleared, whatever the "
    "psychiatric need."),
   ("Response-guided treatment means reassessing after each dose rather than deciding in advance "
    "how many doses there will be. One amp of bicarbonate is a gesture."),
   ("Call toxicology before you need the rescue rather than after. The rescue therapies for "
    "refractory cardiotoxicity rest on case reports and extrapolation, and the time to find out "
    "what is available at your hospital is not during the arrest."),
 ],
 "attempt_history_note": (
   "Blocked attempts are surfaced and not penalised. The block a resident is most likely to meet "
   "in this case is an intravenous drug attempted before a line is in, which is the catalog "
   "prerequisite rather than anything this case authors, and it is the right lesson at the right "
   "moment."),
}

# ==================================================================== provenance
PROVENANCE = {
 "status": ("CONVERTED FROM AN AUTHORED SIMULATION CASE. Not reviewed by a physician in this "
            "form. Not for use with learners."),
 "author": ("Kelly Medwid, MD, wrote the source simulation case and its debriefing guide. "
            "Converted for this platform with her permission, at the request of Aakash Setty, "
            "on 5 September 2026."),
 "warning": (
   "The physician author supplied: the patient, the history and the psychosocial background, the "
   "arrival, the presenting vital signs, the whole of the physical examination, every laboratory "
   "value, the timing spine including the four-minute seizure, the physostigmine trap and its "
   "ordering constraint, the phenytoin warning, the bottle-disclosure mechanic, the nurse's "
   "prompting lines, the disposition, the learning objectives, and the whole of the management "
   "content in the debriefing guide.\n\n"
   "A language model expanded that into this case pack. Everything not in the list above is "
   "model output and awaits primary sign-off: the phase structure and every phase's vital signs "
   "other than the presenting set, every deadline other than the 240-second seizure, every "
   "reference interval, every ECG measurement, the wording of every prompt, narration, debrief "
   "note and interview answer, every paraphrase variant, the additional and alternative "
   "diagnosis lists, the routing of the examination findings, and the tag on every action the "
   "source does not name. Nothing here has been reviewed by a physician."),
 "author_only_fields_pending_signoff": [
   "The physostigmine tag rule list. The author's instruction was that physostigmine is harmful "
   "and leads back to a seizure requiring bicarbonate. The engine's harmful tag halts the case "
   "and cannot lead anywhere, so the instruction is split: harmful before the ECG has resulted, "
   "discouraged with a seizure ten seconds later once it has. This is the most consequential "
   "unsigned decision in the pack. See DIPH-SEED.md section 9.1.",
   "The terminal R wave in aVR, authored present at 5 mm. The author's narrative says the "
   "examinee should recognise 'the lack of' a significant R wave in aVR; her own teaching text "
   "and her debriefing guide both say the terminal R wave is the finding. See DIPH-SEED.md "
   "section 9.2.",
   "The chemistry panel's bicarbonate, authored at 13 rather than the source's CO2 of 34, on the "
   "grounds that 34 gives an anion gap of negative 8. See DIPH-SEED.md section 9.4.",
   "Every reference interval in content_keys.labs. Not one appears in the source document.",
   "Every ECG measurement. The source gives no QRS duration, no QTc and no R wave amplitude.",
   "The magnesium of 1.6, which is invented to make a teaching point about torsades and does not "
   "appear in the source at all.",
   "The three deterioration deadlines: 120 seconds of untreated seizure to a wide-complex "
   "rhythm, 180 seconds of untreated sodium-channel blockade from the post-ictal phase, and 120 "
   "seconds of untreated stable ventricular tachycardia to arrest. The last of these is the "
   "number that decides whether the case can kill the patient.",
   "The tag on phenytoin, authored discouraged where the author wrote 'avoided'. See its debrief "
   "note.",
   "The tag on empirical antibiotics and acyclovir, which are recommended on arrival and "
   "discouraged after the toxicology screen resulted. The author endorses a sepsis bundle at "
   "time zero and her debriefing guide never mentions sepsis; the switch point is a drafting "
   "judgement.",
   "The additional and alternative diagnosis lists, drafted from the case's own findings.",
   "The interview, in full. The mother is the historian on the author's instruction, and every "
   "word she says is model output.",
 ],
 "source_fidelity_note": (
   "The source document contradicts itself in seven places. Four are resolved on the author's "
   "instruction and three are drafting assumptions. All seven, with what was done about each, "
   "are in DIPH-SEED.md section 9. Read that section before reading anything else in this pack."),
 "unused_source_material": (
   "The four images in the source document, the mannequin and supply lists, the confederate "
   "staffing notes, and the Teaching Points essay as prose. The engine cannot display an image "
   "in a result, and the provenance of the two ECG tracings, the chest radiograph and the head "
   "CT is not established in the document, which cites an ACEP toxicology case file and "
   "thepoisonreview.com in its reference list. No text from the source is reproduced verbatim in "
   "this case file."),
 "catalog_change_requests": [
   "physostigmine was added to the action catalog for this case, under Meds - Tox, marked "
   "source=author-supplied. Before this case the catalog held every other toxicology antidote a "
   "resident might reach for and not this one.",
   "RESOLVED 5 September 2026. Three toxicology entries were added to the diagnosis "
   "catalog on author instruction: dx_diphenhydramine_overdose, "
   "dx_sodium_channel_blocker_cardiotoxicity and dx_drug_induced_seizure, each marked "
   "source=author-supplied. Before they existed the correct answer to this case had to be "
   "recorded as the anticholinergic toxidrome, which is the thing the case exists to say is "
   "not the whole story, and a resident who named the toxidrome and stopped could not be "
   "told apart from one who understood it. The toxidrome is now an additional diagnosis and "
   "a defensible-but-incomplete alternative, which is what it is.",
   "The action catalog has no gastric lavage, which the author's teaching text discusses.",
   "The action catalog has no core or rectal temperature measurement. Temperature appears on the "
   "monitor once one is attached and cannot be ordered as an act, so 'check a rectal temperature "
   "in a significantly agitated patient' cannot be taught mechanically.",
   "The catalog's default vascular-access failure message reads 'He doesn't have a line yet', "
   "which is wrong for this patient and for MGCA's. A gendered default in a shared catalog is a "
   "small defect with no case-level fix.",
 ],
}
