#!/usr/bin/env python3
"""
Default (normal) result payloads for every catalog investigation that returns
printed output. Imported by build_catalog.py.

RESOLUTION ORDER (the point of this file):
    case study_results[<id>] for the current phase   ->   used
    otherwise                                        ->   default_result here
A case therefore only authors the studies that matter to it.

DISPLAY: every component here is in range, so nothing renders red. Components
carry "abnormal": false explicitly rather than relying on the renderer to
recompute in-range, so a case that overrides a value must set the flag itself.

PROVENANCE WARNING: these reference ranges and the normal values inside them
were drafted by the AI from general knowledge, not from a laboratory reference
or a cited source. They are conventional US adult ranges and are plausible, but
they are NOT verified. Ranges are assay-, instrument-, and institution-specific.
Entries with "verify" set are ones where the range is known to vary in ways that
change interpretation. A physician must review the whole file before release.
"""

def panel(*rows, **kw):
    return dict(kind="panel", abnormal=False,
                components=[{"label": r[0], "value": r[1], "unit": r[2],
                             "reference_range": r[3], "abnormal": False} for r in rows],
                **kw)

def value(label, val, unit, ref, **kw):
    return dict(kind="value", abnormal=False,
                components=[{"label": label, "value": val, "unit": unit,
                             "reference_range": ref, "abnormal": False}], **kw)

def report(text, **kw):
    return dict(kind="report", abnormal=False, report=text, **kw)

