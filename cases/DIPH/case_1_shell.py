"""DIPH part 1: identity, patient, phases.

Case author: Kelly Medwid, MD. See DIPH-SEED.md for what is hers and what is not.
"""

META = {
 "case_number": 4,
 "working_title": "18-year-old woman, confusion and fever, brought in by EMS",
 "chief_complaint_patient_voice": (
   "Her mother: 'She wasn't making any sense and she didn't know who I was.'"),
 "final_diagnosis": (
   "Diphenhydramine overdose producing an anticholinergic toxidrome with hyperthermia and "
   "delirium, complicated by cardiac sodium-channel blockade with QRS prolongation and by a "
   "generalized seizure. The teaching claim of the case is that the second half of that "
   "sentence changes the management and the first half does not.\n\n"
   "The primary diagnosis is dx_diphenhydramine_overdose, which names the agent. The "
   "cardiotoxicity is dx_sodium_channel_blocker_cardiotoxicity and is the first of the five "
   "additional diagnoses, because it is the finding that decides the management. Both "
   "entries were added to the diagnosis catalog on 5 September 2026 for this case; before "
   "that the correct answer had to be recorded as the anticholinergic toxidrome, which is "
   "the thing the case exists to say is not the whole story. The toxidrome is now scored "
   "twice, as credit when it is named beside the agent and as a defensible-but-incomplete "
   "answer when it is offered as the primary."),
 "target_level": ["junior_resident", "senior_resident"],
 "estimated_runtime_seconds": 720,
 "learning_objectives": [
   # Physician review DIPH-35 (Aakash Setty, 27 October 2026): rewritten as behaviors the
   # case can observe, within six. Objectives 2 and 3 merged, 5 rewritten, and toxicology and
   # critical care added. Model wording.
   "Examine for and name the bedside features of diphenhydramine toxicity: the delirium, the large pupils, the dry hot skin, the absent bowel sounds, the full bladder and the temperature.",
   "Order a twelve-lead ECG early in any significant overdose, and act on the signs of cardiac sodium-channel blockade: a QRS over 100 milliseconds, a terminal R wave in aVR and a rightward terminal axis.",
   "Give sodium bicarbonate for a wide QRS or a wide-complex rhythm, and repeat it against the QRS and the blood pressure rather than a fixed number of ampoules.",
   "Withhold physostigmine while the QRS is wide.",
   "Treat the agitation, the seizure and the hyperthermia with benzodiazepines, sedation and active cooling, not with antipsychotics and antipyretics.",
   "Call toxicology early and arrange a critical care bed for a poisoning with a wide QRS.",
 ],
 "teaching_frame": (
   "A resident who reaches the end of this case having recognized an anticholinergic toxidrome, "
   "and having done nothing about the QRS, has failed the case while feeling that they passed "
   "it. The toxidrome is easy and visible and is on the first page of every toxicology lecture. "
   "The conduction abnormality is on a tracing nobody has ordered yet, and it is what kills her. "
   "Everything in the case is arranged so that the satisfying answer arrives before the "
   "dangerous one."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Adult and pediatric emergency department at a hospital with a medical toxicology service, "
     "a regional poison center on the telephone, intensive care beds and inpatient psychiatry. "
     "Full laboratory and imaging on site. Nothing in this case is limited by resources."),
   "provenance": (
     "Setting is a deployment property and not a clinical fact. The author did not specify one. "
     "It is drafted this way because the disposition question here is about level of care rather "
     "than about transfer, and because a case written for a hospital with no toxicology service "
     "would have a different right answer to the consultation question and the same right answer "
     "to everything else."),
 },
 "arrival": {
   "mode": "ems",
   "location": "resuscitation_bay",
   "line": "Brought in by EMS from home. Handover given on arrival in the resuscitation bay, with her mother following the crew in.",
 },
 "complaint": "Confusion and fever",
 "category": "Toxicology",
 "library": {
   "tempo": "minutes: the seizure and the arrest run on a clock",
   "uncertainty": "the diagnosis, anticholinergic delirium against sodium channel blockade, and whether to give the antidote",
   "right_answer": "do less: no physostigmine, treat the QRS",
   "danger": "behind the fever and the confusion, on the ECG",
   "setting": "18 F, EMS to the resuscitation bay, her mother answers for her, tracings shown as pictures",
   "feel": "tense",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Printed in docs/generated/case-index.md so a new case can say how it differs. Descriptive, not clinical: no physician has reviewed the wording."
 },
}

