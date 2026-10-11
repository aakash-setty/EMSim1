"""TAKO part 4: the interview.

The patient answers for herself in every phase. When her pressure is low she answers in
fewer words with the same facts. Her daughter is at the bedside and is quoted in two
answers, because the daughter's explanation is the frame the learner has to see past.

Every answer is model output restating PATIENT["background"], which is also model output.

Once she is steadied, five answers about the pain and the sweating change, so that she
agrees with her own status line ("pain easing") and skin examination ("Sweating has
settled"). Those five answers were written by a model on 7 October 2026 and are listed in
TAKO-SEED.md as awaiting sign-off.
"""
from case_4_variants import SHARED

LOW = "phase is obstructed OR phase is shock_worse OR phase is shock_untreated"
EASED = "flag analgesia_given set"
STEADY = "phase is steadied"


def steadied(value):
    """A steadied-phase answer. Goes before any flag rule: phase rules first (section 4)."""
    return {"when": STEADY, "value": value}

TOPICS = []
NEGATIVES = {"fever_and_chills", "cough_sore_throat", "abdominal_pain", "headache",
             "leg_swelling_and_lying_flat", "back_or_tearing_pain", "bleeding_risk",
             "prior_heart_problems", "travel_history", "allergies"}
# past_surgical_history is not here: she reports a gallbladder operation, so the answer is
# not a denial (authoring 10.3).


def topic(tid, full, short, canonical=None, variants=None, echo=None, extra=None):
    s = SHARED.get(tid, {})
    rules = [{"when": LOW, "value": short}] + (extra or []) + [{"when": None, "value": full}]
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]), "answer": rules,
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    TOPICS.append(t)
    return t


# --------------------------------------------------------------- the pain
topic("onset",
  "'About an hour ago. We'd just got back to the hall after the service. I was standing "
  "talking to people and it came on all at once.'",
  "'An hour ago. At the reception.'")

topic("what_she_was_doing",
  "'We buried my husband this morning. Forty-one years. I was at the reception, somebody "
  "was telling me a story about him, and this started.' Her daughter says: 'She's been in "
  "pieces all week. It's her nerves.'",
  "'My husband's funeral. Today.'",
  canonical="What were you doing when it started?",
  variants=["What were you doing when it started?", "What brought this on?",
            "What happened today?", "Were you exerting yourself?", "Were you upset when it started?",
            "Has anything stressful happened?", "Tell me about today.", "Why were you at a funeral?",
            "Has there been a bereavement?", "Any recent shock or bad news?",
            "What was going on before the pain?", "Were you resting or active?",
            "Has something happened in the family?", "Any emotional stress lately?"],
  echo="what I was doing")

topic("timing_progression",
  "'It hasn't let up. It's as bad now as when it started, maybe worse.'",
  "'Worse. I feel faint now.'",
  extra=[steadied("'It's easing. Not gone, but better than it was.'")])

topic("character_of_symptoms",
  "'Crushing. Like something heavy sitting on my chest. It's a pressure, not a sharp pain.'",
  "'Crushing. Heavy.'",
  extra=[{"when": EASED, "value": "'It's still a pressure, but duller since you gave me that.'"}])

topic("location_of_pain",
  "'Right in the middle of my chest, behind the bone.'",
  "'The middle of my chest.'")

topic("chest_pain",
  "'Yes. In the middle of my chest, heavy, for the last hour. And my heart is pounding.'",
  "'Yes. My chest.'",
  extra=[steadied("'Yes, in the middle of my chest. It's still there, but it's easing.'")])

topic("radiation_of_pain",
  "'Down my left arm, and up into my jaw. Not through to my back.'",
  "'My left arm. My jaw.'")

topic("severity",
  "'Eight out of ten. I had three children and this is worse.'",
  "'Eight.'",
  extra=[steadied("'Less than it was. It's easing.'"),
         {"when": EASED, "value": "'It's come down. Maybe a five now.'"}])

topic("aggravating_relieving",
  "'Nothing makes it better. It's the same sitting up or lying back. Breathing in doesn't "
  "change it, and pressing on it doesn't change it.'",
  "'Nothing helps.'",
  extra=[steadied("'It's easing now. Sitting up or lying back makes no difference, and breathing "
                  "in doesn't change it.'")])

topic("back_or_tearing_pain",
  "'No, it isn't tearing and it isn't in my back. It's a weight on the front.'",
  "'No. Not my back.'",
  canonical="Is the pain tearing, or does it go through to your back?",
  variants=["Is it a tearing pain?", "Does it rip through to your back?",
            "Any pain between your shoulder blades?", "Is the pain in your back?",
            "Did it feel like something tore?", "Was it at its worst the instant it started?",
            "Any pain moving down your back?", "Does it feel like ripping?",
            "Any back pain with this?", "Is it sharp and tearing?"],
  echo="whether it's tearing")

