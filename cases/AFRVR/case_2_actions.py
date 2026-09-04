"""AFRVR part 2: case actions."""

CRIT_ALWAYS = [{"when": None, "value": "critical"}]
NEUTRAL     = [{"when": None, "value": "neutral"}]
RECOMMENDED = [{"when": None, "value": "recommended"}]
DISCOURAGED = [{"when": None, "value": "discouraged"}]

PRE_IV = {"when": "flag iv_access set OR flag central_access set OR flag io_access set",
          "failure_message": "He hasn't got a line in yet. Do you want me to get IV access first?",
          "source": "catalog_default_retained"}

def A(cid, name=None, tag=None, flags=None, **kw):
    d = {"catalog_id": cid, "tag": tag or NEUTRAL}
    if name: d["display_name"] = name
    if flags is not None: d["flags_set"] = flags
    d.update(kw)
    return d

ACTIONS = []
add = ACTIONS.append

# ------------------------------------------------------------------ infrastructure
add(A("attach_monitor", tag=CRIT_ALWAYS, flags=["monitor_attached"],
  prompt={"deadline_seconds": 20,
          "guard": "NOT flag monitor_attached set",
          "text": "He isn't on the monitor yet, so you've got nothing but what the crew told you. "
                  "Do you want me to hook him up?"},
  debrief_note=(
    "Until an action carrying the monitor capability is taken, every cell on the monitor reads a "
    "dash and there is no heartbeat. That is a property of the simulator that mirrors the "
    "department: nobody knows the rate is 160 and irregular until somebody puts leads on him. In a "
    "case whose entire management hinges on a rate and a rhythm, attaching the monitor is not "
    "housekeeping. It is the first diagnostic act, and it is scored as one.")))

add(A("insert_iv", tag=CRIT_ALWAYS, flags=["iv_access"],
  debrief_note=(
    "Every intravenous drug in this case is gated behind a line, which is the sequence teaching "
    "the prerequisite exists for rather than an obstacle. Two peripheral lines in a patient who "
    "may need cardioversion, an infusion and a diuretic is better practice than one, and neither "
    "is scored here beyond the first.")))

# ------------------------------------------------------------------ oxygenation
NIV_STEPS = [
  {"vital": "oxygen_saturation", "delta": 2, "key": "niv_spo2_step1", "onset_seconds": 0,
   "while": "NOT flag intubated set"},
  {"vital": "oxygen_saturation", "delta": 2, "key": "niv_spo2_step2", "onset_seconds": 20,
   "while": "NOT flag intubated set"},
  {"vital": "oxygen_saturation", "delta": 2, "key": "niv_spo2_step3", "onset_seconds": 40,
   "while": "NOT flag intubated set"},
  {"vital": "oxygen_saturation", "delta": 2, "key": "niv_spo2_step4", "onset_seconds": 60,
   "while": "NOT flag intubated set",
   "note": (
     "Eight points of saturation, authored as four two-point steps at zero, twenty, forty and "
     "sixty seconds rather than as one jump, because the author asked for the number to climb "
     "over about a minute of game time and the engine has no way to ramp a single effect. Each "
     "step triggers the renderer's five-second interpolation, so what the resident sees is a "
     "saturation that walks up rather than one that snaps. Every one of the four is a separate "
     "key, because effects sharing a key do not stack. All four are guarded on not being "
     "intubated: the mask comes off at intubation and the ventilated phase authors its own "
     "saturation. The size and the tempo are teaching choices. No trial supports either number, "
     "and the review packet says so rather than implying the simulator is modelling alveolar "
     "recruitment.")},
]

add(A("non_invasive_positive_pressure_ventilation",
  name="Positive pressure ventilation (BiPAP/CPAP)",
  tag=[{"when": "phase is intubated", "value": "neutral"},
       {"when": "phase is presentation OR phase is respiratory_failure OR phase is rate_controlled_congested",
        "value": "critical"},
       {"when": None, "value": "recommended"}],
  flags=["on_niv"],
  prerequisites=[{"when": "NOT flag intubated set",
                  "failure_message": "He's already got a tube in and he's on the ventilator. The "
                                     "mask isn't going to do anything now.",
                  "source": "case"}],
  prompt={"deadline_seconds": 40,
          "guard": "NOT flag intubated set",
          "text": "He's working hard to breathe and his sat is low. Do you want to do something "
                  "more for his breathing? I can get CPAP or BiPAP on him.",
          "escalation": {
            "deadline_seconds": 100,
            "text": "He's still tripoding and he's still hypoxic on what he's got. I've got the "
                    "CPAP and the BiPAP both at the bedside if you want either of them on him."}},
  vital_effects=NIV_STEPS,
  debrief_note=(
    "Non-invasive positive pressure ventilation is the highest-value early intervention in acute "
    "cardiogenic pulmonary oedema and in this case it is also the intervention a learner is most "
    "likely to defer, because the rate is louder. It recruits flooded alveoli and reduces the work "
    "of breathing, and by raising intrathoracic pressure it reduces preload and left ventricular "
    "transmural pressure, which is afterload reduction by mechanical means. Continuous and bilevel "
    "positive pressure are one button here because they are one decision: 3CPO found no difference "
    "between the modes in mortality or intubation rate, and bilevel is often preferred when the "
    "patient is tiring and hypercapnic, as this one is on his venous gas. Be honest about the "
    "evidence. Meta-analyses report reductions in intubation and mortality against standard oxygen "
    "therapy; 3CPO, the largest randomised trial, found no difference in seven-day mortality or "
    "intubation rate. The strongest defensible claim is faster symptomatic and physiological "
    "improvement, with intubation avoidance supported by meta-analytic but not by single-trial "
    "evidence. The historical concern that bilevel increased myocardial infarction has not been "
    "borne out."),
  references=[
    "Gray A, Goodacre S, Newby DE, Masson M, Sampson F, Nicholl J; 3CPO Trialists. Noninvasive "
    "ventilation in acute cardiogenic pulmonary edema. N Engl J Med. 2008;359(2):142-51. "
    "[UNVERIFIED in this pack, confirm before release]",
    "Berbenetz N, Wang Y, Brown J, et al. Non-invasive positive pressure ventilation (CPAP or "
    "bilevel NPPV) for cardiogenic pulmonary oedema. Cochrane Database Syst Rev. 2019;4:CD005351. "
    "[UNVERIFIED in this pack, confirm before release]"]))

