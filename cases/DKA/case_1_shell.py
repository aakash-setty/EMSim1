"""DKA part 1: identity, patient, phases.

Mild diabetic ketoacidosis with a low potassium in a 24-year-old woman with type 1
diabetes and gastroenteritis. Drafted by a language model on 6 October 2026 from a plan
agreed with Aakash Setty in conversation. No physician has reviewed this pack. DKA-SEED.md
says what a person decided and which sources were opened.

Three learning goals drive the structure:

  1. Recognize ketoacidosis in a patient who looks like a stomach bug, and grade it.
  2. Know the potassium before giving insulin, and when it is under 3.5 replace it first
     and start insulin only once a repeat level is 3.5 or more.
  3. Once insulin is running, plan what follows: potassium in the fluids with the insulin,
     dextrose when the glucose falls, and insulin continued until the ketones clear.

The case has no clock that harms her and she cannot die. Every phase change is the
delayed consequence of something the learner did.
"""

META = {
 "working_title": "24-year-old woman, two days of vomiting and diarrhea, brought through from triage",
 "chief_complaint_patient_voice": "I can't keep anything down and I feel really weak.",
 "final_diagnosis": (
   "Mild diabetic ketoacidosis in type 1 diabetes, set off by gastroenteritis and reduced "
   "insulin doses, with hypokalemia (3.1 mEq/L) and mild hypomagnesemia from "
   "gastrointestinal losses. The potassium is low before any insulin is given, so insulin "
   "waits until it has been replaced."),
 "target_level": ["medical_student", "intern", "junior_resident"],
 "estimated_runtime_seconds": 540,
 "learning_objectives": [
   "Check a glucose, a venous gas, a chemistry and ketones in a vomiting patient with diabetes, and recognize ketoacidosis when the patient looks only mildly unwell.",
   "Grade the ketoacidosis as mild from the pH, the bicarbonate and the mental state.",
   "Read the potassium before giving insulin. Under 3.5 mEq/L, replace potassium first and hold insulin until a repeat level is 3.5 or more.",
   "Give fluid first, and know what fluid alone does and does not fix.",
   "Start insulin without a bolus once the potassium allows, by infusion or by subcutaneous rapid-acting insulin in mild ketoacidosis.",
   "Plan what follows insulin: potassium in the fluids at 20 to 30 mEq per liter with the insulin, dextrose when the glucose falls under 250 mg/dL, and insulin not stopped because the glucose looks better.",
 ],
 "teaching_frame": (
   "The reflex in ketoacidosis is insulin. In about one patient in ten or twenty the "
   "potassium is already low on arrival, and insulin drives it lower. This patient looks "
   "well enough that nothing feels urgent, which is what makes the reflex easy to follow. "
   "The case lets the learner give insulin early, shows what it does, and lets them undo it."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Adult emergency department. Point-of-care glucose and ketone testing, a step-down "
     "unit that runs insulin infusions and intravenous potassium on telemetry, and "
     "endocrinology on call by phone."),
 },
 "arrival": {
   "mode": "triage",
   "location": "patient_room",
   "line": "Walked in with her roommate and was brought through from triage to a monitored room.",
 },
 "complaint": "Vomiting and weakness",
 "category": "Endocrine and metabolic",
 "library": {
   "tempo": "no clock: nothing happens from waiting",
   "uncertainty": "the order, potassium before insulin, and the grade of the ketoacidosis",
   "right_answer": "wait, replace, then treat",
   "danger": "created by the treatment: insulin into a low potassium",
   "setting": "24 F, triage to a patient room",
   "feel": "puzzling",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Printed in docs/generated/case-index.md so a new case can say how it differs. Descriptive, not clinical: no physician has reviewed the wording."
 },
}

