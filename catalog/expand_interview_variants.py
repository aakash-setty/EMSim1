#!/usr/bin/env python3
"""Report or rewrite the interview expansion of one of the FROZEN packs (AFRVR, CHFE, DIPH,
MGCA). Every other pack expands at build time: its topic map lives in its own
`case_4_interview.py` (TOPIC_MAP and EXTRA_COVERED) and `cases/<PREFIX>/build_case.py`
calls `catalog/interview_expand.py`. Nothing per pack is added to this file any more.

    python3 catalog/expand_interview_variants.py AFRVR --dry-run   report, write nothing
    python3 catalog/expand_interview_variants.py AFRVR --force     rewrite a frozen pack

The four packs here were edited by hand after they were last expanded, so a run today
changes their sources and their tuning sets (found by the October 2026 audit; decision of
7 October 2026 to freeze them). The command refuses to write without --force.

What --force writes, per pack:

  cases/<PREFIX>/case_4_interview.py   for AFRVR and DIPH: an EXPANDED block and an
                                       OUT_OF_SCOPE_BANK list between marker comments.
  cases/<PREFIX>/<PREFIX>-case.json    for CHFE and MGCA: topics[].expanded_variants (never
                                       the hand-written `variants`), a `variants_provenance`
                                       note on each topic, and `interview.out_of_scope_bank`.
  cases/<P>/<P>-matcher-tune-questions.json
                                       the withheld slice (see interview_expand.py).

The algorithm is `catalog/interview_expand.py`, shared with the build-time route.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from interview_expand import expand_topics, report, tune_file, PROVENANCE, OOS_BANK_NOTE   # noqa: E402

# ---------------------------------------------------------------- topic -> concepts
# One entry per FROZEN pack. A topic may draw on several concepts. Topics absent from the
# map are left alone, which is how a pack-specific topic with no shared phrasings
# stays hand-authored. Do not add a pack here: put TOPIC_MAP in its case_4_interview.py.
MAP = {
 "AFRVR": {
  "onset": ["onset"], "timing_progression": ["timing_progression"],
  "character_of_palpitations": ["character_palpitations"], "dyspnea_character": ["character_dyspnea", "breathing_sob"],
  "severity": ["severity"], "aggravating_factors": ["aggravating"], "relieving_factors": ["relieving"],
  "chest_pain": ["chest_pain"], "syncope_presyncope": ["syncope"], "dizziness_lightheadedness": ["dizziness"],
  "orthopnea": ["orthopnea"], "paroxysmal_nocturnal_dyspnea": ["pnd"], "leg_swelling": ["leg_swelling"],
  "weight_gain": ["weight_gain"], "exercise_tolerance_baseline": ["functional_baseline"],
  "cough_and_sputum": ["cough_sputum"], "fever_and_chills": ["fever_chills"],
  "prior_afib_or_palpitations": ["prior_afib"], "prior_heart_failure": ["prior_hf"],
  "past_medical_history": ["pmh"], "past_surgical_history": ["psh"], "current_medications": ["meds"],
  "anticoagulant_history_and_bleeding": ["anticoag"], "medication_adherence": ["adherence"],
  "allergies": ["allergies"], "alcohol_and_binge": ["alcohol"], "caffeine_and_stimulants": ["caffeine_stimulants"],
  "thyroid_symptoms": ["thyroid"], "social_history_smoking": ["smoking"], "family_history": ["family_history"],
  "last_oral_intake": ["last_oral_intake"], "recent_illness_or_sick_contacts": ["recent_illness_sick_contacts"],
  "travel_immobility_surgery": ["travel_immobility_surgery"], "calf_pain_or_asymmetry": ["calf_pain"],
  "urine_output": ["urine_output"], "nausea_and_vomiting": ["nausea_vomiting"],
  "snoring_and_sleep_apnea": ["snoring_osa"], "code_status_goals_of_care": ["code_status"],
 },
 "CHFE": {
  "onset": ["onset"], "timing_progression": ["timing_progression"], "character_of_dyspnea": ["character_dyspnea", "breathing_sob"],
  "severity": ["severity"], "aggravating_factors": ["aggravating"], "relieving_factors": ["relieving"],
  "orthopnea": ["orthopnea"], "paroxysmal_nocturnal_dyspnea": ["pnd"], "leg_swelling": ["leg_swelling"],
  "weight_gain": ["weight_gain"], "cough_and_sputum": ["cough_sputum"], "chest_pain": ["chest_pain"],
  "palpitations": ["palpitations"], "fever_and_chills": ["fever_chills"],
  "syncope_and_dizziness": ["syncope_dizziness", "syncope", "dizziness"], "nausea_and_vomiting": ["nausea_vomiting"],
  "abdominal_fullness": ["abdominal_fullness"], "urine_output": ["urine_output"],
  "calf_pain_or_asymmetry": ["calf_pain"], "travel_immobility_surgery": ["travel_immobility_surgery"],
  "hemoptysis": ["hemoptysis"], "medication_adherence": ["adherence"], "dietary_sodium": ["dietary_sodium"],
  "current_medications": ["meds"], "past_medical_history": ["pmh"], "past_surgical_history": ["psh"],
  "allergies": ["allergies"], "social_history_smoking_alcohol": ["smoking_alcohol", "smoking", "alcohol"],
  "substance_use_stimulants": ["substance_use", "caffeine_stimulants"], "family_history": ["family_history"],
  "last_oral_intake": ["last_oral_intake"], "sleep_apnea_and_snoring": ["snoring_osa"],
  "recent_illness_or_sick_contacts": ["recent_illness_sick_contacts"], "functional_baseline": ["functional_baseline"],
 },
 "DIPH": {
  "onset": ["onset"], "progression": ["timing_progression"],
  "last_seen_well": ["timing_progression"], "pain_anywhere": ["location_pain", "radiation_pain", "severity", "character_general"],
  "past_medical_history": ["pmh"], "past_surgical_history": ["psh"],
  "current_medications": ["meds"],
  "allergies": ["allergies"], "family_history": ["family_history"],
  "alcohol_and_drugs": ["alcohol", "substance_use"],
  "smoking": ["smoking"], "fever_or_infection": ["fever_chills", "recent_illness_sick_contacts"],
  "headache": ["headache"], "neck_stiffness": ["neck_stiffness", "photophobia"],
  "rash": ["rash"],
  "vomiting": ["nausea_vomiting"], "abdominal_pain": ["abdominal_pain"],
  "urinary_symptoms": ["dysuria_gu", "urine_output"],
  "chest_or_palpitations": ["chest_pain", "palpitations"],
  "breathing": ["breathing_sob"], "last_oral_intake": ["last_oral_intake"],
  "pregnancy": ["pregnancy", "menstrual_tampon", "sexual_history"],
  "travel_and_contacts": ["travel", "sick_contacts"], "immunizations": ["vaccinations"],
  "vision_or_hallucinations": ["confusion"], "sleep_and_appetite": ["functional_baseline"],
  "collateral_from_brother": ["sick_contacts"],
 },
 "MGCA": {
  "onset": ["onset"], "timing_progression": ["timing_progression"], "character_of_symptoms": ["character_general"],
  "location_of_pain": ["location_pain"], "radiation_of_pain": ["radiation_pain"], "severity": ["severity"],
  "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"], "rash": ["rash"],
  "fever_and_chills": ["fever_chills"], "headache": ["headache"], "neck_stiffness": ["neck_stiffness"],
  "photophobia": ["photophobia"], "nausea_vomiting": ["nausea_vomiting"], "diarrhea": ["diarrhea"],
  "abdominal_pain": ["abdominal_pain"], "chest_pain": ["chest_pain"], "breathing": ["breathing_sob"],
  "cough_sore_throat": ["cough_sore_throat"], "urine_output": ["urine_output"],
  "dizziness_syncope": ["syncope_dizziness", "syncope", "dizziness"], "confusion": ["confusion"],
  "cold_extremities": ["cold_extremities"], "joint_pain": ["joint_pain"], "dysuria_gu_symptoms": ["dysuria_gu"],
  "menstrual_and_tampon": ["menstrual_tampon"], "pregnancy": ["pregnancy"], "sexual_history": ["sexual_history"],
  "past_medical_history": ["pmh"], "past_surgical_history": ["psh"], "current_medications": ["meds"],
  "allergies": ["allergies"], "social_history": ["social_history", "smoking", "alcohol", "substance_use"],
  "family_history": ["family_history"], "last_oral_intake": ["last_oral_intake"], "vaccinations": ["vaccinations"],
  "sick_contacts": ["sick_contacts"], "travel_history": ["travel"], "tick_and_outdoor_exposure": ["tick_outdoor"],
  "recent_antibiotics_healthcare": ["recent_antibiotics_healthcare"], "functional_baseline": ["functional_baseline"],
  "code_status_goals": ["code_status"],
 },
}

# Concepts a pack's topics cover, used to filter the out-of-scope bank. Derived from
# MAP, plus concepts a topic covers without drawing phrasings from (e.g. AFRVR's chest
# pain topic answers location and radiation because the pain does not exist).
# A name here is a concept in interview_phrasings.py or a tag in BANK_ONLY_TAGS in
# interview_out_of_scope.py. Frozen packs only.
EXTRA_COVERED = {
  "AFRVR": ["location_pain", "radiation_pain", "palpitations", "breathing_sob", "smoking_alcohol", "social_history"],
  "CHFE": ["orthopnea", "palpitations", "smoking", "alcohol"],
  "MGCA": ["character_general"],
  "DIPH": ["character_general", "severity", "aggravating", "relieving", "aggravating_relieving",
           "location_pain", "radiation_pain", "smoking_alcohol", "social_history",
           "syncope", "dizziness", "syncope_dizziness", "adherence", "smoking_alcohol"],
}

# ---------------------------------------------------------------- helpers
def load_json(p):
    with open(p) as f: return json.load(f)

def save_json(p, o):
    with open(p, "w") as f:
        json.dump(o, f, indent=1, ensure_ascii=False); f.write("\n")

def topics_of(prefix):
    """Load the pack's topics from its source of truth. For a pack built by a script that
    is its case_4_interview.py, which is also the file the expansion is written back to.
    Reading the generated JSON instead would expand against topics as they were at the last
    build. The module is loaded by file path under a name of its own, and the pack's other
    case_* modules are dropped from the import cache first, so two packs in one run never
    see each other's files."""
    folder = os.path.join(ROOT, "cases", prefix)
    src = os.path.join(folder, "case_4_interview.py")
    if os.path.exists(src):
        import importlib.util
        for name in [n for n in sys.modules if n.startswith("case_")]:
            del sys.modules[name]
        sys.path.insert(0, folder)
        try:
            spec = importlib.util.spec_from_file_location(f"_{prefix}_case_4_interview", src)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        finally:
            sys.path.remove(folder)
        return m.TOPICS
    return load_json(os.path.join(folder, f"{prefix}-case.json"))["interview"]["topics"]

