"""SWEET part 5: handoff, debrief configuration, provenance."""

HANDOFF = {
 "correct_disposition": {
   "id": "picu",
   "label": "Pediatric intensive care unit",
   "level_of_care": "critical_care",
   "explanation": (
     "He goes to the PICU on the epinephrine infusion. It is weaned there over hours, with "
     "continuous monitoring, and he is watched for a second reaction.\n\n"
     "What the receiving team needs to hear: peanut, the time of the dessert, the crew's dose "
     "and the time, the ED dose and the time, that the reaction came back after each, when "
     "the infusion started and its rate, how much fluid he has had, his airway findings, and "
     "his mother's phone number.")},

 "alternative_dispositions": [
   {"id": "discharge_home", "label": "Discharge home", "verdict": "incorrect",
    "explanation": "A child on an epinephrine infusion after refractory anaphylaxis cannot go home."},
   {"id": "observation_unit", "label": "Emergency department observation unit", "verdict": "incorrect",
    "explanation": ("Observation suits a reaction that settled after one dose. He needed two IM "
                    "doses and an infusion.")},
   {"id": "medical_floor_telemetry", "label": "Pediatric ward with monitoring", "verdict": "incorrect",
    "explanation": "A ward does not run an epinephrine infusion that still needs titrating."},
   {"id": "stepdown_telemetry", "label": "Step-down or intermediate care", "verdict": "incorrect",
    "explanation": "Titrating an epinephrine infusion in a child with an airway at risk is intensive care."},
 ],
 "disposition_display_order": ["discharge_home", "observation_unit", "medical_floor_telemetry",
                               "stepdown_telemetry", "picu"],

 "correct_diagnosis": {
   "catalog_id": "dx_anaphylaxis",
   "label": "Anaphylaxis",
   "explanation": (
     "Peanut, then within minutes hives, lip and eyelid swelling, wheeze and a pressure "
     "under 90 at 12 years. Refractory: two appropriate IM doses of epinephrine without a "
     "lasting response.")},

 "minor_diagnoses": [
   {"catalog_id": "dx_food_allergy", "label": "Food allergy",
    "explanation": "Peanut, known since age three. True, and the trigger, not the emergency."}],

 "alternative_diagnoses": [
   {"catalog_id": "dx_angioedema", "label": "Angioedema", "verdict": "acceptable_with_qualification",
    "explanation": ("His lips and eyelids are swollen, and that is part of the picture. With the "
                    "wheeze and the low pressure, it is anaphylaxis.")},
   {"catalog_id": "dx_asthma_exacerbation", "label": "Asthma exacerbation", "verdict": "incorrect",
    "explanation": ("He is wheezing, and he has no asthma. Hives, swelling and a low pressure "
                    "after peanut are not asthma.")},
   {"catalog_id": "dx_status_asthmaticus", "label": "Status asthmaticus", "verdict": "incorrect",
    "explanation": "The wheeze is real. The cause is anaphylaxis, and the treatment is epinephrine."},
   {"catalog_id": "dx_urticaria", "label": "Urticaria", "verdict": "incorrect",
    "explanation": "The hives are the least dangerous part of this. Name what threatens him."},
   {"catalog_id": "dx_foreign_body_aspiration", "label": "Foreign body aspiration", "verdict": "incorrect",
    "explanation": "He ate and then could not breathe, but the hives, swelling and low pressure point elsewhere."},
   {"catalog_id": "dx_panic_attack", "label": "Panic attack", "verdict": "incorrect",
    "explanation": "He is frightened because he cannot breathe. His pressure is low."},
   {"catalog_id": "dx_undifferentiated_shock", "label": "Undifferentiated shock", "verdict": "incorrect",
    "explanation": "The shock has a cause in front of you."}],

 "diagnosis_entry_method": "The learner searches the whole diagnosis catalog and lists as many as apply.",
 "early_exit": {"available": True, "note": "Produces a debrief marked incomplete."},
}

