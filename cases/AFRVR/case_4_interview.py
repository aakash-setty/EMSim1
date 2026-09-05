"""AFRVR part 4: the interview bank."""

def T(topic, canonical, variants, gasping, full, pertinent_negative=False):
    d = {
      "topic": topic,
      "canonical": canonical,
      "variants": variants,
      "answer": [
        {"when": "phase is respiratory_failure", "value": gasping},
        {"when": None, "value": full},
      ],
    }
    if pertinent_negative:
        d["pertinent_negative"] = True
    return d

TOPICS = [

T("onset", "When did this start?",
 ["When did it start?", "How long has this been going on?", "When did your heart start racing?",
  "How long have you been feeling like this?", "When did you first notice it?",
  "What time did this begin?", "How many hours has this been going on?",
  "Did it come on suddenly or gradually?", "When did the palpitations start?",
  "How long has your heart been going like this?", "When did the breathing get bad?",
  "How long have you been short of breath?", "When did all this kick off?",
  "Tell me when this began.", "Was there a moment it started or did it creep up?"],
 "'Yesterday... afternoon.'",
 "'Yesterday afternoon, about three o'clock. I was sat watching the television and it just "
 "started, like something turned over in my chest. It hasn't stopped since. The breathing came on "
 "after, later in the evening.'"),

T("timing_progression", "Has it been getting worse?",
 ["Is it getting worse?", "How has it changed since it started?",
  "Has it been constant or does it come and go?", "Is it worse now than yesterday?",
  "Has anything changed since it started?", "Is it steady or intermittent?",
  "Did it stop at any point?", "Has it been continuous?",
  "How has it progressed?", "Is it better or worse than it was?",
  "Has it come and gone or has it stayed?", "What's the pattern been?",
  "Is this the worst it's been?", "Has it built up over time?",
  "Did it get worse overnight?"],
 "'Worse. All night.'",
 "'It's not stopped once, and the breathing has got worse every hour. Last night was the worst of "
 "it. This morning I couldn't get from the chair to the kitchen without having to stop, and that's "
 "when my daughter called the ambulance.'"),

T("character_of_palpitations", "What does your heart feel like?",
 ["What does the racing feel like?", "Describe the palpitations.", "Is it regular or irregular?",
  "Does it feel fast or does it feel like it's skipping?", "What's the sensation in your chest?",
  "Can you describe your heartbeat?", "Is it fluttering or pounding?",
  "Does it feel steady?", "Tell me about the racing.", "What does it feel like in your chest?",
  "Is your heart beating evenly?", "Does it feel like it's jumping about?",
  "How would you describe the palpitations?", "Is it a flutter or a thump?",
  "What does the racing feel like to you?"],
 "'All over... the place.'",
 "'It's like a bird flapping in there. It doesn't keep any kind of time, it just goes and goes and "
 "then gives a big thump and carries on. I can feel it in my throat.'"),

T("dyspnea_character", "Tell me about the breathing.",
 ["What's the breathing like?", "Describe your shortness of breath.",
  "Is it hard to get air in or out?", "Does it feel tight or does it feel like you can't get "
  "enough air?", "What is the breathlessness like?", "How is your breathing?",
  "Do you feel like you're suffocating?", "Is it wheezy?", "Does your chest feel tight?",
  "What does the breathlessness feel like?", "Are you struggling to breathe?",
  "Is it worse breathing in or breathing out?", "Tell me about the shortness of breath.",
  "How would you describe the breathing trouble?", "Do you feel like you're drowning?"],
 "'Can't... get enough.'",
 "'I can't get a full breath. It's like there's a weight on me and I only get half of what I need "
 "each time, so I have to keep going faster to make up for it. I'm exhausted from it.'"),

T("severity", "How bad is it?",
 ["How bad is this?", "On a scale of one to ten how bad is the breathing?",
  "How severe is it?", "Is this the worst you've felt?", "How bad does it feel right now?",
  "Have you ever felt this bad before?", "How much is this affecting you?",
  "How would you rate it?", "Is it unbearable?", "How bad compared with anything before?",
  "Rate the severity for me.", "How distressing is this?",
  "Is this frightening you?", "How much trouble are you in?",
  "Would you say this is severe?"],
 "'Bad. Really... bad.'",
 "'The worst I've ever felt. I've never had anything like this. I honestly thought I wasn't going "
 "to make it to the front door this morning.'"),

T("aggravating_factors", "What makes it worse?",
 ["What makes it worse?", "Does anything bring it on?", "Is there anything that aggravates it?",
  "What makes the breathing worse?", "Does moving make it worse?",
  "Is it worse when you exert yourself?", "Does lying down make it worse?",
  "What sets it off?", "Does anything trigger it?", "When is it at its worst?",
  "Does walking make it worse?", "What makes it harder?", "Is there anything that worsens it?",
  "Does eating or drinking change it?", "What position is worst?"],
 "'Moving. Lying... flat.'",
 "'Anything at all. Standing up, walking to the bathroom, even talking to you now. And lying flat "
 "is the worst of it, I can't do it at all.'"),

T("relieving_factors", "Does anything make it better?",
 ["What makes it better?", "Does anything help?", "Is there anything that relieves it?",
  "Have you found anything that eases it?", "Does sitting up help?", "Does resting help?",
  "Have you tried anything for it?", "Did anything you did make it better?",
  "Does any position help?", "What relieves the breathing?",
  "Does stopping and resting settle it?", "Has anything eased the racing?",
  "Did you take anything for it?", "Is there anything that calms it down?",
  "Does sitting forward help at all?"],
 "'Sitting... up. A bit.'",
 "'Sitting bolt upright is the only thing. Resting used to settle it a bit yesterday but it "
 "doesn't any more, it just carries on whatever I do. I didn't take anything for it.'"),

T("chest_pain", "Are you having any chest pain?",
 ["Any chest pain?", "Does your chest hurt?", "Have you had any pain in your chest?",
  "Is there any pain with this?", "Any pressure in your chest?",
  "Do you have chest discomfort?", "Any crushing feeling?", "Is there pain anywhere?",
  "Have you had chest pain at any point?", "Any pain going into your arm or jaw?",
  "Does it hurt when your heart races?", "Any tightness that feels like pain?",
  "Have you had any angina?", "Is there pain in your chest now?",
  "Did you have chest pain before this started?"],
 "'No... pain.'",
 "'No, no pain. It's not sore. I can feel it thumping and I can feel that I can't breathe, but "
 "there's no pain to it. Nothing in my arm, nothing in my jaw.'",
 pertinent_negative=True),

T("syncope_presyncope", "Have you passed out?",
 ["Did you faint?", "Have you passed out?", "Any blackouts?", "Did you lose consciousness?",
  "Have you fallen?", "Did you nearly pass out?", "Any episodes of collapse?",
  "Have you blacked out at all?", "Did you go down at any point?",
  "Have you had a funny turn?", "Did you collapse?", "Any loss of consciousness?",
  "Have you been unconscious?", "Did you faint at home?", "Any near-fainting?"],
 "'No. Never... went out.'",
 "'No, I've not passed out. I've felt swimmy when I stand up too quick, but I've not gone down "
 "and I've not blacked out at any point.'",
 pertinent_negative=True),

T("dizziness_lightheadedness", "Have you felt dizzy?",
 ["Any dizziness?", "Do you feel lightheaded?", "Have you been dizzy?",
  "Any spinning sensation?", "Do you feel faint?", "Have you felt woozy?",
  "Any vertigo?", "Do you get lightheaded standing up?", "Have you been unsteady?",
  "Any dizzy spells?", "Do you feel like you might faint?", "Is the room spinning?",
  "Have you felt off balance?", "Any lightheadedness with this?",
  "Do you get dizzy when you move?"],
 "'Bit... swimmy.'",
 "'A bit swimmy when I stand up quickly, and I've had to hold onto the furniture once or twice. "
 "Nothing spinning. It settles once I'm up.'"),

T("orthopnea", "Can you lie flat?",
 ["Can you lie flat?", "How many pillows do you sleep on?",
  "Do you get breathless lying down?", "Can you sleep flat in bed?",
  "Do you have to prop yourself up?", "Does lying down make your breathing worse?",
  "How do you sleep at night?", "Do you need pillows to breathe?",
  "Can you lie down flat without getting short of breath?", "Any orthopnoea?",
  "Has your sleeping position changed?", "Do you sleep sitting up?",
  "How many pillows do you use now compared with before?", "Can you get flat in the bed?",
  "Do you sleep in a chair?"],
 "'Can't... lie down.'",
 "'I can't. The last two nights I've had three pillows behind me and I still ended up sat on the "
 "edge of the bed. Before this week I slept on one pillow, flat, no trouble at all.'"),

T("paroxysmal_nocturnal_dyspnea", "Do you wake up at night short of breath?",
 ["Do you wake up gasping?", "Have you woken up unable to breathe?",
  "Do you get short of breath at night?", "Any waking up fighting for air?",
  "Have you woken in the night breathless?", "Any nocturnal breathlessness?",
  "Do you wake up choking?", "Have you had to get up in the night to breathe?",
  "Any PND?", "Do you wake up and have to open a window?",
  "Have you woken up suddenly short of breath?", "Does the breathing wake you?",
  "Have you had to sit up in the night to catch your breath?",
  "Any episodes at night of breathlessness?", "Do you get breathless when you're asleep?"],
 "'Twice. Last... night.'",
 "'Twice last night. I woke up both times feeling like I was drowning and had to get to the "
 "window and hang out of it. That's never happened to me before.'"),

T("leg_swelling", "Have your legs been swelling?",
 ["Any swelling in your legs?", "Have your ankles been puffy?",
  "Is there swelling anywhere?", "Have your feet been swollen?",
  "Any oedema?", "Have your socks been leaving marks?",
  "Have your legs changed?", "Is there swelling in your ankles?",
  "Have your shoes been tight?", "Any puffiness in your feet?",
  "How long have your legs been swollen?", "Have you noticed swelling?",
  "Are your legs bigger than usual?", "Any fluid in your legs?",
  "Have your ankles been bothering you?"],
 "'Yes. Both... of them.'",
 "'About a week. My socks have been leaving deep marks round the top and my shoes have been "
 "tight. Both legs, the same. I thought it was the heat.'"),

T("weight_gain", "Have you put on weight recently?",
 ["Have you gained weight?", "Any weight change?", "Have you put weight on?",
  "Have your clothes got tighter?", "Do you weigh yourself?",
  "How much weight have you gained?", "Has your weight changed recently?",
  "Any sudden weight gain?", "Have your trousers been tight?",
  "Have you been getting heavier?", "What was your weight before this?",
  "Have you noticed any change in your weight?", "Any bloating or weight gain?",
  "Do you know your usual weight?", "Have you gained anything in the last week?"],
 "'Trousers... tighter.'",
 "'I don't weigh myself, but my trousers have been tight round the waist this last week and I've "
 "had to let my belt out a notch. My middle feels bloated.'"),

T("exercise_tolerance_baseline", "What could you do before this started?",
 ["What's your normal exercise tolerance?", "What could you do a week ago?",
  "How far could you walk before?", "What's your baseline?",
  "Were you well before this?", "How active are you normally?",
  "What can you usually manage?", "Could you climb stairs before this?",
  "How far do you normally walk?", "What's your usual level of activity?",
  "Have you been able to do your usual activities?", "Do you exercise?",
  "How fit are you normally?", "What were you like before yesterday?",
  "How much can you normally do?"],
 "'Walked the... dog. Every day.'",
 "'I walked the dog twice a day, half an hour each time, up the hill and back, no bother at all. "
 "I'm still working part time. A week ago there was nothing wrong with me.'"),

T("cough_and_sputum", "Have you had a cough?",
 ["Any cough?", "Are you coughing anything up?", "Do you have a productive cough?",
  "Any phlegm?", "What colour is the sputum?", "Have you been coughing?",
  "Is the cough dry or wet?", "Any sputum?", "Are you bringing anything up?",
  "Have you coughed up any blood?", "Is there a cough with this?",
  "How long have you had the cough?", "Any frothy sputum?", "Do you cough at night?",
  "Has the cough changed?"],
 "'Dry. When I... lie down.'",
 "'A bit of a dry cough, mostly when I lie down. Nothing comes up. No blood, nothing coloured, "
 "nothing frothy. It's not really a cough so much as a tickle.'"),

T("fever_and_chills", "Have you had a fever?",
 ["Any fever?", "Have you had chills?", "Any temperature?", "Have you been shivering?",
  "Do you feel hot and cold?", "Any night sweats?", "Have you had rigors?",
  "Have you taken your temperature?", "Any signs of infection?",
  "Have you been feverish?", "Any sweats?", "Have you felt hot?",
  "Any chills or shakes?", "Have you had a temperature at home?",
  "Do you think you've got an infection?"],
 "'No... fever.'",
 "'No fever, no shivering, nothing like that. I've been sweaty this morning but that's from the "
 "struggling, not from being hot.'",
 pertinent_negative=True),

T("prior_afib_or_palpitations", "Has your heart ever done this before?",
 ["Have you had palpitations before?", "Has this happened before?",
  "Do you have a history of atrial fibrillation?", "Have you ever had an irregular heartbeat?",
  "Has anyone told you your heart is irregular?", "Any previous arrhythmia?",
  "Is this the first time?", "Have you had this racing before?",
  "Do you have AF?", "Has your heart ever raced like this?",
  "Any history of a heart rhythm problem?", "Have you been told about your heart rhythm?",
  "Have you ever been in atrial fibrillation?", "Is this new for you?",
  "Have you had episodes like this in the past?"],
 "'Never. First... time.'",
 "'Never. Nobody has ever told me my heart is irregular and I've never felt anything like this "
 "before. I've had my blood pressure checked plenty of times and nobody ever said a word about "
 "the rhythm.'",
 pertinent_negative=True),

T("prior_heart_failure", "Have you ever been told you have heart failure?",
 ["Do you have heart failure?", "Any history of heart failure?",
  "Have you ever had a heart scan?", "Have you had an echocardiogram?",
  "Has anyone said your heart is weak?", "Do you have a weak heart?",
  "Any problems with your heart pumping?", "Have you been told about your heart function?",
  "Have you ever had fluid on your lungs before?", "Any previous cardiac diagnosis?",
  "Has a cardiologist ever seen you?", "Has your heart been scanned?",
  "Do you know your ejection fraction?", "Have you had heart trouble before?",
  "Any history of a cardiomyopathy?"],
 "'No. Never... had that.'",
 "'No, never. I've never had a scan of my heart and nobody has ever said anything about it being "
 "weak. They did a CT of my heart arteries three years back and told me there was some furring up "
 "but nothing that needed doing.'",
 pertinent_negative=True),

T("past_medical_history", "What medical problems do you have?",
 ["What's your past medical history?", "Do you have any medical conditions?",
  "What illnesses do you have?", "Any health problems?", "What are you treated for?",
  "Do you see a doctor for anything?", "Any chronic conditions?",
  "What's your background?", "Do you have diabetes or blood pressure?",
  "Tell me about your health.", "What conditions do you have?",
  "Any long-term conditions?", "What do you get treated for?",
  "Have you got any medical history?", "What's wrong with you normally?"],
 "'Blood pressure. Sugar.'",
 "'High blood pressure and diabetes, both for years. And they found some furring up in my heart "
 "arteries on a CT scan three years ago, but they said it wasn't bad enough to do anything about "
 "and just put me on a statin. That's it.'"),

T("past_surgical_history", "Have you had any operations?",
 ["Any previous surgery?", "Have you had any operations?", "What surgery have you had?",
  "Any procedures in the past?", "Have you ever been operated on?",
  "Any stents or bypasses?", "Have you had heart surgery?",
  "Any operations at all?", "Have you been in hospital for surgery?",
  "Any recent procedures?", "What's your surgical history?",
  "Have you had a stent put in?", "Any surgery in the last few months?",
  "Have you ever had an anaesthetic?", "Any operations I should know about?"],
 "'Gallbladder. Years... ago.'",
 "'They took my gallbladder out about fifteen years ago and that's the only time I've been under. "
 "No stents, no bypass, nothing on my heart. Nothing recent at all.'",
 pertinent_negative=True),

T("current_medications", "What medications are you taking?",
 ["What tablets are you on?", "What medications do you take?", "What drugs are you on?",
  "Can you list your medicines?", "What do you take every day?",
  "Are you on any medication?", "What's on your prescription?",
  "What pills do you take?", "Tell me your medications.",
  "Are you taking anything regularly?", "What's your medication list?",
  "Do you take any heart tablets?", "What are you prescribed?",
  "Any regular medicines?", "What do you take at home?"],
 "'Three. Blood pressure... statin... metformin.'",
 "'Three things. A blood pressure tablet, lisinopril I think it's called, twenty milligrams. A "
 "statin at night, atorvastatin. And metformin twice a day for the sugar. That's the lot.'"),

T("anticoagulant_history_and_bleeding", "Are you on any blood thinners?",
 ["Do you take a blood thinner?", "Are you on warfarin?", "Any anticoagulants?",
  "Do you take aspirin?", "Are you on apixaban or rivaroxaban?",
  "Have you ever been on a blood thinner?", "Do you take anything to thin your blood?",
  "Any bleeding problems?", "Have you had a bleed before?",
  "Do you bruise easily?", "Any history of a stomach ulcer?",
  "Have you had any bleeding recently?", "Any reason you couldn't take a blood thinner?",
  "Do you take clopidogrel?", "Any falls recently?"],
 "'No. Nothing... like that.'",
 "'No, nothing like that. I've never been on a blood thinner and I don't even take aspirin. I've "
 "never had a bleed, never had an ulcer, and I haven't had a fall.'",
 pertinent_negative=True),

T("medication_adherence", "Have you been taking your tablets?",
 ["Are you taking your medications?", "Have you missed any doses?",
  "Do you take them regularly?", "Have you run out of anything?",
  "Are you good with your tablets?", "Did you take them this morning?",
  "Have you stopped any of your medicines?", "Any medications you've not been taking?",
  "How reliable are you with your tablets?", "Have you skipped any?",
  "Are you up to date with your prescriptions?", "Have you had trouble getting your tablets?",
  "Do you ever forget them?", "Have you been compliant?",
  "Did you take your medicines yesterday?"],
 "'Take them. Every... day.'",
 "'Every morning without fail, my daughter set me up one of those weekly boxes. I took them "
 "yesterday and I took them this morning before all this.'"),

T("allergies", "Do you have any allergies?",
 ["Any allergies?", "Are you allergic to anything?", "Any drug allergies?",
  "Do you react to any medications?", "Any allergies to medicines?",
  "Have you had a reaction to a drug?", "Are you allergic to any antibiotics?",
  "Any known allergies?", "Do you have any intolerances?",
  "Any reactions to anything?", "Is there anything you can't take?",
  "Any allergy to contrast?", "Have you had an allergic reaction before?",
  "Anything you're allergic to?", "Any adverse drug reactions?"],
 "'None.'",
 "'No, nothing. I can take anything as far as I know.'",
 pertinent_negative=True),

T("alcohol_and_binge", "How much do you drink?",
 ["Do you drink alcohol?", "How much alcohol do you drink?", "Have you been drinking?",
  "Do you drink much?", "How many units a week?", "Did you drink recently?",
  "Have you had a heavy weekend?", "Any binge drinking?",
  "What's your alcohol intake?", "Do you drink beer or spirits?",
  "How much did you have at the weekend?", "Any recent alcohol?",
  "Do you drink every day?", "Have you had more than usual lately?",
  "Tell me about your drinking."],
 "'Few beers. Saturday.'",
 "'Two or three beers at the weekend, that's all, and nothing during the week. Although I had "
 "more than that on Saturday, we had a barbecue for my grandson's birthday and I'd say I had four "
 "or five over the afternoon. Is that what did it?'"),

T("caffeine_and_stimulants", "Do you take any stimulants?",
 ["How much caffeine do you have?", "Do you drink coffee?", "Any energy drinks?",
  "Do you use cocaine?", "Any recreational drugs?", "Do you take any stimulants?",
  "Any drug use?", "Do you use amphetamines?", "Any over the counter medicines or supplements?",
  "How many coffees a day?", "Do you take anything for energy?",
  "Any herbal remedies?", "Have you taken any decongestants?",
  "Do you use any street drugs?", "Any diet pills or supplements?"],
 "'Two coffees. Nothing... else.'",
 "'Two cups of coffee in the morning, same as I've had for forty years. No energy drinks, no "
 "supplements, no herbal things. And no, I've never taken any drugs, not once.'",
 pertinent_negative=True),

T("thyroid_symptoms", "Any problems with your thyroid?",
 ["Do you have thyroid trouble?", "Any heat intolerance?", "Have you lost weight?",
  "Any tremor?", "Do you feel hot all the time?", "Any thyroid problems?",
  "Have you been more anxious or sweaty than usual?", "Any change in your bowels?",
  "Do you have a goitre?", "Any hyperthyroid symptoms?",
  "Have you been losing weight without trying?", "Do your hands shake?",
  "Any neck swelling?", "Have you been intolerant of the heat?",
  "Is your thyroid checked?"],
 "'No. Nothing... like that.'",
 "'No, nothing wrong with my thyroid that I know of. I've not lost weight, my hands don't shake, "
 "and I feel the cold if anything. Nobody has ever checked it as far as I remember.'",
 pertinent_negative=True),

T("social_history_smoking", "Do you smoke?",
 ["Have you ever smoked?", "Are you a smoker?", "How many do you smoke?",
  "When did you stop smoking?", "What's your smoking history?",
  "How many pack years?", "Do you use tobacco?", "Have you smoked in the past?",
  "Do you vape?", "How long did you smoke for?", "Are you an ex-smoker?",
  "Did you ever smoke cigarettes?", "How much did you smoke?",
  "Have you given up smoking?", "Any tobacco use?"],
 "'Gave up. Years... ago.'",
 "'I smoked from my twenties until I was about forty-five, twenty a day at the worst of it, and "
 "then I packed it in and I've not touched one since. That's over twenty years now.'"),

T("family_history", "Any heart problems in the family?",
 ["What's your family history?", "Any heart disease in the family?",
  "Has anyone in your family had a stroke?", "Any family history of arrhythmia?",
  "Did your parents have heart trouble?", "Any sudden deaths in the family?",
  "Does heart disease run in your family?", "Any family history I should know about?",
  "Have your siblings had heart problems?", "Any family history of atrial fibrillation?",
  "Did anyone in your family die young of their heart?",
  "Any clots or strokes in the family?", "What did your parents die of?",
  "Is there anything that runs in the family?", "Any inherited conditions?"],
 "'Dad had... a stroke.'",
 "'My dad had a stroke when he was seventy-four and never really got over it. My brother has "
 "something with his heartbeat, he's on tablets for it, I don't know what it's called. My mother "
 "was fine until she was ninety.'"),

T("last_oral_intake", "When did you last eat or drink?",
 ["When did you last eat?", "What was your last meal?", "When did you last have anything to drink?",
  "Have you eaten today?", "When did you last eat or drink anything?",
  "What time was your last meal?", "Are you nil by mouth?",
  "Have you had breakfast?", "When did you last have food?",
  "What have you had today?", "Have you eaten since this started?",
  "When was your last drink of water?", "Have you had anything this morning?",
  "What did you last eat?", "How long since you ate?"],
 "'Toast. This... morning.'",
 "'Toast and a cup of coffee at about seven this morning. I couldn't finish the toast, I was too "
 "puffed. Nothing since.'"),

T("recent_illness_or_sick_contacts", "Have you been unwell recently?",
 ["Any recent illness?", "Have you had a cold?", "Any sick contacts?",
  "Has anyone around you been ill?", "Have you had an infection recently?",
  "Any recent viral illness?", "Have you been unwell in the last few weeks?",
  "Any coughs or colds recently?", "Have you had COVID?",
  "Anyone at home unwell?", "Any recent chest infection?",
  "Have you been to the doctor recently?", "Any illness before this started?",
  "Have you had flu?", "Any recent fevers or infections?"],
 "'No. Been... well.'",
 "'No, nothing. I've been perfectly well. No colds, nobody at home has been ill, and I've not "
 "been to the doctor since my last diabetes check in the spring.'",
 pertinent_negative=True),

T("travel_immobility_surgery", "Have you travelled recently?",
 ["Any recent travel?", "Have you been on a long flight?",
  "Have you been immobile recently?", "Any long journeys?",
  "Have you been bedbound at all?", "Any recent surgery or immobilisation?",
  "Have you been on a long car journey?", "Any risk factors for a clot?",
  "Have you been abroad?", "Have you been sitting still for long periods?",
  "Any hospital admissions recently?", "Have you had a cast or a splint?",
  "Any history of clots?", "Have you had a DVT or a PE before?",
  "Any reason you'd be at risk of a clot?"],
 "'No. Been... home.'",
 "'No travel, no flights, nothing like that. I've been at home and out with the dog every day "
 "until this week. I've never had a clot and neither has anyone in my family that I know of.'",
 pertinent_negative=True),

T("calf_pain_or_asymmetry", "Any pain in your calves?",
 ["Do your legs hurt?", "Any calf pain?", "Is one leg more swollen than the other?",
  "Any tenderness in your legs?", "Does one calf hurt?",
  "Is there any asymmetry in your legs?", "Any pain in the back of your legs?",
  "Do your calves feel tight?", "Is one leg bigger?",
  "Any redness or heat in your legs?", "Do your legs hurt when you walk?",
  "Any tenderness behind the knee?", "Is either leg painful?",
  "Any leg symptoms other than the swelling?", "Does squeezing your calf hurt?"],
 "'No. Just... puffy.'",
 "'No pain at all, they're just puffy. Both the same, and they've been like that for about a "
 "week. Nothing red, nothing hot, and they don't hurt when I walk.'",
 pertinent_negative=True),

T("urine_output", "How much have you been passing urine?",
 ["Are you passing urine normally?", "How's your urine output?",
  "Have you been going to the toilet as usual?", "Any change in how much you're passing?",
  "Are you passing less water?", "How often are you urinating?",
  "Any problems passing urine?", "Have you been going less?",
  "What colour is your urine?", "Any change in your waterworks?",
  "Have you noticed passing less?", "Are you weeing normally?",
  "How much urine have you passed today?", "Any difficulty passing urine?",
  "Has your urine output dropped?"],
 "'Less. Last... few days.'",
 "'Less than usual, I'd say, these last couple of days, and it's been darker. I used to be up "
 "twice in the night for it and I haven't been at all.'"),

T("nausea_and_vomiting", "Do you feel sick?",
 ["Any nausea?", "Have you been sick?", "Do you feel nauseated?",
  "Any vomiting?", "Have you thrown up?", "Do you feel like you're going to be sick?",
  "Any stomach upset?", "Have you kept food down?",
  "Any retching?", "Do you feel queasy?", "Have you vomited at all?",
  "Any sickness with this?", "Is your stomach upset?",
  "Have you brought anything up?", "Any nausea or vomiting?"],
 "'Bit... sick. Not... vomited.'",
 "'A bit queasy, and my stomach feels full and uncomfortable, but I haven't been sick. No "
 "vomiting.'",
 pertinent_negative=True),

T("snoring_and_sleep_apnea", "Do you snore?",
 ["Does anyone say you snore?", "Do you stop breathing in your sleep?",
  "Any sleep apnoea?", "Do you use a CPAP machine at night?",
  "Are you sleepy during the day?", "Has anyone told you that you stop breathing at night?",
  "Do you snore badly?", "Any sleep study in the past?",
  "Do you fall asleep in the day?", "Is your sleep disturbed?",
  "Do you wake up unrefreshed?", "Any diagnosed sleep disorder?",
  "Has your wife mentioned your breathing at night?",
  "Do you snore loudly?", "Any daytime sleepiness?"],
 "'Wife says... I do.'",
 "'My wife says I snore the house down and that I stop breathing sometimes and then give a great "
 "gasp. She's been on at me about it for years. I've never had it looked into.'"),

T("code_status_goals_of_care", "Have you thought about what you'd want if you got sicker?",
 ["What's your code status?", "Do you have an advance directive?",
  "Have you talked about resuscitation?", "Would you want a breathing tube?",
  "Do you have a living will?", "Have you thought about your wishes if things got worse?",
  "Are you for full resuscitation?", "Do you have a DNR?",
  "What would you want if your breathing got worse?",
  "Have you discussed this with your family?", "Who makes decisions for you?",
  "Do you have a healthcare proxy?", "What are your wishes about intensive care?",
  "Would you want everything done?", "Have you got any paperwork about your care?"],
 "'Whatever... you need. Please.'",
 "'I've not thought about it, no. I'd want you to do whatever you need to do. My daughter is "
 "outside, she knows what I'd want. I've not signed anything.'"),
]