# ---------------------------------------------------------------- expansion
def expand(prefix, dry):
    pack_dir = os.path.join(ROOT, "cases", prefix)
    r = expand_topics(prefix, topics_of(prefix), MAP[prefix], EXTRA_COVERED.get(prefix, []), pack_dir)
    print(report(r))
    if dry: return
    added, oos_bank = r["added"], r["oos_bank"]
    # A pack whose case file is generated by a build script must receive the expansion in
    # the source module, or the next run of that script silently discards it. The test is
    # whether the pack has a case_4_interview.py, not which pack it is.
    if os.path.exists(os.path.join(pack_dir, "case_4_interview.py")):
        write_py_pack(prefix, added, oos_bank)
    else:
        write_json_pack(prefix, added, oos_bank)
    save_json(os.path.join(pack_dir, f"{prefix}-matcher-tune-questions.json"), tune_file(prefix, r))

def write_json_pack(prefix, added, oos_bank):
    p = os.path.join(ROOT, "cases", prefix, f"{prefix}-case.json")
    case = load_json(p)
    for t in case["interview"]["topics"]:
        t.pop("expanded_variants", None); t.pop("variants_provenance", None)
        if t["topic"] in added and added[t["topic"]]:
            t["expanded_variants"] = added[t["topic"]]
            t["variants_provenance"] = PROVENANCE
    case["interview"]["out_of_scope_bank"] = oos_bank
    case["interview"]["out_of_scope_bank_note"] = OOS_BANK_NOTE
    save_json(p, case)

