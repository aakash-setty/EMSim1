"""SWEET part 1: identity, patient, phases.

Refractory anaphylaxis in a 12-year-old boy, 40 kg, after a peanut dessert at home. EMS gave
0.3 mg intramuscular epinephrine about fifteen minutes before arrival. He improved for a few
minutes and is struggling again. Drafted by a language model on 11 November 2026 from a case
structure and three rounds of answers supplied by Aakash Setty in the same conversation. No
physician has reviewed this pack. SWEET-SEED.md says what a person decided and which sources
were opened.

Five learning goals drive the structure (SEED section 2):

  1. A dose in the field is not completed treatment. One more IM dose now, before any adjunct.
  2. Read a child's vitals and behavior against his age. A child who stops talking is worse.
  3. Anaphylactic shock needs volume and posture.
  4. After two IM doses, this is refractory: start the epinephrine infusion, and call for help.
  5. Adjuncts and the airway in their place.

Structure (owner, 11 and 13 November 2026). The first ED dose works within 10 seconds and is
gone by 60, then he is worse than on arrival (phase 2). Phase 2 is the window to order the
infusion, which pharmacy has running 10 seconds after the order. A second IM dose works for
less time (gone by 40 seconds) and he then goes floppy (phase 3), never sooner than he would
have without it. Without the infusion he goes from floppy to silent (phase 4) and then to a
terminal bradycardia. The infusion moves him to phase 5 and, with enough fluid, to phase 6. A
tube without the infusion collapses him (phase 7). With it, he is ventilated (phase 8).
Stopping the infusion sends him to a floppy phase of its own (relapse), or after the tube to a
falling pressure of its own (vent_relapse), from which only restarting it brings him back.
"""

META = {
 "case_number": 11,
 "working_title": "12-year-old boy struggling to breathe after a dessert, despite epinephrine from the crew",
 "chief_complaint_patient_voice": "I can't breathe right.",
 "final_diagnosis": (
   "Anaphylaxis to peanut, refractory to two intramuscular doses of epinephrine (one by EMS, "
   "one in the department), with respiratory and cardiovascular compromise: wheeze, "
   "hypotension for age, and falling mental status. He responds to an epinephrine infusion "
   "with fluid, and goes to the PICU on the infusion."),
 "target_level": ["medical_student", "intern", "junior_resident"],
 "estimated_runtime_seconds": 600,
 "learning_objectives": [
   "Treat epinephrine given before arrival as one dose, not as completed treatment. Give a repeat IM dose in the anterolateral thigh now, before any antihistamine, steroid or nebulizer.",
   "Read the vital signs against the norms for a 12-year-old. Recognize hypotension for age and a child who stops talking or asking for his parent as a child who is getting worse.",
   "Treat anaphylactic shock as a volume problem: two lines, a weight-based crystalloid bolus repeated on reassessment, and lying flat with the legs raised.",
   "After two appropriate IM doses without lasting response, call for senior and PICU help and start an epinephrine infusion, bridging with IM doses until it runs.",
   "Put the adjuncts in their place: albuterol for residual wheeze, antihistamines for the skin, no sedation for distress, and an airway after the circulation is supported.",
 ],
 "teaching_frame": (
   "He already had epinephrine, and it worked for a few minutes. The case asks the learner to "
   "treat that as one dose and not a cure, to give one more, to watch it work and then stop "
   "working, and to change the route instead of reaching for something else. The patient "
   "is a frightened child whose mother is at the bedside, and the sign that he is getting "
   "worse is that he stops asking for her."),
 "care_setting": {
   "label": "Pediatric emergency department",
   "detail": (
     "Pediatric emergency department in a children's hospital with a PICU on site, a "
     "pharmacy that mixes infusions on request, and a senior pediatric emergency physician "
     "and PICU team reachable by phone."),
 },
 "arrival": {
   "mode": "ems",
   "location": "resuscitation_bay",
   "line": "Brought in by EMS from home to the resuscitation bay, his mother with him.",
 },
 "complaint": "Trouble breathing after eating",
 "category": "Pediatrics",
 "library": {
   "tempo": "seconds: an IM dose works for a minute and wears off, then the infusion",
   "uncertainty": "when IM epinephrine has failed",
   "right_answer": "one more IM dose, then an infusion, and call for help early",
   "danger": "behind a brief response to the crew's dose",
   "setting": "12 M, EMS with his mother, pediatric ED with a PICU",
   "feel": "urgent, a frightened child",
   "note": "The six variety dimensions of docs/case-design-guide.md ('Choosing a case'), as this case reads. Descriptive, not clinical: no physician has reviewed the wording.",
 },
}

