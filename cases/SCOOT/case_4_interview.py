"""SCOOT part 4: the interview.

He answers for himself on arrival, briefly and confusedly in the decline (GCS 12, V4), and
not at all once he has herniated, after a tube, or at the end. Every topic the decline can
reach has a shorter, confused answer with the same fact (authoring 8.5). He never names the
diagnosis and quotes no result. He does not remember the crash: what he says about it is
what Marcus told him, and he says so.

Every answer is model output, built from PATIENT["background"]. The positives a model added
and the denials a model added are listed in SCOOT-SEED.md section 2.8.

Hand-written variants on the custom topics include, word for word, the questions from the
shared out-of-scope bank that this patient can answer (seizures, numbness, double vision,
hearing, memory, speech, how he got here, who is with him, his name and age, tetanus), so
the build drops them from the bank instead of giving the fallback (catalog/interview_expand.py
rule 2). No shared file is edited.
"""
from case_4_variants import SHARED

DECL = "phase is decline"

TOPICS = []
NEGATIVES = {"neck_pain", "weakness_numbness", "vision_changes", "seizure", "chest_pain",
             "breathing", "abdominal_pain", "hearing", "past_medical_history",
             "current_medications", "anticoagulants", "allergies", "past_surgical_history"}


def topic(tid, answer, decl, canonical=None, variants=None, echo=None, more=None):
    """decl: the shorter, confused answer in the decline phase, with the same fact."""
    s = SHARED.get(tid, {})
    rules = [{"when": DECL, "value": decl}, {"when": None, "value": answer}]
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]) + list(more or []), "answer": rules,
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    TOPICS.append(t)
    return t


# --------------------------------------------------------------- the crash
topic("mechanism_of_injury",
  "'I don't remember it. Marcus, my buddy, was riding behind me. He says I hit a pothole and "
  "went over the handlebars and landed on the right side of my head.'",
  "'Marcus said... a pothole. I went over. I don't... remember.'",
  canonical="How did the crash happen?",
  variants=["How did you get hurt?", "Tell me about the accident.", "What happened with the scooter?",
            "How did the crash happen?", "Did you fall off the scooter?", "What did you hit?",
            "Mechanism of injury?", "How did you land?", "Where did you hit your head?",
            "Which side of your head hit the ground?",
            "Did you hit a car?", "Did you go over the handlebars?",
            "What happened tonight?", "Can you tell me about the crash?"],
  echo="how the crash happened")

# Owner, 29 October 2026: "If someone asks how fast he was going, you can say I don't know
# but top speed is 40 mph."
topic("speed",
  "'I don't know. I don't remember the ride. It tops out at forty miles an hour.'",
  "'Don't know... forty, tops.'",
  canonical="How fast were you going?",
  variants=["Were you going fast?", "What speed were you going?", "How fast was the scooter going?",
            "Do you know how fast you were going?", "What was your speed?", "Were you speeding?",
            "How fast does the scooter go?", "What's the top speed of the scooter?",
            "How fast can it go?", "Was it a fast scooter?", "Roughly what speed?",
            "Were you going full speed?", "How fast was he going?"],
  echo="how fast I was going")

topic("helmet",
  "'No helmet. I know. It's like a ten minute ride.'",
  "'No... no helmet.'",
  canonical="Were you wearing a helmet?",
  variants=["Helmet?", "Did you have a helmet on?", "Was he wearing a helmet?",
            "Do you wear a helmet?", "Any helmet?", "Was your head protected?",
            "Did you have any protective gear on?", "Helmeted?", "Was there a helmet?",
            "Did the helmet crack?", "Do you usually wear a helmet on the scooter?"],
  echo="the helmet")

topic("loss_of_consciousness",
  "'Marcus says I was out for like a minute. I don't remember being on the ground. The next "
  "thing I really remember is the ambulance.'",
  "'Out... for a minute, Marcus said.'",
  canonical="Did you lose consciousness?",
  variants=["Were you knocked out?", "Did you black out after the crash?", "Were you unconscious?",
            "How long were you out?", "Did you get knocked out?", "Were you out cold?",
            "Did you pass out when you hit your head?", "Were you awake the whole time?",
            "Do you remember hitting the ground?", "Did anyone see you lose consciousness?",
            "How long was he out for?", "Were you unresponsive at the scene?"],
  echo="being knocked out")

topic("memory_of_event",
  "'The last thing I remember is leaving Marcus's building and getting on the scooter. Then "
  "the ambulance. Nothing in between. People keep telling me what happened.'",
  "'I don't... remember. What happened?'",
  canonical="What's the last thing you remember before the crash?",
  variants=["Do you remember the crash?", "Do you remember what happened?", "Any memory loss?",
            "What do you remember?", "Can you remember the accident?", "Any amnesia?",
            "Do you remember getting in the ambulance?", "Is there a gap in your memory?",
            "What's the first thing you remember after?", "Amnesia?",
            "Any trouble with your memory?", "Do you remember coming here?",
            "Do you remember leaving your friend's place?"],
  echo="what I remember")

