"""SCOOT part 2: the action spine, tags, flags, prompts, credit and the one follow-up.

Nothing is tagged harmful and nothing halts the case (model default, SCOOT-SEED.md section
0). Every clinical judgment here is model output awaiting a physician's signature, except
the learning goals and the states, which Aakash Setty approved on 19 October 2026.

Four hidden case actions carry what no flag can (authoring 19 and 22.2):

  neuro_reexamined             a neuro exam done in the decline phase
  neurosurgery_updated         a neurosurgery call made in any phase after arrival
  osmotherapy_for_herniation   mannitol or hypertonic saline given in the herniation phase
  post_intubation_sedation     sedation or analgesia given once the tube is in

The neurosurgery consult needs a resulted head CT, as a prerequisite whose failure message
is the neurosurgeon's request (authoring 9.5). It sets neurosurgery_called, which guards
the herniation clock.
"""

ACTIONS = []


def act(cid, tag, **kw):
    a = {"catalog_id": cid, "tag": tag}
    a.update(kw)
    ACTIONS.append(a)
    return a


ALWAYS = lambda v: [{"when": None, "value": v}]

PRES = "phase is presentation"
DECL = "phase is decline"
HERN = "phase is herniation"
TEMP = "phase is temporized"
LATE = HERN + " OR " + TEMP
AFTER_ARRIVAL = DECL + " OR " + HERN + " OR " + TEMP
TUBED = "flag intubated set"
CT_R = "(study ct_head resulted OR study ct_cta_head_and_neck resulted)"
NO_CT = "NOT study ct_head ordered AND NOT study ct_cta_head_and_neck ordered"
CALLED = "flag neurosurgery_called set"

# Markers only in fields the interface strips (authoring 10.3): action debrief notes.
MEMORY = " [UNVERIFIED: written by a model from memory, no source opened]"
BULLOCK = " [UNVERIFIED: Bullock et al. 2006, read through a summarizing tool]"
BTF = " [UNVERIFIED: BTF 4th edition, read through a summarizing tool]"
CRASH3 = " [UNVERIFIED: CRASH-3, read through a summarizing tool]"

# =====================================================================  FIRST MINUTES

act("attach_monitor",
    [{"when": PRES, "value": "critical"}, {"when": None, "value": "recommended"}],
    prompt={"deadline_seconds": 20, "guard": PRES,
            "text": "He isn't on the monitor yet."},
    debrief_note=(
      "Nothing shows until the monitor is on. In a head injury the monitor matters less than "
      "you would think, and this case is built on that: his numbers barely moved when his "
      "brain did. Watch it anyway, because hypoxia and hypotension are what turn a brain "
      "injury into a worse one." + BTF))

act("insert_iv", ALWAYS("recommended"),
    debrief_note=(
      "Every drug this case can need goes through a line: the antiemetic, the induction "
      "agents and the osmotherapy. Get it in early, while he is still cooperative."))

for cid in ("central_venous_catheter_triple_lumen", "central_venous_catheter_cordis",
            "intraosseous_line"):
    act(cid, ALWAYS("neutral"),
        debrief_note=(
          "Not needed for anything except concentrated saline, which the catalog gives only "
          "through a central line. Mannitol or 3 percent saline run through a peripheral "
          "line. Not scored."))

act("c_collar", ALWAYS("recommended"),
    debrief_note=(
      "A fall over the handlebars at speed with a loss of consciousness is a mechanism for a "
      "neck injury. On arrival he had no midline tenderness and talked normally, and some "
      "would clear his neck clinically. Once his GCS fell he could not be cleared by "
      "examination at all, so his neck is protected until it is imaged." + MEMORY))

act("ct_c_spine", ALWAYS("recommended"),
    debrief_note=(
      "Normal. Worth sending with the head CT: he had a dangerous mechanism and lost "
      "consciousness, and after the decline his exam could no longer clear his neck. It costs "
      "a few seconds in the same scanner." + MEMORY))