PATIENT = {
 "age": 12,
 "sex": "male",
 "weight_kg": 40,
 "background": (
   "Peanut allergy known since age three, one previous reaction (hives only, as a small "
   "child). No asthma, no regular medications, no heart problems, no drug allergies. "
   "Immunizations up to date.\n\n"
   "About twenty-five minutes before arrival he ate a piece of a dessert his aunt brought. A "
   "few minutes later his mouth itched, then he broke out in hives and started wheezing. His "
   "mother could not find his own pen and called 911. The crew gave 0.3 mg of epinephrine IM "
   "in the thigh about fifteen minutes before arrival. He improved for a few minutes, then "
   "about seven minutes later the wheeze and the breathlessness came back, worse."),
 "presenting_vitals_source": "Inherited from phase 'presentation'.",
 "presenting_appearance": (
   "A frightened, tearful boy sitting forward on the stretcher, pulling at a nonrebreather "
   "mask, asking for his mother. Sweaty, covered in hives, lips and eyelids swollen, "
   "wheezing."),
 "arrival_handover": (
   "Twelve-year-old boy, trouble breathing after eating a dessert at home about twenty-five "
   "minutes ago. We gave him point three of epi in the thigh about fifteen minutes ago, he "
   "picked up for a few minutes and then started struggling again on the way in."),
 "handover_authoring_note": (
   "Section 2.3. Two sentences, 44 words. No vital sign, no diagnosis, no allergen. It carries "
   "the treatment already given, which the default leaves out, because a crew states what it "
   "gave and the case is about that dose (owner, 11 November 2026: EMS gives the first dose)."),
}


def phase(pid, label, short, desc, hr, sbp, dbp, rr, spo2, distress, alert,
          transitions, ecg, terminal=False, **kw):
    d = {
      "id": pid, "label": label, "short_label": short, "clinical_description": desc,
      "vitals": {"heart_rate": hr, "systolic_bp": sbp, "diastolic_bp": dbp,
                 "respiratory_rate": rr, "oxygen_saturation": spo2, "temperature_c": 37.1},
      "appearance": {"distress_level": distress, "alertness_level": alert,
                     "pupil_size": "normal", "pupil_reactivity": "reactive"},
      "rhythm": "regular",
      "ecg": ecg,
      "terminal": terminal, "transitions": transitions,
    }
    d.update(kw)
    return d


def ecg(rate_note, pr=130, qrs=80, qtc=420):
    return {"pattern": "organised", "p_waves": True, "pr_ms": pr, "qrs_ms": qrs, "qtc_ms": qtc,
            "author_note": "Sinus at the phase's rate. Normal intervals for a 12-year-old. " + rate_note + " Model output."}


# --------------------------------------------------------------------------- conditions
# The epinephrine infusion runs 10 seconds after it is ordered: pharmacy makes it that fast
# (owner, 13 November 2026). That is a delayed consequence of the order, measured from
# guard_true, written in each phase a learner can order it in. A stopped infusion sends him to
# a phase of its own (relapse, vent_relapse), where only a restart brings him back, so the
# order flag can stay a plain positive guard everywhere else. The infusion's own phases
# (responding, stabilized, ventilated) are where it is running, so a tube there goes to
# ventilated and a tube anywhere else collapses him.
ORDERED = "flag epi_drip_ordered set"
TUBED = "flag intubated set"
RESTARTED = "action drip_restarted taken"
DRIP_SECONDS = 10

