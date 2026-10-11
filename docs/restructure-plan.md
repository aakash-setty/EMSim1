# Restructure plan: a repository that hundreds of cases do not outgrow

Started 7 October 2026. Owner: Aakash Setty. Executed by Claude sessions, one step per
delivery. This file is the record any session reads first: the goal, the decisions, what
is done, what is verified, and what must not be done. Update it in the same delivery as
the change it describes.

## The goal

An AI that has never seen this repository builds a new case correctly from a fixed set of
files, never opens anything else, and misses nothing. That set must not grow as cases are
added, and adding a case must not edit any shared file.

Today a builder reads about 160,000 tokens (measured, see `docs/cold-start-test.md`),
including the whole validator and a whole existing pack, because the case file format is
written down nowhere and rules sit in several places. Every new case makes it worse.

## The mission the cases serve

`docs/case-design-guide.md`. The learner is the doctor and the patient responds to them.
No template: two cases that follow the guide should look nothing alike. Nothing clinical here is reviewed
by a physician unless a SEED names the decision, the person and the date (README, Trust).

## Decisions taken

| Date | Decision | By |
|---|---|---|
| 7 Oct 2026 | Where the design guide and the authoring requirements conflict, the guide governs. Cases must still fit the engine. Restrictions and guardrails are kept to what is necessary | Aakash |
| 7 Oct 2026 | The interview expansions of AFRVR, CHFE, DIPH and MGCA are frozen as committed. The tools that write them refuse to run on them without `--force` | Aakash |
| 7 Oct 2026 | CHFE and MGCA stay as JSON packs, marked legacy. Not converted | Aakash |
| 8 Oct 2026 | The ledger of changes to the authoring document is reviewed by Aakash before any text changes. He reviews the clinical and teaching-policy rows in full and spot-checks the rest | Aakash |
| 8 Oct 2026 | No other session edits `docs/` while step 2 runs | Aakash |
| 8 Oct 2026 | The core plus mechanism-section structure for the authoring document is accepted | Aakash |
| 9 Oct 2026 | Authoring decisions 1 to 6 of the 21 (`claude/ledger-2026-10-09-0-owner-decisions.md`): (1) no rule on phase count, guidance that a case runs around four to ten phases; (2) the clock is used seldom, and is a tool the case may pull in to force action where that helps the case; (3) a harmful action may end the case early, used sparingly so the learner is not discouraged; (4) three to six learning goals stays; (5) prompts name the problem by default and the drug only where the case decides so, prompt-first rule stays; (6) the floors are the only hard deadline rule, generosity is guidance. (7) no diagnosis in the handover stays a must, the other handover rules become defaults with the reason stated per case, vague but never wrong on purpose, the two-sentence check becomes a warning; (8) required topic coverage stays a must; (9) model-added denials allowed, listed in provenance and covered by the sign-off. (10 to 13) recommendations applied at the builder's judgment, with the owner's framing: a physician validates every case, the builder's prompt may be incomplete, and the builder's job is to work out the EM learning goals for the case from several sources and proceed; (14 to 20) recommendations accepted; (21) rejected, the priority order sentence is not put into the authoring document. All 21 answered | Aakash |

## The reading kit

What a builder reads for every case. Measured by `python3 engine/kit_check.py`, which
fails above the budget.

| File | Role | Status |
|---|---|---|
| `CLAUDE.md` | Start file: reading order by task, the build chain, what not to open | step 0 |
| `README.md` | How the repository is put together and how to work in it | exists |
| `docs/case-design-guide.md` | What a case is for | exists |
| `docs/case-authoring-requirements.md` | The rules. Part One is the core (sections 0 to 13), Part Two one section per optional mechanism (14 to 24), read only when the case uses it. Every rule labeled Engine, Truth or Default | rewritten 12 Oct 2026, 27,900 tokens (was 48,700) |
| `docs/generated/field-reference.md` | Every case field: what reads it, what the learner sees, which section governs it | exists |
| `docs/generated/action-index.md` | One line per catalog entry | exists |
| `docs/generated/case-index.md` | One line per case on the design guide's variety dimensions, from `metadata.library` | exists |
| Lookups, not reads: `engine/lookup.py`, `docs/generated/diagnosis-index.md`, `docs/generated/mechanism-index.md` | A full catalog entry, a diagnosis id, a field note, one worked example per mechanism by file and line | exists |
| The scaffold and seed template | The format, with a pointer beside each field | step 3 |

