"""TSS part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "icu",
   "label": "Intensive care unit",
   "level_of_care": "critical_care",
   "explanation": (
     "She goes to intensive care. She is on a vasopressor, her lactate is raised, and her "
     "kidneys, liver, platelets and muscle are all injured. The toxin already absorbed keeps "
     "acting for many hours after the tampon is out, so she can keep getting worse over the "
     "next day.\n\n"
     "What the receiving team needs to hear: the source and that it has been removed, how "
     "much fluid she has had, the vasopressor dose and whether it is still rising, which "
     "antibiotics went in and when, and the last lactate.")},

 # v0.21. Read by the engine's handoffIntercept. Choosing discharge while she still looks
 # well does not end the case. The interface logs the hidden action attempt_discharge
 # instead, she faints, and the learner has a patient to recover. A second attempt, or a
 # discharge from any later phase, is an ordinary handoff and ends the case.
 "disposition_intercepts": [
   {"disposition": "discharge_home",
    "when": "(phase is presentation OR phase is fluid_responsive) AND NOT flag discharge_attempted set",
    "action": "attempt_discharge",
    "author_note": ("Decided by Aakash Setty on 6 October 2026: she faints and the case "
                    "continues.")}],

 "alternative_dispositions": [
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care with telemetry",
    "verdict": "incorrect",
    "explanation": (
      "A step-down unit can watch her and cannot run this resuscitation. She needs a "
      "titrated vasopressor, an arterial line and one nurse who is not looking after three "
      "other patients. A patient on norepinephrine with four injured organ systems is an "
      "intensive care patient.")},
   {"id": "medical_floor_telemetry", "label": "General medical ward with telemetry",
    "verdict": "incorrect",
    "explanation": (
      "Telemetry watches a rhythm. Her problem is her blood pressure and her organs, and "
      "the ward cannot titrate a vasopressor or repeat a lactate every hour.")},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": (
      "Observation is for patients expected to go home within a day. A lactate of 4.6 and "
      "a creatinine of 2.6 took her out of that group before any treatment started.")},
   {"id": "discharge_home", "label": "Discharge home",
    "verdict": "incorrect",
    "explanation": (
      "She is in shock. The story of the flu and a sunburn fits her symptoms and does not fit her "
      "vital signs, her skin or her laboratory results. Sending her home is the error this "
      "case exists to prevent.")},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": (
      "Everything she needs is in this hospital. In a hospital with no intensive care, "
      "transfer after the source is out and a vasopressor is running would be right.")}],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "icu", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_toxic_shock_syndrome",
   "label": "Toxic shock syndrome",
   "explanation": (
     "Fever, a diffuse red rash that blanches, hypotension, and injury to several organ "
     "systems at once, in a menstruating woman with a retained tampon. That is menstrual "
     "staphylococcal toxic shock syndrome.\n\n"
     "The diagnosis is clinical. It is made from the pattern and the source, and it does "
     "not wait for a culture. Blood cultures usually stay negative. The skin of her palms "
     "and soles is expected to peel one to two weeks from now, which confirms it too late "
     "to be useful.\n\n"
     "Naming it matters at handover because it tells the next team three things: the source "
     "is out, clindamycin belongs in the regimen, and this can recur with tampon use.")},

 "additional_diagnoses": [
   {"catalog_id": "dx_septic_shock", "label": "Septic shock",
    "explanation": (
      "She needed a vasopressor to hold a mean pressure of 65 after fluid, with a raised "
      "lactate. Saying so tells the receiving team how sick she is in the terms they use.")},
   {"catalog_id": "dx_acute_kidney_injury", "label": "Acute kidney injury",
    "explanation": (
      "A creatinine of 2.6 at age 22 with almost no urine. It changes how every later drug "
      "is dosed, vancomycin first among them. The ibuprofen she took at home may have "
      "added to it, and she should get no more.")},
   {"catalog_id": "dx_lactic_acidosis", "label": "Lactic acidosis",
    "explanation": (
      "A lactate of 4.6 on arrival with a bicarbonate of 17. The repeat value is how the "
      "next team will judge whether the resuscitation is working.")},
   {"catalog_id": "dx_rhabdomyolysis", "label": "Rhabdomyolysis",
    "explanation": (
      "Her creatine kinase is 2,140 with muscle pain and tenderness. Muscle involvement is "
      "part of toxic shock, and with an injured kidney it needs watching.")},
   # v0.24 audit, finding 22 and catalog finding 4.1. The five below were added on
   # 7 October 2026. Two of them are diagnosis entries this pack asked the catalog for. The
   # other three were true of her chemistry and cost five points each to name. Each
   # explanation only restates values the pack already authors. A model wrote them and a
   # physician has not read them.
   {"catalog_id": "dx_retained_vaginal_foreign_body", "label": "Retained vaginal foreign body",
    "explanation": (
      "The retained tampon found on the pelvic examination. It is the source, and the "
      "next team needs to hear whether it is out.")},
   {"catalog_id": "dx_thrombocytopenia", "label": "Thrombocytopenia",
    "explanation": (
      "Her platelet count is 98, against a lower limit of 150. It is one of the organ "
      "systems involved.")},
   {"catalog_id": "dx_anion_gap_metabolic_acidosis", "label": "Anion gap metabolic acidosis",
    "explanation": (
      "Sodium 131, chloride 97 and bicarbonate 17 give an anion gap of 17, with a lactate "
      "of 4.6 on arrival.")},
   {"catalog_id": "dx_hyponatremia", "label": "Hyponatremia",
    "explanation": "Her sodium is 131, against a lower limit of 135."},
   {"catalog_id": "dx_hypokalemia", "label": "Hypokalemia",
    "explanation": "Her potassium is 3.3, against a lower limit of 3.5."}],

 "alternative_diagnoses": [
   {"catalog_id": "dx_septic_shock", "label": "Septic shock",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "True, and the resuscitation is the same. As the primary diagnosis it leaves out the "
      "cause. Septic shock is what is happening to her circulation. Toxic shock syndrome "
      "says why, and the why is what sends someone to look for a tampon and add "
      "clindamycin.")},
   {"catalog_id": "dx_sepsis", "label": "Sepsis",
    "verdict": "incorrect",
    "explanation": (
      "It understates her. She was hypotensive after fluid and needed a vasopressor, which "
      "is shock. It also names no source.")},
   {"catalog_id": "dx_viral_gastroenteritis", "label": "Viral gastroenteritis",
    "verdict": "incorrect",
    "explanation": (
      "She has no vomiting and no diarrhea, so this does not fit even her symptoms. It does "
      "not explain a temperature of 39.4 with a red rash, a creatinine of 2.6, platelets of "
      "98 or a lactate of 4.6. When a common diagnosis does not explain the vital signs, "
      "keep looking.")},
   {"catalog_id": "dx_infectious_gastroenteritis", "label": "Infectious gastroenteritis",
    "verdict": "incorrect",
    "explanation": (
      "She has no gut symptoms, and a gut infection does not cause a diffuse rash, liver "
      "injury and low platelets.")},
   {"catalog_id": "dx_hypovolemia", "label": "Hypovolemia",
    "verdict": "incorrect",
    "explanation": (
      "She is dry, and that is part of the picture. A patient who is only dry stays better "
      "after two liters. She did not.")},
   {"catalog_id": "dx_meningococcemia", "label": "Meningococcemia",
    "verdict": "incorrect",
    "explanation": (
      "The right thing to fear in a young adult with fever, a rash and shock, and covering "
      "it with ceftriaxone early is reasonable. The rash favors toxic shock. Hers is a "
      "diffuse redness that blanches, where meningococcal disease usually gives petechiae "
      "and purpura that do not. What settles it is that she has a source.")},
   {"catalog_id": "dx_urosepsis", "label": "Urosepsis",
    "verdict": "incorrect",
    "explanation": (
      "Her urine has white cells in it, which is the trap. There are no bacteria and no "
      "nitrite, she has no flank tenderness and no burning. White cells without infection "
      "in the urine are a recognized finding in toxic shock.")},
   {"catalog_id": "dx_pyelonephritis", "label": "Pyelonephritis",
    "verdict": "incorrect",
    "explanation": (
      "White cells in the urine without bacteria, nitrite, flank tenderness or urinary "
      "symptoms are not a kidney infection. They are part of toxic shock.")},
   {"catalog_id": "dx_scarlet_fever", "label": "Scarlet fever",
    "verdict": "incorrect",
    "explanation": (
      "A red rash, a red tongue and a sore throat make this a fair thought. Scarlet fever "
      "does not cause shock with kidney, liver and platelet injury. When a streptococcal "
      "illness does, it is streptococcal toxic shock, which usually comes from a painful "
      "soft tissue infection that she does not have.")},
   {"catalog_id": "dx_heat_stroke", "label": "Heat stroke",
    "verdict": "incorrect",
    "explanation": (
      "She sat on a beach for an hour a day and a half after her fever started. The fever came first, "
      "her mind is clear, and heat stroke does not come with a retained tampon.")},
   {"catalog_id": "dx_heat_exhaustion", "label": "Heat exhaustion",
    "verdict": "incorrect",
    "explanation": (
      "The beach is her explanation for the rash, and it does not hold. She was febrile and "
      "aching a day and a half before she went.")},
   {"catalog_id": "dx_pelvic_inflammatory_disease", "label": "Pelvic inflammatory disease",
    "verdict": "incorrect",
    "explanation": (
      "The pelvis is the right place to look and this is the wrong finding. She has no "
      "cervical motion tenderness and no pelvic pain. What the examination shows is a "
      "retained tampon.")},
   {"catalog_id": "dx_stevens_johnson_syndrome", "label": "Stevens-Johnson syndrome",
    "verdict": "incorrect",
    "explanation": (
      "Her skin is red and intact. There are no blisters, no target lesions and no mouth "
      "ulcers, and she has taken no new drug apart from ibuprofen yesterday.")},
   {"catalog_id": "dx_kawasaki_disease", "label": "Kawasaki disease",
    "verdict": "incorrect",
    "explanation": (
      "The red eyes, red tongue and rash overlap. Kawasaki disease is an illness of young "
      "children with five days of fever, and it does not present with shock and a retained "
      "tampon in an adult.")},
   {"catalog_id": "dx_rocky_mountain_spotted_fever", "label": "Rocky Mountain spotted fever",
    "verdict": "incorrect",
    "explanation": (
      "Fever, rash and low platelets fit. The rash of spotted fever is spotted and starts at "
      "the wrists and ankles. She recalls no tick exposure, which does not exclude it. The "
      "retained tampon is what makes toxic shock the better answer.")}],

 "diagnosis_entry_method": (
   "The learner searches the whole diagnosis catalog and lists as many diagnoses as apply, "
   "the first being the primary."),
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

# ==================================================================== debrief
DEBRIEF = {
 "clinical_domains": [
   {"id": "recognition", "label": "Recognizing shock in a patient who looks well",
    "actions": ["attach_monitor", "exam_circ", "exam_skin", "exam_heent", "exam_neuro",
                "lactate", "basic_chemistry_chem_7", "complete_blood_count_cbc",
                "venous_blood_gas", "arterial_blood_gas", "ecg_12_lead",
                "liver_function_tests_lfts", "creatine_kinase_ck", "coagulation_panel",
                "plasma_procalcitonin", "c_reactive_protein_crp", "peripheral_smear",
                "urine_hcg_qualitative", "serum_hcg_quantitative"]},
   {"id": "source", "label": "Finding and removing the source",
    "actions": ["exam_gu", "remove_vaginal_foreign_body", "ct_abdomen", "ultrasound_fast",
                "exam_abd", "exam_back", "urinalysis", "consult_ob_gyn"]},
   {"id": "resuscitation", "label": "Fluid and vasopressor",
    "actions": ["insert_iv", "second_iv", "normal_saline_1l_bolus", "norepinephrine_drip",
                "normal_saline_infusion", "dopamine_drip", "phenylephrine_bolus",
                "stop_norepinephrine", "insert_foley_catheter", "ultrasound_cardiac",
                "hydrocortisone_bolus", "nasal_cannula_oxygen", "non_rebreather_mask"]},
   {"id": "antimicrobials", "label": "Antibiotics",
    "actions": ["vancomycin", "clindamycin", "ceftriaxone", "cefazolin",
                "blood_culture_x_2", "intravenous_immunoglobulin",
                "consult_infectious_disease"]},
   {"id": "traps", "label": "Things that look reasonable and are not",
    "actions": ["attempt_discharge", "metoprolol_bolus", "ibuprofen", "furosemide_40_mg_iv",
                "lumbar_puncture", "intubate_rapid_sequence", "ondansetron", "acetaminophen"]},
   {"id": "disposition", "label": "Consultation and disposition",
    "actions": ["consult_critical_care", "consult_renal", "handoff_submit"]},
 ],

 "key_exams": ["exam_circ", "exam_skin", "exam_gu", "exam_heent", "exam_neck", "exam_abd"],
 "key_exams_note": (
   "Section 10.4. Every exam is tagged neutral, so the Physical score reads this list. These "
   "six are the ones that separate toxic shock from its mimics: perfusion, the rash, the "
   "pelvis, the mucous membranes, the neck and the abdomen. Model judgment, unreviewed."),

 "intended_path": ["presentation", "fluid_responsive", "hypotensive", "stabilizing",
                   "case_complete"],
 "intended_path_note": (
   "The intended path goes through the hypotensive phase. That is deliberate and it is the "
   "directing physician's decision: norepinephrine is the expected move once the mean "
   "pressure stays under 65 after about 30 mL/kg, so a learner who does everything right "
   "still watches the fluid response fade. A learner who starts a vasopressor during the "
   "fluid-responsive phase skips the hypotensive phase, which the case accepts."),

 "trap_actions": ["ondansetron", "acetaminophen", "ct_abdomen"],
 "trap_actions_note": (
   "Neutral actions that are worth a note when taken. The discouraged traps (discharge, "
   "rate control, ibuprofen, a diuretic, a lumbar puncture, early intubation) are surfaced "
   "by their tag and need no entry here."),

 "cross_cutting_teaching_points": [
   ("Read the vital signs as if you had not heard the story. A common diagnosis that "
    "explains the symptoms and not the heart rate, the fever or the skin is not yet the "
    "diagnosis."),
   ("Shock with no source means you have not finished looking. Ask about menstruation and "
    "tampons, and examine the pelvis, the skin, wounds and anything packed or implanted. "
    "Removing the source is treatment, and nothing given through a vein replaces it."),
   ("Clindamycin belongs beside vancomycin in suspected toxic shock. It reduces toxin "
    "production, which a cell-wall antibiotic does not. This case does not score it, and you "
    "will not see its effect in the department. The evidence is laboratory and observational."),
   ("A young patient holds a blood pressure until she cannot. Tachycardia, slow capillary "
    "refill and a raised lactate are shock, whatever the pressure reads."),
   ("A fluid response that fades is information. A mean pressure under 65 that persists "
    "after fluid is an indication for norepinephrine, and a good peripheral line is enough "
    "to start it."),
   ("Toxic shock syndrome is a clinical diagnosis: fever, a diffuse blanching red rash, "
    "hypotension, and three or more organ systems involved. Blood cultures are usually "
    "negative in the staphylococcal form."),
   ("White cells in the urine without bacteria are not a urinary infection. In this illness "
    "they are part of the syndrome, and treating them as the source ends the search early."),
   ("A fast heart rate that is holding up a blood pressure is not treated. Find the cause."),
 ],
 "attempt_history_note": (
   "Blocked attempts are surfaced and not penalized. This case authors two. Removing a "
   "vaginal foreign body before the pelvic examination, where the nurse says nobody has "
   "looked yet. And stopping a vasopressor when none is running."),
}

# ==================================================================== provenance
PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 6 October 2026, from a "
            "one-paragraph case plan written in the same conversation. Authoring "
            "requirements section 1 applies: the AUTHOR-ONLY fields were generated, and a "
            "physician is authoring the ground truth in review."),
 "warning": (
   "A physician decided four things, listed in TSS-SEED.md section 0: which antibiotic "
   "orders count, what happens on an attempted discharge, how she responds to source "
   "removal, and when norepinephrine is expected. The same physician approved the plan's "
   "patient, story and three learning goals in outline.\n\n"
   "Everything else is model output and awaits sign-off: every vital sign, every "
   "examination finding, every laboratory value and reference interval, every deadline, "
   "every tag, every debrief note, the whole interview, and the diagnosis lists. The "
   "drafting pass wrote them from general knowledge of toxic shock syndrome and sepsis care "
   "and opened no guideline, paper or published simulation while doing so. A second model "
   "pass on the same day did open sources and compared the pack against them. "
   "reference_status below lists each one and how it was read. Neither pass was a "
   "physician's review.\n\n"
   "On 7 October 2026 a model changed the pack to meet the v0.24 authoring rules after an "
   "audit. It added no clinical number except values derived from numbers already in the "
   "pack, each marked in a verify note. The new debrief notes, consultant lines and patient "
   "answers restate what the pack already said, and TSS-SEED.md lists each one as awaiting "
   "sign-off."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase.",
   "Every laboratory value, reference interval and abnormal flag.",
   "Every examination finding and its routing.",
   "The five clocks: 300 seconds without fluid, 150 seconds of fluid response, 240 seconds "
   "hypotensive without fluid and a vasopressor, 270 seconds on a vasopressor with the "
   "source in, and the 5-second faint after an attempted discharge.",
   "That removing the tampon stops the decline within ten seconds. The directing physician "
   "chose the direction. The speed is unsourced.",
   "That she always faints on an attempted discharge.",
   "The tags: vancomycin critical, clindamycin neutral, broad beta-lactams neutral, rate "
   "control and ibuprofen and a diuretic and a lumbar puncture discouraged, intubation "
   "discouraged until she is obtunded.",
   "That nothing in this case is harmful and nothing ends it except a handoff.",
   "The antibiotic regimen named in the debrief notes, and the statements about the "
   "evidence for clindamycin, immunoglobulin, 30 mL/kg, peripheral vasopressors and dopamine.",
   "The interview in full, and the alternative and additional diagnosis lists.",
   # ---- added 7 October 2026 after the audit (authoring section 2, row by row)
   "Consultant advice: every reply of the intensivist, infectious disease, gynecology and "
   "nephrology. The intensivist's tiers were rewritten and the nephrology reply was written "
   "by a model on 7 October 2026.",
   "Prompt deadlines and their relative urgency: monitor 20 seconds, vasopressor 30, line "
   "45, fluid 60, source 60, vancomycin 110, and the escalations at 120 (vasopressor), 170 "
   "(fluid) and 180 (source). Fluid and source were moved to 60 on 7 October 2026 to meet "
   "the default-mode rule.",
   "The two follow-ups, their deadlines and whether they apply: a second liter 60 seconds "
   "after a bolus unless a vasopressor is running, and sedation 90 seconds after "
   "intubation.",
   "The two case prerequisites: a pelvic examination before removal, and a running "
   "vasopressor before a stop.",
   "Every coverage row in the binding map: the crystalloid bolus group, the three "
   "vasopressor infusions under norepinephrine, the five stop entries, the maintenance "
   "infusions, the five broad beta-lactams, the eight rate-control routes and the loop "
   "diuretic group.",
   "The size and duration of every vital effect: fluid plus 6 systolic and minus 6 heart "
   "rate for 60 seconds, a vasopressor without fluid plus 8, a phenylephrine push plus 12 "
   "for 90 seconds, rate control minus 16 heart rate and minus 12 systolic for 180 "
   "seconds, oxygen plus 2 by cannula and plus 4 by mask, bag or non-invasive ventilation, "
   "and acetaminophen minus 0.6 degrees after 30 seconds.",
   "key_topics (nine interview topics) and key_exams (six examinations), which decide the "
   "History and Physical scores.",
   "The neutral tags given on 7 October 2026 to thirteen studies, the nephrology consult, "
   "the maintenance infusions, the bag valve mask, non-invasive ventilation, lorazepam and "
   "morphine. Each is a placeholder.",
   "The five additional diagnoses added on 7 October 2026 and their explanations.",
   "Results and findings derived by a model on 7 October 2026: the FAST report, the skin "
   "biopsy line, the arterial saturation by phase, and the psychiatric finding in the two "
   "vasopressor phases.",
   "Patient answers a model wrote or edited on 7 October 2026. TSS-SEED.md lists them.",
 ],
 "reference_status": [
   {"reference": "CDC 2011 toxic shock syndrome case definition",
    "how_read": "Opened by a model on 6 October 2026, in the independent check after "
                "drafting. The drafting pass opened nothing and wrote from memory",
    "status": "Compared with the pack by that model. Not checked by a physician"},
   {"reference": "Surviving Sepsis Campaign 2021 guideline text",
    "how_read": "Opened by a model on 6 October 2026, in the independent check",
    "status": "Compared with the pack by that model. A newer edition exists and was not "
              "opened. Not checked by a physician"},
   {"reference": "SCCM guideline page",
    "how_read": "Opened by a model on 6 October 2026, in the independent check",
    "status": "Compared with the pack by that model. Not checked by a physician"},
   {"reference": "StatPearls",
    "how_read": "Opened by a model on 6 October 2026, in the independent check",
    "status": "A secondary source. The SEED does not record which article. Not checked by "
              "a physician"},
   {"reference": "Internet Book of Critical Care",
    "how_read": "Opened by a model on 6 October 2026, in the independent check",
    "status": "A secondary source. The SEED does not record which chapter. Not checked by "
              "a physician"},
   {"reference": "De Backer et al., NEJM 2010, the SOAP II trial",
    "how_read": "Not opened. The dopamine note was written from memory",
    "status": "Unverified. The note carries a marker. Not checked by a physician"},
   {"reference": "Current IDSA and local guidance on the empiric regimen",
    "how_read": "Not opened. The vancomycin and clindamycin notes were written from memory",
    "status": "Unverified. The notes carry markers. Not checked by a physician"},
   {"reference": "No source",
    "how_read": "From memory",
    "status": "Four claims have no source at all: that most menstrual toxic shock is "
              "methicillin-susceptible, lactate over 4 as a risk marker, the CT appearance "
              "of a tampon, and sterile pyuria in toxic shock. Each sits in a debrief note "
              "that carries a marker. The pyuria claim is also in the urosepsis and "
              "pyelonephritis explanations, which cannot carry a marker because the "
              "interface prints it there. Not checked by a physician"},
 ],
 "reference_status_summary": (
   "TSS-SEED.md section 4 lists what the independent check confirmed against the opened "
   "sources. It does not record which source confirmed which claim."),
 "reference_status_note": (
   "Markers are [UNVERIFIED] text in square brackets. The interface strips them from an "
   "action's debrief note, a timed transition's debrief note, references and the "
   "cross-cutting teaching points, and prints them everywhere else, so they sit only in "
   "those fields and in verify notes."),
 "catalog_change_requests": [
   "RESOLVED 6 October 2026. 'Remove Vaginal Foreign Body' was added to the action catalog "
   "under Procedures, marked source=author-supplied. Before it existed a retained tampon "
   "could be found on the genitourinary examination and then not acted on.",
   "RESOLVED 7 October 2026. The diagnosis catalog gained Thrombocytopenia and Retained "
   "vaginal foreign body, and this case now credits both as additional diagnoses.",
   "Linezolid is not in the action catalog. The vancomycin note names it as an alternative "
   "some centers prefer.",
   "The diagnosis catalog has no entry for acute liver injury or transaminitis short of "
   "acute liver failure, so her liver involvement cannot be named at handover.",
 ],
}
