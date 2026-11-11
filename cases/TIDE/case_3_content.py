"""TIDE part 3: exam findings, general status, the figure, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT. Reference intervals are the catalog defaults.
Phase rules come before flag rules (authoring 3). No finding or report quotes a vital sign,
because the oxygen devices, fluid, the tube and the pushes all move the monitor. Every gas
agrees with Henderson-Hasselbalch (pH = 6.1 + log10(HCO3 / (0.03 x pCO2))).
"""
import math

# The arrival phase (5 November 2026) is the same patient as presentation, so every
# rule for one is a rule for both. Only the nurse prompts tell them apart.
P1 = "(phase is arrival OR phase is presentation)"
ARRIVAL = "phase is arrival"
P2 = "phase is fluid_response"
P3 = "phase is low_pressure"
P4 = "phase is low_after_fluid"
P5 = "phase is worsening_shock"
P6 = "phase is on_pressor"
P7 = "phase is failing_support"
P8 = "phase is tiring"
P9 = "phase is post_induction_collapse"
P10 = "phase is ventilated"
INTUB = "flag intubated set"
SEVERE = "flag severe_shock set"
STACKED = "flag fluid_stacked set"
FLUID = "flag fluid_given set"

VERIFY = "Model output, not from a physician or a laboratory reference. [UNVERIFIED]"