HANDOFF_T = {"when": "action handoff_submit taken", "to": "case_complete",
             "author_note": "First in every list."}


def tube_rules(running, dest=None):
    if dest:
        return [{"when": TUBED, "to": dest,
                 "author_rationale": (
                   "A tube with the infusion stopped. As collapse after induction, and only "
                   "restarting the infusion brings the pressure back. Model output.")}]
    if running:
        return [{"when": TUBED, "to": "ventilated",
                 "author_rationale": (
                   "A tube with the epinephrine infusion already running. The infusion supports "
                   "the circulation through induction and positive pressure. Model output.")}]
    return [{"when": TUBED, "to": "post_induction_collapse",
             "author_rationale": (
               "A tube with no epinephrine infusion running. Induction drugs and positive "
               "pressure take away vascular tone and venous return in a child already in "
               "distributive and hypovolemic shock, and the pressure falls. Model output.")}]


def sedated(flag, dest):
    return {"when": "flag " + flag + " set", "to": dest,
            "author_rationale": (
              "A benzodiazepine or an opioid given for distress. It blunts the drive of a "
              "hypoxic, tiring child, lowers his pressure, and removes the agitation that was "
              "the warning sign. One phase worse at once, a teaching compression (owner's "
              "structure and defaults, 11 November 2026). The nurse's words are on the drug, "
              "since an instant transition speaks no narration.")}


DRIP_NOTE = (
  "The epinephrine infusion is what changed him. Each intramuscular dose had worked for a "
  "minute or two and worn off. A titrated infusion gives the same drug continuously, which "
  "is the escalation for refractory anaphylaxis. "
  "[UNVERIFIED: Resuscitation Council UK refractory anaphylaxis algorithm 2021, read through search]")


def drip_runs(dest, narration):
    return [{"when": ORDERED, "after_seconds": DRIP_SECONDS, "measured_from": "guard_true", "to": dest,
             "narration": narration, "narration_ventilated": narration, "debrief_note": DRIP_NOTE,
             "author_rationale": ("Delayed consequence of the infusion order: pharmacy has it "
                                  "running 10 seconds after the order (owner, 13 November 2026). "
                                  "A teaching compression of the minutes it takes to mix.")}]


def restart(dest, narration):
    return {"when": RESTARTED, "after_seconds": DRIP_SECONDS, "measured_from": "guard_true", "to": dest,
            "narration": narration, "narration_ventilated": narration,
            "debrief_note": "Restarted, the infusion brought him back. It should not have been stopped.",
            "author_rationale": "Delayed consequence of restarting the infusion after a stop. As fast as a new order. Model timing."}


def stop_rule(dest, relapse_flag, narration):
    return {"when": "flag epi_drip_stopped set AND NOT flag " + relapse_flag + " set",
            "after_seconds": 120, "measured_from": "guard_true", "to": dest,
            "flags_set": [relapse_flag],
            "narration": narration, "narration_ventilated": narration,
            "debrief_note": "The infusion was stopped and the reaction came back. Do not wean it in the department.",
            "author_rationale": STOP_RATIONALE}


STOP_RATIONALE = (
  "Delayed consequence of stopping the infusion. Refractory anaphylaxis needs continuous "
  "epinephrine until the reaction settles, which takes hours. Owner's structure rule 8, 120 "
  "seconds a teaching choice (the structure said within 3 minutes). A restart inside the 120 "
  "seconds still lets the relapse play, and brings him back 10 seconds after it (a known gap). "
  "The relapse flag makes it happen once, so the stop and the restart cannot loop.")

INTO_P2 = ("That epi's worn off already. He's stopped asking for his mom, and he's breathing "
           "harder than when he came in.")
