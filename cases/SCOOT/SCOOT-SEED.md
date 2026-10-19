# SCOOT seed and provenance

A 22-year-old man after an e-scooter crash without a helmet, with a right temporal epidural
hematoma that declines in the department. Drafted by a language model on 19 October 2026 at
the request of Aakash Setty, from an AI-generated case plan he supplied as inspiration and a
plan agreed in the same conversation. **No physician has reviewed this pack.** Read every
number, finding, deadline and tag as a proposal.

The prefix is SCOOT and not EDH because the prefix is public (authoring 2.2).

## 0. What a person decided

Aakash Setty, 19 October 2026, in conversation:

| Decision | What was decided |
|---|---|
| The case | "An epidural hematoma case with clinical deterioration." An AI-generated plan was supplied as inspiration, not as a seed |
| Process | Plan first, build only on the word to build |
| Learning goals | "Learning goals are good." The four goals in section 2.1, as presented, were approved |
| States and summary | "Okay this is good. Please build this case." The four live phases in section 2.4 and the one-paragraph summary were approved |

Everything else is model output. In particular these four choices were offered to him as
open questions with a recommended default, and he asked for the build without choosing. The
model took its own recommendation each time. Each is listed again in section 2.10:

| Choice | Model default taken |
|---|---|
| Setting | Level 1 trauma center with neurosurgery in house. The correct disposition is the operating room |
| The clock in the herniation phase | A terminal phase after five minutes of untreated herniation, with the opt-in |
| Calling neurosurgery back after the decline | Critical |
| Harmful halts | None. Thrombolytics and anticoagulants are left untagged |

## 1. Sources, and how far each was read

| Source | How it was read | What it supplied |
|---|---|---|
| Bullock MR et al. Surgical management of acute epidural hematomas. Neurosurgery 2006, 58(3 Suppl), S7-15 | Through a summarizing tool (a Medbullets evidence page) by a model on 19 October 2026. The paper itself was not opened | "An EDH greater than 30 cm3 should be surgically evacuated regardless of the patient's GCS score." The nonoperative criteria (under 30 cm3, under 15 mm, under 5 mm shift, GCS over 8, no focal deficit, serial CT in a neurosurgical center). "Patients with an acute EDH in coma (GCS score < 9) with anisocoria undergo surgical evacuation as soon as possible." The page gave no evidence grade |
| Brain Trauma Foundation, Guidelines for the Management of Severe TBI, 4th edition, 2016 | The PDF was fetched but came back truncated without the recommendations. The blood pressure line was read through a UMEM educational pearl, through a summarizing tool | "Maintain SBP 100 mmHg for patients 50-69 years old or 110 mmHg for patients 15-49 or >70 years old (Level III)." The guideline population is GCS 3 to 8 |
| CRASH-3 (Lancet 2019), tranexamic acid in traumatic brain injury | Through a summarizing tool (The Bottom Line summary) | Primary outcome RR 0.94 (95% CI 0.86 to 1.02). GCS 9 to 15 subgroup RR 0.78 (0.64 to 0.95), possibly a type I error |
| Stair R. Epidural Hematoma With Coma. MedEdPORTAL 2007 | The abstract only | That a published EDH simulation requires a consultant call and runs a worsening branch on delay. No objectives or critical actions were visible |
| "It's Only Brain Surgery", rural EDH simulation (PMC7704185) | Blocked by a browser check. Not read | Nothing |
| JETem epidural hematoma page | Opened. It is a case report, not a simulation | Nothing used |
| ATLS teaching on a definitive airway at GCS 8 or less, on mannitol for acute neurological deterioration, and on cervical spine clearance | From memory. No source opened | Written by a model. Unverified |
| Cushing's response, uncal herniation, the lucid interval, hypotonic fluid and NSAIDs in intracranial bleeding, post-intubation sedation | From memory. No source opened | Written by a model. Unverified |

The AI-generated plan the owner supplied is not a source. Section 9 lists where it
disagreed with itself or with the engine, and what the build did about each.

## 2.0 How this case differs from the library

