"""DKA part 3: exam findings, general status, the figure, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT. No physician supplied a number, a finding or a
reference interval. Reference intervals are the catalog's where it has one.

A repeat study only changes when the phase or a flag has changed (authoring 11.4), so the
chemistry, the gas, the glucose and the ECG are keyed to both. Phase rules come before
flag rules in every list.

Results hold findings only (authoring 11.4). The one comment left is a caption on the
chemistry. Every interpretive sentence that used to sit in a comment is now in the
debrief note of that study's action in case_2_actions.py.

No report and no exam line quotes a heart rate (authoring 6.1, 11.2 and 11.4). The fluid
effect takes ten off the rate and never ends, so a quoted rate would disagree with the
monitor for the rest of the case. In the treated phase the monitor reads 104 without
fluid and 94 with it, so that phase's report says sinus rhythm and its exam lines do not
say fast.
"""

PRES = "phase is presentation"
REPL = "phase is potassium_replaced"
TREATED = "phase is treated"
FALLING = "phase is potassium_falling"
RECOV = "phase is recovering"
FLUID = "flag fluids_given set"
BICARB = "flag bicarb_given set"
MAG = "flag mag_given set"
ONDAN = "flag ondansetron_given set"
CHEM_R = "study basic_chemistry_chem_7 resulted"
CHEM_O = "study basic_chemistry_chem_7 ordered"
GAS_R = "(study venous_blood_gas resulted OR study arterial_blood_gas resulted)"

VERIFY = "Model output, not from a physician or a laboratory reference. [UNVERIFIED]"


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
   "Section 11.2. Routing follows the catalog map: capillary refill and pulse on "
   "exam_circ, work of breathing on exam_breath, lung sounds on exam_pulm, limb power and "
   "reflexes on exam_neuro, turgor and injection sites on exam_skin."),

 "exam_airway": always(ex("Patent. Speaking in full sentences.", abnormal=False)),

 "exam_breath": [
   {"when": TREATED, "value": ex("Breathing easier, rate about 20. No accessory muscle use.", abnormal=False)},
   {"when": None, "value": ex("Deep, slightly fast breathing. No accessory muscle use.")}],

 "exam_circ": [
   {"when": FALLING, "value": ex("Pulse fast with occasional dropped beats. Capillary refill 3 seconds. Hands cool.")},
   {"when": TREATED, "value": ex("Pulse regular, good volume. Capillary refill 2 seconds. Hands warm.", abnormal=False)},
   {"when": FLUID, "value": ex("Pulse fast, regular. Capillary refill 2 seconds. Hands warming.")},
   {"when": None, "value": ex("Pulse fast, regular, low volume. Capillary refill 3 seconds. Hands cool.")}],

 "exam_heent": always(ex("Lips and tongue dry. Fruity smell on the breath. Pupils equal and reactive.")),

 "exam_neck": always(ex("Neck veins flat. Supple, no stiffness.", abnormal=False)),

 "exam_card": [
   {"when": FALLING, "value": ex("Fast with occasional extra beats. No murmur. No edema.")},
   {"when": TREATED, "value": ex("Regular. No murmur. No edema.", abnormal=False)},
   {"when": None, "value": ex("Fast and regular. No murmur. No edema.", abnormal=False)}],

 "exam_pulm": always(ex("Clear to both bases. No crackles or wheeze.", abnormal=False)),

 "exam_abd": [
   {"when": TREATED, "value": ex("Soft. Tenderness settling. No guarding. Bowel sounds active.", abnormal=False)},
   {"when": None, "value": ex("Soft. Mild diffuse tenderness, no guarding or rebound. Old appendectomy scar. Bowel sounds active.")}],

 "exam_gu": always(ex("No suprapubic or flank tenderness.", abnormal=False)),

 "exam_back": always(ex("No spinal or flank tenderness.", abnormal=False)),

 "exam_msk": always(ex("No calf swelling or tenderness. No joint swelling.", abnormal=False)),

 "exam_skin": always(ex("Dry, reduced turgor. No rash. Injection sites on the abdomen clean. Feet intact.")),

 "exam_neuro": [
   {"when": FALLING, "value": ex("Proximal weakness in arms and legs, 4 of 5. Reflexes reduced. Alert, oriented, GCS 15.")},
   {"when": None, "value": ex("Alert, oriented, GCS 15. Power 5 of 5. Reflexes normal.", abnormal=False)}],

 "exam_psych": always(ex("Tired and cooperative. Oriented. Mood normal.", abnormal=False)),
}

