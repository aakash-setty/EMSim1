#!/usr/bin/env python3
"""Write each topic's `echo` and, for a subset of topics, its `facts` into the case
sources (design 10.7).

    python3 catalog/author_interview_facts.py [AFRVR|CHFE|MGCA ...]

`echo` is a short noun phrase in the patient's voice, used two ways: as a prefix when
the matcher's confidence was marginal ("My tablets? Three things...") so a wrong match
is visible in the transcript at once, and inside a clarifying question ("Sorry, do you
mean when it started, or whether it's getting worse?").

`facts` are the atomic pieces of a topic's answer, each with its own phrasings, so a
follow-up ("what time exactly?", "and how did it start?") is answered by the piece
asked about rather than by the whole paragraph again. Every fact's value is taken
from the topic's existing authored answer and says nothing the paragraph does not.
Facts are authored here for the topics where sub-questions matter most; the rest keep
paragraph answers and gain repeat handling and echoes from the engine alone.

Idempotent: re-running replaces what it wrote. For AFRVR the content lands in a
generated block in case_4_interview.py; for the other packs it is written into the
case JSON.

PROVENANCE: written by an AI assistant in September 2026 from the existing answers.
Not physician-reviewed. Where a fact's value is not a verbatim sub-string of the
paragraph it paraphrases it, and that paraphrase is the thing to review.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

GASP = "phase is respiratory_failure"                                      # AFRVR
PRES = "phase is presentation"                                             # CHFE
SICK = "phase is adrenal_crisis OR phase is progressive_meningococcaemia"  # MGCA

def F(id, asks, short_when, short, full, restate=False):
    d = {"id": id, "asks": asks, "value": [{"when": short_when, "value": short}, {"when": None, "value": full}]}
    if restate: d["restate"] = True
    return d

ECHO = {
 "AFRVR": {
  "onset": "when it started", "timing_progression": "whether it's getting worse",
  "character_of_palpitations": "what the racing feels like", "dyspnea_character": "the breathing",
  "severity": "how bad it is", "aggravating_factors": "what makes it worse", "relieving_factors": "what helps",
  "chest_pain": "chest pain", "syncope_presyncope": "whether I've passed out", "dizziness_lightheadedness": "feeling dizzy",
  "orthopnea": "lying flat", "paroxysmal_nocturnal_dyspnea": "waking up breathless", "leg_swelling": "my legs swelling",
  "weight_gain": "my weight", "exercise_tolerance_baseline": "what I could do before", "cough_and_sputum": "a cough",
  "fever_and_chills": "a temperature", "prior_afib_or_palpitations": "whether it's happened before",
  "prior_heart_failure": "heart failure", "past_medical_history": "my medical history", "past_surgical_history": "operations",
  "current_medications": "my tablets", "anticoagulant_history_and_bleeding": "blood thinners",
  "medication_adherence": "whether I take them", "allergies": "allergies", "alcohol_and_binge": "drink",
  "caffeine_and_stimulants": "coffee and that", "thyroid_symptoms": "my thyroid", "social_history_smoking": "smoking",
  "family_history": "the family", "last_oral_intake": "when I last ate", "recent_illness_or_sick_contacts": "whether I've been unwell",
  "travel_immobility_surgery": "travelling", "calf_pain_or_asymmetry": "my calves", "urine_output": "passing water",
  "nausea_and_vomiting": "feeling sick", "snoring_and_sleep_apnea": "snoring", "code_status_goals_of_care": "what I'd want if it got worse",
 },
 "CHFE": {
  "onset": "when it started", "timing_progression": "whether it's changing", "character_of_dyspnea": "the breathing",
  "severity": "how bad it is", "aggravating_factors": "what makes it worse", "relieving_factors": "what helps",
  "orthopnea": "the pillows", "paroxysmal_nocturnal_dyspnea": "waking up gasping", "leg_swelling": "my legs",
  "weight_gain": "my weight", "cough_and_sputum": "the cough", "chest_pain": "chest pain", "palpitations": "my heart racing",
  "fever_and_chills": "a temperature", "syncope_and_dizziness": "fainting", "nausea_and_vomiting": "feeling sick",
  "abdominal_fullness": "my stomach", "urine_output": "passing water", "calf_pain_or_asymmetry": "my calves",
  "travel_immobility_surgery": "travelling", "hemoptysis": "blood in the phlegm", "medication_adherence": "taking my tablets",
  "dietary_sodium": "salt", "current_medications": "my tablets", "past_medical_history": "my medical history",
  "past_surgical_history": "operations", "allergies": "allergies", "social_history_smoking_alcohol": "smoking and drinking",
  "substance_use_stimulants": "drugs", "family_history": "the family", "last_oral_intake": "when I last ate",
  "sleep_apnea_and_snoring": "snoring", "recent_illness_or_sick_contacts": "whether I've been unwell",
  "functional_baseline": "what I could normally do",
 },
 "MGCA": {
  "onset": "when it started", "timing_progression": "whether it's getting worse", "character_of_symptoms": "what it feels like",
  "location_of_pain": "where it hurts", "radiation_of_pain": "whether it spreads", "severity": "how bad it is",
  "aggravating_relieving": "what makes it better or worse", "rash": "the spots", "fever_and_chills": "a temperature",
  "headache": "my head", "neck_stiffness": "my neck", "photophobia": "the lights", "nausea_vomiting": "being sick",
  "diarrhoea": "diarrhoea", "abdominal_pain": "my stomach", "chest_pain": "chest pain", "breathing": "my breathing",
  "cough_sore_throat": "a cough or sore throat", "urine_output": "passing urine", "dizziness_syncope": "feeling faint",
  "confusion": "whether I'm confused", "cold_extremities": "my hands and feet", "joint_pain": "my joints",
  "dysuria_gu_symptoms": "my waterworks", "menstrual_and_tampon": "my period", "pregnancy": "being pregnant",
  "sexual_history": "sex", "past_medical_history": "my medical history", "past_surgical_history": "operations",
  "current_medications": "my medication", "allergies": "allergies", "social_history": "smoking and drinking and that",
  "family_history": "the family", "last_oral_intake": "when I last ate", "vaccinations": "my vaccines",
  "sick_contacts": "whether anyone else is ill", "travel_history": "travelling",
  "tick_and_outdoor_exposure": "ticks and being outdoors", "recent_antibiotics_healthcare": "antibiotics or seeing a doctor",
  "functional_baseline": "what I'm normally like", "code_status_goals": "what I'd want if it got worse",
 },
}

FACTS = {
 "AFRVR": {
  "onset": [
    F("time", ["what time", "what time exactly", "when exactly", "roughly what time", "how long ago"],
      GASP, "'Three... yesterday.'", "'About three o'clock yesterday afternoon.'", restate=True),
    F("how", ["how did it start", "sudden or gradual", "what were you doing", "did it come on suddenly", "what brought it on"],
      GASP, "'Sudden. Watching... telly.'", "'All at once. I was sat watching the television and it just started, like something turned over in my chest.'"),
    F("breathing_after", ["when did the breathing start", "did the breathing come at the same time", "which came first", "and the breathing"],
      GASP, "'Breathing... later.'", "'The breathing came on after, later in the evening. The heart was first.'"),
  ],
  "character_of_palpitations": [
    F("rhythm", ["regular or irregular", "is it regular", "does it keep time", "steady or all over the place"],
      GASP, "'All over... the place.'", "'It doesn't keep any kind of time. It just goes and goes and then gives a big thump and carries on.'", restate=True),
    F("where_felt", ["where do you feel it", "can you feel it in your neck", "where in your chest", "do you feel it in your throat"],
      GASP, "'Throat.'", "'In my chest, and I can feel it in my throat too.'"),
  ],
  "dyspnea_character": [
    F("sensation", ["what does it feel like", "tight or heavy", "is it a tightness", "can you get a full breath"],
      GASP, "'Can't... get enough.'", "'I can't get a full breath. It's like there's a weight on me and I only get half of what I need each time.'", restate=True),
    F("effort", ["are you breathing fast", "why are you breathing so fast", "are you tired from it", "is it tiring"],
      GASP, "'Exhausted.'", "'I have to keep going faster to make up for it. I'm exhausted from it.'"),
  ],
  "chest_pain": [
    F("pain", ["any pain at all", "is it sore", "does it hurt", "any discomfort"],
      GASP, "'No... pain.'", "'No, no pain. It's not sore. I can feel it thumping and I can feel that I can't breathe, but there's no pain to it.'", restate=True),
    F("arm_jaw", ["anything in your arm", "does it go to your jaw", "any pain in your arm or jaw", "any radiation"],
      GASP, "'Nothing... arm.'", "'Nothing in my arm, nothing in my jaw.'"),
  ],
  "current_medications": [
    F("list", ["what are they", "which tablets", "name them", "what exactly do you take"],
      GASP, "'Blood pressure... statin... metformin.'", "'A blood pressure tablet, lisinopril I think, twenty milligrams. A statin at night, atorvastatin. And metformin twice a day.'", restate=True),
    F("doses", ["what dose", "how much of each", "what strength", "how many milligrams"],
      GASP, "'Twenty... the pressure one.'", "'The lisinopril is twenty milligrams. The metformin is twice a day. I couldn't tell you the statin dose.'"),
    F("anything_else", ["anything else at all", "any inhalers", "anything over the counter", "any other tablets"],
      GASP, "'That's... it.'", "'That's the lot. Nothing else, no inhalers, nothing from the chemist.'"),
  ],
  "past_medical_history": [
    F("conditions", ["what conditions", "which problems", "what have you got", "blood pressure or diabetes"],
      GASP, "'Blood pressure. Sugar.'", "'High blood pressure and diabetes, both for years.'", restate=True),
    F("heart_scan", ["what about your heart", "tell me about the scan", "the furring up", "what did the CT show", "any heart problems"],
      GASP, "'Scan... arteries. Statin.'", "'They found some furring up in my heart arteries on a CT scan three years ago. They said it wasn't bad enough to do anything about and just put me on a statin.'"),
  ],
  "alcohol_and_binge": [
    F("usual", ["how much normally", "what do you usually drink", "during the week", "how many a week"],
      GASP, "'Few beers. Weekend.'", "'Two or three beers at the weekend, that's all, and nothing during the week.'", restate=True),
    F("saturday", ["what about saturday", "the barbecue", "how many on saturday", "more than usual recently", "any binge"],
      GASP, "'Saturday... four or five.'", "'I had more than that on Saturday. We had a barbecue for my grandson's birthday and I'd say I had four or five over the afternoon.'"),
  ],
  "anticoagulant_history_and_bleeding": [
    F("thinners", ["any blood thinner", "warfarin or anything", "aspirin", "any antiplatelet"],
      GASP, "'No. Nothing... like that.'", "'No. I've never been on a blood thinner and I don't even take aspirin.'", restate=True),
    F("bleeding", ["any bleeding", "ever had a bleed", "any ulcers", "any falls"],
      GASP, "'No bleeds.'", "'I've never had a bleed, never had an ulcer, and I haven't had a fall.'"),
  ],
 },
 "CHFE": {
  "onset": [
    F("time", ["how many days", "when exactly", "how long has it been building", "since when"],
      PRES, "'Three, four days.'", "'It's been building for three or four days.'", restate=True),
    F("this_morning", ["what happened this morning", "when did it get bad", "what time this morning", "when did it get much worse"],
      PRES, "'Four this morning.'", "'About four this morning I woke up and couldn't get my breath at all, and it hasn't let up since.'"),
    F("early_symptoms", ["how did it start", "what was it like at first", "what did you notice first"],
      PRES, "'Puffed... walking.'", "'I was getting puffed just walking to the kitchen.'"),
  ],
  "character_of_dyspnea": [
    F("sensation", ["what does it feel like", "tight or heavy", "is it a heaviness", "can you get a breath in"],
      PRES, "'Weight on my chest... can't get it in.'", "'Like I can't get enough in. There's a heaviness on my chest, like something's sat on it.'", restate=True),
  ],
  "orthopnea": [
    F("pillows", ["how many pillows", "how many normally", "number of pillows", "how many do you use"],
      PRES, "'Four pillows.'", "'Normally two pillows. The last few nights I've needed four.'", restate=True),
    F("chair", ["did you sleep in a chair", "where did you sleep last night", "what about last night", "could you lie in bed"],
      PRES, "'Chair last night.'", "'Last night I gave up on the bed altogether and slept in the armchair.'"),
  ],
  "medication_adherence": [
    F("which", ["which one did you run out of", "which tablet", "what did you stop", "the water tablet"],
      PRES, "'The water tablet.'", "'I ran out of the water tablet. That's the one.'", restate=True),
    F("when", ["how long ago", "when did you run out", "how many days without it", "since when"],
      PRES, "'Five days ago.'", "'About five days ago now.'"),
    F("why", ["why did you run out", "why didn't you get more", "what happened", "could you not get to the chemist"],
      PRES, "'Car... off the road.'", "'I meant to get to the chemist but my car's been off the road and I couldn't get a lift down there.'"),
    F("others", ["what about the rest", "are you taking the others", "the other tablets", "everything else"],
      PRES, "'Taking the rest... mostly.'", "'I've been taking the rest of them, I think, though I've probably missed the odd one with all this going on.'"),
  ],
  "current_medications": [
    F("list", ["what are they", "which tablets", "name them", "what exactly"],
      PRES, "'Water tablet... heart tablets... diabetes ones.'", "'The water tablet, furosemide. Carvedilol. The sacubitril one. Spironolactone. Metformin and the newer diabetes one. A statin and a baby aspirin.'", restate=True),
    F("heart", ["which are the heart tablets", "what do you take for your heart", "the heart ones"],
      PRES, "'Carvedilol... the big new one... spironolactone.'", "'Carvedilol I think it is, the newer one, sacubitril something, a big tablet, and the little white one, spironolactone.'"),
    F("diabetes", ["what do you take for diabetes", "the diabetes tablets", "which are for the sugar"],
      PRES, "'Metformin... and a new one.'", "'Metformin, and another new one for the diabetes that they said was good for the heart as well.'"),
  ],
  "past_medical_history": [
    F("heart_attack", ["tell me about the heart attack", "when was the heart attack", "did you have a stent", "what happened to your heart"],
      PRES, "'Heart attack... six years back.'", "'I had a heart attack six years ago and they put a stent in. They told me afterwards the heart doesn't pump the way it should since then.'", restate=True),
    F("other", ["anything else", "what other problems", "blood pressure or diabetes", "kidneys"],
      PRES, "'Blood pressure. Diabetes. Kidneys.'", "'The high blood pressure, and the diabetes, tablets not the injections. And they've said my kidneys aren't brilliant.'"),
  ],
  "chest_pain": [
    F("pain", ["any pain at all", "is it sore", "any discomfort", "does it hurt"],
      PRES, "'No pain... just tight.'", "'No, no pain. It's tightness from working to breathe, not a pain.'", restate=True),
    F("compare", ["like your heart attack", "is it like last time", "how does it compare", "like before"],
      PRES, "'Nothing like... the heart attack.'", "'It's nothing like when I had my heart attack. That was a crushing thing, down my left arm, and I was sick with it. This is completely different.'"),
  ],
  "leg_swelling": [
    F("both", ["both legs", "one or both", "is one worse", "same on both sides"],
      PRES, "'Both legs.'", "'It's both legs the same.'", restate=True),
    F("how_bad", ["how bad is the swelling", "how swollen", "do your shoes fit", "socks"],
      PRES, "'Socks cutting in.'", "'My socks leave marks by the evening and my slippers won't go on properly any more.'"),
  ],
 },
 "MGCA": {
  "onset": [
    F("time", ["what time", "when exactly", "roughly when", "what time yesterday"],
      SICK, "'Yesterday evening.'", "'Yesterday evening, about six. I was fine at dinner.'", restate=True),
    F("how", ["how did it start", "what did you notice first", "what was it like at first"],
      SICK, "'Achy. Cold.'", "'By about six I felt achy and cold, like I was coming down with something.'"),
    F("overnight", ["what happened overnight", "and then", "how did the night go", "when did the shaking start", "when did your legs start"],
      SICK, "'Shaking by ten. Legs at three.'", "'By ten I was shaking so hard my roommate came in to check on me. Then about three this morning my legs started and I couldn't get back to sleep at all.'"),
  ],
  "rash": [
    F("where", ["where are the spots", "where is the rash", "which part", "where did it start"],
      SICK, "'Ankles. Feet.'", "'On my ankles and the tops of my feet.'", restate=True),
    F("when", ["when did you notice it", "when did the spots come", "how long has the rash been there", "who saw it"],
      SICK, "'This morning. Roommate.'", "'My roommate saw them this morning when she was helping me up, maybe two hours ago.'"),
    F("look", ["what do they look like", "what colour", "do they itch", "do they hurt", "do they blanch"],
      SICK, "'Dark red dots. Don't itch.'", "'Little dark red dots. They don't itch, they don't hurt, they're just there.'"),
    F("spreading", ["are they spreading", "are there more", "is it getting worse", "any new ones"],
      SICK, "'More now.'", "'I looked again in the ambulance and I think there are more of them now.'"),
  ],
  "location_of_pain": [
    F("legs", ["which part of your legs", "where in your legs", "thighs or calves", "one side or both"],
      SICK, "'Thighs and calves. Both.'", "'The fronts of my thighs and my calves, both sides the same.'", restate=True),
    F("elsewhere", ["anywhere else", "does your back hurt", "what about your head", "is it just your legs"],
      SICK, "'Back a bit. Head a bit.'", "'My lower back aches too, and my head hurts a bit, but the legs are much worse than anything else.'"),
  ],
  "headache": [
    F("character", ["what is the headache like", "where is the headache", "what kind of headache", "all over or one side"],
      SICK, "'All over. Like a hangover.'", "'All over, like a bad hangover.'", restate=True),
    F("worst", ["worst headache ever", "is it the worst you've had", "how bad is the headache", "is it severe"],
      SICK, "'Not the worst.'", "'It's not the worst headache I've ever had. It's honestly the least of my problems right now.'"),
  ],
  "current_medications": [
    F("regular", ["anything regular", "what do you normally take", "the pill", "any prescriptions"],
      SICK, "'The pill.'", "'Just the pill, and I forget it more often than I should.'", restate=True),
    F("painkillers", ["have you taken anything for it", "any painkillers", "any ibuprofen", "what did you take overnight", "how much ibuprofen"],
      SICK, "'Ibuprofen. Four.'", "'I took four ibuprofen overnight for my legs, two around midnight and two around four.'"),
  ],
  "past_medical_history": [
    F("conditions", ["any conditions", "ever been in hospital", "anything at all", "any illnesses"],
      SICK, "'Nothing. Never ill.'", "'Nothing. I'm never ill. I've never been in hospital.'", restate=True),
    F("immune", ["anything with your immune system", "any blood problems", "do you have your spleen", "any immune problems"],
      SICK, "'Nothing like that.'", "'Nobody's ever said anything about my immune system or my blood or anything like that.'"),
  ],
  "menstrual_and_tampon": [
    F("lmp", ["when was your last period", "when did it finish", "when did it start", "are you on your period now"],
      SICK, "'Finished last week.'", "'My period finished about a week ago. It started maybe two weeks back.'", restate=True),
    F("tampons", ["do you use tampons", "anything in", "pads or tampons", "is there a tampon in"],
      SICK, "'Pads. Nothing in.'", "'I use pads, I've never got on with tampons. So no, there's definitely nothing in.'"),
  ],
  "social_history": [
    F("living", ["who do you live with", "where do you live", "halls", "how many of you"],
      SICK, "'Halls. Three others.'", "'I live in one of the halls, a suite with three other girls. We share a kitchen and a bathroom.'", restate=True),
    F("alcohol", ["how much do you drink", "any alcohol", "do you drink"],
      SICK, "'Weekends.'", "'I drink at weekends, not much during the week.'"),
    F("smoke_drugs", ["do you smoke", "any drugs", "anything injected", "cigarettes or drugs"],
      SICK, "'No smoking. No drugs.'", "'I've never smoked and I've never done any drugs, and definitely nothing injected.'"),
  ],
 },
}

def load(p):
    with open(p) as f: return json.load(f)
def save(p, o):
    with open(p, "w") as f: json.dump(o, f, indent=1, ensure_ascii=False); f.write("\n")

def write_json_pack(prefix):
    p = os.path.join(ROOT, "cases", prefix, f"{prefix}-case.json")
    case = load(p)
    n = 0
    for t in case["interview"]["topics"]:
        t.pop("echo", None); t.pop("facts", None)
        if t["topic"] in ECHO[prefix]: t["echo"] = ECHO[prefix][t["topic"]]
        if t["topic"] in FACTS[prefix]: t["facts"] = FACTS[prefix][t["topic"]]; n += len(t["facts"])
    case["interview"]["facts_note"] = (
        "echo and facts were written by catalog/author_interview_facts.py (design 10.7). A fact's "
        "value restates part of the topic's answer for a follow-up question; it adds nothing the "
        "paragraph does not say. Not physician-reviewed.")
    save(p, case)
    print(f"{prefix}: {len(ECHO[prefix])} echoes, {len(FACTS[prefix])} topics with facts, {n} facts")

def write_afrvr():
    p = os.path.join(ROOT, "cases", "AFRVR", "case_4_interview.py")
    src = open(p).read()
    B, E = "# ---- ECHO AND FACTS (generated, do not edit by hand) ----", "# ---- END ECHO AND FACTS ----"
    lines = [B, "# Written by catalog/author_interview_facts.py (design 10.7). A fact's value restates part",
             "# of the topic's answer for a follow-up; it adds nothing the paragraph does not say.",
             "ECHO = " + json.dumps(ECHO["AFRVR"], indent=1, ensure_ascii=False),
             "FACTS = " + json.dumps(FACTS["AFRVR"], indent=1, ensure_ascii=False)
                .replace(": true", ": True").replace(": false", ": False").replace(": null", ": None"),
             "for _t in TOPICS:",
             "    if _t['topic'] in ECHO: _t['echo'] = ECHO[_t['topic']]",
             "    if _t['topic'] in FACTS: _t['facts'] = FACTS[_t['topic']]",
             E]
    block = "\n".join(lines) + "\n"
    if B in src:
        src = src[:src.index(B)] + block + src[src.index(E) + len(E) + 1:]
    else:
        src = src.rstrip("\n") + "\n\n" + block
    open(p, "w").write(src)
    n = sum(len(v) for v in FACTS["AFRVR"].values())
    print(f"AFRVR: {len(ECHO['AFRVR'])} echoes, {len(FACTS['AFRVR'])} topics with facts, {n} facts")

if __name__ == "__main__":
    args = sys.argv[1:] or ["AFRVR", "CHFE", "MGCA"]
    for prefix in args:
        if prefix == "AFRVR": write_afrvr()
        else: write_json_pack(prefix)