| Dimension | SCOOT | Nearest in the library |
|---|---|---|
| Tempo | Minutes. A clock the learner cannot stop: he declines at four minutes whatever is done | MGCA and AFRVR run clocks that treatment stops. None has unpreventable natural history on the main path |
| What is uncertain | Whether he is getting worse, and when to act | TSS: whether a talking patient is sick |
| Kind of right answer | Ask someone (the surgeon), and do less (no reflexive tube or osmotherapy) until it is time to do more | TAKO also turns on a consultant. DIPH is the "do less" case |
| Where the danger hides | Behind normal vitals and a GCS of 15 at the door. When it shows, it shows in the exam and not on the monitor | TSS, behind near-normal vitals |
| Patient and room | 22 M, EMS to the trauma bay (no pack uses it), alone, his friend on the way | DIPH and TSS have companions |
| How it feels | Deceptively easy, then urgent | TSS, puzzling then urgent |

It is the library's first trauma case and its first neurosurgical one.

## 2.1 Learning goals

Approved by Aakash Setty on 19 October 2026. The sources are as read in section 1.

| # | Goal | Where the learner acts on it, and what the patient shows | Source and standing |
|---|---|---|---|
| G1 | When the exam changes, the plan changes. Re-examine when the patient changes, and escalate on the trend even when vitals and pupils are normal | The decline phase. A neuro exam there credits `neuro_reexamined`. Calling neurosurgery there credits `neurosurgery_updated`. The monitor barely moves (138/82 to 145/84) and the pupils stay equal. Only the exam shows it | Bullock 2006 asks for close neurological observation. Talk and deteriorate is standard teaching (from memory). The call back is model opinion |
| G2 | The treatment for an epidural hematoma is a surgeon. Image early and call neurosurgery the moment the CT is back, without waiting for a blown pupil or Cushing's response | The CT prompt in every phase. The neurosurgery consult cannot be made until a head CT has resulted (a prerequisite whose failure message is the neurosurgeon's request, authoring 9.5). Not making the call by the end of the decline phase leads to herniation | Bullock 2006. The framing of the emergency physician's role is model opinion |
| G3 | Intubate for a reason, not a number. No tube for a GCS 12 patient protecting his airway on his way to the OR. No osmotherapy at GCS 15 | Intubation is discouraged on arrival and in the decline, critical in herniation. After a tube, the neuro exam reads "GCS cannot be assessed", which the learner sees. Osmotherapy is discouraged on arrival, accepted in the decline, critical in herniation | GCS 8 or less is ATLS teaching (from memory). Mannitol for acute deterioration is ATLS teaching (from memory). Partly model opinion |
| G4 | Treat herniation, and leave the compensation alone | Herniation phase. Osmotherapy (a hidden target) and intubation are critical. Every antihypertensive and atropine are discouraged | BTF 4th edition SBP floor (as read). Cushing's physiology is standard. The atropine trap is model opinion |

The idea that travels, carried by G1: **when the exam changes, the plan changes, whatever the
monitor says.** A second idea, carried by G4, prints lower: before you fix a number, ask
whether the body made it on purpose.

Competencies considered and not kept as goals: applying a head CT decision rule (any rule
images this patient, so there is no real decision), cervical spine clearance (kept as
recommended actions), the content of the call to neurosurgery (the engine cannot read it),
and tranexamic acid (contested, kept neutral with a note).

## 2.2 Identity and the public fields

- `working_title`: "22-year-old man after an e-scooter crash"
- `complaint`: "Head injury after crash". `category`: "Trauma" (new to the library)
- `chief_complaint_patient_voice`: "My head is killing me. What happened?"
- `target_level`: medical student, intern, junior resident
- `estimated_runtime_seconds`: 600
- Correct diagnosis: `dx_epidural_hematoma`

None of the public fields names the diagnosis.

## 2.3 Patient, setting and arrival

22-year-old man, 78 kg. Works at a bike shop, lives with a roommate. No medical history, no
medicines, no allergies, no anticoagulants. Riding an e-scooter home from a friend's
apartment at about 9 pm, about 20 mph, no helmet. Hit a pothole and went over the
handlebars, landing on the right side of his head. His friend Marcus, riding behind, says he
was out for about a minute and then got up and talked. He remembers leaving Marcus's
building and nothing after that (about thirty minutes of retrograde amnesia). He had nothing
to drink tonight. Road rash on both palms. No other injury.

Setting: a Level 1 trauma center with neurosurgery in house and an operating room available
(model default, section 0).

Arrival: `ems`, `trauma_bay`. The handover, two sentences, 36 words:

