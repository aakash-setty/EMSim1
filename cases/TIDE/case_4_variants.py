"""TIDE part 4a: hand-written question phrasings, written 4 November 2026. Questions, not
clinical facts (authoring 8.1). The build adds the shared library's phrasings on top. Variants
are in the learner's register, with the abbreviations a resident types.
"""

SHARED = {
 "onset": {"canonical": "When did this start?", "echo": "when it started", "variants": [
   "When did it begin?", "How long has he been sick?", "How many days has this been going on?",
   "When did you first notice he was unwell?", "When did the fever start?", "How long have you had the cough?",
   "When was he last well?", "Onset?", "How long ago did this start?", "When did you get sick?",
   "Has this been going on for days?", "What day did it start?"]},
 "timing_progression": {"canonical": "Has it been getting worse?", "echo": "whether it's getting worse", "variants": [
   "Is he getting worse?", "How has it changed over the last day?", "Was he this bad yesterday?",
   "When did the breathing get worse?", "Has anything changed since last night?", "Is it worse today?",
   "How quickly has this got worse?", "Was it gradual or sudden?", "Has it been steadily worsening?",
   "Any better at all?", "What changed today?"]},
 "cough_sputum": {"canonical": "Is he coughing anything up?", "echo": "the cough", "variants": [
   "Any cough?", "Is the cough productive?", "What color is the phlegm?", "Any sputum?",
   "What is he bringing up?", "Is there any mucus?", "Dry or wet cough?", "What does the phlegm look like?",
   "Any green or yellow sputum?", "How bad is the cough?", "Productive cough?", "Coughing stuff up?"]},
 "hemoptysis": {"canonical": "Is he coughing up blood?", "echo": "coughing up blood", "variants": [
   "Any blood in the sputum?", "Any hemoptysis?", "Has he coughed up blood?", "Is there blood when he coughs?",
   "Any blood-streaked phlegm?", "Any red in the phlegm?", "Coughing blood?", "Blood in what he coughs up?",
   "Has there been any frank blood?", "Is the sputum bloody?"]},
 "chest_pain": {"canonical": "Does he have any chest pain?", "echo": "the chest pain", "variants": [
   "Any chest pain?", "Does it hurt to breathe?", "Where is the pain?", "Is the pain worse when he breathes in?",
   "Pleuritic pain?", "Any pain in the chest when coughing?", "Is it sharp or dull?", "Any chest tightness?",
   "Does his chest hurt?", "CP?", "Does the pain go anywhere?", "Is the pain on one side?"]},
 "breathing": {"canonical": "How is his breathing?", "echo": "his breathing", "variants": [
   "Is he short of breath?", "When did the breathlessness start?", "Any shortness of breath?", "SOB?",
   "How far could he walk before?", "Can he catch his breath?", "Is he breathless at rest?",
   "Is it hard to breathe?", "Dyspnea?", "Has the breathing got worse?", "Can he finish a sentence?"]},
 "fever_and_chills": {"canonical": "Has he had a fever?", "echo": "the fever", "variants": [
   "Any fevers?", "Any chills or shaking?", "Has he had rigors?", "Did you check his temperature?",
   "How high has the fever been?", "Has he been sweating at night?", "Any sweats?", "Fevers or chills?",
   "Has he been hot and cold?", "Did he take anything for the fever?", "Any shivering?"]},
 "confusion": {"canonical": "Has he been confused?", "echo": "whether he's been confused", "variants": [
   "Is he acting like himself?", "Any confusion?", "Has he been mixed up?", "Is he more sleepy than usual?",
   "Any change in his thinking?", "Has he been disoriented?", "Is this his normal mental state?",
   "Any altered mental status?", "AMS?", "Is he making sense?"]},
 "dizziness_syncope": {"canonical": "Has he fainted or felt lightheaded?", "echo": "feeling faint", "variants": [
   "Any dizziness?", "Has he passed out?", "Any syncope?", "Lightheaded when he stands?", "Did he collapse?",
   "Any falls?", "Has he blacked out?", "Feel faint at all?", "Near fainting?", "Any presyncope?"]},
 "urine_output": {"canonical": "Has he been passing urine?", "echo": "passing urine", "variants": [
   "How much has he peed today?", "When did he last urinate?", "Any change in urine?", "Is he making urine?",
   "Peeing less than usual?", "Urine output?", "Any dark urine?", "When did he last pee?",
   "Has he been to the bathroom today?", "Decreased urination?"]},
 "nausea_vomiting": {"canonical": "Any nausea or vomiting?", "echo": "nausea or vomiting", "variants": [
   "Has he been throwing up?", "Any vomiting?", "Feeling sick to his stomach?", "N/V?", "Any nausea?",
   "Has he kept food down?", "Throwing up at all?", "Any retching?", "Is he nauseous?", "Vomiting?"]},
 "abdominal_pain": {"canonical": "Any belly pain?", "echo": "belly pain", "variants": [
   "Any abdominal pain?", "Does his stomach hurt?", "Any pain in the belly?", "Any tummy pain?",
   "Abdo pain?", "Pain in the upper belly?", "Any cramping?", "Stomach pain?", "Any abdominal discomfort?",
   "Belly tender?"]},
 "diarrhea": {"canonical": "Any diarrhea?", "echo": "diarrhea", "variants": [
   "Any loose stools?", "Has he had the runs?", "Bowel movements normal?", "Diarrhea at all?",
   "Any change in his bowels?", "Watery stools?", "How are his bowels?", "Any GI symptoms?",
   "Has he had diarrhoea?", "Stools okay?"]},
 "headache": {"canonical": "Any headache?", "echo": "a headache", "variants": [
   "Does his head hurt?", "Any head pain?", "Headaches?", "Has he had a headache with the fever?",
   "Any neck stiffness or headache?", "HA?", "Any pain in his head?", "Headache at all?", "Bad headache?",
   "Head pain with the fever?"]},
 "leg_swelling": {"canonical": "Any leg swelling?", "echo": "leg swelling", "variants": [
   "Are his legs swollen?", "Any calf pain?", "Ankle swelling?", "Any swelling in the legs?",
   "Pain in his legs?", "Any edema?", "Calf tenderness?", "Leg pain or swelling?", "Swollen ankles?",
   "Any clots in the legs before?"]},
 "orthopnea": {"canonical": "Is it worse lying flat?", "echo": "lying flat", "variants": [
   "Can he lie flat?", "How many pillows does he sleep on?", "Any orthopnea?", "Does he wake up breathless?",
   "Any PND?", "Is he breathless lying down?", "Worse lying down?", "Does he have to sit up to breathe?",
   "Waking at night short of breath?", "Can he sleep flat?"]},
 "palpitations": {"canonical": "Any palpitations?", "echo": "palpitations", "variants": [
   "Any racing heart?", "Heart pounding?", "Any fluttering in the chest?", "Has his heart been racing?",
   "Irregular heartbeat?", "Palps?", "Any skipped beats?", "Heart fluttering?", "Feel his heart beating fast?",
   "Any heart racing?"]},
 "past_medical_history": {"canonical": "What medical problems does he have?", "echo": "his medical history", "variants": [
   "Any past medical history?", "PMH?", "Does he have any health problems?", "Any chronic illnesses?",
   "Does he have COPD?", "Any lung disease?", "Any heart problems?", "Is he diabetic?", "Any asthma?",
   "Is he immunocompromised?", "Any problems with his immune system?", "Any medical conditions?"]},
 "past_surgical_history": {"canonical": "Has he had any operations?", "echo": "operations", "variants": [
   "Any surgeries?", "PSH?", "Any past surgery?", "Ever had an operation?", "Any procedures before?",
   "Surgical history?", "Has he been operated on?", "Any surgeries in the past?", "Ever had surgery?",
   "Any past operations?"]},
 "current_medications": {"canonical": "What medicines does he take?", "echo": "his medicines", "variants": [
   "Meds?", "Any medications?", "What does he take every day?", "Is he on any steroids?",
   "Any blood thinners?", "What pills is he on?", "Any regular medicines?", "Did he take his meds today?",
   "Any inhalers?", "Any new medications?", "Is he on anything?", "Home meds?"]},
 "allergies": {"canonical": "Is he allergic to anything?", "echo": "allergies", "variants": [
   "Any allergies?", "NKDA?", "Any drug allergies?", "Allergic to any medicines?", "Any allergy to penicillin?",
   "Any reactions to antibiotics?", "Allergies?", "Any medication allergies?", "Any rashes with drugs?",
   "Is he allergic to penicillin?"]},
 "recent_antibiotics_healthcare": {"canonical": "Has he been in hospital or on antibiotics recently?",
   "echo": "recent hospital stays or antibiotics", "variants": [
   "Any recent hospitalizations?", "Has he had antibiotics in the last few months?", "Any IV antibiotics recently?",
   "Was he in the hospital in the last three months?", "Any nursing home stays?", "Any recent antibiotics?",
   "Has he ever had MRSA?", "Any resistant infections before?", "Recent hospital admission?",
   "Has he been on antibiotics lately?", "Any dialysis or wound care?", "Recent healthcare exposure?"]},
 "home_oxygen": {"canonical": "Does he use oxygen at home?", "echo": "oxygen at home", "variants": [
   "Is he on home oxygen?", "Any home O2?", "Does he need oxygen normally?", "Home O2?",
   "Does he use a CPAP or BiPAP at home?", "Has he ever needed oxygen before?", "Any oxygen at home?",
   "Is he on oxygen at baseline?", "Does he have a home oxygen tank?", "Any breathing machines at home?"]},
 "social_history": {"canonical": "Does he smoke or drink?", "echo": "smoking and drinking", "variants": [
   "Does he smoke?", "How much does he smoke?", "Any alcohol?", "Does he drink?", "Any drugs?",
   "Pack years?", "Tobacco use?", "How many cigarettes a day?", "Any vaping?", "Who does he live with?",
   "What does he do for work?", "Any recreational drugs?"]},
 "vaccinations": {"canonical": "Is he up to date with vaccines?", "echo": "his vaccines", "variants": [
   "Did he get a flu shot?", "Has he had the pneumonia vaccine?", "Any vaccines this year?",
   "Is he vaccinated?", "Flu vaccine?", "Pneumococcal vaccine?", "COVID vaccine?", "Shots up to date?",
   "Has he had his flu jab?", "Any recent vaccinations?"]},
 "sick_contacts": {"canonical": "Has anyone around him been sick?", "echo": "anyone else sick", "variants": [
   "Any sick contacts?", "Anyone at home ill?", "Has anyone else had this?", "Anyone at work sick?",
   "Any family members unwell?", "Sick contacts?", "Anyone with a cough at home?", "Anyone else with a fever?",
   "Grandkids sick?", "Any exposures?"]},
 "travel_history": {"canonical": "Has he traveled recently?", "echo": "travel", "variants": [
   "Any recent travel?", "Been out of the country?", "Any hotel stays?", "Any cruises?",
   "Any long flights or drives?", "Been anywhere recently?", "Travel history?", "Any trips lately?",
   "Stayed anywhere away from home?", "Any travel in the last month?"]},
 "family_history": {"canonical": "Any illnesses that run in the family?", "echo": "his family history", "variants": [
   "Family history?", "FHx?", "Any heart disease in the family?", "Any lung disease in the family?",
   "Parents' health?", "Anything run in the family?", "Any family history of clots?", "Family medical history?",
   "Any cancer in the family?", "Any family history of heart attacks?"]},
 "functional_baseline": {"canonical": "What is he normally like?", "echo": "how he usually is", "variants": [
   "Is he usually active?", "What's his baseline?", "Can he usually walk far?", "Does he work?",
   "Is he independent?", "How active is he normally?", "Exercise tolerance?", "Can he climb stairs normally?",
   "What can he normally do?", "Baseline function?"]},
 "last_oral_intake": {"canonical": "When did he last eat or drink?", "echo": "when he last ate", "variants": [
   "When did he last eat?", "Last meal?", "Has he been eating?", "Has he been drinking?",
   "Any food today?", "Last PO intake?", "Has he been able to drink fluids?", "When did he last have anything?",
   "Eating okay?", "Appetite?"]},
 "code_status": {"canonical": "What would he want if he got sicker?", "echo": "what he would want", "variants": [
   "What's his code status?", "Would he want to be intubated?", "Does he have advance directives?",
   "Would he want everything done?", "Is he full code?", "Would he want to go on a breathing machine?",
   "Any DNR order?", "Has he talked about end of life wishes?", "Goals of care?", "Would he want CPR?"]},
 "diabetes_control": {"canonical": "How is his diabetes usually?", "echo": "his diabetes", "variants": [
   "How are his sugars?", "Does he check his blood sugar?", "What's his sugar usually?", "Is his diabetes controlled?",
   "Does he use insulin?", "How long has he had diabetes?", "Sugar readings at home?", "A1c?",
   "Has his sugar been high?", "Diabetes well controlled?"]},
}
