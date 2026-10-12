#!/usr/bin/env python3
"""
Builds the global action catalog (system-design-v2.md section 3) from the UI
screenshots supplied by the author.

Every `display_name` and every `group` is transcribed verbatim from a screenshot.
Everything else -- ids, turnaround classes, state_changing, dose_required,
narration templates, default prerequisites -- is DERIVED and flagged as such in
`field_provenance`. Nothing clinical is asserted here: the catalog holds no
appropriateness judgment, per section 3 of the system design.

Regenerate with:  python3 build_catalog.py > action-catalog.json
"""
import json, re, sys
from default_results import DEFAULTS, EXAM_DEFAULTS, GENERAL_STATUS_DEFAULT, EXAM_ROUTING

def sid(name):
    s = name.lower()
    s = s.replace("&", " and ").replace("+", " plus ")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s

ENTRIES = []

def add(display, tab, group, **kw):
    e = {
        "id": kw.pop("id", None) or sid(display),
        "display_name": display,
        "placements": [{"tab": tab, "group": group}],
        "category": kw.pop("category"),
        "state_changing": kw.pop("state_changing", True),
        "dose_required": kw.pop("dose_required", False),
        "turnaround_class": kw.pop("turnaround_class", None),
        "narration_template": kw.pop("narration_template", None),
        "default_prerequisites": kw.pop("default_prerequisites", []),
        "flags_set_default": kw.pop("flags_set_default", []),
    }
    e.update(kw)
    ENTRIES.append(e)

# ---------------------------------------------------------------- prerequisites
# Derived from system-design-v2.md section 6.1 -- the only three prerequisites
# the design puts in scope. Written in the five-predicate condition language.
PRE_VASCULAR = [{
    "when": "flag iv_access set OR flag central_access set OR flag io_access set",
    "failure_message": "No line in {him} yet. Do you want me to get IV access first?",
    "source": "derived",
}]
PRE_RSI = [{
    "when": "flag sedation_given set AND flag paralytic_given set",
    "failure_message": "{He's} not sedated or paralyzed yet. We need induction and a paralytic before we tube {him}.",
    "source": "system-design-v2.md 6.1",
}]
PRE_PADS = [{
    "when": "flag pacing_pads_placed set",
    "failure_message": "Pads aren't on {him} yet. Want me to get them on?",
    "source": "system-design-v2.md 6.1",
}]
PRE_LP = [{
    "when": "flag lumbar_puncture_performed set",
    "failure_message": "We haven't done the LP, so there's no CSF to send.",
    "source": "system-design-v2.md 6.1",
}]

# ============================================================== EXAMS (image 1)
EXAMS = [
    ("AIRWAY", "Perform Airway Exam"), ("BREATH", "Perform Breathing Exam"),
    ("CIRC", "Perform Circulation Exam"), ("HEENT", "Perform HEENT Exam"),
    ("NECK", "Perform Neck Exam"), ("CARD", "Perform Cardiovascular Exam"),
    ("PULM", "Perform Pulmonary Exam"), ("ABD", "Perform Abdominal Exam"),
    ("GU", "Perform Genitourinary Exam"), ("BACK", "Perform Back/Flank Exam"),
    ("MSK", "Perform Musculoskeletal Exam"), ("SKIN", "Perform Skin Exam"),
    ("NEURO", "Perform Neurological Exam"), ("PSYCH", "Perform Psychological Exam"),
]
# v0.26, author instruction (11 October 2026): airway, breathing and circulation are
# examined together, from the Stabilization tab. The three entries stay exactly as they
# were, so every case's findings, tags and expectations keep working, and they stay on
# the exam tab for the debrief's Physical row. They are hidden from the menus and search
# (`menu_hidden`), and one composite entry performs all three in one press (`performs`).
# The interface logs the three constituents, never the composite, so a case binds and
# tags the constituents and never `exam_abc`.
ABC_EXAMS = {"AIRWAY", "BREATH", "CIRC"}
for code, display in EXAMS:
    kw = {"menu_hidden": True} if code in ABC_EXAMS else {}
    add(display, "exam", None, category="exam",
        id="exam_" + code.lower(),
        state_changing=False, short_code=code,
        narration_template=None,  # section 7.1: exams are not narrated
        repeatable=True, **kw)
add("Airway, Breathing and Circulation Exam", "stabilization", None, category="exam",
    id="exam_abc", state_changing=False, short_code="ABC", narration_template=None,
    repeatable=True, performs=["exam_airway", "exam_breath", "exam_circ"],
    source="author-supplied, not in screenshots (v0.26)")

# ================================================ STABILIZATION (images 2-4)
STAB_TOP = ["Insert IV", "Attach Monitor", "Start Chest Compressions"]
for d in STAB_TOP:
    # v0.26, author instruction: chest compressions sit with the nursing acts.
    add(d, "stabilization", "Nursing" if d == "Start Chest Compressions" else None,
        category="stabilization")

# Attaching the monitor is what puts numbers on the screen. Before it, the
# simulator shows no vitals and plays no heartbeat, because the resident has no
# monitor to read them from. That is a property of the act, not of any case, so
# it lives here rather than in a case file. It is a capability flag, not a
# clinical judgment: it says the act reveals the numbers, and says nothing
# about whether attaching the monitor was the right thing to do.

