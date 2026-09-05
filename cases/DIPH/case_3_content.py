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
   "Section 11.2. Thirteen of the fourteen catalog maneuvers are authored; the back "
   "examination inherits the catalog default. The routing is the catalog's and not this "
   "author's preference: the dry hot skin and the absent sweating go to exam_skin, the "
   "agitation and thought content to exam_psych rather than exam_neuro, which owns the level "
   "of consciousness, and the absent bowel sounds and the palpable bladder to exam_abd with "
   "the bladder repeated on exam_gu because the author lists it in both places.\n\n"
   "The findings themselves are the author's physical examination table, verbatim in "
   "substance. Their expansion across phases is not hers."),

 "exam_heent": [
   {"when": SEIZ, "value": ex(
     "Eyes deviated and rolling. Pupils are 7 millimetres and equal, sluggish. Mucous membranes "
     "are dry. There is saliva at the corner of the mouth and no tongue injury you can see.")},
   {"when": RESOLVING, "value": ex(
     "Pupils remain 7 millimetres, equal and now briskly reactive. Mucous membranes are still "
     "dry. The roving eye movements have settled.")},
   {"when": None, "value": ex(
     "Pupils are equal at about 7 millimetres, large, and reactive. There are roving conjugate "
     "eye movements that will not fix on you, which the author describes as opsoclonus. Mucous "
     "membranes are completely dry and the tongue is like paper. No head injury, no facial "
     "asymmetry, no oral burns or corrosion.")}],

 "exam_neck": always(ex(
   "Supple. No meningism and no pain on passive flexion. Trachea central. No lymphadenopathy, "
   "no jugular venous distension, no thyroid mass or bruit.", abnormal=False)),

 "exam_card": [
   {"when": WIDE, "value": ex(
     "Regular wide-complex tachycardia at about 180. Heart sounds are present and soft. "
     "Peripheral pulses are palpable but thready. No murmur. No peripheral oedema.")},
   {"when": "phase is stabilized", "value": ex(
     "Regular sinus rhythm at about 100. Normal first and second heart sounds, no murmur. "
     "Pulses full. No peripheral oedema.", abnormal=False)},
   {"when": "phase is stabilizing", "value": ex(
     "Regular sinus tachycardia at about 115, slower than it was. Normal heart sounds, no "
     "murmur. No peripheral oedema.")},
   {"when": None, "value": ex(
     "Regular sinus tachycardia at about 135. Normal first and second heart sounds, no murmur, "
     "no rub, no gallop. Apex beat not displaced. No peripheral oedema.")}],

 "exam_pulm": always(ex(
   "Clear breath sounds bilaterally with equal air entry. No crackles, no wheeze, no bronchial "
   "breathing, no dullness.", abnormal=False)),

 "exam_abd": [
   {"when": RESOLVING, "value": ex(
     "Soft and non-tender. Bowel sounds are sparse but present. The bladder is no longer "
     "palpable if it has been drained.")},
   {"when": None, "value": ex(
     "Soft, non-tender, not distended. Bowel sounds are absent over four quadrants after a full "
     "minute of listening. There is a firm, non-tender mass arising out of the pelvis to just "
     "below the umbilicus, which is a full bladder. No guarding, no organomegaly.")}],

 "exam_gu": [
   {"when": "flag bladder_drained set", "value": ex(
     "Catheterised, with about 700 mL drained on insertion and dark amber urine in the bag. The "
     "bladder is no longer palpable. No external abnormality.")},
   {"when": None, "value": ex(
     "The bladder is palpable well above the pubic symphysis and is dull to percussion. She has "
     "not passed urine since her mother found her. No external abnormality.")}],

 "exam_skin": [
   {"when": RESOLVING, "value": ex(
     "Cooler than she was and the flush has faded, though she is still warm and the skin is "
     "still dry: there is no sweat anywhere, which is the antimuscarinic effect and outlasts "
     "the temperature. No rash. No needle marks, no patches, no wounds.")},
   {"when": None, "value": ex(
     "Hot to the touch everywhere, and completely dry. There is no sweat in the axillae, on the "
     "forehead or on the palms. Diffusely flushed, most obviously over the face and upper chest. "
     "No rash of any kind, blanching or non-blanching. No needle marks, no patches, no wounds.")}],

 "exam_neuro": [
   {"when": SEIZ, "value": ex(
     "Generalised tonic-clonic activity, not rousable, not protecting her airway. Eyes deviated. "
     "No focus to the movements that you can see.")},
   {"when": POST, "value": ex(
     "Drowsy and rousable to voice with effort. Moves all four limbs to command inconsistently. "
     "Reflexes are present and symmetrical, no clonus, plantars downgoing. No lateralising sign. "
     "Not orientated to place or time.")},
   {"when": RESOLVING, "value": ex(
     "Drowsy but rousable and settling. Orientated to person, not consistently to place. No "
     "focal deficit, no clonus, no meningism.")},
   {"when": None, "value": ex(
     "Awake, agitated, disorientated in place, time and situation. Will not sustain attention "
     "and does not follow a two-step command. No focal motor or sensory deficit that can be "
     "demonstrated. Reflexes are symmetrical. No clonus and no hyperreflexia. No meningism. "
     "Plantars downgoing. Gait not tested.")}],

 "exam_psych": [
   {"when": SEIZ + " OR " + POST, "value": ex(
     "Not assessable. She is not able to converse.")},
   {"when": RESOLVING, "value": ex(
     "Drowsy and settled. Not able to give a reliable account of herself, and this is not the "
     "moment to take a psychiatric history.")},
   {"when": None, "value": ex(
     "Agitated and restless. Plucking repeatedly at the sheet and at the monitoring leads. "
     "Speech is present, fluent and largely nonsensical. She looks past you and does not "
     "consistently register that you are there. She reaches for things that are not in the room. "
     "No sustained eye contact. Pushes hands away when touched. No expressed thought content "
     "that can be assessed.")}],

 "exam_airway": [
   {"when": "flag airway_protected set", "value": ex(
     "Endotracheal tube in place, cuff up, waveform capnography with a normal square trace.")},
   {"when": SEIZ, "value": ex(
     "Not protecting her airway. Secretions at the mouth, teeth clenched, and she is not "
     "ventilating adequately between the movements.")},
   {"when": POST, "value": ex(
     "Patent with a jaw thrust. Gag is reduced. She is snoring intermittently and will need "
     "watching or securing.")},
   {"when": None, "value": ex(
     "Patent and self-maintained. She is speaking, though not sensibly. No stridor, no swelling, "
     "no drooling. Mucous membranes are dry.", abnormal=False)}],

 "exam_breath": [
   {"when": SEIZ, "value": ex(
     "Not ventilating adequately. Chest movement is irregular with the convulsion and there is "
     "no useful tidal volume.")},
   {"when": RESOLVING, "value": ex(
     "Breathing quietly at a normal rate with no increased work. Chest expansion equal.",
     abnormal=False)},
   {"when": POST, "value": ex(
     "Breathing spontaneously at a normal rate. Shallow, and she needs watching, but there is "
     "no increased work of breathing.")},
   {"when": None, "value": ex(
     "Tachypnoeic at about 25 with no increased work of breathing. No accessory muscle use, no "
     "tracheal tug, no intercostal recession. Chest expansion is equal. This is the respiratory "
     "compensation for a metabolic acidosis rather than a lung problem.")}],

 "exam_circ": [
   {"when": WIDE, "value": ex(
     "Cool peripheries for the first time. Capillary refill is three seconds. Radial pulse is "
     "weak and very fast.")},
   {"when": RESOLVING, "value": ex(
     "Warm and well perfused. Capillary refill under two seconds. Pulse regular and slower "
     "than it was. The flush has faded.", abnormal=False)},
   {"when": None, "value": ex(
     "Warm and flushed to the fingertips. Capillary refill under two seconds. Pulse is regular, "
     "fast and full. Skin is hot and dry.")}],

 "exam_msk": always(ex(
   "No deformity, no bruising and no wound. Full passive range of movement at every joint. No "
   "oedema. No compartment is tense. Nothing to suggest she fell or was injured.", abnormal=False)),
}

