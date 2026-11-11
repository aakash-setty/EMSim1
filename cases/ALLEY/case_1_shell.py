"""ALLEY part 1: identity, patient, phases.

Methanol poisoning from windshield washer fluid in a 52-year-old man brought in by EMS to
"sleep it off". Drafted by a language model on 11 November 2026 from a case structure and
answers supplied by Aakash Setty in the same conversation. No physician has reviewed this
pack. ALLEY-SEED.md says what a person decided and which sources were opened.

Six learning goals drive the structure (owner, 11 November 2026):

  1. When "just drunk" does not explain the respiratory rate and the ethanol, get a gas and a
     chemistry.
  2. Work both gaps, the anion gap and the osmolar gap with ethanol in the calculation.
  3. Ask about vision.
  4. Give fomepizole on suspicion, without waiting for a level, and know that it stops
     production and removes nothing.
  5. Give bicarbonate for the acidemia alongside the antidote, not instead of it.
  6. Call for dialysis on the indications, without a level.

Structure. Three untreated phases on an openly compressed clock (U0 presentation, U1
drifting, U2 untreated_floor, where he stays). Fomepizole moves each to a held phase frozen
at that tier (held_early, held_mid, held_late). Bicarbonate in a held phase, or fomepizole
while bicarbonate is acting, moves him to improving. Bicarbonate without fomepizole is an
overlay (an expiring flag with vital effects and flag-keyed results), not a phase, and the
clock keeps running under it. The patient never arrests on the clock (owner's design
constraint). Discharge ends the run in an authored terminal phase. A sedative from the
taggable list halts the run in the untreated and held phases.
"""

META = {
 "case_number": 10,
 "working_title": "52-year-old man found behind an auto parts store, brought in to sleep it off",
 "chief_complaint_patient_voice": "I'm just tired. Let me sleep.",
 "final_diagnosis": (
   "Methanol poisoning from drinking windshield washer fluid after his vodka ran out, with "
   "a high anion gap metabolic acidosis (pH 7.19, anion gap 30), an osmolar gap of 38 that "
   "his ethanol of 28 mg/dL does not explain, and visual impairment from formate. The send-out "
   "methanol level, revealed only in the debrief, is 96 mg/dL. He looks like the intoxicated "
   "regular the crew says he is."),
 "target_level": ["intern", "junior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "When the story says drunk and the respiratory rate and the ethanol level do not fit, get a blood gas and a chemistry and recognize a high anion gap metabolic acidosis.",
   "When lactate and ketones do not explain an anion gap, order a measured serum osmolality and calculate the osmolar gap with ethanol in it. A normal osmolar gap does not exclude a toxic alcohol.",
   "Ask an intoxicated patient about his vision. A new visual deficit is a clue to methanol and an indication for dialysis.",
   "Give fomepizole on suspicion without waiting for a methanol level, and know that it stops formate being made and removes none of it.",
   "Give sodium bicarbonate for a pH under 7.30 alongside the antidote. Without it the effect wears off because acid production continues.",
   "Call nephrology for dialysis on the indications (new vision deficit, anion gap above 24, pH 7.15 or lower) without waiting for a level.",
 ],
 "teaching_frame": (
   "He is the patient everyone has seen before. The crew knows him, the triage note says "
   "he is here to sober up, and he looks it. The only things out of place are a respiratory "
   "rate of 27 with clear lungs, an ethanol level too low for how he looks, and eyes he "
   "keeps rubbing. The case rewards the learner who chases the number the story does not "
   "explain, and then shows that the antidote changes nothing on the monitor."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Adult emergency department with intensive care, nephrology and hemodialysis on site, "
     "and a regional poison center by phone. Toxic alcohol levels are a send-out with a "
     "turnaround of a day or more."),
 },
 "arrival": {
   "mode": "ems",
   "location": "patient_room",
   "line": "Brought in by EMS from behind an auto parts store to a patient room to sleep it off.",
 },
 "complaint": "Intoxication, found outside",
 "category": "Toxicology",
 "library": {
   "tempo": "a slow drift on an openly compressed clock, then a floor",
   "uncertainty": "the diagnosis, hidden behind a common label, and whether to treat before confirmation",
   "right_answer": "act on suspicion, then ask someone (nephrology) for the definitive step",
   "danger": "in the triage note and in a test nobody orders by default; the antidote changes nothing visible",
   "setting": "52 M, unhoused, brought by EMS who know him, to a patient room, alone",
   "feel": "mundane, then unsettling",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Descriptive, not clinical: no physician has reviewed the wording.",
 },
}

