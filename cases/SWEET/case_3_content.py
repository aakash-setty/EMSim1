"""SWEET part 3: exam findings, general status, the figure, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT except the phase findings taken from the owner's case
structure (S1 to S6). Reference intervals are pediatric where the catalog's are adult, and
each needs a signature.

Phase rules come first in every list. Inside a phase, the brief response to an IM dose is a
flag variant above the phase's own line: the first ED dose acts from 10 to 120 seconds in
phase 1 (epi_onset lapses at 10), a later dose from 10 to 60 seconds (epi_bridge_acting).

No report and no exam line quotes a heart rate, a pressure or a respiratory rate: the IM
doses, the boluses, posture, albuterol and the IV push move them.
"""
import math

P1 = "phase is presentation"
P2 = "phase is persistent"
P3 = "phase is worsening"
P4 = "phase is peri_arrest"
P5 = "phase is responding"
P6 = "phase is stabilized"
P7 = "phase is post_induction_collapse"
P8 = "phase is ventilated"
TUBED = "flag intubated set"
FIRST_ACTING = P1 + " AND flag epi_im_ed set AND NOT flag epi_onset set"
BRIDGE_ACTING = "(" + P2 + " OR " + P3 + ") AND flag epi_bridge_acting set AND NOT flag epi_onset set"
ANTIHIST = "flag antihistamine_given set AND NOT flag antihistamine_onset set"
ALB = "flag albuterol_given set"

VERIFY = "Model output, not from a physician or a laboratory reference. Pediatric intervals to be checked. [UNVERIFIED]"


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


def val(label, value, unit, ref, abnormal):
    return {"kind": "value", "abnormal": abnormal,
            "components": [comp(label, value, unit, ref, abnormal)], "verify": VERIFY}


def report(text, abnormal=True):
    return {"kind": "report", "abnormal": abnormal, "report": text, "verify": VERIFY}


def always(v):
    return [{"when": None, "value": v}]

def ecg_image(stem, pr, qrs, qtc, read):
    """Section 23. A generated adult tracing reused from another pack (media/README.md names
    each source). Epinephrine, fluid and position move the rate, so the caption leaves it out."""
    return {"kind": "image", "abnormal": True, "image": "sweet-ecg-" + stem,
            "caption": "Twelve-lead ECG. PR %d ms, QRS %d ms, QTc %d ms" % (pr, qrs, qtc),
            "comment": read, "verify": VERIFY}



def by_phase(pairs, tubed=None):
    rules = [{"when": TUBED, "value": tubed}] if tubed else []
    return rules + [{"when": w, "value": v} for w, v in pairs]


