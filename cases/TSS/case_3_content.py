"""TSS part 3: exam findings, general status, the figure, labs, imaging, consultants.

EVERY VALUE IN THIS FILE IS MODEL OUTPUT. No physician supplied a number, a finding or a
reference interval. The values were chosen to fit the published clinical picture of
staphylococcal toxic shock syndrome (fever, diffuse erythroderma, hypotension, and
involvement of three or more organ systems) and none has been checked against a source.
Reference intervals are the action catalog's where it has one.
"""

PRES = "phase is presentation"
RESP = "phase is fluid_responsive"
HYPO = "phase is hypotensive"
SUPP = "phase is supported"
PROF = "phase is profound_shock"
STAB = "phase is stabilizing"
TUBED = "flag intubated set"
OUT = "flag source_removed set"

VERIFY = "Model output, not from a physician or a laboratory reference. [UNVERIFIED]"
DERIVED = ("Derived by a model from the pack's other values on 7 October 2026. No new "
           "clinical claim was intended. Not from a physician. [UNVERIFIED]")


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


def report(text, abnormal=True, comment=None, verify=None):
    d = {"kind": "report", "abnormal": abnormal, "report": text, "verify": verify or VERIFY}
    if comment:
        d["comment"] = comment
    return d


def always(v):
    return [{"when": None, "value": v}]


# ============================================================== EXAMINATION
EXAM = {
 "authoring_note": (
   "Section 9.2. All fourteen maneuvers are authored. Routing follows the catalog map: "
   "capillary refill and pulse quality on exam_circ, the rash on exam_skin, level of "
   "consciousness on exam_neuro, costovertebral tenderness on exam_back. The pelvic "
   "examination is exam_gu, which is where the retained tampon is found. Phase rules come "
   "before flag rules in every list except where the flag describes something the learner "
   "did to her that is true in any phase (the tube, the tampon)."),

 "exam_airway": [
   {"when": TUBED, "value": ex("Endotracheal tube in place and secured.")},
   {"when": PROF, "value": ex("Patent. Not speaking, moans to pain. Gag present.")},
   {"when": None, "value": ex("Patent. Speaking in full sentences. Lips dry.", abnormal=False)}],

 "exam_breath": [
   {"when": TUBED, "value": ex("Ventilated. Chest rising equally.")},
   {"when": PROF, "value": ex("Rapid shallow breathing. No accessory muscle use.")},
   {"when": HYPO, "value": ex("Tachypneic. Short sentences. No accessory muscle use.")},
   {"when": None, "value": ex("Mildly tachypneic. Full sentences. No accessory muscle use.")}],

 "exam_circ": [
   {"when": PROF, "value": ex(
     "Capillary refill over 6 seconds. Radial pulse barely palpable. Mottled to the thighs.")},
   {"when": HYPO, "value": ex(
     "Capillary refill 5 seconds. Radial pulse weak and fast. Hands and feet cold.")},
   {"when": SUPP, "value": ex(
     "Capillary refill 4 seconds. Radial pulse weak. Hands cool.")},
   {"when": STAB, "value": ex(
     "Capillary refill 3 seconds. Pulses fuller. Hands warming.")},
   {"when": RESP, "value": ex(
     "Capillary refill 3 seconds. Pulse fast, fuller than before. Hands cool.")},
   {"when": None, "value": ex(
     "Capillary refill 4 seconds. Pulse fast and thready. Hands cool.")}],

 "exam_heent": always(ex(
   "Both conjunctivae red, no discharge. Tongue red, lips cracked, mouth dry. Pupils equal, reactive.")),

 "exam_neck": always(ex(
   "Supple, no meningism. Neck veins flat. Trachea central.", abnormal=False)),

 "exam_card": [
   {"when": PROF, "value": ex("Regular tachycardia, heart sounds soft. No rub. No edema.")},
   {"when": None, "value": ex("Regular tachycardia. Soft systolic flow murmur. No rub. No edema.")}],

 "exam_pulm": always(ex(
   "Clear, equal air entry. No crackles or wheeze.", abnormal=False)),

 "exam_abd": always(ex(
   "Soft, non-tender, no guarding or rebound. Bowel sounds present.")),

 "exam_gu": [
   {"when": OUT, "value": ex(
     "Tampon removed. Vaginal walls red, no tear or ulcer. No cervical motion tenderness.")},
   {"when": None, "value": ex(
     "Retained tampon in the vaginal vault, dark and foul-smelling. Vaginal walls red.")}],

 "exam_back": always(ex(
   "No costovertebral angle tenderness. Spine non-tender. Rash continues over the back.")),

 "exam_msk": always(ex(
   "Diffuse muscle tenderness, thighs and calves. No joint swelling. Calves soft.")),

 "exam_skin": [
   {"when": PROF, "value": ex(
     "Diffuse blanching red rash. Knees and thighs mottled. No petechiae, no wounds.")},
   {"when": None, "value": ex(
     "Diffuse blanching red rash, trunk, limbs, palms, under clothing. No petechiae, no wounds.")}],

 "exam_neuro": [
   {"when": TUBED, "value": ex("Sedated. Pupils equal and reactive.")},
   {"when": PROF, "value": ex("Opens eyes to pain, confused words. GCS 10. Moves all limbs.")},
   {"when": HYPO, "value": ex("Drowsy, rouses to voice, oriented when roused. GCS 14. No focal deficit.")},
   {"when": None, "value": ex("Alert, oriented. GCS 15. No focal deficit. No photophobia.", abnormal=False)}],

 "exam_psych": [
   {"when": PROF, "value": ex("Cannot be assessed. Not answering questions.")},
   {"when": HYPO, "value": ex("Drowsy and slow to answer. No longer asking to go home.")},
   {"when": SUPP + " OR " + STAB, "value": ex(
     "Awake, cooperative, tired. No longer asking to go home.", abnormal=False)},
   {"when": None, "value": ex("Calm, cooperative, apologetic. Asks when she can go home.", abnormal=False)}],
}

