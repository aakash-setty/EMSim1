"""DIPH part 4: the interview.

THE HISTORIAN IS THE MOTHER. This is the one structural departure in this pack and it was
the case author's instruction, taken on 5 September 2026. The source case is explicit that
the patient is confused, agitated and combative and that the history comes from EMS and
from the mother, who is a confederate standing in the room. The engine's interview is
patient-facing and has no collateral-historian mechanism, so rather than change the engine
the mother answers in the patient's place. Every answer below is her voice.

Three consequences, and the second is the one a reviewer should push on.

1. Section 10.4 still holds and is easier to hold. The mother uses lay language because she
   is a lay person, and she cannot report a laboratory value or a vital sign because she has
   not been told any. She does not name a diagnosis anywhere.
2. The history does not disappear when the patient's alertness falls. In every other pack an
   obtunded or intubated patient ends the interview. Here the mother is still in the
   department, so the history stays available in the post-ictal and stabilising phases, which
   is a departure from how every other pack behaves. It is withdrawn only where the team
   would genuinely have moved her out: during the convulsion, during the wide-complex phases
   and after the case has ended. That is what GLOBAL_RULES does.
3. The patient herself is never quoted. A resident who types a question addressed to the
   patient gets the mother's answer, and nothing in the interface says so except the answers
   themselves, which are written in the third person about her daughter so that the voice is
   unmistakable from the first reply.
"""

SEIZ = "phase is seizing"
WIDE = "phase is wide_complex_tachycardia"

TOPICS = []


NEGATIVES = {
 "fever_or_infection", "neck_stiffness", "rash", "head_injury", "seizure_history",
 "diabetes", "vomiting", "abdominal_pain", "pain_anywhere", "urinary_symptoms",
 "chest_or_palpitations", "breathing", "travel_and_contacts", "previous_self_harm",
 "suicidal_intent", "past_surgical_history", "allergies", "current_medications",
 "past_medical_history",
}


def topic(tid, canonical, variants, answer, echo, facts=None):
    t = {"topic": tid, "canonical": canonical, "variants": variants,
         "answer": answer if isinstance(answer, list) else [{"when": None, "value": answer}],
         "echo": echo}
    if tid in NEGATIVES:
        t["pertinent_negative"] = True
    if facts:
        t["facts"] = facts
    TOPICS.append(t)
    return t


def fact(fid, asks, value, restate=False):
    f = {"id": fid, "asks": asks,
         "value": value if isinstance(value, list) else [{"when": None, "value": value}]}
    if restate:
        f["restate"] = True
    return f


# --------------------------------------------------------------- the event
topic("onset", "When did this start?",
  ["When did this start?", "How long has she been like this?", "When did you first notice?",
   "What time did this begin?", "How long has this been going on?",
   "When did she start acting strangely?", "When did it come on?", "How long ago?",
   "When did you realise something was wrong?"],
  ("'I got in from work at about four and she was already like this. So an hour and a bit? "
   "I don't know how long she'd been that way before I found her. I was at work all day.'"),
  "when I found her",
  facts=[
    fact("time", ["what time", "what time exactly", "when exactly", "roughly what time",
                  "how long ago"],
         "'About four o'clock. That's when I got in from work.'", restate=True),
    fact("before_that", ["how long before", "how long had she been like that",
                         "was she like that all day", "do you know when it started"],
         ("'That's what I keep thinking about. I left at half seven this morning and she was "
          "asleep. So it could have been any time in there.'")),
    fact("how_found", ["how did you find her", "what was she doing", "where was she",
                       "what did you see"],
         ("'She was on the floor in her bedroom, sat up against the bed. She looked at me and "
          "she didn't know me. That's when I called the ambulance.'"))])

topic("last_seen_well", "When was she last her normal self?",
  ["When was she last normal?", "When did you last see her well?",
   "When was she last herself?", "What was she like this morning?",
   "Was she fine earlier?", "When was she last okay?", "Was she normal yesterday?",
   "When did you last speak to her?"],
  ("'This morning. I looked in before I left for work, about half seven, and she was asleep in "
   "bed. She was fine last night. Quiet, but she's been quiet for months.'"),
  "when she was last herself")

topic("progression", "Has she been getting worse?",
  ["Is she getting worse?", "Has it been getting worse?", "Has she changed since you found her?",
   "Is she worse than she was?", "Has anything changed?", "Is she going downhill?",
   "Was she worse in the ambulance?", "Did she deteriorate?"],
  ("'Worse. When I found her she was talking, just not making sense. In the ambulance she "
   "started grabbing at things that weren't there and trying to get off the bed. She's hotter "
   "than she was too. I could feel it through her top.'"),
  "whether she's getting worse")

topic("what_she_was_doing", "What was she doing before this?",
  ["What was she doing before?", "What happened before she got like this?",
   "What was she up to today?", "Where had she been?", "Was she out anywhere?",
   "Who was she with?", "Was she alone?", "What did she do today?"],
  ("'She was off school today, she said she had a headache last night and wanted a day at home. "
   "So she was in on her own from half seven. Her brother got back about three, he was upstairs "
   "on his computer, he says he didn't hear anything.'"),
  "what she was doing today")

# --------------------------------------------------------------- the disclosure
topic("bottle_or_pills_found", "Was there anything near her? Any bottles or packets?",
  ["Were there any bottles?", "Did you find any pills?", "Was there anything next to her?",
   "Any empty packets?", "Did you see any medication near her?",
   "Was there anything on the floor?", "Any tablets around?", "Did you look around her room?",
   "Is anything missing from the house?", "Could she have taken something?",
   "Any pill bottles?", "Did you find anything in her room?"],
  ("She stops. 'I didn't look. I just saw her on the floor and I called the ambulance, I "
   "didn't look at anything else.' She takes out her phone. 'Let me ring her brother, he's still "
   "at home.'\n\nShe steps out and comes back a couple of minutes later, holding the phone.\n\n"
   "'He's found a bottle. It was on the floor by the bed, half under it. It's Benadryl, the big "
   "bottle, and it's empty. I bought it in about a month ago for my hay fever and I'd hardly "
   "touched it.'"),
  "whether there was anything near her",
  facts=[
    fact("what_bottle", ["what was it", "what bottle", "what kind", "what was in it",
                         "what medication"],
         "'Benadryl. The pink and white bottle. It's what I use for my hay fever.'", restate=True),
    fact("how_many", ["how many were in it", "how full was it", "how many tablets",
                      "what size bottle", "how much was left"],
         ("'It was the big one. I bought it about a month ago and I've maybe taken four or five "
          "out of it. He says it's completely empty.'")),
    fact("where_found", ["where was it", "where did he find it", "whereabouts"],
         "'On the floor by her bed, pushed half under it.'")])

topic("what_she_took", "Do you know what she took?",
  ["What did she take?", "Do you know what she's taken?",
   "Any idea what she swallowed?", "Did she take an overdose?",
   "Do you think she's overdosed?", "Any overdose?", "How much did she swallow?",
   "Did she swallow the whole bottle?", "What was the ingestion?",
   "Do you know the quantity?", "How many did she take?",
   "Was it a deliberate overdose?"],
  ("'I didn't think that at all until you asked. She's never done anything like this.' Pause. "
   "'If it was the Benadryl, then whatever was in that bottle. I don't know when. She'd been on "
   "her own since half seven this morning.'"),
  "what she might have taken")

