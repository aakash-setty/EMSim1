"""DKA part 4: the interview.

The patient answers for herself in every phase. She is alert throughout. The triage
handover does not mention diabetes, so her history is where the learner finds it. She
never names ketoacidosis and never quotes a result she could not know. Her meter reading
at home is hers to report.

Every answer is model output. Most restate PATIENT["background"], which is also model
output. Some add a fact the background does not hold: feeling hot and shivery the first
night, a period two weeks ago and a pill that may have been vomited, her mother's thyroid
disease, a meter reading of 290 last night, nearly fainting in the shower, and being up
four times in the night. Two answers carry denials a model added on 7 October 2026 so
that a question the out-of-scope bank no longer refuses gets an answer: no leg cramps,
and no black stools. DKA-SEED.md lists the whole ground truth with the pertinent
negatives, and marks each of these for the physician.
"""
from case_4_variants import SHARED

FALLING = "phase is potassium_falling"
TREATED = "phase is treated"

TOPICS = []
# Only topics whose answer is a denial in every phase (authoring 8.3). Fever, headache
# and family history report something, so they are not marked.
NEGATIVES = {"cough_sore_throat", "chest_pain", "radiation_of_pain", "dysuria_gu_symptoms",
             "travel_history", "allergies", "pregnancy"}


def topic(tid, answer, canonical=None, variants=None, echo=None, extra=None, more=None,
          facts=None):
    """`more` adds hand-written phrasings to the shared ones for a topic."""
    s = SHARED.get(tid, {})
    rules = (extra or []) + [{"when": None, "value": answer}]
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]) + list(more or []), "answer": rules,
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


def fact(fid, asks, value, restate=False):
    """A piece of a topic's answer, for a follow-up question (authoring 24). It restates
    part of the paragraph and adds nothing to it."""
    f = {"id": fid, "asks": asks, "value": [{"when": None, "value": value}]}
    if restate:
        f["restate"] = True
    return f


# --------------------------------------------------------------- the illness
topic("onset",
  "'Two days ago. I started throwing up on Sunday night, and the diarrhea came a few hours "
  "after.'",
  facts=[
    fact("when", ["when exactly", "what day", "how long ago", "how many days"],
         "'Sunday night. Two days ago.'", restate=True),
    fact("first_symptom", ["what came first", "what was the first thing", "how did it start"],
         "'The throwing up came first. The diarrhea came a few hours after.'")])

topic("timing_progression",
  "'The throwing up has slowed down, there's nothing left. But since yesterday I feel "
  "worse in a different way. Thirsty, weak, sort of washed out.'",
  extra=[{"when": TREATED, "value": "'Better than when I came in. The sick feeling is going.'"}])

topic("character_of_symptoms",
  "'Sick to my stomach, and so tired. My whole body feels heavy and dry.'")

topic("nausea_vomiting",
  "'I've thrown up maybe ten times. Just yellow now. No blood. I can't even keep water "
  "down.'",
  extra=[{"when": TREATED, "value": "'The sick feeling is easing. I haven't thrown up since you started treating me.'"}])

topic("diarrhea",
  "'Watery, six or seven times a day since Sunday. No blood in it, and it isn't black. "
  "It's slowing down today.'",
  more=["Is there any blood in the diarrhea?", "Any blood when you go to the bathroom?",
        "Are your stools black?", "Any black or tarry stools?"],
  # The short form she gives when asked again keeps the denial, so a second question
  # about blood is not answered with the frequency alone.
  facts=[
    fact("what", ["how often", "how many times", "is it watery", "what is it like"],
         "'Watery, six or seven times a day. No blood, and it isn't black.'", restate=True),
    fact("blood", ["any blood", "blood in it", "is it black", "black stools", "tarry"],
         "'No blood in it, and it isn't black.'")])

topic("abdominal_pain",
  "'Crampy, all over my stomach. It comes in waves with the diarrhea. Not sharp, and not "
  "in one place.'")

topic("location_of_pain",
  "'All over my belly, mostly the middle. Nowhere else hurts.'")