PATIENT = {
 "age": 52,
 "sex": "male",
 "weight_kg": 68,
 "background": (
   "Long history of heavy drinking. Lives outside, mostly around the same few blocks. Known "
   "to the department and to the ambulance crews for intoxication. No other medical history "
   "he can give, no medications, no allergies. Smokes. Gets the shakes when he stops "
   "drinking, no known withdrawal seizures.\n\n"
   "His vodka ran out last night. Some time after that he drank most of a jug of blue "
   "windshield washer fluid he found. He cannot say when. The empty jug is in his "
   "backpack. He has not eaten for a couple of days. Since waking he has felt sick, with "
   "a pounding headache and an aching stomach, and everything has looked blurry and white. "
   "Someone saw him sitting slumped behind an auto parts store and called 911. He was not "
   "trying to hurt himself."),
 "presenting_vitals_source": "Inherited from phase 'presentation'.",
 "presenting_appearance": (
   "A thin, disheveled man dozing on the stretcher, slurring when roused, unsteady when "
   "moved. Breathing fast and deep. Faint smell of alcohol. Cooperative."),
 "arrival_handover": (
   "Fifty-two year old man, found sitting behind an auto parts store, slurring and unsteady "
   "on his feet. We know him, we bring him in to sleep it off."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 30 words. No vital sign, no medication, no precipitant. "
   "The second sentence departs from the default: it carries history and the crew's "
   "framing. That framing is the anchoring the case is built to teach (owner's structure, "
   "11 November 2026). It is never false: he is intoxicated, just not only that."),
 "avatar": {"build": "thin"},
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp, distress, alert,
          transitions, ecg, pupil_size="normal", terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": pupil_size, "pupil_reactivity": "sluggish"},
      "rhythm": "regular",
      "ecg": ecg,
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


# Monitor blocks carry the intervals of the borrowed tracings (media/README.md).
ECG_114 = {"pattern": "organised", "p_waves": True, "pr_ms": 140, "qrs_ms": 84, "qtc_ms": 430,
           "author_note": "Intervals of the tracing shown for this phase (TSS stabilizing set, read at 114). Model output."}
ECG_116 = dict(ECG_114, author_note="Intervals of the tracing shown for this phase (read at 116). Model output.")
ECG_96 = {"pattern": "organised", "p_waves": True, "pr_ms": 150, "qrs_ms": 88, "qtc_ms": 410,
          "author_note": "Intervals of the tracing shown for this phase (SCOOT decline set, read at 96). Model output."}

HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}
DISCHARGE_T = {"when": "action attempt_discharge taken", "to": "discharged",
               "author_rationale": (
                 "Owner, 11 November 2026: discharge is a case failure, shown as an end line "
                 "rather than a halt. An instant move into an authored terminal phase. The "
                 "nurse's words are on the action, since an instant transition speaks no "
                 "narration.")}

FOMEP = "flag fomepizole_given set"
BUFFERED = "flag bicarb_acting set"

TO_IMPROVING = {"when": FOMEP + " AND " + BUFFERED, "to": "improving",
                "author_rationale": (
                  "Fomepizole given while bicarbonate is still acting (owner's rule I2). "
                  "Production has stopped and the acid already there is buffered. Model output.")}


def held(dest):
    return {"when": FOMEP, "to": dest,
            "author_rationale": (
              "Fomepizole blocks alcohol dehydrogenase, so no more formate is made. Nothing "
              "has buffered or removed the formate already there, so the patient is frozen "
              "at this tier (owner's structure, rule I1). Frozen is a simplification: over "
              "hours the acidosis may slowly improve once production stops. Model output.")}


CLOCK_RATIONALE = (
  "Scheduled natural history, openly compressed. Untreated methanol keeps being turned into "
  "formate, so the acidosis deepens and vision worsens over hours. 360 seconds to the "
  "second tier and 180 more to the worst (owner, 11 November 2026) stand for a couple of "
  "hours each. Fomepizole is an instant exit from this phase, so this rule fires "
  "only on a patient who never got it. No prompt warns of it by name: the owner decided "
  "on 11 November 2026 that the nurse cues (fast breathing, squinting, an ethanol that does "
  "not fit) are the warning, because a prompt for the antidote would give away goal 4. "
  "TIDE uses the same shape.")