topic("medicines_in_the_house", "What medicines do you keep in the house?",
  ["What medications are in the house?", "What do you have at home?",
   "Is there anything in the medicine cabinet?", "What is in the house she could reach?",
   "Do you keep any prescription medicines at home?", "What's in the bathroom cabinet?",
   "Anything else she could have got hold of?", "Do you take anything yourself?",
   "Any co-ingestants?", "Co-ingestants?", "What else was available to her?",
   "Is there anything else in the house she could have taken?",
   "Any other medicines at home?", "What has she got access to at home?"],
  ("'Not much. Paracetamol and ibuprofen in the kitchen drawer, and the Benadryl. I take "
   "something for my blood pressure, ramipril, and that's in my bedroom and the packet's still "
   "full, I checked it in the ambulance. There's nothing strong in the house. Nobody's got "
   "anything for pain or anything like that.'"),
  "what's in the house")

# --------------------------------------------------------------- background
topic("past_medical_history", "Does she have any medical problems?",
  ["Any medical problems?", "Is she normally healthy?", "Does she see a doctor for anything?",
   "Any past medical history?", "Has she been unwell before?", "Any conditions?",
   "Is she under anyone at the hospital?", "PMH?", "Any health problems?"],
  ("'Nothing. She's never been in hospital in her life. She had her tonsils looked at when she "
   "was about nine and they left them alone. That's it.'"),
  "her health")

topic("past_surgical_history", "Has she had any operations?",
  ["Any operations?", "Has she had surgery?", "Any previous surgery?", "Been under anaesthetic?",
   "Any procedures?", "PSH?"],
  "'No. Never.'", "operations")

topic("current_medications", "Is she on any medication?",
  ["Is she taking anything regularly?", "Any regular medications?",
   "What does she take normally?", "Is she on anything?", "Any regular tablets?",
   "Does she take anything daily?", "Any prescriptions of her own?", "Is she on the pill?",
   "Any inhalers?", "Medications?", "Meds?", "Drug history?", "Any drug history?",
   "What is she prescribed?", "Is she on any regular treatment?"],
  ("'Nothing at all. She's not even on the pill. She won't take a paracetamol for a headache "
   "usually, she doesn't like taking things.'"),
  "what she takes")

topic("allergies", "Does she have any allergies?",
  ["Any allergies?", "Is she allergic to anything?", "Any drug allergies?", "NKDA?",
   "Any reactions to medicines?", "Allergies?"],
  "'No, none. Not that we've ever found.'", "allergies")

topic("family_history", "Is there anything that runs in the family?",
  ["Any family history?", "Does anything run in the family?", "Any illness in the family?",
   "Family history?", "Anyone in the family with heart problems?",
   "Anyone else in the family unwell?", "Any epilepsy in the family?"],
  ("'High blood pressure on my side, me and my mum. Her dad's not in the picture and I don't "
   "know about his lot. Nobody's got fits, if that's what you're asking, and nobody's got "
   "anything with their heart.'"),
  "the family")

topic("who_lives_at_home", "Who does she live with?",
  ["Who lives at home?", "Who's at home?", "Who does she live with?", "Does she live with you?",
   "Anyone else in the house?", "Who's in the family?"],
  "'Me and her brother. He's fifteen. Her dad's not around.'", "who's at home")

# --------------------------------------------------------------- mental health
topic("mental_health_history", "How has her mood been?",
  ["Has she been depressed?", "How's her mood been?", "Any mental health problems?",
   "Has she been low?", "Is she seeing anyone for her mental health?",
   "Any psychiatric history?", "Has she been anxious?", "Has she been unhappy?",
   "Anything going on with her emotionally?", "Any depression?"],
  ("'Yes.' She takes a moment. 'For months now. Since about February. She's been in her room all "
   "the time, she stopped going out, she stopped eating with us. I asked her about it more than "
   "once and she kept saying she was fine and I let it go, because she'd get angry if I "
   "pushed.'\n\n'She's never seen anybody about it. I never took her. I kept thinking it was her "
   "age.'"),
  "how she's been in herself",
  facts=[
    fact("how_long", ["how long", "since when", "when did it start", "how many months"],
         "'Since about February. So six months, seven.'", restate=True),
    fact("professional_help", ["has she seen anyone", "is she under a psychiatrist",
                               "has she had counselling", "has she seen the GP",
                               "is she on antidepressants"],
         "'No. Nobody. She's never been to the doctor about it and she's not on anything.'"),
    fact("what_changed", ["what did you notice", "how was she different", "what changed",
                          "in what way"],
         ("'She stopped coming downstairs. She stopped eating with us. She used to have people "
          "round every weekend and that just stopped.'"))])

topic("previous_self_harm", "Has she ever hurt herself before?",
  ["Has she done this before?", "Any previous overdose?", "Has she ever self-harmed?",
   "Any history of self-harm?", "Has she tried this before?", "Any previous attempts?",
   "Has she ever cut herself?", "Any history of hurting herself?"],
  ("'Never. Not once, not that I know of.' She looks at her daughter. 'I would have seen "
   "something, wouldn't I? I don't know any more.'"),
  "whether she's done this before")

topic("suicidal_intent", "Had she said anything about wanting to hurt herself?",
  ["Did she say anything about hurting herself?", "Had she talked about suicide?",
   "Did she leave a note?", "Was there a note?", "Had she said anything worrying?",
   "Any warning?", "Did she say she wanted to die?", "Was she suicidal?"],
  ("'No. Nothing.' She shakes her head. 'Nobody said anything about a note. He didn't say "
   "anything about a note when he found the bottle, but he wasn't looking for one.'"),
  "whether she'd said anything")

topic("bullying_and_school", "Has anything been happening at school?",
  ["Anything going on at school?", "Any trouble at school?", "Is she being bullied?",
   "Any problems with friends?", "Anything happening online?", "Has she fallen out with anyone?",
   "How's school been?", "Any social media problems?", "Has anyone been picking on her?"],
  ("'There was something online. In the spring. Some girls in her year set up an account and "
   "were putting things on it about her, and it went round the whole school. I only found out "
   "because another mum told me. The school said they dealt with it.'\n\n'She stopped talking to "
   "the two friends she had left after that. I don't know if they were part of it or if she just "
   "cut everyone off.'"),
  "what's been going on at school")

topic("relationship", "Has anything changed at home or in her relationships?",
  ["Has she had a break-up?", "Does she have a boyfriend?", "Any relationship problems?",
   "Has anything happened recently?", "Any recent stress?", "Has she split up with anyone?",
   "Anything happen in the last few weeks?", "Any big changes?"],
  ("'She was seeing a boy for about a year and they broke up three or four weeks ago. She "
   "wouldn't talk about it. She cried for two days and then she just went quiet on it.'"),
  "the break-up")

topic("sleep_and_appetite", "How have her sleep and appetite been?",
  ["Has she been sleeping?", "How's her appetite?", "Has she been eating?",
   "Has she lost weight?", "Is she sleeping alright?", "Any change in her eating?",
   "Has she been up at night?"],
  ("'She's been up half the night and asleep half the day for weeks. And she's not been eating "
   "with us. I don't know what she's been having, she takes things up to her room.'"),
  "her sleeping and eating")

# --------------------------------------------------------------- substances
topic("alcohol_and_drugs", "Does she drink or use anything?",
  ["Does she drink?", "Any drugs?", "Does she use recreational drugs?",
   "Any alcohol?", "Has she been drinking?", "Does she smoke anything?",
   "Any substance use?", "Does she take anything recreationally?", "Any drug use?",
   "Could she have taken something at a party?"],
  ("'She has a drink at a party like they all do. Not at home and not on her own. Drugs, no. "
   "I've never seen anything and I've never smelt anything on her.' She pauses. 'I'd have said "
   "the same thing about the Benadryl an hour ago.'"),
  "drink and drugs")

topic("smoking", "Does she smoke?",
  ["Does she smoke?", "Any smoking?", "Does she vape?", "Is she a smoker?", "Smoking history?"],
  "'She vapes. She thinks I don't know.'", "smoking")