DEFAULTS = {

# ------------------------------------------------------------------ bedside
"doppler": report("Biphasic to triphasic arterial signals in the vessel examined. "
                  "Venous signals present and phasic."),
"ecg_12_lead": report("Normal sinus rhythm at 72. Normal axis. PR 160 ms, QRS 90 ms, "
                      "QTc 420 ms. No ST elevation or depression. No T wave inversion. "
                      "No Q waves."),
"fingerstick_blood_sugar": value("Capillary glucose", "94", "mg/dL", "70-140 (random)"),
"peak_expiratory_flow_meter": value("Peak expiratory flow", "Normal", "",
    "normal for age, sex and height",
    verify="Author choice: qualitative 'Normal' rather than a number, because "
           "predicted PEF is patient-specific. A case teaching serial PEF "
           "improvement must override with numbers and supply units."),
"ultrasound_aorta": report("Abdominal aorta measures within normal limits throughout "
                           "its visualized course. No aneurysm. No intimal flap."),
"ultrasound_cardiac": report("Normal global left ventricular systolic function. No "
                             "pericardial effusion. Right ventricle not dilated. "
                             "Inferior vena cava normal caliber with respiratory variation."),
"ultrasound_fast": report("No free fluid in Morison's pouch, splenorenal recess, "
                          "pelvis or pericardium. Negative FAST."),
"ultrasound_lower_extremity_venous": report("Common femoral, femoral and popliteal veins "
                                            "fully compressible. No intraluminal thrombus."),
"ultrasound_lung": report("Bilateral lung sliding present. A-line predominant pattern. "
                          "No B-lines. No pleural effusion."),
"ultrasound_renal": report("No hydronephrosis bilaterally. Kidneys normal in size and "
                           "echotexture. Bladder without abnormality."),
"ultrasound_ruq": report("Gallbladder without stones or wall thickening. No pericholecystic "
                         "fluid. Negative sonographic Murphy sign. Common bile duct normal "
                         "caliber."),
"ultrasound_soft_tissue": report("No discrete fluid collection or abscess. No cobblestoning. "
                                 "No radiopaque foreign body identified."),

# --------------------------------------------------------------- lab work
"arterial_blood_gas": panel(
    ("pH", "7.40", "", "7.35-7.45"),
    ("pCO2", "40", "mmHg", "35-45"),
    ("pO2", "95", "mmHg", "80-100 on room air"),
    ("HCO3", "24", "mEq/L", "22-26"),
    ("Base excess", "0", "mEq/L", "-2 to +2"),
    ("O2 saturation", "97", "%", "95-100"),
    verify="pO2 and saturation are only interpretable against the FiO2 the patient "
           "is on. A patient on a non-rebreather with a pO2 of 95 is not normal. "
           "This default is only valid on room air."),
"venous_blood_gas": panel(
    ("pH", "7.36", "", "7.31-7.41"),
    ("pCO2", "45", "mmHg", "41-51"),
    ("HCO3", "25", "mEq/L", "22-26"),
    ("Base excess", "0", "mEq/L", "-2 to +2"),
    ("Lactate", "1.2", "mmol/L", "0.5-2.0"),
    verify="Venous reference intervals differ from arterial and are often reported "
           "against the arterial ranges by mistake. A venous pH runs about 0.03 to "
           "0.05 lower and a venous pCO2 about 4 to 6 mmHg higher than arterial. "
           "No pO2 is reported: a venous pO2 says nothing about oxygenation and "
           "printing one invites it to be read as though it did."),
"basic_chemistry_chem_7": panel(
    ("Sodium", "139", "mEq/L", "135-145"),
    ("Potassium", "4.1", "mEq/L", "3.5-5.0"),
    ("Chloride", "103", "mEq/L", "98-107"),
    ("Bicarbonate", "25", "mEq/L", "22-29"),
    ("BUN", "14", "mg/dL", "7-20"),
    ("Creatinine", "0.9", "mg/dL", "0.6-1.2"),
    ("Glucose", "94", "mg/dL", "70-140 (random)"),
    verify="Creatinine range is sex- and muscle-mass-dependent; 0.6-1.2 is a "
           "combined range. Glucose range differs fasting vs random."),
"blood_type_and_screen": panel(
    ("ABO/Rh", "O negative", "", "not applicable"),
    ("Antibody screen", "Negative", "", "negative"),
    verify="Author choice: O negative. Blood type is a patient attribute, not a "
           "normal value. Every unauthored patient is now universal-donor type, "
           "which no case should ever depend on. Cases turning on type-specific "
           "transfusion, Rh status or RhoGAM must override this."),
"calcium_ionized": value("Ionized calcium", "1.22", "mmol/L", "1.12-1.32"),
"calcium_level": value("Total calcium", "9.4", "mg/dL", "8.5-10.5"),
"coagulation_panel": panel(
    ("PT", "12.5", "sec", "11.0-13.5"),
    ("INR", "1.0", "", "0.8-1.1"),
    ("aPTT", "30", "sec", "25-35")),
"complete_blood_count_cbc": panel(
    ("WBC", "7.2", "x10^9/L", "4.0-11.0"),
    ("Hemoglobin", "14.2", "g/dL", "13.5-17.5 (M), 12.0-16.0 (F)"),
    ("Hematocrit", "42", "%", "41-53 (M), 36-46 (F)"),
    ("Platelets", "250", "x10^9/L", "150-400"),
    ("MCV", "89", "fL", "80-100"),
    verify="Hemoglobin and hematocrit ranges are sex-specific. A single default "
           "value of 14.2 reads as normal for a man and high-normal for a woman. "
           "Consider sex-conditional defaults."),
"d_dimer": value("D-dimer", "0.31", "mcg/mL FEU", "< 0.50",
    verify="Age-adjusted cutoffs (age x 0.01 over 50) are widely used and change "
           "interpretation in older patients. Units vary between FEU and DDU by "
           "a factor of two."),
"lactate": value("Lactate", "1.2", "mmol/L", "0.5-2.0"),
"lipase": value("Lipase", "32", "U/L", "10-140"),
"liver_function_tests_lfts": panel(
    ("AST", "22", "U/L", "10-40"),
    ("ALT", "24", "U/L", "7-56"),
    ("Alkaline phosphatase", "75", "U/L", "44-147"),
    ("Total bilirubin", "0.8", "mg/dL", "0.1-1.2"),
    ("Direct bilirubin", "0.2", "mg/dL", "0.0-0.3"),
    ("Albumin", "4.2", "g/dL", "3.5-5.0"),
    ("Total protein", "7.0", "g/dL", "6.0-8.3")),
"magnesium_level": value("Magnesium", "2.0", "mg/dL", "1.7-2.2"),
"phosphate_level": value("Phosphate", "3.5", "mg/dL", "2.5-4.5"),
"plasma_procalcitonin": value("Procalcitonin", "< 0.10", "ng/mL", "< 0.10"),
"pro_bnp": value("NT-proBNP", "Unremarkable", "", "within normal limits",
    verify="Author choice: qualitative, avoiding the age-, renal- and "
           "atrial-fibrillation-dependent cutoffs and the BNP vs NT-proBNP "
           "assay ambiguity. A case using a raw value must override with units."),
"troponin_t": value("Troponin T", "Unremarkable", "", "within normal limits",
    verify="Author choice: qualitative. Note this removes the number, and ED "
           "troponin decisions run on the serial delta rather than a single "
           "value, so any case teaching a rising troponin must override both "
           "draws with numbers and units."),
"urinalysis": panel(
    ("Color", "Yellow", "", "yellow"),
    ("Clarity", "Clear", "", "clear"),
    ("Specific gravity", "1.015", "", "1.005-1.030"),
    ("pH", "6.0", "", "4.5-8.0"),
    ("Protein", "Negative", "", "negative"),
    ("Glucose", "Negative", "", "negative"),
    ("Ketones", "Negative", "", "negative"),
    ("Blood", "Negative", "", "negative"),
    ("Leukocyte esterase", "Negative", "", "negative"),
    ("Nitrite", "Negative", "", "negative"),
    ("WBC", "0-2", "/hpf", "0-5"),
    ("RBC", "0-2", "/hpf", "0-2"),
    ("Bacteria", "None seen", "", "none")),

# -------------------------------------------------------------- other labs
"acetaminophen_level": value("Acetaminophen", "Not detected", "mcg/mL", "< 10"),
"amylase": value("Amylase", "65", "U/L", "25-125"),
"blood_culture_x_2": report("Cultures pending.",
    verify="Blood cultures take 24-48 hours; the 5-second lab turnaround cannot "
           "represent that. 'Cultures pending' is honest, but it means a case "
           "whose teaching point is a positive culture cannot be authored, and "
           "the design 8.3 rule that surfaces unviewed pending results at handoff "
           "will flag this study in every case that orders it."),
"c_reactive_protein_crp": value("CRP", "2.1", "mg/L", "< 5"),
"covid_19_test": report("SARS-CoV-2 nucleic acid: Not detected."),
"creatine_kinase_ck": value("Creatine kinase", "90", "U/L", "30-200",
    verify="CK range varies substantially with sex, race and muscle mass."),
"csf_cell_count": panel(
    ("CSF WBC", "1", "/mm3", "0-5"),
    ("CSF RBC", "0", "/mm3", "0"),
    ("Differential", "Lymphocyte predominant", "", "lymphocyte predominant")),
"csf_culture": report("Cultures pending.", verify="See blood culture note."),
"csf_glucose": value("CSF glucose", "60", "mg/dL", "50-80, roughly two thirds of serum"),
"csf_gram_stain": report("No organisms seen. No white cells seen."),
"csf_protein": value("CSF protein", "35", "mg/dL", "15-45"),
"csf_rapid_antigen_test_for_n_meningitidis": report("Negative."),
"erythrocyte_sedimentation_rate_esr": value("ESR", "10", "mm/hr",
    "0-15 (M), 0-20 (F)", verify="Sex- and age-dependent; rises with age."),
"ethanol_level_etoh": value("Ethanol", "Not detected", "mg/dL", "< 10"),
"influenza_a_and_b_antigen_test": report("Influenza A: Negative. Influenza B: Negative."),
"lactate_dehydrogenase_ldh": value("LDH", "180", "U/L", "140-280"),
"osmolality": value("Serum osmolality", "285", "mOsm/kg", "275-295"),
"peripheral_smear": report("Normal red cell morphology. No schistocytes. Normal white "
                           "cell morphology with no immature forms. Platelets adequate "
                           "in number and morphology."),
"salicylate_aspirin_level": value("Salicylate", "Not detected", "mg/dL", "< 4"),
"serum_hcg_quantitative": value("Serum beta-hCG", "Negative", "", "negative",
    verify="Author choice: negative. Pregnancy is a patient attribute, not a "
           "normal value. Every unauthored patient is now not pregnant, including "
           "male patients, for whom the study should arguably be unavailable. Any "
           "obstetric case must override this."),
"skin_biopsy_of_the_rash": report("Not applicable.",
    verify="Author choice: 'Not applicable', since the study name presupposes a "
           "rash the default patient does not have. Note the resident can still "
           "order it and consume time doing so; if that is unwanted, the action "
           "needs to be case-enabled rather than always available."),
"tsh": value("TSH", "2.0", "mIU/L", "0.4-4.0"),
"uric_acid": value("Uric acid", "5.0", "mg/dL", "3.5-7.2",
                   verify="Sex-specific ranges differ."),
"urine_culture": report("Cultures pending.", verify="See blood culture note."),
"urine_hcg_qualitative": report("Negative.",
    verify="Author choice: negative. See serum hCG note. Serum and urine hCG "
           "defaults are set independently here and nothing enforces that a case "
           "overriding one also overrides the other."),
"urine_rapid_antigen_test_for_n_meningitidis": report("Negative."),
"urine_rapid_antigen_test_for_s_pneumoniae": report("Negative."),
"urine_tox_screen": report("Amphetamines: Negative. Barbiturates: Negative. "
                           "Benzodiazepines: Negative. Cocaine metabolite: Negative. "
                           "Opiates: Negative. Cannabinoids: Negative.",
    verify="Panel composition varies by institution, and the screen misses "
           "synthetics, fentanyl on many panels, and most designer agents. A "
           "negative screen is not a negative exposure."),

# ----------------------------------------------------------------- imaging
"ct_abdomen": report("No acute intra-abdominal or pelvic abnormality. No free air or "
                     "free fluid. Bowel normal in caliber. Solid organs unremarkable. "
                     "No obstructing stone or hydronephrosis."),
"ct_aorta": report("No aortic dissection. No aneurysm. No intramural hematoma or "
                   "periaortic stranding."),
"ct_c_spine": report("No acute cervical spine fracture or malalignment. Prevertebral "
                     "soft tissues normal."),
"ct_chest": report("No acute cardiopulmonary process. Lungs clear. No effusion or "
                   "pneumothorax. Mediastinum normal."),
"ct_head": report("No acute intracranial hemorrhage, mass effect or midline shift. "
                  "No evidence of acute large territory infarct. No skull fracture."),
"ct_pulmonary_embolus": report("No filling defect within the pulmonary arteries. No "
                               "evidence of pulmonary embolism. No right heart strain."),
"ct_cta_head_and_neck": report("No large vessel occlusion. No dissection or aneurysm. "
                               "No high-grade stenosis."),
"mri_c_spine": report("No cord compression, cord signal abnormality or epidural "
                      "collection. No acute fracture."),
"mri_lumbar_spine": report("No cord or cauda equina compression. No epidural abscess "
                           "or collection. No acute fracture."),
"mri_thoracic_spine": report("No cord compression or cord signal abnormality. No "
                             "epidural collection."),
"mri_mra_head_and_neck": report("No acute infarct on diffusion-weighted imaging. No "
                                "large vessel occlusion, dissection or aneurysm."),
"xr_chest": report("Lungs clear. No consolidation, effusion or pneumothorax. Cardiac "
                   "silhouette normal in size. No acute bony abnormality."),
"xr_pelvis": report("No acute pelvic fracture or diastasis. Hips located."),
}


