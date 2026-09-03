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
    for k, out in [("state_changing", "state_changing"), ("turnaround_class", "turnaround_class"),
                   ("narration_template", "narration_template"), ("default_result", "default_result"),
                   ("default_prerequisites", "default_prerequisites"),
                   ("flags_set_default", "flags_set_default"), ("dose_required", "dose_required"),
                   ("persistent", "persistent"), ("repeatable", "repeatable"),
                   # which infusion this action stops; the engine needs it to relate a
                   # stop action to the drip it withdraws
                   ("stops", "stops")]:
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
    "groupOrder": {"stabilization": ["Stabilization", "Vascular Access", "Oxygen", "Intubation",
                                     "Intubation Drugs", "Fluids", "Pacer/Defib"]},
    "matchThreshold": 0.32,
    "nurseIdle": "He's all yours. Tell me what you want and I'll get it.",
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
    "audio": {
        "baseHz": 880.0, "baseNote": "A5", "spo2Reference": 100, "semitonesPerPercent": 1.0,
        "assumption": ("The brief says A5 and one half step lower per percent of SpO2 'below'. The "
                       "reference point is not stated, so 100% is used: A5 at full saturation, one "
                       "semitone down per percent. At 87% that is 13 semitones below A5, about "
                       "415 Hz. Change spo2Reference to move the anchor."),
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
    for a in h.get("alternative_diagnoses", []):
        hit = resolve_dx(a.get("catalog_id")) or resolve_dx(a.get("label"))
        if hit:
            alt_dx[hit] = a["explanation"]
        else:
            notes.append("alternative diagnosis %r does not resolve to a catalog id"
                         % a.get("label", a.get("catalog_id")))

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
    # semantic.js declares `const SEM` and ui.js registers a listener on it at top
    # level, so it MUST come before ui.js. Reversed, the bundle throws before the
    # first render and the page is blank.
    bundle = ("/*__ENGINE_START__*/\n" + open(os.path.join(HERE, "engine.js")).read() +
              "\n/*__ENGINE_END__*/\n" + open(os.path.join(HERE, "audio.js")).read() +
              "\n" + open(os.path.join(HERE, "semantic.js")).read() +
              "\n" + open(os.path.join(HERE, "ui.js")).read() + "\n")

    title = "EM Case Simulator" if len(packs) != 1 else packs[0]["card"]["title"]
    shell = shell.replace("__TITLE__", title.replace("<", ""))
    shell = shell.replace("__ROOM_BG__", room_bg)
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
