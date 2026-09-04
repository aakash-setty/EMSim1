"""AFRVR part 1: identity, patient, phases."""

META = {
 "working_title": "Sixty-eight year old man, palpitations and breathlessness, brought in by EMS",
 "chief_complaint_patient_voice": "My heart won't stop racing and I can't get my breath.",
 "final_diagnosis": ("Atrial fibrillation with rapid ventricular response, complicated by acute "
   "decompensated heart failure with a newly recognised reduced ejection fraction and cardiogenic "
   "pulmonary oedema. The arrhythmia and the ventricular dysfunction are each plausibly cause and "
   "consequence of the other, and the case does not require the learner to decide which came first."),
 "target_level": ["intern", "junior_resident", "senior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "Recognise atrial fibrillation with a rapid ventricular response on a twelve-lead ECG and separate it from the other narrow-complex tachycardias.",
   "Identify acute decompensated heart failure and cardiogenic pulmonary oedema in a patient with no prior diagnosis of either.",
   "Use cardiac and lung point-of-care ultrasound to establish reduced left ventricular systolic function at the bedside, and treat that finding as the pivot the rest of the case turns on.",
   "Select a rate-control strategy that accounts for reduced systolic function, and state why a non-dihydropyridine calcium channel blocker is the wrong agent once the ejection fraction is known.",
   "Sequence non-invasive positive pressure ventilation and diuresis alongside rate control rather than after it, and recognise that a lower heart rate is not by itself a resuscitated patient.",
   "Assess thromboembolic risk in new atrial fibrillation and initiate anticoagulation, including the reason the uncertain duration of the arrhythmia matters if cardioversion is being considered.",
   "Reassess after treatment against clinical response rather than against a target number, and disposition to a setting that can continue what the department started.",
 ],
 "teaching_frame": ("Two problems presenting as one. The rate is what the learner sees, and the "
   "ventricle is what decides the treatment. The case is built so that the correct management of "
   "the visible problem changes once the invisible one is found, which is what the POCUS is for."),
 "care_setting": {
   "label": "Quaternary care, Level 1 trauma centre",
   "detail": ("Adult emergency department. Full laboratory, imaging and blood bank on site. "
     "Cardiology and critical care are available in house at all hours, and there are both "
     "intensive care and step-down beds. Nothing in this case is limited by resources, which "
     "matters because the disposition question is about what the receiving unit must be able to "
     "do rather than about what the hospital has."),
   "provenance": ("Setting is a deployment property, not a clinical fact. A version of this case "
     "written for a hospital with no non-invasive ventilation on the wards has a different right "
     "answer to the disposition question and the same right answer to everything else."),
 },
 "arrival": {
   "mode": "ems",
   "location": "resuscitation_bay",
   "line": "Brought in by EMS from home. Handover given on arrival in the resuscitation bay.",
 },
 "complaint": "Palpitations and breathlessness",
 "category": "Cardiovascular",
}

PATIENT = {
 "age": 68,
 "sex": "male",
 "weight_kg": 84,
 "background": (
   "Hypertension, type 2 diabetes mellitus, and coronary artery disease documented on a "
   "computed tomography coronary angiogram three years ago with moderate non-obstructive "
   "disease and no prior myocardial infarction. No previously documented atrial fibrillation "
   "and no previously documented heart failure; he has never had an echocardiogram. He is on "
   "no anticoagulant and no rate-controlling agent. Home medications: lisinopril 20 mg daily, "
   "atorvastatin 40 mg nightly, metformin 1000 mg twice daily. Ex-smoker, fifteen pack-years, "
   "stopped in his forties. Drinks two or three beers at the weekend and had four or five at a "
   "family barbecue on Saturday, two days before this presentation. Independent, still working "
   "part time, walks his dog twice a day without stopping."
 ),
 "presenting_vitals_source": ("Inherited from phase 'presentation'. EMS applied no oxygen and "
   "established no intravenous access; the saturation on the splash panel is the one the crew "
   "measured on room air at the house."),
 "presenting_appearance": (
   "An older man sitting upright on the EMS stretcher, awake and visibly anxious, breathing "
   "fast and shallowly with his hands on his thighs. He is still able to complete a sentence "
   "before he has to stop for a breath, and he keeps putting his hand flat on his chest as "
   "though to hold something still."
 ),
 "ems_handover_text": (
   "Sixty-eight year old man, called us this morning. He says his heart has been going since "
   "yesterday afternoon and he has been getting more and more short of breath with it. Daughter "
   "was with him, said he was fine at the weekend and today he had to stop halfway across the "
   "living room. Rate was 150 to 160 on our monitor the whole way in, irregular. Sats were 88 "
   "on room air at the house. Pressure about 130 systolic, stayed there. No chest pain that he "
   "would own up to. We gave him nothing."
 ),
 "arrival_handover": (
   "Sixty-eight year old man, heart's been racing since yesterday and he's got more and more "
   "winded with it. His daughter called us this morning when he had to stop halfway across the "
   "living room."
 ),
}