act("ct_head", ALWAYS("critical"),
    # No prompt on arrival (owner, 20 October 2026: "eliminate the CT head prompt at 2:30").
    # Getting the scan on arrival is the learner's own decision.
    prompt={"deadline_seconds": 50, "guard": "NOT " + PRES + " AND " + NO_CT,
            "text": "He hit his head hard and he hasn't had a CT of his head yet."},
    debrief_note=(
      "This is the scan that shows the problem, and he needed it from the door. A loss of "
      "consciousness, amnesia for the crash, a headache and a scalp hematoma each justify a "
      "head CT by any decision rule, and the scooter, the speed and the missing helmet add to "
      "it.\n\n"
      "The scan is yours to read. Scroll from the skull base to the vertex on the brain "
      "window, then look again on the bone window. His shows a biconvex collection over the "
      "right temporoparietal convexity that stops at the sutures, with a linear fracture of "
      "the temporal squama beneath it. That shape is an epidural hematoma: arterial blood, "
      "usually from the middle meningeal artery, stripping the dura off the skull. A "
      "crescent that crosses the sutures would be a subdural.\n\n"
      "The darker pockets inside the clot are the swirl sign: unclotted blood, which means it "
      "is still bleeding. That is why he declined while you watched.\n\n"
      "The size matters to the neurosurgeon. The guideline says an epidural over 30 mL "
      "should be evacuated whatever the GCS, and his was about 50 mL, about 19 mm thick, "
      "with about 6 mm of shift. Your decision is simpler than that: any traumatic epidural "
      "hematoma is a call to neurosurgery now." + BULLOCK))

act("ct_cta_head_and_neck", ALWAYS("neutral"),
    debrief_note=(
      "Shows the hematoma as a plain head CT would, and no arterial injury. Accepted as his "
      "head imaging. A vessel study was not needed: nothing in his story or exam suggested a "
      "neck vessel injury. Not scored."))

act("mri_mra_head_and_neck", ALWAYS("discouraged"),
    debrief_note=(
      "An MRI shows the hematoma, but it takes far longer than a CT, takes him away from the "
      "bay, and is not what a neurosurgeon operates from in an emergency. In acute head "
      "trauma the scan is a CT." + MEMORY))

for cid, note in [
  ("complete_blood_count_cbc",
   "Normal. A platelet count before surgery is the reason to send it."),
  ("coagulation_panel",
   "Normal. Any clotting problem changes what goes into him before the OR, so this is sent "
   "for every intracranial bleed. He is on no blood thinner."),
  ("blood_type_and_screen",
   "He is going to the operating room. The surgeon and the anesthetist want a group and "
   "screen done before he gets there."),
  ("fingerstick_blood_sugar",
   "Normal. Any patient whose consciousness falls gets a glucose, because a low sugar is "
   "quick to find and quick to fix. It was not the answer here."),
]:
    act(cid, ALWAYS("recommended"), debrief_note=note)

ECG_NOTE = (
  "Sinus rhythm, and in herniation sinus bradycardia. The slow pulse in herniation is "
  "Cushing's response to the pressure inside his head, not a heart problem. Not scored.")
act("ecg_12_lead", ALWAYS("neutral"), debrief_note=ECG_NOTE + MEMORY)

# =====================================================================  THE AIRWAY

act("intubate_rapid_sequence",
    [{"when": LATE, "value": "critical"}, {"when": None, "value": "discouraged"}],
    flags_set=["intubated"],
    follow_ups_triggered=["sedation_after_intubation"],
    prompt={"deadline_seconds": 30, "guard": "(" + LATE + ") AND NOT " + TUBED,
            "text": "He isn't protecting his airway anymore."},
    debrief_note=(
      "When he had herniated, with a GCS of 7 or 8 and slow, snoring breathing, he needed a "
      "tube. A definitive airway at GCS 8 or less is standard teaching, and a herniating "
      "patient also needs his oxygen and his carbon dioxide controlled.\n\n"
      "Before that, at GCS 15 or 12, he was talking, protecting his airway and minutes from "
      "an anesthetist. A tube then treats the number rather than the patient. It also takes "
      "away the exam that tells you he is getting worse: after a tube, the neuro exam reads "
      "'cannot be assessed', and the pupils are all you have left. Intubate for a reason: "
      "he cannot protect his airway, cannot oxygenate or ventilate, or is about to travel "
      "somewhere you cannot follow him.\n\n"
      "After the tube in herniation, a short period of mild hyperventilation is a bridge to "
      "surgery that many use. The simulator cannot set the ventilator, so it is not "
      "scored." + MEMORY))