O2_GUARD = "NOT flag on_niv set AND NOT flag intubated set"
add(A("nasal_cannula_oxygen", tag=RECOMMENDED, flags=["supplemental_o2"],
  vital_effects=[{"vital": "oxygen_saturation", "delta": 3, "key": "supplemental_o2_spo2",
                  "while": O2_GUARD,
                  "note": ("Three points, and it shares a key with the non-rebreather so the two "
                           "cannot be stacked into a gain neither would produce. Guarded off once "
                           "positive pressure is on, because the cannula comes off when the mask "
                           "goes on and the two are not additive. Deliberately not enough: a "
                           "resident who reaches for oxygen and watches the number go from 88 to "
                           "91 has learned that oxygen treats hypoxaemia and not the flooded "
                           "alveoli causing it.")}],
  debrief_note=(
    "Reasonable and insufficient. Supplemental oxygen corrects some of the hypoxaemia and does "
    "nothing about the water in the alveoli, the work of breathing, or the ventricular filling "
    "time. It is not a wrong action and it is not a substitute for positive pressure. Note also "
    "that oxygen has no benefit in a patient who is not hypoxaemic; this one is, so it is "
    "indicated here on that ground alone.")))

add(A("non_rebreather_mask", tag=RECOMMENDED, flags=["supplemental_o2"],
  vital_effects=[{"vital": "oxygen_saturation", "delta": 5, "key": "supplemental_o2_spo2",
                  "while": O2_GUARD,
                  "note": "Same key as the nasal cannula, so the most recent of the two wins and "
                          "neither stacks with positive pressure."}],
  debrief_note=(
    "Corrects more of the hypoxaemia than a cannula and still leaves the mechanism untreated. The "
    "reason to know this is that a saturation restored by a high fraction of inspired oxygen can "
    "make a tiring patient look better on the monitor than he is at the bedside. The respiratory "
    "rate and the work of breathing are the numbers to watch here, not the saturation.")))

# ------------------------------------------------------------------ intubation chain
add(A("intubate_rapid_sequence",
  tag=[{"when": "phase is respiratory_failure", "value": "recommended"},
       {"when": None, "value": "discouraged"}],
  flags=["intubated"],
  follow_ups_triggered=["post_intubation_sedation", "post_intubation_cxr"],
  debrief_note=(
    "Appropriate for a patient who has already failed or cannot tolerate non-invasive support, and "
    "premature in a man who is awake, protecting his airway, and has not yet had a mask on his "
    "face. Most patients in acute cardiogenic pulmonary oedema who are intubated are intubated "
    "because positive pressure was started too late. Two specific hazards worth naming before you "
    "do it in this patient: induction removes the endogenous sympathetic drive that a poorly "
    "contracting ventricle is leaning on, and positive pressure ventilation reduces venous return, "
    "so the blood pressure after the tube is frequently much lower than the blood pressure before "
    "it. This case does not model that collapse, which is a simplification and not a claim that it "
    "does not happen.")))

for cid, fl, nm in [("etomidate_bolus", "sedation_given", None),
                    ("ketamine_bolus", "sedation_given", None),
                    ("midazolam_bolus", "sedation_given", None),
                    ("propofol_bolus", "sedation_given", None),
                    ("rocuronium_bolus", "paralytic_given", None),
                    ("succinylcholine_bolus", "paralytic_given", None)]:
    add(A(cid, tag=RECOMMENDED, flags=[fl],
      debrief_note=(
        "Induction and paralysis are prerequisites of intubation in this simulator, which is the "
        "sequence teaching rather than a scoring opportunity. Agent choice matters in this patient: "
        "he has a poorly contracting ventricle and is depending on his own adrenergic tone, so an "
        "agent with less haemodynamic cost is the safer choice and a large dose of any of them is "
        "not." if fl == "sedation_given" else
        "A paralytic is a prerequisite of intubation here. It creates an obligation rather than "
        "discharging one: a paralysed patient who is not sedated is awake, aware and unable to "
        "signal, which is why post-intubation sedation is tracked as a follow-up.")))

for cid in ("propofol_infusion", "ketamine_infusion", "fentanyl_bolus"):
    add(A(cid, tag=RECOMMENDED, flags=["post_intubation_sedation_running"],
      debrief_note=(
        "Discharges the post-intubation sedation and analgesia obligation. Choose with the blood "
        "pressure in mind: this patient's cardiac output is rate and preload sensitive and a "
        "propofol infusion in particular will drop his pressure.")))

add(A("preoxygenate_for_intubation", tag=RECOMMENDED, flags=["preoxygenated"],
  debrief_note=("Good practice, and in this patient the preoxygenation device of choice is the "
                "positive pressure he should already be on.")))
add(A("position_for_intubation", tag=RECOMMENDED, flags=[],
  debrief_note="Good practice. Sitting a patient in pulmonary oedema flat is poorly tolerated."))

# ------------------------------------------------------------------ electricity
add(A("place_pads_for_monitoring", tag=RECOMMENDED, flags=["pacing_pads_placed"],
  debrief_note=(
    "Sensible in any patient in a tachyarrhythmia, because it is the difference between deciding "
    "to cardiovert and being able to. It commits you to nothing.")))

