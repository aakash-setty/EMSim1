"""TIDE part 1: identity, patient, phases.

Severe community-acquired pneumonia with septic shock in a 58-year-old man. He needs oxygen up
to high flow, an antibiotic, fluid and then a vasopressor. Once his pressure is held he tires on
high flow, however well he was treated, and needs a tube, with the vasopressor running first.

Drafted by a language model on 4 November 2026 from a case structure Aakash Setty supplied and
his answers of the same day. No physician has reviewed this pack. TIDE-SEED.md says what a
person decided and which sources were opened.
"""

META = {
 "case_number": 9,
 "working_title": "58-year-old man, four days of fever and cough, now short of breath",
 "chief_complaint_patient_voice": "I can't... catch my breath.",
 "final_diagnosis": (
   "Severe community-acquired pneumonia (pneumococcal by urine antigen), multilobar, with "
   "sepsis-induced hypoperfusion progressing to septic shock that needs a vasopressor, and "
   "acute hypoxemic respiratory failure that fails high-flow oxygen and needs intubation."),
 "target_level": ["medical_student", "intern", "junior_resident"],
 "estimated_runtime_seconds": 720,
 "learning_objectives": [
   "Recognize severe community-acquired pneumonia with sepsis and hypoperfusion, and send the patient to the ICU.",
   "Escalate oxygen in steps to high flow or NIV, and judge support by the work of breathing and the trend, not by the saturation alone.",
   "Give an antibiotic regimen for severe CAP early, give crystalloid, and start a vasopressor when the fluid does not hold the pressure.",
   "Recognize failure of noninvasive support and intubate before the patient tires to a crash.",
   "Have a vasopressor running before induction, and preoxygenate with positive pressure.",
   "Know that ventilation is set from predicted body weight and that a paralyzed patient needs sedation (debrief only in this version).",
 ],
 "teaching_frame": (
   "Two moments carry the case. The first is when the fluid has stopped working: his pressure "
   "rises for a few minutes after a bolus and drifts back, and the answer is a vasopressor, not "
   "more fluid. The second is when a saturation of 88 on high flow is a patient who is failing. "
   "He is confused, breathing paradoxically, and the number still looks almost acceptable."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Resuscitation bay with high-flow oxygen, NIV, a ventilator, video laryngoscopy and "
     "ultrasound. Intensive care on site. Peripheral norepinephrine is allowed by local policy."),
 },
 "arrival": {
   "mode": "triage",
   "location": "resuscitation_bay",
   "line": "Walked in with his wife and was brought straight through from triage to the resuscitation bay.",
 },
 "complaint": "Fever, cough and breathlessness",
 "category": "Cardiopulmonary",
 "library": {
   "tempo": "minutes: shock on a clock, then breathing on an openly compressed clock",
   "uncertainty": "when the fluid has stopped working, and when noninvasive support has failed",
   "right_answer": "do more, at the right moment, and support the circulation before the tube",
   "danger": "behind a reassuring saturation, then created by the treatment",
   "setting": "58 M, walked in with his wife, triage to the resuscitation bay",
   "feel": "urgent, then a slow dread",
   "note": "The six variety dimensions of docs/case-design-guide.md, as this case reads. Descriptive, not clinical. Model wording, not reviewed.",
 },
}

PATIENT = {
 "age": 58,
 "sex": "male",
 "weight_kg": 95,
 "background": (
   "Fifty-eight. Hypertension and type 2 diabetes, on lisinopril and metformin. Smokes about "
   "three quarters of a pack a day since he was eighteen, about thirty pack-years. Never told "
   "he has COPD. No immune problems, no steroids, no hospital stay or antibiotics in the last "
   "three months, no prior MRSA or Pseudomonas. No allergies. Works for the city water "
   "department. Lives with his wife. Full code.\n\n"
   "Fever and shaking chills since Saturday, four days ago, with a cough that brought up rusty "
   "brown phlegm and a sharp right-sided pain when he breathes in. Breathless since last night "
   "and much worse today. His wife drove him in."),
 "predicted_body_weight_note": (
   "Reviewer note. Height 178 cm, kept here because the engine reads no height field. "
   "Predicted body weight about 73 kg (50 + 0.91 x (178 - 152.4)). Six mL/kg "
   "is about 440 mL. BMI 30.0. Model arithmetic."),
 "presenting_vitals_source": "Inherited from phase 'arrival'.",
 "presenting_appearance": (
   "A heavy-set man sitting forward on the stretcher with his hands on his knees, flushed and "
   "sweating, speaking three or four words at a time. His wife is beside him."),
 "ems_handover_text": (
   "Fifty-eight year old man, four days of fever, cough with rusty sputum and right-sided "
   "pleuritic pain, breathless since last night. Triage saturation 85 percent on room air, rate "
   "32, pulse 118, pressure 104 over 60, temperature 39.2."),
 "arrival_handover": (
   "Fifty-eight year old man with four days of fever and cough, much more short of breath since "
   "last night, his wife drove him in. Triage had him at eighty-five percent on room air, so I "
   "brought him straight back."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 40 words. The saturation is a past measurement and agrees with "
   "the first phase. No diagnosis, no past history, no medication, no sputum color (an "
   "interview finding)."),
 "avatar": {"build": "obese"},
 "avatar_note": "BMI 30.0 at 95 kg and 178 cm. Drawn as the heavier build.",
}

