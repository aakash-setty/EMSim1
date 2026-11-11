"""ALLEY part 4: the interview.

The patient answers for himself, in a few slurred words (owner, 11 November 2026: the history
is sparse because he is drunk). He never answers falsely. He volunteers nothing about what he
drank, his eyes or whether he meant to hurt himself: all three are must_ask. In the worst tier
(untreated_floor and held_late) each answer has a shorter second form (authoring 8.5).

Every answer is model output. Facts the owner's structure did not supply are listed in
ALLEY-SEED.md section 3.7: the timing he cannot give, how much he drank, the intent denial,
the withdrawal history, the last meal, the housing, and every denial.
"""
from case_4_variants import SHARED

WORST = "phase is untreated_floor OR phase is held_late"
R1 = "flag reached_u1 set"
R2 = "flag reached_u2 set"

TOPICS = []
NEGATIVES = {"chest_pain", "fever_and_chills", "diarrhea", "cough_sore_throat",
             "dysuria_gu_symptoms", "fall_head_injury", "seizures", "intent",
             "substance_use", "allergies", "palpitations"}


def topic(tid, answer, short=None, canonical=None, variants=None, echo=None, extra=None,
          more=None, facts=None):
    s = SHARED.get(tid, {})
    rules = list(extra or [])
    if short:
        rules.append({"when": WORST, "value": short})
    rules.append({"when": None, "value": answer})
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]) + list(more or []), "answer": rules,
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


def fact(fid, asks, value, short=None, restate=False):
    v = ([{"when": WORST, "value": short}] if short else []) + [{"when": None, "value": value}]
    f = {"id": fid, "asks": asks, "value": v}
    if restate:
        f["restate"] = True
    return f


# --------------------------------------------------------------- what he drank
topic("alcohol",
  "'Vodka. Ran out last night. Then the blue stuff.'",
  short="'Blue stuff.'",
  canonical="What have you been drinking?",
  variants=["What did you drink?", "What were you drinking?", "Have you been drinking?",
            "What did you have to drink today?", "Did you drink anything else?",
            "Anything besides alcohol?", "What kind of alcohol?", "Did you drink anything unusual?",
            "Did you swallow anything?", "Did you take anything?", "Any ingestion?",
            "Etoh?", "Did you drink anything that wasn't alcohol?", "Do you drink?"],
  echo="what you drank",
  facts=[
    fact("blue_stuff", ["what is the blue stuff", "what's the blue stuff", "whats the blue stuff",
                        "what blue stuff", "what was blue", "blue stuff", "the blue stuff",
                        "what was it", "what's that", "what kind of blue", "what is it"],
         "'Window stuff. For the car. Found it.'", short="'Window... for the car.'"),
    fact("how_much", ["how much", "how much of it", "how many", "the whole thing"],
         "'Most of the jug.'", short="'Lot.'"),
    fact("when", ["when", "what time", "how long ago", "last drink", "when did you drink it"],
         "'Last night. Or this morning. I dunno.'", short="'Dunno.'"),
    fact("vodka", ["vodka", "how much vodka"], "'Vodka. Then the blue stuff.'", restate=True),
  ])

topic("intent",
  "'No. I just needed a drink.'",
  short="'No.'",
  canonical="Were you trying to hurt yourself?",
  variants=["Did you want to hurt yourself?", "Were you trying to kill yourself?",
            "Was this on purpose?", "Did you drink it to hurt yourself?", "Any thoughts of suicide?",
            "Are you suicidal?", "Do you want to die?", "Were you trying to end your life?",
            "Did you mean to harm yourself?", "Was it a suicide attempt?", "SI?",
            "Any thoughts of harming yourself?", "Why did you drink it?"],
  echo="whether you meant to hurt yourself")

# --------------------------------------------------------------- his eyes
VISION_ANSWER = [
  {"when": R2, "value": "'I just see light and shapes.'"},
  {"when": R1, "value": "'I can't make out your face.'"},
]
topic("vision",
  "'Everything's blurry and white. Like a snowstorm.'",
  canonical="How is your vision?",
  variants=["Can you see me?", "Any trouble seeing?", "How's your eyesight?", "Is your vision blurry?",
            "Any blurred vision?", "Can you see okay?", "Any changes in your vision?",
            "What do you see?", "How many fingers am I holding up?", "Any problems with your eyes?",
            "Vision changes?", "Can you read that sign?", "Are your eyes okay?", "Visual disturbance?",
            "Why are you rubbing your eyes?", "Can you see clearly?"],
  echo="your eyes",
  extra=VISION_ANSWER,
  facts=[fact("since", ["since when", "when did it start", "how long", "how long has it been blurry"],
              "'Since I woke up.'", short="'Woke up.'")])

