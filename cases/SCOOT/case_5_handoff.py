"""SCOOT part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "operating_room",
   "label": "Operating room with neurosurgery",
   "level_of_care": "operative",
   "explanation": (
     "He needs the clot taken out. A temporoparietal epidural hematoma of about 50 mL with "
     "about 6 mm of shift, still bleeding on the scan, meets the guideline's criterion for evacuation whatever his GCS, and his GCS "
     "was falling. The neurosurgeon decides on the operation. Your job was to get him "
     "there.\n\n"
     "What the neurosurgeon and the anesthetist need: GCS 15 on arrival and 12 four minutes "
     "later, with each part, eyes, voice and motor, the pupils at each exam, that he vomited, "
     "the scan and the time it was done, his vital signs, that he is on no blood thinner, "
     "when he last ate, and what he has been given. If he herniated: when the pupil blew, "
     "what osmotherapy he had and when, and whether he is intubated.")},

 "alternative_dispositions": [
   {"id": "icu", "label": "Neurosurgical intensive care for observation and a repeat CT",
    "verdict": "incorrect",
    "explanation": (
      "That is the plan for a small epidural, under 30 mL, thinner than 15 mm, with less "
      "than 5 mm of shift, in a patient with a good GCS and no focal deficit. His meets none "
      "of the size criteria, and his GCS fell. Watching a clot this size is waiting for the "
      "pupil to blow.")},
   {"id": "medical_floor_telemetry", "label": "General ward with neuro checks",
    "verdict": "incorrect",
    "explanation": "A ward cannot watch a falling GCS closely enough, and he needs an operation, not observation."},
   {"id": "observation_unit", "label": "Emergency department observation unit",
    "verdict": "incorrect",
    "explanation": (
      "Observation suits a concussion with a normal scan. His scan was not normal, and he "
      "needs surgery.")},
   {"id": "discharge_home", "label": "Discharge home with head injury advice",
    "verdict": "incorrect",
    "explanation": (
      "He was talking and his vital signs were normal, which is why this is tempting at "
      "the door. He had lost consciousness, had no memory of the crash and had a scalp "
      "hematoma. Any of those is a reason for a scan, and his scan showed a surgical "
      "bleed.")},
   {"id": "transfer_tertiary", "label": "Transfer to another hospital",
    "verdict": "incorrect",
    "explanation": "This is a Level 1 trauma center with neurosurgery in the building. Transfer adds delay for nothing."}],

 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "icu", "operating_room", "transfer_tertiary"],

 "correct_diagnosis": {
   "catalog_id": "dx_epidural_hematoma",
   "label": "Epidural hematoma",
   "explanation": (
     "A biconvex collection that does not cross the sutures, over a temporal bone fracture, "
     "after a blow to the side of the head. That is blood between the skull and the dura, "
     "usually from a torn middle meningeal artery. It is arterial, so it grows fast, and a "
     "patient can talk on arrival and decline within minutes.")},

 "additional_diagnoses": [],
 "additional_diagnoses_note": (
   "None. His temporal squamous fracture is not a basilar skull fracture, and the catalog "
   "has no calvarial fracture and no moderate traumatic brain injury. Both are catalog "
   "change requests."),

 "alternative_diagnoses": [
   {"catalog_id": "dx_acute_subdural_hematoma", "label": "Acute subdural hematoma",
    "verdict": "incorrect",
    "explanation": (
      "A subdural is a crescent that crosses the sutures, usually venous and usually in an "
      "older patient or one on a blood thinner. His collection is biconvex and stops at the "
      "sutures, over a fracture. The call to neurosurgery is the same. The name tells the "
      "surgeon what to expect.")},
   {"catalog_id": "dx_mild_traumatic_brain_injury", "label": "Mild traumatic brain injury",
    "verdict": "incorrect",
    "explanation": (
      "His GCS on arrival fits, and that is the trap. A concussion is a diagnosis made once "
      "the scan is normal. His was not, and his GCS fell to 12.")},
   {"catalog_id": "dx_severe_traumatic_brain_injury", "label": "Severe traumatic brain injury",
    "verdict": "acceptable_with_qualification",
    "explanation": (
      "True by GCS once he had herniated, at 7 or 8. Before that he was a moderate injury at "
      "12. Either way the severity grade is not the lesion. Name the epidural hematoma, "
      "because that is what the surgeon is going in for.")},
   {"catalog_id": "dx_subarachnoid_hemorrhage", "label": "Subarachnoid hemorrhage",
    "verdict": "incorrect",
    "explanation": "His scan shows no blood in the subarachnoid space. The bleed is outside the dura."},
   {"catalog_id": "dx_basilar_skull_fracture", "label": "Basilar skull fracture",
    "verdict": "incorrect",
    "explanation": (
      "His fracture is in the flat temporal bone at the side of the skull, not the base. He "
      "had no blood behind the eardrums and no fluid from the nose or ears.")},
   {"catalog_id": "dx_cervical_spine_fracture", "label": "Cervical spine fracture",
    "verdict": "incorrect",
    "explanation": "His C-spine CT is normal. It was right to protect and image his neck."},
   {"catalog_id": "dx_intracerebral_hemorrhage", "label": "Intracerebral hemorrhage",
    "verdict": "incorrect",
    "explanation": "The blood is outside the brain, between the skull and the dura, not in the brain tissue."}],

 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "first_minutes", "label": "The first minutes",
    "actions": ["attach_monitor", "insert_iv", "c_collar", "exam_airway", "exam_breath",
                "exam_circ", "exam_heent", "exam_neck", "exam_neuro"]},
   {"id": "imaging", "label": "Imaging",
    "actions": ["ct_head", "ct_cta_head_and_neck", "ct_c_spine", "mri_mra_head_and_neck"]},
   {"id": "the_trend", "label": "Seeing the change, and saying it",
    "actions": ["neuro_reexamined", "neurosurgery_updated", "ondansetron"]},
   {"id": "neurosurgery", "label": "Getting him to a surgeon",
    "actions": ["consult_neurosurgeon", "handoff_submit"]},
   {"id": "airway", "label": "The airway, for a reason",
    "actions": ["intubate_rapid_sequence", "post_intubation_sedation"]},
   {"id": "herniation", "label": "Herniation, and what not to fix",
    "actions": ["osmotherapy_for_herniation", "mannitol_bolus", "hypertonic_saline_25_bolus",
                "hypertonic_saline_3_infusion", "labetalol_bolus", "atropine_bolus",
                "lower_head_of_bed"]},
   {"id": "before_the_or", "label": "Before the OR",
    "actions": ["complete_blood_count_cbc", "coagulation_panel", "blood_type_and_screen",
                "fingerstick_blood_sugar", "tranexamic_acid", "levetiracetam_bolus"]},
 ],
 "intended_path": ["presentation", "decline", "case_complete"],
 "intended_path_note": (
   "Monitor, a baseline exam, a head CT, neurosurgery called once it is back, then the "
   "decline at four minutes: a repeat exam, a second call, an antiemetic, no tube, and the "
   "handoff to the OR. A learner who hands over before four minutes ends in presentation, "
   "which is good care (known gap 1)."),
 "trap_actions": ["mannitol_bolus", "hypertonic_saline_3_infusion", "tranexamic_acid"],
 "trap_actions_note": (
   "Listed under 'looked reasonable and were not' only when pressed while tagged neutral. "
   "Osmotherapy in the decline and tranexamic acid are accepted, and the list is where the "
   "debrief says why they were not needed."),
 "cross_cutting_teaching_points": [
   ("When the exam changes, the plan changes, whatever the monitor says. His pressure went "
    "up seven points and his pulse eight. His GCS went from 15 to 12. Only one of those was "
    "the emergency."),
   ("The treatment for an epidural hematoma is a surgeon. Call neurosurgery the moment the "
    "scan is back. Do not wait for a blown pupil or Cushing's response, because by then the "
    "brain has already herniated. [UNVERIFIED: Bullock et al. 2006, read through a "
    "summarizing tool]"),
   ("Intubate for a reason, not a number. A tube in a talking patient takes away the exam "
    "that tells you he is getting worse."),
   ("Before you fix a number, ask whether the body made it on purpose. A high pressure and a "
    "slow pulse in a herniating brain are the body defending its blood supply. "
    "[UNVERIFIED: written by a model from memory]"),
   ("A plan made on an old exam is out of date when the exam changes. Tell the consultant "
    "what changed, in numbers: GCS 15 to 12, pupils equal, vomited."),
   ("The simulator compresses time. The decline at four minutes, the herniation two minutes "
    "later and the brainstem five minutes after that are teaching choices, not measured "
    "intervals."),
 ],
 "attempt_history_note": "Blocked attempts are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 19 October 2026, from an "
            "AI-generated case plan he supplied as inspiration, and a plan, four learning "
            "goals and four states he approved in the same conversation. Authoring "
            "requirements section 1 applies."),
 "warning": (
   "A person decided the things listed in SCOOT-SEED.md section 0. Everything else is model "
   "output and awaits sign-off: every vital sign, finding, delay, tag, prompt, debrief "
   "note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase, including that presentation and decline differ by only a few points on purpose.",
   "The three clocks: the decline at 240 seconds whatever is done, herniation 120 seconds after the decline (the owner's choice, 19 October 2026) without a call to neurosurgery with the scan, and brainstem compression 300 seconds after herniation without osmotherapy. The 15 seconds from osmotherapy to the temporized phase.",
   "The terminal clock in herniation, a model default the owner did not choose.",
   "Every exam finding and its routing, including the left-sided weakness in herniation and the road rash.",
   "The head CT images (the EDH case of the Head CT Teaching Cases artifact, synthetic), their read (about 19 mm, about 50 mL, about 6 mm of shift, swirl sign, temporal squamous fracture), the CTA and MRI reports, and that one series answers in every phase.",
   "The ECG reports, and the departure from the generated-tracing default.",
   "That the labs are left to normal catalog defaults.",
   "Every tag, including intubation discouraged before herniation, osmotherapy discouraged on arrival and neutral in the decline, the antihypertensives discouraged in every phase, atropine discouraged in herniation, tranexamic acid neutral, and no harmful tag anywhere.",
   "The four hidden targets and the conditions that credit them, and the prerequisite that the neurosurgery consult needs a resulted head CT.",
   "Every prompt deadline (15, 20, 30, 35, 40, 50, 70 with escalation at 90, and 20 with escalation at 60) and the follow-up deadline (60).",
   "The follow-up for sedation after the tube and its satisfiers.",
   "The coverage row: labetalol_bolus covering every catalog antihypertensive the case names.",
   "Everything the neurosurgeon, the intensivist, the trauma surgeon and the neurologist say.",
   "That the operating room is the correct disposition and that nothing else is defensible.",
   "Both diagnosis lists, including severe traumatic brain injury as defensible.",
   "The interview in full, every model-added positive and denial, interview.key_topics and interview.must_ask.",
   "Every debrief note and every handoff explanation.",
 ],
 "reference_status": [
   {"reference": ("Bullock MR, Chesnut R, Ghajar J, et al. Surgical management of acute epidural "
                  "hematomas. Neurosurgery 2006, 58(3 Suppl), S7-15"),
    "how_read": "Through a summarizing tool (a Medbullets evidence page), by a model on 19 October 2026. The paper was not opened",
    "status": "The quoted recommendations are the tool's. No evidence grade was visible. Not checked by a physician"},
   {"reference": "Brain Trauma Foundation. Guidelines for the Management of Severe Traumatic Brain Injury, 4th edition, 2016",
    "how_read": ("The PDF came back truncated. The blood pressure recommendation was read through "
                 "a UMEM educational pearl, through a summarizing tool, by a model on 19 October 2026"),
    "status": "Only the SBP floor (110 mmHg at ages 15 to 49, Level III) is used. Not checked by a physician"},
   {"reference": "CRASH-3 trial collaborators. Lancet 2019",
    "how_read": "Through a summarizing tool (The Bottom Line summary), by a model on 19 October 2026",
    "status": "The figures in the tranexamic acid note are the summary's. Not checked by a physician"},
   {"reference": "Stair R. Epidural Hematoma With Coma. MedEdPORTAL 2007, 3, 702",
    "how_read": "Abstract only",
    "status": "Used only to note that a published case requires a consultant call. Nothing quoted"},
   {"reference": "Teaching on ATLS airway thresholds, mannitol for acute deterioration, cervical spine clearance, Cushing's response, uncal herniation, the lucid interval, head-of-bed elevation, hypotonic fluid, NSAIDs, induction agents and post-intubation sedation",
    "how_read": "From memory. No source opened",
    "status": "Written by a model. Unverified. Each note carries a marker where the field allows one"},
 ],
 "reference_status_note": (
   "Markers sit only where the interface strips them: action debrief notes, timed transition "
   "notes and the cross-cutting teaching points. Handoff explanations and the follow-up note "
   "are printed as written. The disposition explanations that cite the size criteria rest on "
   "the first entry above."),
 "catalog_change_requests": [
   "A 'raise head of bed' action. Only lowering exists.",
   "Diagnosis entries for a calvarial (temporal squamous) skull fracture and for moderate traumatic brain injury.",
   "A ventilator setting or hyperventilation order, for the herniation bridge.",
   "A trauma team activation action.",
   "The hypertonic saline entry is labeled 25%. The common concentration is 23.4%. The voice aliases already accept '23.4'.",
 ],
}
