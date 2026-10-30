"""TSS part 4: the interview.

The patient answers for herself. She is alert in every phase except profound shock, where a
global rule speaks for her, and she is drowsy in the hypotensive phase, where every topic
has a shorter answer carrying the same fact.

Every answer is model output. The history it restates is PATIENT["background"] in case_1,
which is also model output. Nothing here has been reviewed by a physician.

What she knows and does not know, which is the design of this interview:

  - She believes she has a stomach flu and says so. She never names any other diagnosis.
  - She has an explanation for the red skin (the beach) and offers it. It is wrong.
  - She presents fainting, with a fever and a rash (11 October 2026, author instruction), and
    she has vomiting and watery diarrhea (restored 29 October 2026, author instruction: most
    menstrual toxic shock has them, they explain her low potassium, and they keep the
    gastroenteritis trap).
  - She does not connect her period to her illness, but asked about the faint she wonders
    aloud whether her period had something to do with it. That is the one nudge toward the
    source, added the same day to make the diagnosis slightly easier to reach. Asked
    directly about tampons, she says she cannot remember taking the last one out. That is
    the honest answer and it is the single most useful sentence in the history.
"""
from case_4_variants import SHARED

HYPO = "phase is hypotensive"
PROF = "phase is profound_shock"
TUBED = "flag intubated set"

TOPICS = []

# Marked pertinent_negative. Only topics whose answer denies in every phase (authoring
# 10.3). confusion was in this set until 7 October 2026. Its drowsy answer is "I feel
# foggy. Sorry.", which reports a symptom, so the mark came off. The answers are unchanged.
NEGATIVES = {
 "radiation_of_pain", "neck_stiffness", "photophobia", "chest_pain",
 "travel_history", "tick_and_outdoor_exposure", "recent_antibiotics_healthcare",
 "wounds_and_skin", "past_medical_history", "allergies", "pregnancy",
}


# v0.24 audit. Hand-written variants added on 7 October 2026 on top of the shared ones in
# case_4_variants.py. Each is a question the catalog's out-of-scope list holds, or a shared
# phrasing that would otherwise be filed under a topic that denies it, and each is filed
# under the topic whose existing answer covers it. A phrasing owned by a topic here is
# dropped from the out-of-scope bank and from every other topic by the expander. None is a
# held-out question.
EXTRA_VARIANTS = {
 "abdominal_pain": ["Any back pain?", "Does your back hurt?"],
 "joint_pain": ["Any cramps in your legs?", "Do your legs ache?", "Any muscle pain in your legs?"],
 "diarrhea": ["Any blood when you open your bowels?"],
 "social_history": ["What do you do for a living?", "Are you a student?"],
 "wounds_and_skin": ["Any nosebleeds?"],
 "rash": ["Any red, hot or swollen areas of skin?", "Any skin lesions?"],
}


def fact(fid, asks, value, short=None, restate=False):
    rules = ([{"when": HYPO, "value": short}] if short else []) + [{"when": None, "value": value}]
    f = {"id": fid, "asks": asks, "value": rules}
    if restate:
        f["restate"] = True
    return f


