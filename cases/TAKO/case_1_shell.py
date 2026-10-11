"""TAKO part 1: identity, patient, phases.

Takotsubo cardiomyopathy with left ventricular outflow obstruction in a 68-year-old woman.
Drafted by a language model on 6 October 2026 from a plan agreed with Aakash Setty in
conversation. No physician has reviewed this pack. TAKO-SEED.md says what a person decided.

Three learning goals drive the structure:

  1. Treat chest pain with ST elevation as a coronary occlusion, whatever the story.
  2. Look at the heart before treating cardiogenic shock.
  3. Treat outflow obstruction the right way round: no nitrate, no inotrope, a little
     fluid, a vasoconstrictor.
"""

META = {
 "working_title": "68-year-old woman, chest pain at her husband's funeral, brought in by EMS",
 "chief_complaint_patient_voice": "There's an elephant on my chest and I can't get my breath.",
 "final_diagnosis": (
   "Takotsubo (stress) cardiomyopathy, apical type, with dynamic left ventricular outflow "
   "tract obstruction and cardiogenic shock. It cannot be told apart from an anterior "
   "ST-elevation myocardial infarction before angiography, so it is treated as one in the "
   "emergency department. The angiogram, which the learner sees only in the debrief, shows "
   "no obstructive coronary disease and apical ballooning."),
 "target_level": ["intern", "junior_resident", "senior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "Treat chest pain with ST elevation as an acute coronary occlusion whatever the story: ECG early, aspirin, and activation of the catheterization laboratory.",
   "Do not let an emotional trigger or a family's explanation downgrade a dangerous ECG.",
   "Before treating cardiogenic shock, listen to the heart and put a probe on it, because a murmur and an echo can reverse the plan.",
   "Recognize dynamic left ventricular outflow obstruction: a new harsh systolic murmur, a base that squeezes hard and an apex that does not move.",
   "In outflow obstruction avoid nitrates, inotropes and diuretics, and give cautious fluid when the lungs are clear and a vasoconstrictor without inotropic effect.",
   "Call cardiology early when the pressure falls, and stop a drug that is making the patient worse.",
 ],
 "teaching_frame": (
   "Two reflexes are wrong for this patient and both feel right. The first is to believe "
   "the story: she has just buried her husband, so it must be grief. The second is to treat "
   "a weak heart with a low pressure the usual way, with an inotrope. The case is hard on "
   "purpose, and the cardiologist is there to help the moment the learner asks."),
 "care_setting": {
   "label": "Urban academic emergency department with a catheterization laboratory",
   "detail": (
     "Adult emergency department. Interventional cardiology on call and a catheterization "
     "laboratory available at any hour, which is why thrombolysis is the wrong choice here. "
     "Intensive care and mechanical circulatory support on site."),
 },
 "arrival": {
   "mode": "ems",
   "location": "resuscitation_bay",
   "line": "Brought in by EMS from a funeral reception. Her daughter came in the ambulance.",
 },
 "complaint": "Chest pain",
 "category": "Cardiovascular",
 "library": {
   "tempo": "minutes: obstruction and shock run on a clock",
   "uncertainty": "the diagnosis, occlusion against stress cardiomyopathy, and which treatment makes the shock worse",
   "right_answer": "treat it as an occlusion, call cardiology, avoid the drugs that look right",
   "danger": "created by the treatment",
   "setting": "68 F, EMS to the resuscitation bay, a funeral in the story",
   "feel": "tender",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Printed in docs/generated/case-index.md so a new case can say how it differs. Descriptive, not clinical: no physician has reviewed the wording."
 },
}

