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
 "authoring_note": ("Section 11.2. Twelve of the fourteen catalog maneuvers are authored; "
   "genitourinary and back inherit the catalog default. Peripheral edema sits on the "
   "cardiovascular examination and jugular venous pressure on the neck, per exam_finding_routing, "
   "not where a clinician would instinctively look for them."),

 "exam_airway": [
   {"when": VENT, "value": ex("Endotracheal tube at 23 cm at the teeth, cuff inflated. Normal capnography waveform.")},
   {"when": RF, "value": ex("Patent, but he has stopped talking. Single words when pushed. No stridor or secretions.")},
   {"when": None, "value": ex("Patent. Speaks a short sentence before stopping to breathe. No stridor.", abnormal=False)},
 ],

 "exam_breath": [
   {"when": VENT, "value": ex("Ventilated. Symmetric chest rise. No effort against the ventilator.")},
   {"when": RF, "value": ex("Rate 38, shallow. Marked accessory muscle use, retractions, paradoxical abdominal movement. Stopped talking.")},
   {"when": SUPPORTED, "value": ex("Rate down, deeper and more regular on the mask. Much less accessory muscle use.")},
   {"when": None, "value": ex("Rate 30, shallow. Bolt upright. Neck accessory muscle use, mild retractions. Short sentences.")},
 ],

 "exam_circ": [
   {"when": VENT, "value": ex("Warm. Capillary refill 2 seconds. Irregularly irregular radial pulse, variable volume.")},
   {"when": "phase is rate_controlled_congested OR phase is stabilized",
    "value": ex("Irregularly irregular but slower and countable. No pulse deficit now. Warm, capillary refill 2 seconds.")},
   {"when": None, "value": ex("Irregularly irregular, thready radial pulse. Apical about 160, radial about 130: a pulse deficit. Warm, capillary refill 2 seconds.")},
 ],

 "exam_neck": [
   {"when": VENT, "value": ex("JVP elevated above the clavicle at 45 degrees. Trachea midline. No goiter.")},
   {"when": None, "value": ex("JVP two thirds up the neck at 45 degrees, about 12 cm, no a wave. Hepatojugular reflux positive. No goiter.")},
 ],

 "exam_card": [
   {"when": VENT, "value": ex("Irregularly irregular, about 118. Distant heart sounds. 2+ pitting edema to mid-shins.")},
   {"when": "phase is rate_controlled_congested OR phase is stabilized",
    "value": ex("Irregularly irregular, about 105. Variable S1. Displaced apex. No murmur. 2+ edema to mid-shins.")},
   {"when": None, "value": ex("Irregularly irregular, about 160. Variable S1. Displaced, diffuse apex. 2+ pitting edema to mid-shins.")},
 ],

 "exam_pulm": [
   {"when": VENT, "value": ex("Coarse crackles throughout on the ventilator, worse at the bases. No wheeze.")},
   {"when": "flag diuretic_given set AND flag on_niv set",
    "value": ex("Fine crackles at the bases only. Good air entry. Dull at both bases. No wheeze.")},
   {"when": None, "value": ex("Fine crackles to the mid-zones, worse at the bases. Scattered expiratory wheeze. Dull at both bases.")},
 ],

 "exam_abd": [
   {"when": None, "value": ex("Tender, pulsatile liver edge 3 cm below the costal margin. Soft, no ascites or guarding.")},
 ],

 "exam_msk": [
   {"when": None, "value": ex("Symmetric pitting edema to mid-shins. No calf tenderness, cord or asymmetry. Pedal pulses present.", abnormal=False)},
 ],

 "exam_skin": [
   {"when": VENT, "value": ex("Warm and dry. Good color. No mottling.", abnormal=False)},
   {"when": RF, "value": ex("Clammy, gray, sweating. Dusky lips and nailbeds.")},
   {"when": None, "value": ex("Warm, light sweat. No cyanosis. Shins taut and shiny with edema. No rash.")},
 ],

 "exam_neuro": [
   {"when": VENT, "value": ex("Sedated, GCS 3T. Pupils 3 mm, reactive. No spontaneous movement.")},
   {"when": RF, "value": ex("GCS 13 (E3 V4 M6). Drowsy, confused, obeys commands. No focal deficit.")},
   {"when": None, "value": ex("Alert and oriented, GCS 15. No focal deficit.", abnormal=False)},
 ],

 "exam_psych": [
   {"when": VENT, "value": ex("Sedated. Not assessable.")},
   {"when": None, "value": ex("Anxious and frightened, cooperative. Keeps asking if he is having a heart attack.")},
 ],

 "exam_heent": [
   {"when": None, "value": ex("No lid lag, proptosis or pallor. Moist mucous membranes. No thyroid enlargement.",
      abnormal=False)},
 ],
}

