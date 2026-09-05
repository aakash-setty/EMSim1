#!/usr/bin/env python3
"""Build the simulator: one HTML file containing every case pack in `cases/`.

    python3 engine/build_simulator.py                 (all packs)
    python3 engine/build_simulator.py CHFE PE         (named packs only)

Writes `build/simulator.html`. Opening it shows a case picker, then the chosen
case's splash screen, then the case.

WHY THE MERGE MOVED TO RUNTIME
Earlier this script merged each catalog entry with the case action bound to it and
emitted the finished action table. That table is 227 KB and is 95 percent catalog
data, so every case carried its own copy of the whole catalog and the file grew by
roughly 370 KB per case.

Now the script emits the catalog once, plus a small per-case binding map, and the
engine performs the merge when a case is selected. Cost per additional case falls to
the size of its own case file. It is also the better place for the merge: section 6.2
of the system design describes catalog-default and case-prerequisite merging as engine
behaviour, and it was living in the build.

WHAT IS SHARED AND WHAT IS PER CASE
Shared: the catalog action base records, the diagnosis catalog, tab layout, turnaround
classes, difficulty modes, and the global default responses. Per case: the case file,
the catalog bindings, the placements for actions the catalog lacks, and the handoff
resolution.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paths import CasePack, catalog_path, list_packs, BUILD_DIR, ROOT

OUT = os.path.join(BUILD_DIR, "simulator.html")
# The same bytes again as build/index.html, so that build/ can be uploaded to any
# static host and served at the root without renaming anything. Every tool and test
# in this repo addresses build/simulator.html, so that name has to stay; a web server
# looking for a directory index has to find index.html. Writing both is a megabyte on
# disk and removes an unforced deployment error.
SITE_INDEX = os.path.join(BUILD_DIR, "index.html")

catalog = json.load(open(catalog_path("action-catalog.json")))
dxcat = json.load(open(catalog_path("diagnosis-catalog.json")))
CE = {x["id"]: x for x in catalog["entries"]}

# The Patient tab was removed. It printed the whole authored background before the
# learner had asked for any of it; the two-sentence EMS or triage handover now sits at
# the top of History. See docs/arrival-and-history-change.md.
TAB_ORDER = ["history", "exam", "stabilization",
             "investigations", "interventions", "consultations", "handoff"]
TAB_LABEL = {"history": "History", "exam": "Exam",
             "investigations": "Investigations", "stabilization": "Stabilization",
             "interventions": "Interventions", "consultations": "Consults",
             "handoff": "Handoff"}


def orphan_category(eff):
    if eff.startswith("exam_"):
        return "exam"
    if eff.startswith("consult_"):
        return "consultant"
    if eff.startswith(("labs_", "echo_", "cxr", "ct_", "pocus")):
        return "investigation"
    if eff.startswith("interview_topic_"):
        return "interview"
    if eff == "handoff_submit":
        return "handoff"
    return "stabilization"


# ---------------------------------------------------------------- shared
def action_base(ce):
    pl = (ce.get("placements") or [{"tab": "interventions", "group": None}])[0]
    tab = pl["tab"]
    group = pl.get("group") or {"exam": "Examination",
                                "stabilization": "Stabilization"}.get(tab, "Other")
    rec = {"id": ce["id"], "name": ce["display_name"], "tab": tab, "group": group,
           "category": ce["category"]}
    # An entry placed under several groups of the same tab (v0.9: magnesium sulfate
    # under four medication groups) lists them all, so the interface can draw the one
    # button in each place a resident would look. The first placement stays `group`
    # for everything that wants a single home.
    more = [p.get("group") for p in (ce.get("placements") or [])[1:]
            if p.get("tab") == tab and p.get("group") and p.get("group") != group]
    if more:
        rec["groups"] = [group] + more
    for k, out in [("state_changing", "state_changing"), ("turnaround_class", "turnaround_class"),
                   ("narration_template", "narration_template"), ("default_result", "default_result"),
                   ("default_prerequisites", "default_prerequisites"),
                   ("flags_set_default", "flags_set_default"), ("dose_required", "dose_required"),
                   ("persistent", "persistent"), ("repeatable", "repeatable"),
                   # which infusion this action stops; the engine needs it to relate a
                   # stop action to the drip it withdraws
                   ("stops", "stops"),
                   # true on the act that puts numbers on the screen. The interface
                   # shows no vitals and plays no heartbeat until one has been taken
                   ("reveals_vitals", "reveals_vitals")]:
        if ce.get(k) not in (None, [], False):
            rec[out] = ce[k]
    return rec


shared = {
    "catalogVersion": catalog["catalog_version"],
    "actionsBase": {x["id"]: action_base(x) for x in catalog["entries"]},
    "tabOrder": TAB_ORDER,
    "tabLabel": TAB_LABEL,
    "turnaround": catalog["turnaround_seconds_by_class"],
    "generalStatusDefault": catalog.get("general_status_default"),
    "examRouting": catalog.get("exam_finding_routing"),
    "diagnoses": [{"id": d["id"], "label": d["display_name"],
                   "syn": d.get("synonyms") or []} for d in dxcat["entries"]],
    "orderableTabs": ["investigations", "stabilization", "interventions"],
    # Tabs whose groups render collapsed until clicked. Investigations and
    # Stabilization carry enough entries that a flat list is unreadable, the same
    # reason Interventions collapses. Exams and Consults stay flat: 14 and 17 entries
    # in a single group each, where an accordion would add a click and hide nothing.
    "collapsibleTabs": ["interventions", "investigations", "stabilization"],
    "groupOrder": {"stabilization": ["Stabilization", "Nursing", "Vascular Access", "Oxygen",
                                     "Intubation", "Intubation Drugs", "Fluids", "Pacer/Defib"]},
    # Groups that render already open the first time their tab is opened. Stabilization
    # holds the three acts that come first in any resuscitation, and one of them now
    # gates the monitor, so making the resident click a header to find them buries the
    # thing the case needs them to do. Everything else stays collapsed. A learner who
    # collapses it keeps it collapsed for the rest of the run: this seeds the accordion,
    # it does not force it.
    "defaultExpanded": {"stabilization": ["Stabilization"]},
    "matchThreshold": 0.32,
    "nurseIdle": "He's all yours. Tell me what you want and I'll get it.",
    # The patient's conversational scaffolding (design 10.7). A case may override any
    # of these under `interview`: repeat_prefixes, nothing_more, clarify_template.
    # Written in the patient's voice, so they read as speech and not as system text.
    "interviewDefaults": {
        "repeatPrefixes": [
            "'Like I said, {answer}'",
            "'I did tell you. {answer}'",
            "'{answer} You've asked me that.'",
        ],
        "nothingMore": "'No, that's everything, really.'",
        "clarifyTemplate": "'Sorry, do you mean {a}, or {b}?'",
        # Questions that mean "go on" about whatever was last asked. Matched by the
        # interface before the topic matcher runs, only when a topic has already been
        # spoken about in this run.
        "morePhrasings": ["anything else", "what else", "go on", "and", "tell me more",
                          "more", "is that everything", "is that all", "anything more",
                          "and then", "carry on", "what happened next", "then what"],
        # The uncertainty band. A match whose combined score sits under this clears the
        # threshold without much to spare, so the patient echoes the topic before
        # answering and a wrong match is visible at once in the transcript.
        "echoBelow": 0.62,
        # The matcher asks which topic was meant when the top two combined scores sit
        # within this margin of each other and both clear the threshold.
        "clarifyMargin": 0.04,
        # A short question (this many words or fewer) that matches nothing well is tried
        # against the last topic's facts before it is given up on.
        "followUpMaxWords": 6,
    },
    "globalNormalExam": "No abnormality detected on this examination.",
    "globalConsultant": ("They pick up, listen for a moment, and say they are not sure why they "
                         "have been called about this patient."),
    "orphanNote": ("This action is in the case but not in the action catalog. In the real product "
                   "a resident would not see it at all."),
    "unlistedDxNote": ("The case does not anticipate this diagnosis, so there is no authored "
                       "explanation for it. With %d entries in the catalog most wrong answers "
                       "land here; a case can only pre-explain the common ones."
                       % len(dxcat["entries"])),
    "difficulty": {
        "default": "easy",
        "note": ("Mode changes only how long the nurse waits before prompting. Result turnaround, "
                 "phase transitions and clinical tags are identical, so the medicine is the same "
                 "either way."),
        "modes": {
            "easy": {"label": "Easy", "prompt_multiplier": 1,
                     "description": ("The nurse prompts at the authored deadlines. Choose this if "
                                     "the case is unfamiliar.")},
            "hard": {"label": "Hard", "prompt_multiplier": 3,
                     "description": ("The nurse waits three times as long before prompting, and "
                                     "often the case will be over first. Choose this to test "
                                     "whether you would have acted unaided.")},
        },
    },
    # How the debrief opens, and how long the monitor holds on a terminal phase before
    # the run ends. Both are presentation, not fairness: the five seconds are there so a
    # resident sees the arrest happen rather than being thrown straight to a debrief, and
    # they are deliberately outside the validator's 30-second floor on after_seconds
    # because that floor governs how long a resident has to act, and by this point there
    # is nothing left to act on.
    "ending": {
        "terminalGraceSeconds": 5,
        "_note": ("Seconds the interface waits after the case walks into a terminal phase "
                  "by the clock before it ends the run and shows the debrief. A harmful "
                  "action still ends the case immediately, because its halt card is the "
                  "teaching."),
    },
    "audio": {
        "baseHz": 1760.0, "baseNote": "A6", "spo2Reference": 100, "semitonesPerPercent": 1.0,
        "assumption": ("One half step lower per percent of SpO2 'below'. The reference point is "
                       "not stated in the brief, so 100% is used: the anchor note at full "
                       "saturation, one semitone down per percent. At 87% that is 13 semitones "
                       "below, about 831 Hz. Change spo2Reference to move the anchor.\n\n"
                       "The anchor was A5 (880 Hz) and was raised to A6 (1760 Hz) on the author's "
                       "instruction after playing a case. It is worth knowing what that costs: the "
                       "beat is now well inside the band the ear is most sensitive to, so it "
                       "carries further over room noise and is more tiring over a fifteen-minute "
                       "case, and a desaturated patient at 76% sits at 440 Hz where before he sat "
                       "at 220. The mapping is unchanged; only the anchor moved."),
        # The closed vocabulary a phase's `rhythm` may name. It is here rather than in a
        # case because it is a property of how the monitor sounds, not of any diagnosis:
        # the engine has no idea which conditions produce which rhythm, exactly as it has
        # no idea which drugs are harmful. Adding a third entry here is what it would take
        # to give a case a regularly irregular beat, and it would need its own model
        # rather than different parameters for this one.
        "rhythm": {
            "_note": ("Keys are the permitted values of phases[].rhythm. A phase with no "
                      "rhythm, or with one this map does not hold, sounds regular. The "
                      "validator enforces the same set at authoring time so an unknown "
                      "value is caught before it becomes a silent fallback."),
            "regular": {
                "label": "regular",
            },
            "irregularly_irregular": {
                "label": "irregularly irregular",
                # interval = mean * (s + (1 - s) * Exp(1)), where s is raised above this
                # figure wherever absoluteFloorMs would otherwise be breached. The mean is
                # preserved exactly; the coefficient of variation is (1 - s).
                "refractoryFraction": 0.80,
                # No two beats closer than this, whatever the rate. Roughly the
                # atrioventricular nodal refractory period, and also comfortably longer
                # than the lub-dub gap, so the second sound of one beat can never land on
                # the first sound of the next.
                "absoluteFloorMs": 240,
                # Truncates a tail of about one draw in a thousand so a pathological
                # sample cannot leave an audible silence.
                "ceilingMultiple": 2.6,
                # Beat-to-beat variation in loudness, derived from the length of the
                # preceding interval: a long diastole fills the ventricle more.
                "gainPerRatio": 0.80,
                "gainFloor": 0.72,
                "gainCeiling": 1.30,
                "provenance": (
                    "AUTHORED, NOT MEASURED. A coefficient of variation of 0.20 at ordinary "
                    "rates, right-skewed, with the spread narrowing as the rate rises. That "
                    "is the right shape and the right direction; the specific figures are a "
                    "teaching choice made to be clearly audible as irregular, not a fit to "
                    "published R-R interval data, and no case should be described as "
                    "modelling a rhythm. The loudness variation is the same kind of claim: "
                    "the mechanism is real and the coefficient is invented."),
            },
        },
    },
}

DX_IDS = {d["id"] for d in shared["diagnoses"]}


def resolve_dx(ref):
    """Catalog id, exact display name, or exact synonym. No guessing: a wrong guess
    scores the handoff against the wrong answer and nothing downstream would notice."""
    if not ref:
        return None
    if ref in DX_IDS:
        return ref
    low = ref.lower()
    for d in shared["diagnoses"]:
        if d["label"].lower() == low or any(s.lower() == low for s in d["syn"]):
            return d["id"]
    return None


# ---------------------------------------------------------------- per case
def build_pack(pack):
    case = json.load(open(pack.case))
    binding = json.load(open(pack.binding))
    bindmap = json.load(open(pack.binding_map))
    notes = []

    # Interview banks. A topic's hand-written `variants` and its generated
    # `expanded_variants` (catalog/expand_interview_variants.py) are one bank at
    # runtime; they are kept apart in the case file so provenance survives and so the
    # generator can replace its own block without touching the author's. Merged here,
    # once, and nothing downstream knows there were two lists.
    for t in case.get("interview", {}).get("topics", []):
        extra = t.pop("expanded_variants", None) or []
        have = {v.lower() for v in t.get("variants", [])}
        for v in extra:
            if v.lower() not in have:
                t.setdefault("variants", []).append(v); have.add(v.lower())

    rows = {r["case_id"]: r for r in binding["rows"]}
    rev = {}                                   # catalog id -> [case ids], case-file order
    for a in case["case_actions"]:
        r = rows.get(a["catalog_id"])
        if r and r.get("catalog_id"):
            rev.setdefault(r["catalog_id"], []).append(a["catalog_id"])

    bindings, shadowed = {}, {}
    for cid, case_ids in rev.items():
        bindings[cid] = case_ids[0]
        for hidden in case_ids[1:]:
            shadowed[hidden] = case_ids[0]

    # also_covers: one case action claiming several catalog entries, so its tag, halt
    # reason and debrief note apply to every route to the same act. Each covered entry
    # keeps its own button and its own catalog name; only the case-specific fields are
    # shared.
    covers = {}
    for r in binding["rows"]:
        for extra in (r.get("also_covers") or []):
            if extra in bindings:
                notes.append(f"{r['case_id']} claims {extra} through also_covers, but "
                             f"{bindings[extra]} already binds it")
                continue
            covers[extra] = r["case_id"]

    orphans = {}
    for r in bindmap.get("rows", []):
        if r.get("catalog_id") is None and r.get("unmatched_placement"):
            p = r["unmatched_placement"]
            orphans[r["case_id"]] = {
                "tab": p["tab"], "group": p.get("group", "Not in the catalog"),
                "category": orphan_category(r["case_id"]),
                "narration_template": r.get("unmatched_narration"),
            }

    unplaced = [a["catalog_id"] for a in case["case_actions"]
                if a["catalog_id"] not in CE
                and a["catalog_id"] not in {v for v in bindings.values()}
                and a["catalog_id"] not in orphans
                and a["catalog_id"] not in shadowed]
    if unplaced:
        notes.append("unmatched case actions with no placement in the binding map, so they are "
                     "unreachable: " + ", ".join(unplaced))

    h = case["handoff"]
    correct_dx = resolve_dx(h["correct_diagnosis"].get("catalog_id")) \
        or resolve_dx(h["correct_diagnosis"].get("label"))
    if not correct_dx:
        notes.append("the correct diagnosis does not resolve to a diagnosis catalog id, so the "
                     "handoff cannot be scored")
    alt_dx = {}
    alt_dx_defensible = []
    for a in h.get("alternative_diagnoses", []):
        hit = resolve_dx(a.get("catalog_id")) or resolve_dx(a.get("label"))
        if hit:
            alt_dx[hit] = a["explanation"]
            # A case whose formulation has two halves has two catalog ids that are both
            # defensible answers, and the engine scores one. Marking the other outright
            # incorrect teaches a learner who understood the case that they did not.
            if a.get("verdict") == "acceptable_with_qualification":
                alt_dx_defensible.append(hit)
        else:
            notes.append("alternative diagnosis %r does not resolve to a catalog id"
                         % a.get("label", a.get("catalog_id")))

    # v0.9. additional_diagnoses: what is also true of the patient and appropriate to
    # name at handover beside the primary. Resolved the same way; an id that is also
    # the correct diagnosis is dropped with a note, because the primary is scored on
    # its own terms and crediting it twice would inflate the handoff score.
    addl_dx = {}
    for a in h.get("additional_diagnoses", []) or []:
        hit = resolve_dx(a.get("catalog_id")) or resolve_dx(a.get("label"))
        if not hit:
            notes.append("additional diagnosis %r does not resolve to a catalog id"
                         % a.get("label", a.get("catalog_id")))
        elif hit == correct_dx:
            notes.append("additional diagnosis %r is the correct diagnosis; ignored" % hit)
        else:
            addl_dx[hit] = a.get("explanation", "")

    disp_labels = {h["correct_disposition"]["id"]: h["correct_disposition"]["label"]}
    for d in h.get("alternative_dispositions", []):
        disp_labels[d["id"]] = d["label"]
    disp_order = h.get("disposition_display_order") or list(disp_labels)
    missing_order = [d for d in disp_labels if d not in disp_order]
    if missing_order:
        notes.append("dispositions missing from disposition_display_order: "
                     + ", ".join(missing_order))
        disp_order = disp_order + missing_order

    m = case["metadata"]
    dbg = case.get("debrief_configuration", {})

    return {
        "prefix": pack.prefix,
        "id": case["case_id"],
        # everything the picker needs, so it does not have to open the case file
        "card": {
            "title": m.get("working_title", case["case_id"]),
            # The welcome screen lists the short clinical complaint, not the patient's
            # own words; chief_complaint is the quote and belongs on the splash. Both
            # of these are optional and degrade, so a pack written before them lists.
            "complaint": m.get("complaint") or m.get("working_title", case["case_id"]),
            "category": m.get("category"),
            "chief_complaint": m.get("chief_complaint_patient_voice", ""),
            "setting": (m.get("care_setting") or {}).get("label", ""),
            "target_level": m.get("target_level"),
            "runtime_seconds": m.get("estimated_runtime_seconds"),
            "unreviewed": bool((case.get("provenance") or {}).get("warning")),
        },
        "case": case,
        "bindings": bindings,
        "covers": covers,
        "shadowed": shadowed,
        "orphans": orphans,
        "bindingCounts": binding["counts"],
        "phaseShort": {p["id"]: p.get("short_label") or p.get("label") or p["id"]
                       for p in case["phases"]},
        "traps": dbg.get("trap_actions", []),
        "dispOrder": disp_order,
        "dispLabels": disp_labels,
        "correctDxId": correct_dx,
        "correctDxExplanation": h["correct_diagnosis"].get("explanation", ""),
        "altDx": alt_dx,
        "altDxDefensible": alt_dx_defensible,
        "addlDx": addl_dx,
        "promptCap": case.get("prompt_cap_recommendation", {}).get("per_phase", 3),
        "buildNotes": notes,
    }


def main():
    wanted = sys.argv[1:] or list_packs()
    if not wanted:
        raise SystemExit("no case packs found in cases/")
    packs = [build_pack(CasePack(w)) for w in wanted]
    packs.sort(key=lambda p: p["prefix"])

    def jsafe(o):
        return json.dumps(o, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028")

    shell = open(os.path.join(HERE, "shell.html")).read()
    # The blurred room background. Derived from a source image rather than authored,
    # so it lives beside the shell as a data URI rather than inline in it; the command
    # that regenerates it is in a comment at the top of the .room rule.
    room_bg = open(os.path.join(HERE, "room-bg.txt")).read().strip()
    # Welcome screen assets, substituted the same way. Derived from assets/, not
    # authored; see engine/README-assets.md for the regeneration commands.
    hero_bg = open(os.path.join(HERE, "hero-bg.txt")).read().strip()
    avatar_m = open(os.path.join(HERE, "avatar-male.txt")).read().strip()
    avatar_f = open(os.path.join(HERE, "avatar-female.txt")).read().strip()
    # The nurse's portrait, beside the line she speaks. Unlike the patient silhouettes
    # this is a full-colour image rather than a CSS mask, because it is a person rather
    # than a diagram of one, and the interface has no other picture of a human in it.
    # Source kept beside it so the crop can be redone rather than reverse-engineered:
    #   python3 -c "from PIL import Image; im=Image.open('assets/nurse-avatar-source.png');\
    #     im.quantize(colors=96, method=Image.FASTOCTREE).convert('RGBA')\
    #       .save('/tmp/a.png', optimize=True)"
    #   base64 -w0 /tmp/a.png > nurse-avatar.txt
    # 240px square, quantised to 96 colours: 32 KB, against 56 KB for the unquantised
    # crop, and the difference is invisible at the 62px it renders at.
    nurse_av = open(os.path.join(HERE, "nurse-avatar.txt")).read().strip()
    # Ward ambience, base64 mp3. Derived from the author's recording by
    # engine/assets/make-ambience.py: 45 seconds taken from a steady stretch, the tail
    # crossfaded onto the head so it repeats without a seam, peak-normalised so that the
    # gain figure in SHARED.audio.rhythm's neighbour LEVEL block means something, and
    # encoded mono at 48 kbps because it plays at about -51 dBFS and nobody will ever
    # hear the codec. Optional: a checkout without it builds a simulator with a silent
    # room and no other difference, which matters because it is by far the largest single
    # asset in the file.
    amb_path = os.path.join(HERE, "ambience.txt")
    ambience = (open(amb_path).read().strip() if os.path.exists(amb_path) else "")
    # semantic.js declares `const SEM` and ui.js registers a listener on it at top
    # level, so it MUST come before ui.js. Reversed, the bundle throws before the
    # first render and the page is blank.
    # audio.js is fenced separately so the test harness can evaluate it without the
    # engine, and the engine without it. The interval model is a claim about physiology
    # and has to be assertable.
    bundle = ("/*__ENGINE_START__*/\n" + open(os.path.join(HERE, "engine.js")).read() +
              "\n/*__ENGINE_END__*/\n"
              "/*__AUDIO_START__*/\n" + open(os.path.join(HERE, "audio.js")).read() +
              "\n/*__AUDIO_END__*/\n" +
              "\n" + open(os.path.join(HERE, "semantic.js")).read() +
              "\n" + open(os.path.join(HERE, "ui.js")).read() + "\n")

    title = "EM Case Simulator" if len(packs) != 1 else packs[0]["card"]["title"]
    shell = shell.replace("__TITLE__", title.replace("<", ""))
    shell = shell.replace("__ROOM_BG__", room_bg)
    shell = shell.replace("__HERO_BG__", "data:image/jpeg;base64," + hero_bg)
    shell = shell.replace("__AVATAR_M__", "data:image/png;base64," + avatar_m)
    shell = shell.replace("__AVATAR_F__", "data:image/png;base64," + avatar_f)
    shell = shell.replace("__NURSE_AVATAR__", "data:image/png;base64," + nurse_av)
    shell = shell.replace("__AMBIENCE_JSON__",
                          jsafe("data:audio/mpeg;base64," + ambience) if ambience else '""')
    shell = shell.replace("__SHARED_JSON__", jsafe(shared))
    shell = shell.replace("__CASES_JSON__", jsafe(packs))
    shell = shell.replace("</script>\n</body>", bundle + "</script>\n</body>")

    os.makedirs(BUILD_DIR, exist_ok=True)
    open(OUT, "w").write(shell)
    open(SITE_INDEX, "w").write(shell)

    print("wrote", os.path.relpath(OUT, ROOT), round(len(shell) / 1024), "KB",
          "(and", os.path.relpath(SITE_INDEX, ROOT) + ")")
    print("catalog:", len(CE), "actions,", len(shared["diagnoses"]), "diagnoses")
    for p in packs:
        print(f"  {p['prefix']:<8} {p['id']:<20} bindings {len(p['bindings']):>3}  "
              f"orphans {len(p['orphans']):>2}  shadowed {len(p['shadowed'])}")
        for n in p["buildNotes"]:
            print(f"           note: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