add(A("synchronized_cardioversion", tag=DISCOURAGED, flags=["cardioverted"],
  prerequisites=[{"when": "flag sedation_given set",
                  "failure_message": "He's wide awake and talking to us. Do you want to give him "
                                     "something before we shock him?",
                  "source": "case"}],
  follow_ups_triggered=["anticoagulation_after_cardioversion"],
  debrief_note=(
    "Immediate synchronised cardioversion is the right answer for atrial fibrillation with a rapid "
    "ventricular response causing hypotension, ischaemic chest pain, acute heart failure "
    "attributable to the rate, or altered mental status. This patient has none of those in the "
    "form that mandates electricity: his systolic pressure is 132, he is awake and oriented, and "
    "he has no severe chest pain. The heart failure argument is the one worth arguing about, "
    "because he does have pulmonary oedema and the rate is plausibly driving it, and a reviewer "
    "who wants to defend electricity here has a case to make. Two things weigh against it. The "
    "duration of the arrhythmia is unknown and longer than forty-eight hours cannot be excluded, "
    "so cardioversion without anticoagulation or a transoesophageal echocardiogram carries a "
    "thromboembolic risk that is not trivial. And cardioversion of an arrhythmia driven by an "
    "underlying decompensation tends not to hold. It is tagged discouraged rather than harmful "
    "because it is a defensible decision made on incomplete reasoning, not a lethal one."),
  references=[
    "Joglar JA, Chung MK, Armbruster AL, et al. 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis "
    "and Management of Atrial Fibrillation. Circulation. 2023;148(9):e1-e156. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("unsynchronized_cardioversion", tag=DISCOURAGED, flags=[],
  debrief_note=(
    "Unsynchronised shock delivered to an organised rhythm with a palpable pulse risks inducing "
    "ventricular fibrillation by landing the shock on a T wave. If the decision is to cardiovert "
    "atrial fibrillation, the shock is synchronised. This is a button-selection error rather than "
    "a reasoning error, and it is the reason the sync button exists.")))

# ------------------------------------------------------------------ rate control
# What the nurse says the moment any rate-controlling drug goes in. It is a nurse_alert
# rather than an ordinary narration, so it is coloured and it goes into the running chart:
# a resident deciding thirty seconds later whether the drug has failed needs to be able to
# find this line again, and by then it has scrolled off the nurse's banner.
#
# It is load-bearing in this case rather than decorative. The rate does not come fully
# under control until a second dose, so a resident who reads a partial response as a
# failed drug is being set up to conclude the wrong thing about the agent rather than the
# right thing about the dose.
RATE_CONTROL_ALERT = "These agents can take a bit of time to kick in."

# Shared by every route to rate control, so the four never stack with each other. The
# first dose moves the number and does not change the case; that is what a vital effect
# is for. The second dose sets a flag, and the flag is what the phases read.
RATE_CONTROL_HR_EFFECTS = [
  {"vital": "heart_rate", "delta": -22, "key": "rate_control_hr_partial",
   "while": "phase is presentation OR phase is breathing_supported OR phase is respiratory_failure",
   "note": (
     "The partial response to a single dose. Twenty-two beats off the phase baseline, so "
     "a resident who gives one dose and watches sees 160 become 138 and stay there. That "
     "is the point: the drug worked, and the patient is still in a rapid ventricular "
     "response, and the answer is another dose rather than another drug. Guarded on the "
     "three phases where the rate is not already carried by the phase itself, because in "
     "the rate-controlled and stabilised phases the authored number is the controlled one "
     "and this would subtract from it twice. Twenty-two is a teaching choice.")},
  {"vital": "heart_rate", "delta": -13, "key": "rate_control_hr_in_failure",
   "while": "phase is respiratory_failure AND flag rate_control_adequate set",
   "note": (
     "One vitals block per phase, and respiratory failure is reached by two routes. The "
     "authored 166 is the untreated patient tiring; a patient who got there with two doses "
     "of a nodal blocker on board reads 166 minus 22 minus 13, about 131, which is a "
     "rate-controlled patient with a sympathetic surge rather than an untreated one. It is "
     "a workaround for the schema rather than physiology, and the review packet says so.")},
]

# Two pushes, not one. Flags are otherwise binary and permanent and authoring section 15
# tells you not to build a case that depends on redosing; this is the exception the
# mechanic was added for. All four routes share one counter, so a resident who gives
# metoprolol and then amiodarone has made two attempts at nodal blockade and is credited
# with two, which is the clinically right reading and not merely the convenient one.
RATE_CONTROL_REPEAT = [{"flag": "rate_control_adequate", "after_administrations": 2,
                        "counter": "rate_control_doses"}]

add(A("digoxin_bolus",
  tag=CRIT_ALWAYS, flags=["rate_control_given"],
  expectation_label="Rate control for atrial fibrillation (digoxin, amiodarone or metoprolol)",
  nurse_alert=RATE_CONTROL_ALERT,
  prerequisites=[PRE_IV],
  prompt={"deadline_seconds": 190,
          "guard": "NOT flag rate_control_given set",
          "text": "His rate's still up and it's all over the place. Do you want to give him "
                  "something to slow it down? I can draw up digoxin, amiodarone or metoprolol."},
  vital_effects=RATE_CONTROL_HR_EFFECTS,
  flags_set_repeat=RATE_CONTROL_REPEAT,
  follow_ups_triggered=["second_rate_control_dose"],
  debrief_note=(
    "This entry stands for the act of rate control rather than for one drug: digoxin, amiodarone "
    "and metoprolol are bound together, any of the three satisfies the critical action, and all "
    "three carry this note. That is deliberate, because the defensible answer here is a strategy "
    "rather than a named agent, and it should respond to the patient in front of you.\n\n"
    "Why not diltiazem, which is the reflex answer for atrial fibrillation with a rapid "
    "ventricular response: non-dihydropyridine calcium channel blockers are negatively inotropic, "
    "and the 2023 ACC/AHA/ACCP/HRS atrial fibrillation guideline advises against them in patients "
    "with significant left ventricular systolic dysfunction for that reason. Once the POCUS shows "
    "an ejection fraction of 30 to 35 percent, that recommendation applies to this patient.\n\n"
    "Digoxin is the most comfortable choice in decompensated heart failure with reduced ejection "
    "fraction because it slows atrioventricular conduction without negative inotropy, and it is "
    "the least satisfying because its onset is slow, its therapeutic window is narrow, and it "
    "works poorly against high sympathetic tone. Amiodarone is reasonable when nodal blockade is "
    "ineffective or contraindicated and is widely used in decompensated and critically ill "
    "patients; it is not a benign drug and it carries a real chance of chemical cardioversion, "
    "which matters in a patient who is not anticoagulated and whose arrhythmia duration is "
    "unknown. A carefully selected, low-dose beta blocker is defensible once oxygenation is "
    "supported and the haemodynamics permit it, and is the least forgiving of the three in a "
    "patient with active pulmonary oedema, because beta blockade in acute decompensation removes "
    "compensation as well as rate. Aggressive beta blockade in this patient is not the goal.\n\n"
    "On the target: guideline evidence supports a lenient resting rate of under 110 beats per "
    "minute in many patients with atrial fibrillation, derived largely from RACE II, which "
    "enrolled patients with permanent atrial fibrillation rather than acutely decompensated ones. "
    "The optimal target in acute decompensated heart failure with reduced ejection fraction is "
    "less certain, and the endpoint that matters here is clinical response rather than a number."),
  references=[
    "Joglar JA, Chung MK, Armbruster AL, et al. 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis "
    "and Management of Atrial Fibrillation. Circulation. 2023;148(9):e1-e156. "
    "[UNVERIFIED in this pack, confirm before release]",
    "Van Gelder IC, Groenveld HF, Crijns HJGM, et al. Lenient versus strict rate control in "
    "patients with atrial fibrillation (RACE II). N Engl J Med. 2010;362(15):1363-73. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("diltiazem_bolus", tag=[
    {"when": "study ultrasound_cardiac resulted", "value": "discouraged"},
    {"when": None, "value": "discouraged"}],
  flags=["rate_control_given", "ccb_given"],
  prerequisites=[PRE_IV],
  nurse_alert=RATE_CONTROL_ALERT,
  flags_set_repeat=RATE_CONTROL_REPEAT,
  follow_ups_triggered=["second_rate_control_dose"],
  vital_effects=[
    {"vital": "systolic_bp", "delta": -20, "key": "ccb_systolic", "onset_seconds": 15,
     "note": ("Twenty points of systolic pressure, coming on over fifteen seconds and not wearing "
              "off inside this case. This is the negative inotropy and the vasodilation made "
              "visible, and it is deliberately modest: the author's instruction was that a "
              "learner who gives diltiazem before knowing the ejection fraction must not be "
              "punished with a dramatic collapse, because the realistic version of this error is "
              "a patient whose numbers look acceptable while the drug is doing the wrong thing. "
              "Twenty points is a teaching choice, not a measured quantity.")},
    {"vital": "diastolic_bp", "delta": -10, "key": "ccb_diastolic", "onset_seconds": 15}]
    + RATE_CONTROL_HR_EFFECTS,
  debrief_note=(
    "This is the decision the case is built around, and the tag is discouraged rather than harmful "
    "on purpose.\n\n"
    "Giving diltiazem on arrival, to a man in atrial fibrillation with a rapid ventricular "
    "response, a systolic pressure of 132 and no known cardiomyopathy, is a defensible first move "
    "and is what most guidelines would support for that patient as described. It is scored as a "
    "deduction rather than a failure because the ejection fraction was knowable at the bedside in "
    "under a minute and had not been looked for. The lesson is not that you should have known; it "
    "is that you could have.\n\n"
    "Continuing it after the POCUS shows an ejection fraction of 30 to 35 percent is the actual "
    "error, and it is a specific and common one: the drug produced exactly the effect that was "
    "asked of it, the rate came down, and it is still the wrong drug for the disease underneath. "
    "The 2023 ACC/AHA/ACCP/HRS guideline advises avoiding non-dihydropyridine calcium channel "
    "blockers in patients with significant left ventricular systolic dysfunction, because their "
    "negative inotropy reduces stroke volume in a ventricle that has none to spare. Watch what "
    "happened to the blood pressure on your monitor after you gave it.\n\n"
    "A drug that produces the physiological effect you wanted can still be the wrong treatment for "
    "the patient's underlying disease. That is the transferable point, and it is worth more than "
    "the drug name."),
  references=[
    "Joglar JA, Chung MK, Armbruster AL, et al. 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis "
    "and Management of Atrial Fibrillation. Circulation. 2023;148(9):e1-e156. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("adenosine_bolus", tag=DISCOURAGED, flags=[], prerequisites=[PRE_IV],
  debrief_note=(
    "Adenosine does not treat atrial fibrillation. It blocks the atrioventricular node for a few "
    "seconds, which terminates re-entrant tachycardias that use the node as part of the circuit "
    "and does nothing durable to an atrial rhythm that does not. Its legitimate use in an "
    "undifferentiated narrow-complex tachycardia is diagnostic, to slow conduction long enough to "
    "see the atrial activity underneath, and that question is already answered here: the rhythm is "
    "irregularly irregular with no P waves. It also causes a period of asystole that is "
    "unpleasant in a patient who is already hypoxaemic and frightened.")))

add(A("propranolol_bolus", tag=DISCOURAGED, flags=["rate_control_given"], prerequisites=[PRE_IV],
  nurse_alert=RATE_CONTROL_ALERT,
  flags_set_repeat=RATE_CONTROL_REPEAT,
  follow_ups_triggered=["second_rate_control_dose"],
  vital_effects=RATE_CONTROL_HR_EFFECTS,
  debrief_note=(
    "Non-selective beta blockade with a long-acting agent is the least controllable way to slow "
    "this patient. If a beta blocker is the chosen strategy, a short-acting and titratable one is "
    "the safer route in a ventricle whose function you have only just measured. The flag is set, "
    "so the rate does come down, which is the point: it works and it is still not the choice to "
    "make.")))

add(A("esmolol_drip", tag=DISCOURAGED, flags=["rate_control_given"], prerequisites=[PRE_IV],
  nurse_alert=RATE_CONTROL_ALERT,
  flags_set_repeat=RATE_CONTROL_REPEAT,
  follow_ups_triggered=["second_rate_control_dose"],
  vital_effects=RATE_CONTROL_HR_EFFECTS,
  debrief_note=(
    "The argument for esmolol is that it is titratable and short-acting, so if beta blockade is "
    "poorly tolerated it can be withdrawn in minutes, which is a real advantage in a patient whose "
    "ventricle you do not trust. The argument against it here is that this patient has active "
    "pulmonary oedema and beta blockade in acute decompensation removes compensation along with "
    "rate. Reasonable clinicians differ. It is tagged discouraged rather than recommended because "
    "in a patient at a saturation of 88 percent with diffuse B-lines it is not the first thing to "
    "reach for, and because there are two agents on the menu with a better risk profile in this "
    "specific physiology.")))

add(A("procainamide_drip", tag=DISCOURAGED, flags=[], prerequisites=[PRE_IV],
  debrief_note=(
    "Procainamide is a rhythm-control agent, not a rate-control agent, and it is specifically "
    "avoided in structural heart disease and reduced systolic function because of its negative "
    "inotropic and proarrhythmic effects. Its usual place in the atrial fibrillation algorithm is "
    "pre-excited atrial fibrillation, which this is not: the QRS is narrow and there is no delta "
    "wave.")))

add(A("amiodarone_bolus_infusion", tag=CRIT_ALWAYS, flags=["rate_control_given"],
  binding_note="Covered by digoxin_bolus. Present as its own case action only so the binding is "
               "explicit; the engine takes its tag, flags and note from the covering action."))
ACTIONS.pop()   # covered entries must NOT be their own case action; coverage does this

# ------------------------------------------------------------------ heart failure
add(A("furosemide_40_mg_iv", tag=CRIT_ALWAYS, flags=["diuretic_given"],
  prerequisites=[PRE_IV],
  prompt={"deadline_seconds": 160,
          "guard": "NOT flag diuretic_given set",
          "text": "His legs are swollen up past the ankle and his neck veins are up. Do you want "
                  "to give him a diuretic?"},
  no_vital_effect_note=(
    "Deliberate, and it is the author's explicit instruction. Furosemide carries no vital effect "
    "at all in this case, so a resident who gives the diuretic and then watches the saturation "
    "sees nothing move. What it does change is the lung: the B-lines on the repeat ultrasound and "
    "the crackles on auscultation both improve once it is given, and neither of those is on the "
    "monitor. The lesson is where to look for the response, not that the drug does nothing."),
  debrief_note=(
    "He is genuinely volume overloaded and not only redistributed: bilateral pitting oedema, a "
    "jugular venous pressure of about 12 cm, a plethoric inferior vena cava, and diffuse B-lines. "
    "He needs diuresis, and this is a critical action.\n\n"
    "Two things about it are worth saying carefully. The first is dose. He is diuretic-naive, so a "
    "conventional starting dose is reasonable, and the usual rule of two to two and a half times "
    "the home oral dose does not apply to a patient who takes none. The DOSE trial found no "
    "significant difference in its co-primary endpoints between high and low dose or between bolus "
    "and infusion, with better symptom relief on secondary measures in the high-dose arm at the "
    "cost of transient rises in creatinine, so dose is a reasoned choice rather than a rule.\n\n"
    "The second is what the diuretic is treating and how fast. It acts on the accumulated sodium "
    "and water, over tens of minutes to hours. Positive pressure acts on the alveoli that are "
    "flooded right now, over minutes. Rate control gives the ventricle time to fill, over minutes. "
    "In this case the diuretic is necessary and it is not the thing that changes the next ten "
    "minutes, which is why the monitor does not move when you give it. Look at the lung, not at "
    "the saturation."),
  references=[
    "Felker GM, Lee KL, Bull DA, et al. Diuretic strategies in patients with acute decompensated "
    "heart failure (DOSE). N Engl J Med. 2011;364(9):797-805. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("magnesium_sulfate_bolus", tag=RECOMMENDED, flags=["magnesium_given"],
  prerequisites=[PRE_IV],
  debrief_note=(
    "His magnesium is 1.6 mg/dL. Correcting it is straightforward, cheap and safe, and it is worth "
    "doing for two reasons: magnesium is a cofactor for the sodium-potassium pump so hypokalaemia "
    "and hypomagnesaemia travel together and neither corrects properly while the other is low, and "
    "intravenous magnesium has been reported to improve rate control and increase conversion when "
    "added to standard atrioventricular nodal blockade in rapid atrial fibrillation. The evidence "
    "for that second claim rests on small randomised trials and a meta-analysis of them, not on a "
    "large definitive trial, so it is a reasonable adjunct rather than a core therapy.\n\n"
    "AUTHOR NOTE, and this needs your decision. Your brief bundled correcting the hypomagnesaemia "
    "into critical action four alongside the loop diuretic. It is tagged recommended here rather "
    "than critical, because the set of critical actions a phase expects is computed once on entry "
    "to that phase, so a tag that only becomes critical after the magnesium level results can "
    "never appear in the missed list, and an unconditionally critical tag tells a resident who "
    "never had reason to suspect hypomagnesaemia that they missed a critical action. If you want "
    "it critical, that is a one-line change and the review packet says where."),
  references=[
    "Bouida W, Beltaief K, Msolli MA, et al. Low-dose magnesium sulfate versus high dose in the "
    "early management of rapid atrial fibrillation (LOMAGHI). Acad Emerg Med. 2019;26(2):183-91. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("potassium_chloride_kcl", tag=RECOMMENDED, flags=[],
  debrief_note=("His potassium is 3.7 mmol/L, which is within the reference range and at the lower "
                "end of where you would want it in a patient in a new tachyarrhythmia. "
                "Supplementing is defensible and is not scored here. Note that potassium will not "
                "correct properly while the magnesium is low.")))

add(A("nitroglycerin_drip", tag=DISCOURAGED, flags=[], prerequisites=[PRE_IV],
  debrief_note=(
    "Nitrates are the pharmacological priority in hypertensive acute cardiogenic pulmonary oedema, "
    "where a systolic pressure of 180 or more means most of the oedema is redistribution against "
    "afterload. That is a different patient from this one. This man's systolic pressure is 132, so "
    "there is little afterload to unload and a meaningful chance of dropping a pressure that is "
    "already only adequate, in a ventricle that is preload dependent and filling badly because of "
    "the rate. It is not absurd and it is not the treatment this presentation is asking for. "
    "Recognising which pulmonary oedema phenotype is in front of you is the transferable skill.")))

add(A("nitroglycerin_sublingual", tag=DISCOURAGED, flags=[],
  debrief_note=("Same reasoning as the infusion. He is not hypertensive, so there is little to "
                "unload and a pressure to lose.")))

add(A("dobutamine_drip", tag=DISCOURAGED, flags=[], prerequisites=[PRE_IV],
  debrief_note=(
    "Inotropes are for cardiogenic shock: a patient who is cold, underperfused and hypotensive "
    "despite adequate filling. This man is warm, alert, making urine and running a systolic "
    "pressure of 132. Giving an inotrope to a normotensive, well-perfused patient in atrial "
    "fibrillation buys nothing and costs something specific, because beta-1 agonism increases "
    "atrioventricular nodal conduction and can accelerate the ventricular response you are trying "
    "to slow, as well as raising myocardial oxygen demand and lowering the arrhythmia threshold. "
    "A reduced ejection fraction on ultrasound is not by itself an indication for inotropy.")))

add(A("norepinephrine_drip", tag=DISCOURAGED, flags=[], prerequisites=[PRE_IV],
  debrief_note=("He is not hypotensive. A vasopressor in a patient with a systolic pressure of 132 "
                "raises afterload against a failing ventricle and treats a problem he does not "
                "have. If his pressure falls later, the question to ask first is what you gave him.")))

# ------------------------------------------------------------------ anticoagulation
add(A("apixaban", tag=CRIT_ALWAYS, flags=["anticoagulated"],
  expectation_label="Anticoagulation for atrial fibrillation (apixaban, enoxaparin or heparin)",
  prompt={"deadline_seconds": 215,
          "guard": "NOT flag anticoagulated set",
          "text": "Pharmacy is asking whether you want him started on anything for stroke "
                  "prevention while he's in this rhythm."},
  debrief_note=(
    "This entry stands for the act of anticoagulating rather than for one agent: apixaban, "
    "enoxaparin and a heparin infusion are bound together and any of the three satisfies the "
    "critical action.\n\n"
    "The risk assessment first. Counting CHA2DS2-VASc for this man: hypertension one, age 65 to 74 "
    "one, diabetes one, and vascular disease one on the basis of documented coronary artery "
    "disease, which gives four. Whether the vascular disease point applies turns on how the "
    "coronary disease is documented, and a reviewer who counts three rather than four reaches the "
    "same decision, because either score is comfortably above the threshold at which "
    "anticoagulation is recommended for a man. There is nothing in his history that "
    "contraindicates it.\n\n"
    "On the choice of agent. A direct oral anticoagulant is preferred for non-valvular atrial "
    "fibrillation, is what he will go home on, and can be started in the department. A heparin "
    "infusion is a reasonable choice when the plan may include cardioversion or an early "
    "procedure, when renal function is uncertain, or when the admitting team wants something they "
    "can switch off; its disadvantage is that it needs monitoring and it delays the drug he will "
    "actually take. Enoxaparin is a reasonable bridge with the same caveats about renal function "
    "and less flexibility than an infusion. All three are accepted here and the choice is worth "
    "articulating rather than defaulting.\n\n"
    "The duration of his atrial fibrillation is unknown. He noticed it yesterday afternoon, which "
    "is when he noticed it and not necessarily when it started, and that uncertainty is the reason "
    "the anticoagulation question and the cardioversion question cannot be separated."),
  references=[
    "Joglar JA, Chung MK, Armbruster AL, et al. 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis "
    "and Management of Atrial Fibrillation. Circulation. 2023;148(9):e1-e156. "
    "[UNVERIFIED in this pack, confirm before release]"]))

add(A("aspirin", tag=DISCOURAGED, flags=[],
  debrief_note=(
    "Aspirin is not stroke prophylaxis for atrial fibrillation. This is one of the most durable "
    "wrong answers in emergency medicine and it survives because aspirin is an antithrombotic and "
    "the stroke is a thrombus, so the reasoning feels sound. It is not: the thrombus forms in a "
    "fibrillating left atrial appendage by stasis rather than by platelet activation on a ruptured "
    "plaque, and antiplatelet therapy is substantially less effective than anticoagulation for "
    "preventing it while carrying its own bleeding risk. Current guidelines do not recommend "
    "aspirin monotherapy for stroke prevention in atrial fibrillation. Aspirin has a separate and "
    "legitimate indication if you think this is an acute coronary syndrome; if that is why you "
    "gave it, say so, because it is a different decision.")))

add(A("clopidogrel", tag=DISCOURAGED, flags=[],
  debrief_note="Same reasoning as aspirin. Antiplatelet therapy is not anticoagulation."))

# ------------------------------------------------------------------ fluids: the halting act
add(A("normal_saline_1l_bolus", name="Crystalloid bolus",
  tag=[{"when": "phase is stabilized OR phase is intubated", "value": "discouraged"},
       {"when": None, "value": "harmful"}],
  flags=["fluid_given"],
  prerequisites=[PRE_IV],
  halt_reason=(
    "You gave a litre of crystalloid to a man with an ejection fraction of 30 to 35 percent whose "
    "lungs were already full of fluid and who was hypoxaemic on room air. The extra preload went "
    "straight into the alveoli, his saturation fell away, and he required emergency intubation for "
    "a pulmonary oedema you had made worse."),
  debrief_note=(
    "The reasoning that leads here is worth naming because it is not stupid: the patient is "
    "tachycardic, tachycardia is often hypovolaemia, and a fluid challenge is the reflex. In this "
    "patient the tachycardia is an arrhythmia and the ventricle is failing, so volume has nowhere "
    "to go but the lungs. Every route to a crystalloid bolus reaches the same harm, so this tag "
    "covers the whole equivalence group: saline and Ringer's, a litre and 500 mL.\n\n"
    "The tag is phase-dependent. Once he is on positive pressure with a controlled rate and "
    "diuresing, a small fluid challenge is wrong rather than lethal, and it is tagged discouraged "
    "there. Before that it kills him. The general point: in a hypoxaemic tachycardic patient, find "
    "out whether the lungs are wet before you fill them. The lung ultrasound takes under a minute "
    "and answers the question.")))

# ------------------------------------------------------------------ investigations
add(A("ecg_12_lead", tag=CRIT_ALWAYS, flags=[],
  debrief_note=(
    "Mandatory, and for three separate questions rather than one. What is the rhythm: irregularly "
    "irregular, no organised atrial activity, so atrial fibrillation and not sinus tachycardia, "
    "atrial flutter with variable block, or multifocal atrial tachycardia. Is the QRS narrow and "
    "is there pre-excitation, because pre-excited atrial fibrillation is a different disease with "
    "a different and nearly opposite drug list. And is there an acute coronary occlusion driving "
    "the whole presentation, which would redirect the case entirely. Here there is none: the "
    "lateral ST depression is rate-related and it should be re-examined once the rate is "
    "controlled, which is a repeat tracing worth ordering.")))

add(A("ultrasound_cardiac", tag=CRIT_ALWAYS, flags=[],
  prompt={"deadline_seconds": 130,
          "text": "The probe's on the machine at the bedside if you want it. We don't know "
                  "anything about this man's heart."},
  debrief_note=(
    "This is the pivot of the case and it takes under a minute. A visually estimated ejection "
    "fraction of 30 to 35 percent with global hypokinesis converts a routine atrial fibrillation "
    "with a rapid ventricular response into a different problem with a different drug list: it "
    "rules out the calcium channel blocker, it puts digoxin and amiodarone at the front, it "
    "explains the pulmonary oedema, and it changes the disposition.\n\n"
    "Two honest caveats. A visual estimate is exactly that, and a formal echocardiogram is the "
    "measurement; for the decision in front of you, the categorical answer, whether systolic "
    "function is normal or clearly reduced, is what matters and a visual estimate answers it "
    "reliably enough in trained hands. And this study cannot tell you which came first. A "
    "sustained rapid ventricular response can itself produce a tachycardia-induced cardiomyopathy, "
    "and a pre-existing cardiomyopathy can precipitate atrial fibrillation. You do not have to "
    "resolve that in the department, and the treatment is the same either way.")))

add(A("ultrasound_lung", tag=CRIT_ALWAYS, flags=[],
  debrief_note=(
    "Diffuse bilateral B-lines in more than two zones per side, with no focal consolidation, is "
    "interstitial pulmonary oedema. In an undifferentiated breathless patient this single finding "
    "separates cardiogenic pulmonary oedema from an obstructive exacerbation and from pneumonia "
    "faster and more accurately than a portable chest radiograph, and it does it before the film "
    "is taken. Paired with the cardiac view it also tells you, in the same minute, that this "
    "patient must not have a fluid bolus. Repeat it after treatment: the B-lines are one of the "
    "few things in this case that visibly respond to the diuretic.")))

add(A("xr_chest", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Reasonable and slower than the probe. It confirms the interstitial oedema, gives you a cardiac "
    "silhouette and effusions, and mostly serves to exclude the things the ultrasound cannot "
    "exclude as confidently, such as a large consolidation. It should not delay treatment and it "
    "should not be the study you wait for before deciding this patient has pulmonary oedema.")))

add(A("troponin_t", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Worth sending, and the single value is nearly uninterpretable on its own. A modest elevation "
    "in a patient at a ventricular rate of 160 with a poorly contracting ventricle is a demand "
    "pattern: supply-demand mismatch from shortened diastole and raised wall stress, which is type "
    "2 myocardial injury and not acute coronary occlusion. What distinguishes the two is the "
    "trajectory over one to three hours and the clinical picture, not the first number. Treat this "
    "result as a reason to repeat it on the ward rather than as a reason to activate the "
    "laboratory, unless the ECG or the story changes your mind.")))

add(A("pro_bnp", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Supportive rather than diagnostic. A markedly raised natriuretic peptide in a breathless "
    "patient makes heart failure much more likely and does not establish it, and atrial "
    "fibrillation raises it on its own through atrial wall stress, so the number in front of you "
    "has two contributions you cannot separate. It is most useful when it is low, because a low "
    "value in an untreated patient argues strongly against acute heart failure. Here the bedside "
    "ultrasound answered the question faster and more specifically.")))

add(A("basic_chemistry_chem_7", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Baseline renal function before a diuretic and an anticoagulant, and the potassium and "
    "bicarbonate that matter in a new arrhythmia. His creatinine is 1.0, which is worth knowing "
    "because it is the number the choice of anticoagulant dose depends on.")))