def write_py_pack(prefix, added, oos_bank):
    p = os.path.join(ROOT, "cases", prefix, "case_4_interview.py")
    src = open(p).read()
    B, E = "# ---- EXPANDED VARIANTS (generated, do not edit by hand) ----", "# ---- END EXPANDED VARIANTS ----"
    lines = [B,
             "# " + PROVENANCE[:95], "# " + PROVENANCE[95:190], "# " + PROVENANCE[190:],
             "EXPANDED = {"]
    for tid, qs in added.items():
        if not qs: continue
        lines.append(f"  {tid!r}: [")
        for q in qs: lines.append(f"    {q!r},")
        lines.append("  ],")
    lines.append("}")
    lines.append("OUT_OF_SCOPE_BANK = [")
    for q in oos_bank: lines.append(f"  {q!r},")
    lines.append("]")
    lines.append("for _t in TOPICS:")
    lines.append("    if EXPANDED.get(_t['topic']):")
    lines.append("        _t['expanded_variants'] = list(EXPANDED[_t['topic']])")
    lines.append("        _t['variants_provenance'] = " + repr(PROVENANCE))
    lines.append(E)
    block = "\n".join(lines) + "\n"
    if B in src:
        src = src[:src.index(B)] + block + src[src.index(E) + len(E) + 1:]
    else:
        src = src.rstrip("\n") + "\n\n" + block
    open(p, "w").write(src)