# ------------------------------------------------------------------ conditions
INTUB = "flag intubated set"
DRIP = "flag pressor_running set"
FLUID = "flag fluid_given set"
HIGH = "(flag o2_hfnc set OR flag o2_niv set)"
MASK = "(flag o2_nrb set OR flag o2_nc set)"

ECG_SINUS = ("Sinus tachycardia. PR, QRS and QTc match the twelve-lead tracing of the phase "
             "(media/README.md). Model output.")


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp, distress, alert,
          transitions, terminal=False, ecg=None, pupils=("normal", "reactive"), **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": pupils[0], "pupil_reactivity": pupils[1]},
      "rhythm": "regular",
      "ecg": ecg or {"pattern": "organised", "p_waves": True, "pr_ms": 140, "qrs_ms": 84, "qtc_ms": 430,
                     "author_note": ECG_SINUS},
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}

TUBE_OK = {"when": INTUB + " AND " + DRIP, "to": "ventilated",
           "author_rationale": ("Intubated with a vasopressor drip running. The drip carries him "
                                "through induction with a brief dip (an effect on the tube). "
                                "Owner decision B4, 4 November 2026.")}
TUBE_BAD = {"when": INTUB, "to": "post_induction_collapse",
            "author_rationale": (
              "Intubated with no vasopressor running. Induction and positive pressure remove the "
              "tone and venous return he was living on, and in septic shock the pressure falls. "
              "Applied in every phase, MAP 75 included, by owner decision B4 of 4 November 2026. "
              "Post-intubation hypotension is common but not certain. The case makes it certain, "
              "and the nurse and the debrief say it was a risk taken (open question 7).")}

SEVERE = ["severe_shock"]

COMPRESS = "We're moving the clock faster here. Over what would really be a few hours, "