add(A("magnesium_level", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Sent because it is abnormal here and because it is one of the few reversible contributors to "
    "a new tachyarrhythmia that costs nothing to correct. It is not routinely on the basic "
    "chemistry panel, so it has to be asked for deliberately.")))

add(A("complete_blood_count_cbc", tag=RECOMMENDED, flags=[],
  debrief_note=("Normal here. Anaemia is a genuine precipitant of both high-output symptoms and "
                "decompensation, and it is worth excluding before you decide the arrhythmia is the "
                "whole story.")))

add(A("tsh", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Hyperthyroidism is a classic and eminently treatable precipitant of new atrial fibrillation, "
    "and it is missed when nobody sends the test. Normal here, which is a pertinent negative "
    "rather than a wasted test. Note the practical caveat: the result will not be back in time to "
    "change anything you do in the department, so send it and move on.")))

add(A("venous_blood_gas", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "A venous gas gives you the pH and the carbon dioxide, which is what you want to know about a "
    "patient who is tiring, without an arterial puncture. The rising carbon dioxide on this "
    "patient is the number that argues for bilevel rather than continuous positive pressure, and "
    "it is the number that changes if he is left too long.")))

add(A("lactate", tag=RECOMMENDED, flags=[],
  debrief_note=("Mildly raised. In this patient that is the work of breathing and the tachycardia "
                "rather than sepsis or mesenteric ischaemia, and it should fall as he is treated. "
                "A lactate that does not fall is worth taking seriously.")))