# ============================================================== GENERAL STATUS
GENERAL_STATUS = {
 "authoring_note": (
   "Section 11.3. Rendered above the maneuver list and not clickable, so it is the one "
   "examination finding every learner sees. Kept consistent with the neurological and "
   "psychiatric examinations and with the appearance values of each phase."),
 "rules": [
   {"when": SEIZ, "value": gs(
     "Generalised seizure in progress. Not responsive, not protecting her airway, cyanosing at "
     "the lips.")},
   {"when": WIDE, "value": gs(
     "Obtunded and grey. Rousable only to pain. A fast wide-complex rhythm on the monitor with a "
     "thready pulse. GCS 9.")},
   {"when": POST, "value": gs(
     "Post-ictal. Drowsy, rousable to voice, still hot to touch and still flushed. Not orientated. "
     "GCS 12.")},
   {"when": "phase is stabilizing", "value": gs(
     "Settled and drowsy. Colour better and the flush is fading. Still warm. Complexes on the "
     "monitor look narrower than they did. GCS 13.")},
   {"when": "phase is stabilized", "value": gs(
     "Drowsy but rousable and comfortable, on the monitor, cooling. Pupils are still large. GCS 14.")},
   {"when": "phase is pulseless_vt", "value": gs(
     "In cardiac arrest. No pulse, no respiratory effort, wide complexes on the monitor.")},
   {"when": None, "value": gs(
     "Awake, agitated and disorientated, flushed, hot and dry, plucking at the leads. Speaking "
     "but not making sense. Two people are keeping her on the trolley. GCS 13.")},
 ],
}

