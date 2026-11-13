"""SWEET part 2: the action spine, tags, flags, prompts and vital effects.

Every clinical judgment here is model output awaiting a physician's signature, except the
decisions in SWEET-SEED.md section 0. Markers sit only in fields the interface strips
(authoring 10.3): an action's debrief_note.

Doses are not implemented (owner, 11 November 2026: no doses, debrief only). Every note that
names a dose says so for teaching, and nothing in the case depends on it.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

P1 = "phase is presentation"
P2 = "phase is persistent"
P3 = "phase is worsening"
P4 = "phase is peri_arrest"
P5 = "phase is responding"
P6 = "phase is stabilized"
P7 = "phase is post_induction_collapse"
P8 = "phase is ventilated"
RUNNING = P5 + " OR " + P6 + " OR " + P8            # the infusion's own phases
EARLY = P1 + " OR " + P2 + " OR " + P3          # the phases a sedative or an IM dose acts in
SICK = EARLY + " OR " + P4                       # before the infusion
TUBED = "flag intubated set"
ED_EPI = "flag epi_im_ed set"

RCUK = " [UNVERIFIED: Resuscitation Council UK anaphylaxis and refractory anaphylaxis algorithms 2021, read through search]"
JTF = " [UNVERIFIED: Shaker et al., J Allergy Clin Immunol 2020 (anaphylaxis practice parameter), read through a Cleveland Clinic Journal of Medicine summary]"
PUMPHREY = " [UNVERIFIED: Pumphrey, J Allergy Clin Immunol 2003, read through BestBETs]"
CAMPBELL = " [UNVERIFIED: Campbell et al., J Allergy Clin Immunol Pract 2015, abstract read through search]"
PALS = " [UNVERIFIED: PALS 2015 vital sign tables as reproduced by PedsCases, read through search]"
MEMORY = " [UNVERIFIED: written by a model from memory, no source opened]"

IV_LINE = "flag iv_access set OR flag central_access set OR flag io_access set"

# =====================================================================  FIRST MINUTES

act("attach_monitor", ALWAYS("critical"),
    flags_set=["monitor_on"],
    expectation_label="Monitor on",
    debrief_note=(
      "Nothing shows until the monitor is on. Read the numbers against a 12-year-old: a heart "
      "rate of 140 and a systolic of 88 are tachycardia and hypotension at his age, where "
      "hypotension starts below 90." + PALS))

act("insert_iv", [{"when": SICK, "value": "critical"}, {"when": None, "value": "neutral"}],
    flags_set=["iv_access"],
    expectation_label="IV access",
    debrief_note=("Every bolus and the infusion need a line. Either an IV or an intraosseous "
                  "line meets this. Go to the IO if the IV does not come quickly."))

act("second_iv", [{"when": P1, "value": "recommended"},
                  {"when": EARLY + " OR " + P4 + " OR " + P7, "value": "critical"},
                  {"when": None, "value": "neutral"}],
    flags_set=["iv_access", "second_line"],
    expectation_label="A second line",
    debrief_note=(
      "Two lines: one for fluid, one dedicated to the epinephrine infusion. In this case the "
      "pharmacy will not hang the infusion on his only line."))

act("intraosseous_line", ALWAYS("neutral"), flags_set=["io_access"],
    debrief_note="Counts as access for every drug and bolus. Beside an IV it is the second line.")
for cid in ("central_venous_catheter_triple_lumen", "central_venous_catheter_cordis"):
    act(cid, ALWAYS("neutral"), flags_set=["central_access"],
        debrief_note="Counts as access. Not needed in a child who has two peripheral lines.")

act("lay_back_legs_raised",
    [{"when": SICK, "value": "critical"}, {"when": P5 + " OR " + P6, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    display_name="Lay him back, legs raised",
    expectation_label="Lying flat or back, legs raised",
    flags_set=["positioned"],
    narration_override="Lying him back and lifting his legs.",
    nurse_alert="He keeps trying to sit up. I'll keep his legs up.",
    voice_phrases=["legs up", "raise his legs", "lay him back",
                   "legs raised", "trendelenburg"],
    vital_effects=[{"vital": "systolic_bp", "delta": 5, "key": "posture",
                    "while": "NOT " + TUBED,
                    "note": "Teaching choice. The owner's structure gives +4 to 6. Venous return."}],
    prompt={"deadline_seconds": 50, "guard": P1,
            "text": "He keeps trying to sit up and swing his legs off the bed. How do you want him?"},
    debrief_note=(
      "Lying flat with the legs raised keeps blood in the heart. People in anaphylactic shock "
      "have died within seconds of being sat or stood up, from a heart with nothing to pump. "
      "If he cannot breathe lying flat, sit him back with his legs raised, never upright with "
      "his legs down. The evidence is case reports and physiology." + PUMPHREY + RCUK))

act("lower_head_of_bed", ALWAYS("neutral"),
    also_satisfies=[{"id": "lay_back_legs_raised", "when": None}],
    vital_effects=[{"vital": "systolic_bp", "delta": 3, "key": "posture", "while": "NOT " + TUBED,
                    "note": "Teaching choice. Flat without the legs raised."}],
    debrief_note="Counted as lying him back. Raising the legs as well adds a little more venous return.")

# =====================================================================  EPINEPHRINE
# First ED dose (owner, 11 November 2026): kicks in at 10 seconds, fades by 120, then phase 2.
# Every later dose: 10 to 60 seconds, smaller. Separate keys, so the first dose's effect and a
# later one's never stack. In phases 4 and 7 the dose is part of a rescue and has no effect of
# its own here (the phase change carries it).
IM_WHERE = "(" + EARLY + ")"
EPI1 = [("heart_rate", 6), ("systolic_bp", 12), ("diastolic_bp", 8), ("respiratory_rate", -4), ("oxygen_saturation", 2)]
EPI2 = [("heart_rate", 4), ("systolic_bp", 8), ("diastolic_bp", 4), ("respiratory_rate", -2), ("oxygen_saturation", 1)]
def fading(tiers, key, guard, note):
    """A response that fades rather than stops: full, then two thirds, then one third, each
    tier its own key (section 16.1). tiers: [(start, end, fraction)]."""
    out = []
    for v, d in tiers[0]:
        for n, (a, b, f) in enumerate(tiers[1]):
            dd = int(round(d * f))
            if dd:
                out.append({"vital": v, "delta": dd, "key": key + v + "_" + str(n),
                            "onset_seconds": a, "duration_seconds": b, "while": guard, "note": note})
    return out


IM_EFFECTS = (
  fading((EPI1, [(10, 80, 1.0), (80, 100, 2 / 3), (100, 120, 1 / 3)]), "epi1_",
         "NOT flag epi_im_2 set AND " + IM_WHERE,
         "Teaching choice. The first ED dose acts at 10 s and fades from 80 s to nothing at 120 s (owner, 11 November 2026).") +
  fading((EPI2, [(10, 40, 1.0), (40, 50, 2 / 3), (50, 60, 1 / 3)]), "epi2_",
         "flag epi_im_2 set AND " + IM_WHERE,
         "Teaching choice. A later dose acts at 10 s and fades by 60 s, half as long (owner, 11 November 2026)."))

act("epinephrine_intramuscular",
    [{"when": P1 + " OR " + P4 + " OR " + P7, "value": "critical"},
     {"when": P2 + " AND NOT " + ED_EPI, "value": "critical"},
     {"when": P2 + " OR " + P3, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    display_name="Epinephrine (Intramuscular)",
    expectation_label="IM epinephrine, anterolateral thigh",
    flags_set=["epi_im_ed"],
    flags_set_timed=[{"flag": "epi_bridge_acting", "duration_seconds": 60},
                     {"flag": "epi_onset", "duration_seconds": 10}],
    flags_set_repeat=[{"flag": "epi_im_2", "after_administrations": 2, "counter": "epi_im"}],
    also_satisfies=[{"id": "epi_here_p4", "when": P4}, {"id": "bridge_here_p7", "when": P7}],
    vital_effects=IM_EFFECTS,
    nurse_alert=[{"when": P1 + " AND NOT " + ED_EPI, "value": "In his thigh. Let's see what it does."},
                 {"when": P2 + " OR " + P3, "value": "In. It'll buy us a little time."},
                 {"when": None, "value": "In his thigh."}],
    prompt={"deadline_seconds": 30,
            "guard": "NOT " + ED_EPI + " AND NOT " + P4 + " AND NOT " + P7,
            "text": "He's still struggling, even after the epi in the ambulance. What do you want to give him?"},
    debrief_note=(
      "The crew's dose was one dose, not completed treatment. It worked for a few minutes and "
      "wore off, which is the commonest story in anaphylaxis that comes back. Repeat it in "
      "the anterolateral thigh after 5 minutes if there is no lasting response, before any "
      "adjunct.\n\n"
      "The dose is 0.01 mg/kg of the 1 mg/mL solution, 0.4 mg for his 40 kg. US guidance caps "
      "a child's dose at 0.3 mg and UK guidance gives 0.5 mg over 12 years, so 0.3 to 0.5 mg "
      "is reasonable here, and the 0.3 mg pen is acceptable. State the weight before you "
      "order. This simulator does not take doses.\n\n"
      "Here the second dose did what the first had done: better for a minute or two, then "
      "worse. After two appropriate IM doses that is refractory anaphylaxis, and the next "
      "step is the infusion. A further IM dose while it is mixed is right and buys a little "
      "time." + RCUK + JTF))

act("epinephrine_drip",
    [{"when": P1 + " AND NOT " + ED_EPI, "value": "discouraged"},
     {"when": P1, "value": "neutral"},
     {"when": SICK + " OR " + P7, "value": "critical"},
     {"when": None, "value": "neutral"}],
    display_name="Epinephrine drip",
    expectation_label="Epinephrine infusion",
    flags_set=["epi_drip_ordered"],
    also_satisfies=[{"id": "drip_restarted", "when": "flag epi_drip_stopped set"},
                    {"id": "epi_here_p4", "when": P4}],
    prerequisites=[
      {"when": "flag monitor_on set",
       "failure_message": "I can't hang an epi drip without him on the monitor."},
      {"when": "flag second_line set OR flag iv_access set AND flag io_access set OR flag central_access set",
       "failure_message": "The fluid's in his only line. Can we get another one for the drip?"}],
    vital_effects=[],
    nurse_alert=[{"when": "flag epi_drip_stopped set", "value": "Restarting it. The bag's still up."},
                 {"when": "flag help_called set", "value": "Pharmacy's mixing it. With PICU on the way they're rushing it."},
                 {"when": None, "value": "Pharmacy's mixing it. It'll be a couple of minutes."}],
    prompt={"deadline_seconds": 30, "guard": "NOT flag epi_drip_ordered set",
            "text": "He's not picking up, even after the epi. What's next?"},
    debrief_note=(
      "The escalation for refractory anaphylaxis: the same drug, given continuously, on a pump, "
      "on its own line, with continuous monitoring, titrated to his pressure and his breathing. "
      "Not repeated IV pushes and not another vasopressor in its place.\n\n"
      "A common start is 0.1 microgram/kg/min, 4 micrograms a minute at 40 kg. UK guidance "
      "mixes 1 mg in 100 mL and starts at 0.5 to 1 mL/kg/hour, which is 0.08 to 0.17 "
      "microgram/kg/min. Follow your own protocol.\n\n"
      "It takes minutes to mix. Order it as soon as the second IM dose fails, and call for "
      "help, which in this case halved the wait. Keep giving IM doses until it runs."
      + RCUK))

act("stop_epinephrine",
    [{"when": P5 + " OR " + P6 + " OR " + P8, "value": "discouraged"}, {"when": None, "value": "neutral"}],
    flags_set=["epi_drip_stopped"],
    debrief_note=(
      "Refractory anaphylaxis needs the infusion for hours, weaned in the PICU. Stopped here, "
      "the reaction came back within minutes."))

act("epinephrine_bolus",
    [{"when": P4 + " OR " + P7, "value": "neutral"}, {"when": None, "value": "discouraged"}],
    expectation_label="IV epinephrine push",
    also_satisfies=[{"id": "epi_here_p4", "when": P4}, {"id": "bridge_here_p7", "when": P7}],
    vital_effects=[{"vital": "systolic_bp", "delta": 18, "key": "epi_push_sbp", "onset_seconds": 10, "duration_seconds": 120,
                    "note": "Teaching choice. Replaces the catalog default: the owner's structure gives +15 to 20 for 1 to 2 minutes."},
                   {"vital": "diastolic_bp", "delta": 8, "key": "epi_push_dbp", "onset_seconds": 10, "duration_seconds": 120,
                    "note": "Teaching choice."},
                   {"vital": "heart_rate", "delta": 12, "key": "epi_push_hr", "onset_seconds": 10, "duration_seconds": 120,
                    "note": "Teaching choice. The owner's structure gives +10 to 15."}],
    nurse_alert="He's saying his heart's pounding, and I'm seeing extra beats.",
    debrief_note=(
      "A small, diluted IV push lifts the pressure for a minute or two and gives palpitations "
      "and extra beats. It is not the treatment for refractory anaphylaxis, and UK guidance "
      "does not recommend IV boluses outside specialist settings while an infusion is set "
      "up. After the tube, or at the edge of arrest, a small bolus is a reasonable bridge.\n\n"
      "The dangerous version is the cardiac arrest dose, or undiluted drug, pushed into a "
      "child with a pulse. In an emergency department cohort every epinephrine overdose "
      "followed an IV bolus. This simulator does not take doses, so the button here is read "
      "as a small diluted push." + RCUK + CAMPBELL))

act("consult_critical_care",
    [{"when": P2 + " OR " + P3 + " OR " + P4 + " OR " + P7, "value": "critical"},
     {"when": None, "value": "recommended"}],
    display_name="Consult Critical Care (PICU)",
    expectation_label="PICU and senior called",
    narration_override="Paging the PICU fellow and your senior.",
    flags_set=["help_called"], state_changing=True,
    voice_phrases=["call picu", "picu", "call the picu", "page picu", "call my attending",
                   "call the attending", "call for help"],
    prompt={"deadline_seconds": 45, "guard": P2 + " OR " + P3,
            "text": "Who else do you want in here?"},
    debrief_note=(
      "Two doses and still struggling is the moment to call the senior and the PICU, and to "
      "do it while you give the next dose, not after. In this case the call halved the time "
      "to get the infusion running. In the department it brings hands, a pharmacist and an "
      "airway plan.\n\n"
      "This button stands for both the PICU team and the senior pediatric emergency physician "
      "(owner's defaults, 11 November 2026)."))

for cid in ("norepinephrine_drip", "vasopressin_drip", "phenylephrine_drip"):
    act(cid,
        [{"when": "(" + RUNNING + ") AND flag help_called set", "value": "neutral"},
         {"when": None, "value": "discouraged"}],
        debrief_note=(
          "The pressure came up a little and nothing else changed: the wheeze, the saturation "
          "and his mental state stayed where they were. Epinephrine treats every part of "
          "anaphylaxis, the airway swelling, the bronchospasm and the leak, and another "
          "vasopressor treats only the pressure. Started instead of the epinephrine infusion, "
          "it is a mistake. Added to a running epinephrine infusion with PICU involved, it is "
          "reasonable." + RCUK))

act("dopamine_drip", ALWAYS("discouraged"),
    debrief_note="Not a vasopressor for anaphylaxis. Epinephrine is the drug, as an infusion." + MEMORY)

# =====================================================================  CIRCULATION
BOLUS_EFFECTS = [
  {"vital": "systolic_bp", "delta": 7, "key": "bolus_sbp", "onset_seconds": 10, "duration_seconds": 300,
   "note": "Teaching choice. The owner's structure gives +6 to 8 while the bolus runs."},
  {"vital": "diastolic_bp", "delta": 4, "key": "bolus_dbp", "onset_seconds": 10, "duration_seconds": 300,
   "note": "Teaching choice."},
  {"vital": "heart_rate", "delta": -5, "key": "bolus_hr", "onset_seconds": 10, "duration_seconds": 300,
   "note": "Teaching choice. The owner's structure gives -4 to -6."}]
BOLUS_CREDIT = [{"id": "bolus_here_p3", "when": P3}, {"id": "bolus_here_p4", "when": P4},
                {"id": "fluid_here_p5", "when": P5}]
BOLUS_NOTE = (
  "Anaphylactic shock is a leak as well as a dilation: fluid pours out of the vessels. Rapid "
  "crystalloid boluses, repeated on reassessment, are first-line alongside epinephrine.\n\n"
  "UK guidance gives 10 mL/kg a bolus in children, 400 mL for him. US pediatric pathways "
  "give 20 mL/kg, 800 mL, up to 1 L. Here a 500 mL bolus is 12.5 mL/kg and a 1 L bolus is "
  "25 mL/kg, a little above 20. State his weight first. This simulator does not take "
  "volumes, only the two bags.\n\n"
  "Each bolus lifted his pressure while it ran and faded after. Two in total, or one more "
  "once the infusion was running, and he settled." + RCUK)

act("normal_saline_500ml_bolus",
    [{"when": SICK + " OR " + P7, "value": "critical"},
     {"when": P5 + " AND NOT flag fluid_x2 set", "value": "critical"},
     {"when": None, "value": "recommended"}],
    expectation_label="Crystalloid bolus",
    flags_set=["fluid_given"],
    flags_set_repeat=[{"flag": "fluid_x2", "after_administrations": 2, "counter": "crystalloid"}],
    also_satisfies=BOLUS_CREDIT,
    vital_effects=BOLUS_EFFECTS,
    prompt={"deadline_seconds": 45, "guard": P1 + " OR " + P2,
            "text": "His hands are cold. Anything for his circulation?"},
    debrief_note=BOLUS_NOTE)

act("normal_saline_1l_bolus", ALWAYS("neutral"),
    flags_set=["fluid_given"],
    flags_set_repeat=[{"flag": "fluid_x2", "after_administrations": 2, "counter": "crystalloid"}],
    also_satisfies=[{"id": "normal_saline_500ml_bolus", "when": None}] + BOLUS_CREDIT,
    vital_effects=BOLUS_EFFECTS,
    nurse_alert="That's about twenty-five per kilo for him. Running it in.",
    debrief_note=("Counted as his bolus. A liter is 25 mL/kg at 40 kg, a little more than the "
                  "usual pediatric bolus of 10 to 20 mL/kg. State the weight before the volume." + RCUK))

for cid, note in (("normal_saline_infusion", "A maintenance-rate infusion is not a shock bolus. He needed the fluid in minutes."),
                  ("lactated_ringer_s_infusion", "A maintenance-rate infusion is not a shock bolus. He needed the fluid in minutes."),
                  ("d5_1_2_ns_infusion", "Maintenance fluid with glucose is not a shock bolus. Use a glucose-free crystalloid, fast."),
                  ("d5_ns_bolus", "Use a glucose-free crystalloid for a shock bolus.")):
    act(cid, [{"when": P6, "value": "neutral"}, {"when": None, "value": "discouraged"}],
        debrief_note=note + RCUK)

# Hidden targets: one bolus or one dose in a named phase. Read by transitions (authoring 22.2).
for cid, name, tag_when, text, deadline in (
    ("bolus_here_p3", "Bolus while floppy", P3, "He's cold to the knees. Anything for his circulation?", 40),
    ("bolus_here_p4", "Bolus at the edge of arrest", P4, "He's barely breathing and he's blue. What do you need?", 25),
    ("fluid_here_p5", "More fluid once the infusion runs", P5 + " AND NOT flag fluid_x2 set", "His hands are still cool. Anything else for his circulation?", 60),
    ("epi_here_p4", "Epinephrine at the edge of arrest", P4, "He's barely breathing and he's blue. Epi?", 15),
    ("bridge_here_p7", "Epinephrine after the tube", P7, "His pressure's falling since the tube. Should we do something?", 20),
    ("drip_restarted", "Infusion restarted after a stop",
     "(flag relapsed set AND " + P3 + ") OR (flag relapsed_vent set AND " + P7 + ")",
     "Since the epi stopped he's gone downhill. What do you want?", 20)):
    act(cid, [{"when": tag_when, "value": "critical"}, {"when": None, "value": "neutral"}],
        hidden=True, display_name=name, expectation_label=name,
        prompt={"deadline_seconds": deadline, "guard": tag_when, "text": text},
        debrief_note=("Not an order. Credited when the act is done in this phase, so a dose "
                      "earlier in the run does not count for it. A transition reads it."))

# =====================================================================  BREATHING
RESP = "NOT " + TUBED
act("non_rebreather_mask", ALWAYS("neutral"),
    vital_effects=[{"vital": "oxygen_saturation", "delta": 0, "key": "resp_support", "while": RESP,
                    "note": "He arrived on it. The phases' saturations are on it."}],
    debrief_note="He arrived on the crew's mask. Keep high-concentration oxygen on.")
act("nasal_cannula_oxygen", [{"when": P6, "value": "neutral"}, {"when": None, "value": "discouraged"}],
    vital_effects=[{"vital": "oxygen_saturation", "delta": -5, "key": "resp_support", "while": RESP,
                    "note": "Teaching choice. The owner's structure gives -5 to -6."}],
    debrief_note="Less oxygen than the mask he arrived on, and his saturation fell. Keep high-concentration oxygen.")
act("high_flow_nasal_cannula", ALWAYS("neutral"),
    vital_effects=[{"vital": "oxygen_saturation", "delta": 1, "key": "resp_support", "while": RESP,
                    "note": "Teaching choice."}],
    debrief_note="Acceptable. It does not treat the cause.")
act("non_invasive_positive_pressure_ventilation",
    [{"when": P3 + " OR " + P4, "value": "discouraged"}, {"when": None, "value": "neutral"}],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 2, "key": "resp_support", "while": RESP,
                    "note": "Teaching choice. The owner's structure gives +2 to 3, no pressure benefit."}],
    debrief_note=("A small rise in saturation and no help to the pressure. In a floppy child "
                  "with a falling GCS and swelling lips, a tight mask risks vomiting and "
                  "aspiration, and he cannot protect his airway." + MEMORY))
act("bag_valve_mask", ALWAYS("neutral"),
    vital_effects=[{"vital": "oxygen_saturation", "delta": 6, "key": "resp_support",
                    "while": RESP + " AND " + P4,
                    "note": "Teaching choice. Assisted breaths at the edge of arrest."}],
    debrief_note=("At the edge of arrest he needed breaths with a bag. It lifted his "
                  "saturation. It is part of airway care, which this simulator does not score."))

act("albuterol",
    [{"when": P1 + " AND NOT " + ED_EPI, "value": "discouraged"},
     {"when": SICK + " OR " + P5 + " OR " + P6, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    flags_set=["albuterol_given"],
    vital_effects=[{"vital": "oxygen_saturation", "delta": 1, "key": "albuterol_spo2", "onset_seconds": 30, "duration_seconds": 600,
                    "while": RESP, "note": "Teaching choice."},
                   {"vital": "heart_rate", "delta": 5, "key": "albuterol_hr", "onset_seconds": 30, "duration_seconds": 600,
                    "while": RESP, "note": "Teaching choice."}],
    debrief_note=(
      "Albuterol treats the wheeze that is left after epinephrine. Given before the repeat "
      "epinephrine, it made the chest a little better and left the pressure and the swelling "
      "where they were. After epinephrine, it is a good adjunct." + RCUK))
act("ipratropium", ALWAYS("neutral"), debrief_note="An adjunct for persistent bronchospasm. Not scored." + RCUK)

# =====================================================================  ADJUNCTS
BEFORE = P1 + " AND NOT " + ED_EPI
act("diphenhydramine", [{"when": BEFORE, "value": "discouraged"}, {"when": None, "value": "neutral"}],
    flags_set=["antihistamine_given"],
    flags_set_timed=[{"flag": "antihistamine_onset", "duration_seconds": 300}],
    nurse_alert="It's in. He may get a bit sleepier.",
    debrief_note=(
      "An antihistamine eases the itch and the hives, about five minutes later. It does nothing "
      "for the airway, the breathing or the pressure, and it can make a child sleepier at the "
      "moment his drowsiness is the sign you are watching. Before the repeat epinephrine, it "
      "was the wrong first move." + JTF + RCUK))
act("famotidine_bolus", [{"when": BEFORE, "value": "discouraged"}, {"when": None, "value": "neutral"}],
    flags_set=["antihistamine_given"],
    flags_set_timed=[{"flag": "antihistamine_onset", "duration_seconds": 300}],
    debrief_note="An H2 blocker is an adjunct for the skin at most. Never before epinephrine." + JTF)
for cid in ("methylprednisolone_bolus", "dexamethasone", "hydrocortisone_bolus", "prednisone"):
    act(cid, [{"when": BEFORE, "value": "discouraged"}, {"when": None, "value": "neutral"}],
        debrief_note=(
          "Steroids have no effect in the minutes of this case, and the evidence that they "
          "prevent a second reaction is weak. UK guidance left them out of the acute "
          "algorithm. Before epinephrine they were the wrong first move." + JTF + RCUK))
act("glucagon", ALWAYS("discouraged"),
    nurse_alert="He's retching.",
    debrief_note=(
      "Glucagon is for anaphylaxis that does not respond to epinephrine in a patient on a "
      "beta-blocker. He takes nothing. It gave him nausea and vomiting, and an aspiration risk "
      "with a falling GCS." + MEMORY))
act("ondansetron", ALWAYS("neutral"), debrief_note="He is not vomiting. Not scored.")

# =====================================================================  SEDATION
SED_NOTE = (
  "He was frightened because he could not breathe. A sedative took away the drive of a tiring, "
  "hypoxic child, lowered his pressure, and hid the sign you were watching: whether he was "
  "still asking for his mother. Distress in anaphylaxis is treated with epinephrine, oxygen "
  "and his mother at the bedside." + MEMORY)
SED_IF = [{"flag": "sedated_p1", "when": P1}, {"flag": "sedated_p2", "when": P2}, {"flag": "sedated_p3", "when": P3}]
SED_ALERT = [{"when": EARLY, "value": "He's gone very still since that went in."},
             {"when": None, "value": "It's in."}]
for cid in ("lorazepam_bolus", "morphine_bolus"):
    act(cid, [{"when": P7 + " OR " + P8, "value": "neutral"}, {"when": None, "value": "discouraged"}],
        flags_set_if=SED_IF, nurse_alert=SED_ALERT, debrief_note=SED_NOTE)
for cid in ("midazolam_bolus", "fentanyl_bolus"):
    act(cid, ALWAYS("neutral"), flags_set_if=SED_IF, nurse_alert=SED_ALERT,
        debrief_note=SED_NOTE + (
          "\n\nThis drug is on the catalog's list of intubation drugs, which is never graded, so "
          "the case cannot score it (owner's defaults, 11 November 2026). Given for distress "
          "before a tube, it still made him worse."))
for cid in ("haloperidol", "olanzapine", "ziprasidone"):
    act(cid, [{"when": P7 + " OR " + P8, "value": "neutral"}, {"when": None, "value": "discouraged"}],
        debrief_note=("Nothing to treat: his agitation was hypoxia and fear. An antipsychotic "
                      "can drop the pressure further in a child in shock." + MEMORY))

# =====================================================================  AIRWAY
act("intubate_rapid_sequence",
    [{"when": P1 + " OR " + P2 + " OR " + P5 + " OR " + P6, "value": "discouraged"},
     {"when": P4, "value": "recommended"},
     {"when": None, "value": "neutral"}],
    expectation_label="Decision to intubate",
    nurse_alert=[{"when": RUNNING, "value": "Tube's in. His pressure's holding on the drip."},
                 {"when": None, "value": "Tube's in. His pressure's falling."}],
    follow_ups_triggered=["sedation_after_tube"],
    debrief_note=(
      "Intubate for progressive upper airway obstruction, exhaustion, or an airway he cannot "
      "protect, after or alongside support of the circulation. Without the epinephrine "
      "infusion running, induction and positive pressure collapsed him. In the floppy phase "
      "the tube was not wrong, and it still had to come after the infusion.\n\n"
      "This is a difficult airway: swollen lips and tongue, and later stridor. The most "
      "experienced operator, video laryngoscopy, a hemodynamically stable induction agent "
      "such as ketamine, a smaller tube ready, and front-of-neck equipment open. This "
      "simulator does not score airway care." + MEMORY))
act("cricothyrotomy", ALWAYS("neutral"),
    debrief_note=("The last step if he can be neither intubated nor oxygenated. At 12, needle "
                  "or surgical depends on his size and your practice." + MEMORY))

# =====================================================================  STUDIES
for cid, note in (
  ("fingerstick_blood_sugar", "Normal. Any sick child gets one. Not scored."),
  ("venous_blood_gas", "A mixed acidosis as he tires: the pCO2 rises when he can no longer breathe it off. Not scored."),
  ("arterial_blood_gas", "Accepted in place of the venous gas. Not needed."),
  ("lactate", "Raised from the shock, and slow to clear. Not scored."),
  ("complete_blood_count_cbc", "A stress leukocytosis and some hemoconcentration. Not scored."),
  ("basic_chemistry_chem_7", "Normal. Not scored."),
  ("xr_chest", "Hyperinflated, no consolidation. Not needed to treat him."),
  ("ecg_12_lead", "Sinus tachycardia. Not needed to treat him."),
):
    act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)

# =====================================================================  REASSESSMENT
act("reassessed_after_epi", [{"when": EARLY, "value": "recommended"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Reassessed after epinephrine",
    expectation_label="Reassessed after an epinephrine dose",
    debrief_note=(
      "Not an order. Credited when the airway, breathing, circulation or lungs are examined "
      "after an ED epinephrine dose. The brief response after each dose looked like recovery. "
      "Looking again a minute or two later showed it was not."))

EXAM_NOTES = {
  "exam_airway": "Lips and tongue swelling make this an airway to watch. A hoarse voice and stridor mean it is closing.",
  "exam_breath": "Retractions and a falling effort were the trend that mattered more than the saturation.",
  "exam_circ": "Cap refill, cool legs and weak pulses: his circulation, read as a child's.",
  "exam_pulm": "Wheeze that gets quieter is not always better. A near-silent chest means little air is moving.",
  "exam_heent": "Swollen lips and eyelids. Look at the tongue and listen to the voice.",
  "exam_skin": "Hives and redness. Antihistamines change this and nothing else.",
  "exam_neuro": "GCS by phase. A child who stops talking is getting worse.",
  "exam_card": "Tachycardia. No murmur.",
}
for cid, note in EXAM_NOTES.items():
    kw = {}
    if cid in ("exam_airway", "exam_breath", "exam_circ", "exam_pulm"):
        kw["also_satisfies"] = [{"id": "reassessed_after_epi", "when": ED_EPI}]
    act(cid, ALWAYS("recommended" if cid in ("exam_airway", "exam_breath", "exam_circ", "exam_pulm", "exam_skin", "exam_neuro") else "neutral"),
        debrief_note=note + MEMORY, **kw)

# =====================================================================  HISTORY AND HANDOFF
act("interview_topic_epi_given", ALWAYS("recommended"),
    display_name="Asked what was given before arrival",
    debrief_note="The crew gave 0.3 mg IM fifteen minutes before arrival. That is dose one.")
act("interview_topic_allergies", ALWAYS("recommended"),
    display_name="Asked about allergies",
    debrief_note="Peanut allergy since age three. The dessert had peanut in it.")

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnosis.")

FOLLOW_UPS = [
 {"id": "sedation_after_tube",
  "triggered_by": ["intubate_rapid_sequence"],
  "applies_when": TUBED,
  "deadline_seconds": 120,
  "graded": False,
  "satisfied_by": ["propofol_infusion", "ketamine_infusion", "fentanyl_bolus", "midazolam_bolus",
                   "ketamine_bolus", "lorazepam_bolus", "morphine_bolus"],
  "nurse_prompt": "Is he comfortable? He can't move.",
  "debrief_note": ("After a rocuronium tube he needs analgesia and sedation within minutes. "
                   "Not scored: airway care is ungraded.")},
]

# Catalog actions that the follow-up names must be case actions too.
for cid in ("propofol_infusion", "ketamine_infusion", "ketamine_bolus"):
    act(cid, ALWAYS("neutral"),
        debrief_note="Sedation after the tube. Airway care, not scored. Ketamine is the gentler choice for his pressure." + MEMORY)

for cid in ("etomidate_bolus", "rocuronium_bolus", "succinylcholine_bolus"):
    act(cid, ALWAYS("neutral"),
        debrief_note="Intubation care, not scored. Doses are not modeled." + MEMORY)