# ============================================================== GENERAL STATUS
GENERAL_STATUS = {
 "authoring_note": (
   "Section 9.3. The one finding every learner sees. Consistent with exam_neuro and the "
   "appearance values of each phase. It never names the rash as anything but color."),
 "rules": [
   {"when": TUBED, "value": gs("Intubated and sedated. Flushed.")},
   {"when": PROF, "value": gs("Obtunded, gray and mottled, responds only to pain. GCS 10.")},
   {"when": HYPO, "value": gs("Gray and drowsy, rouses to voice. Flushed skin. GCS 14.")},
   {"when": SUPP, "value": gs("Awake, washed out, flushed. Vasopressor running. GCS 15.")},
   {"when": STAB, "value": gs("Awake, tired, flushed. Vasopressor running. GCS 15.")},
   {"when": RESP, "value": gs("Sitting up, flushed, says she feels a bit better. GCS 15.")},
   {"when": None, "value": gs("Sitting up, talking, flushed all over, dry lips. GCS 15.")},
 ],
}

# ============================================================== THE FIGURE
PATIENT_VISUAL = {
 "authoring_note": (
   "MODEL-AUTHORED. The figure cannot show a rash or a flush, so the erythroderma is "
   "carried by the general status line and the skin examination only. Alertness and "
   "distress are drawn from the phase's own appearance values. The only rule here is the "
   "tube."),
 "rules": [
   {"when": TUBED, "value": {"eyes": "closed", "addons": ["intubated"]}},
   {"when": None, "value": {}},
 ],
}

# ============================================================== LABORATORY
# Lactate and the gases follow the phase, because a learner who repeats them should see
# where she is. Everything else is one value: the organ injury does not change within the
# runtime of the case.
LACTATE = {"presentation": "4.6", "fluid_responsive": "4.0", "hypotensive": "6.8",
           "supported": "5.6", "profound_shock": "9.4", "stabilizing": "3.8"}
GAS = {  # pH, pCO2 venous, HCO3, base excess
  "presentation": ("7.30", "34", "17", "-8"),
  "fluid_responsive": ("7.31", "35", "18", "-7"),
  "hypotensive": ("7.24", "31", "14", "-12"),
  "supported": ("7.27", "32", "15", "-10"),
  "profound_shock": ("7.16", "28", "11", "-16"),
  "stabilizing": ("7.31", "34", "17", "-8"),
}
PHASE_ORDER = ["fluid_responsive", "hypotensive", "supported", "profound_shock", "stabilizing"]


def by_phase(make):
    """One rule per phase, presentation last as the unconditional default."""
    rules = [{"when": "phase is " + p, "value": make(p)} for p in PHASE_ORDER]
    rules.append({"when": None, "value": make("presentation")})
    return rules


def lactate_val(p):
    return val("Lactate", LACTATE[p], "mmol/L", "0.5-2.0", True)