STAB = {
    "Oxygen": ["Nasal Cannula Oxygen", "Non-Rebreather Mask",
               "Non-Invasive Positive Pressure Ventilation", "Bag Valve Mask"],
    # Volume and agent are both explicit. A generic "crystalloid bolus" hid the
    # choice a resident actually makes, and it also made a harmful tag easy to
    # under-cover: tagging one entry left the others as a route to the same harm.
    # equivalence_groups below records that the four are interchangeable where a
    # case only requires "some crystalloid".
    "Fluids": ["Normal Saline 1L bolus", "Normal Saline 500mL bolus",
               "Lactated Ringer's 1L bolus", "Lactated Ringer's 500mL bolus",
               "D5 NS bolus", "D5 1/2 NS infusion",
               "Normal Saline infusion", "Lactated Ringer's infusion"],
    "Pacer/Defib": ["Defibrillate", "Cardiac Pacing", "Synchronized Cardioversion",
                    "Unsynchronized Cardioversion", "Place Pads for Monitoring"],
    # v0.26b: the pads entry is renamed and shown in the top Stabilization folder too.
    # See the v0.26 layout block below.
    "Vascular Access": ["Second IV", "Central Venous Catheter (triple lumen)",
                        "Central Venous Catheter (cordis)", "Intraosseous Line",
                        "Arterial Line"],
    "Intubation": ["Position for Intubation", "Prepare Endotracheal Tube", "Suction",
                   "Preoxygenate for Intubation", "Intubate (Rapid Sequence)",
                   "Cricothyrotomy"],
    "Intubation Drugs": ["Lidocaine bolus", "Midazolam bolus", "Etomidate bolus",
                         "Ketamine bolus", "Propofol bolus", "Succinylcholine bolus",
                         "Rocuronium bolus", "Phenylephrine bolus"],
    # Author-supplied, not transcribed from a screenshot. Recorded in
    # resolved_since_v0.1_draft below so the provenance stays visible. These are
    # nursing acts a resident orders and the nurse performs: they change the state
    # of the room rather than of the patient, so each one sets a flag and none of
    # them carries a result, a turnaround or a vital effect. Whether isolation was
    # indicated, and whether warming or cooling helped, is a case's judgment to
    # make through its tags.
    "Nursing": ["Droplet Precautions", "Contact Precautions", "Airborne Precautions",
                "Warming Measures", "Cooling Measures"],
}
for group, items in STAB.items():
    for d in items:
        kw = dict(category="stabilization")
        if group == "Fluids":
            kw.update(dose_required=True, default_prerequisites=PRE_VASCULAR,
                      narration_template="Hanging {dose} of {name}.")
        if group == "Intubation Drugs":
            kw.update(dose_required=True, default_prerequisites=PRE_VASCULAR,
                      narration_template="Giving {dose} of {name}.")
            # v0.18a. The intubation prerequisite asks for these two flags and until now no
            # catalog entry set them, so a case that did not author them could never intubate.
            if d in ("Midazolam bolus", "Etomidate bolus", "Ketamine bolus", "Propofol bolus"):
                kw.update(flags_set_default=["sedation_given"])
            if d in ("Succinylcholine bolus", "Rocuronium bolus"):
                kw.update(flags_set_default=["paralytic_given"])
        if d == "Intubate (Rapid Sequence)":
            kw.update(default_prerequisites=PRE_RSI, flags_set_default=["intubated"])
        if d == "Cardiac Pacing":
            kw.update(default_prerequisites=PRE_PADS)
        if d == "Place Pads for Monitoring":
            kw.update(flags_set_default=["pacing_pads_placed"])
        if d == "Insert IV" or d == "Second IV":
            kw.update(flags_set_default=["iv_access"])
        if group == "Nursing":
            kw.update(flags_set_default=[sid(d)], repeatable=True,
                      narration_template="{name} are in place.")
        add(d, "stabilization", group, **kw)

# add flags to top-level stabilization entries that need them
for e in ENTRIES:
    if e["id"] == "insert_iv":
        e["flags_set_default"] = ["iv_access"]
    if e["id"] == "attach_monitor":
        e["reveals_vitals"] = True
    if e["id"] == "central_venous_catheter_cordis" or e["id"] == "central_venous_catheter_triple_lumen":
        e["flags_set_default"] = ["central_access"]
    if e["id"] == "intraosseous_line":
        e["flags_set_default"] = ["io_access"]

# ============================================== INVESTIGATIONS (images 5-9)
BEDSIDE = ["Doppler", "ECG", "Fingerstick Blood Sugar", "Peak Expiratory Flow Meter",
           "Ultrasound - Aorta", "Ultrasound - Cardiac", "Ultrasound - FAST",
           "Ultrasound - Lower Extremity Venous", "Ultrasound - Lung",
           "Ultrasound - Renal", "Ultrasound - RUQ", "Ultrasound - Soft Tissue"]
LABS = ["Arterial Blood Gas", "Venous Blood Gas", "Basic Chemistry (Chem 7)",
        "Beta-Hydroxybutyrate", "Blood Type & Screen",
        "Calcium (ionized)", "Calcium Level", "Coagulation Panel",
        "Complete Blood Count (CBC)", "D-Dimer", "Lactate", "Lipase",
        "Liver Function Tests (LFTs)", "Magnesium Level", "Phosphate Level",
        "Plasma Procalcitonin", "NT-proBNP", "Troponin-T", "Urinalysis"]
OTHER_LABS = ["Acetaminophen Level", "Amylase", "Blood Culture x 2",
              "C-reactive Protein (CRP)", "COVID-19 test", "Creatine Kinase (CK)",
              "CSF Cell Count", "CSF Culture", "CSF Glucose", "CSF Gram Stain",
              "CSF Protein", "CSF Rapid Antigen Test for N. meningitidis",
              "Erythrocyte Sedimentation Rate (ESR)", "Ethanol Level (EtOH)",
              "Influenza A&B Antigen Test", "Lactate dehydrogenase (LDH)",
              "Osmolality", "Peripheral smear", "Salicylate (Aspirin) Level",
              "Serum HCG (quantitative)", "TSH",
              "Uric Acid", "Urine Culture", "Urine HCG (qualitative)",
              "Urine Rapid Antigen Test for N. meningitidis",
              "Urine Rapid Antigen Test for S. pneumoniae", "Urine Tox Screen"]
IMAGING = ["CT - Abdomen", "CT - Aorta", "CT - C-spine", "CT - Chest", "CT - Head",
           "CT - Pulmonary Embolus", "CT/CTA - Head and Neck", "MRI - C-spine",
           "MRI - Lumbar Spine", "MRI - Thoracic Spine", "MRI/MRA - Head and Neck",
           "XR - Chest", "XR - Pelvis"]
# A plain film is not a cross-sectional study and does not wait like one: it is shot at the
# bedside and is on the screen while the patient is still in the room, where a CT means
# leaving the department. They shared one turnaround class and therefore one delay, which
# made a chest film feel like a trip to the scanner. Radiographs now resolve with the
# labs, and cross-sectional imaging keeps the longer wait.
RADIOGRAPH = {"XR - Chest", "XR - Pelvis"}

for d in BEDSIDE:
    tc = "ecg" if d == "ECG" else "bedside"
    add(d, "investigations", "Bedside Tests", category="investigation",
        id="ecg_12_lead" if d == "ECG" else sid(d),
        turnaround_class=tc, repeatable=True,
        narration_template="{name} is up." )