INTO_P2_NONE = "He's stopped asking for his mom, and he's working harder to breathe."
INTO_P3 = "He's gone floppy on me. He's stopped fighting the mask."
INTO_P4 = "He's barely breathing for himself, and his lips are blue. His voice is just a whisper."
INTO_END = "His heart rate's dropping. I can barely feel a pulse."

P2_NOTE = (
  "The second intramuscular dose did what the crew's dose had done: a few minutes of better "
  "numbers, then worse than before. Two appropriate IM doses without a lasting response is "
  "refractory anaphylaxis. The next step is not a third drug. It is the same drug as a "
  "titrated infusion, and help to run it. "
  "[UNVERIFIED: Resuscitation Council UK refractory anaphylaxis algorithm 2021, read through search]")
P2_NONE_NOTE = (
  "No epinephrine was given here. The crew's dose had already worn off on the way in, and "
  "his breathing and pressure got worse. Prior epinephrine is not completed treatment. "
  "Repeat it in the thigh, now, before anything else.")
P3_NOTE = (
  "He went floppy because nothing was given that lasts. An IM dose buys a minute in a "
  "child who is refractory. The infusion was the step that holds, and it has to be ordered as "
  "soon as the second dose fails. In a real department it takes minutes to mix, which is why "
  "you order it early and keep giving IM doses until it runs.")
P4_NOTE = (
  "Without the infusion, he went from floppy to barely breathing. A child who is silent, "
  "limp and blue with a hoarse voice and a soft noise on breathing in is close to arrest. "
  "Epinephrine by the fastest route, fluid, and breaths with a bag are the next minute. The "
  "airway swelling makes the tube a hard one.")
END_NOTE = (
  "A falling heart rate in a hypoxic, shocked child is the last sign before arrest. In "
  "children, bradycardia with poor perfusion is treated as arrest. "
  "[UNVERIFIED: PALS bradycardia guidance, from memory]")

