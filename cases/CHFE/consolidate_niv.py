#!/usr/bin/env python3
"""ONE-TIME MIGRATION, already applied to CHFE-case.json. Kept as the record of what
changed and why; re-running it on an already-migrated file refuses rather than acting.

Consolidate `niv_cpap` and `niv_bipap` into one case action, `niv_bipap_cpap`.

WHY
Both bound to the single catalog entry `non_invasive_positive_pressure_ventilation`.
The engine maps one catalog entry to one case action, so the second was never in the
action surface at all: its tag, its debrief note and its two references were unreachable
by any learner, and `shadowed` recorded that fact rather than fixing it.

The consequence was not only cosmetic. `CHFE-scenarios.json` contained a step naming
`niv_bipap`, which the engine discarded silently, so that scenario reached `presentation`
while expecting `stabilizing` and had been failing for the wrong reason. Two tests were
added alongside this migration: one asserting the old ids are gone, and a generic one in
`sim_runner.py` reporting any scenario step that names an action the case does not hold.

WHAT WAS PRESERVED
The two notes taught different things and both are kept. The CPAP note carried the
mechanism and the honest 3CPO framing. The BiPAP note carried the point that existed
nowhere else: bilevel adds inspiratory support and is often preferred when the patient is
hypercapnic and tiring, as this one is with a pCO2 of 54, and 3CPO found no difference
between the modes. That paragraph now reads as a choice-between-modes note, which is the
right shape when it is one button. Both references are kept, deduplicated.

IF THE CATALOG EVER SPLITS THE MODES
Add the two entries to the `non_invasive_ventilation` equivalence group and bind this
action to the group with `also_covers_group`. Do not reintroduce two case actions.
Binding through the group today would be a no-op, because the group has one member, and
it would set a misleading `covered_by` annotation on the button.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "CHFE-case.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else CASE

MIGRATION_MARKER = "consolidate_niv"
NEW_ID = "niv_bipap_cpap"
OLD = ("niv_cpap", "niv_bipap")

MERGED_NOTE = (
    "Non-invasive positive pressure ventilation is the single highest-value early "
    "intervention in acute cardiogenic pulmonary oedema. It recruits flooded alveoli, "
    "reduces the work of breathing, and by raising intrathoracic pressure it reduces both "
    "preload and left ventricular transmural pressure, which lowers afterload. Applying it "
    "early is what allows most of these patients to avoid an endotracheal tube. "
    "Be honest with learners about the evidence: earlier meta-analyses reported reductions "
    "in intubation and mortality, but the largest randomised trial, 3CPO, found no "
    "difference in seven-day mortality or intubation rate versus standard oxygen therapy. "
    "The strongest defensible claim is faster symptomatic and physiological improvement, "
    "with intubation avoidance supported by meta-analytic but not by the single largest "
    "trial. "
    "On the choice between modes, which is one button here because it is one decision: "
    "continuous and bilevel positive pressure are equivalent for the purposes of this case. "
    "Bilevel adds inspiratory support and is often preferred when the patient is "
    "hypercapnic and tiring, as this one is with a pCO2 of 54. 3CPO found no difference "
    "between the two modes in mortality or intubation rate, so either is defensible and the "
    "decision that mattered was to apply positive pressure at all. The historical concern "
    "that bilevel increased myocardial infarction has not been borne out."
)


def refuse_if_already_migrated(case):
    if MIGRATION_MARKER in (case.get("migrations") or []):
        raise SystemExit(
            f"{MIGRATION_MARKER} has already been applied to this case file. "
            f"Re-running would overwrite the merged note. Nothing was changed.")


def main():
    case = json.load(open(CASE))
    refuse_if_already_migrated(case)

    acts = case["case_actions"]
    idx = {a["catalog_id"]: i for i, a in enumerate(acts)}
    for o in OLD:
        assert o in idx, f"{o} is not in this case; nothing to consolidate"

    cpap, bipap = acts[idx["niv_cpap"]], acts[idx["niv_bipap"]]
    # they differed only in display name, note and references; if anything else differs
    # the merge is a clinical decision and must not be automated
    for field in ("tag", "flags_set", "prerequisites"):
        assert cpap.get(field) == bipap.get(field), (
            f"{field} differs between the two NIV actions; merge them by hand")

    merged = dict(cpap)
    merged["catalog_id"] = NEW_ID
    merged["display_name"] = "Positive pressure ventilation (BiPAP/CPAP)"
    merged["debrief_note"] = MERGED_NOTE
    acts[idx["niv_cpap"]] = merged
    acts.pop(idx["niv_bipap"])

    for d in case.get("debrief_configuration", {}).get("clinical_domains", []):
        if any(o in d["actions"] for o in OLD):
            d["actions"] = [NEW_ID if a == "niv_cpap" else a
                            for a in d["actions"] if a != "niv_bipap"]

    case.setdefault("migrations", [])
    if MIGRATION_MARKER not in case["migrations"]:
        case["migrations"].append(MIGRATION_MARKER)
    json.dump(case, open(OUT, "w"), indent=1)
    print(f"consolidated the two NIV actions into {NEW_ID}; "
          f"{len(acts)} case actions remain")
    print("the binding, the binding map, the scenarios and the tests reference the new id "
          "and were updated alongside this; they are not rewritten here")


if __name__ == "__main__":
    main()
