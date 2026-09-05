"""Shared phrasings for interview topics, keyed by concept.

Author-time content, not runtime code. `expand_interview_variants.py` reads this
file, maps each case pack's topics onto these concepts, and writes the phrasings into
the pack's own variant bank. Nothing here is loaded by the simulator.

Why a shared library: the three packs ask about the same forty-odd things in the
same forty-odd ways, and a resident who types "pmh?" at one patient types it at all
of them. Writing the phrasings once, in every register, and mapping them per pack is
what makes the banks consistent and what makes the next pack cheap.

Registers, deliberately mixed inside each list:
  - lay paraphrases, the register the original banks were written in
  - clinical shorthand and abbreviations as residents actually type them
    (pmh, psh, meds, nkda, sob, doe, pnd, cp, n/v, lmp, fhx, shx, etoh, uop)
  - imperatives and fragments ("tell me about", "allergies?")
  - indirect and conversational forms

PROVENANCE. Written by an AI assistant in September 2026 from the vocabulary of the
existing banks and ordinary emergency-department usage. Not reviewed by a physician.
A phrasing that maps a question to the wrong concept produces a confident wrong
answer, which section 10.6 names as the failure the learner cannot see, so this file
is clinical content and belongs on the review list with the action catalog.

Held out by construction: `expand_interview_variants.py` diverts every Nth phrasing
per topic into the pack's tuning set instead of its bank, and refuses any phrasing
that collides with a held-out evaluation question.
"""