# ============================================================== EXAM
EXAM = {
 "authoring_note": (
   "Section 9.2. Routing follows the catalog map: work of breathing on exam_breath, lung "
   "sounds on exam_pulm, refill and pulses on exam_circ, lips and eyelids on exam_heent, "
   "hives on exam_skin, consciousness on exam_neuro. The voice and stridor sit on "
   "exam_airway. Ventilated lines first (authoring 8.5)."),

 "exam_airway": by_phase([
   (P4, ex("Hoarse whisper. Soft high-pitched noise on breathing in. Lips and tongue swollen.")),
   (P3, ex("Single words. No stridor. Lips swollen, tongue full.")),
   (P2, ex("Answers slowly. No stridor. Lips swollen.")),
   (None, ex("Talking in short phrases. No stridor. Handling his secretions. Lips swollen."))],
   tubed=ex("Endotracheal tube in place and secured.")),

 "exam_breath": by_phase([
   (FIRST_ACTING, ex("Breathing a little easier for now. Mild retractions.")),
   (BRIDGE_ACTING, ex("A little easier for the moment. Still retracting.")),
   (P4, ex("Shallow, weak effort.")),
   (P3, ex("Marked retractions below and between the ribs. Tiring, poor effort.")),
   (P2, ex("Retractions below and between the ribs.")),
   (P5, ex("Retractions easing.")),
   (P6, ex("Mild retractions.")),
   (None, ex("Fast breathing, mild retractions, sitting forward."))],
   tubed=ex("Ventilated. Chest rising equally.")),

 "exam_pulm": by_phase([
   (FIRST_ACTING, ex("Wheeze throughout, a little less than before.")),
   (BRIDGE_ACTING, ex("Wheeze throughout, a little less for now. Air entry still poor.")),
   (P4, ex("Almost no air movement. Faint wheeze.")),
   (P3 + " AND " + ALB, ex("Wheeze with poor air movement, slightly better after the nebulizer.")),
   (P3, ex("Wheeze with poor air movement.")),
   (P2 + " AND " + ALB, ex("Wheeze throughout, slightly less after the nebulizer.")),
   (P2, ex("Wheeze throughout both lungs.")),
   (P5, ex("Louder wheeze, better air entry.")),
   (P6, ex("Mild end-expiratory wheeze.")),
   (P1 + " AND " + ALB, ex("Wheeze throughout, slightly less after the nebulizer.")),
   (None, ex("Wheeze throughout both lungs."))],
   tubed=ex("Wheeze on both sides. Air entry equal.")),

 "exam_circ": by_phase([
   (P4, ex("Mottled. Central pulse weak. Peripheral pulses barely felt.")),
   (P3, ex("Cool, mottled legs. Weak peripheral pulses. Capillary refill 4 seconds.")),
   (P2, ex("Cool hands. Capillary refill 4 seconds. Pulses fast and thready.")),
   (P5, ex("Capillary refill 3 to 4 seconds. Pulses stronger.")),
   (P6, ex("Warm hands. Capillary refill under 3 seconds.", abnormal=False)),
   (P7, ex("Mottled. Weak pulses. Capillary refill 5 seconds.")),
   (P8, ex("Capillary refill 3 seconds. Pulses palpable.")),
   (None, ex("Capillary refill 3 seconds. Pulses fast and thready."))]),

 "exam_heent": by_phase([
   (P4, ex("Lips and tongue more swollen. Lips blue.")),
   (P6, ex("Lip and eyelid swelling starting to settle.")),
   (None, ex("Lips and eyelids swollen. Tongue normal size. Uvula midline."))],
   tubed=ex("Lips and eyelids swollen. Tube secured.")),

 "exam_skin": by_phase([
   (P5 + " OR " + P6, ex("Hives fading. Redness persists.")),
   (P4, ex("Mottled, hives still visible, clammy.")),
   (ANTIHIST, ex("Hives fading. Redness persists. Sweaty.")),
   (None, ex("Raised hives and redness over trunk, arms and face. Sweaty."))]),

 "exam_neuro": by_phase([
   (P4, ex("Limp. Responds to pain. GCS 8.")),
   (P3, ex("Floppy, opens his eyes to voice. GCS 12.")),
   (P2, ex("Eyes closing between questions, slow answers. GCS 14.")),
   (P5, ex("Opens his eyes to voice, asks for his mother. GCS 13.")),
   (P6, ex("Alert and tired. GCS 15.", abnormal=False)),
   (None, ex("Alert, frightened, asking for his mother. GCS 15.", abnormal=False))],
   tubed=ex("Sedated and paralyzed. Pupils equal and reactive.")),

 "exam_card": always(ex("Fast regular heart sounds. No murmur.")),
}

