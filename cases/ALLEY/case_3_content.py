"""ALLEY part 3: exam findings, general status, the figure, pupils, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT except the arrival numbers and the tier ladder,
which come from the owner's case structure (11 November 2026). Reference intervals are the
catalog's where it has one.

Results are keyed to the phase and, inside the untreated phases, to the bicarbonate
overlay and the sedation overlay, because a result never sees a vital effect (authoring
16). Phase rules come first. The sedation flag is timed, so in each phase the sedated
variant sits above the plain one.

Owner, 11 November 2026: the venous and arterial gases show the same numbers.

No report and no exam line quotes a heart rate or a respiratory rate: the fluid, bicarbonate
and sedation effects move them.
"""

U0 = "phase is presentation"
U1 = "phase is drifting"
U2 = "phase is untreated_floor"
H0 = "phase is held_early"
H1 = "phase is held_mid"
H2 = "phase is held_late"
IMP = "phase is improving"
BUF = "flag bicarb_acting set"
SED = "flag sedated set"
INTUB = "flag intubated set"
R1 = "flag reached_u1 set"
R2 = "flag reached_u2 set"
GAS_R = "(study venous_blood_gas resulted OR study arterial_blood_gas resulted)"
CHEM_R = "study basic_chemistry_chem_7 resulted"
OSM_R = "study osmolality resulted"
FOMEP = "flag fomepizole_given set"
ASKED_DRINK = "action interview_topic_alcohol taken"

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


def report(text, abnormal=True):
    return {"kind": "report", "abnormal": abnormal, "report": text, "verify": VERIFY}


def always(v):
    return [{"when": None, "value": v}]


# ============================================================== EXAM
VISION_EXAM = [
  (R2, "Hand motion only at the bedside. Pupils 6 mm, barely reactive. Optic discs hyperemic and swollen. Mucous membranes dry. Faint alcohol odor. No scalp wound, swelling or skull tenderness. No nystagmus."),
  (R1, "Cannot read the monitor from the bed, counts fingers close up. Pupils 5 mm, sluggish. Optic discs hyperemic. Mucous membranes dry. Faint alcohol odor. No scalp wound, swelling or skull tenderness. No nystagmus."),
  (None, "Counts fingers at the bedside. Pupils 5 mm, sluggish. Optic discs hyperemic. Mucous membranes dry. Faint alcohol odor. No scalp wound, swelling or skull tenderness. No nystagmus."),
]

EXAM = {
 "authoring_note": (
   "Section 9.2. Routing follows the catalog map: work of breathing on exam_breath, lung "
   "sounds on exam_pulm, pulses and refill on exam_circ, acuity, pupils and fundoscopy on "
   "exam_heent, consciousness on exam_neuro. The breathing pattern is described, not named."),

 "exam_airway": [
   {"when": INTUB, "value": ex("Endotracheal tube in place.")},
   {"when": SED, "value": ex("Snoring. Airway opens with a chin lift.")},
   {"when": None, "value": ex("Patent. Talking, slurred.", abnormal=False)}],

 "exam_breath": [
   {"when": INTUB, "value": ex("Ventilated. Chest rises with each breath.")},
   {"when": SED, "value": ex("Slower and shallower than before. No accessory muscle use.")},
   {"when": IMP, "value": ex("Deep breaths, easier than before. No accessory muscle use.")},
   {"when": U2 + " OR " + H2, "value": ex("Deep, fast, labored breathing with accessory muscle use.")},
   {"when": None, "value": ex("Deep, fast, regular breaths. No accessory muscle use.")}],

 "exam_circ": always(ex("Warm hands. Radial pulses strong and fast. Capillary refill 2 seconds.")),

 "exam_heent": [{"when": w, "value": ex(t)} for w, t in VISION_EXAM],

 "exam_pulm": always(ex("Clear to both bases. No crackles or wheeze.", abnormal=False)),

 "exam_abd": always(ex("Soft. Mild epigastric tenderness. No guarding or rebound.")),

 "exam_skin": always(ex("No wounds, bruises or signs of trauma. Not sweating. Dry.", abnormal=False)),

 "exam_neuro": [
   {"when": INTUB, "value": ex("Sedated on the ventilator. Pupils sluggish.")},
   {"when": SED, "value": ex("Hard to rouse, groans to a loud voice. GCS about 12. No focal signs.")},
   {"when": U2 + " OR " + H2, "value": ex("Rousable to voice, confused, slurred. GCS 13. Reaches past objects. Moves all limbs. No tremor. No asterixis.")},
   {"when": None, "value": ex("Drowsy, rouses easily, slurred speech, unsteady. GCS 14. Moves all limbs, no focal weakness. No tremor. No asterixis.")}],

 "exam_psych": [
   {"when": SED, "value": ex("Too drowsy to assess.")},
   {"when": None, "value": ex("Cooperative, not agitated. No hallucinations.", abnormal=False)}],
}

