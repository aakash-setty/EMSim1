#!/usr/bin/env python3
"""Scaffold a new case pack.

    python3 engine/new_case.py CHFE                 (inspect an existing pack)
    python3 engine/new_case.py PE "Acute pulmonary embolism"

Writes `cases/<PREFIX>/` containing a skeleton case file, an empty binding map, an
empty scenario list and an empty test file, each carrying the section references
from `docs/case-authoring-requirements.md` for the author to fill in.

The skeleton is deliberately incomplete and will fail the validator until it is
authored. That is the intent: the validator's error list is the authoring to-do
list, and a skeleton that passed would be a skeleton that taught nothing.

Nothing clinical is generated here. Every field the skeleton contains is either
structural, or a placeholder marked TODO with the section that explains it.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paths import CASES_DIR, catalog_path, list_packs, CasePack


def todo(section, what):
    return f"TODO ({section}): {what}"


def skeleton(prefix, title):
    """Structure only. Every clinical field is a marked placeholder."""
    return {
        "case_id": prefix.lower(),
        "schema_version": "0.3",
        "authored_against": {
            "system_design": "system-design-v2.md (v0.4)",
            "authoring_requirements": "case-authoring-requirements.md (v0.3)",
            "action_catalog": "action-catalog.json",
            "diagnosis_catalog": "diagnosis-catalog.json",
        },
        "provenance": {
            "status": "SKELETON. Not authored, not reviewed, not playable.",
            "warning": "This case has no clinical content yet.",
            "author_only_fields_pending_signoff": ["everything"],
        },
        "metadata": {
            "working_title": title or todo("3.1", "one-line title as the chart would read"),
            "chief_complaint_patient_voice": todo("3.1", "what the patient says, in their words"),
            "final_diagnosis": todo("3.1", "diagnosis catalog id, not free text"),
            "target_level": [todo("3.1", "medical_student | intern | junior_resident | senior_resident")],
            "estimated_runtime_seconds": 480,
            "learning_objectives": [todo("3.1", "three to six objectives")],
            "care_setting": {
                "label": "Quaternary care, Level 1 trauma centre",
                "detail": ("Adult emergency department. Full laboratory, imaging and blood bank on "
                           "site. Change this if the case depends on a resource-limited setting, "
                           "because the correct disposition depends on it."),
            },
            "arrival": {
                "mode": todo("3.2", "Ambulance | Walk-in | Transfer | Police"),
                "line": todo("3.2", "one line on how they reached you"),
            },
        },
        "tag_vocabulary": {
            "values": ["critical", "recommended", "discouraged", "harmful", "neutral"],
            "note": "Section 7.3. Use discouraged for traps that are wrong but not lethal.",
        },
        "patient": {
            "age": None, "sex": None, "weight_kg": None,
            "background": todo("3.2", "relevant history in one paragraph"),
            "presenting_appearance": todo("3.2", "one or two sentences"),
            "ems_handover_text": todo("3.2", "the handover as it would be given"),
        },
        "phases": [
            {
                "id": "presentation",
                "label": "On arrival",
                "short_label": "on arrival",
                "clinical_description": todo("3.3", "one line"),
                "vitals": {"heart_rate": None, "systolic_bp": None, "diastolic_bp": None,
                           "respiratory_rate": None, "oxygen_saturation": None,
                           "temperature_c": None},
                "appearance": {"distress_level": None, "alertness_level": None,
                               "pupil_size": "normal", "pupil_reactivity": "reactive"},
                "transitions": [
                    {"when": todo("5", "condition on this phase's critical actions"),
                     "to": "improving"},
                    {"when": "action handoff_submit taken", "to": "case_complete"},
                ],
                "terminal": False,
            },
            {
                "id": "improving",
                "label": "Responding to treatment",
                "short_label": "responding",
                "clinical_description": todo("3.3", "one line"),
                "vitals": {"heart_rate": None, "systolic_bp": None, "diastolic_bp": None,
                           "respiratory_rate": None, "oxygen_saturation": None,
                           "temperature_c": None},
                "appearance": {"distress_level": None, "alertness_level": None,
                               "pupil_size": "normal", "pupil_reactivity": "reactive"},
                "transitions": [{"when": "action handoff_submit taken", "to": "case_complete"}],
                "terminal": False,
            },
            {
                "id": "halted", "label": "Stopped", "short_label": "stopped",
                "clinical_description": "Terminal. Reached by any harmful action.",
                "vitals": {"heart_rate": 0, "systolic_bp": 0, "diastolic_bp": 0,
                           "respiratory_rate": 0, "oxygen_saturation": 0, "temperature_c": 36.5},
                "appearance": {"distress_level": 3, "alertness_level": 3,
                               "pupil_size": "large", "pupil_reactivity": "fixed"},
                "transitions": [], "terminal": True,
            },
            {
                "id": "case_complete", "label": "Handed over", "short_label": "handed over",
                "clinical_description": "Terminal. Reached by handoff.",
                "vitals": {"heart_rate": None, "systolic_bp": None, "diastolic_bp": None,
                           "respiratory_rate": None, "oxygen_saturation": None,
                           "temperature_c": None},
                "appearance": {"distress_level": 0, "alertness_level": 0,
                               "pupil_size": "normal", "pupil_reactivity": "reactive"},
                "transitions": [], "terminal": True,
            },
        ],
        "case_actions": [
            {
                "catalog_id": "handoff_submit",
                "display_name": "Submit handoff",
                "tag": [{"when": None, "value": "neutral"}],
                "debrief_note": "Ends the case.",
            }
        ],
        "follow_ups": [],
        "content_keys": {
            "general_status": {
                "authoring_note": "Section 11.3. Rendered above the exam list and not skippable.",
                "rules": [{"when": None,
                           "value": {"kind": "general_status", "abnormal": False,
                                     "findings": todo("11.3", "what you see from the end of the bed")}}],
            },
            "exam": {"authoring_note": "Section 11.2. Only the 14 catalog maneuvers. Follow exam_finding_routing."},
            "labs": {"authoring_note": "Section 11.4. Structured payloads with abnormal flags."},
            "imaging": {"authoring_note": "Section 11.4."},
            "consultants": {"authoring_note": "Section 11.5. Author a pending tier."},
        },
        "interview": {
            "global_answer_rules": [],
            "out_of_scope_fallback": [{"when": None,
                                       "value": todo("10.3", "non-committal reply revealing nothing")}],
            "topics": [],
        },
        "handoff": {
            "correct_disposition": {"id": todo("12", "disposition id"),
                                    "label": todo("12", "label"),
                                    "explanation": todo("12", "why this is right")},
            "alternative_dispositions": [],
            "disposition_display_order": [todo("12", "disposition ids, least to most intensive")],
            "correct_diagnosis": {"catalog_id": todo("12", "diagnosis catalog id"),
                                  "label": todo("12", "label"),
                                  "explanation": todo("12", "why this is right")},
            "alternative_diagnoses": [],
        },
        "debrief_configuration": {
            "intended_path": ["presentation", "improving", "case_complete"],
            "clinical_domains": [
                {"id": "examination", "label": "Physical examination", "actions": []},
                {"id": "disposition_and_communication", "label": "Disposition and communication",
                 "actions": ["handoff_submit"]},
            ],
            "trap_actions": [],
            "cross_cutting_teaching_points": [],
        },
        "prompt_cap_recommendation": {"per_phase": 3},
    }


BINDING_MAP = {
    "map_version": "0.1",
    "status": "SKELETON. One row per case action. See section 7.2.",
    "how_to_read": {
        "catalog_id equals case_id": "exact, nothing to review",
        "catalog_id differs": "mapped; the note says why, and it needs the author's signature",
        "catalog_id null": "unmatched; a validator error and a catalog change request",
    },
    "rows": [{"case_id": "handoff_submit", "catalog_id": None,
              "note": "The catalog has no handoff action; listed in its own known_gaps."}],
}

SCENARIOS = {
    "scenarios_version": "0.1",
    "note": ("End-to-end paths. Cover the intended path, every harmful halt, every blocked "
             "prerequisite, every deterioration branch and its rescue, and any ordering a "
             "resident is likely to produce. See system-design section 13.3."),
    "scenarios": [],
}


def case_tests(prefix):
    return f"""/* Case assertions for {prefix}.
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk and the engine.
 * Anything naming a specific drug, study or phase belongs here rather than in the
 * engine suite.
 *
 * Write one section per clinical claim the case makes. At minimum:
 *   - the intended path reaches the resolution phase
 *   - every harmful action halts, from a state a resident could actually be in
 *   - every prerequisite blocks, and stops blocking once satisfied
 *   - findings change after successful treatment
 *   - the handoff completes
 */