# ============================================================== LABORATORY
# Every value is the author's. Every reference interval is model output.
LABS = {
 "authoring_note": (
   "Section 11.4. Structured payloads with abnormal flags set by the author of the case file "
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
        comp("Sodium", "146", "mEq/L", "135-145", True),
        comp("Potassium", "3.1", "mEq/L", "3.5-5.0", True),
        comp("Chloride", "104", "mEq/L", "98-107", False),
        comp("Bicarbonate", "27", "mEq/L", "22-29", False),
        comp("BUN", "12", "mg/dL", "7-20", False),
        comp("Creatinine", "0.8", "mg/dL", "0.6-1.2", False),
        comp("Glucose", "126", "mg/dL", "70-140 (random)", False)],
        comment=("Drawn after sodium bicarbonate. The acidosis has corrected, and the sodium "
                 "and potassium have moved in the directions the treatment moves them: a rising "
                 "sodium from the sodium load and a falling potassium from the alkalinisation "
                 "driving potassium into cells. Both are complications of the treatment rather "
                 "than of the poisoning, and the potassium is the one to replace, because "
                 "hypokalaemia lengthens a QT that is already long."),
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
        comment=("A metabolic acidosis with an anion gap of 13, which agrees with the blood gas "
                 "and with the lactate. The renal function is normal, which is the baseline the "
                 "rhabdomyolysis will be followed against."),
        verify=("The source gives CO2 as 34 in this panel and HCO3 as 13 on the gas. The two "
                "cannot both be true and 13 is the one consistent with the pH and the anion "
                "gap. Corrected on drafting judgement and needs the author's signature."))}]},

 "complete_blood_count_cbc": {
   "changes_with_state": False,
   "rules": always(panel([
     comp("White cell count", "16.0", "K/uL", "4.0-11.0", True),
     comp("Haemoglobin", "16.9", "g/dL", "12.0-16.0 (female)", True),
     comp("Haematocrit", "47.2", "%", "36-46 (female)", True),
     comp("Platelets", "250", "K/uL", "150-400", False)],
     comment=("A leucocytosis without a source, and a haemoglobin and haematocrit at the top of "
              "or above the female interval."),
     verify=("All four values are the author's. The source writes the white count as '16 L/ul', "
             "taken here as 16 K/microlitre. The haemoglobin of 16.9 and haematocrit of 47.2 "
             "are above the usual female interval and are flagged abnormal on that basis; "
             "haemoconcentration is a plausible reading in a hyperthermic patient who has not "
             "drunk for hours, but it is a reading and not the author's statement.")))},

 "arterial_blood_gas": {
   "changes_with_state": True,
   "rules": [
     {"when": SEIZ, "value": panel([
        comp("pH", "7.15", "", "7.35-7.45", True),
        comp("pCO2", "52", "mmHg", "35-45", True),
        comp("pO2", "61", "mmHg", "80-100", True),
        comp("Bicarbonate", "12", "mEq/L", "22-26", True),
        comp("Lactate", "6.4", "mmol/L", "0.5-2.0", True)],
        comment=("A mixed metabolic and respiratory acidosis during the convulsion. This is the "
                 "worst the pH gets and it is not only a respiratory problem: acidaemia "
                 "increases the un-ionised fraction of the drug available to the cardiac sodium "
                 "channel, so the gas is a cardiac measurement here as well as a respiratory "
                 "one."),
        verify="Model output. The author supplies one gas and it is the arrival one below.")},
     {"when": "flag bicarb_given set", "value": panel([
        comp("pH", "7.51", "", "7.35-7.45", True),
        comp("pCO2", "36", "mmHg", "35-45", False),
        comp("pO2", "142", "mmHg", "80-100", True),
        comp("Bicarbonate", "28", "mEq/L", "22-26", True),
        comp("Lactate", "2.2", "mmol/L", "0.5-2.0", True)],
        comment=("Drawn after bicarbonate. A pH of 7.51 is inside the range usually aimed at "
                 "when alkalinising for sodium-channel blockade, commonly taken to about 7.50 "
                 "to 7.55. Further alkalinisation past that buys little and costs potassium and "
                 "ionised calcium. The pO2 reflects supplemental oxygen and the reference "
                 "interval quoted assumes room air, which is a known limitation of the catalog "
                 "default."),
        verify="Model output.")},
     {"when": None, "value": panel([
        comp("pH", "7.28", "", "7.35-7.45", True),
        comp("pCO2", "34", "mmHg", "35-45", True),
        comp("pO2", "94", "mmHg", "80-100", False),
        comp("Bicarbonate", "13", "mEq/L", "22-26", True),
        comp("Lactate", "3.1", "mmol/L", "0.5-2.0", True)],
        comment=("A partly compensated metabolic acidosis on room air. The author's values."),
        verify=("The five values are the author's. The reference intervals are not, and the "
                "catalog's own note applies: an ABG default assumes room air and nothing in "
                "the schema knows when supplemental oxygen is running."))}]},

 "venous_blood_gas": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag bicarb_given set", "value": panel([
        comp("pH", "7.47", "", "7.31-7.41", True),
        comp("pCO2", "42", "mmHg", "41-51", False),
        comp("Bicarbonate", "28", "mEq/L", "22-26", True)],
        comment="Adequate for following the pH and the bicarbonate.", verify="Model output.")},
     {"when": None, "value": panel([
        comp("pH", "7.25", "", "7.31-7.41", True),
        comp("pCO2", "38", "mmHg", "41-51", True),
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
     comp("Colour", "Dark amber", "", "Yellow", True),
     comp("Blood", "3+", "", "Negative", True),
     comp("Red cells", "0-2", "/hpf", "0-2", False),
     comp("Protein", "Trace", "", "Negative", True),
     comp("Leucocyte esterase", "Negative", "", "Negative", False),
     comp("Nitrite", "Negative", "", "Negative", False),
     comp("Ketones", "1+", "", "Negative", True)],
     comment=("Dipstick positive for blood with no red cells on microscopy."),
     verify=("Model output. The author does not supply a urinalysis; she lists it among the "
             "studies she expects to be ordered. The blood-positive, red-cell-negative pattern "
             "is authored to be consistent with her creatine kinase of 540 and is a drafting "
             "inference rather than her statement.")))},

 "magnesium_level": {
   "changes_with_state": False,
   "rules": always(val("Magnesium", "1.6", "mg/dL", "1.7-2.4", True,
     comment="Low. Replace it.",
     verify=("Model output. The author does not supply a magnesium. It is authored low because "
             "her case turns partly on QT prolongation and because magnesium is the treatment "
             "for torsades, so a resident who checks it should find something to act on. This "
             "is a value invented to make a teaching point and the author should decide whether "
             "she wants it.")))},

 "calcium_ionized": {
   "changes_with_state": True,
   "rules": [
     {"when": "flag bicarb_given set", "value": val("Ionised calcium", "1.09", "mmol/L",
        "1.12-1.32", True,
        comment=("Fallen after alkalinisation, which is expected: a rising pH increases the "
                 "fraction of calcium bound to albumin and lowers the ionised fraction."),
        verify="Model output.")},
     {"when": None, "value": val("Ionised calcium", "1.18", "mmol/L", "1.12-1.32", False,
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
     comment=("Mildly raised without an ischaemic pattern on the tracing. Demand and a poisoned "
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
   "Section 11.4, kind report: findings and not conclusions. The words sodium-channel blockade "
   "do not appear in any tracing below; they appear in the debrief note on the ECG action, "
   "where the learner meets them after committing to an interpretation rather than before.\n\n"
   "The source document carries four images: a near-normal chest radiograph, a normal "
   "non-contrast head CT, and two twelve-lead tracings showing wide-complex tachycardia. None "
   "of them is used. The engine has no way to display an image in a result, and the provenance "
   "of the four is not established in the document. Every report below is text."),

 "ecg_12_lead": {
   "changes_with_state": True,
   "result_shape": "structured",
   "rules": [
     {"when": "phase is pulseless_vt", "value": report(
       "Wide-complex tachycardia at approximately 190 per minute. No organised mechanical "
       "activity. QRS duration approximately 200 ms.")},
     {"when": WIDE, "value": report(
       "Monomorphic wide-complex tachycardia at approximately 180 per minute. QRS duration "
       "approximately 180 ms. No discernible P waves. Terminal R wave in aVR of 7 mm with an "
       "R to S ratio in aVR greater than 0.7. Rightward terminal QRS axis. No ST elevation.")},
     {"when": SEIZ, "value": report(
       "Sinus tachycardia at approximately 150 per minute. QRS duration 148 ms, wider than on "
       "the previous tracing. Terminal R wave in aVR of 6 mm. Rightward terminal QRS axis. QTc "
       "512 ms. Frequent ventricular ectopics. Baseline heavily obscured by movement artefact.")},
     {"when": "phase is stabilized", "value": report(
       "Sinus tachycardia at approximately 100 per minute. QRS duration 96 ms. Terminal R wave "
       "in aVR now 1 mm with an R to S ratio below 0.7. Normal QRS axis. QTc 445 ms. No ST "
       "elevation.")},
     {"when": "phase is stabilizing", "value": report(
       "Sinus tachycardia at approximately 115 per minute. QRS duration 104 ms, narrower than "
       "on the previous tracing. Terminal R wave in aVR now 2 mm. QTc 460 ms. No ST elevation.")},
     {"when": None, "value": report(
       "Sinus tachycardia at approximately 135 per minute. QRS duration 132 ms. Terminal R wave "
       "in lead aVR of 5 mm, with an R to S ratio in aVR greater than 0.7. Rightward deviation "
       "of the terminal QRS axis. QTc 495 ms. No ST elevation and no ST depression.",
       comment=None)}],
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
     {"when": None, "value": report(
       "Lungs clear. No consolidation, no effusion, no pneumothorax. Cardiomediastinal "
       "silhouette normal. No free subdiaphragmatic gas.", abnormal=False)}]},

 "ct_head": {
   "changes_with_state": False,
   "rules": always(report(
     "No intracranial haemorrhage. No mass, no midline shift, no established infarct. "
     "Ventricles and sulci normal for age. No skull fracture.", abnormal=False))},

 "ultrasound_cardiac": {
   "changes_with_state": True,
   "rules": [
     {"when": WIDE, "value": report(
       "Fast, poorly organised ventricular contraction with reduced systolic function. No "
       "pericardial effusion. Inferior vena cava small and collapsing.")},
     {"when": None, "value": report(
       "Vigorous left ventricular systolic function at a fast rate. No pericardial effusion. No "
       "right ventricular dilatation. Inferior vena cava small and collapsing.")}],
   "verify": "Model output. The author does not author a bedside echocardiogram."},
}

# ============================================================== CONSULTANTS
CONSULTANTS = {
 "authoring_note": (
   "Section 11.5. Rules run from most specific to least specific and every one of them gates on "
   "the study state, so that no consultant discusses a tracing nobody has ordered and none "
   "discusses a result that has not come back. Each has a pending tier, because with a "
   "ten-second turnaround there is a real window in which the ECG is ordered and not resulted.\n\n"
   "Only toxicology is state-changing: it sets tox_consulted, which is one of the two flags the "
   "stabilised phase requires."),

 "consult_toxicology": [
   {"when": "study ecg_12_lead resulted AND flag bicarb_given set",
    "value": ("Toxicology fellow: good, you have treated the QRS and that is the right call. "
              "Keep going on the same principle. Repeat boluses of 1 to 2 mEq/kg until the QRS "
              "narrows, then put up an infusion, and take her pH to about 7.50 to 7.55 and no "
              "further. Watch the sodium, the potassium and the ionised calcium, because you "
              "will move all three. Serial tracings, and I want continuous monitoring wherever "
              "she goes.\n\nThree other things. Do not give her physostigmine, whatever the "
              "delirium looks like, while that QRS is anything other than normal. Do not use a "
              "class IA or IC antiarrhythmic if she has ventricular ectopy; if she needs "
              "anything beyond bicarbonate, call me and we will talk about lidocaine. And check "
              "her acetaminophen, because these are over-the-counter combination products and "
              "people do not always know what they took.\n\nIf the QRS will not narrow on "
              "adequate bicarbonate and an adequate pH, the options are more sodium as "
              "hypertonic saline, lidocaine, lipid emulsion, and in extremis extracorporeal "
              "support. The evidence for all of those is case reports and extrapolation, so "
              "involve me before you need them rather than after.")},
   {"when": "study ecg_12_lead resulted",
    "value": ("Toxicology fellow: read me the QRS again. A hundred and thirty-two milliseconds "
              "with a terminal R in aVR is sodium-channel blockade, and diphenhydramine does "
              "that at high dose. That is your indication to treat and you do not need to wait "
              "for a level or for the history to firm up. Sodium bicarbonate, 1 to 2 mEq/kg as "
              "a bolus, repeated, with a tracing after each one.\n\nDo not give physostigmine. "
              "I know the delirium is the textbook picture for it and I know somebody will "
              "suggest it. Not with that QRS.\n\nBenzodiazepines for the agitation, and please "
              "do not use haloperidol. Cool her actively and do not bother with paracetamol. "
              "Send a creatine kinase if you have not. Call me back with the repeat tracing.")},
   {"when": "study ecg_12_lead ordered",
    "value": ("Toxicology fellow: the tracing is not through yet, so I am not going to guess. "
              "The one thing I want from you before it comes is the QRS duration and whether "
              "there is a terminal R wave in aVR, because that decides everything else, "
              "including whether physostigmine is even a conversation. While you wait: "
              "benzodiazepines for the agitation, cool her actively, get a glucose if you have "
              "not, and send a creatine kinase, an acetaminophen and a salicylate.")},
   {"when": None,
    "value": ("Toxicology fellow: I need a twelve-lead before I can help you much. A delirious "
              "hyperthermic teenager with big pupils and dry skin is an antimuscarinic picture "
              "and diphenhydramine is at the top of that list in this country, but the thing "
              "that decides her management is the QRS duration and I do not have it. Get me an "
              "ECG and call me straight back. In the meantime, benzodiazepines rather than "
              "antipsychotics, cool her physically, and send a paracetamol and a salicylate "
              "level.")}],

 "consult_critical_care": [
   {"when": "study ecg_12_lead resulted AND flag bicarb_given set",
    "value": ("Intensivist: yes, we will take her. Keep the bicarbonate going, keep her on the "
              "monitor and send me the tracings. She stays on continuous cardiac monitoring "
              "with serial ECGs and serial gases, and nobody moves her to a psychiatric bed "
              "until that QRS has been normal for a good while. Have you got a creatine kinase "
              "and a urine output? If she has been that hot and that agitated she is going to "
              "declare a rhabdomyolysis overnight.")},
   {"when": "study ecg_12_lead resulted",
    "value": ("Intensivist: with a QRS of 132 she is coming to us, and she needs sodium "
              "bicarbonate before she comes rather than after. Start it, get a repeat tracing, "
              "and call me when you have both. Is she cooled? A temperature of 40 with a "
              "conduction abnormality is a bad combination and I would rather she came to me "
              "already coming down.")},
   {"when": "study ecg_12_lead ordered",
    "value": ("Intensivist: I am happy to take a young overdose with a temperature of 40 and a "
              "seizure. What I want before I write anything is the twelve-lead, because whether "
              "she has a conduction problem changes what happens in the first hour with me. "
              "Call me the moment it is through.")},
   {"when": None,
    "value": ("Intensivist: tell me the ECG and the temperature. A confused hyperthermic "
              "eighteen year old with an unknown ingestion is an intensive care patient in "
              "principle, and what I need to know is whether she has a conduction abnormality "
              "and whether anybody has treated it.")}],

 "consult_psychiatry": [
   {"when": "flag bicarb_given set AND flag cooling_started set",
    "value": ("Psychiatry registrar: thank you for calling once she is treated. We will see her, "
              "and not tonight in your department. She needs a monitored medical bed until the "
              "conduction and the temperature are sorted out, and we will assess her there.\n\n"
              "Two things while you have me. Somebody should be with her continuously, and her "
              "mother should not be the one doing it. And the history is worth writing down "
              "while it is fresh: an eighteen year old who has been bullied online, has lost a "
              "relationship and has withdrawn from her friends, who took an entire bottle of "
              "something at home alone in the afternoon while her mother was at work. That is a "
              "planned act in a period of isolation and it is not a low-risk presentation.")},
   {"when": None,
    "value": ("Psychiatry registrar: I will happily see her and she is not ready for me. She has "
              "not got a stable rhythm, she is over 40 degrees and she is delirious, so she "
              "cannot give me any history I could rely on and I cannot assess capacity or risk "
              "in a patient who does not know where she is.\n\nMedical clearance is not a form "
              "somebody signs. It means the medical problem is treated and the patient can "
              "engage. Call me when she is on a monitored bed and awake, and in the meantime "
              "please have someone with her.")}],

 "consult_neurology": [
   {"when": "study ct_head resulted AND study ecg_12_lead resulted",
    "value": ("Neurology registrar: the scan is clear and the tracing is not, and the tracing is "
              "the one I would be looking at. This is a toxic seizure with a cause you can "
              "point to, so it does not need my imaging or my drugs. Benzodiazepines, correct "
              "the acidosis, correct the temperature. If it recurs after adequate "
              "benzodiazepine dosing use levetiracetam or propofol and please do not use "
              "phenytoin, because it does the same thing to the sodium channel that whatever "
              "she took is doing. No indication for an EEG unless she stays down without "
              "waking.")},
   {"when": None,
    "value": ("Neurology registrar: a first seizure in a hyperthermic delirious teenager with an "
              "unknown ingestion is a provoked seizure until proven otherwise, and I would not "
              "be loading her with an anticonvulsant. Benzodiazepines, find and fix the "
              "provocation, and get a head CT if you have not. Do not use phenytoin in an "
              "overdose you have not characterised.")}],

 "consult_cardiology": [
   {"when": "study ecg_12_lead resulted",
    "value": ("Cardiology fellow: that is a wide complex with a terminal R in aVR and it is a "
              "toxicological problem rather than a cardiac one. I have nothing to add to sodium "
              "bicarbonate and I would call toxicology rather than me. No indication for the "
              "catheter laboratory and no indication for an antiarrhythmic. If she needs "
              "electricity because she loses her pressure, that is standard, but the drug that "
              "fixes the substrate is bicarbonate.")},
   {"when": None,
    "value": ("Cardiology fellow: send me the tracing and I will look at it, but a sinus "
              "tachycardia in a poisoned teenager is not a cardiology problem. If she has a "
              "wide QRS from a sodium-channel blocker, the treatment is bicarbonate and the "
              "call is to toxicology.")}],

 "consult_renal": [
   {"when": "study creatine_kinase_ck resulted",
    "value": ("Renal registrar: a creatine kinase of 540 is early and her creatinine is normal, "
              "so this is volume and observation rather than anything from me. Keep her filled, "
              "measure the urine output, repeat the creatine kinase and the electrolytes. Call "
              "me if the creatine kinase climbs into the thousands or the creatinine moves.\n\n"
              "On the drug itself: diphenhydramine is not effectively removed by haemodialysis, "
              "so there is no clearance argument for putting her on a machine.")},
   {"when": None,
    "value": ("Renal registrar: nothing for me yet. Send a creatine kinase and a creatinine and "
              "call me back if either is bad. Dialysis does not remove diphenhydramine, if that "
              "is what you were going to ask.")}],
}
