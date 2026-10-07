"""Build the EMSim Physician Review page from the question bank.

Usage: python3 cases/review/tool/build.py
Writes cases/review/tool/out/emsim-physician-review.html (the page body the Artifact tool publishes)
and out/test.html (the same page wrapped in a document skeleton, for local testing with test.mjs).
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
bank = json.load(open(os.path.join(HERE, "..", "physician-review-bank.json"), encoding="utf-8"))
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
