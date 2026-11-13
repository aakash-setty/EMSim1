"""SWEET part 4: the interview.

THE HISTORIAN IS HIS MOTHER, as in DIPH. He is frightened, breathless and twelve, and the
owner's structure says the parent gives the history. Every answer is her voice, written in
the third person about her son so the voice is plain from the first reply. A question
addressed to him gets her answer. She never names a diagnosis and cannot report a number.

When he is at the edge of arrest, after the tube and once the run has ended, the global
rule takes the history away: she is at the foot of the bed and the team is resuscitating.

Every answer is model output. Facts the owner's structure did not supply are listed in
SWEET-SEED.md section 3.7: the aunt's dessert, the lost pen, the earlier hives, the
dizziness on standing at home, his school year and household, and every denial.
"""
from case_4_variants import SHARED

TOPICS = []
NEGATIVES = {"asthma", "current_medications", "heart_history", "past_surgical_history",
             "nausea_vomiting", "abdominal_pain", "fever_and_chills", "cough_sore_throat",
             "family_history"}
LATER = "phase is persistent OR phase is worsening"


def topic(tid, answer, canonical=None, variants=None, echo=None, extra=None, more=None, facts=None):
    s = SHARED.get(tid, {})
    rules = list(extra or []) + [{"when": None, "value": answer}]
    t = {"topic": tid, "canonical": canonical or s["canonical"],
         "variants": list(variants or s["variants"]) + list(more or []), "answer": rules,
         "echo": echo or s["echo"]}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


def fact(fid, asks, value):
    return {"id": fid, "asks": asks, "value": [{"when": None, "value": value}]}


M = "His mother: "

# --------------------------------------------------------------- the dose before arrival
topic("epi_given",
  M + "'The paramedics gave him a shot in his leg about fifteen minutes before we got here. He got better for a few minutes, then it came back worse.'",
  canonical="Has he had any medicine for this?",
  variants=["Did he get epinephrine?", "Did EMS give him anything?", "Has he had an EpiPen?",
            "Any treatment before he got here?", "Did he get epi?", "What did the paramedics give him?",
            "Did anyone give him a shot?", "Did you use his EpiPen?", "Any epinephrine yet?",
            "Has he had anything for it?", "What has he been given so far?", "Prehospital meds?",
            "Did the ambulance give him anything?", "How many doses of epi has he had?",
            "When was the epi given?", "Did it help?"],
  echo="what he's been given",
  facts=[fact("own_pen", ["his own pen", "his epipen", "why not his epipen", "does he have an epipen",
                          "where is his epipen", "did you have his pen"],
              M + "'I couldn't find it. It wasn't in his bag, so I called 911.'"),
         fact("did_it_help", ["did it help", "did he get better", "how long did it help"],
              M + "'For a few minutes. Then the wheezing came back.'")])

# --------------------------------------------------------------- the allergy
topic("allergies",
  M + "'He's allergic to peanuts. We've known since he was three. No medicine allergies.'",
  more=["Is he allergic to anything?", "Any food allergies?", "Does he have a peanut allergy?",
        "Any known allergies?", "Allergic to nuts?"],
  facts=[fact("prior_reaction", ["before", "has this happened before", "previous reactions", "worst reaction",
                                 "ever had a reaction"],
              M + "'Hives once when he was little. Never like this.'")])
topic("what_he_ate",
  M + "'A piece of a dessert bar my sister brought over. It must have had peanut in it.'",
  canonical="What did he eat?",
  variants=["What did he eat before this started?", "What was in the dessert?", "Did he eat peanuts?",
            "What food was it?", "Did he eat anything new?", "What was the last thing he ate?",
            "Was there peanut in it?", "What triggered this?", "Any new foods?", "Did he eat something?",
            "What dessert was it?", "Where was the food from?"],
  echo="what he ate")
topic("rash",
  M + "'He's been itching all over since the hives came out.'",
  canonical="Does he have a rash or itching?",
  variants=["Any rash?", "Any hives?", "Is he itchy?", "Any itching?", "Any rash on your skin?",
            "When did the hives start?", "Any skin changes?", "Is his skin itchy?", "Any swelling of the skin?",
            "Any welts?"],
  echo="his skin")
