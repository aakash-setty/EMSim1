#!/usr/bin/env python3
"""One-shot, in-place edits that wire engine/patient.js into the simulator.
Every replacement asserts that its anchor exists exactly once, so a drifted file
stops the script instead of being half-patched. Safe to delete after it has run."""
import os, sys
ROOT = sys.argv[1]
def patch(rel, pairs):
    p = os.path.join(ROOT, rel); s = open(p).read()
    for old, new in pairs:
        assert s.count(old) == 1, f"{rel}: anchor found {s.count(old)} times: {old[:70]!r}"
        s = s.replace(old, new)
    open(p, "w").write(s); print("patched", rel)

# ---------------------------------------------------------------- engine.js
patch("engine/engine.js", [
("let PHASE={}, ACT={}, FU={}, CK=null, CONTENT={}, GENERAL_STATUS=null;",
 "let PHASE={}, ACT={}, FU={}, CK=null, CONTENT={}, GENERAL_STATUS=null, PATIENT_VISUAL=null;"),
("  GENERAL_STATUS = CK.general_status ? CK.general_status.rules : null;\n",
 "  GENERAL_STATUS = CK.general_status ? CK.general_status.rules : null;\n"
 "  PATIENT_VISUAL = CK.patient_visual ? CK.patient_visual.rules : null;\n"),
("/* The line above the exam list. Case rules first, catalog default second. */",
 "/* What the figure in the room is doing. A guarded rule list like any other content key:\n"
 "   first match wins and the value is the whole visible state. The engine resolves it and\n"
 "   understands none of it; engine/patient.js draws it. A case that authors nothing gets the\n"
 "   shared default, a patient with open eyes who is breathing and nothing else. */\n"
 "function patientVisual(st){\n"
 "  if(PATIENT_VISUAL){\n"
 "    const v=resolve(PATIENT_VISUAL,st);\n"
 "    if(v) return {value:v,source:'case'};\n"
 "  }\n"
 "  return {value:(SHARED.patient&&SHARED.patient.visualDefault)||{},source:'default'};\n"
 "}\n\n"
 "/* The line above the exam list. Case rules first, catalog default second. */"),
])

# ---------------------------------------------------------------- ui.js
patch("engine/ui.js", [
("/* ---------- nurse ---------- */",
 "/* ---------- the patient in the room ----------\n"
 "   Mounted once per bound case, then told the visible state every frame. setState is a\n"
 "   string compare when nothing has changed, so calling it from the frame loop costs nothing.\n"
 "   The respiratory rate is the one on the monitor, ramp included, so the chest and the number\n"
 "   never disagree; it is read from what the monitor last showed rather than by calling\n"
 "   rampedVitals again, which would re-arm the ramp. The figure is there whether or not the\n"
 "   monitor is on: a resident can see a patient breathe without a monitor. Paused means\n"
 "   still, for the reason the monitor's jitter stops: movement behind a Paused overlay says\n"
 "   the case is still going. */\n"
 "let PT=null, PT_CASE=null;\n"
 "function renderPatient(){\n"
 "  const host=el('patientfig');\n"
 "  if(!host||typeof PATIENT==='undefined'||!PATIENT.available||!ST) return;\n"
 "  if(!PT||PT_CASE!==CASE){\n"
 "    if(PT) PT.destroy();\n"
 "    PT=PATIENT.mount(host,(CASE.patient||{}).avatar); PT_CASE=CASE;\n"
 "  }\n"
 "  const v=Object.assign({},patientVisual(ST).value);\n"
 "  const shown=RAMP_SHOWN||targetVitals()||{};\n"
 "  if(typeof shown.respiratory_rate==='number') v.respiratory_rate=shown.respiratory_rate;\n"
 "  PT.setState(v);\n"
 "  PATIENT.setPaused(PAUSED||ENDED);\n"
 "}\n"
 "function clearPatient(){ if(PT){ PT.destroy(); PT=null; PT_CASE=null; } }\n\n"
 "/* ---------- nurse ---------- */"),
("  renderMonitor(); renderNurse(); renderRail();\n  requestAnimationFrame(tick);",
 "  renderMonitor(); renderNurse(); renderRail(); renderPatient();\n  requestAnimationFrame(tick);"),
("  renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();\n  VOICE.paint();",
 "  renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor(); renderPatient();\n  VOICE.paint();"),
("function backToPicker(){\n  VOICE.reset();\n",
 "function backToPicker(){\n  VOICE.reset();\n  clearPatient();\n"),
])