section('intended path');
chk('TODO: write the intended path assertion', false);
"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("existing packs:", ", ".join(list_packs()) or "(none)")
        return 0

    prefix = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None

    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", prefix):
        raise SystemExit("prefix must be 2 to 10 upper-case letters or digits, for example CHFE or PE")

    if prefix in list_packs():
        pk = CasePack(prefix)
        print(f"{prefix} already exists at {pk.dir}")
        for f in sorted(os.listdir(pk.dir)):
            print("  ", f)
        return 1

    d = os.path.join(CASES_DIR, prefix)
    os.makedirs(d)
    pk = CasePack.__new__(CasePack)
    pk.dir, pk.prefix = d, prefix

    json.dump(skeleton(prefix, title), open(pk.case, "w"), indent=1)
    json.dump(dict(BINDING_MAP, case_id=prefix.lower()), open(pk.binding_map, "w"), indent=1)
    json.dump(dict(SCENARIOS, case_id=prefix.lower()), open(pk.scenarios, "w"), indent=1)
    open(pk.tests, "w").write(case_tests(prefix))

    catalog = json.load(open(catalog_path("action-catalog.json")))
    exams = sorted(x["id"] for x in catalog["entries"] if x["category"] == "exam")
    routing = catalog.get("exam_finding_routing", {})

    open(os.path.join(d, f"{prefix}-SEED.md"), "w").write(f"""# {prefix} author's seed

Fill this in before any drafting. Section numbers refer to
`docs/case-authoring-requirements.md`. About an hour for a case you know well.

## 3.1 Case identity
- Working title:
- Chief complaint, patient's words:
- Final diagnosis (diagnosis catalog id):
- Learning objectives (three to six):
- Target level:

## 3.2 Patient
- Age, sex, weight:
- Background:
- Presenting vitals:
- Presenting appearance:
- How they arrived, and the care setting if it is not a quaternary centre:

## 3.3 Phases (three to six clinical, plus the two terminals)
For each: label, one-line description, and the six vital signs.
At least one resolution phase. A deterioration phase if deterioration is plausible.
**Every deterioration branch needs an exit action that exists in the catalog.**

## 3.4 The action spine
- Critical, and in which phase each becomes critical, and which are time-sensitive:
- Harmful, with a one-line reason for each:
- Discouraged, meaning wrong but not lethal:
- Recommended:
- Traps, and why they look right:

For every harmful and discouraged action, **name every catalog route to it**.
A bolus and an infusion are different entries. Saline and Ringer's are different entries.

## 3.5 Sequencing
- Prerequisites specific to this case:
- Follow-ups, and whether they apply here:
- Catalog prerequisites to waive here, and why:

## 3.6 Key findings
For each abnormal value: the number, the units, the reference interval, and confirmation
that it is abnormal. For each exam finding, the finding; routing is below.

## 3.7 Interview ground truth
The history as a list of facts. **Pertinent negatives listed explicitly.**

## 3.8 Disposition
Correct level of care and correct diagnosis, plus the plausible wrong answers and why.

---

## The exam maneuvers available to you

The catalog set is closed. These are the only maneuvers a resident can perform:

{chr(10).join('- `' + e + '`' for e in exams)}

Plus a general status line above them, which is not clickable and cannot be skipped.

## Where findings go

Follow this map even where you would have chosen differently, so that a resident
learns where to look rather than learning that the tool is arbitrary.

{chr(10).join('- ' + k + ' -> `' + v + '`' for k, v in routing.items())}
""")

    print(f"created {os.path.relpath(d, os.path.dirname(HERE))}/")
    for f in sorted(os.listdir(d)):
        print("  ", f)
    print(f"""
next:
  1. fill in {prefix}-SEED.md                      (author, about an hour)
  2. draft {prefix}-case.json from the seed
  3. python3 engine/bind_catalog.py cases/{prefix}
  4. python3 engine/validate_case.py cases/{prefix}   until the only errors are catalog requests
  5. python3 engine/build_simulator.py
  6. python3 engine/sim_runner.py   cases/{prefix}
  7. node    engine/engine-tests.js build/simulator.html cases/{prefix}/{prefix}-tests.js {prefix}
  8. read {prefix}-review-matrix.md in full, then play the case, then sign off""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
