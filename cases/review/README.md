# Physician review

The open clinical decisions for all four cases, as one question bank, and the page physicians use to answer them.

Page: [EMSim Physician Review](https://claude.ai/artifact/DarnShPm7RCY5X8urhY7q9) (private claude.ai artifact, owner Aakash Setty).

## Files

| File | What it is |
|---|---|
| `physician-review-bank.json` | The question bank. 209 questions: AFRVR 35, CHFE 44, DIPH 46, MGCA 45, cross-case 39. Each has a `short` block (2 to 3 bullet situation, one line on the case now, one line per option, a short reason) that the page shows by default, plus the full context, what the case does now, verbatim quotes, three options with the exact file change each implies, a recommendation and its reasoning, and a content hash. |
| `tool/page.html`, `tool/app.js` | The page source. The bank is inlined at build time. |
| `tool/build.py` | Builds `tool/out/emsim-physician-review.html` (what gets published) and `tool/out/test.html` (for local tests). |
| `tool/test.mjs` | Headless browser test of every interaction: blind reveal, change after reveal, own answer, abstain, flags, undo and redo, filters, persistence, export round trip, consensus import, the shared store with a fake runtime, owner-only consensus, phone width and dark theme. Run with `PW=$(npm root -g)/playwright node cases/review/tool/test.mjs` after building. |

## How the bank was built (29 September 2026)

Five drafting agents, one per case plus one cross-case, read the review packets, seeds, deterioration timelines, review matrices, CHANGELOG v0.18a to v0.18c and the v0.18a audit, and checked every statement about current behavior against the case JSON. A merge review removed one duplicate (AFRVR-14 into ALL-03), resolved two contradicting recommendations (ALL-03, CHFE-22), and relabelled check options. An independent verifier then re-checked all 58 high-priority questions against the case files and found 5 errors and 13 minor issues, all corrected. The bank's `merge_log` records each change.

The packets for AFRVR, CHFE and DIPH predate the v0.18a audit and are stale in many places. Each case entry in the bank lists its `stale_packet_findings`. Questions follow the case JSON, not the packet.

Case JSON SHA-256 at the time of writing is stored per case (`cases[].case_json_sha256`). If a case changes, re-verify the affected questions before applying answers.

## How answers come back

1. Each reviewer's answers save to the artifact's database at `reviews/<their account id>`. Reviewers must be invited by email as Editors to save there. Access rules: only the owner reads the `reviews` collection. Each reviewer reads and writes only their own document. Verified after publishing.
2. Reviewers without edit access work in their browser and export text from Progress and export.
3. The owner's Consensus tab shows all reviewers side by side, imports exported text, and produces a combined paste-back.
4. A Claude session can also read the answers directly with the ArtifactData tool (`list` on collection `reviews`).

## Changing the bank

Edit `physician-review-bank.json`, bump `bank_version`, recompute each changed question's `hash` (first 10 hex characters of the SHA-256 of Python `json.dumps({title, question, current, options, recommended}, sort_keys=True, ensure_ascii=False)`), rebuild, and republish to the same artifact URL. Answers given against an older hash show as "Question changed since you answered".
