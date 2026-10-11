#!/usr/bin/env python3
"""Look one thing up instead of reading a whole catalog or pack.

    python3 engine/lookup.py action calcium          catalog entries whose id or name contains the word
    python3 engine/lookup.py action calcium_chloride_bolus --full
                                                     the whole entry, including the default result
    python3 engine/lookup.py diagnosis hyperkal      diagnosis entries, with synonyms
    python3 engine/lookup.py field short_label       what a case field does and who reads it
    python3 engine/lookup.py mechanism expiring      a mechanism and its worked example
    python3 engine/lookup.py flags                   every flag the catalog grants, and what tests it
    python3 engine/lookup.py prereq insulin_bolus    the catalog's default prerequisites for an entry

Matching is a case-insensitive substring on the id, the display name and the synonyms.
Without --full an action prints one line per hit; with it, the full JSON.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def load(name):
    with open(os.path.join(ROOT, "catalog", name), encoding="utf-8") as f:
        return json.load(f)


def one_line(e):
    pl = (e.get("placements") or [{}])[0]
    bits = [f"{e['id']:<42} {e.get('display_name', '')}", f"[{pl.get('tab')}/{pl.get('group')}]", e.get("category", "")]
    if e.get("turnaround_class"):
        bits.append(e["turnaround_class"])
    if e.get("flags_set_default"):
        bits.append("sets " + ",".join(e["flags_set_default"]))
    if e.get("default_prerequisites"):
        bits.append(f"{len(e['default_prerequisites'])} prereq")
    if e.get("stops"):
        bits.append("stops " + e["stops"])
    return "  ".join(bits)


def cmd_action(words, full):
    cat = load("action-catalog.json")
    hits = [e for e in cat["entries"] if any(w in (e["id"] + " " + e.get("display_name", "")).lower() for w in words)]
    if not hits:
        print("no catalog entry matches", " ".join(words), "(a missing entry is a catalog change request, authoring 6.1)")
        return 1
    for e in hits:
        if full:
            print(json.dumps(e, indent=1, ensure_ascii=False))
        else:
            print(one_line(e))
    groups = cat.get("equivalence_groups") or {}
    for g, members in groups.items():
        ids = members.get("members", members) if isinstance(members, dict) else members
        if any(e["id"] in ids for e in hits):
            print(f"\nequivalence group {g}: " + ", ".join(ids))
    return 0


def cmd_diagnosis(words):
    d = load("diagnosis-catalog.json")
    ents = d.get("entries") or max((v for v in d.values() if isinstance(v, list)), key=len)
    hits = [e for e in ents if any(w in (e["id"] + " " + e.get("display_name", "") + " " + " ".join(e.get("synonyms") or [])).lower() for w in words)]
    if not hits:
        print("no diagnosis matches", " ".join(words), "(a missing entry is a catalog change request, authoring 10.1)")
        return 1
    for e in hits:
        print(f"{e['id']:<48} {e.get('display_name', '')}  [{e.get('category', '')}]  " + ", ".join(e.get("synonyms") or []))
    return 0


def cmd_field(words):
    from field_notes import FIELDS
    hits = [(k, v) for k, v in FIELDS.items() if any(w in k.lower() for w in words)]
    if not hits:
        print("no field note matches", " ".join(words), "(see docs/generated/field-reference.md for every field)")
        return 1
    for k, (sees, section, note) in hits:
        print(f"{k}\n   sees: {sees}   section: {section or '(note)'}\n   {note}")
    return 0


def cmd_mechanism(words):
    p = os.path.join(ROOT, "docs", "generated", "mechanism-index.md")
    if not os.path.exists(p):
        print("docs/generated/mechanism-index.md is missing: run python3 engine/gen_docs.py")
        return 1
    n = 0
    for line in open(p, encoding="utf-8"):
        if line.startswith("| ") and any(w in line.lower() for w in words):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0] != "mechanism":
                print(f"{cells[0]}\n   {cells[1]}\n   authoring section {cells[2]}, example {cells[3]}")
                n += 1
    if not n:
        print("no mechanism matches", " ".join(words))
        return 1
    return 0


def cmd_flags():
    cat = load("action-catalog.json")
    granted, tested = {}, {}
    for e in cat["entries"]:
        for fl in e.get("flags_set_default") or []:
            granted.setdefault(fl, []).append(e["id"])
        for pr in e.get("default_prerequisites") or []:
            w = pr.get("when", pr) if isinstance(pr, dict) else pr
            for fl in re.findall(r"flag (\w+) set", str(w)):
                tested.setdefault(fl, set()).add(e["id"])
    print("catalog-owned flags (a case flag with one of these names collides):")
    for fl in sorted(set(granted) | set(tested)):
        print(f"  {fl:<24} granted by {', '.join(granted.get(fl, [])) or 'nothing'}; tested by {len(tested.get(fl, []))} entries")
    return 0


def cmd_prereq(words):
    cat = load("action-catalog.json")
    hits = [e for e in cat["entries"] if e["id"] in words or any(w in e["id"] for w in words)]
    if not hits:
        print("no catalog entry matches", " ".join(words))
        return 1
    for e in hits:
        print(e["id"])
        for pr in e.get("default_prerequisites") or []:
            print("   ", json.dumps(pr, ensure_ascii=False))
        if not e.get("default_prerequisites"):
            print("    (no catalog prerequisites)")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv
    if not args:
        print(__doc__)
        return 2
    what, words = args[0], [w.lower() for w in args[1:]]
    if what == "action":
        return cmd_action(words, full)
    if what == "diagnosis":
        return cmd_diagnosis(words)
    if what == "field":
        return cmd_field(words)
    if what == "mechanism":
        return cmd_mechanism(words)
    if what == "flags":
        return cmd_flags()
    if what == "prereq":
        return cmd_prereq(words)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
