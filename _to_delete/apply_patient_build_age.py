#!/usr/bin/env python3
"""One-shot: body build and age group."""
import json, os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: {s.count(old)}x {old[:60]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)
patch("engine/ui.js", [(
 "    PT=PATIENT.mount(host,PATIENT.baseFor(p.sex,p.avatar)); PT_CASE=CASE;\n",
 "    /* The age group is drawn from patient.age, which every case already has. A case may\n"
 "       still author avatar.ageGroup to overrule it, for a patient who looks older or younger\n"
 "       than their years. Build has no number to come from and is authored. */\n"
 "    const av=Object.assign({ageGroup:PATIENT.ageGroupFor(p.age)},p.avatar||{});\n"
 "    PT=PATIENT.mount(host,PATIENT.baseFor(p.sex,av)); PT_CASE=CASE;\n")])
patch("engine/build_simulator.py", [(
 "    \"eyes\": [\"open\", \"closed\"],\n",
 "    # Two appearance keys that are not avataaars options. build is authored in patient.avatar.\n"
 "    # ageGroup is derived from patient.age by the interface (under 40, 40 to 59, 60 and over)\n"
 "    # and may be overruled there.\n"
 "    \"builds\": [\"thin\", \"average\", \"obese\"],\n"
 "    \"ageGroups\": [\"young\", \"middle\", \"older\"],\n"
 "    \"eyes\": [\"open\", \"closed\"],\n")])
patch("engine/validate_case.py", [
 ("PATIENT_EYES = {\"open\", \"closed\"}\n",
  "PATIENT_EYES = {\"open\", \"closed\"}\nPATIENT_BUILDS = {\"thin\", \"average\", \"obese\"}\nPATIENT_AGE_GROUPS = {\"young\", \"middle\", \"older\"}\n"),
 ("                if k in PATIENT_AVATAR_PARTS:\n",
  "                if k == \"build\":\n"
  "                    if v not in PATIENT_BUILDS:\n"
  "                        errors.append(f\"[patient] avatar.build {v!r} is not one of {sorted(PATIENT_BUILDS)}\")\n"
  "                elif k == \"ageGroup\":\n"
  "                    if v not in PATIENT_AGE_GROUPS:\n"
  "                        errors.append(f\"[patient] avatar.ageGroup {v!r} is not one of {sorted(PATIENT_AGE_GROUPS)}\")\n"
  "                    warnings.append(\"[patient] avatar.ageGroup overrules the group drawn from patient.age; \"\n"
  "                                    \"make sure that is meant\")\n"
  "                elif k in PATIENT_AVATAR_PARTS:\n")])
patch("engine/engine-tests.js", [(
 "    chk('the standard patient is not smiling',",
 "    chk('age bands: under 40 young, 40 to 59 middle, 60 and over older',\n"
 "        [18, 39, 40, 59, 60, 100].map(PATIENT.ageGroupFor).join() === 'young,young,middle,middle,older,older');\n"
 "    chk('build and age group are validated like any other avatar key',\n"
 "        PATIENT.normalizeAppearance({ build: 'obese', ageGroup: 'older' }).problems.length === 0 &&\n"
 "        PATIENT.normalizeAppearance({ build: 'huge', ageGroup: 'ancient' }).problems.length === 2);\n"
 "    chk('build and age vocabularies agree with the shared block',\n"
 "        same(voc.builds, sp.builds) && same(voc.ageGroups, sp.ageGroups));\n"
 "    chk('the standard patient is not smiling',")])
patch("docs/case-authoring-requirements.md", [(
 "`content_keys.patient_visual` says what is visible now.",
 "Two appearance keys are not avataaars options. `\"build\"` is `thin`, `average` or `obese`, and\n"
 "is the one key worth authoring now: write it only where the seed or the presenting appearance\n"
 "says so. The age group is **not authored**: the figure is drawn young under 40, middle from\n"
 "40 to 59 and older from 60, from `patient.age`, with greying hair and facial lines.\n"
 "`\"ageGroup\"` in the avatar overrules that, with a validator warning.\n\n"
 "`content_keys.patient_visual` says what is visible now.")])
p = os.path.join(ROOT, "cases", "CHFE", "CHFE-case.json"); j = json.load(open(p))
j["patient"]["avatar"] = {"authoring_note": ("Only what differs from the standard patient. build is obese from the presenting "
    "appearance, 'a heavy-set older man', and 88 kg; the case gives no height, so this is the text's word and not a BMI. "
    "The age group is not authored: it is drawn from patient.age."), "build": "obese"}
with open(p, "w") as f: json.dump(j, f, indent=1, ensure_ascii=False); f.write("\n")
print("edited", p)
p = os.path.join(ROOT, "CHANGELOG.md"); s = open(p).read()
a = "## v0.17f: a check of the patient figure"; assert s.count(a) == 1
s = s.replace(a, """## v0.17g: build and age

**Build.** `patient.avatar.build` is `thin`, `average` or `obese`. avataaars has one head and one
torso, so both work by suggestion. Obese: a fuller lower face with a second chin under the
first, drawn in the skin tone beneath the features so jaundice follows it, a head 6 percent
wider and a torso 14 percent wider, which takes the neck with it. Thin: a head 7 percent
narrower, a torso 13 percent narrower, hollows under the cheekbones, shadowed temples and the
two cords of the neck. Every device still fits on both.

**Age.** Three groups on the author's bands: young under 40, middle 40 to 59, older 60 and
over. The bands as given overlap at 40 and 60; a patient of exactly 40 draws as middle and of
exactly 60 as older. The hair and any facial hair grey part way at middle and fully at older,
the eyebrows stay dark, and lines are drawn on the face: at middle a forehead line and the
folds from nose to mouth, faintly; at older those deeper, two more forehead lines, crow's feet
and the lower lids. **The age group is not authored.** The interface derives it from
`patient.age`, which every case has; `avatar.ageGroup` overrules it with a validator warning.
Hairstyles do not change with age.

**Applied.** By age with no edit: CHFE (65) and AFRVR (68) draw as older, MGCA (21) and DIPH
(18) as young. No case has a middle-aged patient. By text: CHFE is `obese`, from 'a heavy-set
older man'. No other case's text describes a build, and none describes a thin patient, so the
rest stay average; weights alone (84, 60 kg) with no height say nothing.

Both are fixed for the case and mount from the appearance; a case cannot switch them on as
add-ons. The depiction of obesity and of age on a cartoon face is the model's and is the kind
of thing worth a second opinion before learners see it.

""" + a)
open(p, "w").write(s); print("patched CHANGELOG.md")
