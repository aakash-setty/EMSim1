"""AFRVR part 3: exam, general status, labs, imaging, consultants."""

def ex(findings, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": findings}
def gs(findings, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": findings}
def rep(text, abnormal=True):
    return {"kind": "report", "abnormal": abnormal, "report": text}
def c(label, value, unit, ref, abn):
    return {"label": label, "value": value, "unit": unit, "reference_range": ref, "abnormal": abn}
def panel(comps, comment=None, kind="panel", verify=None):
    d = {"kind": kind, "abnormal": any(x["abnormal"] for x in comps), "components": comps}
    if comment: d["comment"] = comment
    # `comment` is rendered under the result. `verify` is not rendered anywhere and is
    # where a note addressed to the reviewing physician belongs, the same way the
    # catalog's own defaults use it.
    if verify: d["verify"] = verify
    return d
def val(comps, comment=None, verify=None):
    return panel(comps, comment, kind="value", verify=verify)

VENT = "phase is intubated"
RF   = "phase is respiratory_failure"
SUPPORTED = "phase is breathing_supported OR phase is stabilized"

EXAM = {
 "authoring_note": ("Section 11.2. Twelve of the fourteen catalog manoeuvres are authored; "
   "genitourinary and back inherit the catalog default. Peripheral edema sits on the "
   "cardiovascular examination and jugular venous pressure on the neck, per exam_finding_routing, "
   "not where a clinician would instinctively look for them."),

 "exam_airway": [
   {"when": VENT, "value": ex("Endotracheal tube in place at 23 cm at the teeth. Cuff inflated. "
      "Waveform capnography with a normal square trace.")},
   {"when": RF, "value": ex("Airway still patent but he is no longer talking. Answers in single "
      "words when pushed. No stridor and no secretions, but he is not going to protect this "
      "airway for much longer at this rate of work.")},
   {"when": None, "value": ex("Patent and self-maintained. He can complete a short sentence "
      "before he has to stop for a breath. No stridor, no drooling, no oropharyngeal swelling. "
      "Voice normal.", abnormal=False)},
 ],

 "exam_breath": [
   {"when": VENT, "value": ex("Ventilated. Chest rises symmetrically with each delivered breath. "
      "No spontaneous respiratory effort against the ventilator at present.")},
   {"when": RF, "value": ex("Respiratory rate 38 and shallow. Marked accessory muscle use with "
      "sternocleidomastoid and scalene recruitment, intercostal indrawing, and paradoxical "
      "abdominal movement on inspiration. He has stopped talking. This is a fatiguing pattern.")},
   {"when": SUPPORTED, "value": ex("Respiratory rate down and the pattern is deeper and more "
      "regular on positive pressure. Much less accessory muscle use. He is tolerating the mask "
      "and no longer bracing against it. Chest expansion symmetrical.")},
   {"when": None, "value": ex("Respiratory rate 30 and shallow. Sitting bolt upright and will not "
      "lie back. Visible sternocleidomastoid and scalene use with mild intercostal indrawing. "
      "Speaks in short sentences, stopping to breathe. Chest expansion symmetrical, no "
      "splinting.")},
 ],

 "exam_circ": [
   {"when": VENT, "value": ex("Peripheries warm. Capillary refill 2 seconds. Radial pulse "
      "irregularly irregular with variable volume. No pulse deficit appreciable at this rate.")},
   {"when": "phase is rate_controlled_congested OR phase is stabilized",
    "value": ex("Radial pulse still irregularly irregular but slower and much easier to count, "
      "with far less beat-to-beat variation in volume. The radial and apical rates now agree, so "
      "the pulse deficit has closed. Peripheries warm, capillary refill 2 seconds, no mottling.")},
   {"when": None, "value": ex("Radial pulse irregularly irregular, thready and impossible to count "
      "reliably at the wrist. Marked beat-to-beat variation in volume. Auscultated apical rate is "
      "around 160 while the palpated radial rate is nearer 130: a pulse deficit of about 30, "
      "because the shortest cycles do not fill the ventricle enough to open the aortic valve "
      "usefully. Peripheries are warm and capillary refill is 2 seconds. No mottling, no cool "
      "line up the limbs.")},
 ],

 "exam_neck": [
   {"when": VENT, "value": ex("Jugular venous pulsation elevated, harder to assess against "
      "positive pressure ventilation but clearly above the clavicle at 45 degrees. Trachea "
      "midline. No goitre, no thyroid nodule, no bruit.")},
   {"when": None, "value": ex("Jugular venous pulsation visible two thirds of the way up the neck "
      "with the head of the bed at 45 degrees, roughly 12 cm of water, with no discernible "
      "waveform because the rhythm is irregular and the a wave is absent. Elevated. Trachea "
      "midline. No lymphadenopathy. Thyroid not enlarged, no nodule, no bruit. Sustained pressure "
      "over the right upper quadrant raises the venous column and it does not fall back while "
      "pressure is maintained: hepatojugular reflux positive.")},
 ],

 "exam_card": [
   {"when": VENT, "value": ex("Irregularly irregular, rate around 118. Heart sounds distant "
      "against the ventilator. Bilateral pitting edema to mid-shin, unchanged.")},
   {"when": "phase is rate_controlled_congested OR phase is stabilized",
    "value": ex("Irregularly irregular at a rate you can now count, around 105. First heart sound "
      "still varies in intensity from beat to beat, which is expected in atrial fibrillation "
      "because the diastolic filling time varies. Apex is displaced laterally to the anterior "
      "axillary line in the sixth interspace. No murmur audible. Bilateral pitting edema to "
      "mid-shin, unchanged: days of accumulated fluid do not leave in ten minutes.")},
   {"when": None, "value": ex("Irregularly irregular, far too fast to count accurately by "
      "auscultation, around 160. The first heart sound varies in intensity beat to beat. No "
      "murmur that can be characterised at this rate. A third heart sound cannot be excluded and "
      "cannot be confirmed at 160. Apex beat displaced laterally to the anterior axillary line in "
      "the sixth interspace, diffuse rather than tapping. Bilateral pitting edema to mid-shin, "
      "symmetrical, pitting to about 2 cm.")},
 ],

 "exam_pulm": [
   {"when": VENT, "value": ex("Coarse crackles throughout both lung fields on the ventilator, "
      "worse at the bases. No wheeze. No focal dullness.")},
   {"when": "flag diuretic_given set AND flag on_niv set",
    "value": ex("Fine inspiratory crackles now confined to both bases rather than reaching the "
      "mid-zones. Air entry good throughout. No wheeze. Percussion note dull at both bases, "
      "unchanged, consistent with small effusions.")},
   {"when": None, "value": ex("Fine inspiratory crackles in both lung fields to the mid-zones, "
      "symmetrical, worse at the bases. Scattered expiratory wheeze in both lower zones, which in "
      "this patient is peribronchial edema rather than bronchospasm. Percussion note dull at both "
      "bases. No focal consolidation, no pleural rub.")},
 ],

 "exam_abd": [
   {"when": None, "value": ex("Soft. Mildly tender in the right upper quadrant. Liver edge "
      "palpable 3 cm below the costal margin, smooth and tender, and it is pulsatile. No ascites, "
      "no guarding, no rebound. Bowel sounds present.")},
 ],

 "exam_msk": [
   {"when": None, "value": ex("Symmetrical pitting edema of both lower limbs to mid-shin. No "
      "unilateral calf swelling, no calf tenderness, no palpable cord, no asymmetry in calf "
      "circumference. Dorsalis pedis and posterior tibial pulses present bilaterally and "
      "irregular. Full range of movement at both ankles and knees.", abnormal=False)},
 ],

 "exam_skin": [
   {"when": VENT, "value": ex("Warm and dry. Colour good. No rash, no mottling.", abnormal=False)},
   {"when": RF, "value": ex("Clammy and grey. Diaphoretic across the forehead and upper chest. "
      "Dusky discoloration of the lips and nailbeds. No rash.")},
   {"when": None, "value": ex("Warm to the touch with a light sweat over the forehead and upper "
      "chest. Colour is reasonable centrally with no frank cyanosis. No rash, no petechiae, no "
      "wounds, no cellulitis. Skin over both shins is taut and shiny with the edema.")},
 ],

 "exam_neuro": [
   {"when": VENT, "value": ex("Sedated and ventilated. Glasgow Coma Scale 3T on the current "
      "sedation. Pupils 3 mm and reactive bilaterally. No spontaneous movement.")},
   {"when": RF, "value": ex("Glasgow Coma Scale 14: eyes open to voice, confused, obeys commands. "
      "Drowsy and difficult to keep engaged, and he has stopped answering questions in the middle "
      "of them. No focal deficit, no asymmetry, plantars downgoing. This is the carbon dioxide, "
      "not a new neurological event.")},
   {"when": None, "value": ex("Glasgow Coma Scale 15. Alert, oriented to person, place and time. "
      "Cranial nerves intact. Power 5 out of 5 and symmetrical in all four limbs. No pronator "
      "drift, no ataxia, plantars downgoing. No focal deficit.", abnormal=False)},
 ],

 "exam_psych": [
   {"when": VENT, "value": ex("Sedated. Not assessable.")},
   {"when": None, "value": ex("Anxious and frightened, and appropriately so. Cooperative with "
      "examination. Thought content coherent, no delusional material, no hallucinations. He keeps "
      "asking whether he is having a heart attack. Insight intact.")},
 ],

 "exam_heent": [
   {"when": None, "value": ex("Normocephalic, atraumatic. Conjunctivae not pale, sclerae not "
      "icteric. No lid lag, no lid retraction, no proptosis. Pupils equal and reactive. Mucous "
      "membranes moist. Oropharynx clear. No thyroid enlargement palpable from the front.",
      abnormal=False)},
 ],
}

GENERAL_STATUS = {
 "authoring_note": ("Section 11.3. Rendered above the exam list and not clickable, so it is the "
   "one examination finding every learner sees. Kept consistent with the neurological examination "
   "and with the appearance values in each phase."),
 "rules": [
  {"when": VENT, "value": gs("Intubated and sedated on the ventilator. Not responsive. Colour good.")},
  {"when": RF, "value": gs("Severe respiratory distress and tiring. Drowsy, grey and sweaty, "
     "speaking in single words. GCS 14.")},
  {"when": "phase is rate_controlled_congested",
   "value": gs("Still in obvious respiratory distress, sitting bolt upright, speaking in short "
     "phrases. Heart rate visibly slower on the monitor. GCS 15.")},
  {"when": "phase is breathing_supported",
   "value": gs("Moderate respiratory distress, improving behind the mask. Tolerating positive "
     "pressure. GCS 15.")},
  {"when": "phase is stabilized",
   "value": gs("Comfortable at rest on the mask, settled and talking between breaths. GCS 15.")},
  {"when": None, "value": gs("Awake, anxious and visibly breathless. Sitting upright, hands on "
     "his thighs, speaking in short sentences. GCS 15.")},
 ],
}

LABS = {
 "authoring_note": ("Section 11.4. Structured payloads with abnormal flags set by the author, not "
   "computed by the renderer. Reference intervals are assay- and institution-specific and every "
   "one of them is awaiting a physician's signature; see the review packet."),

 "basic_chemistry_chem_7": {"changes_with_state": False, "rules": [
   {"when": None, "value": panel([
     c("Sodium", "138", "mEq/L", "135-145", False),
     c("Potassium", "3.7", "mEq/L", "3.5-5.0", False),
     c("Chloride", "102", "mEq/L", "98-107", False),
     c("Bicarbonate", "24", "mEq/L", "22-29", False),
     c("BUN", "22", "mg/dL", "7-20", True),
     c("Creatinine", "1.0", "mg/dL", "0.6-1.2", False),
     c("Glucose", "148", "mg/dL", "70-140 (random)", True),
     c("Calcium", "9.1", "mg/dL", "8.5-10.2", False)],
     comment="Renal function is normal. The potassium is within range and at the lower end of "
             "where you would want it in a new tachyarrhythmia, and it will not correct properly "
             "while the magnesium is low. Magnesium is not on this panel and has to be asked for.")}]},

 "magnesium_level": {"changes_with_state": True, "rules": [
   {"when": "flag magnesium_given set", "value": val([
     c("Magnesium", "2.1", "mg/dL", "1.7-2.2", False)],
     comment="Corrected after replacement.")},
   {"when": None, "value": val([
     c("Magnesium", "1.6", "mg/dL", "1.7-2.2", True)],
     comment="Low. Worth correcting: magnesium is a cofactor for the sodium-potassium pump so a "
             "low potassium will not correct while this is low, and intravenous magnesium has "
             "been reported as a useful adjunct to nodal blockade in rapid atrial fibrillation on "
             "the evidence of small randomised trials.")}]},

 "troponin_t": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("Troponin T, high sensitivity", "38", "ng/L", "under 14", True)],
     comment="Modestly elevated. A single value cannot separate demand injury from acute coronary "
             "occlusion; the trajectory over one to three hours and the clinical picture do. At a "
             "ventricular rate of 160 with an ejection fraction of 30 to 35 percent, supply-demand "
             "mismatch is the expected explanation. The ECG shows no acute occlusion pattern.")}]},

 "nt_probnp": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("NT-proBNP", "3480", "pg/mL", "under 300 (age-adjusted cut-offs apply)", True)],
     comment="Markedly raised. Supportive of acute heart failure and not diagnostic of it: atrial "
             "fibrillation raises natriuretic peptides independently through atrial wall stress, "
             "and the two contributions cannot be separated in this patient. Most useful when low.",
     verify="ASSAY NOTE, for the reviewer and not for the learner. The catalog entry is "
            "NT-proBNP (renamed from 'pro-BNP' in v0.9 so the assay is unambiguous) and this "
            "payload is written as NT-proBNP with an NT-proBNP reference interval. BNP and "
            "NT-proBNP have different units and different cut-offs and are not interchangeable. "
            "This sits in `verify` rather than in `comment` because `comment` is the "
            "interpretation the debrief shows after the case.")}]},

 "complete_blood_count_cbc": {"changes_with_state": False, "rules": [
   {"when": None, "value": panel([
     c("White cell count", "8.4", "x10^9/L", "4.0-11.0", False),
     c("Haemoglobin", "13.9", "g/dL", "13.5-17.5", False),
     c("Haematocrit", "41", "%", "38-50", False),
     c("Platelets", "232", "x10^9/L", "150-400", False)],
     comment="Unremarkable. Anaemia is a genuine precipitant of decompensation and is excluded here.")}]},

 "tsh": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("TSH", "1.8", "mIU/L", "0.4-4.0", False)],
     comment="Normal. Hyperthyroidism is a classic and treatable precipitant of new atrial "
             "fibrillation and is excluded. In practice this result would not return in time to "
             "change department management, which is a reason to send it, not a reason to wait "
             "for it.")}]},

 "venous_blood_gas": {"changes_with_state": True, "rules": [
   {"when": RF, "value": panel([
     c("pH", "7.22", "", "7.31-7.41 (venous)", True),
     c("pCO2", "64", "mmHg", "41-51 (venous)", True),
     c("pO2", "28", "mmHg", "30-40 (venous)", True),
     c("Bicarbonate", "26", "mEq/L", "22-29", False),
     c("Lactate", "3.1", "mmol/L", "under 2.0", True)],
     comment="Worsening acute respiratory acidosis. He is not clearing carbon dioxide because he "
             "is tiring, and this is the number that explains the drowsiness.")},
   {"when": None, "value": panel([
     c("pH", "7.30", "", "7.31-7.41 (venous)", True),
     c("pCO2", "52", "mmHg", "41-51 (venous)", True),
     c("pO2", "33", "mmHg", "30-40 (venous)", False),
     c("Bicarbonate", "25", "mEq/L", "22-29", False),
     c("Lactate", "2.4", "mmol/L", "under 2.0", True)],
     comment="Mild acute respiratory acidosis despite a respiratory rate of 30, which means he is "
             "moving a lot of air and not clearing carbon dioxide with it. In a patient breathing "
             "that fast, a carbon dioxide that is not low is a warning. This is the finding that "
             "argues for bilevel rather than continuous positive pressure.")}]},

 "lactate": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("Lactate", "2.4", "mmol/L", "under 2.0", True)],
     comment="Mildly raised, and in this patient attributable to the work of breathing and the "
             "tachycardia rather than to sepsis or mesenteric ischaemia. It should fall with "
             "treatment. One that does not fall deserves a different explanation.")}]},

 "d_dimer": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("D-dimer", "940", "ng/mL FEU", "under 500", True)],
     comment="Raised, and this is the trap. D-dimer rises with heart failure, with atrial "
             "fibrillation and with age, all three of which this patient has. Ordered in a "
             "presentation with a low pretest probability of pulmonary embolism, a raised result "
             "commits you to a contrast study you did not need.")}]},

 "liver_function_tests_lfts": {"changes_with_state": False, "rules": [
   {"when": None, "value": panel([
     c("AST", "46", "U/L", "10-40", True),
     c("ALT", "52", "U/L", "7-56", False),
     c("Alkaline phosphatase", "118", "U/L", "44-147", False),
     c("Total bilirubin", "1.4", "mg/dL", "0.2-1.2", True),
     c("Albumin", "3.8", "g/dL", "3.5-5.0", False)],
     comment="A mild mixed picture consistent with hepatic congestion, which fits the pulsatile "
             "tender liver and the raised venous pressure. Not a reason to start a hepatology "
             "workup.")}]},

 "coagulation_panel": {"changes_with_state": False, "rules": [
   {"when": None, "value": panel([
     c("INR", "1.1", "", "0.8-1.2", False),
     c("aPTT", "30", "seconds", "25-35", False)],
     comment="Normal. Worth having before anticoagulation, and not a reason to delay it.")}]},
}