topic("radiation_of_pain",
  "'No, it doesn't go anywhere. Not to my back and not to my shoulder.'",
  more=["Any back pain?", "Does your back hurt?"])

topic("severity",
  "'The cramps are maybe a four out of ten. It's the weakness that scared me.'")

topic("aggravating_relieving",
  "'Trying to drink makes me sick again. Lying still helps a bit. Nothing else changes "
  "it.'")

topic("thirst_and_urination",
  "'I've been so thirsty since yesterday, and peeing all the time, even though I can't "
  "keep a drink down. I was up four times in the night.'",
  canonical="Have you been very thirsty or passing a lot of urine?",
  variants=["Have you been thirsty?", "Are you drinking a lot?", "Are you peeing more than usual?",
            "Any excessive thirst?", "Have you been passing a lot of urine?",
            "Are you up at night to pee?", "Any polyuria or polydipsia?", "Polyuria?",
            "Have you been going to the toilet to pee a lot?", "Is your mouth dry all the time?",
            "Have you been drinking more water than normal?", "Any increase in urination?",
            "How much are you drinking?", "Are you always thirsty?",
            "Do you get up at night to pass urine?", "How many times were you up in the night?"],
  echo="being thirsty and peeing")

topic("urine_output",
  "'A lot yesterday and through the night. Less this morning, and it was dark.'")

topic("weakness",
  "'I feel weak all over, like I have the flu. No cramps. I can walk, I just don't want to.'",
  canonical="Do you feel weak?",
  variants=["Are you weak?", "Any weakness?", "Do your arms or legs feel weak?",
            "Any muscle weakness?", "Can you lift your arms?", "Do your legs feel heavy?",
            "Any trouble walking?", "Do you feel tired or weak?", "How is your strength?",
            "Any cramps in your muscles?", "Are your muscles aching?", "Can you stand up?",
            "Is the weakness all over or in one place?", "Any fatigue?",
            "Any cramps in your legs?", "Any leg cramps?", "Are your legs the worst of it?"],
  echo="feeling weak",
  extra=[{"when": FALLING, "value": "'It's much worse. My arms and legs feel heavy and it's an effort to lift them. No cramps.'"}],
  # As for the diarrhea: the short form keeps the denial.
  facts=[
    {"id": "how", "asks": ["how weak", "where is it weak", "is it all over", "can you walk"],
     "restate": True,
     "value": [{"when": FALLING, "value": "'My arms and legs feel heavy. No cramps.'"},
               {"when": None, "value": "'Weak all over, like I have the flu. No cramps.'"}]},
    fact("cramps", ["any cramps", "leg cramps", "muscle cramps", "cramping in your legs"],
         "'No cramps.'")])

topic("palpitations",
  "'It's beating fast, I can feel that. It isn't jumping about.'",
  canonical="Can you feel your heart racing?",
  variants=["Any palpitations?", "Is your heart racing?", "Is your heart pounding?",
            "Can you feel your heartbeat?", "Does your heart feel irregular?",
            "Any fluttering in your chest?", "Is your heart skipping beats?",
            "Does your heart feel fast?", "Any thumping in your chest?", "Is your pulse racing?"],
  echo="my heart racing",
  extra=[{"when": FALLING, "value": "'Yes. It's fluttering and missing beats. That's new.'"}])

topic("breathing",
  "'I'm not short of breath exactly. I keep taking big breaths, I can't seem to help it. "
  "No wheeze.'",
  extra=[{"when": TREATED, "value": "'It feels easier now. I'm not sighing so much.'"}])

topic("dizziness_syncope",
  "'Lightheaded when I stand up. I had to sit down in the shower this morning. I haven't "
  "fainted.'")

topic("chest_pain", "'No, no chest pain.'")
topic("fever_and_chills",
  "'I felt hot and shivery the first night. I haven't taken my temperature. Not since.'")
topic("cough_sore_throat", "'No cough, no sore throat.'")
topic("headache", "'A bit of a dull head, like when you haven't drunk enough. Not a bad headache.'")
topic("dysuria_gu_symptoms",
  "'No burning when I pee, no smell, no pain in my sides. No discharge.'")