PHASES = [
 phase("presentation",
   "Recurrent anaphylaxis after one EMS dose",
   "on arrival",
   "Fifteen minutes after the crew's IM dose, the reaction has come back: hypotensive for "
   "age, tachycardic, wheezing, hives and facial swelling, frightened and asking for his "
   "mother. On the crew's nonrebreather.",
   140, 88, 54, 32, 93, 2, 0,
   [HANDOFF_T]
   + drip_runs("responding", "The epi infusion's up and running.")
   + [sedated("sedated_p1", "persistent")]
   + tube_rules(False) +
   [{"when": "flag epi_im_ed set", "after_seconds": 60, "measured_from": "guard_true",
     "to": "persistent", "narration": INTO_P2, "debrief_note": P2_NOTE,
     "author_rationale": (
       "Delayed consequence, scripted. The first ED dose acts from 10 seconds and is gone by "
       "60 (owner, 11 November 2026: kicks in at 10 seconds, then fades; 13 November 2026: "
       "lasts only 60 seconds). This child is refractory by design, so when it wears off he is "
       "worse than on arrival. One minute is a teaching compression of the five to fifteen "
       "minutes a real dose acts.")},
    {"when": "NOT flag epi_im_ed set", "after_seconds": 180, "to": "persistent",
     "narration": INTO_P2_NONE, "debrief_note": P2_NONE_NOTE,
     "author_rationale": (
       "Deterioration on inaction. No ED epinephrine. Owner's structure rule 3: advance at 3 "
       "minutes with no epinephrine. Prompted at 30 seconds (90 in normal mode).")}],
   ecg("Rate 140.")),

 phase("persistent",
   "Refractory anaphylaxis after two IM doses",
   "still struggling",
   "The second IM dose has worn off. Worse than on arrival: lower pressure, faster heart and "
   "breathing, drowsy with slow answers, no longer asking for his mother. This is refractory "
   "anaphylaxis. The window to order the infusion.",
   152, 76, 40, 36, 91, 2, 1,
   [HANDOFF_T]
   + drip_runs("responding", "The epi infusion's up and running.")
   + [sedated("sedated_p2", "worsening")]
   + tube_rules(False) +
   [{"when": "NOT flag epi_drip_ordered set AND NOT flag epi_bridge_acting set",
     "after_seconds": 150, "to": "worsening",
     "narration": INTO_P3, "debrief_note": P3_NOTE,
     "author_rationale": (
       "Deterioration on inaction: no infusion ordered. 150 seconds, owner's revision of 11 "
       "November 2026. A second IM dose holds him here only while it acts (epi_bridge_acting, "
       "40 seconds), so it never brings phase 3 sooner than no dose would (owner, 11 November "
       "2026). Prompted for the infusion at 30 seconds (90 in normal mode).")},
    {"when": "NOT flag epi_bridge_acting set", "after_seconds": 240, "to": "worsening",
     "narration": INTO_P3, "debrief_note": P3_NOTE,
     "author_rationale": (
       "The cap for a learner who keeps repeating IM doses instead of ordering the infusion: "
       "each dose holds him while it acts, and at 240 seconds he goes floppy once none is "
       "acting. An ordered infusion runs within 10 seconds, so it never meets this rule. "
       "Model output.")}],
   ecg("Rate 152.")),

 phase("worsening",
   "Refractory anaphylaxis, decompensating",
   "getting floppy",
   "Floppy, single words, no longer fighting the mask, GCS 12. Wheeze with poor air movement, "
   "cool mottled legs, weak peripheral pulses.",
   160, 70, 38, 40, 89, 3, 1,
   [HANDOFF_T]
   + drip_runs("responding", "The epi infusion's running. He's opening his eyes and asking for his mom.")
   + [sedated("sedated_p3", "peri_arrest")]
   + tube_rules(False) +
   [{"when": "NOT flag epi_drip_ordered set", "after_seconds": 150, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": (
       "Deterioration on inaction: no infusion ordered. A floppy, refractory child without "
       "continuous epinephrine. 150 seconds a teaching choice. Prompted for the infusion at 30 "
       "seconds (90 in normal mode).")},
    {"when": "NOT action bolus_here_p3 taken", "after_seconds": 240, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": (
       "Deterioration on inaction: no fluid bolus in this phase. Anaphylactic shock is a "
       "volume problem as well as a vasodilation problem (owner's structure, learning point "
       "3). Prompted at 40 seconds (120 in normal mode).")},
    {"when": None, "after_seconds": 360, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": "Scheduled natural history: refractory anaphylaxis with no infusion running.",
     "unguarded_rationale": (
       "Without a running epinephrine infusion this child keeps getting worse, whatever else "
       "is given. IM doses and fluid buy time and do not stop it (owner's structure rule 4). "
       "The infusion rules above are the exit.")}],
   ecg("Rate 160.")),

 phase("peri_arrest",
   "Peri-arrest",
   "going silent",
   "Silent and limp, cyanotic, mottled. Hoarse whisper then soft inspiratory stridor, near "
   "silent chest. GCS 8. Pre-arrest.",
   168, 58, 30, 44, 82, 3, 2,
   [HANDOFF_T]
   + tube_rules(False) +
   [{"when": "flag relapsed set AND NOT flag rescued_once set AND action bolus_here_p4 taken AND action epi_here_p4 taken",
     "after_seconds": 30, "measured_from": "guard_true", "to": "relapse",
     "flags_set": ["rescued_once"],
     "narration": "He's breathing for himself again, but he's still floppy.",
     "debrief_note": ("Epinephrine and fluid pulled him back from the edge. The infusion was "
                      "still stopped, and only restarting it would hold him."),
     "author_rationale": ("As the rescue below, for a child whose infusion had been stopped: "
                          "back to the relapse phase, where only a restart brings him back.")},
    {"when": "NOT flag rescued_once set AND action bolus_here_p4 taken AND action epi_here_p4 taken",
     "after_seconds": 30, "measured_from": "guard_true", "to": "worsening",
     "flags_set": ["rescued_once"],
     "narration": "He's breathing for himself again, but he's still floppy.",
     "debrief_note": ("Epinephrine and fluid pulled him back from the edge to floppy. Without "
                      "the infusion running he will slide again. Allowed once (owner's "
                      "structure rule 9)."),
     "author_rationale": ("Delayed consequence of the rescue. Owner's structure: S6 to S3, once. "
                          "Bag-mask is not in the gate: it is ungraded and cannot be prompted "
                          "(owner's defaults, B9). An infusion order counts as the epinephrine. "
                          "30 seconds is the validator's floor for a guard with a NOT in it.")},
    {"when": None, "after_seconds": 180, "to": "bradycardic_arrest",
     "narration": INTO_END, "debrief_note": END_NOTE,
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": "Owner's structure rule 9: S6 to arrest at 3 minutes without rescue.",
     "author_rationale": "Scheduled natural history to a terminal phase.",
     "unguarded_rationale": "Peri-arrest anaphylaxis without rescue. The rescue rule above fires first when met."}],
   ecg("Rate 168.")),

 phase("responding",
   "Responding to the epinephrine infusion",
   "talking again",
   "Opens his eyes to voice and asks for his mother again. Better air movement, louder wheeze "
   "because more air is moving, cap refill 3 to 4 seconds. GCS 13.",
   150, 86, 50, 34, 92, 2, 1,
   [HANDOFF_T]
   + tube_rules(True) +
   [stop_rule("relapse", "relapsed", "Since the epi stopped, he's gone floppy again."),
    {"when": "flag fluid_x2 set OR action fluid_here_p5 taken", "after_seconds": 180,
     "to": "stabilized",
     "narration": ("We're moving the clock faster here. Over what would be several minutes, "
                   "he's pinked up and he's talking in full sentences."),
     "debrief_note": ("The infusion and enough fluid together. Two boluses, or one more here, "
                      "and he settled. Time was compressed."),
     "author_rationale": (
       "Positive guard from phase entry. 180 seconds openly compresses the owner's 5 to 8 "
       "minutes (B6). Without enough fluid he holds here, with a prompt. Titration is not "
       "gated: the catalog has no titrate action (catalog request).")}],
   ecg("Rate 150.")),

 phase("stabilized",
   "Stabilized on the infusion",
   "settling",
   "Alert and tired, full sentences. Mild residual wheeze, swelling starting to settle, warm "
   "hands, cap refill under 3 seconds. Heart rate still above his age norm on the infusion.",
   122, 102, 64, 24, 96, 1, 0,
   [HANDOFF_T]
   + tube_rules(True) +
   [stop_rule("relapse", "relapsed", "Since the epi stopped, he's gone floppy again.")],
   ecg("Rate 122.")),

 phase("post_induction_collapse",
   "Collapse after intubation without an infusion",
   "after the tube",
   "Intubated and paralyzed. Pressure falling after induction and positive pressure.",
   172, 60, 32, 20, 88, 0, 3,
   [HANDOFF_T]
   + drip_runs("ventilated", "The epi infusion's running. His pressure's coming up.")
   + [{"when": "NOT action bridge_here_p7 taken", "after_seconds": 150, "to": "bradycardic_arrest",
     "narration": INTO_END, "narration_ventilated": INTO_END, "debrief_note": (
       "Induction without epinephrine running, and no bridge dose afterwards. " + END_NOTE),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": "Collapse after induction with no epinephrine given. Prompted at 20 seconds (60 in normal mode).",
     "author_rationale": "Deterioration on inaction to a terminal phase."},
    {"when": None, "after_seconds": 360, "to": "bradycardic_arrest",
     "narration": INTO_END, "narration_ventilated": INTO_END, "debrief_note": (
       "A bridge dose bought time, and the infusion never ran. " + END_NOTE),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": "Six minutes after the tube with no infusion running.",
     "author_rationale": "Scheduled natural history to a terminal phase.",
     "unguarded_rationale": "The infusion rules above are the exit. Bridge doses do not stop the collapse."}],
   ecg("Rate 172."), ventilated=True),

 phase("ventilated",
   "Ventilated with the infusion running",
   "on the ventilator",
   "Tube in, on the ventilator, epinephrine infusion running. The owner's S6 success values "
   "(SpO2 94, continuing at S4).",
   148, 88, 52, 20, 94, 0, 3,
   [HANDOFF_T,
    stop_rule("vent_relapse", "relapsed_vent", "Since the epi stopped, his pressure's falling.")],
   ecg("Rate 148."), ventilated=True),

 phase("relapse",
   "Relapse after the infusion was stopped",
   "floppy again",
   "The infusion was stopped and the reaction has come back: floppy, single words, poor air "
   "movement, mottled legs, as in phase 3. Only restarting the infusion brings him back.",
   160, 70, 38, 40, 89, 3, 1,
   [HANDOFF_T,
    restart("responding", "The epi's back on. He's opening his eyes again."),
    sedated("sedated_p3", "peri_arrest")]
   + tube_rules(False, dest="vent_relapse") +
   [{"when": "NOT " + RESTARTED, "after_seconds": 150, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": (
       "Deterioration on inaction: the infusion not restarted. As phase 3's no-order rule. "
       "Prompted at 20 seconds (60 in normal mode).")},
    {"when": "NOT action bolus_here_p3 taken", "after_seconds": 240, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": "As phase 3: no fluid bolus in this phase. Prompted at 40 seconds (120 in normal mode)."},
    {"when": None, "after_seconds": 360, "to": "peri_arrest",
     "narration": INTO_P4, "debrief_note": P4_NOTE,
     "author_rationale": "Scheduled natural history: refractory anaphylaxis with the infusion off.",
     "unguarded_rationale": "As phase 3. The restart rule above is the exit."}],
   ecg("Rate 160.")),

 phase("vent_relapse",
   "Ventilated, infusion stopped",
   "pressure falling",
   "Intubated, the infusion stopped, the pressure falling as after induction. Only restarting "
   "the infusion brings it back.",
   172, 60, 32, 20, 88, 0, 3,
   [HANDOFF_T,
    restart("ventilated", "The epi's back on. His pressure's coming up."),
    {"when": "NOT " + RESTARTED, "after_seconds": 150, "to": "bradycardic_arrest",
     "narration": INTO_END, "narration_ventilated": INTO_END, "debrief_note": (
       "The infusion was stopped after the tube and not restarted. " + END_NOTE),
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": "Intubated with the infusion off and not restarted. Prompted at 20 seconds (60 in normal mode).",
     "author_rationale": "Deterioration on inaction to a terminal phase."},
    {"when": None, "after_seconds": 360, "to": "bradycardic_arrest",
     "narration": INTO_END, "narration_ventilated": INTO_END, "debrief_note": END_NOTE,
     "allow_time_to_terminal": True,
     "terminal_opt_in_rationale": "Six minutes intubated with the infusion off.",
     "author_rationale": "Scheduled natural history to a terminal phase.",
     "unguarded_rationale": "The restart rule above is the exit."}],
   ecg("Rate 172."), ventilated=True),

 phase("bradycardic_arrest",
   "Bradycardia with poor perfusion, then arrest",
   "heart slowing",
   "Terminal. Reached from peri-arrest after 180 seconds without rescue, or after the tube "
   "without epinephrine.",
   48, 40, 20, 6, 70, 0, 3, [],
   ecg("Rate 48, sinus bradycardia.", pr=150, qtc=440), terminal=True,
   timeout_reason=(
     "His heart rate fell below sixty and he lost his pulse. Refractory anaphylaxis needed an "
     "epinephrine infusion, started once two IM doses had failed, with fluid. A tube without "
     "it, or a sedative, brings this sooner.")),

 phase("case_complete",
   "Handoff confirmed",
   "handed over",
   "Terminal phase entered when the learner confirms a handoff.",
   122, 102, 64, 24, 96, 1, 0, [],
   ecg("Rate 122."), terminal=True, inherit_vitals=True),
]