# ============================================================================
# DEFAULT EXAM FINDINGS
# ============================================================================
# case-authoring-requirements.md section 11: "Author only maneuvers whose
# findings are abnormal or that change with treatment. Everything else inherits
# the global normal finding." This is that global normal finding.
#
# Section 2 of the same document lists "Normal exam findings, normal labs" as
# AI-DRAFTABLE, so unlike the reference ranges above these are inside the
# drafting remit. They still need a physician read for phrasing and for what a
# US EM resident would expect a normal maneuver to report.
#
# Exams are reads: they never change state (design principle 4) and are never
# narrated (section 9.1). They may be repeated freely and return current state.
#
# The 14 entries here are the complete set. There is no fifteenth exam. The
# generator fails if an exam has no default or a default has no exam, so this
# list and the catalog cannot diverge.

def exam(text, **kw):
    return dict(kind="exam_findings", abnormal=False, findings=text, **kw)

EXAM_DEFAULTS = {
"exam_airway": exam(
    "Airway patent and self-maintained. Speaking in full sentences. No stridor, "
    "drooling, or oropharyngeal swelling. No foreign body visible. Mouth opening "
    "and thyromental distance normal."),
"exam_breath": exam(
    "Breathing spontaneously at a normal rate. Chest rises symmetrically. No "
    "accessory muscle use and no retractions. Air entry equal bilaterally."),
"exam_circ": exam(
    "Warm and dry peripherally. Capillary refill under two seconds. Radial and "
    "dorsalis pedis pulses palpable and equal bilaterally. No external hemorrhage."),
"exam_heent": exam(
    "Normocephalic and atraumatic. Pupils equal, round and reactive to light. "
    "Extraocular movements intact. Conjunctivae and sclerae normal. Tympanic "
    "membranes normal. Oropharynx moist and clear without erythema or exudate."),
"exam_neck": exam(
    "Supple with full range of motion. No jugular venous distension. Trachea "
    "midline. No lymphadenopathy, thyromegaly or carotid bruit. No midline "
    "cervical tenderness."),
"exam_card": exam(
    "Regular rate and rhythm. Normal S1 and S2. No murmur, rub or gallop. Point "
    "of maximal impulse not displaced. No peripheral edema."),
"exam_pulm": exam(
    "Clear to auscultation bilaterally. No crackles, wheezes or rhonchi. "
    "Resonant to percussion. Symmetric chest expansion."),
"exam_abd": exam(
    "Soft, non-distended and non-tender. No guarding or rebound. Bowel sounds "
    "present and normal. No organomegaly, palpable mass or pulsatile mass. No "
    "hernia."),
"exam_gu": exam(
    "External genitalia normal without lesion, swelling or discharge. No "
    "testicular tenderness or asymmetry. No vaginal bleeding or discharge. No "
    "suprapubic tenderness.",
    verify="Written to cover both sexes in one string, so part of it is always "
           "irrelevant. If the renderer cannot select by patient sex, this "
           "should be split into two defaults."),
"exam_back": exam(
    "No midline spinal tenderness, step-off or deformity. No costovertebral "
    "angle tenderness bilaterally. No rash or lesion over the back or flanks."),
"exam_msk": exam(
    "No deformity, swelling or joint effusion. Full active and passive range of "
    "motion. No focal bony tenderness. Compartments soft. Distal pulses, "
    "sensation and motor function intact in all four limbs."),
"exam_skin": exam(
    "Warm and dry with normal color. No rash, petechiae, purpura or bruising. "
    "No wounds, ulcers or cellulitis. No diaphoresis."),
"exam_neuro": exam(
    "Alert and oriented to person, place and time. GCS 15. Speech fluent. "
    "Cranial nerves II through XII intact. Strength 5 out of 5 throughout. "
    "Sensation intact. Coordination and gait normal. No pronator drift."),
"exam_psych": exam(
    "Calm and cooperative with appropriate affect. Thought linear and goal "
    "directed. No suicidal or homicidal ideation. No hallucinations. Insight "
    "and judgment intact."),
}

