#!/usr/bin/env python3
"""
Global diagnosis catalog for the EM case simulator.
system-design-v2.md section 3 / section 9; case-authoring-requirements.md section 12.

Hand-curated and EM-scoped: the entries are diagnoses a US emergency physician
would plausibly commit to at handoff, plus the near-misses that make searching a
real cognitive task rather than a lookup.

STATUS: DRAFT, NOT CLINICALLY REVIEWED. This list was assembled by the drafting
AI. Diagnosis naming is not a clinical fact in the sense of section 2 of the
authoring requirements (no symptom, finding, value, or recommendation is asserted
here), but list COMPOSITION is a clinical judgement, and an omission is invisible
to the learner: a resident who cannot find the right answer cannot tell "wrong"
from "not in the list". A physician must review before release.

No ICD-10 or SNOMED codes are included. Emitting codes from memory would put
plausible-looking wrong codes into the file, which is worse than none.

Regenerate:  python3 build_diagnoses.py > diagnosis-catalog.json
"""
import json, re, sys

def sid(name):
    s = name.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return "dx_" + s

# Each entry: name, or (name, [search synonyms]).
CATALOG = {
"cardiovascular": [
    ("ST-elevation myocardial infarction", ["STEMI", "heart attack", "MI"]),
    ("Non-ST-elevation myocardial infarction", ["NSTEMI"]),
    ("Unstable angina", []), ("Stable angina", []),
    ("Acute coronary syndrome, unspecified", ["ACS"]),
    ("Atrial fibrillation with rapid ventricular response", ["AF RVR", "afib RVR"]),
    ("Atrial fibrillation", ["afib"]), ("Atrial flutter", []),
    ("Supraventricular tachycardia", ["SVT"]),
    ("Ventricular tachycardia", ["VT", "V tach"]),
    ("Ventricular fibrillation", ["VF", "V fib"]),
    ("Torsades de pointes", []), ("Wolff-Parkinson-White syndrome", ["WPW"]),
    ("Third-degree atrioventricular block", ["complete heart block", "3rd degree AV block"]),
    ("Second-degree AV block, Mobitz type I", ["Wenckebach"]),
    ("Second-degree AV block, Mobitz type II", []),
    ("First-degree AV block", []), ("Sick sinus syndrome", []),
    ("Symptomatic bradycardia", []), ("Pacemaker malfunction", []),
    ("Acute decompensated heart failure with reduced ejection fraction",
     ["ADHF HFrEF", "CHF exacerbation", "systolic heart failure"]),
    ("Acute decompensated heart failure with preserved ejection fraction",
     ["ADHF HFpEF", "diastolic heart failure"]),
    ("Cardiogenic shock", []), ("Cardiogenic pulmonary edema", ["flash pulmonary edema"]),
    ("Hypertensive emergency", []), ("Hypertensive urgency", []),
    ("Acute pericarditis", []), ("Cardiac tamponade", []),
    ("Pericardial effusion without tamponade", []), ("Myocarditis", []),
    ("Infective endocarditis", []), ("Aortic dissection", []),
    ("Thoracic aortic aneurysm", []),
    ("Ruptured abdominal aortic aneurysm", ["ruptured AAA"]),
    ("Abdominal aortic aneurysm, unruptured", ["AAA"]),
    ("Acute limb ischemia", []), ("Peripheral arterial disease", ["PAD"]),
    ("Deep vein thrombosis", ["DVT"]), ("Superficial thrombophlebitis", []),
    ("Severe aortic stenosis", []), ("Acute mitral regurgitation", []),
    ("Prosthetic valve thrombosis", []),
    ("Left ventricular assist device malfunction", ["LVAD malfunction"]),
    ("Cardiac arrest", []), ("Post-cardiac arrest syndrome", []),
    ("Takotsubo cardiomyopathy", ["stress cardiomyopathy"]),
    ("Hypertrophic cardiomyopathy", ["HCM"]),
    ("Vasovagal syncope", []), ("Orthostatic hypotension", []),
],
"respiratory": [
    ("Community-acquired pneumonia", ["CAP"]),
    ("Hospital-acquired pneumonia", ["HAP"]),
    ("Aspiration pneumonia", []), ("Aspiration pneumonitis", []),
    ("COPD exacerbation", ["AECOPD", "emphysema exacerbation"]),
    ("Asthma exacerbation", []), ("Status asthmaticus", []),
    ("Pulmonary embolism", ["PE"]), ("Massive pulmonary embolism", ["saddle PE"]),
    ("Primary spontaneous pneumothorax", []),
    ("Secondary spontaneous pneumothorax", []),
    ("Tension pneumothorax", []), ("Hemothorax", []),
    ("Pleural effusion", []), ("Empyema", []),
    ("Acute respiratory distress syndrome", ["ARDS"]),
    ("Acute hypoxemic respiratory failure", []),
    ("Acute hypercapnic respiratory failure", []),
    ("Bronchiolitis", []), ("Foreign body aspiration", []),
    ("Lung abscess", []), ("Bronchiectasis exacerbation", []),
    ("Pertussis", ["whooping cough"]), ("Influenza", ["flu"]),
    ("COVID-19", ["SARS-CoV-2"]), ("Respiratory syncytial virus infection", ["RSV"]),
    ("Pulmonary hypertension", []), ("Interstitial lung disease exacerbation", []),
    ("Pulmonary tuberculosis", ["TB"]), ("Massive hemoptysis", []),
    ("Tracheostomy obstruction", []), ("Ventilator-associated pneumonia", ["VAP"]),
],
"neurologic": [
    ("Acute ischemic stroke", ["CVA", "stroke"]),
    ("Transient ischemic attack", ["TIA"]),
    ("Intracerebral hemorrhage", ["ICH"]),
    ("Subarachnoid hemorrhage", ["SAH"]),
    ("Acute subdural hematoma", ["SDH"]), ("Chronic subdural hematoma", []),
    ("Epidural hematoma", ["EDH"]),
    ("Cerebral venous sinus thrombosis", ["CVST"]),
    ("Carotid artery dissection", []), ("Vertebral artery dissection", []),
    ("Status epilepticus", []), ("First-time generalized seizure", []),
    ("Breakthrough seizure", []), ("Nonconvulsive status epilepticus", []),
    ("Bacterial meningitis", []), ("Viral meningitis", ["aseptic meningitis"]),
    ("Encephalitis", []), ("Brain abscess", []),
    ("Migraine headache", []), ("Cluster headache", []), ("Tension headache", []),
    ("Idiopathic intracranial hypertension", ["pseudotumor cerebri"]),
    ("Giant cell arteritis", ["temporal arteritis"]),
    ("Bell palsy", []), ("Guillain-Barre syndrome", ["GBS"]),
    ("Myasthenic crisis", []), ("Multiple sclerosis relapse", ["MS flare"]),
    ("Spinal epidural abscess", []), ("Cauda equina syndrome", []),
    ("Transverse myelitis", []),
    ("Benign paroxysmal positional vertigo", ["BPPV"]),
    ("Vestibular neuritis", []), ("Meniere disease", []),
    ("Delirium", []), ("Dementia", []), ("Wernicke encephalopathy", []),
    ("Ventriculoperitoneal shunt malfunction", ["VP shunt malfunction"]),
    ("Normal pressure hydrocephalus", ["NPH"]),
],
"gastrointestinal": [
    ("Acute appendicitis", []), ("Acute cholecystitis", []), ("Biliary colic", []),
    ("Choledocholithiasis", []), ("Ascending cholangitis", []),
    ("Acute pancreatitis", []), ("Small bowel obstruction", ["SBO"]),
    ("Large bowel obstruction", []), ("Ileus", []),
    ("Perforated peptic ulcer", []), ("Peptic ulcer disease", ["PUD"]),
    ("Upper gastrointestinal bleed", ["UGIB"]),
    ("Lower gastrointestinal bleed", ["LGIB"]),
    ("Variceal hemorrhage", []), ("Diverticulitis", []),
    ("Acute mesenteric ischemia", []), ("Sigmoid volvulus", []),
    ("Cecal volvulus", []), ("Incarcerated hernia", []),
    ("Strangulated hernia", []), ("Inflammatory bowel disease flare", ["Crohn", "ulcerative colitis"]),
    ("Clostridioides difficile colitis", ["C diff"]),
    ("Infectious gastroenteritis", []), ("Viral gastroenteritis", []),
    ("Esophageal food impaction", []), ("Boerhaave syndrome", ["esophageal rupture"]),
    ("Mallory-Weiss tear", []), ("Gastroesophageal reflux disease", ["GERD"]),
    ("Acute viral hepatitis", []), ("Alcoholic hepatitis", []),
    ("Decompensated cirrhosis", []),
    ("Spontaneous bacterial peritonitis", ["SBP"]),
    ("Hepatic encephalopathy", []), ("Acute liver failure", []),
    ("Intussusception", []), ("Hypertrophic pyloric stenosis", []),
    ("Necrotizing enterocolitis", ["NEC"]),
    ("Anorectal abscess", []), ("Thrombosed external hemorrhoid", []),
    ("Anal fissure", []), ("Constipation", []),
    ("Gastrostomy tube dislodgement", ["G tube dislodgement"]),
    ("Toxic megacolon", []),
],
"renal_genitourinary": [
    ("Acute kidney injury", ["AKI"]), ("Chronic kidney disease", ["CKD"]),
    ("Nephrolithiasis", ["kidney stone", "renal colic"]),
    ("Obstructive uropathy", []), ("Urinary tract infection", ["UTI"]),
    ("Pyelonephritis", []), ("Urosepsis", []), ("Urinary retention", []),
    ("Testicular torsion", []), ("Epididymitis", []), ("Orchitis", []),
    ("Fournier gangrene", []), ("Priapism", []), ("Paraphimosis", []),
    ("Renal infarction", []), ("Rhabdomyolysis", []),
    ("Dialysis catheter complication", []),
    ("Volume overload from missed dialysis", []),
    ("Bleeding hemodialysis access site", []),
    ("Acute bacterial prostatitis", []),
],
"infectious_disease": [
    ("Sepsis", []), ("Septic shock", []), ("Cellulitis", []),
    ("Cutaneous abscess", []),
    ("Necrotizing soft tissue infection", ["necrotizing fasciitis"]),
    ("Septic arthritis", []), ("Osteomyelitis", []),
    ("Meningococcemia", []), ("Toxic shock syndrome", ["TSS"]),
    ("Malaria", []), ("Dengue fever", []), ("Typhoid fever", []),
    ("Tetanus", []), ("Rabies exposure", []), ("Lyme disease", []),
    ("Rocky Mountain spotted fever", ["RMSF"]),
    ("Acute retroviral syndrome", ["acute HIV"]),
    ("Pneumocystis pneumonia", ["PJP", "PCP"]),
    ("Herpes zoster", ["shingles"]), ("Herpes zoster ophthalmicus", []),
    ("Infectious mononucleosis", ["mono", "EBV"]),
    ("Measles", []), ("Varicella", ["chickenpox"]), ("Scarlet fever", []),
    ("Central line-associated bloodstream infection", ["CLABSI"]),
    ("Streptococcal pharyngitis", ["strep throat"]),
],
"endocrine_metabolic": [
    ("Diabetic ketoacidosis", ["DKA"]),
    ("Hyperosmolar hyperglycemic state", ["HHS"]),
    ("Hypoglycemia", []), ("Alcoholic ketoacidosis", ["AKA"]),
    ("Thyroid storm", []), ("Myxedema coma", []),
    ("Hypothyroidism", []), ("Hyperthyroidism", []),
    ("Adrenal crisis", []), ("Pheochromocytoma crisis", []),
    ("Hyperkalemia", []), ("Hypokalemia", []),
    ("Hyponatremia", []), ("Hypernatremia", []),
    ("Hypercalcemia", []), ("Hypocalcemia", []),
    ("Hypermagnesemia", []), ("Hypomagnesemia", []),
    ("Anion gap metabolic acidosis", []), ("Non-anion gap metabolic acidosis", []),
    ("Metabolic alkalosis", []), ("Respiratory acidosis", []),
    ("Respiratory alkalosis", []), ("Lactic acidosis", []),
    ("Hypovolemia", ["dehydration"]),
],
"hematology_oncology": [
    ("Acute blood loss anemia", []), ("Iron deficiency anemia", []),
    ("Sickle cell vaso-occlusive crisis", ["sickle cell pain crisis"]),
    ("Acute chest syndrome", []), ("Splenic sequestration crisis", []),
    ("Immune thrombocytopenia", ["ITP"]),
    ("Thrombotic thrombocytopenic purpura", ["TTP"]),
    ("Hemolytic uremic syndrome", ["HUS"]),
    ("Disseminated intravascular coagulation", ["DIC"]),
    ("Hemophilia A with acute bleeding", []),
    ("Hemophilia B with acute bleeding", []),
    ("Von Willebrand disease with acute bleeding", []),
    ("Warfarin-associated coagulopathy", ["supratherapeutic INR"]),
    ("Direct oral anticoagulant-associated bleeding", ["DOAC bleed"]),
    ("Heparin-induced thrombocytopenia", ["HIT"]),
    ("Febrile neutropenia", []), ("Tumor lysis syndrome", ["TLS"]),
    ("Hypercalcemia of malignancy", []),
    ("Superior vena cava syndrome", ["SVC syndrome"]),
    ("Malignant spinal cord compression", []), ("Leukostasis", []),
    ("Acute hemolytic transfusion reaction", []),
    ("Transfusion-related acute lung injury", ["TRALI"]),
    ("Transfusion-associated circulatory overload", ["TACO"]),
],
"toxicology": [
    ("Acetaminophen toxicity", ["Tylenol overdose", "paracetamol"]),
    ("Salicylate toxicity", ["aspirin overdose"]),
    ("Opioid overdose", []), ("Benzodiazepine overdose", []),
    ("Acute alcohol intoxication", []), ("Alcohol withdrawal", []),
    ("Delirium tremens", ["DTs"]),
    ("Methanol toxicity", []), ("Ethylene glycol toxicity", ["antifreeze"]),
    ("Isopropanol ingestion", []),
    ("Tricyclic antidepressant overdose", ["TCA overdose"]),
    ("SSRI overdose", []), ("Serotonin syndrome", []),
    ("Neuroleptic malignant syndrome", ["NMS"]),
    ("Lithium toxicity", []), ("Digoxin toxicity", []),
    ("Beta-blocker overdose", []), ("Calcium channel blocker overdose", []),
    ("Sympathomimetic toxicity", ["cocaine", "amphetamine", "methamphetamine"]),
    ("Anticholinergic toxidrome", []),
    # Author instruction, 5 September 2026, for the diphenhydramine case. Three entries,
    # and the middle one is the important one.
    #
    # The catalog held "Anticholinergic toxidrome" and nothing else an antihistamine
    # overdose could be handed off as, so a case whose whole teaching point is that the
    # toxidrome is NOT the whole story had to record the toxidrome as its correct answer.
    # The agent now has an entry of its own.
    #
    # Sodium channel blocker cardiotoxicity is deliberately a mechanism rather than an
    # agent, because that is how it is handed over and because it is the thing a receiving
    # team acts on: the same entry serves tricyclic, diphenhydramine, cocaine, bupropion,
    # flecainide and local anaesthetic poisoning, all of which are treated the same way.
    # It is the entry a wide QRS after any exposure should resolve to.
    #
    # Drug-induced seizure exists because the nearest previous fit was status epilepticus,
    # which claims something about duration that a single toxic convulsion does not.
    ("Diphenhydramine overdose",
     ["Benadryl overdose", "antihistamine overdose", "diphenhydramine toxicity",
      "H1 antihistamine overdose", "sedating antihistamine overdose"]),
    ("Sodium channel blocker cardiotoxicity",
     ["sodium channel blockade", "QRS widening from poisoning", "wide QRS overdose",
      "membrane stabilising effect", "membrane stabilizing effect"]),
    ("Drug-induced seizure", ["toxic seizure", "seizure from overdose", "poisoning seizure"]),
    ("Organophosphate poisoning", ["cholinergic toxidrome"]),
    ("Carbon monoxide poisoning", ["CO poisoning"]),
    ("Cyanide poisoning", []), ("Methemoglobinemia", []),
    ("Iron toxicity", []), ("Lead poisoning", []),
    ("Caustic ingestion", []), ("Hydrocarbon ingestion", []),
    ("Button battery ingestion", []),
    ("Body packer or body stuffer", []),
    ("Cannabinoid hyperemesis syndrome", ["CHS"]),
    ("Synthetic cannabinoid toxicity", []),
    ("Opioid withdrawal", []), ("Sedative-hypnotic withdrawal", []),
    ("Crotalid snake envenomation", ["rattlesnake bite"]),
    ("Scorpion envenomation", []),
    ("Black widow spider envenomation", []),
    ("Brown recluse spider envenomation", []),
],
"environmental": [
    ("Heat exhaustion", []), ("Heat stroke", []),
    ("Accidental hypothermia", []), ("Frostbite", []),
    ("Drowning", ["submersion injury"]),
    ("Decompression sickness", ["the bends"]),
    ("Arterial gas embolism", []),
    ("High-altitude cerebral edema", ["HACE"]),
    ("High-altitude pulmonary edema", ["HAPE"]),
    ("Acute mountain sickness", ["AMS"]),
    ("Electrical injury", []), ("Lightning injury", []),
    ("Thermal burn", []), ("Chemical burn", []),
    ("Inhalation injury", []), ("Acute radiation syndrome", []),
],
"trauma": [
    ("Severe traumatic brain injury", ["severe TBI"]),
    ("Mild traumatic brain injury", ["concussion"]),
    ("Diffuse axonal injury", []), ("Basilar skull fracture", []),
    ("Cervical spine fracture", []), ("Thoracolumbar spine fracture", []),
    ("Spinal cord injury", []), ("Rib fractures", []), ("Flail chest", []),
    ("Pulmonary contusion", []), ("Traumatic pneumothorax", []),
    ("Traumatic hemothorax", []), ("Blunt cardiac injury", []),
    ("Blunt aortic injury", []), ("Splenic laceration", []),
    ("Hepatic laceration", []), ("Traumatic bowel perforation", []),
    ("Retroperitoneal hematoma", []), ("Pelvic fracture", []),
    ("Penetrating chest trauma", []), ("Penetrating abdominal trauma", []),
    ("Traumatic cardiac arrest", []), ("Hemorrhagic shock", []),
    ("Crush injury", []), ("Acute compartment syndrome", []),
    ("Traumatic amputation", []), ("Open fracture", []),
    ("Orbital fracture", []), ("Midface fracture", ["Le Fort fracture"]),
    ("Mandibular fracture", []), ("Dental avulsion", []),
    ("Major burn", []), ("Suspected physical child abuse", ["non-accidental trauma"]),
    ("Suspected elder abuse or neglect", []),
    ("Intimate partner violence-related injury", []),
],
"musculoskeletal": [
    ("Hip fracture", []), ("Femoral shaft fracture", []),
    ("Distal radius fracture", ["Colles fracture"]),
    ("Scaphoid fracture", []), ("Humerus fracture", []),
    ("Clavicle fracture", []), ("Ankle fracture", []),
    ("Tibial plateau fracture", []),
    ("Anterior shoulder dislocation", []), ("Posterior shoulder dislocation", []),
    ("Hip dislocation", []), ("Elbow dislocation", []),
    ("Patellar dislocation", []), ("Knee dislocation", []),
    ("Achilles tendon rupture", []), ("Gout", []),
    ("Pseudogout", ["calcium pyrophosphate deposition"]),
    ("Olecranon bursitis", []), ("Nonspecific low back pain", []),
    ("Lumbar radiculopathy", ["sciatica"]), ("Rotator cuff tear", []),
    ("Radial head subluxation", ["nursemaid's elbow"]),
    ("Slipped capital femoral epiphysis", ["SCFE"]),
    ("Legg-Calve-Perthes disease", []), ("Toddler's fracture", []),
    ("Paronychia", []), ("Felon", []),
    ("Flexor tenosynovitis", []), ("High-pressure injection injury", []),
],
"dermatologic": [
    ("Stevens-Johnson syndrome", ["SJS"]),
    ("Toxic epidermal necrolysis", ["TEN"]),
    ("DRESS syndrome", ["drug reaction with eosinophilia"]),
    ("Erythema multiforme", []), ("Urticaria", ["hives"]),
    ("Angioedema", []), ("Hereditary angioedema", ["HAE"]),
    ("ACE inhibitor-induced angioedema", []),
    ("Contact dermatitis", []), ("Pemphigus vulgaris", []),
    ("Staphylococcal scalded skin syndrome", ["SSSS"]),
    ("Purpura fulminans", []),
],
"obstetric_gynecologic": [
    ("Ectopic pregnancy", []), ("Ruptured ectopic pregnancy", []),
    ("Threatened abortion", []), ("Incomplete abortion", []),
    ("Missed abortion", []), ("Septic abortion", []),
    ("Hyperemesis gravidarum", []), ("Preeclampsia", []),
    ("Preeclampsia with severe features", []), ("Eclampsia", []),
    ("HELLP syndrome", []), ("Placental abruption", []),
    ("Placenta previa", []), ("Preterm labor", []),
    ("Precipitous delivery", []), ("Postpartum hemorrhage", ["PPH"]),
    ("Retained products of conception", []), ("Chorioamnionitis", []),
    ("Postpartum endometritis", []), ("Amniotic fluid embolism", []),
    ("Peripartum cardiomyopathy", []), ("Ovarian torsion", []),
    ("Ruptured ovarian cyst", []),
    ("Pelvic inflammatory disease", ["PID"]),
    ("Tubo-ovarian abscess", ["TOA"]), ("Bartholin abscess", []),
    ("Abnormal uterine bleeding", []), ("Sexual assault", []),
    ("Trauma in pregnancy", []), ("Postpartum preeclampsia", []),
],
"ent_ophthalmology_dental": [
    ("Anterior epistaxis", []), ("Posterior epistaxis", []),
    ("Peritonsillar abscess", []), ("Retropharyngeal abscess", []),
    ("Ludwig angina", []), ("Epiglottitis", []), ("Croup", ["laryngotracheitis"]),
    ("Acute otitis media", []), ("Otitis externa", []),
    ("Malignant otitis externa", []), ("Mastoiditis", []),
    ("Acute bacterial sinusitis", []),
    ("Sudden sensorineural hearing loss", []),
    ("Nasal foreign body", []), ("Aural foreign body", []),
    ("Dental abscess", []),
    ("Acute angle-closure glaucoma", []),
    ("Central retinal artery occlusion", ["CRAO"]),
    ("Central retinal vein occlusion", ["CRVO"]),
    ("Retinal detachment", []), ("Optic neuritis", []),
    ("Orbital cellulitis", []), ("Periorbital cellulitis", ["preseptal cellulitis"]),
    ("Corneal abrasion", []), ("Corneal ulcer", []), ("Hyphema", []),
    ("Chemical eye injury", []), ("Anterior uveitis", ["iritis"]),
    ("Endophthalmitis", []), ("Ruptured globe", []),
],
"psychiatric": [
    ("Suicidal ideation", []), ("Suicide attempt", []),
    ("Homicidal ideation", []), ("Acute psychosis", []),
    ("Schizophrenia exacerbation", []),
    ("Bipolar disorder, manic episode", []),
    ("Major depressive episode", []), ("Panic attack", []),
    ("Acute agitation", []), ("Catatonia", []),
    ("Substance use disorder", []),
    ("Eating disorder with medical complication", []),
    ("Functional neurologic disorder", ["conversion disorder"]),
],
"allergy_immunology": [
    ("Anaphylaxis", []), ("Localized allergic reaction", []),
    ("Drug hypersensitivity reaction", []), ("Food allergy", []),
],
"pediatric": [
    ("Simple febrile seizure", []), ("Complex febrile seizure", []),
    ("Fever without a source in a young infant", []),
    ("Neonatal sepsis", []), ("Neonatal jaundice", []),
    ("Kawasaki disease", []),
    ("Multisystem inflammatory syndrome in children", ["MIS-C"]),
    ("IgA vasculitis", ["Henoch-Schonlein purpura", "HSP"]),
    ("Ductal-dependent congenital heart disease", []),
    ("Brief resolved unexplained event", ["BRUE", "ALTE"]),
    ("Sudden infant death syndrome", ["SIDS"]),
    ("Pediatric dehydration", []),
    ("Pediatric exploratory ingestion", []),
],
"undifferentiated": [
    ("Undifferentiated shock", []),
    ("Undifferentiated syncope", []),
    ("Undifferentiated chest pain", []),
    ("Undifferentiated abdominal pain", []),
    ("Undifferentiated altered mental status", ["AMS"]),
    ("Undifferentiated fever", []),
    ("Generalized weakness", []),
    ("Undifferentiated dizziness", []),
    ("Undifferentiated dyspnea", []),
    ("Cardiac arrest of undetermined cause", []),
    ("No acute pathology identified", []),
],
}