# --------------------------------------------------------------- pertinent negatives
topic("fever_or_infection", "Has she been unwell or feverish recently?",
  ["Has she had a fever?", "Has she been unwell?", "Any infection?", "Any cough or cold?",
   "Has she had a temperature before today?", "Any sore throat?", "Has she been ill?",
   "Any infectious symptoms?", "Any diarrhoea or vomiting recently?"],
  ("'No. Nothing. She's not had so much as a cold. She said she had a headache last night and "
   "that's the only thing, and I think that was an excuse not to go in today.'"),
  "whether she's been ill")

topic("headache", "Has she complained of a headache?",
  ["Any headache?", "Has she had a headache?", "Did she complain of head pain?",
   "Any head pain?", "Was she complaining of anything before?"],
  ("'She said she had one last night and wanted the day off. Nothing today, she's not said "
   "anything I could understand today.'"),
  "a headache")

topic("neck_stiffness", "Any stiff neck or dislike of the light?",
  ["Any neck stiffness?", "Stiff neck?", "Any photophobia?", "Does light bother her?",
   "Any meningitis symptoms?", "Any neck pain?"],
  "'No. Nothing like that at all.'", "her neck")

topic("rash", "Has she had any rash?",
  ["Any rash?", "Any spots?", "Any skin changes?", "Have you seen a rash?",
   "Any marks on her skin?", "Any purple spots?"],
  ("'No. She's gone very red in the face and the chest, but that's since she's been hot. No "
   "spots.'"),
  "a rash")

topic("head_injury", "Could she have hit her head or fallen?",
  ["Any head injury?", "Did she fall?", "Could she have hit her head?", "Any trauma?",
   "Was there any injury?", "Did she bang her head?", "Any sign of a fall?"],
  ("'She was sat on the floor when I found her, up against the bed. She could have gone down, I "
   "suppose, but there's nothing on her and nothing was knocked over.'"),
  "whether she fell")

topic("seizure_history", "Has she ever had a fit before?",
  ["Any history of seizures?", "Has she had fits before?", "Any epilepsy?",
   "Is she epileptic?", "Has she ever convulsed?", "Any seizure history?"],
  "'Never. Nothing like that, ever.'", "fits")

topic("diabetes", "Is she diabetic?",
  ["Any diabetes?", "Is she diabetic?", "Does she have blood sugar problems?",
   "Any diabetes in her?", "Is she on insulin?"],
  "'No.'", "diabetes")

topic("vomiting", "Has she been sick?",
  ["Has she vomited?", "Any vomiting?", "Has she been sick?", "Any nausea?",
   "Did she throw up?", "Any diarrhoea?"],
  "'Not that I've seen. Nothing in the room and nothing in the ambulance.'", "being sick")

topic("abdominal_pain", "Has she complained of tummy pain?",
  ["Any abdominal pain?", "Any tummy pain?", "Any stomach pain?", "Has her belly hurt?",
   "Any pain in her abdomen?"],
  "'No. She hasn't complained of anything that I could make out.'", "tummy pain")

topic("pain_anywhere", "Is she in pain anywhere?",
  ["Is she in pain?", "Any pain?", "Does anything hurt?", "Where does it hurt?",
   "Is she hurting anywhere?", "How bad is the pain?", "Does the pain go anywhere?",
   "What does the pain feel like?"],
  ("'I don't know. She's not said. She's not been able to tell me anything since I found her.' "
   "She has not complained of pain and does not appear to be guarding anywhere."),
  "whether she's in pain")

topic("urinary_symptoms", "Has she passed urine?",
  ["Has she passed urine?", "Any urinary symptoms?", "Has she been to the toilet?",
   "When did she last wee?", "Any problems passing urine?", "Any burning when she wees?"],
  ("'Not since I found her, and she hasn't asked to go. I don't know about before that.'"),
  "passing urine")

topic("chest_or_palpitations", "Has she complained of her chest or her heart racing?",
  ["Any chest pain?", "Any palpitations?", "Has her heart been racing?",
   "Any heart symptoms?", "Has she complained of her chest?", "Any chest symptoms?"],
  "'No. Nothing about her chest, ever.'", "her chest")

topic("breathing", "Has she had any trouble breathing?",
  ["Any breathing problems?", "Is she short of breath?", "Any asthma?",
   "Any wheeze?", "Has she had trouble breathing?", "Any respiratory problems?"],
  "'No. She's breathing fast now but she's never had anything wrong with her chest.'",
  "her breathing")

topic("vision_or_hallucinations", "Has she been seeing things?",
  ["Is she hallucinating?", "Has she been seeing things?", "Any hallucinations?",
   "Is she seeing things that aren't there?", "Any visual problems?",
   "Has she been talking to people who aren't there?"],
  ("'In the ambulance she kept reaching out at the air next to her and saying there was somebody "
   "there. And she was picking at the blanket the whole way in.'"),
  "seeing things")

topic("last_oral_intake", "When did she last eat or drink?",
  ["When did she last eat?", "Last oral intake?", "When did she last drink anything?",
   "Has she eaten today?", "When did she last have anything?", "NPO status?"],
  ("'I don't know. There was a glass in her room and nothing else. She wasn't down for breakfast "
   "before I left and there's nothing gone from the kitchen.'"),
  "when she last ate")

topic("pregnancy", "Is there any chance she's pregnant?",
  ["Could she be pregnant?", "Any chance of pregnancy?", "When was her last period?",
   "Is she pregnant?", "LMP?", "Any pregnancy?", "Is she sexually active?"],
  ("'She had a boyfriend until a month ago, so I suppose there's a chance. Her periods have been "
   "all over the place but so has everything else about her. I don't know when the last one "
   "was.'"),
  "whether she could be pregnant")

topic("travel_and_contacts", "Has she travelled or been around anyone unwell?",
  ["Any recent travel?", "Has she been abroad?", "Any sick contacts?",
   "Has she been around anyone ill?", "Any travel history?", "Anyone else at home unwell?"],
  "'No travel, nowhere. Nobody's ill at home and nobody's ill at school that I've heard about.'",
  "travel and contacts")

topic("immunisations", "Are her vaccinations up to date?",
  ["Is she vaccinated?", "Any immunisations?", "Are her jabs up to date?",
   "Has she had her meningitis vaccine?", "Vaccination history?"],
  "'Yes, everything. She had the meningitis one at school when she was fourteen.'",
  "her jabs")

topic("what_ems_said", "What did the ambulance crew tell you?",
  ["What did EMS say?", "What did the paramedics say?", "What happened in the ambulance?",
   "What did the crew do?", "Did they give her anything?", "What did they find?"],
  ("'They said her heart was going fast and she was very warm. They didn't give her anything. "
   "They tried to put a line in her arm and she wouldn't have it, she kept pulling away.'"),
  "what the crew said")

topic("collateral_from_brother", "Has anyone spoken to her brother?",
  ["What does her brother say?", "Was anyone else home?", "Did her brother hear anything?",
   "Who else was in the house?", "Has anyone spoken to anyone at home?"],
  ("'He got in about three and went straight upstairs. He says he didn't hear anything and he "
   "didn't look in on her. He's the one who found the bottle when I rang him.'"),
  "her brother")

# ------------------------------------------------------------------ global rules
GLOBAL_RULES = [
 {"when": SEIZ + " OR " + WIDE + " OR phase is pulseless_vt OR phase is halted",
  "value": ("Her mother has been taken out to the relatives' room. There is no history to be had "
            "at the bedside right now."),
  "note": ("Prepended to every topic's rule list. Corresponds to alertness level 3 in the seizing "
           "phase, 2 in the wide-complex phase, and 3 in the two terminal phases.\n\n"
           "It reads differently from the equivalent rule in every other pack, and it has to. "
           "Elsewhere the rule says the patient cannot speak. Here the patient has not been "
           "speaking usefully since before she arrived, and what changes in these phases is that "
           "the person who can speak has been moved out of the room while the team resuscitates. "
           "That is why the history returns in the post-ictal and stabilising phases rather than "
           "being gone for the rest of the case: the mother comes back.\n\n"
           "The validator requires that every phase at alertness 2 or above is covered by a "
           "global rule. It is covered here, and the coverage is doing something slightly "
           "different from what the rule was designed for. Do not remove the check.")},
]

