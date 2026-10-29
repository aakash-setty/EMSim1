#!/usr/bin/env python3
"""Check a procedure pack (procedures/<P>/<P>-procedure.json) before it is built.

    python3 engine/validate_procedure.py procedures/CRIC

The build runs the same checks and stops on an error. What is checked: the fields the
engine reads are there and of the right shape, every id a step names exists, every step
type is one the engine implements, the text follows the house style, and the pack says
whether a physician has reviewed it. The behavior is tested by engine/procsim-tests.js.
"""
import json, os, re, sys

STEP_TYPES = {"action", "choice", "palpate", "stab", "rotate", "insert", "turn", "advance",
              "railroad", "inflate", "confirm"}
LAYER_KINDS = {"slab", "surface", "tube", "repeat"}
TOOL_KINDS = {"finger", "blade", "rod", "tube", "syringe", "bag"}
STEP_TOOL_KIND = {"stab": "blade", "rotate": "blade", "insert": "rod", "turn": "rod", "advance": "rod",
                  "railroad": "tube", "inflate": "syringe", "confirm": "bag"}
DIRS = {"operator", "far", "head", "feet"}
PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}$")


def learner_text(pack):
    """Every string a learner reads, with where it came from."""
    out = []
    def add(where, t):
        if isinstance(t, str): out.append((where, t))
    c = pack.get("card", {})
    for k in ("title", "subtitle", "blurb"): add("card." + k, c.get(k))
    for s in pack.get("steps", []):
        for k in ("label", "prompt", "why", "wrong"): add(s.get("id", "?") + "." + k, s.get(k))
        for k, v in (s.get("errors") or {}).items(): add(s.get("id", "?") + ".errors." + k, v)
        for o in s.get("options", []): add(s.get("id", "?") + ".option", o.get("label"))
    for z in pack.get("zones", []):
        for k in ("name", "feel", "wrong"): add("zone " + z.get("id", "?") + "." + k, z.get(k))
    for k, v in (pack.get("feel") or {}).items():
        add("feel." + k + ".learn", v.get("learn")); add("feel." + k + ".feel", v.get("feel"))
    for d in pack.get("distractors", []): add("distractor " + d.get("id", "?"), d.get("label")); add("distractor " + d.get("id", "?"), d.get("feedback"))
    for p in (pack.get("debrief") or {}).get("points", []): add("debrief", p)
    for k, v in (pack.get("hands") or {}).items(): add("hands." + k, v)
    for t in pack.get("tools", []): add("tool " + t.get("id", "?"), t.get("name")); add("tool " + t.get("id", "?"), t.get("desc"))
    return out


