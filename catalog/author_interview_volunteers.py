#!/usr/bin/env python3
"""Write each topic's `adjacent` topics and `volunteer` line, and each case's `must_ask`
safety screens, into the case sources (v0.18a).

    python3 catalog/author_interview_volunteers.py [AFRVR|CHFE|DIPH|MGCA ...]

A real patient answering "when did this start?" rarely stops at a time. They say how it
has gone since, and the learner needs fewer questions to see the picture. The engine
(composeInterview, volunteersFor) appends the `volunteer` line of each `adjacent` topic to
the first answer of a topic and counts the adjacent topic as asked.

Rules this file keeps:
- A volunteer line says nothing the topic's own answer does not say. It is a clause in the
  same voice, and it never repeats what the answer it rides on has just said.
- Safety screens (allergies, drugs, pregnancy, sexual and menstrual history, self-harm and
  intent, anticoagulant and bleeding history, goals of care, and in DIPH the discovery of
  the bottle) are in `must_ask`. They carry no volunteer line and no topic lists them, so
  the learner still has to ask. The validator enforces this.
- Nothing is volunteered while a global rule speaks for the patient, or while the case's
  `volunteer_blocked_when` holds: MGCA when she is confused, AFRVR in respiratory failure.
  CHFE keeps volunteering while breathless, in the same clipped speech as its answers.

Idempotent: re-running replaces what it wrote. CHFE and MGCA are written into the case
JSON; AFRVR and DIPH get a generated block in case_4_interview.py that build_case.py reads.

PROVENANCE: written by an AI assistant in September 2026 from the existing answers. Not
physician-reviewed.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CHFE_BREATHLESS = "phase is presentation OR phase is niv_supported OR phase is nitrate_responding"

def two(breathless, calm):
    """CHFE speaks in fragments until he is stabilizing, like its answers do."""
    return [{"when": CHFE_BREATHLESS, "value": breathless}, {"when": None, "value": calm}]

CASES = {
 # ------------------------------------------------------------------------ CHFE
 "CHFE": {
  "must_ask": ["allergies", "substance_use_stimulants", "pde5_inhibitor_use"],
  "blocked_when": None,
  "adjacent": {
   "onset": ["timing_progression"],
   "timing_progression": ["functional_baseline"],
   "character_of_dyspnea": ["chest_pain"],
   "severity": ["aggravating_factors"],
   "aggravating_factors": ["relieving_factors", "orthopnea"],
   "relieving_factors": ["orthopnea"],
   "orthopnea": ["paroxysmal_nocturnal_dyspnea"],
   "paroxysmal_nocturnal_dyspnea": ["orthopnea"],
   "leg_swelling": ["calf_pain_or_asymmetry", "weight_gain"],
   "weight_gain": ["leg_swelling", "abdominal_fullness"],
   "cough_and_sputum": ["hemoptysis", "fever_and_chills"],
   "chest_pain": ["palpitations"],
   "palpitations": ["syncope_and_dizziness"],
   "syncope_and_dizziness": ["palpitations"],
   "fever_and_chills": ["recent_illness_or_sick_contacts"],
   "recent_illness_or_sick_contacts": ["fever_and_chills"],
   "nausea_and_vomiting": ["abdominal_fullness"],
   "abdominal_fullness": ["nausea_and_vomiting"],
   "urine_output": ["medication_adherence"],
   "calf_pain_or_asymmetry": ["travel_immobility_surgery"],
   "travel_immobility_surgery": ["calf_pain_or_asymmetry"],
   "hemoptysis": ["cough_and_sputum"],
   "medication_adherence": ["dietary_sodium"],
   "dietary_sodium": ["medication_adherence"],
   "current_medications": ["medication_adherence"],
   "past_medical_history": ["past_surgical_history"],
   "past_surgical_history": ["past_medical_history"],
   "functional_baseline": ["timing_progression"],
  },
  "volunteer": {
   "timing_progression": two("'Worse... every day.'",
                             "'It's got worse every day, and this morning's the worst it's been.'"),
   "functional_baseline": two("'Normally... I do the stairs.'",
                              "'Before this I could get round the shops and do the stairs.'"),
   "chest_pain": two("'No pain. Just tight.'",
                     "'It's not a pain, mind. It's tightness from working to breathe.'"),
   "aggravating_factors": two("'Lying down... makes it worse.'",
                              "'Lying flat makes it much worse, and so does moving about.'"),
   "relieving_factors": two("'Sitting up... only thing.'",
                            "'Sitting up is the only thing that helps.'"),
   "orthopnea": two("'Four pillows now.'",
                    "'I've needed four pillows this week and still had to sit right up.'"),
   "paroxysmal_nocturnal_dyspnea": two("'Woke twice... gasping.'",
                                       "'Twice this week I've woken up in the night gasping.'"),
   "calf_pain_or_asymmetry": two("'Legs... don't hurt.'",
                                 "'My legs don't hurt, and neither one's red or hot.'"),
   "weight_gain": two("'Nine pounds up.'",
                      "'I'm about nine pounds up this last week.'"),
   "leg_swelling": two("'Legs... swollen. Both.'",
                       "'My legs have been swelling as well, both the same.'"),
   "abdominal_fullness": two("'Belly's tight.'",
                             "'My belly's been bloated and I fill up after a few mouthfuls.'"),
   # The calm cough answer already says there was no blood, so only the breathless one adds it.
   "hemoptysis": two("'No blood.'", None),
   "cough_and_sputum": two("'Dry cough.'",
                           "'I've had a dry cough, worse lying down.'"),
   "fever_and_chills": two("'No fever.'",
                           "'I've not had a fever or shivers.'"),
   "palpitations": two("'Heart's not... racing.'",
                       "'I've not felt my heart racing or skipping.'"),
   "syncope_and_dizziness": two("'Not passed out.'",
                                "'I've not blacked out or gone dizzy.'"),
   "recent_illness_or_sick_contacts": two("'Nobody's... been ill.'",
                                          "'Nobody at home's been ill, and I've not had a cold.'"),
   "nausea_and_vomiting": two("'Not sick.'",
                              "'I've not been sick, though.'"),
   "medication_adherence": two("'Ran out... water tablet. Five days.'",
                               "'I ran out of the water tablet about five days ago.'"),
   "dietary_sodium": two("'Christening... lot of salty food.'",
                         "'And I ate a lot of salty food at my granddaughter's christening at the weekend.'"),
   "travel_immobility_surgery": two("'Not been anywhere.'",
                                    "'I've not traveled or had any operations.'"),
   "past_surgical_history": two("'Stent. Gallbladder out.'",
                                "'The only operations were the stent and my gallbladder out years back.'"),
   "past_medical_history": two("'Heart attack... six years.'",
                               "'I had a heart attack six years ago, and I've got blood pressure and diabetes.'"),
  },
 },

 # ------------------------------------------------------------------------ MGCA
 "MGCA": {
  "must_ask": ["allergies", "pregnancy", "sexual_history", "menstrual_and_tampon", "social_history",
               "code_status_goals"],
  "blocked_when": "phase is adrenal_crisis OR phase is progressive_meningococcemia",
  "adjacent": {
   "onset": ["timing_progression"],
   "timing_progression": ["dizziness_syncope"],
   "character_of_symptoms": ["location_of_pain", "rash"],
   "location_of_pain": ["radiation_of_pain", "joint_pain"],
   "radiation_of_pain": ["location_of_pain"],
   "severity": ["aggravating_relieving"],
   "aggravating_relieving": ["severity"],
   "fever_and_chills": ["headache", "sick_contacts"],
   "headache": ["neck_stiffness", "photophobia"],
   "neck_stiffness": ["photophobia"],
   "photophobia": ["neck_stiffness"],
   "nausea_vomiting": ["diarrhea", "last_oral_intake"],
   "diarrhea": ["abdominal_pain"],
   "abdominal_pain": ["diarrhea"],
   "chest_pain": ["breathing"],
   "breathing": ["cough_sore_throat"],
   "urine_output": ["dysuria_gu_symptoms"],
   "dizziness_syncope": ["confusion"],
   "confusion": ["dizziness_syncope"],
   "cold_extremities": ["rash"],
   "joint_pain": ["location_of_pain"],
   "dysuria_gu_symptoms": ["urine_output"],
   "past_medical_history": ["vaccinations", "past_surgical_history"],
   "past_surgical_history": ["past_medical_history"],
   "current_medications": ["recent_antibiotics_healthcare"],
   "last_oral_intake": ["nausea_vomiting"],
   "vaccinations": ["past_medical_history"],
   "sick_contacts": ["travel_history"],
   "travel_history": ["tick_and_outdoor_exposure"],
   "recent_antibiotics_healthcare": ["current_medications"],
  },
  "volunteer": {
   "timing_progression": "\"It's got worse every hour. This morning my legs gave way and I ended up on the floor.\"",
   "fever_and_chills": "\"I've had shaking chills all night. My roommate said it was a hundred and three.\"",
   "dizziness_syncope": "\"When I sit up everything goes gray, though I haven't actually passed out.\"",
   "location_of_pain": "\"It's mostly the fronts of my thighs and my calves, both sides.\"",
   "radiation_of_pain": "\"It doesn't shoot anywhere, it's just in the muscles.\"",
   "joint_pain": "\"It's the muscles, not my joints. Nothing's swollen.\"",
   "rash": "\"And there are little dark red dots on my ankles and feet. My roommate saw them this morning.\"",
   "headache": "\"I've got a bit of a headache too, but it's the least of it.\"",
   "severity": "\"My legs are a nine out of ten.\"",
   "aggravating_relieving": "\"Moving makes it worse, and the ibuprofen did nothing.\"",
   "neck_stiffness": "\"My neck's fine, though. I can move it.\"",
   "photophobia": "\"The light doesn't bother me.\"",
   "diarrhea": "\"My bowels have been normal.\"",
   "last_oral_intake": "\"I haven't eaten since dinner last night.\"",
   "abdominal_pain": "\"My stomach doesn't hurt.\"",
   "breathing": "\"I'm breathing fast, but it doesn't feel hard.\"",
   "cough_sore_throat": "\"I had a scratchy throat two days ago, but no cough.\"",
   "sick_contacts": "\"A couple of people on our floor have had colds this week.\"",
   # The urine answer already says it does not burn.
   "dysuria_gu_symptoms": "\"And there's no discharge or anything down there.\"",
   "urine_output": "\"I haven't passed urine since about eleven last night, and it was really dark.\"",
   "confusion": "\"I keep losing track of things, and I don't really remember the ambulance.\"",
   "vaccinations": "\"I had all the vaccines the school made us get, including two meningitis ones.\"",
   "past_surgical_history": "\"The only operation I've had is my wisdom teeth.\"",
   "past_medical_history": "\"I'm never ill, and I've never been in hospital.\"",
   "recent_antibiotics_healthcare": "\"I haven't had antibiotics since I was a kid.\"",
   "current_medications": "\"I only take the pill, plus the ibuprofen overnight.\"",
   "nausea_vomiting": "\"I've been sick three times and I can't keep water down.\"",
   "travel_history": "\"I haven't been off campus all semester.\"",
   "tick_and_outdoor_exposure": "\"No hiking or camping, and no tick bites.\"",
  },
 },

 # ------------------------------------------------------------------------ AFRVR
 "AFRVR": {
  "must_ask": ["allergies", "caffeine_and_stimulants", "anticoagulant_history_and_bleeding",
               "code_status_goals_of_care"],
  "blocked_when": "phase is respiratory_failure",
  "adjacent": {
   "onset": ["timing_progression"],
   "timing_progression": ["exercise_tolerance_baseline"],
   "character_of_palpitations": ["prior_afib_or_palpitations", "chest_pain"],
   "dyspnea_character": ["orthopnea"],
   "severity": ["chest_pain"],
   "aggravating_factors": ["relieving_factors"],
   "relieving_factors": ["paroxysmal_nocturnal_dyspnea"],
   "chest_pain": ["syncope_presyncope"],
   "dizziness_lightheadedness": ["syncope_presyncope"],
   "orthopnea": ["paroxysmal_nocturnal_dyspnea"],
   "paroxysmal_nocturnal_dyspnea": ["orthopnea"],
   "leg_swelling": ["calf_pain_or_asymmetry", "weight_gain"],
   "weight_gain": ["leg_swelling"],
   "cough_and_sputum": ["fever_and_chills"],
   "fever_and_chills": ["recent_illness_or_sick_contacts"],
   "recent_illness_or_sick_contacts": ["fever_and_chills"],
   "prior_afib_or_palpitations": ["prior_heart_failure"],
   "prior_heart_failure": ["prior_afib_or_palpitations"],
   "past_medical_history": ["prior_heart_failure", "past_surgical_history"],
   "past_surgical_history": ["past_medical_history"],
   "current_medications": ["medication_adherence"],
   "medication_adherence": ["current_medications"],
   "alcohol_and_binge": ["social_history_smoking"],
   "social_history_smoking": ["alcohol_and_binge"],
   "travel_immobility_surgery": ["calf_pain_or_asymmetry"],
   "calf_pain_or_asymmetry": ["travel_immobility_surgery"],
   "nausea_and_vomiting": ["weight_gain"],
  },
  "volunteer": {
   "timing_progression": "'The breathing has got worse every hour since.'",
   "exercise_tolerance_baseline": "'A week ago I was walking the dog up the hill twice a day.'",
   "prior_afib_or_palpitations": "'And nobody's ever said my heart was irregular.'",
   "chest_pain": "'There's no pain with it, mind.'",
   "orthopnea": "'I can't lie flat at all.'",
   "relieving_factors": "'Sitting bolt upright is the only thing that helps.'",
   "paroxysmal_nocturnal_dyspnea": "'Twice last night I woke up feeling like I was drowning.'",
   "syncope_presyncope": "'I've not passed out, though.'",
   "calf_pain_or_asymmetry": "'My legs don't hurt, and they're not red or hot.'",
   "weight_gain": "'My trousers have got tight round the waist this week too.'",
   "leg_swelling": "'My legs have been swelling this last week, both of them.'",
   "fever_and_chills": "'I've had no fever or shivering.'",
   "recent_illness_or_sick_contacts": "'I've not had a cold, and nobody at home's been ill.'",
   "prior_heart_failure": "'Nobody's ever said my heart was weak.'",
   "past_surgical_history": "'My only operation was my gallbladder, years ago.'",
   "past_medical_history": "'I've got high blood pressure and diabetes.'",
   "medication_adherence": "'I take them every morning from a pill box.'",
   "current_medications": "'I take lisinopril, a statin and metformin.'",
   "social_history_smoking": "'I gave up smoking over twenty years ago.'",
   "alcohol_and_binge": "'I have a few beers at weekends, and I had four or five at a barbecue on Saturday.'",
   "travel_immobility_surgery": "'I've not traveled anywhere.'",
  },
 },

 # ------------------------------------------------------------------------ DIPH
 # The historian is her mother, so every line is the mother's voice.
 "DIPH": {
  "must_ask": ["allergies", "pregnancy", "alcohol_and_drugs", "smoking", "mental_health_history",
               "previous_self_harm", "suicidal_intent", "bottle_or_pills_found", "what_she_took"],
  "blocked_when": None,
  "adjacent": {
   "onset": ["last_seen_well", "what_she_was_doing"],
   "last_seen_well": ["what_she_was_doing"],
   "medicines_in_the_house": ["current_medications"],
   "past_medical_history": ["seizure_history", "current_medications"],
   "past_surgical_history": ["past_medical_history"],
   "current_medications": ["past_medical_history"],
   "who_lives_at_home": ["collateral_from_brother"],
   "bullying_and_school": ["relationship"],
   "relationship": ["sleep_and_appetite"],
   "fever_or_infection": ["travel_and_contacts", "rash"],
   "headache": ["neck_stiffness"],
   "neck_stiffness": ["rash"],
   "rash": ["neck_stiffness"],
   "vomiting": ["abdominal_pain"],
   "abdominal_pain": ["vomiting"],
   "chest_or_palpitations": ["breathing"],
   "breathing": ["chest_or_palpitations"],
   "vision_or_hallucinations": ["progression"],
   "last_oral_intake": ["vomiting"],
   "travel_and_contacts": ["fever_or_infection"],
   "what_ems_said": ["progression"],
  },
  "volunteer": {
   "last_seen_well": "'She was fine when I looked in at half seven this morning.'",
   "what_she_was_doing": "'She'd stayed off school today, so she was home on her own.'",
   "vision_or_hallucinations": "'In the ambulance she was reaching for people who weren't there.'",
   "current_medications": "'She doesn't take anything regularly.'",
   "seizure_history": "'She's never had a fit.'",
   "past_medical_history": "'She's never been in hospital.'",
   "collateral_from_brother": "'Her brother got home about three and says he didn't hear anything.'",
   "relationship": "'She broke up with her boyfriend three or four weeks ago.'",
   "sleep_and_appetite": "'She's been up half the night and not eating with us for weeks.'",
   "travel_and_contacts": "'Nobody at home or at school has been ill.'",
   "rash": "'She's gone red in the face and chest, but there are no spots.'",
   "neck_stiffness": "'She's not had a stiff neck.'",
   "fever_or_infection": "'She hasn't had so much as a cold.'",
   "abdominal_pain": "'She hasn't complained of her stomach.'",
   "vomiting": "'She hasn't been sick that I've seen.'",
   "breathing": "'She's breathing fast now, though.'",
   "chest_or_palpitations": "'She's never had anything wrong with her heart.'",
   "progression": "'She's got worse since I found her, and hotter.'",
  },
 },
}

NOTE = ("adjacent, volunteer, must_ask and volunteer_blocked_when were written by "
        "catalog/author_interview_volunteers.py (v0.18a). A first answer carries the volunteer "
        "line of each adjacent topic, and the adjacent topic counts as asked. must_ask topics are "
        "safety screens and are never volunteered. Every volunteer line restates part of that "
        "topic's own answer. Not physician-reviewed.")

def apply(topics, spec):
    ids = {t["topic"] for t in topics}
    for k, v in list(spec["adjacent"].items()) + [(k, None) for k in spec["volunteer"]]:
        assert k in ids, k
    for t in topics:
        t.pop("adjacent", None); t.pop("volunteer", None)
        adj = spec["adjacent"].get(t["topic"])
        if adj:
            for a in adj:
                assert a in ids and a not in spec["must_ask"], (t["topic"], a)
            t["adjacent"] = adj
        v = spec["volunteer"].get(t["topic"])
        if v is not None:
            assert t["topic"] not in spec["must_ask"], t["topic"]
            t["volunteer"] = v

def settings(spec):
    s = {"must_ask": spec["must_ask"], "volunteers_note": NOTE}
    if spec["blocked_when"]:
        s["volunteer_blocked_when"] = spec["blocked_when"]
    return s

def write_json_pack(prefix):
    p = os.path.join(ROOT, "cases", prefix, f"{prefix}-case.json")
    case = json.load(open(p, encoding="utf-8"))
    spec = CASES[prefix]
    iv = case["interview"]
    apply(iv["topics"], spec)
    for k in ("must_ask", "volunteer_blocked_when", "volunteers_note"):
        iv.pop(k, None)
    iv.update(settings(spec))
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(case, indent=1, ensure_ascii=False) + "\n")
    print(f"{prefix}: {len(spec['adjacent'])} topics volunteer, {len(spec['volunteer'])} volunteer lines, "
          f"{len(spec['must_ask'])} must-ask screens")

def write_py_pack(prefix):
    p = os.path.join(ROOT, "cases", prefix, "case_4_interview.py")
    src = open(p, encoding="utf-8").read()
    spec = CASES[prefix]
    B, E = "# ---- VOLUNTEERED ANSWERS (generated, do not edit by hand) ----", "# ---- END VOLUNTEERED ANSWERS ----"
    py = lambda o: (json.dumps(o, indent=1, ensure_ascii=False)
                    .replace(": true", ": True").replace(": false", ": False").replace(": null", ": None")
                    .replace("[null", "[None").replace(", null", ", None"))
    lines = [B, "# Written by catalog/author_interview_volunteers.py (v0.18a). See that file for the rules.",
             "ADJACENT = " + py(spec["adjacent"]),
             "VOLUNTEER = " + py(spec["volunteer"]),
             "VOLUNTEER_SETTINGS = " + py(settings(spec)),
             "for _t in TOPICS:",
             "    _t.pop('adjacent', None); _t.pop('volunteer', None)",
             "    if _t['topic'] in ADJACENT: _t['adjacent'] = ADJACENT[_t['topic']]",
             "    if _t['topic'] in VOLUNTEER: _t['volunteer'] = VOLUNTEER[_t['topic']]",
             E]
    block = "\n".join(lines) + "\n"
    if B in src:
        src = src[:src.index(B)] + block + src[src.index(E) + len(E) + 1:]
    else:
        src = src.rstrip("\n") + "\n\n" + block
    open(p, "w", encoding="utf-8", newline="\n").write(src)
    # the topics module is imported by build_case.py; check the ids against it
    import importlib.util
    spec_mod = importlib.util.spec_from_file_location("iv_" + prefix, p)
    m = importlib.util.module_from_spec(spec_mod); sys.path.insert(0, os.path.dirname(p))
    spec_mod.loader.exec_module(m)
    apply(m.TOPICS, spec)
    print(f"{prefix}: {len(spec['adjacent'])} topics volunteer, {len(spec['volunteer'])} volunteer lines, "
          f"{len(spec['must_ask'])} must-ask screens")

if __name__ == "__main__":
    for prefix in (sys.argv[1:] or ["AFRVR", "CHFE", "DIPH", "MGCA"]):
        (write_py_pack if prefix in ("AFRVR", "DIPH") else write_json_pack)(prefix)
