#!/usr/bin/env python3
"""Bind case action ids to action-catalog ids.

Case-agnostic. The mapping itself lives in the case pack as
`<PREFIX>-binding-map.json`, because a mapping is an author judgement and belongs
with the case rather than in engine code.

Three statuses are derived, not authored:

  exact     the case id is already a catalog id
  mapped    a different id for the same action; the author's note says why
  unmatched the catalog has no entry for it

Nothing here invents a catalog entry. Unmatched rows become validator errors and
catalog change requests; they are not silently dropped, because several of them are
usually load-bearing.

    python3 engine/bind_catalog.py [cases/CHFE]
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_pack, catalog_path

PACK = resolve_pack(sys.argv)
CAT = catalog_path("action-catalog.json")
CASE = PACK.case


def load_binding_map():
    with open(PACK.binding_map) as f:
        doc = json.load(f)
    out = {}
    for r in doc["rows"]:
        out[r["case_id"]] = (r.get("catalog_id"), r.get("note"))
    return out


def load_group_coverage():
    """also_covers / also_covers_group: one case action claiming several catalog entries.

    Needed wherever the case is making a claim about the act rather than about one
    agent. A harmful tag bound to normal saline alone leaves lactated Ringer's as an
    unguarded route to the same harm.
    """
    with open(PACK.binding_map) as f:
        doc = json.load(f)
    with open(CAT) as f:
        groups = json.load(f).get("equivalence_groups", {})
    out = {}
    for r in doc["rows"]:
        extra = list(r.get("also_covers") or [])
        g = r.get("also_covers_group")
        if g:
            if g not in groups:
                raise SystemExit(f"{r['case_id']}: no equivalence group {g!r} in the catalog")
            extra += [x for x in groups[g] if x != r.get("catalog_id")]
        if extra:
            out[r["case_id"]] = sorted(set(extra))
    return out


BINDING = load_binding_map()
COVERAGE = load_group_coverage()


def main():
    cat = json.load(open(CAT))
    E = {x["id"]: x for x in cat["entries"]}
    case = json.load(open(CASE))
    case_ids = [a["catalog_id"] for a in case["case_actions"]]

    rows, missing_from_binding, bad_target = [], [], []
    for cid in case_ids:
        if cid not in BINDING:
            missing_from_binding.append(cid)
            continue
        target, note = BINDING[cid]
        if target is None:
            status = "unmatched"
        elif target == cid:
            status = "exact"
        else:
            status = "mapped"
            if target not in E:
                bad_target.append((cid, target))
        row = {"case_id": cid, "catalog_id": target, "status": status, "note": note}
        if cid in COVERAGE:
            bad = [x for x in COVERAGE[cid] if x not in E]
            if bad:
                bad_target.extend((cid, x) for x in bad)
            row["also_covers"] = COVERAGE[cid]
        rows.append(row)

    out = {
        "binding_version": "0.1",
        "case_id": case["case_id"],
        "catalog_version": cat["catalog_version"],
        "status": "DRAFT. Every mapped row is an author judgement and needs review.",
        "counts": {s: sum(1 for r in rows if r["status"] == s) for s in ("exact", "mapped", "unmatched")},
        "group_coverage": {r["case_id"]: r["also_covers"] for r in rows if r.get("also_covers")},
        "blocking": [r["case_id"] for r in rows
                     if r["status"] == "unmatched" and r["note"] and r["note"].startswith("BLOCKING")],
        "rows": rows,
    }
    json.dump(out, open(PACK.binding, "w"), indent=1)
    print("binding written:", os.path.relpath(PACK.binding, os.path.dirname(CAT) + "/.."), out["counts"])
    if missing_from_binding:
        print("case actions with no binding row:", missing_from_binding)
    if bad_target:
        print("binding points at ids that are not in the catalog:", bad_target)
    if out["blocking"]:
        print("BLOCKING unmatched:", out["blocking"])
    return 1 if (missing_from_binding or bad_target) else 0


if __name__ == "__main__":
    sys.exit(main())
