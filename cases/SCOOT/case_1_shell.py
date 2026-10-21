"""SCOOT part 1: identity, patient, phases.

A right temporal epidural hematoma in a 22-year-old man after an e-scooter crash, who
arrives talking and declines in the department. Drafted by a language model on 19 October
2026 at the request of Aakash Setty. No physician has reviewed this pack. SCOOT-SEED.md
says what a person decided and which sources were opened.

Four learning goals, approved by Aakash Setty on 19 October 2026:

  G1. When the exam changes, the plan changes. Re-examine and escalate on the trend.
  G2. The treatment for an epidural hematoma is a surgeon. Image early and call.
  G3. Intubate for a reason, not a number. No osmotherapy without a reason either.
  G4. Treat herniation, and leave the compensation alone.

The decline at 240 seconds is scheduled natural history: nothing the learner does stops it.
Herniation is a deterioration on inaction. The clock can end the run in herniation, with
the opt-in. All three deadlines are teaching choices, not measured intervals.
"""

META = {
 "working_title": "22-year-old man after an e-scooter crash",
 "chief_complaint_patient_voice": "My head is killing me. What happened?",
 "final_diagnosis": (
   "Acute right temporoparietal epidural hematoma, about 19 mm thick and about 50 mL, with a "
   "swirl sign and about 6 mm of midline shift, over a linear right temporal squamous fracture, after a fall from an e-scooter without a "
   "helmet. He arrives at GCS 15 and declines to GCS 12 in the department. Left without a "
   "neurosurgeon, it herniates."),
 "target_level": ["medical_student", "intern", "junior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "When the exam changes, the plan changes. Re-examine when the patient changes, and escalate on the trend even when the vitals and the pupils are normal.",
   "The treatment for an epidural hematoma is a surgeon. Image early, and call neurosurgery the moment the CT is back, without waiting for a blown pupil or Cushing's response.",
   "Intubate for a reason, not a number. Do not intubate a GCS 12 patient who is protecting his airway on his way to the operating room, and do not give osmotherapy at GCS 15.",
   "Recognize herniation and temporize with osmotherapy and an airway, and leave the hypertension and the bradycardia alone.",
 ],
 "teaching_frame": (
   "Every number on the monitor says concussion. The one thing that says otherwise is the "
   "exam, and only if the learner looks again. The case lets the learner sit on a scan, "
   "reach for the tube or the mannitol because a number fell, or lower a pressure that is "
   "keeping the brain alive, and shows what each does."),
 "care_setting": {
   "label": "Level 1 trauma center",
   "detail": (
     "Adult emergency department in a Level 1 trauma center. CT next to the trauma bay, "
     "neurosurgery in house at all hours, an operating room available, and a neurosurgical "
     "intensive care unit."),
   "provenance": "Model default, taken when the owner asked for the build without choosing. SCOOT-SEED.md section 0.",
 },
 "arrival": {
   "mode": "ems",
   "location": "trauma_bay",
   "line": "Brought in by ambulance from the scene of an e-scooter crash, to the trauma bay.",
 },
 "complaint": "Head injury after crash",
 "category": "Trauma",
 "library": {
   "tempo": "minutes: a decline the learner cannot stop, then a clock to herniation that a call stops",
   "uncertainty": "whether he is getting worse, and when to act",
   "right_answer": "ask someone, the surgeon, and do less until it is time to do more",
   "danger": "behind normal vitals and a GCS of 15, and when it shows, it shows in the exam and not on the monitor",
   "setting": "22 M, EMS to the trauma bay, alone, his friend on the way",
   "feel": "deceptively easy, then urgent",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Descriptive, not clinical. No physician has reviewed the wording.",
 },
}