> Twenty-two year old guy came off an e-scooter, no helmet, and his friend says he was out for
> maybe a minute. He's been talking to us the whole way in but keeps asking what happened.

It carries the loss of consciousness because a crew that heard it from the friend would say
it, and it is the reason he came by ambulance. It carries no vital sign, no history and no
diagnosis.

## 2.4 The stories, and the states

**Treated well.** He arrives talking. The learner attaches the monitor, examines him (GCS
15, pupils equal) and scans his head. The CT shows a large right temporal collection with
shift. The learner calls neurosurgery, who book the OR. Four minutes in he vomits and becomes
hard to wake. The learner re-examines him (GCS 12), calls neurosurgery back, gives an
antiemetic, leaves the airway alone and hands him to the OR.

**Treated well but late.** The scan is ordered only after the decline. It is back in seconds,
neurosurgery is called with it, and he goes to the OR at GCS 12.

**Called it concussion.** The decline is put down to concussion and the scan sits unread, or
neurosurgery is never called with it. Five minutes later his right pupil blows and his pulse
slows while his pressure climbs. The learner who now gives osmotherapy sees the pupil come
back a little and can still get him to the OR. The learner who also lowers the pressure or
gives atropine is told why in the debrief.

**Tubed for the number.** The learner intubates at GCS 15 or 12. Nothing crashes. The exam
now reads "GCS cannot be assessed", and the decline arrives with only the pupils to follow.

**Left alone.** Declines at four minutes, herniates at nine, and dies of brainstem
compression at fourteen.

| Phase | Short label | The patient | What now? | If nothing is done |
|---|---|---|---|---|
| `presentation` | on arrival | GCS 15, 138/82, HR 88, RR 16, SpO2 99, pupils equal | Monitor, primary survey, baseline neuro exam, CT head and C-spine, neurosurgery once the CT is back | Declines at 240 s whatever is done (scheduled natural history) |
| `decline` | harder to wake | GCS 12 (E3 V4 M5), vomited, 145/84, HR 96, RR 18, pupils equal | Re-examine. CT now, or call neurosurgery with it, or call them back. Antiemetic. No tube | Herniation at 300 s unless neurosurgery has been called with the scan |
| `herniation` | right pupil big | GCS 7, 178/94, HR 56, RR 10, SpO2 95, right pupil fixed | Osmotherapy, intubate, neurosurgery now, leave the pressure alone | Terminal at 300 s without osmotherapy given in this phase |
| `temporized` | pupil reacting | GCS 8, 160/88, HR 70, RR 14, right pupil sluggish | Secure the airway if not done, hand off to the OR | Indefinitely. Known gap 3 |
| `brainstem_compression` | not responding | Terminal. 196/108, HR 44, RR 6, SpO2 86 | | |
| `case_complete` | handed over | Terminal, inherits vitals | | |

Every non-terminal phase hands off to `case_complete`, first in its list. No phase is
`halted`.

The presentation and decline vitals differ by a few points. That departs from the default
of numbers that differ frankly (authoring 4) on purpose: the lesson is that the monitor does
not show this. The nurse's narration on the timed transition and the exam carry the change.

**Every link as a claim about cause** (model output, for the physician):

- presentation to decline: an expanding arterial hematoma raises intracranial pressure
  within minutes to hours of injury. Nothing in the department stops it except evacuation.
- decline to herniation: an untreated expanding temporal EDH displaces the uncus and
  compresses the third nerve and the brainstem.
- herniation to temporized: osmotherapy lowers intracranial pressure for a while, and a
  dilated pupil can become reactive again. The 15 seconds is a teaching choice.
- herniation to brainstem compression: untreated uncal herniation progresses to brainstem
  failure. Five minutes is a teaching choice, not a measured interval.

### The race tables (authoring 15.4)

`presentation` has two rules at 240 s from entry. The rule guarded on `flag intubated set` is
above the unguarded one, so an intubated patient gets the narration that fits him. Either
way he enters `decline` at 240 s. The two cannot disagree on the destination.

`herniation` has two timed rules. The terminal rule is `NOT action osmotherapy_for_herniation
taken`, 300 s from phase entry. The rescue is `action osmotherapy_for_herniation taken`, 15 s
from guard true.