def topic(tid, full, short, canonical=None, variants=None, echo=None, facts=None):
    """`full` is the answer when she is alert. `short` is the same fact said by a drowsy,
    hypotensive patient (authoring 8.5). Phrasings come from SHARED unless given."""
    s = SHARED.get(tid, {})
    t = {"topic": tid,
         "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]) + EXTRA_VARIANTS.get(tid, []),
         "answer": [{"when": HYPO, "value": short}, {"when": None, "value": full}],
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


# --------------------------------------------------------------- the illness
topic("onset",
  "'Two days ago. Thursday night I started shivering and aching, and by Friday morning I "
  "had a proper fever and was throwing up. The diarrhea started Friday too.'",
  "'Two days ago. Thursday night.'",
  facts=[
    fact("when", ["when exactly", "what day", "what time", "how long ago"],
         "'Thursday night, maybe eleven. So two and a half days.'",
         "'Thursday night.'", restate=True),
    fact("first_symptom", ["what came first", "what was the first thing", "how did it start"],
         "'The shivering and the aching came first. Then the fever.'",
         "'Shivering. Then the fever.'")])

topic("timing_progression",
  "'Worse. Yesterday I could get up and about for a bit. Today I can't stand without "
  "everything going gray.'",
  "'Worse. Much worse today.'")

topic("character_of_symptoms",
  "'Like the worst flu I've ever had. Everything aches, I'm hot and cold, and my stomach "
  "keeps turning over.'",
  "'Like flu. Everything aches.'")

topic("location_of_pain",
  "'All over, really. My thighs and calves are the worst. My stomach is crampy too, but "
  "it's not one spot.'",
  "'Everywhere. My legs mostly.'")

topic("radiation_of_pain",
  "'No, it doesn't go anywhere. It's just a general ache.'",
  "'No.'")

topic("severity",
  "'The aching is maybe a six. It's more that I feel so weak. I've never felt this ill.'",
  "'Six, maybe. I just feel awful.'")

topic("aggravating_relieving",
  "'Standing up makes everything worse. I get dizzy and my heart pounds. I took some "
  "ibuprofen yesterday and it brought the fever down for a couple of hours. Nothing has "
  "stayed down today.'",
  "'Standing is worse. Nothing helps.'")

topic("rash",
  "'Oh, the red? I went to the beach for an hour yesterday because I thought the air would "
  "help. I figured I'd burned. It doesn't sting like sunburn, though, and it's on my "
  "stomach, where I had a shirt on.'",
  "'I thought it was sunburn. From yesterday.'",
  canonical="How long has your skin been red?",
  variants=["Tell me about the rash", "When did the rash start?", "Why is your skin so red?",
            "Is that sunburn?", "Have you been in the sun?", "Does the rash itch?",
            "Does the redness hurt?", "Where did the redness start?", "Is the rash spreading?",
            "Have you had a rash like this before?", "When did you notice your skin was red?",
            "Is your skin peeling?", "Did you use sunscreen?", "How long were you in the sun?"],
  echo="my skin being red",
  facts=[
    fact("when", ["when did it start", "when did you notice", "how long has it been there"],
         "'I noticed it last night when I got back from the beach.'",
         "'Last night.'", restate=True),
    fact("where", ["where is it", "where did it start", "is it everywhere"],
         "'Everywhere, I think. My chest, my stomach, my arms and legs. My palms are red too.'",
         "'Everywhere.'"),
    fact("feel", ["does it itch", "does it hurt", "does it sting", "is it peeling"],
         "'It doesn't itch and it doesn't sting. It just feels hot. It isn't peeling.'",
         "'No. Just hot.'")])

topic("fever_and_chills",
  "'Yes. I've been shivering and then burning up since Thursday night. I took my "
  "temperature yesterday and it was 102.'",
  "'Yes. Hot and shivery for two days.'",
  facts=[
    fact("since_when", ["since when", "when did the fever start", "how long have you had a fever"],
         "'Since Thursday night.'", "'Two days.'", restate=True),
    fact("how_high", ["how high", "how high was it", "what was your temperature",
                      "did you take your temperature", "did you measure it"],
         "'I took it yesterday and it was 102.'", "'102 yesterday.'")])

topic("headache",
  "'A bit of one, across my forehead. It's not the main thing.'",
  "'A little.'")

topic("neck_stiffness",
  "'No. My neck's fine, I can move it.'",
  "'No.'")

topic("photophobia",
  "'No, the lights are okay.'",
  "'No.'")

topic("nausea_vomiting",
  "'Yes, constantly. I've thrown up maybe eight or ten times since Friday. No blood in it. I "
  "can't even keep water down now.'",
  "'Yes. I keep throwing up.'",
  echo="throwing up",
  facts=[
    fact("how_often", ["how many times", "how often", "how much"],
         "'Maybe eight or ten times since Friday.'", "'I keep throwing up.'", restate=True),
    fact("blood", ["any blood in it", "was there blood", "is there blood"],
         "'No blood in it.'", "'No blood in it.'"),
    fact("fluids", ["can you keep water down", "can you keep anything down", "can you drink"],
         "'I can't even keep water down now.'", "'I keep throwing up.'")])

topic("diarrhea",
  "'Yes, watery. Maybe six times yesterday and a few today. No blood.'",
  "'Yes. Watery.'")

topic("abdominal_pain",
  "'Crampy, all over, and it comes with the diarrhea. It's not a sharp pain anywhere, and "
  "not in my sides or my back.'",
  "'Crampy. Not my back.'")

topic("chest_pain",
  "'No chest pain. My heart's racing, though. I can feel it when I stand up.'",
  "'No. My heart's racing.'")

topic("breathing",
  "'I'm not short of breath exactly. I just feel like I'm breathing fast.'",
  "'A bit fast. I'm okay.'")

topic("cough_sore_throat",
  "'No cough, no cold. My throat's sore, I thought from throwing up so much.'",
  "'No cough. Sore throat.'")

topic("urine_output",
  "'Hardly at all. I think I went once yesterday and it was really dark. Nothing today. It "
  "doesn't burn.'",
  "'Barely. Not today.'")

topic("dizziness_syncope",
  "'Yes. This morning in the shower everything went gray and I went down. My roommate heard "
  "me and found me on the floor. She says I was out for a few seconds. I didn't hit my head. "
  "I thought maybe it was my period on top of the flu.'",
  "'Yes. I fainted this morning.'")

topic("confusion",
  "'No, I know where I am. I'm just exhausted.'",
  "'I feel foggy. Sorry.'")

topic("cold_extremities",
  "'My hands and feet are freezing, which is weird, because the rest of me is burning.'",
  "'Yes. Freezing.'")

topic("joint_pain",
  "'It's not my joints, it's the muscles. My thighs and calves feel like I ran a marathon. "
  "Nothing's swollen.'",
  "'Muscles. Not joints.'")

# --------------------------------------------------------------- the source
topic("dysuria_gu_symptoms",
  "'No burning, no pain down there. There's been a bit of a smell the last day or two. I "
  "thought it was just the end of my period.'",
  "'No burning. A bit of a smell.'")

topic("menstrual_and_tampon",
  "'It started five days ago, so it's pretty much done. I use tampons, the super ones.' She "
  "stops. 'I put one in on Wednesday before I went out. I honestly can't remember taking it "
  "out. I've been so sick I haven't thought about it.'",
  "'Started five days ago. I use tampons. I don't remember taking the last one out.'",
  facts=[
    fact("lmp", ["when was your last period", "when did it start", "when did it finish",
                 "are you on your period now"],
         "'It started five days ago, on Tuesday. It's pretty much finished.'",
         "'Five days ago.'", restate=True),
    fact("tampons", ["do you use tampons", "pads or tampons", "what do you use"],
         "'Tampons. The super ones, because the first couple of days are heavy.'",
         "'Tampons.'"),
    fact("last_changed", ["when did you last change it", "is there a tampon in",
                          "anything in at the moment", "could one still be in",
                          "when did you take it out"],
         "'I put one in on Wednesday evening. I can't remember taking it out. I suppose it "
         "could still be there.'",
         "'Wednesday. I don't remember taking it out.'")])

topic("pregnancy",
  "'I don't think so. I'm on the pill and I've just had my period.'",
  "'No. I'm on the pill.'")

topic("sexual_history",
  "'I have a boyfriend, we've been together about a year. Nobody else. He's fine.'",
  "'One partner. He's fine.'")

# --------------------------------------------------------------- background
topic("past_medical_history",
  "'Nothing. I'm never sick. I've never been in the hospital.'",
  "'Nothing. I'm healthy.'")

topic("past_surgical_history",
  "'I had my wisdom teeth out at eighteen. That's it, nothing else removed.'",
  "'Wisdom teeth. That's all.'")

topic("current_medications",
  "'Just the pill. I took ibuprofen yesterday, two pills a couple of times. Nothing else, "
  "no supplements.'",
  "'The pill. Some ibuprofen yesterday.'",
  facts=[
    fact("regular", ["what do you take every day", "anything regular", "anything on prescription"],
         "'Just the pill.'", "'The pill.'", restate=True),
    fact("painkillers", ["did you take anything for it", "any painkillers", "what dose",
                         "how much did you take", "how many tablets", "when did you take it"],
         "'Ibuprofen yesterday. Two pills, a couple of times.'", "'Some ibuprofen yesterday.'"),
    fact("other", ["anything else", "any supplements", "anything over the counter"],
         "'Nothing else, no supplements.'", "'Nothing else.'")])

topic("allergies",
  "'None that I know of. I've had penicillin before and it was fine.'",
  "'No allergies.'")

topic("social_history",
  "'I don't smoke or vape. I drink at weekends, a few drinks. No drugs, and I've never "
  "injected anything. I'm a grad student and I share an apartment with my roommate.'",
  "'No smoking. No drugs. I live with my roommate.'")

topic("family_history",
  "'My dad has high blood pressure. Nothing else I know of, and nothing like this.'",
  "'Dad has high blood pressure. That's all.'")

topic("last_oral_intake",
  "'A few sips of water this morning, and they came back up. I haven't eaten since "
  "Thursday.'",
  "'Sips of water. They came back up.'")

topic("vaccinations",
  "'I think so. I had everything for college, including the meningitis ones. I had a flu "
  "shot last fall.'",
  "'Yes. Everything for college.'")

topic("sick_contacts",
  "'No. My roommate's fine and my boyfriend's fine. Nobody I know is sick.'",
  "'No. Nobody.'")

topic("suspect_meal",
  "'Nothing unusual. My roommate eats what I eat and she's fine. I figured it was a "
  "stomach flu.'",
  "'Nothing unusual. Stomach flu, I thought.'",
  canonical="What did you eat before this started?",
  variants=["What did you eat?", "What do you think caused this?", "Was it something you ate?",
            "What was the last meal before you got sick?", "Did you eat anything unusual?",
            "Where did the food come from?", "Why do you think it's food poisoning?",
            "Did you eat out recently?", "Any undercooked food?", "Any seafood or chicken?",
            "What was in the takeout?", "Did anyone share the meal with you?"],
  echo="what I ate")

topic("travel_history",
  "'No, I haven't been anywhere. Just the beach yesterday, twenty minutes away.'",
  "'No. Just the beach yesterday.'")

topic("tick_and_outdoor_exposure",
  "'No bites that I've seen. No hiking or camping, no pets. I sat on the beach for an hour "
  "yesterday, that's all.'",
  "'No bites. Just the beach.'")

topic("recent_antibiotics_healthcare",
  "'No. No antibiotics, no doctors, no dentist. I haven't seen anyone about this.'",
  "'No. Nothing.'")

topic("wounds_and_skin",
  "'No. No cuts, no boils, nothing like that. No new piercings or tattoos.'",
  "'No cuts. Nothing.'",
  canonical="Any cuts, wounds or skin infections recently?",
  variants=["Any cuts or wounds?", "Any skin infections?", "Any boils or abscesses?",
            "Have you had any burns?", "Any recent injuries to your skin?",
            "Any bites that got infected?", "Any nosebleeds or nasal packing?",
            "Any new piercings?", "Any new tattoos?", "Have you cut yourself shaving?",
            "Any sores anywhere?", "Any wound that is red or draining?"],
  echo="cuts or wounds")

topic("functional_baseline",
  "'I'm healthy. I run three times a week. I was completely fine on Wednesday.'",
  "'Healthy. I was fine on Wednesday.'")

topic("code_status_goals",
  "'What? Do whatever you need to. My mom's number is in my phone.' She looks at you. 'Is "
  "it that bad?'",
  "'Do everything. Call my mom.'")

# --------------------------------------------------------------- global rules
GLOBAL_RULES = [
 {"when": TUBED,
  "value": "She is intubated and sedated and cannot answer.",
  "note": "Covers intubation in a phase whose alertness would otherwise permit speech."},
 {"when": PROF,
  "value": ("She opens her eyes when you press on her shoulder and closes them again. She "
            "does not answer. Her roommate has gone to move the car."),
  "note": "Alertness level 2 in profound_shock. The validator requires this coverage."},
]

OUT_OF_SCOPE = [
 {"when": TUBED, "value": "She is intubated and sedated and cannot answer."},
 {"when": PROF, "value": "She does not answer."},
 {"when": HYPO, "value": "She frowns with her eyes closed. 'Sorry. I can't think.'"},
 {"when": None,
  "value": "'Sorry, I'm not sure what you're asking. I feel so rough.'"},
]

AUTHORING_NOTES = {
 "voice": ("A 22-year-old graduate student. Lay words, apologetic, minimizing. She is sure "
           "it is a stomach flu and says so, which is her belief and not a diagnosis the "
           "case endorses."),
 "the_tampon": ("She does not volunteer it and it is a must-ask topic, so no other answer "
                "carries it. Asked about her period or tampons in any wording, she says she "
                "cannot remember taking the last one out. Section 8.4 holds: she reports "
                "what she knows and draws no conclusion from it."),
 "close_to_the_line": ("Two answers sit near the section 8.4 line and are flagged for the "
                       "reviewer. The rash answer says the redness is under her shirt, and "
                       "the genitourinary answer mentions a smell. Both are things a patient "
                       "would notice and say. Neither names a cause."),
 "phrasings": ("The canonical question, hand-written variants and echo for forty topics are "
               "MGCA's, in case_4_variants.py. Three topics are this case's own: rash, "
               "suspect_meal and wounds_and_skin. EXTRA_VARIANTS adds eleven phrasings by "
               "hand, each under the topic whose answer covers it."),
 "changed_7_october_2026": (
   "After the audit a model edited these and no physician has read them. location_of_pain "
   "said her back was among the worst places and abdominal_pain said the pain was not in "
   "her back. The case's reasoning against a kidney source rests on no flank pain, so "
   "location_of_pain now says thighs and calves. The drowsy abdominal_pain answer gained "
   "'Not my back.' Three topics gained facts (fever_and_chills, nausea_vomiting, "
   "current_medications), each restating part of its own answer. Three volunteer lines "
   "were replaced because they repeated the answer they ride on. Four British usages were "
   "made American."),
 "pertinent_negatives": (
   "Eleven topics are marked. confusion was the twelfth. Its drowsy answer is 'I feel "
   "foggy. Sorry.', which is not a denial, and authoring 8.3 asks that a marked topic deny "
   "in every phase, so the mark was removed on 7 October 2026 and the answers were left "
   "alone. Whether the drowsy answer should deny instead is an open question for the "
   "physician (TSS-SEED.md)."),
}

KEY_TOPICS = ["menstrual_and_tampon", "rash", "sick_contacts", "urine_output",
              "dizziness_syncope", "fever_and_chills", "pregnancy", "allergies",
              "current_medications"]

# --------------------------------------------------------------- volunteered answers
# Written by hand for this pack. Safety screens and the topic the case is built around the
# learner discovering are in must_ask and are never volunteered (authoring 24).
ADJACENT = {
 "onset": ["fever_and_chills"],
 "suspect_meal": ["sick_contacts"],
 "past_medical_history": ["past_surgical_history"],
 "location_of_pain": ["joint_pain"],
}
VOLUNTEER = {
 "fever_and_chills": "'It was 102 when I took it yesterday.'",
 "sick_contacts": "'Nobody else is sick.'",
 "past_surgical_history": "'Just my wisdom teeth out.'",
 "joint_pain": "'It's the muscles, not the joints.'",
}
VOLUNTEER_SETTINGS = {
 "must_ask": ["allergies", "pregnancy", "sexual_history", "menstrual_and_tampon",
              "dysuria_gu_symptoms", "social_history", "code_status_goals"],
 "volunteer_blocked_when": HYPO,
 "volunteers_note": ("Hand-written for this pack. A first answer carries the volunteer line "
                     "of each adjacent topic, and the adjacent topic counts as asked. Nothing "
                     "is volunteered while she is drowsy."),
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
 'answer': [{'when': 'phase is hypotensive',
             'value': "'Fever... throwing up. Two days. I fainted.'"},
            {'when': None,
             'value': "'Thursday night I started shivering and aching, and by Friday I had a fever "
                      'and was throwing up, with diarrhea too. Yesterday I went red all over. This '
                      "morning I fainted in the shower, so my roommate drove me in.'"}],
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
 "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"], "rash": ["rash"],
 "fever_and_chills": ["fever_chills"], "headache": ["headache"], "neck_stiffness": ["neck_stiffness"],
 "photophobia": ["photophobia"], "nausea_vomiting": ["nausea_vomiting"], "diarrhea": ["diarrhea"],
 "abdominal_pain": ["abdominal_pain"], "chest_pain": ["chest_pain"], "breathing": ["breathing_sob"],
 "cough_sore_throat": ["cough_sore_throat"], "urine_output": ["urine_output"],
 "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"], "confusion": ["confusion"],
 "cold_extremities": ["cold_extremities"], "joint_pain": ["joint_pain"], "dysuria_gu_symptoms": ["dysuria_gu"],
 "menstrual_and_tampon": ["menstrual_tampon"], "pregnancy": ["pregnancy"], "sexual_history": ["sexual_history"],
 "past_medical_history": ["pmh"], "past_surgical_history": ["psh"], "current_medications": ["meds"],
 "allergies": ["allergies"], "social_history": ["social_history", "smoking", "alcohol", "substance_use"],
 "family_history": ["family_history"], "last_oral_intake": ["last_oral_intake"], "vaccinations": ["vaccinations"],
 "sick_contacts": ["sick_contacts"], "travel_history": ["travel"], "tick_and_outdoor_exposure": ["tick_outdoor"],
 "recent_antibiotics_healthcare": ["recent_antibiotics_healthcare"], "functional_baseline": ["functional_baseline"],
 "code_status_goals": ["code_status"],
 "suspect_meal": ["suspect_meal"], "wounds_and_skin": ["wounds_skin"],
}

# Concepts and cover tags this case's answers cover without drawing phrasings from them
# (a concept in catalog/interview_phrasings.py, or a tag in BANK_ONLY_TAGS in
# catalog/interview_out_of_scope.py). Only used to keep those questions out of the
# out-of-scope bank. List one only when an authored answer really covers the question.
EXTRA_COVERED = ["character_general", "nosebleeds", "back_pain", "leg_cramps"]