# --------------------------------------------------------------- with it
topic("sweating",
  "'I'm drenched. I came over cold and clammy when it started.'",
  "'Yes. Cold and clammy.'",
  canonical="Have you been sweating?",
  variants=["Are you sweaty?", "Did you break out in a sweat?", "Any sweating with the pain?",
            "Have you been clammy?", "Did you go cold and clammy?", "Any diaphoresis?",
            "Are you hot or cold?", "Did you come over sweaty?", "Have you been perspiring?",
            "Any cold sweats?", "Any sweats?"],
  echo="sweating",
  extra=[steadied("'I was drenched. It's settled now.'")])

topic("nausea_vomiting",
  "'I feel sick. I haven't been sick, there's nothing in me to bring up.'",
  "'I feel sick. Not vomited.'")

topic("breathing",
  "'I can't get a full breath. It came on with the pain. I'm not wheezy.'",
  "'Short of breath. Yes.'")

topic("palpitations",
  "'My heart's racing and thumping. It feels regular, just fast and hard.'",
  "'It's racing.'",
  canonical="Can you feel your heart racing?",
  variants=["Any palpitations?", "Is your heart racing?", "Is your heart pounding?",
            "Can you feel your heartbeat?", "Does your heart feel irregular?",
            "Any fluttering in your chest?", "Is your heart skipping beats?",
            "Does your heart feel fast?", "Any thumping in your chest?", "Is your pulse racing?"],
  echo="my heart racing")

topic("dizziness_syncope",
  "'A bit lightheaded when they stood me up for the ambulance. I haven't passed out.'",
  "'Yes. Everything's going gray.'")

topic("leg_swelling_and_lying_flat",
  "'No swollen ankles. I sleep flat with one pillow and I've never woken up breathless.'",
  "'No. No swelling.'",
  canonical="Any ankle swelling, or trouble breathing when you lie flat?",
  variants=["Any swelling in your legs?", "Are your ankles swollen?", "Can you lie flat?",
            "How many pillows do you sleep on?", "Do you wake up short of breath at night?",
            "Any leg swelling?", "Any breathlessness lying down?", "Have your shoes been tight?",
            "Any fluid in your legs?", "Do you get breathless in bed?", "Any calf pain?",
            "Is one leg more swollen than the other?"],
  echo="swelling or lying flat")

topic("fever_and_chills",
  "'No fever. I've not been ill, just worn out.'", "'No.'")
topic("cough_sore_throat",
  "'No cough, no cold.'", "'No.'")
topic("abdominal_pain",
  "'No, my stomach's fine. It's all in my chest.'", "'No.'")
topic("headache",
  "'No headache.'", "'No.'")

# --------------------------------------------------------------- background
topic("prior_heart_problems",
  "'Never. No heart attack, no angina, nothing like this before. Nobody has ever told me I "
  "have a murmur, and I had a checkup in the spring.'",
  "'Never. No heart trouble.'",
  canonical="Have you ever had heart problems or been told you have a murmur?",
  variants=["Any heart problems before?", "Have you had a heart attack before?",
            "Have you ever had angina?", "Has anyone told you that you have a heart murmur?",
            "Have you had chest pain like this before?", "Any stents or bypass?",
            "Have you seen a cardiologist?", "Have you ever had an echo?",
            "Any history of heart failure?", "Has this ever happened before?",
            "Any valve problems?", "Have you had a stress test?"],
  echo="my heart before this")

topic("past_medical_history",
  "'High blood pressure and high cholesterol. That's all. No diabetes.'",
  "'Blood pressure. Cholesterol.'")

topic("past_surgical_history",
  "'I had my gallbladder out twenty years ago. Nothing since.'",
  "'Gallbladder. Years ago.'")

topic("current_medications",
  "'Amlodipine for my blood pressure and atorvastatin. I took them this morning. No aspirin, "
  "and nothing for my nerves.'",
  "'Amlodipine. Atorvastatin.'")

topic("bleeding_risk",
  "'No blood thinners. I've never had a stroke or a bleed, no ulcers, and no operations "
  "lately. I haven't fallen or hit my head.'",
  "'No blood thinners. No bleeding.'",
  canonical="Are you on blood thinners, or have you had any bleeding or a stroke?",
  variants=["Are you on any blood thinners?", "Do you take warfarin?", "Any history of stroke?",
            "Have you ever had a stroke?",
            "Any blood when you open your bowels?",
            "Have you ever had bleeding in your brain?", "Any stomach ulcers or bleeding?",
            "Any recent surgery?", "Any recent head injury?", "Do you bruise or bleed easily?",
            "Any black stools?", "Have you had a bleed before?", "Any anticoagulants?",
            "Any reason you couldn't have a clot-busting drug?"],
  echo="blood thinners and bleeding")

topic("allergies",
  "'None. I can take aspirin.'", "'No allergies.'")

topic("social_history",
  "'I've never smoked. A glass of wine at Christmas. No drugs. I live on my own now, my "
  "daughter is twenty minutes away.'",
  "'Never smoked. I live alone now.'")

topic("family_history",
  "'My father had a heart attack at seventy. My mother lived to ninety.'",
  "'My father. Heart attack at seventy.'")

topic("last_oral_intake",
  "'I've hardly eaten since he died. Five days. A bit of toast, cups of tea I didn't "
  "finish. Nothing today.'",
  "'Hardly anything. For days.'")

