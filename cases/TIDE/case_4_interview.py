"""TIDE part 4: the interview.

His wife answers. He is too short of breath for more than a few words, and from the
failing phase on he cannot answer at all. From the moment he is too sick to stay with (the
tiring phase, after the tube) she has been taken to the family room, which is a global rule.

Every answer is model output written from PATIENT["background"] and the owner's structure.
Facts the owner's structure did not supply are listed in TIDE-SEED.md section 3.7 as
model-added: the home thermometer reading, the father's heart attack, the knee scope, his
work, the missed flu shot, and every pertinent negative except allergies and recent
antibiotics or hospital stays. Neither he nor his wife names a diagnosis or quotes a number
from this visit.
"""
from case_4_variants import SHARED

LATE = "phase is failing_support"

TOPICS = []
NEGATIVES = {"allergies", "recent_antibiotics_healthcare", "home_oxygen", "leg_swelling",
             "travel_history", "sick_contacts", "abdominal_pain", "diarrhea", "palpitations"}


def topic(tid, she, he=None, late=None, facts=None, canonical=None, more=None):
    """`she` is the wife's answer. `he` is the few words he manages before she goes on, in
    phases 1 to 6. In the failing phase she answers alone (`late`, or `she` again)."""
    s = SHARED[tid]
    default = (f"'{he}' he gets out, and his wife goes on. '{she}'" if he
               else f"His wife answers. '{she}'")
    rules = [{"when": LATE, "value": f"His wife answers for him. '{late or she}'"},
             {"when": None, "value": default}]
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(s["variants"]) + list(more or []), "answer": rules, "echo": s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


def fact(fid, asks, value, restate=False):
    f = {"id": fid, "asks": asks, "value": [{"when": None, "value": value}]}
    if restate:
        f["restate"] = True
    return f


# ------------------------------------------------------------------ the illness
topic("onset",
  "It started Saturday. Fever and shaking chills first, then the cough the next day.",
  he="Saturday.",
  facts=[fact("when", ["what day", "how many days", "how long ago", "when exactly"],
              "His wife: 'Saturday. Four days.'", restate=True),
         fact("first", ["what came first", "how did it start", "first symptom"],
              "His wife: 'The fever and the shakes came first. The cough the day after.'")])

topic("timing_progression",
  "He was sick but managing until last night. Since then he can't get his breath, and today "
  "he couldn't walk across the kitchen without stopping.",
  he="Worse... since last night.",
  late="He's much worse than when we came in. He doesn't know where he is.")

topic("cough_sputum",
  "A deep cough, all day and night. He's bringing up thick phlegm, rusty brown, like the color "
  "of a brick.",
  he="Coughing... all night.",
  facts=[fact("color", ["what color", "what does it look like", "color of the phlegm", "green or yellow"],
              "His wife: 'Rusty brown. Like a brick.'", restate=True),
         fact("blood", ["any blood", "bright red"],
              "His wife: 'Not bright red blood. It's that rusty color.'")])

topic("hemoptysis",
  "Not bright red blood, no. The phlegm is that rusty brown color.",
  he="No blood.")

topic("chest_pain",
  "A sharp pain on the right side of his chest when he breathes in or coughs. It started with "
  "the cough. He holds his side.",
  he="Right side... when I breathe.",
  facts=[fact("where", ["where is it", "which side", "where does it hurt"],
              "His wife: 'The right side, low down.'", restate=True),
         fact("breathing", ["worse when he breathes", "worse with breathing", "worse with coughing",
                            "pleuritic"],
              "His wife: 'It catches him every time he breathes in or coughs.'")],
  more=["Does it go to his arm or jaw?", "Any crushing pain?"])

topic("breathing",
  "Since last night he can't get his breath. He's never been like this. He can't finish a "
  "sentence.",
  he="Can't... get a breath.",
  late="He can't get his breath at all now, and he's stopped making sense.")

topic("fever_and_chills",
  "Shaking chills every night since Saturday, soaking sweats. The thermometer said a hundred "
  "and two last night.",
  he="Freezing... then sweating.",
  facts=[fact("temp", ["how high", "did you check", "what was the temperature"],
              "His wife: 'A hundred and two on our thermometer last night.'", restate=True)])

topic("confusion",
  "He's been himself, just exhausted. Sharp as ever until today.",
  late="He's mixing things up now. He asked me where we were.")

topic("dizziness_syncope",
  "He nearly went down when he stood up this morning. He sat on the bed till it passed. He "
  "didn't black out.",
  he="Dizzy... when I stood.")

topic("urine_output",
  "He's hardly been to the bathroom today. Once this morning, and it was dark.")