for d in LABS:
    # v0.23. Beta-Hydroxybutyrate was added on author instruction, not from a screenshot.
    kw = {"source": "author-supplied, not in screenshots (v0.23)"} if d == "Beta-Hydroxybutyrate" else {}
    add(d, "investigations", "Lab Work", category="investigation",
        turnaround_class="lab", repeatable=True,
        narration_template="Sending {name}.", **kw)
for d in OTHER_LABS:
    kw = {}
    if d.startswith("CSF"):
        kw["default_prerequisites"] = PRE_LP
    add(d, "investigations", "Other Labs", category="investigation",
        turnaround_class="lab", repeatable=True,
        narration_template="Sending {name}.", **kw)
for d in IMAGING:
    add(d, "investigations", "Imaging", category="investigation",
        turnaround_class="radiograph" if d in RADIOGRAPH else "imaging", repeatable=True,
        narration_template="{name} is ordered.")

# ================================================ INTERVENTIONS (images 10-20)
PROCEDURES = ["Arterial Line", "C-Collar", "Central Venous Catheter (cordis)",
              "Central Venous Catheter (triple lumen)",
              "Decontaminate (Hazmat activation)", "Don Personal Protective Equipment",
              "Insert Chest Tube", "Insert Foley Catheter", "Lower Head of Bed",
              "Lumbar Puncture", "Place Nasogastric Tube", "Place Orogastric Tube",
              "Place Patient on Isolation Precautions",
              "Remove Vaginal Foreign Body",
              "Whole Bowel Irrigation by NG tube"]
BLOOD_BANK = ["Factor IX", "Factor VIII", "Intravenous Immunoglobulin",
              "Prothrombin Complex Concentrate", "Transfuse FFP",
              "Transfuse Platelets", "Transfuse pRBC"]
MEDS = {
    "Meds - Resuscitation": ["Alteplase (tPA)", "Atropine bolus", "Epinephrine bolus",
                             "Vasopressin bolus"],
    "Meds - Vasoactive Agents": ["Dopamine drip", "Epinephrine drip", "Esmolol drip",
                                 "Labetalol bolus", "Labetalol drip", "Nicardipine drip",
                                 "Nitroglycerin drip", "Nitroprusside drip",
                                 "Norepinephrine drip", "Phenylephrine drip",
                                 "Vasopressin drip"],
    "Meds - Sedation/Analgesia": ["Acetaminophen", "Etomidate bolus", "Fentanyl bolus",
                                  "Ibuprofen", "Ketamine bolus", "Ketamine infusion",
                                  "Lorazepam bolus", "Morphine bolus", "Propofol bolus",
                                  "Propofol infusion"],
    "Meds - Cardiac": ["Adenosine bolus", "Amiodarone bolus/infusion", "Aspirin",
                       "Atorvastatin", "Clopidogrel", "Diltiazem bolus",
                       "Heparin bolus/drip", "Metoprolol bolus", "Nitroglycerin",
                       "Procainamide drip", "Propranolol bolus",
                       "Tenecteplase (TNK) bolus"],
    "Meds - Respiratory": ["Albuterol", "Ipratropium"],   # INCOMPLETE, see known_gaps
    "Meds - Intubation": ["Etomidate bolus", "Ketamine bolus", "Lidocaine bolus",
                          "Midazolam bolus", "Phenylephrine bolus", "Propofol bolus",
                          "Rocuronium bolus", "Succinylcholine bolus"],
    "Meds - Gastrointestinal": ["Esomeprazole bolus", "Famotidine bolus", "Glucagon",
                                "Metoclopramide", "Octreotide bolus/infusion",
                                "Ondansetron"],
    "Meds - Antibiotics": ["Acyclovir", "Amoxicillin", "Amphotericin", "Ampicillin",
                           "Azithromycin", "Aztreonam", "Cefazolin", "Cefepime",
                           "Cefotaxime", "Ceftriaxone", "Chloramphenicol",
                           "Ciprofloxacin", "Clindamycin", "Doxycycline", "Fluconazole",
                           "Gentamicin", "Levofloxacin", "Meropenem", "Metronidazole",
                           "Minocycline", "Moxifloxacin", "Oseltamivir", "Penicillin G",
                           "Piperacillin-tazobactam", "Rifampin", "Vancomycin"],
    "Meds - OB/GYN": ["Methergine", "Misoprostol", "RhoGAM", "Oxytocin IM/IV"],
    "Meds - Allergy": ["Dexamethasone", "Diphenhydramine", "Epinephrine (Intramuscular)",
                       "Methylprednisolone bolus", "Prednisone"],
    "Meds - Tox": ["Activated Charcoal", "Digoxin immune Fab", "Flumazenil", "Fomepizole",
                   "Intralipid", "N-acetylcysteine", "Na-Bicarbonate bolus",
                   "Na-Bicarbonate infusion", "Naloxone bolus", "Pralidoxime (2-PAM)",
                   "Thiamine"],
    "Meds - Psych": ["Haloperidol", "Olanzapine", "Ziprasidone"],
    "Meds - Miscellaneous": ["Calcium Chloride bolus", "Colchicine", "D50 bolus",
                             "fos-Phenytoin", "Furosemide 40 mg IV", "Hydrocortisone bolus",
                             "Hypertonic saline (25%) bolus",
                             "Hypertonic saline (3%) infusion", "Insulin bolus",
                             "Insulin drip", "Levetiracetam bolus",
                             "Magnesium Sulfate bolus", "Mannitol bolus",
                             "Potassium Chloride (KCl)", "Potassium Iodide & Iodine",
                             "Propylthiouracil", "TDaP", "Tranexamic acid"],
}

