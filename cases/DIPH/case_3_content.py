"""DIPH part 3: exam findings, general status, labs, imaging, consultants.

Every value in LABS is the author's, transcribed from her ABEM admitting form and her
Ideal Scenario Flow. Every reference interval is model output: not one appears in the
source document. See DIPH-SEED.md section 3.6 for the four values that need her signature
and the one the case corrects.
"""

PRES = "phase is presentation"
SEIZ = "phase is seizing"
POST = "phase is post_ictal"
WIDE = "phase is wide_complex_tachycardia"
RESOLVING = "phase is stabilizing OR phase is stabilized"
# Still convulsing in the wide-complex rhythm: she has seized and nothing has ended it. The
# same definition as SEIZURE_STOPPED in case_1_shell.py. Physician review DIPH-29, option C.
STILL_SEIZING = ("phase is wide_complex_tachycardia AND flag seized set AND NOT "
                 "(flag benzo_given set OR action propofol_bolus taken OR action propofol_infusion taken)")


def ex(findings, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": findings}


def gs(findings, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": findings}


def comp(label, value, unit, ref, abnormal, **kw):
    d = {"label": label, "value": value, "unit": unit,
         "reference_range": ref, "abnormal": abnormal}
    d.update(kw)
    return d


def panel(components, comment=None, **kw):
    d = {"kind": "panel", "abnormal": any(c["abnormal"] for c in components),
         "components": components}
    if comment:
        d["comment"] = comment
    d.update(kw)
    return d


def val(label, value, unit, ref, abnormal, comment=None, **kw):
    d = {"kind": "value", "abnormal": abnormal,
         "components": [comp(label, value, unit, ref, abnormal)]}
    if comment:
        d["comment"] = comment
    d.update(kw)
    return d


# ------------------------------------------------------------------ images
# Three images live in cases/DIPH/media/ and are inlined as data URIs at build time. The
# ids below are the file stems. THE ASSIGNMENT OF THE TWO TRACINGS IS THE ONE THING HERE
# MOST LIKELY TO BE WRONG AND IT IS DELIBERATELY ONE LINE: swapping the two values below
# swaps them everywhere.
#
# ONE tracing is a picture, and that is a decision rather than an oversight.
#
# The source supplied two ECGs. Both are wide-complex tachycardias to the eye that drafted
# this, and the second was briefly assigned to the narrowing phase, where the case describes
# a sinus tachycardia at 115 with a QRS of 104 ms that is NARROWER than the arrival tracing.
# It does not look narrower. A picture that contradicts the nurse standing next to it is
# worse than no picture, so the narrowing phase went back to a text report on Aakash Setty's
# instruction, 5 September 2026. `diph-ecg-post-bicarb.jpg` is kept in cases/DIPH/assets/
# rather than in media/, because the build inlines everything in media/ whether a payload
# names it or not. See review packet section 2.9.
#
# What the reviewer is still being asked to confirm: that the remaining image is in fact the
# arrival tracing rather than the repeat, which the source document does not establish, and
# that the arrival tracing is compatible with what the case says about it, which is a sinus
# tachycardia at 135 with a QRS of 132 ms.
#
# 13 October 2026, author instruction: every other tracing is now a picture too, drawn by
# the ECG generator from the case's own read (media/README.md), so unlike the supplied
# repeat it shows what the read says. The arrival tracing stays the supplied image, also
# by instruction. The generated ones carry the same bare caption as the arrival one, since
# this case prints no measurement beside a tracing (v0.12), and each keeps its read as the
# comment, which the debrief prints under it.
ECG_ARRIVAL = "diph-ecg-arrival"
CXR = "diph-cxr"


def image(image_id, caption, abnormal=True, **kw):
    """A result that IS the picture. No report text, by instruction: these carry no
    interpretation at all, so a resident reads the tracing themselves or asks cardiology."""
    d = {"kind": "image", "abnormal": abnormal, "image": image_id, "caption": caption}
    d.update(kw)
    return d


def report(text, abnormal=True, comment=None):
    d = {"kind": "report", "abnormal": abnormal, "report": text}
    if comment:
        d["comment"] = comment
    return d


def always(v):
    return [{"when": None, "value": v}]


# ============================================================== EXAMINATION
EXAM = {
 "authoring_note": (
   "Section 9.2. Thirteen of the fourteen catalog maneuvers are authored; the back "
   "examination inherits the catalog default. The routing is the catalog's and not this "
   "author's preference: the dry hot skin and the absent sweating go to exam_skin, the "
   "agitation and thought content to exam_psych rather than exam_neuro, which owns the level "
   "of consciousness, and the absent bowel sounds and the palpable bladder to exam_abd with "
   "the bladder repeated on exam_gu because the author lists it in both places.\n\n"
   "The findings themselves are the author's physical examination table, verbatim in "
   "substance. Their expansion across phases is not hers."),

 "exam_heent": [
   {"when": SEIZ, "value": ex(
     "Eyes deviated and roving. Pupils 7 mm, equal, sluggish. Dry mucosa. Saliva at the mouth.")},
   {"when": RESOLVING, "value": ex(
     "Pupils 7 mm, equal, sluggish. Mucosa still dry. Roving eye movements settled.")},
   {"when": None, "value": ex(
     "Pupils 7 mm, equal, reactive. Roving eye movements. Mucosa bone dry. No head injury.")}],

 "exam_neck": always(ex(
   "Supple. No meningism. Trachea central. No JVD or thyroid mass.", abnormal=False)),

 "exam_card": [
   {"when": WIDE, "value": ex(
     "Regular wide-complex tachycardia, about 180. Soft heart sounds. Thready pulses.")},
   {"when": "phase is stabilized", "value": ex(
     "Sinus rhythm, about 100. Normal heart sounds. Pulses full.", abnormal=False)},
   {"when": "phase is stabilizing", "value": ex(
     "Sinus tachycardia, about 115, slower than before. Normal heart sounds.")},
   {"when": None, "value": ex(
     "Sinus tachycardia, about 135. Normal heart sounds, no murmur or gallop.")}],

 "exam_pulm": always(ex(
   "Clear, equal air entry. No crackles or wheeze.", abnormal=False)),

 "exam_abd": [
   {"when": RESOLVING, "value": ex(
     "Soft, non-tender. Sparse bowel sounds. Bladder no longer palpable if drained.")},
   {"when": None, "value": ex(
     "Absent bowel sounds after a full minute. Distended bladder to below the umbilicus. Soft, non-tender.")}],

 "exam_gu": [
   {"when": "flag bladder_drained set", "value": ex(
     "Catheterized, 700 mL drained, dark amber urine. Bladder no longer palpable.")},
   {"when": None, "value": ex(
     "Bladder palpable well above the pubis, dull to percussion. No urine passed since she was found.")}],

 "exam_skin": [
   {"when": RESOLVING, "value": ex(
     "Still warm and completely dry, no sweat anywhere. Flush fading. No rash or needle marks.")},
   {"when": None, "value": ex(
     "Hot, flushed and completely dry, no sweat even in the axillae. No rash or needle marks.")}],

 "exam_neuro": [
   {"when": STILL_SEIZING, "value": ex(
     "Still seizing. Generalized jerking, eyes deviated, not rousable.")},
   {"when": WIDE, "value": ex(
     "Obtunded, responds only to pain. Pupils large. No focal deficit.")},
   {"when": SEIZ, "value": ex(
     "Generalized tonic-clonic seizure. Not rousable, eyes deviated, not protecting her airway.")},
   {"when": POST, "value": ex(
     "Post-ictal. Drowsy, rousable to voice with effort. Disoriented. Symmetric reflexes, no lateralizing signs.")},
   {"when": RESOLVING, "value": ex(
     "Drowsy but rousable, settling. Oriented to person only. No focal deficit or clonus.")},
   {"when": None, "value": ex(
     "Agitated, disoriented, inattentive. No focal deficit. Symmetric reflexes, no clonus or hyperreflexia. No meningism.")}],

 "exam_psych": [
   {"when": SEIZ + " OR " + POST + " OR " + WIDE, "value": ex(
     "Not assessable. Unable to converse.")},
   {"when": RESOLVING, "value": ex(
     "Drowsy and settled. Cannot give a reliable account yet.")},
   {"when": None, "value": ex(
     "Agitated, plucking at the sheets and leads, reaching for things not there. Nonsensical speech.")}],

 "exam_airway": [
   {"when": "flag airway_protected set", "value": ex(
     "Endotracheal tube in place, cuff up. Normal capnography waveform.")},
   {"when": SEIZ, "value": ex(
     "Not protecting her airway. Clenched teeth, secretions at the mouth.")},
   {"when": POST, "value": ex(
     "Patent with a jaw thrust. Reduced gag, intermittent snoring.")},
   {"when": WIDE, "value": ex(
     "Not protecting her airway well. Snoring respirations, secretions pooling.")},
   {"when": None, "value": ex(
     "Patent. Talking, though not sensibly. No stridor. Dry mucosa.", abnormal=False)}],

 "exam_breath": [
   {"when": SEIZ, "value": ex(
     "Not ventilating adequately. Irregular chest movement with the seizure.")},
   {"when": RESOLVING, "value": ex(
     "Normal rate, no increased work. Equal expansion.",
     abnormal=False)},
   {"when": POST, "value": ex(
     "Spontaneous, normal rate but shallow. No increased work.")},
   {"when": WIDE, "value": ex(
     "Rate about 22, shallow. No increased work of breathing.")},
   {"when": None, "value": ex(
     "Rate about 25, no increased work of breathing. No accessory muscle use.")}],

 "exam_circ": [
   {"when": WIDE, "value": ex(
     "Cool peripheries. Capillary refill 3 seconds. Weak, very fast radial pulse.")},
   {"when": RESOLVING, "value": ex(
     "Warm, capillary refill under 2 seconds. Regular pulse, slower than before. Flush faded.", abnormal=False)},
   {"when": None, "value": ex(
     "Warm and flushed to the fingertips. Capillary refill under 2 seconds. Fast, full pulse.")}],

 "exam_msk": always(ex(
   "No deformity, bruising or wounds. Full range of movement. No sign of a fall.", abnormal=False)),
}

# ============================================================== GENERAL STATUS
GENERAL_STATUS = {
 "authoring_note": (
   "Section 9.3. Rendered above the maneuver list and not clickable, so it is the one "
   "examination finding every learner sees. Kept consistent with the neurological and "
   "psychiatric examinations and with the appearance values of each phase."),
 "rules": [
   {"when": "flag airway_protected set AND " + WIDE, "value": gs(
     "Intubated and sedated. Gray, wide-complex rhythm on the monitor, thready pulse.")},
   {"when": "flag airway_protected set AND phase is stabilized", "value": gs(
     "Intubated and sedated. Warm, cooling under way. Narrow complexes on the monitor.")},
   {"when": "flag airway_protected set", "value": gs(
     "Intubated and sedated. Hot to touch.")},
   {"when": STILL_SEIZING, "value": gs(
     "Still seizing, gray and unresponsive. Wide-complex rhythm, thready pulse.")},
   {"when": SEIZ, "value": gs(
     "Generalized seizure. Unresponsive, not protecting her airway, cyanosed lips.")},
   {"when": WIDE, "value": gs(
     "Obtunded and gray, responds only to pain. Wide-complex rhythm, thready pulse. GCS 9.")},
   {"when": POST, "value": gs(
     "Post-ictal. Drowsy, rousable to voice, hot and flushed. Disoriented. GCS 12.")},
   {"when": "phase is stabilizing", "value": gs(
     "Settled and drowsy, still warm, flush fading. Narrower complexes on the monitor. GCS 13.")},
   {"when": "phase is stabilized", "value": gs(
     "Drowsy but rousable, comfortable. Pupils still large. GCS 14.")},
   {"when": "phase is pulseless_vt", "value": gs(
     "Cardiac arrest. No pulse or breathing. Wide complexes on the monitor.")},
   {"when": None, "value": gs(
     "Agitated, disoriented, flushed, hot and dry, plucking at the leads. Nonsense speech. GCS 13.")},
 ],
}

# ============================================================== LABORATORY
# Every value is the author's. Every reference interval is model output.
# What the figure in the room is doing (engine/patient.js). A guarded rule list like
# GENERAL_STATUS above, and kept consistent with it: both describe the same patient.
# 19 October 2026, author instruction: the pupils, for the magnified view of the eyes over the
# figure and the penlight (engine/pupils.js). Taken from this case's own HEENT findings,
# "Pupils 7 mm, equal", sluggish when seizing and when stabilizing and "reactive" otherwise.
PUPILS = {
 "authoring_note": "MODEL-AUTHORED, NOT PHYSICIAN-AUTHORED. Drawn sizes and responses for the eye view. 7 mm and equal throughout, from exam_heent. Anticholinergic mydriasis is drawn with a sluggish response in every state, including the arrival state where exam_heent says 'reactive': a sluggish pupil still reacts, and a brisk one would constrict from 7 mm to about 4 mm, which this toxidrome does not do.",
 "verify": "Two choices to check. (1) The arrival pupils are drawn sluggish where exam_heent says reactive; change either so the two agree. (2) In pulseless VT and the halted state the pupils are drawn dilated and fixed, 8 mm, which no text in this case states; it is the expected finding in a patient in arrest, not an authored one.",
 "rules": [
  {"when": "phase is pulseless_vt OR phase is halted", "value": {"state": "dilated_fixed", "size_mm": 8}},
  {"when": None, "value": {"state": "dilated", "size_mm": 7, "reaction": "sluggish"}},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": "MODEL-AUTHORED, NOT PHYSICIAN-AUTHORED. Drives the figure in the room (engine/patient.js). Derived from this case's own phase descriptions, alertness levels, general status lines and action flags, and adds no clinical fact of its own: eyes closed where the phase is unresponsive, sedated or arrested; work of breathing where the phase description names it; the mask and the tube where the flag the resident's own action sets is set. The respiratory rate is not authored here, the figure breathes at the monitor's rate. Verify each rule against the phase and flag it names, as for any other content key.",
 "verify": "Three choices to check. (1) The convulsion is drawn with the eyes OPEN, on the understanding that the eyes are usually open in a generalized tonic-clonic seizure and that closed eyes during the event point toward a functional seizure; change it if that is not what should be taught. (2) Once airway_protected is set the figure is intubated, still and eyes closed even in the seizing phase, on the assumption of induction and paralysis; a paralyzed patient may still be seizing electrically and the figure cannot show that. (3) Since physician review DIPH-29 (27 October 2026) the wide-complex phase is drawn convulsing when she reached it still seizing (flag seized set, nothing has ended the seizure) and eyes closed, obtunded, otherwise. (4) post_ictal has no rule of its own: it is alertness level 1 and is drawn drowsy, with heavy lids and a nodding head, by the figure itself. Agitation is drawn on arrival, from 'agitated ... plucking at the leads', until the airway is protected. She is 'hot and dry', so she is never drawn sweating.",
 "rules": [
  {
   "when": "flag airway_protected set",
   "value": {
    "eyes": "closed",
    "addons": [
     "intubated"
    ]
   }
  },
  {
   "when": "phase is pulseless_vt OR phase is halted",
   "value": {
    "eyes": "closed"
   }
  },
  {
   "when": "phase is seizing",
   "value": {
    "eyes": "open",
    "seizure": True
   }
  },
  {
   "when": STILL_SEIZING,
   "value": {
    "eyes": "open",
    "seizure": True
   }
  },
  {
   "when": "phase is wide_complex_tachycardia",
   "value": {
    "eyes": "closed"
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
   "when": "phase is presentation AND NOT flag airway_protected set",
   "addons": [
    "agitation"
   ]
  }
 ]
}

LABS = {
 "authoring_note": (
   "Section 9.4. Structured payloads with abnormal flags set by the author of the case file "
   "and not computed by the renderer. The numbers are Dr Medwid's, from her admitting form and "
   "her scenario flow. Not one reference interval appears in her document, so every one below "
   "is model output awaiting a physician's signature. Where the catalog carries a default for "
   "the same analyte, the catalog's interval is used so that the two agree.\n\n"
   "One value is corrected rather than transcribed. The source's chemistry panel gives CO2 as "
   "34 mEq/L and its blood gas gives HCO3 as 13 mEq/L; with a sodium of 135 and a chloride of "
   "109 the second is consistent with the pH of 7.28 and the first gives an anion gap of "
   "negative 8. The panel below carries 13. See DIPH-SEED.md section 3.6."),

 "fingerstick_blood_sugar": {
   "changes_with_state": False,
   "rules": always(val("Capillary glucose", "110", "mg/dL", "70-140 (random)", False,
     comment="Normal. The author's value."))},

 "basic_chemistry_chem_7": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag bicarb_given set", "value": panel([
        comp("Sodium", "141", "mEq/L", "135-145", False),
        comp("Potassium", "3.1", "mEq/L", "3.5-5.0", True),
        comp("Chloride", "107", "mEq/L", "98-107", False),
        comp("Bicarbonate", "21", "mEq/L", "22-29", True),
        comp("BUN", "12", "mg/dL", "7-20", False),
        comp("Creatinine", "0.8", "mg/dL", "0.6-1.2", False),
        comp("Glucose", "126", "mg/dL", "70-140 (random)", False)],
        comment=("Drawn after sodium bicarbonate. The acidosis is correcting, and the sodium "
                 "and potassium have moved in the directions the treatment moves them: a rising "
                 "sodium from the sodium load and a falling potassium from the alkalinization "
                 "driving potassium into cells. Both are complications of the treatment rather "
                 "than of the poisoning, and the potassium is the one to replace, because "
                 "hypokalemia lengthens a QT that is already long."),
        verify=("This panel is entirely model output. The author supplied one chemistry panel "
                "and it is the pre-treatment one below. The direction of every change here is "
                "textbook and the magnitudes are invented."))},
     {"when": None, "value": panel([
        comp("Sodium", "135", "mEq/L", "135-145", False),
        comp("Potassium", "3.8", "mEq/L", "3.5-5.0", False),
        comp("Chloride", "109", "mEq/L", "98-107", True),
        comp("Bicarbonate", "13", "mEq/L", "22-29", True),
        comp("BUN", "12", "mg/dL", "7-20", False),
        comp("Creatinine", "0.8", "mg/dL", "0.6-1.2", False),
        comp("Glucose", "120", "mg/dL", "70-140 (random)", False)],
        comment=("A metabolic acidosis with an anion gap of 13, near normal, so the lactate explains only part of the fall in bicarbonate. The renal function is normal, which is the baseline the "
                 "rhabdomyolysis will be followed against."),
        verify=("The source gives CO2 as 34 in this panel and HCO3 as 13 on the gas. The two "
                "cannot both be true and 13 is the one consistent with the pH and the anion "
                "gap. Corrected on drafting judgment and needs the author's signature."))}]},

 "complete_blood_count_cbc": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("White cell count", "16.0", "K/uL", "4.0-11.0", True),
     comp("Hemoglobin", "16.9", "g/dL", "12.0-16.0 (female)", True),
     comp("Hematocrit", "47.2", "%", "36-46 (female)", True),
     comp("Platelets", "250", "K/uL", "150-400", False)],
     comment=("A leukocytosis without a source, and a hemoglobin and hematocrit at the top of "
              "or above the female interval."),
     verify=("All four values are the author's. The source writes the white count as '16 L/ul', "
             "taken here as 16 K/microlitre. The hemoglobin of 16.9 and hematocrit of 47.2 "
             "are above the usual female interval and are flagged abnormal on that basis; "
             "hemoconcentration is a plausible reading in a hyperthermic patient who has not "
             "drunk for hours, but it is a reading and not the author's statement.")))},

 "arterial_blood_gas": {
   "changes_with_state": True,
   "rules": [
     {"when": SEIZ, "value": panel([
        comp("pH", "6.99", "", "7.35-7.45", True),
        comp("pCO2", "52", "mmHg", "35-45", True),
        comp("pO2", "61", "mmHg", "80-100", True),
        comp("Bicarbonate", "12", "mEq/L", "22-26", True),
        comp("Lactate", "6.4", "mmol/L", "0.5-2.0", True)],
        comment=("A mixed metabolic and respiratory acidosis during the convulsion. This is the "
                 "worst the pH gets and it is not only a respiratory problem: acidemia increases the ionized fraction of the drug, the form that binds the cardiac sodium channel, so the gas is a cardiac measurement here as well as a respiratory "
                 "one."),
        verify="Model output. The author supplies one gas and it is the arrival one below.")},
     {"when": "flag bicarb_given set", "value": panel([
        comp("pH", "7.47", "", "7.35-7.45", True),
        comp("pCO2", "30", "mmHg", "35-45", True),
        comp("pO2", "142", "mmHg", "80-100", True),
        comp("Bicarbonate", "21", "mEq/L", "22-26", True),
        comp("Lactate", "2.2", "mmol/L", "0.5-2.0", True)],
        comment=("Drawn after bicarbonate. A pH of 7.47 is approaching the range usually aimed at when alkalinizing for sodium-channel blockade, commonly taken to about 7.50 to 7.55. Further alkalinization past that buys little and costs potassium and "
                 "ionized calcium. The pO2 reflects supplemental oxygen and the reference "
                 "interval quoted assumes room air, which is a known limitation of the catalog "
                 "default."),
        verify="Model output.")},
     {"when": None, "value": panel([
        comp("pH", "7.28", "", "7.35-7.45", True),
        comp("pCO2", "28", "mmHg", "35-45", True),
        comp("pO2", "94", "mmHg", "80-100", False),
        comp("Bicarbonate", "13", "mEq/L", "22-26", True),
        comp("Lactate", "3.1", "mmol/L", "0.5-2.0", True)],
        comment=("An appropriately compensated metabolic acidosis on room air. The pCO2 is revised from the source's 34 to 28 so that the three values agree."),
        verify=("Four values are the author's: pH 7.28, pO2 94, bicarbonate 13 and lactate 3.1. "
                "The pCO2 is revised from her 34 to 28 (v0.18a), kept by physician review DIPH-06 "
                "(Aakash Setty, 27 October 2026). The reference intervals are not hers, and the "
                "catalog's own note applies: an ABG default assumes room air and nothing in "
                "the schema knows when supplemental oxygen is running."))}]},

 "venous_blood_gas": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag bicarb_given set", "value": panel([
        comp("pH", "7.41", "", "7.31-7.41", False),
        comp("pCO2", "34", "mmHg", "41-51", True),
        comp("Bicarbonate", "21", "mEq/L", "22-26", True)],
        comment="Adequate for following the pH and the bicarbonate.", verify="Model output.")},
     {"when": None, "value": panel([
        comp("pH", "7.25", "", "7.31-7.41", True),
        comp("pCO2", "31", "mmHg", "41-51", True),
        comp("Bicarbonate", "13", "mEq/L", "22-26", True)],
        comment=("The venous equivalent of the arterial sample. Adequate for the two numbers "
                 "this case follows, which are the pH and the bicarbonate."),
        verify="Derived from the author's arterial values, not supplied by her.")}]},

 "lactate": {
   "changes_with_state": True,
   "rules": [
     {"when": WIDE, "value": val("Lactate", "7.8", "mmol/L", "0.5-2.0", True,
        comment=("High, and rising. By this point it reflects hypoperfusion as well as muscle "
                 "activity."),
        verify="Model output. The author supplies one lactate and it is the arrival value.")},
     {"when": SEIZ, "value": val("Lactate", "6.4", "mmol/L", "0.5-2.0", True,
        comment="Rises with the convulsion. It should fall once she is sedated.")},
     {"when": RESOLVING, "value": val("Lactate", "2.0", "mmol/L", "0.5-2.0", False,
        comment="Falling, as expected once the muscle activity has stopped.")},
     {"when": None, "value": val("Lactate", "3.1", "mmol/L", "0.5-2.0", True,
        comment=("The author's value. Produced by agitation and muscle activity rather than by "
                 "sepsis or hypoperfusion, which matters because it is not a reason to escalate "
                 "the sepsis pathway."))}]},

 "creatine_kinase_ck": {
   "changes_with_state": False,
   "rules": always(val("Creatine kinase", "540", "U/L", "30-200", True,
     comment=("Raised, and this is early rather than established rhabdomyolysis. Follow it "
              "serially with the creatinine and the electrolytes, keep her volume replete, and "
              "measure the urine output."),
     verify=("The value is the author's. The reference interval of 30 to 200 U/L is model "
             "output; creatine kinase intervals vary widely by assay, sex and muscle mass.")))},

 "acetaminophen_level": {
   "changes_with_state": False,
   "rules": always(val("Acetaminophen", "<10", "mcg/mL", "Not detected", False,
     comment=("Not detected. The author's value. Worth having: combination sleep preparations "
              "contain acetaminophen and a reported exposure in a deliberate overdose is often "
              "incomplete.")))},

 "salicylate_aspirin_level": {
   "changes_with_state": False,
   "rules": always(val("Salicylate", "0", "mg/dL", "<4", False,
     comment="Not detected. The author's value."))},

 "ethanol_level_etoh": {
   "changes_with_state": False,
   "rules": always(val("Ethanol", "<10", "mg/dL", "<10", False,
     comment="Not detected. The author's value."))},

 "urine_tox_screen": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("Tricyclic antidepressants", "POSITIVE", "", "Negative", True),
     comp("Amphetamines", "Negative", "", "Negative", False),
     comp("Benzodiazepines", "Negative", "", "Negative", False),
     comp("Cocaine metabolite", "Negative", "", "Negative", False),
     comp("Opiates", "Negative", "", "Negative", False),
     comp("Cannabinoids", "Negative", "", "Negative", False),
     comp("Barbiturates", "Negative", "", "Negative", False)],
     comment=("Qualitative immunoassay. Detection windows differ by class and a positive result "
              "reports exposure at some point rather than the cause of the presentation in "
              "front of you."),
     verify=("The author states in her teaching text that the urine screen may be falsely "
             "positive for tricyclic antidepressants in diphenhydramine poisoning, and this "
             "case authors that positive. Which platforms cross-react, and how reliably, is "
             "assay-specific and is not stated in her document. The panel of seven classes and "
             "the negative results are model output; only the tricyclic positive is hers.")))},

 "urine_hcg_qualitative": {
   "changes_with_state": False,
   "rules": always(val("Urine hCG", "Negative", "", "Negative", False,
     comment="Not pregnant. The author's value."))},

 "serum_hcg_quantitative": {
   "changes_with_state": False,
   "rules": always(val("Serum beta-hCG", "<1", "mIU/mL", "<5 (not pregnant)", False,
     comment="Not pregnant. Derived from the author's negative hCG."))},

 "urinalysis": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("Color", "Amber", "", "Yellow", True),
     comp("Specific gravity", "1.030", "", "1.005-1.025", True),
     comp("Blood", "Negative", "", "Negative", False),
     comp("Red cells", "0-2", "/hpf", "0-2", False),
     comp("Protein", "Trace", "", "Negative", True),
     comp("Leukocyte esterase", "Negative", "", "Negative", False),
     comp("Nitrite", "Negative", "", "Negative", False),
     comp("Ketones", "1+", "", "Negative", True)],
     comment=("Concentrated urine. Negative for blood."),
     verify=("Model output. The author does not supply a urinalysis; she lists it among the "
             "studies she expects to be ordered. Physician review DIPH-20 (Aakash Setty, 27 "
             "October 2026) replaced the blood-positive, red-cell-negative pattern with negative "
             "blood and concentrated urine, because a creatine kinase of 540 is early. The "
             "reference interval for specific gravity is model output.")))},

 "magnesium_level": {
   "changes_with_state": False,
   "rules": always(val("Magnesium", "2.0", "mg/dL", "1.7-2.4", False,
     comment="Normal.",
     verify=("Model output. The author does not supply a magnesium. It was invented low (1.6) "
             "to make a teaching point about torsades, and physician review DIPH-18 (Aakash "
             "Setty, 27 October 2026) set it normal.")))},

 "calcium_ionized": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag bicarb_given set", "value": val("Ionized calcium", "1.09", "mmol/L",
        "1.12-1.32", True,
        comment=("Fallen after alkalinization, which is expected: a rising pH increases the "
                 "fraction of calcium bound to albumin and lowers the ionized fraction."),
        verify="Model output.")},
     {"when": None, "value": val("Ionized calcium", "1.18", "mmol/L", "1.12-1.32", False,
        comment="Normal before treatment.", verify="Model output.")}]},

 "liver_function_tests_lfts": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("Total bilirubin", "0.6", "mg/dL", "0.2-1.2", False),
     comp("ALT", "28", "U/L", "7-52", False),
     comp("AST", "46", "U/L", "13-39", True),
     comp("Alkaline phosphatase", "72", "U/L", "34-104", False),
     comp("Albumin", "4.4", "g/dL", "3.5-5.0", False)],
     comment=("Essentially normal. The mildly raised AST is of muscle rather than hepatic origin "
              "and tracks with the creatine kinase."),
     verify="Model output. The author does not supply liver function tests."))},

 "coagulation_panel": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("INR", "1.0", "", "0.9-1.1", False),
     comp("Prothrombin time", "12.4", "s", "11.0-13.5", False),
     comp("aPTT", "29", "s", "25-35", False)],
     comment="Normal.", verify="Model output."))},

 "troponin_t": {
   "changes_with_state": False,
   "rules": always(val("Troponin T", "0.04", "ng/mL", "<0.01", True,
     comment=("Mildly raised without an ischemic pattern on the tracing. Demand and a poisoned "
              "myocardium rather than an acute coronary syndrome. It does not change what you "
              "do."),
     verify="Model output. The author does not supply a troponin."))},

 "tsh": {
   "changes_with_state": False,
   "rules": always(val("TSH", "1.8", "mIU/L", "0.4-4.0", False,
     comment="Normal. Thyroid storm is off the list.", verify="Model output."))},
}

