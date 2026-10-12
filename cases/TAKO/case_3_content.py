"""TAKO part 3: exam findings, general status, the figure, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT. No physician supplied a number, a finding or a
reference interval.
"""

PRES = "phase is presentation"
OBS = "phase is obstructed"
WORSE_I = "phase is shock_worse"
WORSE = "(phase is shock_worse OR phase is shock_untreated)"
STEADY = "phase is steadied"
LOW = OBS + " OR phase is shock_worse OR phase is shock_untreated"
ACTIVE = "flag inotrope_given set AND NOT flag inotrope_stopped set"
FLUID = "flag fluids_given set"
VASO = "flag vasoconstrictor_running set"
ECHO = "study ultrasound_cardiac resulted"
ECG = "study ecg_12_lead resulted"

VERIFY = "Model output, not from a physician or a laboratory reference. [UNVERIFIED]"
DERIVED = ("Derived by a model from this pack's other values on 7 October 2026. No new "
           "clinical claim was intended. Not from a physician. [UNVERIFIED] ")


def ex(findings, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": findings}


def gs(findings, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": findings}


def comp(label, value, unit, ref, abnormal):
    return {"label": label, "value": value, "unit": unit,
            "reference_range": ref, "abnormal": abnormal}


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


def report(text, abnormal=True, comment=None):
    d = {"kind": "report", "abnormal": abnormal, "report": text, "verify": VERIFY}
    if comment:
        d["comment"] = comment
    return d


def always(v):
    return [{"when": None, "value": v}]


EXAM = {
 "authoring_note": (
   "Section 9.2. Routing follows the catalog map: neck veins on exam_neck, the murmur on "
   "exam_card, capillary refill on exam_circ, lung sounds on exam_pulm. The murmur's "
   "response to posture is written into the cardiac finding because the catalog has no "
   "maneuver for it."),

 "exam_airway": [
   {"when": WORSE, "value": ex("Patent. Barely speaking.")},
   {"when": None, "value": ex("Patent. Speaking in short sentences.", abnormal=False)}],

 "exam_breath": [
   {"when": WORSE, "value": ex("Fast, shallow breathing. No accessory muscle use.")},
   {"when": None, "value": ex("Mildly tachypneic with the pain. No accessory muscle use.")}],

 "exam_circ": [
   {"when": WORSE, "value": ex("Capillary refill 5 seconds. Radial pulse weak. Hands cold and clammy.")},
   {"when": OBS, "value": ex("Capillary refill 4 seconds. Radial pulse weak. Hands cool and clammy.")},
   {"when": STEADY, "value": ex("Capillary refill 2 seconds. Pulse fuller. Hands warming.", abnormal=False)},
   {"when": None, "value": ex("Capillary refill 3 seconds. Pulse fast, low volume. Hands cool and clammy.")}],

 "exam_heent": always(ex("Mouth dry. Pupils equal and reactive. No facial droop.")),

 "exam_neck": always(ex("Neck veins flat. No carotid bruit. Trachea central.", abnormal=False)),

 "exam_card": [
   {"when": WORSE, "value": ex(
     "Very loud harsh systolic murmur, left sternal edge. Louder with Valsalva. No rub. No edema.")},
   {"when": OBS, "value": ex(
     "Loud harsh systolic murmur, left sternal edge. Louder with Valsalva. No rub.")},
   {"when": STEADY, "value": ex(
     "Soft systolic murmur, left sternal edge. No rub. No edema.")},
   {"when": None, "value": ex(
     "Harsh systolic murmur, left sternal edge. Louder with Valsalva, softer legs raised. No rub.")}],

 "exam_pulm": always(ex("Clear to both bases. No crackles or wheeze.", abnormal=False)),

 "exam_abd": always(ex("Soft, non-tender. No pulsatile mass.", abnormal=False)),

 "exam_back": always(ex("No spinal or flank tenderness.", abnormal=False)),

 "exam_msk": always(ex("No calf swelling or tenderness. Pulses equal in both arms.", abnormal=False)),

 "exam_skin": [
   {"when": STEADY, "value": ex("Pale. Sweating has settled. No rash.")},
   {"when": None, "value": ex("Pale and sweating. No rash.")}],

 "exam_neuro": [
   {"when": WORSE, "value": ex("Drowsy and confused about the time. GCS 14. Moves all limbs.")},
   {"when": None, "value": ex("Alert, oriented. GCS 15. No focal deficit.", abnormal=False)}],

 "exam_psych": [
   {"when": WORSE, "value": ex("Confused and frightened. Asks for her husband.")},
   {"when": None, "value": ex("Tearful and frightened. Oriented. Says she wants this to stop.")}],
}

GENERAL_STATUS = {
 "authoring_note": "Section 9.3. Consistent with exam_neuro and each phase's appearance values.",
 "rules": [
   {"when": WORSE, "value": gs("Gray, cold and confused. Barely speaking. GCS 14.")},
   {"when": OBS, "value": gs("Gray and sweating, says she feels faint. Fist on her chest. GCS 15.")},
   {"when": STEADY, "value": gs("Color better, sitting back, pain easing. GCS 15.")},
   {"when": None, "value": gs("Pale and sweating, sitting upright, fist on her chest. Daughter at the bedside. GCS 15.")},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED. Sweating is drawn until she is steadied. Nothing else is authored.",
 "rules": [{"when": None, "value": {}}],
 "also": [{"when": "NOT " + STEADY + " AND NOT phase is case_complete", "addons": ["sweating"]}],
}

# ============================================================== LABORATORY
LACTATE = {"presentation": "2.6", "obstructed": "3.4", "shock_worse": "5.8", "shock_untreated": "5.8", "steadied": "3.6"}
ORDER = ["obstructed", "shock_worse", "shock_untreated", "steadied"]


def by_phase(make):
    rules = [{"when": "phase is " + p, "value": make(p)} for p in ORDER]
    rules.append({"when": None, "value": make("presentation")})
    return rules


def gas(p):
    """Bicarbonate from the chemistry (22 in every phase) and lactate from the lactate key."""
    d = panel([comp("HCO3", "22", "mEq/L", "22-26", False),
               comp("Lactate", LACTATE[p], "mmol/L", "0.5-2.0", True)])
    d["verify"] = (DERIVED + "HCO3 equals the bicarbonate on this pack's chemistry, with the "
                   "catalog's interval for a gas. Lactate equals this pack's lactate key in "
                   "the same phase. pH, pCO2, pO2, base excess and oxygen saturation are "
                   "left out on purpose and need a physician.")
    return d


LABS = {
 "authoring_note": (
   "Section 11.4. The pattern a reviewer should check: a raised troponin, a very high natriuretic "
   "peptide, and mild "
   "prerenal changes from five days of poor intake. Every value needs a signature."),

 # No comment on either. A comment may not name the diagnosis or quote another result
 # (authoring 9.4). The interpretation is in each study's debrief note.
 "troponin_t": {"changes_with_state": False, "rules": always(val(
     "Troponin T, high sensitivity", "186", "ng/L", "< 14", True))},

 "nt_probnp": {"changes_with_state": False, "rules": always(val(
     "NT-proBNP", "5200", "pg/mL", "< 125", True))},

 "lactate": {"changes_with_state": True, "rules": by_phase(
     lambda p: val("Lactate", LACTATE[p], "mmol/L", "0.5-2.0", True))},

 "basic_chemistry_chem_7": {"changes_with_state": False, "rules": always(panel([
     comp("Sodium", "141", "mEq/L", "135-145", False),
     comp("Potassium", "3.9", "mEq/L", "3.5-5.0", False),
     comp("Chloride", "104", "mEq/L", "98-107", False),
     comp("Bicarbonate", "22", "mEq/L", "22-29", False),
     comp("BUN", "29", "mg/dL", "7-20", True),
     comp("Creatinine", "1.1", "mg/dL", "0.6-1.2", False),
     comp("Glucose", "148", "mg/dL", "70-140 (random)", True)],
     comment="BUN raised with a normal creatinine."))},

 # ---- Derived keys (catalog audit 5.1 to 5.3). The catalog defaults showed a normal
 # lactate of 1.2 on a gas in shock and a capillary glucose of 94 beside a chemistry
 # glucose of 148. Each row below repeats a number this pack already authors. No pH, pCO2,
 # pO2 or base excess is authored: a pH would be a new clinical number, and the others
 # cannot be derived without one. They are listed for the physician in TAKO-SEED.md.
 "venous_blood_gas": {"changes_with_state": True, "rules": by_phase(lambda p: gas(p))},
 "arterial_blood_gas": {"changes_with_state": True, "rules": by_phase(lambda p: gas(p))},

 "fingerstick_blood_sugar": {"changes_with_state": False, "rules": always(dict(
     val("Capillary glucose", "148", "mg/dL", "70-140 (random)", True),
     verify=DERIVED + "Equal to the glucose on this pack's chemistry."))},
}

IMAGING = {
 "authoring_note": (
   "Section 9.4. Findings only: no report names takotsubo or obstruction. No report "
   "carries a comment, because the interface never shows a comment on a report. The "
   "interpretation is in each study's debrief note. The ECG report quotes no rate, because "
   "three vital effects on the heart rate have no end (authoring 9.4)."),

 "ecg_12_lead": {"changes_with_state": False, "rules": always(report(
     "Sinus tachycardia. ST elevation 2 to 3 mm in V2 to V5 and 1 mm in II. ST "
     "depression in aVR. No ST elevation in V1. No ST depression elsewhere. QRS 92 ms, "
     "QTc 470 ms."))},

 # Authored from what this pack's own notes say about the film: clear lungs, a normal
 # mediastinum and a normal heart size. The catalog default did not mention the mediastinum.
 "xr_chest": {"changes_with_state": False, "rules": always(dict(
     report("Lungs clear. Mediastinum not widened. Heart size normal.", abnormal=False),
     verify=DERIVED + "Restates the chest film debrief note and the catalog default."))},

 "ultrasound_cardiac": {"changes_with_state": True, "rules": [
   {"when": STEADY, "value": report(
     "Apex and mid ventricle do not contract and bulge in systole. Base contracts "
     "vigorously. Ejection fraction about 30 percent. Anterior mitral leaflet moves only "
     "slightly toward the septum in systole. No pericardial effusion. Right ventricle "
     "normal.")},
   {"when": None, "value": report(
     "Apex and mid ventricle do not contract and bulge in systole. Base contracts "
     "vigorously. Ejection fraction about 30 percent. Anterior mitral leaflet moves toward "
     "the septum in systole. No pericardial effusion. Right ventricle normal. Inferior "
     "vena cava small.")}]},

 "ultrasound_lung": {"changes_with_state": False, "rules": always(report(
     "Lung sliding present on both sides. A-line pattern. No B-lines. No effusion.",
     abnormal=False))},
}

# ============================================================== CONSULTANTS
# Most specific first. The cardiologist never quotes a study that has not resulted. On the
# directing physician's instruction the cardiologist gives the plan outright and, ninety
# seconds after being called with a low pressure, arrives and carries it out (case_1).
COMING = " I'm coming down to take over."
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. The cardiologist cannot be reached until the ECG and the echo have both "
   "resulted (a prerequisite on the consult), so every rule may speak about both and no "
   "pending tier is needed. Rules are ordered steadied, on an inotrope, then by what is "
   "already running. The catheterization laboratory cannot be activated until the "
   "twelve-lead has resulted (two prerequisites on the action, 7 October 2026), so its one "
   "reply may speak about the ECG. Its pending tier is the second prerequisite's failure "
   "message, which the nurse says while the tracing is still printing."),

 "consult_cardiology": [
   {"when": STEADY,
    "value": ("Cardiologist: Good, that's holding. Keep the vasoconstrictor where it is, no "
              "nitrates and nothing inotropic. The lab is ready, so bring her up on the "
              "monitor.")},
   {"when": ACTIVE,
    "value": ("Cardiologist: Stop that inotrope now. You're driving the obstruction. Then give "
              "250 to 500 of crystalloid and start phenylephrine or vasopressin." + COMING)},
   {"when": "(" + LOW + ") AND " + FLUID + " AND NOT " + VASO,
    "value": ("Cardiologist: The fluid was right. Now start phenylephrine or vasopressin. No "
              "dobutamine, no epinephrine, no nitrates." + COMING)},
   {"when": "(" + LOW + ") AND " + VASO + " AND NOT " + FLUID,
    "value": ("Cardiologist: Good choice of pressor. Add 250 to 500 of crystalloid, because "
              "she's dry. No inotropes and no nitrates." + COMING)},
   {"when": LOW,
    "value": ("Cardiologist: A still apex, a hard-working base and that murmur. She's "
              "obstructing. No nitrates or inotropes. Give 250 to 500 of crystalloid and start "
              "phenylephrine or vasopressin. She still comes to the lab." + COMING)},
   {"when": None,
    "value": ("Cardiologist: Sorry, I was scrubbed. ST elevation with ongoing pain is the lab. "
              "Activate and give aspirin. That echo worries me for obstruction. Hold nitrates "
              "and inotropes, and if her pressure falls give fluid and start phenylephrine.")}],

 "consult_activate_cath_lab": [
   {"when": None,
    "value": ("Catheterization laboratory: Activated. The team is coming in and the "
              "interventional cardiologist has the ECG. We will call when the table is "
              "ready. Keep her monitored and send her with aspirin on board.")}],

 "consult_critical_care": [
   {"when": STEADY,
    "value": ("Intensivist: She goes to the catheterization laboratory first. Tell them we "
              "have a bed for her afterwards and I'll see her there.")},
   {"when": None,
    "value": ("Intensivist: A low pressure with ST elevation needs cardiology at the "
              "bedside more than it needs me. Have you called them?")}],
}