add(A("d_dimer", tag=DISCOURAGED, flags=[],
  debrief_note=(
    "This is a trap and it works because the reflex is strong. His pretest probability of pulmonary "
    "embolism is low: gradual onset over more than a day, an irregularly irregular rhythm with an "
    "obvious alternative explanation for every symptom, no unilateral leg swelling, no "
    "immobilisation, surgery or malignancy, and a bedside ultrasound showing a poorly contracting "
    "left ventricle with diffuse B-lines rather than a strained right ventricle with clear lungs. "
    "A D-dimer sent in that setting is very likely to be raised, because it is raised by heart "
    "failure, atrial fibrillation and being 68 years old, and the raised result then commits you to "
    "a contrast study in a man whose kidneys and volume status you have just decided to manipulate. "
    "The cost of this test is not the test.")))

add(A("ct_pulmonary_embolus", tag=DISCOURAGED, flags=[],
  debrief_note=(
    "Almost always ordered downstream of the D-dimer. It is negative, it delays treatment by the "
    "time it takes to move an unstable hypoxaemic patient out of the department, and it gives a "
    "contrast load to a man in acute heart failure. If you genuinely suspect pulmonary embolism in "
    "a patient like this, the bedside ultrasound is the first study, not the last: a dilated "
    "hypokinetic right ventricle with a small underfilled left ventricle is a different picture "
    "from the one you saw.")))

