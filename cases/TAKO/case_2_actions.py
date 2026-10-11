"""TAKO part 2: the action spine, tags, flags, prompts and vital effects.

Nothing is tagged harmful and nothing ends the case except a handoff. Every wrong drug
shows its effect on the monitor and can be undone. Every clinical judgment here is model
output awaiting a physician's signature, except the decisions in TAKO-SEED.md section 0.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

PRES = "phase is presentation"
OBS = "phase is obstructed"
WORSE_I = "phase is shock_worse"
WORSE = "(phase is shock_worse OR phase is shock_untreated)"
STEADY = "phase is steadied"
LOW = OBS + " OR phase is shock_worse OR phase is shock_untreated"
LOW_G = "(" + LOW + ")"
ACTIVE = "flag inotrope_given set AND NOT flag inotrope_stopped set"
ECG_BACK = "study ecg_12_lead resulted"
# A chest examination, a lung ultrasound or a chest film counts as the recheck only when it
# is taken after fluid has been given (authoring 8.2, the hidden target pattern).
RECHECK = [{"id": "chest_rechecked", "when": "flag fluids_given set"}]

# =====================================================================  FIRST MINUTES

act("attach_monitor",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["monitor_on"],
    prompt={"deadline_seconds": 15, "guard": PRES,
            "text": "She's not on a monitor yet. Do you want her hooked up?"},
    debrief_note=(
      "Nothing shows until the monitor is on. Her pressure of 96 over 60 is the number "
      "that should make you careful with everything you give for the pain."))

act("insert_iv", ALWAYS("critical"),
    debrief_note="A line comes before any intravenous drug, and she will need several.")

act("second_iv", ALWAYS("recommended"),
    debrief_note="A second line is worth having in anyone who may need a vasoactive infusion.")

act("ecg_12_lead",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    prompt={"deadline_seconds": 40, "guard": PRES,
            "text": "Chest pain for an hour and no ECG yet. Do you want a twelve-lead?"},
    debrief_note=(
      "A twelve-lead within ten minutes of arrival is the standard for chest pain. Hers "
      "shows anterior ST elevation, and that decides the pathway whatever the story is.\n\n"
      "Takotsubo can produce exactly this tracing. Elevation centered on V2 to V5 and II "
      "with little reciprocal depression is the pattern described in takotsubo. No feature "
      "of the ECG separates it reliably from an occluded artery, so the tracing is acted on "
      "as an infarct. "
      "[UNVERIFIED: the ten-minute standard was written from memory of the STEMI "
      "guidelines. The ECG pattern is from Ghadri et al. 2018, read through a summarizing "
      "tool]"))

act("aspirin", ALWAYS("critical"),
    # The guard tests the tracing, because the text cites it (authoring 9.5 rule 3). The
    # twelve-lead prompt at 40 seconds covers the learner who has no tracing.
    prompt={"deadline_seconds": 90, "guard": "(" + PRES + " OR " + STEADY + ") AND " + ECG_BACK,
            "text": "She has ST elevation and she hasn't had aspirin. Do you want it given?"},
    debrief_note=(
      "Aspirin is given for a suspected coronary occlusion as soon as the ECG shows one. It "
      "is cheap, safe here, and the diagnosis that would make it unnecessary is not "
      "available until after the angiogram."))

act("consult_activate_cath_lab", ALWAYS("critical"),
    display_name="Activate Catheterization Lab",
    expectation_label="Activate the catheterization laboratory",
    flags_set=["cath_lab_activated"], state_changing=True,
    narration_override="Calling the cath lab activation now.",
    # Model choice of 7 October 2026, for the owner to confirm: the laboratory is not
    # activated without a twelve-lead that has come back. Two prerequisites, so the refusal
    # says which is true: no tracing ordered, or one still printing. A refused press sets no
    # flag and earns no credit (authoring 11.5). Written like the cardiology prerequisite.
    prerequisites=[
      {"when": "study ecg_12_lead ordered",
       "failure_message": ("The cath lab will want a twelve-lead before they call the team "
                           "in. Do you want one now?")},
      {"when": ECG_BACK,
       "failure_message": ("The twelve-lead is still printing. The cath lab will want to "
                           "see it before they call the team in.")}],
    # Spoken phrases for a case-only action, which has no row in the voice table
    # (authoring 7.1, v0.24). Each was tried in the built simulator's parser.
    voice_phrases=["activate the cath lab", "activate cath lab", "cath lab",
                   "cath lab activation", "call the cath lab", "code stemi", "stemi alert",
                   "stemi activation", "catheterization lab", "cardiac cath", "primary pci"],
    prompt={"deadline_seconds": 130, "guard": ECG_BACK,
            "text": ("That ECG has ST elevation across the front. Do you want me to "
                     "activate the cath lab?")},
    debrief_note=(
      "ST elevation with ongoing chest pain is a catheterization laboratory activation, "
      "and the usual target is the artery open within 90 minutes of first medical "
      "contact. Her daughter's explanation, the funeral and her grief do not change "
      "that. The laboratory takes the call once there is a twelve-lead to show them.\n\n"
      "The angiogram is also the only test that makes the diagnosis here. It showed "
      "arteries without obstruction and a ventricle ballooning at the apex, which is "
      "takotsubo cardiomyopathy. Activating was right, and it was right for a patient who "
      "turned out not to have an infarct. "
      "[UNVERIFIED: the 90-minute target was written from memory of the STEMI guidelines]"))

act("heparin_bolus_drip", ALWAYS("neutral"),
    flags_set=["anticoagulated"],
    debrief_note=(
      "Accepted as part of the infarct pathway. Many cardiologists want it given before "
      "the laboratory and some prefer to give it there. Not scored."))

act("clopidogrel", ALWAYS("neutral"),
    debrief_note="A second antiplatelet is the cardiologist's call before angiography. Not scored.")

# ---------------------------------------------------------------- pain
for cid, name in [("fentanyl_bolus", "Fentanyl"), ("morphine_bolus", "Morphine")]:
    act(cid, ALWAYS("neutral"), flags_set=["analgesia_given"],
        debrief_note=(
          name + " in a small dose is a reasonable way to treat her pain when a nitrate is "
          "the wrong choice. Opioids lower the pressure a little in some patients, so give "
          "it slowly and watch."))

act("lorazepam_bolus", ALWAYS("neutral"),
    debrief_note=(
      "She is frightened and grieving, and a small dose is not wrong. It treats nothing "
      "that is causing the ST elevation, and feeling calmer is not the same as being "
      "safer."))

# =====================================================================  THE WRONG DRUGS

NITRATE_NOTE = (
  "Nitrates are a reflex for cardiac chest pain. They lower the filling of the heart and "
  "the resistance it pumps against. In outflow obstruction both make the obstruction "
  "worse, and her pressure was only 96 over 60 before it was given.\n\n"
  "Guidelines say to hold nitrates with a systolic pressure under 90, or well below the "
  "patient's usual pressure, or with a fast heart rate. She is a treated hypertensive at "
  "96 with a rate of 115. And a new murmur should be explained before preload is lowered. "
  "[UNVERIFIED: the nitrate thresholds were written from memory of the STEMI guidelines]")
act("nitroglycerin", ALWAYS("discouraged"),
    expectation_label="Nitrate",
    flags_set=["nitrate_given"],
    vital_effects=[{"vital": "systolic_bp", "delta": -12, "key": "nitrate_bp",
                    "duration_seconds": 120,
                    "while": "NOT " + PRES + " AND NOT " + OBS,
                    "note": ("Teaching choice. On arrival the nitrate moves her to the "
                             "obstructed phase, and that phase's own numbers are the fall. "
                             "The effect is guarded off there by name so the fall is counted "
                             "once (authoring 6.1). A guard is read against the state now and "
                             "cannot see where the drug was given, so a nitrate given in the "
                             "obstructed phase also shows no further fall while she stays "
                             "there. In worsening shock or once steadied it costs twelve "
                             "points for what is left of two minutes.")}],
    debrief_note=NITRATE_NOTE)

INOTROPE_NOTE = (
  "A low pressure with a poor ejection fraction usually gets an inotrope. In this patient "
  "the base of the ventricle is overactive and is squeezing the outflow tract shut. More "
  "contractility and a faster rate tighten it, and the pressure falls further.\n\n"
  "The murmur was the clue that her shock had a mechanical cause. When a treatment makes "
  "the patient worse, stop it. Dobutamine, epinephrine and dopamine all count as the same "
  "act here.\n\n"
  "Avoiding catecholamine inotropes in takotsubo with outflow obstruction rests on "
  "physiology and expert consensus. There are no trials. "
  "[UNVERIFIED: Ghadri et al., International Expert Consensus Document on Takotsubo "
  "Syndrome, part II, Eur Heart J 2018]")
act("dobutamine_drip", ALWAYS("discouraged"),
    expectation_label="Inotrope",
    flags_set=["inotrope_given"],
    vital_effects=[
      {"vital": "systolic_bp", "delta": -14, "key": "inotrope_bp",
       "while": STEADY + " AND NOT flag inotrope_stopped set AND NOT flag cardiology_called set",
       "note": ("Teaching choice. Once she is steadied an inotrope still costs her pressure. "
                "Guarded off once cardiology has been called, because a takeover stops the "
                "inotrope and a timed transition can set no flag. The cost: an inotrope "
                "started after a cardiology call shows nothing in the steadied phase.")},
      {"vital": "heart_rate", "delta": 16, "key": "inotrope_hr",
       "while": STEADY + " AND NOT flag inotrope_stopped set AND NOT flag cardiology_called set",
       "note": "As above."}],
    debrief_note=INOTROPE_NOTE)

act("stop_dobutamine",
    [{"when": "phase is shock_worse", "value": "critical"},
     {"when": "flag inotrope_given set", "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Stop the inotrope",
    flags_set=["inotrope_stopped"],
    narration_override="The inotrope is stopped.",
    vital_effects=[{"vital": "systolic_bp", "delta": 8, "key": "inotrope_off",
                    "while": "phase is shock_worse",
                    "note": ("Teaching choice. Stopping the inotrope alone gives back part of "
                             "the pressure. The phase changes when fluid and a "
                             "vasoconstrictor are added.")}],
    prompt={"deadline_seconds": 25, "guard": "phase is shock_worse AND NOT flag inotrope_stopped set",
            "text": "That inotrope is not helping her. Do you want it stopped?"},
    debrief_note=(
      "Stopping a drug that is making the patient worse is the first step of the rescue. "
      "It gives back part of the pressure she lost, and she then still needs fluid and a "
      "vasoconstrictor."))

act("furosemide_40_mg_iv", ALWAYS("discouraged"),
    vital_effects=[{"vital": "systolic_bp", "delta": -8, "key": "diuretic_bp",
                    "onset_seconds": 20, "duration_seconds": 240,
                    "note": "Teaching choice: a diuretic empties a ventricle that needs filling."}],
    debrief_note=(
      "Her lungs are clear and she has barely eaten or drunk for five days. A diuretic "
      "empties a ventricle that needs filling, and an emptier ventricle obstructs more."))

act("tenecteplase_tnk_bolus", ALWAYS("discouraged"),
    expectation_label="Thrombolysis",
    flags_set=["thrombolysed"],
    debrief_note=(
      "Thrombolysis is for ST elevation when angioplasty cannot be delivered in time, "
      "usually taken as a delay of more than about two hours. This hospital has a "
      "laboratory. She was given the bleeding risk of a "
      "thrombolytic for a condition that turned out to have no clot in it.\n\n"
      "The lesson is not that you should have known it was takotsubo. You could not have. "
      "It is that angiography is preferred whenever it is available, and one reason is "
      "that some patients with ST elevation have no occlusion. "
      "[UNVERIFIED: the two-hour figure was written from memory of the STEMI guidelines]"))

# =====================================================================  THE RIGHT PAIR

act("normal_saline_1l_bolus",
    [{"when": LOW, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Small crystalloid bolus",
    flags_set=["fluids_given"],
    follow_ups_triggered=["recheck_lungs_after_fluid"],
    vital_effects=[{"vital": "systolic_bp", "delta": 6, "key": "fluid_alone",
                    "duration_seconds": 60,
                    "while": LOW_G + " AND NOT flag vasoconstrictor_running set",
                    "note": "Teaching choice: fluid alone helps a little and briefly."}],
    # 45 seconds, so that in the default mode (times 3, 135 seconds) it is spoken well
    # before the 240-second deterioration (authoring 9.7).
    prompt={"deadline_seconds": 45, "guard": LOW,
            "text": ("Her chest is clear and she's hardly had a drink in five days. Do you "
                     "want a small fluid bolus?")},
    debrief_note=(
      "Fluid is the unusual part of this plan. A weak heart with a low pressure usually "
      "does not get fluid. She got it because her lungs were clear, her neck veins were "
      "flat, she was dry, and a fuller ventricle holds the outflow tract open.\n\n"
      "The dose that matters is small, 250 to 500 mL, with a reassessment. The simulator "
      "offers only 500 mL and one liter and does not count volume. With pulmonary edema "
      "the fluid would be wrong, and some patients with takotsubo have it. "
      "[UNVERIFIED: consensus recommendation, no trials]"))

act("phenylephrine_drip",
    [{"when": LOW, "value": "critical"}, {"when": None, "value": "neutral"}],
    expectation_label="Vasoconstrictor without inotropic effect (phenylephrine or vasopressin)",
    flags_set=["vasoconstrictor_running"],
    vital_effects=[{"vital": "systolic_bp", "delta": 8, "key": "vaso_alone",
                    "while": LOW_G + " AND NOT flag fluids_given set",
                    "note": "Teaching choice: a vasoconstrictor alone helps a little."}],
    # 60 seconds. At 80 the default mode put this at 240, the same instant as the
    # deterioration it warns about, and the nurse never said it. Now 180 (authoring 9.7).
    prompt={"deadline_seconds": 60, "guard": LOW,
            "text": ("Her pressure is still low. Do you want a pressor that squeezes the "
                     "vessels without driving the heart, like phenylephrine?")},
    debrief_note=(
      "Phenylephrine raises the resistance the heart pumps against and has no direct "
      "effect on contractility. It tends to slow the heart by reflex. In outflow "
      "obstruction all three of those help. Vasopressin does the same job without acting "
      "on catecholamine receptors and counts as the same act here.\n\n"
      "This choice is borrowed from hypertrophic obstructive cardiomyopathy, where it is "
      "standard teaching. For takotsubo it is physiological reasoning and expert opinion. "
      "The 2018 consensus document recommends fluid and avoiding inotropes, nitrates and "
      "diuretics, and does not name a vasoconstrictor. Reviews that do name one prefer "
      "phenylephrine. Vasopressin is an extrapolation.\n\n"
      "Phenylephrine adds load to a ventricle that is already weak, so it is right only "
      "while obstruction is the main problem. In takotsubo with shock and no obstruction "
      "the advice differs and mechanical support is often preferred. If drugs fail, the "
      "next step is mechanical support with a pump such as an Impella. A balloon pump "
      "lowers afterload and can worsen the obstruction. "
      "[UNVERIFIED: Ghadri et al. 2018 read through a summarizing tool. The reviews that "
      "name a vasoconstrictor are listed in TAKO-SEED.md without full citations]"))

act("norepinephrine_drip", ALWAYS("neutral"),
    flags_set=["vasoconstrictor_running"],
    also_satisfies=[{"id": "phenylephrine_drip", "when": None}],
    vital_effects=[{"vital": "heart_rate", "delta": 6, "key": "norepi_hr",
                    "note": "Teaching choice: some beta effect, shown as a small rise in rate."}],
    debrief_note=(
      "Norepinephrine is mostly a vasoconstrictor with some effect on contractility and "
      "rate. It is the usual first vasopressor in shock. The case accepts it as the "
      "vasoconstrictor and treats it as the second choice. A drug with no beta effect is "
      "cleaner in obstruction. Some authors accept norepinephrine with careful titration "
      "and others consider it counterproductive."))

BETA_NOTE = (
  "A short-acting beta blocker slows the heart and reduces the force of the overactive "
  "base, which may relieve outflow obstruction. The consensus document says so, and it "
  "also says beta blockers are contraindicated in acute severe heart failure with a low "
  "ejection fraction and in hypotension.\n\n"
  "She has both. The case treats a beta blocker as discouraged while her pressure is "
  "unsupported, and as neither right nor wrong once a vasoconstrictor is holding it. That "
  "later decision belongs to the cardiologist. "
  "[UNVERIFIED: Ghadri et al. 2018, read through a summarizing tool]")
act("esmolol_drip",
    [{"when": STEADY, "value": "neutral"}, {"when": None, "value": "discouraged"}],
    expectation_label="Short-acting beta blocker",
    flags_set=["beta_blocked"],
    vital_effects=[
      {"vital": "systolic_bp", "delta": -10, "key": "beta_bp", "duration_seconds": 180,
       "while": "NOT " + STEADY, "note": "Teaching choice: before her pressure is supported it falls."},
      {"vital": "heart_rate", "delta": -10, "key": "beta_hr_early", "duration_seconds": 180,
       "while": "NOT " + STEADY, "note": "As above."},
      {"vital": "heart_rate", "delta": -14, "key": "beta_hr", "while": STEADY,
       "note": "Teaching choice: once steadied the rate comes down and the pressure holds."}],
    debrief_note=BETA_NOTE)

# =====================================================================  LOOKING AT THE HEART

act("ultrasound_cardiac", ALWAYS("critical"),
    expectation_label="Bedside cardiac ultrasound",
    debrief_note=(
      "This is the second learning goal of the case. Before treating a low pressure in a "
      "patient with a weak heart, look at the heart. Hers shows an apex that does not "
      "contract and a base that contracts hard, and the mitral valve being drawn toward "
      "the septum.\n\n"
      "That picture, with the murmur, means the low pressure has a mechanical cause that "
      "an inotrope makes worse. The same check applies in hypertrophic cardiomyopathy, in "
      "some anterior infarcts and in an over-diuresed small ventricle.\n\n"
      "A bedside echo by an emergency physician can show the wall motion. Mitral valve "
      "motion and a gradient are harder to see and often need cardiology."))

act("troponin_t", ALWAYS("recommended"),
    debrief_note=(
      "Raised. On arrival the troponin in takotsubo looks like the troponin of an infarct. "
      "The difference shows over the next day, when the peak stays lower than the extent "
      "of the wall motion problem would predict. An early value separates nothing, and the "
      "decision to activate does not wait for it."))

act("nt_probnp", ALWAYS("neutral"),
    debrief_note=(
      "Very high. Takotsubo often produces a natriuretic peptide out of proportion to the "
      "troponin. A clue for afterwards, not a result to act on."))

act("xr_chest", ALWAYS("recommended"),
    also_satisfies=RECHECK,
    debrief_note=(
      "Clear lungs and a normal mediastinum. The clear lungs are what make a fluid bolus "
      "safe, and a normal mediastinum is one small point against aortic dissection."))

act("ultrasound_lung", ALWAYS("neutral"),
    also_satisfies=RECHECK,
    debrief_note="No B-lines. Dry lungs on ultrasound are the bedside evidence that a fluid bolus is safe.")

act("lactate", ALWAYS("neutral"),
    debrief_note="Rises with the shock. Worth repeating once she is supported.")

# Studies with an authored result need a case action, or they have no note (authoring
# 11.4). All four are neutral, which is what an unbound study already was.
act("basic_chemistry_chem_7", ALWAYS("neutral"),
    debrief_note=(
      "A raised BUN with a normal creatinine fits several days of poor intake. She is "
      "dry, which is part of why a small fluid bolus is right for her."))

GAS_NOTE = (
  "The lactate on the gas rises with the shock, as the laboratory lactate does. The "
  "simulator reports only the bicarbonate and the lactate on her gas.")
act("venous_blood_gas", ALWAYS("neutral"), debrief_note=GAS_NOTE)
act("arterial_blood_gas", ALWAYS("neutral"), debrief_note=GAS_NOTE)

act("fingerstick_blood_sugar", ALWAYS("neutral"),
    debrief_note="Mildly raised, as on the chemistry. Not a result to act on here.")

# =====================================================================  CONSULTS

act("consult_cardiology",
    [{"when": LOW, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["cardiology_called"], state_changing=True,
    # Decided by Aakash Setty, 6 October 2026: the cardiologist is busy until both a
    # twelve-lead and a bedside echo have been done. A prerequisite, so an early call is
    # refused with the reason, sets no flag and is not penalized.
    prerequisites=[{
      "when": "study ecg_12_lead resulted AND study ultrasound_cardiac resulted",
      "failure_message": ("Cardiology is scrubbed in a case. The fellow says they'll come to "
                          "the phone once we have a twelve-lead and a bedside echo to tell "
                          "them about.")}],
    prompt={"deadline_seconds": 20, "guard": LOW,
            "text": ("Her pressure is low and I'm not sure why. I'd get cardiology on "
                     "the phone. They will want a twelve-lead and an echo first. Do you "
                     "want me to call?")},
    debrief_note=(
      "Calling cardiology when the pressure falls is the right move in any patient on the "
      "way to the catheterization laboratory, and in this one it is the fastest route to "
      "the right plan. The cardiologist tells you what to stop and what to start, and "
      "comes to the bedside.\n\n"
      "In this case the cardiologist is in a procedure and takes the call only once there "
      "is an ECG and a bedside echo to describe. That is how a useful call goes anyway: "
      "have the findings before you call.\n\n"
      "Asking for help early in a patient you do not fully understand is a skill, not a "
      "failure."))

act("consult_critical_care", ALWAYS("neutral"),
    flags_set=["icu_called"], state_changing=True,
    debrief_note="Reasonable once she is supported. She goes to the laboratory first.")

# The target of the recheck follow-up. Nothing presses it. A chest examination, a lung
# ultrasound or a chest film taken after fluid credits it through also_satisfies.
act("chest_rechecked", ALWAYS("neutral"),
    display_name="Chest rechecked after fluid",
    hidden=True,
    debrief_note=(
      "Not a button. It records that the chest was examined, scanned or filmed after a "
      "fluid bolus."))

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
EXAM_NOTES = {
  "exam_airway": "Her airway is her own throughout.",
  "exam_breath": "Breathless with the pain and not working hard to breathe.",
  "exam_circ": "Cool hands and a thready pulse are low output, whatever its cause.",
  "exam_heent": "Nothing here. Dry mouth fits five days of poor intake.",
  "exam_neck": (
    "Flat neck veins. In cardiogenic shock from a large infarct they may be raised. Flat "
    "veins and clear lungs are part of why fluid is safe."),
  "exam_card": (
    "The examination that changes the plan. A new harsh systolic murmur at the left "
    "sternal edge that is louder with a Valsalva strain and softer with her legs raised "
    "behaves like outflow obstruction: it gets louder when the ventricle is emptier. That "
    "bedside pattern is taught for hypertrophic cardiomyopathy and is assumed here to "
    "carry over. No source was found for it in takotsubo, where the murmur can also be "
    "mitral regurgitation. "
    "[UNVERIFIED: no source was found for the murmur's response to maneuvers in takotsubo]"),
  "exam_pulm": (
    "Clear. This is what separates her from the takotsubo patient in pulmonary edema, for "
    "whom fluid would be wrong."),
  "exam_abd": "Nothing to find.",
  "exam_gu": "Nothing to find.",
  "exam_back": "No tearing pain and no tenderness. One small point against dissection.",
  "exam_msk": "No calf swelling. One small point against a clot in the lung.",
  "exam_skin": "Pale and sweating. No rash.",
  "exam_neuro": "Alert early. Confusion later is the brain not being perfused.",
  "exam_psych": (
    "Frightened and grieving, and oriented. Distress explains how she feels. It does not "
    "explain ST elevation."),
}
for cid, note in EXAM_NOTES.items():
    if cid == "exam_pulm":
        act(cid, ALWAYS("neutral"), debrief_note=note, also_satisfies=RECHECK)
    else:
        act(cid, ALWAYS("neutral"), debrief_note=note)

FOLLOW_UPS = [
 {"id": "recheck_lungs_after_fluid",
  "triggered_by": "normal_saline_1l_bolus",
  "applies_when": "flag fluids_given set",
  "deadline_seconds": 60,
  # Only a chest examination, a lung ultrasound or a chest film taken AFTER the fluid
  # discharges this. Each of the three credits the hidden action chest_rechecked through
  # also_satisfies when fluids_given is already set (authoring 8.2). Once credited it stays
  # credited, so a second bolus asks for nothing.
  "satisfied_by": ["chest_rechecked"],
  "nurse_prompt": "That bolus is in. Do you want to listen to her chest before she gets any more?",
  "debrief_note": (
    "Fluid in a patient with an ejection fraction of 30 percent is given in small amounts "
    "with a reassessment after each one. Listening to her chest, a lung ultrasound or a "
    "chest film after the bolus all count. An examination from before the bolus does not. "
    "Her lungs were clear before and stay clear. In a patient whose lungs fill, the fluid "
    "stops and the plan changes.")},
]