IMAGING = {
 "authoring_note": (
   "Section 11.4. Reports freeze at the state in which they were ordered, so a tracing "
   "taken before rate control still reads 160 when it arrives after.\n\n"
   "FINDINGS ONLY. No report in this case carries an interpretation line, and that is an "
   "authoring decision rather than an oversight. Naming the rhythm, calling the ST "
   "depression rate-related, or concluding that the B-lines are cardiogenic is the "
   "resident's work, and a report that does it for them removes the task the case exists "
   "to set. The reasoning that used to sit at the end of these reports has not been lost; "
   "it is in the debrief note on each study, which is where a learner reads it after they "
   "have committed to an answer rather than before.\n\n"
   "They are also deliberately short. A resident who has to read eight sentences to find "
   "the ejection fraction is spending attention on comprehension rather than on "
   "management, and length in a report reads as importance, so a long report about a "
   "negative study is actively misleading."),

 # Five tiers, keyed on how much rate control is on board rather than on the phase,
 # because that is what decides the rate on the tracing. The two phase-guarded rules come
 # first, per the rule-ordering guidance: the ventilated phase carries its own rate, and
 # the respiratory-failure phase is the one place a rate-controlled patient is still fast.
 "ecg_12_lead": {"changes_with_state": True, "result_shape": "structured", "rules": [
   {"when": "phase is intubated",
    "value": rep("Atrial fibrillation, ventricular rate approximately 118. Irregularly "
      "irregular, no P waves. Narrow QRS at 92 ms. No ST elevation. QTc 444 ms.")},
   {"when": "phase is respiratory_failure AND flag rate_control_adequate set",
    "value": rep("Atrial fibrillation, ventricular rate approximately 130. Irregularly "
      "irregular, no P waves. Narrow QRS at 90 ms. Horizontal ST depression 1 mm in V5 and "
      "V6. No ST elevation. QTc 446 ms.")},
   {"when": "flag rate_control_adequate set",
    "value": rep("Atrial fibrillation, ventricular rate approximately 105. Irregularly "
      "irregular, no P waves. Narrow QRS at 92 ms. Horizontal ST depression 0.5 mm in V5 "
      "and V6, less than on the earlier tracing. No ST elevation. QTc 442 ms.")},
   {"when": "flag rate_control_given set",
    "value": rep("Atrial fibrillation, ventricular rate approximately 140. Irregularly "
      "irregular, no P waves. Narrow QRS at 90 ms. Horizontal ST depression 1 mm in V4 to "
      "V6, less than on the earlier tracing. No ST elevation. QTc 446 ms.")},
   {"when": None,
    "value": rep("Atrial fibrillation with rapid ventricular response, ventricular rate "
      "approximately 160. Irregularly irregular, no P waves. Narrow QRS at 88 ms, no delta "
      "wave. Horizontal ST depression up to 1.5 mm in V4 to V6. No ST elevation, no Q "
      "waves. QTc 448 ms.")}]},

 "ultrasound_cardiac": {"changes_with_state": False, "result_shape": "structured", "rules": [
   {"when": None,
    "value": rep("Globally reduced left ventricular systolic function with global "
      "hypokinesis and no regional wall motion abnormality. Visually estimated ejection "
      "fraction 30 to 35 percent. Left ventricle mildly dilated. No pericardial effusion. "
      "Right ventricle not dilated, no septal flattening. Inferior vena cava 2.3 cm with "
      "minimal respiratory variation.")}]},

 "ultrasound_lung": {"changes_with_state": True, "result_shape": "structured", "rules": [
   {"when": "flag diuretic_given set AND flag on_niv set",
    "value": rep("B-lines reduced in number and now confined to the dependent "
      "posterolateral zones, with A-lines returning anteriorly on both sides. Lung sliding "
      "present. Small bilateral pleural effusions, unchanged.")},
   {"when": "flag diuretic_given set",
    "value": rep("B-lines reduced in number anteriorly, still confluent in the lower zones "
      "on both sides. Lung sliding present. Small bilateral pleural effusions.")},
   {"when": None,
    "value": rep("Diffuse bilateral B-lines, three or more per field in every zone and "
      "confluent at the bases. Symmetrical. Lung sliding present throughout. Small "
      "bilateral pleural effusions. No consolidation.")}]},

 "xr_chest": {"changes_with_state": False, "result_shape": "structured", "rules": [
   {"when": None,
    "value": rep("Portable semi-erect film. Cardiomegaly, cardiothoracic ratio about 0.58. "
      "Upper zone vascular redistribution. Perihilar interstitial and alveolar opacity with "
      "Kerley B lines at both bases. Small bilateral pleural effusions. No focal "
      "consolidation. No pneumothorax.")}]},

 "ct_pulmonary_embolus": {"changes_with_state": False, "result_shape": "structured", "rules": [
   {"when": None,
    "value": rep("No filling defect in the pulmonary arteries to subsegmental level. "
      "Cardiomegaly with left atrial enlargement. Bilateral ground-glass opacity with "
      "smooth interlobular septal thickening in a perihilar distribution. Small bilateral "
      "pleural effusions. Coronary artery calcification. No consolidation.")}]},

 "ultrasound_lower_extremity_venous": {"changes_with_state": False, "result_shape": "structured",
  "rules": [
   {"when": None,
    "value": rep("Common femoral and popliteal veins fully compressible on both sides. No "
      "echogenic intraluminal material. Symmetrical subcutaneous edema of both calves.",
      abnormal=False)}]},
}