GENERAL_STATUS = {
 "authoring_note": "Section 9.3. Consistent with exam_neuro, each phase's appearance values and the figure.",
 "rules": [
   {"when": TUBED + " AND " + P7, "value": gs("Intubated and paralyzed. Mottled.")},
   {"when": TUBED, "value": gs("Intubated and sedated.")},
   {"when": P4, "value": gs("Silent and limp, lips blue. GCS 8.")},
   {"when": P3, "value": gs("Floppy, single words, no longer fighting the mask. GCS 12.")},
   {"when": P2, "value": gs("Has stopped crying and stopped asking for his mother. Slow answers. GCS 14.")},
   {"when": P5, "value": gs("Opening his eyes, asking for his mother again. GCS 13.")},
   {"when": P6, "value": gs("Alert and tired, talking in full sentences. GCS 15.")},
   {"when": None, "value": gs("Frightened and tearful, sitting forward, pulling at the mask, asking for his mother. GCS 15.")},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED. Nonrebreather from the crew on arrival. Signs by phase.",
 "verify": ("Check that the child figure reads as 12, that he looks frightened on arrival and "
            "floppy in phase 3, and that the cyanosis in phase 4 reads. Nothing draws hives or "
            "lip swelling."),
 "rules": [
   {"when": TUBED, "value": {"eyes": "closed", "work_of_breathing": "normal", "addons": ["intubated"]}},
   {"when": P4, "value": {"work_of_breathing": "severe", "addons": ["nonrebreather", "cyanosis", "pallor"]}},
   {"when": P3, "value": {"work_of_breathing": "severe", "addons": ["nonrebreather", "sweating"]}},
   {"when": P6, "value": {"work_of_breathing": "normal", "addons": ["nonrebreather", "flushed"]}},
   {"when": None, "value": {"work_of_breathing": "increased", "addons": ["nonrebreather", "flushed", "sweating"]}},
 ],
}

# ============================================================== LABORATORY
#         venous pCO2, HCO3, lactate, arterial pO2
GAS = {
 "p1": (36, 19, "3.0", 70), "p2": (38, 18, "4.0", 62), "p3": (48, 17, "5.5", 56),
 "p4": (62, 15, "7.0", 46), "p5": (40, 18, "4.2", 64), "p6": (38, 19, "3.6", 88),
 "p7": (55, 15, "6.5", 56), "p8": (45, 17, "5.0", 74),
}
PHASE_KEY = [(P1, "p1"), (P2, "p2"), (P3, "p3"), (P4, "p4"), (P5, "p5"), (P6, "p6"),
             (P7, "p7"), (P8, "p8")]


def ph(pco2, hco3):
    return "%.2f" % (6.1 + math.log10(hco3 / (0.03 * pco2)))


def gas(key, arterial):
    pco2, hco3, lac, po2 = GAS[key]
    if arterial:
        pco2, hco3 = pco2 - 5, hco3 - 1
    p = ph(pco2, hco3)
    lo, hi = (7.35, 7.45) if arterial else (7.31, 7.41)
    clo, chi = (35, 45) if arterial else (41, 51)
    comps = [comp("pH", p, "", "%.2f-%.2f" % (lo, hi), not (lo <= float(p) <= hi)),
             comp("pCO2", str(pco2), "mmHg", "%d-%d" % (clo, chi), not (clo <= pco2 <= chi))]
    if arterial:
        comps.append(comp("pO2", str(po2), "mmHg", "80-100", po2 < 80))
    comps += [comp("HCO3", str(hco3), "mEq/L", "22-26", hco3 < 22),
              comp("Lactate", lac, "mmol/L", "0.5-2.0", True)]
    return panel(comps)


def gas_rules(arterial):
    return [{"when": w, "value": gas(k, arterial)} for w, k in PHASE_KEY[:-1]] + \
           [{"when": None, "value": gas("p8", arterial)}]


CHEM_HCO3 = {"p1": 20, "p2": 19, "p3": 18, "p4": 16, "p5": 19, "p6": 20, "p7": 16, "p8": 18}


def chem(key):
    na, k, cl, bun, cr, glu = 139, "3.8", 105, 12, "0.6", 138
    hco3 = CHEM_HCO3[key]
    gap = na - cl - hco3
    return panel([
      comp("Sodium", str(na), "mEq/L", "135-145", False),
      comp("Potassium", k, "mEq/L", "3.5-5.0", False),
      comp("Chloride", str(cl), "mEq/L", "98-107", False),
      comp("Bicarbonate", str(hco3), "mEq/L", "22-29", True),
      comp("BUN", str(bun), "mg/dL", "7-20", False),
      comp("Creatinine", cr, "mg/dL", "0.3-0.7 (age 12)", False),
      comp("Glucose", str(glu), "mg/dL", "70-140 (random)", False),
      comp("Anion gap", str(gap), "mEq/L", "8-16", gap > 16)],
      comment="Anion gap calculated without potassium.")


LABS = {
 "authoring_note": (
   "Section 9.4. Gases follow Henderson-Hasselbalch in every phase (computed in this file). "
   "The pCO2 rises as he tires (phases 3 and 4) and falls once the infusion runs. Lactate "
   "rises with the shock and falls only a little in minutes. The arterial gas is the venous "
   "one with a pCO2 5 lower and a bicarbonate 1 lower, recomputed. All model output."),
 "venous_blood_gas": {"changes_with_state": True, "rules": gas_rules(False)},
 "arterial_blood_gas": {"changes_with_state": True, "rules": gas_rules(True)},
 "lactate": {"changes_with_state": True, "rules":
   [{"when": w, "value": val("Lactate", GAS[k][2], "mmol/L", "0.5-2.0", True)} for w, k in PHASE_KEY[:-1]] +
   [{"when": None, "value": val("Lactate", GAS["p8"][2], "mmol/L", "0.5-2.0", True)}]},
 "basic_chemistry_chem_7": {"changes_with_state": True, "rules":
   [{"when": w, "value": chem(k)} for w, k in PHASE_KEY[:-1]] + [{"when": None, "value": chem("p8")}]},
 "complete_blood_count_cbc": {"changes_with_state": False, "rules": always(panel([
   comp("WBC", "14.2", "x10^3/uL", "4.5-13.5 (age 12)", True),
   comp("Hemoglobin", "14.8", "g/dL", "11.5-15.5 (age 12)", False),
   comp("Hematocrit", "44", "%", "35-45 (age 12)", False),
   comp("Platelets", "320", "x10^3/uL", "150-450", False)]))},
 "fingerstick_blood_sugar": {"changes_with_state": False, "rules": always(
   val("Capillary glucose", "118", "mg/dL", "70-140 (random)", False))},
}

# ============================================================== IMAGING AND ECG
CXR = ("Hyperinflated lungs. No consolidation, effusion or pneumothorax. Normal heart size "
       "for age.")
IMAGING = {
 "authoring_note": (
   "Section 9.4 and 23. Both studies are text reports in this pack, a departure from the "
   "default picture: the owner's chest film folder holds adult films only, and the generated "
   "tracings in the library are adult rates that do not match his. Recorded in the SEED. "
   "Neither quotes a rate, which the IM doses, boluses and albuterol move."),
 "xr_chest": {"changes_with_state": True, "rules": [
   {"when": TUBED, "value": report(CXR + " Endotracheal tube tip above the carina.")},
   {"when": None, "value": report(CXR)}]},
 "ecg_12_lead": {"changes_with_state": True, "rules": [
   {"when": P6, "value": ecg_image("sinus-124", 132, 82, 448,
      "Sinus tachycardia. Normal axis. PR 132 ms, QRS 82 ms, QTc 448 ms. No ST elevation or depression.")},
   {"when": P1, "value": ecg_image("sinus-138", 140, 84, 430,
      "Sinus tachycardia. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST elevation or depression.")},
   {"when": "phase is bradycardic_arrest", "value": ecg_image("brady-56", 150, 88, 430,
      "Sinus bradycardia. Normal axis. PR 150 ms, QRS 88 ms, QTc 430 ms. No ST change.")},
   {"when": None, "value": ecg_image("sinus-150", 128, 84, 468,
      "Sinus tachycardia. Normal axis. PR 128 ms, QRS 84 ms, QTc 468 ms. No ST elevation or "
      "depression. T waves are not peaked.")}]},
}

# ============================================================== CONSULTANTS
# Most specific first. 40 words or fewer. No line quotes a number.
DRIP_ORDERED = "flag epi_drip_ordered set"
ED_EPI = "flag epi_im_ed set"
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. consult_critical_care stands for the PICU fellow and, through them, the "
   "senior (owner's defaults, 11 November 2026). The replies give the next step by phase, "
   "which is how a PICU fellow answers. No reply names a study result."),
 "consult_critical_care": [
   {"when": TUBED + " AND " + P8,
    "value": "PICU fellow: Keep the epi infusion going and titrate to his pressure. Keep the fluid going. We're bringing a vent down. He comes to us."},
   {"when": TUBED,
    "value": "PICU fellow: His pressure's going after the tube. Epi now, IM or a small push, and get the infusion running. Fluid in fast. I'm coming down."},
   {"when": P6,
    "value": "PICU fellow: Great. Keep the infusion running and don't wean it down there. Albuterol for the wheeze. We have a bed. Bring him up."},
   {"when": P5,
    "value": "PICU fellow: He's turning. Keep the infusion on, titrate to his pressure, and give more fluid. We'll come and get him."},
   {"when": P4,
    "value": "PICU fellow: Running down. Epi now, IM if the drip isn't up. Fluid in fast. Bag him. Get the airway kit and the video scope ready."},
   {"when": P3 + " AND " + DRIP_ORDERED,
    "value": "PICU fellow: Coming. Keep IM epi going until the infusion runs, and push fluid. Have the airway kit ready, but drip before tube."},
   {"when": P3,
    "value": "PICU fellow: He needs an epi infusion now. Get it mixing, IM again until it runs, and push fluid. I'm coming down."},
   {"when": P2 + " AND " + DRIP_ORDERED,
    "value": "PICU fellow: Good, an epi infusion. I'll get pharmacy to rush it. IM again if it's slow, second line, more fluid. Attending's coming too."},
   {"when": P2,
    "value": "PICU fellow: Two doses and worse is refractory. Start an epi infusion and I'll rush pharmacy. IM again until it runs. Attending's coming too."},
   {"when": ED_EPI,
    "value": "PICU fellow: Second dose is in, good. Fluid, legs up, a second line. If he's worse when it wears off, he needs an infusion. Call me."},
   {"when": None,
    "value": "PICU fellow: He's had one dose and he's back? Give IM epi again now, fluid, legs up. If it doesn't hold, call me back for an infusion."}],
}