# --------------------------------------------------------------- the illness
topic("onset", "'Woke up sick. Last night, this morning. I dunno.'", short="'Dunno.'")
topic("timing_progression", "'Worse. Just feel bad.'", short="'Worse.'")
topic("character_of_symptoms", "'Just sick. Sick and tired.'", short="'Sick.'")
topic("nausea_vomiting", "'Feel like I'm gonna throw up.'", short="'Threw up.'",
      extra=[{"when": "phase is drifting OR phase is held_mid OR flag reached_u1 set", "value": "'Threw up. Still feel sick.'"}])
topic("abdominal_pain", "'Stomach hurts. Up here.'", short="'Hurts.'")
topic("location_of_pain", "'Up here. Top of my stomach.'", short="'Here.'")
topic("severity", "'Bad.'", short="'Bad.'")
topic("headache", "'Yeah. Pounding.'", short="'Head.'",
      canonical="Do you have a headache?",
      variants=["Any headache?", "Does your head hurt?", "Headache?", "Is your head sore?",
                "Any pain in your head?", "How's your head?", "Is your head pounding?",
                "Any head pain?", "Do you have a sore head?", "Is it a bad headache?"],
      echo="your head")
topic("breathing", "'I'm fine. Just tired.'", short="'Can't... get air.'",
      extra=[{"when": "phase is improving", "value": "'Breathing's easier.'"}])
topic("chest_pain", "'No.'", short="'No.'")
topic("palpitations", "'No.'", short="'No.'",
      canonical="Do you feel your heart racing?",
      variants=["Any palpitations?", "Is your heart racing?", "Can you feel your heart pounding?",
                "Any fluttering in your chest?", "Heart beating fast?", "Palpitations?",
                "Does your heart feel funny?", "Any skipped beats?", "Is your heart pounding?",
                "Any racing heart?"],
      echo="your heart")
topic("fever_and_chills", "'No.'", short="'No.'")
topic("cough_sore_throat", "'No.'", short="'No.'")
topic("diarrhea", "'No.'", short="'No.'")
topic("dysuria_gu_symptoms", "'No.'", short="'No.'")
topic("urine_output", "'Dunno.'", short="'Dunno.'")
topic("dizziness_syncope", "'Little dizzy. Didn't pass out.'", short="'Dizzy.'")
topic("fall_head_injury", "'Didn't fall.'", short="'No.'",
      canonical="Did you fall or hit your head?",
      variants=["Did you fall?", "Did you hit your head?", "Any head injury?", "Any trauma?",
                "Did you get hurt?", "Were you assaulted?", "Did anyone hit you?", "Did you fall over?",
                "Any falls?", "Did you bang your head?", "Head trauma?", "Are you hurt anywhere?",
                "Any injuries?"],
      echo="whether you fell")
topic("seizures", "'No.'", short="'No.'",
      canonical="Have you had a seizure?",
      variants=["Any seizures?", "Did you have a fit?", "Ever had a seizure?", "Any convulsions?",
                "Did you shake or jerk?", "History of seizures?", "Have you ever had a fit?",
                "Withdrawal seizures?", "Any epilepsy?", "Any seizure activity?"],
      echo="seizures")
topic("withdrawal",
  "'Get the shakes when I stop. Not now.'", short="'No.'",
  canonical="Do you get withdrawal when you stop drinking?",
  variants=["Have you had withdrawal before?", "Do you get the shakes?", "Ever had the DTs?",
            "Any withdrawal symptoms?", "What happens when you stop drinking?", "Do you shake in the morning?",
            "History of DTs?", "Have you ever been in withdrawal?", "Do you need a drink in the morning?",
            "Any tremor?", "Are you shaky?", "Ever detoxed?"],
  echo="withdrawal")
topic("weakness_tiredness", "'Just tired. Let me sleep.'", short="'Tired.'",
      canonical="Do you feel weak?",
      variants=["Are you weak?", "Any weakness?", "Do you feel tired?", "Are you sleepy?",
                "Any fatigue?", "Can you stand up?", "Can you walk?", "How's your strength?",
                "Do your legs feel weak?", "Why are you so sleepy?"],
      echo="feeling tired")

# --------------------------------------------------------------- background
topic("past_medical_history", "'Nothing. Just the drinking.'", short="'Nothing.'")
topic("past_surgical_history", "'Nah.'", short="'No.'")
topic("current_medications", "'None.'", short="'None.'")
topic("allergies", "'No.'", short="'No.'")
topic("substance_use", "'No. Just drink.'", short="'No.'",
      canonical="Do you use any drugs?",
      variants=["Any drugs?", "Do you use drugs?", "Any other drugs?", "Any pills?", "Any cocaine?",
                "Any heroin or opioids?", "Do you inject?", "Any street drugs?", "Recreational drugs?",
                "Drug use?", "Did you take anything else?", "Any meth?"],
      echo="other drugs")