Never opened to build a case: another pack, `CHANGELOG.md`, `docs/system-design-v2.md`,
any generated file in a pack, `cases/review/`, `docs/readme-reference.md`,
`docs/spec-addendum.md`, `docs/decisions/`.

Budget: see `engine/kit_check.py`. It is set at the measured size plus headroom and is
lowered as steps land.

## Steps

| Step | What | Status | Verified by |
|---|---|---|---|
| 0 | This file. `CLAUDE.md`. `engine/kit_check.py`. The three interview tools refuse to write frozen packs without `--force`. `engine/site-check/flow.js` counts cases instead of asserting four. `docs/cold-start-test.md` written and the baseline run | done 9 Oct 2026 | all suites, site check 54 ok, baseline scored |
| 1 | Generated lookups: field reference, action and diagnosis indexes with a lookup command, mechanism index, case index. Generators under `engine/`, output under `docs/generated/`, regenerated by the build chain | done 9 Oct 2026 | all suites and the validator on the Mac, kit check 0 errors at 79,058 tokens, an independent check of 146 field-reference rows against the code (18 corrected) |
| 2 | The authoring document rewritten from the four ledgers (578 rows) and the 21 owner decisions: core plus mechanism sections, history out, stale examples fixed, every rule labeled Engine, Truth or Default, the guide's seed requirements (library difference, sourced goals, stories, states, the idea that travels) in section 2 and the sign-off. Section numbers remapped in `engine/field_notes.py`, the mechanism index, the validator's messages, the scaffold and every pack's source comments. Six validator checks the text names as engine facts added with nine tests (a transition into `case_complete` on every non-terminal phase, a narration on an instant rule warns, correct and alternative diagnosis ids resolve, a dead `waived` string warns, the two-sentence handover is a warning, `global_answer_rules` may be empty). The splash says time is compressed (decision 14). Kit budget lowered to 65,000 | done 12 Oct 2026 | an independent agent checked every Engine claim against the code (7 wrong and 20 imprecise, all corrected), kit check 0 errors at 58,994 tokens, `engine/test_packs.py` 7 packs 0 failed, case files byte-identical except the remapped section numbers inside authored note strings (listed in the delivery log) |
| 3 | DKA named the reference pack. `new_case.py` scaffolds the Python layout with placeholders and one-line pointers. Seed template carrying the design guide's requirements and the case-index block | pending | |
| 4 | Stop per-case edits to shared files. The topic map moved into each Python pack (`TOPIC_MAP`, `EXTRA_COVERED` in `case_4_interview.py`) and the bank is expanded at build time by `catalog/interview_expand.py`, so the generated block is gone from TSS, TAKO and DKA (each `case_4_interview.py` about 750 lines shorter). `catalog/expand_interview_variants.py` keeps the four frozen packs only and asserts so. The physician review page merges one optional `cases/XX/XX-review-questions.json` per pack at build time, the shared bank untouched. A case's history lives in its own folder (README). `engine/kit_check.py` check 5 fails on any per-pack table or pack path in `engine/` or `catalog/` outside the three frozen scripts. Voice aliases: not changed, see below | done 9 Oct 2026 | TSS, TAKO and DKA `*-case.json`, `*-matcher-tune-questions.json` and `*-binding-map.json` byte-identical before and after, also when expanded from sources with no prior block. Site and build byte-identical to step 5. `engine/test_packs.py` 7 packs 0 failed. Kit check 0 errors, negative test of check 5 passes |
| 5 | Validator gaps closed with tests (tag values, the follow-ups field, crashes on bad input, the fairness bypass, CHFE flag names in `implausible()`). A per-pack test runner that builds one pack at a time. Two engine-test checks that forced unasked authoring fixed | done 9 Oct 2026 | `engine/test_packs.py` 7 packs 0 failed on the Mac (68 s) and in the cloud (28 s), the full-build suites and site check 54 ok in the cloud, 13 new negative tests, review matrices byte-identical |
| 6 | Layout: generated files in a marked subfolder, `build/` out of git, legacy markers on CHFE and MGCA, the six CHFE migration scripts archived, `cases/review` moved out of `cases/` | pending | |
| 7 | The cold-start test rerun with the kit, compared with the baseline | pending | |