| Osmotherapy given, seconds after entering herniation | What happens |
|---|---|
| Any time before 300 | The terminal rule's guard turns false at the order and the rule is canceled. Temporized 15 s later |
| Exactly 300 | An action logged at the deadline is applied first, so the terminal rule is canceled. Temporized at 315 |
| After 300 | Brainstem compression at 300. The order never reaches a live phase |
| Before entering herniation (in the decline) | Does not count. The hidden target is credited only in `herniation`, so a dose on the way in does not satisfy the exit (authoring 15.2 rule 6). A second dose is needed, which is clinical practice |

`decline` has one timed rule, so it has no race.

## 2.5 The action spine

**Critical**

| Action | When | Time-sensitive |
|---|---|---|
| `attach_monitor` | presentation | prompt at 20 s |
| `exam_neuro` | every phase (the baseline) | prompt at 35 s on arrival |
| `ct_head` | every phase | prompt at 50 s while not ordered |
| `consult_neurosurgeon` (needs a resulted head CT or CT/CTA, sets `neurosurgery_called`) | every live phase | prompt at 70 s, escalation at 90 s. On arrival only once a scan is back, so a GCS 15 patient with no imaging is not pointed at a surgeon. After arrival with or without a scan, and a learner without one is sent for it by the prerequisite |
| `neuro_reexamined` (hidden, credited by a neuro exam in the decline) | decline | prompt at 15 s |
| `neurosurgery_updated` (hidden, credited by a neurosurgery call in any phase after arrival) | decline, herniation, temporized | prompt at 40 s, guarded on `neurosurgery_called` |
| `osmotherapy_for_herniation` (hidden, credited by mannitol or hypertonic saline in herniation) | herniation | prompt at 20 s, escalation at 60 s |
| `intubate_rapid_sequence` | herniation, temporized | prompt at 30 s while not intubated |

**Recommended:** `insert_iv`, `c_collar`, `ct_c_spine`, `complete_blood_count_cbc`,
`coagulation_panel`, `blood_type_and_screen`, `fingerstick_blood_sugar`, the airway,
breathing and circulation exams, `exam_heent`, `exam_neck`, and `ondansetron` in the decline.

**Discouraged**

| Action, with every route | Where | Why |
|---|---|---|
| `intubate_rapid_sequence` | presentation, decline | He protects his airway and is minutes from an anesthetist. The tube costs the exam |
| `mannitol_bolus`, `hypertonic_saline_25_bolus`, `hypertonic_saline_3_infusion` | presentation | No sign of raised pressure at GCS 15 |
| `labetalol_bolus` covering `labetalol_drip`, `nicardipine_drip`, `esmolol_drip`, `nitroprusside_drip`, `nitroglycerin_drip`, `nitroglycerin`, `nitroglycerin_sublingual`, `metoprolol_bolus` | every phase | Nothing to treat early. In herniation the pressure is keeping the brain perfused |
| `atropine_bolus` | herniation, temporized | The slow pulse is Cushing's response. The treatment is the pressure inside the head |
| `lower_head_of_bed` | every phase | Lying flat raises intracranial pressure |
| `d5_1_2_ns_infusion` | every phase | Hypotonic fluid in a brain injury |
| `ibuprofen` | every phase | Antiplatelet effect in a bleeding head |

The covered antihypertensive siblings are bound through `also_covers` on `labetalol_bolus`,
and the shared note says "the blood pressure medicine", not one drug.

**Neutral, with a note:** osmotherapy in the decline (accepted, not required, because good
doctors disagree), osmotherapy in temporized, `tranexamic_acid`, `levetiracetam_bolus`,
`fos_phenytoin`, `acetaminophen`, `fentanyl_bolus`, `morphine_bolus`, the induction agents
and paralytics, `preoxygenate_for_intubation`, `normal_saline_1l_bolus`, the consultations
other than neurosurgery.

**Harmful:** none (model default, section 0).

**One case prerequisite.** `consult_neurosurgeon` needs `(study ct_head resulted OR study
ct_cta_head_and_neck resulted)`, failure message "Neurosurgery will want to see his head CT
first. Call them as soon as it's back." This replaced a hidden target in the first draft,
because the validator's prompt-first check reads a prompt guard with the phase alone and
cannot see a study, and because authoring 9.5 names a prerequisite as the way to make a
consult need a study. Its cost: a learner cannot place a heads-up call for a falling GCS
before the scan, which is reasonable in life. The debrief note says so.