DEBRIEF = {
 "clinical_domains": [
   {"id": "first", "label": "The first minutes",
    "actions": ["epinephrine_intramuscular", "exam_airway", "normal_saline_500ml_bolus",
                "reassessed_after_epi", "lay_back_legs_raised", "attach_monitor", "insert_iv",
                "second_iv"]},
   {"id": "refractory", "label": "When it does not hold",
    "actions": ["epinephrine_drip", "consult_critical_care", "bolus_here_p3", "fluid_here_p5",
                "drip_restarted"]},
   {"id": "rescue", "label": "At the edge",
    "actions": ["epi_here_p4", "bolus_here_p4", "bridge_here_p7", "intubate_rapid_sequence"]},
   {"id": "adjuncts", "label": "Adjuncts in their place",
    "actions": ["albuterol", "diphenhydramine", "famotidine_bolus", "methylprednisolone_bolus",
                "dexamethasone", "hydrocortisone_bolus", "glucagon"]},
   {"id": "harm", "label": "What made it worse",
    "actions": ["lorazepam_bolus", "morphine_bolus", "midazolam_bolus", "epinephrine_bolus",
                "norepinephrine_drip", "nasal_cannula_oxygen", "stop_epinephrine",
                "normal_saline_infusion"]},
   {"id": "history", "label": "The history",
    "actions": ["interview_topic_epi_given", "interview_topic_allergies"]},
   {"id": "people", "label": "Disposition",
    "actions": ["handoff_submit"]},
 ],
 "key_exams": ["exam_airway", "exam_breath", "exam_circ", "exam_pulm", "exam_skin", "exam_neuro"],
 "key_exams_note": "The six recommended exams. Model judgment.",
 "intended_path": ["presentation", "persistent", "responding", "stabilized", "case_complete"],
 "intended_path_note": (
   "IM epinephrine on arrival, the airway examined, a bolus, with the monitor, posture and two "
   "lines. When it wears off, look at him again, order the infusion and call PICU. A second "
   "bolus. Albuterol for the wheeze. PICU."),
 "trap_actions": ["diphenhydramine", "methylprednisolone_bolus", "lorazepam_bolus", "norepinephrine_drip",
                  "epinephrine_bolus"],
 "cross_cutting_teaching_points": [
   ("A drug that helped and then stopped helping has not finished its job. Give it once more, "
    "on time, and when that fails too, change how you give it rather than what you give."),
   ("Epinephrine before arrival is one dose, not completed treatment. Repeat it in the thigh "
    "now, before any antihistamine, steroid or nebulizer. [UNVERIFIED: Resuscitation Council "
    "UK anaphylaxis algorithm 2021, read through search]"),
   ("Read a child's numbers against his age. At 12, a systolic under 90 is hypotension and a "
    "heart rate of 140 is tachycardia. A child who stops talking and stops asking for his "
    "parent is getting worse, whatever the monitor says. [UNVERIFIED: PALS 2015 vital sign "
    "tables as reproduced by PedsCases]"),
   ("After two IM doses without a lasting response, start the infusion and call for help, "
    "and keep giving IM doses until it runs. [UNVERIFIED: "
    "Resuscitation Council UK refractory anaphylaxis algorithm 2021, read through search]"),
   ("Anaphylactic shock needs volume and posture: two lines, weight-based boluses, and lying "
    "flat with the legs up. Never sit or stand a hypotensive child. [UNVERIFIED: Pumphrey, J "
    "Allergy Clin Immunol 2003, read through BestBETs]"),
   ("State the weight before any drug or fluid. This simulator does not take doses, so it is "
    "taught here: IM epinephrine 0.01 mg/kg (0.4 mg at 40 kg, 0.3 to 0.5 mg acceptable), "
    "boluses of 10 to 20 mL/kg, an infusion from about 0.1 microgram/kg/min."),
 ],
 "attempt_history_note": "Blocked attempts (the infusion without a monitor or a second line) are surfaced and not penalized.",
}

