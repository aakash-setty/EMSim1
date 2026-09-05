#!/usr/bin/env python3
"""Expand every case pack's interview variant bank from the shared phrasing library,
write an out-of-scope bank into each case, and withhold a tuning set from both.

    python3 catalog/expand_interview_variants.py            all packs
    python3 catalog/expand_interview_variants.py AFRVR      one pack
    python3 catalog/expand_interview_variants.py --dry-run  report, write nothing

What it writes, per pack:

  cases/CHFE/CHFE-case.json            topics[].expanded_variants written (never the
  cases/MGCA/MGCA-case.json            hand-written `variants`), a `variants_provenance`
                                       note on each topic, and `interview.out_of_scope_bank`.
                                       build_simulator.py merges expanded_variants into
                                       variants at build time, so nothing at runtime changes.
  cases/AFRVR/case_4_interview.py      an EXPANDED block and an OUT_OF_SCOPE_BANK list
                                       between marker comments (the case JSON is generated
                                       from these sources by build_case.py)
  cases/<P>/<P>-matcher-tune-questions.json
                                       the withheld slice: every Nth new phrasing per
                                       topic, and every Nth out-of-scope entry, kept out
                                       of the banks so thresholds can be tuned on them

Idempotent: re-running replaces what it wrote and adds nothing twice.

Three rules it enforces rather than trusts:
  1. Nothing written into a bank may match a held-out evaluation question, normalised.
     Such a phrasing is dropped and reported. The evaluation harness checks again.
  2. A phrasing lives in exactly one topic per pack. If it already sits in another
     topic's bank it is not added to this one.
  3. The tuning slice is chosen by position, not by hand, so nobody picks the easy ones.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from interview_phrasings import CONCEPTS, OPENERS          # noqa: E402
from interview_out_of_scope import OUT_OF_SCOPE            # noqa: E402

HOLD_EVERY = 6            # every 6th new phrasing per topic goes to the tuning set
OPENER_CORES = 3          # phrasings per topic that also get conversational openers
OPENERS_PER_CORE = 2      # openers applied to each of those, rotating through OPENERS

# ---------------------------------------------------------------- topic -> concepts
# One entry per pack. A topic may draw on several concepts. Topics absent from the
# map are left alone, which is how a pack-specific topic with no shared phrasings
# stays hand-authored.
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
 "MGCA": {
  "onset": ["onset"], "timing_progression": ["timing_progression"], "character_of_symptoms": ["character_general"],
  "location_of_pain": ["location_pain"], "radiation_of_pain": ["radiation_pain"], "severity": ["severity"],
  "aggravating_relieving": ["aggravating_relieving", "aggravating", "relieving"], "rash": ["rash"],
  "fever_and_chills": ["fever_chills"], "headache": ["headache"], "neck_stiffness": ["neck_stiffness"],
  "photophobia": ["photophobia"], "nausea_vomiting": ["nausea_vomiting"], "diarrhoea": ["diarrhoea"],
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
EXTRA_COVERED = {
  "AFRVR": ["location_pain", "radiation_pain", "palpitations", "breathing_sob", "smoking_alcohol", "social_history"],
  "CHFE": ["orthopnea", "palpitations", "smoking", "alcohol"],
  "MGCA": ["character_general"],
}

PROVENANCE = ("Expanded by catalog/expand_interview_variants.py from catalog/interview_phrasings.py "
              "in Sep 2026. The added phrasings were written by an AI assistant, not by a physician, "
              "and mix lay paraphrase, clinical shorthand and conversational forms. Every sixth new "
              "phrasing was withheld into the pack's tuning set rather than added here.")

# ---------------------------------------------------------------- helpers
def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

def load_json(p):
    with open(p) as f: return json.load(f)

def save_json(p, o):
    with open(p, "w") as f:
        json.dump(o, f, indent=1, ensure_ascii=False); f.write("\n")

def held_out_questions(prefix):
    p = os.path.join(ROOT, "cases", prefix, f"{prefix}-matcher-eval-questions.json")
    if not os.path.exists(p): return set()
    return {norm(q["q"]) for q in load_json(p)["questions"]}

def with_openers(q):
    """Conversational forms of a full question. Only applied to real questions, never
    to shorthand, and the opener rotation is deterministic in the phrasing text."""
    if len(q) < 14 or not q.endswith("?") or q.lower() == q: return []
    body = q[0].lower() + q[1:]
    start = sum(map(ord, q)) % len(OPENERS)
    out = []
    for k in range(OPENERS_PER_CORE):
        t = OPENERS[(start + k * 3) % len(OPENERS)]
        out.append(t.replace("{q}", body).replace("{Q}", q))
    return out

def topics_of(prefix):
    """Load the pack's topics from its source of truth."""
    if prefix == "AFRVR":
        sys.path.insert(0, os.path.join(ROOT, "cases", "AFRVR"))
        import importlib
        m = importlib.import_module("case_4_interview")
        importlib.reload(m)
        return m.TOPICS
    return load_json(os.path.join(ROOT, "cases", prefix, f"{prefix}-case.json"))["interview"]["topics"]