# Author-supplied addition: present in the reference case but not in any screenshot.
#
# The three anticoagulant and rate-control entries added for the atrial fibrillation
# case are author instruction, not transcription. Each was requested by name for a case
# where the alternatives the screenshots do carry are the wrong drug: digoxin because a
# non-dihydropyridine calcium channel blocker is contraindicated in reduced systolic
# function and the catalog offered no agent that is not, apixaban because the catalog
# held heparin as the only anticoagulant, and enoxaparin for the same reason. They carry
# source=author-supplied so a reader can see they were not seen in the interface.
AUTHOR_ADDED = {"Meds - Vasoactive Agents": ["Dobutamine drip"],
                "Meds - Cardiac": ["Nitroglycerin sublingual", "Digoxin bolus",
                                   "Apixaban", "Enoxaparin", "Magnesium Sulfate"],
                # v0.9, author instruction (Kelly Medwid case, via Aakash Setty,
                # 5 September 2026): physostigmine, the anticholinergic antidote. The
                # catalog held every other tox antidote a resident might reach for and
                # not this one, which made a diphenhydramine case unauthorable: the
                # lesson is what happens when it is given to a patient whose QRS is
                # already wide, and an action a case cannot offer is an action no
                # learner can get wrong. Placed under Meds - Tox beside the other
                # antidotes. The catalog holds no appropriateness judgment about it,
                # exactly as it holds none about naloxone or flumazenil.
                "Meds - Tox": ["Physostigmine"],
                # v0.9, author instruction: magnesium sulfate as an ordinary intravenous
                # medication (not the "bolus" entry, which stays) placed under every
                # group where a resident would look for it: severe asthma under
                # Respiratory, prolonged QT and torsades under Cardiac, repletion under
                # Miscellaneous, pre-eclampsia and eclampsia under OB/GYN. One id,
                # four placements.
                "Meds - Respiratory": ["Magnesium Sulfate"],
                # v0.23, author instruction (Aakash Setty, 6 October 2026) for the
                # diabetic ketoacidosis case: subcutaneous rapid-acting insulin, which the
                # 2024 consensus report accepts for mild and moderate ketoacidosis, and
                # oral potassium, so that the route of potassium is a choice a learner
                # makes. Both are in NON_IV. The existing "Potassium Chloride (KCl)" entry
                # is unchanged and a case that means the intravenous route says so.
                # v0.23a, author instruction (6 October 2026): insulin glargine, so the
                # basal dose the patient missed can be ordered. Subcutaneous, in NON_IV.
                "Meds - Miscellaneous": ["Magnesium Sulfate", "Insulin (Subcutaneous)",
                                         "Insulin Glargine (Subcutaneous)",
                                         "Potassium Chloride (oral)"],
                "Meds - OB/GYN": ["Magnesium Sulfate"]}
for g, items in AUTHOR_ADDED.items():
    MEDS.setdefault(g, [])
    MEDS[g] = sorted(set(MEDS[g] + items))

# Default failure messages carry pronoun tokens ({He's}, {him}) rather than a sex, because
# one catalog serves every case and most packs have a woman on the bed. They
# are substituted at bind time from patient.sex; see PRONOUNS and pron() in engine.js. Until
# v0.11 these said "he", and the packs that noticed worked around it by authoring a
# prerequisite override on every intravenous action, which is why MGCA carries about forty
# near-identical failure messages whose only difference from this one is a pronoun.
#
# Write these so that no bare subject pronoun is followed by a present-tense verb, because
# the fallback for a case that states no sex is singular they and "they doesn't" is not a
# sentence. Hence "No line in {him} yet" rather than "{He} hasn't got a line in yet".

# Routes that do not need vascular access. DERIVED, not transcribed: the
# screenshots carry no route information. Author confirmation required.
NON_IV = {"Prednisone", "Epinephrine (Intramuscular)", "Activated Charcoal",
          "Colchicine", "Propylthiouracil", "TDaP", "Potassium Iodide & Iodine",
          "Aspirin", "Atorvastatin", "Clopidogrel", "Misoprostol", "Methergine",
          "Albuterol", "Ipratropium", "Nitroglycerin sublingual",
          # Apixaban is oral and enoxaparin is subcutaneous. Neither needs a line, and
          # gating either on vascular access would teach a sequence that does not exist.
          "Apixaban", "Enoxaparin",
          # v0.23. Subcutaneous insulin and oral potassium need no line.
          "Insulin (Subcutaneous)", "Potassium Chloride (oral)",
          "Insulin Glargine (Subcutaneous)"}
ROUTE_AMBIGUOUS = {"Acetaminophen", "Ibuprofen", "Dexamethasone", "Diphenhydramine",
                   "Ondansetron", "Metoclopramide", "Thiamine", "Oxytocin IM/IV",
                   "RhoGAM", "Haloperidol", "Olanzapine", "Ziprasidone",
                   "Potassium Chloride (KCl)", "N-acetylcysteine", "Oseltamivir",
                   "Amoxicillin", "Doxycycline", "Minocycline", "Rifampin",
                   # v0.18a. Each has a standard route that needs no line (intramuscular or
                   # intranasal naloxone, intramuscular glucagon for hypoglycemia,
                   # intramuscular hydrocortisone in adrenal crisis), so gating them on IV
                   # access taught a delay that does not exist.
                   "Naloxone bolus", "Glucagon", "Hydrocortisone bolus"}
INDEX = {e["id"]: e for e in ENTRIES}

def add_or_place(display, tab, group, **kw):
    """Same drug can appear under several tabs; one id, several placements."""
    i = sid(display)
    if i in INDEX:
        INDEX[i]["placements"].append({"tab": tab, "group": group})
        return
    add(display, tab, group, **kw)
    INDEX[ENTRIES[-1]["id"]] = ENTRIES[-1]

for d in PROCEDURES:
    kw = dict(category="procedure", narration_template="{name} done.")
    if d == "Lumbar Puncture":
        kw["flags_set_default"] = ["lumbar_puncture_performed"]
    if d == "Remove Vaginal Foreign Body":
        # v0.21. Added on author instruction for the toxic shock case, not from a screenshot.
        # Source control had no button: a retained tampon could be found on the GU exam and
        # then not acted on. Named for the act, not for the object, so it reads the same in
        # every case and gives nothing away in the cases where there is nothing to remove.
        # The default line states the outcome. A procedure has no result, so a case that
        # does not bind this action would otherwise leave the learner waiting for one.
        # A case with something to remove overrides the line.
        kw["narration_template"] = "Speculum exam done. There is nothing to remove."
        kw["source"] = "author-supplied, not in screenshots (v0.21)"
    add_or_place(d, "interventions", "Procedures", **kw)
for d in BLOOD_BANK:
    add_or_place(d, "interventions", "Blood Bank", category="blood_product",
                 dose_required=True, default_prerequisites=PRE_VASCULAR,
                 narration_template="Hanging {dose} of {name}.")