topic("how_he_got_here",
  "'The ambulance brought me. I don't really remember getting in it.'",
  "'Ambulance... I think.'",
  canonical="How did you get here?",
  variants=["How did you get here today?", "Did you come in by ambulance?", "Who brought you in?",
            "Did EMS bring you?", "Did you come by ambulance?", "Did the paramedics bring you?",
            "Did someone drive you here?", "Did you walk in?", "Who called the ambulance?",
            "Did Marcus call 911?"],
  echo="how I got here")

topic("orientation",
  "'I'm Danny. Danny Ortiz. I'm twenty-two, my birthday's March third. I'm in the hospital, "
  "because I crashed the scooter, they told me. It's Monday night.'",
  "'Danny... I'm at... work? No. I don't know what day it is.'",
  canonical="Can you tell me your name and where you are?",
  variants=["What's your name?", "Can you confirm your name for me?", "What is your date of birth?",
            "How old are you?", "Do you know where you are?", "Where are you right now?",
            "What day is it?", "What is the date today?", "Do you know why you are here?",
            "What year is it?", "Do you know what happened to you?", "Are you oriented?",
            "Who is the president?", "What month is it?", "Can you tell me where we are?"],
  echo="where I am")

# --------------------------------------------------------------- the head
topic("headache",
  "'My head is killing me. The right side, where I hit it. It's pounding.'",
  "'My head... it really hurts.'")

topic("location_of_pain",
  "'The right side of my head, over my ear. It's swollen there.'",
  "'Here... the side.'")

topic("radiation_of_pain",
  "'It's mostly the right side. It's spreading a bit over the top.'",
  "'All over... now.'")

topic("severity",
  "'Like a six out of ten. Maybe worse when I move.'",
  "'Bad. Really bad.'")

topic("character_of_symptoms",
  "'Pounding. Like a hangover headache, but on one side.'",
  "'Pounding...'")

topic("onset",
  "'Right after the crash, I guess. Whenever I woke up it was already there.'",
  "'Since... the crash.'")

topic("timing_progression",
  "'The headache's been getting worse since the ambulance. And I feel a bit sick now.'",
  "'Worse. It's worse.'")

topic("aggravating_relieving",
  "'Moving my head makes it worse. The ice pack helps a little.'",
  "'Moving... makes it worse.'")

topic("nausea_vomiting",
  "'A bit queasy. I haven't thrown up.'",
  "'I threw up. I feel... sick.'")

topic("vision_changes",
  "'No double vision. Everything looks normal. The lights are okay.'",
  "'No... I can see okay.'",
  canonical="Any changes in your vision?",
  variants=["Any double vision?", "Any blurred vision?", "Is your vision blurry?",
            "Can you see properly?", "Any trouble seeing?", "Are you seeing double?",
            "Any vision problems?", "Diplopia?", "Visual changes?", "Can you see clearly?",
            "Any loss of vision?", "Are your eyes okay?"],
  echo="my vision")

topic("hearing",
  "'No, I can hear fine. No ringing.'",
  "'I can hear... you.'",
  canonical="Any problems with your hearing?",
  variants=["Any ringing or buzzing in your ears?",
            "Any earache?", "Can you hear okay?", "Any ringing in your ears?", "Tinnitus?",
            "Any hearing loss?", "Is there anything coming out of your ears?",
            "Any fluid from your ears or nose?", "Any bleeding from your ear?",
            "Is your hearing the same on both sides?"],
  echo="my hearing")

topic("weakness_numbness",
  "'No, my arms and legs feel normal. No numbness or tingling. I'm talking okay, I think.'",
  "'Arms... legs are fine.'",
  canonical="Any weakness or numbness?",
  variants=["Any numbness anywhere?", "Any pins and needles?", "Any tingling?",
            "Any problems with your speech?", "Can you move everything?",
            "Any trouble moving your arms or legs?", "Is one side weaker than the other?",
            "Numbness or tingling?", "Any facial droop?", "Can you feel your hands and feet?",
            "Any focal weakness?", "Any slurred speech?"],
  echo="weakness or numbness")

topic("seizure",
  "'Not that I know of. Marcus didn't say anything like that.'",
  "'No... I don't think so.'",
  canonical="Did you have a seizure?",
  variants=["Any seizures or fits?", "Did you shake at all after the crash?", "Any seizure activity?",
            "Did Marcus see you shaking?", "Did you have a fit?", "Seizure?",
            "Any convulsions?", "Have you ever had a seizure?", "Did you bite your tongue?",
            "Did you wet yourself?", "Any jerking movements?"],
  echo="a seizure")

