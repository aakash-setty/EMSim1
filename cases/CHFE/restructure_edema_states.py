#!/usr/bin/env python3
"""ONE-TIME MIGRATION for CHFE-case.json. Kept as the record of what changed and why;
re-running it on an already-migrated file fails its own assertions, which is intended.

WHAT CHANGED, AND WHY IT WAS ASKED FOR
The case had one improvement phase and one gate into it: positive pressure AND a nitrate,
together, in a single step. That made the two treatments indistinguishable. A learner who
put the mask on and stopped saw nothing at all happen, and a learner who gave both could
not tell which one had done the work. The author's instruction was to separate them:
the mask should visibly move the patient from severe to moderate pulmonary edema, and only
a nitrate should take him to mild, with the oxygen saturation starting two points lower
than before.

Separating them needs the two-by-two the treatments actually describe, so three phases are
added:

  niv_supported                   positive pressure, afterload untreated  (moderate)
  nitrate_responding              afterload treated, no positive pressure (moderate)
  impending_respiratory_failure   neither, for long enough that he tires  (severe, worse)

and the existing `stabilizing` becomes the both-treatments corner (mild). `improving` is
unchanged in meaning: `stabilizing` plus the diuretic.

THE OXYGENATION CONVENTION IS UNCHANGED AND IS WHY THE NUMBERS LOOK ODD
`oxygen_saturation` on a phase is the UNSUPPORTED baseline, exactly as the phases_note has
always said. What the monitor reads is that baseline plus the positive-pressure effect
while the mask is on. So:

  phase                          baseline   mask on   monitor reads
  presentation                      85        no          85
  niv_supported                     85        yes         89
  nitrate_responding                88        no          88
  stabilizing                       90        yes         94
  improving                         90        yes         94
  impending_respiratory_failure     80      either      80 or 84

The mask moves the number and not the lung: `niv_supported` carries the same 85 as arrival,
and the four points on the screen are the mask. The nitrate moves the lung: its baseline
rises to 88 with no mask on the patient at all. That contrast is the case's first learning
objective made mechanical rather than asserted, and it is the reason the baseline convention
was kept rather than folding the mask into the phase.

Diuresis still moves heart rate, blood pressure and respiratory rate and moves the
saturation by nothing: `improving` carries the same 90 as `stabilizing`. That was the
previous migration's teaching point and it survives this one intact.

WHAT IS NOW FORCED, AND HOW HARD
Three things, in ascending order of force:
  1. `stabilizing` and `improving` are unreachable without a nitrate. The mask alone
     plateaus at moderate.
  2. `nitroglycerin_infusion` is critical in every phase where it has not been given, so
     it is on the expected list of every run and appears in the debrief as missed.
  3. A patient left without a nitrate tires. Four minutes in `presentation` with neither
     treatment, or four minutes in `niv_supported` with the mask but no nitrate, reaches
     `impending_respiratory_failure`. Five minutes in `nitrate_responding` with no mask
     reaches the same place.

`impending_respiratory_failure` is NOT terminal and has no clock of its own. Both
treatments together rescue it to `stabilizing`; intubation leads where intubation always
led. This case still cannot kill the patient, which is deliberate: `medical_student` is in
its target level list and the deterioration is there to teach that delay costs something,
not to teach reflexes. See AFRVR's `respiratory_failure` for the same shape.

THE NEW SHARED FLAG
`nitrate_given` is set by both nitrate routes alongside their own flags, so every guard
that means "a nitrate has been given" is one atom rather than a parenthesised pair. The
route-specific flags are untouched: `nitro_infusion_running` still drives the
blood-pressure-cycling follow-up and the post-intubation rescue.

PROMPTS THAT NAMED A NUMBER
Two prompts quoted vital signs that were true only in `presentation`. They now fire in
phases with different numbers, so the numbers are out and the observation stays. The
nitrate prompt gains a guard, `NOT flag nitrate_given set`, so the nurse does not ask for
a nitrate in the phase the nitrate created, and an escalation that names the infusion,
which is what a learner who gave a tablet needs to hear.

NOT CHANGED, DELIBERATELY
The chest radiograph does not improve with the patient. Radiographic clearing lags clinical
improvement by hours and a film that cleared in ten minutes would teach something false.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE

case = json.load(open(CASE))

ids = [p["id"] for p in case["phases"]]
assert ids == ["presentation", "stabilizing", "improving", "post_intubation_hypotension",
               "intubated_stabilized", "halted", "case_complete"], \
    "phases are not in the pre-migration shape: %r" % (ids,)
assert "restructure_edema_states" not in case.get("migrations", []), "already applied"

P = {p["id"]: p for p in case["phases"]}
A = {a["catalog_id"]: a for a in case["case_actions"]}

MODERATE = "phase is niv_supported OR phase is nitrate_responding"
DISTRESSED = ("phase is presentation OR phase is niv_supported "
              "OR phase is nitrate_responding OR phase is impending_respiratory_failure")

# ---------------------------------------------------------------- 1. phases
def appearance(distress, alert):
    return {"distress_level": distress, "alertness_level": alert,
            "pupil_size": "normal", "pupil_reactivity": "reactive"}

HANDOFF = {"when": "action handoff_submit taken", "to": "case_complete"}
TUBE = {"when": "flag intubated set", "to": "post_intubation_hypotension"}

P["presentation"]["label"] = "Severe hypertensive acute cardiogenic pulmonary edema"
P["presentation"]["clinical_description"] = (
    "Severe respiratory distress with hypoxaemia and marked hypertension; warm, "
    "well-perfused, congested. Severe pulmonary edema. Nohria profile B.")
P["presentation"]["vitals"]["oxygen_saturation"] = 85
P["presentation"]["transitions"] = [
    HANDOFF,
    dict(TUBE, author_note=(
        "Intubation in a preload-dependent, vasodilated patient predictably drops the "
        "blood pressure. Modelled as certain here for teaching; see review packet, this "
        "is the most debatable transition in the case.")),
    # There is deliberately no "both at once" rule here. Two orders submitted in the same
    # batch are two log entries and the engine re-checks the transitions after each, so a
    # learner who sends the mask and the nitrate together passes through the intermediate
    # phase in the same second and arrives at `stabilizing` anyway. A combined rule would
    # be unreachable, and unreachable rules with confident comments on them are how a case
    # comes to describe behaviour it does not have.
    {"when": "flag on_niv set", "to": "niv_supported",
     "author_note": (
        "The mask alone. Work of breathing and oxygenation improve and the edema goes "
        "from severe to moderate; the driving pressure is untouched, so this is as far "
        "as it goes. Reached in passing, for one instant, by a learner who submits the "
        "mask and the nitrate in the same batch.")},
    {"when": "flag nitrate_given set", "to": "nitrate_responding",
     "author_note": (
        "The nitrate alone. The edema itself improves because a large part of it is "
        "redistribution against afterload, but he is still doing all the work of "
        "breathing himself.")},
    {"when": "NOT flag on_niv set AND NOT flag nitrate_given set", "after_seconds": 240,
     "measured_from": "phase_entry", "to": "impending_respiratory_failure",
     "narration": ("He's wearing out on me. He's stopped answering and he's gone grey "
                   "round the lips."),
     "debrief_note": (
        "Four minutes of severe hypertensive pulmonary edema with neither positive "
        "pressure nor a vasodilator. Both were asked for by name before this fired. The "
        "patient is not lost: the mask and a nitrate together still turn him around, and "
        "nothing in this case kills him. What has been lost is the part of the history he "
        "can no longer give you."),
     "author_rationale": (
        "AUTHOR SIGNATURE REQUIRED. The claim is that a sixty-five year old man in "
        "hypertensive acute cardiogenic pulmonary edema at a saturation of 85 percent and "
        "a respiratory rate of 32 begins to tire inside four minutes if nothing is done. "
        "Four minutes is compressed against real disease tempo the way every deadline in "
        "these packs is. The guard names both treatments so that either one alone stops "
        "it, which is the fairness claim: a learner who did something is not punished for "
        "not doing everything.")},
]

P["stabilizing"]["label"] = "Mild pulmonary edema on positive pressure and a nitrate"
P["stabilizing"]["clinical_description"] = (
    "Work of breathing and oxygenation improving on non-invasive ventilation with "
    "afterload reduction; pulmonary edema now mild. Still congested and not yet diuresed.")
P["stabilizing"]["vitals"].update({"heart_rate": 104, "systolic_bp": 144,
                                   "diastolic_bp": 84, "respiratory_rate": 22,
                                   "oxygen_saturation": 90})
P["stabilizing"]["appearance"] = appearance(1, 0)
P["stabilizing"]["short_label"] = "responding"
P["stabilizing"]["transitions"] = [
    HANDOFF, TUBE,
    {"when": "flag diuretic_given set", "to": "improving"},
]

P["improving"]["clinical_description"] = (
    "Decongesting on positive pressure, a nitrate and a loop diuretic. Mild pulmonary "
    "edema, clearing.")
P["improving"]["vitals"].update({"heart_rate": 92, "systolic_bp": 132, "diastolic_bp": 80,
                                 "respiratory_rate": 18, "oxygen_saturation": 90})
P["improving"]["appearance"] = appearance(0, 0)
P["improving"]["transitions"] = [HANDOFF, TUBE]

P["case_complete"]["vitals"].update({"heart_rate": 92, "systolic_bp": 132,
                                     "diastolic_bp": 80, "respiratory_rate": 18,
                                     "oxygen_saturation": 94})

niv_supported = {
    "id": "niv_supported",
    "label": "Moderate pulmonary edema on positive pressure, afterload untreated",
    "clinical_description": (
        "Work of breathing and oxygenation improved on non-invasive ventilation. The "
        "pulmonary edema is moderate rather than severe and the blood pressure driving it "
        "has not been treated."),
    "vitals": {"heart_rate": 110, "systolic_bp": 178, "diastolic_bp": 98,
               "respiratory_rate": 28, "oxygen_saturation": 85, "temperature_c": 36.8},
    "appearance": appearance(2, 0),
    "terminal": False,
    "transitions": [
        HANDOFF, TUBE,
        {"when": "flag nitrate_given set", "to": "stabilizing"},
        {"when": "NOT flag nitrate_given set", "after_seconds": 240,
         "measured_from": "phase_entry", "to": "impending_respiratory_failure",
         "narration": ("He's tiring under the mask. He's stopped talking to me and his "
                       "pressure is no better than when he came in."),
         "debrief_note": (
            "The mask bought four minutes and the afterload driving the edema was never "
            "treated. This is the commonest way this version of the case is lost: "
            "positive pressure looks like an answer because the saturation on the screen "
            "improves, and the number improved because of the mask rather than because "
            "the patient did."),
         "author_rationale": (
            "AUTHOR SIGNATURE REQUIRED. Non-invasive ventilation failure in hypertensive "
            "acute cardiogenic pulmonary edema is real and is the usual route to "
            "intubation in these patients. Four minutes is a teaching tempo, not a "
            "measured interval.")},
    ],
    "short_label": "on the mask",
}

nitrate_responding = {
    "id": "nitrate_responding",
    "label": "Moderate pulmonary edema after vasodilation, no positive pressure",
    "clinical_description": (
        "Afterload reduction has moved the edema from severe to moderate. He is doing all "
        "of the work of breathing himself, at a rate around thirty, with no positive "
        "pressure."),
    "vitals": {"heart_rate": 108, "systolic_bp": 152, "diastolic_bp": 88,
               "respiratory_rate": 30, "oxygen_saturation": 88, "temperature_c": 36.8},
    "appearance": appearance(2, 0),
    "terminal": False,
    "transitions": [
        HANDOFF, TUBE,
        {"when": "flag on_niv set", "to": "stabilizing"},
        {"when": "NOT flag on_niv set", "after_seconds": 300,
         "measured_from": "phase_entry", "to": "impending_respiratory_failure",
         "narration": ("He's still pulling hard and he's starting to flag. He's gone quiet "
                       "on me."),
         "debrief_note": (
            "The right drug and no support for the breathing. The vasodilator is treating "
            "the cause and it is not doing the work of breathing for him; five minutes at "
            "a respiratory rate of thirty in a man of sixty-five ends the same way whether "
            "or not the pressure has come down."),
         "author_rationale": (
            "AUTHOR SIGNATURE REQUIRED. Longer than the other two deadlines on the "
            "judgement that a treated afterload buys more time than an untreated one. "
            "Five minutes is a teaching tempo.")},
    ],
    "short_label": "nitrate running",
}

impending = {
    "id": "impending_respiratory_failure",
    "label": "Tiring, with hypercapnic respiratory failure",
    "clinical_description": (
        "Exhausted after minutes of untreated work. Hypercapnic and drowsy with a "
        "saturation in the low eighties. Still warm and still hypertensive: the problem "
        "has not changed, only how much of it he can compensate for."),
    "vitals": {"heart_rate": 126, "systolic_bp": 176, "diastolic_bp": 98,
               "respiratory_rate": 38, "oxygen_saturation": 80, "temperature_c": 36.8},
    "appearance": appearance(3, 2),
    "terminal": False,
    "transitions": [
        HANDOFF, TUBE,
        {"when": "flag on_niv set AND flag nitrate_given set", "to": "stabilizing",
         "author_note": (
            "The only way out that is not a tube, and it needs both treatments because he "
            "arrives here having had at most one of them. Authoring both separately would "
            "return him to the phase he came from the instant he arrived, since one of "
            "the two flags is already set.")},
    ],
    "short_label": "tiring",
}

case["phases"] = [P["presentation"], niv_supported, nitrate_responding, P["stabilizing"],
                  P["improving"], impending, P["post_intubation_hypotension"],
                  P["intubated_stabilized"], P["halted"], P["case_complete"]]

case["phase_notes"] = {
    "count_justification": (
        "Eight clinical phases plus two terminal phases, against the three to six the "
        "authoring requirements ask for. This is the largest phase count in any pack and "
        "it is a deliberate overrun: six of the eight are the two-by-two of positive "
        "pressure against vasodilation plus the two states either side of it, and "
        "collapsing any pair of them puts the case back to being unable to say which "
        "treatment did what. Flagged for the design owner in the review packet."),
    "deterioration_path": (
        "Two deterioration phases now, and they are different in kind. "
        "impending_respiratory_failure is reached by the clock when a treatment is "
        "missing; it is recoverable and not terminal, and both treatments together turn "
        "it around. post_intubation_hypotension is reached by intubating, whenever that "
        "happens; it is recoverable and not terminal. Neither can kill the patient: no "
        "transition in this case reaches a terminal phase on the clock, and the only "
        "terminal phases are the handoff and a harmful action."),
}

case["phases_note"] = (
    "label is the full clinical description used in the debrief; short_label is what fits "
    "on the monitor beside the vitals. Keep short_label to a few words. "
    "oxygen_saturation is authored as the UNSUPPORTED baseline in every non-terminal "
    "phase: what the monitor reads is that baseline plus whatever vital_effects are "
    "acting, and the only thing in this case that acts on the saturation is positive "
    "pressure, worth four points while the mask is on. The baselines are 85 on arrival, "
    "85 on the mask, 88 on a nitrate with no mask, 90 with both, 90 after diuresis and 80 "
    "when he has tired. Read that column twice: the mask moves the number by four and "
    "moves the baseline by nothing, and the nitrate moves the baseline by three with no "
    "mask on the patient at all. That is the difference between making a number look "
    "better and making a patient better, and it is the case's first learning objective "
    "expressed as arithmetic. Diuresis moves heart rate, blood pressure and respiratory "
    "rate and moves the saturation by nothing, which is the second. The terminal phases "
    "are exempt from effects and read exactly as authored. case_complete is one authored "
    "snapshot regardless of the path taken to it: it reads 94, the number a patient on "
    "the mask with a nitrate running has been showing, so handing off does not jump the "
    "monitor on the way to the debrief.")

# ---------------------------------------------------------------- 2. flags
for act, own in (("nitroglycerin_infusion", "nitro_infusion_running"),
                 ("nitroglycerin_sublingual", "nitro_sl_given")):
    a = A[act]
    assert a["flags_set"] == [own], (act, a["flags_set"])
    a["flags_set"] = [own, "nitrate_given"]

case["flag_namespace_note"] = case["flag_namespace_note"].rstrip() + (
    " nitrate_given is set by both nitrate routes alongside the route-specific flag, so "
    "that a guard meaning 'a nitrate has been given' is one atom. The route-specific "
    "flags still exist and still differ: nitro_infusion_running is what the "
    "blood-pressure-cycling obligation and the post-intubation rescue read, because "
    "stopping an infusion is an act and swallowing a tablet cannot be undone.")

# ---------------------------------------------------------------- 3. tags
def tags(act, rules):
    A[act]["tag"] = rules

tags("niv_bipap_cpap", [
    {"when": "phase is post_intubation_hypotension OR phase is intubated_stabilized",
     "value": "neutral"},
    {"when": ("phase is presentation OR phase is nitrate_responding "
              "OR phase is impending_respiratory_failure"), "value": "critical"},
    {"when": None, "value": "recommended"},
])
tags("nitroglycerin_infusion", [
    {"when": "phase is post_intubation_hypotension OR phase is intubated_stabilized",
     "value": "harmful"},
    {"when": ("phase is presentation OR phase is niv_supported "
              "OR phase is nitrate_responding OR phase is impending_respiratory_failure"),
     "value": "critical"},
    {"when": None, "value": "recommended"},
])
# Harmful in every phase where the patient is warm, hypertensive and perfusing, which is
# now six phases rather than three. Missing one of them would have made a pressor merely
# neutral in the phases this migration added.
WARM = ("phase is presentation OR phase is niv_supported OR phase is nitrate_responding "
        "OR phase is stabilizing OR phase is improving "
        "OR phase is impending_respiratory_failure")
for act in ("norepinephrine_infusion", "epinephrine_push_dose", "dobutamine_infusion"):
    rules = A[act]["tag"]
    hit = [r for r in rules if r.get("when") == "phase is presentation OR phase is stabilizing OR phase is improving"]
    assert len(hit) == 1, act
    hit[0]["when"] = WARM

# ---------------------------------------------------------------- 4. prompts
niv = A["niv_bipap_cpap"]["prompt"]
assert "87" in niv["text"]
niv["text"] = ("He's working really hard to breathe and his sat is low on the oxygen "
               "he's got. Do you want to do something more for his breathing? I can get "
               "the CPAP mask on him.")
niv["escalation"]["text"] = ("He's still tripoding and pulling with his neck muscles. "
                             "I've got CPAP and BiPAP both at the bedside. Do you want "
                             "either of them on him?")

ntg = A["nitroglycerin_infusion"]["prompt"]
assert ntg["guard"] == "NOT flag intubated set"
ntg["guard"] = "NOT flag intubated set AND NOT flag nitrate_given set"
ntg["text"] = ("His pressure is still right up, doctor. Do you want anything for the "
               "blood pressure while we're sorting out his breathing?")
# 60 rather than the 75 it was, and the reason is the difficulty multiplier rather than
# anything clinical. Prompt deadlines are multiplied by the mode's prompt_multiplier and
# deterioration deadlines are not, so in the default mode (normal, x3) a prompt authored at
# 75 seconds is heard at 225, fifteen seconds before a deterioration authored at 240. The
# validator's fairness rule compares the authored numbers and sees a lead of 165 seconds.
# At 60 the played lead in the default mode is 60 seconds, which is the number that matters
# because normal is the mode a case starts in.
ntg["deadline_seconds"] = 60
ntg["escalation"] = {
    "deadline_seconds": 140,
    "text": ("Nothing has come off his blood pressure. Do you want me to get a "
             "nitroglycerin infusion mixed and running?"),
}

# The adherence question is critical in every phase, so it was being prompted at a
# sedated patient after intubation and would now be prompted at one too exhausted to
# answer. Guarded to the phases where he can still speak.
adh = A["interview_topic_medication_adherence"]["prompt"]
assert adh.get("guard") is None
adh["guard"] = ("NOT flag intubated set AND NOT phase is impending_respiratory_failure")

case["prompt_cap_recommendation"] = {
    "per_phase": 3,
    "rationale": (
        "Three new things per phase, and an escalation is exempt from the cap since "
        "engine v0.9. Prompts are scheduled only for actions that are critical in the "
        "phase being entered, so each phase carries its own short list. In presentation "
        "the nurse can say three things before the 240-second deterioration: the mask at "
        "45 seconds, the nitrate at 75 and the tracing at 90, with the chest film at 150 "
        "and the adherence question at 210 suppressed. Both treatments the deterioration "
        "guard names are therefore heard, with the mask escalating at 90 and the nitrate "
        "at 150 on top. In niv_supported the list is the nitrate at 75 and the adherence "
        "question at 210; in nitrate_responding it is the mask at 45, the nitrate at 75 "
        "and the adherence question at 210."),
}

# ---------------------------------------------------------------- 5. vital effects
niv_fx = A["niv_bipap_cpap"]["vital_effects"]
assert len(niv_fx) == 1 and niv_fx[0]["delta"] == 3
niv_fx[0]["delta"] = 4
niv_fx[0]["note"] = (
    "Four points, held for as long as the mask is on, in every phase where it is on. "
    "Alveolar recruitment and the reduction in work of breathing are the mechanism and "
    "they persist rather than wearing off, which is why there is no duration here. The "
    "guard removes it at intubation: the mask comes off and the ventilator phases author "
    "their own saturation. It was three points before the phases were split. The size is "
    "an author's teaching choice, not a measured quantity, and no trial supports a "
    "specific number. What it is doing structurally is carrying the whole of the mask's "
    "contribution to the number on the screen, because the phase baselines carry none of "
    "it: niv_supported is authored at the same 85 as arrival.")

# The two nitrate routes carried five points of saturation for thirty seconds each. That
# excursion existed because nothing else in the case moved the number, and the phases now
# do: a nitrate moves the patient to a phase whose baseline is three points higher and
# stays there. Keeping both would have counted the same drug twice, and the transient
# would have said the effect wears off while the phase said it does not.
for act in ("nitroglycerin_infusion", "nitroglycerin_sublingual"):
    fx = A[act].get("vital_effects")
    assert fx and fx[0]["key"] == "nitrate_spo2", act
    A[act].pop("vital_effects")

# ---------------------------------------------------------------- 6. metadata
m = case["metadata"]
m["estimated_runtime_seconds"] = 600
objectives = m["learning_objectives"]
assert not any("afterload is the lever" in o for o in objectives)
objectives.insert(2, (
    "Separate what positive pressure does from what a vasodilator does. The mask improves "
    "oxygenation and the work of breathing and leaves the driving pressure untreated; "
    "afterload is the lever on the edema itself. Neither alone finishes this patient."))

case.setdefault("migrations", []).append("restructure_edema_states")

json.dump(case, open(OUT, "w"), indent=1, ensure_ascii=False)
open(OUT, "a").write("\n")
print("phases:", [p["id"] for p in case["phases"]])
print("wrote", OUT)