add(A("ultrasound_lower_extremity_venous", tag=DISCOURAGED, flags=[],
  debrief_note=("Negative, and it is the wrong question. His legs are symmetrically swollen, which "
                "is what bilateral venous congestion looks like, not what a deep vein thrombosis "
                "looks like.")))

add(A("urinalysis", tag=NEUTRAL, flags=[],
  debrief_note="Neither indicated nor harmful. Nothing in this presentation points at the urinary tract."))

add(A("insert_foley_catheter", tag=RECOMMENDED, flags=["foley_in"],
  debrief_note=("Reasonable once a diuretic has been given, both for the patient's comfort and "
                "because urine output is the most direct measure of whether the diuretic has "
                "worked. Not required, and it is an infection risk in a man who can use a bottle.")))

# ------------------------------------------------------------------ consults
add(A("consult_cardiology", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "The right call, and the timing matters more than the fact of it. Cardiology is not needed to "
    "start positive pressure, a diuretic or a rate-controlling drug, and calling before you have a "
    "rhythm, an ejection fraction and a plan produces a conversation nobody benefits from. Once "
    "you have those three, the questions worth asking are the rate-control agent in a newly "
    "recognised reduced ejection fraction, whether they want a rhythm-control strategy considered, "
    "and what they want done about the anticoagulation and the formal echocardiogram.")))