OUT_OF_SCOPE = [
 {"when": SEIZ + " OR " + WIDE + " OR phase is pulseless_vt OR phase is halted",
  "value": ("There is nobody at the bedside to ask. Her mother is in the relatives' room.")},
 {"when": "phase is stabilizing OR phase is stabilized",
  "value": ("Her mother shakes her head. 'I don't know. I'm sorry. I keep going over this "
            "morning and there isn't anything else.'")},
 {"when": None,
  "value": ("Her mother shakes her head. 'I'm sorry, I don't know. I've only just got here "
            "myself.' She looks at you and then at her daughter. 'Is she going to be "
            "alright?'")},
]

AUTHORING_NOTES = {
 "who_is_answering": (
   "The mother, throughout, on the case author's instruction. See the module docstring. Every "
   "answer is written in the third person about her daughter, so that a resident who typed a "
   "question meant for the patient can tell from the first reply who they are talking to."),
 "alertness_gating": (
   "Section 10.5. The condition language has no alertness predicate, so alertness is reached "
   "through the phases that carry it. Three phases sit at alertness 2 or above and all three are "
   "named in the global rule, along with the halted phase. If a phase is added later at "
   "alertness 2 or 3 the validator will catch it."),
 "speech_gating": (
   "Section 10.5's second gate, speech limited by distress, does not apply here and this is the "
   "one place where the mother-as-historian makes authoring easier rather than harder. The "
   "person answering is not the person who is short of breath, so no topic needs a second "
   "clipped answer for a distressed phase, and the doubling of interview effort that section "
   "10.5 warns about does not happen. What replaces it is a different cost: the history is "
   "available in phases where every other pack would have withdrawn it."),
 "diagnosis_disclosure": (
   "Section 10.4. The mother never names a diagnosis, never uses a clinical word, and never "
   "reports a number she could not have been told. She names Benadryl, which is a brand on a "
   "bottle her son is holding rather than a diagnosis, and she names it only in answer to a "
   "question about what was found. She does not connect it to how her daughter is behaving, and "
   "she says so: 'I didn't think that at all until you asked.'"),
 "the_disclosure": (
   "The pivot of the case in the author's original: the team must ask whether there was anything "
   "near the bed, at which point the mother telephones home and the empty bottle is found. It is "
   "authored as an ordinary interview topic, bottle_or_pills_found, whose answer contains the "
   "call and its result, because interview topics cannot set flags and nothing else in the case "
   "needs to know whether it was asked.\n\n"
   "The author's five-minute rule, that the mother volunteers it if nobody has asked, is carried "
   "by the nurse instead: the escalation on the toxicology prompt delivers it in the post-ictal "
   "phase. A resident who never asks and never reaches the post-ictal phase never learns what "
   "she took, which is a truthful outcome and is what the debrief says about it.\n\n"
   "Nothing in the case's management depends on the disclosure. Sodium bicarbonate is indicated "
   "by the ECG and not by the history, and that is the point being made."),
 "required_coverage": (
   "Section 10.2. Onset, timing and progression, past medical and surgical history, current "
   "medications, allergies, social history including substance use, family history, last oral "
   "intake and pregnancy status are all present. Location, radiation, character and severity are "
   "collapsed into one topic, pain_anywhere, because the presenting problem is confusion rather "
   "than a pain and four separate topics about the character of a pain nobody has would produce "
   "four near-identical denials for the matcher to confuse with one another. Aggravating and "
   "relieving factors are folded into progression for the same reason. Code status and goals of "
   "care are not authored: she is eighteen, previously well, and the presentation does not make "
   "them live."),
 "pertinent_negatives": (
   "Section 10.3. Fifteen topics exist to be denied: fever and infection, headache, neck "
   "stiffness, rash, head injury, seizure history, diabetes, vomiting, abdominal pain, pain "
   "anywhere, urinary symptoms, chest symptoms, breathing, travel and contacts, and previous "
   "self-harm. Each has an explicit denial rather than falling through to the out-of-scope "
   "response, because a learner cannot tell a denial from a matcher failure and the two are "
   "clinically opposite. The meningitis negatives carry the most weight here, since meningitis "
   "is the differential the fever and the confusion will send most residents toward first."),
 "variants_provenance": (
   "The variants in this file are hand-written. Expanded variants are added by "
   "catalog/expand_interview_variants.py from catalog/interview_phrasings.py and are marked as "
   "such on each topic. The expansion library was written by an AI assistant and a phrasing that "
   "maps a question to the wrong concept produces a confident wrong answer, so it is on the "
   "review list."),
}

KEY_TOPICS = ["bottle_or_pills_found", "what_she_took", "medicines_in_the_house",
              "onset", "last_seen_well", "past_medical_history", "current_medications",
              "mental_health_history", "alcohol_and_drugs", "seizure_history",
              "previous_self_harm", "pregnancy"]