# --------------------------------------------------------------- the diabetes
topic("past_medical_history",
  "'I have type 1 diabetes, since I was eleven. That's all. No other problems.'")

topic("diabetes_history",
  "'Type 1, since I was eleven. I was in the hospital for a few days when it was found, they "
  "said my blood had gone acidic. I haven't been admitted with it since. My last clinic check "
  "was fine, my doctor was happy with my numbers.'",
  canonical="Tell me about your diabetes.",
  variants=["Do you have diabetes?", "Are you diabetic?", "What type of diabetes do you have?",
            "How long have you had diabetes?", "Is your diabetes well controlled?",
            "Have you ever had DKA?", "Have you been in hospital with your diabetes?",
            "Have you had ketoacidosis before?", "Any problems with your diabetes?",
            "When were you diagnosed with diabetes?", "How is your sugar control usually?",
            "What is your A1c?", "Any complications from your diabetes?", "Type 1 or type 2?"],
  echo="my diabetes")

topic("current_medications",
  "'Lantus at night, eighteen units, and Humalog with meals, I work it out from what I'm "
  "eating. Both in pens. And the pill. Nothing else, nothing new.'",
  facts=[
    fact("basal", ["what dose of lantus", "how much lantus", "how many units",
                   "long-acting dose", "what dose"],
         "'Eighteen units of Lantus at night.'", restate=True),
    fact("mealtime", ["how much humalog", "mealtime dose", "short-acting dose", "with meals"],
         "'Humalog with meals. I work the dose out from what I'm eating.'"),
    fact("other", ["anything else", "any other medicines", "the pill", "anything new",
                   "over the counter"],
         "'The pill. Nothing else, nothing new.'")])

topic("insulin_taken_recently",
  "'Not properly. I wasn't eating, so I didn't take any Humalog. I halved my Lantus on "
  "Sunday night because I was scared of going low, and last night I didn't take it at "
  "all. I thought that was the safe thing to do.'",
  canonical="Have you been taking your insulin while you've been ill?",
  variants=["Have you been taking your insulin?", "When did you last take your insulin?",
            "Have you missed any insulin?", "Did you take your Lantus last night?",
            "Have you skipped any doses?", "Are you still taking your insulin?",
            "Have you changed your insulin doses?", "Did you reduce your insulin?",
            "When was your last dose of insulin?", "Have you stopped your insulin?",
            "Any missed doses?", "Insulin adherence?", "Have you been compliant with insulin?",
            "What did you do with your insulin when you were sick?", "Did you take your long-acting insulin?",
            "Have you been taking your meds?", "Have you missed any doses?",
            "Have you been skipping doses?", "Are you taking your insulin as prescribed?"],
  echo="taking my insulin",
  facts=[
    fact("basal", ["the lantus", "long-acting", "last night", "basal"],
         "'I halved my Lantus on Sunday night, and last night I didn't take it at all.'",
         restate=True),
    fact("mealtime", ["the humalog", "mealtime insulin", "short-acting", "with meals"],
         "'I didn't take any Humalog, because I wasn't eating.'"),
    fact("why", ["why did you stop", "why did you cut it", "why not", "what made you stop"],
         "'I wasn't eating and I was scared of going low. I thought that was the safe "
         "thing to do.'")])

topic("glucose_monitoring",
  "'I checked this morning and it said 380. It was 290 last night. I don't have any of "
  "the ketone strips, they ran out a while ago.'",
  canonical="Have you been checking your sugars?",
  variants=["What have your sugars been?", "Have you checked your blood sugar?",
            "What was your last glucose reading?", "Have you tested for ketones?",
            "Do you have ketone strips?", "What did your meter say?", "Have your sugars been high?",
            "Have your sugars been low?", "Do you have a glucose monitor?",
            "Any high readings at home?", "Did you check your ketones?", "What are your numbers?",
            "Do you wear a sensor?", "Any hypos?"],
  echo="my sugar readings",
  facts=[
    fact("this_morning", ["this morning", "latest reading", "last reading", "most recent"],
         "'380 this morning.'", restate=True),
    fact("last_night", ["last night", "yesterday", "before that"],
         "'290 last night.'"),
    fact("ketones", ["ketones", "ketone strips", "urine strips"],
         "'I don't have any ketone strips. They ran out a while ago.'")])

