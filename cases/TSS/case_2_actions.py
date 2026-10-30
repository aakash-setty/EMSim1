"""TSS part 2: the action spine, tags, flags, prompts and vital effects.

Tag rule lists are ordered and first match wins. Every list ends unconditionally.
Nothing in this case is tagged harmful and there is no halted phase: every mistake here is
recoverable, which is a design decision (see TSS-SEED.md).

Every clinical judgment in this file is model output awaiting a physician's signature,
except the four decisions recorded in TSS-SEED.md section 0.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

PRES = "phase is presentation"
RESP = "phase is fluid_responsive"
HYPO = "phase is hypotensive"
SUPP = "phase is supported"
PROF = "phase is profound_shock"
STAB = "phase is stabilizing"
LOW = HYPO + " OR " + PROF                       # mean arterial pressure under 65
LOW_G = "(" + LOW + ")"
ANY_LOW = HYPO + " OR " + SUPP + " OR " + PROF   # phases with no fluid bonus of their own
ANY_LOW_G = "(" + ANY_LOW + ")"

# =====================================================================  STABILIZATION

act("attach_monitor",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["monitor_on"],
    prompt={"deadline_seconds": 20, "guard": PRES,
            "text": "She's not on a monitor yet. Do you want her hooked up?"},
    debrief_note=(
      "The monitor is dark until it is attached. In this case the numbers are the whole "
      "argument against the story she tells: a heart rate of 128, a pressure of 94 over 58 "
      "and a temperature of 39.4 in someone who says she has a stomach flu."))

# The prompt says she has no line, so its guard tests the peripheral access flag (authoring
# 9.5 rule 2). Without that the nurse said it to a learner who had pressed Second IV first,
# which grants the flag and does not satisfy this action. Both actions name the flag the
# catalog already grants, so the validator can see it. Known limit: a learner whose only
# access is a central line or an intraosseous needle still hears this line, because those
# are not case actions and their flags cannot be named here (TSS-SEED.md, known gaps).
act("insert_iv", ALWAYS("critical"),
    flags_set=["iv_access"],
    prompt={"deadline_seconds": 45,
            "guard": "(" + PRES + " OR " + HYPO + ") AND NOT flag iv_access set",
            "text": "She's got no line and she's barely drunk anything in two days. Do you want access?"},
    debrief_note=(
      "Everything she needs goes through a vein: fluid, antibiotics and a vasopressor. A "
      "large peripheral line is enough to start all three, including norepinephrine."))

act("second_iv", ALWAYS("recommended"),
    flags_set=["iv_access"],
    debrief_note=(
      "A second line lets fluid run beside a vasopressor and antibiotics. Worth having in "
      "any patient in shock."))

# ---------------------------------------------------------------- fluid
# One case action bound to the catalog's crystalloid group, so saline and Ringer's in
# either volume are the same act with the same tag, flag and note.
#
# The phase carries the response to the FIRST bolus (presentation to fluid_responsive).
# In the three phases that have no fluid bonus of their own, a further bolus buys six
# points of pressure for a minute and then nothing. That is the lesson stated as
# behavior: each bolus buys less.
act("normal_saline_1l_bolus",
    [{"when": STAB, "value": "neutral"}, {"when": None, "value": "critical"}],
    expectation_label="Crystalloid bolus",
    flags_set=["fluids_given"],
    flags_set_repeat=[{"flag": "fluids_30mlkg", "after_administrations": 2,
                       "counter": "crystalloid_boluses"}],
    follow_ups_triggered=["second_liter"],
    vital_effects=[
      {"vital": "systolic_bp", "delta": 6, "key": "fluid_bolus", "duration_seconds": 60,
       "while": ANY_LOW,
       "note": "Teaching choice, not a modeled quantity: a small, short rise that fades."},
      {"vital": "heart_rate", "delta": -6, "key": "fluid_bolus_hr", "duration_seconds": 60,
       "while": ANY_LOW,
       "note": "As above."}],
    # v0.24 audit. The deadline was 80. In the default mode that is 240, the same instant
    # as the hypotensive phase's exit, so the nurse never said it there. 60 gives 180, which
    # is 120 seconds before the 300-second exit and 60 before the 240-second one. Both lines
    # are true in every phase the guard allows: neither says what is about to happen, and
    # "bolus" stays true when a maintenance infusion is running.
    prompt={"deadline_seconds": 60, "guard": PRES + " OR " + LOW,
            "text": ("Her heart rate is fast, her pressure is soft, and she's kept nothing "
                     "down for two days. Do you want a fluid bolus?"),
            "escalation": {"deadline_seconds": 170,
                           "text": ("She still hasn't had a fluid bolus. She is dry and she "
                                    "needs volume. Can I hang a liter?")}},
    debrief_note=(
      "Crystalloid is the first treatment for septic shock, and the usual target is about "
      "30 mL/kg in the first hours. She weighs 62 kg, so that is close to two liters. "
      "Guidelines suggest a balanced crystalloid over saline. Both are accepted here.\n\n"
      "Two things to take from how she responded. The first liter helped and the help did "
      "not last, because toxic shock dilates vessels and makes them leak. And once her "
      "mean pressure was under 65 after fluid, more fluid alone moved the number for a "
      "minute and no longer. That pattern is the indication for a vasopressor.\n\n"
      "The 30 mL/kg figure is a guideline default with weak evidence behind the exact "
      "number. It is a starting point for reassessment, not a dose to complete before "
      "thinking. [UNVERIFIED, confirm against the current Surviving Sepsis guideline]"))

# ---------------------------------------------------------------- maintenance infusions
# v0.24 audit. The two crystalloid infusions were unbound, so a learner who hung one heard
# the catalog line, set no flag and got no note. They are their own action, covering both
# agents (build_case.py), and they are NOT the bolus: no flag, no effect, no credit. The
# alert and the note say only what the bolus note already teaches. Neutral, awaiting a
# physician's decision on the tag.
act("normal_saline_infusion", ALWAYS("neutral"),
    expectation_label="Maintenance crystalloid infusion",
    nurse_alert="That's running at a maintenance rate. It isn't a bolus.",
    debrief_note=(
      "A maintenance infusion is not a bolus. Crystalloid is the first treatment for septic "
      "shock, and the usual target is about 30 mL/kg in the first hours, which for her is "
      "close to two liters. An infusion at a maintenance rate does not deliver that. The "
      "case counts a bolus as fluid resuscitation and does not count this."))

# ---------------------------------------------------------------- oxygen
# Four routes, one key, so no two of them stack (authoring 16). The cannula and the mask
# were authored on 6 October 2026. The bag and non-invasive ventilation were bound on
# 7 October 2026 after the audit, with the mask's delta and a neutral tag. The delta is
# derived by a model from the mask's and is a teaching choice awaiting sign-off.
O2 = "oxygen_support"
O2_WHILE = LOW_G + " AND NOT flag intubated set"
# 29 October 2026 (owner: one act by any route). The mask carries the one oxygen
# expectation and the cannula meets it. Before this, a cannula alone was marked as a missed
# mask and a mask alone as a missed cannula.
for cid, delta in [("nasal_cannula_oxygen", 2), ("non_rebreather_mask", 4)]:
    act(cid, ([{"when": LOW, "value": "recommended"}, {"when": None, "value": "neutral"}]
              if cid == "non_rebreather_mask" else ALWAYS("neutral")),
        **({"also_satisfies": [{"id": "non_rebreather_mask", "when": None}]}
           if cid == "nasal_cannula_oxygen" else {"expectation_label": "Oxygen, by any device"}),
        flags_set=["oxygen_applied"],
        vital_effects=[{"vital": "oxygen_saturation", "delta": delta, "key": O2,
                        "while": O2_WHILE,
                        "note": "Teaching choice, not a modeled quantity."}],
        debrief_note=(
          "Her saturation is normal until she is in established shock, so oxygen has nothing "
          "to add early. It does no harm. It is worth applying once she is hypotensive and "
          "her saturation falls. Either device is enough at her saturations, and either one "
          "counts."))
for cid in ["bag_valve_mask", "non_invasive_positive_pressure_ventilation"]:
    act(cid, ALWAYS("neutral"),
        flags_set=["oxygen_applied"],
        vital_effects=[{"vital": "oxygen_saturation", "delta": 4, "key": O2,
                        "while": O2_WHILE,
                        "note": ("Teaching choice. The same four points as the non-rebreather "
                                 "mask, on the same key, so this route cannot be stacked on "
                                 "a mask. Derived by a model from the mask's delta on "
                                 "7 October 2026. Needs a physician's signature.")}],
        debrief_note=(
          "Another route to oxygen. In this case it raises the saturation by the same amount "
          "as a non-rebreather mask once she is hypotensive, and it does not add to one. She "
          "is breathing for herself and protecting her airway until she is obtunded, and "
          "her saturation is normal until she is in established shock."))

# ---------------------------------------------------------------- airway
INDUCTION = {
  "etomidate_bolus": (["sedation_given"], "neutral",
    "A reasonable induction agent in shock because it has little effect on the pressure."),
  "ketamine_bolus": (["sedation_given"], "neutral",
    "A reasonable induction agent in shock. Use a reduced dose: a patient with no reserve can "
    "drop her pressure with any induction agent."),
  # propofol and midazolam were discouraged. Intubation care is never graded (owner,
  # 23 October 2026, authoring 6.3). The notes stay and say why.
  "propofol_bolus": (["sedation_given"], "neutral",
    "Propofol dilates vessels and depresses the heart. In a patient whose pressure depends "
    "on a vasopressor it is the induction agent most likely to cause collapse."),
  "midazolam_bolus": (["sedation_given"], "neutral",
    "Slow in onset and it lowers the pressure. Etomidate or ketamine asks less of her."),
  "rocuronium_bolus": (["paralytic_given"], "neutral", "A standard paralytic."),
  "succinylcholine_bolus": (["paralytic_given"], "neutral",
    "Usable. Her potassium is low, so the risk of hyperkalemia is small. With muscle injury "
    "and failing kidneys, rocuronium is the cleaner choice."),
}
for cid, (flags, tag, note) in INDUCTION.items():
    a = act(cid, ALWAYS(tag), flags_set=flags, debrief_note=note)
    if cid == "midazolam_bolus":
        # Given with the tube in it is post-intubation sedation, as in MGCA and AFRVR.
        # Given before the tube it is the induction dose and does not discharge the
        # follow-up. The tag is unchanged.
        a["also_satisfies"] = [{"id": "sedation_after_tube", "when": "flag intubated set"}]

act("intubate_rapid_sequence",
    [{"when": PROF, "value": "neutral"}, {"when": None, "value": "discouraged"}],
    flags_set=["intubated"],
    follow_ups_triggered=["post_intubation_sedation"],
    debrief_note=(
      "She is breathing for herself and protecting her airway until she is obtunded. "
      "Intubating a patient in shock removes her own respiratory drive and adds "
      "sedation and positive pressure, each of which lowers the blood pressure. Resuscitate "
      "first. If she becomes obtunded and cannot protect her airway, intubation is "
      "reasonable, with a vasopressor already running."))

# v0.24 audit. The follow-up below asks what she is sedated with once she is tubed. Its
# satisfied_by was set membership, so a fentanyl bolus given before the tube discharged it.
# A bolus now counts only when it is given with the tube in: each one credits the hidden
# target action sedation_after_tube through also_satisfies, with a condition (authoring
# 8.2). An infusion keeps running, so one started before the tube still counts and the two
# infusions stay in satisfied_by directly.
AFTER_TUBE = [{"id": "sedation_after_tube", "when": "flag intubated set"}]
SEDATION_AFTER_NOTE = (
  "Counts as sedation after intubation in this case when it is given with the tube in. In "
  "shock, choose agents and doses that spare the blood pressure.")
for cid, note in [
  ("fentanyl_bolus", "Analgesia and sedation after intubation with little effect on the pressure."),
  ("lorazepam_bolus", SEDATION_AFTER_NOTE),
  ("morphine_bolus", SEDATION_AFTER_NOTE),
]:
    act(cid, ALWAYS("neutral"), flags_set=["post_intubation_sedation_given"],
        also_satisfies=AFTER_TUBE, debrief_note=note)
for cid, note in [
  ("ketamine_infusion", "A reasonable sedative infusion in shock."),
  ("propofol_infusion", "Sedates well and lowers the pressure. In a patient on a vasopressor, "
                        "expect to need more of the vasopressor."),
]:
    act(cid, ALWAYS("neutral"), flags_set=["post_intubation_sedation_given"], debrief_note=note)

act("sedation_after_tube", ALWAYS("neutral"),
    display_name="Sedation given after intubation",
    hidden=True,
    debrief_note=(
      "Not a button. The case credits this when a sedative or analgesic bolus is given with "
      "the tube in, so that a dose given before intubation does not discharge the "
      "post-intubation sedation follow-up."))

# =====================================================================  SOURCE CONTROL

act("remove_vaginal_foreign_body", ALWAYS("critical"),
    expectation_label="Find and remove the retained tampon",
    flags_set=["source_removed"],
    prerequisites=[{
      "when": "action exam_gu taken",
      "failure_message": ("I can set up a speculum, but nobody has examined her down there "
                          "yet. Do you want to do the pelvic exam first?")}],
    narration_override=(
      "Speculum is in. There's a tampon high in the vault, dark brown and foul-smelling. "
      "It's out, and I've bagged it and sent a swab."),
    # v0.24 audit. The text said "We've given her fluid and she's on norepinephrine". The
    # guard allows profound shock, which the do-nothing path reaches with neither given, and
    # a covered sibling can be the drug running. The line now claims no treatment, and it is
    # also true for a learner who found the tampon and has not removed it. The escalation
    # said "I don't think anyone has asked about her period", which is false for a learner
    # who asked. It is now a question. The deadline was 75. In the default mode 60 gives
    # 180, which leaves 90 seconds before the 270-second exit. The line says "a pelvic
    # exam" and not "a pelvic", because the spoken phrase "pelvic exam" orders the
    # genitourinary examination and a bare "pelvic" is offered as a choice with a film.
    # 28 October 2026, author instruction: the nurse only asks whether anyone checked for
    # pregnancy. Her answer to that ("I've just had my period") is the cue to periods and
    # tampons, so the prompt no longer names the period, the source or the pelvic exam.
    prompt={"deadline_seconds": 60, "guard": SUPP + " OR " + PROF,
            "text": "Did someone check if she's pregnant?",
            "escalation": {"deadline_seconds": 180,
                           "text": "Has anyone checked whether she could be pregnant?"}},
    debrief_note=(
      "This is the action the case turns on. A tampon left in for four days was the site "
      "where Staphylococcus aureus was making toxin, and nothing given through a vein "
      "removes it.\n\n"
      "Nobody will tell you it is there. She thinks her period is over and has forgotten "
      "the tampon. You find it by asking about menstruation and tampon use, or by doing a "
      "pelvic examination because a febrile patient in shock with a red rash has no other "
      "source. A CT of the abdomen and pelvis would also show it, later.\n\n"
      "The idea that travels: septic shock without a source means you have not finished "
      "looking. Examine the places that are easy to skip, which are the pelvis, the "
      "perineum, the back, wounds, and anything packed or implanted.\n\n"
      "In this simulator the pelvic examination has to come first, because you cannot "
      "remove what you have not found."))

# =====================================================================  VASOPRESSORS

act("norepinephrine_drip",
    [{"when": LOW, "value": "critical"},
     # 29 October 2026 (owner): neutral while she still answers fluid. Accepted, not expected.
     {"when": SUPP + " OR " + STAB, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Vasopressor (norepinephrine first)",
    flags_set=["pressor_running"],
    vital_effects=[{"vital": "systolic_bp", "delta": 8, "key": "pressor_without_fluid",
                    "while": LOW_G + " AND NOT flag fluids_given set",
                    "note": ("Teaching choice. A vasopressor in a patient who has had no "
                             "fluid raises the number a little and does not get her out of "
                             "the phase. The phase change needs both.")}],
    # v0.24 audit. This action covers three other infusions, and the alert is spoken for
    # each of them, so it names the class. "through the peripheral line" was not something
    # the prerequisites guarantee. The escalation named a consequence in a phase that has
    # no worse phase to go to. It now states what is on the monitor: with no norepinephrine
    # or covered sibling running the mean is under 65 in both phases, with every effect.
    nurse_alert=("The vasopressor is running. I'll titrate to a mean of 65 and watch the "
                 "site."),
    # 28 October 2026, author instruction: the nurse states the number and does not name the
    # drug. Choosing the vasopressor is the resident's step.
    prompt={"deadline_seconds": 30, "guard": LOW,
            "text": ("Her mean pressure is under 65. Should we do something?"),
            "escalation": {"deadline_seconds": 120,
                           "text": ("Her mean pressure is still under 65. What do you want "
                                    "to do?")}},
    debrief_note=(
      "Norepinephrine is the first vasopressor in septic shock. The indication is a mean "
      "arterial pressure under 65 that persists after fluid. In this case that moment "
      "arrives when the effect of the first liters fades.\n\n"
      "Starting it earlier, while a second liter runs, is also accepted here. Guidelines "
      "allow a vasopressor through a good peripheral line for a short time, so it should "
      "not wait for a central line.\n\n"
      "Epinephrine, vasopressin and phenylephrine infusions count as the same act in this "
      "case. Norepinephrine is the one to reach for first. "
      "[UNVERIFIED, confirm against the current Surviving Sepsis guideline]"))

act("dopamine_drip", ALWAYS("discouraged"),
    flags_set=["pressor_running"],
    # No default pressor effect (owner, 27 October 2026): pressor_running moves the phase,
    # and the phase's vitals already carry the rise.
    vital_effects=[],
    debrief_note=(
      "Dopamine raises the pressure and the case treats it as a running vasopressor. It is "
      "discouraged because it causes more arrhythmias than norepinephrine in shock, and she "
      "already has a heart rate over 120. Norepinephrine is first line. "
      "[UNVERIFIED: De Backer et al., NEJM 2010, the SOAP II trial]"))

act("phenylephrine_bolus", ALWAYS("neutral"),
    vital_effects=[{"vital": "systolic_bp", "delta": 12, "key": "push_dose_pressor",
                    "duration_seconds": 90, "while": ANY_LOW,
                    "note": "Teaching choice: a push dose buys a minute or two."}],
    debrief_note=(
      "A push-dose vasopressor buys a minute or two while an infusion is set up. It is a "
      "bridge and does not replace the infusion."))

# v0.24 audit. Covers the stop entry of every vasopressor infusion the case counts
# (build_case.py), because a learner who started vasopressin and pressed Stop Vasopressin
# was told it had stopped, was not scored, and the flag stayed set. Discouraged only while
# a vasopressor is running. With none running the prerequisite blocks it, so the nurse no
# longer says she has left running something that was never started.
act("stop_norepinephrine",
    [{"when": "flag pressor_running set", "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    expectation_label="Stop the vasopressor",
    prerequisites=[{
      "when": "flag pressor_running set",
      "failure_message": "There's no vasopressor running to stop."}],
    narration_override=("Her pressure depends on it, so I've left it running. Tell me again "
                        "if you really want it off."),
    debrief_note=(
      "She is vasopressor dependent in every phase after it is started. In this simulator "
      "the infusion keeps running. Weaning happens in intensive care, over hours, once the "
      "dose requirement has fallen."))

# =====================================================================  ANTIBIOTICS

act("vancomycin", ALWAYS("critical"),
    expectation_label="Antibiotic with MRSA cover (vancomycin)",
    flags_set=["mrsa_cover_given", "abx_given"],
    prompt={"deadline_seconds": 110,
            "text": ("She's febrile and in shock and nothing is covering MRSA yet. Do you want "
                     "vancomycin up?")},
    debrief_note=(
      "Antibiotics in septic shock are given as early as possible, after cultures if the "
      "cultures do not delay them. For suspected toxic shock the usual empiric regimen is "
      "vancomycin plus clindamycin. Vancomycin covers Staphylococcus aureus including MRSA "
      "until the swab and cultures say otherwise. Linezolid is an alternative some centers "
      "prefer, and it is not in this simulator.\n\n"
      "Clindamycin is the other half. It stops bacterial protein synthesis and so reduces "
      "toxin production, which a cell-wall drug does not do. The support for this is "
      "laboratory and observational data, not trials. It is not scored in this case, and "
      "you should still give it.\n\n"
      "The patient will not show you the benefit of either drug in the emergency "
      "department. Antibiotics change the next days, not the next minutes, and the case "
      "does not pretend otherwise. "
      "[UNVERIFIED, confirm regimen against current IDSA and local guidance]"))

act("clindamycin", ALWAYS("neutral"),
    flags_set=["toxin_suppression_given", "abx_given"],
    debrief_note=(
      "The right drug to add. Clindamycin suppresses toxin production by stopping "
      "bacterial protein synthesis. It is given with vancomycin, not instead of it, because "
      "clindamycin resistance in Staphylococcus aureus is common enough to matter. Not "
      "scored in this case on the directing physician's decision. "
      "[UNVERIFIED: toxin suppression and the resistance rate]"))

act("ceftriaxone", ALWAYS("neutral"),
    flags_set=["abx_given", "broad_cover_given"],
    debrief_note=(
      "Reasonable broad cover while the source is unknown. Fever, rash and shock in a "
      "young adult also raise meningococcal disease, which ceftriaxone treats. A broad "
      "beta-lactam does not replace vancomycin and clindamycin here, and adding one is not "
      "penalized."))

act("cefazolin", ALWAYS("neutral"),
    flags_set=["abx_given"],
    debrief_note=(
      "Covers methicillin-susceptible staphylococci, which cause most menstrual toxic "
      "shock. It is a drug for after the susceptibilities are known. Empirically it leaves "
      "MRSA uncovered. "
      "[UNVERIFIED: that most menstrual toxic shock is methicillin-susceptible]"))

act("intravenous_immunoglobulin", ALWAYS("neutral"),
    debrief_note=(
      "Sometimes given in severe toxic shock on the theory that it neutralizes toxin. The "
      "evidence is weak and is better for streptococcal than for staphylococcal disease. A "
      "decision for intensive care and infectious disease, and not scored here. "
      "[UNVERIFIED: the evidence for immunoglobulin]"))

act("hydrocortisone_bolus", ALWAYS("neutral"),
    debrief_note=(
      "Considered in septic shock that needs a rising vasopressor dose despite fluid. A "
      "reasonable later step and not a substitute for finding the source. "
      "[UNVERIFIED, confirm against the current Surviving Sepsis guideline]"))

# =====================================================================  SYMPTOMS AND TRAPS

act("acetaminophen", ALWAYS("neutral"),
    vital_effects=[{"vital": "temperature_c", "delta": -0.6, "key": "antipyretic",
                    "onset_seconds": 30,
                    "note": "Teaching choice. An antipyretic lowers the number and changes nothing else."}],
    debrief_note="Lowers the temperature and makes her more comfortable. It treats nothing.")

act("ondansetron", ALWAYS("neutral"),
    debrief_note=(
      "She is vomiting, so an antiemetic is kind. It treats a symptom and not the shock. "
      "Feeling less sick is not the same as being less sick, and her vital signs do not "
      "change with it."))

act("ibuprofen", ALWAYS("discouraged"),
    debrief_note=(
      "Her creatinine is 2.6 and her platelets are 98. A nonsteroidal drug reduces renal "
      "blood flow in a patient who is already underperfusing her kidneys, and impairs "
      "platelets she is short of. Use acetaminophen."))

RATE_NOTE = (
  "Her fast heart rate is what is holding her blood pressure up. Slowing it takes away the "
  "compensation. A sinus tachycardia in a febrile, hypotensive patient is a sign to find "
  "and treat the cause, and is not the thing to treat.")
act("metoprolol_bolus", ALWAYS("discouraged"),
    expectation_label="Rate control",
    flags_set=["rate_slowed"],
    vital_effects=[
      {"vital": "heart_rate", "delta": -16, "key": "rate_control_hr", "duration_seconds": 180,
       "note": "Teaching choice: the rate falls and the pressure falls with it."},
      {"vital": "systolic_bp", "delta": -12, "key": "rate_control_bp", "duration_seconds": 180,
       "note": "As above."}],
    nurse_alert="Her rate has come down and so has her pressure.",
    debrief_note=RATE_NOTE)

act("furosemide_40_mg_iv", ALWAYS("discouraged"),
    expectation_label="Loop diuretic",
    debrief_note=(
      "Her kidneys are failing because they are not being perfused. A diuretic removes "
      "volume she does not have. The treatment for this kidney injury is restoring the "
      "circulation."))

act("lumbar_puncture", ALWAYS("discouraged"),
    debrief_note=(
      "Fever and a rash make meningitis worth a thought. She has only a mild headache and "
      "no neck stiffness or photophobia, and she is in shock. Positioning an unstable "
      "patient for a lumbar puncture delays what she needs. Treat first. If "
      "meningitis is a real concern, give ceftriaxone and reconsider when she is stable."))

# =====================================================================  PROCEDURES

act("insert_foley_catheter", ALWAYS("recommended"),
    flags_set=["foley_placed"],
    narration_override="Foley is in. About 40 mL of dark urine in the bag.",
    debrief_note=(
      "Urine output is the cheapest measure of whether the kidneys are being perfused. "
      "With a creatinine of 2.6 and a vasopressor running, hourly output is worth knowing."))

# =====================================================================  INVESTIGATIONS

act("lactate", ALWAYS("recommended"),
    debrief_note=(
      "Her lactate on arrival was 4.6. A raised lactate in a patient who is talking is the "
      "laboratory's way of saying what the heart rate already said. A value over 4 marks a "
      "high-risk septic patient whatever the blood pressure is. Repeat it after "
      "resuscitation. [UNVERIFIED: lactate over 4 as a risk marker]"))

act("blood_culture_x_2", ALWAYS("recommended"),
    debrief_note=(
      "Draw two sets before antibiotics when that does not delay them. In staphylococcal "
      "toxic shock the blood cultures are usually negative, because the illness is caused "
      "by toxin absorbed from a local site and not by bacteria in the blood. A negative "
      "culture does not argue against the diagnosis."))

act("basic_chemistry_chem_7", ALWAYS("recommended"),
    debrief_note=(
      "Her creatinine is 2.6 at age 22. Two days of vomiting and diarrhea make a young "
      "person dry, and the potassium of 3.3 is what those losses do. A creatinine of 2.6 with "
      "a lactate of 4.6 is shock, not a stomach bug. This is one of the results that should "
      "end the stomach bug story."))

act("complete_blood_count_cbc", ALWAYS("recommended"),
    debrief_note=(
      "A high white count and a platelet count of 98. Thrombocytopenia with fever, rash "
      "and hypotension is multi-organ involvement and is one of the criteria used to define "
      "toxic shock syndrome. The hemoglobin is at the top of the range in a patient on day "
      "five of her period, which fits a dry patient."))

act("urine_hcg_qualitative", ALWAYS("recommended"),
    debrief_note=(
      "A pregnancy test belongs in the workup of any woman of reproductive age with "
      "vomiting, fainting or abdominal symptoms. It is negative."))

act("ct_abdomen", ALWAYS("neutral"),
    debrief_note=(
      "A reasonable way to look for a source once she is supported, and it shows the "
      "tampon. It takes her out of the department, and a pelvic examination finds the same "
      "thing in two minutes at the bedside. [UNVERIFIED: the CT appearance of a tampon]"))

# ---------------------------------------------------------------- studies bound after the audit
# v0.24 audit, finding 8. Each of these has an authored result in case_3_content.py and
# had no case action, so no tag and no debrief note. Every tag here is NEUTRAL and is a
# placeholder awaiting a physician's decision (TSS-SEED.md lists them). The notes are the
# interpretation that used to sit in the result comments, where the learner read it under
# the numbers, plus sentences the pack already says elsewhere. A model assembled them on
# 7 October 2026 and no physician has read them.
STUDY_NOTES = {
  "venous_blood_gas": (
    "A metabolic acidosis with a raised lactate and respiratory compensation. Her fast "
    "breathing with clear lungs is that compensation."),
  "arterial_blood_gas": (
    "A metabolic acidosis with respiratory compensation. Her fast breathing with clear "
    "lungs is that compensation."),
  "liver_function_tests_lfts": (
    "Liver involvement: raised transaminases and bilirubin, and a low albumin. Kidney, "
    "liver, platelets and muscle are all involved in her, and that pattern is what "
    "separates toxic shock from a stomach bug or another viral illness."),
  "creatine_kinase_ck": (
    "Her creatine kinase is 2,140. That is muscle involvement, and it matches her muscle "
    "pain and tenderness. Muscle involvement is part of toxic shock, and with an injured "
    "kidney it needs watching."),
  "coagulation_panel": (
    "Mildly prolonged clotting times with low platelets: early coagulopathy of sepsis."),
  "plasma_procalcitonin": (
    "Raised at 24.0 ng/mL against a limit of 0.10. A number like this does not tell you "
    "where the source is. Shock with no source means you have not finished looking."),
  "c_reactive_protein_crp": (
    "Raised at 238 mg/L against a limit of 5. It does not tell you where the source is."),
  "urinalysis": (
    "White cells without bacteria or nitrite. Pyuria with no evidence of urinary infection "
    "is a recognized finding in toxic shock. The blood, and some of the white cells, may be "
    "menstrual contamination.\n\n"
    "This result is the trap in the case. White cells in the urine without bacteria are "
    "not a urinary infection, and treating them as the source ends the search early. "
    "[UNVERIFIED: sterile pyuria in toxic shock]"),
  "serum_hcg_quantitative": (
    "A pregnancy test belongs in the workup of any woman of reproductive age with vomiting, "
    "fainting or abdominal symptoms. It is negative."),
  "peripheral_smear": (
    "The film shows what the blood count shows: a neutrophilia with a left shift and "
    "reduced platelets. No schistocytes and no blasts."),
  "ecg_12_lead": (
    "Sinus tachycardia with narrow complexes and no ST change. A sinus tachycardia in a "
    "febrile, hypotensive patient is a sign to find and treat the cause, and is not the "
    "thing to treat."),
  "ultrasound_cardiac": (
    "A small collapsing vena cava and a vigorous ventricle: an empty, dilated circulation "
    "and a heart that is working."),
  "ultrasound_fast": (
    "A small volume of free fluid in the pelvis, which the CT of the abdomen also reports. "
    "No fluid anywhere else."),
}
for cid, note in STUDY_NOTES.items():
    act(cid, ALWAYS("neutral"), debrief_note=note)

# =====================================================================  CONSULTS

# 28 October 2026, author instruction: no longer recommended. She still needs the ICU, and
# the disposition scores that. Calling the consultant is the resident's choice.
act("consult_critical_care", ALWAYS("neutral"),
    flags_set=["icu_consulted"], state_changing=True,
    debrief_note=(
      "She needs intensive care: a vasopressor, organ support and close monitoring. Call "
      "early, with the lactate and the vasopressor dose."))

act("consult_infectious_disease", ALWAYS("neutral"),
    flags_set=["id_consulted"], state_changing=True,
    debrief_note="Useful for the antibiotic plan and for the question of immunoglobulin.")

act("consult_ob_gyn", ALWAYS("neutral"),
    flags_set=["gyn_consulted"], state_changing=True,
    debrief_note=(
      "Not needed to remove a tampon, which is a bedside procedure for the emergency "
      "physician. Reasonable afterwards for follow-up."))

# v0.24 audit, catalog finding 5.10. Nephrology answered with the global "not sure why I
# was called" line in a case that credits acute kidney injury. The reply in case_3 restates
# what the furosemide, ibuprofen, Foley and kidney injury notes already say. Neutral,
# awaiting a physician's decision on the tag and on the reply.
act("consult_renal", ALWAYS("neutral"),
    debrief_note=(
      "Her kidneys are failing because they are not being perfused, and the treatment for "
      "this kidney injury is restoring the circulation. Nephrology adds nothing tonight "
      "that the resuscitation does not. The kidney injury changes how every later drug is "
      "dosed, vancomycin first among them."))

# =====================================================================  DISPOSITION

act("attempt_discharge", ALWAYS("discouraged"),
    display_name="Discharge home",
    hidden=True,
    flags_set=["discharge_attempted"],
    # v0.24 audit. It said "Her rate is still fast". After a liter and a rate-controlling
    # drug the monitor reads 98. The fever holds in both phases with every effect.
    narration_override=("You want her to go home? She still has a fever. All right, I'll "
                        "get her up and dressed."),
    debrief_note=(
      "You chose to send her home while she still looked well, and she fainted on standing. "
      "The case let that play out instead of ending.\n\n"
      "Before discharging anyone, read the vital signs as if you had not heard the story. "
      "A heart rate over 110 with a fever, a low pressure and a faint is not explained by a "
      "stomach bug until everything else has been excluded."))

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
# Tagged neutral, as in the other packs. The Physical score reads key_exams in case_5.
EXAM_NOTES = {
  "exam_airway": "Her airway is her own until she is obtunded.",
  "exam_breath": "A fast respiratory rate with clear lungs is compensation for a metabolic acidosis.",
  "exam_circ": (
    "Capillary refill of four seconds with a thready pulse is shock, whatever the blood "
    "pressure reads. This examination takes ten seconds and contradicts the story."),
  "exam_heent": (
    "Red eyes without discharge and a red tongue are mucous membrane signs of toxic shock. "
    "They are easy to miss if you are not looking for them."),
  "exam_neck": "A supple neck does not exclude meningitis. With no photophobia and a clear mind it makes it less likely.",
  "exam_card": "A fast regular rhythm and a flow murmur. No sign of a failing heart.",
  "exam_pulm": "Clear lungs. This is not a pneumonia, and she can take fluid.",
  "exam_abd": (
    "A soft abdomen, mildly tender all over with active bowel sounds, as two days of "
    "vomiting and diarrhea would leave it. No guarding or rebound, so no abdominal source "
    "here, which is one more reason to keep looking."),
  "exam_gu": (
    "The examination that finds the diagnosis. A pelvic examination is part of looking for a "
    "source in a febrile woman in shock, and it is the one most often left out. Do it with a "
    "chaperone and explain why."),
  "exam_back": "No flank tenderness, which argues against a kidney source.",
  "exam_msk": "Diffuse muscle tenderness goes with the raised creatine kinase.",
  "exam_skin": (
    "A diffuse red rash that blanches, like a sunburn, including places the sun does not "
    "reach. She has an explanation for it and the explanation is wrong. Petechiae that do "
    "not blanch would raise meningococcal disease, though early on the two rashes can "
    "look alike."),
  "exam_neuro": "Alert and oriented early. Drowsiness later is cerebral hypoperfusion.",
  "exam_psych": "Calm and cooperative. Her wish to go home is not a sign that she is well.",
}
for cid, note in EXAM_NOTES.items():
    act(cid, ALWAYS("neutral"), debrief_note=note)

# =====================================================================  FOLLOW-UPS

FOLLOW_UPS = [
 {"id": "second_liter",
  "triggered_by": "normal_saline_1l_bolus",
  "applies_when": "flag fluids_given set AND NOT flag pressor_running set",
  "deadline_seconds": 60,
  "satisfied_when": "flag fluids_30mlkg set OR flag pressor_running set",
  "nurse_prompt": ("That bolus is in. She's 62 kilos, so 30 per kilo is nearly two liters. "
                   "Do you want another one running?"),
  "debrief_note": (
    "One bolus is the start of fluid resuscitation. The usual target in septic shock is "
    "about 30 mL/kg, followed by a reassessment of the pressure, the capillary refill and "
    "the lactate. The obligation is also discharged by starting a vasopressor, because that "
    "is the same decision made the other way: fluid alone is not going to be enough.\n\n"
    "The simulator counts boluses and not volume, so two 500 mL boluses discharge this the "
    "same way two liters do. That is a limit of the tool.")},

 {"id": "post_intubation_sedation",
  "triggered_by": "intubate_rapid_sequence",
  "graded": False,
  "applies_when": "flag intubated set",
  "deadline_seconds": 90,
  "satisfied_by": ["propofol_infusion", "ketamine_infusion", "sedation_after_tube"],
  "satisfied_by_note": (
    "v0.24 audit. An infusion counts whenever it was started. A bolus of fentanyl, "
    "midazolam, lorazepam or morphine counts only when it is given with the tube in, through "
    "the hidden action sedation_after_tube. The sibling packs list midazolam, lorazepam and "
    "morphine as satisfiers and this pack did not."),
  "nurse_prompt": "She's tubed and the paralytic is still on board. What do you want her sedated with?",
  "debrief_note": (
    "A paralyzed patient with no sedation is awake and cannot say so. In shock, choose "
    "agents and doses that spare the blood pressure. A dose given before the tube went in "
    "does not count here.")},
]
