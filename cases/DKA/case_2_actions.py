"""DKA part 2: the action spine, tags, flags, prompts and vital effects.

Nothing is tagged harmful and nothing ends the case except a handoff. Every wrong drug
shows its effect and can be undone. Every clinical judgment here is model output awaiting
a physician's signature, except the decisions in DKA-SEED.md section 0.

Sources opened on 6 October 2026 are listed in DKA-SEED.md. "Consensus report" below means
Umpierrez et al., Hyperglycaemic crises in adults with diabetes: a consensus report,
Diabetologia and Diabetes Care 2024, read through a summarizing tool.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

PRES = "phase is presentation"
REPL = "phase is potassium_replaced"
TREATED = "phase is treated"
FALLING = "phase is potassium_falling"
RECOV = "phase is recovering"
READY = REPL + " OR " + RECOV
CHEM = "study basic_chemistry_chem_7 resulted"

# The catalog's own rule for an intravenous drug (authoring 8.1), so a central or an
# intraosseous line counts.
IV_LINE = [{
  "when": "flag iv_access set OR flag central_access set OR flag io_access set",
  "failure_message": "She doesn't have a line yet. Do you want me to get IV access first?"}]

# Markers go only in fields the interface strips (authoring 13): an action's debrief_note.
REPORT = " [UNVERIFIED: Umpierrez et al. 2024, read through a summarizing tool]"
MEMORY = " [UNVERIFIED: general teaching written by a model from memory, no source opened]"
# The potassium rule by level (hold insulin under 3.5, 20 to 40 mEq an hour, recheck every
# one to two hours, insulin at 3.5 or more, 20 to 30 mEq per liter between 3.5 and 5.5, hold
# potassium over 5.5) is from a reference table the directing physician supplied on
# 7 October 2026. Its own citation was not visible to the model.
TABLE = " [Potassium rule from the reference table supplied by the directing physician, 7 October 2026]"

# =====================================================================  FIRST MINUTES

act("attach_monitor",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    flags_set=["monitor_on"],
    prompt={"deadline_seconds": 20, "guard": PRES,
            "text": "She's not on a monitor yet. Do you want her hooked up?"},
    debrief_note=(
      "Nothing shows until the monitor is on. In this patient it matters for a second "
      "reason: a low potassium and the treatment for it are both reasons to watch the "
      "rhythm."))

act("insert_iv", ALWAYS("critical"),
    flags_set=["iv_access"],
    debrief_note="Fluid, potassium and an insulin infusion all need a line.")

act("second_iv", ALWAYS("neutral"),
    debrief_note=(
      "Useful when potassium, insulin and fluid are all running, because potassium is "
      "not mixed into every line. Not scored."))

# Bound so that the potassium prerequisite can use the catalog's three-flag line rule.
# The validator accepts a flag in a case prerequisite only when a case action sets it.
# Neutral and unscored. Whether either should be discouraged here is not decided.
for cid, flag in (("central_venous_catheter_triple_lumen", "central_access"),
                  ("central_venous_catheter_cordis", "central_access"),
                  ("intraosseous_line", "io_access")):
    act(cid, ALWAYS("neutral"), flags_set=[flag],
        debrief_note="Counts as a line for intravenous potassium and for everything else. Not scored.")

act("fingerstick_blood_sugar",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    expectation_label="Bedside glucose",
    prompt={"deadline_seconds": 40, "guard": PRES + " AND NOT study fingerstick_blood_sugar ordered",
            "text": "She looks dry and she's breathing deeply. Do you want a fingerstick glucose?"},
    debrief_note=(
      "A bedside glucose takes seconds and it is what turns a stomach bug into a "
      "different problem. The triage note did not mention diabetes. Any vomiting adult who "
      "looks dry or is breathing deeply gets one.\n\n"
      "Repeated hourly once insulin is running." + REPORT))

act("venous_blood_gas", ALWAYS("critical"),
    expectation_label="Blood gas (venous is enough)",
    debrief_note=(
      "The pH is one of the three things that make the diagnosis and it sets the "
      "severity. Hers is 7.27, which with a bicarbonate of 16 and a clear head is mild "
      "ketoacidosis in the 2024 consensus report. The gas is a metabolic acidosis with a "
      "low pCO2 from deep breathing. A venous sample is enough. An arterial "
      "puncture adds pain and no information here." + REPORT))

act("arterial_blood_gas", ALWAYS("neutral"),
    also_satisfies=[{"id": "venous_blood_gas", "when": None}],
    debrief_note=(
      "Accepted in place of the venous gas, and it says the same thing a venous one "
      "would have. An arterial sample is not needed to diagnose "
      "or follow ketoacidosis when the saturation is normal, and it hurts." + MEMORY))

act("basic_chemistry_chem_7", ALWAYS("critical"),
    expectation_label="Chemistry, for the potassium and the anion gap",
    # A chemistry sent once the potassium has run in is the repeat level the follow-up
    # asks for. Judged on the phase at the moment of the order (authoring 8.2), so a
    # second panel sent before the potassium does not count.
    also_satisfies=[{"id": "repeat_potassium_level", "when": READY + " OR " + TREATED}],
    prompt={"deadline_seconds": 75, "guard": PRES + " AND NOT " + "study basic_chemistry_chem_7 ordered",
            "text": "Do you want labs sent? I can send a chemistry and a gas off the line."},
    debrief_note=(
      "Two numbers on this panel run the case. The anion gap of 18 with a bicarbonate of "
      "16 is the acidosis. The potassium of 3.1 is the reason insulin waits.\n\n"
      "Most patients in ketoacidosis arrive with a normal or high potassium, because "
      "acidosis and lack of insulin move it out of cells. The consensus report puts a "
      "level under 3.5 on arrival at 5 to 10 percent of patients. Two days of vomiting "
      "and diarrhea is how she got there.\n\n"
      "A repeat panel shows what each treatment did. After fluid the glucose and the BUN "
      "are a little lower, the bicarbonate has not moved, the anion gap has barely moved "
      "and the potassium is slightly lower by dilution. After bicarbonate the bicarbonate "
      "is a little higher, the potassium is lower and ketone production has not changed. "
      "After the potassium infusion the level is back to 3.5 or more and the acidosis is "
      "untreated and a little worse, which is the cost of the wait. On insulin with the "
      "potassium replaced the glucose falls, the bicarbonate rises, the anion gap narrows "
      "and the potassium holds. After insulin given too early the potassium is 2.6, and "
      "the glucose has fallen by the same insulin effect that moved the potassium."
      + REPORT))

act("beta_hydroxybutyrate", ALWAYS("recommended"),
    expectation_label="Blood ketones",
    debrief_note=(
      "A blood beta-hydroxybutyrate of 3.0 mmol/L or more is the ketone criterion in the "
      "2024 consensus report, and it is the number that says when the ketoacidosis has "
      "resolved (under 0.6). Urine ketones lag behind and can look worse as she gets "
      "better." + REPORT))

act("urinalysis", ALWAYS("recommended"),
    debrief_note=(
      "Ketones and glucose in the urine support the diagnosis. The reason to send it is "
      "the search for a trigger: urinary infection is one of the commonest. Hers shows "
      "none." + MEMORY))

act("urine_hcg_qualitative", ALWAYS("recommended"),
    expectation_label="Pregnancy test",
    debrief_note=(
      "A woman of 24 who is vomiting gets a pregnancy test whatever she says about her "
      "pill. Pregnancy lowers the glucose at which ketoacidosis occurs and raises the "
      "stakes. Hers is negative." + MEMORY))

act("serum_hcg_quantitative", ALWAYS("neutral"),
    also_satisfies=[{"id": "urine_hcg_qualitative", "when": None}],
    debrief_note="Accepted in place of the urine test. Negative.")

act("ecg_12_lead",
    [{"when": FALLING, "value": "critical"}, {"when": None, "value": "recommended"}],
    prompt={"deadline_seconds": 70, "guard": FALLING,
            "text": "She says her heart is fluttering. Do you want a twelve-lead?"},
    debrief_note=(
      "A potassium of 3.1 is a reason for an ECG and a monitor. At that level many "
      "tracings are normal. Hers shows subtle T wave flattening and small U waves. After "
      "insulin given too early the T waves flatten, the U waves grow and the QT "
      "lengthens.\n\n"
      "Flat T waves and U waves are the ECG of a low potassium. The QT is hard to "
      "measure when a U wave follows the T wave.\n\n"
      "The ECG is a rough guide to potassium. A normal tracing does not mean a normal "
      "level." + MEMORY))

act("magnesium_level", ALWAYS("recommended"),
    debrief_note=(
      "Low at 1.5. A low magnesium often travels with a low potassium after vomiting and "
      "diarrhea, and it makes the potassium harder to correct. The consensus report does "
      "not discuss magnesium. This is general teaching on hypokalemia." + MEMORY))

act("phosphate_level", ALWAYS("neutral"),
    debrief_note=(
      "Normal on arrival, as it usually is, and expected to fall with insulin. The "
      "consensus report advises against routine phosphate replacement and considers it "
      "when the level is low with muscle weakness or respiratory or cardiac compromise. "
      "The report prints the cutoff as under 1.0 mmol/L. Older guidance used 1.0 mg/dL. "
      "Check your own protocol." + REPORT))

for cid, note in [
  ("complete_blood_count_cbc",
   "A white count of 13 is common in ketoacidosis without infection. It is a stress "
   "response and does not on its own mean she needs antibiotics. Her hemoglobin is at "
   "the top of her range from dehydration."),
  ("lipase",
   "Normal. Lipase is often raised in ketoacidosis without pancreatitis, sometimes several "
   "times the upper limit, so a raised one would have needed interpreting with the abdomen."),
  ("lactate", "Normal. Her acidosis is ketones."),
  ("osmolality",
   "At the top of the normal range. A high osmolality with a very high glucose and little "
   "ketosis would be the hyperosmolar state, which she does not have."),
  ("xr_chest",
   "Clear. Pneumonia is a common trigger and she has no cough, so this was optional."),
  ("ultrasound_cardiac",
   "A vigorous ventricle and a small vena cava that collapses with each breath fit the "
   "fluid she has lost. It was not needed to make the diagnosis. Not scored."),
]:
    act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)

act("ct_abdomen", ALWAYS("discouraged"),
    debrief_note=(
      "Her cramps fit the gastroenteritis, her abdomen is soft with no guarding and her "
      "appendix is out. A scan adds radiation and delay for a young woman.\n\n"
      "Abdominal pain from ketoacidosis itself tracks the severity of the acidosis. In "
      "mild ketoacidosis, significant pain should not be put down to the ketoacidosis, "
      "and pain that persists as she improves is the reason to look further." + REPORT))

# =====================================================================  FLUID

act("normal_saline_1l_bolus", ALWAYS("critical"),
    expectation_label="Crystalloid bolus",
    flags_set=["fluids_given"],
    vital_effects=[
      {"vital": "heart_rate", "delta": -10, "key": "fluid_hr",
       "note": ("Teaching choice. Fluid is what brings her rate down. Every phase's "
                "authored rate is the rate without fluid.")},
      {"vital": "systolic_bp", "delta": 6, "key": "fluid_bp", "note": "As above."}],
    prompt={"deadline_seconds": 100, "guard": "NOT flag fluids_given set",
            "text": "She's dry and her pulse is fast. Do you want fluid running?"},
    debrief_note=(
      "Fluid comes first. The consensus report recommends isotonic saline or a balanced "
      "crystalloid at 500 to 1000 mL an hour for the first two to four hours. Either "
      "counts here.\n\n"
      "Watch what fluid did and did not do. Her rate came down and her glucose fell a "
      "little by dilution and by better kidney perfusion. Her bicarbonate and anion gap "
      "did not move. Fluid treats the dehydration. Insulin treats the ketoacidosis.\n\n"
      "Fluid also dilutes the potassium slightly, which is one more reason to know the "
      "level early." + REPORT))

# A crystalloid infusion is fluid too. It sets the same flag, moves the same two numbers
# under the same keys (so a bolus and an infusion do not stack), and discharges the fluid
# expectation. Whether an infusion earns the same credit as a bolus is recorded in the
# SEED as a question for the physician.
for cid in ("normal_saline_infusion", "lactated_ringer_s_infusion"):
    act(cid, ALWAYS("neutral"),
        flags_set=["fluids_given"],
        vital_effects=[
          {"vital": "heart_rate", "delta": -10, "key": "fluid_hr",
           "note": "Teaching choice. The same effect and the same key as the bolus."},
          {"vital": "systolic_bp", "delta": 6, "key": "fluid_bp", "note": "As above."}],
        also_satisfies=[{"id": "normal_saline_1l_bolus", "when": None}],
        debrief_note=(
          "Counted as her fluid. The consensus report gives the first fluid as a rate, 500 "
          "to 1000 mL an hour, so an infusion started at that rate is the same treatment "
          "as a bolus. Continuing fluid afterwards is part of treatment too. With the "
          "potassium between 3.5 and 5.5, 20 to 30 mEq of potassium goes into each liter. "
          "Not scored separately from the bolus." + REPORT + TABLE))

# =====================================================================  POTASSIUM

act("potassium_chloride_kcl",
    [{"when": PRES + " OR " + FALLING, "value": "critical"},
     {"when": None, "value": "recommended"}],
    display_name="Potassium Chloride (KCl) IV",
    expectation_label="Intravenous potassium before insulin",
    flags_set=["potassium_iv_given"],
    prerequisites=IV_LINE,
    follow_ups_triggered=["repeat_potassium_after_replacement"],
    nurse_alert="It's on the pump. It takes a while to run in.",
    # The guard is read once, at the deadline. The nurse asks for the chemistry at 75
    # seconds, so the first potassium prompt comes after a learner who needed that prompt
    # can have the result (authoring 9.5 rule 4). The escalation reads as a first warning
    # too, and claims no result, because in the falling phase the guard tests none.
    prompt={"deadline_seconds": 110,
            "guard": "(" + PRES + " AND " + CHEM + " AND NOT flag potassium_iv_given set) OR ("
                     + FALLING + " AND NOT flag potassium_iv_given set)",
            "text": "I'm worried about her potassium. Do you want some running through the line?",
            "escalation": {"deadline_seconds": 170,
                           "text": ("Nothing has gone in for her potassium. Do you want it "
                                    "running before anything else goes in?")}},
    debrief_note=(
      "This is the step that makes the case. Her potassium was 3.1 before any insulin. "
      "Insulin moves potassium into cells, and a level that is already low falls to one "
      "that can stop the heart or the breathing muscles.\n\n"
      "The rule by level:\n\n"
      "Under 3.5: hold insulin. Intravenous potassium chloride at 20 to 40 mEq an hour, "
      "on a monitor. Recheck the level every one to two hours. Start insulin only once "
      "it is 3.5 or more.\n\n"
      "3.5 to 5.5: 20 to 30 mEq of potassium in each liter of fluid, and insulin can start "
      "at the same time.\n\n"
      "Over 5.5: hold the potassium, start insulin, and recheck in one to two hours. "
      "Insulin and fluid bring it down fast.\n\n"
      "Rates of 20 mEq an hour and above usually mean a central line or two peripheral "
      "lines, and always a monitor. Follow your own policy. Potassium is never given as "
      "a push.\n\n"
      "Sources differ on the numbers. The 2024 consensus report, as read for this case, "
      "gave a lower starting rate, and the 2009 American Diabetes Association statement "
      "used 3.3 as the threshold, which many hospital protocols still do. This case uses "
      "3.5 and 20 to 40 mEq an hour, from the reference the directing physician set on "
      "7 October 2026.\n\n"
      "The simulator compresses hours of infusion into twenty seconds and does not model "
      "the dose."
      + TABLE + REPORT + " [UNVERIFIED: the 2009 threshold of 3.3 and the line "
      "requirements are from memory]"))

act("potassium_chloride_oral", ALWAYS("neutral"),
    flags_set=["oral_potassium_tried"],
    narration_override="She's taken the potassium. I can't promise it stays down.",
    debrief_note=(
      "Oral potassium is a good route in a patient who can keep it down, and it is often "
      "given alongside the infusion. She came in vomiting, so it cannot be relied on. "
      "With a level of 3.1 and insulin waiting on it, the intravenous route is the one "
      "to use. The simulator gives the oral dose no effect at any point in the case, "
      "which is a simplification once her vomiting has settled. Not scored." + MEMORY))

act("magnesium_sulfate", ALWAYS("recommended"),
    expectation_label="Magnesium replacement",
    flags_set=["mag_given"],
    debrief_note=(
      "A low magnesium makes the kidneys waste potassium, so replacing it helps the "
      "potassium hold. It also protects against the rhythm problems of a long QT. This is "
      "standard teaching on hypokalemia and is not addressed in the consensus report."
      + MEMORY))

# =====================================================================  INSULIN

INSULIN_NOTE = (
  "Insulin is the treatment for ketoacidosis and its timing is the lesson here.\n\n"
  "Given once a repeat level was 3.5 or more, it was right. Given while the potassium was "
  "3.1, or before the result was back, it drove the level down to 2.6 and made her weak. "
  "Under 3.5, insulin is held and the potassium is replaced first. Insulin starts once "
  "the level is 3.5 or more, and between 3.5 and 5.5 it runs with potassium in the "
  "fluids.\n\n"
  "The report recommends a fixed-rate infusion of 0.1 units per kg per hour, and accepts "
  "subcutaneous rapid-acting insulin every one to two hours for uncomplicated mild or "
  "moderate ketoacidosis. Either route counts in this case.\n\n"
  "Potassium that has been started is not potassium that has been replaced. In the "
  "simulator, insulin waits for a repeat level of 3.5 or more, and rapid insulin ordered "
  "at any point before the potassium infusion has finished drops her potassium."
  + REPORT + TABLE)
INSULIN_TAG = [{"when": READY, "value": "critical"},
               {"when": TREATED, "value": "neutral"},
               {"when": None, "value": "discouraged"}]
# Order is carried by two hidden actions that nothing presses (authoring 6.8 and 8.2).
# The credit is judged on the phase at the moment of the order.
#   early_insulin    rapid insulin by any route, ordered in the arrival phase
#   insulin_restart  an infusion or a subcutaneous dose ordered in the recovering phase
EARLY_CREDIT = {"id": "early_insulin", "when": PRES}
RESTART_CREDIT = {"id": "insulin_restart", "when": RECOV}

act("insulin_drip", INSULIN_TAG,
    expectation_label="Insulin, once the potassium is 3.5 or more",
    flags_set=["insulin_given", "insulin_running"],
    also_satisfies=[EARLY_CREDIT, RESTART_CREDIT],
    follow_ups_triggered=["dextrose_plan_after_insulin"],
    # Asks for the level, and does not invite insulin on a dose alone. The same question
    # in the recovering phase is carried by insulin_restart below, because there this
    # action may already count as done and a done action never prompts.
    prompt={"deadline_seconds": 45, "guard": REPL,
            "text": ("The potassium has gone in. Do you want a repeat level, and insulin "
                     "if it's 3.5 or more?")},
    debrief_note=INSULIN_NOTE)

act("insulin_subcutaneous",
    [{"when": READY + " OR " + TREATED, "value": "neutral"},
     {"when": None, "value": "discouraged"}],
    expectation_label="Subcutaneous rapid-acting insulin",
    flags_set=["insulin_given", "insulin_running"],
    also_satisfies=[{"id": "insulin_drip", "when": READY}, EARLY_CREDIT, RESTART_CREDIT],
    follow_ups_triggered=["dextrose_plan_after_insulin"],
    debrief_note=(
      INSULIN_NOTE.replace(REPORT, "") + "\n\n"
      "Subcutaneous insulin cannot be turned off once it is in. That is one more reason "
      "to be sure of the potassium first." + REPORT))

act("insulin_bolus", ALWAYS("discouraged"),
    flags_set=["insulin_given"],
    also_satisfies=[EARLY_CREDIT],
    debrief_note=(
      "An insulin bolus is not part of routine treatment. The consensus report mentions "
      "a bolus of 0.1 units per kg, intravenous or intramuscular, only when starting the "
      "infusion is going to be delayed. Some protocols differ. A bolus moves potassium "
      "into cells as fast as an infusion does, so before the potassium was replaced it "
      "carried the same risk. A bolus alone does not treat her. She needs the infusion "
      "or subcutaneous doses." + REPORT))

act("early_insulin", ALWAYS("neutral"),
    hidden=True, display_name="Rapid insulin ordered before the potassium had run in",
    debrief_note=(
      "Not an order. The simulator credits this when rapid insulin is ordered in the "
      "arrival phase, and the phase rules read it. A learner never sees it."))

act("insulin_restart",
    [{"when": RECOV, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Insulin restarted after the hold",
    expectation_label="Insulin back on, once the potassium is 3.5 or more",
    # insulin_drip may already count as done from the early order, and a done action
    # never prompts. This one can only be met by an order placed in the recovering phase.
    prompt={"deadline_seconds": 45, "guard": RECOV,
            "text": ("The potassium has gone in. Do you want a repeat level, and insulin "
                     "back on if it's 3.5 or more?")},
    debrief_note=(
      "After insulin given too early, the insulin is held, the potassium is replaced and "
      "the level is repeated. Insulin then goes back on, by infusion or by subcutaneous "
      "rapid-acting insulin, and this time it treats her. In the simulator a held "
      "insulin stays off until it is ordered again." + REPORT))

act("stop_insulin",
    [{"when": FALLING, "value": "critical"},
     {"when": TREATED, "value": "discouraged"},
     {"when": None, "value": "neutral"}],
    display_name="Stop Insulin (hold further doses)",
    expectation_label="Hold the insulin",
    flags_set=["insulin_stopped"],
    narration_override="Insulin is on hold. It stays off until you order it again.",
    prompt={"deadline_seconds": 25, "guard": FALLING + " AND NOT flag insulin_stopped set",
            "text": "She's weaker since the insulin. Do you want it held?"},
    debrief_note=(
      "After insulin given too early her potassium is 2.6, and holding insulin is the "
      "first step of the rescue. It goes back on once the potassium is 3.5 or more.\n\n"
      "Stopping insulin in a patient who is responding is the opposite mistake. A glucose "
      "that looks better is not the end point. Resolution in the consensus report is "
      "ketones under 0.6 mmol/L with a pH of 7.3 or a bicarbonate of 18 or more, and "
      "many hospitals also use a closed anion gap. Insulin continues with dextrose until "
      "then. Basal insulin is started one to two hours before an infusion is stopped."
      + REPORT))

act("insulin_glargine_subcutaneous",
    [{"when": TREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    expectation_label="Her usual basal insulin",
    flags_set=["basal_given"],
    narration_override="That's her long-acting insulin in, her usual dose.",
    debrief_note=(
      "She skipped her basal insulin, and that is why she is here. Giving it back is "
      "part of the treatment. The consensus report says a regimen the patient was "
      "already on 'can be continued at the usual dose', and that basal insulin 'should "
      "be started 1-2 h before cessation of intravenous insulin'.\n\n"
      "How early to give it is not settled. The report says many clinicians give basal "
      "insulin during the infusion and others avoid it because of the risk of a low "
      "glucose or a low potassium, and that several studies of a low "
      "dose found a shorter time to resolution and less rebound hyperglycemia.\n\n"
      "This case counts it once insulin is running and the potassium is 3.5 or more, and "
      "does not score it before then. Glargine acts over hours, so the simulator does "
      "not let it drop the potassium the way rapid insulin does. That is a "
      "simplification. It also does not replace the infusion or the rapid-acting "
      "doses. Basal insulin alone will not clear the ketones." + REPORT))

# =====================================================================  WHAT FOLLOWS INSULIN

act("d5_1_2_ns_infusion",
    [{"when": TREATED, "value": "recommended"}, {"when": None, "value": "neutral"}],
    expectation_label="Dextrose-containing fluid, ordered for when the glucose is under 250",
    flags_set=["dextrose_planned"],
    narration_override="I'll have the dextrose fluid ready and switch to it when her sugar is under 250.",
    debrief_note=(
      "Once the glucose is under 250 mg/dL the consensus report changes the fluid to one "
      "containing 5 to 10 percent dextrose, so that insulin can continue until the "
      "ketones clear without the glucose going low. Ordering it ahead is the plan the "
      "receiving team needs.\n\n"
      "Before insulin is running it does nothing useful." + REPORT))

act("d5_ns_bolus", ALWAYS("neutral"),
    also_satisfies=[{"id": "d5_1_2_ns_infusion", "when": TREATED}],
    debrief_note=(
      "Accepted as the dextrose plan once insulin is running. An infusion is the usual "
      "form."))

act("d50_bolus", ALWAYS("discouraged"),
    debrief_note=(
      "Concentrated dextrose is for a low glucose. Hers was never under 250. It raises "
      "the glucose and the osmolality in a patient being treated for both." + MEMORY))

act("na_bicarbonate_bolus", ALWAYS("discouraged"),
    expectation_label="Sodium bicarbonate",
    flags_set=["bicarb_given"],
    debrief_note=(
      "Bicarbonate is not a treatment for mild ketoacidosis. The consensus report "
      "considers it only when the pH is under 7.0. Hers is 7.27, and insulin clears the "
      "acid by stopping ketone production.\n\n"
      "It can also lower the potassium. A chemistry sent after it, before anything else "
      "has changed her, shows hers slightly lower than on arrival." + REPORT))

# =====================================================================  SYMPTOMS

act("ondansetron", ALWAYS("neutral"),
    flags_set=["ondansetron_given"],
    debrief_note=(
      "Treating her vomiting is kind and reasonable. Ondansetron lengthens the QT "
      "interval by a few milliseconds at usual doses, which matters only when the QT is "
      "already long. A low potassium and a low magnesium lengthen it too, and the drug "
      "label says to correct both first. In her, look at the ECG and start the "
      "replacement. A repeat ECG after it shows the QT about 5 ms longer, which is "
      "within measurement error. Not scored."
      " [UNVERIFIED: FDA drug safety communication on ondansetron, opened by a model, "
      "not checked by a physician]"))

act("metoclopramide", ALWAYS("neutral"),
    debrief_note="A reasonable antiemetic. Not scored.")

# =====================================================================  CONSULTS

act("consult_endocrinology", ALWAYS("recommended"),
    flags_set=["endocrine_called"], state_changing=True,
    debrief_note=(
      "The endocrinologist asks for the potassium and the gas before anything else, and "
      "gives the same order of treatment the case rewards. Calling is good practice and "
      "is what you would do before admission anyway."))

act("consult_critical_care", ALWAYS("neutral"),
    flags_set=["icu_called"], state_changing=True,
    debrief_note=(
      "Mild ketoacidosis in an alert patient does not usually need intensive care. The "
      "consensus report suggests a regular or observation unit for mild ketoacidosis and "
      "step-down for moderate. Some hospitals require intensive care for any insulin "
      "infusion." + REPORT))

act("repeat_potassium_level", ALWAYS("neutral"),
    hidden=True, display_name="Repeat potassium after replacement",
    debrief_note=(
      "Not an order. The simulator credits this when a chemistry is sent once the "
      "potassium has run in, and the repeat-level follow-up reads it. A learner never "
      "sees it."))

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
EXAM_NOTES = {
  "exam_airway": "Her airway is her own throughout.",
  "exam_breath": (
    "Deep, slightly fast breathing with clear lungs is the body blowing off acid. In a "
    "vomiting patient it is easy to read as anxiety."),
  "exam_circ": "A fast pulse and slow capillary refill are the fluid she has lost.",
  "exam_heent": (
    "A dry mouth and a fruity smell on the breath. Not everyone can smell ketones, so "
    "its absence means nothing."),
  "exam_neck": "Flat neck veins fit dehydration. No stiffness.",
  "exam_card": "Fast and regular with no murmur. After early insulin, extra beats.",
  "exam_pulm": "Clear. No pneumonia as a trigger.",
  "exam_abd": (
    "Mild diffuse tenderness without guarding is common in ketoacidosis and improves "
    "with treatment. A rigid or localized abdomen would need its own explanation."),
  "exam_gu": "No flank or suprapubic tenderness. One point against a urinary source.",
  "exam_back": "Nothing to find.",
  "exam_msk": "No calf swelling.",
  "exam_skin": (
    "Dry with reduced turgor. Her injection sites are clean. An infected site or a foot "
    "wound is a trigger worth looking for in any patient with diabetes."),
  "exam_neuro": (
    "Fully alert, which is part of what makes this mild. After early insulin she has "
    "proximal weakness and reduced reflexes, which is the low potassium."),
  "exam_psych": "Tired and cooperative.",
}
for cid, note in EXAM_NOTES.items():
    act(cid, ALWAYS("neutral"), debrief_note=note + MEMORY)

FOLLOW_UPS = [
 {"id": "repeat_potassium_after_replacement",
  "triggered_by": ["potassium_chloride_kcl"],
  "applies_when": "flag potassium_iv_given set",
  "deadline_seconds": 50,
  # A hidden target, credited by a chemistry sent once the potassium has run in
  # (authoring 8.2). A panel sent before the potassium, or while it runs, does not count.
  "satisfied_by": ["repeat_potassium_level"],
  "nurse_prompt": "The potassium has been through for a bit. Do you want a repeat level?",
  "debrief_note": (
    "Insulin waits for a number, not for a dose. The level is repeated after replacement "
    "and insulin starts when it is 3.5 or more. While potassium is being replaced the "
    "level is rechecked every one to two hours. Once insulin is running, potassium goes "
    "into the fluids and the level is still checked every one to two hours at first.\n\n"
    "A sample sent before the infusion had run in shows the old level.")},

 {"id": "dextrose_plan_after_insulin",
  "triggered_by": ["insulin_drip", "insulin_subcutaneous"],
  "applies_when": "phase is treated",
  "deadline_seconds": 60,
  # The D5 bolus credits d5_1_2_ns_infusion through also_satisfies, in the treated phase
  # only. Listing the bolus here as well let one given on arrival discharge this.
  "satisfied_by": ["d5_1_2_ns_infusion"],
  "nurse_prompt": ("She's on insulin now. What do you want in her fluids when her sugar "
                   "gets under 250?"),
  "debrief_note": (
    "Her glucose will reach 250 well before her ketones clear. The plan is dextrose in "
    "the fluids at that point, with insulin continued. Stopping insulin because the "
    "glucose looks normal lets the ketoacidosis return.")},
]
