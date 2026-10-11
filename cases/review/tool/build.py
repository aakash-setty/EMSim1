"""Build the EMSim Physician Review page from the question bank.

Usage: python3 cases/review/tool/build.py
Writes cases/review/tool/out/emsim-physician-review.html (the page body the Artifact tool publishes)
and out/test.html (the same page wrapped in a document skeleton, for local testing with test.mjs).
"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bank = json.load(open(os.path.join(HERE, "..", "physician-review-bank.json"), encoding="utf-8"))


def merge_pack_banks(bank):
    """A pack's own review questions, `cases/<PREFIX>/<PREFIX>-review-questions.json`, are
    merged in here at build time, so a new case adds questions without editing the shared
    bank. The file holds {"case": {...one entry for `cases`...}, "questions": [...]} with the
    same shape as the shared bank (cases/review/README.md). Ids must not collide."""
    seen_ids = {q["id"] for q in bank["questions"]}
    seen_cases = {c["id"] for c in bank["cases"]}
    for path in sorted(glob.glob(os.path.join(ROOT, "cases", "*", "*-review-questions.json"))):
        prefix = os.path.basename(os.path.dirname(path))
        extra = json.load(open(path, encoding="utf-8"))
        case = extra.get("case")
        if case:
            if case["id"] in seen_cases:
                sys.exit(f"{path}: case {case['id']} is already in the shared bank")
            bank["cases"].append(case); seen_cases.add(case["id"])
        for q in extra.get("questions", []):
            if q["id"] in seen_ids:
                sys.exit(f"{path}: question id {q['id']} is already in the bank")
            q.setdefault("case", prefix)
            bank["questions"].append(q); seen_ids.add(q["id"])
        print(f"merged {len(extra.get('questions', []))} questions from {os.path.relpath(path, ROOT)}")
    return bank


bank = merge_pack_banks(bank)
data = json.dumps(bank, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
page = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
app = open(os.path.join(HERE, "app.js"), encoding="utf-8").read()
assert "</script" not in app
out = page.replace("__BANK__", data, 1).replace("__APP__", app, 1)
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "emsim-physician-review.html"), "w", encoding="utf-8").write(out)
open(os.path.join(HERE, "out", "test.html"), "w", encoding="utf-8").write(
    '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}</style></head><body>' + out + "</body></html>")
print("built", len(out) // 1024, "KB,", len(bank["questions"]), "questions")
