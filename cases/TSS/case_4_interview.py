"""TSS part 4: the interview.

The patient answers for herself. She is alert in every phase except profound shock, where a
global rule speaks for her, and she is drowsy in the hypotensive phase, where every topic
has a shorter answer carrying the same fact.

Every answer is model output. The history it restates is PATIENT["background"] in case_1,
which is also model output. Nothing here has been reviewed by a physician.

What she knows and does not know, which is the design of this interview:

  - She believes she has food poisoning and says so. She never names any other diagnosis.
  - She has an explanation for the red skin (the beach) and offers it. It is wrong.
  - She does not connect her period to her illness and will not bring it up. Asked
    directly, she says she cannot remember taking the last tampon out. That is the honest
    answer and it is the single most useful sentence in the history.
  - Her roommate ate the same meal and is well. She finds that odd and says so if asked.
"""
from case_4_variants import SHARED

HYPO = "phase is hypotensive"
PROF = "phase is profound_shock"
TUBED = "flag intubated set"

TOPICS = []

NEGATIVES = {
 "radiation_of_pain", "neck_stiffness", "photophobia", "chest_pain", "confusion",
 "travel_history", "tick_and_outdoor_exposure", "recent_antibiotics_healthcare",
 "wounds_and_skin", "past_medical_history", "allergies", "pregnancy",
}


def fact(fid, asks, value, short=None, restate=False):
    rules = ([{"when": HYPO, "value": short}] if short else []) + [{"when": None, "value": value}]
    f = {"id": fid, "asks": asks, "value": rules}
    if restate:
        f["restate"] = True
    return f


def topic(tid, full, short, canonical=None, variants=None, echo=None, facts=None):
    """`full` is the answer when she is alert. `short` is the same fact said by a drowsy,
    hypotensive patient (authoring 10.5). Phrasings come from SHARED unless given."""
    s = SHARED.get(tid, {})
    t = {"topic": tid,
         "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]),
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
  "'Two days ago. Thursday night I started shivering and aching, and by the early hours I "
  "was throwing up. The diarrhea started Friday morning.'",
  "'Two days ago. Thursday night.'",
  facts=[
    fact("when", ["when exactly", "what day", "what time", "how long ago"],
         "'Thursday night, maybe eleven. So two and a half days.'",
         "'Thursday night.'", restate=True),
    fact("first_symptom", ["what came first", "what was the first thing", "how did it start"],
         "'The shivering and the aching came first. The vomiting was a few hours after that.'",
         "'Shivering. Then being sick.'")])

topic("timing_progression",
  "'Worse. Yesterday I could get up and about for a bit. Today I can't stand without "
  "everything going gray.'",
  "'Worse. Much worse today.'")

topic("character_of_symptoms",
  "'Like the worst flu I've ever had. Everything aches, I'm hot and cold, and my stomach "
  "keeps turning over.'",
  "'Like flu. Everything aches.'")

topic("location_of_pain",
  "'All over, really. My thighs and my back are the worst. My stomach is crampy but it's "
  "not one spot.'",
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
  "'Yes. Hot and shivery for two days.'")

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
  "'Constantly. I've thrown up maybe eight or ten times since Friday. No blood in it. I "
  "can't even keep water down now.'",
  "'Yes. Loads. Can't keep water down.'")

topic("diarrhea",
  "'Yes, watery. Maybe six times yesterday and a few today. No blood.'",
  "'Yes. Watery. No blood.'")

topic("abdominal_pain",
  "'Crampy, all over, and it comes with the diarrhea. It's not a sharp pain anywhere, and "
  "not in my sides or my back.'",
  "'Crampy. All over.'")

topic("chest_pain",
  "'No chest pain. My heart's racing, though. I can feel it when I stand up.'",
  "'No. My heart's racing.'")

topic("breathing",
  "'I'm not short of breath exactly. I just feel like I'm breathing fast.'",
  "'A bit fast. I'm okay.'")

topic("cough_sore_throat",
  "'No cough, no cold. My throat's sore, I thought from being sick so much.'",
  "'No cough. Sore throat.'")

topic("urine_output",
  "'Hardly at all. I think I went once yesterday and it was really dark. Nothing today. It "
  "doesn't burn.'",
  "'Barely. Not today.'")

topic("dizziness_syncope",
  "'Yes. This morning in the shower everything went gray and I had to sit down on the "
  "floor. I didn't black out. My roommate found me and made me come in.'",
  "'Yes. Nearly fainted this morning.'")

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
  "'Nothing. I'm never ill. I've never been in hospital.'",
  "'Nothing. I'm healthy.'")