PATIENT = {
 "age": 68,
 "sex": "female",
 "weight_kg": 64,
 "background": (
   "Retired schoolteacher. Treated high blood pressure and high cholesterol, on amlodipine "
   "and atorvastatin. No known heart disease and no murmur ever mentioned. Never smoked. "
   "Father had a heart attack at 70. No allergies. Gallbladder removed twenty years ago. "
   "Three children. Walks two miles a day and had a routine checkup in the spring.\n\n"
   "Her husband of 41 years died five days ago. She has barely eaten or drunk since. At "
   "the reception after his funeral, about an hour ago, she developed crushing central "
   "chest pain going into her left arm and jaw, with sweating, nausea and breathlessness. "
   "Her daughter thinks it is grief and exhaustion and says so to everyone."),
 "presenting_vitals_source": "Inherited from phase 'presentation'.",
 "presenting_appearance": (
   "A woman in a black dress, sitting upright on the stretcher, pale and sweating, one fist "
   "against her breastbone. She answers in short sentences. Her daughter is beside her "
   "holding her other hand."),
 "ems_handover_text": (
   "Sixty-eight year old woman, crushing central chest pain for about an hour, came on at "
   "her husband's funeral reception. Radiates to the left arm and jaw, with sweating and "
   "nausea. Hypertension and high cholesterol. Rate 115, pressure 96 over 60 with us. We "
   "gave nothing, she didn't have a line when we left. Daughter thinks it's stress."),
 "arrival_handover": (
   "Sixty-eight year old lady, chest pain for about an hour, came on at her husband's "
   "funeral. Her daughter's with her and says she's been in a state all week."),
 "handover_authoring_note": (
   "Section 3.2. Two sentences, 29 words. No vital sign, no past history, no medication, "
   "no pertinent negative. It carries the misleading frame on purpose: the crew repeats "
   "the daughter's explanation, as crews do."),
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp, distress, alert,
          transitions, terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": "normal", "pupil_reactivity": "reactive"},
      "rhythm": "regular",
      "ecg": {"pattern": "organised", "p_waves": True, "qrs_ms": 92, "qtc_ms": 470,
              "st_mv": 0.1,
              "author_note": ("Sinus tachycardia, narrow complexes. The report gives 1 mm of "
                              "ST elevation in lead II, so the monitor lead is drawn with "
                              "0.1 mV. Model output.")},
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}

FLUID = "flag fluids_given set"
VASO = "flag vasoconstrictor_running set"
TREATED = FLUID + " AND " + VASO
# An inotrope that has been started and not stopped. Flags are permanent, so "stopped" is
# its own flag and "active" is the pair.
# Positive guard only: the validator reads a negated flag in a timed guard as a
# deterioration on inaction. So this guard cannot see a stop. Known limits, pinned by
# tests and listed in TAKO-SEED.md section 7: an inotrope stopped inside the ten-second
# window still sends her to shock_worse, and an inotrope started less than ten seconds
# before a transition to steadied does not prevent it.
ACTIVE = "flag inotrope_given set"
CARDS = "flag cardiology_called set"

TAKEOVER_NOTE = (
  "Cardiology came to the bedside and took over. They stopped anything with inotropic "
  "effect, gave a small fluid bolus because her lungs were clear, and started a pure "
  "vasoconstrictor.\n\n"
  "Calling for help was the right move and it is what you would do. The reasoning to take "
  "from it: the base of her heart is squeezing hard into a narrowed outflow tract. Anything "
  "that makes the heart squeeze harder or faster, or empties it, tightens the obstruction. "
  "Filling it and raising the resistance it pumps against opens it.")
TAKEOVER_RATIONALE = (
  "Added on Aakash Setty's instruction of 6 October 2026: the cardiologist can take over "
  "and help, because this is a hard case. Ninety seconds after a call that is made, or was "
  "already made, when the pressure is low. A delayed consequence of the learner's own "
  "action, so the five-second floor applies. Ninety seconds leaves a learner who wants to "
  "act on the cardiologist's advice time to do it first. The clock belongs to one phase: a "
  "call made on arrival starts counting again when the pressure falls. Model output for "
  "the number.")