GENERAL_STATUS = {
 "authoring_note": ("Section 11.3. Rendered above the exam list and not clickable, so it is the "
   "one examination finding every learner sees. Kept consistent with the neurological examination "
   "and with the appearance values in each phase."),
 "rules": [
  {"when": VENT, "value": gs("Intubated and sedated. Good color.")},
  {"when": RF, "value": gs("Severe distress, tiring. Drowsy, gray, sweaty, single words. GCS 13.")},
  {"when": "phase is rate_controlled_congested",
   "value": gs("Still in obvious distress, bolt upright, short phrases. Visibly slower rate. GCS 15.")},
  {"when": "phase is breathing_supported",
   "value": gs("Moderate distress, improving on the mask. GCS 15.")},
  {"when": "phase is stabilized",
   "value": gs("Comfortable at rest on the mask. GCS 15.")},
  {"when": None, "value": gs("Awake, anxious, visibly breathless. Upright, hands on thighs, short sentences. GCS 15.")},
 ],
}

# What the figure in the room is doing (engine/patient.js). A guarded rule list like
# GENERAL_STATUS above, and kept consistent with it: both describe the same patient.
PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED, NOT PHYSICIAN-AUTHORED. Drives the figure in the room (engine/patient.js). Derived from this case's own phase descriptions, alertness levels, general status lines and action flags, and adds no clinical fact of its own: eyes closed where the phase is unresponsive, sedated or arrested; work of breathing where the phase description names it; the mask and the tube where the flag the resident's own action sets is set. The respiratory rate is not authored here, the figure breathes at the monitor's rate. Verify each rule against the phase and flag it names, as for any other content key.",
 "verify": "The mask follows flag on_niv and the tube follows flag intubated. presentation is drawn as increased rather than severe because he can still finish a sentence; rate_controlled_congested is drawn as severe from 'still working hard to breathe' at distress level 3. respiratory_failure is drowsy and is drawn eyes open. Sweating is drawn in respiratory_failure, from 'gray and sweaty'. The pads and the central line follow flags pacing_pads_placed and central_access; the line is drawn in the right internal jugular, which the case does not specify.",
 "rules": [
  {
   "when": "flag intubated set OR phase is intubated",
   "value": {
    "eyes": "closed",
    "addons": [
     "intubated"
    ]
   }
  },
  {
   "when": "phase is halted",
   "value": {
    "eyes": "closed"
   }
  },
  {
   "when": "flag on_niv set AND (phase is respiratory_failure OR phase is rate_controlled_congested)",
   "value": {
    "eyes": "open",
    "work_of_breathing": "severe",
    "addons": [
     "bipap_mask"
    ]
   }
  },
  {
   "when": "flag on_niv set AND phase is presentation",
   "value": {
    "eyes": "open",
    "work_of_breathing": "increased",
    "addons": [
     "bipap_mask"
    ]
   }
  },
  {
   "when": "flag on_niv set",
   "value": {
    "eyes": "open",
    "work_of_breathing": "normal",
    "addons": [
     "bipap_mask"
    ]
   }
  },
  {
   "when": "phase is respiratory_failure OR phase is rate_controlled_congested",
   "value": {
    "eyes": "open",
    "work_of_breathing": "severe"
   }
  },
  {
   "when": "phase is presentation",
   "value": {
    "eyes": "open",
    "work_of_breathing": "increased"
   }
  },
  {
   "when": None,
   "value": {
    "eyes": "open",
    "work_of_breathing": "normal"
   }
  }
 ],
 "also": [
  {
   "when": "phase is respiratory_failure",
   "addons": [
    "sweating"
   ]
  },
  {
   "when": "flag pacing_pads_placed set",
   "addons": [
    "defib_pads"
   ]
  },
  {
   "when": "flag central_access set",
   "addons": [
    "central_line"
   ]
  }
 ]
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
             "the evidence of small randomized trials.")}]},

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
     c("Hemoglobin", "13.9", "g/dL", "13.5-17.5", False),
     c("Hematocrit", "41", "%", "38-50", False),
     c("Platelets", "232", "x10^9/L", "150-400", False)],
     comment="Unremarkable. Anemia is a genuine precipitant of decompensation and is excluded here.")}]},

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

 # v0.18a: an arterial gas returned a normal default (pH 7.40, pCO2 40) in a man with a
 # respiratory acidosis on the venous gas. Derived from the venous values.
 "arterial_blood_gas": {"changes_with_state": True, "rules": [
   {"when": RF, "value": panel([
     c("pH", "7.26", "", "7.35-7.45", True),
     c("pCO2", "58", "mmHg", "35-45", True),
     c("pO2", "48", "mmHg", "80-100", True),
     c("Bicarbonate", "25", "mEq/L", "22-26", False),
     c("Lactate", "3.1", "mmol/L", "under 2.0", True)],
     comment="Worsening acute respiratory acidosis with hypoxemia. He is tiring.")},
   {"when": None, "value": panel([
     c("pH", "7.34", "", "7.35-7.45", True),
     c("pCO2", "46", "mmHg", "35-45", True),
     c("pO2", "58", "mmHg", "80-100", True),
     c("Bicarbonate", "24", "mEq/L", "22-26", False),
     c("Lactate", "2.4", "mmol/L", "under 2.0", True)],
     comment="Hypoxemia with a carbon dioxide that is not low despite a respiratory rate of 30.")}]},

 "lactate": {"changes_with_state": False, "rules": [
   {"when": None, "value": val([
     c("Lactate", "2.4", "mmol/L", "under 2.0", True)],
     comment="Mildly raised, and in this patient attributable to the work of breathing and the "
             "tachycardia rather than to sepsis or mesenteric ischemia. It should fall with "
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

 # v0.18a: a chest CT returned "Lungs clear" by default in a man with pulmonary edema.
 "ct_chest": {"changes_with_state": False, "rules": [
   {"when": None, "value": rep("CT chest without contrast. Cardiomegaly with enlargement of the left atrium. "
     "Bilateral perihilar ground-glass opacity with smooth interlobular septal thickening and small "
     "bilateral pleural effusions. No consolidation, no mass. Findings are consistent with pulmonary edema.")}]},

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
     "anticoagulated, and his CHA2DS2-VASc is at least four so there is no argument to have "
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
     "the treatment is the edema and the hypoxemia, not more nodal blockade in a ventricle that "
     "is already struggling. Get the positive pressure on him and diurese him, and the rate will "
     "often follow."},
  {"when": DX_KNOWN + " AND " + ECG_DONE,
   "value": "Cardiology fellow: right, so this is new atrial fibrillation with a rapid ventricular "
     "response and a left ventricle you have just found is running at thirty to thirty-five "
     "percent. Two things follow from that. Do not use diltiazem or verapamil, they are negative "
     "inotropes and the guideline is explicit about avoiding them when systolic function is "
     "significantly reduced. Digoxin or amiodarone are the sensible choices, and if you want a "
     "beta blocker use a small dose and only once his oxygenation is sorted out, because he is "
     "leaning on his sympathetic tone at the moment. Expect it to take more than one dose: the first will take the edge off and will not get him where you want him, and digoxin in particular is loaded over hours. Second thing: anticoagulate him. His "
     "CHA2DS2-VASc is at least four and there is nothing stopping you, and I would not cardiovert "
     "him today because nobody can tell me how long he has been in it. Get the positive pressure "
     "on, diurese him, slow him down, and we will see him upstairs. He needs a formal "
     "echocardiogram this admission."},
  {"when": DX_KNOWN,
   "value": "Cardiology fellow: an ejection fraction of thirty to thirty-five in a man who has "
     "never had an echocardiogram is a significant finding and it changes your drug choice, so "
     "stay away from diltiazem. I have not seen a twelve-lead on him though, and I am not going "
     "to commit to anything about the rhythm or about ischemia until somebody shows me one. Send "
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
     "bronchospasm. Treat the heart. If you want us later for the sleep apnea question, that is "
     "an outpatient conversation."},
 ],
}
