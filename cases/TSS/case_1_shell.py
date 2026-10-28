"""TSS part 1: identity, patient, phases.

Menstrual toxic shock syndrome in a 22-year-old woman. Drafted by a language model from a
one-paragraph plan and four decisions given by Aakash Setty on 6 October 2026. No physician
has reviewed this pack. See TSS-SEED.md for what was decided by a person and what was not.

The design guide this case was written against is the "EMSim case design guide". Three
learning goals drive the structure, and every phase below exists to make the learner act on
one of them:

  1. Recognize shock in a young patient who compensates.
  2. Find the source and remove it.
  3. Resuscitate toxin-mediated shock: fluid, then a vasopressor when fluid is not holding,
     and antibiotics that cover staphylococci.
"""

META = {
 "working_title": "22-year-old woman, fainted at home with a fever and a rash, walked in with her roommate",
 "chief_complaint_patient_voice": "I fainted in the shower. I've had a fever for two days and now I'm red all over.",
 "final_diagnosis": (
   "Menstrual staphylococcal toxic shock syndrome from a tampon retained for about four days, "
   "with septic shock, acute kidney injury, thrombocytopenia, transaminitis and early "
   "rhabdomyolysis. Blood cultures are expected to stay negative, as they usually do in "
   "staphylococcal toxic shock."),
 "target_level": ["medical_student", "intern", "junior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "Recognize shock in a young, talking patient from the heart rate, the blood pressure, the capillary refill and the lactate, and do not let a plausible story of flu and a sunburn explain them away.",
   "In fever, rash and hypotension with no clear source, ask about menstruation and tampon use and do a pelvic examination.",
   "Remove the source. A retained tampon is found and removed at the bedside, and nothing else in the resuscitation replaces that.",
   "Give about 30 mL/kg of crystalloid, reassess, and start norepinephrine when the mean arterial pressure stays under 65 after fluid.",
   "Start antibiotics early that cover staphylococci including MRSA, and know why clindamycin is added in toxin-mediated disease.",
   "Admit to intensive care, and name the organ injuries at handover.",
 ],
 "teaching_frame": (
   "She looks well enough to send home, and the easy story is one every learner has heard a "
   "hundred times. The case is built so that the numbers contradict the patient's own "
   "explanation from the first second, and so that the one thing that changes her course is "
   "something nobody will mention unless the learner asks or looks."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Adult emergency department with an intensive care unit, infectious disease and "
     "gynecology on call, and a full laboratory and imaging service. Nothing in this case is "
     "limited by resources."),
 },
 "arrival": {
   "mode": "triage",
   "location": "patient_room",
   "line": "Walked in with her roommate after fainting at home. Triaged as fever and rash and placed in a room.",
 },
 "complaint": "Fainting, fever and rash",
 "category": "Infectious disease",
 "library": {
   "tempo": "minutes: the shock progresses without fluid",
   "uncertainty": "the diagnosis in a talking patient, and whether to send her home",
   "right_answer": "ask the question nobody asks, and remove the source",
   "danger": "behind near-normal vitals in a young patient; discharge is the trap",
   "setting": "22 F, walked into a patient room with her roommate",
   "feel": "puzzling, then urgent",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Printed in docs/generated/case-index.md so a new case can say how it differs. Descriptive, not clinical: no physician has reviewed the wording."
 },
}