def validate(pack, folder_prefix=None):
    E = []
    err = E.append
    pre = pack.get("prefix")
    if not isinstance(pre, str) or not PREFIX_RE.match(pre):
        err("prefix must be 2 to 16 capitals and digits, starting with a capital")
    if folder_prefix and pre != folder_prefix:
        err(f"prefix {pre!r} does not match its folder {folder_prefix!r}")
    if pack.get("kind") != "procedure":
        err('kind must be "procedure"')
    if pack.get("units") != "mm":
        err('units must be "mm"')
    card = pack.get("card") or {}
    if not card.get("title"):
        err("card.title is required")
    review = pack.get("review") or ""
    if not re.search(r"not physician reviewed|physician reviewed by .+ on \d", review, re.I):
        err('review must say "Not physician reviewed", or name the physician and the date')

    layers = pack.get("layers") or []
    ids = []
    for L in layers:
        lid = L.get("id")
        if not lid: err("a layer has no id"); continue
        if lid in ids: err(f"layer {lid} appears twice")
        ids.append(lid)
        if L.get("mirror_of"):
            if L["mirror_of"] not in ids[:-1]: err(f"layer {lid}: mirror_of {L['mirror_of']!r} must name an earlier layer")
            continue
        k = L.get("kind")
        if k not in LAYER_KINDS: err(f"layer {lid}: kind must be one of {sorted(LAYER_KINDS)}"); continue
        if k in ("slab", "surface"):
            st = L.get("stations") or []
            if len(st) < 2: err(f"layer {lid}: needs at least two stations")
            zs = [s.get("z") for s in st]
            if any(not isinstance(z, (int, float)) for z in zs) or zs != sorted(zs) or len(set(zs)) != len(zs):
                err(f"layer {lid}: station z values must be numbers in increasing order")
            for s in st:
                shp = s.get("outer") if k == "slab" else s.get("shape")
                if not shp or not (shp.get("ellipse") or shp.get("poly")):
                    err(f"layer {lid}: every station needs an {'outer' if k=='slab' else 'shape'} ellipse or poly")
                if k == "slab" and not s.get("inner") and not (shp or {}).get("offset"):
                    err(f"layer {lid}: a slab station needs an inner cross-section or an offset")
        if k == "tube":
            if len(L.get("path") or []) < 2 or not isinstance(L.get("radius"), (int, float)):
                err(f"layer {lid}: a tube needs a path of two or more points and a radius")
        if k == "repeat":
            if not L.get("template") or not L.get("at"):
                err(f"layer {lid}: a repeat needs a template and a list of z values in at")
    if not layers or layers[0].get("id") is None:
        err("the first layer is the skin, which the pointer and every depth are measured from")
    airs = [L for L in layers if L.get("air")]
    if len(airs) != 1:
        err("exactly one layer must be marked air (the airway the instruments reach)")
    groups = {g.get("id") for g in pack.get("groups") or []}
    for L in layers:
        if not L.get("mirror_of") and L.get("group") not in groups:
            err(f"layer {L.get('id')}: group {L.get('group')!r} is not in groups")

    zones = {z.get("id") for z in pack.get("zones") or []}
    for z in pack.get("zones") or []:
        for k in ("x", "z"):
            v = z.get(k)
            if not (isinstance(v, list) and len(v) == 2 and v[0] < v[1]):
                err(f"zone {z.get('id')}: {k} must be [low, high]")
        for k in ("feel", "wrong"):
            if not z.get(k): err(f"zone {z.get('id')}: {k} is required")
    for k in (pack.get("feel") or {}):
        if k not in ids: err(f"feel names no layer: {k}")

    tools = {t.get("id"): t for t in pack.get("tools") or []}
    for t in tools.values():
        if t.get("kind") not in TOOL_KINDS: err(f"tool {t.get('id')}: kind must be one of {sorted(TOOL_KINDS)}")
        for k, lo, hi in (("tract_deg", 30, 90), ("bend_mm", 4, 80), ("straight_mm", 0, 40), ("coude_deg", 10, 80), ("tip_mm", 5, 60)):
            if k in t and not (isinstance(t[k], (int, float)) and lo <= t[k] <= hi):
                err(f"tool {t.get('id')}: {k} must be a number from {lo} to {hi}")
    sources = {s.get("id") for s in pack.get("sources") or []}
    step_ids = set()
    types_seen = []
    for s in pack.get("steps") or []:
        sid = s.get("id")
        if not sid: err("a step has no id"); continue
        if sid in step_ids: err(f"step {sid} appears twice")
        step_ids.add(sid)
        t = s.get("type")
        types_seen.append(t)
        if t not in STEP_TYPES: err(f"step {sid}: type {t!r} is not one the engine implements"); continue
        for k in ("label", "prompt", "why"):
            if not s.get(k): err(f"step {sid}: {k} is required")
        if s.get("source") and s["source"] not in sources: err(f"step {sid}: source {s['source']!r} is not in sources")
        if t in STEP_TOOL_KIND:
            tool = tools.get(s.get("tool"))
            if not tool: err(f"step {sid}: tool {s.get('tool')!r} is not in tools")
            elif tool.get("kind") != STEP_TOOL_KIND[t]: err(f"step {sid}: a {t} step needs a {STEP_TOOL_KIND[t]} tool")
        if t in ("palpate", "stab") and s.get("target") not in zones: err(f"step {sid}: target {s.get('target')!r} is not a zone")
        if t == "stab":
            if s.get("edge", "operator") not in DIRS: err(f"step {sid}: edge must be one of {sorted(DIRS)}")
            if s.get("reach") and s["reach"] not in ids: err(f"step {sid}: reach names no layer")
        if t in ("rotate", "turn") and s.get("to") not in ("head", "feet"): err(f"step {sid}: to must be head or feet")
        if t == "choice":
            opts = {o.get("id") for o in s.get("options") or []}
            if len(opts) < 2: err(f"step {sid}: a choice needs two or more options")
            right = list((s.get("correct_by_hand") or {}).values()) + ([s["correct"]] if s.get("correct") else [])
            if not right or any(r not in opts for r in right): err(f"step {sid}: the right option must be one of the options")
        if t == "advance":
            r = s.get("range_mm")
            if not (isinstance(r, list) and len(r) == 2 and r[0] < r[1]): err(f"step {sid}: range_mm must be [low, high]")
        if t == "railroad":
            for k in ("cuff_mm", "depth_mm"):
                r = s.get(k)
                if not (isinstance(r, list) and len(r) == 2 and r[0] < r[1]): err(f"step {sid}: {k} must be [low, high]")
        if t == "inflate":
            r = s.get("range_ml")
            if not (isinstance(r, list) and len(r) == 2 and r[0] < r[1]): err(f"step {sid}: range_ml must be [low, high]")
        if s.get("clicks") and s["clicks"] not in ids: err(f"step {sid}: clicks names no layer")
        eff = s.get("effect") or {}
        if eff.get("remove") and eff["remove"] not in tools: err(f"step {sid}: effect.remove names no tool")
        if eff.get("hand") and eff["hand"] != "free" and eff["hand"] not in (pack.get("hands") or {}):
            err(f"step {sid}: effect.hand {eff['hand']!r} has no line in hands")
    order = [t for t in types_seen if t in ("stab", "rotate", "insert", "turn", "advance", "railroad")]
    if order and order != [x for x in ("stab", "rotate", "insert", "turn", "advance", "railroad") if x in order]:
        err("the instrument steps must come in the order stab, rotate, insert, turn, advance, railroad")
    for d in pack.get("distractors") or []:
        if d.get("id") in step_ids: err(f"distractor {d.get('id')} shares an id with a step")
        if not d.get("feedback"): err(f"distractor {d.get('id')}: feedback is required")

    for where, t in learner_text(pack):
        if "—" in t: err(f"{where}: no em dashes")
        if re.search(r"\bquiet(ly)?\b", t, re.I): err(f"{where}: the word quiet is not used")
        if re.search(r"\[(UNVERIFIED|VERIFY|PubMed|MODEL OUTPUT)", t): err(f"{where}: a reviewer marker would be shown to the learner")
    return E


def load(folder):
    P = os.path.basename(os.path.normpath(folder))
    return json.load(open(os.path.join(folder, P + "-procedure.json"), encoding="utf-8")), P


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    bad = 0
    for f in sys.argv[1:]:
        pack, P = load(f)
        errs = validate(pack, P)
        for e in errs: print("  ERROR:", e)
        print(f"{P}: {len(errs)} errors")
        bad += len(errs)
    sys.exit(1 if bad else 0)