DX_KNOWN = "study ultrasound_cardiac resulted"
ECG_DONE = "study ecg_12_lead resulted"

CONSULTANTS = {
 "authoring_note": ("Section 11.5. Ordered most specific to least specific, with a pending tier "
   "per study rather than per group, so a consultant never claims to be looking at something that "
   "has not come back."),

 "consult_cardiology": [
  {"when": DX_KNOWN + " AND " + ECG_DONE + " AND flag rate_control_adequate set",
   "value": "Cardiology fellow: good, that is a rate I can live with, and he does not have to be "
     "in sinus rhythm today. Nobody can tell me how long he has been in it, so I am not "
     "cardioverting him and neither should you. Three things before he leaves you. He needs to be "
     "anticoagulated, and his CHA2DS2-VASc is at least three so there is no argument to have "
     "about it. He needs a bed that can keep the mask on him and watch the rate, because a "
     "ventricle at thirty to thirty-five percent that has just been slowed can go the other way "
     "if the edema is not treated. And he needs a formal echocardiogram this admission, because "
     "if this cardiomyopathy turns out to be rate related it may recover once he stays in rhythm, "
     "and that changes what he goes home on."},
  {"when": DX_KNOWN + " AND " + ECG_DONE + " AND flag rate_control_given set",
   "value": "Cardiology fellow: so he has had a dose and he is still up around 140. That is a "
     "partial response, which is what one dose usually buys you, and the answer is another dose "
     "of the same thing rather than a second drug. Do not let a partial response push you toward "
     "diltiazem, because with an ejection fraction of thirty to thirty-five that is the one agent "
     "you should not use. Give it again and watch the pressure.\n\n"
     "And know when to stop. If he is still fast after two decent doses, that is telling you "
     "something rather than asking for a third: a rate that will not come down in acute "
     "decompensated heart failure is usually being driven by the decompensation. At that point "
     "the treatment is the edema and the hypoxaemia, not more nodal blockade in a ventricle that "
     "is already struggling. Get the positive pressure on him and diurese him, and the rate will "
     "often follow."},
  {"when": DX_KNOWN + " AND " + ECG_DONE,
   "value": "Cardiology fellow: right, so this is new atrial fibrillation with a rapid ventricular "
     "response and a left ventricle you have just found is running at thirty to thirty-five "
     "percent. Two things follow from that. Do not use diltiazem or verapamil, they are negative "
     "inotropes and the guideline is explicit about avoiding them when systolic function is "
     "significantly reduced. Digoxin or amiodarone are the sensible choices, and if you want a "
     "beta blocker use a small dose and only once his oxygenation is sorted out, because he is "
     "leaning on his sympathetic tone at the moment. Expect to give it twice: one dose will take "
     "the edge off and will not get him where you want him. Second thing: anticoagulate him. His "
     "CHA2DS2-VASc is at least three and there is nothing stopping you, and I would not cardiovert "
     "him today because nobody can tell me how long he has been in it. Get the positive pressure "
     "on, diurese him, slow him down, and we will see him upstairs. He needs a formal "
     "echocardiogram this admission."},
  {"when": DX_KNOWN,
   "value": "Cardiology fellow: an ejection fraction of thirty to thirty-five in a man who has "
     "never had an echocardiogram is a significant finding and it changes your drug choice, so "
     "stay away from diltiazem. I have not seen a twelve-lead on him though, and I am not going "
     "to commit to anything about the rhythm or about ischaemia until somebody shows me one. Send "
     "it through."},
  {"when": ECG_DONE,
   "value": "Cardiology fellow: I have the tracing. That is atrial fibrillation with a rapid "
     "ventricular response, the QRS is narrow, there is no pre-excitation, and the lateral ST "
     "depression is rate related rather than an occlusion, so I am not activating the laboratory "
     "on this. Before I tell you what to slow him down with I want to know what his ventricle is "
     "doing. Put the probe on him and call me back, because if the ejection fraction is reduced "
     "the answer is not diltiazem."},
  {"when": "study ecg_12_lead ordered",
   "value": "Cardiology fellow: I can see an ECG has been requested and there is nothing on my "
     "screen yet. I am not going to talk about the rhythm from a description. Send it through when "
     "it prints and put an ultrasound probe on his heart while you wait, because that is the other "
     "thing I am going to ask you for."},
  {"when": None,
   "value": "Cardiology fellow: you have told me he is fast and irregular and that is about all I "
     "have. I need a twelve-lead and I need to know what his left ventricle is doing before I can "
     "give you anything useful. Get both and call me back."},
 ],

 "consult_critical_care": [
  {"when": "phase is intubated",
   "value": "Intensive care registrar: he is tubed, so he is coming to us. Keep him sedated, watch "
     "his pressure closely because a poorly contracting ventricle on positive pressure with a "
     "recently given rate-controlling drug is exactly the combination that drops, and get me a "
     "film. Have you anticoagulated him yet, and has anybody sorted out what caused this?"},
  {"when": "flag on_niv set AND " + DX_KNOWN,
   "value": "Intensive care registrar: non-invasive ventilation plus a new ejection fraction of "
     "thirty to thirty-five is a monitored bed at minimum, and if he is going to stay on the mask "
     "it is us or a step-down unit that can run it. What I need to know is whether he is settling "
     "on it: respiratory rate, whether he is tolerating the mask, and what his carbon dioxide is "
     "doing. If his rate is still 160 he is going to keep failing whatever I do with the "
     "ventilator settings, so slow him down first."},
  {"when": "flag on_niv set",
   "value": "Intensive care registrar: a patient on non-invasive ventilation is a patient we will "
     "take, but tell me what you are treating. Have you established why he is in pulmonary "
     "edema, and specifically does anybody know what his left ventricle looks like? Put a probe "
     "on him before you call me back."},
  {"when": None,
   "value": "Intensive care registrar: from what you are describing he is in respiratory failure "
     "and nothing has been done about it. Get positive pressure on him before we have a "
     "conversation about beds, because that decision is more urgent than my decision."},
 ],

 "consult_pulmonology": [
  {"when": None,
   "value": "Respiratory registrar: I have listened to what you have described and I do not think "
     "this is a primary lung problem. Diffuse symmetrical B-lines, a raised jugular venous "
     "pressure and peripheral edema in a man in fast atrial fibrillation is cardiogenic pulmonary "
     "edema, and the wheeze you are hearing is edema around the airways rather than "
     "bronchospasm. Treat the heart. If you want us later for the sleep apnoea question, that is "
     "an outpatient conversation."},
 ],
}
