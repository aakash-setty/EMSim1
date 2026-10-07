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
      "and a temperature of 39.4 in someone who says she has a stomach bug."))

act("insert_iv", ALWAYS("critical"),
    prompt={"deadline_seconds": 45, "guard": PRES + " OR " + HYPO,
            "text": "She's got no line and she's been vomiting for two days. Do you want access?"},
    debrief_note=(
      "Everything she needs goes through a vein: fluid, antibiotics and a vasopressor. A "
      "large peripheral line is enough to start all three, including norepinephrine."))

act("second_iv", ALWAYS("recommended"),
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
    prompt={"deadline_seconds": 80, "guard": PRES + " OR " + LOW,
            "text": ("Her heart rate is fast, her pressure is soft, and she's kept nothing "
                     "down for two days. Do you want fluid running?"),
            "escalation": {"deadline_seconds": 170,
                           "text": ("She still hasn't had any fluid. If we don't fill her "
                                    "she is going to drop her pressure. Can I hang a liter?")}},
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

# ---------------------------------------------------------------- oxygen
O2 = "oxygen_support"
for cid, delta in [("nasal_cannula_oxygen", 2), ("non_rebreather_mask", 4)]:
    act(cid, [{"when": PROF, "value": "recommended"}, {"when": None, "value": "neutral"}],
        flags_set=["oxygen_applied"],
        vital_effects=[{"vital": "oxygen_saturation", "delta": delta, "key": O2,
                        "while": LOW_G + " AND NOT flag intubated set"}],
        debrief_note=(
          "Her saturation is normal until she is in established shock, so oxygen has nothing "
          "to add early. It does no harm. It is worth applying once she is hypotensive and "
          "her saturation falls."))

# ---------------------------------------------------------------- airway
INDUCTION = {
  "etomidate_bolus": (["sedation_given"], "neutral",
    "A reasonable induction agent in shock because it has little effect on the pressure."),
  "ketamine_bolus": (["sedation_given"], "neutral",
    "A reasonable induction agent in shock. Use a reduced dose: a patient with no reserve can "
    "drop her pressure with any induction agent."),
  "propofol_bolus": (["sedation_given"], "discouraged",
    "Propofol dilates vessels and depresses the heart. In a patient whose pressure depends "
    "on a vasopressor it is the induction agent most likely to cause collapse."),
  "midazolam_bolus": (["sedation_given"], "discouraged",
    "Slow in onset and it lowers the pressure. Etomidate or ketamine asks less of her."),
  "rocuronium_bolus": (["paralytic_given"], "neutral", "A standard paralytic."),
  "succinylcholine_bolus": (["paralytic_given"], "neutral",
    "Usable. Her potassium is low, so the risk of hyperkalemia is small. With muscle injury "
    "and failing kidneys, rocuronium is the cleaner choice."),
}
for cid, (flags, tag, note) in INDUCTION.items():
    act(cid, ALWAYS(tag), flags_set=flags, debrief_note=note)

act("intubate_rapid_sequence",
    [{"when": PROF, "value": "neutral"}, {"when": None, "value": "discouraged"}],
    flags_set=["intubated"],
    follow_ups_triggered=["post_intubation_sedation"],
    debrief_note=(
      "She is breathing for herself and protecting her airway in every phase except the "
      "last. Intubating a patient in shock removes her own respiratory drive and adds "
      "sedation and positive pressure, each of which lowers the blood pressure. Resuscitate "
      "first. If she becomes obtunded and cannot protect her airway, intubation is "
      "reasonable, with a vasopressor already running."))

for cid, note in [
  ("fentanyl_bolus", "Analgesia and sedation after intubation with little effect on the pressure."),
  ("ketamine_infusion", "A reasonable sedative infusion in shock."),
  ("propofol_infusion", "Sedates well and lowers the pressure. In a patient on a vasopressor, "
                        "expect to need more of the vasopressor."),
]:
    act(cid, ALWAYS("neutral"), flags_set=["post_intubation_sedation_given"], debrief_note=note)

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
    prompt={"deadline_seconds": 75, "guard": SUPP + " OR " + PROF,
            "text": ("We've given her fluid and she's on norepinephrine, and I keep having to "
                     "turn it up. Has anyone examined her from head to toe, including a pelvic?"),
            "escalation": {"deadline_seconds": 180,
                           "text": ("She's a young woman with a fever, a rash and shock, and I "
                                    "don't think anyone has asked about her period. Do you "
                                    "want to examine her?")}},
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
     {"when": RESP + " OR " + SUPP + " OR " + STAB, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Vasopressor (norepinephrine first)",
    flags_set=["pressor_running"],
    vital_effects=[{"vital": "systolic_bp", "delta": 8, "key": "pressor_without_fluid",
                    "while": LOW_G + " AND NOT flag fluids_given set",
                    "note": ("Teaching choice. A vasopressor in a patient who has had no "
                             "fluid raises the number a little and does not get her out of "
                             "the phase. The phase change needs both.")}],
    nurse_alert=("Norepinephrine is running through the peripheral line. I'll titrate to a "
                 "mean of 65 and watch the site."),
    prompt={"deadline_seconds": 30, "guard": LOW,
            "text": ("Her mean pressure is under 65. Do you want norepinephrine started?"),
            "escalation": {"deadline_seconds": 120,
                           "text": ("Her pressure is still not holding. If we don't get a "
                                    "pressor on her she is going to get worse. Norepinephrine?")}},
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

act("stop_norepinephrine", ALWAYS("discouraged"),
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
      "scored in this case on the directing physician's decision."))

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
      "MRSA uncovered."))