CONCEPTS = {

# ------------------------------------------------------------------ history of the complaint
"onset": [
  "When did this begin?", "What time did it start?", "How long ago did this come on?",
  "Onset?", "Time of onset?", "When did you first feel unwell?", "When did it come on?",
  "Was it sudden or did it build up?", "Sudden or gradual onset?", "How long have you had this?",
  "When did you start feeling like this?", "What were you doing when it started?",
  "Where were you when it began?", "Roughly what time yesterday, or today, did this start?",
  "How many hours or days has this been going on?", "Tell me how it began.",
  "Take me back to when this started.", "Walk me through the start of this.",
  "When did things first go wrong?", "Did this start today or before that?",
],
"timing_progression": [
  "Is it getting worse or better?", "How has it changed since it began?",
  "Constant or does it come and go?", "Intermittent or continuous?", "Progression?",
  "Has it been the same the whole time?", "Is it worse than it was earlier?",
  "Any change over the last few hours?", "Is it easing off at all?", "Getting worse?",
  "Has it settled at any point?", "Has it stayed the same or changed?",
  "Compared with when it started, how is it now?", "Is this the worst it has been?",
  "Does it fluctuate?", "Has it been steadily building?", "Better, worse, or the same?",
  "Any pattern to it through the day?", "Has it let up at all?",
],
"character_palpitations": [
  "Describe the heartbeat for me.", "What does the heartbeat feel like?",
  "Is the rhythm regular?", "Does it feel regular or all over the place?",
  "Fast, skipping, or thumping?", "Character of the palpitations?", "Regular or irregular?",
  "Can you tap out the rhythm on the bed?", "Is it a flutter or a pounding?",
  "Does it feel like it misses beats?", "Does your heart feel like it is racing?",
  "How would you describe the palpitations?", "Is it fast and steady or fast and chaotic?",
  "Tell me what you feel in your chest.", "Is it like a bird flapping or a drum beating?",
],
"character_dyspnea": [
  "Describe the breathlessness.", "What does the breathing feel like?",
  "Is it hard to breathe in or out?", "Character of the dyspnoea?", "Character of the dyspnea?",
  "Does it feel tight or like you cannot get enough air?", "Any wheeze with it?",
  "Is it a tightness or a smothering feeling?", "Do you feel you are drowning?",
  "Is it painful to breathe?", "Are you breathing fast or just struggling?",
  "Tell me about the shortness of breath.", "Is it worse with talking?",
  "Can you finish a sentence?", "What does the shortness of breath feel like?",
],
"character_general": [
  "Describe what you are feeling.", "What does it feel like?", "Tell me about the symptoms.",
  "How would you describe it?", "Character of the symptoms?", "What is the main thing bothering you?",
  "What sort of feeling is it?", "Is it an ache, a pain, or something else?",
  "Can you put it into words for me?", "What does it feel like in your body?",
  "Tell me more about how you feel.", "Describe the discomfort.",
],
"location_pain": [
  "Where is the pain?", "Show me where it hurts.", "Point to where it hurts.",
  "Location of the pain?", "Where exactly is it?", "Is it in one place or all over?",
  "Where do you feel it most?", "Which part of you hurts?", "Is it your arms, your legs, or everywhere?",
  "Can you localise the pain?", "Where is it worst?", "Is the pain in your muscles?",
  "Are your legs the worst of it?", "Where does it hurt right now?",
],
"radiation_pain": [
  "Does the pain move anywhere?", "Does it spread?", "Does it go anywhere else?",
  "Radiation?", "Does the pain travel?", "Does it go into your arm or jaw?",
  "Does it go through to your back?", "Any radiation of the pain?", "Does it stay put or move around?",
  "Does the pain shoot anywhere?", "Is it spreading from where it started?",
],
"severity": [
  "Out of ten, how bad is it?", "Rate the pain out of ten.", "Severity?", "How severe is it?",
  "On a scale of one to ten?", "Is it the worst you have ever had?", "How bad is it right now?",
  "Ten being the worst pain imaginable, where are you?", "Mild, moderate, or severe?",
  "How much is it bothering you?", "Can you score it for me?", "Pain score?",
  "How bad on a scale?", "Is it bearable?", "How intense is it?",
],
"aggravating": [
  "What makes it worse?", "Anything that brings it on?", "Does anything set it off?",
  "Aggravating factors?", "Is it worse with movement?", "Worse with exertion?",
  "Does walking make it worse?", "Does lying down make it worse?", "What triggers it?",
  "Does anything make it flare up?", "Is it worse at any particular time?", "What aggravates it?",
  "Does breathing in make it worse?", "Does it get worse when you do anything?",
],
"relieving": [
  "What makes it better?", "Does anything help?", "Relieving factors?", "Anything ease it?",
  "Does resting help?", "Does sitting up help?", "Have you taken anything for it?",
  "Did anything you tried make a difference?", "What helps?", "Does it settle with rest?",
  "Is there anything that eases it off?", "Any position that helps?",
  "Does oxygen help?", "Did painkillers help?",
],
"aggravating_relieving": [
  "What makes it better or worse?", "Anything make it better or worse?",
  "Aggravating or relieving factors?", "Does anything help or make it worse?",
  "What eases it and what sets it off?", "Does movement change it?", "Does position change it?",
  "Have you found anything that helps?", "Is there anything that makes it flare?",
  "Does anything you do change it?", "Does lying still help?", "What have you tried for it?",
],

# ------------------------------------------------------------------ cardiorespiratory
"chest_pain": [
  "Any chest pain?", "Chest pain?", "cp?", "Any cp?", "Pain in the chest?",
  "Is your chest hurting?", "Any tightness in your chest?", "Any pressure in the chest?",
  "Does your chest hurt at all?", "Chest tightness?", "Any pain across the chest?",
  "Has there been any chest discomfort?", "Any chest pain with this?", "Is there pain in your chest?",
  "Any heaviness on your chest?", "Any pain when you breathe in?", "c/o chest pain?",
],
"palpitations": [
  "Palpitations?", "Any palpitations?", "Is your heart racing?", "Heart racing at all?",
  "Does your heart feel like it is skipping?", "Any fluttering in the chest?",
  "Have you felt your heart beating fast?", "Any awareness of your heartbeat?",
  "Is your heart thumping?", "Any irregular heartbeat?", "Does your heart feel odd?",
  "Have you noticed your pulse racing?", "Any pounding in your chest?",
],
"syncope": [
  "Have you fainted?", "Did you black out?", "Syncope?", "Any syncope?", "Any collapse?",
  "Did you pass out?", "Have you lost consciousness at all?", "Any blackouts?",
  "Did you go down at any point?", "Have you collapsed?", "LOC?", "Any loss of consciousness?",
  "Did you faint or nearly faint?", "Have you keeled over?", "Any funny turns?",
],
"dizziness": [
  "Any dizziness?", "Dizzy at all?", "Do you feel lightheaded?", "Lightheaded?", "Presyncope?",
  "Do you feel faint?", "Have you felt woozy?", "Any spinning sensation?", "Do you feel like you might pass out?",
  "Any giddiness?", "Is the room spinning?", "Do you feel unsteady?", "Any near-fainting?",
],
"syncope_dizziness": [
  "Any dizziness or fainting?", "Have you felt faint or passed out?", "Dizzy or lightheaded at all?",
  "Syncope or presyncope?", "Any blackouts or dizzy spells?", "Did you collapse or feel like you would?",
  "Have you lost consciousness or felt close to it?", "Any funny turns or fainting?",
  "Have you felt woozy or blacked out?", "Any loss of consciousness or lightheadedness?",
  "Do you feel like you might pass out?", "Any giddiness or collapse?",
],
"orthopnea": [
  "Orthopnoea?", "Orthopnea?", "Can you lie down flat?", "Do you have to sit up to breathe?",
  "How many pillows?", "Pillows?", "Do you sleep propped up?", "Is it worse when you lie down?",
  "Can you lie on your back?", "Do you sleep in a chair?", "Do you get breathless lying flat?",
  "Do you need to be upright?", "Does lying down make the breathing worse?", "Are you sleeping sitting up?",
  "How do you sleep at night, flat or propped?", "Number of pillows at night?",
],
"pnd": [
  "PND?", "Any PND?", "Paroxysmal nocturnal dyspnoea?", "Paroxysmal nocturnal dyspnea?",
  "Do you wake up gasping?", "Do you wake at night breathless?", "Woken up short of breath?",
  "Do you wake up fighting for breath?", "Ever wake in the night unable to breathe?",
  "Do you have to get up at night to catch your breath?", "Any breathlessness waking you?",
  "Do you wake up choking?", "Nocturnal dyspnoea?", "Night-time breathlessness?",
  "Do you sit on the edge of the bed at night to breathe?",
],
"leg_swelling": [
  "Any ankle swelling?", "Ankle oedema?", "Ankle edema?", "Pedal oedema?", "Pedal edema?",
  "Are your legs swollen?", "Swollen feet?", "Any swelling in your legs?", "Leg swelling?",
  "Do your shoes feel tight?", "Have your ankles puffed up?", "Any oedema?", "Any edema?",
  "Are your legs bigger than usual?", "Do your socks leave marks?", "Peripheral oedema?",
  "Any fluid in the legs?", "Have your calves swollen?",
],
"weight_gain": [
  "Any weight gain?", "Has your weight gone up?", "Weight change?", "Recent weight gain?",
  "Have you put on any pounds recently?", "Do your clothes feel tighter?", "Any change in your weight?",
  "Have you been weighing yourself?", "Has your weight changed over the last week or two?",
  "Have you gained weight?", "Are you heavier than usual?", "Any fluid weight?",
],
"functional_baseline": [
  "What is your normal exercise tolerance?", "Exercise tolerance?", "ET?", "Baseline function?",
  "How far can you normally walk?", "Can you normally manage stairs?", "What can you usually do?",
  "How active are you normally?", "What were you like before this?", "Functional baseline?",
  "What is your baseline?", "Do you normally get breathless walking?", "How far could you walk last week?",
  "What is normal for you?", "Do you manage your own shopping and housework?",
  "How were you managing before this started?", "Are you usually fit and well?",
  "DOE at baseline?", "SOB on exertion normally?",
],
"cough_sputum": [
  "Any cough?", "Cough?", "Have you been coughing?", "Are you bringing anything up?",
  "Any phlegm?", "Sputum?", "What colour is the sputum?", "Productive cough?",
  "Is the cough dry or chesty?", "Coughing anything up?", "Any mucus?", "Frothy sputum?",
  "Is there anything coming up when you cough?", "Any pink froth?", "Cough productive?",
  "Have you got a chesty cough?",
],
"hemoptysis": [
  "Haemoptysis?", "Hemoptysis?", "Any blood in the sputum?", "Coughed up blood?",
  "Any blood when you cough?", "Have you coughed up any blood?", "Blood in the phlegm?",
  "Any blood-streaked sputum?", "Any blood coming up?", "Have you seen blood when coughing?",
  "Is there blood in what you cough up?",
],
"breathing_sob": [
  "Are you breathless?", "Short of breath?", "SOB?", "Any SOB?", "Any shortness of breath?",
  "Any difficulty breathing?", "Is it hard to breathe?", "Are you struggling to breathe?",
  "Any breathing problems?", "Do you feel you cannot get your breath?", "Breathless at all?",
  "Dyspnoea?", "Dyspnea?", "Any trouble with your breathing?", "Is your breathing okay?",
  "Are you getting enough air?",
],
"fever_chills": [
  "Any fever?", "Fever?", "Fevers or chills?", "Fevers, chills, rigors?", "Any temperature?",
  "Have you had a temperature?", "Any rigors?", "Have you been shivering?", "Any sweats?",
  "Night sweats?", "Do you feel hot and cold?", "Have you felt feverish?", "Any shaking chills?",
  "Have you had the shivers?", "Temp at home?", "Did you measure a temperature?",
  "Have you been burning up?",
],
"cold_extremities": [
  "Are your hands cold?", "Cold hands and feet?", "Are your feet cold?", "Do your hands feel icy?",
  "Cold peripheries?", "Have your hands and feet gone cold?", "Do you feel cold in your hands?",
  "Are your extremities cold?", "Are your fingers cold?", "Have your hands changed colour?",
  "Do your feet feel like ice?", "Cold to the touch?",
],

# ------------------------------------------------------------------ past history
"prior_afib": [
  "Any history of AF?", "Hx of afib?", "any hx of afib", "Have you had atrial fibrillation before?",
  "Has this happened before?", "Have you ever had palpitations before?", "Previous AF?",
  "Has your heart ever raced like this before?", "Any previous episodes?", "Has anyone said your heart was irregular?",
  "Have you been told you have an irregular heartbeat?", "Any history of an irregular pulse?",
  "First time this has happened?", "Is this new for you?", "Have you had this before?",
  "Known AF?", "Previous palpitations?", "Ever been told you have a fast heart rhythm?",
],
"prior_hf": [
  "Any history of heart failure?", "Hx of CHF?", "Known heart failure?", "Have you been told your heart is weak?",
  "Any heart failure?", "Has anyone said you have a weak heart?", "Do you have a heart condition?",
  "Have you ever had fluid on the lungs?", "Any previous heart problems?", "History of cardiac failure?",
  "Has a doctor told you your heart does not pump properly?", "Any known cardiomyopathy?",
  "Have you had an echo before?", "Any history of a weak heart muscle?", "Do you have heart failure?",
],
"pmh": [
  "PMH?", "pmh", "Past medical history?", "Any medical history?", "Any medical problems?",
  "What conditions do you have?", "Do you have any health problems?", "Any past history?",
  "What is your medical history?", "Any long-term conditions?", "Do you have any illnesses?",
  "Any chronic conditions?", "What are you known to have?", "Any diagnoses?", "Any ongoing health issues?",
  "Are you known to the hospital for anything?", "Do you see a doctor for anything regularly?",
  "Any history of diabetes, high blood pressure, anything like that?", "Medical history?",
],
"psh": [
  "PSH?", "psh", "Past surgical history?", "Any operations?", "Any surgery?", "Ever had surgery?",
  "Have you had any procedures?", "Surgical history?", "Any operations in the past?",
  "Have you been under the knife?", "Any previous surgeries?", "Ever been operated on?",
  "Any history of surgery?", "Have you had anything done surgically?",
],
"meds": [
  "Meds?", "meds", "What meds are you on?", "Medications?", "Current medications?", "What do you take?",
  "Any regular medications?", "What tablets are you on?", "Are you on any medication?",
  "What prescriptions do you have?", "List your medications.", "What pills do you take?",
  "Any regular meds?", "Do you take anything regularly?", "Any medicines at home?",
  "What are you prescribed?", "Any OTC medicines?", "Anything from the chemist?",
  "What is your medication list?", "Do you take any tablets?",
],
"adherence": [
  "Have you been taking your meds?", "Compliance?", "Adherence?", "Are you taking them as prescribed?",
  "Have you missed any doses?", "Did you run out of anything?", "Have you stopped any medication?",
  "Are you up to date with your tablets?", "Any missed medications?", "Have you been off your tablets?",
  "When did you last take your medication?", "Do you take them every day?", "Have you been skipping doses?",
  "Are you compliant with your medications?", "Did you stop your water tablet?",
  "Have you been taking everything you should?", "Any problems getting your prescriptions?",
],
"anticoag": [
  "Are you on blood thinners?", "Anticoagulated?", "On anticoagulation?", "Any anticoagulant?",
  "On a DOAC?", "on doac?", "Are you on warfarin?", "Any apixaban or rivaroxaban?", "On warfarin or a DOAC?",
  "Do you take a blood thinner?", "Any anticoagulation history?", "Ever been on blood thinners?",
  "Any bleeding problems?", "Do you bleed easily?", "Any history of bleeds?", "Ever had a serious bleed?",
  "Are you on aspirin or clopidogrel?", "Antiplatelets or anticoagulants?", "Any bleeding history?",
],
"allergies": [
  "Allergies?", "allergies", "NKDA?", "nkda?", "Any allergies?", "Any drug allergies?",
  "Are you allergic to anything?", "Allergic to any medications?", "Any known allergies?",
  "Any allergy to antibiotics?", "Any reactions to medicines?", "Allergic to penicillin?",
  "Do you have any allergies I should know about?", "What are you allergic to?", "Any adverse drug reactions?",
  "Any medication allergies?", "Drug allergies?", "Any allergies to anything?",
],
"alcohol": [
  "Do you drink?", "How much alcohol?", "EtOH?", "etoh hx", "Alcohol history?", "Alcohol intake?",
  "How much do you drink a week?", "Any alcohol?", "Do you drink alcohol?", "Units per week?",
  "Have you been drinking heavily?", "Any binge drinking?", "Did you have a lot to drink recently?",
  "Big weekend?", "How many drinks a day?", "Any drinking over the weekend?", "Are you a drinker?",
  "When did you last have a drink?", "Alcohol use?",
],
"caffeine_stimulants": [
  "Any caffeine?", "How much coffee?", "Energy drinks?", "Any stimulants?", "Do you take anything to keep you going?",
  "Any decongestants?", "Any cold and flu tablets?", "Any diet pills?", "Do you use cocaine or amphetamines?",
  "Any recreational stimulants?", "How many coffees a day?", "Any pre-workout supplements?",
  "Any stimulant use?", "Have you taken any uppers?", "Any pseudoephedrine?",
],
"thyroid": [
  "Any thyroid problems?", "Thyroid history?", "Thyroid?", "Any thyroid disease?", "Are you on thyroxine?",
  "Do you feel hot all the time?", "Any heat intolerance?", "Have you lost weight without trying?",
  "Any tremor?", "Have you been sweaty and shaky?", "Any change in your neck?", "Any goitre?",
  "Overactive thyroid?", "Any weight loss or feeling hot?", "Have you been told your thyroid is overactive?",
  "Hyperthyroid symptoms?",
],
"smoking": [
  "Do you smoke?", "Smoker?", "Smoking history?", "Tobacco?", "tob?", "Any smoking?",
  "How many a day?", "Ever smoked?", "Pack years?", "Are you a smoker?", "Have you ever been a smoker?",
  "Do you vape?", "Cigarettes?", "When did you quit?", "Any tobacco use?",
],
"smoking_alcohol": [
  "Do you smoke or drink?", "Smoking and alcohol?", "Any smoking or drinking?", "Tobacco and alcohol?",
  "Do you smoke, and how much do you drink?", "Social history, smoking and alcohol?", "EtOH and tobacco?",
  "Are you a smoker or a drinker?", "Any cigarettes or alcohol?", "How much do you smoke and drink?",
  "Smoker? Drinker?", "Any alcohol or tobacco?",
],
"social_history": [
  "Social history?", "SHx?", "shx", "Do you smoke, drink, or use drugs?", "Any drugs, alcohol, smoking?",
  "Tell me about smoking, alcohol and drugs.", "Any recreational drugs?", "Any substance use?",
  "Do you drink or smoke?", "Any alcohol?", "Do you use any drugs?", "Smoking, drinking, drugs?",
  "Tobacco, alcohol, illicit drugs?", "Any drug use at all?", "Do you smoke?",
  "What is your social situation?", "Who do you live with?",
],
"substance_use": [
  "Any recreational drugs?", "Drug use?", "Any illicit drugs?", "Do you use cocaine?",
  "Any street drugs?", "Have you taken anything?", "Any stimulants or cocaine?", "Substance use?",
  "Do you take anything recreational?", "Any drugs at all?", "Any amphetamines or cocaine?",
  "Have you used any drugs recently?", "Any illicit substance use?",
],
"family_history": [
  "Family history?", "FHx?", "fhx", "fhx cardiac", "Any family history?", "Any heart problems in the family?",
  "Any family history of heart disease?", "Did anyone in your family have heart trouble?",
  "Anything run in the family?", "Any relatives with heart problems?", "Any sudden deaths in the family?",
  "Did your parents have heart disease?", "Any family history of illness?", "Any inherited conditions?",
  "Is there anything that runs in your family?", "Family history of cardiac disease?",
],
"last_oral_intake": [
  "When did you last eat?", "Last oral intake?", "Last PO intake?", "last PO", "When did you last drink?",
  "NPO since when?", "Have you eaten today?", "When was your last meal?", "Have you had anything to eat or drink?",
  "Last food or drink?", "Anything to eat or drink today?", "When did you last have something to drink?",
  "Are you eating and drinking?", "Have you kept any fluids down?", "How much have you been drinking?",
  "When did you last eat anything?", "Have you managed any food?",
],
"recent_illness_sick_contacts": [
  "Have you been unwell recently?", "Any recent illness?", "Any recent infection?", "Recent cold or flu?",
  "Anyone at home unwell?", "Any sick contacts?", "Have you had a bug recently?", "Any coughs or colds lately?",
  "Any recent chest infection?", "Has anyone around you been ill?", "Any viral illness recently?",
  "Been poorly in the last few weeks?", "Any recent infections?",
],
"sick_contacts": [
  "Any sick contacts?", "Anyone else unwell?", "Is anyone around you sick?", "Has anyone you live with been ill?",
  "Anyone at home with the same thing?", "Any contact with someone unwell?", "Anyone in your halls been ill?",
  "Has anyone else got this?", "Any friends or flatmates sick?", "Anybody close to you unwell recently?",
  "Any outbreaks where you live?", "Has anyone you know had similar symptoms?",
],
"travel_immobility_surgery": [
  "Any recent travel?", "Any long flights?", "Have you been immobile?", "Any recent surgery?",
  "Any long journeys recently?", "Been sitting still for long periods?", "Any flights or long drives?",
  "Have you been bedbound?", "Any recent operations?", "Recent travel, surgery, or immobility?",
  "Any risk factors for a clot?", "Have you been laid up recently?", "Any recent hospital stays?",
  "Any long-haul travel?", "Been abroad?",
],
"travel": [
  "Any recent travel?", "Been abroad recently?", "Have you travelled?", "Any foreign travel?",
  "Travel history?", "Have you been out of the country?", "Any trips recently?", "Where have you been recently?",
  "Any travel in the last few months?", "Have you been anywhere unusual?", "Any overseas travel?",
  "Been away anywhere?",
],
"calf_pain": [
  "Any calf pain?", "Is one leg more swollen than the other?", "Any pain in your calves?", "Calf tenderness?",
  "Is one calf bigger?", "Any pain in the back of your leg?", "Are your calves sore?", "Any leg pain?",
  "Is one leg red or hot?", "Any swelling in one leg only?", "Any signs of a DVT?", "Any unilateral leg swelling?",
  "Any pain when you press your calf?", "One leg worse than the other?",
],
"urine_output": [
  "Are you passing urine?", "Urine output?", "UOP?", "How much urine?", "Passing water okay?",
  "When did you last pass urine?", "Have you peed today?", "Any drop in your urine?", "Are you peeing less?",
  "How often are you going to the toilet?", "Have you been passing less water?", "Passing much urine?",
  "Any reduction in urine output?", "When did you last go for a wee?", "Are you making urine?",
  "Have you passed water since this started?",
],
"nausea_vomiting": [
  "Any nausea?", "N/V?", "n/v", "Any vomiting?", "Nausea or vomiting?", "Have you been sick?",
  "Have you thrown up?", "Do you feel sick?", "Any retching?", "Have you vomited?", "Feeling queasy?",
  "Been throwing up?", "Any nausea or vomiting?", "Have you brought anything up?", "Do you feel nauseous?",
  "How many times have you vomited?", "Any sickness?",
],
"snoring_osa": [
  "Do you snore?", "Any sleep apnoea?", "Any sleep apnea?", "OSA?", "Do you stop breathing in your sleep?",
  "Has anyone said you snore?", "Do you use a CPAP machine?", "Are you tired during the day?",
  "Do you wake up unrefreshed?", "Any snoring?", "Sleep apnoea history?", "Do you fall asleep in the day?",
  "Has your partner noticed you stop breathing at night?", "Any obstructive sleep apnoea?",
],
"code_status": [
  "Code status?", "Have you thought about resuscitation?", "Do you have an advance directive?",
  "What would you want if things got worse?", "Any wishes about treatment?", "Full code?",
  "Would you want to be resuscitated?", "Have you discussed ceilings of care?", "Any DNR in place?",
  "Do you have a living will?", "What matters most to you if this gets serious?", "Goals of care?",
  "Have you ever talked about what you would want in an emergency?", "Any advance care plan?",
  "If your heart stopped, what would you want us to do?", "Is there a DNACPR?",
],
"abdominal_fullness": [
  "Any bloating?", "Does your stomach feel full?", "Any abdominal swelling?", "Is your belly bigger?",
  "Any tightness in your abdomen?", "Do you feel bloated?", "Is your stomach distended?",
  "Any fullness after eating?", "Has your waistband got tighter?", "Any swelling of the tummy?",
  "Does your abdomen feel tight?", "Any abdominal distension?",
],
"dietary_sodium": [
  "How much salt do you eat?", "Any salty food recently?", "Dietary sodium?", "Salt intake?",
  "Have you eaten a lot of takeaways?", "Any processed food lately?", "Have you been watching your salt?",
  "Any change in your diet?", "What have you been eating?", "Any crisps or salty snacks?",
  "Have you had a lot of salty meals recently?", "Do you add salt to your food?", "Any tinned or ready meals?",
],

# ------------------------------------------------------------------ infection and sepsis
"rash": [
  "Any rash?", "Tell me about the rash.", "Where is the rash?", "When did the rash start?",
  "Does the rash blanch?", "Is the rash spreading?", "Any spots?", "Any marks on your skin?",
  "Describe the rash.", "What does the rash look like?", "Any bruising or spots?", "Any skin changes?",
  "Any purple spots?", "Does the rash fade when pressed?", "Where did the spots start?",
  "Is the rash getting bigger?", "Any new spots?", "Any petechiae?",
],
"headache": [
  "Any headache?", "Headache?", "Does your head hurt?", "Any head pain?", "Is your head sore?",
  "Any pain in your head?", "How bad is the headache?", "Where is the headache?", "Worst headache ever?",
  "Any pressure in your head?", "Have you had a headache with this?", "Is the headache new?",
  "Any pounding in your head?",
],
"neck_stiffness": [
  "Neck stiffness?", "Is your neck stiff?", "Any stiffness in the neck?", "Can you touch your chin to your chest?",
  "Does it hurt to move your neck?", "Any neck pain?", "Meningism?", "Can you bend your neck?",
  "Is your neck sore?", "Any stiff neck?", "Does your neck feel tight?", "Can you look down at your feet?",
  "Is your neck painful to move?", "Any nuchal rigidity?",
],
"photophobia": [
  "Photophobia?", "Do lights hurt your eyes?", "Any photophobia?", "Is the light bothering you?",
  "Are the lights too bright?", "Do you want the lights off?", "Does light hurt?", "Are your eyes sensitive to light?",
  "Is the brightness painful?", "Do bright lights make it worse?", "Any sensitivity to light?",
  "Do you prefer it dark?", "Does looking at the light hurt?",
],
"diarrhoea": [
  "Any diarrhoea?", "Diarrhea?", "Any loose stools?", "Any loose motions?", "Have your bowels been loose?",
  "Any change in your bowels?", "Been to the toilet a lot?", "Any runny stools?", "Any diarrhoea or vomiting?",
  "Have you had the runs?", "Bowels okay?", "Any loose bowel movements?", "How are your bowels?",
],
"abdominal_pain": [
  "Any abdominal pain?", "Any tummy pain?", "Does your belly hurt?", "Any stomach pain?", "Abdo pain?",
  "Any pain in your abdomen?", "Is your stomach sore?", "Any belly ache?", "Any pain in the tummy?",
  "Does it hurt in your stomach?", "Any cramping in your belly?", "Any abdominal tenderness?",
],
"cough_sore_throat": [
  "Any cough or sore throat?", "Sore throat?", "Any cough?", "Any cold symptoms?", "Runny nose or sore throat?",
  "Any coryzal symptoms?", "Did you have a cold first?", "Any URTI symptoms?", "Have you had a cough?",
  "Any throat pain?", "Any flu-like symptoms before this?", "Any sniffles or cough?", "Is your throat sore?",
  "Any cold before this started?",
],
"confusion": [
  "Any confusion?", "Have you felt confused?", "Are you thinking clearly?", "Do you know where you are?",
  "Have you been muddled?", "Any change in your thinking?", "Do you feel foggy?", "Have you been disorientated?",
  "Are you having trouble concentrating?", "Do you know what day it is?", "Any memory problems today?",
  "Have you been making sense to people?", "Any altered mental state?",
],
"joint_pain": [
  "Any joint pain?", "Are your joints sore?", "Any swollen joints?", "Do your knees hurt?", "Arthralgia?",
  "Any pain in the joints?", "Are your joints swollen?", "Any joint swelling?", "Do your joints ache?",
  "Any pain in your knees or ankles?", "Any red or hot joints?", "Muscle or joint pain?",
],
"dysuria_gu": [
  "Any burning when you pee?", "Dysuria?", "Any urinary symptoms?", "Does it sting to pass urine?",
  "Any discharge?", "Any vaginal symptoms?", "Any pain passing water?", "Any frequency or urgency?",
  "Any GU symptoms?", "Any pelvic pain?", "Any pain when urinating?", "Any itching or discharge?",
  "Any trouble with your waterworks?", "Burning on urination?",
],
"menstrual_tampon": [
  "LMP?", "lmp", "Last menstrual period?", "When was your last period?", "Are you on your period?",
  "Do you use tampons?", "Tampon use?", "Any tampon in at the moment?", "When did your last period start?",
  "Are your periods regular?", "Menstrual history?", "Are you menstruating?", "Any tampon left in?",
  "Have you got a tampon in?", "Date of last period?",
],
"pregnancy": [
  "Could you be pregnant?", "Any chance of pregnancy?", "Are you pregnant?", "Pregnancy?",
  "Is there any chance you are pregnant?", "When was your last period, could you be pregnant?",
  "Have you done a pregnancy test?", "Any possibility of pregnancy?", "Are you using contraception?",
  "Is pregnancy possible?", "Could you be expecting?", "Any chance you might be pregnant?",
],
"sexual_history": [
  "Are you sexually active?", "Sexual history?", "Any sexual partners?", "Do you have a partner?",
  "Any new partners recently?", "Any unprotected sex?", "Sexually active?", "Any risk of an STI?",
  "When did you last have sex?", "Any sexual contact recently?", "Do you use protection?",
  "Any history of sexually transmitted infections?",
],
"vaccinations": [
  "Are your vaccinations up to date?", "Vaccination history?", "Vaccines?", "Any immunisations?",
  "Have you had your jabs?", "Immunisation history?", "Have you had the meningitis vaccine?",
  "Are you vaccinated?", "Did you have your school vaccines?", "Are your immunisations current?",
  "Any vaccines recently?", "Have you had all your childhood vaccines?", "Meningococcal vaccine?",
  "Have you been vaccinated against meningitis?",
],
"tick_outdoor": [
  "Any tick bites?", "Any insect bites?", "Have you been hiking or camping?", "Any time outdoors?",
  "Been in the woods recently?", "Any bites?", "Any exposure to ticks?", "Have you been in long grass?",
  "Any outdoor activities recently?", "Any animal exposure?", "Have you been bitten by anything?",
  "Any camping trips?", "Tick exposure?",
],
"recent_antibiotics_healthcare": [
  "Any recent antibiotics?", "Have you seen a doctor recently?", "Any recent hospital visits?",
  "Have you been on antibiotics?", "Any recent healthcare contact?", "Did you see your GP about this?",
  "Have you had any treatment already?", "Any antibiotics in the last few weeks?", "Been to a doctor for this?",
  "Have you taken any antibiotics?", "Any recent prescriptions?", "Did anyone treat you before you came in?",
  "Any recent medical care?",
],
}

# Openers that turn a core phrasing into a conversational one. Applied to a few
# phrasings per topic, not all, because every opener on every phrasing would swamp
# the bank with near-duplicates and bury the terse forms that matter more.
OPENERS = [
  "Can I ask, {q}", "Quick one: {q}", "Just so I know, {q}", "Sorry to ask, but {q}",
  "Before we go on, {q}", "I need to know, {q}", "One more thing. {Q}", "And {q}",
  "Right. {Q}", "Okay, {q}",
]