# ---- further hand-written variants ----
# Section 10.1 asks for ten to twenty paraphrases per topic and the validator warns below
# ten. These are hand-written like the ones in the topic() calls above, kept separate only
# because they were added in a second pass. They are not generated and they are not the
# expansion library: the generated phrasings live in the EXPANDED block below and are
# marked as such on each topic.
MORE = {'onset': ['Do you know when this started?', 'How long has she been confused?', 'When did she become like this?', 'What time did you find her?', 'How many hours has she been this way?', 'Time of onset?', 'Time of ingestion?', 'When did she take it?', 'How long since the ingestion?', 'When did you get home?', 'What time did you get in?', 'When was she found?'], 'last_seen_well': ['When was she last completely normal?', 'Was she alright yesterday?', 'When did you last see her acting normally?', 'Was she well before today?', 'Last time she seemed fine?', 'Had she been herself recently?', 'Was she normal this morning?', 'Last known well?', 'When was she last known well?'], 'progression': ['Is she deteriorating?', 'Has she got worse since you found her?', 'Any change on the way in?', 'Was she more awake earlier?', "Is this the worst she's been?", 'Has the confusion got worse?', 'Any improvement at all?'], 'what_she_was_doing': ['Was she at school today?', 'Had she been out with anyone?', 'Was anyone with her at home?', 'What was her day like?', 'Did she go anywhere today?', 'Was she on her own all day?', "Any idea what she'd been doing?"], 'bottle_or_pills_found': ['Was there a bottle by the bed?', 'Any containers near her?', 'Have you checked her room?', "Could you look and see if anything's missing?", 'Was anything found with her?', 'Anything at the scene?', 'Any containers at the scene?', 'Did anyone look for a bottle?'], 'what_she_took': ['Could she have swallowed something?', "Is there any chance she's taken pills?", 'Do you think this is an overdose?', "Any chance she's taken tablets?", 'Has she taken anything at all?', "What do you think she's had?", 'Any ingestion?'], 'medicines_in_the_house': ['What tablets are at home?', 'Any painkillers in the house?', 'Does anyone at home take medication?', "What's in your medicine cupboard?", 'Are there any pills she could reach?', 'Any over-the-counter medicines at home?', 'Anything of yours she could have got?'], 'past_medical_history': ['Has she got any health conditions?', 'Anything wrong with her normally?', 'Any chronic illness?', 'Has she been in hospital before?', 'Does she have a GP she sees regularly?', 'Any diagnoses?', 'Past med hx?', 'Med hx?', 'Any background history?', 'Has she ever been treated for anything?', 'Is she known to any specialty?'], 'past_surgical_history': ['Has she ever had an operation?', 'Any previous procedures?', 'Has she been to theatre before?', 'Any surgical history at all?', 'Has she ever had a general anaesthetic?', 'Any operations as a child?', 'Anything ever removed?', 'Any past surgery?', 'Has she had anything done?', 'Surgical hx?', 'Any surgical hx?', 'Op history?'], 'allergies': ['Does she react to any medicines?', 'Any known allergies?', "Is there anything she can't have?", 'Any food or drug allergies?', 'Has she ever had a reaction to anything?', "Anything we shouldn't give her?", 'Any allergy to penicillin?', 'Does she carry an EpiPen?', 'Any intolerances?', 'Allergy status?', 'Allergy hx?', 'Any known allergies at all?'], 'family_history': ['Anything medical in the family?', 'Any heart conditions in the family?', 'Does anyone in the family have seizures?', 'Any sudden deaths in the family?', 'Any mental health problems in the family?', "What about her father's side?", 'Anyone else in the family had anything like this?', 'Any inherited conditions?', 'Family hx?', 'Any FHx?'], 'who_lives_at_home': ['How many people live at home?', 'Is there anyone else in the house?', 'Does she have brothers or sisters?', "Who's her next of kin?", 'Is her father involved?', 'Who else could we speak to?', 'Who was in the house today?', 'Is there anyone else at home?', 'Any siblings?', 'Living situation?', 'Social situation?'], 'previous_self_harm': ['Any history of overdose?', 'Has she taken tablets before?', 'Any previous episodes like this?', 'Has she ever been to hospital for self-harm?', 'Has she done anything to hurt herself in the past?', 'Any past deliberate self-harm?', 'Is this the first time?', 'Any prior self-harm?', 'Any previous OD?', 'Prior DSH?', 'Any history of deliberate self-harm?', 'Has she overdosed before?'], 'suicidal_intent': ['Was there any note?', 'Had she threatened anything?', 'Did she say goodbye to anyone?', 'Any indication she was planning this?', 'Had she talked about not wanting to be here?', 'Did anything she said worry you?', 'Any suicidal ideation that you knew about?', 'Any suicidal intent?', 'Any stated intent?', 'Was there a note left?'], 'bullying_and_school': ['Has anything happened at school?', 'Is she being picked on?', 'Any issues with other students?', 'How is she getting on at school?', 'Has she been going to school?', 'Any bullying you know about?', 'Has anyone been giving her trouble online?', 'Anything on social media?', 'Has she been having a hard time with anyone?', 'Any bullying?', 'Any problems with people at school?', 'Anything happening online?'], 'relationship': ['Is she in a relationship?', 'Any boyfriend or girlfriend?', 'Has anything happened with a partner?', 'Any recent loss?', 'Has anyone close to her died?', 'Any bereavement?', 'Any recent upset at home?'], 'mental_health_history': ['Any history of depression?', 'Has she seen a psychiatrist?', 'Is she under mental health services?', 'Has she been diagnosed with anything psychiatric?', 'Any anxiety or depression?', 'Has she ever been on antidepressants?', 'Psych hx?', 'Any psychiatric history?', 'Mental health hx?', 'Tell me about her mood.', 'How has her mood been over the last few months?', 'Has her mood changed?', 'Any low mood?'], 'sleep_and_appetite': ['Is she sleeping normally?', 'Any weight loss?', 'Has her eating changed?', 'Has she been withdrawn?', 'Is she still doing the things she enjoys?', 'Any change in her energy?', 'Has she been staying in bed?', 'Any change in her routine?', 'Any biological symptoms?', 'How is her sleep and appetite?'], 'alcohol_and_drugs': ['Does she use any substances?', 'Any recreational drug use?', 'Could she have taken something at a party?', 'Does she drink much?', 'Any cannabis?', 'Any history of substance misuse?', 'Substance hx?', 'Any illicit drug use?', 'Recreational drugs?'], 'smoking': ['Does she use tobacco?', 'Any vaping?', 'Is she a smoker?', 'Does she smoke cigarettes?', 'How much does she smoke?', 'Has she ever smoked?', 'Any nicotine use?', 'Does she smoke or vape?', 'Social history for smoking?', 'Any tobacco history?', 'Smoking hx?', 'Any tobacco?'], 'fever_or_infection': ['Has she had a temperature recently?', 'Any recent illness?', 'Has she been off colour?', 'Any sign of infection?', 'Has she had flu-like symptoms?', 'Any recent virus?', 'Any preceding illness?', 'Any prodrome?'], 'headache': ['Has she complained of head pain?', 'Any headaches recently?', 'Was she getting headaches before today?', 'Did she mention her head hurting?', 'Any migraines?', 'Has she had a bad headache?', 'Any headache before this?', 'Worst headache of her life?', 'Was the headache sudden?', 'Any neck or head pain?'], 'neck_stiffness': ['Can she move her neck?', 'Any pain when you move her neck?', 'Has she complained of a stiff neck?', 'Does bright light bother her?', 'Any meningism?', 'Has she been avoiding the light?', 'Any neck symptoms?', 'Any stiffness anywhere?', 'Any signs of meningitis?'], 'rash': ['Has she got a rash anywhere?', 'Any purple or red marks?', 'Any non-blanching spots?', 'Have you noticed anything on her skin?', 'Any petechiae?', 'Any skin rash?', "Any bruising you've noticed?", 'Anything on her arms or legs?', 'Any skin changes at all?'], 'head_injury': ['Any chance she fell?', "Was there any sign she'd collapsed?", 'Any bruises or bumps on her head?', 'Could she have hit anything?', 'Was anything knocked over in her room?', 'Any recent injury?', 'Any trauma at all?', 'Did she hit her head when she went down?', 'Any head strike?', 'Any evidence of trauma?'], 'seizure_history': ['Has she ever had a convulsion?', 'Any history of fits?', 'Is she known to have epilepsy?', 'Has she ever fitted before?', 'Any funny turns in the past?', 'Any blackouts before?', 'Has she had anything like this before?', 'Any previous seizures?', 'Any epilepsy history?', 'Any epilepsy hx?', 'Seizure hx?', 'Any prior fits?'], 'diabetes': ['Any sugar problems?', 'Does she have type 1 diabetes?', 'Is she on insulin?', 'Any history of low blood sugar?', 'Has she ever had hypos?', 'Any endocrine problems?', 'Is there diabetes in the family?', 'Does she check her blood sugar?', 'Any thyroid or diabetes?', "Has she ever been told she's diabetic?"], 'vomiting': ['Has she been sick at all?', 'Any retching?', 'Did she vomit at home?', 'Was there any vomit in the room?', 'Any sickness today?', 'Has she brought anything up?', 'Any nausea or vomiting?', 'Did she vomit in the ambulance?', 'Any loose stools?'], 'abdominal_pain': ['Any belly pain?', 'Has she held her tummy at all?', 'Any pain in the stomach?', 'Has she complained of cramps?', 'Any abdominal symptoms?', 'Does her tummy seem to hurt?', 'Any pain when you touch her belly?', 'Any GI symptoms?', 'Has she been constipated?', 'Any bowel problems?'], 'pain_anywhere': ['Where is the pain?', 'Is anything painful?', 'Has she complained of pain anywhere?', 'Any discomfort?', 'Does the pain move anywhere?', 'How severe is it?', 'What sort of pain is it?'], 'urinary_symptoms': ['When did she last go to the toilet?', 'Any trouble weeing?', 'Has she wet herself?', 'Any incontinence?', 'Any urinary problems?', 'Has she been passing water normally?', 'Any pain passing urine?', 'Any frequency or urgency?', 'How much urine has she passed?'], 'chest_or_palpitations': ['Any chest tightness?', 'Has she said her heart was racing?', 'Any complaints about her chest?', 'Has she had chest pain before?', 'Any cardiac symptoms?', 'Has she felt her heart pounding?', 'Any history of heart problems?', 'Any chest discomfort?', 'Any fluttering in the chest?'], 'breathing': ['Any shortness of breath?', 'Has she been breathless?', 'Any wheezing?', 'Does she have asthma?', 'Any inhalers?', 'Any cough?', 'Has her breathing changed?', 'Any difficulty breathing?', 'Any chest infection recently?'], 'vision_or_hallucinations': ['Has she been talking to herself?', "Is she reaching for things that aren't there?", 'Any strange behaviour?', 'Has she been seeing or hearing things?', 'Any delusions?', 'Has she said anything odd?', 'Is she picking at things?', 'Any visual disturbance?', 'Has she been paranoid?', 'Is she hallucinating at all?', 'Any visual hallucinations?'], 'last_oral_intake': ['Has she eaten today?', 'When did she last have a meal?', 'Any food or drink today?', 'When did she last drink anything?', 'Has she had breakfast?', 'Is she nil by mouth?', 'How long since she last ate?', 'Anything to eat or drink in the last few hours?', 'Any fluids today?', 'NPO status?', 'Last meal?', 'Last oral intake?'], 'pregnancy': ['Could she be pregnant?', 'Is she on contraception?', 'When was her last menstrual period?', 'Any chance of pregnancy at all?', 'Has she missed a period?', 'Is she sexually active that you know of?', 'Any pregnancy test recently?', 'Are her periods regular?', 'LMP?', 'Any chance she is pregnant at all?', 'Obstetric history?'], 'travel_and_contacts': ['Has she been abroad recently?', 'Anyone at home unwell?', 'Any contact with anyone infectious?', 'Has she been camping or outdoors?', 'Any tick bites?', 'Anyone at school off sick?', 'Any recent trips?', 'Has she been anywhere unusual?', 'Any exposure history?', 'Travel hx?', 'Any contact history?'], 'immunisations': ['Has she had all her vaccines?', 'Any missed immunisations?', 'Did she have the meningococcal vaccine?', 'Is her childhood schedule complete?', 'Any recent vaccinations?', 'Has she had the HPV jab?', 'Are her boosters up to date?', 'Any vaccine history?', 'Is she fully immunised?', 'Any vaccines in the last month?', 'Vaccination hx?', 'Immunisation status?'], 'what_ems_said': ['What did the ambulance find?', 'Did the crew give her anything?', 'What were her observations in the ambulance?', 'How was she on the way in?', 'Did she change en route?', 'What did the paramedics tell you?', 'Anything happen in the ambulance?', 'Did the crew say anything about her heart?', 'What treatment did she get before arriving?', 'What did the crew hand over?', 'EMS handover?', 'Prehospital findings?'], 'collateral_from_brother': ['Is there anyone else who saw her?', 'Can we speak to anyone at the house?', 'Did anyone hear anything?', 'Who else was there?', 'Has anyone looked round her room?', 'Is there anyone at home now?', 'Could someone check the house?', 'Did her brother notice anything?', 'Any other witnesses?', 'Anyone else who could tell us more?', 'Any collateral history?', 'Is there any collateral?'], 'current_medications': ['Does she take any tablets regularly?', 'Any repeat prescriptions?', 'Is she on anything from the doctor?', 'Any medication at all?', 'Does she take vitamins or supplements?', 'Any herbal remedies?', 'Regular meds?', 'Home meds?']}
for _t in TOPICS:
    for _v in MORE.get(_t["topic"], []):
        if _v not in _t["variants"]:
            _t["variants"].append(_v)