topic("swelling",
  M + "'His lips and his eyes puffed up fast. He says his lips feel big.'",
  canonical="Any swelling of his face or lips?",
  variants=["Is his face swollen?", "Any lip swelling?", "Is his tongue swollen?", "Any swelling in the mouth?",
            "Any trouble swallowing?", "Is his throat closing?", "Can he swallow?", "Any drooling?",
            "Does his throat feel tight?", "Any change in his voice?", "Is his voice hoarse?",
            "Are his eyes swollen?"],
  echo="the swelling")

# --------------------------------------------------------------- the illness
topic("onset",
  M + "'About twenty-five minutes ago now. A few minutes after he ate it.'")
topic("timing_progression",
  M + "'Better for a few minutes after the shot, then worse again on the way here.'",
  extra=[{"when": LATER, "value": M + "'He was talking to me before. Now he's so sleepy.'"}])
topic("breathing",
  M + "'He says his chest feels tight and he can't get enough air.'")
topic("character_of_symptoms",
  M + "'He says it's tight, like breathing through a straw.'")
topic("chest_pain", M + "'He says his chest feels tight when he breathes.'")
topic("asthma",
  M + "'No, he's never had asthma. He's never needed an inhaler.'",
  canonical="Does he have asthma?",
  variants=["Any history of asthma?", "Does he use an inhaler?", "Asthma?", "Has he wheezed before?",
            "Any lung problems?", "Does he have any breathing problems normally?", "Is he asthmatic?",
            "Has he ever been on albuterol?", "Any reactive airway disease?", "Any chest problems?"],
  echo="asthma")
topic("dizziness_syncope",
  M + "'He said he felt dizzy when he tried to stand up at home, so I made him sit down. He didn't pass out.'")
topic("weakness_tiredness",
  M + "'He's scared, not sleepy.'",
  canonical="Is he more sleepy than usual?",
  variants=["Is he drowsy?", "Is he acting normally?", "Is he more tired than usual?", "Is he confused?",
            "Is he himself?", "Is he sleepy?", "Is he weak?", "Is this his normal behavior?",
            "Has he been more drowsy?", "Is he less responsive?"],
  echo="how alert he is",
  extra=[{"when": LATER, "value": M + "'He's getting sleepy. That's not like him at all.'"}])
topic("nausea_vomiting", M + "'No, he hasn't been sick.'")
topic("abdominal_pain", M + "'He hasn't said his tummy hurts.'")
topic("fever_and_chills", M + "'No fever. He was fine this morning.'")
topic("cough_sore_throat", M + "'No cough, no cold.'")

# --------------------------------------------------------------- background
topic("past_medical_history", M + "'Just the peanut allergy. Nothing else.'",
      more=["Any medical problems?", "Is he healthy otherwise?", "Any chronic conditions?"])
topic("heart_history",
  M + "'No, his heart's fine.'",
  canonical="Any heart problems?",
  variants=["Does he have a heart condition?", "Any heart disease?", "Any congenital heart problems?",
            "Has he had heart surgery?", "Any murmurs?", "Any heart history?", "Is his heart normal?",
            "Any problems with his heart?", "Does he see a cardiologist?", "Any arrhythmia?"],
  echo="his heart")
topic("past_surgical_history", M + "'No surgeries.'")
topic("current_medications", M + "'Nothing. He doesn't take anything.'",
      more=["Is he on any beta-blockers?", "Any regular medicines?", "Does he take anything every day?"])
topic("immunizations",
  M + "'He's up to date with all his shots.'",
  canonical="Are his vaccinations up to date?",
  variants=["Is he immunized?", "Any vaccines missing?", "Are his shots up to date?", "Vaccinations?",
            "Is he fully vaccinated?", "Has he had all his immunizations?", "Up to date on vaccines?",
            "Any missed vaccines?", "Immunization history?", "Did he get his school shots?"],
  echo="his vaccinations")
topic("family_history", M + "'Nothing like this in the family.'")
topic("social_history",
  M + "'He's in sixth grade. He lives with me and his little sister.'",
  more=["Where does he go to school?", "Who does he live with?"])
topic("last_oral_intake", M + "'The dessert, about half an hour ago now.'")
topic("weight",
  M + "'Forty kilos. He was weighed at the doctor's last month.'",
  canonical="How much does he weigh?",
  variants=["What's his weight?", "Weight?", "How heavy is he?", "Do you know his weight?",
            "How many kilos is he?", "How much does he weigh in kilograms?", "What does he weigh?",
            "Has he been weighed recently?", "Weight in kg?", "Approximately how much does he weigh?"],
  echo="his weight")