# Packs whose committed expansion is frozen (decision of 7 October 2026). Their banks were
# edited by hand after the last expansion, so a run cannot reproduce what is committed:
# it changes the case file and, for DIPH, gives a different bank on every run. This script
# will not write to them without --force. --dry-run still reports.
FROZEN = {"AFRVR", "CHFE", "DIPH", "MGCA"}
assert set(MAP) == FROZEN, "this command holds the frozen packs only; new packs expand at build time"

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    unknown = [a for a in args if a not in MAP]
    if not args or unknown:
        if unknown:
            print("not a frozen pack: " + ", ".join(unknown) + ". A pack that is not frozen expands at build "
                  "time: put TOPIC_MAP and EXTRA_COVERED in its case_4_interview.py and run its "
                  "build_case.py (the reference pack named in CLAUDE.md shows the layout).", file=sys.stderr)
        print("usage: python3 catalog/expand_interview_variants.py PACK [PACK ...] --dry-run | --force\n"
              "       frozen packs: " + " ".join(sorted(MAP)), file=sys.stderr)
        sys.exit(2)
    if not dry and not force:
        sys.exit("refusing to write " + ", ".join(args) + ": these packs' expansions are frozen "
                 "(see docs/restructure-plan.md). Use --dry-run to read the report, or --force "
                 "if you have decided to regenerate them and will commit the changed case files.")
    for prefix in args:
        expand(prefix, dry)
