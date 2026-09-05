"""DIPH part 2: the action spine, tags, flags, prompts and vital effects.

Tag rule lists are ordered and first match wins. Every list ends unconditionally.
The fallthrough in every phase is the thing to read: authoring 7.3 says so and it is
the commonest defect in a case that otherwise validates.
"""

ACTIONS = []

def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a

ALWAYS = lambda v: [{"when": None, "value": v}]

# Phases in which the sodium-channel blockade is established and visible, used by
# several tag lists and by the rescue-therapy guards.
WIDE = "phase is wide_complex_tachycardia"
POST = "phase is post_ictal"
SEIZ = "phase is seizing"
PRES = "phase is presentation"
RESOLVING = "phase is stabilizing OR phase is stabilized"

# Oxygen delivery shares one vital-effect key across the cannula, the mask and the tube,
# so escalating replaces the previous device rather than adding to it. Effects sharing a
# key do not stack; three separate keys would let a resident stack a cannula, a mask and a
# tube for fifteen points of saturation, which is not a thing that happens to a patient.
O2_KEY = "oxygen_support"
# Oxygen delivery is guarded to the phases where she is hypoxaemic. She arrives at 98 percent
# on room air, so there is nothing for a mask to add there, and an unguarded effect would be
# clamped by the engine's physiological bounds rather than being right: validator rule V says
# so, and what it is really saying is that a phase baseline plus a delta that leaves the range
# is a phase baseline that already includes the gain. The airway is the second guard, because
# a mask on an intubated patient is not what is oxygenating her.
HYPOXIC = "phase is seizing OR phase is post_ictal OR phase is wide_complex_tachycardia"
# Parenthesised, and it has to be. AND binds tighter than OR in the section 4 grammar, so
# HYPOXIC + " AND NOT flag airway_protected set" parses as
#   seizing OR post_ictal OR (wide_complex AND NOT airway_protected)
# which is true in the post-ictal phase whatever the airway is doing. The effect of that was
# a non-rebreather still adding five points to an intubated patient, and it was silent: the
# case validated, the scenarios passed, and only a case assertion comparing the two runs
# found it. Anywhere a multi-term OR is ANDed with something, group it.
HYPOXIC_G = "(" + HYPOXIC + ")"

# =====================================================================  STABILISATION

act("attach_monitor",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["monitor_on"],
    prompt={"deadline_seconds": 20,
            "text": "She's on the trolley and she's got nothing on her. Do you want her on the monitor?"},
    nurse_alert="Monitor's on her. Would you like anything else?",
    debrief_note=(
      "Nothing is visible until this is done: the interface shows dashes for every vital and plays "
      "no heartbeat until an action carrying the catalog's reveals_vitals capability has been "
      "taken, and attaching a monitor is the only one. That is a property of the simulator and it "
      "is also true of the room. In this case it matters more than usual, because the temperature "
      "is one of the six numbers on the monitor and 40.1 degrees is half the diagnosis.\n\n"
      "The nurse's line after it is the author's own, from the Anticipated Management Mistakes "
      "list in the source case: the monitor is on, would you like anything else. It is there to "
      "open the door to the ECG, which is the thing this patient most needs and the thing "
      "residents most often leave until the workup comes back."))

act("insert_iv", ALWAYS("critical"),
    debrief_note=(
      "Two large-bore lines, per the author's Ideal Scenario Flow. Everything this patient needs "
      "is intravenous: the benzodiazepine, the bicarbonate, the fluid and the sedation for "
      "intubation. The simulator enforces this through the catalog prerequisite on every "
      "intravenous drug rather than through a prompt, so a resident who reaches for lorazepam "
      "without a line is told why it did not happen and is not penalised for the attempt."))

act("second_iv", ALWAYS("recommended"),
    debrief_note=(
      "The author asks for two lines. In practice the second one earns its place here when the "
      "bicarbonate is running as an infusion and something else has to go in beside it, and "
      "again if she needs induction drugs. Not case-determining."))

act("intraosseous_line",
    [{"when": SEIZ, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Reasonable in a convulsing patient in whom peripheral access has failed or was never "
      "obtained. It is not the first move in a patient who was agitated rather than "
      "unconscious, but a seizing patient with no line and a treatable cause is exactly the "
      "situation intraosseous access exists for."))

act("nasal_cannula_oxygen",
    [{"when": HYPOXIC, "value": "recommended"}, {"when": None, "value": "neutral"}],
    flags_set=["oxygen_applied"],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 2, "key": O2_KEY,
                    "onset_seconds": 0,
                    "while": HYPOXIC_G + " AND NOT flag airway_protected set"}],
    debrief_note=(
      "Two points of saturation in the phases where she is hypoxaemic, and nothing in the "
      "phases where she is not, because her saturation on arrival is 98 percent on room air. "
      "Oxygen is not the treatment for anything in this case. It is worth having on during the "
      "seizure and worth escalating from."))

act("non_rebreather_mask",
    [{"when": SEIZ, "value": "recommended"}, {"when": HYPOXIC, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    flags_set=["oxygen_applied"],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 5, "key": O2_KEY,
                    "onset_seconds": 0,
                    "while": HYPOXIC_G + " AND NOT flag airway_protected set"}],
    debrief_note=(
      "Five points, sharing the same effect key as the cannula and the tube, so it replaces "
      "whichever was on rather than adding to it. During the convulsion this is the right "
      "device and the useful one, because the saturation of 84 in that phase is the product of "
      "a patient who is not ventilating rather than of a lung problem."))

act("bag_valve_mask",
    [{"when": SEIZ, "value": "recommended"}, {"when": None, "value": "neutral"}],
    flags_set=["oxygen_applied"],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 6, "key": O2_KEY,
                    "onset_seconds": 0,
                    "while": SEIZ + " AND NOT flag airway_protected set"}],
    debrief_note=(
      "Assisted ventilation during the convulsion, and it is worth more here than the number "
      "suggests. Ventilation is not only about the saturation in a sodium-channel-blocker "
      "poisoning: carbon dioxide retention during a seizure produces a respiratory acidosis, "
      "and acidaemia increases the un-ionised fraction of the drug available to block the "
      "cardiac sodium channel. Bagging her is treating the heart as well as the lungs."))

act("suction",
    [{"when": SEIZ, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note="Airway housekeeping during and after the convulsion. Not scored beyond the point.")

act("intubate_rapid_sequence",
    [{"when": PRES, "value": "neutral"},
     {"when": SEIZ, "value": "recommended"},
     {"when": None, "value": "recommended"}],
    flags_set=["airway_protected"],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 8, "key": O2_KEY,
                    "onset_seconds": 0, "while": HYPOXIC}],
    follow_ups_triggered=["post_intubation_sedation"],
    prompt={"deadline_seconds": 70, "guard": SEIZ + " AND NOT flag airway_protected set",
            "text": "She's still not protecting anything and I'm bagging her between the jerks. Do you want to tube her?"},
    debrief_note=(
      "Defensible at almost any point in this case and required in several of them. The author "
      "writes that the patient may be intubated for airway protection during the seizure and "
      "that she is intubated before going to the unit.\n\n"
      "Three separate indications converge here and they are worth separating. Airway protection "
      "in a patient who is convulsing or post-ictal. Ventilation, because keeping the carbon "
      "dioxide down keeps the pH up and the pH is part of the cardiac toxicity. And control of "
      "the hyperthermia: sedation and paralysis stop the muscle activity that is generating the "
      "heat, which is why the temperature guidance in this poisoning reads intubate, sedate and "
      "paralyse rather than give an antipyretic.\n\n"
      "It is tagged neutral rather than recommended in the arrival phase only because a "
      "delirious patient who is maintaining her own airway and saturating at 98 percent has "
      "other things needed first, and none of them is the tube. It is never wrong here, and a "
      "resident who intubated early to control the agitation and the temperature has an "
      "argument."))

# The catalog's intubation prerequisite is `flag sedation_given set AND flag paralytic_given
# set`, and the catalog sets neither flag itself, so every case has to author them on its own
# induction agents or intubation is unreachable. AFRVR does the same. Missing them here made
# intubation permanently blocked, which the case-agnostic engine suite caught and the
# scenario runner did not, because the scenario that should have caught it asserted a phase
# that does not change on intubation either way.
INDUCTION_FLAGS = {"etomidate_bolus": ["sedation_given"], "propofol_bolus": ["sedation_given"],
                   "ketamine_bolus": ["sedation_given"], "rocuronium_bolus": ["paralytic_given"]}