PATIENT = {
 "age": 24,
 "sex": "female",
 "weight_kg": 58,
 "background": (
   "Graduate student. Type 1 diabetes since age 11, on insulin glargine 18 units at night "
   "and insulin lispro with meals, by pen. One admission with ketoacidosis, at diagnosis. "
   "Appendix removed at 15. Takes a combined contraceptive pill. No other medical "
   "problems, no allergies. Drinks a little on weekends, no drugs.\n\n"
   "Her roommate had vomiting and diarrhea three days ago. Two days ago she started "
   "vomiting, then had watery diarrhea. Because she was not eating she took no mealtime "
   "insulin, halved her long-acting insulin the first night and skipped it last night. "
   "Since yesterday she has been very thirsty, passing a lot of urine, and weak. Her meter "
   "read 380 this morning. She has no ketone strips at home."),
 "presenting_vitals_source": "Inherited from phase 'presentation'.",
 "presenting_appearance": (
   "A slim young woman lying on the stretcher with a vomit bowl, tired and dry-lipped, "
   "breathing a little deeply. She answers clearly. Her roommate is in the chair."),
 "ems_handover_text": (
   "Twenty-four year old woman with type 1 diabetes, two days of vomiting and diarrhea "
   "after her roommate had the same. Not eating, so she cut back and then stopped her "
   "insulin. Thirsty and weak since yesterday. Rate 112, pressure 104 over 64, "
   "respirations 22, saturation 99 percent, temperature 37.3. No sugar done at triage."),
 "arrival_handover": (
   "Twenty-four year old woman, two days of vomiting and diarrhea, says she feels weak and "
   "can't keep fluids down. She looked dry and worn out so I brought her straight through."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 31 words. No vital sign, no past history, no medication, "
   "no pertinent negative. It leaves out the diabetes on purpose: the triage nurse did not "
   "ask, and the learner finds it by asking or by checking a sugar."),
 "avatar": {"build": "thin"},
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp, distress, alert,
          transitions, qtc, t_mv, ecg_note, terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": "normal", "pupil_reactivity": "reactive"},
      "rhythm": "regular",
      "ecg": {"pattern": "organised", "p_waves": True, "qrs_ms": 88, "qtc_ms": qtc,
              "t_mv": t_mv, "author_note": ecg_note},  # QRS 88 ms in every phase's report
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}

# Positive guards only. The validator reads a negated flag in a timed guard as a
# deterioration on inaction, and nothing in this case deteriorates on inaction.
K_IV = "flag potassium_iv_given set"
ANY_INSULIN = "flag insulin_given set"
RUNNING = "flag insulin_running set"
HELD = "flag insulin_stopped set"
# Two hidden case actions carry "when" for the phase machine, because no flag can
# (authoring 19 and 8.2). Nothing presses them. Each is credited through also_satisfies
# on the real insulin orders, with a condition on the phase at the moment of the order.
#   early_insulin    any rapid insulin ordered in the arrival phase
#   insulin_restart  an infusion or a subcutaneous dose ordered in the recovering phase
EARLY = "action early_insulin taken"
RESTARTED = "action insulin_restart taken"

ECG_LOW_K = ("Sinus tachycardia with a slightly flattened T wave and a QTc of 460, as the phase's "
             "twelve-lead report says. The monitor lead cannot draw a U wave. Model output.")

EARLY_INSULIN_RATIONALE = (
  "A delayed consequence of the learner's own action. Insulin moves potassium into cells "
  "within minutes, and the 2024 consensus report says to delay insulin when the potassium "
  "is under 3.5 mmol/L to avoid arrhythmia and respiratory muscle weakness. The size of "
  "the fall (3.1 to 2.6) and the ten seconds are teaching choices. Ten seconds stands for "
  "about an hour. Model output.")

EARLY_INSULIN_NARRATION = ("She says her arms and legs feel heavy and her heart is fluttering. "
                           "Her rate has gone up.")

UNVERIFIED_REPORT = " [UNVERIFIED: Umpierrez et al. 2024, read through a summarizing tool]"

