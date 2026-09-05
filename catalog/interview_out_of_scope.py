"""Questions the patient has no authored answer to, for the out-of-scope bank.

Author-time content. `expand_interview_variants.py` filters this list per case pack
and writes the survivors into `interview.out_of_scope_bank` in the case, where the
matcher embeds them beside the topic bank. A learner's question that lands closer to
one of these than to any topic is answered by the out-of-scope fallback rather than
by the nearest topic.

Why this exists: on the AFRVR held-out set, nineteen of thirty unrelated questions
were answered with a confident wrong topic, and the cosine scores of in-scope and
out-of-scope questions overlapped so completely that no threshold could separate
them. "Have you had a colonoscopy?" is not far from "When did you last eat?" in
embedding space. The fix is to give "nothing relevant" its own neighbourhood.

Each entry is (phrasing, covers). `covers` lists concepts from interview_phrasings.py:
if a case authors any of them, the entry is dropped for that case, because there the
question IS in scope. An empty list means the entry is generic.

PROVENANCE: written by an AI assistant in September 2026. Not physician-reviewed.
Nothing here may repeat a held-out evaluation question; the expansion script refuses
if it does.
"""

OUT_OF_SCOPE = [
  # ---- gastrointestinal
  ("Have you ever had a colonoscopy?", []),
  ("Any blood when you open your bowels?", []),
  ("Are you constipated?", []),
  ("Any heartburn?", []),
  ("Any indigestion after meals?", []),
  ("Any trouble swallowing?", []),
  ("Any change in your bowel habit?", ["diarrhoea"]),
  ("Any diarrhoea at all?", ["diarrhoea"]),
  ("Any pain in your tummy?", ["abdominal_pain", "abdominal_fullness"]),
  ("Have you had piles?", []),
  ("Any black stools?", []),
  ("Any yellowing of your skin or eyes?", []),

  # ---- genitourinary
  ("Do you get up at night to pass water?", []),
  ("Any blood in your urine?", []),
  ("Any trouble with your prostate?", []),
  ("Any burning when you pass urine?", ["dysuria_gu"]),
  ("Any kidney stones in the past?", []),
  ("Any incontinence?", []),
  ("When was your last smear test?", ["menstrual_tampon", "pregnancy", "sexual_history"]),

  # ---- neurological
  ("Any headaches at all?", ["headache"]),
  ("Any seizures or fits?", []),
  ("Any weakness in your arms or legs?", []),
  ("Any pins and needles?", []),
  ("Any numbness anywhere?", []),
  ("Any problems with your speech?", []),
  ("Any tremor in your hands?", ["thyroid"]),
  ("Any trouble with your memory?", ["confusion"]),
  ("Any double vision?", []),
  ("Any problems with your balance?", ["dizziness", "syncope_dizziness"]),
  ("Have you ever had a stroke?", []),
  ("Any migraines?", ["headache"]),

  # ---- musculoskeletal
  ("Any back pain?", []),
  ("Any pain in your hands?", ["joint_pain"]),
  ("Any pain in your hips?", ["joint_pain"]),
  ("Any arthritis?", ["joint_pain"]),
  ("Have you broken any bones?", []),
  ("Any cramps in your legs?", ["calf_pain"]),
  ("Any neck pain?", ["neck_stiffness"]),
  ("Do you use a frame or a stick to walk?", ["functional_baseline"]),
  ("Any falls recently?", ["syncope", "syncope_dizziness"]),

  # ---- ENT, eyes, skin, teeth
  ("Any problems with your hearing?", []),
  ("Any ringing or buzzing in your ears?", []),
  ("Any earache?", []),
  ("Do you wear glasses or contact lenses?", []),
  ("Any blurred vision?", ["photophobia"]),
  ("When did you last have your eyes tested?", []),
  ("Any nosebleeds?", []),
  ("Any sinus trouble?", ["cough_sore_throat"]),
  ("Any rash on your skin?", ["rash"]),
  ("Any itching?", ["rash"]),
  ("Any moles that have changed?", []),
  ("Any hair loss?", ["thyroid"]),
  ("When did you last see the dentist?", []),
  ("Any toothache?", []),
  ("Any mouth ulcers?", []),
  ("Any lumps or bumps anywhere?", []),

  # ---- endocrine and general
  ("Have you lost weight without trying?", ["thyroid", "weight_gain"]),
  ("Are you diabetic?", ["pmh"]),
  ("Any excessive thirst?", []),
  ("Any hay fever?", ["allergies"]),
  ("Any change in your appetite?", ["last_oral_intake"]),
  ("Have you been feeling low in mood?", []),
  ("Any anxiety or panic attacks?", []),
  ("How are you sleeping generally?", ["snoring_osa"]),
  ("Any trouble sleeping?", ["snoring_osa"]),

  # ---- preventive and administrative
  ("Have you had a flu vaccine this year?", ["vaccinations"]),
  ("When was your last tetanus?", ["vaccinations"]),
  ("Have you had the covid vaccine?", ["vaccinations"]),
  ("Have you ever received blood?", []),
  ("Do you have a blood donor card?", []),
  ("Have you ever had a hernia repair?", ["psh"]),
  ("Who is your GP?", []),
  ("Who is your family doctor?", []),
  ("Do you have health insurance?", []),
  ("Have you got your NHS number?", []),
  ("Do you have a pharmacy you usually use?", []),
  ("Is there anyone we should call for you?", []),
  ("Who is your next of kin?", []),
  ("Do you have any religious needs we should know about?", []),

  # ---- small talk and the room
  ("What is your favourite food?", ["last_oral_intake", "dietary_sodium"]),
  ("Do you have any pets at home?", ["tick_outdoor"]),
  ("What do you do for a living?", []),
  ("What did you do before you retired?", []),
  ("Did you come in by ambulance?", []),
  ("Is anyone here with you?", []),
  ("Is your family in the waiting room?", []),
  ("How did you get here today?", []),
  ("Is it raining outside?", []),
  ("Do you live alone?", ["social_history"]),
  ("Do you have children?", []),
  ("How many kids do you have?", []),
  ("Where do you live?", []),
  ("Have you been anywhere nice on holiday?", ["travel", "travel_immobility_surgery"]),
  ("Do you follow any sports?", []),
  ("Do you watch much television?", []),
  ("What do you do to relax?", []),
  ("Do you have a garden?", ["tick_outdoor"]),
  ("Are you comfortable on that trolley?", []),
  ("Would you like a blanket?", []),
  ("Would you like a cup of tea?", ["last_oral_intake"]),
  ("Is the bed at the right height?", []),
  ("Can I get you anything?", []),
  ("What is your date of birth?", []),
  ("Can you confirm your name for me?", []),
  ("What is your address?", []),
  ("Do you know why you are here?", []),
  ("How old are you?", []),
  ("Is it okay if the students watch?", []),
  ("Would you prefer a female doctor?", []),
  ("Have you been waiting long?", []),
  ("Is there anything you would like to ask me?", []),
  ("What year are you in at university?", []),
  ("What are you studying?", []),
  ("Do you get on with your flatmates?", []),
  ("How much does it cost to park here?", []),
  ("Can I have a drink of water?", ["last_oral_intake"]),
  ("Who is the prime minister?", ["confusion"]),
  ("What is the date today?", ["confusion"]),
]
