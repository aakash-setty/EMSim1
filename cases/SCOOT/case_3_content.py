"""SCOOT part 3: exam findings, general status, the figure, imaging, ECG, consultants.

EVERY FINDING AND VALUE IN THIS FILE IS MODEL OUTPUT. No physician supplied a number.

The labs are left to the catalog defaults, which are normal, and that is intended
(SCOOT-SEED.md section 2.7). The CT C-spine is the catalog's normal read.

Phase rules come before flag rules. Inside a phase, the intubated variant comes first,
because after a tube the neuro exam cannot be assessed (goal G3). No result quotes a vital
sign that an effect could move: this case has no vital effects, so the ECG reports quote
the phase rate, and the tracing captions quote it.
"""

PRES = "phase is presentation"
DECL = "phase is decline"
HERN = "phase is herniation"
TEMP = "phase is temporized"
BRAIN = "phase is brainstem_compression"
TUBED = "flag intubated set"
CT_R = "(study ct_head resulted OR study ct_cta_head_and_neck resulted)"
CT_O = "(study ct_head ordered OR study ct_cta_head_and_neck ordered)"

VERIFY = "Model output, not from a physician or a radiology report. [UNVERIFIED]"


def ex(findings, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": findings}


def gs(findings, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": findings}


def report(text, abnormal=True):
    return {"kind": "report", "abnormal": abnormal, "report": text, "verify": VERIFY}


def always(v):
    return [{"when": None, "value": v}]


def tubed_first(rules):
    """rules: list of (phase_condition, tubed_value, untubed_value)."""
    out = []
    for cond, tubed, plain in rules:
        if tubed is not None:
            out.append({"when": cond + " AND " + TUBED, "value": tubed})
        out.append({"when": cond, "value": plain})
    return out


PUPILS_EQUAL = "Pupils 3 mm, equal and reactive."
PUPILS_BLOWN = "Right pupil 6 mm and fixed. Left 3 mm and reactive."
PUPILS_BACK = "Right pupil 4 mm and sluggish. Left 3 mm and reactive."
PUPILS_BOTH = "Both pupils 6 mm and fixed."
# Owner, 29 October 2026: blood behind the right eardrum, described and not named.
EARS = " Right eardrum intact, dark blue-purple behind it. Left eardrum normal."

EXAM = {
 "authoring_note": (
   "Section 9.2. Consciousness and GCS on exam_neuro, by the catalog map. The pupils are "
   "on exam_heent, where the catalog default puts them, and are repeated on exam_neuro so "
   "that a learner who looks in either place finds them. The neck is on exam_neck, the "
   "palms on exam_skin. Nothing on the figure draws the pupils (field reference)."),

 "exam_airway": [
   {"when": TUBED, "value": ex("Endotracheal tube in place.", abnormal=False)},
   {"when": HERN + " OR " + BRAIN, "value": ex("Snoring. Jaw thrust opens the airway. Weak gag.")},
   {"when": TEMP, "value": ex("Snoring less. Weak gag.")},
   {"when": DECL, "value": ex("Patent. Speaking slowly with slurred words. Swallowing his secretions. Vomitus on the gown.")},
   {"when": None, "value": ex("Patent. Talking in full sentences.", abnormal=False)}],

 "exam_breath": [
   {"when": TUBED + " AND (" + HERN + " OR " + BRAIN + ")", "value": ex("On the ventilator. Breath sounds equal.")},
   {"when": TUBED, "value": ex("On the ventilator. Breath sounds equal.", abnormal=False)},
   {"when": HERN + " OR " + BRAIN, "value": ex("Slow, irregular breathing. Chest rises equally.")},
   {"when": None, "value": ex("Breathing comfortably. Chest rises equally.", abnormal=False)}],

 "exam_circ": [
   {"when": HERN + " OR " + BRAIN, "value": ex("Pulse slow and bounding. Capillary refill under 2 seconds.")},
   {"when": None, "value": ex("Pulse strong and regular. Capillary refill under 2 seconds.", abnormal=False)}],

 "exam_heent": tubed_first([
   (HERN, None, ex("Boggy right temporal scalp hematoma. " + PUPILS_BLOWN + EARS)),
   (TEMP, None, ex("Boggy right temporal scalp hematoma. " + PUPILS_BACK + EARS)),
   (BRAIN, None, ex("Boggy right temporal scalp hematoma. " + PUPILS_BOTH + EARS)),
   ("phase is presentation OR phase is decline OR phase is case_complete", None,
    ex("Boggy right temporal scalp hematoma, no laceration. " + PUPILS_EQUAL + EARS +
       " No fluid from the nose or ears. No bruising behind the ears or around the eyes.")),
 ]) + [{"when": None, "value": ex("Boggy right temporal scalp hematoma. " + PUPILS_EQUAL + EARS)}],

 "exam_neck": [
   {"when": PRES, "value": ex("No midline cervical tenderness. Turns his head without pain.", abnormal=False)},
   {"when": DECL, "value": ex("Says no to midline tenderness, but his answers change from one question to the next.")},
   {"when": None, "value": ex("Cannot report midline tenderness. No step or deformity felt.")}],

 "exam_neuro": tubed_first([
   (HERN, ex("Sedated and paralyzed. GCS cannot be assessed. " + PUPILS_BLOWN),
    ex("GCS 7 (E1 V2 M4). Groans to pain. Withdraws to pain, less on the left. " + PUPILS_BLOWN)),
   (TEMP, ex("Sedated and paralyzed. GCS cannot be assessed. " + PUPILS_BACK),
    ex("GCS 8 (E2 V2 M4). Eyes flicker to pain. Withdraws to pain, less on the left. " + PUPILS_BACK)),
   (BRAIN, ex("No response. " + PUPILS_BOTH), ex("GCS 3. No response. " + PUPILS_BOTH)),
   (DECL, ex("Sedated and paralyzed. GCS cannot be assessed. " + PUPILS_EQUAL),
    ex("GCS 12 (E3 V4 M5). Opens eyes to voice. Confused. Localizes pain. " + PUPILS_EQUAL +
       " Moves all four limbs equally.")),
   (PRES, ex("Sedated and paralyzed. GCS cannot be assessed. " + PUPILS_EQUAL),
    ex("GCS 15 (E4 V5 M6). Oriented, asks again what happened. " + PUPILS_EQUAL +
       " Power 5 of 5 in all four limbs.", abnormal=True)),
 ]) + [{"when": None, "value": ex("GCS 15 (E4 V5 M6). " + PUPILS_EQUAL, abnormal=False)}],

 "exam_skin": always(ex("Road rash on both palms. No other wounds.")),

 "exam_msk": always(ex("Grazed palms. No deformity or tenderness of the limbs or pelvis.", abnormal=False)),

 "exam_psych": [
   {"when": PRES, "value": ex("Cooperative. Asks the same question about the crash several times.")},
   {"when": None, "value": ex("Cannot be assessed.")}],
}

GENERAL_STATUS = {
 "authoring_note": "Section 9.3. Consistent with exam_neuro, the appearance values and the figure.",
 "rules": [
   {"when": BRAIN, "value": gs("Unresponsive. Slow, gasping breaths. GCS 3.")},
   {"when": HERN + " AND " + TUBED, "value": gs("Intubated and sedated. GCS cannot be assessed.")},
   {"when": HERN, "value": gs("Eyes closed. Groans to pain only. Snoring breaths. GCS 7.")},
   {"when": TEMP + " AND " + TUBED, "value": gs("Intubated and sedated. GCS cannot be assessed.")},
   {"when": TEMP, "value": gs("Eyes flicker to pain. Breathing more regularly. GCS 8.")},
   {"when": DECL + " AND " + TUBED, "value": gs("Intubated and sedated. GCS cannot be assessed.")},
   {"when": DECL, "value": gs("Drowsy, eyes close when left alone. Vomit on his gown. Answers slowly and muddles his words. GCS 12.")},
   {"when": TUBED, "value": gs("Intubated and sedated. GCS cannot be assessed.")},
   {"when": None, "value": gs("Sitting up, holding an ice pack to the right side of his head. Talking, asks again what happened. GCS 15.")},
 ],
}

PUPILS = {
 "authoring_note": ("MODEL-AUTHORED, NOT PHYSICIAN-AUTHORED. Drawn sizes and responses for the eye view "
   "(engine/pupils.js), taken from PUPILS_EQUAL, PUPILS_BLOWN, PUPILS_BACK and PUPILS_BOTH, the "
   "sentences exam_heent and exam_neuro print, so the drawing and the text agree phase by phase. "
   "In herniation the right pupil is 6 mm and fixed and the left 3 mm and brisk: light in either "
   "eye reaches both, so the left constricts to light in the right while the right does not move. "
   "In the temporized phase the right is 4 mm and sluggish, drawn with affected_mm and "
   "affected_reaction. 'Reactive' in the text is drawn brisk."),
 "verify": ("Four choices to check. (1) The blown pupil is drawn 6 mm, as the exam text says, where "
   "the renderer's default for a blown pupil is 8 mm. (2) After osmotherapy the right pupil is drawn "
   "4 mm and sluggish, larger than the left and still reacting, within 15 s of the dose. Whether a "
   "pupil comes back that far that fast is a teaching choice (see the SEED, section 4). (3) In "
   "brainstem compression both are 6 mm and fixed, a midposition-to-large fixed pupil, not 8 mm. "
   "(4) Sedation and an opioid after the tube are not drawn: the pupils stay as the phase says, "
   "as the exam text does. An opioid would shrink a pupil that can still move."),
 "rules": [
  {"when": BRAIN, "value": {"state": "dilated_fixed", "size_mm": 6}},
  {"when": HERN, "value": {"state": "blown", "side": "right", "size_mm": 3, "reaction": "brisk",
                           "affected_mm": 6}},
  {"when": TEMP, "value": {"state": "blown", "side": "right", "size_mm": 3, "reaction": "brisk",
                           "affected_mm": 4, "affected_reaction": "sluggish"}},
  {"when": None, "value": {"state": "normal", "size_mm": 3, "reaction": "brisk"}},
 ],
}

PATIENT_VISUAL = {
 "authoring_note": (
   "MODEL-AUTHORED. Beyond the phase's own distress and alertness, one rule: his eyes are "
   "closed in the decline (owner, 19 October 2026). At GCS 12 he opens them only to voice "
   "(E3), so at rest they are shut. The airway device follows the last airway button pressed."),
 "verify": "Check that the closed eyes in the decline and the obtunded face in herniation read as intended.",
 "rules": [{"when": DECL, "value": {"eyes": "closed"}},
           {"when": None, "value": {}}],
}

LABS = {
 "authoring_note": (
   "Section 9.1. No lab is authored. The catalog defaults are normal and that is the truth "
   "of this patient: a normal CBC, coagulation panel, type and screen, chemistry, glucose, "
   "ethanol level and urine toxicology. Each is named in SCOOT-SEED.md section 2.7."),
}

# ============================================================== IMAGING AND ECG
CT_READ = (
  "Biconvex hyperdense extra-axial collection over the right temporoparietal convexity, "
  "limited by the sutures, about 19 mm thick and about 50 mL. Low-density pockets within it. "
  "Linear fracture of the right temporal squama beneath it, seen on the bone window. Right "
  "temporal scalp hematoma. Leftward midline shift of about 6 mm with effacement of the "
  "right lateral ventricle. No subdural, subarachnoid or parenchymal blood.")
CTA_TAIL = " No arterial injury in the head or neck. No contrast extravasation."
CT_VERIFY = (
  "The images are the EDH case (Case 3) of the owner's Head CT Teaching Cases artifact, "
  "synthetic, built on the Colin27 MRI phantom (media/README.md). The read is that "
  "artifact's own findings list, checked by a model against the images: 19 mm and about "
  "6 mm of shift are the artifact's measurements, and the volume is about 47 mL by its "
  "count and about 50 mL by the model's sum of its lesion map. Not reviewed by a "
  "radiologist or a physician. [UNVERIFIED]")

LATE_PHASES = HERN + " OR " + TEMP + " OR " + BRAIN


def ecg_image(stem, rate, qtc, read):
    """Authoring 23, default of 13 October 2026: a generated tracing, captioned with the
    machine measurements, its read kept as the comment the debrief prints. Drawn by
    Claude outputs/scoot-ecg/generate-scoot.mjs (media/README.md). No vital effect moves
    the rate in this case, so the caption quotes it, as TSS does."""
    return {"kind": "image", "abnormal": "bradycardia" in read, "image": "scoot-ecg-" + stem,
            "caption": "Twelve-lead ECG. Ventricular rate %d, PR 150 ms, QRS 88 ms, QTc %d ms" % (rate, qtc),
            "comment": read, "verify": VERIFY}


IMAGING = {
 "authoring_note": (
   "Section 9.4 and 23. The head CT is the image stack itself, one series for every phase "
   "(SCOOT-SEED.md 2.7). The CT/CTA reports the same head findings in words, because its "
   "source images would show them. The MRI shows the clot too, so that an "
   "MRI ordered by mistake does not answer with the catalog's normal read. The C-spine CT "
   "is the catalog default. The chest film is the owner's normal male film, with a tube "
   "drawn in once he is intubated, and the FAST is the catalog's negative read. The ECG is a generated tracing per phase (media/README.md), "
   "its read the debrief comment. The brainstem phase has none: a terminal phase cannot "
   "order one."),

 # 19 October 2026 (author instruction): the head CT is the scan itself, a stack the resident
 # scrolls in the CT viewer, with its still as the thumbnail. One series for every phase:
 # there is one volume, so a scan sent after the decline or in herniation shows the same
 # images (SCOOT-SEED.md known gap 6). The read is the debrief comment, never shown in play.
 "ct_head": {"changes_with_state": False, "rules": always({
   "kind": "image", "abnormal": True, "image": "scoot-ct-head", "series": "scoot-ct-head",
   "caption": "CT head without contrast. 31 axial images, 5 mm",
   "comment": CT_READ, "verify": CT_VERIFY})},

 # A CT angiogram's source images would show the same collection. It stays a report, since
 # the series is a non-contrast study and showing it as an angiogram would be false.
 "ct_cta_head_and_neck": {"changes_with_state": False, "rules": always(report(CT_READ + CTA_TAIL))},

 "mri_mra_head_and_neck": {"changes_with_state": False, "rules": always(report(
   "Right temporal biconvex extra-axial collection with signal of acute blood, compressing "
   "the right temporal lobe, with leftward midline shift. Right temporal squamous fracture. "
   "Intracranial and neck arteries normal."))},

 # 29 October 2026, owner instruction: "pull a normal cxr from the chest xray folder". The
 # folder's Normal_Male.png (media/README.md), captioned only, with the read the debrief
 # prints. Once he is intubated, the same film with a tube drawn in, so the picture agrees
 # with the state (a model choice, SCOOT-SEED.md 2.16).
 "xr_chest": {"changes_with_state": True, "rules": [
   {"when": TUBED, "value": {
     "kind": "image", "abnormal": False, "image": "scoot-cxr-normal-ett", "caption": "Chest radiograph",
     "comment": ("Portable AP chest. Endotracheal tube tip about 3 to 4 cm above the carina. "
                 "Lungs clear. No consolidation, effusion or pneumothorax. Cardiac silhouette "
                 "normal in size. No acute bony abnormality."),
     "verify": ("The tube is drawn on the film (media/README.md). The carina was estimated by "
                "eye and the film has no recorded pixel spacing, so the distance is an "
                "estimate. " + VERIFY)}},
   {"when": None, "value": {
     "kind": "image", "abnormal": False, "image": "scoot-cxr-normal", "caption": "Chest radiograph",
     "comment": ("Lungs clear. No consolidation, effusion or pneumothorax. Cardiac silhouette "
                 "normal in size. No acute bony abnormality."),
     "verify": VERIFY}}]},

 # 29 October 2026, owner instruction: the FAST is a critical action. The catalog's own
 # negative read, authored here so the validator sees a result for a critical study.
 "ultrasound_fast": {"changes_with_state": False, "rules": always(report(
   "No free fluid in Morison's pouch, splenorenal recess, pelvis or pericardium. Negative "
   "FAST.", abnormal=False))},

 "ecg_12_lead": {"changes_with_state": True, "rules": [
   {"when": HERN, "value": ecg_image("herniation", 56, 430,
     "Sinus bradycardia at 56. Normal axis. PR 150 ms, QRS 88 ms, QTc 430 ms. No ST change.")},
   {"when": TEMP, "value": ecg_image("temporized", 70, 420,
     "Sinus rhythm at 70. Normal axis. PR 150 ms, QRS 88 ms, QTc 420 ms. No ST change.")},
   {"when": DECL, "value": ecg_image("decline", 96, 410,
     "Sinus rhythm at 96. Normal axis. PR 150 ms, QRS 88 ms, QTc 410 ms. No ST change.")},
   {"when": None, "value": ecg_image("arrival", 88, 410,
     "Sinus rhythm at 88. Normal axis. PR 150 ms, QRS 88 ms, QTc 410 ms. No ST change.")}]},
}

# ============================================================== CONSULTANTS
# Most specific first. A line that quotes the scan tests that a head CT has resulted, and
# quotes only what is true of every variant a learner can have on the chart in that phase:
# in presentation and decline the only scan that can have resulted is the arrival scan. The
# late tiers quote no number. 40 words or fewer each.
CONSULTANTS = {
 "authoring_note": (
   "Section 9.5. The neurosurgery consult cannot be made until a head CT (or the CT/CTA) has "
   "resulted, by a prerequisite, so every neurosurgeon tier is reached with a scan on the "
   "chart and no pending tier is needed. No tier quotes a number. The default is unreachable and exists because the list needs one. "
   "The neurosurgeon never names the lesion: naming it is the learner's job at the "
   "handoff."),

 "consult_neurosurgeon": [
   {"when": TEMP,
    "value": ("Neurosurgeon: Good, the osmotherapy has bought us some time, not much. Secure "
              "his airway, keep his pressure up, and bring him straight to the OR.")},
   {"when": LATE_PHASES,
    "value": ("Neurosurgeon: He's herniating. Give osmotherapy now if he hasn't had it, secure "
              "his airway, and don't let his pressure drop. We're taking him straight to the "
              "OR.")},
   {"when": DECL,
    "value": ("Neurosurgeon: A big collection with shift, and now his GCS is falling. I'm "
              "booking the OR and coming down now. Keep his oxygen and his pressure normal. "
              "Call me if a pupil changes.")},
   {"when": PRES,
    "value": ("Neurosurgeon: A collection that size with shift needs to come out, even though "
              "he's talking. I'm booking the OR. Call me straight away if he gets drowsy or a "
              "pupil changes.")},
   {"when": None,
    "value": "Neurosurgeon: Send me his head CT and call me back with it."}],

 "consult_critical_care": [
   {"when": LATE_PHASES,
    "value": ("Intensivist: He needs the OR before he needs us. Osmotherapy and an airway now, "
              "and get neurosurgery. We'll take him after surgery.")},
   {"when": None,
    "value": ("Intensivist: Call neurosurgery first. Whatever they decide, we can take him "
              "afterwards.")}],

 "consult_general_surgery": [
   {"when": None,
    "value": ("Trauma surgeon: Your survey sounds like an isolated head injury. His head is "
              "the problem, so get neurosurgery on the phone. Page me if anything else "
              "turns up.")}],

 "consult_neurology": [
   {"when": None,
    "value": ("Neurologist: A head injury with a possible bleed is neurosurgery, not us. Call "
              "them now.")}],
}