topic("past_surgical_history",
  "'I had my appendix out when I was fifteen. Nothing else.'")

topic("allergies", "'No allergies.'")

topic("pregnancy",
  "'I don't think so. I'm on the pill and I had a period two weeks ago. I threw up on "
  "Sunday so I might have lost a pill.'")

# --------------------------------------------------------------- around it
topic("sick_contacts",
  "'My roommate had exactly this last week, three days of throwing up and diarrhea. She's "
  "fine now. We didn't eat anything odd.'")

topic("last_oral_intake",
  "'Nothing solid since Sunday. Sips of water and flat soda, and most of that came "
  "back. I tried a cracker this morning.'")

topic("social_history",
  "'I'm a grad student, I share an apartment. I don't smoke. A couple of glasses of wine on the "
  "weekend, none this week. No drugs, no weed.'",
  more=["What do you do for a living?", "What are you studying?", "Are you a student?",
        "What do you do for work?", "Do you work or study?"])

topic("family_history",
  "'My mom has a thyroid problem. Nobody else has diabetes.'")

topic("functional_baseline",
  "'Normally I'm fine. I run twice a week. I was in class on Friday.'")

topic("travel_history", "'No, I haven't been anywhere.'")

GLOBAL_RULES = [
 {"when": "phase is case_complete", "value": "She has been admitted.",
  "note": "No live phase is at alertness 2 or 3. This rule exists because the list may not be empty."},
]

OUT_OF_SCOPE = [
 {"when": None, "value": "'Sorry, I'm not sure what you mean. Can you ask me another way?'"},
]

AUTHORING_NOTES = {
 "voice": "A 24-year-old graduate student. Clear, a little embarrassed, worried she has done something wrong.",
 "the_insulin": (
   "She reduced and then stopped her insulin because she was not eating. She says so only "
   "when asked about her insulin. It is in must_ask and is never volunteered."),
 "the_diabetes": (
   "The handover does not mention diabetes. Past medical history, medications, the "
   "diabetes topic, the sugar readings and the thirst topic all lead to it."),
 "no_global_rule": "No phase is at alertness 2 or 3, so there is no alertness rule.",
 "near_the_10_4_line": (
   "Two answers sit close to the limits in authoring 8.4 and are flagged for the "
   "reviewer. The diabetes topic says 'they said my blood had gone acidic' about her "
   "admission at age eleven. That is her own past history in lay words, and she does not "
   "connect it to today. The sugar topic quotes her home meter, 380 and 290. Those are "
   "numbers she read herself, not results from this visit. A reviewer may prefer either "
   "softened."),
 "added_denials": (
   "Model-written on 7 October 2026, awaiting sign-off: 'No cramps' in the weakness "
   "answer and 'it isn't black' in the diarrhea answer. Both were added so that "
   "questions the out-of-scope bank used to refuse now get an answer."),
 "facts": (
   "Six topics carry facts: onset, diarrhea, weakness, current_medications, "
   "insulin_taken_recently and glucose_monitoring. Each fact restates part of its "
   "topic's paragraph. On diarrhea and weakness the short form given on a repeat keeps "
   "the denial (no blood, no cramps)."),
}

# The same list as management_changing in DKA-matcher-eval-questions.json (authoring 8.6).
KEY_TOPICS = ["past_medical_history", "diabetes_history", "current_medications",
              "insulin_taken_recently", "glucose_monitoring", "thirst_and_urination",
              "sick_contacts", "pregnancy", "allergies"]