# ---------------------------------------------------------------- shell.html
patch("engine/shell.html", [
("/* ============================================================\n   LEFT PANEL: the workspace. Slides out from behind the rail.",
 "/* ============================================================\n"
 "   THE PATIENT. A drawn figure standing in the room, in the gap between the\n"
 "   workspace and the record. It sits above the room photograph and below every\n"
 "   panel, so a panel that widens simply covers it, and it never takes a click.\n"
 "   The stage spans exactly the gap: its left edge is the workspace's right edge\n"
 "   (the same min() the panel uses for its width) or the rail when the workspace\n"
 "   is closed, and its right edge is the record. Closing the workspace therefore\n"
 "   slides the patient to the middle of the room and lets them grow. With the\n"
 "   record expanded there is no gap, and the figure fades rather than peeking out\n"
 "   from behind glass. The drawing is engine/patient.js.\n"
 "   ============================================================ */\n"
 ".ptstage{position:fixed;z-index:5;top:var(--top);bottom:0;right:var(--rdock);\n"
 "  left:calc(var(--rail) + min(var(--lwidth),calc(100vw - var(--rail) - var(--rdock) - 20px)));\n"
 "  display:flex;align-items:center;justify-content:center;padding:0 12px 4vh;pointer-events:none;\n"
 "  transition:left .42s var(--ease),right .42s var(--ease),opacity .3s ease}\n"
 "body[data-left=\"closed\"] .ptstage{left:var(--rail)}\n"
 "body[data-right=\"wide\"] .ptstage{opacity:0}\n"
 ".ptfig{width:min(100%,clamp(140px,52vh,420px));\n"
 "  filter:drop-shadow(0 22px 26px rgba(21,48,66,.24));animation:ptin .7s var(--ease) both}\n"
 "@keyframes ptin{from{opacity:0;transform:translateY(10px) scale(.97)}to{opacity:1;transform:none}}\n"
 ".pt-svg{display:block;width:100%;height:auto;overflow:visible}\n"
 "/* The disc is the same frosted white as the panes, so the figure reads as part of the\n"
 "   interface's glass and not as a sticker on the photograph. */\n"
 ".pt-disc{fill:rgba(255,255,255,.66);stroke:rgba(255,255,255,.95);stroke-width:1.5}\n\n"
 "/* ============================================================\n   LEFT PANEL: the workspace. Slides out from behind the rail."),
("@media (max-width:1000px){\n  :root{--rdock:max(30vw,300px)}\n",
 "@media (max-width:1000px){\n  :root{--rdock:max(30vw,300px)}\n"
 "  /* the workspace covers the room at this width, so the figure shows only when it is closed */\n"
 "  .ptstage{left:var(--rail);opacity:0}\n"
 "  body[data-left=\"closed\"] .ptstage{opacity:1}\n"
 "  body[data-left=\"closed\"][data-right=\"wide\"] .ptstage{opacity:0}\n"),
("<div id=\"playview\">\n",
 "<div id=\"playview\">\n\n"
 "  <div class=\"ptstage\" id=\"patientstage\"><div class=\"ptfig\" id=\"patientfig\"></div></div>\n"),
])