PATIENT = {
 "age": 18,
 "sex": "female",
 "weight_kg": 60,
 "background": (
   "No past medical history and no past surgical history. On no regular medication. No known "
   "drug allergies. She gets occasional allergic reactions (hives) and keeps her own bottle "
   "of Benadryl in her bedroom for them. Family history of hypertension on her mother's side. She is in her final "
   "year at school and lives at home with her mother and a younger brother.\n\n"
   "Not known to the department and not known to the resident: for the past several months she "
   "has been increasingly low. She has been bullied on social media, she broke up with her "
   "boyfriend a few weeks ago, and she has stopped speaking to several friends since. About four "
   "hours before her mother came home from work she swallowed the contents of her own bottle "
   "of diphenhydramine. The bottle is on the floor beside her bed and nobody has looked for it."),
 "presenting_vitals_source": (
   "Inherited from phase 'presentation'. The crew put no oxygen on her and got no line in on the "
   "way. The temperature is the one the department measured, not one the crew reported."),
 "presenting_appearance": (
   "A young woman lying on the trolley, awake, flushed and pouring off heat, plucking at the "
   "sheet and at the monitoring leads. She looks past you rather than at you and answers "
   "questions with words that do not go together. She pushes hands away when anyone reaches for "
   "her. Her skin is hot and completely dry."),
 "ems_handover_text": (
   "Eighteen year old female, mom came in from work about an hour ago and found her like this in "
   "her bedroom. Mom says she was asleep when she left this morning. She's been confused the whole "
   "way in, doesn't know where she is, kept trying to get off the trolley. She's very warm to "
   "touch and she's dry as a bone. Rate was 130 to 140 on our monitor, regular. We didn't get a "
   "line in, she wouldn't have it. No injuries we could find. Mom's just behind us."),
 "arrival_handover": (
   "Eighteen year old, her mom found her like this when she got in from work about an hour ago. "
   "She's been fighting us the whole way in and she's burning up."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 32 words, no vital sign, no past history, no medication, no "
   "allergy, no pertinent negative and no word that names a diagnosis. It is deliberately worse "
   "than the ems_handover_text above it: the crew knows more than this, and a resident who wants "
   "it has to ask for it. 'Burning up' is a lay description of what anyone touching her would "
   "feel and is not a temperature."),
}

# ---------------------------------------------------------------- phases
#
# Six clinical phases and three terminals. The authoring document capped the clinical count at six at the time, and
# this case uses all six, so there is deliberately NO separate intubated phase. Intubation
# sets a flag, moves the saturation through a vital effect and changes the airway and
# general-status content, and it does not change the phase. Two reasons, and the second is
# the one that matters:
#
#   1. The six slots are spent on the two axes the case actually turns on, which are whether
#      the seizure has been treated and whether the sodium-channel blockade has been treated.
#   2. In every other pack an intubated phase sits at alertness 3 and ends the interview.
#      Here the historian is the mother, who is standing in the corridor and is not sedated.
#      Gating the history on the patient's airway would be wrong. See case_4_interview.
#
# Oxygen saturation in every phase is the UNSUPPORTED baseline (section 16). A cannula, a
# non-rebreather and an endotracheal tube each add to it through vital effects that share one
# key, so they replace one another rather than stacking. Temperature in every phase is the
# UNCOOLED baseline; active cooling subtracts 0.9 through its own effect. If either is
# rebased wrongly the gain is counted twice and validator rule V will say so.
#
# Pupils are large in every phase including the resolution phases, because the mydriasis
# outlasts the cardiotoxicity by many hours and a resident who rechecks them late in the case
# should not find them normal. Rhythm is regular everywhere: nothing in this case turns on an
# irregular beat, and irregularly_irregular would be a claim the source does not make.

def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, temp,
          distress, alert, transitions, terminal=False, pupil="large", react="reactive",
          rhythm="regular", **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": temp},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": pupil, "pupil_reactivity": react},
      "rhythm": rhythm,
      # The monitor's lead (authoring 5.2), looked up by phase id from ECG below so the
      # picture and the phase's ECG report are authored from one set of numbers.
      **({"ecg": ECG[pid]} if pid in ECG else {}),
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d

# What the monitor draws in each phase: lead II, from the same figures as the phase's
# ecg_12_lead report, so the tracing on the wall and the tracing in the chart cannot
# disagree. The QRS is the clock in this case, and this is where the resident watches it
# widen and, after bicarbonate, narrow. Every figure carries the provenance of the report
# it comes from, and the arrival report's own verify note applies to all of them: the
# source gives no measurements, so every millisecond here is model output awaiting the
# author's signature.
ECG_SOURCE = ("Figures from this phase's ecg_12_lead report, whose verify note says every "
              "number in it is model output: the source gives no measurements. "
              "[UNVERIFIED, confirm before release]")