PHASES = [
 phase("presentation",
   "Chest pain with ST elevation, borderline pressure",
   "on arrival",
   "In pain, sweating, talking. Anterior ST elevation. Pressure 96 over 60 with a new harsh "
   "systolic murmur and clear lungs. The obstruction is already there and has not yet "
   "declared itself.",
   115, 96, 60, 22, 96, 36.9, 2, 0,
   [HANDOFF_T,
    {"when": ACTIVE,
     "after_seconds": 10, "measured_from": "guard_true", "to": "shock_worse",
     "narration": ("She's worse since that inotrope went in. Her rate is up, her pressure "
                   "is down and she's confused."),
     "debrief_note": (
       "An inotrope made her worse within seconds. Her ventricle is weak at the apex and "
       "overactive at the base. Driving it harder narrowed the outflow tract further, and "
       "the faster rate left it less time to fill.\n\n"
       "This is the reflex the case exists to interrupt. A low pressure with a poor "
       "ejection fraction usually gets an inotrope. Here the murmur was the warning that "
       "the usual answer was wrong."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. Catecholamine inotropes worsen "
       "dynamic outflow obstruction by physiological reasoning and consensus. The size and "
       "speed are teaching choices. Model output.")},
    {"when": "flag nitrate_given set",
     "after_seconds": 10, "measured_from": "guard_true", "to": "obstructed",
     "narration": ("Her pressure has dropped since that vasodilator and her rate is up. "
                   "She says she feels faint."),
     "debrief_note": (
       "A nitrate dropped her pressure. Nitrates lower the filling of the heart and the "
       "resistance it pumps against. In outflow obstruction a smaller, emptier ventricle "
       "obstructs more.\n\n"
       "The warning was there before the drug: a pressure of 96 over 60 and a new murmur. "
       "A borderline pressure is a reason to hold a nitrate in any chest pain patient."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. She would have reached this "
       "phase anyway at 180 seconds. The nitrate brings it forward and gives it a cause. "
       "Model output.")},
    {"when": ACTIVE + " OR flag nitrate_given set",
     "after_seconds": 180, "measured_from": "phase_entry", "to": "obstructed",
     "narration": ("Her pressure has fallen and her rate is up. She's gone gray and I can "
                   "hear that murmur from here."),
     "debrief_note": (
       "Her pressure fell at the moment this illness makes it fall. A nitrate or an "
       "inotrope had been given seconds before, and what that drug does to an obstructed "
       "outflow tract is described under the drug."),
     "author_rationale": (
       "Added on 7 October 2026 to close a race between timed rules (authoring 5.4). A "
       "nitrate or an inotrope given less than ten seconds before the scripted fall, with "
       "fluid and a vasoconstrictor already running, used to send her straight to steadied "
       "with the wrong drug's effect on the monitor and a nurse line that said her pressure "
       "was holding. Now the fall happens first and the wrong drug acts from the "
       "obstructed phase, as it does at every other time. Same clock as the two rules "
       "below, so the owner's 180 seconds is unchanged. A positive guard, so it asks for "
       "no prompt. Model output.")},
    {"when": TREATED,
     "after_seconds": 180, "measured_from": "phase_entry", "to": "steadied",
     "narration": ("Her pressure is holding on the vasoconstrictor and her rate has come "
                   "down."),
     "debrief_note": (
       "The fall in pressure that this illness produces arrived and was already treated, "
       "because fluid and a vasoconstrictor were running. Acting on the murmur and the "
       "echo before the pressure fell is the best version of this case."),
     "author_rationale": (
       "Same clock as the unguarded rule below, so the obstruction declares itself at one "
       "moment whatever was done. Model output.")},
    {"when": None,
     "after_seconds": 180, "measured_from": "phase_entry", "to": "obstructed",
     "narration": ("Her pressure has fallen and her rate is up. She's gone gray and I can "
                   "hear that murmur from here."),
     "debrief_note": (
       "Her pressure fell without anything being given. This is the outflow obstruction "
       "declaring itself, and it is not a mistake on your part.\n\n"
       "It is the decision point of the case. She has a weak ventricle, ST elevation and a "
       "low pressure, which looks like cardiogenic shock from a large infarct. The murmur "
       "and the echo say something more specific, and the treatment is different."),
     "author_rationale": (
       "Scheduled natural history, so that every learner meets the obstruction. Three "
       "minutes of case clock. Outflow obstruction is the minority course in takotsubo and "
       "this case makes it happen every time. A teaching choice, approved in outline by "
       "the directing physician. Model output for the number."),
     "unguarded_rationale": (
       "Without this rule a careful learner who never gives a nitrate or an inotrope never "
       "meets the third learning goal. The phase it leads to is recoverable, the nurse "
       "recommends cardiology twenty seconds after it in easy mode and sixty seconds after "
       "it in the default mode, and the cardiologist gives the plan and will take over.")}],
   ),

 phase("obstructed",
   "Outflow obstruction, hypotensive",
   "hypotensive",
   "Mean arterial pressure 61. Gray, lightheaded, still talking. The murmur is louder. "
   "Fluid and a vasoconstrictor together get her out. An inotrope makes her worse.",
   124, 82, 50, 24, 95, 36.9, 2, 0,
   [HANDOFF_T,
    {"when": ACTIVE,
     "after_seconds": 10, "measured_from": "guard_true", "to": "shock_worse",
     "narration": ("She's worse since that inotrope went in. Her rate is up, her pressure "
                   "is down and she's confused."),
     "debrief_note": (
       "An inotrope made her worse. The base of her heart was already squeezing hard into "
       "a narrow outflow tract. More contractility and a faster rate narrowed it further.\n\n"
       "Stop the drug. Then give a small fluid bolus and a vasoconstrictor with no "
       "inotropic effect."),
     "author_rationale": "As for the same rule on arrival. Model output."},
    {"when": TREATED,
     "after_seconds": 10, "measured_from": "guard_true", "to": "steadied",
     "narration": ("That's working. Her pressure is up, her rate is down and the murmur "
                   "is softer."),
     "debrief_note": (
       "Fluid and a vasoconstrictor opened the outflow tract. A fuller ventricle and a "
       "higher resistance to pump against hold the obstruction apart, and the slower rate "
       "gives the heart time to fill.\n\n"
       "This is the reverse of the usual plan for a weak heart. It applies to obstruction "
       "specifically, and it rests on physiology and expert consensus, not trials. She "
       "also had clear lungs. With pulmonary edema the fluid would be wrong."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. Ten seconds compresses a "
       "titration of several minutes. Model output.")},
    {"when": CARDS,
     "after_seconds": 90, "measured_from": "guard_true", "to": "steadied",
     "narration": ("Cardiology is at the bedside and has taken over. They've given a small "
                   "fluid bolus and have a vasoconstrictor running. Her pressure is up and "
                   "her rate is down."),
     "debrief_note": TAKEOVER_NOTE,
     "author_rationale": TAKEOVER_RATIONALE},
    {"when": "NOT " + FLUID + " OR NOT " + VASO,
     "after_seconds": 240, "measured_from": "phase_entry", "to": "shock_untreated",
     "narration": ("She's getting worse. Her rate is up, her pressure is down and she's "
                   "not making sense."),
     "debrief_note": (
       "Her outflow tract stayed obstructed and her output kept falling. The base of her "
       "heart was squeezing hard into a narrowed outflow tract, and a ventricle that "
       "cannot empty past the obstruction supplies less blood to the brain and to the "
       "heart itself. The fast rate left it less time to fill, and an emptier ventricle "
       "obstructs more.\n\n"
       "A small fluid bolus and a vasoconstrictor with no inotropic effect, given "
       "together, would have opened it. Either one alone was not enough.\n\n"
       "If you were unsure what to do, that is reasonable. This is a hard presentation. "
       "Calling cardiology was always available, and the nurse suggested it."),
     "author_rationale": (
       "Deterioration on inaction. The nurse recommends cardiology at 20 seconds, fluid at "
       "45 and a vasoconstrictor at 60. In the default mode those are 60, 135 and 180 "
       "seconds, so all three are spoken before this rule fires at 240 (authoring 9.7). "
       "Four minutes is a drafting judgment.")}],
   ),

 phase("shock_untreated",
   "Worsening shock, obstruction untreated",
   "worsening shock",
   "Mean arterial pressure 51, confused, cold. Reached from the obstructed phase after "
   "four minutes without both fluid and a vasoconstrictor. No clock leaves it.",
   138, 70, 42, 28, 93, 36.8, 3, 1,
   [HANDOFF_T,
    {"when": ACTIVE,
     "after_seconds": 10, "measured_from": "guard_true", "to": "shock_worse",
     "narration": ("That inotrope hasn't helped. She's still in shock and the murmur is "
                   "louder than ever."),
     "debrief_note": (
       "An inotrope was started in a patient already in shock from outflow obstruction. "
       "It could not help, and it has to come off before anything else will work."),
     "author_rationale": "A delayed consequence of the learner's own action. Model output."},
    {"when": TREATED,
     "after_seconds": 10, "measured_from": "guard_true", "to": "steadied",
     "narration": ("She's coming back. Her pressure is up, her rate is down and she knows "
                   "where she is."),
     "debrief_note": (
       "Fluid and a vasoconstrictor opened the outflow tract, even this late. A fuller "
       "ventricle and a higher resistance to pump against hold the obstruction apart, and "
       "the slower rate gives the heart time to fill.\n\n"
       "The same pair given in the first four minutes after her pressure fell would have "
       "kept her out of worsening shock. One of the two alone does not do it."),
     "author_rationale": "A delayed consequence of the learner's own action. Model output."},
    {"when": CARDS,
     "after_seconds": 90, "measured_from": "guard_true", "to": "steadied",
     "narration": ("Cardiology is at the bedside and has taken over. They've given a small "
                   "fluid bolus and have a vasoconstrictor running. Her pressure is up and "
                   "her rate is down."),
     "debrief_note": TAKEOVER_NOTE,
     "author_rationale": TAKEOVER_RATIONALE}],
   authoring_note="Same numbers as shock_worse. Two phases because the exits differ.",
   ),

 phase("shock_worse",
   "Worse on an inotrope",
   "worsening shock",
   "Mean arterial pressure 51, confused, cold, on an inotrope that is tightening the "
   "obstruction. No clock leaves it. Stopping the inotrope and giving fluid and a "
   "vasoconstrictor get her out, and so does cardiology.",
   138, 70, 42, 28, 93, 36.8, 3, 1,
   [HANDOFF_T,
    {"when": "flag inotrope_stopped set AND " + TREATED,
     "after_seconds": 10, "measured_from": "guard_true", "to": "steadied",
     "narration": ("She's coming back now that inotrope is off. Her pressure is up, her "
                   "rate is down and she knows where she is."),
     "debrief_note": (
       "You stopped the drug that was making her worse and replaced it with fluid and a "
       "vasoconstrictor. Recognizing that a treatment is hurting the patient and "
       "withdrawing it is a skill, and you used it."),
     "author_rationale": "A delayed consequence of the learner's own action. Model output."},
    {"when": CARDS,
     "after_seconds": 90, "measured_from": "guard_true", "to": "steadied",
     "narration": ("Cardiology is at the bedside and has taken over. The inotrope is off, "
                   "they've given a small fluid bolus and a vasoconstrictor is running. Her "
                   "pressure is up and her rate is down."),
     "debrief_note": TAKEOVER_NOTE,
     "author_rationale": TAKEOVER_RATIONALE}],
   authoring_note=(
     "No clock leaves this phase and the case has no arrest. Stopping the inotrope alone "
     "shows as eight points of pressure through a vital effect and does not change the "
     "phase. She leaves once it is stopped and fluid and a vasoconstrictor are running."),
   ),

 phase("steadied",
   "Steadied, ready for the catheterization laboratory",
   "steadied",
   "Awake, pain easing, mean pressure 75 on a vasoconstrictor, murmur softer. The intended "
   "endpoint. She still needs an angiogram, because nothing done here has excluded an "
   "occluded artery.",
   104, 100, 62, 20, 97, 36.9, 1, 0,
   [HANDOFF_T],
   ),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   104, 100, 62, 20, 97, 36.9, 0, 0, [], terminal=True,
   inherit_vitals=True,
   ),
]