for group, items in MEDS.items():
    for d in items:
        infusion = any(w in d.lower() for w in ("drip", "infusion"))
        if d in NON_IV:
            route, pre = "non_iv", []
        elif d in ROUTE_AMBIGUOUS:
            route, pre = "unspecified", []
        else:
            route, pre = ("infusion" if infusion else "iv_bolus"), PRE_VASCULAR
        add_or_place(d, "interventions", group, category="medication",
                     dose_required=True,
                     route_class=route,
                     default_prerequisites=pre,
                     narration_template=("Starting {name} at {dose}." if infusion
                                         else "Giving {dose} of {name}."))
        if infusion:
            INDEX[sid(d)]["persistent"] = True   # author: drips stay running once started
        if d == "Hypertonic saline (25%) bolus":
            # v0.18a. Concentrated saline (23.4 percent is the product sold) is given through
            # a central line; a peripheral or intraosseous line is not an acceptable route.
            INDEX[sid(d)]["default_prerequisites"] = [{
                "when": "flag central_access set",
                "failure_message": "That concentration has to go through a central line. Do you want one placed?",
                "source": "derived: concentrated sodium chloride is a central-line drug"}]
        if d in AUTHOR_ADDED.get(group, []):
            INDEX[sid(d)]["source"] = "author-supplied, not in screenshots"

# The route sits in parentheses in these three display names, and the engine does not
# lower a token in parentheses, so the standard template read "Giving insulin
# (Subcutaneous)." Each gets a line that says the route in words.
INDEX["insulin_subcutaneous"]["narration_template"] = "Giving {dose} of subcutaneous insulin."
INDEX["insulin_glargine_subcutaneous"]["narration_template"] = "Giving {dose} of subcutaneous insulin glargine."
INDEX["potassium_chloride_oral"]["narration_template"] = "Giving {dose} of oral potassium chloride."

# The four-group magnesium entry carries the indications it was added for, so the
# catalog says why a repletion drug sits under OB/GYN. Nothing clinical is scored here.
INDEX["magnesium_sulfate"]["source"] = "author-supplied, not in screenshots (v0.9)"
# Not a push. Asthma, torsades, repletion and pre-eclampsia all give it over minutes to
# an hour, so the route is a timed infusion that completes rather than a bolus or a
# persistent drip that would need a stop action.
INDEX["magnesium_sulfate"]["route_class"] = "iv_timed_infusion"
INDEX["magnesium_sulfate"]["indications_note"] = (
    "Placed under Respiratory (severe asthma), Cardiac (prolonged QT, torsades de pointes), "
    "Miscellaneous (repletion) and OB/GYN (pre-eclampsia, eclampsia). Dose and rate are the "
    "case's to author; the catalog holds no appropriateness judgment.")

# ================================================ STOP ACTIONS
# Infusions are persistent: once started they run for the rest of the case. Without a
# way to stop one, any deterioration branch whose rescue is "turn the drip off" has no
# exit and the patient cannot be rescued. One stop action per persistent infusion.
def soft_lower(name):
    """The engine's softLower, restated. Only ordinary Title Case words are lowered. A word
    with a digit, an inner capital, a slash or a parenthesis is a unit, an acronym or a name."""
    return " ".join(w.lower() if re.fullmatch(r"[A-Z][a-z]+(-[A-Z][a-z]+)*", w) else w
                    for w in name.split(" "))

def stop_line(base):
    """The nurse's line for a stop action. It names the drug and nothing else, so the
    "bolus/infusion" in a combined entry's name is dropped and "Na-" keeps its capital."""
    drug = re.sub(r" bolus/(infusion|drip)$", "", base)
    drug = " ".join(w if w.startswith("Na-") else soft_lower(w) for w in drug.split(" "))
    return "Stopping the " + drug + "."

STOPPABLE = [e for e in ENTRIES if e.get("persistent") and e["category"] == "medication"]
for e in STOPPABLE:
    base = e["display_name"]
    for suffix in (" drip", " infusion"):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    add(f"Stop {base}", *[p["tab"] for p in e["placements"]][:1],
        e["placements"][0].get("group"),
        category="medication",
        state_changing=True,
        repeatable=False,
        dose_required=False,
        route_class="none",
        # The drug is written into the line. "{name}" would be this entry's own name, which
        # starts with "Stop", and the nurse said "Stopping the stop insulin."
        narration_template=stop_line(base),
        stops=e["id"],
        source="derived: every persistent infusion needs a way to withdraw it")

# ================================================ CONSULTATIONS (image 5, batch 2)
CONSULTS = ["Consult Cardiology", "Consult Endocrinology", "Consult Gastroenterology",
            "Consult General Surgery", "Consult Heme/Onc", "Consult Infectious Disease",
            "Consult Neurology", "Consult Neurosurgeon", "Consult OB/GYN",
            "Consult Orthopedics", "Consult Psychiatry",
            "Consult Public Health Authorities", "Consult Pulmonology",
            "Consult Critical Care", "Consult Renal", "Consult Toxicology",
            "Consult Vascular Surgery"]
for d in CONSULTS:
    add(d, "consultations", "Consultations", category="consultant",
        # Design 5.1: most consults are observational; a consult that unlocks a
        # disposition or intervention is state-changing and sets a flag. That is a
        # per-case decision, so the catalog default is observational.
        state_changing=False,
        state_changing_overridable=True,
        repeatable=True,
        narration_template="Paging {name}.",
        default_response="global unrelated-consultant response (design section 3)")

# ---- v0.26 layout, author instruction (11 October 2026) ----
# Placement only. No id, result, turnaround or prerequisite changes, so no case changes.
# A placement may carry `subgroup`: the interface draws a group's subgroups as headings
# inside the one folder, or as sub-tabs where the build lists the group in subgroupTabs.
#   Intubation and Intubation Drugs are one folder, with the drugs under Medications.
#   Imaging is split into CT, X-ray, Ultrasound and MRI, and the bedside ultrasounds move
#   into it from Bedside Tests. Doppler stays a bedside test.
def _imaging_subgroup(e):
    i = e["id"]
    if i.startswith("ct_"): return "CT"
    if i.startswith("xr_"): return "X-ray"
    if i.startswith("ultrasound_"): return "Ultrasound"
    if i.startswith("mri_"): return "MRI"
    raise SystemExit("imaging entry with no subgroup: " + i)
# v0.26b, author instruction (11 October 2026): the pads are named "Place Defibrillator
# Pads" and sit in the top Stabilization folder, where they order on a click, and stay
# under Pacer/Defib as well. Same id, same flag (pacing_pads_placed), so no case changes.
for e in ENTRIES:
    if e["id"] == "place_pads_for_monitoring":
        e["display_name"] = "Place Defibrillator Pads"
        e["placements"] = [{"tab": "stabilization", "group": None},
                           {"tab": "stabilization", "group": "Pacer/Defib"}]
        e["source"] = "renamed and placed on author instruction (v0.26b); was 'Place Pads for Monitoring'"