PATIENT = {
 "age": 22,
 "sex": "female",
 "weight_kg": 62,
 "background": (
   "Graduate student, lives with one roommate. No past medical history. Wisdom teeth "
   "removed at eighteen and no other surgery. Takes a combined oral contraceptive pill. She "
   "took ibuprofen yesterday, two tablets a couple of times, and nothing else. No allergies. "
   "Does not smoke, drinks socially, uses no drugs.\n\n"
   "Her period started five days ago. She uses super-absorbency tampons. Four days ago she "
   "put one in before an evening out, came home late, and did not take it out. She believes "
   "her period has ended and has not thought about the tampon since. Two days ago she "
   "developed fever, chills, muscle aches and a sore throat, which she puts down to the flu. "
   "She has no vomiting and no diarrhea, and she has barely eaten or drunk since. Yesterday "
   "she took her temperature and it was 102. The same day she spent an hour at the beach "
   "and blames her red skin on that. This morning she fainted in the shower, for a few "
   "seconds by her roommate's account and without hitting her head, and her roommate "
   "drove her in. Rewritten on 11 October 2026 on author instruction: she presents fainting, "
   "febrile and with a rash, not with vomiting and diarrhea."),
 "presenting_vitals_source": "Inherited from phase 'presentation'. Measured at triage.",
 "presenting_appearance": (
   "A young woman sitting up on the bed, talking in full sentences and apologizing for coming "
   "in. She is flushed red all over and her lips are dry. She does not look as sick as her "
   "numbers."),
 "ems_handover_text": (
   "Twenty-two year old woman, two days of fever, chills and body aches. She thinks it is "
   "the flu. Fainted in the shower this morning, out for a few seconds by her roommate's "
   "account, no head strike. Heart rate 128 and pressure 94 over 58 at triage, temperature "
   "39.4. She looks sunburned and says she was at the beach yesterday. Walking, talking, "
   "roommate with her."),
 "arrival_handover": (
   "Twenty-two year old, fever for two days and red all over since yesterday. She fainted in "
   "the shower this morning and her roommate drove her in."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 26 words, in a triage nurse's voice. No vital sign, no past "
   "history, no medication, no pertinent negative, and no diagnosis in clinical or lay "
   "words. Rewritten on 11 October 2026: the presentation is fainting, fever and a rash. "
   "The period is left for the learner to find. The earlier wording repeated her "
   "'something she ate', a recorded exception to section 11.5 that no longer applies."),
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp,
          distress, alert, transitions, terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": "normal", "pupil_reactivity": "reactive"},
      "rhythm": "regular",
      "ecg": {"pattern": "organised", "p_waves": True, "pr_ms": 140, "qrs_ms": 84,
              "qtc_ms": 430,
              "author_note": "Sinus tachycardia with narrow complexes in every phase, with "
                             "the PR, QRS and QTc the ECG report gives. Model output."},
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list so that a handoff is never overtaken by a "
                            "clinical rule in the same step."}

FLUIDS = "flag fluids_given set"
PRESSOR = "flag pressor_running set"
SOURCE = "flag source_removed set"

# ---------------------------------------------------------------- the discharge
# The learner chose "discharge home" on the Handoff tab while she still looked well. The
# interface logs the hidden action attempt_discharge instead of a handoff (see HANDOFF in
# case_5 and handoffIntercept in the engine), which sets this flag, and five seconds later
# she is on the floor. Decided by Aakash Setty, 6 October 2026: she faints and the case
# continues.
# v0.24 audit, on every narration in this file. A timed narration is spoken at the moment
# the monitor changes, and the monitor shows the destination phase's numbers plus every
# vital effect acting there (authoring 7.3). Rate control acts in every phase, and fluid,
# a push-dose vasopressor and a vasopressor without fluid act in the low phases, so every
# destination can carry an effect and no narration quotes a figure. Each keeps the
# direction. "Pressure" is judged on the mean arterial pressure. TSS-tests.js folds each
# effect-bearing route and compares each line with the folded vitals before and after.
DISCHARGE_T = {
  "when": "flag discharge_attempted set",
  "after_seconds": 5,
  "measured_from": "guard_true",
  "to": "hypotensive",
  "narration": ("She stood up to get dressed and went straight down. I've got her back on the "
                "bed. She's gray and drowsy and her pressure has dropped."),
  "debrief_note": (
    "She was discharged with a heart rate over 110 and a fever, and she fainted when she "
    "stood up. She is both dry and vasodilated. A young adult in that state holds a blood "
    "pressure with her heart rate, and standing takes that away.\n\n"
    "The trap was the story. The flu and a day at the beach seem to explain the fever and "
    "the red skin, and fluid makes most people feel better. They do not explain a fit 22 "
    "year old who fainted, with a low pressure and slow capillary refill. A patient you are "
    "about to send home should have vital signs you would accept at home."),
  "author_rationale": (
    "A delayed consequence of the learner's own action, so the five-second floor applies. "
    "Orthostatic syncope in compensated distributive shock is plausible. That it happens "
    "every time is a teaching choice. Model output, needs a physician's signature."),
}