**Traps:** intubation and osmotherapy before herniation (G3), antihypertensives and atropine
in herniation (G4), lowering the head of the bed.

## 2.6 Sequencing

- Case prerequisite: the neurosurgery consult needs a resulted head CT or CT/CTA (section 2.5).
- Catalog prerequisites kept: a line before every intravenous drug, central access for 23.4%
  or 25% saline, sedation and a paralytic before the tube. None waived.
- One follow-up: `sedation_after_intubation`, triggered by `intubate_rapid_sequence`, applies
  while intubated, deadline 60 s, satisfied by the hidden target `post_intubation_sedation`,
  which a propofol or ketamine infusion, a fentanyl or morphine bolus or midazolam credits only
  once the tube is in. A dose given for the headache earlier does not discharge it.

## 2.7 Key findings

| Finding | Value | Changes |
|---|---|---|
| GCS | 15, then 12 (E3 V4 M5), then 7 (E1 V2 M4), then 8 (E2 V2 M4) | By phase. After a tube: "cannot be assessed" |
| Pupils | 3 mm equal reactive, then right 6 mm fixed, then right 4 mm sluggish | In exam_heent and exam_neuro, and drawn in the eye view (`content_keys.pupils`, section 2.13) to the same sizes and responses, phase by phase. Both 6 mm and fixed in brainstem compression |
| Motor | Normal, then withdraws to pain left less than right | Model-added left-sided weakness in herniation (contralateral to the clot) |
| Scalp | Boggy right temporal hematoma, no laceration | Every phase |
| Skin | Road rash on both palms | Model-added. Every phase |
| CT head, every phase | The image stack itself (since 19 October 2026, owner instruction): the EDH case of the owner's Head CT Teaching Cases artifact, 31 synthetic axial images, opened in the CT viewer. Its read, kept for the debrief: biconvex hyperdense collection over the right temporoparietal convexity, limited by the sutures, about 19 mm thick and about 50 mL, low-density pockets (swirl sign), linear fracture of the right temporal squama on the bone window, right temporal scalp hematoma, about 6 mm of leftward shift with right ventricular effacement, no other blood | One series for every phase, because there is one volume. The case's text was changed to match the images: it was drafted at 32 mL and 5 mm. The volume is about 47 mL by the artifact's own count and about 50 mL by a model's sum of its lesion map |
| ECG | Sinus rhythm 88, sinus 96, sinus bradycardia 56, sinus 70 | A generated tracing per phase, by the 13 October default, which the engine suite enforces. Drawn with the ECG generator (media/README.md). The read is the debrief comment. The caption quotes the rate because nothing moves it |

The labs are left to the catalog defaults, which are normal, and that is intended: a normal
CBC, coagulation panel, type and screen, chemistry, glucose, ethanol and urine toxicology.
The CT C-spine is the catalog's normal read. Each is named here so that a reviewer knows the
default answers on purpose (authoring 9.1).

The scan does not change in the minutes between arrival and the decline. That is a
simplification: an early scan can underestimate a hematoma that is still growing.

## 2.8 Interview ground truth

He answers for himself on arrival, briefly and confusedly in the decline, and not at all in
herniation, temporized, after a tube, or at the end (one global rule).

Facts: the crash as told by Marcus (he does not remember it), about a minute out, memory gap
from leaving Marcus's building, right-sided headache 6 of 10 and worse, queasy on arrival and
vomiting in the decline, no helmet, scooter does about 20, ambulance ride he barely
remembers, palms sting, nothing to drink tonight, vapes nicotine sometimes, no drugs, dinner
at about seven, no medical history, no surgery, no medicines, no allergies, no blood thinners,
no family bleeding problems, tetanus probably in high school, works at a bike shop, lives
with a roommate, Marcus is on his way.

Pertinent negatives, each a denial in every phase that answers: no neck pain, no weakness or
numbness or trouble speaking, no double or blurred vision, no seizure, no chest pain, no
trouble breathing, no belly pain, no hearing change, no medical history, no medicines, no
blood thinners, no allergies. All are model-added except the anticoagulant denial, which the
supplied plan stated.

Model-added positives, listed for sign-off: the road rash, the vaping, the bike shop, the
roommate, Marcus by name, dinner at seven, the 6 of 10.

## 2.9 Disposition and diagnosis