# ---------------------------------------------------------------- phases
# Every non-terminal phase's oxygen saturation is the UNSUPPORTED baseline. Positive
# pressure adds up to eight points through four staged vital effects, and supplemental
# oxygen adds three or five, so any of these numbers with a mask on will read higher.
# Authoring 6.1: if a phase is rebased wrongly the gain is counted twice.
def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp,
          distress, alert, transitions, terminal=False, pupil="normal", react="reactive", **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": pupil, "pupil_reactivity": react},
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d

HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete"}

RATE_CONTROL_NARRATION = ("His rate's coming down. Still all over the place, but I can actually "
  "count it now.")
RATE_CONTROL_NOTE = (
  "The ventricular rate fell about a minute after the rate-controlling drug was given rather than "
  "the moment it was pushed. None of the three agents this case accepts works instantly: "
  "intravenous metoprolol takes several minutes, amiodarone rather longer, and digoxin considerably "
  "longer than either, so sixty seconds is already a compression rather than a delay. The reason it "
  "is not instant is that a resident who watches the number change on the same click as the "
  "injection learns that rate control is a button, and then gives a second dose thirty seconds "
  "later because the first one appeared not to work.")
RATE_CONTROL_RATIONALE = (
  "AUTHOR: sixty seconds of game time stands in for the several minutes an intravenous "
  "rate-controlling agent actually takes to slow atrioventricular nodal conduction. The number is a "
  "teaching choice about tempo, not a pharmacokinetic claim, and it is the same for all three "
  "agents in the group even though their real onsets differ by an order of magnitude. If the "
  "reviewing physician wants the difference between agents represented, that needs three separate "
  "case actions and three separate transitions, and the cost is that the critical action can no "
  "longer be 'rate control' as a single act.")