topic("functional_baseline",
  "'I walk every day, two miles. I do my own garden. I was fine last week.'",
  "'Fit. I walk every day.'")

topic("travel_history",
  "'No, I haven't been anywhere. No long journeys.'", "'No.'")

topic("code_status_goals",
  "'I want you to do everything. I've got grandchildren.' Her daughter nods. 'Whatever she "
  "needs.'",
  "'Everything. Please.'")

GLOBAL_RULES = [
 {"when": "phase is case_complete", "value": "She has gone to the catheterization laboratory.",
  "note": "No live phase is at alertness 2 or 3. This rule exists because the list may not be empty."},
]

OUT_OF_SCOPE = [
 {"when": LOW, "value": "She shakes her head. 'I can't think. I'm sorry.'"},
 {"when": None, "value": "'I'm sorry, I don't follow. Can you ask me another way?'"},
]

AUTHORING_NOTES = {
 "voice": "A 68-year-old retired teacher. Plain, precise, frightened. She does not minimize the pain.",
 "the_daughter": ("Quoted in two answers. She says it is nerves. That is a relative's opinion "
                  "and the case does not endorse it."),
 "no_global_rule": ("No phase is at alertness 2 or 3 and nothing in this case intubates her. "
                    "The one global rule speaks for her after the handoff, because the list "
                    "may not be empty. If a phase is added at alertness 2, add it to that rule."),
}

KEY_TOPICS = ["onset", "radiation_of_pain", "prior_heart_problems", "current_medications",
              "bleeding_risk", "allergies", "last_oral_intake", "what_she_was_doing"]

ADJACENT = {
 "onset": ["what_she_was_doing"],
 "location_of_pain": ["radiation_of_pain"],
 "character_of_symptoms": ["sweating"],
 "breathing": ["leg_swelling_and_lying_flat"],
 "past_medical_history": ["prior_heart_problems"],
}
VOLUNTEER = {
 "what_she_was_doing": "'We buried my husband this morning.'",
 "radiation_of_pain": "'It goes down my left arm and into my jaw.'",
 "sweating": "'And I came over cold and clammy.'",
 "leg_swelling_and_lying_flat": "'I've no swollen ankles and I sleep flat.'",
 "prior_heart_problems": "'I've never had heart trouble.'",
}
VOLUNTEER_SETTINGS = {
 "must_ask": ["allergies", "bleeding_risk", "current_medications", "social_history",
              "code_status_goals", "last_oral_intake"],
 "volunteer_blocked_when": LOW,
 "volunteers_note": "Hand-written for this pack. Nothing is volunteered while her pressure is low.",
}
for _t in TOPICS:
    if _t["topic"] in ADJACENT:
        _t["adjacent"] = ADJACENT[_t["topic"]]
    if _t["topic"] in VOLUNTEER:
        _t["volunteer"] = VOLUNTEER[_t["topic"]]

# ---------------------------------------------------------------- shared phrasings
# Topic -> the shared concepts in catalog/interview_phrasings.py it draws phrasings from.
# build_case.py expands the bank from this at build time (catalog/interview_expand.py), so
# the expansion is never stored here. A topic absent from the map keeps only its own
# hand-written variants. Every concept named here counts as covered by this case.
TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"], "character_of_symptoms": ["character_general"],
 "location_of_pain": ["location_pain"], "radiation_of_pain": ["radiation_pain"], "severity": ["severity"],
 "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"],
 "chest_pain": ["chest_pain"], "nausea_vomiting": ["nausea_vomiting"], "breathing": ["breathing_sob"],
 "palpitations": ["palpitations"], "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"],
 "leg_swelling_and_lying_flat": ["leg_swelling", "orthopnea", "pnd", "calf_pain"],
 "fever_and_chills": ["fever_chills"], "cough_sore_throat": ["cough_sore_throat"],
 "abdominal_pain": ["abdominal_pain"], "headache": ["headache"],
 "past_medical_history": ["pmh"], "past_surgical_history": ["psh"], "current_medications": ["meds"],
 "bleeding_risk": ["anticoag"], "allergies": ["allergies"],
 "social_history": ["social_history", "smoking", "alcohol", "substance_use"],
 "family_history": ["family_history"], "last_oral_intake": ["last_oral_intake"],
 "functional_baseline": ["functional_baseline"], "travel_history": ["travel", "travel_immobility_surgery"],
 "code_status_goals": ["code_status"],
 "what_she_was_doing": ["emotional_trigger"], "back_or_tearing_pain": ["back_pain", "tearing_pain"],
 "sweating": ["sweating"], "prior_heart_problems": ["prior_cardiac", "prior_hf"],
}

# Concepts and cover tags this case's answers cover without drawing phrasings from them
# (a concept in catalog/interview_phrasings.py, or a tag in BANK_ONLY_TAGS in
# catalog/interview_out_of_scope.py). Only used to keep those questions out of the
# out-of-scope bank. List one only when an authored answer really covers the question.
EXTRA_COVERED = ["character_general", "cough_sputum", "prior_hf", "stroke_history", "gi_bleeding"]