def ex(findings, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": findings}


def gs(findings, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": findings}


def comp(label, value, unit, ref, abnormal):
    return {"label": label, "value": value, "unit": unit, "reference_range": ref, "abnormal": abnormal}


def panel(components, comment=None):
    d = {"kind": "panel", "abnormal": any(c["abnormal"] for c in components),
         "components": components, "verify": VERIFY}
    if comment:
        d["comment"] = comment
    return d


def val(label, value, unit, ref, abnormal, comment=None):
    d = {"kind": "value", "abnormal": abnormal,
         "components": [comp(label, value, unit, ref, abnormal)], "verify": VERIFY}
    if comment:
        d["comment"] = comment
    return d


def report(text, abnormal=True):
    return {"kind": "report", "abnormal": abnormal, "report": text, "verify": VERIFY}


def always(v):
    return [{"when": None, "value": v}]


# ================================================================ EXAM
EXAM = {
 "authoring_note": (
   "Section 9.2. Routing follows the catalog map: work of breathing on exam_breath, lung "
   "sounds on exam_pulm, capillary refill and skin temperature on exam_circ, mottling and "
   "sweating on exam_skin, consciousness and GCS on exam_neuro, calf on exam_msk."),

 "exam_airway": [
   {"when": INTUB, "value": ex("Endotracheal tube secured at the lips. Equal chest rise with each ventilator breath.", abnormal=False)},
   {"when": P8, "value": ex("Snoring, gurgling breaths. Opens with a jaw thrust.")},
   {"when": P7, "value": ex("Patent. One or two words at a time.")},
   {"when": None, "value": ex("Patent. Speaking three or four words at a time.")}],

 "exam_breath": [
   {"when": INTUB, "value": ex("On the ventilator. Chest rising with each machine breath. No breaths over the set rate.")},
   {"when": P8, "value": ex("Slow, shallow, irregular breaths. Head bobbing has stopped.")},
   {"when": P7, "value": ex("Paradoxical belly movement, head bobbing, accessory muscles straining. Nasal flaring.")},
   {"when": P5, "value": ex("Fast, labored breathing. Accessory muscles. Too drowsy to sit forward.")},
   {"when": "flag o2_hfnc set OR flag o2_niv set",
    "value": ex("Still fast and labored on the support. Less accessory muscle use than on arrival.")},
   {"when": None, "value": ex("Tripoding. Accessory muscles and nasal flaring. Fast, labored breathing.")}],

 "exam_circ": [
   {"when": P9, "value": ex("Pulse fast and weak. Capillary refill 5 seconds. Hands cool.")},
   {"when": P8, "value": ex("Pulse slow and weak. Capillary refill 4 seconds. Hands cool.")},
   {"when": P5, "value": ex("Pulse fast and thready. Capillary refill 5 seconds. Hands and feet cold.")},
   {"when": P3 + " OR " + P4, "value": ex("Pulse fast and thready. Capillary refill 4 seconds. Hands cooling.")},
   {"when": P2, "value": ex("Pulse fast, better volume. Capillary refill 3 seconds. Warm.")},
   {"when": P6 + " OR " + P7 + " OR " + P10, "value": ex("Pulse fast and regular. Capillary refill 3 seconds. Warm.")},
   {"when": None, "value": ex("Pulse fast and bounding. Capillary refill 3 seconds. Warm and flushed.")}],

 "exam_pulm": [
   {"when": INTUB + " AND " + STACKED, "value": ex("Coarse crackles at both bases and into the mid zones, worse on the right. Equal air entry on the ventilator.")},
   {"when": INTUB, "value": ex("Coarse crackles at both bases, worse on the right. Bronchial breathing at the right base. Equal air entry.")},
   {"when": STACKED, "value": ex("Coarse crackles at both bases and now into the mid zones, worse on the right. Bronchial breathing and egophony at the right base.")},
   {"when": None, "value": ex("Coarse crackles at both bases, worse on the right. Bronchial breathing and egophony at the right base. Dull to percussion there.")}],

 "exam_card": always(ex("Fast and regular. No murmur, rub or gallop. No leg edema.", abnormal=False)),

 "exam_neck": always(ex("Neck veins flat. Trachea midline. Supple.", abnormal=False)),

 "exam_heent": [
   {"when": INTUB, "value": ex("Tube secured. Pupils equal and reactive. Mucous membranes dry.")},
   {"when": None, "value": ex("Dry mouth. Lips dusky. Pupils equal and reactive.")}],

 "exam_skin": [
   {"when": P5 + " OR " + P9, "value": ex("Mottled from the knees to the mid thighs. Cool hands and feet.")},
   {"when": P3 + " OR " + P4 + " OR " + P8, "value": ex("Hot. Mottling over both knees.")},
   {"when": SEVERE, "value": ex("Hot. Mottling fading over both thighs.")},
   {"when": None, "value": ex("Hot, flushed and sweaty. No rash.")}],

 "exam_neuro": [
   {"when": INTUB, "value": ex("On the ventilator after induction. Not moving. Pupils equal and reactive.")},
   {"when": P8, "value": ex("Rouses to pain only. Groans, no words. GCS 9: eyes 2, verbal 2, motor 5.")},
   {"when": P7, "value": ex("Confused. Opens eyes to voice. Words, but muddled. GCS 13: eyes 3, verbal 4, motor 6.")},
   {"when": P5, "value": ex("Drowsy. Opens eyes to voice. Oriented to person only. GCS 13.")},
   {"when": None, "value": ex("Alert and oriented. GCS 15. Moves all four limbs.", abnormal=False)}],

 "exam_msk": always(ex("No calf swelling or tenderness.", abnormal=False)),

 "exam_abd": always(ex("Soft, non-tender. No guarding.", abnormal=False)),

 "exam_psych": [
   {"when": INTUB + " OR " + P8, "value": ex("Cannot be assessed.")},
   {"when": P7, "value": ex("Restless and confused. Pulling at the oxygen.")},
   {"when": None, "value": ex("Anxious and frightened. Cooperative.")}],
}

GENERAL_STATUS = {
 "authoring_note": "Section 9.3. Consistent with exam_neuro and each phase's appearance values.",
 "rules": [
   {"when": INTUB, "value": gs("Intubated and ventilated after induction. GCS not assessable.")},
   {"when": P8, "value": gs("Slumped, gasping, rousable only to pain. GCS 9.")},
   {"when": P7, "value": gs("Exhausted and confused, head bobbing with each breath. GCS 13.")},
   {"when": P5, "value": gs("Drowsy, mottled, breathing fast. GCS 13.")},
   {"when": None, "value": gs("Sitting forward, hot and sweaty, three or four words a breath. GCS 15.")},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": (
   "MODEL-AUTHORED. Devices are not drawn from rules: the figure shows the last airway "
   "button pressed (authoring 5.3)."),
 "verify": "Check the drawn work of breathing in each phase. [UNVERIFIED]",
 "rules": [
   {"when": INTUB, "value": {"eyes": "closed", "work_of_breathing": "normal"}},
   {"when": P8, "value": {"work_of_breathing": "increased", "addons": ["sweating"]}},
   {"when": P7, "value": {"work_of_breathing": "severe", "addons": ["sweating", "agitation"]}},
   {"when": P5, "value": {"work_of_breathing": "severe", "addons": ["sweating"]}},
   {"when": None, "value": {"work_of_breathing": "severe", "addons": ["sweating"]}},
 ],
}

# ---- Skin signs on the figure (owner, 11 November 2026) ----
# Drawn from the drawn skin tone (engine/patient.js: pallor, flushed, cyanosis). Each
# condition copies this case's own general status or examination condition for the line
# that names the sign. "Gray" is drawn as pallor and "dusky" or "cyanosed" lips as
# cyanosis. Mottling and purpura are not drawn: the text puts them on the knees, thighs,
# forearms and legs, which the figure does not show. MODEL-AUTHORED, not physician reviewed.
PATIENT_VISUAL.setdefault("also", []).extend([
  {"when": "NOT (phase is low_pressure OR phase is low_after_fluid OR phase is worsening_shock OR phase is tiring OR phase is post_induction_collapse OR phase is arrest OR phase is case_complete) AND NOT flag severe_shock set",
   "addons": ["flushed"]},
  {"when": "phase is arrival AND NOT " + INTUB, "addons": ["cyanosis"]},
])
PATIENT_VISUAL["verify"] = (PATIENT_VISUAL.get("verify") or "") + (" Skin signs (11 November 2026): flushed wherever the skin examination reads 'hot, flushed and sweaty'. Cyanosis on arrival only, from the prompt's 'lips look dusky' before oxygen. Note for review: exam_heent says 'lips dusky' in every phase without a tube, which is drawn only on arrival.")

# ================================================================ LABORATORY

def hh(hco3, pco2):
    return 6.1 + math.log10(hco3 / (0.03 * pco2))


def be(ph, hco3):
    return round(0.93 * (hco3 - 24.4 + 14.8 * (ph - 7.4)))


def vbg(ph_s, pco2, hco3, lact):
    ph = float(ph_s)
    assert abs(hh(hco3, pco2) - ph) < 0.015, (ph_s, pco2, hco3, hh(hco3, pco2))
    b = be(ph, hco3)
    return panel([
      comp("pH", ph_s, "", "7.31-7.41", not (7.31 <= ph <= 7.41)),
      comp("pCO2", str(pco2), "mmHg", "41-51", not (41 <= pco2 <= 51)),
      comp("HCO3", str(hco3), "mEq/L", "22-26", not (22 <= hco3 <= 26)),
      comp("Base excess", str(b), "mEq/L", "-2 to +2", not (-2 <= b <= 2)),
      comp("Lactate", lact, "mmol/L", "0.5-2.0", float(lact) > 2.0)])


# Saturation on the monitor -> PaO2 on the curve, rounded. Model's reading of the
# oxyhemoglobin curve at a raised temperature and a low pH. [UNVERIFIED]
PAO2 = {76: 42, 79: 45, 80: 46, 81: 47, 82: 48, 83: 49, 84: 50, 85: 51, 86: 53, 87: 55, 88: 56,
        89: 58, 90: 60, 91: 63, 92: 66, 93: 70, 94: 74, 95: 78}


def abg(ph_s, pco2, hco3, sat, fio2_label):
    ph = float(ph_s)
    assert abs(hh(hco3, pco2) - ph) < 0.015, (ph_s, pco2, hco3, hh(hco3, pco2))
    pao2 = PAO2[sat]
    b = be(ph, hco3)
    return panel([
      comp("pH", ph_s, "", "7.35-7.45", not (7.35 <= ph <= 7.45)),
      comp("pCO2", str(pco2), "mmHg", "35-45", not (35 <= pco2 <= 45)),
      comp("pO2", str(pao2), "mmHg", "80-100 on room air", True),
      comp("HCO3", str(hco3), "mEq/L", "22-26", not (22 <= hco3 <= 26)),
      comp("Base excess", str(b), "mEq/L", "-2 to +2", not (-2 <= b <= 2)),
      comp("O2 saturation", str(sat), "%", "95-100", sat < 95),
      comp("Oxygen", fio2_label, "", "room air", False)])


# Phase baselines on room air, and the device deltas (case_2_actions.py).
BASE = {"early": 85, "p5": 83, "p7": 81, "p8": 76, "p9": 90, "p10": 95}  # p10 equals the ventilated phase
DEVICES = [  # highest device assumed when several were used (known gap 3)
  ("flag o2_niv set", 8, "BiPAP, FiO2 0.6"),
  ("flag o2_hfnc set", 7, "High flow 60 L/min, FiO2 0.6"),
  ("flag o2_nrb set", 6, "Nonrebreather 15 L/min"),
  ("flag o2_nc set", 3, "Nasal cannula 6 L/min"),
  (None, 0, "Room air"),
]


def by_device(base, ph_s, pco2, hco3, late_ph=None, late_hco3=None, fio2_high=None, late_pco2=None):
    rows = []
    for when, d, label in DEVICES:
        if fio2_high and d >= 7:
            label = label.replace("0.6", fio2_high)
        if late_ph:
            rows.append({"when": SEVERE + (" AND " + when if when else ""),
                         "value": abg(late_ph, late_pco2 or pco2, late_hco3, base + d, label)})
        rows.append({"when": when, "value": abg(ph_s, pco2, hco3, base + d, label)})
    return rows


def ph_rows(phase_cond, rows):
    out = []
    for r in rows:
        w = r["when"]
        out.append({"when": phase_cond + (" AND " + w if w else ""), "value": r["value"]})
    return out


ABG_RULES = (
  [{"when": P10 + " AND " + SEVERE, "value": abg("7.15", 45, 15, 95, "Ventilator, FiO2 0.7, PEEP 12")},
   {"when": P10, "value": abg("7.22", 45, 18, 95, "Ventilator, FiO2 0.7, PEEP 12")},
   {"when": P9 + " AND " + SEVERE, "value": abg("7.16", 44, 15, 90, "Ventilator, FiO2 1.0")},
   {"when": P9, "value": abg("7.23", 44, 18, 90, "Ventilator, FiO2 1.0")},
   {"when": P8 + " AND " + SEVERE, "value": abg("7.02", 60, 15, 76, "Oxygen running, not effective")},
   {"when": P8, "value": abg("7.11", 60, 18.5, 76, "Oxygen running, not effective")}]
  + ph_rows(P7, by_device(BASE["p7"], "7.22", 46, 18.5, late_ph="7.15", late_hco3=15.5, fio2_high="1.0"))
  + ph_rows(P5, by_device(BASE["p5"], "7.29", 28, 13, fio2_high=None))
  + by_device(BASE["early"], "7.35", 31, 16.5, late_ph="7.29", late_hco3=13, late_pco2=28)
)

VBG_RULES = [
  {"when": "(" + P10 + " OR " + P9 + ") AND " + SEVERE, "value": vbg("7.11", 52, 16, "5.4")},
  {"when": P10 + " OR " + P9, "value": vbg("7.19", 52, 19, "3.8")},
  {"when": P8 + " AND " + SEVERE, "value": vbg("7.01", 70, 17, "5.4")},
  {"when": P8, "value": vbg("7.10", 70, 21, "3.8")},
  {"when": P7 + " AND " + SEVERE, "value": vbg("7.11", 56, 17, "5.4")},
  {"when": P7, "value": vbg("7.18", 56, 20, "3.8")},
  {"when": SEVERE + " OR " + P5, "value": vbg("7.27", 30, 13.5, "5.4")},
  {"when": None, "value": vbg("7.33", 33, 17, "3.8")},
]

LACTATE_RULES = [
  {"when": SEVERE + " OR " + P5, "value": val("Lactate", "5.4", "mmol/L", "0.5-2.0", True)},
  {"when": None, "value": val("Lactate", "3.8", "mmol/L", "0.5-2.0", True)},
]


def chem(na, k, cl, hco3, bun, cr, glu):
    gap = na - cl - hco3
    return panel([
      comp("Sodium", str(na), "mEq/L", "135-145", na < 135),
      comp("Potassium", str(k), "mEq/L", "3.5-5.0", not (3.5 <= k <= 5.0)),
      comp("Chloride", str(cl), "mEq/L", "98-107", not (98 <= cl <= 107)),
      comp("Bicarbonate", str(hco3), "mEq/L", "22-29", hco3 < 22),
      comp("BUN", str(bun), "mg/dL", "7-20", bun > 20),
      comp("Creatinine", str(cr), "mg/dL", "0.7-1.3", cr > 1.3),
      comp("Glucose", str(glu), "mg/dL", "70-140 (random)", glu > 140),
      comp("Anion gap", str(gap), "mEq/L", "8-12", gap > 12)],
      comment="Anion gap calculated without potassium.")


LABS = {
 "authoring_note": (
   "Results freeze at the state in which they were ordered. The lactate and gases split on "
   "severe_shock, granted by every timed rule into worsening_shock. The arterial gas splits "
   "on the device flags, highest device first (known gap 3)."),
 "venous_blood_gas": {"rules": VBG_RULES, "changes_with_state": True},
 "arterial_blood_gas": {"rules": ABG_RULES, "changes_with_state": True},
 "lactate": {"rules": LACTATE_RULES, "changes_with_state": True},
 "basic_chemistry_chem_7": {"rules": [
   {"when": SEVERE, "value": chem(133, 4.4, 99, 15, 36, 1.9, 252)},
   {"when": None, "value": chem(133, 4.1, 99, 18, 34, 1.7, 244)}], "changes_with_state": True},
 "complete_blood_count_cbc": {"rules": always(panel([
   comp("WBC", "18.6", "x10^9/L", "4.0-11.0", True),
   comp("Bands", "14", "%", "0-5", True),
   comp("Hemoglobin", "13.8", "g/dL", "13.5-17.5 (M), 12.0-16.0 (F)", False),
   comp("Hematocrit", "41", "%", "41-53 (M), 36-46 (F)", False),
   comp("Platelets", "168", "x10^9/L", "150-400", False)])), "changes_with_state": False},
 "plasma_procalcitonin": {"rules": always(val("Procalcitonin", "18.4", "ng/mL", "< 0.10", True)),
                          "changes_with_state": False},
 "urine_rapid_antigen_test_for_s_pneumoniae": {"rules": always(report("Positive.")),
                                               "changes_with_state": False},
 "influenza_a_and_b_antigen_test": {"rules": always(report("Influenza A: Negative. Influenza B: Negative.", abnormal=False)),
                                    "changes_with_state": False},
 "fingerstick_blood_sugar": {"rules": always(val("Capillary glucose", "238", "mg/dL", "70-140 (random)", True)),
                             "changes_with_state": False},
}

CXR_READ = ("Patchy airspace opacities in both lower zones, more extensive on the right, in the "
            "right mid and lower zones and the left lower zone, with air bronchograms. No pleural "
            "effusion. No pneumothorax. Heart size normal.")
CXR_TUBE_READ = (CXR_READ + " Endotracheal tube in the trachea, its tip in the mid trachea above "
                 "the carina.")

def ecg_image(stem, rate, pr, qrs, read):
    """Section 23. A generated tracing reused from another pack, its read the debrief comment.
    media/README.md names the source file of each. No vital effect moves the heart rate in this
    case, so the caption quotes the rate."""
    return {"kind": "image", "abnormal": True, "image": "tide-ecg-" + stem,
            "caption": "Twelve-lead ECG. Ventricular rate %d, PR %d ms, QRS %d ms, QTc 430 ms" % (rate, pr, qrs),
            "comment": read, "verify": VERIFY}


def sinus(rate):
    return ecg_image("sinus-%d" % rate, rate, 140, 84,
                     "Sinus tachycardia at %d. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. "
                     "No ST elevation or depression." % rate)


ECG_RULES = [
  {"when": P8, "value": ecg_image("brady-56", 56, 150, 88,
     "Sinus bradycardia at 56. Normal axis. PR 150 ms, QRS 88 ms, QTc 430 ms. No ST change.")},
  {"when": P5, "value": sinus(138)},
  {"when": P3 + " OR " + P9, "value": sinus(128)},
  {"when": P2 + " OR " + P6 + " OR " + P7 + " OR " + P10, "value": sinus(114)},
  {"when": None, "value": sinus(116)},
]


IMAGING = {
 "authoring_note": (
   "Section 23. The film is Pneumonia/Multifocal_Male.png from the owner's folder, looked at "
   "by the model on 4 November 2026 beside its read. The tube was drawn in with "
   "Claude outputs/ett_v1/cxr_ett_draw.py. media/README.md records both."),
 "xr_chest": {"rules": [
   {"when": INTUB, "value": {"kind": "image", "abnormal": True, "image": "tide-cxr-multifocal-ett",
                            "caption": "Chest radiograph", "comment": CXR_TUBE_READ, "verify": VERIFY}},
   {"when": None, "value": {"kind": "image", "abnormal": True, "image": "tide-cxr-multifocal",
                           "caption": "Chest radiograph", "comment": CXR_READ, "verify": VERIFY}}],
   "changes_with_state": True},
 "ecg_12_lead": {"rules": ECG_RULES, "changes_with_state": True,
   "author_note": ("Generated tracings reused from TSS and SCOOT (media/README.md), because the "
                   "generator could not be run for this pack. Each phase gets the tracing nearest "
                   "its monitor rate. The reads are those the tracings were drawn from.")},
 "ultrasound_lung": {"rules": [
   {"when": STACKED, "value": report("Consolidation with dynamic air bronchograms at both bases, larger on the right. B-lines in both mid and upper zones, more than before. Lung sliding present. No effusion.")},
   {"when": None, "value": report("Consolidation with dynamic air bronchograms at both bases, larger on the right. Scattered B-lines. Lung sliding present. No effusion.")}],
   "changes_with_state": True},
 "ultrasound_cardiac": {"rules": [
   {"when": FLUID, "value": report("Hyperdynamic left ventricle. Normal right ventricle. No pericardial effusion. Inferior vena cava fuller, with less respiratory variation.")},
   {"when": None, "value": report("Hyperdynamic left ventricle with a small cavity. Normal right ventricle. No pericardial effusion. Small inferior vena cava, collapsing more than half with each breath.")}],
   "changes_with_state": True},
 "ct_chest": {"rules": always(report("Consolidation with air bronchograms in the right middle and lower lobes and the left lower lobe. Scattered ground-glass opacity. No effusion, no cavity, no mass."))},
 "ct_pulmonary_embolus": {"rules": always(report("No pulmonary embolism. Consolidation with air bronchograms in the right middle and lower lobes and the left lower lobe. No effusion."))},
}

# ================================================================ CONSULTANTS
CXR_R = "study xr_chest resulted"
LAB_R = "(study lactate resulted OR study venous_blood_gas resulted OR study arterial_blood_gas resulted)"
LAB_O = "(study lactate ordered OR study venous_blood_gas ordered OR study arterial_blood_gas ordered OR study xr_chest ordered)"
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. The intensivist's tiers run from the most specific phase down. Only tiers "
   "that test a resulted study name a finding from it, and none quotes a number."),
 "consult_critical_care": [
   {"when": P9,
    "value": "Intensivist: His pressure fell with induction. Start a vasopressor drip now, push-dose to bridge. I'm on my way down."},
   {"when": P8,
    "value": "Intensivist: He's peri-arrest. Tube him now, with the drip running. I'm coming."},
   {"when": P7,
    "value": "Intensivist: He's failing the high flow. Intubate now, drip running, preoxygenate on BiPAP. Bed's ready upstairs."},
   {"when": P10,
    "value": "Intensivist: Good. Analgesia and sedation, a film, a gas. Low tidal volumes from his predicted weight. Bring him up."},
   {"when": P5,
    "value": "Intensivist: He's in shock. Norepinephrine now, peripheral is fine. Antibiotics in? I'll come and see him."},
   {"when": P6 + " AND " + CXR_R + " AND " + LAB_R,
    "value": "Intensivist: Severe pneumonia, septic shock on a pressor. Yes, he's ours. Hydrocortisone is reasonable. Call me the moment his breathing turns."},
   {"when": P6,
    "value": "Intensivist: Shock on a pressor, I'll take him. Send a film and a gas or lactate, and call me if his breathing gets worse."},
   {"when": P3 + " OR " + P4,
    "value": "Intensivist: Mean under 65? If fluid hasn't held it, start norepinephrine peripherally. I'll take him."},
   {"when": CXR_R + " AND " + LAB_R,
    "value": "Intensivist: Multilobar pneumonia, high lactate, fast breathing. That's severe. Fluid, antibiotics, high flow. I'll take him upstairs."},
   {"when": LAB_O,
    "value": "Intensivist: Sounds sick. Call me back with the film and a lactate. Antibiotics shouldn't wait for them."},
   {"when": None,
    "value": "Intensivist: Sounds sick. What does his film show, and what's his lactate? Get antibiotics in meanwhile."}],
 "consult_pulmonology": [
   {"when": None, "value": "Pulmonologist: This sounds like the ICU's patient. Call them. I'm happy to see him upstairs."}],
 "consult_infectious_disease": [
   {"when": None, "value": "Infectious disease: Severe CAP with no MRSA or Pseudomonas risk: ceftriaxone and azithromycin. Cultures first if they don't delay it."}],
}