for e in ENTRIES:
    p = e["placements"][0]
    if p["tab"] == "stabilization" and p["group"] == "Intubation Drugs":
        p["group"], p["subgroup"] = "Intubation", "Medications"
    elif p["tab"] == "investigations" and p["group"] == "Bedside Tests" \
            and e["id"].startswith("ultrasound_"):
        p["group"] = "Imaging"
    if p["tab"] == "investigations" and p["group"] == "Imaging":
        p["subgroup"] = _imaging_subgroup(e)

# ---- v0.26c, author instruction (11 October 2026): labs by tube and source ----
# Lab Work and Other Labs become one Lab Work folder, sectioned by what is drawn or
# collected: blood by tube top, blood gas, blood cultures, CSF, urine, point of care, other.
# Fingerstick glucose moves in from Bedside Tests as point of care. Placement only.
# THE TUBE ASSIGNMENTS ARE NOT PHYSICIAN REVIEWED and vary between laboratories (lactate on
# a gray top or the gas, chemistry on green or gold). They follow common US practice.
S_LAV, S_BLUE = "Blood, lavender or pink top (EDTA)", "Blood, light blue top (citrate)"
S_CSF, S_URINE, S_POC, S_OTHER = "CSF", "Urine", "Point of care", "Other"
# Author instruction, same day: gold top folded into green; blood gas, blood cultures, the
# gray-top tests (lactate, ethanol) and the skin biopsy together under Other.
S_GREEN = "Blood, green top (lithium heparin)"
S_GOLD = S_GREEN
S_GRAY = S_GAS = S_CULT = S_OTHER
LAB_SECTION = {
    # Author instruction, same evening: the two blood gases are point of care.
    "Arterial Blood Gas": S_POC, "Venous Blood Gas": S_POC, "Calcium (ionized)": S_GAS,
    "Basic Chemistry (Chem 7)": S_GREEN, "Beta-Hydroxybutyrate": S_GREEN,
    "Calcium Level": S_GREEN, "Lipase": S_GREEN, "Liver Function Tests (LFTs)": S_GREEN,
    "Magnesium Level": S_GREEN, "Phosphate Level": S_GREEN, "Plasma Procalcitonin": S_GREEN,
    "NT-proBNP": S_GREEN, "Troponin-T": S_GREEN, "Acetaminophen Level": S_GREEN,
    "Amylase": S_GREEN, "C-reactive Protein (CRP)": S_GREEN, "Creatine Kinase (CK)": S_GREEN,
    "Lactate dehydrogenase (LDH)": S_GREEN, "Salicylate (Aspirin) Level": S_GREEN,
    "Uric Acid": S_GREEN,
    "Blood Type & Screen": S_LAV, "Complete Blood Count (CBC)": S_LAV,
    "Erythrocyte Sedimentation Rate (ESR)": S_LAV, "Peripheral smear": S_LAV,
    "Coagulation Panel": S_BLUE, "D-Dimer": S_BLUE,
    "TSH": S_GOLD, "Serum HCG (quantitative)": S_GOLD, "Osmolality": S_GOLD,
    "Lactate": S_GRAY, "Ethanol Level (EtOH)": S_GRAY,
    "Blood Culture x 2": S_CULT,
    "CSF Cell Count": S_CSF, "CSF Culture": S_CSF, "CSF Glucose": S_CSF, "CSF Gram Stain": S_CSF,
    "CSF Protein": S_CSF, "CSF Rapid Antigen Test for N. meningitidis": S_CSF,
    "Urinalysis": S_URINE, "Urine Culture": S_URINE, "Urine HCG (qualitative)": S_URINE,
    "Urine Rapid Antigen Test for N. meningitidis": S_URINE,
    "Urine Rapid Antigen Test for S. pneumoniae": S_URINE, "Urine Tox Screen": S_URINE,
    "Fingerstick Blood Sugar": S_POC, "COVID-19 test": S_POC, "Influenza A&B Antigen Test": S_POC,
}
# The specimen, for the colour of each lab button's edge (author instruction, same day):
# blood dark red, blood gas light red, urine yellow, CSF gray, swabs green.
# Only the arterial gas is light red. Venous gas and ionized calcium are venous blood
# (author instruction, same evening).
GAS_LABS = {"Arterial Blood Gas"}
SWAB_LABS = {"COVID-19 test", "Influenza A&B Antigen Test"}
for e in ENTRIES:
    p = e["placements"][0]
    if p["tab"] != "investigations" or p["group"] not in ("Lab Work", "Other Labs", "Bedside Tests"):
        continue
    sec = LAB_SECTION.get(e["display_name"])
    if sec is None:
        if p["group"] == "Bedside Tests":
            continue
        raise SystemExit("lab with no section: " + e["display_name"])
    p["group"], p["subgroup"] = "Lab Work", sec
    d = e["display_name"]
    e["specimen"] = ("gas" if d in GAS_LABS else "swab" if d in SWAB_LABS
                     else "urine" if sec == S_URINE else "csf" if sec == S_CSF else "blood")

# ---- attach default normal findings to every exam ----
ex_missing, ex_orphan = [], set(EXAM_DEFAULTS)
for e in ENTRIES:
    if e["category"] != "exam":
        continue
    d = EXAM_DEFAULTS.get(e["id"])
    if d is None:
        ex_missing.append(e["id"])
    else:
        e["default_result"] = d
        ex_orphan.discard(e["id"])
if ex_missing:
    raise SystemExit("exams with no default findings: " + ", ".join(ex_missing))
if ex_orphan:
    raise SystemExit("exam defaults with no catalog entry: " + ", ".join(sorted(ex_orphan)))

# ---- attach default (normal) results to every printed-output investigation ----
missing, orphan = [], set(DEFAULTS)
for e in ENTRIES:
    if e["category"] != "investigation":
        continue
    d = DEFAULTS.get(e["id"])
    if d is None:
        missing.append(e["id"])
    else:
        e["default_result"] = d
        orphan.discard(e["id"])
if missing:
    raise SystemExit("investigations with no default_result: " + ", ".join(missing))
if orphan:
    raise SystemExit("default_results with no catalog entry: " + ", ".join(sorted(orphan)))