PROVENANCE = {
 "status": ("DRAFTED BY A LANGUAGE MODEL. Not reviewed by a physician. Not for use with "
            "learners until the section 11.5 checklist is complete."),
 "author": ("Drafted by Claude at the request of Aakash Setty on 11 November 2026, from his "
            "case structure and his answers to three rounds of questions the same day. "
            "Authoring requirements section 1 applies."),
 "warning": (
   "A physician decided the things listed in SWEET-SEED.md section 0. Everything else is "
   "model output and awaits sign-off: every vital sign, finding, laboratory value, delay, "
   "tag, debrief note, interview answer and diagnosis explanation."),
 "author_only_fields_pending_signoff": [
   "Every vital sign in every phase. Phases 1 to 6 are the owner's S1 to S6, with temperature 37.1 added. Phases 7 and 8, relapse, vent_relapse and the terminal phase are model output.",
   "Every delay: the first IM dose acting from 10 seconds and fading from 40 to 60, a later dose from 10 and fading from 25 to 40, the 150 and 240 second exits from phase 2, the infusion's 10 second preparation and 10 second restart, the phase 3 exits (150, 240, 360), the relapse exits (150, 240, 360), the rescue at 30 seconds, the 180 seconds to the terminal phase, the 150 seconds after a tube with no bridge or after a stop with no restart, the 120 seconds after a stop, phase 5 to 6 at 180 seconds.",
   "Every laboratory value and interval, including the pediatric intervals.",
   "Every abnormal flag on every result, finding and status line.",
   "The vital effects of IM epinephrine, the IV push, the boluses, posture, albuterol and the oxygen devices. Teaching choices.",
   "That a sedative moves him one phase worse at once in phases 1 to 3.",
   "The infusion's two prerequisites (monitor, second line) and their messages.",
   "Every clinical tag, every prompt deadline and every prompt text.",
   "Every consultant line.",
   "The interview in full, including the model-added facts and denials (SWEET-SEED.md 3.7).",
   "interview.key_topics, interview.must_ask and debrief_configuration.key_exams.",
   "Both diagnosis lists and every disposition explanation.",
   "Every debrief note.",
 ],
 "reference_status": [
   {"reference": "Resuscitation Council UK. Anaphylaxis algorithm and refractory anaphylaxis algorithm, 2021 (in the paediatric emergency algorithms, March 2022 and June 2024)",
    "how_read": "PDF text read by a model through search on 11 November 2026",
    "status": "Refractory after two IM doses, IM every 5 minutes until the infusion runs, infusion 1 mg in 100 mL at 0.5 to 1 mL/kg/hour, child bolus 10 mL/kg, lie flat, IV boluses not recommended, nebulized epinephrine for stridor. Not checked by a physician"},
   {"reference": "Shaker MS, et al. Anaphylaxis: a 2020 practice parameter update. J Allergy Clin Immunol 2020;145:1082-1123",
    "how_read": "Read through the Cleveland Clinic Journal of Medicine summary (2022) and a Children's Mercy summary, via search",
    "status": "IM dose 0.01 mg/kg, maximum 0.5 mg adult and 0.3 mg child. No benefit of antihistamines or glucocorticoids in preventing biphasic reactions. Unverified against the paper"},
   {"reference": "Golden DBK, et al. Anaphylaxis: a 2023 practice parameter update. Ann Allergy Asthma Immunol 2024;132:124-176",
    "how_read": "Abstract and first page only, via search",
    "status": "Not used for any claim"},
   {"reference": "Pumphrey RSH. Fatal posture in anaphylactic shock. J Allergy Clin Immunol 2003;112:451-452",
    "how_read": "Read through BestBETs, via search",
    "status": "Deaths within seconds of a move to a more upright posture. Case series. Not opened"},
   {"reference": "Campbell RL, et al. Epinephrine in anaphylaxis: higher risk of cardiovascular complications and overdose after administration of intravenous bolus epinephrine compared with intramuscular epinephrine. J Allergy Clin Immunol Pract 2015;3:76-80",
    "how_read": "Abstract and a news summary, via search",
    "status": "All overdoses after IV boluses. Not opened"},
   {"reference": "PALS 2015 normal vital sign tables",
    "how_read": "As reproduced by PedsCases and the University of Calgary, via search. Not the AHA source",
    "status": "Used for the age bands in SHARED.vital_normals and the debrief. Not checked by a physician"},
   {"reference": "Johns Hopkins All Children's Hospital anaphylaxis pathway, July 2023",
    "how_read": "PDF text via search",
    "status": "20 mL/kg boluses to 1 L, albuterol, glucagon only on beta-blockers. Not checked"},
   {"reference": "Strother C, Webb T. EM ReSCu Peds case 1: Anaphylaxis. ALiEM",
    "how_read": "Page summary via search",
    "status": "Published simulation source for goals 1 and 4. Not checked"},
   {"reference": "Reid J, Stone K. Pediatric Emergency Medicine Simulation Curriculum: Anaphylaxis. MedEdPORTAL 2013;9:9638",
    "how_read": "Abstract only",
    "status": "Published simulation source. Not opened"},
   {"reference": "PALS bradycardia guidance, difficult pediatric airway teaching, sedation and glucagon notes",
    "how_read": "From memory. No source opened",
    "status": "Written by a model. Unverified. Marked where the field allows"},
 ],
 "reference_status_note": (
   "Markers sit only where the interface strips them: action debrief notes, timed "
   "transition notes and the cross-cutting teaching points."),
 "catalog_change_requests": [
   "A dose field on dose_required entries with a per-case accepted range (owner, 11 November 2026: deferred, debrief only for now).",
   "Call for senior help, as an action of its own. consult_critical_care stands for it here.",
   "A PICU consultant, or a pediatric label for critical care.",
   "Supine with legs elevated. A case-only button stands for it here.",
   "Titrate an infusion, so the case can gate stabilization on titration (also asked for by TIDE).",
   "Nebulized epinephrine, for stridor.",
   "Video laryngoscopy, oral and nasal airways, and an anesthesia or ENT consultant.",
   "A pediatric chest film, and pediatric twelve-lead tracings, for the picture defaults.",
   "Serum tryptase (optional; not needed to run the case).",
   "A 'prepare infusion' concept, so an infusion's preparation time is a catalog property. This pack builds it from two expiring flags.",
   "The ungraded intubation-care list makes midazolam and fentanyl unscorable when given as sedatives with no tube to follow.",
 ],
}