for drug, tag_v, note in [
  ("etomidate_bolus", "recommended",
   "Reasonable induction agent here. Haemodynamically neutral in a patient whose pressure is "
   "adequate but whose myocardium is poisoned."),
  ("propofol_bolus", "recommended",
   "Reasonable, and it has a second job: propofol is an anticonvulsant, which matters in a "
   "patient whose seizure may recur. The cost is vasodilatation and negative inotropy in a "
   "myocardium with sodium channels already blocked, so watch the pressure after it."),
  ("ketamine_bolus", "neutral",
   "Usable and not the obvious choice. Ketamine is sympathomimetic and this patient is already "
   "tachycardic at 150 with a temperature of 40.4 and a drug on board that blocks cardiac "
   "sodium channels. Nothing here says it is dangerous, and the case does not penalise it; "
   "etomidate or propofol asks less of the same heart."),
  ("rocuronium_bolus", "recommended",
   "The paralytic to prefer in this patient. See the note on succinylcholine."),
]:
    act(drug, ALWAYS(tag_v), debrief_note=note,
        flags_set=INDUCTION_FLAGS[drug])

act("succinylcholine_bolus",
    ALWAYS("discouraged"),
    flags_set=["paralytic_given"],
    debrief_note=(
      "Discouraged rather than forbidden, and the reasoning is worth having rather than the "
      "rule. She has been agitated and hyperthermic for hours and has now convulsed, her "
      "creatine kinase is already 540, and rhabdomyolysis is under way. Succinylcholine causes "
      "a transient rise in serum potassium, which is small in a normal patient and is not "
      "reliably small in one with muscle injury. Her potassium was 3.8 when it was drawn, which "
      "is the last thing anybody knows about it.\n\n"
      "The honest strength of this claim: the dangerous hyperkalaemic response to "
      "succinylcholine is well described in established rhabdomyolysis, denervation and burns, "
      "and is not well quantified in the first hours of exertional or drug-induced muscle "
      "injury. Rocuronium is available, works, and asks none of these questions, which is why "
      "this is discouraged rather than neutral. A resident who used succinylcholine and can "
      "say why they were comfortable has not made an error of knowledge."))

act("cooling_measures",
    [{"when": RESOLVING, "value": "recommended"}, {"when": None, "value": "critical"}],
    flags_set=["cooling_started"],
    vital_effects=[{"vital": "temperature_c", "delta": -0.9, "key": "active_cooling",
                    "onset_seconds": 30}],
    prompt={"deadline_seconds": 140,
            "guard": PRES + " OR " + POST + " OR " + RESOLVING,
            "text": "Her temperature's 40.1 and she's dry as a bone. Do you want anything done about it?",
            "escalation": {"deadline_seconds": 170,
                           "text": "She's still over 40. I've got ice packs and a cooling blanket if you want them."}},
    debrief_note=(
      "A critical action, and the one most often left until the end. The temperature here is not "
      "a fever and it will not respond to the treatment for a fever. Anticholinergic "
      "hyperthermia has two mechanisms and neither of them is a raised hypothalamic set point: "
      "the muscle activity of agitation and convulsion generates heat, and the blockade of "
      "muscarinic receptors on the sweat glands stops her losing it. That is why the skin is hot "
      "and dry rather than hot and wet, and it is why the treatment is sedation and physical "
      "cooling.\n\n"
      "Practically: benzodiazepines to stop the muscle activity, remove the clothing, active "
      "external cooling, cooled fluids, and intubation with sedation and paralysis if the "
      "temperature will not come down. The author asks for cooling blankets in the six to ten "
      "minute block of her scenario.\n\n"
      "Why it is worth the urgency: sustained core temperatures above 40 degrees cause "
      "neurological injury and drive the rhabdomyolysis that her creatine kinase of 540 is the "
      "start of. It is also one of the two things this case will not let her leave the "
      "department without."))

act("warming_measures", ALWAYS("discouraged"),
    debrief_note=(
      "She is at 40.1 degrees. This is almost certainly a misclick, and it is tagged discouraged "
      "rather than harmful because the case has no basis for claiming that a warming blanket "
      "applied and presumably removed kills this patient. It is here so that the action is "
      "scored rather than silent."))