Correct: `operating_room`, operating room with neurosurgery. Wrong: discharge, observation
unit, medical floor, neurosurgical ICU for observation and a repeat scan (the nonoperative
path, which this hematoma does not meet), transfer (neurosurgery is here).

Correct diagnosis: `dx_epidural_hematoma`. Alternatives: acute subdural hematoma, mild
traumatic brain injury, subarachnoid hemorrhage, basilar skull fracture and cervical spine
fracture as incorrect, severe traumatic brain injury as defensible with qualification.
No additional diagnoses: the catalog has no calvarial skull fracture and no moderate TBI.

## 2.10 Known gaps and open questions

**Known gaps** (each pinned by a scenario named "Known gap:")

1. A learner who calls neurosurgery with the scan and hands off before four minutes never
   meets the decline. That is good care, and G1 is not exercised on that run.
2. Neurosurgery cannot take over. The learner hands off, and the case ends there.
3. Temporized has no clock. Osmotherapy buys time in life, and the case does not model it
   running out.
4. The consult cannot carry what was said. G1's call back is credited by pressing the button
   in a later phase.
5. Hyperventilation as a bridge cannot be ordered. It is mentioned in the debrief only.
6. There is one CT series, so a scan sent after the decline or in herniation shows the same
   images as one sent on arrival. A real scan in herniation would show more shift and
   effaced basal cisterns.
7. The nurse's decline narration after an early tube does not say he vomited, because a
   sedated, paralyzed patient may not.

**Open questions for the physician**

1. The four model defaults in section 0: Level 1 setting, the terminal clock in herniation,
   the call back as critical, and no halts.
2. Osmotherapy in the decline: neutral (accepted) as built, or discouraged, or recommended?
3. Is 240 s for the decline, 300 s to herniation and 300 s to brainstem compression right
   relative to each other?
4. Should a CT C-spine be recommended at GCS 15 with no midline tenderness? Built as
   recommended in every phase.
5. Should tranexamic acid be recommended (CRASH-3 subgroup) or stay neutral?
6. Should the herniation phase also require a second call to neurosurgery, separate from the
   decline call back? Built as one hidden target for any call after arrival.

Questions the documents did not answer:

1. Whether `also_satisfies` is lent to covered siblings through `also_covers`. Not settled by
   reading the engine. The case gives each osmotic agent its own action instead.
2. The prompt-first rule (authoring 15.2 rule 2) does not say that the validator evaluates a
   prompt's guard with only the phase known, so a prompt guarded on a study never counts as
   the warning. Found by reading the validator after its error, which CLAUDE.md asks builders
   not to do. Recorded here as a gap in the documents.
3. Section 23's generated-tracing default names the generator but not how to run it for a new
   pack without regenerating every pack. This case used its own small script beside the
   generator (media/README.md) and did not edit the generator's files.
4. The out-of-scope bank holds "Any seizures or fits?", "Any numbness anywhere?" and similar
   with no cover tag, so a trauma case must copy them into its own variants to remove them.
   A cover tag for neurological symptoms would fix it for every later pack.

## 2.11 The first run (19 October 2026)

All counts from the last run, not from memory.

- `engine/test_packs.py` for all eight packs: all pass. SCOOT: engine 562 checks, scenarios
  12 of 12, validator 0 errors and 1 warning (the case-only actions), validator negative
  tests 101, timeline written.