ECG = {
  "presentation": {"p_waves": True, "qrs_ms": 132, "qtc_ms": 495,
                   "verify": "Arrival tracing: QRS 132 ms, QTc 495 ms. " + ECG_SOURCE},
  "seizing": {"p_waves": True, "qrs_ms": 148, "qtc_ms": 512,
              "verify": ("Seizing tracing: QRS 148 ms, QTc 512 ms. The report also describes "
                         "frequent ventricular ectopics and movement artifact, neither of which "
                         "the monitor draws; the trace shows the widened sinus complexes and "
                         "nothing else. " + ECG_SOURCE)},
  "post_ictal": {"p_waves": True, "qrs_ms": 132, "qtc_ms": 495,
                 "verify": ("No tracing is authored for this phase; the phase description says "
                            "the QRS is unchanged at around 130 ms, so the arrival figures are "
                            "carried. " + ECG_SOURCE)},
  "wide_complex_tachycardia": {"p_waves": False, "qrs_ms": 180,
                               "verify": ("Monomorphic wide-complex tachycardia at 180 with a "
                                          "QRS of 180 ms and no discernible P waves, as the "
                                          "report says. The terminal R in aVR and the rightward "
                                          "axis are not visible in lead II. " + ECG_SOURCE)},
  "stabilizing": {"p_waves": True, "qrs_ms": 104, "qtc_ms": 470,
                  "verify": "Stabilizing tracing: QRS 104 ms, QTc 470 ms. " + ECG_SOURCE},
  "stabilized": {"p_waves": True, "qrs_ms": 96, "qtc_ms": 445,
                 "verify": "Stabilized tracing: QRS 96 ms, QTc 445 ms. " + ECG_SOURCE},
  "pulseless_vt": {"p_waves": False, "qrs_ms": 200,
                   "verify": ("Wide-complex tachycardia at 190 with a QRS of 200 ms and no "
                              "mechanical activity: the same rhythm as the phase before it, "
                              "faster and wider, which is what the nurse says she sees. "
                              + ECG_SOURCE)},
  "halted": {"p_waves": False, "qrs_ms": 200,
             "verify": ("MODEL OUTPUT, NOT IN THE SOURCE. The halted phase carries generic "
                        "bradycardic peri-arrest numbers (see the CHANGELOG entry on amiodarone), "
                        "so the monitor draws a slow, wide, P-less idioventricular rhythm. A "
                        "reviewer who prefers asystole sets pattern to asystole here. "
                        "[UNVERIFIED, confirm before release]")},
  "case_complete": {"p_waves": True, "qrs_ms": 100, "qtc_ms": 460,
                    "author_note": ("Handed over between the stabilizing and stabilized figures, "
                                    "as the vitals for this phase are; no tracing is authored for "
                                    "it.")},
}

# v0.18a: the actions that end a convulsion in this case. Used by every guard that asks
# whether the seizure has been treated, so a benzodiazepine and propofol count the same way.
SEIZURE_STOPPED = "(flag benzo_given set OR action propofol_bolus taken OR action propofol_infusion taken)"

HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list so that a handoff is never overtaken by a "
                            "clinical rule in the same step."}

# The author's own sentence, and the reason the first deterioration in this case is unguarded.
SEIZURE_RATIONALE = (
  "The author writes, of the seizure: 'A seizure will occur as part of the natural process, "
  "regardless of how well the examinee is doing.' That is a scheduled natural history in the "
  "sense of authoring section 15.1, and the rule carries no guard, exactly as she wrote it. "
  "The clinical claim behind it is hers: a patient four hours into a diphenhydramine "
  "ingestion large enough to widen the QRS is going to seize. The deadline is her own four "
  "minutes, carried at its authored value.\n\n"
  "From 5 September to 27 October 2026 a rule above this one moved a patient who had received "
  "both sodium bicarbonate and a benzodiazepine out of the arrival phase before four minutes, "
  "so the seizure could be avoided. Physician review DIPH-01 (Aakash Setty, 27 October 2026) "
  "deleted that escape and restored the author's sentence: every run that has not ended by "
  "four minutes seizes.")

SEIZURE_NARRATION = (
  "She's stiffened up and she's seizing. I'm putting her on her side and I've got the suction. "
  "Her sats are dropping.")