AWAY_RATIONALE = (
  "Delayed consequence of the learner's own action. A CT before the antidote, or sending "
  "him to the hallway to sleep it off, takes him away for what would be the better part of "
  "an hour, and untreated formate production continues. The move is to the phase that time "
  "would have produced. Credited to a hidden target only when ordered in this phase, so it "
  "happens once. Five seconds is the validator's floor, not a clinical claim. Owner's "
  "structure (I11, I12), 11 November 2026.")

INTO_U1 = ("We're moving the clock faster here. Over what would be a couple of hours, his "
           "breathing has gotten deeper. He threw up once, and he keeps rubbing his eyes.")
INTO_U1_VENT = "We're moving the clock faster here. Over what would be a couple of hours, his gas has gotten worse."
INTO_U2 = ("He's working to breathe now and talking in short phrases. He reached for the cup "
           "I handed him and missed it. We're holding the clock here. Untreated, he would keep "
           "getting worse over the next hours.")
INTO_U2_VENT = "His gas has gotten worse. We're holding the clock here. Untreated, he would keep getting worse."

U1_NOTE = (
  "Nobody blocked alcohol dehydrogenase, so methanol kept being turned into formate. His pH "
  "fell from 7.19 to 7.15, his anion gap rose, and his vision got worse. From the doorway he "
  "looked the same. The monitor and the gas did not.\n\n"
  "Fomepizole on suspicion would have stopped this. It does not need a methanol level."
  " [UNVERIFIED: fomepizole prescribing information, read through search]")
U2_NOTE = (
  "Another stretch without the antidote. His pH is 7.12, he is working to breathe, and he can "
  "only see light and shapes.\n\n"
  "The case holds him here and he never crashes. That is a design choice. Untreated methanol "
  "poisoning goes on to coma, seizures and death, and a pH under 7.0 with coma predicts "
  "death. An awake, talking patient with methanol poisoning is not safe to watch.")


def away(target, dest, flag, narration):
    return {"when": "action " + target + " taken", "after_seconds": 5,
            "measured_from": "guard_true", "to": dest, "flags_set": [flag],
            "narration": narration,
            "narration_ventilated": "He's back. His gas is worse than when he left.",
            "debrief_note": (
              "He went to CT or to the hallway before anyone blocked the alcohol "
              "dehydrogenase, and formate kept being made while he was away. A CT is "
              "reasonable in an altered drinker found outside. After the fomepizole, not "
              "before it."),
            "author_rationale": AWAY_RATIONALE}