CATALOG = {
    # 0.3-draft: five entries added since 0.2-draft (v0.21 to v0.23a), default narration fixed
    # for the stop actions and the three route-named drugs. A binding file records the
    # version it was bound against.
    "catalog_version": "0.3-draft",
    "result_resolution_order": [
        "1. case study_results[<action_id>] for the current phase, if authored",
        "2. entry.default_result in this catalog",
        "3. if neither exists, the study returns nothing and the validator errors",
    ],
    "default_result_contract": {
        "purpose": "A case authors only the studies that matter to it. Everything "
                   "else returns the catalog default so the resident can order "
                   "broadly without the author writing 70 normal panels.",
        "display": "Every component of a default_result is in range and carries "
                   "abnormal=false, so nothing renders red. A case that overrides "
                   "a value must set abnormal itself; the renderer does not "
                   "recompute in-range.",
        "freezing": "Defaults are subject to the same result-freezing rule as "
                    "authored results (design 5.2): a result displayed in one "
                    "phase does not silently change in the next.",
        "risk": "A normal default is not a neutral default. If an author forgets "
                "to write the troponin in an MI case, the resident is shown a "
                "normal troponin and taught the wrong thing. See "
                "recommended_validator_rules.",
    },
    "general_status_default": GENERAL_STATUS_DEFAULT,
    "exam_finding_routing": EXAM_ROUTING,
    "exam_set_is_closed": "The 14 exam entries are the complete set. No other "
                          "maneuver is available. Findings that belong to an "
                          "anatomic region with no maneuver are routed per "
                          "exam_finding_routing.",
    "recommended_validator_rules": [
        "WARN when a case names a study in critical_actions or in a transition "
        "condition but authors no result for it, since it will silently return "
        "normal.",
        "WARN when a case's correct diagnosis implies an abnormal study that the "
        "case has not authored. This cannot be checked automatically without "
        "clinical knowledge, so it is a human review checklist item, not a "
        "code rule.",
        "ERROR when an authored result overrides a default but omits abnormal.",
        "ERROR when a case authors an exam key that is not one of the 14 catalog exam ids.",
        "WARN when a case overrides exam_neuro with an altered level of consciousness but does not override general_status, or the reverse, since the two will contradict on screen.",
        "WARN when a case overrides serum hCG or urine hCG but not both.",
    ],
    # No version numbers here. They went stale twice. Each case records the document
    # versions it was authored against in its own authored_against block.
    "aligned_to": ["system-design-v2.md section 3",
                   "case-authoring-requirements.md section 7"],
    "status": "INCOMPLETE -- see known_gaps",
    "field_provenance": {
        "transcribed_from_screenshots": ["display_name", "placements.tab",
                                         "placements.group", "short_code"],
        "derived_by_convention": ["id (snake_case of display_name)",
                                  "reveals_vitals",
                                  "category", "state_changing", "dose_required",
                                  "route_class", "repeatable", "stoppable",
                                  "narration_template"],
        "derived_from_design_docs": ["turnaround_class (design 2.1/8.1)",
                                     "default_prerequisites (design 6.1)",
                                     "flags_set_default"],
        "not_present_and_not_invented": ["clinical appropriateness", "dose values",
                                         "normal result values", "consultant list"],
    },
    # Seconds from order to result, per class. These are compressions of clinical time and
    # the ratios are what carry meaning, not the absolute numbers: bedside is instant, a
    # tracing and a plain film come back while the resident is still working the patient,
    # and cross-sectional imaging is the one study that costs real waiting. The ECG dropped
    # from 10 to 5 with the radiographs, on Aakash Setty's instruction, 5 September 2026:
    # a twelve-lead in a resuscitation bay is handed over in well under a minute, and in a
    # case whose next decision depends on the QRS the wait was buying nothing.
    "turnaround_seconds_by_class": {"lab": 5, "radiograph": 5, "imaging": 10,
                                    "ecg": 5, "bedside": 0},
    "equivalence_groups": {
        "_note": "Sets of entries a case may treat as interchangeable. Where a case "
                 "requires or forbids the act rather than one specific agent, bind one "
                 "case action to the whole group with also_covers_group so the tag "
                 "applies to every route. A harmful tag on one member and not the "
                 "others leaves an escape hatch from the lesson.",
        "crystalloid_bolus": ["normal_saline_1l_bolus", "normal_saline_500ml_bolus",
                              "lactated_ringer_s_1l_bolus", "lactated_ringer_s_500ml_bolus"],
        "non_invasive_ventilation": ["non_invasive_positive_pressure_ventilation"],
        "loop_diuretic": ["furosemide_40_mg_iv"],
        "_anticoagulation_note": "There is deliberately no anticoagulation equivalence "
                                 "group. Apixaban, enoxaparin and a heparin infusion are "
                                 "interchangeable for the purpose of 'was this patient "
                                 "anticoagulated', but a case that teaches the choice "
                                 "between them scores them differently, and a group "
                                 "would flatten that into one tag. Cases requiring only "
                                 "the act should list all three as satisfiers instead.",
        "_insulin_and_potassium_note": "There is deliberately no insulin group and no potassium "
                                       "group. The route is the lesson in the ketoacidosis case.",
    },
    "resolved_since_v0.1_draft": [
        "Meds - Allergy, Tox, Psych, Miscellaneous transcribed from the second screenshot batch.",
        "Consultations tab transcribed; 16 entries added.",
        "Dobutamine drip added on author instruction; marked source=author-supplied, not in screenshots.",
        "CPAP and BiPAP collapsed into the single UI entry 'Non-Invasive Positive Pressure Ventilation' on author instruction.",
        "Stop actions added: every persistent infusion now has a matching stop entry, so a drip can be withdrawn and a rescue that depends on it is reachable.",
        "Venous Blood Gas added alongside the arterial gas.",
        "Consult Critical Care added; 17 consultants.",
        "Fluid boluses made explicit in agent and volume (NS and LR, 1L and 500mL). The generic crystalloid bolus is gone; see equivalence_groups.",
        "Bumetanide removed. Furosemide carries its dose in the display name.",
        "Catalog prerequisites rewritten with the mandatory trailing keyword so they parse in the section 4 grammar.",
        "Nitroglycerin sublingual added as a separate route variant on author instruction.",
        "Digoxin bolus, Apixaban and Enoxaparin added to Meds - Cardiac on author "
        "instruction for the atrial fibrillation case. Not transcribed from any "
        "screenshot; each carries source=author-supplied. Apixaban and enoxaparin are "
        "in NON_IV, so neither requires vascular access.",
        "Beta-Hydroxybutyrate added under Lab Work, and Insulin (Subcutaneous) and Potassium "
        "Chloride (oral) under Meds - Miscellaneous, on author instruction for the diabetic "
        "ketoacidosis case (v0.23). Not from a screenshot. All three carry "
        "source=author-supplied. The two drugs need no vascular access.",
        "Insulin Glargine (Subcutaneous) added under Meds - Miscellaneous on author instruction "
        "(v0.23a), so a missed basal dose can be ordered. Not from a screenshot. No vascular access.",
        "Remove Vaginal Foreign Body added under Procedures on author instruction for the toxic "
        "shock case (v0.21). Not from a screenshot; carries source=author-supplied. It is inert "
        "in every case that does not bind it.",
        "Nursing group added under Stabilization on author instruction, not from a screenshot: "
        "droplet, contact and airborne precautions, warming measures and cooling measures. "
        "Each sets a flag of its own name and asserts nothing clinical.",
        "attach_monitor carries reveals_vitals. The interface shows no vitals and plays no "
        "heartbeat until an action carrying this flag has been taken.",
        "Physostigmine added to Meds - Tox on author instruction for the diphenhydramine "
        "case. Not transcribed from any screenshot; carries source=author-supplied. It is "
        "an intravenous push and is not in NON_IV, so it inherits the vascular-access "
        "prerequisite like every other intravenous drug.",
        "Skin Biopsy of the Rash removed on author instruction (11 October 2026): not used in "
        "this simulator. MGCA and TSS no longer reference it.",
        "v0.26 layout on author instruction (11 October 2026), placement only: airway, "
        "breathing and circulation exams hidden from the menus and performed together by the "
        "composite exam_abc on Stabilization; Start Chest Compressions moved to Nursing; "
        "Intubation Drugs folded into Intubation under the subgroup Medications; Imaging "
        "split into the subgroups CT, X-ray, Ultrasound and MRI, with the bedside "
        "ultrasounds moved into it. No ids, results or prerequisites changed.",
    ],
    "known_gaps": [
        "Meds - Respiratory truncated in screenshot: only Albuterol and Ipratropium visible, list continues.",
        "Meds - Antibiotics may continue past Vancomycin (alphabetical, screenshot cut at the V's).",
        "Lab Work may continue past Urinalysis (alphabetical, cut at the U's).",
        "Imaging list has no plain radiographs other than chest and pelvis; may be truncated.",
        "No Handoff tab / disposition options, required by design section 9.",
        "Default normal results were drafted by the AI from general knowledge, not from a laboratory reference. Ranges are assay- and institution-specific and are unverified. Entries carrying a 'verify' field are the ones known to vary in ways that change interpretation.",
        "Blood Type & Screen, serum hCG and urine hCG have defaults but are patient attributes rather than normal values. Defaulting to O positive and not pregnant is a silent assertion about every unauthored patient.",
        "Culture defaults read 'Cultures pending.' because the 5-second lab turnaround cannot represent a 24-48 hour culture. Cases whose teaching point is a positive culture cannot be authored honestly.",
        "Peak expiratory flow has no meaningful global normal, since predicted values depend on age, sex and height. Its default is a placeholder.",
        "ABG defaults assume room air. On supplemental oxygen the same numbers are abnormal, and nothing in the schema knows that.",
        "Dose behavior is not visible in the screenshots; dose_required is a guess per category and no dose values are recorded.",
        "route_class is derived, not transcribed. Entries marked 'unspecified' need author confirmation because the vascular-access prerequisite depends on it.",
        "Infusions are persistent=true. Stopping one is a separate action rather than a toggle, so a case must author the stop as its own step.",
        "Meds - Cardiac now holds both 'Nitroglycerin' (transcribed, route unspecified) and 'Nitroglycerin sublingual' (author-supplied). If the transcribed entry IS the sublingual one, these are duplicates and one must be removed.",
        "Remove Vaginal Foreign Body is offered for every patient, including men. The catalog has no sex filter.",
        "Meds - Miscellaneous now holds both 'Potassium Chloride (KCl)' (transcribed, route unspecified, no vascular access prerequisite) and 'Potassium Chloride (oral)' (author-supplied). The first is the intravenous one in practice. Until it is renamed and gated, a case that means the intravenous route must say so, as DKA does.",
        "No 250 mL crystalloid bolus. TAKO teaches 250 to 500 mL and can only offer 500.",
        "No action restarts a stopped infusion. DKA reads a second administration of insulin as the restart.",
        "No catheterization laboratory activation. TAKO carries it as a case-only action on the Consults tab, by physician decision.",
        "Venous Blood Gas and the five Nursing entries were added on author instruction and carry no source marker. field_provenance lists display_name as transcribed, which is not true of any author-supplied entry.",
        "Reference-case ids with still no catalog counterpart: bp_cycling_q5min, urine_output_monitoring, vent_settings_lung_protective, peep_reduce, handoff_submit. See reference_case_id_map.",
    ],
    "reference_case_id_map": {
        "_note": "Ids used in sim_check.py mapped to this catalog. 'unmatched' means "
                 "the case file assumes an action the UI does not offer.",
        "furosemide_iv": "furosemide_40_mg_iv",
        "dobutamine_infusion": "dobutamine_drip",
        "niv_bipap_cpap": "non_invasive_positive_pressure_ventilation",
        
        "cardiac_monitor": "attach_monitor",
        "crystalloid_bolus_1l": "equivalence group crystalloid_bolus (four entries)",
        "cxr_portable": "xr_chest (catalog does not distinguish portable)",
        "intubation_rsi": "intubate_rapid_sequence",
        "etomidate_iv": "etomidate_bolus",
        "rocuronium_iv": "rocuronium_bolus",
        "nitroglycerin_infusion": "nitroglycerin_drip",
        "norepinephrine_infusion": "norepinephrine_drip",
        "post_intubation_sedation_infusion": "propofol_infusion or ketamine_infusion",
        "consult_cardiology": "consult_cardiology",
        "iv_access_peripheral": "insert_iv",
        "nitroglycerin_stop": "stop_nitroglycerin",
        "bp_cycling_q5min": "unmatched",
        "urine_output_monitoring": "unmatched",
        "nitroglycerin_sublingual": "nitroglycerin_sublingual",
        "handoff_submit": "unmatched",
    },
    "entries": ENTRIES,
}

json.dump(CATALOG, sys.stdout, indent=2, ensure_ascii=False)