topic("age",
  M + "'He's twelve.'",
  canonical="How old is he?",
  variants=["How old are you?", "What's his age?", "Age?", "When was he born?", "How old is your son?",
            "Is he twelve?", "What grade is he in?", "What year was he born?", "How old is the patient?",
            "Is he a teenager yet?"],
  echo="his age")
topic("companion",
  M + "'I'm his mom. I'm right here.'",
  canonical="Who is here with him?",
  variants=["Is anyone here with you?", "Are you his mother?", "Who are you?", "Is a parent here?",
            "Who came with him?", "Are you his parent?", "Is his mom here?", "Who is the adult with him?",
            "Are you family?", "Can I talk to his mom?"],
  echo="who is with him")
topic("arrival",
  M + "'The paramedics brought us. I rode with him.'",
  canonical="How did he get here?",
  variants=["Did you come in by ambulance?", "How did you get here today?", "Who brought him in?",
            "Did EMS bring him?", "Did you drive him here?", "Did he come by ambulance?",
            "How did you get to the hospital?", "Was he brought in by paramedics?", "Who called the ambulance?",
            "Did you call 911?"],
  echo="how he got here")

# --------------------------------------------------------------- presenting_story
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
 "answer": [{"when": LATER, "value": M + "'He ate some dessert and his mouth started itching, then hives and wheezing. The shot helped for a few minutes. Now he's so sleepy.'"},
            {"when": None,
             "value": M + "'He had a piece of a dessert my sister brought. A few minutes later he said his mouth itched, then he broke out in hives and started wheezing. I couldn't find his EpiPen, so I called 911.'"}],
 "echo": "what happened",
 "authoring_note": ("Authoring 8.2. Written by a model from the case structure. The peanut is "
                    "behind the allergy question. The crew's dose is in the handover and behind "
                    "its own question. Not physician reviewed.")})

# ------------------------------------------------------------------ global rules
GLOBAL_RULES = [
 {"when": ("flag intubated set OR phase is peri_arrest OR phase is post_induction_collapse OR "
           "phase is ventilated OR phase is bradycardic_arrest OR phase is case_complete"),
  "value": "His mother is at the foot of the bed, crying. 'Please, just help him.' There is no history to be had right now.",
  "note": ("Section 8.5. Covers the phases at alertness 2 and 3 (peri-arrest, after the tube, "
           "ventilated, the terminal phase) and every intubated state. The mother is present "
           "but the team is resuscitating.")},
]

OUT_OF_SCOPE = [
 {"when": None, "value": M + "'I don't know. Is he going to be okay?'"},
]

AUTHORING_NOTES = {
 "voice": "His mother answers for him throughout, frightened and clear. Third person about her son.",
 "the_dose": "The crew's dose is in the handover and behind epi_given. She volunteers nothing about it unprompted beyond the presenting story's lost pen.",
 "the_allergen": "Behind the allergy question and what_he_ate. The handover names no allergen.",
 "distress": ("No shorter distress forms: she is the speaker and is not short of breath. "
              "Authoring 8.5's distress rule is about the patient's own speech."),
 "diagnosis_disclosure": "She never names anaphylaxis or an allergic reaction.",
}

KEY_TOPICS = ["epi_given", "allergies", "asthma", "current_medications", "weight"]

VOLUNTEER_SETTINGS = {
 "must_ask": ["epi_given", "allergies", "asthma", "current_medications", "weight"],
 "volunteers_note": "Nothing is volunteered beyond the presenting story.",
}

TOPIC_MAP = {
 "onset": ["onset"], "timing_progression": ["timing_progression"],
 "character_of_symptoms": ["character_general"], "breathing": ["breathing_sob"],
 "chest_pain": ["chest_pain"], "allergies": ["allergies"], "what_he_ate": ["suspect_meal"],
 "rash": ["rash"], "nausea_vomiting": ["nausea_vomiting"], "abdominal_pain": ["abdominal_pain"],
 "fever_and_chills": ["fever_chills"], "cough_sore_throat": ["cough_sore_throat"],
 "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"],
 "weakness_tiredness": ["weakness"], "past_medical_history": ["pmh"], "past_surgical_history": ["psh"],
 "current_medications": ["meds"], "heart_history": ["prior_cardiac"], "immunizations": ["vaccinations"],
 "family_history": ["family_history"], "social_history": ["social_history"],
 "last_oral_intake": ["last_oral_intake"],
}

EXTRA_COVERED = []