add(A("consult_critical_care", tag=RECOMMENDED, flags=[],
  debrief_note=(
    "Appropriate for a patient who is on non-invasive ventilation and is going to stay on it. What "
    "the receiving unit needs to be able to do is the actual disposition question in this case, "
    "and this is the conversation in which it gets answered.")))

add(A("consult_pulmonology", tag=NEUTRAL, flags=[],
  debrief_note=("Not the right team. The lung findings are cardiogenic and the treatment is "
                "cardiac.")))

# ------------------------------------------------------------------ exams
EXAM_NOTES = {
 "exam_airway": "Patent and self-maintained on arrival. The reason to check it is that it will not "
   "stay that way if the respiratory failure is left, and the transition from full sentences to "
   "single words is the finding worth returning for.",
 "exam_breath": "Work of breathing is the most sensitive bedside marker in this case and it is the "
   "one that responds first to positive pressure. Accessory muscle use, the ability to complete a "
   "sentence, and the respiratory rate tell you more about whether the treatment is working than "
   "the saturation does.",
 "exam_circ": "The pulse is the diagnosis here if you take the time to feel it. Irregularly "
   "irregular with beat-to-beat variation in volume, and a radial rate lower than the apical rate, "
   "which is the pulse deficit of atrial fibrillation: the shortest cycles do not generate enough "
   "stroke volume to reach the wrist. Peripheries are warm and capillary refill is normal, which "
   "is what tells you he is congested and still perfusing rather than in cardiogenic shock.",
 "exam_neck": "The jugular venous pressure is the single most useful bedside finding for "
   "separating cardiogenic from non-cardiogenic breathlessness, and it is elevated here at about "
   "12 cm. It is also difficult to read in a tachypnoeic patient at a rate of 160, so read it with "
   "the ultrasound view of the inferior vena cava rather than instead of it.",
 "exam_card": "Peripheral oedema is routed here by the catalog rather than to the musculoskeletal "
   "examination, which is worth knowing so you look in the right place. The auscultatory findings "
   "in fast atrial fibrillation are unreliable: an S3 is very hard to hear at 160 and a variable "
   "first heart sound is expected. The oedema does not resolve during this case, and it should "
   "not: days of accumulated fluid do not leave in ten minutes.",
 "exam_pulm": "Bibasilar crackles to the mid-zones. They improve with the diuretic and the "
   "positive pressure and they are less sensitive than the lung ultrasound, which is why the probe "
   "is a critical action and the stethoscope is not.",
 "exam_abd": "A tender, pulsatile liver edge and the absence of ascites are the abdominal signs of "
   "right-sided congestion. Worth eliciting because congestive hepatopathy explains abdominal "
   "symptoms that would otherwise start a second workup.",
 "exam_msk": "Symmetry is the point. Bilateral symmetrical oedema with no calf tenderness and no "
   "asymmetry argues against deep vein thrombosis and pulmonary embolism, which is the differential "
   "the D-dimer trap in this case is built on.",
 "exam_skin": "Warm and mildly diaphoretic, which fits sympathetic drive and work of breathing "
   "rather than shock. Cool, mottled skin in this patient would change the case completely, because "
   "it would mean he had stopped perfusing.",
 "exam_neuro": "Normal on arrival and it is the finding that matters most if it changes. A patient "
   "in respiratory failure who becomes drowsy is not settling, and in this case the drop in the "
   "Glasgow Coma Scale is the clinical sign of the rising carbon dioxide.",
 "exam_psych": "Anxiety in a hypoxaemic patient is a physical sign. It is worth recording because "
   "it is one of the things that improves visibly once positive pressure goes on, and because "
   "treating it as anxiety rather than as hypoxaemia is a recognised way to lose this patient.",
 "exam_heent": "Normal, and the negatives are the point: no thyromegaly, no lid lag, no proptosis. "
   "Hyperthyroidism is a treatable precipitant of new atrial fibrillation and this is where you "
   "look for it at the bedside while you wait for the thyroid function test that will not be back "
   "in time.",
}
for eid, note in EXAM_NOTES.items():
    add(A(eid, tag=RECOMMENDED, debrief_note=note, state_changing=False))