topic("social_history", "'Outside, mostly. Around here. I smoke.'", short="'Outside.'")
topic("family_history", "'Dunno.'", short="'Dunno.'")
topic("last_oral_intake", "'Couple days? Dunno.'", short="'Dunno.'")

# --------------------------------------------------------------- presenting_story
TOPICS.insert(0, {'topic': 'presenting_story',
 'canonical': 'What happened?',
 'variants': ['Hi', 'Hello', 'Hi there', 'Hey', "Hi, I'm one of the doctors.", "Hello, I'm the doctor.",
              "What's going on?", 'What is going on?', 'What is going on today?', "What's been going on?",
              'What happened?', 'What happened today?', 'What brings you in?', 'What brings you in today?',
              'What brought you here?', 'What brings you to the emergency department?', "What's wrong?",
              "What's the matter?", 'What seems to be the problem?', 'Tell me what happened.',
              'Can you tell me what happened?', "Tell me what's going on.", "What's the story?",
              'How can I help you today?', 'Why are you here today?', 'Talk me through what happened.'],
 'answer': [{'when': WORST, 'value': "'Sick... tired...'"},
            {'when': None,
             'value': "'Been drinking. Ran out last night. Feel sick, head hurts. Somebody called you guys.'"}],
 'echo': 'what happened',
 'authoring_note': ('Authoring 8.2. Written by a model from the case structure. Short and slurred on '
                    "the owner's instruction (11 November 2026). The blue fluid, the eyes and intent "
                    'stay behind their own questions. Not physician reviewed.')})

# ------------------------------------------------------------------ global rules
GLOBAL_RULES = [
 {"when": "flag intubated set OR phase is halted OR phase is discharged OR phase is case_complete",
  "value": "He can't answer right now.",
  "note": ("Section 8.5. Intubation is blocked in this case, but the validator requires the "
           "ventilated patient to be described. No live phase is at alertness 2 or 3.")},
 {"when": "flag sedated set",
  "value": "He's snoring. He doesn't answer.",
  "note": "The sedation overlay, 150 seconds after a sedative."},
]

OUT_OF_SCOPE = [
 {"when": WORST, "value": "'Huh?'"},
 {"when": None, "value": "'Huh? ... What?'"},
]

AUTHORING_NOTES = {
 "voice": "Slurred, a few words at a time, cooperative, drowsy. Owner, 11 November 2026: sparse because he is drunk.",
 "the_drink": (
   "'The blue stuff' is behind the drink question, and 'window stuff, for the car' is behind "
   "one more question. Never volunteered."),
 "the_eyes": "Behind the vision question and the HEENT exam. Never volunteered. Owner's tiers V0 to V2.",
 "timing": "He cannot say when he drank it. This keeps the ethanol of 28 plausible (case map M1).",
 "diagnosis_disclosure": "He never names methanol and could not know it.",
}

KEY_TOPICS = ["alcohol", "vision", "intent", "fall_head_injury"]

VOLUNTEER_SETTINGS = {
 "must_ask": ["alcohol", "vision", "intent", "substance_use", "allergies", "current_medications"],
 "volunteers_note": "Nothing is volunteered in this pack.",
}

TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"],
 "character_of_symptoms": ["character_general"], "nausea_vomiting": ["nausea_vomiting"],
 "abdominal_pain": ["abdominal_pain"], "location_of_pain": ["location_pain"], "severity": ["severity"],
 "headache": ["headache"], "breathing": ["breathing_sob"], "chest_pain": ["chest_pain"],
 "palpitations": ["palpitations"], "fever_and_chills": ["fever_chills"],
 "cough_sore_throat": ["cough_sore_throat"], "diarrhea": ["diarrhea"], "dysuria_gu_symptoms": ["dysuria_gu"],
 "urine_output": ["urine_output"], "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"],
 "weakness_tiredness": ["weakness"], "past_medical_history": ["pmh"], "past_surgical_history": ["psh"],
 "current_medications": ["meds"], "allergies": ["allergies"], "substance_use": ["substance_use"],
 "social_history": ["social_history", "smoking"], "family_history": ["family_history"],
 "last_oral_intake": ["last_oral_intake"], "alcohol": ["alcohol"], "vision": ["photophobia"],
 "confusion_proxy": [],
}
TOPIC_MAP.pop("confusion_proxy")

EXTRA_COVERED = []