def vbg(p):
    ph, pco2, hco3, be = GAS[p]
    return panel([
      comp("pH", ph, "", "7.31-7.41", float(ph) < 7.31),
      comp("pCO2", pco2, "mmHg", "41-51", True),
      comp("HCO3", hco3, "mEq/L", "22-26", True),
      comp("Base excess", be, "mEq/L", "-2 to +2", True),
      comp("Lactate", LACTATE[p], "mmol/L", "0.5-2.0", True)],
      comment="A metabolic acidosis with a raised lactate and respiratory compensation.")


def abg(p):
    ph, pco2, hco3, be = GAS[p]
    hco3 = str(int(hco3) - 2)   # keeps pH, pCO2 and HCO3 consistent with each other
    aph = "%.2f" % (float(ph) + 0.03)
    apco2 = str(int(pco2) - 5)
    # v0.24 audit. The saturation was 97 in every phase but two, against a monitor reading
    # 98 after fluid and 96 on a vasopressor. It is now the phase's own authored
    # saturation. Derived by a model from the phase vitals on 7 October 2026. The pO2 is
    # unchanged. The gas never sees a vital effect (authoring 12), so oxygen running in
    # the two low phases still shows a higher number on the monitor than on the gas.
    sat = {"presentation": "97", "fluid_responsive": "98", "hypotensive": "95",
           "supported": "96", "profound_shock": "92", "stabilizing": "97"}[p]
    po2 = {"hypotensive": "78", "profound_shock": "64"}.get(p, "92")
    return panel([
      comp("pH", aph, "", "7.35-7.45", True),
      comp("pCO2", apco2, "mmHg", "35-45", True),
      comp("pO2", po2, "mmHg", "80-100 on room air", float(po2) < 80),
      comp("HCO3", hco3, "mEq/L", "22-26", True),
      comp("Base excess", be, "mEq/L", "-2 to +2", True),
      comp("O2 saturation", sat, "%", "95-100", float(sat) < 95)],
      comment="A metabolic acidosis with respiratory compensation.")


LABS = {
 "authoring_note": (
   "Section 9.4. Structured payloads with model-set abnormal flags. The pattern is the "
   "point: kidney, liver, platelets and muscle are all involved, which is what separates "
   "toxic shock from a viral illness. Every value needs a physician's signature."),

 "lactate": {"changes_with_state": True, "rules": by_phase(lactate_val)},
 "venous_blood_gas": {"changes_with_state": True, "rules": by_phase(vbg)},
 "arterial_blood_gas": {"changes_with_state": True, "rules": by_phase(abg)},

 "basic_chemistry_chem_7": {"changes_with_state": False, "rules": always(panel([
     comp("Sodium", "131", "mEq/L", "135-145", True),
     comp("Potassium", "3.3", "mEq/L", "3.5-5.0", True),
     comp("Chloride", "97", "mEq/L", "98-107", True),
     comp("Bicarbonate", "17", "mEq/L", "22-29", True),
     comp("BUN", "41", "mg/dL", "7-20", True),
     comp("Creatinine", "2.6", "mg/dL", "0.6-1.2", True),
     comp("Glucose", "104", "mg/dL", "70-140 (random)", False)],
     comment="Anion gap 17, calculated without potassium."))},

 "complete_blood_count_cbc": {"changes_with_state": False, "rules": always(panel([
     comp("WBC", "17.4", "x10^9/L", "4.0-11.0", True),
     comp("Hemoglobin", "14.9", "g/dL", "12.0-16.0 (F)", False),
     comp("Hematocrit", "45", "%", "36-46 (F)", False),
     comp("Platelets", "98", "x10^9/L", "150-400", True),
     comp("MCV", "88", "fL", "80-100", False)],
     comment="A high white count and low platelets."))},

 "liver_function_tests_lfts": {"changes_with_state": False, "rules": always(panel([
     comp("AST", "148", "U/L", "10-40", True),
     comp("ALT", "121", "U/L", "7-56", True),
     comp("Alkaline phosphatase", "118", "U/L", "44-147", False),
     comp("Total bilirubin", "2.6", "mg/dL", "0.1-1.2", True),
     comp("Direct bilirubin", "1.4", "mg/dL", "0.0-0.3", True),
     comp("Albumin", "2.9", "g/dL", "3.5-5.0", True),
     comp("Total protein", "5.8", "g/dL", "6.0-8.3", True)],
     comment="Raised transaminases and bilirubin. Low albumin and total protein."))},

 "creatine_kinase_ck": {"changes_with_state": False, "rules": always(val(
     "Creatine kinase", "2140", "U/L", "30-200", True))},

 "coagulation_panel": {"changes_with_state": False, "rules": always(panel([
     comp("PT", "15.4", "sec", "11.0-13.5", True),
     comp("INR", "1.3", "", "0.8-1.1", True),
     comp("aPTT", "39", "sec", "25-35", True)],
     comment="Mildly prolonged clotting times."))},

 "plasma_procalcitonin": {"changes_with_state": False, "rules": always(val(
     "Procalcitonin", "24.0", "ng/mL", "< 0.10", True))},

 "c_reactive_protein_crp": {"changes_with_state": False, "rules": always(val(
     "CRP", "238", "mg/L", "< 5", True))},

 "urinalysis": {"changes_with_state": False, "rules": always(panel([
     comp("Color", "Dark amber", "", "yellow", True),
     comp("Clarity", "Slightly cloudy", "", "clear", True),
     comp("Specific gravity", "1.030", "", "1.005-1.030", False),
     comp("pH", "5.5", "", "4.5-8.0", False),
     comp("Protein", "1+", "", "negative", True),
     comp("Glucose", "Negative", "", "negative", False),
     comp("Ketones", "2+", "", "negative", True),
     comp("Blood", "2+", "", "negative", True),
     comp("Leukocyte esterase", "1+", "", "negative", True),
     comp("Nitrite", "Negative", "", "negative", False),
     comp("WBC", "10-20", "/hpf", "0-5", True),
     comp("RBC", "10-20", "/hpf", "0-2", True),
     comp("Bacteria", "None seen", "", "none", False)],
     comment="White cells and red cells. No bacteria and no nitrite."))},

 "urine_hcg_qualitative": {"changes_with_state": False, "rules": always(
     report("Negative.", abnormal=False))},

 "serum_hcg_quantitative": {"changes_with_state": False, "rules": always(val(
     "Serum beta-hCG", "< 5", "mIU/mL", "< 5 (non-pregnant)", False))},

 "blood_culture_x_2": {"changes_with_state": False, "rules": always(report(
     "Two sets collected from separate sites. No growth to report at this time.",
     abnormal=False))},

 "peripheral_smear": {"changes_with_state": False, "rules": always(report(
     "Neutrophilia with a left shift and toxic granulation. Platelets reduced. No "
     "schistocytes. No blasts."))},

 # The skin biopsy line was removed with the catalog entry on 11 October 2026 (author
 # instruction: a skin biopsy is not used in this simulator).
}