topic("nausea_vomiting",
  "He hasn't thrown up. He just hasn't wanted to eat.")

topic("abdominal_pain",
  "No, his stomach's fine. It's his chest and his breathing.",
  he="No.")

topic("diarrhea",
  "No, no diarrhea. His bowels are normal.")

topic("headache",
  "A bit of a headache with the fever. Nothing bad. His neck isn't stiff.")

topic("leg_swelling",
  "No, his legs are fine. No swelling and no pain in his calves.",
  more=["Any pain in his calves?", "Is one leg bigger than the other?"])

topic("orthopnea",
  "He's never had trouble lying flat before. Last night he sat up in the chair because of the "
  "cough.")

topic("palpitations",
  "Not that he's said. Just the breathing.",
  he="No.")

# ------------------------------------------------------------------ background
topic("past_medical_history",
  "High blood pressure and diabetes, the tablet kind. Nobody's ever said anything about his "
  "lungs. No heart problems, nothing with his immune system.",
  he="Pressure... sugar.",
  more=["Has he ever been told he has emphysema?"])

topic("past_surgical_history",
  "Just a knee scope, years ago.")

topic("current_medications",
  "Lisinopril for his pressure and metformin for his sugar. He took both this morning. No "
  "steroids, no inhalers, no blood thinners.",
  facts=[fact("which", ["what does he take", "which medicines", "what tablets"],
              "His wife: 'Lisinopril and metformin.'", restate=True),
         fact("today", ["did he take them today", "this morning", "last dose"],
              "His wife: 'He took both this morning.'"),
         fact("steroids", ["any steroids", "prednisone", "any inhalers", "blood thinners"],
              "His wife: 'No steroids, no inhalers, no blood thinners.'")])

topic("allergies",
  "No allergies. He's had penicillin before with no trouble.",
  he="None.")

topic("recent_antibiotics_healthcare",
  "No, he hasn't been in the hospital in years, and he hasn't had antibiotics this year. "
  "Nobody's ever told him he had a resistant infection.",
  he="No.")

topic("home_oxygen",
  "No, never. He's never needed oxygen or a breathing machine.",
  he="No.")

topic("social_history",
  "He smokes, about three quarters of a pack a day, since he was eighteen. A couple of beers "
  "on the weekend. No drugs. He works for the city water department, and it's just the two "
  "of us at home.",
  facts=[fact("smoking", ["how much does he smoke", "pack years", "cigarettes a day", "does he smoke"],
              "His wife: 'About three quarters of a pack a day, since he was eighteen.'", restate=True),
         fact("alcohol", ["does he drink", "any alcohol", "how much does he drink"],
              "His wife: 'A couple of beers on the weekend. Nothing this week.'"),
         fact("work", ["what does he do", "where does he work", "his job"],
              "His wife: 'He works for the city water department.'")])

topic("vaccinations",
  "He didn't get his flu shot this year. I don't know about the pneumonia one.")

topic("sick_contacts",
  "Nobody at home has been sick, and nobody at his work that he's said.")

topic("travel_history",
  "No, we haven't been anywhere. No trips, no hotels.")

topic("family_history",
  "His father had a heart attack at seventy. Nothing with lungs that I know of.")

topic("functional_baseline",
  "He works full time and walks the dog every evening. Last week he was fine.",
  he="Walk the dog... every night.")

topic("last_oral_intake",
  "Some soup at lunch, and sips of water since. He hasn't wanted much.")

topic("code_status",
  "He'd want everything done. We've talked about it. He'd want the breathing machine if he "
  "needs it.",
  he="Everything.",
  late="He'd want everything done, the breathing machine too. We've talked about it.")

topic("diabetes_control",
  "Tablets only. He doesn't check his sugar much. The doctor says it could be better.")

# ------------------------------------------------------------------ presenting story
# Authoring 8.2: a greeting or an open question gets a brief history of the present illness.
# Variants copied from DKA (questions, not facts).
TOPICS.insert(0, {
 "topic": "presenting_story",
 "canonical": "What happened?",
 "variants": ["Hi", "Hello", "Hi there", "Hey", "Hi, I'm one of the doctors.", "Hello, I'm the doctor.",
              "What's going on?", "What is going on?", "What is going on today?", "What's been going on?",
              "What happened?", "What happened today?", "What brings you in?", "What brings you in today?",
              "What brought you here?", "What brings you to the emergency department?", "What's wrong?",
              "What's the matter?", "What seems to be the problem?", "Tell me what happened.",
              "Can you tell me what happened?", "Tell me what's going on.", "What's the story?",
              "How can I help you today?", "Why are you here today?", "Talk me through what happened."],
 "answer": [
   {"when": LATE,
    "value": ("His wife answers for him. 'He's had a fever and a terrible cough since Saturday. Since "
              "last night he can't get his breath, and now he's not making sense.'")},
   {"when": None,
    "value": ("'Can't catch my breath,' he gets out, and his wife goes on. 'He's had a fever and a "
              "bad cough since Saturday. Since last night he can't breathe, so I drove him in.'")}],
 "echo": "what happened",
 "authoring_note": ("Authoring 8.2. Written by a model from this case's own onset, cough, fever and "
                    "breathing answers and the arrival handover. It leaves the sputum color, the chest "
                    "pain and the history behind their own questions. Not physician reviewed."),
})