PATIENT = {
 "age": 22,
 "sex": "male",
 "weight_kg": 78,
 "background": (
   "Works at a bike shop and lives with a roommate. No medical history, no surgery, no "
   "medicines, no allergies, no blood thinners. Vapes nicotine now and then, drinks a "
   "little at weekends, no drugs, nothing to drink tonight.\n\n"
   "Riding an e-scooter home from his friend Marcus's apartment at about 9 pm, at about 20 "
   "mph, without a helmet. He hit a pothole and went over the handlebars, landing on the "
   "right side of his head. Marcus, riding behind him, says he was out for about a minute, "
   "then got up and talked. He remembers leaving Marcus's building and nothing after that. "
   "Right-sided headache, queasy. Road rash on both palms. Dinner at about seven. Marcus is "
   "following the ambulance."),
 "presenting_vitals_source": "Inherited from phase 'presentation'.",
 "presenting_appearance": (
   "A young man sitting up on the trauma stretcher with an ice pack held to the right side "
   "of his head, talking, asking again what happened."),
 "ems_handover_text": (
   "Twenty-two year old male, e-scooter versus pothole at about twenty miles an hour, no "
   "helmet, over the handlebars onto the right side of his head. Friend on scene reports "
   "about a minute of loss of consciousness. GCS 15 throughout transport, repetitive "
   "questioning, right temporal hematoma, abrasions to both palms. Rate 88, pressure 138 "
   "over 82, saturation 99 percent on room air. No blood thinners per the patient."),
 "arrival_handover": (
   "Twenty-two year old guy came off an e-scooter, no helmet, and his friend says he was "
   "out for maybe a minute. He's been talking to us the whole way in but keeps asking what "
   "happened."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 36 words. No vital sign, no history, no diagnosis. It "
   "carries the loss of consciousness because a crew that heard it from the friend would "
   "say it, and it is why he came by ambulance. Recorded in SCOOT-SEED.md section 2.3."),
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp, distress, alert,
          pupil_size, pupil_react, transitions, qtc, ecg_note, terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": pupil_size, "pupil_reactivity": pupil_react},
      "rhythm": "regular",
      "ecg": {"pattern": "organised", "p_waves": True, "pr_ms": 150, "qrs_ms": 88,
              "qtc_ms": qtc, "author_note": ecg_note},
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}

TUBED = "flag intubated set"
HAS_SCAN = "flag neurosurgery_called set"
OSMO = "action osmotherapy_for_herniation taken"
MEMORY = " [UNVERIFIED: written by a model from memory, no source opened]"
BULLOCK = " [UNVERIFIED: Bullock et al. 2006, read through a summarizing tool]"

DECLINE_NOTE = (
  "He got worse four minutes in, whatever you were doing. The hematoma was still growing, "
  "and nothing in the department stops that except a surgeon.\n\n"
  "The monitor hardly moved. His pressure went up a few points and his pulse a few beats. "
  "His pupils stayed equal. What changed was the exam: he went from GCS 15 to 12, and he "
  "vomited. That is the alarm in a head injury, and it only sounds for the doctor who looks "
  "again. A fall of two points or more is a reason to act now, not to watch.\n\n"
  "Some patients with an epidural hematoma talk on arrival and then deteriorate, which is "
  "the lucid interval. Many do not have one. A talking patient is not a safe patient."
  + MEMORY)

DECLINE_RATIONALE = (
  "Scheduled natural history. An expanding arterial epidural hematoma raises intracranial "
  "pressure over minutes to hours after injury, and the department cannot stop it. Every "
  "learner meets the decline, which is where G1 is acted on. 240 seconds is a teaching "
  "choice from the supplied plan's 3 to 5 minutes. Approved as part of the states by "
  "Aakash Setty on 19 October 2026. The timing is model output.")

