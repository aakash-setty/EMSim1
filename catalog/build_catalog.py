#!/usr/bin/env python3
"""
Builds the global action catalog (system-design-v2.md section 3) from the UI
screenshots supplied by the author.

Every `display_name` and every `group` is transcribed verbatim from a screenshot.
Everything else -- ids, turnaround classes, state_changing, dose_required,
narration templates, default prerequisites -- is DERIVED and flagged as such in
`field_provenance`. Nothing clinical is asserted here: the catalog holds no
appropriateness judgement, per section 3 of the system design.

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
    "failure_message": "He doesn't have a line yet. Do you want me to get IV access first?",
    "source": "derived",
}]
PRE_RSI = [{
    "when": "flag sedation_given set AND flag paralytic_given set",
    "failure_message": "He isn't sedated or paralyzed yet. We need induction and a paralytic before we tube him.",
    "source": "system-design-v2.md 6.1",
}]
PRE_PADS = [{
    "when": "flag pacing_pads_placed set",
    "failure_message": "Pads aren't on him yet. Want me to get them on?",
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
for code, display in EXAMS:
    add(display, "exam", None, category="exam",
        id="exam_" + code.lower(),
        state_changing=False, short_code=code,
        narration_template=None,  # section 7.1: exams are not narrated
        repeatable=True)

# ================================================ STABILIZATION (images 2-4)
STAB_TOP = ["Insert IV", "Attach Monitor", "Start Chest Compressions"]
for d in STAB_TOP:
    add(d, "stabilization", None, category="stabilization")

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
    "Vascular Access": ["Second IV", "Central Venous Catheter (triple lumen)",
                        "Central Venous Catheter (cordis)", "Intraosseous Line",
                        "Arterial Line"],
    "Intubation": ["Position for Intubation", "Prepare Endotracheal Tube", "Suction",
                   "Preoxygenate for Intubation", "Intubate (Rapid Sequence)",
                   "Cricothyrotomy"],
    "Intubation Drugs": ["Lidocaine bolus", "Midazolam bolus", "Etomidate bolus",
                         "Ketamine bolus", "Propofol bolus", "Succinylcholine bolus",
                         "Rocuronium bolus", "Phenylephrine bolus"],
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
        if d == "Intubate (Rapid Sequence)":
            kw.update(default_prerequisites=PRE_RSI, flags_set_default=["intubated"])
        if d == "Cardiac Pacing":
            kw.update(default_prerequisites=PRE_PADS)
        if d == "Place Pads for Monitoring":
            kw.update(flags_set_default=["pacing_pads_placed"])
        if d == "Insert IV" or d == "Second IV":
            kw.update(flags_set_default=["iv_access"])
        add(d, "stabilization", group, **kw)

# add flags to top-level stabilization entries that need them
for e in ENTRIES:
    if e["id"] == "insert_iv":
        e["flags_set_default"] = ["iv_access"]
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
        "Blood Type & Screen",
        "Calcium (ionized)", "Calcium Level", "Coagulation Panel",
        "Complete Blood Count (CBC)", "D-Dimer", "Lactate", "Lipase",
        "Liver Function Tests (LFTs)", "Magnesium Level", "Phosphate Level",
        "Plasma Procalcitonin", "pro-BNP", "Troponin-T", "Urinalysis"]
OTHER_LABS = ["Acetaminophen Level", "Amylase", "Blood Culture x 2",
              "C-reactive Protein (CRP)", "COVID-19 test", "Creatine Kinase (CK)",
              "CSF Cell Count", "CSF Culture", "CSF Glucose", "CSF Gram Stain",
              "CSF Protein", "CSF Rapid Antigen Test for N. meningitidis",
              "Erythrocyte Sedimentation Rate (ESR)", "Ethanol Level (EtOH)",
              "Influenza A&B Antigen Test", "Lactate dehydrogenase (LDH)",
              "Osmolality", "Peripheral smear", "Salicylate (Aspirin) Level",
              "Serum HCG (quantitative)", "Skin Biopsy of the Rash", "TSH",
              "Uric Acid", "Urine Culture", "Urine HCG (qualitative)",
              "Urine Rapid Antigen Test for N. meningitidis",
              "Urine Rapid Antigen Test for S. pneumoniae", "Urine Tox Screen"]
IMAGING = ["CT - Abdomen", "CT - Aorta", "CT - C-spine", "CT - Chest", "CT - Head",
           "CT - Pulmonary Embolus", "CT/CTA - Head and Neck", "MRI - C-spine",
           "MRI - Lumbar Spine", "MRI - Thoracic Spine", "MRI/MRA - Head and Neck",
           "XR - Chest", "XR - Pelvis"]

for d in BEDSIDE:
    tc = "ecg" if d == "ECG" else "bedside"
    add(d, "investigations", "Bedside Tests", category="investigation",
        id="ecg_12_lead" if d == "ECG" else sid(d),
        turnaround_class=tc, repeatable=True,
        narration_template="{name} is up." )
for d in LABS:
    add(d, "investigations", "Lab Work", category="investigation",
        turnaround_class="lab", repeatable=True,
        narration_template="Sending {name}.")
for d in OTHER_LABS:
    kw = {}
    if d.startswith("CSF"):
        kw["default_prerequisites"] = PRE_LP
    add(d, "investigations", "Other Labs", category="investigation",
        turnaround_class="lab", repeatable=True,
        narration_template="Sending {name}.", **kw)
for d in IMAGING:
    add(d, "investigations", "Imaging", category="investigation",
        turnaround_class="imaging", repeatable=True,
        narration_template="{name} is ordered.")

# ================================================ INTERVENTIONS (images 10-20)
PROCEDURES = ["Arterial Line", "C-Collar", "Central Venous Catheter (cordis)",
              "Central Venous Catheter (triple lumen)",
              "Decontaminate (Hazmat activation)", "Don Personal Protective Equipment",
              "Insert Chest Tube", "Insert Foley Catheter", "Lower Head of Bed",
              "Lumbar Puncture", "Place Nasogastric Tube", "Place Orogastric Tube",
              "Place Patient on Isolation Precautions",
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
AUTHOR_ADDED = {"Meds - Vasoactive Agents": ["Dobutamine drip"],
                "Meds - Cardiac": ["Nitroglycerin sublingual"]}
for g, items in AUTHOR_ADDED.items():
    MEDS.setdefault(g, [])
    MEDS[g] = sorted(set(MEDS[g] + items))

# Routes that do not need vascular access. DERIVED, not transcribed: the
# screenshots carry no route information. Author confirmation required.
NON_IV = {"Prednisone", "Epinephrine (Intramuscular)", "Activated Charcoal",
          "Colchicine", "Propylthiouracil", "TDaP", "Potassium Iodide & Iodine",
          "Aspirin", "Atorvastatin", "Clopidogrel", "Misoprostol", "Methergine",
          "Albuterol", "Ipratropium", "Nitroglycerin sublingual"}
ROUTE_AMBIGUOUS = {"Acetaminophen", "Ibuprofen", "Dexamethasone", "Diphenhydramine",
                   "Ondansetron", "Metoclopramide", "Thiamine", "Oxytocin IM/IV",
                   "RhoGAM", "Haloperidol", "Olanzapine", "Ziprasidone",
                   "Potassium Chloride (KCl)", "N-acetylcysteine", "Oseltamivir",
                   "Amoxicillin", "Doxycycline", "Minocycline", "Rifampin"}
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
        if d in AUTHOR_ADDED.get(group, []):
            INDEX[sid(d)]["source"] = "author-supplied, not in screenshots"

# ================================================ STOP ACTIONS
# Infusions are persistent: once started they run for the rest of the case. Without a
# way to stop one, any deterioration branch whose rescue is "turn the drip off" has no
# exit and the patient cannot be rescued. One stop action per persistent infusion.
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
        narration_template="Stopping the {name_lower}.",
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
    "catalog_version": "0.1-draft",
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
    "aligned_to": ["system-design-v2.md v0.3 section 3",
                   "case-authoring-requirements.md v0.2 section 7"],
    "status": "INCOMPLETE -- see known_gaps",
    "field_provenance": {
        "transcribed_from_screenshots": ["display_name", "placements.tab",
                                         "placements.group", "short_code"],
        "derived_by_convention": ["id (snake_case of display_name)",
                                  "category", "state_changing", "dose_required",
                                  "route_class", "repeatable", "stoppable",
                                  "narration_template"],
        "derived_from_design_docs": ["turnaround_class (design 2.1/8.1)",
                                     "default_prerequisites (design 6.1)",
                                     "flags_set_default"],
        "not_present_and_not_invented": ["clinical appropriateness", "dose values",
                                         "normal result values", "consultant list"],
    },
    "turnaround_seconds_by_class": {"lab": 5, "imaging": 10, "ecg": 10, "bedside": 0},
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
    },
    "resolved_since_v0.1_draft": [
        "Meds - Allergy, Tox, Psych, Miscellaneous transcribed from the second screenshot batch.",
        "Consultations tab transcribed; 16 entries added.",
        "Furosemide present as 'Furosemide bolus' under Meds - Miscellaneous.",
        "Dobutamine drip added on author instruction; marked source=author-supplied, not in screenshots.",
        "CPAP and BiPAP collapsed into the single UI entry 'Non-Invasive Positive Pressure Ventilation' on author instruction.",
        "Stop actions added: every persistent infusion now has a matching stop entry, so a drip can be withdrawn and a rescue that depends on it is reachable.",
        "Venous Blood Gas added alongside the arterial gas.",
        "Consult Critical Care added; 17 consultants.",
        "Fluid boluses made explicit in agent and volume (NS and LR, 1L and 500mL). The generic crystalloid bolus is gone; see equivalence_groups.",
        "Bumetanide removed. Furosemide carries its dose in the display name.",
        "Catalog prerequisites rewritten with the mandatory trailing keyword so they parse in the section 4 grammar.",
        "Nitroglycerin sublingual added as a separate route variant on author instruction.",
    ],
    "known_gaps": [
        "Meds - Respiratory truncated in screenshot: only Albuterol and Ipratropium visible, list continues.",
        "Meds - Antibiotics may continue past Vancomycin (alphabetical, screenshot cut at the V's).",
        "Lab Work may continue past Urinalysis (alphabetical, cut at the U's).",
        "Imaging list has no plain radiographs other than chest and pelvis; may be truncated.",
        "No Handoff tab / disposition options, required by design section 9.",
        "No diagnosis catalog, required by design section 9.",
        "Default normal results were drafted by the AI from general knowledge, not from a laboratory reference. Ranges are assay- and institution-specific and are unverified. Entries carrying a 'verify' field are the ones known to vary in ways that change interpretation.",
        "Blood Type & Screen, serum hCG and urine hCG have defaults but are patient attributes rather than normal values. Defaulting to O positive and not pregnant is a silent assertion about every unauthored patient.",
        "Culture defaults read 'no growth to date' because the 5-second lab turnaround cannot represent a 24-48 hour culture. Cases whose teaching point is a positive culture cannot be authored honestly.",
        "Peak expiratory flow has no meaningful global normal, since predicted values depend on age, sex and height. Its default is a placeholder.",
        "ABG defaults assume room air. On supplemental oxygen the same numbers are abnormal, and nothing in the schema knows that.",
        "Dose behaviour is not visible in the screenshots; dose_required is a guess per category and no dose values are recorded.",
        "route_class is derived, not transcribed. Entries marked 'unspecified' need author confirmation because the vascular-access prerequisite depends on it.",
        "Infusions are persistent=true. Stopping one is a separate action rather than a toggle, so a case must author the stop as its own step.",
        "Meds - Cardiac now holds both 'Nitroglycerin' (transcribed, route unspecified) and 'Nitroglycerin sublingual' (author-supplied). If the transcribed entry IS the sublingual one, these are duplicates and one must be removed.",
        "Reference-case ids with still no catalog counterpart: bp_cycling_q5min, urine_output_monitoring, echo_formal, vent_settings_lung_protective, peep_reduce, handoff_submit. See reference_case_id_map.",
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