# ------------------------------------------------------------------ global rules
GONE = ("phase is tiring OR phase is post_induction_collapse OR phase is ventilated OR "
        "flag intubated set OR phase is arrest OR phase is case_complete")
GLOBAL_RULES = [
 {"when": GONE,
  "value": ("His wife has been taken to the family room while the team works on him. There's "
            "nobody at the bedside to ask right now."),
  "note": ("Section 8.5. Covers the phases at alertness 2 or 3 (tiring, post_induction_collapse, "
           "ventilated) and the intubated patient, as the validator requires, and the two terminal "
           "phases.")},
]

OUT_OF_SCOPE = [
 {"when": LATE, "value": "His wife shakes her head. 'I don't know. I'm sorry. Please just help him.'"},
 {"when": None, "value": "His wife looks at him, then at you. 'I'm not sure what you mean. Can you ask it another way?'"},
]

AUTHORING_NOTES = {
 "who_is_answering": (
   "His wife, in the third person, because he can manage only three or four words a breath. He "
   "adds a few words of his own on some topics in phases 1 to 6. From phase 7 he is confused and "
   "she answers alone. Owner default Q12 of 4 November 2026."),
 "speech_gating": (
   "Section 8.5's shorter answer for a distressed phase is carried by the wife: the facts are the "
   "same in every phase, and only his own words drop out."),
 "diagnosis_disclosure": (
   "Neither names a diagnosis. The rusty phlegm is described, not named. The thermometer reading "
   "is her own, from home."),
 "model_added": "TIDE-SEED.md section 3.7 lists every fact the owner's structure did not supply.",
}

# The same list as management_changing in TIDE-matcher-eval-questions.json (authoring 8.6).
KEY_TOPICS = ["onset", "cough_sputum", "fever_and_chills", "chest_pain", "past_medical_history",
              "current_medications", "allergies", "recent_antibiotics_healthcare", "code_status"]

VOLUNTEER_SETTINGS = {
 "must_ask": ["allergies", "recent_antibiotics_healthcare", "code_status", "current_medications",
              "past_medical_history", "social_history"],
 "volunteers_note": "Nothing is volunteered in this pack.",
}

TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"],
 "cough_sputum": ["cough_sputum", "cough_sore_throat"], "hemoptysis": ["hemoptysis"],
 "chest_pain": ["chest_pain", "location_pain", "radiation_pain"],
 "breathing": ["breathing_sob", "character_dyspnea"], "fever_and_chills": ["fever_chills", "sweating"],
 "confusion": ["confusion"], "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"],
 "urine_output": ["urine_output"], "nausea_vomiting": ["nausea_vomiting"],
 "abdominal_pain": ["abdominal_pain"], "diarrhea": ["diarrhea"], "headache": ["headache", "neck_stiffness"],
 "leg_swelling": ["leg_swelling", "calf_pain"], "orthopnea": ["orthopnea", "pnd"],
 "palpitations": ["palpitations"],
 "past_medical_history": ["pmh", "prior_cardiac", "prior_hf"], "past_surgical_history": ["psh"],
 "current_medications": ["meds", "anticoag", "adherence"], "allergies": ["allergies"],
 "recent_antibiotics_healthcare": ["recent_antibiotics_healthcare"],
 "social_history": ["social_history", "smoking", "alcohol", "substance_use", "smoking_alcohol"],
 "vaccinations": ["vaccinations"], "sick_contacts": ["sick_contacts", "recent_illness_sick_contacts"],
 "travel_history": ["travel", "travel_immobility_surgery"], "family_history": ["family_history"],
 "functional_baseline": ["functional_baseline"], "last_oral_intake": ["last_oral_intake"],
 "code_status": ["code_status"], "diabetes_control": ["diabetes_history", "glucose_monitoring"],
}

# Covered by an authored answer without drawing phrasings (keeps them out of the
# out-of-scope bank). His work is in the social answer, and his wife is the companion.
EXTRA_COVERED = ["occupation", "companion"]