SEIZURE_NOTE = (
  "She seized at four minutes. The case schedules this: the case author wrote it as the "
  "natural history of the ingestion, and it happens in every run whatever was done before it. "
  "It does not mean you did something wrong. What the four minutes before it were for was the "
  "monitor, the line, the glucose and above all the ECG, because the seizure is far easier to "
  "manage in a patient whose conduction you already understand. Bicarbonate given before it is "
  "not wasted: it narrows the QRS once the convulsion has stopped.\n\n"
  "The physiology worth carrying away: the seizure is not an isolated neurological event here. "
  "Convulsion produces lactate and carbon dioxide, and acidemia increases the fraction of the drug that is ionized, which is the charged form that binds the cardiac sodium channel. A seizure in a "
  "sodium-channel-blocker overdose therefore makes the cardiotoxicity worse while it is "
  "happening, which is why it is terminated with a benzodiazepine at once and why ventilation "
  "matters as much as the anticonvulsant does.")

# Physician review DIPH-23 (Aakash Setty, 27 October 2026): phenytoin stays discouraged and
# now has a consequence, on arrival and after the seizure.
PHENYTOIN_NARRATION = (
  "Her rate's gone up and the complexes on the monitor have gone broad since the phenytoin. "
  "She's still got a pressure but it's down.")
PHENYTOIN_NOTE = (
  "Phenytoin widened her QRS into a wide-complex tachycardia. It acts on the same cardiac "
  "sodium channels the diphenhydramine is already blocking, so it added to a block that was "
  "already 132 milliseconds wide. The treatment now is sodium bicarbonate.\n\n"
  "For a seizure in this poisoning, give a benzodiazepine, then propofol or levetiracetam if "
  "it recurs. Not phenytoin.")
PHENYTOIN_RATIONALE = (
  "Physician review DIPH-23 (Aakash Setty, 27 October 2026), option C: discouraged with a "
  "consequence. The direction follows the author's warning that Dilantin 'should be avoided "
  "since it also prolongs sodium channels'. The ten seconds is invented and matches the "
  "case's other drug effects. The harm is extrapolated from tricyclic and animal data rather "
  "than shown in humans, which is why the tag stays discouraged rather than harmful.")

# v0.18a: the physostigmine seizure arrow and its narration were removed. Physostigmine is
# harmful in every phase in which the QRS is wide, so the arrow could never fire.