# ---------------------------------------------------------------- build_simulator.py
patch("engine/build_simulator.py", [
("\nDX_IDS = {d[\"id\"] for d in shared[\"diagnoses\"]}",
 "\n# The figure in the room. What a case may say about what is visible, and nothing about why.\n"
 "# The part and colour options are not restated here: engine/patient-art.json is their one\n"
 "# vocabulary, and both the renderer and the validator read it. The add-on list IS restated,\n"
 "# in validate_case.py (PATIENT_ADDONS) and in the register() calls in engine/patient.js, and\n"
 "# engine-tests.js fails if the three disagree.\n"
 "shared[\"patient\"] = {\n"
 "    \"_note\": (\"The patient figure (engine/patient.js). content_keys.patient_visual is a guarded \"\n"
 "              \"rule list whose value is the whole visible state; patient.avatar is the fixed \"\n"
 "              \"appearance in avataaars option names. The respiratory rate is never authored \"\n"
 "              \"here: the figure breathes at the monitor's rate. Nothing in this block \"\n"
 "              \"associates any of it with a diagnosis.\"),\n"
 "    \"eyes\": [\"open\", \"closed\"],\n"
 "    \"work_of_breathing\": [\"normal\", \"increased\", \"severe\"],\n"
 "    \"addons\": [\"gaze_left\", \"gaze_right\", \"nystagmus\", \"nasal_cannula\"],\n"
 "    \"visualDefault\": {\"eyes\": \"open\", \"seizure\": False, \"work_of_breathing\": \"normal\"},\n"
 "}\n"
 "\nDX_IDS = {d[\"id\"] for d in shared[\"diagnoses\"]}"),
("    bundle = (\"/*__ENGINE_START__*/\\n\" + open(os.path.join(HERE, \"engine.js\")).read() +\n"
 "              \"\\n/*__ENGINE_END__*/\\n\"\n",
 "    # The patient figure. patient-art.json is derived from the avataaars library by\n"
 "    # engine/assets/avataaars/extract.js and is injected as a constant ahead of patient.js,\n"
 "    # inside the same fence, so the harness can evaluate the pair without the page. The MIT\n"
 "    # licence requires its notice to travel with the artwork, so the licence text goes into\n"
 "    # every file the artwork goes into. patient.js depends on nothing else in the bundle\n"
 "    # and ui.js calls it from the frame loop, so the only ordering rule is: before ui.js.\n"
 "    # Optional in the same way the ambience is: without the art file PATIENT.available is\n"
 "    # false, the stage stays empty and nothing else changes.\n"
 "    art_path = os.path.join(HERE, \"patient-art.json\")\n"
 "    art = json.load(open(art_path)) if os.path.exists(art_path) else None\n"
 "    notice = (\"Patient artwork: avataaars, https://github.com/fangpenlin/avataaars\\n\" +\n"
 "              open(os.path.join(HERE, \"assets\", \"avataaars\", \"LICENSE\")).read()).replace(\"*/\", \"* /\")\n"
 "    patient_js = open(os.path.join(HERE, \"patient.js\")).read()\n"
 "    patient_block = (\"/*\\n\" + notice + \"\\n*/\\nconst PATIENT_ART=\" + jsafe(art) + \";\\n\" + patient_js)\n"
 "    lab_src = os.path.join(HERE, \"patient-lab.html\")\n"
 "    if art and os.path.exists(lab_src):\n"
 "        lab = open(lab_src).read()\n"
 "        lab = lab.replace(\"__PATIENT_NOTICE__\", notice.replace(\"--\", \"- -\"))\n"
 "        lab = lab.replace(\"__PATIENT_ART__\", jsafe(art)).replace(\"__PATIENT_JS__\", patient_js)\n"
 "        os.makedirs(BUILD_DIR, exist_ok=True)\n"
 "        open(os.path.join(BUILD_DIR, \"patient-lab.html\"), \"w\").write(lab)\n"
 "    bundle = (\"/*__ENGINE_START__*/\\n\" + open(os.path.join(HERE, \"engine.js\")).read() +\n"
 "              \"\\n/*__ENGINE_END__*/\\n\"\n"
 "              \"/*__PATIENT_START__*/\\n\" + patient_block +\n"
 "              \"\\n/*__PATIENT_END__*/\\n\"\n"),
])
print("done")