PHASES = [
 phase("presentation",
   "Untreated methanol poisoning, arrival tier",
   "on arrival",
   "Looks drunk: slurred, dozing, unsteady. Breathing fast and deep with clear lungs and a "
   "normal saturation. pH 7.19, pCO2 19, bicarbonate 7, anion gap 30, osmolar gap 38, "
   "ethanol 28. Vision blurry and white. Already meets two dialysis indications (anion gap "
   "above 24, new vision deficit).",
   112, 132, 84, 27, 99, 36.6, 1, 1,
   [HANDOFF_T, DISCHARGE_T, TO_IMPROVING, held("held_early"),
    away("away_from_u0", "drifting", "reached_u1",
         "He's back. While he was away he threw up, and his breathing's deeper."),
    {"when": None, "after_seconds": 360, "to": "drifting", "flags_set": ["reached_u1"],
     "narration": INTO_U1, "narration_ventilated": INTO_U1_VENT,
     "debrief_note": U1_NOTE, "author_rationale": CLOCK_RATIONALE,
     "unguarded_rationale": CLOCK_RATIONALE}],
   ECG_114),

 phase("drifting",
   "Untreated methanol poisoning, second tier",
   "breathing deeper",
   "Looks the same from the door. Breathing deeper, has vomited, rubbing his eyes, dozes "
   "mid-sentence. pH 7.15, anion gap 31. Cannot make out faces. Meets the pH, anion gap and "
   "vision indications for dialysis.",
   114, 130, 82, 30, 99, 36.6, 1, 1,
   [HANDOFF_T, DISCHARGE_T, TO_IMPROVING, held("held_mid"),
    away("away_from_u1", "untreated_floor", "reached_u2",
         "He's back. He's working harder to breathe than when he left."),
    {"when": None, "after_seconds": 180, "to": "untreated_floor", "flags_set": ["reached_u2"],
     "narration": INTO_U2, "narration_ventilated": INTO_U2_VENT,
     "debrief_note": U2_NOTE, "author_rationale": CLOCK_RATIONALE,
     "unguarded_rationale": CLOCK_RATIONALE}],
   ECG_114),

 phase("untreated_floor",
   "Untreated methanol poisoning, worst tier, held by design",
   "working to breathe",
   "Breathing is work, short phrases, confused, reaches for things and misses. pH 7.12, "
   "anion gap 32. Sees light and shapes only. Pupils 6 mm, barely reactive. No clock leaves "
   "this phase. The floor is the owner's design constraint, stated openly in the narration.",
   116, 126, 80, 32, 98, 36.6, 2, 1,
   [HANDOFF_T, DISCHARGE_T, TO_IMPROVING, held("held_late")],
   ECG_116, pupil_size="large"),

 phase("held_early",
   "Fomepizole given at the arrival tier",
   "not getting worse",
   "Identical to arrival. No more formate is being made, and nothing has buffered or "
   "removed what is there. A repeat gas is unchanged. Vision locked at the arrival tier.",
   112, 132, 84, 27, 99, 36.6, 1, 1,
   [HANDOFF_T, DISCHARGE_T,
    {"when": BUFFERED, "to": "improving",
     "author_rationale": "Bicarbonate with alcohol dehydrogenase blocked (owner's rule I3). Model output."}],
   ECG_114),

 phase("held_mid",
   "Fomepizole given at the second tier",
   "not getting worse",
   "Identical to the second tier, frozen. Vision locked at the second tier.",
   114, 130, 82, 30, 99, 36.6, 1, 1,
   [HANDOFF_T, DISCHARGE_T,
    {"when": BUFFERED, "to": "improving",
     "author_rationale": "Bicarbonate with alcohol dehydrogenase blocked (owner's rule I3). Model output."}],
   ECG_114),

 phase("held_late",
   "Fomepizole given at the worst tier",
   "not getting worse",
   "Identical to the worst tier, frozen. Vision locked at light and shapes.",
   116, 126, 80, 32, 98, 36.6, 2, 1,
   [HANDOFF_T, DISCHARGE_T,
    {"when": BUFFERED, "to": "improving",
     "author_rationale": "Bicarbonate with alcohol dehydrogenase blocked (owner's rule I3). Model output."}],
   ECG_116, pupil_size="large"),

 phase("improving",
   "Antidote and bicarbonate on board",
   "breathing easier",
   "Still slurred and unsteady, breathing easier, more conversational. pH 7.29, bicarbonate "
   "12, anion gap 28. The gap persists because formate is buffered, not removed, and the "
   "vision he had when he was held persists. What removes formate is dialysis.",
   96, 130, 80, 22, 99, 36.6, 1, 1,
   [HANDOFF_T, DISCHARGE_T],
   ECG_96),

 phase("discharged",
   "Discharged home untreated or before dialysis",
   "sent out",
   "Terminal phase entered when the learner confirms discharge home. The run ends here.",
   112, 132, 84, 27, 99, 36.6, 1, 1, [],
   ECG_114, terminal=True, inherit_vitals=True,
   timeout_reason=("He was brought back four hours later, unresponsive."),
   authoring_note=(
     "Owner, 11 November 2026: discharge is a case failure, and the end line is his own "
     "words. Reached by one action route only. Inherits the vitals of the phase it came "
     "from.")),

 phase("halted",
   "Case halted after a harmful action",
   "stopped",
   "Terminal phase entered directly when a harmful action is taken (a sedative in the "
   "untreated or held phases), carrying the action's halt reason. Not reached through "
   "transition rules.",
   124, 100, 60, 10, 90, 36.4, 0, 2, [],
   ECG_116, terminal=True,
   schema_gap_note=(
     "Numbers for a man whose compensatory breathing has been taken away by a sedative: "
     "slower, shallower breathing, a falling saturation, a falling pressure. The learner "
     "never sees them: the run ends at once and the debrief opens with the halt reason.")),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   96, 130, 80, 22, 99, 36.6, 1, 1, [],
   ECG_96, terminal=True, inherit_vitals=True),
]