# ============================================================== IMAGING, ECG, BEDSIDE
IMAGING = {
 "authoring_note": (
   "Section 9.4, kind report: findings and not conclusions. The words sodium-channel blockade "
   "do not appear in any tracing below; they appear in the debrief note on the ECG action, "
   "where the learner meets them after committing to an interpretation rather than before.\n\n"
   "Two of the source document's four images ARE used, since v0.12: the arrival twelve-lead "
   "and the chest radiograph, inlined from cases/DIPH/media/ and shown as a thumbnail in the "
   "chart that opens full size. The head CT is not, because nothing in this case turns on "
   "looking at it, and the second tracing is not, for the reason below.\n\n"
   "Both carry NO report text at all, by instruction. A twelve-lead tracing is a picture and "
   "reading it is the skill; handing a resident 'QRS duration 132 ms' beside it does the "
   "measurement for them, and this case is built around whether they look. What follows from "
   "that, and is worth knowing before playing it: the arrival QRS duration appears nowhere in "
   "the interface until the debrief, except in what a consultant says. consult_cardiology "
   "will read the tracing for a resident who asks, which is the intended escape hatch and is "
   "deliberately not prompted for.\n\n"
   "Every other tracing in this case is text, including the narrowing phase, which was "
   "briefly an image and was reverted: the second supplied tracing is as broad as the first "
   "and contradicted the nurse line about the complexes narrowing. So the arrival tracing is "
   "the one study in this case a resident has to read for themselves, and everything after it "
   "reports itself. That asymmetry is deliberate and it is the thing to sign off. See review "
   "packet section 2.9.\n\n"
   "The provenance of the source images is still not established in the document, which cites "
   "an ACEP toxicology case file and thepoisonreview.com in its reference list. That question "
   "was avoidable while the images were unused and is not avoidable now."),

 "ecg_12_lead": {
   "changes_with_state": True,
   "result_shape": "structured",
   "rules": [
     {"when": "phase is pulseless_vt", "value": image("diph-ecg-pulseless-vt", "Twelve-lead ECG", comment=
       "Wide-complex tachycardia at approximately 190 per minute. No organized mechanical "
       "activity. QRS duration approximately 200 ms.")},
     {"when": WIDE, "value": image("diph-ecg-wide-complex-tachycardia", "Twelve-lead ECG", comment=
       "Monomorphic wide-complex tachycardia at approximately 180 per minute. QRS duration "
       "approximately 180 ms. No discernible P waves. Terminal R wave in aVR of 7 mm with an "
       "R to S ratio in aVR greater than 0.7. Rightward terminal QRS axis. No ST elevation.")},
     {"when": SEIZ, "value": image("diph-ecg-seizing", "Twelve-lead ECG", comment=
       "Sinus tachycardia at approximately 150 per minute. QRS duration 148 ms, wider than on "
       "the previous tracing. Terminal R wave in aVR of 6 mm. Rightward terminal QRS axis. QTc "
       "512 ms. Frequent ventricular ectopics. Baseline heavily obscured by movement artifact.")},
     {"when": "phase is stabilized", "value": image("diph-ecg-stabilized", "Twelve-lead ECG", comment=
       "Sinus tachycardia at approximately 100 per minute. QRS duration 96 ms. Terminal R wave "
       "in aVR now 1 mm with an R to S ratio below 0.7. Normal QRS axis. QTc 445 ms. No ST "
       "elevation.")},
     # A generated picture since 13 October 2026 (see the images note above). Before that,
     # text, not a picture. Both supplied tracings are wide-complex; neither is narrow, so
     # showing one here put a broad tracing under the nurse's line about the complexes
     # narrowing. Reverted on Aakash Setty's instruction, 5 September 2026. The numbers are
     # the ones consult_cardiology already reads aloud on the repeat tracing, and the rate is
     # this phase's own authored heart rate.
     {"when": "phase is stabilizing", "value": image("diph-ecg-stabilizing", "Twelve-lead ECG", comment=
       "Sinus tachycardia at approximately 115 per minute. QRS duration 104 ms, narrower than "
       "on the arrival tracing. Terminal R wave in aVR now 2 mm with an R to S ratio below "
       "0.7. QTc 470 ms, still prolonged. No ST elevation.")},
     # v0.18a: bicarbonate given before the seizure narrows the QRS in the arrival phase too,
     # so a repeat tracing does not tell the resident that the drug failed.
     {"when": "phase is presentation AND flag bicarb_given set", "value": image("diph-ecg-arrival-after-bicarbonate", "Twelve-lead ECG", comment=
       "Sinus tachycardia at approximately 135 per minute. QRS duration 116 ms, narrower than "
       "on the arrival tracing. Terminal R wave in aVR of 3 mm. QTc 480 ms. No ST elevation.")},
     {"when": None, "value": image(ECG_ARRIVAL, "Twelve-lead ECG")}],
   "verify": (
     "The arrival tracing is the case. The author's narrative says the examinee 'should "
     "recognize the lack of a significant R wave in lead aVR', and her own teaching text four "
     "pages later says there may be a large terminal R in aVR and that physostigmine should be "
     "withheld for an R in aVR greater than 3 mm with a widened QRS; her debriefing guide lists "
     "a terminal R wave in aVR and an increased R to S ratio among the findings of "
     "sodium-channel blockade. Three of the four say the R wave is present. It is authored "
     "present at 5 mm. Every number in every tracing here, including the 132 ms and the QTc of "
     "495, is model output: the source gives no measurements at all. See DIPH-SEED.md section "
     "9.2. [UNVERIFIED, confirm before release]")},

 "xr_chest": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag airway_protected set", "value": report(
       "Endotracheal tube tip 4 cm above the carina. Lungs clear. Heart size normal. No "
       "pneumothorax.")},
     {"when": None, "value": image(CXR, "Chest radiograph", abnormal=False)}]},

 "ct_head": {
   "changes_with_state": False,
   "rules": always(report(
     "No intracranial hemorrhage. No mass, no midline shift, no established infarct. "
     "Ventricles and sulci normal for age. No skull fracture.", abnormal=False))},

 "ultrasound_cardiac": {
   "changes_with_state": True,
   "rules": [
     {"when": WIDE, "value": report(
       "Fast, poorly organized ventricular contraction with reduced systolic function. No "
       "pericardial effusion. Inferior vena cava small and collapsing.")},
     {"when": None, "value": report(
       "Vigorous left ventricular systolic function at a fast rate. No pericardial effusion. No "
       "right ventricular dilatation. Inferior vena cava small and collapsing.")}],
   "verify": "Model output. The author does not author a bedside echocardiogram."},
}