# ------------------------------------------------------------------ handoff
add(A("handoff_submit", name="Submit handoff", tag=NEUTRAL, flags=["handoff_submitted"],
  state_changing=True,
  debrief_note="Completion of the case. Disposition and diagnosis are scored separately below."))

FOLLOW_UPS = [
 {"id": "post_intubation_sedation",
  "triggered_by": "intubate_rapid_sequence",
  "applies_when": "flag intubated set",
  "deadline_seconds": 60,
  "satisfied_by": ["propofol_infusion", "ketamine_infusion", "fentanyl_bolus", "midazolam_bolus"],
  "nurse_prompt": "He's tubed and he's still paralysed from the induction. Do you want to write "
                  "him up for sedation and something for pain?",
  "debrief_note": (
    "A paralysed patient without sedation is awake, aware and unable to signal. The obligation is "
    "created by the intubation and cannot precede it, which is why it is a follow-up rather than a "
    "prerequisite. Choose the agent with his blood pressure in mind: his cardiac output is preload "
    "and rate sensitive and a propofol infusion will drop it.")},
 {"id": "post_intubation_cxr",
  "triggered_by": "intubate_rapid_sequence",
  "applies_when": "flag intubated set",
  "deadline_seconds": 120,
  "satisfied_by": ["xr_chest"],
  "nurse_prompt": "Do you want a film to check the tube?",
  "debrief_note": (
    "Tube position is confirmed by waveform capnography and the film is for depth and for the lung "
    "underneath it, which in this patient is worth seeing.")},
 {"id": "second_rate_control_dose",
  "triggered_by": ["digoxin_bolus", "diltiazem_bolus", "esmolol_drip", "propranolol_bolus"],
  "applies_when": "flag rate_control_given set AND NOT flag rate_control_adequate set",
  "deadline_seconds": 55,
  "satisfied_when": "flag rate_control_adequate set",
  "nurse_prompt": "He's slower than he was but he's still running fast. Do you want me to draw "
                  "up another dose?",
  "debrief_note": (
    "One dose is a trial, not a treatment. A single intravenous dose of any of the agents this "
    "case accepts produces a partial fall in the ventricular rate, and the correct response to a "
    "partial response is another dose of the same agent, not a different agent and not the "
    "conclusion that the drug failed. That is the specific error this obligation exists to catch: "
    "a resident who reads 160 becoming 138 as a failure will reach for something else, and what "
    "they reach for in atrial fibrillation with a reduced ejection fraction is usually the "
    "calcium channel blocker.\n\n"
    "It is discharged by a second dose of any of the four routes, because two attempts at "
    "atrioventricular nodal blockade is two attempts whichever drugs they were. It is not "
    "discharged by time, and it is not discharged by the first dose, which is why it is authored "
    "against a condition rather than against a list of actions: the action that would satisfy it "
    "is the action that created it.\n\n"
    "Know when to stop. If the rate is still fast after two adequate doses, that is information "
    "rather than a reason for a third: a ventricular rate that will not come down in acute "
    "decompensated heart failure is usually being driven by the decompensation, and the "
    "treatment is the pulmonary oedema and the hypoxaemia rather than more nodal blockade in a "
    "ventricle that is already struggling.")},
 {"id": "anticoagulation_after_cardioversion",
  "triggered_by": "synchronized_cardioversion",
  "applies_when": "action synchronized_cardioversion taken",
  "deadline_seconds": 90,
  "satisfied_by": ["apixaban"],
  "nurse_prompt": "You've cardioverted him. Did you want anything written up for anticoagulation?",
  "debrief_note": (
    "Cardioversion of atrial fibrillation of unknown or greater than 48 hours' duration carries a "
    "thromboembolic risk both at the moment of conversion and in the weeks afterwards, because "
    "atrial mechanical function recovers more slowly than electrical function and the stunned "
    "appendage remains a site for thrombus. Anticoagulation is indicated after cardioversion "
    "regardless of the apparent success of the shock, and for at least four weeks. This patient's "
    "arrhythmia duration is unknown, which is precisely the situation this rule exists for. Any of "
    "the three anticoagulants in this case discharges the obligation.")},
]

# ------------------------------------------------------------------ vascular access
# The catalog's default vascular-access prerequisite is satisfied by a peripheral line,
# central access or an intraosseous needle, so all three routes have to exist as case
# actions or the condition names flags nothing can set. Retaining the full catalog
# condition rather than narrowing it to a peripheral line is deliberate: a resident who
# cannot get a peripheral line in a congested arm should be able to reach for an IO and
# have every drug in the case unlock.
add(A("second_iv", tag=RECOMMENDED, flags=["iv_access"],
  debrief_note=("A second line is good practice in a patient who may need a diuretic, a "
                "rate-controlling drug and possibly sedation for cardioversion. Not scored.")))
add(A("central_venous_catheter_triple_lumen", tag=DISCOURAGED, flags=["central_access"],
  debrief_note=(
    "Central access is not indicated here and it is not free. He is not on a vasopressor, he does "
    "not need one, and he is lying at forty-five degrees because he cannot lie flat, which makes "
    "an internal jugular or subclavian line both harder and more dangerous. If peripheral access "
    "is genuinely impossible, an intraosseous needle is faster and safer for the drugs this case "
    "needs.")))
add(A("central_venous_catheter_cordis", tag=DISCOURAGED, flags=["central_access"],
  debrief_note=("Same reasoning as the triple lumen, and a large-bore introducer is a volume "
                "line in a patient who must not be given volume.")))
add(A("intraosseous_line", tag=RECOMMENDED, flags=["io_access"],
  debrief_note=(
    "A reasonable rescue if peripheral access fails, which it can in a patient with swollen, "
    "congested arms. It unlocks every intravenous drug in this case. It is uncomfortable in a "
    "conscious patient, so it is a fallback rather than a first move.")))
add(A("arterial_line", tag=NEUTRAL, flags=[],
  debrief_note=("Reasonable if he ends up intubated and on vasoactive support, and unnecessary "
                "otherwise. It is not a reason to delay anything.")))