topic("past_surgical_history",
  "'I had my wisdom teeth out at eighteen. That's it, nothing else removed.'",
  "'Wisdom teeth. That's all.'")

topic("current_medications",
  "'Just the pill. I took ibuprofen yesterday, two tablets a couple of times. Nothing else, "
  "no supplements.'",
  "'The pill. Some ibuprofen yesterday.'")

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
  "'I had a few sips of water this morning and brought them back up. I haven't eaten since "
  "Thursday.'",
  "'Sips of water. Nothing since Thursday.'")

topic("vaccinations",
  "'I think so. I had everything for college, including the meningitis ones. I had a flu "
  "shot last fall.'",
  "'Yes. Everything for college.'")

topic("sick_contacts",
  "'No. My roommate had the same takeout I did on Thursday and she's completely fine. My "
  "boyfriend's fine too. Nobody I know is sick.'",
  "'No. My roommate ate the same and she's fine.'")

topic("suspect_meal",
  "'Thai takeout on Thursday, about seven. I started feeling ill a few hours later. My "
  "roommate ate the same dishes and she's fine, which is the part I don't get.'",
  "'Takeout on Thursday. My roommate had it too.'",
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
           "it is food poisoning and says so, which is her belief and not a diagnosis the "
           "case endorses."),
 "the_tampon": ("She does not volunteer it and it is a must-ask topic, so no other answer "
                "carries it. Asked about her period or tampons in any wording, she says she "
                "cannot remember taking the last one out. Section 10.4 holds: she reports "
                "what she knows and draws no conclusion from it."),
 "close_to_the_line": ("Two answers sit near the section 10.4 line and are flagged for the "
                       "reviewer. The rash answer says the redness is under her shirt, and "
                       "the genitourinary answer mentions a smell. Both are things a patient "
                       "would notice and say. Neither names a cause."),
 "phrasings": ("The canonical question, hand-written variants and echo for forty topics are "
               "MGCA's, in case_4_variants.py. Three topics are this case's own: rash, "
               "suspect_meal and wounds_and_skin."),
}

KEY_TOPICS = ["menstrual_and_tampon", "rash", "sick_contacts", "urine_output",
              "dizziness_syncope", "fever_and_chills", "pregnancy", "allergies",
              "current_medications"]

