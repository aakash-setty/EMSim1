"""ALLEY part 2: the action spine, tags, flags, prompts and vital effects.

Every clinical judgment here is model output awaiting a physician's signature, except the
decisions in ALLEY-SEED.md section 0. Markers sit only in fields the interface strips
(authoring 10.3): an action's debrief_note.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

U0 = "phase is presentation"
U1 = "phase is drifting"
U2 = "phase is untreated_floor"
H0 = "phase is held_early"
H1 = "phase is held_mid"
H2 = "phase is held_late"
IMP = "phase is improving"
UNTREATED = U0 + " OR " + U1 + " OR " + U2
HELD = H0 + " OR " + H1 + " OR " + H2
NOT_IMPROVED = UNTREATED + " OR " + HELD
GAS_R = "(study venous_blood_gas resulted OR study arterial_blood_gas resulted)"

EXTRIP = " [UNVERIFIED: Roberts et al., Crit Care Med 2015 (EXTRIP), read through an abstract page and a summary via search]"
LABEL = " [UNVERIFIED: fomepizole prescribing information, read through search]"
AACT = " [UNVERIFIED: AACT 2002 guideline not opened, criteria read through secondary summaries via search]"
KRAUT = " [UNVERIFIED: Kraut and Mullins, N Engl J Med 2018, not opened]"
MEMORY = " [UNVERIFIED: general teaching written by a model from memory, no source opened]"
BC = " [UNVERIFIED: Emergency Care BC methanol summary and the Austin Health toxicology guideline, read through search]"

IV_LINE = [{
  "when": "flag iv_access set OR flag central_access set OR flag io_access set",
  "failure_message": "He doesn't have a line yet. Do you want me to get IV access first?"}]

# =====================================================================  FIRST MINUTES

act("attach_monitor", ALWAYS("recommended"),
    flags_set=["monitor_on"],
    debrief_note="Nothing shows until the monitor is on. His respiratory rate is the first clue in the case.")

act("insert_iv", ALWAYS("recommended"),
    flags_set=["iv_access"],
    debrief_note="Fomepizole, bicarbonate and folinic acid all need a line.")

for cid, flag in (("central_venous_catheter_triple_lumen", "central_access"),
                  ("central_venous_catheter_cordis", "central_access"),
                  ("intraosseous_line", "io_access")):
    act(cid, ALWAYS("neutral"), flags_set=[flag],
        debrief_note="Counts as a line for every intravenous drug. Not needed and not scored.")

# =====================================================================  STUDIES

act("venous_blood_gas",
    [{"when": UNTREATED, "value": "critical"}, {"when": None, "value": "recommended"}],
    expectation_label="Blood gas (venous is enough)",
    also_satisfies=[{"id": "gas_repeated", "when": "flag bicarb_acting set OR " + IMP}],
    prompt={"deadline_seconds": 40,
            "guard": U0 + " AND NOT study venous_blood_gas ordered AND NOT study arterial_blood_gas ordered",
            "text": "Doc, he's breathing awfully fast for someone who's just drunk. Anything you want to check?"},
    debrief_note=(
      "A respiratory rate of 27 with clear lungs and a normal saturation is breathing to "
      "blow off acid until proven otherwise. His gas showed a pH of 7.19 with a pCO2 of 19 "
      "and a bicarbonate of 7: a severe metabolic acidosis with the breathing doing all it "
      "can. By Winter's formula the expected pCO2 is 1.5 times 7 plus 8, about 18.5, give "
      "or take 2, so this is appropriate compensation and not a second disorder.\n\n"
      "Here both gases show the same numbers. In practice venous pCO2 runs a few points "
      "higher, and Winter's formula is for arterial pCO2.\n\n"
      "A repeat gas is how you see what a treatment did: unchanged after fomepizole alone, "
      "better for a few minutes after bicarbonate alone, better and staying better with both."
      + MEMORY))

act("gas_repeated", ALWAYS("neutral"),
    hidden=True, display_name="Repeat gas after bicarbonate",
    debrief_note=("Not an order. Credited when a gas is sent while bicarbonate is acting or "
                  "once he is improving. The repeat-gas follow-up reads it."))

act("arterial_blood_gas",
    [{"when": UNTREATED, "value": "neutral"}, {"when": None, "value": "neutral"}],
    also_satisfies=[{"id": "venous_blood_gas", "when": None},
                    {"id": "gas_repeated", "when": "flag bicarb_acting set OR " + IMP}],
    debrief_note=(
      "Accepted in place of the venous gas. In this case both show the same numbers, which "
      "is a simplification. Nothing here needs an arterial puncture." + MEMORY))

act("basic_chemistry_chem_7",
    [{"when": UNTREATED, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Chemistry, for the anion gap",
    debrief_note=(
      "Sodium 140 minus chloride 103 minus bicarbonate 7 is an anion gap of 30. His lactate "
      "of 3.6 and beta-hydroxybutyrate of 0.5 account for a few of those. Something "
      "unmeasured accounts for the rest. In a drinker the list is short: alcoholic "
      "ketoacidosis (the ketones say no), lactate (too low), salicylate (undetectable), "
      "and the toxic alcohols." + MEMORY))

act("ethanol_level_etoh",
    [{"when": UNTREATED, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Ethanol level",
    debrief_note=(
      "Twenty-eight mg/dL. Too low to explain how drunk he looks, especially in a heavy "
      "drinker, and far too low to protect him. About 100 mg/dL of ethanol is needed to "
      "block alcohol dehydrogenase. It is also part of the osmolar gap: divide by about 3.7 "
      "to 4.6 and subtract it." + KRAUT))

act("osmolality",
    [{"when": UNTREATED, "value": "critical"}, {"when": HELD, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Measured serum osmolality",
    prompt={"deadline_seconds": 50,
            "guard": "(" + U0 + " OR " + U1 + ") AND study ethanol_level_etoh resulted AND NOT study osmolality ordered",
            "text": "His alcohol level was only twenty-eight. Why does he look like this?"},
    debrief_note=(
      "It has to be ordered by name. Measured 328. Calculated: two times the sodium (280) "
      "plus glucose over 18 (5) plus BUN over 2.8 (5) is 290. The gap is 38. His ethanol "
      "explains 6 to 8 of it. About 30 is unexplained.\n\n"
      "The methanol level, a send-out that came back the next day, was 96 mg/dL. Divided by "
      "3.2 that is about 30, the unexplained gap.\n\n"
      "The osmolar gap is highest early, while the alcohol is still there, and falls as it "
      "is turned into acid and the anion gap rises. A normal osmolar gap late in the course "
      "does not exclude a toxic alcohol." + KRAUT + MEMORY))

act("lactate", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note="3.6 to 4.6. Raised, and nowhere near enough to explain an anion gap of 30. Formate itself raises lactate a little." + MEMORY)

act("beta_hydroxybutyrate", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "0.5 mmol/L. A drinker who has not eaten for days is the classic setting for alcoholic "
      "ketoacidosis, and this result is how you rule it out." + MEMORY))

act("salicylate_aspirin_level", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Undetectable. Salicylate causes fast breathing and an anion gap acidosis, often with "
      "a pCO2 lower than Winter's formula predicts. His compensation was appropriate." + MEMORY))

act("acetaminophen_level", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note="Undetectable. The standard co-ingestant screen in any unclear poisoning." + MEMORY)

act("fingerstick_blood_sugar", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    expectation_label="Bedside glucose",
    debrief_note="90. Any altered patient gets one." + MEMORY)

act("ecg_12_lead", [{"when": UNTREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note="Sinus tachycardia with normal intervals. Worth having with a potassium of 4.9 to 5.2 and a severe acidosis." + MEMORY)

act("urinalysis", ALWAYS("neutral"),
    debrief_note="Trace ketones, no crystals. Crystals are an ethylene glycol finding, and their absence excludes nothing." + MEMORY)

act("xr_chest", ALWAYS("neutral"),
    debrief_note="Clear. His fast breathing is not from his lungs.")

act("ct_head", ALWAYS("neutral"),
    also_satisfies=[{"id": "away_from_u0", "when": U0}, {"id": "away_from_u1", "when": U1}],
    debrief_note=(
      "Normal. A CT is reasonable in an altered drinker found outside. Ordered before the "
      "fomepizole, it took him away for what stands for the better part of an hour, and "
      "formate kept being made while he was gone. After the fomepizole it cost nothing.\n\n"
      "Methanol can injure the putamen, but that shows on imaging later if at all." + MEMORY))

# =====================================================================  TREATMENT

act("fomepizole",
    [{"when": UNTREATED, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Fomepizole, on suspicion",
    flags_set=["fomepizole_given"],
    prerequisites=IV_LINE,
    prompt={"deadline_seconds": 60, "guard": U2,
            "text": ("Same as before, but he's working to breathe and he missed the cup when I "
                     "handed it to him. What do you think is going on?"),
            "escalation": {"deadline_seconds": 150,
                           "text": ("There's an empty jug of something blue in his backpack. "
                                    "Want me to get poison control on the phone?")}},
    debrief_note=(
      "Fomepizole blocks alcohol dehydrogenase, so the methanol still in him is no longer "
      "turned into formate. Give it on suspicion. The label says to begin it on suspicion of "
      "ingestion based on the history or the acid-base findings, and a methanol level here "
      "is a send-out that takes a day.\n\n"
      "Then watch what it did not do. Nothing changed on the monitor and a repeat gas was "
      "the same. Fomepizole stops production. It does not buffer the acid or remove the "
      "formate already there. The patient stops getting worse and does not get better.\n\n"
      "It also makes the methanol itself leave very slowly, with a half-life measured in "
      "days, which is one more reason he needs dialysis.\n\n"
      "The commonly taught criteria for starting it: a documented level of 20 mg/dL or "
      "more, or a documented ingestion with an osmolar gap above 10, or suspicion plus at "
      "least two of pH under 7.3, bicarbonate under 20 and osmolar gap above 10. He met all "
      "three on arrival.\n\n"
      "Vision: given at the arrival tier, his vision is likely to improve. Given later, "
      "after his vision had worsened, it locked in that loss. The case scripts this as a "
      "teaching device, not an outcome prediction."
      + LABEL + AACT + " [UNVERIFIED: methanol half-life under fomepizole from the Utah Poison Control Center page, read through search]"))

BICARB_EFFECTS = []
for ph, deltas in (("presentation", {"heart_rate": -8, "systolic_bp": -2, "diastolic_bp": -2, "respiratory_rate": -3}),
                   ("drifting", {"heart_rate": -10, "respiratory_rate": -6}),
                   ("untreated_floor", {"heart_rate": -12, "systolic_bp": 4, "diastolic_bp": 2,
                                        "respiratory_rate": -8, "oxygen_saturation": 1})):
    for vital, d in deltas.items():
        BICARB_EFFECTS.append({
          "vital": vital, "delta": d, "key": "bicarb_" + vital + "_" + ph,
          "while": "flag bicarb_acting set AND phase is " + ph,
          "note": ("Teaching choice. Takes this tier to the owner's buffered numbers (HR 104, "
                   "BP 130/82, RR 24) while bicarbonate acts without fomepizole. In a held "
                   "phase bicarbonate moves the phase instead.")})

BICARB_NOTE = (
  "Sodium bicarbonate is recommended when the pH is under 7.30. Correcting the acidemia is "
  "thought to reduce formic acid entering tissue, including the optic nerve.\n\n"
  "Alone, it bought a few minutes. His breathing eased and the gas looked better, and acid "
  "production carried on underneath: the clock kept running, and when the bicarbonate was "
  "used up he was where the untreated clock had taken him. With fomepizole on board, the "
  "same bicarbonate stayed, because no more acid was being made.\n\n"
  "The anion gap barely moved. Bicarbonate buffers formate. It does not remove it."
  + BC + KRAUT)

act("na_bicarbonate_bolus",
    [{"when": NOT_IMPROVED, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Sodium bicarbonate",
    flags_set_timed=[{"flag": "bicarb_acting", "duration_seconds": 180,
                      "lapse_note": "That bicarb's all run in. Want a repeat gas?"}],
    follow_ups_triggered=["repeat_gas_after_bicarbonate"],
    prerequisites=IV_LINE,
    vital_effects=BICARB_EFFECTS,
    prompt={"deadline_seconds": 120, "guard": HELD,
            "text": ("He's not getting worse, but he's still breathing fast and he still can't "
                     "see. Should we do something?")},
    debrief_note=BICARB_NOTE)

act("na_bicarbonate_infusion", ALWAYS("neutral"),
    flags_set_timed=[{"flag": "bicarb_acting", "duration_seconds": 1800,
                      "lapse_note": "That bicarb's all run in. Want a repeat gas?"}],
    follow_ups_triggered=["repeat_gas_after_bicarbonate"],
    prerequisites=IV_LINE,
    vital_effects=BICARB_EFFECTS,
    also_satisfies=[{"id": "na_bicarbonate_bolus", "when": None}],
    debrief_note=(
      "Counted as his bicarbonate. Within this case an infusion keeps buffering for as long "
      "as the case runs, which is a simplification: without fomepizole, acid production "
      "keeps outrunning it over hours, and the clock kept running underneath." + BC))

act("stop_na_bicarbonate", ALWAYS("neutral"),
    debrief_note=(
      "In this case stopping the infusion does not end its buffering. A simplification, "
      "listed as a known gap."))

act("folinic_acid", ALWAYS("recommended"),
    display_name="Folinic acid (leucovorin)",
    flags_set=["folinic_given"],
    prerequisites=IV_LINE,
    voice_phrases=["folinic acid", "leucovorin", "give folinic acid", "give leucovorin"],
    debrief_note=(
      "Folinic acid is a cofactor for the enzyme that breaks formate down to carbon dioxide "
      "and water, so it is given to speed formate clearance. It is low risk and widely "
      "recommended. Human evidence that it changes outcome is limited. Folic acid is used "
      "where folinic acid is not available.\n\n"
      "This button exists only in this case (owner, 11 November 2026)." + MEMORY))

act("thiamine", ALWAYS("neutral"),
    debrief_note=(
      "Reasonable in a malnourished heavy drinker with altered mentation. It does nothing "
      "for methanol and it is not penalized (owner, 11 November 2026)." + MEMORY))

act("normal_saline_1l_bolus", ALWAYS("neutral"),
    flags_set=["fluids_given"],
    vital_effects=[{"vital": "heart_rate", "delta": -5, "key": "fluid_hr",
                    "note": "Teaching choice. He is a little dry from vomiting and not eating."}],
    debrief_note=(
      "Reasonable. He has been vomiting and not eating. Notice what it did not do: his heart "
      "rate came down a little and his breathing did not change, because the breathing is "
      "for the acid and fluid does nothing about the acid." + MEMORY))

for cid, note in [
  ("d50_bolus", "His glucose was 90. Not needed, and not harmful. Not scored."),
  ("naloxone_bolus", ("Not an opioid picture: he is breathing fast and deep, not slow, and his "
                      "pupils are not small. Not harmful. Not scored.")),
  ("ondansetron", "Kind and reasonable for his nausea. Not scored."),
  ("nasal_cannula_oxygen", "His saturation is 99 on room air. Not needed. Not scored."),
  ("non_rebreather_mask", "His saturation is 99 on room air. Not needed. Not scored."),
]:
    act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)

act("activated_charcoal", ALWAYS("discouraged"),
    debrief_note=(
      "Charcoal does not bind alcohols, and absorption was long over. He is drowsy and "
      "vomiting, so it added aspiration risk for no benefit." + KRAUT))

# =====================================================================  SEDATION
SED_EFFECTS = [
  {"vital": "respiratory_rate", "delta": -6, "key": "sed_rr", "while": "flag sedated set",
   "note": "Teaching choice. The sedative takes away part of his compensatory breathing."},
  {"vital": "systolic_bp", "delta": -8, "key": "sed_sbp", "while": "flag sedated set", "note": "Teaching choice."},
  {"vital": "diastolic_bp", "delta": -4, "key": "sed_dbp", "while": "flag sedated set", "note": "Teaching choice."},
  {"vital": "oxygen_saturation", "delta": -2, "key": "sed_spo2", "while": "flag sedated set", "note": "Teaching choice."},
]
SED_TIMED = [{"flag": "sedated", "duration_seconds": 150, "lapse_note": "He's waking up a bit."}]
SED_NOTE = (
  "He was not agitated. He had no tremor, no sweating and no hallucinations, so there was "
  "no withdrawal to treat, and nothing else to sedate for.\n\n"
  "His breathing was the only thing defending his pH. With a bicarbonate of 5 to 7, losing "
  "even a few breaths a minute drops the pH below 7.0. Intoxicated patients with a severe "
  "metabolic acidosis are sedated or intubated at the moment they lose that defense." + MEMORY)
SED_HALT = ("A sedative took away the fast breathing that was holding his pH up. With a "
            "bicarbonate this low, his pH fell below 7.0 and he stopped protecting himself.")

for cid in ("lorazepam_bolus", "morphine_bolus", "diphenhydramine"):
    act(cid,
        [{"when": NOT_IMPROVED, "value": "harmful"}, {"when": None, "value": "discouraged"}],
        flags_set_timed=SED_TIMED, vital_effects=SED_EFFECTS,
        halt_reason=SED_HALT,
        debrief_note=SED_NOTE + (
          "\n\nIn this case, before both the antidote and bicarbonate were in, it ended the "
          "case (owner, 11 November 2026). After them, the effect was a few minutes of "
          "worse gas and drowsiness."))

# Ungraded by the catalog rule (intubation care, owner 23 October 2026): neutral wherever
# they are given. Their effects still play.
for cid in ("midazolam_bolus", "propofol_bolus", "fentanyl_bolus"):
    act(cid, ALWAYS("neutral"),
        flags_set_timed=SED_TIMED, vital_effects=SED_EFFECTS,
        debrief_note=SED_NOTE + (
          "\n\nThis drug is on the catalog's list of intubation drugs, which is never graded, "
          "so the case cannot score it. It still took his breathing down for a few minutes."))

for cid in ("haloperidol", "olanzapine", "ziprasidone"):
    act(cid, ALWAYS("discouraged"),
        debrief_note=(
          "He was cooperative and not agitated, so there was nothing to treat. Antipsychotics "
          "depress breathing less than benzodiazepines, so the case shows no effect, and the "
          "indication still was not there." + MEMORY))

act("intubate_rapid_sequence", ALWAYS("neutral"),
    prerequisite_overrides=[{"waived": "flag sedation_given set AND flag paralytic_given set"}],
    # The block waits on a flag only a hidden, buttonless case action sets, so a learner can
    # never meet it and the engine suite's airway-device check can still induce it.
    prerequisites=[{"when": "flag intubation_approved set",
                    "failure_message": ("Attending's asking what the indication is. He's "
                                        "talking and his sat is fine, and the vent won't "
                                        "breathe as fast as he does.")}],
    debrief_note=(
      "Blocked in this case (owner, 11 November 2026). He was awake, protecting his airway "
      "and saturating 99 percent. His fast breathing was holding his pH up. On standard "
      "ventilator settings his pCO2 would rise and his pH would fall, and peri-intubation "
      "arrest is a known risk in severe metabolic acidosis. If he ever needs a tube, the "
      "ventilator has to match the minute ventilation he was generating himself." + MEMORY))

# =====================================================================  PEOPLE

RENAL_PREREQS = [
  {"when": GAS_R + " AND study basic_chemistry_chem_7 resulted",
   "failure_message": "Renal wants to see his gas and his chemistry first."},
  {"when": "study osmolality resulted OR action interview_topic_alcohol taken OR action interview_topic_vision taken",
   "failure_message": "Renal's asking why we think he needs dialysis. What do we know about what he drank?"},
]

act("consult_renal", ALWAYS("critical"),
    expectation_label="Nephrology for emergent dialysis",
    flags_set=["renal_called"], state_changing=True,
    prerequisites=RENAL_PREREQS,
    prompt={"deadline_seconds": 150,
            "guard": "(" + HELD + " OR " + IMP + ") AND " + GAS_R,
            "text": "ICU is asking what the plan is for the acid that's still there."},
    voice_phrases=["nephrology", "call nephrology", "consult nephrology", "dialysis", "call renal for dialysis"],
    debrief_note=(
      "Dialysis removes the formate and the methanol, and corrects the acidosis. It is the "
      "only treatment here that does.\n\n"
      "The consensus indications attributed to methanol: coma, seizures, new vision "
      "deficits, a pH of 7.15 or lower, persistent acidosis despite supportive care and the "
      "antidote, or an anion gap above 24. When no level is available the osmolar gap is "
      "informative. He met two on arrival (the gap and his vision) and the pH criterion as "
      "soon as he drifted. None of them needs a level.\n\n"
      "Tell nephrology that fomepizole is dosed every four hours during dialysis, because "
      "dialysis removes it." + EXTRIP + LABEL))

act("consult_toxicology", ALWAYS("critical"),
    display_name="Consult Toxicology (poison center)",
    expectation_label="Poison center or toxicology",
    flags_set=["poison_center_called"], state_changing=True,
    voice_phrases=["poison control", "poison center", "call poison control", "call the poison center"],
    debrief_note=(
      "The poison center is free, available all hours, and has seen this before. It also "
      "tells you what to send and what to start, which is why it is critical here (owner, "
      "11 November 2026). Calling early is not a weakness."))

act("consult_critical_care", ALWAYS("recommended"),
    flags_set=["icu_called"], state_changing=True,
    debrief_note="He needs the ICU: emergent dialysis, a bicarbonate infusion, gases every few hours and fomepizole every four hours on dialysis.")

act("consult_psychiatry", ALWAYS("neutral"), state_changing=False,
    debrief_note=(
      "He denied trying to hurt himself. Psychiatry is not part of the emergency plan, and "
      "the inpatient team can involve them once he is medically safe."))

# =====================================================================  HISTORY TARGETS

act("interview_topic_alcohol", ALWAYS("recommended"),
    display_name="Asked what he drank",
    debrief_note=(
      "The fastest route to suspicion. 'The blue stuff', followed by one more question, "
      "was windshield washer fluid, which is usually methanol."))

act("interview_topic_vision",
    [{"when": UNTREATED, "value": "critical"}, {"when": None, "value": "recommended"}],
    display_name="Asked about or examined his vision",
    expectation_label="Vision asked about or examined",
    prompt={"deadline_seconds": 55, "guard": U0 + " OR " + U1,
            "text": "He keeps squinting and rubbing his eyes. Is that something?"},
    debrief_note=(
      "Methanol inebriates. Formate injures, and the optic nerve is where it shows first. "
      "Intoxicated patients rarely volunteer that everything looks blurry and white. His "
      "vision was a clue to the diagnosis and, as a new deficit, an indication for dialysis "
      "by itself." + EXTRIP))

act("interview_topic_intent", ALWAYS("recommended"),
    display_name="Asked whether he meant to hurt himself",
    debrief_note=(
      "Washer fluid can be a substitute for alcohol or an attempt at self-harm. Ask. His "
      "answer was no, and it changes the inpatient plan, not the emergency one."))

# =====================================================================  DISPOSITION AND HIDDEN TARGETS

act("attempt_discharge", ALWAYS("discouraged"),
    display_name="Discharge home",
    hidden=True,
    flags_set=["discharge_attempted"],
    narration_override="You want him to go? He can't walk straight. All right, I'll get him up.",
    debrief_note=(
      "He was sent out with a severe acidosis and formate still in him, and he came back "
      "unresponsive (owner, 11 November 2026). Before discharging an intoxicated patient, "
      "the numbers have to fit the story. His respiratory rate and his ethanol did not."))

act("attempt_observation", ALWAYS("discouraged"),
    display_name="Observation, let him sleep it off",
    hidden=True,
    flags_set=["observation_attempted"],
    also_satisfies=[{"id": "away_from_u0", "when": U0}, {"id": "away_from_u1", "when": U1}],
    narration_override="Okay. I'll put him in the hallway to sleep it off.",
    nurse_alert=[{"when": U2, "value": "I'll keep him close. He's working to breathe and I don't love it."},
                 {"when": None, "value": "I'll check on him in a bit."}],
    debrief_note=(
      "Sending him to sleep it off is the plan the triage note hands you. It was the plan "
      "the numbers did not support. While he was in the hallway, untreated, formate kept "
      "being made."))

act("attending_approves_intubation", ALWAYS("neutral"),
    hidden=True, display_name="Attending approves intubation",
    flags_set=["intubation_approved"],
    debrief_note=("Not an order and not a button. It exists only so the intubation block is "
                  "a prerequisite the engine suite can satisfy. A learner never sees it."))

act("away_from_u0", ALWAYS("neutral"),
    hidden=True, display_name="Away from the bedside before the antidote (arrival tier)",
    debrief_note="Not an order. Credited when a CT head or the hallway is chosen in the arrival phase. A learner never sees it.")

act("away_from_u1", ALWAYS("neutral"),
    hidden=True, display_name="Away from the bedside before the antidote (second tier)",
    debrief_note="Not an order. Credited when a CT head or the hallway is chosen in the second phase. A learner never sees it.")

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
EXAM_NOTES = {
  "exam_airway": "He is protecting his airway throughout.",
  "exam_breath": (
    "Deep, fast, regular breathing with clear lungs is the body blowing off acid. In a "
    "drunk man it is easy to miss, and it was the first clue."),
  "exam_circ": "Warm and well perfused. His problem is not his circulation.",
  "exam_heent": (
    "The eye exam is where methanol shows: reduced acuity, sluggish pupils and hyperemic "
    "optic discs. It also counts as asking about his vision."),
  "exam_pulm": "Clear. His breathing is not from his lungs.",
  "exam_abd": "Mild epigastric tenderness, common with methanol and with drinking. No peritonitis.",
  "exam_skin": "No trauma, no sweating. The sweating would have pointed toward withdrawal.",
  "exam_neuro": (
    "Slurred, unsteady, drowsy, no focal signs, no tremor, no nystagmus. No tremor argues "
    "against withdrawal. No nystagmus argues against Wernicke and does not exclude it."),
  "exam_psych": "Cooperative and not agitated, which means there was nothing to sedate.",
}
# Owner, 11 November 2026: a man with an unclear cause of delirium, found outside, needs a
# trauma survey. Head (HEENT), neurological and abdominal exams are critical in every live
# phase. The breathing and lung exams are recommended so the Physical score still reads them.
TRAUMA = ("\n\nPart of the trauma survey (owner, 11 November 2026). An intoxicated man found "
          "outside with an unclear cause of his confusion is examined for injury: head and "
          "scalp, a neurological exam for focal signs, and the abdomen. His were normal, which "
          "is what lets the toxic explanation stand.")
TAGS = {"exam_heent": "critical", "exam_neuro": "critical", "exam_abd": "critical",
        "exam_breath": "recommended", "exam_pulm": "recommended"}
for cid, note in EXAM_NOTES.items():
    kw = {}
    if cid == "exam_heent":
        kw["also_satisfies"] = [{"id": "interview_topic_vision", "when": None}]
    if cid in ("exam_heent", "exam_neuro", "exam_abd"):
        kw["expectation_label"] = {"exam_heent": "Head exam (trauma survey) and eyes",
                                   "exam_neuro": "Neurological exam (trauma survey)",
                                   "exam_abd": "Abdominal exam (trauma survey)"}[cid]
        note = note + TRAUMA
    act(cid, ALWAYS(TAGS.get(cid, "neutral")), debrief_note=note + MEMORY, **kw)

FOLLOW_UPS = [
 {"id": "repeat_gas_after_bicarbonate",
  "triggered_by": ["na_bicarbonate_bolus", "na_bicarbonate_infusion"],
  "applies_when": "flag bicarb_acting set OR " + IMP,
  "deadline_seconds": 60,
  # A hidden target credited by a gas sent while bicarbonate acts or once improving
  # (authoring 22.2), so a gas sent before the bicarbonate does not discharge it.
  "satisfied_by": ["gas_repeated"],
  "nurse_prompt": "The bicarb's going in. Do you want a repeat gas to see what it did?",
  "debrief_note": (
    "A repeat gas is how you see what a treatment did. After bicarbonate alone it looks "
    "better for a few minutes. With fomepizole on board it stays better. In both, the anion "
    "gap barely moves. Owner's structure lists the repeat gas as a bonus action.")},
]