PHASES = [
 phase("presentation",
   "Compensated shock, looks well",
   "on arrival",
   "Alert, talking, flushed and febrile. Tachycardic with a low-normal pressure and a narrow "
   "margin. Capillary refill is slow and the lactate is raised. She has had nothing but sips "
   "for two days and has a retained tampon nobody knows about.",
   128, 94, 58, 22, 97, 39.4, 1, 0,
   [HANDOFF_T,
    DISCHARGE_T,
    {"when": FLUIDS,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "fluid_responsive",
     "narration": ("That fluid is in. Her pressure is better and she says she feels a bit "
                   "better."),
     "debrief_note": (
       "The first bolus helped, as it should. She was dry from two days of fever and barely "
       "drinking, and she is leaking fluid out of her vessels.\n\n"
       "Read the response as information, not as a result. A patient who is still "
       "tachycardic with a temperature over 39 after a liter was not only dehydrated. The "
       "target is about 30 mL/kg, which for her is close to two liters, followed by a "
       "reassessment."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. Ten seconds stands for the time a "
       "liter takes to run in, heavily compressed. The size of the response is a teaching "
       "choice. Model output.")},
    {"when": "NOT " + FLUIDS,
     "after_seconds": 300,
     "measured_from": "phase_entry",
     "to": "hypotensive",
     "narration": ("She's gone gray and she's getting drowsy. Her pressure has dropped and "
                   "her rate is up."),
     "debrief_note": (
       "She was given no fluid bolus and she stopped compensating. On arrival she was "
       "already in shock: a heart rate of 128, a pressure of 94 over 58, a slow capillary "
       "refill and a fever. She was holding her pressure with her heart rate.\n\n"
       "Young patients do this well and then fail quickly. The time to treat shock is while "
       "the patient is still talking to you."),
     "author_rationale": (
       "Deterioration on inaction. Untreated toxic shock progresses to hypotension over hours, "
       "and five minutes of case clock stands for that. The number is a drafting judgment and "
       "needs a physician's signature. The nurse asks for a line at 45 seconds and for fluid "
       "at 60 and again at 170. In the default mode those are 135, 180 and 510, so the first "
       "fluid warning comes 120 seconds before this rule and the escalation is never heard.")}],
   ),

 phase("fluid_responsive",
   "Transient response to fluid",
   "after fluid",
   "Better after the first bolus and still tachycardic and febrile. This is the phase in "
   "which she looks most like a patient who could go home. The response does not last.",
   114, 104, 62, 20, 98, 39.2, 1, 0,
   [HANDOFF_T,
    DISCHARGE_T,
    {"when": PRESSOR + " AND " + SOURCE,
     "after_seconds": 150,
     "measured_from": "phase_entry",
     "to": "stabilizing",
     "narration": ("The fluid on its own isn't holding her any more, but the vasopressor is, "
                   "and her pressure is steady."),
     "debrief_note": (
       "The effect of the fluid faded, which is the natural course of this illness, and she "
       "did not drop because a vasopressor was already running and the source was out. "
       "Starting a vasopressor before the pressure falls is a reasonable choice in septic "
       "shock and the case accepts it."),
     "author_rationale": (
       "The same clock as the unguarded rule below, so that the fade happens at one moment "
       "whatever was done. Listed first so a learner who has done everything goes straight "
       "to the stable phase. Model output.")},
    {"when": PRESSOR,
     "after_seconds": 150,
     "measured_from": "phase_entry",
     "to": "supported",
     "narration": ("The fluid on its own isn't holding her any more. The vasopressor is "
                   "keeping her pressure up and I've had to turn it up."),
     "debrief_note": (
       "The effect of the fluid faded and the vasopressor caught her. She is holding a "
       "borderline pressure on a rising dose, which means something is still driving the "
       "shock."),
     "author_rationale": "As above. Model output."},
    {"when": None,
     "after_seconds": 150,
     "measured_from": "phase_entry",
     "to": "hypotensive",
     "narration": ("That fluid isn't holding. Her pressure is back down, her rate is back up "
                   "and she's getting drowsy."),
     "debrief_note": (
       "The response to fluid wore off. This is expected in toxic shock and is not a "
       "mistake on your part. The toxin dilates vessels and makes them leak, so crystalloid "
       "leaves the circulation soon after it goes in.\n\n"
       "This is the moment the case is built around. A mean arterial pressure under 65 "
       "that persists after fluid is an indication for norepinephrine. The usual fluid "
       "target is about 30 mL/kg, and a vasopressor does not have to wait for all of it. "
       "More fluid alone will buy less each time."),
     "author_rationale": (
       "Scheduled natural history. The rules above it catch a learner who already started a "
       "vasopressor, so in effect this fires when none is running. Two and a half minutes "
       "stands for the hour or so over which a transient responder declares herself. Model "
       "output, needs a physician's signature. No prompt names a vasopressor in this phase, "
       "so this fade arrives unwarned in both modes. That is deliberate and follows the "
       "directing physician's fourth decision (TSS-SEED.md section 0 and section 4a)."),
     "unguarded_rationale": (
       "The fade is the illness and not a consequence of anything the learner did or did not "
       "do, and the physician directing this case asked for exactly this: the pressure stays "
       "under a mean of 65 after about 30 mL/kg and norepinephrine is then the expected move. "
       "The nurse says after the first bolus that 30 per kilo is nearly two liters, and the "
       "phase this leads to is recoverable with one order.")}],
   ),

 phase("hypotensive",
   "Hypotensive shock",
   "hypotensive",
   "Mean arterial pressure 54. Drowsy but rousable, gray, tachypneic. Reached when the fluid "
   "response fades, when no fluid was given, or when she was stood up to go home. Fluid and a "
   "vasopressor together get her out.",
   138, 78, 42, 26, 95, 39.6, 2, 1,
   [HANDOFF_T,
    {"when": PRESSOR + " AND " + FLUIDS + " AND " + SOURCE,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": ("The vasopressor is working. Her pressure is up and she's more awake."),
     "debrief_note": (
       "The vasopressor restored her pressure, and it is holding because the source is out. "
       "Ten seconds is a compression of the several minutes a titration takes."),
     "author_rationale": "A delayed consequence of the learner's own action. Model output."},
    {"when": PRESSOR + " AND " + FLUIDS,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "supported",
     "narration": ("The vasopressor has brought her pressure up and she's more awake. I've "
                   "had to go up on it twice to get there."),
     "debrief_note": (
       "The vasopressor restored a borderline pressure. She needs a rising dose to stay "
       "there, which is what an untreated source looks like from the infusion pump."),
     "author_rationale": "A delayed consequence of the learner's own action. Model output."},
    {"when": "NOT " + PRESSOR + " OR NOT " + FLUIDS,
     "after_seconds": 240,
     "measured_from": "phase_entry",
     "to": "profound_shock",
     "narration": ("I can barely rouse her. Her pressure has dropped again and her rate is "
                   "higher."),
     "debrief_note": (
       "Her mean arterial pressure stayed under 65 without both fluid and a vasopressor, and "
       "she progressed to profound shock.\n\n"
       "Hypotension that persists after fluid is not treated with more waiting or with fluid "
       "alone. Norepinephrine can be started through a good peripheral line while central "
       "access is arranged. A vasopressor without any fluid is also not enough in a patient "
       "this dry."),
     "author_rationale": (
       "Deterioration on inaction. The nurse says the mean pressure is under 65 at 30 seconds and again "
       "at 120, and for fluid at 60 if none has been given. In the default mode those are 90, "
       "360 and 180, so both first warnings come at least 60 seconds before this rule and the "
       "escalation is never heard. Four minutes is a drafting judgment and needs a "
       "physician's signature.")}],
   ),

 phase("supported",
   "On a vasopressor, source still in place",
   "on a vasopressor",
   "Awake again with a mean arterial pressure of 64 on a vasopressor, and the dose is "
   "climbing. Fluid and a vasopressor are treating the consequence. The tampon is still "
   "there and the toxin is still being made.",
   124, 92, 50, 24, 96, 39.5, 2, 0,
   [HANDOFF_T,
    {"when": SOURCE,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": ("I've stopped having to go up on the vasopressor since that came out. "
                   "She's holding her pressure on the same dose."),
     "debrief_note": (
       "Removing the tampon stopped the decline. It did not cure her: the toxin already "
       "absorbed keeps acting for many hours, and she stays on a vasopressor. What changed is "
       "that the dose stopped rising.\n\n"
       "The case shows this within seconds. In a real patient you would see it over the "
       "next hour or more, and you would not be able to tell it apart from the effect of "
       "everything else you did. That is the reason source control is done on principle and "
       "not judged by the monitor."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. The physician directing this case "
       "chose 'stops the decline, no dramatic rebound'. Ten seconds is a heavy compression "
       "and the debrief note says so. The speed of real improvement after tampon removal is "
       "unsourced. Needs a physician's signature.")},
    {"when": "NOT " + SOURCE,
     "after_seconds": 270,
     "measured_from": "phase_entry",
     "to": "profound_shock",
     "narration": ("I've been going up and up on the vasopressor and it isn't enough any "
                   "more. Her pressure has dropped, her rate is up, and I can barely rouse "
                   "her."),
     "debrief_note": (
       "She had fluid and a vasopressor and still got worse, because the source was never "
       "removed. A retained tampon colonized with toxin-producing staphylococci keeps "
       "delivering toxin for as long as it stays in.\n\n"
       "Shock that needs a rising vasopressor dose after adequate fluid means the cause is "
       "still active. Go back and look for it: a full examination including the pelvis, "
       "wounds, lines and packing."),
     "author_rationale": (
       "Deterioration on inaction. The nurse asks whether anyone has checked for pregnancy at "
       "60 seconds and again at 180. In the default mode those are 180 and "
       "540, so the first warning comes 90 seconds before this rule and the escalation is "
       "never heard. Four and a half minutes is longer than "
       "the other clocks on purpose: the directing physician asked that treated sepsis with a "
       "missed source decline more slowly. Needs a physician's signature.")}],
   ),

 phase("profound_shock",
   "Profound shock, obtunded",
   "profound shock",
   "Mean arterial pressure 43, obtunded, mottled. Reached from the hypotensive phase without "
   "fluid and a vasopressor, or from the supported phase with the source still in. Not "
   "terminal. Fluid, a vasopressor and source removal together get her out.",
   148, 66, 32, 30, 92, 39.8, 3, 2,
   [HANDOFF_T,
    {"when": PRESSOR + " AND " + FLUIDS + " AND " + SOURCE,
     "after_seconds": 15,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": ("She's coming back. Her pressure is up on the vasopressor, her rate is "
                   "down, and she's opening her eyes to my voice."),
     "debrief_note": (
       "She recovered a pressure once all three things were done: fluid, a vasopressor and "
       "removal of the source. She spent time at a mean pressure in the 40s on the way, and "
       "her kidneys and liver will show it over the next days."),
     "author_rationale": (
       "A delayed consequence of the learner's own action. That recovery from this phase is "
       "always possible is a teaching choice: the case has no death, so a learner who gets "
       "here can still find the answer. Model output.")}],
   authoring_note=(
     "No clock leaves this phase. A learner who does nothing further stays here until they "
     "hand over or end the case. That is a decision: the design guide asks that failure be "
     "recoverable, and this case has no arrest."),
   ),

 phase("stabilizing",
   "Source removed, holding on a vasopressor",
   "stabilizing",
   "Awake, mean arterial pressure 70 on a steady dose of a vasopressor, still febrile and "
   "tachycardic. This is the intended endpoint and she is not well. She needs intensive care.",
   116, 98, 56, 22, 97, 39.1, 1, 0,
   [HANDOFF_T],
   ),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   116, 98, 56, 22, 97, 39.1, 0, 0, [], terminal=True,
   inherit_vitals=True,
   schema_note=(
     "inherit_vitals: the monitor keeps the numbers of the phase the learner handed over "
     "from, so a patient handed over in shock is shown in shock. The authored vitals are the "
     "fallback and match the stabilizing phase."),
   ),
]