topic("dizziness",
  "'A little off when I sat up, but not spinning. Mostly it's the headache.'",
  "'Dizzy... a bit.'",
  canonical="Do you feel dizzy?",
  variants=["Any problems with your balance?", "Are you dizzy?", "Is the room spinning?",
            "Do you feel unsteady?", "Vertigo?", "Any lightheadedness?", "Do you feel off balance?",
            "Any dizziness since the crash?", "Were you steady on your feet at the scene?",
            "Could you walk after the crash?"],
  echo="feeling dizzy")

topic("neck_pain",
  "'No, my neck's fine. Just my head.'",
  "'Neck... fine.'",
  canonical="Does your neck hurt?",
  variants=["Neck pain?", "Any pain in your neck?", "Does it hurt in the back of your neck?",
            "Any tenderness in your neck?", "Did you hurt your neck?", "Is your neck okay?",
            "Any pain when you move your neck?", "Does your neck hurt when I press here?",
            "Any C-spine pain?", "Midline neck pain?"],
  echo="my neck")

topic("other_injuries",
  "'My hands sting, I must have put them out. Nothing else hurts. My back's fine.'",
  "'My hands... sting.'",
  canonical="Does anything else hurt?",
  variants=["Any other injuries?", "Are you hurt anywhere else?", "Any back pain?",
            "Have you broken any bones?", "Any pain in your hands?", "Does your chest or belly hurt?",
            "Any other pain?", "Where else are you hurt?", "Did you hurt anything else?",
            "Any pain in your arms or legs?", "Any injuries other than your head?"],
  echo="anything else that hurts")

topic("chest_pain", "'No, my chest is fine.'", "'No.'")
topic("breathing", "'Breathing's fine.'", "'Fine...'")
topic("abdominal_pain", "'No, my stomach doesn't hurt.'", "'No.'")

# --------------------------------------------------------------- history
topic("past_medical_history",
  "'Nothing. I'm healthy. Never been in the hospital.'",
  "'Nothing... I'm healthy.'")

topic("past_surgical_history", "'No surgeries.'", "'No.'")

topic("current_medications",
  "'I don't take anything. Nothing at all.'",
  "'Nothing.'")

topic("anticoagulants",
  "'No blood thinners. No aspirin or anything. I don't take any pills.'",
  "'No... no pills.'",
  canonical="Are you on any blood thinners?",
  variants=["Do you take aspirin?", "Any aspirin or ibuprofen today?", "Are you on Eliquis?",
            "Are you on Xarelto?", "Do you take anything that thins your blood?",
            "Any antiplatelets?", "Blood thinners?", "Any blood thinning medication?",
            "Are you on Plavix?", "Any history of bleeding problems?", "Do you bruise easily?"],
  echo="blood thinners")

topic("allergies", "'No allergies.'", "'No.'")

topic("family_history",
  "'My dad has high blood pressure. Nobody has bleeding problems that I know of.'",
  "'I don't... know.'")

topic("social_history",
  "'I work at a bike shop. I live with a roommate. I vape sometimes. I'll have a couple of "
  "beers at the weekend, but nothing tonight. No drugs.'",
  "'Nothing tonight... no drugs.'",
  more=["Have you had anything to drink tonight?", "Have you been drinking?", "Any alcohol tonight?",
        "Did you take anything tonight?", "Any drugs tonight?", "Were you drunk?",
        "What do you do for a living?", "Where do you work?", "Who do you live with?"])

topic("last_oral_intake",
  "'Dinner around seven. Tacos at Marcus's place. Just water since.'",
  "'Dinner... at seven.'")

topic("functional_baseline",
  "'Normally I'm totally fine. I ride to work every day.'",
  "'I'm... normally fine.'")

topic("tetanus",
  "'I think I had one in high school? I'm not sure.'",
  "'I don't know.'",
  canonical="When was your last tetanus shot?",
  variants=["When was your last tetanus?", "Are you up to date with tetanus?", "Tetanus status?",
            "Have you had a tetanus booster?", "Tdap?", "When was your last Tdap?",
            "Are your shots up to date?", "Tetanus shot?", "Have you had a tetanus jab?",
            "Is your tetanus current?"],
  echo="my tetanus shot")

topic("companion",
  "'Marcus was with me. He's on his way here. My mom's in Orlando, Marcus has her number.'",
  "'Marcus... is coming.'",
  canonical="Is anyone here with you?",
  variants=["Is anyone with you?", "Is there anyone we should call for you?", "Who is your next of kin?",
            "Is your family in the waiting room?", "Who can we contact for you?", "Is your friend here?",
            "Where is Marcus?", "Is anyone coming?", "Do you want us to call someone?",
            "Emergency contact?"],
  echo="who's with me")

