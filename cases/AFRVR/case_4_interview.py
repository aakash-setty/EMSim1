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