## The rule for every delivery

Every `cases/*/*-case.json` and `site/index.html` byte-identical to the previous delivery
where no content change was intended, and every intended change listed. All suites, the
validator for every pack, and `engine/kit_check.py` pass in the cloud and again on the
Mac after install. Nothing in `engine/` names a case.

## Frozen, and why

- `catalog/expand_interview_variants.py` on AFRVR, CHFE, DIPH or MGCA: the committed
  expansions were hand-edited afterwards and cannot be regenerated. DIPH's output differs
  on every run. The script refuses without `--force`.
- `catalog/author_interview_facts.py` and `catalog/author_interview_volunteers.py`: same
  reason. On CHFE a re-run reverts 19 hand-edited fact guards with no error. Both refuse
  without `--force`.

Voice aliases (`catalog/build_voice_aliases.py`) are keyed by catalog id, not by case. A
case adds a spoken phrase only when it adds a catalog entry, which is a catalog change by
definition (README, "New catalog entry"). There is no per-case edit to remove, so the step
4 item "voice aliases as data" is closed without a change.

## Open for the owner

- CHFE's `norepinephrine_infusion` waives `central_venous_access_required`, which names no
  catalog prerequisite and so waives nothing. The validator now warns on it. Delete the
  entry, or leave the warning (CHFE is legacy).
- The system design (`docs/system-design-v2.md`) still carries the old authoring section
  numbers where it cites them. It is not in the kit and is read for engine work only.

## Content that cannot be regenerated

- `cases/review/physician-review-bank.json`: 27 signed physician decisions.
- The physician decision tables in `cases/AFRVR/AFRVR-review-packet.md` and the "What a
  person decided" sections of the SEED files.

## Where the audit is

Nine audit notes with file:line citations, written 7 October 2026 against v0.23a, are in
the Claude project as `claude/audit-2026-10-07-*.md`. Their line numbers predate v0.24.
Every finding is re-checked against the current files before it is acted on.

## Delivery log

| Date | Step | Delivered as | Mac verification |
|---|---|---|---|
| 9 Oct 2026 | 4 | `Claude outputs/emsim-restructure-step4.tgz` | installed, 16 files by md5. No content change intended and none made: TSS, TAKO and DKA case files, tuning files and binding maps rebuilt on the Mac byte-identical (cbb16041, 25ed0c6d, 515363a8), site and build unchanged (4c2e4be0, 025666d4). `engine/test_packs.py` 7 packs 0 failed on the Mac (72 s), gen_docs and kit check 0 errors, review page builds. The plan file on the Mac had been the step 0 version (the step 1 and 5 delivery rows were added after those tarballs were cut); this delivery carries the full file |
| 9 Oct 2026 | 5 | `Claude outputs/emsim-restructure-step5.tgz` | installed, 13 files by md5. Intended content change: `review_hints.implausible` added to CHFE (its two matrix pairs as data), so CHFE's pack and the site stubs changed (site 4c2e4be0, build 025666d4). `engine/test_packs.py` passes every pack on the Mac; the Mac rebuild reproduces the cloud build |
| 9 Oct 2026 | 1 | `Claude outputs/emsim-restructure-step1.tgz` | installed, 34 files by md5. Intended content change: `metadata.library` added to every case (the six variety dimensions), so every case file, the private packs and the site stubs changed (site 969872eb, build a380a142). Seven engine suites, seven scenario runs and the validator pass on the Mac; gen_docs --check and kit check 0 errors |
| 9 Oct 2026 | 0 | `Claude outputs/emsim-restructure-step0.tgz` | installed, 10 files by md5, site and build unchanged (aed3ecf0, ff42ac00), seven engine suites pass, kit check 0 errors. Site check 54 ok was run in the cloud only |
