#!/usr/bin/env python3
"""One-shot, second pass: the standard man and woman, and a transparent figure standing at
the bottom of the room instead of a disc floating in it."""
import os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: anchor found {s.count(old)} times: {old[:70]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)

patch("engine/ui.js", [
("    PT=PATIENT.mount(host,(CASE.patient||{}).avatar); PT_CASE=CASE;\n",
 "    /* The standard man or woman by patient.sex, from SHARED.patient.base. A case may author\n"
 "       patient.avatar to differ from the base, key by key; none does yet. The appearance is\n"
 "       fixed for the whole case: states never touch hair, clothes or colours. */\n"
 "    PATIENT.setBases((SHARED.patient||{}).base);\n"
 "    const p=CASE.patient||{};\n"
 "    PT=PATIENT.mount(host,PATIENT.baseFor(p.sex,p.avatar)); PT_CASE=CASE;\n"),
])
patch("engine/shell.html", [
("  display:flex;align-items:center;justify-content:center;padding:0 12px 4vh;pointer-events:none;\n",
 "  display:flex;align-items:flex-end;justify-content:center;padding:0 12px;pointer-events:none;overflow:hidden;\n"),
(".ptfig{width:min(100%,clamp(140px,52vh,420px));\n"
 "  filter:drop-shadow(0 22px 26px rgba(21,48,66,.24));animation:ptin .7s var(--ease) both}\n",
 "/* No disc and no frame: the figure is transparent and stands on the bottom edge of the\n"
 "   window, which crops the bust where the drawing ends. The small negative margin pushes the\n"
 "   drawing's flat lower edge just out of sight, so a seizure's rotation never lifts a corner\n"
 "   of it into view. */\n"
 ".ptfig{width:min(100%,clamp(150px,62vh,460px));margin-bottom:-1.2%;\n"
 "  filter:drop-shadow(0 0 22px rgba(21,48,66,.20));animation:ptin .7s var(--ease) both}\n"),
(".pt-svg{display:block;width:100%;height:auto;overflow:visible}\n"
 "/* The disc is the same frosted white as the panes, so the figure reads as part of the\n"
 "   interface's glass and not as a sticker on the photograph. */\n"
 ".pt-disc{fill:rgba(255,255,255,.66);stroke:rgba(255,255,255,.95);stroke-width:1.5}\n",
 ".pt-svg{display:block;width:100%;height:auto;overflow:visible;margin-bottom:-3%}\n"),
("   record expanded there is no gap, and the figure fades rather than peeking out\n"
 "   from behind glass.",
 "   record expanded there is no gap, and the figure fades rather than peeking out\n"
 "   from behind glass. The figure is transparent, as the avataaars generator's\n"
 "   Transparent style is, and stands on the bottom edge of the window."),
])
patch("engine/build_simulator.py", [
("    \"eyes\": [\"open\", \"closed\"],\n",
 "    # The standard patient, by patient.sex. avataaars option names. Identical but for the hair,\n"
 "    # on purpose: until cases choose their own bases, the figure should say nothing about a\n"
 "    # patient beyond their sex. A case's patient.avatar overrides these key by key.\n"
 "    \"base\": {\n"
 "        \"male\":   {\"topType\": \"ShortHairShortFlat\", \"accessoriesType\": \"Blank\", \"hairColor\": \"BrownDark\",\n"
 "                   \"facialHairType\": \"Blank\", \"clotheType\": \"ShirtVNeck\", \"clotheColor\": \"Gray01\",\n"
 "                   \"eyeType\": \"Default\", \"eyebrowType\": \"Default\", \"mouthType\": \"Default\",\n"
 "                   \"skinColor\": \"Brown\"},\n"
 "        \"female\": {\"topType\": \"LongHairStraight\", \"accessoriesType\": \"Blank\", \"hairColor\": \"BrownDark\",\n"
 "                   \"facialHairType\": \"Blank\", \"clotheType\": \"ShirtVNeck\", \"clotheColor\": \"Gray01\",\n"
 "                   \"eyeType\": \"Default\", \"eyebrowType\": \"Default\", \"mouthType\": \"Default\",\n"
 "                   \"skinColor\": \"Brown\"},\n"
 "    },\n"
 "    \"eyes\": [\"open\", \"closed\"],\n"),
("        lab = lab.replace(\"__PATIENT_ART__\", jsafe(art)).replace(\"__PATIENT_JS__\", patient_js)\n",
 "        lab = lab.replace(\"__PATIENT_BASES__\", jsafe(shared[\"patient\"][\"base\"]))\n"
 "        lab = lab.replace(\"__PATIENT_ART__\", jsafe(art)).replace(\"__PATIENT_JS__\", patient_js)\n"),
])
print("done")
