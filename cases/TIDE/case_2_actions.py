"""TIDE part 2: the action spine, tags, flags, prompts and vital effects.

Nothing is harmful and nothing halts the case. Every clinical judgment here is model output
awaiting a physician's signature, except the decisions in TIDE-SEED.md section 0.

Markers go only in fields the interface strips (authoring 10.3): an action's debrief_note.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

P1 = "phase is presentation"
P2 = "phase is fluid_response"
P3 = "phase is low_pressure"
P4 = "phase is low_after_fluid"
P5 = "phase is worsening_shock"
P6 = "phase is on_pressor"
P7 = "phase is failing_support"
P8 = "phase is tiring"
P9 = "phase is post_induction_collapse"
P10 = "phase is ventilated"
PRE_TUBE = " OR ".join([P1, P2, P3, P4, P5, P6])
SHOCK_LOW = " OR ".join([P4, P5, P9])
ON_DRIP = " OR ".join([P6, P7, P8, P9, P10])
INTUB = "flag intubated set"
DRIP = "flag pressor_running set"

SSC = " [UNVERIFIED: SSC 2026, read through the SCCM page and summaries, not opened]"
ATS19 = " [UNVERIFIED: IDSA/ATS 2019 CAP guideline, from memory]"
ATS25 = " [UNVERIFIED: ATS CAP guideline update 2025, read through summaries, not opened]"
ACEP = " [UNVERIFIED: ACEP clinical policy on endotracheal intubation, read through its web page]"
MEMORY = " [UNVERIFIED: general teaching written by a model from memory, no source opened]"
OWNER = " [From the owner's case structure, 4 November 2026. Its sources were not opened by the model]"

# =====================================================================  LOOK AND CONNECT

act("attach_monitor",
    [{"when": P1, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["monitor_on"],
    debrief_note=(
      "Nothing shows until the monitor is on, and this man's numbers are about to move. Not "
      "prompted: a dark monitor in a breathless patient is its own prompt."))

act("insert_iv", ALWAYS("recommended"),
    debrief_note="Fluid, the antibiotic and a vasopressor all need a line. A peripheral line is enough for norepinephrine to start.")

for cid in ("second_iv", "intraosseous_line"):
    act(cid, ALWAYS("neutral"),
        debrief_note="Counts as access. A second line is useful once fluid, an antibiotic and a drip are all running. Not scored.")

for cid in ("central_venous_catheter_triple_lumen", "central_venous_catheter_cordis"):
    act(cid, ALWAYS("neutral"),
        debrief_note=(
          "A central line is reasonable in a man who will need a vasopressor for hours. It "
          "should not delay the vasopressor: a peripheral line in a good vein is enough to "
          "start norepinephrine." + SSC))

act("arterial_line", ALWAYS("neutral"),
    debrief_note="Useful on a vasopressor and on the ventilator. Not needed to make any decision here. Not scored.")

# =====================================================================  OXYGEN

RESP_GUARD = "NOT " + INTUB + " AND NOT " + P8


def resp_effects(spo2, rr, note):
    return [
      {"vital": "oxygen_saturation", "delta": spo2, "key": "resp_spo2", "while": RESP_GUARD,
       "note": note},
      {"vital": "respiratory_rate", "delta": rr, "key": "resp_rr", "while": RESP_GUARD,
       "note": note + " A delta of 0 replaces an earlier device's rate effect under the same key."}]


DEVICE_NOTE = ("Teaching choice. Every non-terminal phase's saturation is authored on room air. "
               "One key per vital, so the last device applied is the one shown. Switched off in "
               "the tiring phase and after intubation.")

act("hidden_oxygen", [{"when": P1, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Oxygen started",
    expectation_label="Oxygen, any device",
    prompt={"deadline_seconds": 20, "guard": P1,
            "text": "He's working really hard to breathe and his lips look dusky. Should we do something?"},
    debrief_note=(
      "Not an order. Credited by any oxygen device. On arrival he was at 85 percent on room "
      "air, breathing 32 times a minute in three or four words a breath."))

act("hidden_support",
    [{"when": PRE_TUBE, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="High-flow oxygen or NIV",
    expectation_label="High-flow oxygen or NIV",
    prompt={"deadline_seconds": 45, "guard": P1 + " OR " + P2 + " OR " + P3 + " OR " + P4
                                              + " OR " + P5 + " OR " + P6,
            "text": "He's still working hard to breathe. Do you want more support for him?"},
    debrief_note=(
      "Not an order. Credited by high-flow nasal oxygen or NIV.\n\n"
      "A cannula left him at 88 percent and a mask at about 91, still breathing near 30. "
      "Severe hypoxemia in pneumonia, with a respiratory rate over 30, is what high flow is "
      "for. In nonimmunocompromised hypoxemic patients, high flow was noninferior to NIV for "
      "intubation or death at seven days in RENOVATE, and it is better tolerated. NIV is "
      "reasonable while he is alert and not vomiting. Either counts here."
      " [UNVERIFIED: Maia et al., RENOVATE, JAMA 2025, read through summaries]"))

act("nasal_cannula_oxygen", ALWAYS("neutral"),
    flags_set=["o2_nc"],
    also_satisfies=[{"id": "hidden_oxygen", "when": None}],
    vital_effects=resp_effects(3, 0, DEVICE_NOTE),
    nurse_alert="Six liters by nasal cannula is on.",
    debrief_note=(
      "A start. His saturation came up to about 88 and stopped there, and he was still "
      "breathing at 32. Low-flow oxygen does not meet this demand." + MEMORY))

act("non_rebreather_mask", ALWAYS("neutral"),
    flags_set=["o2_nrb"],
    also_satisfies=[{"id": "hidden_oxygen", "when": None}],
    vital_effects=resp_effects(6, -2, DEVICE_NOTE),
    nurse_alert="Nonrebreather is on at fifteen liters.",
    debrief_note=(
      "Reasonable as a bridge. His saturation reached about 91 at a rate near 30. The FiO2 a "
      "nonrebreather delivers falls when a patient breathes this fast, and it does nothing "
      "for the work of breathing. High flow or NIV was the next step." + MEMORY))

act("high_flow_nasal_cannula",
    [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
    flags_set=["o2_hfnc"],
    also_satisfies=[{"id": "hidden_oxygen", "when": None}, {"id": "hidden_support", "when": None}],
    vital_effects=resp_effects(7, -2, DEVICE_NOTE),
    nurse_alert=[
      {"when": P7 + " OR " + P8, "value": "High flow is on, sixty liters at a hundred percent."},
      {"when": None, "value": "High flow is on, sixty liters at sixty percent."}],
    debrief_note=(
      "The right first support. On arrival at sixty percent his saturation came to 92 at a "
      "rate of 30: a ROX index of about 5.1, which is reassuring at the two-hour mark. "
      "ROX is the saturation over the FiO2, divided by the respiratory rate. Once he was "
      "failing, at a hundred percent, 88 and 38 gave a ROX of about 2.3. The number to watch "
      "is the trend, with the work of breathing and the mental state beside it. ROX was "
      "validated at two, six and twelve hours and its accuracy is moderate. "
      "[UNVERIFIED: Roca et al., AJRCCM 2019, from memory and the owner's structure]"))

act("non_invasive_positive_pressure_ventilation",
    [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
    flags_set=["o2_niv"],
    flags_set_if=[{"flag": "preox_pp", "when": P7 + " OR " + P8}],
    also_satisfies=[{"id": "hidden_oxygen", "when": None}, {"id": "hidden_support", "when": None}],
    vital_effects=resp_effects(8, -4, DEVICE_NOTE),
    nurse_alert=[
      {"when": P7 + " OR " + P8, "value": "BiPAP is on. He's fighting the mask a bit, but it's sealing."},
      {"when": None, "value": "BiPAP is on."}],
    debrief_note=(
      "Two uses here. Before he failed, NIV was a fair alternative to high flow while he was "
      "alert and not vomiting. Once he was confused and failing, it was not a treatment to "
      "continue, because it does not reverse his failure and a confused patient may vomit "
      "into a tight mask. As a few minutes of preoxygenation before the tube it is the best "
      "choice: in PREOXI, NIV preoxygenation roughly halved hypoxemia during intubation "
      "compared with an oxygen mask. In phase 7 it did not stop his clock."
      " [UNVERIFIED: Gibbs et al., PREOXI, NEJM 2024. The percentages are the owner's "
      "structure's and were not checked]" + ACEP))

act("bag_valve_mask", ALWAYS("neutral"),
    flags_set_if=[{"flag": "preox_pp", "when": P7 + " OR " + P8}],
    debrief_note=(
      "Bag-mask ventilation with a PEEP valve counts as positive-pressure preoxygenation in "
      "this case. It is intubation care and is not scored."))

act("preoxygenate_for_intubation", ALWAYS("neutral"),
    flags_set_if=[{"flag": "preox_pp", "when": "flag o2_niv set"}],
    nurse_alert=[
      {"when": "flag o2_niv set", "value": "Preoxygenating on the BiPAP."},
      {"when": "flag o2_hfnc set", "value": "Preoxygenating on the high flow at a hundred percent."},
      {"when": None, "value": "Preoxygenating on a nonrebreather."}],
    debrief_note=(
      "How he was preoxygenated decided how low he went during the attempt. NIV, or a bag "
      "with a PEEP valve, gives the most reserve. High flow at a hundred percent is the "
      "fallback when NIV is not feasible. A nonrebreather gives the least. Intubation care, "
      "not scored." + ACEP))

# =====================================================================  INTUBATION

INTUB_TAG = [{"when": P7 + " OR " + P8, "value": "critical"}, {"when": None, "value": "neutral"}]
act("intubate_rapid_sequence", INTUB_TAG,
    expectation_label="Decision to intubate",
    flags_set=["intubated"],   # restates the catalog default so the validator's warning rule sees it (authoring 15.2)
    prompt={"deadline_seconds": 30, "guard": P7 + " OR " + P8,
            "text": "He's barely responding and his breathing doesn't look right. Are we okay with what he's on?"},
    nurse_alert=[
      {"when": "NOT " + DRIP,
       "value": ("Tube's in, first pass. His pressure is falling fast, and nothing is running for "
                 "it. That was the risk we took.")},
      {"when": "flag preox_pp set",
       "value": "Tube's in, first pass. Lowest sat was ninety-one on the way down."},
      {"when": "flag o2_hfnc set",
       "value": "Tube's in. His sats dipped to the mid-eighties while we were tubing. They're coming back up."},
      {"when": None,
       "value": ("Tube's in. His sats dropped into the seventies while we were tubing. They're coming "
                 "back up on the vent. That's the risk with a mask.")}],
    vital_effects=[
      {"vital": "oxygen_saturation", "delta": -3, "key": "tube_spo2", "duration_seconds": 30,
       "while": "flag preox_pp set",
       "note": "Teaching choice. Nadir about 91 with positive-pressure preoxygenation."},
      {"vital": "oxygen_saturation", "delta": -10, "key": "tube_spo2", "duration_seconds": 30,
       "while": "flag o2_hfnc set AND NOT flag preox_pp set",
       "note": "Teaching choice. Nadir in the mid-eighties after high-flow preoxygenation."},
      {"vital": "oxygen_saturation", "delta": -18, "key": "tube_spo2", "duration_seconds": 30,
       "while": "NOT flag o2_hfnc set AND NOT flag preox_pp set",
       "note": "Teaching choice. Nadir in the seventies after mask preoxygenation."},
      {"vital": "systolic_bp", "delta": -14, "key": "tube_sbp", "duration_seconds": 60,
       "while": DRIP, "note": "Teaching choice. A dip that the drip carries him through."},
      {"vital": "diastolic_bp", "delta": -8, "key": "tube_dbp", "duration_seconds": 60,
       "while": DRIP, "note": "As above."}],
    follow_ups_triggered=["sedation_after_the_tube"],
    debrief_note=(
      "The decision this case is built around. In phase 7 he was at 88 percent on a hundred "
      "percent, breathing near 40, confused, with paradoxical breathing and a rising pCO2. "
      "The saturation was the least worrying number in the room. That is failure of "
      "noninvasive support, and the tube goes in before he tires further.\n\n"
      "How it went depended on what was in place first. With a vasopressor running, his "
      "pressure dipped and recovered. Without one, induction and positive pressure took away "
      "the tone he was living on and his pressure fell. Post-intubation hypotension happens "
      "in a large share of emergency intubations and is predictable in septic shock. The case "
      "makes it certain to show the risk. Preoxygenation with positive pressure set how far "
      "his saturation fell.\n\n"
      "Choosing the tube earlier, while his pressure was held, is also defensible in severe "
      "pneumonia with shock. Waiting for him to tire is not."
      + OWNER + ACEP))

for cid in ("etomidate_bolus", "ketamine_bolus", "propofol_bolus", "midazolam_bolus",
            "rocuronium_bolus", "succinylcholine_bolus", "position_for_intubation",
            "prepare_endotracheal_tube", "suction"):
    act(cid, ALWAYS("neutral"),
        debrief_note=(
          "Intubation care, not scored. In septic shock, ACEP advises against propofol, "
          "midazolam or fentanyl as the induction agent when post-intubation hypotension is "
          "likely. Doses are not modeled." + ACEP))

act("hidden_sedation", ALWAYS("neutral"),
    hidden=True, ungraded=True, display_name="Sedation after the tube",
    debrief_note=(
      "Not an order. Credited by a sedative or an analgesic given after the tube. Intubation "
      "care, not scored."))

SED_NOTE = (
  "After rocuronium he cannot move for most of an hour and cannot show distress. Analgesia "
  "first, then sedation, started as soon as the tube is confirmed. In ED-AWARENESS, 2.6 "
  "percent of ventilated patients had awareness with paralysis, all after a longer-acting "
  "paralytic, and a multicenter cohort found 3.4 percent. Rising heart rate and blood "
  "pressure are unreliable signs, and their absence does not mean he is comfortable. "
  "Intubation care, not scored."
  " [UNVERIFIED: Pappal et al., Ann Emerg Med 2021, and Fuller et al., Crit Care Med 2022, "
  "read through summaries]")
act("fentanyl_bolus", ALWAYS("neutral"),
    also_satisfies=[{"id": "hidden_sedation", "when": INTUB}],
    debrief_note=SED_NOTE + " Fentanyl first is gentler on a pressure that is already supported.")
act("propofol_infusion", ALWAYS("neutral"),
    also_satisfies=[{"id": "hidden_sedation", "when": INTUB}],
    vital_effects=[
      {"vital": "systolic_bp", "delta": -8, "key": "propofol_sbp", "while": "NOT action stop_propofol taken",
       "note": "Teaching choice. Propofol lowers the pressure of a man on a vasopressor."},
      {"vital": "diastolic_bp", "delta": -4, "key": "propofol_dbp", "while": "NOT action stop_propofol taken",
       "note": "As above."}],
    debrief_note=SED_NOTE + " Propofol lowered his pressure a little. Expect to turn the vasopressor up.")
act("stop_propofol", ALWAYS("neutral"), debrief_note="Not scored.")
for cid in ("ketamine_infusion", "morphine_bolus", "lorazepam_bolus"):
    act(cid, ALWAYS("neutral"),
        also_satisfies=[{"id": "hidden_sedation", "when": INTUB}],
        debrief_note=SED_NOTE)

act("place_orogastric_tube", ALWAYS("neutral"),
    debrief_note="Decompresses the stomach after bag and NIV ventilation. Part of settling him on the ventilator. Not scored.")

# =====================================================================  CIRCULATION

FLUID_NOTE = (
  "Fluid is a drug here, and its effect wore off. On arrival his MAP was 75 and his lactate "
  "3.8, just under the guideline's threshold for hypoperfusion, but he was hot, fast, with a "
  "small collapsing vena cava, and his pressure fell within minutes. A first liter lifted it "
  "for a few minutes and it drifted back. The 2026 Surviving Sepsis guideline suggests at "
  "least 30 mL/kg in the first three hours for hypoperfusion or shock, with low certainty, "
  "about 2.8 liters for him, and frequent reassessment. When fluid stops holding the "
  "pressure, the next step is a vasopressor. Beyond two boluses, with a P/F near 117 and "
  "B-lines, more fluid went to his lungs." + SSC)
act("normal_saline_1l_bolus",
    [{"when": "flag fluid_twice set", "value": "discouraged"},
     {"when": P1 + " OR " + P3, "value": "critical"},
     {"when": P2, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Crystalloid bolus",
    flags_set=["fluid_given"],
    flags_set_repeat=[
      # Two named counters on purpose: the engine adds one to a counter for every entry in this
      # list, so two entries sharing the default counter would count each bolus twice (engine
      # note in the handoff, 4 November 2026). Named counters are shared by covered siblings.
      {"flag": "fluid_twice", "after_administrations": 2, "counter": "crystalloid_two"},
      {"flag": "fluid_stacked", "after_administrations": 3, "counter": "crystalloid_three"}],
    vital_effects=[
      {"vital": "oxygen_saturation", "delta": -3, "key": "fluid_spo2",
       "while": "flag fluid_stacked set AND NOT " + INTUB + " AND NOT " + P8,
       "note": "Teaching choice. More fluid in leaky lungs. Starts with the third bolus."},
      {"vital": "respiratory_rate", "delta": 4, "key": "fluid_rr",
       "while": "flag fluid_stacked set AND NOT " + INTUB + " AND NOT " + P8,
       "note": "As above."}],
    prompt={"deadline_seconds": 40, "guard": "NOT flag fluid_given set",
            "text": "He's hot and his heart's racing. What do you want to give him?",
            "escalation": {"deadline_seconds": 70,
                           "text": "Nothing's running for his pressure yet. Do you want something hung?"}},
    debrief_note=FLUID_NOTE)

for cid in ("normal_saline_infusion", "lactated_ringer_s_infusion"):
    act(cid, ALWAYS("neutral"),
        debrief_note=(
          "A maintenance rate is not resuscitation. In the case it does not move his pressure. "
          "A bolus does. Not scored." + MEMORY))
for cid in ("d5_ns_bolus", "d5_1_2_ns_infusion"):
    act(cid, ALWAYS("neutral"),
        debrief_note="Dextrose-containing fluid is not resuscitation fluid, and his glucose is 244. Not scored.")

act("hidden_reassessed",
    [{"when": P2 + " OR " + P4 + " OR " + P6, "value": "recommended"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Reassessed after fluid",
    expectation_label="Reassessment after fluid",
    debrief_note=(
      "Not an order. Credited by a circulation exam, a cardiac or lung ultrasound, or a "
      "lactate sent after fluid. Dynamic measures such as ultrasound or a passive leg raise "
      "are suggested over static ones. A passive leg raise is not in the simulator." + SSC))

PRESSOR_NOTE = (
  "Norepinephrine is the first vasopressor, and a peripheral line is enough to start it. "
  "The target is a MAP of 65. Practice has moved toward smaller fluid volumes and earlier "
  "vasopressors. His pressure drifted back after fluid, and that was the moment. Once his "
  "pressure was held, intubation could be survived. Without a vasopressor, his shock "
  "progressed to arrest, and an intubation without one collapsed him."
  + SSC + " [UNVERIFIED: Munroe et al., AJRCCM 2023, from the owner's structure]")
LATE = [{"flag": "pressor_restarted", "when": "flag pressor_stopped set"}]
act("norepinephrine_drip",
    [{"when": SHOCK_LOW, "value": "critical"}, {"when": P3, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Vasopressor drip",
    flags_set=["pressor_running"], flags_set_if=LATE,
    vital_effects=[],
    no_vital_effect_note="The phases it moves to carry the rise. Authoring 16, pressors have a default.",
    prompt={"deadline_seconds": 30, "guard": SHOCK_LOW + " OR " + P9,
            "text": "His pressure is still low and nothing's running for it. Should we do something?",
            "escalation": {"deadline_seconds": 45,
                           "text": "He's not holding a pressure. Do you want a pressor started?"}},
    debrief_note=PRESSOR_NOTE)

for cid, note in (
  ("vasopressin_drip", "Vasopressin is the usual second agent once norepinephrine is running. Accepted here as the vasopressor."),
  ("epinephrine_drip", "Epinephrine is a second-line vasopressor in septic shock. Accepted here as the vasopressor."),
  ("phenylephrine_drip", "Phenylephrine raises the pressure without much help for the heart. Not first line in septic shock. Accepted here as the vasopressor."),
):
    act(cid, ALWAYS("neutral"),
        flags_set=["pressor_running"], flags_set_if=LATE,
        also_satisfies=[{"id": "norepinephrine_drip", "when": None}],
        vital_effects=[],
        debrief_note=note + " " + PRESSOR_NOTE)

act("dopamine_drip", ALWAYS("discouraged"),
    flags_set=["pressor_running"], flags_set_if=LATE,
    also_satisfies=[{"id": "norepinephrine_drip", "when": None}],
    vital_effects=[],
    debrief_note=(
      "Dopamine held his pressure here. In septic shock it causes more arrhythmias than "
      "norepinephrine and is not recommended as the first vasopressor." + SSC))

STOP_FX = [
  {"vital": "systolic_bp", "delta": -24, "key": "stop_sbp",
   "while": DRIP + " AND NOT flag pressor_restarted set",
   "note": "Teaching choice. Display only: stopping the drip drops the monitor, and no phase changes (known gap 5)."},
  {"vital": "diastolic_bp", "delta": -14, "key": "stop_dbp",
   "while": DRIP + " AND NOT flag pressor_restarted set", "note": "As above."}]
for cid in ("stop_norepinephrine", "stop_vasopressin", "stop_epinephrine", "stop_phenylephrine",
            "stop_dopamine"):
    act(cid, [{"when": DRIP, "value": "discouraged"}, {"when": None, "value": "neutral"}],
        flags_set=["pressor_stopped"], vital_effects=STOP_FX,
        nurse_alert=[{"when": DRIP, "value": "It's off. His pressure's dropping."},
                     {"when": None, "value": "There's nothing running to stop."}],
        debrief_note=(
          "His pressure depended on the drip. Stopping it dropped the pressure, and restarting "
          "it brought it back. The simulator shows this on the monitor and moves no phase."))

act("hidden_push_dose", [{"when": P9, "value": "recommended"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Push-dose vasopressor",
    expectation_label="Push-dose vasopressor as a bridge",
    debrief_note=(
      "Not an order. Credited by a push-dose epinephrine, phenylephrine or vasopressin bolus. "
      "It bridges the minutes until a drip runs. It does not replace the drip." + MEMORY))
for cid in ("epinephrine_bolus", "phenylephrine_bolus", "vasopressin_bolus"):
    act(cid, ALWAYS("neutral"),
        also_satisfies=[{"id": "hidden_push_dose", "when": None}],
        debrief_note=(
          "A push-dose bolus lifts the pressure for a few minutes. After the tube it is a "
          "bridge to a drip. It moves no phase in the simulator." + MEMORY))

STEROID_NOTE = (
  "Corticosteroids are now suggested in two ways that both fit him. The 2025 ATS update "
  "suggests systemic corticosteroids for inpatients with severe CAP, a conditional "
  "recommendation on low-quality evidence, not for influenza pneumonia, and IDSA did not "
  "endorse it. The 2026 Surviving Sepsis guideline suggests IV corticosteroids in septic "
  "shock. In CAPE COD, hydrocortisone lowered 28-day mortality in severe CAP in the ICU, "
  "6.2 against 11.9 percent, in a trial that by its summaries excluded septic shock. His "
  "influenza test is negative. Expect a higher glucose. Nothing changes in the case's "
  "minutes."
  + ATS25 + SSC + " [UNVERIFIED: Dequin et al., NEJM 2023, PubMed abstract and a summary]")
act("hydrocortisone_bolus",
    [{"when": ON_DRIP, "value": "recommended"}, {"when": None, "value": "neutral"}],
    expectation_label="Corticosteroid",
    debrief_note=STEROID_NOTE)
act("methylprednisolone_bolus", ALWAYS("neutral"),
    also_satisfies=[{"id": "hydrocortisone_bolus", "when": None}],
    debrief_note="Accepted as the corticosteroid. Trials in severe CAP used hydrocortisone and methylprednisolone. " + STEROID_NOTE)
act("dexamethasone", ALWAYS("neutral"),
    debrief_note="Not the agent the septic shock and severe CAP trials used. Not scored." + MEMORY)

# =====================================================================  INFECTION

ABX_NOTE = (
  "Severe CAP with no risk factor for MRSA or Pseudomonas: no hospital stay or IV "
  "antibiotics in 90 days and no prior isolate. The recommended regimen is a beta-lactam, "
  "such as ceftriaxone, with a macrolide, or a beta-lactam with a respiratory "
  "fluoroquinolone. A fluoroquinolone alone is a regimen for non-severe pneumonia. In shock, "
  "antibiotics go in within the first hour of recognition. In the simulator the antibiotic "
  "changes nothing you can see, because an antibiotic does not change a pressure in "
  "minutes. It is scored."
  + ATS19 + SSC)
act("hidden_beta_lactam",
    [{"when": PRE_TUBE + " OR " + P7 + " OR " + P10, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Beta-lactam with pneumococcal activity",
    expectation_label="Antibiotic: a beta-lactam",
    prompt={"deadline_seconds": 50, "guard": PRE_TUBE + " OR " + P7,
            "text": "He's had a fever for four days and nothing's running for it yet. Anything you want to start?"},
    debrief_note="Not an order. Credited by ceftriaxone, cefotaxime or a broader beta-lactam. " + ABX_NOTE)
act("hidden_atypical",
    [{"when": PRE_TUBE + " OR " + P7 + " OR " + P10, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Atypical cover",
    expectation_label="Antibiotic: atypical cover",
    debrief_note="Not an order. Credited by azithromycin, levofloxacin or moxifloxacin. " + ABX_NOTE)

for cid in ("ceftriaxone", "cefotaxime", "ampicillin"):
    act(cid, ALWAYS("neutral"), flags_set=["abx_given"],
        also_satisfies=[{"id": "hidden_beta_lactam", "when": None}],
        debrief_note=ABX_NOTE)
act("azithromycin", ALWAYS("neutral"), flags_set=["abx_given"],
    also_satisfies=[{"id": "hidden_atypical", "when": None}],
    debrief_note=ABX_NOTE + " Azithromycin alone does not cover him: pneumococcal macrolide resistance is common." + MEMORY)
for cid in ("levofloxacin", "moxifloxacin"):
    act(cid, ALWAYS("neutral"), flags_set=["abx_given"],
        also_satisfies=[{"id": "hidden_atypical", "when": None}],
        debrief_note=ABX_NOTE + " Alone, it covers his organism, and severe CAP still gets a beta-lactam with it.")
for cid in ("piperacillin_tazobactam", "cefepime", "meropenem"):
    act(cid, ALWAYS("neutral"), flags_set=["abx_given"],
        also_satisfies=[{"id": "hidden_beta_lactam", "when": None}],
        debrief_note=(
          "Covers him, and more than he needs. Without risk factors, antipseudomonal cover "
          "is reserved for prior isolation or recent hospital antibiotics. Some clinicians add "
          "it for shock or ventilation while cultures are pending, and sources differ. "
          "Counted as the beta-lactam. " + ABX_NOTE
          + " [UNVERIFIED: File and Ramirez, NEJM 2023, from the owner's structure]"))
act("vancomycin", ALWAYS("neutral"), flags_set=["abx_given"],
    debrief_note=(
      "MRSA cover without a risk factor. A negative MRSA nares PCR lets it come off early. "
      "It does not replace the beta-lactam. Not scored." + ATS19))
for cid in ("doxycycline", "clindamycin", "metronidazole", "cefazolin", "oseltamivir"):
    act(cid, ALWAYS("neutral"),
        debrief_note={
          "doxycycline": "Doxycycline is an atypical agent for non-severe pneumonia when a macrolide or fluoroquinolone cannot be used. Not counted as atypical cover in severe CAP. Not scored.",
          "clindamycin": "No role in this pneumonia. Not scored.",
          "metronidazole": "Anaerobic cover is not needed without a risk factor for aspiration or abscess. Not scored.",
          "cefazolin": "Not a pneumonia antibiotic. Not counted as the beta-lactam. Not scored.",
          "oseltamivir": "Reasonable while an influenza result is pending in flu season. His test is negative. Not scored.",
        }[cid] + MEMORY)

# =====================================================================  STUDIES

act("blood_culture_x_2",
    [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Two sets before the antibiotic when that does not delay it. The simulator cannot tell "
      "the order, and cultures take days." + SSC))
act("lactate",
    [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
    also_satisfies=[{"id": "hidden_reassessed", "when": "flag fluid_given set"}],
    debrief_note=(
      "3.8 on arrival, 5.4 if his shock was let reach the very-low-pressure phase. A lactate "
      "does not clear in ten minutes, so a repeat soon after fluid reads the same. The "
      "guideline suggests measuring it, with low certainty." + SSC))
act("venous_blood_gas",
    [{"when": PRE_TUBE + " OR " + P7, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "On arrival a metabolic acidosis with a low pCO2 from fast breathing. In phase 7 the "
      "pCO2 has risen to 56 and the pH fallen to 7.18: a man who can no longer blow off his "
      "acid is tiring. A rising pCO2 in a patient who was hyperventilating is a late sign."
      + MEMORY))
act("arterial_blood_gas",
    [{"when": P7 + " OR " + P10, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Gives the PaO2 for a P/F ratio. On high flow at sixty percent his PaO2 was 70, a P/F "
      "of about 117. After intubation on FiO2 0.7 and PEEP 12, 78, about 111. Either gas "
      "meets the other's expectation." + MEMORY))
for cid, note in (
  ("complete_blood_count_cbc", "A white count of 18.6 with bands. One of the minor criteria for severe CAP is a low count, not a high one."),
  ("basic_chemistry_chem_7", "A BUN of 34 is one of the minor severity criteria. A creatinine of 1.7 is acute kidney injury: hold the metformin and the lisinopril."),
  ("influenza_a_and_b_antigen_test", "Negative. In flu season it decides oseltamivir and whether corticosteroids are safe."),
):
    act(cid, [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
        debrief_note=note + MEMORY)
act("xr_chest",
    [{"when": PRE_TUBE + " OR " + P10, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Bilateral airspace opacities, worse on the right. Multilobar infiltrates are one of the "
      "minor severity criteria. After the tube, a film confirms its position." + ATS19))
for cid in ("ultrasound_lung", "ultrasound_cardiac"):
    act(cid, [{"when": PRE_TUBE, "value": "recommended"}, {"when": None, "value": "neutral"}],
        also_satisfies=[{"id": "hidden_reassessed", "when": "flag fluid_given set"}],
        debrief_note=(
          "Bedside ultrasound answers the fluid question as it changes: a small collapsing "
          "vena cava and a hyperdynamic heart before fluid, a fuller cava after, and more "
          "B-lines if fluid went to his lungs. Dynamic measures are suggested over static "
          "ones." + SSC))
for cid, note in (
  ("plasma_procalcitonin", "Markedly raised. It does not decide whether to give antibiotics in pneumonia. Not scored."),
  ("urine_rapid_antigen_test_for_s_pneumoniae", "Positive. Pneumococcus, which ceftriaxone covers. Not needed to treat him. Not scored."),
  ("covid_19_test", "Negative. Not scored."),
  ("ecg_12_lead", "Sinus tachycardia. Not scored."),
  ("fingerstick_blood_sugar", "High, as expected in a man with diabetes and sepsis. Not scored."),
  ("troponin_t", "Not part of this case's question. Not scored."),
  ("nt_probnp", "Not part of this case's question. Not scored."),
):
    act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)

for cid in ("ct_chest", "ct_pulmonary_embolus"):
    act(cid, ALWAYS("discouraged"),
        debrief_note=(
          "A scanner is a bad place for a man in shock on high flow, and the film and the "
          "ultrasound had answered the question." + MEMORY))

# =====================================================================  TRAPS

act("furosemide_40_mg_iv", ALWAYS("discouraged"),
    debrief_note=(
      "Crackles, B-lines and opacities on the film tempt a diuretic. This is pneumonia in "
      "septic shock with a small vena cava and acute kidney injury. A diuretic lowers a "
      "pressure he cannot spare." + MEMORY))
for cid in ("metoprolol_bolus", "esmolol_drip", "labetalol_bolus", "labetalol_drip",
            "propranolol_bolus", "diltiazem_bolus"):
    act(cid, ALWAYS("discouraged"),
        debrief_note="His tachycardia is compensation for fever and shock. Slowing it lowers his output and his pressure." + MEMORY)
for cid in ("nitroglycerin", "nitroglycerin_sublingual", "nitroglycerin_drip"):
    act(cid, ALWAYS("discouraged"),
        debrief_note="No indication, and it lowers a pressure he cannot spare." + MEMORY)
for cid in ("na_bicarbonate_bolus", "na_bicarbonate_infusion"):
    act(cid, ALWAYS("discouraged"),
        debrief_note=(
          "His acidosis is lactate and, later, carbon dioxide. Bicarbonate makes more carbon "
          "dioxide for a man who cannot breathe it off. The guideline suggests against it "
          "above a pH of 7.2 in septic shock." + SSC))
act("acetaminophen", ALWAYS("neutral"),
    debrief_note="Reasonable for comfort. It does not change his course. Not scored.")
act("albuterol", ALWAYS("neutral"), debrief_note="No wheeze and no COPD. Not scored.")

# =====================================================================  PEOPLE

act("consult_critical_care", ALWAYS("recommended"),
    expectation_label="ICU called",
    debrief_note=(
      "He meets the definition of severe CAP from arrival (respiratory rate over 30, P/F under "
      "250, multilobar infiltrates, a high BUN, and soon hypotension needing fluid), and the "
      "major criteria once he needs a vasopressor and a tube. Patients who deteriorate after "
      "admission to a ward do worst, which is the argument for an early ICU call." + ATS19
      + " [UNVERIFIED: Martin-Loeches et al. 2023, from the owner's structure]"))
for cid in ("consult_pulmonology", "consult_infectious_disease"):
    act(cid, ALWAYS("neutral"), state_changing=False,
        debrief_note="Not needed to treat him in the department. Not scored.")

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
EXAM_NOTES = {
  "exam_airway": "His own airway until he tires, then gurgling and a jaw thrust. After the tube, check it is where it should be.",
  "exam_breath": "Tripoding and accessory muscles on arrival, then paradoxical breathing and head bobbing as he fails. Work of breathing is the sign the saturation hides.",
  "exam_circ": "Capillary refill and mottling track his shock better than one blood pressure, and they change after fluid and a pressor.",
  "exam_pulm": "Crackles worse on the right with bronchial breathing at the base: consolidation. More crackles higher up after too much fluid.",
  "exam_card": "Fast, no murmur, no edema. Nothing points to the heart as the cause.",
  "exam_neck": "Flat neck veins fit a man who needs fluid.",
  "exam_skin": "Hot and flushed, then mottled knees, then thighs: the progression of septic shock on the skin.",
  "exam_neuro": "Alert on arrival. Drowsy as the shock deepens, confused as he tires. New confusion is a severity criterion.",
  "exam_heent": "Dry mouth and dusky lips.",
  "exam_msk": "No calf swelling. One point against a clot.",
  "exam_psych": "Anxious, then restless and confused as he tires.",
}
for cid, note in EXAM_NOTES.items():
    a = act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)
    if cid == "exam_circ":
        a["also_satisfies"] = [{"id": "hidden_reassessed", "when": "flag fluid_given set"}]

FOLLOW_UPS = [
 {"id": "sedation_after_the_tube",
  "triggered_by": ["intubate_rapid_sequence"],
  "applies_when": "action rocuronium_bolus taken",
  "deadline_seconds": 120,
  "graded": False,
  "satisfied_by": ["hidden_sedation"],
  "nurse_prompt": "Is he comfortable? He can't move.",
  "debrief_note": (
    "After rocuronium he could not move or show distress for most of an hour. Analgesia and "
    "sedation go in as soon as the tube is confirmed, and the signs of awareness are "
    "unreliable. Intubation care, not scored.")},
]