PHASES = [
 phase("presentation",
   "Talking after a head injury, GCS 15",
   "on arrival",
   "Alert and oriented, repeating questions, right temporal scalp hematoma, pupils equal. "
   "Normal vitals. An epidural hematoma of about 50 mL is already there. What now: monitor, primary "
   "survey, a baseline neuro exam, a head CT, and neurosurgery once the CT is back.",
   88, 138, 82, 16, 99, 36.8, 1, 0, "normal", "reactive",
   [HANDOFF_T,
    {"when": TUBED,
     "after_seconds": 240, "measured_from": "phase_entry", "to": "decline",
     "narration": ("He's sedated on the ventilator, so we can't follow how he's talking. "
                   "His pupils are still equal."),
     "debrief_note": (
       "He got worse four minutes in, as he would have whatever you did. You could not see "
       "it, because the tube and the sedation had taken away the exam you would have seen "
       "it in. With an intubated head injury, the pupils are what is left to follow.\n\n"
       + DECLINE_NOTE),
     "author_rationale": (
       "Outcome chosen at a scheduled time: a positive guard above the unguarded rule with "
       "the same after_seconds, so an intubated patient gets a narration that is true of "
       "him. Same destination. " + DECLINE_RATIONALE)},
    {"when": None,
     "after_seconds": 240, "measured_from": "phase_entry", "to": "decline",
     "narration": ("He just vomited, and he's hard to keep awake now. He keeps drifting off "
                   "in the middle of a sentence."),
     "debrief_note": DECLINE_NOTE,
     "author_rationale": DECLINE_RATIONALE,
     "unguarded_rationale": (
       "Nothing the learner can do in the department stops an expanding hematoma within "
       "minutes. A guard would imply that some action prevents the decline, which is false. "
       "The decline is where the first goal is taught, so every learner meets it. Approved "
       "as part of the states by Aakash Setty on 19 October 2026.")}],
   410,
   "Sinus rhythm at the phase rate, as the phase's ECG report says. Model output.",
   ),

 phase("decline",
   "Drowsy and vomiting, GCS 12, pupils equal",
   "harder to wake",
   "Opens his eyes to voice, confused, localizes pain (E3 V4 M5). Vomited. Pupils still "
   "equal and reactive. Vitals a few points higher than on arrival. What now: re-examine, "
   "get the CT now or call neurosurgery with it, or call them back, give an antiemetic, and "
   "leave the airway alone.",
   96, 145, 84, 18, 98, 36.8, 1, 1, "normal", "reactive",
   [HANDOFF_T,
    {"when": "NOT " + HAS_SCAN,
     "after_seconds": 120, "measured_from": "phase_entry", "to": "herniation",
     "narration": ("His right pupil has gone big and it isn't reacting, and his heart rate "
                   "has dropped. He's not answering me."),
     "debrief_note": (
       "His brain herniated. The hematoma kept growing, pushed the right temporal lobe "
       "inward against the nerve that works the right pupil and against the brainstem, and "
       "the blown pupil and the slow pulse are what that looks like.\n\n"
       "Neurosurgery had not been called with his scan in the two minutes since he "
       "dropped his GCS. The scan was the step, or the call once the scan was back. An "
       "epidural hematoma over 30 mL is evacuated whatever the GCS, and the decision to "
       "operate belongs to the neurosurgeon. The emergency physician's decision is to call "
       "them, and the moment to call is when the CT is back, not when a pupil changes."
       + BULLOCK),
     "author_rationale": (
       "Deterioration on inaction. An untreated expanding temporal epidural hematoma "
       "progresses to uncal herniation. Guarded on the flag the neurosurgery consult sets. "
       "The consult cannot be made until a head CT has resulted (a prerequisite, authoring "
       "9.5), so a learner who called with the scan before or during the decline never "
       "herniates. 120 seconds is the owner's choice (Aakash Setty, 19 October 2026: the "
       "pupil blows at 6:00). The prompt for that call lands at 25 seconds (75 in the "
       "default mode) with an escalation at 35 (105), after the repeat-exam prompt at 15 "
       "(45). The CT prompt at 50 (150) lands here only in easy mode, and there is none on "
       "arrival. In the default mode a "
       "learner with no scan hears the neurosurgery prompt and is sent for the scan by its "
       "prerequisite. Model output.")}],
   410,
   "Sinus rhythm at the phase rate, as the phase's ECG report says. Model output.",
   ),

 phase("herniation",
   "Uncal herniation, GCS 7, right pupil fixed",
   "right pupil big",
   "Groans to pain only (E1 V2 M4), right pupil 6 mm and fixed, left 3 mm and reactive, "
   "withdraws less on the left. Cushing's response: pressure up, pulse down, slow breathing. "
   "What now: osmotherapy, intubate, neurosurgery now, and leave the pressure and the pulse "
   "alone.",
   56, 178, 94, 10, 95, 36.9, 0, 2, "large", "fixed",
   [HANDOFF_T,
    {"when": OSMO,
     "after_seconds": 15, "measured_from": "guard_true", "to": "temporized",
     "narration": ("His right pupil is a little smaller and it's reacting again. His heart "
                   "rate is coming up."),
     "debrief_note": (
       "The osmotherapy worked for now. Mannitol or hypertonic saline draws water out of "
       "the brain and lowers the pressure inside the skull, and a blown pupil can come back. "
       "It buys minutes to hours. It does not take the clot out, so the surgeon still has "
       "to." + MEMORY),
     "author_rationale": (
       "Delayed consequence of the learner's action. Guarded on a hidden action credited "
       "only in this phase, so a dose given during the decline does not satisfy the exit "
       "(authoring 15.2 rule 6). 15 seconds is a teaching choice. Model output.")},
    {"when": "NOT " + OSMO,
     "after_seconds": 300, "measured_from": "phase_entry", "to": "brainstem_compression",
     "narration": ("He's barely breathing and his heart rate is in the forties. Both pupils "
                   "are big now."),
     "debrief_note": (
       "He died of brainstem compression. The herniation went untreated for five minutes. "
       "Osmotherapy was the one thing that could have bought time for the surgeon, and it "
       "was never given after his pupil blew.\n\n"
       "This is the only way the case ends on the clock, and it took two missed chances to "
       "get here: the call to neurosurgery in the decline, and the osmotherapy here."
       + MEMORY),
     "author_rationale": (
       "Deterioration on inaction into a terminal phase. Untreated uncal herniation "
       "progresses to brainstem failure. 300 seconds is a teaching choice. The osmotherapy "
       "prompt lands at 20 seconds (60 in the default mode) with an escalation at 60 (180). "
       "The terminal clock is a model default the owner has not chosen (SCOOT-SEED.md "
       "section 0). Model output."),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Untreated herniation does not wait. The learner reaches this only after ignoring "
       "the scan or the call through the decline, and then the osmotherapy prompt and its "
       "escalation for five minutes. Without it the case would show a herniating patient "
       "waiting indefinitely, which is false. The owner may remove it (SCOOT-SEED.md open "
       "question 1).")}],
   430,
   "Sinus bradycardia at the phase rate, as the phase's ECG report says. Model output.",
   ),

 phase("temporized",
   "After osmotherapy, GCS 8, right pupil sluggish",
   "pupil reacting",
   "Eyes flicker to pain (E2 V2 M4), right pupil 4 mm and sluggish, pulse and pressure "
   "settling. Still needs the clot out. What now: secure the airway if that is not done, "
   "and hand him to the operating room.",
   70, 160, 88, 14, 98, 36.9, 0, 2, "normal", "sluggish",
   [HANDOFF_T],
   420,
   "Sinus rhythm at the phase rate, as the phase's ECG report says. Model output.",
   authoring_note=(
     "No clock. Osmotherapy buys time in life and the case does not model it running out. "
     "Known gap 3 in SCOOT-SEED.md."),
   ),

 phase("brainstem_compression",
   "Brainstem compression after untreated herniation",
   "not responding",
   "Terminal. Both pupils fixed, slow and gasping breathing, pulse in the forties, pressure "
   "very high. Reached only by the clock in herniation.",
   44, 196, 108, 6, 86, 36.9, 0, 3, "large", "fixed",
   [],
   440,
   "Sinus bradycardia at 44, as the narration says. The monitor draws no escape beats. Model output.",
   terminal=True,
   timeout_reason=(
     "His brain herniated and nothing was given for it. After his right pupil blew, five "
     "minutes passed without osmotherapy, and the pressure crushed his brainstem before a "
     "surgeon could take the clot out."),
   ),

 phase("case_complete",
   "Handed to the operating room",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   88, 138, 82, 16, 99, 36.8, 0, 0, "normal", "reactive", [], 410,
   "Fallback only. The phase inherits the vitals of the phase the handoff came from.",
   terminal=True, inherit_vitals=True,
   ),
]