# ---------------------------------------------------------------- expansion
def expand(prefix, dry):
    topics = topics_of(prefix)
    held = held_out_questions(prefix)
    tmap = MAP[prefix]
    covered = set(EXTRA_COVERED.get(prefix, []))
    for cs in tmap.values(): covered.update(cs)

    # Everything already in a bank, so a phrasing lands in exactly one topic. A topic's
    # own previously expanded list is NOT counted: it is recomputed and replaced, which is
    # what makes a re-run idempotent rather than cumulative.
    owner = {}
    for t in topics:
        for f in [t["canonical"]] + list(t.get("variants", [])):
            owner.setdefault(norm(f), t["topic"])
    prior = {t["topic"]: {norm(f) for f in t.get("expanded_variants", [])} for t in topics}

    added, tune, dropped = {}, [], []
    for t in topics:
        tid = t["topic"]
        if tid not in tmap: continue
        pool = []
        for c in tmap[tid]:
            for q in CONCEPTS[c]:
                pool.append(q)
        # conversational openers on the first few real questions
        cores = [q for q in pool if len(q) >= 14 and q.endswith("?")][:OPENER_CORES]
        for q in cores: pool.extend(with_openers(q))
        fresh, seen = [], set()
        for q in pool:
            n = norm(q)
            if not n or n in seen: continue
            seen.add(n)
            if n in held: dropped.append((tid, q, "held-out eval question")); continue
            if n in owner and owner[n] != tid: dropped.append((tid, q, f"already in {owner[n]}")); continue
            if n in owner and owner[n] == tid: continue   # already hand-authored on this topic
            if any(n in prior[o] for o in prior if o != tid): dropped.append((tid, q, "expanded on another topic")); continue
            fresh.append(q)
        bank, held_slice = [], []
        for i, q in enumerate(fresh):
            (held_slice if (i + 1) % HOLD_EVERY == 0 else bank).append(q)
        for q in bank: owner[norm(q)] = tid
        added[tid] = bank
        tune.extend({"register": "expansion", "q": q, "expect": tid} for q in held_slice)

    # out-of-scope bank, filtered to what this case does not author
    oos_all = [q for q, covers in OUT_OF_SCOPE if not (set(covers) & covered)]
    oos_bank, oos_tune = [], []
    for i, q in enumerate(oos_all):
        n = norm(q)
        if n in held: dropped.append(("out_of_scope", q, "held-out eval question")); continue
        if n in owner: dropped.append(("out_of_scope", q, f"already in {owner[n]}")); continue
        ((oos_tune if (i + 1) % HOLD_EVERY == 0 else oos_bank)).append(q)
    tune.extend({"register": "out_of_scope_expansion", "q": q, "expect": None} for q in oos_tune)

    n_new = sum(len(v) for v in added.values())
    print(f"{prefix}: {len(added)} topics expanded, +{n_new} variants, "
          f"{len(oos_bank)} out-of-scope bank entries, {len(tune)} tuning questions, {len(dropped)} dropped")
    for tid, q, why in dropped: print(f"   dropped [{tid}] {q!r}: {why}")
    if dry: return

    if prefix == "AFRVR":
        write_afrvr(added, oos_bank)
    else:
        write_json_pack(prefix, added, oos_bank)
    save_json(os.path.join(ROOT, "cases", prefix, f"{prefix}-matcher-tune-questions.json"), {
        "case_prefix": prefix,
        "status": ("TUNING SET. Generated by catalog/expand_interview_variants.py: every sixth new phrasing "
                   "per topic and every sixth out-of-scope entry, withheld from the banks. Sweep thresholds "
                   "against this file and quote the held-out file, never the other way round."),
        "questions": tune,
    })

def write_json_pack(prefix, added, oos_bank):
    p = os.path.join(ROOT, "cases", prefix, f"{prefix}-case.json")
    case = load_json(p)
    for t in case["interview"]["topics"]:
        t.pop("expanded_variants", None); t.pop("variants_provenance", None)
        if t["topic"] in added and added[t["topic"]]:
            t["expanded_variants"] = added[t["topic"]]
            t["variants_provenance"] = PROVENANCE
    case["interview"]["out_of_scope_bank"] = oos_bank
    case["interview"]["out_of_scope_bank_note"] = (
        "Questions this case has no authored answer to, from catalog/interview_out_of_scope.py filtered "
        "to the concepts this case does not cover. The matcher embeds them beside the topic bank; a "
        "question closer to one of these than to any topic gets the out-of-scope fallback rather than "
        "the nearest topic's answer.")
    save_json(p, case)

def write_afrvr(added, oos_bank):
    p = os.path.join(ROOT, "cases", "AFRVR", "case_4_interview.py")
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

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    for prefix in (args or ["AFRVR", "CHFE", "MGCA"]):
        expand(prefix, dry)
