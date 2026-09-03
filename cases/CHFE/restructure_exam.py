#!/usr/bin/env python3
"""ONE-TIME MIGRATION, already applied to CHFE-case.json. Kept as the record of
what changed and why; re-running it on an already-migrated file will fail its own
assertions, which is the intended safety.

NOTE, later: this file still names `niv_cpap`, which no longer exists. That action was
merged into `niv_bipap_cpap` by `consolidate_niv.py`. The reference is left as it was
because this file is a record of what the case looked like when the migration ran, and
editing it would falsify that record.

Redistribute the case's exam findings into the catalog's closed set of 14 manoeuvres.

The action catalog states that the 14 exam entries are the complete set and supplies
`exam_finding_routing`, which fixes where a finding belongs when its anatomy does not map
cleanly onto a manoeuvre. The case was written before that existed and used its own
manoeuvres (general appearance, JVP, hepatojugular reflux, extremities), four of which do
not exist in the interface.

This script rewrites `content_keys.exam` onto the catalog ids and follows the routing map
exactly. It also adds `content_keys.general_status`, which the catalog defines as a line
rendered above the exam list rather than a clickable action.

WHAT IS CARRIED ACROSS AND WHAT IS NEW
Every finding in the original nine keys is preserved; nothing authored was dropped.
Three categories had no prior authored content and were written during redistribution
from findings already stated elsewhere in the case:

  exam_airway  patency and speech, from the general appearance rules
  exam_breath  work of breathing, from the general appearance rules
  exam_psych   anxiety and cooperativeness, from the neuro rules

Those three are the only new clinical statements, and each restates something the case
already asserted in another key. They still need physician review like everything else.

ROUTING DECISIONS FORCED BY THE MAP
  peripheral oedema        -> exam_card   (the map says so; not exam_msk and not exam_circ)
  jugular venous pressure  -> exam_neck
  hepatojugular reflux     -> exam_neck   (a jugular manoeuvre; no separate entry exists)
  capillary refill,
  peripheral temperature,
  pulse quality            -> exam_circ
  calf tenderness and
  asymmetry                -> exam_msk    ("extremity findings")
  lung auscultation        -> exam_pulm

The hepatojugular reflux loses its identity as a discrete act. That is a real loss: the
case tagged it as a separate confirmatory manoeuvre with its own teaching note. The note
is folded into exam_neck.
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE

INTUB = "phase is post_intubation_hypotension OR phase is intubated_stabilized"
HYPO = "phase is post_intubation_hypotension"
STAB = "phase is intubated_stabilized"
PRES = "phase is presentation"
RESP = "phase is stabilizing"


def F(text, abnormal=True):
    return {"kind": "exam_findings", "abnormal": abnormal, "findings": text}


def G(text, abnormal=True):
    return {"kind": "general_status", "abnormal": abnormal, "findings": text}


# ---------------------------------------------------------------- general status
GENERAL_STATUS = [
    {"when": HYPO, "value": G("Intubated and sedated. Not responsive. Mottled and cool peripherally.")},
    {"when": STAB, "value": G("Intubated and sedated on the ventilator. Colour improved, peripherally warm.")},
    {"when": PRES, "value": G("Severe respiratory distress. Upright, sweating, speaking in short bursts. GCS 15.")},
    {"when": RESP, "value": G("Moderate respiratory distress, improving on the mask. Speaking in short sentences. GCS 15.")},
    {"when": None, "value": G("Comfortable at rest on the mask. Talking in full sentences. GCS 15.")},
]

# ---------------------------------------------------------------- the 14 manoeuvres
EXAM = {

 "exam_airway": [
   {"when": INTUB, "value": F(
     "Endotracheal tube in place and secured at the teeth, cuff inflated. Airway protected by the tube. "
     "No secretions requiring suction.")},
   {"when": PRES, "value": F(
     "Airway patent and self-maintained. No stridor, no drooling, no oropharyngeal swelling. "
     "He is speaking, but only in two or three word bursts, pausing to breathe between them.")},
   {"when": RESP, "value": F(
     "Airway patent and self-maintained under the mask. Speaking in short sentences.")},
   {"when": None, "value": F(
     "Airway patent and self-maintained. Speaking in full sentences. No stridor.", abnormal=False)},
 ],

 "exam_breath": [
   {"when": INTUB, "value": F(
     "Ventilated. Chest rises symmetrically with each delivered breath. No accessory muscle use, "
     "no spontaneous effort against the ventilator.")},
   {"when": PRES, "value": F(
     "Marked increase in the work of breathing. Respiratory rate in the low thirties. Accessory muscle "
     "use at the neck with intercostal indrawing. Sitting bolt upright, gripping the trolley rails and "
     "refusing to lie back. Chest rise symmetrical.")},
   {"when": RESP, "value": F(
     "Work of breathing reduced on the mask. Rate in the mid twenties. Accessory muscle use present but "
     "less marked. No longer gripping the rails. Chest rise symmetrical.")},
   {"when": None, "value": F(
     "Breathing comfortably at a normal rate. No accessory muscle use and no indrawing. Chest rise "
     "symmetrical and air entry equal.", abnormal=False)},
 ],

 "exam_circ": [
   {"when": HYPO, "value": F(
     "Cool peripherally with mottling over the knees. Capillary refill four seconds. Radial pulses "
     "thready. No external haemorrhage.")},
   {"when": STAB, "value": F(
     "Peripherally warm again. Capillary refill under three seconds. Pulses easily palpable and equal. "
     "No external haemorrhage.")},
   {"when": PRES, "value": F(
     "Warm and well perfused peripherally despite the distress. Capillary refill under two seconds. "
     "Radial and dorsalis pedis pulses full and equal bilaterally. Skin is sweaty but not cold. "
     "No external haemorrhage.")},
   {"when": None, "value": F(
     "Warm and well perfused. Capillary refill under two seconds. Peripheral pulses full and equal. "
     "No external haemorrhage.", abnormal=False)},
 ],

 "exam_neck": [
   {"when": INTUB, "value": F(
     "Jugular venous pulsation visible to the angle of the jaw at 45 degrees, approximately 14 cm of "
     "water. Harder to assess against positive pressure ventilation, but clearly elevated. Trachea "
     "midline. Sustained right upper quadrant pressure raises the venous column further and it does not "
     "fall back while pressure is maintained: hepatojugular reflux positive.")},
   {"when": None, "value": F(
     "Jugular venous pulsation visible to the angle of the jaw with the head of the bed at 45 degrees, "
     "approximately 14 cm of water. Clearly and unambiguously elevated. Trachea midline. No "
     "lymphadenopathy. Sustained pressure over the right upper quadrant produces a rise in the jugular "
     "venous column that does not fall back while pressure is maintained: hepatojugular reflux positive.")},
 ],

 "exam_card": [
   {"when": HYPO, "value": F(
     "Tachycardic at around 128, regular, heart sounds quiet. A third heart sound is present. Soft "
     "systolic murmur at the apex. Two plus pitting oedema to the mid-shin bilaterally, symmetrical.")},
   {"when": STAB, "value": F(
     "Regular at around 96. Third heart sound still audible. Grade 2 out of 6 holosystolic murmur at the "
     "apex. Two plus pitting oedema to the mid-shin bilaterally, symmetrical.")},
   {"when": PRES + " OR " + RESP, "value": F(
     "Tachycardic and regular. A third heart sound is present at the apex, best heard with the bell in "
     "the left lateral position. Grade 2 out of 6 blowing holosystolic murmur at the apex radiating "
     "toward the axilla. The apex beat is displaced laterally to the anterior axillary line. Two plus "
     "pitting oedema to the mid-shin bilaterally, symmetrical, with indentation from his sock at the "
     "ankle.")},
   {"when": None, "value": F(
     "Regular, rate around 90. A third heart sound is still audible. Grade 2 out of 6 holosystolic "
     "murmur at the apex. Apex beat displaced laterally. Two plus pitting oedema to the mid-shin "
     "bilaterally, symmetrical.")},
 ],

 "exam_pulm": [
   {"when": INTUB, "value": F(
     "Bilateral coarse crackles to the mid-zones. Equal breath sounds both sides with the tube in place. "
     "No wheeze.")},
   {"when": PRES, "value": F(
     "Fine and coarse crackles bilaterally from the bases up to the upper zones, with a scattered "
     "expiratory wheeze overlying them. Air entry is poor at both bases. No focal absence of breath "
     "sounds.")},
   {"when": RESP, "value": F(
     "Crackles bilaterally to the mid-zones, no longer audible in the upper zones. The wheeze has "
     "resolved. Air entry improved.")},
   {"when": None, "value": F(
     "Crackles limited to both bases. No wheeze. Good air entry throughout.")},
 ],

 "exam_abd": [
   {"when": None, "value": F(
     "Soft and mildly distended. The liver edge is palpable about three centimetres below the costal "
     "margin and is tender to press. No rebound, no guarding. No pulsatile mass. Bowel sounds present.")},
 ],

 "exam_msk": [
   {"when": None, "value": F(
     "No deformity, joint effusion or focal bony tenderness. Compartments soft. No calf tenderness, "
     "asymmetry or palpable cords. Distal sensation and motor function intact in all four limbs. "
     "Bilateral symmetrical pitting oedema is present; see the cardiovascular examination.",
     abnormal=False)},
 ],

 "exam_skin": [
   {"when": HYPO, "value": F("Cool and mottled over the knees and forearms. No rash.")},
   {"when": STAB, "value": F("Warm and dry. Mottling resolved. No rash.", abnormal=False)},
   {"when": PRES, "value": F(
     "Warm to the touch and visibly sweating over the forehead, neck and chest. No rash. No cyanosis of "
     "the lips at present.")},
   {"when": RESP, "value": F("Damp but no longer actively sweating. Warm. No rash.")},
   {"when": None, "value": F("Warm and dry. No rash.", abnormal=False)},
 ],

 "exam_neuro": [
   {"when": INTUB, "value": F(
     "Sedated and not responsive to voice. Pupils equal and reactive but sluggish. Moving nothing "
     "spontaneously.")},
   {"when": PRES, "value": F(
     "Alert and oriented to person, place and time, GCS 15, though answers are clipped by "
     "breathlessness. No focal deficit. Moving all four limbs normally.", abnormal=False)},
   {"when": None, "value": F(
     "Alert and oriented, GCS 15, answering in full sentences. No focal deficit.", abnormal=False)},
 ],

 "exam_psych": [
   {"when": INTUB, "value": F("Sedated. Not assessable.")},
   {"when": PRES, "value": F(
     "Anxious and frightened, but cooperative and following instruction. Thought linear. No suicidal or "
     "homicidal ideation. No hallucinations.")},
   {"when": None, "value": F(
     "Calm and cooperative with appropriate affect. Thought linear and goal directed. No suicidal or "
     "homicidal ideation.", abnormal=False)},
 ],
}

# Not authored, inherit the catalog default: exam_heent, exam_gu, exam_back.

# ---------------------------------------------------------------- action metadata
# Debrief notes move with the findings. Where two old manoeuvres merge, the notes merge.
OLD = {}
NEW_ACTION_META = {
 "exam_airway": ("Perform Airway Exam",
   "In a breathless patient the airway question is answered by listening to him talk. Speech fragmented "
   "into two or three word bursts is a measurement of respiratory reserve, not a communication problem, "
   "and it is the finding that tells you how close he is to tiring. A patient who can still protect his "
   "airway and speak does not need a tube yet, however bad he looks."),
 "exam_breath": ("Perform Breathing Exam",
   "Work of breathing is the end-of-bed assessment and it does most of the triage in this case. Upright "
   "posture the patient will not abandon, accessory muscle use, intercostal indrawing and diaphoresis "
   "together identify a patient who needs an intervention in the next few minutes rather than the next "
   "hour. This is also the finding that improves first and most visibly with non-invasive ventilation, "
   "which makes it the one to re-check after you act."),
 "exam_circ": ("Perform Circulation Exam",
   "This is the manoeuvre that decides the case. Warm peripheries with a capillary refill under two "
   "seconds and full pulses place him in the warm profile, which is what makes vasodilation and diuresis "
   "safe and inotropes wrong. The same patient after intubation is cool and mottled with a four second "
   "refill, and the treatment inverts. Perfusion is not a number on the monitor; it is this examination."),
 "exam_neck": ("Perform Neck Exam",
   "The single most useful physical sign in this case, and the one most often skipped. A raised jugular "
   "venous pressure separates this patient from the septic patient who needs fluid and from the "
   "asthmatic who needs bronchodilators. Auscultating the chest without also looking at the neck veins "
   "is how the wheeze gets misread as bronchospasm. The hepatojugular reflux is the confirmatory "
   "manoeuvre when the column is technically difficult to see, which it often is in a heavy, breathless "
   "patient who will not lie back; a sustained rise that does not fall back while pressure is maintained "
   "is a positive test."),
 "exam_card": ("Perform Cardiovascular Exam",
   "A third heart sound is one of the few examination findings in dyspnoea with a high positive "
   "likelihood ratio for heart failure. It is insensitive, so its absence proves little, but hearing it "
   "in this context is close to diagnostic. The laterally displaced apex is chronic, not acute. The "
   "symmetrical pitting oedema measures how long this has been building; it is days of accumulated "
   "sodium and water, and it will not resolve in the emergency department however much you diurese."),
 "exam_pulm": ("Perform Pulmonary Exam",
   "Crackles with an overlying expiratory wheeze. Cardiac asthma is the trap: the wheeze is deliberate "
   "and it is there to attract a bronchodilator. What settles it is not the chest at all, it is the "
   "neck veins and the peripheries."),
 "exam_abd": ("Perform Abdominal Exam",
   "The tender enlarged liver is congestive hepatopathy from raised right-sided pressures, and it "
   "matches the abnormal liver enzymes if those were sent. It also matters as a negative: a soft abdomen "
   "without peritonism moves an intra-abdominal catastrophe well down the list in a patient who is "
   "tachycardic and unwell."),
 "exam_msk": ("Perform Musculoskeletal Exam",
   "Here this is a pertinent negative and nothing else. Symmetrical oedema with no calf tenderness, "
   "asymmetry or cords argues against deep vein thrombosis, which is the reasoning that should stop the "
   "D-dimer being sent rather than the D-dimer result stopping it afterwards."),
 "exam_skin": ("Perform Skin Exam",
   "Peripheral temperature and sweating are the two bedside proxies for perfusion and sympathetic drive. "
   "He is sweating heavily but his skin is warm, which is the sympathetic response to respiratory "
   "distress rather than the vasoconstriction of shock. Cold and sweaty would mean something entirely "
   "different and would change the treatment."),
 "exam_neuro": ("Perform Neurological Exam",
   "Mental status is a perfusion measurement, and here it is the reassuring one. A patient who is alert, "
   "oriented and anxious is perfusing his brain, which supports the warm classification and argues "
   "against cardiogenic shock. A patient with the same vital signs who has become drowsy is a different "
   "and much more urgent problem."),
 "exam_psych": ("Perform Psychological Exam",
   "Anxiety in acute pulmonary oedema is a symptom of hypoxaemia and air hunger, not a psychiatric "
   "finding, and it settles as the physiology settles. Recording it matters because it is the baseline "
   "against which a later change in mental state is judged."),
}


MIGRATION_MARKER = "restructure_exam"


def refuse_if_already_migrated(case):
    """A one-time migration that silently re-runs destroys the thing it created.

    structure_results.py stores the original prose alongside the structured payload;
    running it twice overwrites that prose with the payload, losing the diffable record
    the reviewing physician needs. The docstring said re-running would fail its own
    assertions. It did not: the assertions checked rule counts and conditions, both of
    which still hold after migration. This checks the thing that actually changes.
    """
    if MIGRATION_MARKER in (case.get("migrations") or []):
        raise SystemExit(
            f"{MIGRATION_MARKER} has already been applied to this case file. "
            f"Re-running would overwrite migrated data. Nothing was changed.")


def mark_migrated(case):
    case.setdefault("migrations", [])
    if MIGRATION_MARKER not in case["migrations"]:
        case["migrations"].append(MIGRATION_MARKER)


def main():
    case = json.load(open(CASE))
    refuse_if_already_migrated(case)

    old_exam = {k: v for k, v in case["content_keys"]["exam"].items() if k != "authoring_note"}
    old_ids = set(old_exam)

    case["content_keys"]["exam"] = {
        "authoring_note":
            "Bound to the action catalog's closed set of 14 manoeuvres. Findings are placed according to "
            "the catalog's exam_finding_routing map, not by the author's preference: peripheral oedema "
            "sits under the cardiovascular exam, jugular venous pressure and hepatojugular reflux under "
            "the neck exam, capillary refill and peripheral temperature under the circulation exam. "
            "exam_heent, exam_gu and exam_back are not authored and inherit the catalog default.",
    }
    for k, rules in EXAM.items():
        case["content_keys"]["exam"][k] = rules

    case["content_keys"]["general_status"] = {
        "authoring_note":
            "Rendered above the exam list. Not a clickable action, so it has no catalog entry and cannot "
            "be omitted by the learner. The catalog supplies a default for it the same way it does for "
            "the manoeuvres.",
        "rules": GENERAL_STATUS,
    }

    # rebuild the exam case_actions onto catalog ids
    kept = [a for a in case["case_actions"] if a["catalog_id"] not in old_ids]
    new_actions = []
    for cid, (name, note) in NEW_ACTION_META.items():
        new_actions.append({
            "catalog_id": cid,
            "display_name": name,
            "tag": [{"when": None, "value": "neutral"}],
            "state_changing": False,
            "debrief_note": note,
        })
    # exams keep their position in the file, ahead of the handoff action
    case["case_actions"] = kept + new_actions

    # display name corrections requested by the author
    for a in case["case_actions"]:
        if a["catalog_id"] == "iv_access_peripheral":
            a["display_name"] = "Insert IV"
        if a["catalog_id"] == "niv_cpap":
            a["display_name"] = "Positive pressure ventilation (CPAP/BIPAP)"

    # the examination debrief domain must name the new manoeuvres
    for d in case["debrief_configuration"]["clinical_domains"]:
        if d["id"] == "examination":
            d["actions"] = list(NEW_ACTION_META)
        else:
            d["actions"] = [a for a in d["actions"] if a not in old_ids]

    case.setdefault("provenance", {}).setdefault("author_only_fields_pending_signoff", [])
    case["provenance"]["exam_redistribution"] = {
        "reason": "The action catalog defines a closed set of 14 exam manoeuvres and a routing map. The "
                  "case's own manoeuvres (general appearance, jugular venous pressure, hepatojugular "
                  "reflux, extremities) do not exist in the interface.",
        "newly_authored_during_redistribution": ["exam_airway", "exam_breath", "exam_psych"],
        "lost_as_a_discrete_act": ["exam_hepatojugular_reflux"],
        "not_authored_inherit_catalog_default": ["exam_heent", "exam_gu", "exam_back"],
    }

    mark_migrated(case)
    json.dump(case, open(OUT, "w"), indent=1)
    print("exam keys:", len(EXAM), "| general status rules:", len(GENERAL_STATUS),
          "| exam actions rebuilt:", len(new_actions))
    print("replaced:", sorted(old_ids))


if __name__ == "__main__":
    main()