for cid, note in [
  ("etomidate_bolus",
   "An induction agent that keeps the pressure up, which matters in a brain injury."),
  ("ketamine_bolus",
   "An induction agent that keeps the pressure up. The old worry that it raises "
   "intracranial pressure has not held up, and many use it in head injury."),
  ("propofol_bolus",
   "Drops the pressure more than etomidate or ketamine. In herniation, a fall in pressure "
   "is a fall in the brain's blood supply, so use it carefully."),
  ("midazolam_bolus",
   "Sedation. After the tube it counts as sedation. Before it, it clouds the exam you are "
   "following."),
  ("rocuronium_bolus", "A paralytic for the tube."),
  ("succinylcholine_bolus", "A paralytic for the tube."),
]:
    kw = {}
    if cid in ("midazolam_bolus", "propofol_bolus", "ketamine_bolus"):
        kw["also_satisfies"] = [{"id": "post_intubation_sedation", "when": TUBED}]
    act(cid, ALWAYS("neutral"), debrief_note=note + " Not scored." + MEMORY, **kw)

for cid in ("propofol_infusion", "ketamine_infusion"):
    act(cid, ALWAYS("neutral"),
        also_satisfies=[{"id": "post_intubation_sedation", "when": TUBED}],
        debrief_note=(
          "Sedation after the tube. A brain-injured patient who wakes on the ventilator "
          "coughs and strains, and his intracranial pressure rises with it. Not scored "
          "itself." + MEMORY))

act("post_intubation_sedation", ALWAYS("neutral"),
    hidden=True, display_name="Sedation after the tube",
    expectation_label="Sedation once he was intubated",
    debrief_note=(
      "Not an order. The simulator credits this when sedation or analgesia is given once the "
      "tube is in, and the follow-up reads it. A learner never sees it."))

# =====================================================================  NEUROSURGERY

act("consult_neurosurgeon", ALWAYS("critical"),
    state_changing=True,
    expectation_label="Neurosurgery called once the CT was back",
    flags_set=["neurosurgery_called"],
    prerequisites=[{"when": CT_R,
                    "failure_message": ("Neurosurgery will want to see his head CT first. Call "
                                        "them as soon as it's back.")}],
    also_satisfies=[{"id": "neurosurgery_updated", "when": AFTER_ARRIVAL}],
    # No prompt on arrival (owner, 19 October 2026: a nudge at 3:30 in the default mode
    # came too soon). Calling with the scan is the learner's decision there, which is goal
    # G2. After arrival it fires with or without a scan: a learner without one is sent for
    # it by the prerequisite's message.
    # 25 s and 35 s (75 s and 105 s in the default mode) so both land inside the 120 s
    # decline (owner, 19 October 2026: herniation at 6:00).
    prompt={"deadline_seconds": 25, "guard": "NOT " + PRES,
            "text": "Neurosurgery hasn't heard about him yet.",
            "escalation": {"deadline_seconds": 35,
                           "text": "Nobody has called neurosurgery about him."}},
    debrief_note=(
      "The call that decides how this goes. Any traumatic epidural hematoma is a call to "
      "neurosurgery the moment you see it. Do not wait for the pupils, for Cushing's "
      "response or for the final report. The guideline reserves nonoperative management for "
      "small, thin clots without shift in a patient with a good GCS and no focal deficit, "
      "and even then under neurosurgical observation. His met none of that.\n\n"
      "Call again when he changes. A neurosurgeon who booked the OR for a talking patient "
      "will move faster for a drowsy, vomiting one, but only if someone tells them. In the "
      "simulator, a second call in a later phase is how that is credited. In real life it is "
      "a sentence: his GCS was 15 and is now 12, his pupils are equal, he vomited, and here "
      "is the scan.\n\n"
      "The simulator will not put the call through before a head CT has resulted. In real "
      "life a heads-up call for a falling GCS before the scan is reasonable, and the scan "
      "takes minutes." + BULLOCK))