# --------------------------------------------------------------- volunteered answers
# Written by hand for this pack. Safety screens and the topic the case is built around the
# learner discovering are in must_ask and are never volunteered (authoring 10.7).
ADJACENT = {
 "onset": ["fever_and_chills", "nausea_vomiting"],
 "nausea_vomiting": ["diarrhea"],
 "diarrhea": ["abdominal_pain"],
 "suspect_meal": ["sick_contacts"],
 "past_medical_history": ["past_surgical_history"],
 "location_of_pain": ["joint_pain"],
}
VOLUNTEER = {
 "fever_and_chills": "'I've been hot and shivery the whole time.'",
 "nausea_vomiting": "'I've been throwing up since early Friday.'",
 "diarrhea": "'And I've had watery diarrhea since Friday morning.'",
 "abdominal_pain": "'My stomach's crampy with it.'",
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

# ---- EXPANDED VARIANTS (generated, do not edit by hand) ----
# Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py in Sep 202
# 6. The added phrasings were written by an AI assistant, not by a physician, and mix lay paraphr
# ase, clinical shorthand and conversational forms. Every sixth new phrasing was withheld into the pack's tuning set rather than added here.
EXPANDED = {
  'onset': [
    'When did this begin?',
    'How long ago did this come on?',
    'Onset?',
    'Time of onset?',
    'When did it come on?',
    'Sudden or gradual onset?',
    'How long have you had this?',
    'When did you start feeling like this?',
    'What were you doing when it started?',
    'Where were you when it began?',
    'How many hours or days has this been going on?',
    'Tell me how it began.',
    'Take me back to when this started.',
    'Walk me through the start of this.',
    'When did things first go wrong?',
    'Sorry to ask, but when did this begin?',
    'One more thing. When did this begin?',
    'Can I ask, what time did it start?',
    'Sorry to ask, but what time did it start?',
    'One more thing. How long ago did this come on?',
  ],
  'timing_progression': [
    'Is it getting worse or better?',
    'How has it changed since it began?',
    'Constant or does it come and go?',
    'Intermittent or continuous?',
    'Progression?',
    'Is it worse than it was earlier?',
    'Any change over the last few hours?',
    'Is it easing off at all?',
    'Getting worse?',
    'Has it settled at any point?',
    'Compared with when it started, how is it now?',
    'Is this the worst it has been?',
    'Does it fluctuate?',
    'Has it been steadily building?',
    'Better, worse, or the same?',
    'Has it let up at all?',
    'And is it getting worse or better?',
    'Can I ask, is it getting worse or better?',
    'Right. How has it changed since it began?',
    'Quick one: how has it changed since it began?',
    'Before we go on, constant or does it come and go?',
  ],
  'character_of_symptoms': [
    'Describe what you are feeling.',
    'Tell me about the symptoms.',
    'Character of the symptoms?',
    'What is the main thing bothering you?',
    'What sort of feeling is it?',
    'Can you put it into words for me?',
    'What does it feel like in your body?',
    'Tell me more about how you feel.',
    'Describe the discomfort.',
    'One more thing. What does it feel like?',
    'Quick one: how would you describe it?',
    'Before we go on, how would you describe it?',
    'Can I ask, character of the symptoms?',
    'Sorry to ask, but character of the symptoms?',
  ],
  'location_of_pain': [
    'Location of the pain?',
    'Where exactly is it?',
    'Is it in one place or all over?',
    'Where do you feel it most?',
    'Which part of you hurts?',
    'Can you localize the pain?',
    'Where is it worst?',
    'Is the pain in your muscles?',
    'Are your legs the worst of it?',
    'Where does it hurt right now?',
    'Before we go on, where is the pain?',
    'Just so I know, location of the pain?',
    'I need to know, location of the pain?',
    'Okay, where exactly is it?',
    'Just so I know, where exactly is it?',
  ],
  'radiation_of_pain': [
    'Does the pain move anywhere?',
    'Does it spread?',
    'Does it go anywhere else?',
    'Radiation?',
    'Does the pain travel?',
    'Does it go through to your back?',
    'Any radiation of the pain?',
    'Does it stay put or move around?',
    'Does the pain shoot anywhere?',
    'Is it spreading from where it started?',
    'Can I ask, does the pain move anywhere?',
    'Just so I know, does it spread?',
    'I need to know, does it spread?',
    'Sorry to ask, but does it go anywhere else?',
    'One more thing. Does it go anywhere else?',
  ],
  'severity': [
    'Out of ten, how bad is it?',
    'Severity?',
    'Is it the worst you have ever had?',
    'Ten being the worst pain imaginable, where are you?',
    'Mild, moderate, or severe?',
    'Can you score it for me?',
    'Pain score?',
    'How bad on a scale?',
    'Is it bearable?',
    'How intense is it?',
    'Before we go on, out of ten, how bad is it?',
    'Just so I know, how severe is it?',
    'I need to know, how severe is it?',
    'Can I ask, on a scale of one to ten?',
    'Sorry to ask, but on a scale of one to ten?',
  ],
  'aggravating_relieving': [
    'What makes it better or worse?',
    'Anything make it better or worse?',
    'Aggravating or relieving factors?',
    'Does anything help or make it worse?',
    'What eases it and what sets it off?',
    'Have you found anything that helps?',
    'Is there anything that makes it flare?',
    'Does anything you do change it?',
    'What have you tried for it?',
    'Anything that brings it on?',
    'Aggravating factors?',
    'Is it worse with movement?',
    'Worse with exertion?',
    'Does walking make it worse?',
    'Does lying down make it worse?',
    'Does anything make it flare up?',
    'Is it worse at any particular time?',
    'Does breathing in make it worse?',
    'Does it get worse when you do anything?',
    'What makes it better?',
    'Anything ease it?',
    'Does resting help?',
    'Does sitting up help?',
    'Did anything you tried make a difference?',
    'What helps?',
    'Is there anything that eases it off?',
    'Any position that helps?',
    'Does oxygen help?',
    'Did painkillers help?',
    'Right. What makes it better or worse?',
    'Sorry to ask, but anything make it better or worse?',
    'One more thing. Anything make it better or worse?',
    'Before we go on, aggravating or relieving factors?',
    'And aggravating or relieving factors?',
  ],
  'rash': [
    'Any rash?',
    'Where is the rash?',
    'Does the rash blanch?',
    'Any spots?',
    'Any marks on your skin?',
    'What does the rash look like?',
    'Any bruising or spots?',
    'Any skin changes?',
    'Any purple spots?',
    'Does the rash fade when pressed?',
    'Is the rash getting bigger?',
    'Any new spots?',
    'Any petechiae?',
    'And where is the rash?',
    'Can I ask, where is the rash?',
    'Can I ask, when did the rash start?',
    'Quick one: does the rash blanch?',
    'Before we go on, does the rash blanch?',
  ],
  'fever_and_chills': [
    'Fever?',
    'Fevers or chills?',
    'Fevers, chills, rigors?',
    'Any temperature?',
    'Have you had a temperature?',
    'Night sweats?',
    'Do you feel hot and cold?',
    'Have you felt feverish?',
    'Have you had the shivers?',
    'Temp at home?',
    'Have you been burning up?',
    'Can I ask, fevers or chills?',
    'Sorry to ask, but fevers or chills?',
    'I need to know, fevers, chills, rigors?',
    'Right. Fevers, chills, rigors?',
    'Just so I know, any temperature?',
  ],
  'headache': [
    'Headache?',
    'Any pain in your head?',
    'Worst headache ever?',
    'Have you had a headache with this?',
    'Is the headache new?',
    'Can I ask, does your head hurt?',
    'Sorry to ask, but does your head hurt?',
    'Okay, any head pain?',
    'Just so I know, any head pain?',
    'Sorry to ask, but is your head sore?',
  ],
  'neck_stiffness': [
    'Neck stiffness?',
    'Any stiffness in the neck?',
    'Can you touch your chin to your chest?',
    'Does it hurt to move your neck?',
    'Meningism?',
    'Is your neck sore?',
    'Any stiff neck?',
    'Does your neck feel tight?',
    'Can you look down at your feet?',
    'Is your neck painful to move?',
    'Quick one: neck stiffness?',
    'Before we go on, neck stiffness?',
    'And is your neck stiff?',
    'Can I ask, is your neck stiff?',
    'Quick one: any stiffness in the neck?',
  ],
  'photophobia': [
    'Photophobia?',
    'Do lights hurt your eyes?',
    'Is the light bothering you?',
    'Are the lights too bright?',
    'Does light hurt?',
    'Is the brightness painful?',
    'Do bright lights make it worse?',
    'Do you prefer it dark?',
    'Sorry to ask, but do lights hurt your eyes?',
    'One more thing. Do lights hurt your eyes?',
    'I need to know, any photophobia?',
    'And is the light bothering you?',
    'Can I ask, is the light bothering you?',
  ],
  'nausea_vomiting': [
    'N/V?',
    'Nausea or vomiting?',
    'Have you thrown up?',
    'Do you feel sick?',
    'Any retching?',
    'Been throwing up?',
    'Any nausea or vomiting?',
    'Do you feel nauseous?',
    'How many times have you vomited?',
    'Any sickness?',
    'And nausea or vomiting?',
    'Just so I know, have you been sick?',
    'I need to know, have you been sick?',
    'Okay, have you thrown up?',
    'Just so I know, have you thrown up?',
  ],
  'diarrhea': [
    'Diarrhea?',
    'Have your bowels been loose?',
    'Any change in your bowels?',
    'Been to the toilet a lot?',
    'Any runny stools?',
    'Bowels okay?',
    'Any loose bowel movements?',
    'I need to know, any loose stools?',
    'Right. Any loose stools?',
    'One more thing. Any loose motions?',
    'Can I ask, have your bowels been loose?',
    'Sorry to ask, but have your bowels been loose?',
  ],
  'abdominal_pain': [
    'Any tummy pain?',
    'Does your belly hurt?',
    'Any stomach pain?',
    'Abdo pain?',
    'Is your stomach sore?',
    'Any pain in the tummy?',
    'Does it hurt in your stomach?',
    'Any cramping in your belly?',
    'Any abdominal tenderness?',
    'Just so I know, any abdominal pain?',
    'Okay, any tummy pain?',
    'Just so I know, any tummy pain?',
    'Before we go on, does your belly hurt?',
    'And does your belly hurt?',
  ],
  'chest_pain': [
    'Chest pain?',
    'cp?',
    'Any cp?',
    'Pain in the chest?',
    'Is your chest hurting?',
    'Any pressure in the chest?',
    'Does your chest hurt at all?',
    'Chest tightness?',
    'Any pain across the chest?',
    'Has there been any chest discomfort?',
    'Is there pain in your chest?',
    'Any heaviness on your chest?',
    'Any pain when you breathe in?',
    'c/o chest pain?',
    'Just so I know, any chest pain?',
    'Just so I know, pain in the chest?',
    'I need to know, pain in the chest?',
    'Before we go on, is your chest hurting?',
    'And is your chest hurting?',
  ],
  'breathing': [
    'Short of breath?',
    'SOB?',
    'Any SOB?',
    'Any difficulty breathing?',
    'Are you struggling to breathe?',
    'Do you feel you cannot get your breath?',
    'Breathless at all?',
    'Dyspnea?',
    'Dyspnoea?',
    'Any trouble with your breathing?',
    'Are you getting enough air?',
    'I need to know, are you breathless?',
    'Right. Are you breathless?',
    'Right. Short of breath?',
    'Quick one: short of breath?',
    'Just so I know, any shortness of breath?',
  ],
  'cough_sore_throat': [
    'Sore throat?',
    'Any cough?',
    'Any cold symptoms?',
    'Runny nose or sore throat?',
    'Any coryzal symptoms?',
    'Any URTI symptoms?',
    'Have you had a cough?',
    'Any flu-like symptoms before this?',
    'Any sniffles or cough?',
    'Any cold before this started?',
    'Right. Any cough or sore throat?',
    'Okay, any cold symptoms?',
    'Just so I know, any cold symptoms?',
    'Just so I know, runny nose or sore throat?',
    'I need to know, runny nose or sore throat?',
  ],
  'urine_output': [
    'Are you passing urine?',
    'Urine output?',
    'How much urine?',
    'Passing water okay?',
    'When did you last pass urine?',
    'Any drop in your urine?',
    'Are you peeing less?',
    'How often are you going to the toilet?',
    'Have you been passing less water?',
    'Passing much urine?',
    'Are you making urine?',
    'Have you passed water since this started?',
    'Just so I know, are you passing urine?',
    'I need to know, are you passing urine?',
    'I need to know, how much urine?',
    'I need to know, passing water okay?',
    'Right. Passing water okay?',
  ],
  'dizziness_syncope': [
    'Any dizziness or fainting?',
    'Have you felt faint or passed out?',
    'Dizzy or lightheaded at all?',
    'Syncope or presyncope?',
    'Any blackouts or dizzy spells?',
    'Have you lost consciousness or felt close to it?',
    'Any funny turns or fainting?',
    'Have you felt woozy or blacked out?',
    'Any loss of consciousness or lightheadedness?',
    'Do you feel like you might pass out?',
    'Did you black out?',
    'Syncope?',
    'Any syncope?',
    'Any collapse?',
    'Did you pass out?',
    'Did you go down at any point?',
    'LOC?',
    'Any loss of consciousness?',
    'Did you faint or nearly faint?',
    'Have you keeled over?',
    'Lightheaded?',
    'Do you feel faint?',
    'Have you felt woozy?',
    'Any spinning sensation?',
    'Any giddiness?',
    'Do you feel unsteady?',
    'Any near-fainting?',
    'Sorry to ask, but any dizziness or fainting?',
    'One more thing. Any dizziness or fainting?',
    'Right. Have you felt faint or passed out?',
    'Okay, dizzy or lightheaded at all?',
    'Just so I know, dizzy or lightheaded at all?',
  ],
  'confusion': [
    'Are you thinking clearly?',
    'Have you been muddled?',
    'Any change in your thinking?',
    'Have you been disoriented?',
    'Are you having trouble concentrating?',
    'Any altered mental state?',
    'Quick one: any confusion?',
    'Before we go on, any confusion?',
    'Right. Have you felt confused?',
    'Quick one: have you felt confused?',
    'Okay, are you thinking clearly?',
  ],
  'cold_extremities': [
    'Cold hands and feet?',
    'Are your feet cold?',
    'Do your hands feel icy?',
    'Cold peripheries?',
    'Have your hands and feet gone cold?',
    'Are your fingers cold?',
    'Cold to the touch?',
    'One more thing. Are your hands cold?',
    'Okay, are your hands cold?',
    'Right. Cold hands and feet?',
    'Can I ask, are your feet cold?',
    'Sorry to ask, but are your feet cold?',
  ],
  'joint_pain': [
    'Are your joints sore?',
    'Any swollen joints?',
    'Arthralgia?',
    'Any pain in the joints?',
    'Are your joints swollen?',
    'Do your joints ache?',
    'Any pain in your knees or ankles?',
    'Any red or hot joints?',
    'Muscle or joint pain?',
    'I need to know, any joint pain?',
    'One more thing. Are your joints sore?',
    'Okay, are your joints sore?',
    'Right. Any swollen joints?',
    'Quick one: any swollen joints?',
  ],
  'dysuria_gu_symptoms': [
    'Any burning when you pee?',
    'Dysuria?',
    'Does it sting to pass urine?',
    'Any discharge?',
    'Any vaginal symptoms?',
    'Any frequency or urgency?',
    'Any GU symptoms?',
    'Any pain when urinating?',
    'Any trouble with your waterworks?',
    'Burning on urination?',
    'Before we go on, any burning when you pee?',
    'Okay, any urinary symptoms?',
    'Just so I know, any urinary symptoms?',
    'Quick one: does it sting to pass urine?',
    'Before we go on, does it sting to pass urine?',
  ],
  'menstrual_and_tampon': [
    'LMP?',
    'Last menstrual period?',
    'Tampon use?',
    'Any tampon in at the moment?',
    'When did your last period start?',
    'Are you menstruating?',
    'Any tampon left in?',
    'Have you got a tampon in?',
    'Date of last period?',
    'Quick one: last menstrual period?',
    'One more thing. When was your last period?',
    'Okay, when was your last period?',
    'And are you on your period?',
    'Can I ask, are you on your period?',
  ],
  'pregnancy': [
    'Pregnancy?',
    'Is there any chance you are pregnant?',
    'When was your last period, could you be pregnant?',
    'Have you done a pregnancy test?',
    'Any chance you might be pregnant?',
    'One more thing. Could you be pregnant?',
    'I need to know, any chance of pregnancy?',
    'Right. Any chance of pregnancy?',
    'Okay, are you pregnant?',
    'Just so I know, are you pregnant?',
  ],
  'sexual_history': [
    'Sexual history?',
    'Any sexual partners?',
    'Any new partners recently?',
    'Sexually active?',
    'Any risk of an STI?',
    'Any sexual contact recently?',
    'Any history of sexually transmitted infections?',
    'Quick one: are you sexually active?',
    'Before we go on, are you sexually active?',
    'And sexual history?',
    'Can I ask, any sexual partners?',
    'Sorry to ask, but any sexual partners?',
  ],
  'past_medical_history': [
    'PMH?',
    'Past medical history?',
    'Any medical history?',
    'Any medical problems?',
    'What conditions do you have?',
    'Any past history?',
    'What is your medical history?',
    'Any long-term conditions?',
    'Do you have any illnesses?',
    'Any chronic conditions?',
    'Any diagnoses?',
    'Are you known to the hospital for anything?',
    'Do you see a doctor for anything regularly?',
    'Any history of diabetes, high blood pressure, anything like that?',
    'Medical history?',
    'Sorry to ask, but past medical history?',
    'Right. Any medical history?',
    'Quick one: any medical history?',
    'Can I ask, any medical problems?',
    'Sorry to ask, but any medical problems?',
  ],
  'past_surgical_history': [
    'PSH?',
    'Past surgical history?',
    'Any operations?',
    'Any surgery?',
    'Ever had surgery?',
    'Any operations in the past?',
    'Have you been under the knife?',
    'Any previous surgeries?',
    'Ever been operated on?',
    'Any history of surgery?',
    'Okay, past surgical history?',
    'Just so I know, past surgical history?',
    'Sorry to ask, but any operations?',
    'One more thing. Any operations?',
    'I need to know, ever had surgery?',
  ],
  'current_medications': [
    'What meds are you on?',
    'Medications?',
    'Current medications?',
    'What do you take?',
    'Any regular medications?',
    'What prescriptions do you have?',
    'List your medications.',
    'What pills do you take?',
    'Any regular meds?',
    'Do you take anything regularly?',
    'What are you prescribed?',
    'Any OTC medicines?',
    'Anything from the chemist?',
    'What is your medication list?',
    'Do you take any tablets?',
    'I need to know, what meds are you on?',
    'Just so I know, current medications?',
    'I need to know, current medications?',
    'Before we go on, what do you take?',
    'And what do you take?',
  ],
  'allergies': [
    'Allergies?',
    'Any allergies?',
    'Allergic to any medications?',
    'Any allergy to antibiotics?',
    'Allergic to penicillin?',
    'What are you allergic to?',
    'Any medication allergies?',
    'Drug allergies?',
    'Any allergies to anything?',
    'Sorry to ask, but any allergies?',
    'Okay, any drug allergies?',
    'Just so I know, any drug allergies?',
    'Right. Are you allergic to anything?',
    'Quick one: are you allergic to anything?',
  ],
  'social_history': [
    'Social history?',
    'SHx?',
    'Do you smoke, drink, or use drugs?',
    'Any drugs, alcohol, smoking?',
    'Tell me about smoking, alcohol and drugs.',
    'Do you drink or smoke?',
    'Do you use any drugs?',
    'Smoking, drinking, drugs?',
    'Tobacco, alcohol, illicit drugs?',
    'Any drug use at all?',
    'Smoker?',
    'Smoking history?',
    'Tobacco?',
    'tob?',
    'Any smoking?',
    'Ever smoked?',
    'Pack years?',
    'Are you a smoker?',
    'Have you ever been a smoker?',
    'Do you vape?',
    'When did you quit?',
    'Any tobacco use?',
    'Do you drink?',
    'How much alcohol?',
    'EtOH?',
    'Alcohol history?',
    'Alcohol intake?',
    'How much do you drink a week?',
    'Do you drink alcohol?',
    'Units per week?',
    'Any binge drinking?',
    'Did you have a lot to drink recently?',
    'Big weekend?',
    'How many drinks a day?',
    'Any drinking over the weekend?',
    'When did you last have a drink?',
    'Alcohol use?',
    'Drug use?',
    'Any illicit drugs?',
    'Do you use cocaine?',
    'Have you taken anything?',
    'Any stimulants or cocaine?',
    'Substance use?',
    'Do you take anything recreational?',
    'Any drugs at all?',
    'Have you used any drugs recently?',
    'Any illicit substance use?',
    'Before we go on, social history?',
    'And social history?',
    'And do you smoke, drink, or use drugs?',
    'Can I ask, any drugs, alcohol, smoking?',
    'Sorry to ask, but any drugs, alcohol, smoking?',
  ],
  'family_history': [
    'Family history?',
    'FHx?',
    'fhx cardiac',
    'Any family history?',
    'Any heart problems in the family?',
    'Anything run in the family?',
    'Any relatives with heart problems?',
    'Any sudden deaths in the family?',
    'Did your parents have heart disease?',
    'Any family history of illness?',
    'Is there anything that runs in your family?',
    'Family history of cardiac disease?',
    'Quick one: family history?',
    'Before we go on, family history?',
    'Quick one: any family history?',
    'And any heart problems in the family?',
    'Can I ask, any heart problems in the family?',
  ],
  'last_oral_intake': [
    'Last oral intake?',
    'Last PO intake?',
    'last PO',
    'When did you last drink?',
    'NPO since when?',
    'Last food or drink?',
    'Anything to eat or drink today?',
    'When did you last have something to drink?',
    'Are you eating and drinking?',
    'Have you kept any fluids down?',
    'When did you last eat anything?',
    'Have you managed any food?',
    'And when did you last eat?',
    'Can I ask, when did you last eat?',
    'And last oral intake?',
    'One more thing. Last PO intake?',
    'Okay, last PO intake?',
  ],
  'vaccinations': [
    'Vaccination history?',
    'Vaccines?',
    'Any immunizations?',
    'Have you had your jabs?',
    'Immunization history?',
    'Are you vaccinated?',
    'Did you have your school vaccines?',
    'Are your immunizations current?',
    'Have you had all your childhood vaccines?',
    'Meningococcal vaccine?',
    'Right. Are your vaccinations up to date?',
    'Quick one: are your vaccinations up to date?',
    'One more thing. Vaccination history?',
    'Okay, vaccination history?',
    'Just so I know, any immunizations?',
  ],
  'sick_contacts': [
    'Anyone else unwell?',
    'Is anyone around you sick?',
    'Has anyone you live with been ill?',
    'Anyone at home with the same thing?',
    'Any contact with someone unwell?',
    'Has anyone else got this?',
    'Any friends or flatmates sick?',
    'Anybody close to you unwell recently?',
    'Has anyone you know had similar symptoms?',
    'Just so I know, any sick contacts?',
    'Sorry to ask, but anyone else unwell?',
    'One more thing. Anyone else unwell?',
    'Sorry to ask, but is anyone around you sick?',
    'One more thing. Is anyone around you sick?',
  ],
  'travel_history': [
    'Been abroad recently?',
    'Have you traveled?',
    'Any foreign travel?',
    'Travel history?',
    'Any trips recently?',
    'Any travel in the last few months?',
    'Any overseas travel?',
    'Been away anywhere?',
    'Right. Any recent travel?',
    'Quick one: any recent travel?',
    'I need to know, been abroad recently?',
    'Okay, have you traveled?',
    'Just so I know, have you traveled?',
  ],
  'tick_and_outdoor_exposure': [
    'Any tick bites?',
    'Have you been hiking or camping?',
    'Any time outdoors?',
    'Been in the woods recently?',
    'Any bites?',
    'Any outdoor activities recently?',
    'Any animal exposure?',
    'Have you been bitten by anything?',
    'Any camping trips?',
    'Tick exposure?',
    'Right. Any tick bites?',
    'Before we go on, any insect bites?',
    'And any insect bites?',
    'Before we go on, have you been hiking or camping?',
    'And have you been hiking or camping?',
  ],
  'recent_antibiotics_healthcare': [
    'Have you seen a doctor recently?',
    'Any recent hospital visits?',
    'Have you been on antibiotics?',
    'Any recent healthcare contact?',
    'Did you see your GP about this?',
    'Any antibiotics in the last few weeks?',
    'Been to a doctor for this?',
    'Have you taken any antibiotics?',
    'Any recent prescriptions?',
    'Did anyone treat you before you came in?',
    'Quick one: any recent antibiotics?',
    'Before we go on, any recent antibiotics?',
    'I need to know, have you seen a doctor recently?',
    'Right. Have you seen a doctor recently?',
    'Right. Any recent hospital visits?',
  ],
  'functional_baseline': [
    'What is your normal exercise tolerance?',
    'Exercise tolerance?',
    'ET?',
    'Baseline function?',
    'How far can you normally walk?',
    'What can you usually do?',
    'How active are you normally?',
    'What were you like before this?',
    'Functional baseline?',
    'What is your baseline?',
    'How far could you walk last week?',
    'What is normal for you?',
    'Do you manage your own shopping and housework?',
    'How were you managing before this started?',
    'Are you usually fit and well?',
    'SOB on exertion normally?',
    'Just so I know, what is your normal exercise tolerance?',
    'I need to know, what is your normal exercise tolerance?',
    'One more thing. Exercise tolerance?',
    'Okay, exercise tolerance?',
    'Quick one: baseline function?',
  ],
  'code_status_goals': [
    'Code status?',
    'Have you thought about resuscitation?',
    'What would you want if things got worse?',
    'Any wishes about treatment?',
    'Full code?',
    'Have you discussed ceilings of care?',
    'Any DNR in place?',
    'Do you have a living will?',
    'What matters most to you if this gets serious?',
    'Goals of care?',
    'Any advance care plan?',
    'If your heart stopped, what would you want us to do?',
    'Is there a DNACPR?',
    'Okay, have you thought about resuscitation?',
    'Just so I know, have you thought about resuscitation?',
    'Just so I know, do you have an advance directive?',
    'And what would you want if things got worse?',
    'Can I ask, what would you want if things got worse?',
  ],
}
OUT_OF_SCOPE_BANK = [
  'Have you ever had a colonoscopy?',
  'Any blood when you open your bowels?',
  'Are you constipated?',
  'Any heartburn?',
  'Any indigestion after meals?',
  'Have you had piles?',
  'Any black stools?',
  'Any yellowing of your skin or eyes?',
  'Do you get up at night to pass water?',
  'Any blood in your urine?',
  'Any kidney stones in the past?',
  'Any incontinence?',
  'Any seizures or fits?',
  'Any weakness in your arms or legs?',
  'Any pins and needles?',
  'Any problems with your speech?',
  'Any tremor in your hands?',
  'Any double vision?',
  'Have you ever had a stroke?',
  'Any back pain?',
  'Any cramps in your legs?',
  'Any problems with your hearing?',
  'Any ringing or buzzing in your ears?',
  'Any earache?',
  'Do you wear glasses or contact lenses?',
  'Any nosebleeds?',
  'Any moles that have changed?',
  'Any hair loss?',
  'When did you last see the dentist?',
  'Any toothache?',
  'Any lumps or bumps anywhere?',
  'Have you lost weight without trying?',
  'Any excessive thirst?',
  'Have you been feeling low in mood?',
  'Any anxiety or panic attacks?',
  'Any trouble sleeping?',
  'Have you ever received blood?',
  'Do you have a blood donor card?',
  'Who is your GP?',
  'Who is your family doctor?',
  'Have you got your NHS number?',
  'Do you have a pharmacy you usually use?',
  'Is there anyone we should call for you?',
  'Who is your next of kin?',
  'Do you have any religious needs we should know about?',
  'What did you do before you retired?',
  'Did you come in by ambulance?',
  'Is anyone here with you?',
  'Is your family in the waiting room?',
  'How did you get here today?',
  'Do you have children?',
  'How many kids do you have?',
  'Do you follow any sports?',
  'Do you watch much television?',
  'Are you comfortable on that trolley?',
  'Would you like a blanket?',
  'Is the bed at the right height?',
  'Can I get you anything?',
  'What is your date of birth?',
  'What is your address?',
  'Do you know why you are here?',
  'How old are you?',
  'Is it okay if the students watch?',
  'Would you prefer a female doctor?',
  'Is there anything you would like to ask me?',
  'What year are you in at university?',
  'What are you studying?',
  'Do you get on with your flatmates?',
  'How much does it cost to park here?',
]
for _t in TOPICS:
    if EXPANDED.get(_t['topic']):
        _t['expanded_variants'] = list(EXPANDED[_t['topic']])
        _t['variants_provenance'] = "Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py in Sep 2026. The added phrasings were written by an AI assistant, not by a physician, and mix lay paraphrase, clinical shorthand and conversational forms. Every sixth new phrasing was withheld into the pack's tuning set rather than added here."
# ---- END EXPANDED VARIANTS ----