# ---- EXPANDED VARIANTS (generated, do not edit by hand) ----
# Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py in Sep 202
# 6. The added phrasings were written by an AI assistant, not by a physician, and mix lay paraphr
# ase, clinical shorthand and conversational forms. Every sixth new phrasing was withheld into the pack's tuning set rather than added here.
EXPANDED = {
  'onset': [
    'When did this begin?',
    'What time did it start?',
    'How long ago did this come on?',
    'Onset?',
    'When did you first feel unwell?',
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
  'last_seen_well': [
    'Is it getting worse or better?',
    'How has it changed since it began?',
    'Constant or does it come and go?',
    'Intermittent or continuous?',
    'Progression?',
    'Any change over the last few hours?',
    'Is it easing off at all?',
    'Getting worse?',
    'Has it settled at any point?',
    'Compared with when it started, how is it now?',
    'Does it fluctuate?',
    'Has it been steadily building?',
    'Better, worse, or the same?',
    'Has it let up at all?',
    'And is it getting worse or better?',
    'Right. How has it changed since it began?',
    'Quick one: how has it changed since it began?',
    'Before we go on, constant or does it come and go?',
  ],
  'progression': [
    'Has it been the same the whole time?',
    'Is it worse than it was earlier?',
    'Has it stayed the same or changed?',
    'Is this the worst it has been?',
    'Any pattern to it through the day?',
    'Quick one: constant or does it come and go?',
  ],
  'past_medical_history': [
    'Past medical history?',
    'Any medical history?',
    'What conditions do you have?',
    'Do you have any health problems?',
    'Any past history?',
    'Any long-term conditions?',
    'Do you have any illnesses?',
    'Any chronic conditions?',
    'What are you known to have?',
    'Any ongoing health issues?',
    'Do you see a doctor for anything regularly?',
    'Any history of diabetes, high blood pressure, anything like that?',
    'Medical history?',
    'Can I ask, past medical history?',
    'Sorry to ask, but past medical history?',
    'Quick one: any medical history?',
    'Can I ask, any medical problems?',
    'Sorry to ask, but any medical problems?',
  ],
  'past_surgical_history': [
    'Past surgical history?',
    'Any surgery?',
    'Ever had surgery?',
    'Have you had any procedures?',
    'Surgical history?',
    'Have you been under the knife?',
    'Any previous surgeries?',
    'Ever been operated on?',
    'Any history of surgery?',
    'Have you had anything done surgically?',
    'Just so I know, past surgical history?',
    'Sorry to ask, but any operations?',
    'One more thing. Any operations?',
    'I need to know, ever had surgery?',
    'Right. Ever had surgery?',
  ],
  'current_medications': [
    'What prescriptions do you have?',
    'List your medications.',
    'What are you prescribed?',
    'Anything from the chemist?',
    'I need to know, what meds are you on?',
  ],
  'allergies': [
    'Are you allergic to anything?',
    'Allergic to any medications?',
    'Any allergy to antibiotics?',
    'Allergic to penicillin?',
    'Do you have any allergies I should know about?',
    'Any adverse drug reactions?',
    'Any medication allergies?',
    'Drug allergies?',
    'Any allergies to anything?',
    'Sorry to ask, but any allergies?',
    'Okay, any drug allergies?',
    'Just so I know, any drug allergies?',
    'Right. Are you allergic to anything?',
    'Quick one: are you allergic to anything?',
  ],
  'family_history': [
    'fhx cardiac',
    'Any heart problems in the family?',
    'Any family history of heart disease?',
    'Did anyone in your family have heart trouble?',
    'Anything run in the family?',
    'Did your parents have heart disease?',
    'Any family history of illness?',
    'Is there anything that runs in your family?',
    'Family history of cardiac disease?',
    'Quick one: family history?',
    'Quick one: any family history?',
    'Before we go on, any family history?',
    'And any heart problems in the family?',
    'Can I ask, any heart problems in the family?',
  ],
  'sleep_and_appetite': [
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
  'alcohol_and_drugs': [
    'Do you drink?',
    'How much alcohol?',
    'EtOH?',
    'etoh hx',
    'Alcohol history?',
    'How much do you drink a week?',
    'Do you drink alcohol?',
    'Units per week?',
    'Have you been drinking heavily?',
    'Any binge drinking?',
    'Big weekend?',
    'How many drinks a day?',
    'Any drinking over the weekend?',
    'Are you a drinker?',
    'When did you last have a drink?',
    'Any recreational drugs?',
    'Drug use?',
    'Any illicit drugs?',
    'Do you use cocaine?',
    'Any street drugs?',
    'Any stimulants or cocaine?',
    'Substance use?',
    'Do you take anything recreational?',
    'Any drugs at all?',
    'Any amphetamines or cocaine?',
    'Any illicit substance use?',
    'One more thing. How much alcohol?',
    'Okay, how much alcohol?',
    'And alcohol history?',
    'Can I ask, alcohol history?',
    'Can I ask, alcohol intake?',
  ],
  'smoking': [
    'Do you smoke?',
    'Smoker?',
    'Tobacco?',
    'tob?',
    'How many a day?',
    'Pack years?',
    'Are you a smoker?',
    'Have you ever been a smoker?',
    'Do you vape?',
    'Cigarettes?',
    'Any tobacco use?',
    'Okay, smoking history?',
    'Just so I know, smoking history?',
    'Sorry to ask, but how many a day?',
    'One more thing. How many a day?',
    'I need to know, are you a smoker?',
  ],
  'fever_or_infection': [
    'Any fever?',
    'Fever?',
    'Fevers or chills?',
    'Fevers, chills, rigors?',
    'Any temperature?',
    'Any rigors?',
    'Have you been shivering?',
    'Any sweats?',
    'Night sweats?',
    'Do you feel hot and cold?',
    'Any shaking chills?',
    'Have you had the shivers?',
    'Temp at home?',
    'Did you measure a temperature?',
    'Have you been burning up?',
    'Any recent infection?',
    'Recent cold or flu?',
    'Have you had a bug recently?',
    'Any coughs or colds lately?',
    'Any recent chest infection?',
    'Any viral illness recently?',
    'Been poorly in the last few weeks?',
    'Any recent infections?',
    'Can I ask, fevers or chills?',
    'Sorry to ask, but fevers or chills?',
    'Right. Fevers, chills, rigors?',
    'Okay, any temperature?',
    'Just so I know, any temperature?',
  ],
  'headache': [
    'Headache?',
    'Does your head hurt?',
    'Is your head sore?',
    'Any pain in your head?',
    'How bad is the headache?',
    'Worst headache ever?',
    'Any pressure in your head?',
    'Have you had a headache with this?',
    'Is the headache new?',
    'Any pounding in your head?',
    'Sorry to ask, but does your head hurt?',
    'Okay, any head pain?',
    'Just so I know, any head pain?',
    'Sorry to ask, but is your head sore?',
    'One more thing. Is your head sore?',
  ],
  'neck_stiffness': [
    'Neck stiffness?',
    'Is your neck stiff?',
    'Any stiffness in the neck?',
    'Can you touch your chin to your chest?',
    'Does it hurt to move your neck?',
    'Can you bend your neck?',
    'Is your neck sore?',
    'Any stiff neck?',
    'Does your neck feel tight?',
    'Can you look down at your feet?',
    'Any nuchal rigidity?',
    'Photophobia?',
    'Do lights hurt your eyes?',
    'Is the light bothering you?',
    'Are the lights too bright?',
    'Does light hurt?',
    'Are your eyes sensitive to light?',
    'Is the brightness painful?',
    'Do bright lights make it worse?',
    'Any sensitivity to light?',
    'Does looking at the light hurt?',
    'Quick one: neck stiffness?',
    'Before we go on, neck stiffness?',
    'And is your neck stiff?',
    'Can I ask, is your neck stiff?',
    'Before we go on, any stiffness in the neck?',
  ],
  'rash': [
    'Tell me about the rash.',
    'Where is the rash?',
    'When did the rash start?',
    'Does the rash blanch?',
    'Is the rash spreading?',
    'Describe the rash.',
    'What does the rash look like?',
    'Any bruising or spots?',
    'Does the rash fade when pressed?',
    'Where did the spots start?',
    'Any new spots?',
    'And where is the rash?',
    'Can I ask, where is the rash?',
    'And when did the rash start?',
    'Can I ask, when did the rash start?',
    'Before we go on, does the rash blanch?',
  ],
  'vomiting': [
    'N/V?',
    'Nausea or vomiting?',
    'Have you been sick?',
    'Have you thrown up?',
    'Do you feel sick?',
    'Feeling queasy?',
    'Been throwing up?',
    'Have you brought anything up?',
    'Do you feel nauseous?',
    'How many times have you vomited?',
    'Before we go on, nausea or vomiting?',
    'And nausea or vomiting?',
    'Just so I know, have you been sick?',
    'I need to know, have you been sick?',
    'Okay, have you thrown up?',
  ],
  'abdominal_pain': [
    'Does your belly hurt?',
    'Abdo pain?',
    'Any pain in your abdomen?',
    'Is your stomach sore?',
    'Any belly ache?',
    'Does it hurt in your stomach?',
    'Any cramping in your belly?',
    'Any abdominal tenderness?',
    'Just so I know, any abdominal pain?',
    'I need to know, any abdominal pain?',
    'Just so I know, any tummy pain?',
    'Before we go on, does your belly hurt?',
    'And does your belly hurt?',
  ],
  'pain_anywhere': [
    'Show me where it hurts.',
    'Point to where it hurts.',
    'Location of the pain?',
    'Where exactly is it?',
    'Is it in one place or all over?',
    'Which part of you hurts?',
    'Is it your arms, your legs, or everywhere?',
    'Can you localise the pain?',
    'Where is it worst?',
    'Is the pain in your muscles?',
    'Where does it hurt right now?',
    'Does it spread?',
    'Does it go anywhere else?',
    'Radiation?',
    'Does the pain travel?',
    'Does it go through to your back?',
    'Any radiation of the pain?',
    'Does it stay put or move around?',
    'Does the pain shoot anywhere?',
    'Is it spreading from where it started?',
    'Rate the pain out of ten.',
    'Severity?',
    'On a scale of one to ten?',
    'Is it the worst you have ever had?',
    'How bad is it right now?',
    'Mild, moderate, or severe?',
    'How much is it bothering you?',
    'Can you score it for me?',
    'Pain score?',
    'How bad on a scale?',
    'How intense is it?',
    'Describe what you are feeling.',
    'What does it feel like?',
    'Tell me about the symptoms.',
    'How would you describe it?',
    'What is the main thing bothering you?',
    'What sort of feeling is it?',
    'Is it an ache, a pain, or something else?',
    'Can you put it into words for me?',
    'What does it feel like in your body?',
    'Describe the discomfort.',
    'Quick one: where is the pain?',
    'Before we go on, where is the pain?',
    'Just so I know, location of the pain?',
    'I need to know, location of the pain?',
    'Just so I know, where exactly is it?',
  ],
  'urinary_symptoms': [
    'Any burning when you pee?',
    'Dysuria?',
    'Does it sting to pass urine?',
    'Any discharge?',
    'Any vaginal symptoms?',
    'Any GU symptoms?',
    'Any pelvic pain?',
    'Any pain when urinating?',
    'Any itching or discharge?',
    'Any trouble with your waterworks?',
    'Are you passing urine?',
    'Urine output?',
    'UOP?',
    'How much urine?',
    'Passing water okay?',
    'Have you peed today?',
    'Any drop in your urine?',
    'Are you peeing less?',
    'How often are you going to the toilet?',
    'Have you been passing less water?',
    'Any reduction in urine output?',
    'When did you last go for a wee?',
    'Are you making urine?',
    'Have you passed water since this started?',
    'Quick one: any burning when you pee?',
    'Okay, any urinary symptoms?',
    'Just so I know, any urinary symptoms?',
    'Quick one: does it sting to pass urine?',
    'Before we go on, does it sting to pass urine?',
  ],
  'chest_or_palpitations': [
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
    'Palpitations?',
    'Heart racing at all?',
    'Does your heart feel like it is skipping?',
    'Have you felt your heart beating fast?',
    'Any awareness of your heartbeat?',
    'Is your heart thumping?',
    'Does your heart feel odd?',
    'Have you noticed your pulse racing?',
    'Any pounding in your chest?',
    'Just so I know, any chest pain?',
    'I need to know, any chest pain?',
    'I need to know, pain in the chest?',
    'Before we go on, is your chest hurting?',
    'And is your chest hurting?',
  ],
  'breathing': [
    'Are you breathless?',
    'Short of breath?',
    'SOB?',
    'Any SOB?',
    'Is it hard to breathe?',
    'Do you feel you cannot get your breath?',
    'Breathless at all?',
    'Dyspnoea?',
    'Dyspnea?',
    'Any trouble with your breathing?',
    'Are you getting enough air?',
    'I need to know, are you breathless?',
    'Right. Are you breathless?',
    'Right. Short of breath?',
    'Quick one: short of breath?',
    'Just so I know, any shortness of breath?',
  ],
  'vision_or_hallucinations': [
    'Any change in your thinking?',
    'Do you feel foggy?',
    'Have you been making sense to people?',
    'Quick one: any confusion?',
    'One more thing. Are you thinking clearly?',
  ],
  'last_oral_intake': [
    'When did you last eat?',
    'last PO',
    'When did you last drink?',
    'NPO since when?',
    'Have you eaten today?',
    'Have you had anything to eat or drink?',
    'Last food or drink?',
    'Anything to eat or drink today?',
    'When did you last have something to drink?',
    'Are you eating and drinking?',
    'How much have you been drinking?',
    'When did you last eat anything?',
    'Have you managed any food?',
    'And when did you last eat?',
    'Can I ask, when did you last eat?',
    'Can I ask, last oral intake?',
    'One more thing. Last PO intake?',
    'Okay, last PO intake?',
  ],
  'pregnancy': [
    'Could you be pregnant?',
    'Are you pregnant?',
    'Pregnancy?',
    'Is there any chance you are pregnant?',
    'When was your last period, could you be pregnant?',
    'Any possibility of pregnancy?',
    'Are you using contraception?',
    'Is pregnancy possible?',
    'Could you be expecting?',
    'Any chance you might be pregnant?',
    'Are you on your period?',
    'Do you use tampons?',
    'Tampon use?',
    'Any tampon in at the moment?',
    'When did your last period start?',
    'Menstrual history?',
    'Are you menstruating?',
    'Any tampon left in?',
    'Have you got a tampon in?',
    'Date of last period?',
    'Sexual history?',
    'Any sexual partners?',
    'Do you have a partner?',
    'Any new partners recently?',
    'Any unprotected sex?',
    'Any risk of an STI?',
    'When did you last have sex?',
    'Any sexual contact recently?',
    'Do you use protection?',
    'Any history of sexually transmitted infections?',
    'One more thing. Could you be pregnant?',
    'I need to know, any chance of pregnancy?',
    'Right. Any chance of pregnancy?',
    'Okay, are you pregnant?',
    'Just so I know, are you pregnant?',
  ],
  'travel_and_contacts': [
    'Been abroad recently?',
    'Have you travelled?',
    'Any foreign travel?',
    'Travel history?',
    'Have you been out of the country?',
    'Where have you been recently?',
    'Any travel in the last few months?',
    'Have you been anywhere unusual?',
    'Any overseas travel?',
    'Been away anywhere?',
    'Is anyone around you sick?',
    'Has anyone you live with been ill?',
    'Anyone at home with the same thing?',
    'Any contact with someone unwell?',
    'Anyone in your halls been ill?',
    'Any friends or flatmates sick?',
    'Anybody close to you unwell recently?',
    'Any outbreaks where you live?',
    'Has anyone you know had similar symptoms?',
    'Right. Any recent travel?',
    'Just so I know, been abroad recently?',
    'I need to know, been abroad recently?',
    'And have you travelled?',
    'Can I ask, have you travelled?',
  ],
  'immunisations': [
    'Are your vaccinations up to date?',
    'Vaccines?',
    'Have you had your jabs?',
    'Immunisation history?',
    'Have you had the meningitis vaccine?',
    'Did you have your school vaccines?',
    'Are your immunisations current?',
    'Any vaccines recently?',
    'Have you had all your childhood vaccines?',
    'Meningococcal vaccine?',
    'Right. Are your vaccinations up to date?',
    'Quick one: are your vaccinations up to date?',
    'One more thing. Vaccination history?',
    'Okay, vaccination history?',
    'I need to know, any immunisations?',
  ],
  'collateral_from_brother': [
    'Anyone else unwell?',
    'Has anyone else got this?',
    'Just so I know, any sick contacts?',
    'I need to know, any sick contacts?',
    'Sorry to ask, but anyone else unwell?',
    'Sorry to ask, but is anyone around you sick?',
    'One more thing. Is anyone around you sick?',
  ],
}
OUT_OF_SCOPE_BANK = [
  'Have you ever had a colonoscopy?',
  'Any blood when you open your bowels?',
  'Are you constipated?',
  'Any heartburn?',
  'Any indigestion after meals?',
  'Any change in your bowel habit?',
  'Any diarrhoea at all?',
  'Have you had piles?',
  'Any black stools?',
  'Any yellowing of your skin or eyes?',
  'Any blood in your urine?',
  'Any trouble with your prostate?',
  'Any kidney stones in the past?',
  'Any seizures or fits?',
  'Any pins and needles?',
  'Any numbness anywhere?',
  'Any problems with your speech?',
  'Any tremor in your hands?',
  'Any double vision?',
  'Any pain in your hands?',
  'Any pain in your hips?',
  'Any arthritis?',
  'Have you broken any bones?',
  'Any problems with your hearing?',
  'Any ringing or buzzing in your ears?',
  'Any earache?',
  'Do you wear glasses or contact lenses?',
  'When did you last have your eyes tested?',
  'Any sinus trouble?',
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
  'Who is your next of kin?',
  'Do you have any religious needs we should know about?',
  'What do you do for a living?',
  'What did you do before you retired?',
  'Did you come in by ambulance?',
  'Is anyone here with you?',
  'Is your family in the waiting room?',
  'Is it raining outside?',
  'Do you have children?',
  'How many kids do you have?',
  'Where do you live?',
  'Do you follow any sports?',
  'What do you do to relax?',
  'Do you have a garden?',
  'Are you comfortable on that trolley?',
  'Would you like a blanket?',
  'Is the bed at the right height?',
  'What is your date of birth?',
  'Can you confirm your name for me?',
  'What is your address?',
  'Do you know why you are here?',
  'How old are you?',
  'Would you prefer a female doctor?',
  'Have you been waiting long?',
  'Is there anything you would like to ask me?',
  'What year are you in at university?',
  'What are you studying?',
  'How much does it cost to park here?',
]
for _t in TOPICS:
    if EXPANDED.get(_t['topic']):
        _t['expanded_variants'] = list(EXPANDED[_t['topic']])
        _t['variants_provenance'] = "Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py in Sep 2026. The added phrasings were written by an AI assistant, not by a physician, and mix lay paraphrase, clinical shorthand and conversational forms. Every sixth new phrasing was withheld into the pack's tuning set rather than added here."
# ---- END EXPANDED VARIANTS ----