# One adjacency. A volunteer line must not repeat the answer it rides on, and a key topic
# is never volunteered (authoring 24). The three removed on 7 October 2026: location
# rode on the abdominal pain answer and repeated it, and thirst and the diabetes history
# are key topics.
ADJACENT = {
 "onset": ["diarrhea"],
}
VOLUNTEER = {
 "diarrhea": "'It's watery, six or seven times a day.'",
}
VOLUNTEER_SETTINGS = {
 "must_ask": ["allergies", "pregnancy", "insulin_taken_recently", "current_medications",
              "social_history", "glucose_monitoring", "past_medical_history",
              "diabetes_history", "thirst_and_urination"],
 "volunteers_note": (
   "Hand-written for this pack. Her diabetes, her insulin doses, her sugar readings and "
   "her thirst are never volunteered."),
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

# --------------------------------------------------------------- presenting_story
# Authoring 8.2, owner's instruction 30 October 2026: a greeting or an open question gets a
# brief history of the present illness. Written by a model from this case's own answers and
# copied here from the case file, so a rebuild keeps it. Not physician reviewed.
TOPICS.insert(0, {'topic': 'presenting_story',
 'canonical': 'What happened?',
 'variants': ['Hi',
              'Hello',
              'Hi there',
              'Hey',
              "Hi, I'm one of the doctors.",
              "Hello, I'm the doctor.",
              "What's going on?",
              'What is going on?',
              'What is going on today?',
              "What's been going on?",
              'What happened?',
              'What happened today?',
              'What brings you in?',
              'What brings you in today?',
              'What brought you here?',
              'What brings you to the emergency department?',
              "What's wrong?",
              "What's the matter?",
              'What seems to be the problem?',
              'Tell me what happened.',
              'Can you tell me what happened?',
              "Tell me what's going on.",
              "What's the story?",
              'How can I help you today?',
              'Why are you here today?',
              'Talk me through what happened.'],
 'answer': [{'when': None,
             'value': "'I started throwing up on Sunday night, and the diarrhea came a few hours "
                      "after. I can't keep anything down, not even water. Since yesterday I've "
                      "felt so weak and washed out that it scared me.'"}],
 'echo': 'what happened',
 'authoring_note': 'Authoring 8.2: a greeting or an open question gets a brief history of the '
                   "present illness. Added 30 October 2026 on the owner's instruction. The answer "
                   "was written by a model from this case's own onset, progression and character "
                   'answers and its arrival handover, and stops short of every disclosure the case '
                   'keeps behind its own question. Not physician reviewed. Variants copied from '
                   'DIPH and catalog/interview_phrasings.py (questions, not facts).'})

TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"], "character_of_symptoms": ["character_general"],
 "location_of_pain": ["location_pain"], "radiation_of_pain": ["radiation_pain"], "severity": ["severity"],
 "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"],
 "nausea_vomiting": ["nausea_vomiting"], "diarrhea": ["diarrhea"], "abdominal_pain": ["abdominal_pain"],
 "urine_output": ["urine_output"], "palpitations": ["palpitations"], "breathing": ["breathing_sob"],
 "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"], "chest_pain": ["chest_pain"],
 "fever_and_chills": ["fever_chills"], "cough_sore_throat": ["cough_sore_throat"], "headache": ["headache"],
 "dysuria_gu_symptoms": ["dysuria_gu"], "past_medical_history": ["pmh"], "past_surgical_history": ["psh"],
 "current_medications": ["meds"], "allergies": ["allergies"],
 "pregnancy": ["pregnancy"], "sick_contacts": ["sick_contacts"],
 "last_oral_intake": ["last_oral_intake"],
 "social_history": ["social_history", "smoking", "alcohol", "substance_use"],
 "family_history": ["family_history"], "functional_baseline": ["functional_baseline"],
 "travel_history": ["travel"],
 "thirst_and_urination": ["thirst_polyuria"], "weakness": ["weakness"],
 "diabetes_history": ["diabetes_history"], "glucose_monitoring": ["glucose_monitoring"],
}

# Concepts and cover tags this case's answers cover without drawing phrasings from them
# (a concept in catalog/interview_phrasings.py, or a tag in BANK_ONLY_TAGS in
# catalog/interview_out_of_scope.py). Only used to keep those questions out of the
# out-of-scope bank. List one only when an authored answer really covers the question.
EXTRA_COVERED = ["character_general", "cough_sputum", "menstrual_tampon", "sexual_history", "occupation",
    "leg_cramps", "gi_bleeding", "back_pain"]