GLOBAL_RULES = [
 {"when": "phase is intubated",
  "value": "He is intubated and sedated. He does not respond to your voice and cannot give any "
           "history. Anything you still need has to come from the crew, from his daughter in the "
           "relatives' room, or from the chart.",
  "note": "Prepended to every topic. Corresponds to alertness level 3 in the intubated phase, "
          "which is the only phase in this case at alertness 2 or above."},
]

OUT_OF_SCOPE = [
 {"when": "phase is respiratory_failure",
  "value": "He looks at you, still pulling hard for each breath, and shakes his head without "
           "answering."},
 {"when": None,
  "value": "He frowns and shakes his head between breaths. 'I'm sorry, doctor. I don't know what "
           "you mean by that.'"},
]

AUTHORING_NOTES = {
 "alertness_gating": (
   "Section 10.5. The condition language has no alertness predicate, so alertness is reached "
   "indirectly through the phases that carry it. Only the intubated phase in this case is at "
   "alertness 2 or above, and the global rule names it. If a phase is added later at alertness 2 "
   "or 3 the validator will catch it; do not remove that check."),
 "speech_gating": (
   "Section 10.5 covers alertness and not speech limited by respiratory distress, which is the "
   "commoner problem. This patient is deliberately authored as able to complete a short sentence "
   "on arrival, per the seed, so the arrival phase gets the full answer. What he cannot do is talk "
   "in the respiratory failure phase, so every topic carries a second, clipped answer for that "
   "phase with the pauses marked by ellipses. That is two answers per topic rather than the three "
   "a case with a distressed arrival would need."),
 "diagnosis_disclosure": (
   "Section 10.4. He never names a rhythm, an ejection fraction or heart failure, because he has "
   "never been told any of them and the case turns on the resident finding them. He does describe "
   "his heartbeat in lay terms, which is his own sensation and not a diagnosis, and he does "
   "describe the coronary calcification found on a CT three years ago, which is a past diagnosis "
   "he was given and is entitled to know. He offers the barbecue and the extra beers "
   "spontaneously, framed as a question, because that is how patients volunteer a precipitant, "
   "and it is not an assertion that alcohol caused this."),
 "precipitant_note": (
   "The case authors three plausible contributors and settles none of them: a weekend alcohol "
   "load two days before onset, undiagnosed obstructive sleep apnoea, and a cardiomyopathy that "
   "may be the cause of the arrhythmia or its consequence. A resident who takes a full history "
   "finds all three. Deciding between them is not the emergency department's task and the case "
   "does not score it."),
 "coverage": (
   "Every topic in the section 10.2 minimum list is authored except pregnancy status, which does "
   "not apply to a sixty-eight year old man; a resident who asks gets the out-of-scope response. "
   "Location and radiation of pain are folded into the chest pain topic because the pain being "
   "asked about does not exist, and a denial is the whole content."),
}

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
    'Time of onset?',
    'When did it come on?',
    'Was it sudden or did it build up?',
    'Sudden or gradual onset?',
    'How long have you had this?',
    'When did you start feeling like this?',
    'Where were you when it began?',
    'Roughly what time yesterday, or today, did this start?',
    'How many hours or days has this been going on?',
    'Tell me how it began.',
    'Take me back to when this started.',
    'When did things first go wrong?',
    'Did this start today or before that?',
    'Sorry to ask, but when did this begin?',
    'One more thing. When did this begin?',
    'Can I ask, what time did it start?',
    'One more thing. How long ago did this come on?',
    'Okay, how long ago did this come on?',
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
  'character_of_palpitations': [
    'Describe the heartbeat for me.',
    'What does the heartbeat feel like?',
    'Is the rhythm regular?',
    'Does it feel regular or all over the place?',
    'Fast, skipping, or thumping?',
    'Regular or irregular?',
    'Can you tap out the rhythm on the bed?',
    'Is it a flutter or a pounding?',
    'Does it feel like it misses beats?',
    'Does your heart feel like it is racing?',
    'Tell me what you feel in your chest.',
    'Is it like a bird flapping or a drum beating?',
    'Just so I know, what does the heartbeat feel like?',
    'I need to know, what does the heartbeat feel like?',
    'Can I ask, is the rhythm regular?',
    'Quick one: does it feel regular or all over the place?',
    'Before we go on, does it feel regular or all over the place?',
  ],
  'dyspnea_character': [
    'Describe the breathlessness.',
    'What does the breathing feel like?',
    'Is it hard to breathe in or out?',
    'Character of the dyspnoea?',
    'Character of the dyspnea?',
    'Any wheeze with it?',
    'Is it a tightness or a smothering feeling?',
    'Do you feel you are drowning?',
    'Is it painful to breathe?',
    'Are you breathing fast or just struggling?',
    'Can you finish a sentence?',
    'What does the shortness of breath feel like?',
    'Are you breathless?',
    'Short of breath?',
    'SOB?',
    'Any shortness of breath?',
    'Any difficulty breathing?',
    'Is it hard to breathe?',
    'Any breathing problems?',
    'Do you feel you cannot get your breath?',
    'Dyspnoea?',
    'Dyspnea?',
    'Any trouble with your breathing?',
    'Is your breathing okay?',
    'Are you getting enough air?',
    'Okay, what does the breathing feel like?',
    'Sorry to ask, but is it hard to breathe in or out?',
    'One more thing. Is it hard to breathe in or out?',
    'Okay, character of the dyspnoea?',
    'Just so I know, character of the dyspnoea?',
  ],
  'severity': [
    'Out of ten, how bad is it?',
    'Rate the pain out of ten.',
    'Severity?',
    'On a scale of one to ten?',
    'Is it the worst you have ever had?',
    'Ten being the worst pain imaginable, where are you?',
    'Mild, moderate, or severe?',
    'How much is it bothering you?',
    'Can you score it for me?',
    'Pain score?',
    'Is it bearable?',
    'How intense is it?',
    'Quick one: out of ten, how bad is it?',
    'Before we go on, out of ten, how bad is it?',
    'Just so I know, how severe is it?',
    'Can I ask, on a scale of one to ten?',
    'Sorry to ask, but on a scale of one to ten?',
  ],
  'aggravating_factors': [
    'Anything that brings it on?',
    'Does anything set it off?',
    'Aggravating factors?',
    'Is it worse with movement?',
    'Worse with exertion?',
    'Does anything make it flare up?',
    'Is it worse at any particular time?',
    'What aggravates it?',
    'Does breathing in make it worse?',
    'Does it get worse when you do anything?',
    'One more thing. What makes it worse?',
    'I need to know, anything that brings it on?',
    'Right. Anything that brings it on?',
    'Can I ask, does anything set it off?',
    'Sorry to ask, but does anything set it off?',
  ],
  'relieving_factors': [
    'Relieving factors?',
    'Anything ease it?',
    'Have you taken anything for it?',
    'Did anything you tried make a difference?',
    'What helps?',
    'Is there anything that eases it off?',
    'Any position that helps?',
    'Does oxygen help?',
    'Did painkillers help?',
    'Okay, what makes it better?',
    'Sorry to ask, but does anything help?',
    'One more thing. Does anything help?',
    'Just so I know, relieving factors?',
    'I need to know, relieving factors?',
  ],
  'chest_pain': [
    'Chest pain?',
    'Any cp?',
    'Pain in the chest?',
    'Is your chest hurting?',
    'Any tightness in your chest?',
    'Does your chest hurt at all?',
    'Chest tightness?',
    'Any pain across the chest?',
    'Has there been any chest discomfort?',
    'Any chest pain with this?',
    'Any heaviness on your chest?',
    'Any pain when you breathe in?',
    'c/o chest pain?',
    'Just so I know, any chest pain?',
    'I need to know, any chest pain?',
    'I need to know, pain in the chest?',
    'Before we go on, is your chest hurting?',
    'And is your chest hurting?',
  ],
  'syncope_presyncope': [
    'Have you fainted?',
    'Did you black out?',
    'Syncope?',
    'Any syncope?',
    'Any collapse?',
    'Have you lost consciousness at all?',
    'Have you collapsed?',
    'LOC?',
    'Did you faint or nearly faint?',
    'Have you keeled over?',
    'I need to know, have you fainted?',
    'Right. Have you fainted?',
    'Before we go on, did you black out?',
    'And did you black out?',
    'Before we go on, did you pass out?',
  ],
  'dizziness_lightheadedness': [
    'Dizzy at all?',
    'Lightheaded?',
    'Presyncope?',
    'Do you feel like you might pass out?',
    'Any giddiness?',
    'One more thing. Any dizziness?',
    'Okay, any dizziness?',
    'Right. Do you feel lightheaded?',
    'Quick one: do you feel lightheaded?',
    'Okay, do you feel faint?',
  ],
  'orthopnea': [
    'Orthopnoea?',
    'Can you lie down flat?',
    'Do you have to sit up to breathe?',
    'How many pillows?',
    'Pillows?',
    'Is it worse when you lie down?',
    'Can you lie on your back?',
    'Do you get breathless lying flat?',
    'Do you need to be upright?',
    'Does lying down make the breathing worse?',
    'How do you sleep at night, flat or propped?',
    'Number of pillows at night?',
    'Quick one: can you lie down flat?',
    'Before we go on, can you lie down flat?',
    'I need to know, do you have to sit up to breathe?',
    'Before we go on, how many pillows?',
    'And how many pillows?',
  ],
  'paroxysmal_nocturnal_dyspnea': [
    'Paroxysmal nocturnal dyspnoea?',
    'Paroxysmal nocturnal dyspnea?',
    'Do you wake at night breathless?',
    'Woken up short of breath?',
    'Do you wake up fighting for breath?',
    'Do you have to get up at night to catch your breath?',
    'Any breathlessness waking you?',
    'Nocturnal dyspnoea?',
    'Night-time breathlessness?',
    'Do you sit on the edge of the bed at night to breathe?',
    'Quick one: paroxysmal nocturnal dyspnoea?',
    'And paroxysmal nocturnal dyspnea?',
    'Can I ask, paroxysmal nocturnal dyspnea?',
    'And do you wake up gasping?',
    'Can I ask, do you wake up gasping?',
  ],
  'leg_swelling': [
    'Any ankle swelling?',
    'Ankle oedema?',
    'Ankle edema?',
    'Pedal oedema?',
    'Pedal edema?',
    'Swollen feet?',
    'Leg swelling?',
    'Do your shoes feel tight?',
    'Have your ankles puffed up?',
    'Any edema?',
    'Peripheral oedema?',
    'Any fluid in the legs?',
    'Have your calves swollen?',
    'I need to know, any ankle swelling?',
    'Right. Any ankle swelling?',
    'Before we go on, are your legs swollen?',
    'Quick one: any swelling in your legs?',
    'Before we go on, any swelling in your legs?',
  ],
  'weight_gain': [
    'Any weight gain?',
    'Has your weight gone up?',
    'Weight change?',
    'Recent weight gain?',
    'Have you put on any pounds recently?',
    'Any change in your weight?',
    'Have you been weighing yourself?',
    'Has your weight changed over the last week or two?',
    'Are you heavier than usual?',
    'Any fluid weight?',
    'Okay, any weight gain?',
    'Can I ask, has your weight gone up?',
    'Sorry to ask, but has your weight gone up?',
    'I need to know, weight change?',
    'Right. Weight change?',
  ],
  'exercise_tolerance_baseline': [
    'What is your normal exercise tolerance?',
    'Exercise tolerance?',
    'ET?',
    'Baseline function?',
    'How far can you normally walk?',
    'What can you usually do?',
    'What were you like before this?',
    'Functional baseline?',
    'What is your baseline?',
    'Do you normally get breathless walking?',
    'What is normal for you?',
    'Do you manage your own shopping and housework?',
    'How were you managing before this started?',
    'Are you usually fit and well?',
    'DOE at baseline?',
    'Just so I know, what is your normal exercise tolerance?',
    'I need to know, what is your normal exercise tolerance?',
    'One more thing. Exercise tolerance?',
    'Okay, exercise tolerance?',
    'Right. Baseline function?',
  ],
  'cough_and_sputum': [
    'Cough?',
    'Sputum?',
    'Productive cough?',
    'Is the cough dry or chesty?',
    'Coughing anything up?',
    'Frothy sputum?',
    'Is there anything coming up when you cough?',
    'Any pink froth?',
    'Cough productive?',
    'Have you got a chesty cough?',
    'Quick one: have you been coughing?',
    'Sorry to ask, but are you bringing anything up?',
    'One more thing. Are you bringing anything up?',
    'Just so I know, what colour is the sputum?',
    'I need to know, what colour is the sputum?',
  ],
  'fever_and_chills': [
    'Fever?',
    'Fevers or chills?',
    'Fevers, chills, rigors?',
    'Have you had a temperature?',
    'Any rigors?',
    'Have you felt feverish?',
    'Any shaking chills?',
    'Have you had the shivers?',
    'Temp at home?',
    'Did you measure a temperature?',
    'Can I ask, fevers or chills?',
    'Sorry to ask, but fevers or chills?',
    'I need to know, fevers, chills, rigors?',
    'Right. Fevers, chills, rigors?',
    'Okay, any temperature?',
  ],
  'prior_afib_or_palpitations': [
    'Any history of AF?',
    'Hx of afib?',
    'Have you had atrial fibrillation before?',
    'Have you ever had palpitations before?',
    'Previous AF?',
    'Any previous episodes?',
    'Has anyone said your heart was irregular?',
    'Have you been told you have an irregular heartbeat?',
    'Any history of an irregular pulse?',
    'First time this has happened?',
    'Known AF?',
    'Previous palpitations?',
    'Ever been told you have a fast heart rhythm?',
    'Okay, any history of AF?',
    'Just so I know, any history of AF?',
    'And have you had atrial fibrillation before?',
    'And has this happened before?',
    'Can I ask, has this happened before?',
  ],
  'prior_heart_failure': [
    'Hx of CHF?',
    'Known heart failure?',
    'Have you been told your heart is weak?',
    'Any heart failure?',
    'Has anyone said you have a weak heart?',
    'Have you ever had fluid on the lungs?',
    'Any previous heart problems?',
    'History of cardiac failure?',
    'Has a doctor told you your heart does not pump properly?',
    'Any known cardiomyopathy?',
    'Any history of a weak heart muscle?',
    'Just so I know, any history of heart failure?',
    'I need to know, any history of heart failure?',
    'Right. Known heart failure?',
    'Quick one: known heart failure?',
    'Quick one: have you been told your heart is weak?',
  ],
  'past_medical_history': [
    'Past medical history?',
    'Any medical history?',
    'Any medical problems?',
    'Do you have any health problems?',
    'Any past history?',
    'Do you have any illnesses?',
    'What are you known to have?',
    'Any diagnoses?',
    'Any ongoing health issues?',
    'Are you known to the hospital for anything?',
    'Any history of diabetes, high blood pressure, anything like that?',
    'Medical history?',
    'Can I ask, past medical history?',
    'Sorry to ask, but past medical history?',
    'Right. Any medical history?',
    'Can I ask, any medical problems?',
    'Sorry to ask, but any medical problems?',
  ],
  'past_surgical_history': [
    'PSH?',
    'Past surgical history?',
    'Any operations?',
    'Any surgery?',
    'Ever had surgery?',
    'Surgical history?',
    'Any operations in the past?',
    'Have you been under the knife?',
    'Any previous surgeries?',
    'Ever been operated on?',
    'Have you had anything done surgically?',
    'Okay, past surgical history?',
    'Just so I know, past surgical history?',
    'Sorry to ask, but any operations?',
    'One more thing. Any operations?',
    'Right. Ever had surgery?',
  ],
  'current_medications': [
    'What meds are you on?',
    'Medications?',
    'Current medications?',
    'What do you take?',
    'Any regular medications?',
    'List your medications.',
    'Any regular meds?',
    'Do you take anything regularly?',
    'Any medicines at home?',
    'Any OTC medicines?',
    'What is your medication list?',
    'Do you take any tablets?',
    'Just so I know, what meds are you on?',
    'I need to know, what meds are you on?',
    'Just so I know, current medications?',
    'Before we go on, what do you take?',
    'And what do you take?',
  ],
  'anticoagulant_history_and_bleeding': [
    'Are you on blood thinners?',
    'Anticoagulated?',
    'On anticoagulation?',
    'Any anticoagulant?',
    'On a DOAC?',
    'On warfarin or a DOAC?',
    'Any anticoagulation history?',
    'Ever been on blood thinners?',
    'Do you bleed easily?',
    'Any history of bleeds?',
    'Are you on aspirin or clopidogrel?',
    'Antiplatelets or anticoagulants?',
    'Any bleeding history?',
    'Before we go on, are you on blood thinners?',
    'And are you on blood thinners?',
    'Quick one: anticoagulated?',
    'One more thing. On anticoagulation?',
    'Okay, on anticoagulation?',
  ],
  'medication_adherence': [
    'Have you been taking your meds?',
    'Compliance?',
    'Adherence?',
    'Are you taking them as prescribed?',
    'Did you run out of anything?',
    'Are you up to date with your tablets?',
    'Any missed medications?',
    'Have you been off your tablets?',
    'When did you last take your medication?',
    'Do you take them every day?',
    'Are you compliant with your medications?',
    'Did you stop your water tablet?',
    'Have you been taking everything you should?',
    'Any problems getting your prescriptions?',
    'One more thing. Have you been taking your meds?',
    'Quick one: are you taking them as prescribed?',
    'Before we go on, are you taking them as prescribed?',
    'Sorry to ask, but have you missed any doses?',
    'One more thing. Have you missed any doses?',
  ],
  'allergies': [
    'Allergies?',
    'Allergic to any medications?',
    'Any allergy to antibiotics?',
    'Any reactions to medicines?',
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
  'alcohol_and_binge': [
    'Do you drink?',
    'How much alcohol?',
    'EtOH?',
    'Alcohol history?',
    'Alcohol intake?',
    'Any alcohol?',
    'Units per week?',
    'Have you been drinking heavily?',
    'Did you have a lot to drink recently?',
    'Big weekend?',
    'Any drinking over the weekend?',
    'Are you a drinker?',
    'When did you last have a drink?',
    'Alcohol use?',
    'One more thing. How much alcohol?',
    'And alcohol history?',
    'Can I ask, alcohol history?',
    'And alcohol intake?',
    'Can I ask, alcohol intake?',
  ],
  'caffeine_and_stimulants': [
    'Any caffeine?',
    'How much coffee?',
    'Energy drinks?',
    'Any stimulants?',
    'Do you take anything to keep you going?',
    'Any cold and flu tablets?',
    'Any diet pills?',
    'Do you use cocaine or amphetamines?',
    'Any recreational stimulants?',
    'Any pre-workout supplements?',
    'Have you taken any uppers?',
    'Any pseudoephedrine?',
    'Before we go on, how much coffee?',
    'And how much coffee?',
    'Before we go on, energy drinks?',
    'Okay, any stimulants?',
    'Just so I know, any stimulants?',
  ],
  'thyroid_symptoms': [
    'Thyroid history?',
    'Thyroid?',
    'Any thyroid disease?',
    'Are you on thyroxine?',
    'Have you lost weight without trying?',
    'Any change in your neck?',
    'Any goitre?',
    'Overactive thyroid?',
    'Any weight loss or feeling hot?',
    'Have you been told your thyroid is overactive?',
    'Just so I know, any thyroid problems?',
    'I need to know, any thyroid problems?',
    'Can I ask, thyroid history?',
    'Sorry to ask, but thyroid history?',
    'Right. Any thyroid disease?',
  ],
  'social_history_smoking': [
    'Smoker?',
    'Smoking history?',
    'Tobacco?',
    'tob?',
    'Any smoking?',
    'Ever smoked?',
    'Pack years?',
    'Have you ever been a smoker?',
    'Cigarettes?',
    'When did you quit?',
    'Just so I know, smoking history?',
    'Sorry to ask, but how many a day?',
    'One more thing. How many a day?',
    'Just so I know, are you a smoker?',
    'I need to know, are you a smoker?',
  ],
  'family_history': [
    'Family history?',
    'FHx?',
    'Any family history?',
    'Any family history of heart disease?',
    'Did anyone in your family have heart trouble?',
    'Any relatives with heart problems?',
    'Did your parents have heart disease?',
    'Any family history of illness?',
    'Is there anything that runs in your family?',
    'Family history of cardiac disease?',
    'Before we go on, family history?',
    'Quick one: any family history?',
    'Before we go on, any family history?',
    'And any heart problems in the family?',
    'Can I ask, any heart problems in the family?',
  ],
  'last_oral_intake': [
    'Last oral intake?',
    'Last PO intake?',
    'last PO',
    'When did you last drink?',
    'NPO since when?',
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
  'recent_illness_or_sick_contacts': [
    'Any recent infection?',
    'Recent cold or flu?',
    'Have you had a bug recently?',
    'Any coughs or colds lately?',
    'Any viral illness recently?',
    'Any recent infections?',
    'Quick one: have you been unwell recently?',
    'Before we go on, have you been unwell recently?',
    'One more thing. Any recent illness?',
    'Okay, any recent illness?',
    'One more thing. Any recent infection?',
  ],
  'travel_immobility_surgery': [
    'Any long flights?',
    'Have you been immobile?',
    'Any recent surgery?',
    'Any long journeys recently?',
    'Been sitting still for long periods?',
    'Have you been bedbound?',
    'Any recent operations?',
    'Recent travel, surgery, or immobility?',
    'Have you been laid up recently?',
    'Any recent hospital stays?',
    'Been abroad?',
    'Right. Any recent travel?',
    'Quick one: any recent travel?',
    'Right. Any long flights?',
    'Quick one: any long flights?',
    'I need to know, have you been immobile?',
  ],
  'calf_pain_or_asymmetry': [
    'Calf tenderness?',
    'Is one calf bigger?',
    'Any pain in the back of your leg?',
    'Are your calves sore?',
    'Any leg pain?',
    'Any swelling in one leg only?',
    'Any signs of a DVT?',
    'Any unilateral leg swelling?',
    'Any pain when you press your calf?',
    'One leg worse than the other?',
    'One more thing. Any calf pain?',
    'Can I ask, is one leg more swollen than the other?',
    'Sorry to ask, but is one leg more swollen than the other?',
    'And any pain in your calves?',
    'Can I ask, any pain in your calves?',
  ],
  'urine_output': [
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
    'Just so I know, are you passing urine?',
    'I need to know, how much urine?',
    'Right. How much urine?',
    'I need to know, passing water okay?',
    'Right. Passing water okay?',
  ],
  'nausea_and_vomiting': [
    'N/V?',
    'Nausea or vomiting?',
    'Have you vomited?',
    'Feeling queasy?',
    'Been throwing up?',
    'How many times have you vomited?',
    'Any sickness?',
    'Before we go on, nausea or vomiting?',
    'And nausea or vomiting?',
    'Just so I know, have you been sick?',
    'Okay, have you thrown up?',
    'Just so I know, have you thrown up?',
  ],
  'snoring_and_sleep_apnea': [
    'Any sleep apnea?',
    'OSA?',
    'Has anyone said you snore?',
    'Do you use a CPAP machine?',
    'Are you tired during the day?',
    'Sleep apnoea history?',
    'Has your partner noticed you stop breathing at night?',
    'Any obstructive sleep apnoea?',
    'Right. Any sleep apnoea?',
    'Quick one: any sleep apnoea?',
    'Can I ask, any sleep apnea?',
    'Can I ask, do you stop breathing in your sleep?',
    'Sorry to ask, but do you stop breathing in your sleep?',
  ],
  'code_status_goals_of_care': [
    'Code status?',
    'Have you thought about resuscitation?',
    'What would you want if things got worse?',
    'Any wishes about treatment?',
    'Full code?',
    'Have you discussed ceilings of care?',
    'Any DNR in place?',
    'What matters most to you if this gets serious?',
    'Goals of care?',
    'Have you ever talked about what you would want in an emergency?',
    'If your heart stopped, what would you want us to do?',
    'Is there a DNACPR?',
    'Okay, have you thought about resuscitation?',
    'Just so I know, have you thought about resuscitation?',
    'Okay, do you have an advance directive?',
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
  'Any change in your bowel habit?',
  'Any diarrhoea at all?',
  'Any pain in your tummy?',
  'Have you had piles?',
  'Any black stools?',
  'Do you get up at night to pass water?',
  'Any blood in your urine?',
  'Any trouble with your prostate?',
  'Any burning when you pass urine?',
  'Any kidney stones in the past?',
  'When was your last smear test?',
  'Any headaches at all?',
  'Any seizures or fits?',
  'Any weakness in your arms or legs?',
  'Any pins and needles?',
  'Any problems with your speech?',
  'Any trouble with your memory?',
  'Any double vision?',
  'Have you ever had a stroke?',
  'Any migraines?',
  'Any pain in your hands?',
  'Any pain in your hips?',
  'Any arthritis?',
  'Have you broken any bones?',
  'Any neck pain?',
  'Any ringing or buzzing in your ears?',
  'Any earache?',
  'Do you wear glasses or contact lenses?',
  'Any blurred vision?',
  'When did you last have your eyes tested?',
  'Any sinus trouble?',
  'Any rash on your skin?',
  'Any itching?',
  'Any moles that have changed?',
  'When did you last see the dentist?',
  'Any mouth ulcers?',
  'Any lumps or bumps anywhere?',
  'Any excessive thirst?',
  'Have you been feeling low in mood?',
  'Any anxiety or panic attacks?',
  'When was your last tetanus?',
  'Have you had the covid vaccine?',
  'Have you ever received blood?',
  'Do you have a blood donor card?',
  'Who is your GP?',
  'Do you have health insurance?',
  'Have you got your NHS number?',
  'Do you have a pharmacy you usually use?',
  'Is there anyone we should call for you?',
  'Who is your next of kin?',
  'Do you have any pets at home?',
  'What do you do for a living?',
  'What did you do before you retired?',
  'Did you come in by ambulance?',
  'Is anyone here with you?',
  'How did you get here today?',
  'Is it raining outside?',
  'Do you have children?',
  'How many kids do you have?',
  'Where do you live?',
  'Do you watch much television?',
  'What do you do to relax?',
  'Do you have a garden?',
  'Are you comfortable on that trolley?',
  'Would you like a blanket?',
  'Can I get you anything?',
  'What is your date of birth?',
  'Can you confirm your name for me?',
  'What is your address?',
  'Do you know why you are here?',
  'Is it okay if the students watch?',
  'Would you prefer a female doctor?',
  'Have you been waiting long?',
  'Is there anything you would like to ask me?',
  'What year are you in at university?',
  'Do you get on with your flatmates?',
  'How much does it cost to park here?',
  'Who is the prime minister?',
  'What is the date today?',
]
for _t in TOPICS:
    if EXPANDED.get(_t['topic']):
        _t['expanded_variants'] = list(EXPANDED[_t['topic']])
        _t['variants_provenance'] = "Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py in Sep 2026. The added phrasings were written by an AI assistant, not by a physician, and mix lay paraphrase, clinical shorthand and conversational forms. Every sixth new phrasing was withheld into the pack's tuning set rather than added here."
# ---- END EXPANDED VARIANTS ----

# ---- ECHO AND FACTS (generated, do not edit by hand) ----
# Written by catalog/author_interview_facts.py (design 10.7). A fact's value restates part
# of the topic's answer for a follow-up; it adds nothing the paragraph does not say.
ECHO = {
 "onset": "when it started",
 "timing_progression": "whether it's getting worse",
 "character_of_palpitations": "what the racing feels like",
 "dyspnea_character": "the breathing",
 "severity": "how bad it is",
 "aggravating_factors": "what makes it worse",
 "relieving_factors": "what helps",
 "chest_pain": "chest pain",
 "syncope_presyncope": "whether I've passed out",
 "dizziness_lightheadedness": "feeling dizzy",
 "orthopnea": "lying flat",
 "paroxysmal_nocturnal_dyspnea": "waking up breathless",
 "leg_swelling": "my legs swelling",
 "weight_gain": "my weight",
 "exercise_tolerance_baseline": "what I could do before",
 "cough_and_sputum": "a cough",
 "fever_and_chills": "a temperature",
 "prior_afib_or_palpitations": "whether it's happened before",
 "prior_heart_failure": "heart failure",
 "past_medical_history": "my medical history",
 "past_surgical_history": "operations",
 "current_medications": "my tablets",
 "anticoagulant_history_and_bleeding": "blood thinners",
 "medication_adherence": "whether I take them",
 "allergies": "allergies",
 "alcohol_and_binge": "drink",
 "caffeine_and_stimulants": "coffee and that",
 "thyroid_symptoms": "my thyroid",
 "social_history_smoking": "smoking",
 "family_history": "the family",
 "last_oral_intake": "when I last ate",
 "recent_illness_or_sick_contacts": "whether I've been unwell",
 "travel_immobility_surgery": "travelling",
 "calf_pain_or_asymmetry": "my calves",
 "urine_output": "passing water",
 "nausea_and_vomiting": "feeling sick",
 "snoring_and_sleep_apnea": "snoring",
 "code_status_goals_of_care": "what I'd want if it got worse"
}
FACTS = {
 "onset": [
  {
   "id": "time",
   "asks": [
    "what time",
    "what time exactly",
    "when exactly",
    "roughly what time",
    "how long ago"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Three... yesterday.'"
    },
    {
     "when": None,
     "value": "'About three o'clock yesterday afternoon.'"
    }
   ],
   "restate": True
  },
  {
   "id": "how",
   "asks": [
    "how did it start",
    "sudden or gradual",
    "what were you doing",
    "did it come on suddenly",
    "what brought it on"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Sudden. Watching... telly.'"
    },
    {
     "when": None,
     "value": "'All at once. I was sat watching the television and it just started, like something turned over in my chest.'"
    }
   ]
  },
  {
   "id": "breathing_after",
   "asks": [
    "when did the breathing start",
    "did the breathing come at the same time",
    "which came first",
    "and the breathing"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Breathing... later.'"
    },
    {
     "when": None,
     "value": "'The breathing came on after, later in the evening. The heart was first.'"
    }
   ]
  }
 ],
 "character_of_palpitations": [
  {
   "id": "rhythm",
   "asks": [
    "regular or irregular",
    "is it regular",
    "does it keep time",
    "steady or all over the place"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'All over... the place.'"
    },
    {
     "when": None,
     "value": "'It doesn't keep any kind of time. It just goes and goes and then gives a big thump and carries on.'"
    }
   ],
   "restate": True
  },
  {
   "id": "where_felt",
   "asks": [
    "where do you feel it",
    "can you feel it in your neck",
    "where in your chest",
    "do you feel it in your throat"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Throat.'"
    },
    {
     "when": None,
     "value": "'In my chest, and I can feel it in my throat too.'"
    }
   ]
  }
 ],
 "dyspnea_character": [
  {
   "id": "sensation",
   "asks": [
    "what does it feel like",
    "tight or heavy",
    "is it a tightness",
    "can you get a full breath"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Can't... get enough.'"
    },
    {
     "when": None,
     "value": "'I can't get a full breath. It's like there's a weight on me and I only get half of what I need each time.'"
    }
   ],
   "restate": True
  },
  {
   "id": "effort",
   "asks": [
    "are you breathing fast",
    "why are you breathing so fast",
    "are you tired from it",
    "is it tiring"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Exhausted.'"
    },
    {
     "when": None,
     "value": "'I have to keep going faster to make up for it. I'm exhausted from it.'"
    }
   ]
  }
 ],
 "chest_pain": [
  {
   "id": "pain",
   "asks": [
    "any pain at all",
    "is it sore",
    "does it hurt",
    "any discomfort"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'No... pain.'"
    },
    {
     "when": None,
     "value": "'No, no pain. It's not sore. I can feel it thumping and I can feel that I can't breathe, but there's no pain to it.'"
    }
   ],
   "restate": True
  },
  {
   "id": "arm_jaw",
   "asks": [
    "anything in your arm",
    "does it go to your jaw",
    "any pain in your arm or jaw",
    "any radiation"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Nothing... arm.'"
    },
    {
     "when": None,
     "value": "'Nothing in my arm, nothing in my jaw.'"
    }
   ]
  }
 ],
 "current_medications": [
  {
   "id": "list",
   "asks": [
    "what are they",
    "which tablets",
    "name them",
    "what exactly do you take"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Blood pressure... statin... metformin.'"
    },
    {
     "when": None,
     "value": "'A blood pressure tablet, lisinopril I think, twenty milligrams. A statin at night, atorvastatin. And metformin twice a day.'"
    }
   ],
   "restate": True
  },
  {
   "id": "doses",
   "asks": [
    "what dose",
    "how much of each",
    "what strength",
    "how many milligrams"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Twenty... the pressure one.'"
    },
    {
     "when": None,
     "value": "'The lisinopril is twenty milligrams. The metformin is twice a day. I couldn't tell you the statin dose.'"
    }
   ]
  },
  {
   "id": "anything_else",
   "asks": [
    "anything else at all",
    "any inhalers",
    "anything over the counter",
    "any other tablets"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'That's... it.'"
    },
    {
     "when": None,
     "value": "'That's the lot. Nothing else, no inhalers, nothing from the chemist.'"
    }
   ]
  }
 ],
 "past_medical_history": [
  {
   "id": "conditions",
   "asks": [
    "what conditions",
    "which problems",
    "what have you got",
    "blood pressure or diabetes"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Blood pressure. Sugar.'"
    },
    {
     "when": None,
     "value": "'High blood pressure and diabetes, both for years.'"
    }
   ],
   "restate": True
  },
  {
   "id": "heart_scan",
   "asks": [
    "what about your heart",
    "tell me about the scan",
    "the furring up",
    "what did the CT show",
    "any heart problems"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Scan... arteries. Statin.'"
    },
    {
     "when": None,
     "value": "'They found some furring up in my heart arteries on a CT scan three years ago. They said it wasn't bad enough to do anything about and just put me on a statin.'"
    }
   ]
  }
 ],
 "alcohol_and_binge": [
  {
   "id": "usual",
   "asks": [
    "how much normally",
    "what do you usually drink",
    "during the week",
    "how many a week"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Few beers. Weekend.'"
    },
    {
     "when": None,
     "value": "'Two or three beers at the weekend, that's all, and nothing during the week.'"
    }
   ],
   "restate": True
  },
  {
   "id": "saturday",
   "asks": [
    "what about saturday",
    "the barbecue",
    "how many on saturday",
    "more than usual recently",
    "any binge"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'Saturday... four or five.'"
    },
    {
     "when": None,
     "value": "'I had more than that on Saturday. We had a barbecue for my grandson's birthday and I'd say I had four or five over the afternoon.'"
    }
   ]
  }
 ],
 "anticoagulant_history_and_bleeding": [
  {
   "id": "thinners",
   "asks": [
    "any blood thinner",
    "warfarin or anything",
    "aspirin",
    "any antiplatelet"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'No. Nothing... like that.'"
    },
    {
     "when": None,
     "value": "'No. I've never been on a blood thinner and I don't even take aspirin.'"
    }
   ],
   "restate": True
  },
  {
   "id": "bleeding",
   "asks": [
    "any bleeding",
    "ever had a bleed",
    "any ulcers",
    "any falls"
   ],
   "value": [
    {
     "when": "phase is respiratory_failure",
     "value": "'No bleeds.'"
    },
    {
     "when": None,
     "value": "'I've never had a bleed, never had an ulcer, and I haven't had a fall.'"
    }
   ]
  }
 ]
}
for _t in TOPICS:
    if _t['topic'] in ECHO: _t['echo'] = ECHO[_t['topic']]
    if _t['topic'] in FACTS: _t['facts'] = FACTS[_t['topic']]
# ---- END ECHO AND FACTS ----
