#!/usr/bin/env python3
"""ONE-TIME MIGRATION for CHFE-case.json, and the companion to
restructure_edema_states.py, which must have run first. Re-running it fails its own
assertions, which is intended.

WHAT CHANGED

1. Every content key that described the patient now describes him in the three phases the
   companion migration added. The pulmonary edema is the thing the case is now teaching
   the severity of, so it is staged explicitly and in the same words everywhere it is
   described:

     severe      presentation, impending_respiratory_failure
     moderate    niv_supported, nitrate_responding
     mild        stabilizing, improving

   Lung ultrasound is the readout that says so most directly, and it now has a rule per
   tier rather than a rule per treatment. It previously keyed its improved picture on
   `flag diuretic_given set`, which was wrong twice over: a diuretic given in the first
   minute changed the ultrasound while the patient was still in the arrival phase, and it
   credited the diuretic with clearing edema that the vasodilator had cleared. The rule is
   now `phase is improving`, which is the same set of runs by a different route and
   cannot fire early.

2. The patient is more breathless in what he says. He is answering in one and two word
   bursts on arrival rather than in short phrases, and the breathless register now covers
   the two moderate phases as well: a man at a respiratory rate of 28 with a mask strapped
   to his face does not speak in sentences either. The content of every answer is
   unchanged. A learner who asks about the water tablet gets the water tablet, in fewer
   words.

3. He stops answering when he tires. `impending_respiratory_failure` is authored at
   alertness 2, so section 10.5 requires it to be covered by a global answer rule, and the
   rule is the point rather than a formality: the history closes when the patient tires,
   and a learner who spent four minutes taking one loses the rest of it.

4. The venous gas and the lactate now have a reading for the phases either side of the
   arrival state. The gas in impending_respiratory_failure is the hypercapnia that
   explains the drowsiness, which is the finding that makes that phase legible rather than
   arbitrary.

NOT CHANGED, DELIBERATELY
The chest radiograph, the ECG and the consultants. A film does not clear in ten minutes
and neither does the ECG of an old anterior infarct.

PROVENANCE
Every clinical description here is an AI assistant's writing in the register the case
already used, not a physician's. The severity staging in particular is a teaching choice:
no trial says a mask moves this patient from severe to moderate in four minutes.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE

case = json.load(open(CASE))
assert "restructure_edema_states" in case.get("migrations", []), "run the companion first"
assert "rewrite_findings_and_speech" not in case["migrations"], "already applied"

CK = case["content_keys"]
TUBED = "phase is post_intubation_hypotension OR phase is intubated_stabilized"
SEVERE = "phase is presentation OR phase is impending_respiratory_failure"
MODERATE = "phase is niv_supported OR phase is nitrate_responding"
TALKING = "phase is presentation OR phase is niv_supported OR phase is nitrate_responding"


def finding(text):
    return {"kind": "exam_findings", "abnormal": True, "findings": text}


def report(text):
    return {"kind": "report", "abnormal": True, "report": text}


def rules(*pairs):
    out = [{"when": w, "value": v} for w, v in pairs]
    assert out[-1]["when"] is None, "the last rule must be unconditional"
    return out


# ---------------------------------------------------------------- general status
gs = CK["general_status"]
keep = {r["when"]: r["value"] for r in gs["rules"]}
gs["rules"] = rules(
    ("phase is post_intubation_hypotension", keep["phase is post_intubation_hypotension"]),
    ("phase is intubated_stabilized", keep["phase is intubated_stabilized"]),
    ("phase is impending_respiratory_failure", {
        "kind": "general_status", "abnormal": True,
        "findings": ("Exhausted. Drowsy, eyes closing between breaths, no longer "
                     "answering. Grey, sweating heavily, dusky at the lips. Still upright "
                     "because he cannot lie back.")}),
    ("phase is presentation", {
        "kind": "general_status", "abnormal": True,
        "findings": ("Severe respiratory distress. Upright, sweating, speaking one or two "
                     "words at a time and pausing to breathe between them. GCS 15.")}),
    ("phase is niv_supported", {
        "kind": "general_status", "abnormal": True,
        "findings": ("Moderate respiratory distress, better on the mask. Still "
                     "tachypnoeic, speaking in short bursts between breaths. GCS 15.")}),
    ("phase is nitrate_responding", {
        "kind": "general_status", "abnormal": True,
        "findings": ("Moderate respiratory distress. Still upright and breathing fast "
                     "with nothing on his face, but less frantic than on arrival. "
                     "Speaking in short bursts. GCS 15.")}),
    ("phase is stabilizing", {
        "kind": "general_status", "abnormal": True,
        "findings": ("Mild respiratory distress on the mask. Talking in short sentences "
                     "between breaths. GCS 15.")}),
    (None, keep[None]),
)

# ---------------------------------------------------------------- exams
EX = CK["exam"]
old = {k: {r["when"]: r["value"] for r in EX[k]}
       for k in EX if isinstance(EX[k], list)}

EX["exam_airway"] = rules(
    (TUBED, old["exam_airway"][TUBED]),
    ("phase is impending_respiratory_failure", finding(
        "Airway still patent and self-maintained, but he is no longer speaking and no "
        "longer clearing his own secretions readily. No stridor, no oropharyngeal "
        "swelling. This is an airway that is about to need help rather than one that is "
        "obstructed.")),
    ("phase is presentation", old["exam_airway"]["phase is presentation"]),
    ("phase is niv_supported OR phase is stabilizing", finding(
        "Airway patent and self-maintained under the mask. Speaking in short bursts when "
        "the mask is lifted. No stridor.")),
    ("phase is nitrate_responding", finding(
        "Airway patent and self-maintained. Speaking in short bursts, pausing to breathe. "
        "No stridor.")),
    (None, old["exam_airway"][None]),
)

EX["exam_breath"] = rules(
    (TUBED, old["exam_breath"][TUBED]),
    ("phase is impending_respiratory_failure", finding(
        "Exhausted respiratory effort. The rate is high and the breaths have become "
        "shallow, with the abdomen drawing in as the chest rises. Marked accessory muscle "
        "use at the neck. He no longer responds when you ask him to take a deep breath.")),
    ("phase is presentation", finding(
        "Marked increase in the work of breathing. Respiratory rate in the low thirties. "
        "Accessory muscle use at the neck with intercostal indrawing. Sitting bolt "
        "upright, gripping the trolley rails and refusing to lie back. Unable to complete "
        "a sentence. Chest rise symmetrical.")),
    ("phase is niv_supported", finding(
        "Work of breathing reduced on the mask though still increased. Rate in the high "
        "twenties. Accessory muscle use present and less marked than on arrival. "
        "Tolerating the mask and no longer gripping the rails. Chest rise symmetrical.")),
    ("phase is nitrate_responding", finding(
        "Still doing all the work himself at a rate around thirty, with accessory muscle "
        "use at the neck. Less frantic than on arrival and no longer refusing to be "
        "touched. Chest rise symmetrical.")),
    ("phase is stabilizing", finding(
        "Work of breathing close to normal on the mask. Rate in the low twenties. Minimal "
        "accessory muscle use, no indrawing. Chest rise symmetrical.")),
    (None, old["exam_breath"][None]),
)

EX["exam_pulm"] = rules(
    (TUBED, old["exam_pulm"][TUBED]),
    ("phase is impending_respiratory_failure", finding(
        "Fine and coarse crackles bilaterally from the bases to the apices. Air entry is "
        "poor throughout and the chest is quieter than the effort would suggest, which is "
        "the finding that matters here. No wheeze now.")),
    ("phase is presentation", old["exam_pulm"]["phase is presentation"]),
    (MODERATE, finding(
        "Crackles bilaterally to the mid-zones, no longer audible in the upper zones. The "
        "wheeze has settled. Air entry improved.")),
    ("phase is stabilizing", finding(
        "Crackles limited to the lower zones. No wheeze. Good air entry throughout.")),
    (None, finding(
        "Scattered fine crackles at both bases only. No wheeze. Air entry good "
        "throughout.")),
)

EX["exam_circ"] = rules(
    ("phase is post_intubation_hypotension",
     old["exam_circ"]["phase is post_intubation_hypotension"]),
    ("phase is intubated_stabilized", old["exam_circ"]["phase is intubated_stabilized"]),
    ("phase is impending_respiratory_failure", finding(
        "Still warm peripherally, which is the point: he is tiring, not shocked. "
        "Capillary refill under three seconds. Radial pulses full. Drenched in sweat. No "
        "external haemorrhage.")),
    (TALKING, old["exam_circ"]["phase is presentation"]),
    (None, old["exam_circ"][None]),
)

EX["exam_card"] = rules(
    ("phase is post_intubation_hypotension",
     old["exam_card"]["phase is post_intubation_hypotension"]),
    ("phase is intubated_stabilized", old["exam_card"]["phase is intubated_stabilized"]),
    (TALKING + " OR phase is impending_respiratory_failure OR phase is stabilizing",
     old["exam_card"]["phase is presentation OR phase is stabilizing"]),
    (None, old["exam_card"][None]),
)

EX["exam_skin"] = rules(
    ("phase is post_intubation_hypotension",
     old["exam_skin"]["phase is post_intubation_hypotension"]),
    ("phase is intubated_stabilized", old["exam_skin"]["phase is intubated_stabilized"]),
    ("phase is impending_respiratory_failure", finding(
        "Drenched in sweat, cool over the forehead with it, and dusky at the lips. Trunk "
        "still warm. No rash.")),
    ("phase is presentation", old["exam_skin"]["phase is presentation"]),
    (MODERATE + " OR phase is stabilizing", old["exam_skin"]["phase is stabilizing"]),
    (None, old["exam_skin"][None]),
)

EX["exam_neuro"] = rules(
    (TUBED, old["exam_neuro"][TUBED]),
    ("phase is impending_respiratory_failure", finding(
        "Drowsy and slow to rouse, opening his eyes to voice but not answering. No focal "
        "deficit, moving all four limbs to stimulation. Pupils equal and reactive. This is "
        "carbon dioxide, not a neurological event.")),
    (TALKING, old["exam_neuro"]["phase is presentation"]),
    (None, old["exam_neuro"][None]),
)

EX["exam_psych"] = rules(
    (TUBED, old["exam_psych"][TUBED]),
    ("phase is impending_respiratory_failure", finding(
        "Too drowsy to assess. No agitation.")),
    (TALKING, old["exam_psych"]["phase is presentation"]),
    (None, old["exam_psych"][None]),
)

# ---------------------------------------------------------------- lung ultrasound
pocus = CK["imaging"]["pocus_lung_cardiac"]
prev = {r["when"]: r["value"] for r in pocus["rules"]}
assert "flag diuretic_given set" in prev
CARDIAC = (" Cardiac: severely reduced left ventricular systolic function, visually "
           "consistent with an ejection fraction in the mid twenties, globally "
           "hypokinetic with anterior wall akinesis. No pericardial effusion. Right "
           "ventricle not dilated and no septal flattening.")
pocus["rules"] = rules(
    ("phase is post_intubation_hypotension", prev["phase is post_intubation_hypotension"]),
    ("phase is impending_respiratory_failure", report(
        "Lung: severe. Confluent B lines in every anterior and lateral zone bilaterally, "
        "coalescing into a white lung appearance anteriorly, with small bilateral pleural "
        "effusions." + CARDIAC +
        " Inferior vena cava 2.3 cm with minimal respiratory variation.")),
    ("phase is presentation", prev[None]),
    ("phase is niv_supported", report(
        "Lung: moderate. Three or more B lines per field remain in every zone, less dense "
        "anteriorly than at the bases, with small bilateral pleural effusions. No lung "
        "sliding abnormality, no pneumothorax." + CARDIAC +
        " Inferior vena cava 2.3 cm with minimal respiratory variation, unchanged.")),
    ("phase is nitrate_responding", report(
        "Lung: moderate. B lines reduced to two or three per field in the upper zones and "
        "still dense at the bases, with small bilateral pleural effusions." + CARDIAC +
        " Inferior vena cava 2.2 cm with minimal respiratory variation.")),
    ("phase is stabilizing", report(
        "Lung: mild. B lines now confined to the lower zones at one or two per field, "
        "with the anterior fields clear. Small bilateral pleural effusions unchanged." +
        CARDIAC + " Inferior vena cava 2.1 cm with minimal respiratory variation.")),
    ("phase is improving", report(
        "Lung: mild and clearing. Isolated B lines at both bases only, anterior and "
        "lateral fields clear, small bilateral pleural effusions unchanged." + CARDIAC +
        " Inferior vena cava 2.0 cm with a little more respiratory variation than on the "
        "earlier study.")),
    (None, prev[None]),
)

# ---------------------------------------------------------------- gas and lactate
vbg = CK["labs"]["labs_vbg"]
prevg = {r["when"]: r for r in vbg["rules"]}


def gas(ph, pco2, bicarb, be, lac, comment, ph_abn=True, pco2_abn=True):
    comps = [
        {"label": "pH (venous)", "value": ph, "unit": "",
         "reference_range": "7.31-7.41 (venous)", "abnormal": ph_abn},
        {"label": "pCO2", "value": pco2, "unit": "mmHg",
         "reference_range": "41-51 (venous)", "abnormal": pco2_abn},
        {"label": "Bicarbonate", "value": bicarb, "unit": "mEq/L",
         "reference_range": "22-26", "abnormal": False},
        {"label": "Base excess", "value": be, "unit": "mEq/L",
         "reference_range": "-2 to +2", "abnormal": False},
        {"label": "Lactate", "value": lac, "unit": "mmol/L",
         "reference_range": "under 2.0", "abnormal": float(lac) >= 2.0},
    ]
    return {"kind": "panel", "abnormal": True, "components": comps, "comment": comment}


vbg["rules"] = rules(
    ("phase is post_intubation_hypotension", prevg["phase is post_intubation_hypotension"]["value"]),
    ("phase is intubated_stabilized", prevg["phase is intubated_stabilized"]["value"]),
    ("phase is impending_respiratory_failure", gas(
        "7.21", "68", "26", "-1", "2.8",
        "Worsening acute respiratory acidosis. He is not clearing carbon dioxide because "
        "he is tiring, and this is the number that explains the drowsiness.")),
    ("phase is stabilizing OR phase is improving", gas(
        "7.36", "44", "24", "-1", "1.5",
        "The respiratory acidosis has corrected on positive pressure and afterload "
        "reduction.", ph_abn=False, pco2_abn=False)),
    (None, prevg[None]["value"]),
)
for r in vbg["rules"]:
    if "prose" in prevg.get(r["when"], {}):
        r["prose"] = prevg[r["when"]]["prose"]
    else:
        v = r["value"]
        r["prose"] = " ".join(
            "%s %s%s." % (c["label"], c["value"], (" " + c["unit"]) if c["unit"] else "")
            for c in v["components"]) + " " + v["comment"]

lac = CK["labs"]["labs_lactate"]
prevl = {r["when"]: r for r in lac["rules"]}
assert "flag on_niv set" in prevl
lac["rules"] = rules(
    ("phase is post_intubation_hypotension", prevl["phase is post_intubation_hypotension"]["value"]),
    ("phase is intubated_stabilized", prevl["phase is intubated_stabilized"]["value"]),
    ("phase is impending_respiratory_failure", {
        "kind": "value", "abnormal": True,
        "components": [{"label": "Lactate", "value": "2.8", "unit": "mmol/L",
                        "reference_range": "under 2.0", "abnormal": True}],
        "comment": "Higher than on arrival. The work of breathing is the source."}),
    ("phase is stabilizing OR phase is improving", prevl["flag on_niv set"]["value"]),
    (None, prevl[None]["value"]),
)
for r in lac["rules"]:
    src = prevl.get(r["when"])
    if src and "prose" in src:
        r["prose"] = src["prose"]
    elif r["when"] == "phase is stabilizing OR phase is improving":
        r["prose"] = prevl["flag on_niv set"].get("prose", "Lactate 1.4 mmol/L.")
    else:
        r["prose"] = "Lactate 2.8 mmol/L (high). Higher than on arrival."

# ---------------------------------------------------------------- the patient's speech
BREATHLESS = {
    "onset": "'Three... four days. Worse since... four this morning.'",
    "timing_progression": "'Worse. Every day. Since four... this morning... terrible.'",
    "character_of_dyspnea": "'Like drowning. Can't... get it in. Weight... on my chest.'",
    "severity": "'Ten. Worst... ever.'",
    "aggravating_factors": "'Lying down. Moving... anything.'",
    "relieving_factors": "'Sitting up. That's... all.'",
    "orthopnea": "'Four pillows. Chair... last night.'",
    "paroxysmal_nocturnal_dyspnea": "'Twice. Woke up... gasping.'",
    "leg_swelling": "'Both legs. Socks... cutting in.'",
    "weight_gain": "'Nine pounds. This week.'",
    "cough_and_sputum": "'Dry cough. Worse... lying down.'",
    "chest_pain": "'No pain. Just tight... from breathing.'",
    "palpitations": "'No. Not felt it.'",
    "fever_and_chills": "'No fever. No shivers.'",
    "syncope_and_dizziness": "'No. Not passed out.'",
    "nausea_and_vomiting": "'No. Not sick.'",
    "abdominal_fullness": "'Belly's full. Tight.'",
    "urine_output": "'Going less. Than usual.'",
    "calf_pain_or_asymmetry": "'No pain. Both... the same.'",
    "travel_immobility_surgery": "'No. Been at home.'",
    "hemoptysis": "'No blood.'",
    "medication_adherence": "'Ran out. Water tablet. Five days.'",
    "dietary_sodium": "'Christening. Weekend. Big spread.'",
    "current_medications": "'Water tablet. Heart tablets. Diabetes ones. Wife... has the list.'",
    "past_medical_history": "'Heart attack. Six years. Blood pressure. Diabetes.'",
    "past_surgical_history": "'Stent. Gallbladder.'",
    "allergies": "'No allergies.'",
    "social_history_smoking_alcohol": "'Stopped smoking. Six years. Beer... at weekends.'",
    "substance_use_stimulants": "'No. Never.'",
    "family_history": "'Dad. Heart attack. Brother... same.'",
    "last_oral_intake": "'Toast. Seven... this morning.'",
    "sleep_apnea_and_snoring": "'Wife says... I snore. Stop breathing.'",
    "recent_illness_or_sick_contacts": "'No. Nobody's... been ill.'",
    "functional_baseline": "'Normally... the stairs. Not this week.'",
}

iv = case["interview"]
assert set(BREATHLESS) == {t["topic"] for t in iv["topics"]}, "topic set has moved"

retagged = 0
for t in iv["topics"]:
    hit = [r for r in t["answer"] if r["when"] == "phase is presentation"]
    assert len(hit) == 1, t["topic"]
    hit[0]["when"] = TALKING
    hit[0]["value"] = BREATHLESS[t["topic"]]
    retagged += 1
    for f in t.get("facts") or []:
        if isinstance(f["value"], list):
            for r in f["value"]:
                if r["when"] == "phase is presentation":
                    r["when"] = TALKING
                    retagged += 1

for r in iv["out_of_scope_fallback"]:
    if r["when"] == "phase is presentation":
        r["when"] = TALKING
        r["value"] = ("He looks at you, still pulling hard for each breath, and shakes his "
                      "head. 'Sorry... I don't... know.'")
        retagged += 1

g = iv["global_answer_rules"]
assert len(g) == 1 and g[0]["when"] == TUBED
g.insert(0, {
    "when": "phase is impending_respiratory_failure",
    "value": ("He is too exhausted to answer. He opens his eyes when you speak and closes "
              "them again without saying anything."),
})

iv["authoring_notes"]["breathlessness_gating"] = (
    "Section 10.5 covers alertness but not speech limited by respiratory distress. Every "
    "topic is authored twice: a breathless register for the three phases where he is in "
    "distress and still talking, which is presentation and the two moderate phases, and "
    "the full answer for the phases where he is comfortable enough to give one. The "
    "content is identical between them and only the number of words changes, so a learner "
    "who asks the right question early is not punished with a worse answer, only a "
    "shorter one. On arrival he is down to one and two word bursts. That is the same "
    "register a resident hears from a real patient in this state, and it is the reason "
    "the case makes taking a history early expensive rather than impossible.")
iv["authoring_notes"]["alertness_gating"] = (
    iv["authoring_notes"]["alertness_gating"].rstrip() +
    " A third phase joined the two intubated ones when impending_respiratory_failure was "
    "added: he is drowsy from carbon dioxide rather than from sedation, and the effect on "
    "the history is the same. The history closes when the patient tires.")

case["migrations"].append("rewrite_findings_and_speech")

json.dump(case, open(OUT, "w"), indent=1, ensure_ascii=False)
open(OUT, "a").write("\n")
print("answers and facts retagged:", retagged)
print("wrote", OUT)