act("intravenous_immunoglobulin", ALWAYS("neutral"),
    debrief_note=(
      "Sometimes given in severe toxic shock on the theory that it neutralizes toxin. The "
      "evidence is weak and is better for streptococcal than for staphylococcal disease. A "
      "decision for intensive care and infectious disease, and not scored here."))

act("hydrocortisone_bolus", ALWAYS("neutral"),
    debrief_note=(
      "Considered in septic shock that needs a rising vasopressor dose despite fluid. A "
      "reasonable later step and not a substitute for finding the source."))

# =====================================================================  SYMPTOMS AND TRAPS

act("acetaminophen", ALWAYS("neutral"),
    vital_effects=[{"vital": "temperature_c", "delta": -0.6, "key": "antipyretic",
                    "onset_seconds": 30,
                    "note": "Teaching choice. An antipyretic lowers the number and changes nothing else."}],
    debrief_note="Lowers the temperature and makes her more comfortable. It treats nothing.")

act("ondansetron", ALWAYS("neutral"),
    debrief_note=(
      "Reasonable for the vomiting. Feeling less sick is not the same as being less sick, "
      "and her vital signs do not change with it."))

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
      "A lactate of 4.6 in a patient who is talking is the laboratory's way of saying what "
      "the heart rate already said. A value over 4 marks a high-risk septic patient "
      "whatever the blood pressure is. Repeat it after resuscitation."))

act("blood_culture_x_2", ALWAYS("recommended"),
    debrief_note=(
      "Draw two sets before antibiotics when that does not delay them. In staphylococcal "
      "toxic shock the blood cultures are usually negative, because the illness is caused "
      "by toxin absorbed from a local site and not by bacteria in the blood. A negative "
      "culture does not argue against the diagnosis."))

act("basic_chemistry_chem_7", ALWAYS("recommended"),
    debrief_note=(
      "Her creatinine is 2.6 at age 22. Vomiting does not do that in two days without "
      "shock. This is one of the results that should end the gastroenteritis story."))

act("complete_blood_count_cbc", ALWAYS("recommended"),
    debrief_note=(
      "A high white count and a platelet count of 98. Thrombocytopenia with fever, rash "
      "and hypotension is multi-organ involvement and is one of the criteria used to define "
      "toxic shock syndrome."))

act("urine_hcg_qualitative", ALWAYS("recommended"),
    debrief_note=(
      "A pregnancy test belongs in the workup of any woman of reproductive age with "
      "vomiting, fainting or abdominal symptoms. It is negative."))

act("ct_abdomen", ALWAYS("neutral"),
    debrief_note=(
      "A reasonable way to look for a source once she is supported, and it shows the "
      "tampon. It takes her out of the department, and a pelvic examination finds the same "
      "thing in two minutes at the bedside."))

# =====================================================================  CONSULTS

act("consult_critical_care", ALWAYS("recommended"),
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

# =====================================================================  DISPOSITION

act("attempt_discharge", ALWAYS("discouraged"),
    display_name="Discharge home",
    hidden=True,
    flags_set=["discharge_attempted"],
    narration_override=("You want her to go home? Her rate is still fast. All right, I'll "
                        "get her up and dressed."),
    debrief_note=(
      "You chose to send her home while she still looked well, and she fainted on standing. "
      "The case let that play out instead of ending.\n\n"
      "Before discharging anyone, read the vital signs as if you had not heard the story. "
      "A heart rate over 110 with a fever and a low pressure is not explained by a stomach "
      "bug until everything else has been excluded."))

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
# Tagged neutral, as in the other packs. The Physical score reads key_exams in case_5.
EXAM_NOTES = {
  "exam_airway": "Her airway is her own until the last phase.",
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
    "Mild diffuse tenderness with a soft abdomen and no guarding. Enough to fit "
    "gastroenteritis, and not enough to explain shock."),
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
  "applies_when": "flag intubated set",
  "deadline_seconds": 90,
  "satisfied_by": ["propofol_infusion", "ketamine_infusion", "fentanyl_bolus"],
  "nurse_prompt": "She's tubed and the paralytic is still on board. What do you want her sedated with?",
  "debrief_note": (
    "A paralyzed patient with no sedation is awake and cannot say so. In shock, choose "
    "agents and doses that spare the blood pressure.")},
]