GENERAL_STATUS = {
 "authoring_note": "Section 9.3. Consistent with exam_neuro and each phase's appearance values.",
 "rules": [
   {"when": INTUB, "value": gs("Intubated and sedated.")},
   {"when": SED, "value": gs("Snoring, hard to rouse, breathing slower and shallower. GCS about 12.")},
   {"when": IMP, "value": gs("Still slurred and unsteady, breathing easier, talking more. GCS 14.")},
   {"when": U2 + " OR " + H2, "value": gs("Working to breathe, talking in short phrases, confused. GCS 13.")},
   {"when": U1 + " OR " + H1, "value": gs("Dozes off mid-sentence, rubbing his eyes. Breathing deep and fast. GCS 14.")},
   {"when": None, "value": gs("Disheveled, dozing, rouses easily, slurred speech. Breathing deep and fast. GCS 14.")},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED. Eyes closed only when sedated. Work of breathing by phase.",
 "verify": "Check that the deep breathing reads as increased and that the sedated figure reads as asleep.",
 "rules": [
   {"when": INTUB, "value": {"work_of_breathing": "normal"}},
   {"when": SED, "value": {"eyes": "closed", "work_of_breathing": "normal"}},
   {"when": U2 + " OR " + H2, "value": {"work_of_breathing": "severe"}},
   {"when": None, "value": {"work_of_breathing": "increased"}},
 ],
}

PUPILS = {
 "iris": "#5a4632",
 "verify": "Owner's structure: 5 mm sluggish, 6 mm minimally reactive at the worst vision tier. Model output.",
 "rules": [
   {"when": R2, "value": {"state": "dilated", "size_mm": 6, "reaction": "sluggish"}},
   {"when": None, "value": {"state": "dilated", "size_mm": 5, "reaction": "sluggish"}},
 ],
}

# ============================================================== LABORATORY
#         pH      pCO2  HCO3  lactate  pO2 (arterial, room air)
GAS = {
 "u0":     ("7.19", 19, 7, "3.6", 112),
 "u1":     ("7.15", 18, 6, "4.2", 114),
 "u2":     ("7.12", 16, 5, "4.6", 116),
 "buf":    ("7.28", 24, 11, None, 106),
 "imp":    ("7.29", 26, 12, "3.6", 104),
 "u0_sed": ("7.07", 25, 7, "3.6", 96),
 "u1_sed": ("7.02", 24, 6, "4.2", 98),
 "u2_sed": ("6.98", 22, 5, "4.6", 98),
 "buf_sed": ("7.19", 30, 11, None, 92),
 "imp_sed": ("7.20", 32, 12, "3.6", 90),
}
TIER_LACTATE = {"u0": "3.6", "u1": "4.2", "u2": "4.6"}

#         Na   K      Cl   HCO3 BUN Cr     Glu
CHEM = {
 "u0":  (140, "4.9", 103, 7, 14, "1.0", 90),
 "u1":  (140, "5.1", 103, 6, 14, "1.0", 90),
 "u2":  (140, "5.2", 103, 5, 14, "1.0", 90),
 "buf": (143, "4.5", 103, 11, 14, "1.0", 90),
 "imp": (143, "4.5", 103, 12, 14, "1.0", 90),
}
OSM = {"u0": 328, "u1": 327, "u2": 326, "buf_u0": 334, "buf_u1": 333, "buf_u2": 332, "imp": 333}


def gas(key, lactate=None, arterial=False):
    ph, pco2, hco3, lac, po2 = GAS[key]
    lac = lactate or lac
    comps = [comp("pH", ph, "", "7.35-7.45" if arterial else "7.31-7.41", float(ph) < (7.35 if arterial else 7.31)),
             comp("pCO2", str(pco2), "mmHg", "35-45" if arterial else "41-51", True)]
    if arterial:
        comps.append(comp("pO2", str(po2), "mmHg", "80-100", po2 > 100))
    comps += [comp("HCO3", str(hco3), "mEq/L", "22-26", True),
              comp("Lactate", lac, "mmol/L", "0.5-2.0", True)]
    return panel(comps)


def gas_rules(arterial):
    g = lambda k, lac=None: gas(k, lac, arterial)
    rules = []
    for tier, phases in (("u0", (U0, H0)), ("u1", (U1, H1)), ("u2", (U2, H2))):
        untreated, held = phases
        lac = TIER_LACTATE[tier]
        rules += [
          {"when": untreated + " AND " + BUF + " AND " + SED, "value": g("buf_sed", lac)},
          {"when": untreated + " AND " + BUF, "value": g("buf", lac)},
          {"when": "(" + untreated + " OR " + held + ") AND " + SED, "value": g(tier + "_sed")},
          {"when": untreated + " OR " + held, "value": g(tier)},
        ]
    # Improving keeps the lactate of the tier he was held at: buffering does not clear it
    # in minutes. The phase rules above come first, so these flag rules only reach improving.
    for flag, lac in ((R2, "4.6"), (R1, "4.2")):
        rules += [{"when": IMP + " AND " + flag + " AND " + SED, "value": g("imp_sed", lac)},
                  {"when": IMP + " AND " + flag, "value": g("imp", lac)}]
    rules += [{"when": IMP + " AND " + SED, "value": g("imp_sed")},
              {"when": None, "value": g("imp")}]
    return rules


def chem(key):
    na, k, cl, hco3, bun, cr, glu = CHEM[key]
    gap = na - cl - hco3
    return panel([
      comp("Sodium", str(na), "mEq/L", "135-145", na > 145),
      comp("Potassium", k, "mEq/L", "3.5-5.0", float(k) > 5.0),
      comp("Chloride", str(cl), "mEq/L", "98-107", False),
      comp("Bicarbonate", str(hco3), "mEq/L", "22-29", True),
      comp("BUN", str(bun), "mg/dL", "7-20", False),
      comp("Creatinine", cr, "mg/dL", "0.7-1.3 (M)", False),
      comp("Glucose", str(glu), "mg/dL", "70-140 (random)", False),
      comp("Anion gap", str(gap), "mEq/L", "8-12", gap > 12)],
      comment="Anion gap calculated without potassium.")


def chem_rules():
    rules = []
    for tier, (untreated, held) in (("u0", (U0, H0)), ("u1", (U1, H1)), ("u2", (U2, H2))):
        rules += [{"when": untreated + " AND " + BUF, "value": chem("buf")},
                  {"when": untreated + " OR " + held, "value": chem(tier)}]
    rules.append({"when": None, "value": chem("imp")})
    return rules


def osm_rules():
    o = lambda n: val("Serum osmolality (measured)", str(n), "mOsm/kg", "275-295", True)
    rules = []
    for tier, (untreated, held) in (("u0", (U0, H0)), ("u1", (U1, H1)), ("u2", (U2, H2))):
        rules += [{"when": untreated + " AND " + BUF, "value": o(OSM["buf_" + tier])},
                  {"when": untreated + " OR " + held, "value": o(OSM[tier])}]
    rules.append({"when": None, "value": o(OSM["imp"])})
    return rules


def lactate_rules():
    v = lambda x: val("Lactate", x, "mmol/L", "0.5-2.0", True)
    return [{"when": U2 + " OR " + H2, "value": v("4.6")},
            {"when": U1 + " OR " + H1, "value": v("4.2")},
            {"when": U0 + " OR " + H0, "value": v("3.6")},
            {"when": R2, "value": v("4.6")},
            {"when": R1, "value": v("4.2")},
            {"when": None, "value": v("3.6")}]


LABS = {
 "authoring_note": (
   "Section 9.4. The pattern a reviewer should check: an anion gap of 30 with a lactate of "
   "3.6 and a beta-hydroxybutyrate of 0.5, a measured osmolality of 328 against a calculated "
   "290, an ethanol of 28, and gases that follow Henderson-Hasselbalch and Winter's formula "
   "in every state. Venous and arterial gases show the same numbers (owner, 11 November "
   "2026). The osmolar gap falls by one for each point the anion gap rises, as methanol "
   "becomes formate. Bicarbonate raises the sodium to 143, which keeps the anion gaps of 29 "
   "and 28 true and raises the measured osmolality. Every value needs a signature."),

 "venous_blood_gas": {"changes_with_state": True, "rules": gas_rules(False)},
 "arterial_blood_gas": {"changes_with_state": True, "rules": gas_rules(True)},
 "basic_chemistry_chem_7": {"changes_with_state": True, "rules": chem_rules()},
 "osmolality": {"changes_with_state": True, "rules": osm_rules()},
 "lactate": {"changes_with_state": True, "rules": lactate_rules()},

 "ethanol_level_etoh": {"changes_with_state": False, "rules": always(
     val("Ethanol", "28", "mg/dL", "< 10", True))},
 "beta_hydroxybutyrate": {"changes_with_state": False, "rules": always(
     val("Beta-hydroxybutyrate", "0.5", "mmol/L", "< 0.6", False))},
 "fingerstick_blood_sugar": {"changes_with_state": False, "rules": always(
     val("Capillary glucose", "90", "mg/dL", "70-140 (random)", False))},
 "salicylate_aspirin_level": {"changes_with_state": False, "rules": always(
     val("Salicylate", "Undetectable", "mg/dL", "< 3", False))},
 "acetaminophen_level": {"changes_with_state": False, "rules": always(
     val("Acetaminophen", "Undetectable", "mcg/mL", "< 10", False))},
 "urinalysis": {"changes_with_state": False, "rules": always(panel([
     comp("Specific gravity", "1.025", "", "1.005-1.030", False),
     comp("pH", "5.0", "", "4.5-8.0", False),
     comp("Glucose", "Negative", "", "negative", False),
     comp("Ketones", "Trace", "", "negative", True),
     comp("Blood", "Negative", "", "negative", False),
     comp("Protein", "Negative", "", "negative", False),
     comp("Crystals", "None seen", "", "none", False),
     comp("WBC", "0-2", "/hpf", "0-5", False)]))},
}

# ============================================================== IMAGING AND ECG
def ecg_image(image_id, caption, read):
    return {"kind": "image", "abnormal": True, "image": image_id, "caption": caption,
            "comment": read, "verify": VERIFY}


READ_114 = "Sinus tachycardia. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST elevation or depression."
READ_96 = "Sinus rhythm. Normal axis. PR 150 ms, QRS 88 ms, QTc 410 ms. No ST elevation or depression."
IMAGING = {
 "authoring_note": (
   "Section 9.4 and 23. The ECGs are tracings borrowed from other packs at the nearest rate "
   "(media/README.md). Captions leave out the rate, which fluid, bicarbonate and sedation "
   "move. The chest film is the owner's normal male film. The CT head is a report."),
 "ecg_12_lead": {"changes_with_state": True, "rules": [
   {"when": IMP, "value": dict(ecg_image("alley-ecg-sinus-96", "Twelve-lead ECG. PR 150 ms, QRS 88 ms, QTc 410 ms", READ_96), abnormal=False)},
   {"when": U2 + " OR " + H2, "value": ecg_image("alley-ecg-sinus-116", "Twelve-lead ECG. PR 140 ms, QRS 84 ms, QTc 430 ms", READ_114)},
   {"when": None, "value": ecg_image("alley-ecg-sinus-114", "Twelve-lead ECG. PR 140 ms, QRS 84 ms, QTc 430 ms", READ_114)}]},
 "xr_chest": {"changes_with_state": False, "rules": always({
   "kind": "image", "abnormal": False, "image": "alley-cxr-normal", "caption": "Chest radiograph",
   "comment": ("Lungs clear. No consolidation, effusion or pneumothorax. Cardiac silhouette "
               "normal in size. No acute bony abnormality."),
   "verify": VERIFY})},
 "ct_head": {"changes_with_state": False, "rules": always(report(
   "No intracranial hemorrhage, mass or midline shift. Gray-white differentiation preserved. "
   "Basal ganglia normal. No skull fracture.", abnormal=False))},
}

# ============================================================== CONSULTANTS
# Most specific first. No line quotes a number. Renal's two prerequisites guarantee a gas,
# a chemistry and a reason for suspicion before any reply is given.
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. Nephrology is gated by prerequisites (gas and chemistry resulted, and an "
   "osmolality resulted or the drink or vision asked), so every reply may read those. The "
   "poison center has a tier per state of the workup."),

 "consult_renal": [
   {"when": IMP,
    "value": ("Nephrologist: The gap and the acidosis are dialysis indications by themselves. "
              "No level needed. I'm getting a line and the nurse. Dose fomepizole every four "
              "hours on dialysis. ICU after.")},
   {"when": FOMEP,
    "value": ("Nephrologist: He needs dialysis, no level needed. His pH is still under "
              "seven-thirty, so start bicarbonate. I'm getting a line and the nurse. "
              "Fomepizole every four hours on dialysis.")},
   {"when": None,
    "value": ("Nephrologist: That's a dialysis case. Has he had fomepizole? Start it now, don't "
              "wait for a level. Bicarbonate too while his pH is under seven-thirty. I'm "
              "getting the dialysis nurse.")}],

 "consult_toxicology": [
   {"when": ASKED_DRINK + " AND " + FOMEP,
    "value": ("Poison center: Blue stuff in a drinker is often windshield washer fluid, which "
              "is methanol. Good, fomepizole is in. Bicarbonate, folinic acid, nephrology for "
              "dialysis, and the ICU.")},
   {"when": ASKED_DRINK,
    "value": ("Poison center: Blue stuff in a drinker is often windshield washer fluid, which "
              "is methanol. Fomepizole now, don't wait for a level. Bicarbonate, folinic acid, "
              "nephrology for dialysis, and the ICU.")},
   {"when": GAS_R + " AND " + CHEM_R + " AND " + OSM_R,
    "value": ("Poison center: An anion gap that wide with an osmolar gap the ethanol doesn't "
              "explain is a toxic alcohol until proven otherwise. Fomepizole now, bicarbonate, "
              "folinic acid, nephrology, ICU. What did he drink?")},
   {"when": GAS_R + " AND " + CHEM_R,
    "value": ("Poison center: That gap needs an explanation. Send a measured serum osm with "
              "an ethanol and work out the osmolar gap. Ask him what he drank. Call me back.")},
   {"when": None,
    "value": ("Poison center: What did he take, and what do his gas and chemistry show? Send a "
              "gas, a chemistry, a serum osm and an ethanol, then call me back.")}],

 "consult_critical_care": [
   {"when": FOMEP + " AND flag renal_called set",
    "value": "Intensivist: We'll take him for dialysis upstairs. Keep the bicarbonate going and send a gas every two hours."},
   {"when": FOMEP,
    "value": "Intensivist: We'll take him. Has renal been called? He'll need dialysis."},
   {"when": GAS_R,
    "value": "Intensivist: We'll take him, but what's causing that acidosis? Has he had anything for it?"},
   {"when": None,
    "value": "Intensivist: He looks drunk to me from here. Get a gas and a chemistry and call me back."}],
}