# ============================================================== CONSULTANTS
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. Rules run from most specific to least specific and every one of them gates on "
   "the study state, so that no consultant discusses a tracing nobody has ordered and none "
   "discusses a result that has not come back. Each has a pending tier, because with a "
   "ten-second turnaround there is a real window in which the ECG is ordered and not resulted.\n\n"
   "Only toxicology is state-changing: it sets tox_consulted, which is one of the two flags the "
   "stabilized phase requires."),

 "consult_toxicology": [
   # Physician review DIPH-30 (Aakash Setty, 27 October 2026): phase tiers first, so a
   # consultant does not quote the arrival QRS during a seizure or a wide-complex rhythm.
   {"when": WIDE,
    "value": ("Toxicology fellow: a wide-complex rhythm in this poisoning is the sodium "
              "channel. Sodium bicarbonate now, 1 to 2 mEq/kg, repeated until the complexes "
              "narrow. No amiodarone, procainamide or physostigmine. A benzodiazepine if she is "
              "still seizing.")},
   {"when": SEIZ,
    "value": ("Toxicology fellow: stop the seizure first, with a benzodiazepine, repeated if "
              "she keeps going. The seizure is making her acid worse and her QRS wider, so if "
              "the complexes look broad, sodium bicarbonate too. No phenytoin, no physostigmine.")},
   {"when": "study ecg_12_lead resulted AND flag bicarb_given set",
    "value": ("Toxicology fellow: good, keep going. Repeat the boluses until the QRS narrows, "
              "then start an infusion, aiming for a pH of about 7.50 to 7.55. Watch the sodium, "
              "potassium and ionized calcium. No physostigmine until the QRS is normal.")},
   {"when": "study ecg_12_lead resulted",
    "value": ("Toxicology fellow: a wide QRS with a terminal R in aVR is sodium-channel "
              "blockade. Give sodium bicarbonate, 1 to 2 mEq/kg, repeated, with a tracing after "
              "each. No physostigmine and no haloperidol. Benzodiazepines and active cooling.")},
   {"when": "study ecg_12_lead ordered",
    "value": ("Toxicology fellow: I need the QRS duration and whether there is a terminal R in "
              "aVR, because that decides everything. Meanwhile benzodiazepines, active cooling, "
              "a glucose, and an acetaminophen level.")},
   {"when": None,
    "value": ("Toxicology fellow: this looks antimuscarinic, but the QRS decides her "
              "management. Get me an ECG and call me straight back. Meanwhile benzodiazepines "
              "rather than antipsychotics, cool her, and send an acetaminophen level.")}],

 "consult_critical_care": [
   {"when": WIDE,
    "value": ("Intensivist: she is coming to us, but she is not safe to move in this rhythm. "
              "Sodium bicarbonate now, a benzodiazepine if she is still seizing, pads on, and "
              "call toxicology. Ring me when the complexes narrow.")},
   {"when": SEIZ,
    "value": ("Intensivist: she is coming to us. Stop the seizure first with a benzodiazepine, "
              "protect her airway, and treat a wide QRS with sodium bicarbonate. Call me back "
              "once she has stopped.")},
   {"when": "study ecg_12_lead resulted AND flag bicarb_given set",
    "value": ("Intensivist: yes, we will take her. Keep the bicarbonate going with continuous "
              "monitoring and serial ECGs. No psychiatric bed until the QRS has been normal for "
              "a good while. Send a creatine kinase.")},
   {"when": "study ecg_12_lead resulted",
    "value": ("Intensivist: with a QRS like that she is coming to us, but start sodium "
              "bicarbonate before she comes. Get a repeat tracing, and cool her.")},
   {"when": "study ecg_12_lead ordered",
    "value": ("Intensivist: she is coming to us. I want the twelve-lead first, because a "
              "conduction problem changes her first hour. Call me when it is through.")},
   {"when": None,
    "value": ("Intensivist: tell me the ECG and the temperature. What I need to know is whether "
              "she has a conduction abnormality and whether anyone has treated it.")}],

 "consult_psychiatry": [
   {"when": "flag bicarb_given set AND flag cooling_started set",
    "value": ("Psychiatry registrar: thank you for waiting until she is treated. She needs a "
              "monitored medical bed and we will assess her there. Someone should be with her "
              "continuously, and not her mother.")},
   {"when": None,
    "value": ("Psychiatry registrar: she is not ready for me. She is delirious, so I cannot "
              "assess capacity or risk. Call me when she is on a monitored bed and awake, and "
              "keep someone with her.")}],

 "consult_neurology": [
   {"when": "study ct_head resulted AND study ecg_12_lead resulted",
    "value": ("Neurology registrar: the scan is clear and the tracing is not. This is a toxic "
              "seizure, so benzodiazepines and fix the physiology. If it recurs, levetiracetam "
              "or propofol, and no phenytoin.")},
   {"when": None,
    "value": ("Neurology registrar: this is a provoked seizure until proven otherwise. "
              "Benzodiazepines, fix the cause, and get a head CT if you have not. No phenytoin "
              "in an unknown overdose.")}],

 "consult_cardiology": [
   # The escape hatch for a resident who cannot read the tracing, and it is deliberately not
   # prompted for and tagged neutral: the case wants them to look first. Cardiology reads the
   # ECG out loud, which is the one thing the images cannot do for themselves, and then hands
   # the management back, because the management is toxicological.
   {"when": "phase is wide_complex_tachycardia OR phase is pulseless_vt",
    "value": ("Cardiology fellow, looking at the monitor: in a poisoning this is the sodium "
              "channel, and it is not mine. Bicarbonate, no amiodarone and no procainamide. If "
              "she loses her pressure, shock her. Call toxicology.")},
   {"when": "study ecg_12_lead resulted AND flag bicarb_given set AND flag ecg_repeated set",
    "value": ("Cardiology fellow: the QRS was 132 milliseconds with a terminal R in aVR, and on "
              "the repeat it is about 104, so the bicarbonate is working. Keep going. This "
              "needs toxicology, not me.")},
   {"when": "study ecg_12_lead resulted",
    "value": ("Cardiology fellow: sinus tachycardia, a QRS of 132 milliseconds and a terminal R "
              "in aVR. That is sodium-channel blockade, not ischemia. Treat it with sodium "
              "bicarbonate, and the call is to toxicology.")},
   {"when": "study ecg_12_lead ordered",
    "value": ("Cardiology fellow: the tracing is not through yet. Send it to me and I will read "
              "it with you.")},
   {"when": None,
    "value": ("Cardiology fellow: send me a twelve-lead and I will read it with you. If the QRS "
              "is wide from a sodium-channel blocker, the treatment is bicarbonate and the call "
              "is to toxicology.")}],

 "consult_renal": [
   {"when": "study creatine_kinase_ck resulted",
    "value": ("Renal registrar: that creatine kinase is early and her creatinine is normal, so "
              "keep her filled and measure the urine output. Dialysis does not remove "
              "diphenhydramine.")},
   {"when": None,
    "value": ("Renal registrar: nothing for me yet. Send a creatine kinase and a creatinine and "
              "call me back if either is bad. Dialysis does not remove diphenhydramine, if that "
              "is what you were going to ask.")}],
}
