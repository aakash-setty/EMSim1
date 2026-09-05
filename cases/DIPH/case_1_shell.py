"""DIPH part 1: identity, patient, phases.

Case author: Kelly Medwid, MD. See DIPH-SEED.md for what is hers and what is not.
"""

META = {
 "working_title": "Eighteen year old woman, confusion and fever, brought in by EMS",
 "chief_complaint_patient_voice": (
   "She does not give one. She is delirious and does not know where she is. Her mother, "
   "at the bedside: 'She wasn't making any sense and she didn't know who I was.'"),
 "final_diagnosis": (
   "Diphenhydramine overdose producing an anticholinergic toxidrome with hyperthermia and "
   "delirium, complicated by cardiac sodium-channel blockade with QRS prolongation and by a "
   "generalised seizure. The teaching claim of the case is that the second half of that "
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
   "Recognise the clinical features of diphenhydramine toxicity at the bedside: the delirium, the mydriasis, the dry hot skin, the absent bowel sounds, the retained urine and the temperature.",
   "Obtain an early twelve-lead ECG in any significant overdose, and identify the findings of cardiac sodium-channel blockade on it: a QRS above 100 milliseconds, a terminal R wave in lead aVR, and a rightward terminal axis.",
   "Separate uncomplicated anticholinergic delirium from life-threatening cardiotoxicity, and state what changes when the QRS is wide.",
   "Give sodium bicarbonate for QRS widening or ventricular dysrhythmia, and titrate repeat boluses to the QRS and the blood pressure rather than to a fixed number of ampoules.",
   "State why physostigmine is contraindicated in a patient with a wide QRS, and what the ECG has to show before it could be considered at all.",
   "Treat the agitation, the seizure and the hyperthermia with benzodiazepines, sedation and active cooling rather than with antipsychotics and antipyretics.",
 ],
 "teaching_frame": (
   "A resident who reaches the end of this case having recognised an anticholinergic toxidrome, "
   "and having done nothing about the QRS, has failed the case while feeling that they passed "
   "it. The toxidrome is easy and visible and is on the first page of every toxicology lecture. "
   "The conduction abnormality is on a tracing nobody has ordered yet, and it is what kills her. "
   "Everything in the case is arranged so that the satisfying answer arrives before the "
   "dangerous one."),
 "care_setting": {
   "label": "Urban academic emergency department",
   "detail": (
     "Adult and paediatric emergency department at a hospital with a medical toxicology service, "
     "a regional poison centre on the telephone, intensive care beds and inpatient psychiatry. "
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
}

PATIENT = {
 "age": 18,
 "sex": "female",
 "weight_kg": 60,
 "background": (
   "No past medical history and no past surgical history. On no regular medication. No known "
   "drug allergies. Family history of hypertension on her mother's side. She is in her final "
   "year at school and lives at home with her mother and a younger brother.\n\n"
   "Not known to the department and not known to the resident: for the past several months she "
   "has been increasingly low. She has been bullied on social media, she broke up with her "
   "boyfriend a few weeks ago, and she has stopped speaking to several friends since. About four "
   "hours before her mother came home from work she swallowed the contents of a bottle of "
   "diphenhydramine. The bottle is on the floor beside her bed and nobody has looked for it."),
 "presenting_vitals_source": (
   "Inherited from phase 'presentation'. The crew put no oxygen on her and got no line in on the "
   "way. The temperature is the one the department measured, not one the crew reported."),
 "presenting_appearance": (
   "A young woman lying on the trolley, awake, flushed and pouring off heat, plucking at the "
   "sheet and at the monitoring leads. She looks past you rather than at you and answers "
   "questions with words that do not go together. She pushes hands away when anyone reaches for "
   "her. Her skin is hot and completely dry."),
 "ems_handover_text": (
   "Eighteen year old female, mum came in from work about an hour ago and found her like this in "
   "her bedroom. Mum says she was completely normal this morning. She's been confused the whole "
   "way in, doesn't know where she is, kept trying to get off the trolley. She's very warm to "
   "touch and she's dry as a bone. Rate was 130 to 140 on our monitor, regular. We didn't get a "
   "line in, she wouldn't have it. No injuries we could find. Mum's just behind us."),
 "arrival_handover": (
   "Eighteen year old, her mom found her like this when she got in from work about an hour ago. "
   "She's been fighting us the whole way in and she's burning up."),
 "handover_authoring_note": (
   "Section 3.2. Two sentences, 32 words, no vital sign, no past history, no medication, no "
   "allergy, no pertinent negative and no word that names a diagnosis. It is deliberately worse "
   "than the ems_handover_text above it: the crew knows more than this, and a resident who wants "
   "it has to ask for it. 'Burning up' is a lay description of what anyone touching her would "
   "feel and is not a temperature."),
}

# ---------------------------------------------------------------- phases
#
# Six clinical phases and three terminals. Section 3.3 caps the clinical count at six and
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
# Oxygen saturation in every phase is the UNSUPPORTED baseline (section 6.1). A cannula, a
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
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d

HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list so that a handoff is never overtaken by a "
                            "clinical rule in the same step."}

# The author's own sentence, and the reason the first deterioration in this case is unguarded.
SEIZURE_RATIONALE = (
  "The author writes, of the seizure: 'A seizure will occur as part of the natural process, "
  "regardless of how well the examinee is doing.' That is a scheduled natural history in the "
  "sense of authoring section 5.1, and the rule carries no guard, exactly as she wrote it. "
  "The clinical claim behind it is hers: a patient four hours into a diphenhydramine "
  "ingestion large enough to widen the QRS is going to seize. The deadline is her own four "
  "minutes, carried at its authored value.\n\n"
  "**The rule is unguarded and it is no longer unavoidable, and the difference matters.** "
  "Since 5 September 2026 the rule above it moves a patient who has received sodium "
  "bicarbonate out of this phase after ten seconds, so a resident who treats the conduction "
  "before four minutes never reaches this rule at all. Nothing about this rule changed; it "
  "was given an escape. Whether that escape should exist is the open question in the "
  "rationale on the rule above, and it is the one place in this pack where the conversion "
  "departs from a sentence the case author wrote in her own words.")

SEIZURE_NARRATION = (
  "She's stiffened up and she's fitting. I'm putting her on her side and I've got the suction. "
  "Her sats are dropping.")

SEIZURE_NOTE = (
  "She seized. This was going to happen: it is written into the case as the natural history of "
  "the ingestion rather than as a consequence of anything done or not done, and it fires at four "
  "minutes whatever the resident has achieved by then. What the four minutes before it were for "
  "was the monitor, the line, the glucose and above all the ECG, because the seizure is far "
  "easier to manage in a patient whose conduction you already understand.\n\n"
  "The physiology worth carrying away: the seizure is not an isolated neurological event here. "
  "Convulsion produces lactate and carbon dioxide, and acidaemia increases the fraction of the "
  "drug that is un-ionised and available to block the cardiac sodium channel. A seizure in a "
  "sodium-channel-blocker overdose therefore makes the cardiotoxicity worse while it is "
  "happening, which is why it is terminated with a benzodiazepine at once and why ventilation "
  "matters as much as the anticonvulsant does.")

PHYSO_SEIZURE_NARRATION = (
  "Her heart rate's come right down and now she's fitting again. That went in about ten seconds "
  "ago.")

PHYSO_SEIZURE_NOTE = (
  "The seizure followed the physostigmine. Physostigmine is a carbamate acetylcholinesterase "
  "inhibitor, and the acetylcholine it leaves in the synapse is the reason it reverses "
  "anticholinergic delirium and also the reason it causes bradycardia and lowers the seizure "
  "threshold. In a patient whose sodium channels are already blocked, both of those land on a "
  "myocardium that has no reserve.\n\n"
  "The case does not halt here because the seizure is survivable and because what happens next "
  "is the lesson: the QRS is still wide, it is now wider, and the treatment is sodium "
  "bicarbonate. Terminate the seizure with a benzodiazepine, then treat the conduction. Do not "
  "give a second dose of physostigmine, and do not give atropine unless the bradycardia is "
  "haemodynamically significant.\n\n"
  "See the physostigmine action's own note for why it should not have been given at all.")

PHASES = [
 phase("presentation",
   "Anticholinergic toxidrome with unrecognised sodium-channel blockade",
   "on arrival",
   "Awake, delirious, agitated and hyperthermic, with dry hot skin, mydriasis, absent bowel "
   "sounds and a palpable bladder. The QRS is already 132 milliseconds and nobody has looked "
   "at it. She is perfusing and her saturation is normal.",
   135, 130, 75, 25, 98, 40.1, 3, 0,
   [HANDOFF_T,
    {"when": "flag physostigmine_given set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "seizing",
     "narration": PHYSO_SEIZURE_NARRATION,
     "debrief_note": PHYSO_SEIZURE_NOTE,
     "author_rationale": (
       "A delayed consequence of the resident's own action, in the sense of authoring section "
       "5.1, so the five-second floor applies rather than the thirty-second one. Ten seconds "
       "is a compression: physostigmine given as a slow push over one to two minutes produces "
       "its cholinergic effects during and shortly after the injection. Reaching this rule at "
       "all means the tag evaluated to discouraged rather than harmful, which means the ECG "
       "had already resulted. Given before the ECG the action halts the case and this rule is "
       "never reached, because a harmful action bypasses transitions entirely.")},
    {"when": "flag bicarb_given set AND flag benzo_given set",
     "after_seconds": 10,
     "measured_from": "guard_true",
     "to": "stabilizing",
     "narration": ("The complexes have narrowed and her rate's coming down. That's since "
                   "the bicarb went in."),
     "debrief_note": (
       "You found the conduction abnormality and treated it before anything else happened, "
       "and the case gives you the credit for that: the QRS narrows and she does not "
       "convulse.\n\n"
       "What earned it was the order of the first two minutes. The toxidrome is visible on "
       "examination and the sodium-channel blockade is only visible on a tracing, so a "
       "resident who reaches this phase has ordered an ECG early, read the QRS rather than "
       "the rate, and acted on it without waiting for a level, a screen or a history. "
       "Bicarbonate here is given for the tracing and not for the ingestion, which is the "
       "single most transferable thing in this case.\n\n"
       "She is not well. She is still 39.6 degrees, still delirious, still mydriatic and "
       "still absorbing drug from a gut her own antimuscarinic effect has slowed down. The "
       "QRS can widen again when the bicarbonate stops. Cool her, sedate her, keep her on "
       "the monitor, repeat the tracing, and call toxicology."),
     "author_rationale": (
       "A delayed consequence of the resident's own action, so the five-second floor "
       "applies rather than the thirty-second one, and ten seconds matches the two other "
       "bicarbonate transitions in this case rather than introducing a third number.\n\n"
       "AUTHOR NOTE. This arrow was added on Aakash Setty's instruction of 5 September 2026 "
       "and it is a departure from the case author's own sentence, quoted in the rule below: "
       "'A seizure will occur as part of the natural process, regardless of how well the "
       "examinee is doing.' With this rule in place that is no longer true. A resident who "
       "gets both drugs in before about 230 seconds leaves the arrival phase and never "
       "convulses, so the seizure has become preventable.\n\n"
       "The guard requires BOTH drugs, and that is what makes the claim defensible. An "
       "earlier draft required sodium bicarbonate alone, which was a weak claim dressed as a "
       "mechanism: bicarbonate is not an anticonvulsant. It treats the cardiac sodium-channel "
       "blockade and, by correcting the acidaemia, reduces the un-ionised fraction of drug "
       "available to that channel, which is an indirect argument at best, and the agent "
       "lowering her seizure threshold is still on board and still being absorbed from a gut "
       "its own antimuscarinic effect has slowed down. The drug that prevents a drug-induced "
       "seizure is a benzodiazepine, and the guard now says so.\n\n"
       "Requiring both also makes the rule say something this case wanted to teach anyway: "
       "the two things that matter in the first four minutes are sedating the agitation, "
       "which is generating the heat and the acid and is itself worsening the cardiotoxicity, "
       "and treating the conduction. Neither alone is enough, and the escape is now a reward "
       "for doing both rather than for reaching for one drug.\n\n"
       "What remains a teaching choice rather than a physiological certainty is that the "
       "combination PREVENTS the seizure rather than making it less likely. A patient who has "
       "swallowed a gram of diphenhydramine may seize through an adequate benzodiazepine "
       "dose. Deleting this rule restores the author's sentence exactly and nothing else in "
       "the pack depends on it.")},
    {"when": None,
     "after_seconds": 240,
     "measured_from": "phase_entry",
     "to": "seizing",
     "narration": SEIZURE_NARRATION,
     "debrief_note": SEIZURE_NOTE,
     "author_rationale": SEIZURE_RATIONALE,
     "unguarded_rationale": SEIZURE_RATIONALE}],
   ),

 phase("seizing",
   "Generalised tonic-clonic seizure",
   "seizing",
   "Generalised convulsion with no airway protection and falling saturation. Entered either on "
   "the clock at four minutes, which is the author's natural history, or ten seconds after "
   "physostigmine. The QRS is wider than it was.",
   150, 145, 90, 8, 84, 40.4, 3, 3, react="sluggish",
   transitions=[HANDOFF_T,
    {"when": "flag benzo_given set", "to": "post_ictal",
     "author_note": "Instantaneous. A benzodiazepine terminates most drug-induced seizures "
                    "within a minute or two and the case does not model the delay, because "
                    "nothing here turns on how long it takes."},
    {"when": "NOT flag benzo_given set",
     "after_seconds": 120,
     "measured_from": "phase_entry",
     "to": "wide_complex_tachycardia",
     "narration": "She's still fitting and the complexes on the monitor have gone broad and fast. I can't get a pressure on her.",
     "debrief_note": (
       "Two minutes of untreated convulsion took her into a wide-complex tachycardia. The chain "
       "is the one the seizure note describes: the convulsion produces a lactic and respiratory "
       "acidosis, the acidaemia increases the un-ionised fraction of the drug at the cardiac "
       "sodium channel, and conduction that was already slowed slows further until the "
       "ventricle takes over.\n\n"
       "The action that would have prevented this is a benzodiazepine, and the nurse asked for "
       "one twice. Once the wide-complex rhythm is established the treatment is sodium "
       "bicarbonate, and the benzodiazepine is still needed."),
     "author_rationale": (
       "Two minutes of continuous convulsion in a patient who is already acidaemic at pH 7.28 "
       "with a QRS of 132 milliseconds. The number is a drafting judgement and not the "
       "author's: she specifies that the seizure happens and that lorazepam and bicarbonate "
       "are given, and does not say how long an untreated seizure is tolerated. It is set at "
       "the shorter end of what is defensible because the case has already established the "
       "acidaemia. Needs the author's signature.")}],
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
       "gradient across a channel that is partially blocked, and the alkalinisation reduces "
       "the fraction of drug bound to it. That is why hyperventilation alone is not the same "
       "treatment and why hypertonic saline is the rescue when alkalaemia is already at its "
       "ceiling."),
     "author_rationale": (
       "A delayed consequence of the resident's own action, so the five-second floor applies. "
       "The size of the compression is a drafting judgement.")},
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
       "drafting judgement and needs the author's signature.")}],
   ),

 phase("wide_complex_tachycardia",
   "Haemodynamically stable wide-complex tachycardia",
   "wide-complex",
   "Monomorphic wide-complex tachycardia at 180 from untreated sodium-channel blockade. She "
   "still has a blood pressure and she still has a pulse. This is the author's stable VT and it "
   "is the last phase in which bicarbonate can still turn the case around.",
   180, 95, 60, 22, 90, 40.0, 3, 2, react="sluggish",
   transitions=[HANDOFF_T,
    {"when": "flag amiodarone_given set",
     "to": "pulseless_vt",
     "author_note": (
       "Instantaneous, and the only transition in this pack that reaches a terminal phase "
       "without a clock. Added on instruction, 5 September 2026.\n\n"
       "Why it is a transition rather than a harmful tag. A harmful tag halts the case into "
       "the shared halted phase, which carries generic bradycardic peri-arrest numbers, and "
       "those are wrong here: this patient does not slow down and stop, she degenerates into "
       "a faster and wider rhythm and loses output. Reaching the arrest phase puts her on the "
       "numbers and the tracing this case already authors for it.\n\n"
       "Two costs of that choice, both real. Amiodarone stays tagged discouraged rather than "
       "harmful, because a harmful tag would halt the case and this rule would never be "
       "reached, so it costs one point on its tab rather than zeroing it; the run is still "
       "recorded as failed, which is what the learner sees. And the arrest phase's "
       "timeout_reason now has to be true of two routes rather than one, so it is rewritten "
       "to name the outcome they share and both causes.\n\n"
       "It is placed first among the clinical rules so that a resident who writes bicarbonate "
       "and amiodarone in the same batch of orders gets the amiodarone consequence rather "
       "than the rescue. That is deliberate: the amiodarone is the more instructive event, "
       "and treating the mechanism does not undo an agent that adds to the block.")},
    {"when": "flag bicarb_given set",
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
       "the potassium, the ionised calcium and the pH, because the complications of the "
       "treatment are hypernatraemia, hypokalaemia and alkalaemia."),
     "author_rationale": "As above. A delayed consequence of the resident's own action."},
    {"when": "NOT flag bicarb_given set",
     "after_seconds": 120,
     "measured_from": "phase_entry",
     "to": "pulseless_vt",
     "narration": "I've lost the pulse. Same rhythm on the monitor and there's no output. I'm starting compressions.",
     "debrief_note": (
       "She arrested in pulseless ventricular tachycardia. This is the end of the path the "
       "author describes: stable VT first, then pulseless VT. Sodium bicarbonate was never "
       "given, and it was indicated from the moment the first ECG resulted with a QRS of 132 "
       "milliseconds and a terminal R wave in aVR.\n\n"
       "The single most useful thing to carry out of this run: in a poisoning with a wide QRS, "
       "the ECG is the indication to treat and the ingestion history is not. You do not need "
       "to know what she took to give bicarbonate for a wide complex, and waiting to find out "
       "is what the two minutes in this phase were spent on."),
     "author_rationale": (
       "Two minutes of untreated stable ventricular tachycardia at 180 with a systolic pressure "
       "of 95 in a hyperthermic acidaemic patient. The progression from stable to pulseless VT "
       "is the author's, stated in her narrative. The two minutes is a drafting judgement and "
       "is the single most consequential unsigned number in this pack, because it is the one "
       "that decides whether the case can kill the patient. Needs the author's signature."),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": (
       "Death by clock is forbidden by the validator unless a case opts in explicitly. It is "
       "authored here because the author states the progression to pulseless VT in her own "
       "narrative description of the case, because untreated sodium-channel-blocker "
       "cardiotoxicity genuinely does this, and because bicarbonate has been prompted for by "
       "the nurse in this phase at 20 seconds and again at 70, and in the phase before this "
       "one at 25 and at 90. A resident reaching this transition has been asked for "
       "bicarbonate four times.")}],
   ),

 phase("stabilizing",
   "QRS narrowing after bicarbonate",
   "narrowing",
   "The complexes are narrowing and the rate is falling. Still hot at 39.6 and still "
   "delirious or post-ictal. The ingestion may or may not have been established by this "
   "point; the conduction has been treated either way. Reachable from three places: "
   "directly from arrival if the bicarbonate went in before she seized, from the post-ictal "
   "phase, and from the wide-complex rhythm.",
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
   "stabilised",
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
   190, 44, 22, 4, 52, 39.8, 0, 3, react="fixed", terminal=True,
   transitions=[],
   timeout_reason=(
     "She lost mechanical output in a wide-complex tachycardia. Conduction through a sodium "
     "channel that was already blocked failed completely, either because two minutes passed "
     "with no sodium bicarbonate given, or because an antiarrhythmic that blocks the same "
     "channel was given into the rhythm."),
   entered_by="time, or an antiarrhythmic given into the wide-complex rhythm",
   authoring_note=(
     "Reachable two ways since 5 September 2026: on the clock after two minutes of untreated "
     "blockade, and instantaneously when amiodarone is given into the wide-complex rhythm. "
     "The timeout_reason above therefore names the outcome the two share and both causes, "
     "because the engine reads that one field whichever route was taken; the route-specific "
     "teaching is in the amiodarone action's own debrief note, which is always shown for an "
     "action the resident took. The engine gained a byClock flag on the failed record at the "
     "same time, because the debrief used to assert that any run ending in a terminal phase "
     "had been ended by the clock, which is now false for one of the two routes.\n\n"
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
     "Generic peri-arrest numbers, as in the reference case. This case has four halting "
     "actions and they do not share a physiology: physostigmine before the ECG produces "
     "cholinergic bradycardia, flumazenil produces refractory seizure, a further dose of "
     "diphenhydramine deepens the block, and procainamide widens it into a pulseless rhythm. "
     "One block of numbers cannot be all four, and the bradycardia these carry fits the first "
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