PHASES = [
 phase("presentation",
   "Anticholinergic toxidrome with unrecognized sodium-channel blockade",
   "on arrival",
   "Awake, delirious, agitated and hyperthermic, with dry hot skin, mydriasis, absent bowel "
   "sounds and a palpable bladder. The QRS is already 132 milliseconds and nobody has looked "
   "at it. She is perfusing and her saturation is normal.",
   135, 130, 75, 25, 98, 40.1, 3, 0,
   [HANDOFF_T,
    # Physician review DIPH-01 (Aakash Setty, 27 October 2026): the escape that took a
    # patient given bicarbonate and a benzodiazepine to the narrowing phase before four
    # minutes is deleted. Every run that has not ended by 240 seconds seizes.
    {"when": "action fos_phenytoin taken",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "wide_complex_tachycardia",
     "narration": PHENYTOIN_NARRATION,
     "debrief_note": PHENYTOIN_NOTE,
     "author_rationale": PHENYTOIN_RATIONALE},
    {"when": None,
     "after_seconds": 240,
     "measured_from": "phase_entry",
     "to": "seizing",
     # She has now seized, which the wide-complex phase reads (DIPH-29 and the phenytoin route).
     "flags_set": ["seized"],
     "narration": SEIZURE_NARRATION,
     "debrief_note": SEIZURE_NOTE,
     "author_rationale": SEIZURE_RATIONALE,
     "unguarded_rationale": SEIZURE_RATIONALE}],
   ),

 phase("seizing",
   "Generalized tonic-clonic seizure",
   "seizing",
   "Generalized convulsion with no airway protection and falling saturation. Entered on the clock at four minutes, which is the author's natural history, or from the wide-complex phase when bicarbonate has been given without an anticonvulsant. The QRS is wider than on arrival.",
   150, 145, 90, 8, 84, 40.4, 3, 3, react="sluggish",
   transitions=[HANDOFF_T,
    {"when": SEIZURE_STOPPED, "to": "post_ictal",
     "author_note": "Instantaneous. A benzodiazepine terminates most drug-induced seizures "
                    "within a minute or two and the case does not model the delay, because "
                    "nothing here turns on how long it takes."},
    {"when": "NOT " + SEIZURE_STOPPED + " AND NOT flag bicarb_given set",
     "after_seconds": 120,
     "measured_from": "phase_entry",
     "to": "wide_complex_tachycardia",
     "narration": "She's still seizing and the complexes on the monitor have gone broad and fast. Her pressure's down to ninety-five.",
     "debrief_note": (
       "Two minutes of untreated convulsion took her into a wide-complex tachycardia. The chain "
       "is the one the seizure note describes: the convulsion produces a lactic and respiratory "
       "acidosis, the acidemia increases the ionized fraction of the drug, the form that binds the cardiac sodium channel, and conduction that was already slowed slows further until the "
       "ventricle takes over.\n\n"
       "The action that would have prevented this is a benzodiazepine, and the nurse asked for "
       "one twice. Once the wide-complex rhythm is established the treatment is sodium "
       "bicarbonate, and the benzodiazepine is still needed."),
     "author_rationale": (
       "Two minutes of continuous convulsion in a patient who is already acidemic at pH 7.28 "
       "with a QRS of 132 milliseconds. The number is a drafting judgment and not the "
       "author's: she specifies that the seizure happens and that lorazepam and bicarbonate "
       "are given, and does not say how long an untreated seizure is tolerated. It is set at "
       "the shorter end of what is defensible because the case has already established the "
       "acidemia. Needs the author's signature.")},
    # Physician review DIPH-09 (Aakash Setty, 27 October 2026), option B: a one-time relapse.
    {"when": "NOT " + SEIZURE_STOPPED + " AND flag bicarb_given set AND NOT flag seizure_relapsed set",
     "after_seconds": 180,
     "measured_from": "phase_entry",
     "to": "wide_complex_tachycardia",
     "flags_set": ["seizure_relapsed"],
     "narration": "She's still seizing, and the complexes on the monitor have gone broad and fast again. Her pressure's down.",
     "debrief_note": (
       "Bicarbonate without an anticonvulsant bought time and did not end the problem. She kept "
       "seizing for three minutes, the convulsion went on making heat and acid, and the QRS "
       "widened back into a wide-complex tachycardia. The bicarbonate already given is used "
       "up: the rhythm needs a fresh dose.\n\n"
       "Bicarbonate treats the conduction. A benzodiazepine is what ends the seizure, and the "
       "nurse asked for one."),
     "author_rationale": (
       "Physician review DIPH-09 (Aakash Setty, 27 October 2026), option B. A seizure treated "
       "with bicarbonate and no anticonvulsant relapses once into the wide-complex rhythm, "
       "three minutes after this phase is entered. It happens once: the transition grants "
       "seizure_relapsed, and the guard needs it unset. In the wide-complex phase only a "
       "bicarbonate dose given after the relapse (flag bicarb_after_relapse) narrows the rhythm "
       "again. Three minutes is invented and needs a signature. No second arrest clock is "
       "authored for the relapsed rhythm: she stays in it until fresh bicarbonate is given.")}],
   ),

 phase("post_ictal",
   "Post-ictal, still hyperthermic, QRS still wide",
   "post-ictal",
   "The convulsion has stopped. She is drowsy and not protecting her airway well. Still hot, "
   "still tachycardic, and the QRS is unchanged at around 130 milliseconds because nothing has "
   "been done about it.",
   140, 120, 70, 16, 92, 40.2, 2, 1, react="sluggish",
   transitions=[HANDOFF_T,
    {"when": "flag bicarb_given set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": "The complexes are getting narrower. That's since the bicarb went in.",
     "debrief_note": (
       "The QRS narrowed after sodium bicarbonate. Ten seconds is a heavy compression of "
       "something that in practice takes a minute or two and is watched for on serial "
       "tracings, and the delay is authored rather than making the change instantaneous "
       "because a number that moves on the same click as the injection teaches that "
       "bicarbonate is a button.\n\n"
       "Both halves of the mechanism matter. The sodium load raises the electrochemical "
       "gradient across a channel that is partially blocked, and the alkalinization reduces "
       "the fraction of drug bound to it. That is why hyperventilation alone is not the same "
       "treatment and why hypertonic saline is the rescue when alkalemia is already at its "
       "ceiling."),
     "author_rationale": (
       "A delayed consequence of the resident's own action, so the five-second floor applies. "
       "The size of the compression is a drafting judgment.")},
    # After the bicarbonate rescue, so a resident who gives both at once is rescued.
    {"when": "action fos_phenytoin taken",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "wide_complex_tachycardia",
     "narration": PHENYTOIN_NARRATION,
     "debrief_note": PHENYTOIN_NOTE,
     "author_rationale": PHENYTOIN_RATIONALE},
    {"when": "NOT flag bicarb_given set",
     "after_seconds": 180,
     "measured_from": "phase_entry",
     "to": "wide_complex_tachycardia",
     "narration": "Her rate's gone up and the complexes have gone broad. She's still got a pressure but it's down.",
     "debrief_note": (
       "Untreated sodium-channel blockade progressed to a wide-complex tachycardia. The ECG "
       "had shown a QRS of 132 milliseconds and a terminal R wave in aVR, the nurse had said "
       "so, and no bicarbonate was given. QRS prolongation in this poisoning is not a "
       "curiosity to be monitored; it is the marker that identifies the patients who go on to "
       "have ventricular dysrhythmias, and it is the indication to treat.\n\n"
       "The one thing to take from this branch: she was post-ictal and looked calmer, and "
       "calmer is not better. Clinical improvement in the agitation says nothing about the "
       "conduction."),
     "author_rationale": (
       "Three minutes of untreated sodium-channel blockade in a patient with an established "
       "QRS of 132 milliseconds who has just convulsed. The direction is the author's, who "
       "writes that without bicarbonate the patient 'will first develop hemodynamically "
       "stable ventricular tachycardia (VT), then pulseless VT'. The three minutes is a "
       "drafting judgment and needs the author's signature.")}],
   ),

 phase("wide_complex_tachycardia",
   "Hemodynamically stable wide-complex tachycardia",
   "wide-complex",
   "Monomorphic wide-complex tachycardia at 180 from untreated sodium-channel blockade. She "
   "still has a blood pressure and she still has a pulse. This is the author's stable VT and it "
   "is the last phase in which bicarbonate can still turn the case around.",
   180, 95, 60, 22, 90, 40.0, 3, 2, react="sluggish",
   transitions=[HANDOFF_T,
    # Physician review DIPH-12 (Aakash Setty, 27 October 2026): the amiodarone arrest arrow
    # is deleted. Amiodarone now drops her pressure through a vital effect on the action.
    #
    # Physician review DIPH-09: after a relapse (seizure_relapsed, granted by the seizing
    # phase's relapse rule) only a dose given after it (bicarb_after_relapse) works, so each
    # bicarbonate rule has a relapse twin. Separate rules rather than one OR, so each has its
    # own guard_true clock.
    {"when": "flag bicarb_given set AND NOT flag seizure_relapsed set AND " + SEIZURE_STOPPED,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": "The complexes have narrowed and the rate's come down. That's the bicarb.",
     "debrief_note": (
       "Sodium bicarbonate terminated the wide-complex rhythm. This is the treatment for a "
       "wide-complex tachycardia caused by sodium-channel blockade, and it is not the treatment "
       "a standard wide-complex algorithm reaches for first. Amiodarone is at best unhelpful "
       "here and a class IA or IC agent makes the block worse.\n\n"
       "Give it as repeated boluses of 1 to 2 mEq/kg and reassess the QRS and the pressure "
       "after each one, rather than deciding in advance how many ampoules the patient will "
       "get. Follow it with an infusion once the complexes have narrowed, and watch the sodium, "
       "the potassium, the ionized calcium and the pH, because the complications of the "
       "treatment are hypernatremia, hypokalemia and alkalemia."),
     "author_rationale": "As above. A delayed consequence of the resident's own action."},
    {"when": "flag bicarb_given set AND flag bicarb_after_relapse set AND " + SEIZURE_STOPPED,
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": "The complexes have narrowed and the rate's come down. That's the fresh bicarb.",
     "debrief_note": (
       "Sodium bicarbonate terminated the wide-complex rhythm. This is the treatment for a "
       "wide-complex tachycardia caused by sodium-channel blockade, and it is not the treatment "
       "a standard wide-complex algorithm reaches for first. Amiodarone is at best unhelpful "
       "here and a class IA or IC agent makes the block worse.\n\n"
       "Give it as repeated boluses of 1 to 2 mEq/kg and reassess the QRS and the pressure "
       "after each one, rather than deciding in advance how many ampoules the patient will "
       "get. Follow it with an infusion once the complexes have narrowed, and watch the sodium, "
       "the potassium, the ionized calcium and the pH, because the complications of the "
       "treatment are hypernatremia, hypokalemia and alkalemia."),
     "author_rationale": "The relapse twin of the rule above (DIPH-09). A fresh dose after the relapse."},
    # Reached from arrival through phenytoin (DIPH-23), she has not yet had the scheduled
    # seizure. Bicarbonate alone narrows the rhythm and the seizure comes now.
    {"when": "flag bicarb_given set AND NOT flag seized set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "seizing",
     "flags_set": ["seized"],
     "narration": ("The complexes have narrowed since the bicarb. Now she's stiffened up and "
                   "she's seizing."),
     "debrief_note": (
       "Sodium bicarbonate narrowed the complexes and ended the wide-complex rhythm. She then "
       "had the seizure this case schedules for every patient. Bicarbonate is not an "
       "anticonvulsant: a benzodiazepine ends it."),
     "author_rationale": (
       "Only reachable after phenytoin on arrival (DIPH-23), the one route into the "
       "wide-complex phase that has not been through the seizure. Returning her to the "
       "seizing phase keeps the author's scheduled seizure in every run, which DIPH-01 asks "
       "for. Model judgment, needs a signature.")},
    {"when": "flag bicarb_given set AND NOT flag seizure_relapsed set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "seizing",
     "narration": ("The complexes have narrowed and the rate's come down since the bicarb. "
                   "She's still seizing, though."),
     "debrief_note": (
       "Sodium bicarbonate narrowed the complexes and ended the wide-complex rhythm, but it is "
       "not an anticonvulsant and she kept seizing. The convulsion goes on producing heat and "
       "acid, and both will widen the QRS again. A benzodiazepine is what ends it, with "
       "propofol as the next step if it does not."),
     "author_rationale": (
       "Added in the v0.18a review. Without it a resident who gave bicarbonate but no "
       "anticonvulsant stayed in the wide-complex phase with no exit except the handoff, "
       "showing a rate of 180 after the drug that treats it. Returning to the seizing phase "
       "keeps the rhythm and the seizure consistent with what was given. Ten seconds matches "
       "the other bicarbonate transitions. A resident who gives the anticonvulsant a few "
       "seconds after the bicarbonate passes through the seizing phase on the way and still "
       "reaches stabilizing, ten seconds later. Needs the author's signature.")},
    # bicarb_given is implied, and written out so the validator can see the loop through the
    # untreated-seizure rule cannot repeat.
    {"when": "flag bicarb_given set AND flag bicarb_after_relapse set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "seizing",
     "narration": ("The complexes have narrowed again since the bicarb. She's still seizing, "
                   "though."),
     "debrief_note": (
       "Sodium bicarbonate narrowed the complexes and ended the wide-complex rhythm, but it is "
       "not an anticonvulsant and she kept seizing. The convulsion goes on producing heat and "
       "acid, and both will widen the QRS again. A benzodiazepine is what ends it, with "
       "propofol as the next step if it does not."),
     "author_rationale": "The relapse twin of the rule above (DIPH-09). She does not relapse a second time."},
    {"when": "NOT flag bicarb_given set",
     "after_seconds": 120,
     "measured_from": "phase_entry",
     "to": "pulseless_vt",
     "narration": "I've lost the pulse. Same rhythm on the monitor and there's no output. I'm starting compressions.",
     "debrief_note": (
       "She arrested in pulseless ventricular tachycardia. This is where an untreated sodium-channel crisis leads: stable VT first, then pulseless VT. Sodium bicarbonate was never "
       "given, and it was indicated from the moment the first ECG resulted with a QRS of 132 "
       "milliseconds and a terminal R wave in aVR.\n\n"
       "The single most useful thing to carry out of this run: in a poisoning with a wide QRS, "
       "the ECG is the indication to treat and the ingestion history is not. You do not need "
       "to know what she took to give bicarbonate for a wide complex, and waiting to find out "
       "is what the two minutes in this phase were spent on."),
     "author_rationale": (
       "Two minutes of untreated stable ventricular tachycardia at 180 with a systolic pressure "
       "of 95 in a hyperthermic acidemic patient. The progression from stable to pulseless VT "
       "is the author's, stated in her narrative. The two minutes is a drafting judgment and "
       "is the single most consequential unsigned number in this pack, because it is the one "
       "that decides whether the case can kill the patient. Needs the author's signature."),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Death by clock is forbidden by the validator unless a case opts in explicitly. It is "
       "authored here because the author states the progression to pulseless VT in her own "
       "narrative description of the case, because untreated sodium-channel-blocker "
       "cardiotoxicity genuinely does this, and because the nurse has said the complexes look "
       "broad and asked what the resident wants to give for them, at 25 seconds in this phase "
       "and at 25 seconds in the phase before it (authored times, multiplied by the difficulty "
       "setting). The escalation that named bicarbonate was removed on the owner's instruction "
       "of 27 October 2026, so the warning names the problem and not the drug.")}],
   ),

 phase("stabilizing",
   "QRS narrowing after bicarbonate",
   "narrowing",
   "The complexes are narrowing and the rate is falling. Still hot at 39.6 and still "
   "delirious or post-ictal. The ingestion may or may not have been established by this "
   "point; the conduction has been treated either way. Reachable from two places: the "
   "post-ictal phase and the wide-complex rhythm. Since physician review DIPH-01 there is no "
   "route from arrival.",
   115, 115, 70, 18, 96, 39.6, 1, 1,
   transitions=[HANDOFF_T,
    {"when": "flag cooling_started set AND flag tox_consulted set", "to": "stabilized",
     "author_note": (
       "The two things still outstanding once the conduction is treated: the temperature, which "
       "is the remaining threat to life and the driver of the rhabdomyolysis, and the "
       "toxicologist, who decides what happens over the next twelve hours. Both are needed. "
       "There is no timed exit from this phase, which is a claim that a patient whose QRS is "
       "narrowing does not deteriorate again within the runtime of the case.")}],
   ),

 phase("stabilized",
   "Cooled, conduction treated, ready for critical care",
   "stabilized",
   "Narrow complexes, a controlled rate, an improving temperature and a toxicology plan. Still "
   "drowsy and still mydriatic. This is the intended endpoint and it is not a well patient: she "
   "needs a monitored bed and serial tracings.",
   100, 118, 72, 16, 98, 38.0, 0, 1,
   transitions=[HANDOFF_T],
   ),

 # ------------------------------------------------------------------ terminals
 phase("pulseless_vt",
   "Cardiac arrest in pulseless ventricular tachycardia",
   "arrested",
   "Terminal phase entered by the clock, not by an action, after two minutes of stable "
   "wide-complex tachycardia with no sodium bicarbonate given.",
   190, 0, 0, 4, 52, 39.8, 0, 3, react="fixed", terminal=True,
   transitions=[],
   timeout_reason=(
     "She lost mechanical output in a wide-complex tachycardia. Conduction through a sodium "
     "channel that was already blocked failed completely, because two minutes passed with no "
     "sodium bicarbonate given."),
   entered_by="time",
   authoring_note=(
     "Reachable one way: on the clock after two minutes of untreated blockade. From 5 "
     "September to 27 October 2026 amiodarone given into the wide-complex rhythm also led here "
     "instantaneously. Physician review DIPH-12 (Aakash Setty, 27 October 2026) replaced that "
     "arrest with a fall in blood pressure, so the timeout_reason names the clock route only. "
     "The engine's byClock flag on the failed record, added for the amiodarone route, stays.\n\n"
     "A terminal phase of its own rather than the shared 'halted' phase, because 'halted' "
     "carries a harmful action's halt reason and nothing harmful was done here. Attributing an "
     "omission to a commission would tell the resident something false about their own run. "
     "Content keys are not authored for this phase: the case has ended and nothing is "
     "queryable from it.\n\n"
     "Resuscitation from this rhythm is not authorable. The phase is terminal and the engine "
     "ends the case five seconds after entering it, so defibrillation, compressions and the "
     "bicarbonate that would still be the right drug are all out of reach. That is an engine "
     "boundary rather than a clinical claim, and the debrief note on the transition says what "
     "should have happened instead."),
   ),

 phase("halted",
   "Case halted after a harmful action",
   "stopped",
   "Terminal phase entered directly when a harmful action is taken, carrying that action's "
   "halt reason. Not reached through transition rules.",
   36, 58, 32, 5, 74, 39.6, 0, 3, react="fixed", terminal=True,
   transitions=[],
   schema_gap_note=(
     "Generic peri-arrest numbers, as in the reference case. This case has five halting "
     "actions and they do not share a physiology: physostigmine while the QRS is wide produces cholinergic bradycardia, flumazenil produces refractory seizure, a further dose of "
     "diphenhydramine deepens the block, and procainamide and propranolol widen it into a pulseless rhythm. "
     "One block of numbers cannot be all five, and the bradycardia these carry fits the first "
     "and fits the others less well. The halt reason on each action carries the physiology; "
     "these numbers carry none of it. In practice the beat stops the moment the case ends, so "
     "few learners will read them."),
   ),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the resident confirms a handoff. The debrief is generated "
   "from here.",
   105, 116, 72, 16, 97, 38.2, 0, 1, terminal=True,
   transitions=[],
   schema_gap_note=(
     "Placeholder, as in every other pack. A completion phase should inherit the vitals of the "
     "phase the resident handed off from and the schema cannot express that. These numbers "
     "assume the intended path with bicarbonate given and cooling running. A resident who hands "
     "over from the post-ictal phase without treating the conduction sees numbers here that are "
     "better than the patient they handed over, which is the one place in this case where the "
     "interface flatters a run it should not."),
   ),
]