# ============================================================== IMAGING AND ECG
HR = {"presentation": 128, "fluid_responsive": 114, "hypotensive": 138, "supported": 124,
      "profound_shock": 148, "stabilizing": 116}


def ecg(p):
    return report(
      "Sinus tachycardia at %d. Normal axis. PR 140 ms, QRS 84 ms, QTc 430 ms. No ST "
      "elevation or depression." % HR[p])


IMAGING = {
 "authoring_note": (
   "Section 9.4. The chest film is left to the catalog default, which is normal, and that "
   "is intended: her lungs are clear. The CT shows the tampon, so it is a second and slower "
   "route to the source for a learner who did not examine her."),

 "ecg_12_lead": {"changes_with_state": True, "rules": by_phase(ecg)},

 "ultrasound_cardiac": {"changes_with_state": False, "rules": always(report(
     "Hyperdynamic left ventricle. No pericardial effusion. Right ventricle not dilated. "
     "Inferior vena cava small and collapsing with each breath.",
     verify=(VERIFY + " The case shows the same picture in every phase, which is a "
             "simplification.")))},

 # v0.24 audit, catalog finding 5.4. The catalog default said there was no free fluid in
 # the pelvis, and this pack's own CT reports a small volume of free pelvic fluid. The
 # report now agrees with the CT and adds nothing to it.
 "ultrasound_fast": {"changes_with_state": False, "rules": always(report(
     "No free fluid in Morison's pouch or the splenorenal recess. Small volume of free "
     "fluid in the pelvis. No pericardial effusion.",
     verify=DERIVED + " Derived from the CT report's free pelvic fluid."))},

 "ct_abdomen": {"changes_with_state": True, "rules": [
   {"when": OUT, "value": report(
     "Mild diffuse small bowel wall thickening. Small volume of free pelvic fluid. No "
     "abscess. Normal appendix. No hydronephrosis.")},
   {"when": None, "value": report(
     "Cylindrical air-containing object in the vaginal canal. Mild diffuse small bowel wall "
     "thickening. Small volume of free pelvic fluid. No abscess. Normal appendix. No "
     "hydronephrosis.")}]},
}