entries, seen = [], {}
for category, items in CATALOG.items():
    for it in items:
        name, syn = it if isinstance(it, tuple) else (it, [])
        i = sid(name)
        if i in seen:
            raise SystemExit(f"duplicate id {i} ({name} vs {seen[i]})")
        seen[i] = name
        entries.append({"id": i, "display_name": name,
                        "category": category, "synonyms": syn})

AUTHOR_SUPPLIED = {"dx_diphenhydramine_overdose",
                   "dx_sodium_channel_blocker_cardiotoxicity",
                   "dx_drug_induced_seizure"}
for _e in entries:
    if _e["id"] in AUTHOR_SUPPLIED:
        _e["source"] = "author-supplied, added for a case rather than drafted with the list"

OUT = {
  "catalog_version": "0.1-draft",
  "status": "DRAFT, NOT CLINICALLY REVIEWED",
  "aligned_to": ["system-design-v2.md v0.3 sections 3 and 9",
                 "case-authoring-requirements.md v0.2 section 12"],
  "scope": "US emergency department practice; diagnoses a resident could "
           "plausibly commit to at handoff, plus the near-misses that make "
           "search a real cognitive task.",
  "provenance": {
      "assembled_by": "drafting AI, not a physician",
      "codes": "none. ICD-10 and SNOMED codes are deliberately absent rather "
               "than generated from memory.",
      "review_required": "list composition is a clinical judgement and an "
                         "omission is invisible to the learner.",
  },
  "search_contract": {
      "match_on": ["display_name", "synonyms"],
      "note": "synonyms exist so a resident typing STEMI, DKA, or AAA finds "
              "the entry. Coverage is uneven and needs an author pass.",
  },
  "open_questions": [
      "The 'undifferentiated' category lets a resident hand off without "
      "committing to a specific diagnosis. Whether that should ever be scored "
      "as correct is a pedagogical decision, not a data one.",
      "No severity or acuity qualifier is attached to any entry. If a case "
      "wants to distinguish 'sepsis' from 'septic shock' as the handoff answer, "
      "both exist, but nothing enforces which is right.",
      "Many entries pair a general and a specific form (heart failure with "
      "reduced vs preserved EF; AAA ruptured vs not). Cases must decide "
      "whether the general form counts as partially correct.",
      "No pediatric-vs-adult flag. Some entries are pediatric-only and will "
      "appear in adult case searches.",
      "Peds, tox, and environmental sections are thinner than cardiovascular "
      "and GI. That reflects drafting effort, not clinical importance.",
      "Three toxicology entries were added on author instruction rather than "
      "drafted with the rest: diphenhydramine overdose, sodium channel blocker "
      "cardiotoxicity and drug-induced seizure. They are marked "
      "source=author-supplied. The gap they filled is worth stating because it "
      "is the kind that recurs: the catalog held the syndrome (anticholinergic "
      "toxidrome) and not the agent, and not the complication that decides the "
      "treatment, so a case teaching that the syndrome is not the whole story "
      "could not express its own correct answer. Check the other toxidromes for "
      "the same shape before the next tox case.",
  ],
  "counts": {k: len(v) for k, v in CATALOG.items()},
  "total": len(entries),
  "entries": entries,
}
json.dump(OUT, sys.stdout, indent=2, ensure_ascii=False)