act("place_pads_for_monitoring",
    [{"when": WIDE, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Sensible in a patient in a wide-complex tachycardia, and it costs nothing to have them on "
      "before you need them. It is not the treatment: see the note on defibrillation."))

act("defibrillate",
    [{"when": WIDE, "value": "discouraged"}, {"when": None, "value": "discouraged"}],
    debrief_note=(
      "She has a pulse and a blood pressure of 95 over 60. An unsynchronised shock delivered to "
      "a perfusing rhythm can produce ventricular fibrillation, and that is the immediate "
      "objection.\n\n"
      "The deeper one is that electricity does not treat this. The wide complex is a poisoned "
      "sodium channel, not a re-entrant circuit, and a rhythm converted by a shock while the "
      "drug is still bound to the channel comes straight back. Sodium bicarbonate is what "
      "changes the substrate. Cardioversion and defibrillation have a place in this poisoning "
      "and it is in the patient who is unstable or pulseless, alongside bicarbonate rather than "
      "instead of it.\n\n"
      "Tagged discouraged rather than harmful because the shock is survivable and because "
      "halting the case here would teach that electricity is forbidden in poisoning, which is "
      "not true."))

act("synchronized_cardioversion",
    [{"when": WIDE, "value": "discouraged"}, {"when": None, "value": "discouraged"}],
    debrief_note=(
      "The synchronised version of the same reasoning, and a smaller error. This patient is "
      "perfusing, so there is time for the drug that treats the mechanism. If she loses her "
      "pressure, cardioversion becomes appropriate and sodium bicarbonate is still indicated "
      "alongside it. She is also awake enough to need sedation first, which the catalog "
      "prerequisite enforces."))

act("start_chest_compressions", ALWAYS("neutral"),
    debrief_note="Not indicated while she has a pulse. Scored as neutral rather than wrong.")

act("place_patient_on_isolation_precautions",
    [{"when": PRES, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "The author's own suggestion: a team thinking about meningitis in a febrile confused "
      "eighteen year old may reasonably isolate her while they find out. Recommended on arrival "
      "for exactly that reason and neutral afterwards, once the toxidrome has declared itself. "
      "It costs nothing and it is the right instinct at the moment it is taken."))

act("insert_foley_catheter", ALWAYS("recommended"),
    flags_set=["bladder_drained"],
    debrief_note=(
      "She has a palpable bladder, which is the anticholinergic urinary retention and is one of "
      "the findings that makes the toxidrome. Two reasons to drain it: it is uncomfortable and "
      "it contributes to the agitation, and it gives you urine output, which is what you will be "
      "following as the rhabdomyolysis declares itself. Send the sample: myoglobinuria produces "
      "a urinalysis positive for blood with no red cells on microscopy."))

# =====================================================================  MEDICATIONS

act("lorazepam_bolus",
    [{"when": SEIZ, "value": "critical"},
     {"when": PRES, "value": "critical"},
     {"when": None, "value": "recommended"}],
    flags_set=["benzo_given", "sedation_given"],
    display_name="Lorazepam (or midazolam)",
    prompt={"deadline_seconds": 15, "guard": SEIZ,
            "text": "She's fitting. What do you want for it?",
            "escalation": {"deadline_seconds": 60,
                           "text": "She's still going. I've got lorazepam and midazolam drawn up. Which one?"}},
    debrief_note=(
      "First-line for all four of the things wrong with this patient that a drug can touch "
      "quickly: the agitation, the seizure, the sympathetic overactivity and, through the first "
      "of those, the hyperthermia. Titrate to effect and expect to need more than one dose.\n\n"
      "The reason it earns a critical tag on arrival as well as during the convulsion is that "
      "the agitation is not a behavioural problem here. It is generating the heat, it is "
      "generating the lactate, and both of those are making the cardiac toxicity worse. Sedating "
      "her is treating the heart.\n\n"
      "If seizures recur despite adequate benzodiazepine dosing, go to propofol or a "
      "barbiturate, secure the airway, and correct the hypoxia, the acidaemia and the "
      "temperature. Do not reach for phenytoin: see its own note.\n\n"
      "Coverage note: midazolam is in the catalog under the intubation drugs and is bound to "
      "this action, so a resident who uses midazolam as an induction agent will also set the "
      "benzodiazepine flag and terminate the seizure. That is clinically true and it is the "
      "reason the coverage is there, but it means the case cannot distinguish a deliberate "
      "anticonvulsant from an induction agent that happened to be one."))

act("na_bicarbonate_bolus",
    [{"when": WIDE, "value": "critical"},
     {"when": POST, "value": "critical"},
     {"when": SEIZ, "value": "critical"},
     {"when": PRES + " AND study ecg_12_lead resulted", "value": "critical"},
     {"when": PRES, "value": "recommended"},
     {"when": None, "value": "recommended"}],
    flags_set=["bicarb_given"],
    flags_set_repeat=[{"flag": "bicarb_titrated", "after_administrations": 2,
                       "counter": "bicarbonate_doses"}],
    follow_ups_triggered=["bicarbonate_reassessment", "repeat_ecg_after_bicarbonate"],
    nurse_alert="It can take a minute or two before you see the complexes change.",
    prompt={"deadline_seconds": 25,
            "guard": SEIZ + " OR " + POST + " OR " + WIDE,
            "text": "Her complexes look broad to me. Is there anything you want to give for that?",
            "escalation": {"deadline_seconds": 90,
                           "text": "The QRS on the monitor is still wide. Do you want bicarb?"}},
    debrief_note=(
      "The treatment this case exists for. Sodium bicarbonate is first-line for QRS widening, "
      "ventricular dysrhythmia and hypotension caused by sodium-channel blockade, whatever the "
      "agent, and it is given for the ECG rather than for the ingestion history.\n\n"
      "How it works, both halves: the sodium load raises the transmembrane sodium gradient "
      "across channels that are partially blocked, and the alkalinisation reduces the fraction "
      "of drug bound to the channel. Hyperventilation alone gives you the second and not the "
      "first, which is why it is not an equivalent treatment.\n\n"
      "How to give it: 1 to 2 mEq/kg as an intravenous bolus, repeated, with the QRS and the "
      "blood pressure reassessed after each dose, and an infusion considered once the complexes "
      "have narrowed. The endpoint is not a number of ampoules. It is a narrowing QRS, the "
      "resolution of ventricular ectopy and a better pressure, with a serum pH commonly taken "
      "toward about 7.50 to 7.55 and not beyond.\n\n"
      "What to watch while you do it: sodium, potassium, ionised calcium, pH and volume. "
      "Hypernatraemia, hypokalaemia, metabolic alkalosis, a fall in ionised calcium and fluid "
      "overload are all complications of the treatment rather than of the poisoning.\n\n"
      "The gap this case is built to expose is giving one dose and moving on. One amp is a "
      "gesture. The nurse asks about a second, and the case counts them."),
    references=["Part 2 of the author's document, sections 4 and 5. [UNVERIFIED, confirm before release]"])

act("na_bicarbonate_infusion",
    [{"when": WIDE, "value": "recommended"},
     {"when": RESOLVING, "value": "recommended"},
     {"when": None, "value": "recommended"}],
    flags_set=["bicarb_given", "bicarb_infusion_running"],
    debrief_note=(
      "The right second step and the wrong first one. An infusion maintains the alkalinisation "
      "and the sodium load after the boluses have narrowed the complex, and it is what stops the "
      "QRS drifting back out over the following hours as the drug redistributes. Started instead "
      "of a bolus in a patient in a wide-complex tachycardia it is too slow for the problem in "
      "front of you.\n\n"
      "It satisfies the same flag as the bolus, so a resident who reaches for the drip alone is "
      "not treated by this case as having failed to give bicarbonate. That is a deliberate "
      "choice and it is arguable: the alternative would have been to make the drip an unscored "
      "route around the critical action, which is worse."))

act("stop_na_bicarbonate", ALWAYS("discouraged"),
    debrief_note=(
      "Stopping the infusion inside the department, in a patient whose QRS was wide an hour ago, "
      "gives back the alkalinisation and the sodium load while the drug is still on board and "
      "still redistributing. If it was stopped because of a rising pH or a falling potassium, "
      "that is a reason to check a gas and replace the potassium rather than to stop.\n\n"
      "Authored because the catalog makes every infusion stoppable and an unscored stop is an "
      "unscored way to undo the treatment."))

act("physostigmine",
    [{"when": "NOT study ecg_12_lead resulted", "value": "harmful"},
     {"when": None, "value": "discouraged"}],
    flags_set=["physostigmine_given"],
    halt_reason=(
      "You gave physostigmine to a patient whose ECG you had not seen. Her QRS was already 132 "
      "milliseconds with a terminal R wave in aVR, which is cardiac sodium-channel blockade. The "
      "acetylcholine you left in the synapse produced profound bradycardia in a myocardium that "
      "had no conduction reserve, she convulsed, and she arrested."),
    debrief_note=(
      "Physostigmine is a carbamate that reversibly inhibits acetylcholinesterase, raising "
      "acetylcholine at central and peripheral muscarinic and nicotinic receptors. It genuinely "
      "reverses anticholinergic delirium, and that is what makes it tempting in a patient who "
      "looks exactly like this one.\n\n"
      "Why it is wrong here. It is contraindicated where there is QRS widening, sodium-channel "
      "blockade, ventricular dysrhythmia, significant conduction abnormality, seizure, or a "
      "suspected tricyclic co-ingestion. This patient has five of the six. The harms are "
      "bradycardia, asystole and seizure, and every one of them lands on a heart that is already "
      "conducting badly. Anticholinergic delirium plus a wide QRS is a bicarbonate case, not a "
      "physostigmine case.\n\n"
      "Why the ECG is the gate rather than the history. The standard teaching, including in the "
      "author's own source, is to look at the ECG for signs of sodium-channel blockade before "
      "considering physostigmine at all: an R wave over 3 millimetres in aVR, and a widened "
      "QRS. Her urine screen is also positive for tricyclics, which is a false positive from the "
      "diphenhydramine and is not something you can know at the time. Given blind, you are "
      "giving it to a patient who may have taken a tricyclic.\n\n"
      "What this case does with it. Given before the ECG has resulted it halts the case, because "
      "at that point the drug is being given without the one piece of information that decides "
      "whether it is safe. Given after the ECG has resulted, with a QRS of 132 milliseconds on "
      "the screen, it does not halt the case: it produces a seizure ten seconds later and leaves "
      "you with a patient who still needs sodium bicarbonate and now needs an anticonvulsant "
      "too. Both routes are the same lesson and the second one is the more instructive, because "
      "you have to treat what you caused.\n\n"
      "If you do ever give it, in a patient with a genuinely normal QRS and isolated "
      "anticholinergic delirium: 0.5 to 2 milligrams intravenously over one to two minutes, with "
      "atropine at the bedside.\n\n"
      "AUTHOR NOTE. The source document disagrees with itself here. The narrative case "
      "description says the use of physostigmine is warranted once diphenhydramine is "
      "established and the poison centre has been consulted; the debriefing guide says it is not "
      "appropriate when the QRS is wide. This pack follows the debriefing guide, on the case "
      "author's instruction of 5 September 2026. See DIPH-SEED.md section 9.1. [UNVERIFIED, "
      "confirm before release]"))

act("atropine_bolus",
    [{"when": "flag physostigmine_given set", "value": "recommended"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Recommended only after physostigmine has been given, which is the one circumstance in "
      "this case that produces a bradycardia worth treating. Standard teaching is to have "
      "atropine drawn up at the bedside before physostigmine goes in, for exactly this.\n\n"
      "Neutral otherwise. This patient is tachycardic at 135 and atropine is an antimuscarinic, "
      "which is the class of drug she has overdosed on."))

act("flumazenil", ALWAYS("harmful"),
    halt_reason=(
      "You gave flumazenil to a patient with an undifferentiated overdose who was already "
      "primed to seize. She had a prolonged seizure that would not respond to a benzodiazepine, "
      "because you had just blocked the receptor it works at, and she arrested with a QRS that "
      "had never been treated."),
    debrief_note=(
      "Flumazenil reverses benzodiazepine sedation and is a reasonable thought in an obtunded "
      "patient of unknown cause. It is dangerous in an undifferentiated overdose for two "
      "reasons, and this patient has both. It lowers the seizure threshold in patients who have "
      "co-ingested a proconvulsant, and diphenhydramine at this dose is one. And it removes the "
      "one drug class that treats her seizure, her agitation and her hyperthermia, at the moment "
      "she most needs it.\n\n"
      "The general rule worth carrying: flumazenil belongs to iatrogenic, single-agent, "
      "benzodiazepine-naive sedation. It does not belong in a deliberate overdose of unknown "
      "content."))

act("diphenhydramine", ALWAYS("harmful"),
    halt_reason=(
      "You gave diphenhydramine to a patient who had overdosed on diphenhydramine. Her QRS "
      "widened further, she lost her pressure, and she arrested."),
    debrief_note=(
      "This is here because the catalog offers diphenhydramine under Meds - Allergy and a "
      "resident treating a presumed allergic reaction, a dystonic reaction or an itch can reach "
      "it in two clicks. The flushing and the agitation can be read as anaphylaxis by someone "
      "who has not yet examined the pupils, the skin or the bowel sounds.\n\n"
      "The teaching point is not that anyone would do this deliberately. It is that the "
      "diagnosis has to be made before the treatment is chosen, and that in a poisoning the "
      "differential includes the drug you are about to give."))

act("fos_phenytoin", ALWAYS("discouraged"),
    debrief_note=(
      "The author's instruction is that this should be avoided, and her reason is the right one: "
      "phenytoin acts on the same cardiac sodium channels the diphenhydramine is already "
      "blocking. Giving a sodium-channel blocker to a patient poisoned by one is at best "
      "unhelpful and is plausibly harmful in a patient whose QRS is already 132 milliseconds.\n\n"
      "It is tagged discouraged rather than harmful, and the author should decide whether that "
      "is right. The reason for the softer tag: the evidence that phenytoin worsens outcomes in "
      "sodium-channel-blocker poisoning is extrapolated from tricyclic antidepressant work and "
      "from animal data rather than established in humans, and authoring 7.3 says that halting a "
      "case is the strongest claim this system can make and should be reserved for genuine "
      "lethality. The author wrote 'avoided', not 'kills'.\n\n"
      "What to use instead if the seizure recurs after adequate benzodiazepine dosing: "
      "levetiracetam, propofol or a barbiturate, alongside airway control and correction of the "
      "acidaemia, the hypoxia and the temperature. And remember that in this poisoning a "
      "recurrent seizure is also a reason to look at the QRS again."))

act("levetiracetam_bolus",
    [{"when": "flag benzo_given set", "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "A reasonable second-line anticonvulsant after adequate benzodiazepine dosing, and the "
      "sensible alternative to phenytoin here because it does not act at the cardiac sodium "
      "channel. Neutral before any benzodiazepine has been given, because a benzodiazepine is "
      "the first-line drug for a toxic seizure and going past it is the error."))

act("propofol_infusion",
    [{"when": "flag airway_protected set", "value": "recommended"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Sedation for an intubated patient, and it does three jobs at once here: it keeps her "
      "asleep, it is an anticonvulsant in a patient whose seizure may recur, and it stops the "
      "muscle activity that is generating the heat. Watch the pressure."))

for d, note in [
  ("ketamine_infusion", "Alternative post-intubation sedation. Sympathomimetic, which asks more of a tachycardic hyperthermic patient than propofol does."),
  ("fentanyl_bolus", "Analgesia and sedation adjunct after intubation. Unremarkable here."),
  ("morphine_bolus", "Nothing in this case hurts. Not wrong, not useful."),
]:
    act(d, ALWAYS("neutral"), debrief_note=note)

for d, label in [("haloperidol", "Haloperidol"), ("olanzapine", "Olanzapine"),
                 ("ziprasidone", "Ziprasidone")]:
    act(d, ALWAYS("discouraged"),
        debrief_note=(
          label + " for the agitation is the reflex this case wants to interrupt. Three "
          "objections, and they compound.\n\n"
          "It is the wrong drug for this agitation. The agitation is anticholinergic delirium "
          "and the first-line treatment is a benzodiazepine, titrated to effect.\n\n"
          "It adds to the poisoning. The antipsychotics have antimuscarinic activity of their "
          "own, so the drug is being added to the class that caused the problem.\n\n"
          "It prolongs the QT in a patient whose QTc is already 495 milliseconds and who has a "
          "drug on board that blocks potassium channels as well as sodium ones. QRS widening and "
          "QT prolongation are different electrophysiological problems, they coexist here, and "
          "this treats neither while worsening one.\n\n"
          "Fourth, and least often thought about: antipsychotics impair thermoregulation, in a "
          "patient at 40.1 degrees who cannot sweat."))

act("acetaminophen", ALWAYS("discouraged"),
    debrief_note=(
      "An antipyretic for a temperature of 40.1 degrees. It will not work, and the reason it "
      "will not work is the point. Antipyretics act by lowering a raised hypothalamic set point. "
      "This temperature is not a raised set point: it is heat generated by muscle activity in a "
      "patient whose sweat glands are blocked. The set point is normal and the thermostat is not "
      "the problem.\n\n"
      "Treat it with sedation, removal of clothing, active external cooling, and paralysis if "
      "that is not enough. There is also a smaller, separate reason to leave it alone: she has "
      "taken an unknown quantity of an over-the-counter preparation, combination sleep aids "
      "contain acetaminophen, and adding more before her level is back is untidy. Her "
      "acetaminophen level in this case is zero, which you do not know when you reach for it."))

act("ibuprofen", ALWAYS("discouraged"),
    debrief_note=(
      "The same reasoning as acetaminophen, with the addition that she is hypovolaemic, "
      "hyperthermic and developing rhabdomyolysis, which is the wrong combination for a "
      "non-steroidal."))

act("naloxone_bolus",
    [{"when": "study fingerstick_blood_sugar resulted", "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "A defensible reflex in undifferentiated altered mental status and the wrong answer here, "
      "and the examination tells you so before the drug does. Opioid toxicity is small pupils, a "
      "low respiratory rate and a sedated patient. She has large pupils, a respiratory rate of "
      "25 and is agitated rather than sedated. Every one of those points the other way.\n\n"
      "Neutral before anything has come back, because an empirical dose in an unknown overdose "
      "is a reasonable thing to have done. Discouraged once the case has given you information "
      "and the information does not support it."))

act("thiamine", ALWAYS("neutral"),
    debrief_note=(
      "Harmless and reasonable in undifferentiated altered mental status. Nothing in this "
      "patient's history suggests deficiency and nothing about giving it is wrong."))

act("d50_bolus",
    [{"when": "study fingerstick_blood_sugar resulted", "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Her point-of-care glucose is 110, which is why the case asks for the glucose as a "
      "critical action: it is the one immediately reversible cause of this presentation and it "
      "is excluded in fifteen seconds. Empirical dextrose before the reading is defensible. "
      "After a normal reading it is treating a number you already have."))

act("procainamide_drip",
    [{"when": WIDE, "value": "harmful"},
     {"when": "phase is pulseless_vt", "value": "harmful"},
     {"when": None, "value": "discouraged"}],
    halt_reason=(
      "You gave procainamide, a class IA antiarrhythmic and itself a sodium-channel blocker, to "
      "a patient in a wide-complex tachycardia caused by sodium-channel blockade. The QRS "
      "widened further, the rhythm degenerated, and she arrested."),
    debrief_note=(
      "This is the trap that a wide-complex tachycardia algorithm walks you into. Procainamide "
      "is a reasonable drug for a wide-complex tachycardia of unknown cause. It is a "
      "sodium-channel blocker, and in a poisoning whose whole problem is a blocked sodium "
      "channel it adds to the block.\n\n"
      "The class rule: avoid class IA and class IC antiarrhythmics in sodium-channel-blocker "
      "toxicity. The general rule underneath it, which is worth more than the class rule: treat "
      "the toxicological mechanism rather than reflexively applying a standard antiarrhythmic to "
      "every wide-complex rhythm.\n\n"
      "The drug that treats this rhythm is sodium bicarbonate. If the rhythm is refractory to "
      "adequate bicarbonate and adequate alkalinisation, lidocaine is the antiarrhythmic to "
      "consider, and the reason it is a different answer from procainamide is that it binds and "
      "unbinds the channel fast enough not to add to the block."))

act("amiodarone_bolus_infusion", ALWAYS("discouraged"),
    flags_set=["amiodarone_given"],
    debrief_note=(
      "The commonest wrong drug in a wide-complex tachycardia that is not sinus, and in this "
      "case, given into that rhythm, it arrests her on the spot.\n\n"
      "The reasoning that gets a resident here is the reasoning the case is testing. A "
      "wide-complex tachycardia at 180 with a pressure of 95 is, on a standard algorithm, an "
      "amiodarone rhythm. On that algorithm this is a correct move. What makes it wrong is "
      "that this rhythm is not a re-entrant circuit in a structurally abnormal heart: it is a "
      "poisoned sodium channel, and amiodarone blocks sodium channels among several other "
      "things. Giving it adds to the block that produced the rhythm. It also prolongs the QT, "
      "which is already 495 milliseconds here, in a patient whose potassium channels are "
      "affected too.\n\n"
      "**Treat the mechanism, not the morphology.** The drug for this rhythm is sodium "
      "bicarbonate, which raises the electrochemical gradient across a partially blocked "
      "channel and reduces the fraction of drug bound to it. If the rhythm persists after "
      "adequate bicarbonate and adequate alkalinisation, the antiarrhythmic to discuss with "
      "toxicology is lidocaine, and the reason it is a different answer is that it binds and "
      "unbinds the channel fast enough not to add to the block. Amiodarone and the class IA "
      "and IC agents do not.\n\n"
      "A note on how firmly this case is making the claim. The evidence against amiodarone in "
      "sodium-channel-blocker poisoning is weaker than the evidence against procainamide: it "
      "is mechanistic reasoning and case experience rather than trial data, and amiodarone is "
      "a mixed agent whose class III action is not the problem. The tag is therefore "
      "discouraged rather than harmful, which is the honest strength of the claim, while the "
      "consequence in this phase is an arrest, which is the teaching the case author asked "
      "for. Those two can disagree and here they do; the reviewer should decide whether the "
      "consequence should be softened to match the tag or the tag hardened to match the "
      "consequence. [UNVERIFIED, confirm before release]\n\n"
      "Outside the wide-complex phase it is discouraged and nothing happens, which is also "
      "arguable: amiodarone given to this patient at any point is adding a sodium-channel "
      "blocker to a sodium-channel blocker overdose."))

act("lidocaine_bolus",
    [{"when": WIDE + " AND flag bicarb_given set", "value": "recommended"},
     {"when": WIDE, "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    display_name="Lidocaine",
    debrief_note=(
      "The rescue antiarrhythmic for this poisoning, and only after bicarbonate. Lidocaine is a "
      "class IB agent: it binds the sodium channel with fast on and off kinetics, so unlike the "
      "class IA and IC drugs it does not add meaningfully to the block, and it can suppress the "
      "ventricular ectopy that persists once the pH has been corrected as far as it usefully "
      "can be.\n\n"
      "Be honest about the strength of this. It rests on case reports, on toxicology practice, "
      "and on extrapolation from tricyclic poisoning, and there are recent reports of it working "
      "for refractory diphenhydramine-associated wide-complex dysrhythmia after bicarbonate was "
      "not enough. That is not the same as trial evidence and it should be a toxicology "
      "conversation rather than a reflex.\n\n"
      "Discouraged before bicarbonate, because reaching for the rescue before the first-line "
      "treatment is the error this ordering exists to mark. Note also that the catalog places "
      "lidocaine under the intubation drugs, where it is the pretreatment agent; it is the same "
      "drug and this case is scoring the antiarrhythmic use of it.\n\n"
      "[UNVERIFIED, confirm before release]"))

act("hypertonic_saline_25_bolus",
    [{"when": WIDE + " AND flag bicarb_given set", "value": "recommended"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Additional sodium loading for a QRS that will not narrow when the pH is already at the "
      "top of the useful range, around 7.50 to 7.55. It separates the two halves of what "
      "bicarbonate does: this gives you the sodium without pushing the pH further, which matters "
      "once further alkalinisation costs more than it buys.\n\n"
      "A toxicology-guided move rather than a routine one, and the evidence for it in this "
      "poisoning is limited."))

act("intralipid",
    [{"when": WIDE + " AND flag bicarb_given set", "value": "recommended"},
     {"when": WIDE, "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Intravenous lipid emulsion for life-threatening cardiotoxicity from a lipophilic drug "
      "that has not responded to everything else. Diphenhydramine is lipophilic, and there are "
      "case reports of lipid emulsion in severe diphenhydramine cardiotoxicity.\n\n"
      "Two cautions. The evidence outside local anaesthetic systemic toxicity is case reports "
      "and it is a rescue rather than a treatment, so it belongs after bicarbonate, adequate "
      "alkalinisation and a conversation with toxicology. And it interferes with laboratory "
      "assays and with extracorporeal circuits, which matters if the next step after it is "
      "extracorporeal support.\n\n"
      "Discouraged if it is reached for before bicarbonate."))

act("magnesium_sulfate",
    [{"when": "study magnesium_level resulted", "value": "recommended"},
     {"when": None, "value": "recommended"}],
    flags_set=["magnesium_given"],
    debrief_note=(
      "Two separate reasons, and it is worth knowing which one you are acting on. Her magnesium "
      "is 1.6, which is low, and correcting it is straightforward good care in a patient with a "
      "QTc of 495 who has just seized.\n\n"
      "The second reason is torsades de pointes, which is a real risk in this poisoning and is a "
      "different problem from the wide QRS. Diphenhydramine affects potassium channels as well "
      "as sodium ones, so QT prolongation and QRS widening coexist here. Magnesium is the "
      "treatment for torsades. Sodium bicarbonate is the treatment for the wide QRS. They are "
      "not interchangeable and giving one does not cover the other."))

act("potassium_chloride_kcl",
    [{"when": "flag bicarb_given set", "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Her potassium is 3.8 before any treatment. Bicarbonate drives potassium intracellularly, "
      "so a patient who receives repeated boluses and then an infusion will become hypokalaemic, "
      "and hypokalaemia prolongs the QT in a patient whose QT is already long. Replacing it is "
      "part of running the treatment rather than a separate thought."))

act("norepinephrine_drip",
    [{"when": WIDE + " AND flag bicarb_given set", "value": "recommended"},
     {"when": WIDE, "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    flags_set=["pressor_running"],
    debrief_note=(
      "For hypotension that persists after sodium bicarbonate and after the acidaemia, the "
      "hypoxia and the calcium have been addressed. Norepinephrine is the reasonable first "
      "choice: the hypotension in this poisoning is partly peripheral alpha-receptor blockade "
      "and partly a poisoned myocardium, and an alpha agonist addresses the first directly.\n\n"
      "Discouraged as the first response to a systolic of 95 in the wide-complex phase, because "
      "the pressure there is a consequence of the conduction and the drug that fixes the "
      "conduction fixes the pressure."))

act("normal_saline_1l_bolus", ALWAYS("recommended"),
    flags_set=["fluids_given"],
    debrief_note=(
      "Three reasons and none of them is the tachycardia. She has been agitated and febrile for "
      "hours and is dry. Her creatine kinase is 540 and rising, and volume is the treatment that "
      "protects the kidney in rhabdomyolysis. And judicious crystalloid is part of the response "
      "to the hypotension of a sodium-channel-blocker poisoning, alongside the bicarbonate.\n\n"
      "The author asks for fluid at time zero as part of an empirical sepsis response, which is "
      "the right instinct in an undifferentiated hyperthermic tachycardic eighteen year old.\n\n"
      "The tag covers every crystalloid bolus in the catalog through the equivalence group, "
      "because this case is making a claim about volume rather than about an agent. Judicious is "
      "the word to hold onto: this is not the patient for four litres, and her lungs are clear "
      "for now."))

act("activated_charcoal",
    [{"when": "flag airway_protected set", "value": "recommended"},
     {"when": None, "value": "discouraged"}],
    flags_set=["charcoal_given"],
    debrief_note=(
      "The decontamination question, and the answer turns on the airway rather than on the "
      "drug. Charcoal binds diphenhydramine well, and there is a specific argument for it here: "
      "anticholinergic poisoning slows gastrointestinal motility, so drug remains unabsorbed in "
      "the gut for longer than the usual one-hour window would suggest, and multiple-dose "
      "charcoal has a rationale in a large ingestion for the same reason.\n\n"
      "Against that: she is delirious, agitated and about to seize, and charcoal aspirated into "
      "a lung is a chemical pneumonitis that outlasts the poisoning. It should not be given to a "
      "severely agitated, seizing or obtunded patient without a protected airway, and it must "
      "never delay stabilisation.\n\n"
      "So: discouraged in an unintubated patient in this case, recommended once she has a tube. "
      "Airway safety takes priority over decontamination. Haemodialysis, for completeness, does "
      "not remove diphenhydramine."))

act("whole_bowel_irrigation_by_ng_tube",
    [{"when": "flag airway_protected set", "value": "neutral"},
     {"when": None, "value": "discouraged"}],
    debrief_note=(
      "Not indicated for this ingestion. Whole bowel irrigation belongs to sustained-release "
      "preparations, metal ingestions and body packers, and it carries the same aspiration "
      "objection as charcoal in an unprotected airway. The author's teaching text discusses "
      "gastric lavage for a massive early presentation, which the catalog does not offer and "
      "which is in any case not this."))

for d, note in [
  ("place_orogastric_tube", "The route for charcoal in an intubated patient, and unremarkable."),
  ("place_nasogastric_tube", "As above. Prefer the orogastric route in a patient who has just been intubated."),
]:
    act(d, [{"when": "flag airway_protected set", "value": "neutral"},
            {"when": None, "value": "discouraged"}],
        debrief_note=note + " Discouraged before the airway is protected, for the same aspiration "
                            "reason as charcoal.")

# -------------------------------------------------- the empirical sepsis and CNS workup
# Part 1's Ideal Scenario Flow asks for a sepsis bundle at time zero and Part 2 never
# mentions sepsis. Both are right for the moment they describe, so these are tagged for the
# moment rather than for the case: good practice in a febrile confused eighteen year old
# before anything is known, and the wrong road to still be on once the toxidrome has
# declared itself. The switch is the toxicology screen resulting, which is the first piece
# of hard evidence the case gives, rather than a flag for "the resident has worked it out",
# because the condition language cannot see what anybody has worked out.

act("ceftriaxone",
    [{"when": "study urine_tox_screen resulted", "value": "discouraged"},
     {"when": PRES, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    flags_set=["abx_given"],
    display_name="Empirical antibiotics",
    debrief_note=(
      "Empirical antibiotics in a confused, febrile, tachycardic eighteen year old with a white "
      "count of 16 are good practice, and the author asks for a sepsis bundle at time zero. "
      "Nothing about giving them is wrong, and this case does not want a resident to learn that "
      "covering for meningitis in this patient is a mistake.\n\n"
      "What the case does want is that the antibiotics are not the end of the thought. The neck "
      "is supple, there is no rash, the skin is hot and dry rather than hot and wet, the pupils "
      "are large, the bowel sounds are absent and the bladder is palpable. That combination is a "
      "toxidrome and not a meningitis, and every minute spent on the infectious workup after "
      "that point is a minute the ECG is not being looked at.\n\n"
      "Tagged discouraged once the toxicology screen has resulted, which is the case saying that "
      "continuing down this road after the evidence has arrived is the error, not starting down "
      "it.\n\n"
      "Coverage note: this action covers vancomycin and cefepime as well, because the case is "
      "scoring the act of empirical antimicrobial cover rather than a regimen. It is not making "
      "a claim about which regimen is right for suspected bacterial meningitis in this age "
      "group."))

act("acyclovir",
    [{"when": "study urine_tox_screen resulted", "value": "discouraged"},
     {"when": PRES, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "The same reasoning as the antibiotics. Herpes encephalitis belongs on the differential "
      "for a febrile confused young person and empirical acyclovir before the picture is clear "
      "is defensible. It stops being defensible once the toxidrome is established."))

act("lumbar_puncture",
    [{"when": "study urine_tox_screen resulted", "value": "discouraged"},
     {"when": SEIZ + " OR " + WIDE, "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    debrief_note=(
      "Reasonable to have considered at time zero and a poor idea by the time it can be done. "
      "Three objections in this patient, and the third is the one that matters. She is agitated "
      "and will not hold still. She is about to seize, or has just seized, and positioning her "
      "for a lumbar puncture in the middle of that is not safe. And the examination is against "
      "it: the neck is supple, there is no meningism and there is no rash.\n\n"
      "Empirical antibiotics do not require a lumbar puncture first. If meningitis remains a "
      "real concern, cover her and defer the tap. Discouraged rather than harmful because a "
      "deferred tap in a covered patient costs a microbiological diagnosis rather than a life."))

for cid, tag_v, note in [
  ("ecg_12_lead", None,
   "The pivot of the case and the action the whole thing is arranged around. Two facts make it "
   "urgent. Diphenhydramine at this dose blocks fast cardiac sodium channels, and QRS "
   "prolongation is the marker that separates the patients who are going to have ventricular "
   "dysrhythmias from the ones who are not. And the widening is invisible without the tracing: "
   "she looks like an ordinary anticholinergic toxidrome and her monitor shows a sinus "
   "tachycardia.\n\n"
   "What to look for: a QRS above 100 milliseconds, a terminal R wave in lead aVR, an increased "
   "R to S ratio in aVR, rightward deviation of the terminal QRS axis, and any wide-complex "
   "rhythm. Hers is 132 milliseconds with a 5 millimetre terminal R in aVR. A prolonged QTc, "
   "which she also has, is a separate problem needing a separate treatment.\n\n"
   "It is also the gate on physostigmine. The standard teaching is to look at the ECG for signs "
   "of sodium-channel effect before considering physostigmine at all, and this case enforces "
   "that: physostigmine given before this study has resulted halts the run.\n\n"
   "Repeat it. A normal ECG early does not exclude later cardiotoxicity, and the QRS is what you "
   "titrate the bicarbonate against, so it is a serial measurement rather than a single one."),
  ("fingerstick_blood_sugar", "critical",
   "Fifteen seconds, and it removes the one cause of this presentation that is instantly "
   "reversible. Hers is 110, which is normal, and the point of it is that it is normal: a "
   "resident who has not checked it is carrying an unexcluded hypoglycaemia through the rest of "
   "the case. The author lists it in her Anticipated Management Mistakes."),
]:
    if cid == "ecg_12_lead":
        act(cid,
            [{"when": PRES, "value": "critical"}, {"when": None, "value": "critical"}],
            flags_set_repeat=[{"flag": "ecg_repeated", "after_administrations": 2,
                               "counter": "ecg_tracings"}],
            prompt={"deadline_seconds": 75,
                    "guard": "(" + PRES + " OR " + POST + ") AND NOT study ecg_12_lead ordered",
                    "text": "What do you think is causing her confusion? Do you want a tracing on her?",
                    "escalation": {"deadline_seconds": 150,
                                   "text": "There's still no ECG on her. Do you want me to run one now?"}},
            debrief_note=note)
    elif cid == "fingerstick_blood_sugar":
        act(cid, ALWAYS(tag_v), debrief_note=note,
            prompt={"deadline_seconds": 55,
                    "guard": PRES + " AND NOT study fingerstick_blood_sugar ordered",
                    "text": ("Do you want a sugar on her? I can do it now while I have got her "
                             "arm.")})
    else:
        act(cid, ALWAYS(tag_v), debrief_note=note)

for cid, tag_v, note in [
  ("basic_chemistry_chem_7", "recommended",
   "Sodium 135, potassium 3.8, chloride 109, bicarbonate 13, urea 12, creatinine 0.8, glucose "
   "120. The bicarbonate of 13 is the number to look at: with the chloride of 109 it gives an "
   "anion gap of 13 and it agrees with the pH of 7.28 on the gas. It is also the baseline "
   "against which the effect of treatment is read, because sodium bicarbonate will move the "
   "sodium, the potassium and the pH."),
  ("complete_blood_count_cbc", "recommended",
   "White count 16, which is a stress response rather than an infection and is not a reason to "
   "stop thinking about the toxidrome. The haemoglobin of 16.9 and the haematocrit of 47.2 are "
   "above the usual female interval and read as haemoconcentration in a patient who has been hot "
   "and not drinking for hours. Both numbers are the author's; the reading of them is not."),
  ("creatine_kinase_ck", "recommended",
   "540, and rising. Prolonged agitation, hyperthermia and a convulsion produce rhabdomyolysis, "
   "and this is the beginning of it rather than established disease. What follows from it is "
   "practical: serial creatine kinase, creatinine and electrolytes, volume with crystalloid, "
   "urine output measured, and a urinalysis that is positive for blood with no red cells on "
   "microscopy if myoglobin is there. Sedating her and cooling her are also treatments for it, "
   "because they stop the muscle activity producing it."),
  ("arterial_blood_gas", "recommended",
   "pH 7.28, pCO2 34, pO2 94, bicarbonate 13, lactate 3.1 on room air. A partly compensated "
   "metabolic acidosis from the agitation and the muscle activity. It matters more here than it "
   "would elsewhere: acidaemia increases the un-ionised fraction of a sodium-channel blocker "
   "available to the channel, so the pH is part of the cardiac problem rather than a separate "
   "observation. It is also the measurement you titrate alkalinisation against, taking the pH "
   "toward about 7.50 to 7.55 and not beyond."),
  ("venous_blood_gas", "recommended",
   "Adequate for the pH and the bicarbonate, which are the two numbers being followed. Prefer "
   "the arterial sample if the oxygenation is in question."),
  ("lactate", "recommended",
   "3.1, from the agitation and the muscle activity rather than from sepsis or from hypoperfusion. "
   "Worth repeating after she is sedated, because it should fall."),
  ("acetaminophen_level", "recommended",
   "Zero here, and the reason to send it is that you cannot know that without sending it. "
   "Over-the-counter sleep and cold preparations combine diphenhydramine with acetaminophen, the "
   "reported exposure in a deliberate overdose is often incomplete, and acetaminophen poisoning "
   "is silent for the first day and treatable throughout it. Forgetting co-ingestions is on the "
   "performance gap list of the author's own debriefing guide."),
  ("salicylate_aspirin_level", "recommended",
   "Zero. The same reasoning as acetaminophen, with the added point that salicylate poisoning "
   "also produces hyperthermia, agitation and a metabolic acidosis, which is the picture in "
   "front of you."),
  ("ethanol_level_etoh", "recommended", "Under 10 mg/dL. Routine in a deliberate ingestion."),
  ("urine_tox_screen", "recommended",
   "Positive for tricyclic antidepressants, and it is a false positive. Diphenhydramine "
   "cross-reacts with the tricyclic immunoassay on several platforms. Two things follow.\n\n"
   "The trap: a resident who anchors on it now has a tricyclic overdose, which is the wrong "
   "history. It does not change the immediate management, because the treatment for a wide QRS "
   "is sodium bicarbonate either way, and that is the more useful lesson: the ECG told you what "
   "to do and the screen did not add to it.\n\n"
   "The general point about these assays: a urine drug screen is a qualitative immunoassay with "
   "known cross-reactants and a long detection window. It tells you what somebody may have been "
   "exposed to at some point. It does not tell you what is causing what is in front of you, and "
   "it is not the reason to give or withhold a treatment."),
  ("urine_hcg_qualitative", "recommended",
   "Negative. Mandatory in a woman of reproductive age with an overdose, and the author lists "
   "hCG among the studies she expects."),
  ("serum_hcg_quantitative", "recommended", "Negative. Either route answers the question."),
  ("urinalysis", "recommended",
   "Send it. In rhabdomyolysis the dipstick is positive for blood and the microscopy shows no "
   "red cells, which is myoglobin. It also excludes the urinary source a febrile confused "
   "patient might have."),
  ("magnesium_level", "recommended",
   "1.6, which is low. Correct it: hypomagnesaemia prolongs the QT in a patient whose QTc is "
   "already 495, and magnesium is the treatment for torsades if it comes."),
  ("calcium_ionized", "recommended",
   "Worth having before and during bicarbonate. Alkalinisation lowers the ionised calcium, and "
   "a falling ionised calcium is one of the complications of the treatment rather than of the "
   "poisoning."),
  ("liver_function_tests_lfts", "recommended",
   "Reasonable in a deliberate ingestion of unknown content. Normal here."),
  ("coagulation_panel", "neutral", "Normal. Not case-determining."),
  ("blood_culture_x_2", "recommended",
   "Part of the empirical sepsis workup the author asks for at time zero, and there is no cost "
   "to having sent them. Note the limitation of this simulator rather than of the medicine: "
   "cultures return 'no growth to date' because a five-second laboratory turnaround cannot "
   "represent a 48-hour culture."),
  ("troponin_t", "neutral",
   "Reasonable and not diagnostic. A mildly raised troponin in this setting reflects demand "
   "ischaemia and the poisoned myocardium, and it will not change what you do."),
  ("tsh", "neutral",
   "Thyroid storm is on the differential for a hyperthermic tachycardic agitated young woman "
   "and this is the test that addresses it. It is normal, and it will not come back in time to "
   "matter."),
  ("ultrasound_cardiac", "neutral",
   "Not the study this case turns on. It will show a fast heart with reasonable function and it "
   "will not tell you about the sodium channel, which is what the ECG is for."),
]:
    act(cid, ALWAYS(tag_v), debrief_note=note)

act("xr_chest", ALWAYS("recommended"),
    debrief_note=(
      "Normal. Reasonable in an obtunded patient of unknown cause and worth having as a baseline "
      "before she is intubated and before she is given charcoal. Its value here is exclusion: no "
      "aspiration, no pneumonia, no pulmonary oedema."))

act("ct_head", ALWAYS("recommended"),
    debrief_note=(
      "Normal. Defensible and often necessary in altered mental status and a first seizure, and "
      "the thing to keep hold of is what it costs. The scanner is not on the monitor and she is "
      "hyperthermic with a wide QRS and about to seize. If she goes, she goes late, sedated, "
      "with an airway and with somebody watching the rhythm, and she does not go instead of "
      "getting an ECG.\n\n"
      "The examination points away from a structural cause: the neck is supple, the pupils are "
      "equal, there are no lateralising signs and there is no history of trauma."))

for cid, tag_v, note in [
  ("consult_toxicology", None,
   "The critical consultation, and it is early rather than late. A regional poison centre or a "
   "medical toxicology service will help with three things this case actually contains: how far "
   "to push the alkalinisation and what to watch while doing it, whether and when to reach for "
   "lidocaine, hypertonic saline or lipid emulsion, and what the next twelve hours look like.\n\n"
   "The author asks for it explicitly and puts it in her debriefing objectives as the importance "
   "of calling the poison centre. The rule underneath it: call before you need the rescue, not "
   "after. Do not wait for cardiac arrest to involve toxicology or to find out whether "
   "extracorporeal support is available."),
  ("consult_critical_care", "critical",
   "She is going to a critical care bed and the earlier that is arranged the better. Part 2 of "
   "the author's document lists nine indications for critical care admission after this "
   "poisoning and this patient meets at least six: QRS widening, a seizure, persistent delirium, "
   "hyperthermia, a bicarbonate infusion, and a significant metabolic abnormality. Add "
   "intubation if she has been intubated."),
]:
    if cid == "consult_toxicology":
        act(cid,
            [{"when": PRES, "value": "critical"}, {"when": None, "value": "critical"}],
            flags_set=["tox_consulted"],
            prompt={"deadline_seconds": 100,
                    "guard": POST + " OR " + RESOLVING,
                    "text": ("Her mom's back in. She got her son to look round the bedroom and he's "
                             "found an empty Benadryl bottle by the bed. Do you want me to get "
                             "anyone on the phone about it?"),
                    "escalation": {"deadline_seconds": 160,
                                   "text": "Nobody's spoken to toxicology or the poison centre yet. Do you want me to call them?"}},
            debrief_note=note)
    else:
        act(cid, ALWAYS(tag_v), debrief_note=note)

act("consult_psychiatry",
    [{"when": RESOLVING, "value": "recommended"},
     {"when": PRES + " OR " + SEIZ + " OR " + WIDE, "value": "discouraged"},
     {"when": None, "value": "recommended"}],
    debrief_note=(
      "She needs psychiatry, and she does not need it yet. This is a deliberate ingestion in a "
      "depressed eighteen year old who has been bullied and has withdrawn from her friends, and "
      "a psychiatric assessment and a safety plan are part of her care.\n\n"
      "The reason it is discouraged early is the thing this case most wants said about "
      "disposition. Medical clearance is not a form and it is not a phase you enter by "
      "recognising that the overdose was intentional. A patient with an unresolved wide QRS, a "
      "temperature of 40 degrees and a recent seizure is not medically cleared, and a psychiatric "
      "unit cannot monitor her rhythm. Consult when the medical problem is treated, and hand her "
      "over to a monitored medical bed with psychiatry involved rather than to psychiatry."))

for cid, note in [
  ("consult_neurology", "Reasonable for a first seizure and not what this seizure needs. It is a "
                        "toxic seizure with an identified cause and the treatment is a benzodiazepine "
                        "and correction of the physiology."),
  ("consult_cardiology", "Understandable in a wide-complex tachycardia and not the call this "
                         "rhythm needs. The rhythm is a poisoning; toxicology is the service that "
                         "will help with it."),
  ("consult_renal", "Reasonable to have in mind for the rhabdomyolysis. Diphenhydramine itself is "
                    "not removed by haemodialysis, which is worth knowing before anyone asks."),
]:
    act(cid, ALWAYS("neutral"), debrief_note=note)

# -------------------------------------------------------------------- examinations
# Section 11.2: fourteen maneuvers, closed set, and the routing map decides which one owns
# each finding. Twelve are authored here; back and genitourinary carry the catalog default,
# except that the palpable bladder is authored on the genitourinary examination because the
# author lists it there and it is one of the findings that makes the toxidrome.
for cid, note in [
  ("exam_heent", "The pupils are the finding. Equal, large and reactive, with the roving "
                 "conjugate eye movements the author describes as opsoclonus, and dry mucous "
                 "membranes. Mydriasis plus dry mucosa plus dry skin is an antimuscarinic "
                 "picture and is what separates it from a sympathomimetic one, where the patient "
                 "is wet."),
  ("exam_neck", "Supple, no meningism. A negative that matters: it is the examination finding "
                "that most argues against the meningitis the fever and the confusion suggest."),
  ("exam_card", "Sinus tachycardia, no murmur, no peripheral oedema. The rate is the "
                "antimuscarinic effect on the heart and it is the least informative abnormal "
                "sign she has, because it is present in every differential on the list."),
  ("exam_pulm", "Clear. Another negative that earns its place: no aspiration, no pneumonia, and "
                "nothing to explain a fever."),
  ("exam_abd", "Absent bowel sounds and a palpable bladder. Both are antimuscarinic, both are "
               "easy to miss, and together with the pupils and the skin they are the toxidrome. "
               "The distended bladder is also part of the agitation."),
  ("exam_gu", "The palpable bladder again, from the genitourinary side. Drain it."),
  ("exam_skin", "Hot and dry, with no sweating anywhere. This is the discriminator. A "
                "hyperthermic agitated patient who is soaked is sympathomimetic, septic or in a "
                "serotonin syndrome. One who is bone dry at 40 degrees has blocked muscarinic "
                "receptors on her sweat glands, and it is also why she cannot cool herself."),
  ("exam_neuro", "Confused and agitated with no focal deficit, no meningism and no clonus. Two "
                 "negatives are doing work here: no focal signs argues against a structural "
                 "cause, and no clonus or hyperreflexia argues against serotonin syndrome, which "
                 "is otherwise the closest mimic of what you are looking at."),
  ("exam_psych", "Agitated, disoriented, picking at the bedclothes and at the leads, and not "
                 "consistently responsive to voice. This is delirium rather than a psychiatric "
                 "presentation, and the distinction is the difference between a medical bed and "
                 "a psychiatric one."),
  ("exam_airway", "Patent on arrival and progressively less so. Worth reassessing after the "
                  "seizure rather than once."),
  ("exam_breath", "Tachypnoeic without increased work of breathing, which is the respiratory "
                  "compensation for a metabolic acidosis rather than a lung problem."),
  ("exam_circ", "Warm, flushed, well perfused, with a fast regular pulse. Perfusion is fine "
                "until the conduction fails."),
  ("exam_msk", "No trauma, no oedema, full range of movement. Worth a look because she was "
               "found on the floor of her bedroom and nobody saw what happened."),
]:
    act(cid, ALWAYS("neutral"), debrief_note=note)

act("handoff_submit", ALWAYS("neutral"),
    debrief_note="Ends the case and generates the debrief.")

# ==================================================================== follow-ups

FOLLOW_UPS = [
 {"id": "post_intubation_sedation",
  "triggered_by": "intubate_rapid_sequence",
  "applies_when": "flag airway_protected set",
  "deadline_seconds": 90,
  "satisfied_by": ["propofol_infusion", "ketamine_infusion", "propofol_bolus",
                   "fentanyl_bolus", "morphine_bolus", "lorazepam_bolus"],
  "satisfied_by_note": ("Midazolam is not listed because it is not a case action in its own "
                        "right: it is covered by lorazepam_bolus, and a covered sibling records "
                        "the covering action as taken, so inducing with midazolam discharges "
                        "this obligation through lorazepam_bolus."),
  "nurse_prompt": "She's tubed and the roc is still on board. What do you want her sedated with?",
  "debrief_note": (
    "A paralysed patient with no sedation is awake and cannot say so. Beyond the general "
    "obligation, sedation is a treatment in this case rather than a comfort measure: it stops "
    "the muscle activity that is generating the hyperthermia and the rhabdomyolysis, and "
    "propofol and the benzodiazepines are anticonvulsants in a patient whose seizure may "
    "recur.")},

 {"id": "bicarbonate_reassessment",
  "triggered_by": "na_bicarbonate_bolus",
  "applies_when": "flag bicarb_given set",
  "deadline_seconds": 100,
  "satisfied_when": "flag bicarb_titrated set OR flag bicarb_infusion_running set",
  "nurse_prompt": "That's one amp of bicarb in. Do you want another, or do you want it as a drip?",
  "debrief_note": (
    "Giving one dose of bicarbonate and moving on is on the author's own list of common "
    "performance gaps, and it is the failure mode this obligation exists to catch. The endpoint "
    "of bicarbonate therapy is not a predetermined number of ampoules. It is a narrowing QRS, "
    "the resolution of ventricular dysrhythmia and an improving blood pressure, reassessed after "
    "each dose, with an infusion started once the initial improvement is there.\n\n"
    "The obligation is discharged either by a second bolus or by starting an infusion, because "
    "both are the same decision: that the treatment continues until the conduction says it can "
    "stop. It uses satisfied_when rather than satisfied_by because a repeat of the triggering "
    "action cannot be expressed as set membership, per authoring 8.2.")},

 {"id": "repeat_ecg_after_bicarbonate",
  "triggered_by": "na_bicarbonate_bolus",
  "applies_when": "flag bicarb_given set",
  "deadline_seconds": 130,
  "satisfied_when": "flag ecg_repeated set",
  "nurse_prompt": "Do you want another tracing to see what the bicarb has done to the QRS?",
  "debrief_note": (
    "The QRS is the thing being titrated against, so it has to be measured more than once. A "
    "normal or improved tracing early does not exclude later cardiotoxicity either: the drug is "
    "still being absorbed from a gut that antimuscarinic effects have slowed down, and the "
    "complexes can widen again hours later. Serial tracings and continuous monitoring are the "
    "standard of care here, and the case asks for a second one.")},
]