# ============================================================== CONSULTANTS
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. No consultant quotes a laboratory value. The intensivist and the "
   "infectious disease physician both ask about a source, which is what they would ask, "
   "and which makes a consult one honest way to be pointed at the pelvic examination.\n\n"
   "v0.24 audit. The intensivist's list was rewritten. It opens with a tier for the "
   "obtunded patient, which claims no treatment. Every later tier that says a treatment was "
   "given tests that treatment's flag, so 'Fluid in' is no longer said to a patient who had "
   "none, and the drug running is called a vasopressor because a covered sibling can be the "
   "one running. No tier says a lactate has been sent. Nephrology has a reply, with a tier "
   "for a chemistry that is back, one for a chemistry that is pending and one that asks for "
   "it. Every new sentence restates a note the pack already carries. A model wrote them on "
   "7 October 2026 and no physician has read them."),

 "consult_critical_care": [
   {"when": PROF,
    "value": ("Intensivist: If she's obtunded with a pressure like that, I'm coming down. "
              "She needs three things together: fluid, a vasopressor and the source found "
              "and removed. Has anyone done a pelvic exam? Start whichever of those is "
              "missing now.")},
   {"when": "flag pressor_running set AND flag fluids_given set AND flag source_removed set",
    "value": ("Intensivist: Good. Fluid in, a vasopressor running, source out. I'll take "
              "her. I want a lactate from after the resuscitation before she comes up, and "
              "make sure she has had vancomycin and clindamycin.")},
   {"when": "flag pressor_running set AND flag source_removed set",
    "value": ("Intensivist: A vasopressor running and the source out. Has she had fluid? "
              "She's dry, and a vasopressor with no fluid behind it is not enough. Give her "
              "about 30 per kilo and call me back.")},
   {"when": "flag pressor_running set AND flag fluids_given set",
    "value": ("Intensivist: I'll take her. Before she comes up, what is the source? Has anyone "
              "asked about tampons or done a pelvic exam? If something is in there, it comes "
              "out before she moves.")},
   {"when": "flag pressor_running set",
    "value": ("Intensivist: A vasopressor with no fluid behind it is not enough in a "
              "patient this dry. Give her about 30 per kilo. And what is the source? Has "
              "anyone asked about tampons or done a pelvic exam?")},
   {"when": "flag fluids_given set AND flag source_removed set",
    "value": ("Intensivist: Good that the source is out. Keep filling her to about 30 per "
              "kilo. If her mean is still under 65 after that, start norepinephrine through "
              "a good peripheral line and call me back.")},
   {"when": "flag fluids_given set",
    "value": ("Intensivist: Keep filling her to about 30 per kilo. If her mean is still "
              "under 65 after that, start norepinephrine through a good peripheral line and "
              "call me back. And keep looking for where this is coming from.")},
   {"when": None,
    "value": ("Intensivist: Tell me her vital signs and what you've done. A febrile young "
              "woman with a fast heart rate and a soft pressure needs a line, fluid, cultures "
              "and antibiotics now. Call me back when that is running.")}],

 "consult_renal": [
   {"when": "study basic_chemistry_chem_7 resulted",
    "value": ("Nephrology: Her kidneys are not being perfused, so the treatment is your "
              "resuscitation, not us. No more ibuprofen and no diuretic. Dose the vancomycin "
              "for her kidneys and watch her urine output.")},
   {"when": "study basic_chemistry_chem_7 ordered",
    "value": "Nephrology: Her chemistry isn't back. Call me when you have it."},
   {"when": None,
    "value": ("Nephrology: I can't add anything without a creatinine. Send a chemistry and "
              "call me when you have it.")}],

 "consult_infectious_disease": [
   {"when": "flag source_removed set",
    "value": ("Infectious disease: With a retained tampon, treat this as menstrual toxic shock. "
              "Vancomycin plus clindamycin, which cuts toxin production. Expect the blood "
              "cultures to stay negative.")},
   {"when": None,
    "value": ("Infectious disease: Cover with vancomycin and clindamycin, and add ceftriaxone "
              "if meningococcal disease is possible. Has she been examined fully for a tampon, "
              "a wound or packing?")}],

 "consult_ob_gyn": [
   {"when": "flag source_removed set",
    "value": ("Gynecology: Glad it's out. Nothing more from us tonight. No tampons until "
              "she has been seen in clinic, and tell her this can come back.")},
   {"when": "action exam_gu taken",
    "value": ("Gynecology: If there's a tampon in the vault, take it out now with a "
              "speculum and forceps. You don't need us for that. Call if you can't see it "
              "or it won't come.")},
   {"when": None,
    "value": ("Gynecology: What did the pelvic exam show? I can't add anything until "
              "someone has looked.")}],
}