act("neurosurgery_updated",
    [{"when": AFTER_ARRIVAL, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Neurosurgery told he got worse",
    expectation_label="Neurosurgery told when he changed",
    prompt={"deadline_seconds": 40, "guard": CALLED,
            "text": "Neurosurgery hasn't heard that he's changed."},
    debrief_note=(
      "Not an order. Credited when neurosurgery is called in any phase after arrival.\n\n"
      "A plan made on an old exam is out of date the moment the exam changes. The OR was "
      "booked for a man at GCS 15. At GCS 12 and vomiting, he is a more urgent case, and the "
      "neurosurgeon needs to hear it from you rather than find out when they arrive. This is "
      "model opinion, not a guideline."))

act("neuro_reexamined",
    [{"when": DECL, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Neuro exam repeated after he changed",
    expectation_label="Neuro exam repeated once he got drowsy",
    prompt={"deadline_seconds": 15, "guard": DECL,
            "text": "He's harder to wake than he was a few minutes ago."},
    debrief_note=(
      "Not an order. Credited by a neuro exam done after he became drowsy.\n\n"
      "The exam is the vital sign in a head injury. His went from GCS 15 to 12 while his "
      "monitor barely moved and his pupils stayed equal. The only way to see that is to "
      "examine him again, and the moment to do it is the moment someone says he is "
      "different. A fall of two points or more needs action now." + MEMORY))

# =====================================================================  OSMOTHERAPY

OSMO_NOTE = (
  "Osmotherapy draws water out of the brain and lowers the pressure inside the skull for a "
  "while. It is a bridge to the surgeon, not a treatment for the clot.\n\n"
  "Once his right pupil blew, it was the drug that mattered most, and mannitol or "
  "hypertonic saline both count. Before that the picture differs by phase. At GCS 15 there "
  "was no sign of raised pressure and nothing to treat. After the decline, some give it on "
  "the way to the OR for an acute deterioration and some wait for signs of herniation. "
  "Good doctors disagree, and the case accepts either.\n\n"
  "Mannitol is a diuretic, so watch the pressure afterwards. Concentrated saline goes "
  "through a central line.")
for cid in ("mannitol_bolus", "hypertonic_saline_25_bolus", "hypertonic_saline_3_infusion"):
    act(cid, [{"when": PRES, "value": "discouraged"}, {"when": None, "value": "neutral"}],
        also_satisfies=[{"id": "osmotherapy_for_herniation", "when": HERN}],
        debrief_note=OSMO_NOTE + MEMORY)

act("osmotherapy_for_herniation",
    [{"when": HERN, "value": "critical"}, {"when": None, "value": "neutral"}],
    hidden=True, display_name="Osmotherapy once the pupil blew",
    expectation_label="Osmotherapy for the blown pupil",
    prompt={"deadline_seconds": 20, "guard": HERN,
            "text": "His right pupil is blown.",
            "escalation": {"deadline_seconds": 60,
                           "text": "His right pupil is still blown and nothing has gone in for it."}},
    debrief_note=(
      "Not an order. Credited by mannitol or hypertonic saline given once the pupil blew. A "
      "dose given earlier did not count, because his brain needed one now.\n\n"
      "A blown pupil, a slow pulse and a rising pressure in a head injury is herniation. "
      "Osmotherapy and an airway buy the minutes the surgeon needs." + MEMORY))

# =====================================================================  WHAT NOT TO FIX

act("labetalol_bolus", ALWAYS("discouraged"),
    expectation_label="Lowering his blood pressure",
    debrief_note=(
      "There was no pressure to treat early on. When he herniated, his pressure climbed and "
      "his pulse slowed. That is Cushing's response: the brain pushing blood in against a "
      "rising pressure inside the skull. Bringing the pressure down cuts the brain's blood "
      "supply at the worst moment. The guideline for severe brain injury sets a floor for "
      "the systolic pressure, 110 at his age. Treat the pressure inside his "
      "head, and leave the one on the monitor alone." + BTF))

act("atropine_bolus",
    [{"when": LATE, "value": "discouraged"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "His slow pulse in herniation was Cushing's response, not a heart problem, and his "
      "pressure was high. Atropine treats the number and not the cause. The treatment for "
      "this bradycardia is lowering the pressure inside his head." + MEMORY))

act("lower_head_of_bed", ALWAYS("discouraged"),
    debrief_note=(
      "Lying flat raises the pressure inside the skull. A head-injured patient is nursed with "
      "the head of the bed up at about 30 degrees, with the neck protected." + MEMORY))

act("d5_1_2_ns_infusion", ALWAYS("discouraged"),
    debrief_note=(
      "Hypotonic fluid moves water into an injured brain. If he needs fluid it is an "
      "isotonic crystalloid." + MEMORY))

act("normal_saline_1l_bolus", ALWAYS("neutral"),
    expectation_label="Crystalloid bolus",
    debrief_note=(
      "He was never hypotensive, so fluid was not needed. If his pressure had fallen, "
      "isotonic crystalloid to keep the systolic at 110 or more is right: low pressure is "
      "one of the two things that make a brain injury worse. Not scored." + BTF))

act("ibuprofen", ALWAYS("discouraged"),
    debrief_note=(
      "An anti-inflammatory weakens platelet function, and he is bleeding inside his head. "
      "Acetaminophen is the analgesic for a head injury." + MEMORY))

act("acetaminophen", ALWAYS("neutral"),
    debrief_note="A reasonable analgesic for his headache. Not scored.")

for cid in ("fentanyl_bolus", "morphine_bolus"):
    act(cid, ALWAYS("neutral"),
        also_satisfies=[{"id": "post_intubation_sedation", "when": TUBED}],
        debrief_note=(
          "A small dose for his headache is kind. Before the tube, an opioid can blunt the "
          "exam you are following, so give little and examine before you give it. After the "
          "tube it counts as analgesia for the ventilator. Not scored." + MEMORY))

# =====================================================================  OTHER TREATMENTS

act("ondansetron",
    [{"when": DECL, "value": "recommended"}, {"when": None, "value": "neutral"}],
    debrief_note=(
      "Vomiting raises the pressure inside his head, and a drowsy patient who vomits can "
      "aspirate. An antiemetic once he vomited was right. It does not change what is "
      "happening inside his skull." + MEMORY))

act("metoclopramide", ALWAYS("neutral"),
    also_satisfies=[{"id": "ondansetron", "when": DECL}],
    debrief_note="A reasonable antiemetic. Counted in place of ondansetron once he vomited.")

act("tranexamic_acid", ALWAYS("neutral"),
    debrief_note=(
      "Contested. In CRASH-3, tranexamic acid within three hours did not significantly "
      "reduce head-injury deaths overall. In the subgroup with mild to moderate injury, GCS 9 "
      "to 15, it did, and that subgroup result may be a chance finding. Some give it, some do "
      "not, and the case accepts both. It is not what saves this patient: the surgeon "
      "is." + CRASH3))

act("levetiracetam_bolus", ALWAYS("neutral"),
    debrief_note=(
      "Early seizure prophylaxis after a significant brain injury is common practice, and "
      "the neurosurgeon will usually ask for it. Not part of the decision in this case. Not "
      "scored." + MEMORY))

act("fos_phenytoin", ALWAYS("neutral"),
    debrief_note=(
      "The older agent for early seizure prophylaxis after severe brain injury. Not part of "
      "the decision in this case. Not scored." + MEMORY))

# =====================================================================  OTHER CONSULTS

for cid, note in [
  ("consult_critical_care",
   "He needs an operating room before an intensive care bed. The intensivist says so."),
  ("consult_general_surgery",
   "At a trauma center the trauma surgeon may lead his care, and calling is reasonable. "
   "His injury is isolated to the head, so the call that matters is neurosurgery."),
  ("consult_neurology",
   "A traumatic bleed is a neurosurgical problem. The neurologist sends you there."),
]:
    act(cid, ALWAYS("neutral"), state_changing=False, debrief_note=note + " Not scored.")

act("handoff_submit", ALWAYS("neutral"),
    display_name="Submit handoff",
    flags_set=["handoff_submitted"], state_changing=True,
    debrief_note="Completion of the case. Scored on level of care and diagnoses.")

# ---------------------------------------------------------------- examinations
EXAM_TAGS = {
  "exam_airway": "recommended", "exam_breath": "recommended", "exam_circ": "recommended",
  "exam_heent": "recommended", "exam_neck": "recommended",
}
EXAM_NOTES = {
  "exam_airway": (
    "Talking in sentences on arrival, then slurred but protecting his airway, then snoring "
    "in herniation. The airway exam is part of the decision about a tube."),
  "exam_breath": "Normal until herniation, when his breathing slows. That is the brainstem.",
  "exam_circ": "Normal throughout. His circulation was never the problem.",
  "exam_heent": (
    "The scalp hematoma over the temple is the sign of where he hit, and the pupils are the "
    "sign of herniation. The pupils stayed equal through the decline and blew only once the "
    "brain herniated, which is why waiting for them is waiting too long."),
  "exam_neck": (
    "No midline tenderness on arrival. After the decline his answers could not be trusted, "
    "so his neck could not be cleared by examination."),
  "exam_neuro": (
    "The exam that runs this case. GCS 15 on arrival, 12 in the decline, 7 in herniation "
    "with a fixed right pupil and less movement on the left. Record each part, eyes, voice "
    "and motor, so that the next examiner can see what changed."),
  "exam_card": "Normal.",
  "exam_pulm": "Clear. No chest injury.",
  "exam_abd": "Soft and nontender. No abdominal injury.",
  "exam_gu": "Nothing to find.",
  "exam_back": "No spinal tenderness or step.",
  "exam_msk": "No long bone injury. His palms are grazed.",
  "exam_skin": "Road rash on both palms, where he put his hands out.",
  "exam_psych": "Repetitive questioning on arrival is the amnesia, not anxiety.",
}
for cid, note in EXAM_NOTES.items():
    if cid == "exam_neuro":
        act(cid, ALWAYS("critical"),
            also_satisfies=[{"id": "neuro_reexamined", "when": DECL}],
            # 60 s, so 3:00 in the default mode (owner, 20 October 2026).
            prompt={"deadline_seconds": 60, "guard": PRES,
                    "text": "He's talking, but nobody has done a neuro exam on him yet."},
            debrief_note=note + MEMORY)
    else:
        act(cid, ALWAYS(EXAM_TAGS.get(cid, "neutral")), debrief_note=note + MEMORY)

FOLLOW_UPS = [
 {"id": "sedation_after_intubation",
  "graded": False,   # post-intubation care, never graded (owner, 23 October 2026)
  "triggered_by": ["intubate_rapid_sequence"],
  "applies_when": TUBED,
  "deadline_seconds": 60,
  # A hidden target credited only once the tube is in (authoring 22.2), so fentanyl given
  # for the headache earlier does not discharge it.
  "satisfied_by": ["post_intubation_sedation"],
  "nurse_prompt": "He's tubed. What do you want running to keep him sedated?",
  "debrief_note": (
    "After the tube, the induction drug wears off in minutes. A brain-injured patient who "
    "wakes paralyzed or coughs on the tube raises his intracranial pressure. Sedation and "
    "analgesia go in once the tube is in.")},
]