# The General Status line rendered above the exam list. Not an exam and not
# clickable, so it is not a catalog action, but it needs a default for the same
# reason the exams do.
GENERAL_STATUS_DEFAULT = {
    "kind": "general_status",
    "abnormal": False,
    "findings": "No acute distress. GCS 15.",
    "verify": "This line duplicates content that also lives in exam_neuro (GCS) "
              "and in the animated patient's appearance. A case that makes the "
              "patient obtunded and overrides exam_neuro but forgets this line "
              "will display GCS 15 above a comatose neuro exam. Recommend a "
              "validator rule.",
}

# Findings whose anatomy does not map cleanly onto the 14 available maneuvers.
# Without a fixed routing an author puts pedal edema under CARD in one case and
# MSK in another, and the resident learns the tool is arbitrary rather than
# learning where to look. Authors should follow this map.
EXAM_ROUTING = {
    "Jugular venous distension": "exam_neck",
    "Peripheral or pedal edema": "exam_card",
    "Capillary refill, skin temperature, pulse quality": "exam_circ",
    "Extremity findings (deformity, swelling, range of motion, compartments)": "exam_msk",
    "Distal neurovascular status of a limb": "exam_msk",
    "Rash, wounds, cellulitis, diaphoresis": "exam_skin",
    "Level of consciousness and GCS": "exam_neuro",
    "Agitation, cooperativeness, thought content": "exam_psych",
    "Rectal examination": "exam_gu",
    "Breast examination": "no available maneuver",
    "Fundoscopy": "exam_heent",
    "Costovertebral angle tenderness": "exam_back",
    "Tracheal position": "exam_neck",
    "Accessory muscle use, work of breathing": "exam_breath",
    "Lung auscultation": "exam_pulm",
    "_note": "There is no extremity, vascular, rectal or lymphatic maneuver in "
             "the UI. Findings belonging to those go to the nearest listed "
             "maneuver above. Anything mapped to 'no available maneuver' cannot "
             "be examined for and must not be a case's teaching point.",
}