GLOBAL_RULES = [
 {"when": "phase is case_complete", "value": "He has gone to the operating room.",
  "note": "After the handoff."},
 {"when": "flag intubated set", "value": "He's intubated and sedated. He can't answer you.",
  "note": "After a tube, in any phase. Goal G3: the tube costs the history as well as the exam."},
 {"when": "phase is herniation OR phase is temporized OR phase is brainstem_compression",
  "value": "He doesn't answer. He only groans when the nurse rubs his chest.",
  "note": ("Alertness 2 in herniation and temporized, 3 in brainstem compression (authoring "
           "8.5). Nobody else is at the bedside: Marcus is on his way.")},
]

OUT_OF_SCOPE = [
 {"when": DECL, "value": "'What? I... sorry. My head.'"},
 {"when": None, "value": "'Sorry, I'm not following. My head's pounding. Can you ask me another way?'"},
]

AUTHORING_NOTES = {
 "voice": "A 22-year-old who is friendly, a bit embarrassed about the helmet, and repeats himself. In the decline, two to five words, trailing off.",
 "the_crash": (
   "He does not remember the crash. Everything he says about it is what Marcus told him, "
   "and he says so. That is the amnesia, and it is a finding."),
 "the_decline": (
   "Every topic has a decline answer that keeps the fact. The decline answer to nausea is "
   "different because he has now vomited. Orientation is the one topic where the decline "
   "answer is wrong on purpose: that is the V4."),
 "facts_not_used": "No topic carries facts. Each answer is short enough to stand on its own.",
 "added": (
   "Model-added, awaiting sign-off: his name (Danny Ortiz) and birthday, Marcus by name, "
   "the bike shop, the roommate, vaping, a couple of beers at weekends, tacos at seven, his "
   "father's high blood pressure, his mother in Orlando, the 6 of 10, the tetanus answer, "
   "and every denial."),
}

# The same list as management_changing in SCOOT-matcher-eval-questions.json (authoring 8.6).
KEY_TOPICS = ["mechanism_of_injury", "loss_of_consciousness", "memory_of_event", "headache",
              "nausea_vomiting", "seizure", "neck_pain", "anticoagulants", "current_medications",
              "past_medical_history", "allergies", "social_history", "last_oral_intake"]

VOLUNTEER_SETTINGS = {
 "must_ask": ["anticoagulants", "allergies", "current_medications", "past_medical_history",
              "social_history", "last_oral_intake", "seizure", "helmet"],
 "volunteers_note": "Nothing is volunteered. No topic carries adjacent topics or volunteer lines.",
}

# ---------------------------------------------------------------- shared phrasings

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
 'answer': [{'when': 'phase is decline',
             'value': "'The scooter... I don't... remember. My head...'"},
            {'when': None,
             'value': "'I came off my scooter. I don't remember it, but Marcus says I hit a "
                      'pothole and went over the handlebars onto the right side of my head. My '
                      "head's been pounding ever since, and it's getting worse.'"}],
 'echo': 'what happened',
 'authoring_note': 'Authoring 8.2: a greeting or an open question gets a brief history of the '
                   "present illness. Added 30 October 2026 on the owner's instruction. The answer "
                   "was written by a model from this case's own onset, progression and character "
                   'answers and its arrival handover, and stops short of every disclosure the case '
                   'keeps behind its own question. Not physician reviewed. Variants copied from '
                   'DIPH and catalog/interview_phrasings.py (questions, not facts).'})

TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"],
 "character_of_symptoms": ["character_general"], "location_of_pain": ["location_pain"],
 "radiation_of_pain": ["radiation_pain"], "severity": ["severity"],
 "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"],
 "nausea_vomiting": ["nausea_vomiting"], "headache": ["headache"],
 "chest_pain": ["chest_pain"], "breathing": ["breathing_sob"], "abdominal_pain": ["abdominal_pain"],
 "past_medical_history": ["pmh"], "past_surgical_history": ["psh"], "current_medications": ["meds"],
 "allergies": ["allergies"], "family_history": ["family_history"],
 "social_history": ["social_history", "smoking", "alcohol", "substance_use"],
 "last_oral_intake": ["last_oral_intake"], "functional_baseline": ["functional_baseline"],
 "loss_of_consciousness": ["syncope"], "orientation": ["confusion"], "neck_pain": ["neck_stiffness"],
 "vision_changes": ["photophobia"], "weakness_numbness": ["weakness"], "dizziness": ["dizziness"],
 "anticoagulants": ["anticoag"],
}

# Cover tags the answers cover without drawing phrasings. occupation: the social history
# answer says where he works. back_pain: the other injuries answer says his back is fine.
EXTRA_COVERED = ["occupation", "back_pain"]