PHASES = [
 phase("presentation",
   "Mild ketoacidosis, potassium low, nothing given",
   "on arrival",
   "Tired, dry, breathing a little deeply, fully alert. Glucose 348, pH 7.27, bicarbonate "
   "16, potassium 3.1. Fluid helps her circulation and does not change the question, "
   "which is what has to happen before insulin.",
   112, 104, 64, 22, 99, 37.3, 1, 0,
   [HANDOFF_T,
    {"when": ANY_INSULIN,
     "after_seconds": 10, "measured_from": "guard_true", "to": "potassium_falling",
     "narration": EARLY_INSULIN_NARRATION,
     "debrief_note": (
       "Insulin was given before her potassium was replaced. It was 3.1 on arrival. "
       "Insulin moves potassium into cells, and hers fell to 2.6. She became weak and her "
       "ECG changed.\n\n"
       "This is the decision the case is built around. In ketoacidosis the body is short "
       "of potassium even when the blood level looks normal, and vomiting and diarrhea had "
       "already taken hers low. The potassium result comes before the insulin. Under 3.5, "
       "replace it and hold insulin until it is back to 3.5 or more." + UNVERIFIED_REPORT),
     "author_rationale": EARLY_INSULIN_RATIONALE},
    {"when": K_IV,
     "after_seconds": 20, "measured_from": "guard_true", "to": "potassium_replaced",
     "narration": ("That potassium has run through on the pump. Do you want a repeat "
                   "level?"),
     "debrief_note": (
       "The potassium infusion ran in. A level sent after this point reads 3.6.\n\n"
       "Twenty seconds here stands for one to three hours of infusion at 20 to 40 mEq an "
       "hour, with a level every one to two hours. This is the slow part of the real case "
       "and insulin waits for it. The wait has a cost. With no insulin on board her "
       "ketones keep rising, which is the reason to start the potassium promptly."
       " [UNVERIFIED: the hours are a rough rule written by a model from the rate the "
       "directing physician set, not from a source]"),
     "author_rationale": (
       "A delayed consequence of the learner's own action. A rise from 3.1 to 3.6 is "
       "taken as about 40 to 60 mEq, by a rough rule that often underestimates the need "
       "in ketoacidosis. Compressed openly, and the nurse says the infusion takes a while. "
       "Model output.")}],
   460, 0.1, ECG_LOW_K,
   ),

 phase("potassium_replaced",
   "Potassium infusion finished, level back to 3.5 or more",
   "after potassium",
   "Unchanged to look at. Potassium 3.6, glucose 320, pH 7.26, ketones a little higher. "
   "She is still in ketoacidosis, and now insulin is safe to start. A learner who gave "
   "insulin while the potassium was still running passes through here for five seconds "
   "on the way to potassium_falling.",
   112, 104, 64, 22, 99, 37.3, 1, 0,
   [HANDOFF_T,
    {"when": EARLY,
     "after_seconds": 5, "measured_from": "guard_true", "to": "potassium_falling",
     "narration": EARLY_INSULIN_NARRATION,
     "debrief_note": (
       "Insulin was ordered while the potassium was still running in, before any repeat "
       "level. The infusion finished first, and then the insulin did what it does at a "
       "low potassium. It moved potassium into cells and her level fell to 2.6.\n\n"
       "Potassium that has been started is not potassium that has been replaced. Insulin "
       "waits for the infusion to finish and for a level of 3.5 or more." + UNVERIFIED_REPORT),
     "author_rationale": (
       EARLY_INSULIN_RATIONALE + " This rule closes a race. Insulin ordered more than ten "
       "seconds after potassium used to be outrun by the potassium rule and reach the "
       "treated phase. The guard is a hidden action credited when rapid insulin is "
       "ordered in the arrival phase, so it holds on entry and this rule fires five "
       "seconds later, ahead of the ten second rule below. Five seconds is the "
       "validator's floor for a delayed consequence and is not a clinical claim."),
     "author_note": "Above the insulin rule on purpose. See the race table in DKA-SEED.md."},
    {"when": RUNNING,
     "after_seconds": 10, "measured_from": "guard_true", "to": "treated",
     "narration": ("Her sugar is coming down on the insulin, 266 on the meter, and she "
                   "says the sick feeling is easing. Her rate is settling."),
     "debrief_note": (
       "Insulin was started after the potassium had run in and the level was back to 3.5 "
       "or more. Her glucose is falling and the ketones are clearing.\n\n"
       "From here the work is watching. Glucose every hour, potassium every one to two "
       "hours at first with 20 to 30 mEq in each liter of fluid, and a plan for when the "
       "glucose gets under 250." + UNVERIFIED_REPORT),
     "author_rationale": (
       "A delayed consequence of the learner's own action. Ten seconds stands for about "
       "an hour. Model output.")}],
   450, 0.14,
   "Sinus tachycardia, T wave fuller than on arrival, as the phase's report says. Model output.",
   ),

 phase("treated",
   "On insulin with the potassium replaced",
   "improving",
   "Nausea easing, rate settling. Glucose 268, pH 7.30, bicarbonate 18, potassium 3.7. The "
   "intended endpoint. She needs dextrose in the fluids soon, and insulin until the "
   "ketones clear.",
   104, 106, 66, 20, 99, 37.2, 0, 0,
   [HANDOFF_T],
   445, 0.18,
   "Sinus rhythm, T waves normal, as the phase's report says. Model output.",
   ),

 phase("potassium_falling",
   "Potassium driven down by insulin",
   "weak",
   "Weak in the arms and legs, aware of her heartbeat, still alert. Potassium 2.6. The ECG "
   "shows flat T waves, larger U waves and a longer QT. No clock leaves this phase. "
   "Holding insulin with intravenous potassium given gets her out. Potassium given "
   "before she fell counts, because an infusion that is running is still running.",
   118, 102, 62, 22, 99, 37.3, 2, 0,
   [HANDOFF_T,
    {"when": K_IV + " AND " + HELD,
     "after_seconds": 20, "measured_from": "guard_true", "to": "recovering",
     "narration": ("The potassium has run through. She says her arms feel stronger and "
                   "her rate has come back down. Do you want a repeat level?"),
     "debrief_note": (
       "You held the insulin and replaced the potassium, and she recovered. Seeing that a "
       "treatment is hurting the patient and withdrawing it is a skill.\n\n"
       "Potassium that was already running when she became weak counted. An infusion "
       "that is running is still running, so holding the insulin was the step that was "
       "missing.\n\n"
       "Insulin restarts once a repeat potassium is 3.5 or more. In the simulator a held "
       "insulin stays off until it is ordered again."),
     "author_rationale": (
       "A delayed consequence of the learner's own actions. Twenty seconds stands for "
       "several hours of infusion, measured from the moment both the hold and the "
       "potassium are in. Model output.")}],
   520, 0.03,
   ("Sinus tachycardia with a nearly flat T wave and a QT of about 520 ms, as the phase's "
    "report says. The report also describes U waves and occasional ventricular ectopic "
    "beats, and the monitor draws neither. Model output."),
   ),

 phase("recovering",
   "Recovered after early insulin, potassium replaced",
   "recovering",
   "Strength back. Potassium 3.6, glucose 285, still in ketoacidosis. One order of an "
   "insulin infusion or subcutaneous insulin placed in this phase moves her to the "
   "treated phase.",
   112, 104, 64, 22, 99, 37.3, 1, 0,
   [HANDOFF_T,
    {"when": RESTARTED,
     "after_seconds": 10, "measured_from": "guard_true", "to": "treated",
     "narration": ("Insulin is back on and her sugar is coming down, 266 on the meter. "
                   "Her rate is settling."),
     "debrief_note": (
       "Insulin was restarted with the potassium at 3.5 or more. This is where the first "
       "dose belonged."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. The guard is a hidden action "
       "credited when an insulin infusion or a subcutaneous dose is ordered in this "
       "phase, so one order after the rescue is the restart whatever was ordered "
       "before it. Ten seconds stands for about an hour. Model output.")}],
   450, 0.14,
   "Sinus tachycardia, T wave fuller again, as the phase's report says. Model output.",
   authoring_note=(
     "Same numbers as potassium_replaced. Two phases because the exits differ: here the "
     "insulin flags are already set, so the exit is an insulin order placed in this phase."),
   ),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   104, 106, 66, 20, 99, 37.2, 0, 0, [], 445, 0.18,
   "Fallback only. The phase inherits the vitals of the phase the handoff came from.",
   terminal=True, inherit_vitals=True,
   ),
]