- `engine/kit_check.py`: 0 errors, 0 warnings.
- Matcher, lexical only, on the held-out file: in scope 40 of 52 (77 percent), 6 wrong, all six
  on management-changing topics, out of scope refused 17 of 32 (53 percent). The semantic
  stage was not run: huggingface.co was unreachable from the owner's machine. The held-out
  file was not tuned against after this run. Several questions labeled out of scope ("Do you
  have asthma?", "Do you have diabetes?") are answered correctly by the past medical history
  topic, so the refusal figure understates what the patient handles. That is a labeling
  choice in the held-out file and is left as written.
- A scripted Playwright play-through against `build/simulator.html`, in the default mode, at
  1x and 16x: the intended path (case complete, six of six critical actions), the concussion
  path through herniation, osmotherapy and a tube (case complete, seven of eight, the repeat
  exam missed), and the do-nothing path (case failed at 14:00 with the timeout reason). A
  first attempt that failed to order the CT, through a script fault, walked the no-scan
  route and showed every prompt at its tripled time. Screenshots in
  `Claude outputs/scoot-playthrough/`.

## 2.12 The head CT as images (19 October 2026, owner instruction)

Aakash Setty asked for a DICOM-style viewer in the simulator showing a CT head of an epidural
hematoma from his Head CT Teaching Cases artifact, with a clickable thumbnail in the Record
like the other images. Built as a general engine feature (a `series` on an image payload,
authoring 23), and SCOOT's head CT now uses the artifact's EDH case (Case 3).

- The source is not DICOM files. It is a Hounsfield-unit volume the artifact stores in its own
  format. The viewer reads that volume and behaves like a DICOM viewer (scroll, windows, HU).
- The images showed a bigger clot than the case was written with, so the case's text was
  changed to match the images, not the other way round (section 2.7).
- The head CT is now read by the resident. The text read is the debrief comment. That makes
  goal G2 harder: the learner has to see the collection. The nurse, the prompts and the
  consultant are unchanged, except that the neurosurgeon no longer quotes a volume.
- The CT/CTA stays a text report, because the series is a non-contrast study.
- Air below -300 HU was flattened to -1000 HU to make the file a third smaller. Nothing inside
  the head changed. The HU readout over air shows -1000.
- The images open on image 16 of 31, the middle of the stack, by a rule that does not point at
  the lesion. The thumbnail is the same image. The hematoma is visible on it.
- The Colin27 copyright notice travels with the images and is printed under "About this image".

## 2.13 The pupils drawn (19 October 2026, owner instruction)

Aakash Setty asked for the eye view (`content_keys.pupils`, authoring 5.3) in SCOOT, to show
the blown right pupil in herniation. Hovering over the figure's eyes opens both eyes close up,
and the pointer inside is a penlight. The drawing follows the four pupil sentences the exam
already prints:

| Phase | Exam text | Drawn |
|---|---|---|
| presentation, decline, case_complete | Pupils 3 mm, equal and reactive | Both 3 mm, brisk |
| herniation | Right pupil 6 mm and fixed. Left 3 mm and reactive | Right 6 mm, no response. Left 3 mm, brisk, and it constricts to light in either eye |
| temporized | Right pupil 4 mm and sluggish. Left 3 mm and reactive | Right 4 mm, sluggish. Left 3 mm, brisk |
| brainstem_compression | Both pupils 6 mm and fixed | Both 6 mm, no response |

- The renderer could not draw two of these when the request came. A blown pupil was always
  8 mm and fixed, and nothing drew a pupil partly back after treatment. Rather than change the
  case's text to fit the drawing, the engine gained two keys, `affected_mm` and
  `affected_reaction`, for the affected eye of a blown pupil (authoring 5.3, CHANGELOG). Nothing
  in the engine names this case.
- "Reactive" in the text is drawn brisk.
- Sedation and an opioid after the tube are not drawn, as the exam text does not change with
  them. A pupil that can still move would be smaller on an opioid.
- How far and how fast the pupil comes back after osmotherapy (4 mm and sluggish within 15 s)
  is a teaching choice, the same one section 2.4 already names.

Model-written, not reviewed.

## 3. Catalog change requests

- A "raise head of bed" action. Only lowering exists.
- Diagnosis entries for a calvarial (temporal squamous) skull fracture and for moderate
  traumatic brain injury.
- A ventilator or hyperventilation order, for the herniation bridge.
- A trauma team activation action.

## 9. The supplied plan, where it disagreed with itself or with the engine

| Point in the plan | What the build did | Resolved by |
|---|---|---|
| "Workup underway" and "CT confirms EDH" as states | Not phases. A study result and flags | Builder, by the design guide |
| "Routine vs STAT consult" | Not expressible. Dropped | Builder |
| "Misses one component of the neuro exam" | Not expressible. One exam returns all of it | Builder |
| "Repeat CT despite an adequate scan" and "waits for a repeat exam before calling" | Not expressible (no counting or order). Dropped | Builder |
| No herniation, yet failure "after the defined rescue window" | Herniation is a recoverable phase, and death needs five more minutes of inaction in it | Builder, then the owner approved the states |
| Intubation causing hypotension | Not modeled. A healthy 22-year-old at 138/82 is unlikely to crash | Builder |
| The 30 cm3 rule as the learner's decision | In the debrief as the neurosurgeon's criterion. The learner's decision is to call | Builder, goals approved by the owner |