PHASES = [
 phase("arrival",
   "Severe pneumonia with sepsis, pressure still held",
   "on arrival",
   "The first two minutes. The same patient as presentation, with the same findings. It exists "
   "only for the nurse's timing: she asks about oxygen at 1:00 in the default mode and nothing "
   "else until 4:00 (owner, 5 November 2026).",
   118, 104, 60, 32, 85, 39.2, 2, 0,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": FLUID, "to": "fluid_response",
     "author_rationale": "A first bolus lifts his pressure for a few minutes. Model output."},
    {"when": None, "after_seconds": 120, "measured_from": "phase_entry", "to": "presentation",
     "author_rationale": (
       "No change in the patient. The phase ends so the fluid, support and antibiotic prompts "
       "start counting from 2:00 instead of from arrival (owner, 5 November 2026)."),
     "unguarded_rationale": (
       "Nothing about him changes here, so the move cannot depend on anything the learner "
       "does. Its only effect is on when the nurse speaks."),
     "silent_rationale": (
       "The patient, the monitor and the findings are the same on both sides, so there is "
       "nothing for the nurse to say. The owner asked for no line between the oxygen question "
       "at 1:00 and the next one at 4:00 (5 November 2026).")}]),

 phase("presentation",
   "Severe pneumonia with sepsis, pressure still held",
   "on arrival",
   "Tripoding, three or four words a breath, hot and flushed. MAP 75, lactate 3.8, SpO2 85 on "
   "room air. Hypotension is coming. Fluid, oxygen and an antibiotic now.",
   118, 104, 60, 32, 85, 39.2, 2, 0,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": FLUID, "to": "fluid_response",
     "author_rationale": "A first bolus lifts his pressure for a few minutes. Model output."},
    {"when": DRIP, "after_seconds": 240, "measured_from": "phase_entry", "to": "on_pressor",
     "narration": "He's still hot and flushed, and the drip is holding his pressure.",
     "debrief_note": (
       "His pressure was falling on its own, and the vasopressor you had already started "
       "held it. He never had a bolus. With a small, collapsing vena cava he needed fluid "
       "as well. [UNVERIFIED: SSC 2026, read through summaries]"),
     "author_rationale": (
       "Outcome chosen at a scheduled time, above the deterioration below with the same "
       "after_seconds. Natural history of sepsis-induced hypotension met by a drip already "
       "running. Model output.")},
    {"when": "NOT " + FLUID, "after_seconds": 240, "measured_from": "phase_entry",
     "to": "low_pressure",
     "narration": "His knees have gone blotchy and his pressure has dropped.",
     "debrief_note": (
       "Without fluid his pressure fell below a mean of 65 and his knees mottled. He was "
       "tachycardic, hot, with a lactate near 4 and a vena cava that collapsed with each "
       "breath, and hypotension was on its way. Fluid would have delayed it, not prevented "
       "it. Six minutes from arrival stand for much longer. [UNVERIFIED: SSC 2026, read through "
       "summaries]"),
     "author_rationale": (
       "Deterioration on inaction. Sepsis-induced hypotension in severe pneumonia over hours, "
       "compressed to six minutes from arrival (two in arrival, four here). The guard is the missing fluid, which is the treatment "
       "the prompt asks for. Model output.")}]),

 phase("fluid_response",
   "Transient response to the first bolus",
   "after fluid",
   "MAP 71 after the first bolus. It will not last: this phase always ends in 150 s. Reassess, "
   "give the antibiotic if missing, line up a vasopressor.",
   112, 96, 58, 32, 85, 39.2, 2, 0,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": DRIP, "after_seconds": 150, "measured_from": "phase_entry", "to": "on_pressor",
     "narration": "His pressure started to drift, and the drip has caught it.",
     "debrief_note": (
       "The response to fluid faded, as it does in this kind of shock, and the vasopressor "
       "already running held him. Starting it early, before the pressure fell again, is "
       "defensible. [UNVERIFIED: SSC 2026, read through summaries]"),
     "author_rationale": (
       "Outcome chosen at a scheduled time, above the unguarded rule with the same "
       "after_seconds. Model output.")},
    {"when": None, "after_seconds": 150, "measured_from": "phase_entry", "to": "low_after_fluid",
     "narration": "He looked better for a few minutes, but his pressure is drifting back down.",
     "debrief_note": (
       "The bolus lifted his pressure and it drifted back. A transient response is not "
       "resolution. When fluid stops holding the pressure, the next step is a vasopressor, "
       "and peripheral norepinephrine is fine while a central line is not in. [UNVERIFIED: "
       "SSC 2026 and Munroe et al. 2023, read through summaries or from the owner's "
       "structure]"),
     "author_rationale": "Scheduled natural history. Model output.",
     "unguarded_rationale": (
       "The fluid response in this phenotype is transient whatever else is given. The owner's "
       "structure scripts the drift. A second bolus does not stop it.")}]),

 phase("low_pressure",
   "Sepsis-induced hypotension, no fluid yet",
   "pressure low",
   "MAP 61, mottled knees, no urine. Fluid now. A vasopressor if the pressure does not respond.",
   128, 84, 50, 32, 85, 39.2, 2, 0,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": DRIP, "to": "on_pressor",
     "author_rationale": "A vasopressor holds the pressure. Fluid is still owed. Model output."},
    {"when": FLUID, "to": "fluid_response",
     "author_rationale": "The first bolus, given late, lifts him for a few minutes. Model output."},
    {"when": "NOT " + FLUID, "after_seconds": 150, "measured_from": "phase_entry",
     "to": "worsening_shock", "flags_set": SEVERE,
     "narration": "The blotching has spread up his thighs and his hands are cold. He's drowsy now.",
     "debrief_note": (
       "With no fluid and no vasopressor his shock progressed: mottling to the thighs, cold "
       "hands, a falling level of consciousness, and a lactate of 5.4. Two and a half minutes "
       "stands for much longer. [UNVERIFIED: model judgment of the timescale]"),
     "author_rationale": (
       "Deterioration on inaction. Untreated septic shock progresses. Grants severe_shock, which "
       "keys the lactate from here on. Model output.")}]),

 phase("low_after_fluid",
   "Hypotension again after a transient fluid response",
   "pressure low again",
   "MAP 62 with fluid already given. The answer is a vasopressor, not more fluid.",
   120, 86, 50, 32, 85, 39.2, 2, 0,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": DRIP, "to": "on_pressor",
     "author_rationale": "A vasopressor holds the pressure. Model output."},
    {"when": "NOT " + DRIP, "after_seconds": 150, "measured_from": "phase_entry",
     "to": "worsening_shock", "flags_set": SEVERE,
     "narration": "The blotching has spread up his thighs and his hands are cold. He's drowsy now.",
     "debrief_note": (
       "His pressure stayed below a mean of 65 after fluid and nothing was started for it. His "
       "shock progressed: mottling to the thighs, cold hands, a falling level of consciousness "
       "and a lactate of 5.4. When fluid has not held the pressure, a vasopressor should not "
       "wait, and a peripheral line is enough to start one. [UNVERIFIED: SSC 2026, read "
       "through summaries]"),
     "author_rationale": (
       "Deterioration on inaction. The owner's structure gives five minutes from persistent "
       "hypotension to progressive shock. Compressed to 150 s. Model output.")}]),

 phase("worsening_shock",
   "Progressive septic shock",
   "pressure very low",
   "MAP 51, mottled to the thighs, cool, drowsy (GCS 13). Vasopressor now.",
   140, 72, 40, 36, 83, 39.0, 2, 1,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": DRIP, "to": "on_pressor",
     "author_rationale": "A late vasopressor still holds him. severe_shock stays set. Model output."},
    {"when": "NOT " + DRIP, "after_seconds": 150, "measured_from": "phase_entry", "to": "arrest",
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Accepted by the owner with the clocks of the case map, 4 November 2026. Untreated "
       "progressive septic shock ends in arrest. The prompt for a vasopressor comes at 30 s "
       "(90 s in the default mode) with an escalation."),
     "narration": "I can't feel a pulse.",
     "debrief_note": (
       "His shock was never treated with a vasopressor and he arrested. Fluid alone could not "
       "hold this pressure. [UNVERIFIED: model judgment of the timescale]"),
     "author_rationale": (
       "Deterioration on inaction to a terminal phase. Model output, accepted by the owner as "
       "part of the clocks on 4 November 2026.")}]),

 phase("on_pressor",
   "Septic shock, pressure held on a vasopressor",
   "pressure holding",
   "MAP 70 on a drip. Antibiotic if missing, steroid, ICU. His breathing is the next problem: "
   "this phase always ends in 180 s.",
   110, 94, 58, 32, 85, 39.0, 2, 0,
   [HANDOFF_T,
    {"when": INTUB, "to": "ventilated",
     "author_rationale": "Early intubation with the drip running. Accepted. Model output."},
    {"when": HIGH, "after_seconds": 180, "measured_from": "phase_entry", "to": "failing_support",
     "narration": (COMPRESS + "he's tired on the support. RT has his oxygen up to a hundred "
                   "percent, and he's barely answering me."),
     "debrief_note": (
       "He failed noninvasive support however well he was treated. That is this patient, not "
       "a verdict on your care. Real failure on high flow develops over hours: the ROX index "
       "was validated at two, six and twelve hours. The case moves the clock faster. "
       "[UNVERIFIED: Roca et al. 2019, from memory and the owner's structure]"),
     "author_rationale": (
       "Scheduled natural history, with the narration chosen by the device in use. Owner "
       "decision of 4 November 2026: the patient fails noninvasive support whatever is done, "
       "and the compression is said aloud (B1).")},
    {"when": MASK, "after_seconds": 180, "measured_from": "phase_entry", "to": "failing_support",
     "narration": (COMPRESS + "he's tired, even with the oxygen as high as that mask goes. "
                   "He's barely answering me."),
     "debrief_note": (
       "He tired on a mask. He would have tired on high flow too, but with less reserve here, "
       "and severe hypoxemia in pneumonia is what high flow or NIV is for. The case moves the "
       "clock faster than real life. [UNVERIFIED: RENOVATE, read through summaries]"),
     "author_rationale": "As above, for a mask or a cannula. Model output."},
    {"when": None, "after_seconds": 180, "measured_from": "phase_entry", "to": "failing_support",
     "narration": (COMPRESS + "he's tired. He's still on room air and he's barely answering me."),
     "debrief_note": (
       "He was never given oxygen. He was always going to tire, and he did it with nothing to "
       "spare. The case moves the clock faster than real life. [UNVERIFIED: model judgment]"),
     "author_rationale": "Scheduled natural history. Model output.",
     "unguarded_rationale": (
       "Owner decision of 4 November 2026: failure of noninvasive support is scripted and "
       "arrives on the same clock whatever the device (B5).")}]),

 phase("failing_support",
   "Failing noninvasive support",
   "working harder",
   "Confused, paradoxical breathing, head bobbing, one or two words. On HFNC at FiO2 1.0, SpO2 "
   "88 and RR 38 (ROX 2.3). Decide to intubate, with the drip running and positive-pressure "
   "preoxygenation.",
   112, 92, 56, 40, 81, 38.8, 3, 1,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": "NOT " + INTUB, "after_seconds": 150, "measured_from": "phase_entry", "to": "tiring",
     "narration": "His breathing has slowed right down and he's hard to rouse.",
     "debrief_note": (
       "He tired to the point of hypercapnia and a falling heart rate before anyone decided "
       "to intubate. A saturation of 88 on a hundred percent, a rate near 40, confusion and "
       "paradoxical breathing were the signal. Intubation chosen before that point is safer "
       "than intubation near arrest, though the evidence for timing is observational. "
       "[UNVERIFIED: Roca et al. 2019 and the observational studies in the owner's "
       "structure, not opened]"),
     "author_rationale": (
       "Deterioration on inaction. The owner's structure gives four minutes from failing "
       "support to pre-arrest fatigue. Compressed to 150 s. Model output.")}]),

 phase("tiring",
   "Pre-arrest respiratory fatigue",
   "breathing slowing",
   "Slow shallow breathing, bradycardic, obtunded (GCS 9). Intubate now.",
   56, 84, 48, 14, 76, 38.6, 1, 2,
   [HANDOFF_T, TUBE_OK, TUBE_BAD,
    {"when": "NOT " + INTUB, "after_seconds": 120, "measured_from": "phase_entry", "to": "arrest",
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Accepted by the owner with the clocks of the case map, 4 November 2026. Hypercapnic and "
       "hypoxemic fatigue ends in arrest. The prompt to intubate comes at 30 s (90 s in the "
       "default mode)."),
     "narration": "I can't feel a pulse.",
     "debrief_note": (
       "He arrested from respiratory fatigue. The tube came too late or not at all. "
       "[UNVERIFIED: model judgment of the timescale]"),
     "author_rationale": "Deterioration on inaction to a terminal phase. Model output."}],
   ecg={"pattern": "organised", "p_waves": True, "pr_ms": 150, "qrs_ms": 88, "qtc_ms": 430,
        "author_note": ("Sinus bradycardia from hypoxemia and hypercapnia. Intervals match the "
                        "tracing of this phase (media/README.md). Model output.")}),

 phase("post_induction_collapse",
   "Post-induction hypotension, no vasopressor running",
   "after the tube",
   "Intubated without a vasopressor running. MAP 50. A drip now. A push-dose bolus bridges but "
   "does not leave the phase.",
   128, 70, 40, 24, 90, 38.8, 0, 3,
   [HANDOFF_T,
    {"when": DRIP, "to": "ventilated",
     "author_rationale": (
       "A vasopressor drip started after the tube. Entered only without one, so the exit is "
       "not satisfied by anything he had on the way in. Model output.")},
    {"when": "NOT " + DRIP, "after_seconds": 120, "measured_from": "phase_entry", "to": "arrest",
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Accepted by the owner with the clocks of the case map, 4 November 2026. The prompt for a "
       "vasopressor comes at 30 s (90 s in the default mode)."),
     "narration": "I can't feel a pulse.",
     "debrief_note": (
       "His pressure fell after induction and no vasopressor drip followed. He arrested. A "
       "push-dose bolus buys minutes. A drip holds him. [UNVERIFIED: model judgment]"),
     "author_rationale": "Deterioration on inaction to a terminal phase. Model output."}],
   ventilated=True),

 phase("ventilated",
   "Intubated and ventilated, pressure held",
   "on the ventilator",
   "On the ventilator with a drip running. Sedation, film, gas, ICU, handoff.",
   112, 94, 58, 24, 95, 38.8, 0, 3,
   [HANDOFF_T],
   ventilated=True),

 phase("arrest",
   "Cardiac arrest",
   "no pulse",
   "Terminal. Pulseless electrical activity from untreated shock, respiratory fatigue, or "
   "collapse after the tube with no vasopressor.",
   30, 44, 24, 0, 58, 38.4, 0, 3,
   [], terminal=True, pupils=("large", "fixed"),
   timeout_reason=(
     "He arrested. Either his shock went untreated, or he tired without a tube, or his "
     "pressure fell after intubation with no vasopressor running."),
   ecg={"pattern": "organised", "p_waves": False, "qrs_ms": 160, "qtc_ms": 480,
        "verify": ("A slow wide idioventricular rhythm with no output, drawn as pulseless "
                   "electrical activity, as MGCA's arrest. Model output. [UNVERIFIED]")}),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   112, 94, 58, 24, 95, 38.8, 0, 0,
   [], terminal=True, inherit_vitals=True),
]