PHASES = [
  phase("presentation",
    "Atrial fibrillation with rapid ventricular response and cardiogenic pulmonary oedema",
    "on arrival",
    "Awake, anxious, tachypnoeic and hypoxaemic with an irregularly irregular ventricular rate of "
    "160. Congested and perfusing. The reduced ejection fraction has not yet been found.",
    160, 132, 78, 30, 88, 37.0, 2, 0,
    [
      {"when": "flag intubated set", "to": "intubated",
       "author_note": "Intubation is reachable from anywhere and always leads to the ventilated phase."},
      {"when": "flag on_niv set", "to": "breathing_supported",
       "author_note": "Positive pressure acts within a minute or two on alveolar recruitment and "
                      "work of breathing, so this transition is instantaneous. The saturation it "
                      "buys is authored as a staged vital effect rather than as this phase change, "
                      "so the number climbs rather than jumping."},
      {"when": "flag rate_control_given set", "to": "rate_controlled_congested",
       "after_seconds": 60, "measured_from": "guard_true",
       "narration": RATE_CONTROL_NARRATION,
       "debrief_note": RATE_CONTROL_NOTE,
       "author_rationale": RATE_CONTROL_RATIONALE},
      {"when": "NOT flag on_niv set", "after_seconds": 240, "measured_from": "phase_entry",
       "to": "respiratory_failure",
       "narration": "He's wearing out. He's stopped talking to me and his sat has dropped "
                    "since you came in.",
       "debrief_note": (
         "Four minutes of hypoxaemic respiratory failure at a respiratory rate of thirty, with no "
         "positive pressure and no supplemental oxygen that changes anything, and he tired. This is "
         "the commonest way this case is lost: the rate is the visible abnormality, the learner "
         "spends the first four minutes on it, and the problem that was going to kill him first was "
         "the flooded lung. In acute cardiogenic pulmonary oedema, positive pressure is a treatment "
         "for the oedema and not merely a support measure while you treat something else. It "
         "recruits flooded alveoli, reduces the work of breathing, and by raising intrathoracic "
         "pressure it lowers both preload and left ventricular transmural pressure. Applying it in "
         "the first minutes is what keeps most of these patients off a ventilator. Be honest with "
         "learners about the strength of the claim: meta-analyses report reductions in intubation "
         "rate, and the largest single randomised trial, 3CPO, found no difference in seven-day "
         "mortality or intubation against standard oxygen therapy. The defensible claim is faster "
         "physiological and symptomatic improvement."),
       "author_rationale": (
         "AUTHOR SIGNATURE REQUIRED. The claim is that a sixty-eight year old man in cardiogenic "
         "pulmonary oedema at a saturation of 88 percent on room air, a respiratory rate of thirty "
         "and a ventricular rate of 160 will begin to tire inside four minutes if nothing is done "
         "for his breathing. Four minutes is compressed against real disease tempo in the same way "
         "the five-second laboratory turnaround is; the honest version of the claim is that he is "
         "on a trajectory that ends in intubation and that a case cannot spend twenty minutes "
         "demonstrating it. The deadline is a single integer in this transition and is the "
         "reviewer's to change.")},
      HANDOFF_T,
    ]),

  phase("respiratory_failure",
    "Tiring on an untreated flooded lung",
    "in respiratory failure",
    "Hypoxaemic and hypercapnic respiratory failure from untreated cardiogenic pulmonary oedema. "
    "Drowsy, tachypnoeic, and no longer able to sustain the work of breathing. Still perfusing. "
    "The authored heart rate here is the UNTREATED one; a patient who reached this phase with "
    "atrioventricular nodal blockade already on board reads about 35 beats lower, which is a "
    "vital effect on the rate-control action guarded on this phase.",
    166, 118, 70, 38, 82, 37.0, 3, 1,
    [
      {"when": "flag intubated set", "to": "intubated"},
      {"when": "flag on_niv set AND flag rate_control_given set", "to": "stabilized",
       "author_note": "Rate control was already given in an earlier phase and has had time to act, "
                      "so adding positive pressure here completes the resuscitation rather than "
                      "starting a second clock."},
      {"when": "flag on_niv set", "to": "breathing_supported",
       "author_note": "The rescue. Positive pressure applied late still works; the case does not "
                      "punish lateness beyond the phase it has already cost."},
      HANDOFF_T,
    ],
    schema_gap_note=(
      "There is deliberately no rate-control exit from this phase. A learner who reaches "
      "respiratory failure and responds by giving another rate-controlling drug sees the flag set, "
      "the debrief credit the critical action, and the patient not improve, which is the whole "
      "lesson of wrong path one stated as behaviour. The flag is remembered, so applying positive "
      "pressure afterwards goes straight to the stabilised phase.")),

  phase("breathing_supported",
    "Oxygenating on positive pressure, ventricular rate still uncontrolled",
    "on positive pressure",
    "Work of breathing and oxygenation improving on non-invasive ventilation. Still in atrial "
    "fibrillation at a rate that is itself shortening diastolic filling in a poorly contracting "
    "ventricle.",
    152, 126, 76, 24, 88, 37.0, 1, 0,
    [
      {"when": "flag intubated set", "to": "intubated"},
      {"when": "flag rate_control_given set", "to": "stabilized",
       "after_seconds": 60, "measured_from": "guard_true",
       "narration": RATE_CONTROL_NARRATION,
       "debrief_note": RATE_CONTROL_NOTE,
       "author_rationale": RATE_CONTROL_RATIONALE},
      HANDOFF_T,
    ]),

  phase("rate_controlled_congested",
    "Ventricular rate controlled, lung still flooded",
    "rate controlled, still congested",
    "The ventricular rate has come down and nothing has been done for the pulmonary oedema. "
    "Tachypnoeic, hypoxaemic, and still working hard to breathe.",
    108, 118, 70, 32, 86, 37.0, 3, 0,
    [
      {"when": "flag intubated set", "to": "intubated"},
      {"when": "flag on_niv set", "to": "stabilized"},
      {"when": "NOT flag on_niv set", "after_seconds": 240, "measured_from": "phase_entry",
       "to": "respiratory_failure",
       "narration": "His rate's crept up again and he's working much harder than he was. His "
                    "sat has come down.",
       "debrief_note": (
         "The heart rate improved and the patient did not. This is wrong path one in its pure "
         "form: the arrhythmia was the visible problem, it was treated competently, and the flooded "
         "lung underneath it was never addressed. A ventricular rate of 108 in a man at a "
         "saturation of 86 percent breathing 32 times a minute is not a resuscitated patient. Rate "
         "control and treatment of the pulmonary oedema are parallel tasks in this case, not "
         "sequential ones, and if anything the oedema is the more urgent of the two."),
       "author_rationale": (
         "AUTHOR SIGNATURE REQUIRED. Same claim and same four minutes as the arrival phase, "
         "applied to a patient whose rate is now 108. The rate control is a genuine improvement in "
         "diastolic filling time, so a reviewer might reasonably argue this patient tires more "
         "slowly than the one at 160 and that the deadline here should be longer. It is set the "
         "same deliberately, so that the case does not teach that treating the rate buys time it "
         "has not been shown to buy.")},
      HANDOFF_T,
    ]),

  phase("stabilized",
    "Rate controlled and ventilating on positive pressure",
    "responding",
    "Comfortable on non-invasive ventilation with a controlled ventricular rate, improving "
    "oxygenation and falling work of breathing. Still in atrial fibrillation, still congested, and "
    "requiring a monitored bed.",
    104, 124, 74, 20, 89, 37.0, 0, 0,
    [
      {"when": "flag intubated set", "to": "intubated"},
      HANDOFF_T,
    ]),

  phase("intubated",
    "Intubated and mechanically ventilated",
    "intubated",
    "Sedated and ventilated after failure of, or in place of, non-invasive support. Oxygenating on "
    "the ventilator. Cannot give any further history.",
    118, 108, 62, 16, 96, 37.0, 0, 3,
    [HANDOFF_T],
    schema_gap_note=(
      "One vitals block for a phase that is reached by two very different routes: elective "
      "intubation of a man who was talking to you, and intubation of a man who had already tired. "
      "The schema provides one block per phase. The numbers here are the post-intubation state and "
      "assume no peri-intubation collapse, which is a deliberate simplification: this case is not "
      "about the airway and adding a hypotension branch would make it about the airway.")),

  phase("halted", "Case halted after a harmful action", "stopped",
    "Terminal phase entered directly when a harmful action is taken, carrying that action's halt "
    "reason. Not reached through transition rules.",
    38, 62, 34, 6, 76, 36.8, 0, 3, [], terminal=True, pupil="large", react="sluggish",
    schema_gap_note=(
      "Generic peri-arrest numbers. This case has one halting action, so unlike CHFE there is no "
      "second physiology these numbers have to cover.")),

  phase("case_complete", "Handoff confirmed", "handed over",
    "Terminal phase entered when the resident confirms a handoff. The debrief is generated from here.",
    104, 124, 74, 20, 95, 37.0, 0, 0, [], terminal=True,
    schema_gap_note=(
      "Placeholder, as in the reference case. A completion phase should inherit the vitals of the "
      "phase the resident handed off from and the schema cannot express that. The saturation of 95 "
      "assumes the intended path with positive pressure running; a resident who hands over from the "
      "rate-controlled-and-congested phase sees a number here that is better than the patient they "
      "handed over.")),
]