GENERAL_STATUS = {
 "authoring_note": "Section 11.3. Consistent with exam_neuro and each phase's appearance values.",
 "rules": [
   {"when": FALLING, "value": gs("Lying flat, says her arms and legs are heavy. Alert and frightened. GCS 15.")},
   {"when": TREATED, "value": gs("Sitting up, color better, no longer retching. GCS 15.", abnormal=False)},
   {"when": None, "value": gs("Tired and dry, vomit bowl in her lap, breathing deeply. Alert and talking. GCS 15.")},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED. Nothing beyond the phase's own distress and alertness is drawn.",
 "rules": [{"when": None, "value": {}}],
}

# ============================================================== LABORATORY
# One table of numbers per state. "pres" is arrival with nothing given.
#            Na    K     Cl    HCO3  BUN  Cr     Glu
CHEM = {
 "pres":        (133, "3.1", 99, 16, 24, "1.2", 348),
 "pres_fluid":  (134, "3.0", 101, 16, 22, "1.1", 318),
 "pres_bicarb": (135, "2.9", 99, 18, 24, "1.2", 345),
 "pres_both":   (136, "2.9", 101, 18, 22, "1.1", 316),
 "replaced":    (134, "3.6", 102, 15, 22, "1.1", 320),
 "treated":     (135, "3.7", 104, 18, 20, "1.0", 268),
 "falling":     (134, "2.6", 101, 17, 22, "1.1", 262),
 "recovering":  (134, "3.6", 102, 17, 22, "1.1", 285),
}
# A caption, not a reading (authoring 11.4). The same words in every state.
CHEM_CAPTION = "Anion gap calculated without potassium."
FINGERSTICK = {"pres": 342, "pres_fluid": 314, "pres_bicarb": 342, "pres_both": 314,
               "replaced": 318, "treated": 266, "falling": 258, "recovering": 282}
#           pH      HCO3  BE     lactate.  The pCO2 is calculated from the pH and the
# bicarbonate by the Henderson-Hasselbalch equation, so each row is self-consistent.
GAS = {
 "pres":        ("7.27", 16, "-9", "1.8"),
 "pres_fluid":  ("7.27", 16, "-9", "1.6"),
 "pres_bicarb": ("7.30", 18, "-7", "1.8"),
 "pres_both":   ("7.30", 18, "-7", "1.6"),
 "replaced":    ("7.26", 15, "-10", "1.6"),
 "treated":     ("7.30", 18, "-7", "1.4"),
 "falling":     ("7.29", 17, "-8", "1.6"),
 "recovering":  ("7.28", 17, "-8", "1.6"),
}
BHB = {"pres": "4.2", "pres_fluid": "4.1", "pres_bicarb": "4.2", "pres_both": "4.1",
       "replaced": "4.6", "treated": "3.1", "falling": "3.4", "recovering": "3.8"}


def pco2(ph, hco3):
    return int(round(hco3 / (0.03 * 10 ** (float(ph) - 6.1))))


def by_state(make):
    """Phase rules first, then the arrival phase split by what has been given."""
    return [
      {"when": REPL, "value": make("replaced")},
      {"when": TREATED, "value": make("treated")},
      {"when": FALLING, "value": make("falling")},
      {"when": RECOV, "value": make("recovering")},
      {"when": BICARB + " AND " + FLUID, "value": make("pres_both")},
      {"when": BICARB, "value": make("pres_bicarb")},
      {"when": FLUID, "value": make("pres_fluid")},
      {"when": None, "value": make("pres")},
    ]


def chem(s):
    na, k, cl, hco3, bun, cr, glu = CHEM[s]
    gap = na - cl - hco3
    return panel([
      comp("Sodium", str(na), "mEq/L", "135-145", na < 135),
      comp("Potassium", k, "mEq/L", "3.5-5.0", float(k) < 3.5),
      comp("Chloride", str(cl), "mEq/L", "98-107", False),
      comp("Bicarbonate", str(hco3), "mEq/L", "22-29", True),
      comp("BUN", str(bun), "mg/dL", "7-20", bun > 20),
      comp("Creatinine", cr, "mg/dL", "0.5-1.1 (F)", float(cr) > 1.1),
      comp("Glucose", str(glu), "mg/dL", "70-140 (random)", True),
      comp("Anion gap", str(gap), "mEq/L", "8-12", gap > 12)],
      comment=CHEM_CAPTION)


def gas(s):
    ph, hco3, be, lac = GAS[s]
    return panel([
      comp("pH", ph, "", "7.31-7.41", float(ph) < 7.31),
      comp("pCO2", str(pco2(ph, hco3)), "mmHg", "41-51", True),
      comp("HCO3", str(hco3), "mEq/L", "22-26", True),
      comp("Base excess", be, "mEq/L", "-2 to +2", True),
      comp("Lactate", lac, "mmol/L", "0.5-2.0", False)])


def art_gas(s):
    ph, hco3, be, lac = GAS[s]
    aph = "%.2f" % (float(ph) + 0.03)
    return panel([
      comp("pH", aph, "", "7.35-7.45", True),
      comp("pCO2", str(pco2(aph, hco3 - 1)), "mmHg", "35-45", True),
      comp("pO2", "98", "mmHg", "80-100", False),
      comp("HCO3", str(hco3 - 1), "mEq/L", "22-26", True),
      comp("Base excess", be, "mEq/L", "-2 to +2", True)])


LABS = {
 "authoring_note": (
   "Section 11.4. The pattern a reviewer should check: a glucose near 350, an anion gap of "
   "18, a pH of 7.27, ketones of 4.2 mmol/L, and a potassium of 3.1 with a magnesium of "
   "1.5 from two days of gastrointestinal loss. The phosphate is normal. Every value needs a signature. The anion "
   "gap is printed as a component and is calculated without potassium."),

 "basic_chemistry_chem_7": {"changes_with_state": True, "rules": by_state(chem)},

 "venous_blood_gas": {"changes_with_state": True, "rules": by_state(gas)},

 "arterial_blood_gas": {"changes_with_state": True, "rules": by_state(art_gas)},

 "fingerstick_blood_sugar": {"changes_with_state": True, "rules": by_state(
     lambda s: val("Capillary glucose", str(FINGERSTICK[s]), "mg/dL", "70-140 (random)", True))},

 "beta_hydroxybutyrate": {"changes_with_state": True, "rules": by_state(
     lambda s: val("Beta-hydroxybutyrate", BHB[s], "mmol/L", "< 0.6", True))},

 "magnesium_level": {"changes_with_state": True, "rules": [
     {"when": MAG, "value": val("Magnesium", "2.1", "mg/dL", "1.7-2.2", False)},
     {"when": None, "value": val("Magnesium", "1.5", "mg/dL", "1.7-2.2", True)}]},

 "phosphate_level": {"changes_with_state": False, "rules": always(
     val("Phosphate", "3.4", "mg/dL", "2.5-4.5", False))},

 "lactate": {"changes_with_state": False, "rules": always(
     val("Lactate", "1.8", "mmol/L", "0.5-2.0", False))},

 "lipase": {"changes_with_state": False, "rules": always(
     val("Lipase", "48", "U/L", "10-140", False))},

 "osmolality": {"changes_with_state": False, "rules": always(
     val("Serum osmolality", "295", "mOsm/kg", "275-295", False))},

 "complete_blood_count_cbc": {"changes_with_state": False, "rules": always(panel([
     comp("WBC", "13.4", "x10^9/L", "4.0-11.0", True),
     comp("Hemoglobin", "14.9", "g/dL", "13.5-17.5 (M), 12.0-16.0 (F)", False),
     comp("Hematocrit", "45", "%", "41-53 (M), 36-46 (F)", False),
     comp("Platelets", "310", "x10^9/L", "150-400", False),
     comp("MCV", "88", "fL", "80-100", False)]))},

 "urinalysis": {"changes_with_state": False, "rules": always(panel([
     comp("Color", "Dark yellow", "", "yellow", False),
     comp("Clarity", "Clear", "", "clear", False),
     comp("Specific gravity", "1.030", "", "1.005-1.030", False),
     comp("pH", "5.0", "", "4.5-8.0", False),
     comp("Protein", "Trace", "", "negative", True),
     comp("Glucose", "3+", "", "negative", True),
     comp("Ketones", "Large", "", "negative", True),
     comp("Blood", "Negative", "", "negative", False),
     comp("Leukocyte esterase", "Negative", "", "negative", False),
     comp("Nitrite", "Negative", "", "negative", False),
     comp("WBC", "0-2", "/hpf", "0-5", False),
     comp("RBC", "0-2", "/hpf", "0-2", False),
     comp("Bacteria", "None seen", "", "none", False)]))},

 "urine_hcg_qualitative": {"changes_with_state": False, "rules": always(
     report("Negative.", abnormal=False))},

 "serum_hcg_quantitative": {"changes_with_state": False, "rules": always(
     val("Serum hCG", "< 5", "mIU/mL", "< 5 (not pregnant)", False))},
}

# ============================================================== IMAGING AND ECG
QTC = {"pres": 460, "replaced": 450, "treated": 445, "falling": 520, "recovering": 450}
# No rate in any report. The treated phase reads 94 on the monitor after fluid, so its
# report says sinus rhythm. Every other phase is above 100 with or without fluid.
ECG_TEXT = {
 "pres": ("Sinus tachycardia. Subtle T wave flattening in the chest leads. Small U "
          "waves in V2 and V3. No ST elevation or depression. QRS 88 ms, QTc about %d ms."),
 "replaced": ("Sinus tachycardia. T waves fuller than before. Small U waves in V2 "
              "and V3. No ST change. QRS 88 ms, QTc %d ms."),
 "treated": ("Sinus rhythm. T waves normal. Small U waves in V2 and V3. No ST "
             "change. QRS 88 ms, QTc %d ms."),
 "falling": ("Sinus tachycardia with occasional ventricular ectopic beats. T waves "
             "flat. Prominent U waves in V2 to V5, taller than the T waves. ST depression "
             "0.5 mm in the lateral leads. QRS 88 ms, QTc about %d ms."),
 "recovering": ("Sinus tachycardia. No ectopic beats. T waves fuller. Small U waves "
                "in V2 and V3. QRS 88 ms, QTc %d ms."),
}


def ecg(s, ondansetron=False):
    q = QTC[s] + (5 if ondansetron else 0)
    return report(ECG_TEXT[s] % q, abnormal=True)


ECG_RULES = []
for _when, _s in [(REPL, "replaced"), (TREATED, "treated"), (FALLING, "falling"), (RECOV, "recovering")]:
    ECG_RULES.append({"when": _when + " AND " + ONDAN, "value": ecg(_s, True)})
    ECG_RULES.append({"when": _when, "value": ecg(_s)})
ECG_RULES.append({"when": ONDAN, "value": ecg("pres", True)})
ECG_RULES.append({"when": None, "value": ecg("pres")})

IMAGING = {
 "authoring_note": (
   "Section 11.4. The chest film and the abdominal CT are left to the catalog defaults, "
   "which are normal, and that is intended. The ECG report is findings only and quotes "
   "no rate. Each phase's monitor block in case_1_shell.py carries the same QRS and QTc "
   "as its report here, without the ondansetron increment."),
 "ecg_12_lead": {"changes_with_state": True, "rules": ECG_RULES},

 # The catalog default says the vena cava is of normal caliber. This pack credits
 # hypovolemia and authors a dry mouth, reduced turgor, flat neck veins and a fast pulse,
 # so the default contradicted it (catalog audit 5.11). The wording is the one TSS uses
 # for a dry patient. One value in every state, like the neck veins and the skin.
 "ultrasound_cardiac": {"changes_with_state": False, "rules": always({
     "kind": "report", "abnormal": True,
     "report": ("Hyperdynamic left ventricle. No pericardial effusion. Right ventricle not "
                "dilated. Inferior vena cava small and collapsing with each breath."),
     "verify": ("Derived by a model on 7 October 2026 from the pack's other values (dry "
                "mucosa, reduced turgor, flat neck veins, a fast pulse and a credited "
                "diagnosis of hypovolemia). No new clinical claim is intended. It does not "
                "change after fluid, which is a simplification. [UNVERIFIED]")})},
}

# ============================================================== CONSULTANTS
# Most specific first. No line names a value. A line that reads a result sits on a rule
# that tests the study resulted, and says only what is true of every variant of that
# result (authoring 11.5). `study S resulted` means a result exists, not that it was
# sent in this phase, so the falling-phase lines read no result at all: they describe
# what the room can see and ask for the studies.
ENDO_PLAN = (
  "Endocrinologist: Her potassium is under 3.5, and that changes the order. Insulin "
  "waits. Fluids, and intravenous potassium on a monitor, 20 to 40 an hour, which on "
  "most units means a central line or two peripheral lines. Check a magnesium. Repeat "
  "the potassium every hour or two, and start insulin once it's 3.5 or more. After that "
  "keep 20 to 30 in each liter. No bolus and no bicarbonate.")
ICU_WORKUP = "Intensivist: Call me back when you have a gas and a chemistry."
CONSULTANTS = {
 "authoring_note": (
   "Section 11.5. Rules are ordered by phase, then by study state. The endocrinologist "
   "and the intensivist each have a tier for both studies back, one for each study "
   "alone, a pending tier and a default. In the arrival phase every variant of the "
   "chemistry reads a potassium under 3.5 (3.1, 3.0 or 2.9), which is all the "
   "endocrinologist says of it. Grading the ketoacidosis as mild needs the gas, so that "
   "word sits behind the gas. The phase rules for the ready and treated phases give "
   "advice and read no result."),

 "consult_endocrinology": [
   {"when": FALLING,
    "value": ("Endocrinologist: Hold the insulin now. Weakness and a fluttering heart "
              "after insulin is a falling potassium until a level says otherwise. Give "
              "intravenous potassium on the monitor, give magnesium, get a twelve-lead "
              "and send a chemistry. Insulin goes back on when the potassium is 3.5 or "
              "more.")},
   {"when": TREATED + " AND flag basal_given set",
    "value": ("Endocrinologist: Good, and I'm glad the glargine is back in. Glucose every "
              "hour, potassium every one to two hours at first, and 20 to 30 of potassium "
              "in each liter. When the glucose is under 250 change to fluid with dextrose "
              "and keep the insulin going. Don't stop insulin because the sugar looks "
              "better.")},
   {"when": TREATED,
    "value": ("Endocrinologist: Good. Glucose every hour, potassium every one to two "
              "hours at first, and 20 to 30 of potassium in each liter. When the glucose is under "
              "250 change to fluid with dextrose and keep the insulin going. Don't stop "
              "insulin because the sugar looks better. Give her usual long-acting "
              "insulin tonight, and well before any infusion comes off.")},
   {"when": REPL + " OR " + RECOV,
    "value": ("Endocrinologist: If the repeat potassium is 3.5 or more, start insulin now. "
              "An infusion at 0.1 units per kilo an hour. Subcutaneous rapid-acting "
              "insulin is an option if the gas says this is mild. No bolus. Keep 20 to "
              "30 of potassium in each liter.")},
   {"when": CHEM_R + " AND " + GAS_R,
    "value": (ENDO_PLAN + " It's mild on the gas, so an infusion at 0.1 units per kilo "
              "an hour or subcutaneous rapid-acting insulin both work.")},
   {"when": CHEM_R,
    "value": ENDO_PLAN + " Get a gas so we can grade this."},
   {"when": CHEM_O,
    "value": ("Endocrinologist: The chemistry is still in the lab. Call me back with the "
              "potassium. I don't want insulin started until we know it.")},
   {"when": None,
    "value": ("Endocrinologist: I need numbers before I can help. What's her glucose, "
              "her gas and her potassium?")}],

 "consult_critical_care": [
   {"when": FALLING,
    "value": ("Intensivist: She's weak with extra beats after insulin. Hold it, replace "
              "her potassium on a monitor, and get a chemistry and a twelve-lead now. If "
              "she settles she can go to step-down.")},
   {"when": CHEM_R + " AND " + GAS_R,
    "value": ("Intensivist: Mild ketoacidosis in an alert patient doesn't need us. A "
              "step-down bed with telemetry can run her potassium and her insulin.")},
   {"when": CHEM_R,
    "value": "Intensivist: I can see the chemistry. I need a gas before I can say how sick she is."},
   {"when": GAS_R,
    "value": "Intensivist: I can see the gas. I need the chemistry before I can say where she goes."},
   {"when": CHEM_O + " OR study venous_blood_gas ordered OR study arterial_blood_gas ordered",
    "value": "Intensivist: Her labs aren't back. " + ICU_WORKUP[len("Intensivist: "):]},
   {"when": None,
    "value": ("Intensivist: I'm not sure why I'm being called. " + ICU_WORKUP[len("Intensivist: "):])}],
}
