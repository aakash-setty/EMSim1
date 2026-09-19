#!/usr/bin/env python3
"""One-shot: evaluate the PATIENT fence in engine-tests.js and assert what it claims."""
import os, sys
p = os.path.join(sys.argv[1], "engine", "engine-tests.js"); s = open(p).read()
a1 = "/* audio.js is fenced separately in the bundle."
a2 = "/* ================= case pack assertions ================= */"
assert s.count(a1) == 1 and s.count(a2) == 1
s = s.replace(a1, """/* patient.js is fenced with its artwork constant. Inert in node: it touches the document
   only when a figure is mounted, and its matchMedia probe is inside a try. Evaluated here
   because its vocabulary is restated in two other places and nothing else can notice the
   three drifting apart. */
const pat = html.match(/\\/\\*__PATIENT_START__\\*\\/([\\s\\S]*?)\\/\\*__PATIENT_END__\\*\\//);
if (pat) global.PATIENT = eval(pat[1] + '\\n;PATIENT');

""" + a1)
s = s.replace(a2, """section('the patient in the room');
if (typeof PATIENT === 'undefined') chk('patient block is fenced in the build', false);
else {
  const voc = PATIENT.vocabulary(), sp = SHARED.patient || {};
  const same = (x, y) => JSON.stringify([...x].sort()) === JSON.stringify([...y].sort());
  chk('the artwork is in the build', PATIENT.available);
  chk('every avataaars option survived extraction',
      voc.parts.topType.length === 35 && voc.parts.accessoriesType.length === 7 &&
      voc.parts.facialHairType.length === 6 && voc.parts.clotheType.length === 10 &&
      voc.parts.graphicType.length === 11 && voc.parts.eyeType.length === 12 &&
      voc.parts.eyebrowType.length === 13 && voc.parts.mouthType.length === 12,
      JSON.stringify(Object.keys(voc.parts).map(k => k + ':' + voc.parts[k].length)));
  chk('registered add-ons are exactly the shared vocabulary', same(voc.addons, sp.addons || []),
      voc.addons + ' vs ' + sp.addons);
  const vsrc = fs.readFileSync(path.join(ROOT, 'engine', 'validate_case.py'), 'utf8');
  const vm = vsrc.match(/PATIENT_ADDONS = \\{([^}]*)\\}/);
  chk('the validator restates the same add-ons',
      !!vm && same(vm[1].split(',').map(x => x.trim().replace(/"/g, '')).filter(Boolean), sp.addons || []));
  chk('eyes and work of breathing vocabularies agree', same(voc.eyes, sp.eyes) && same(voc.work_of_breathing, sp.work_of_breathing));
  for (const sex of Object.keys(sp.base || {})) {
    const r = PATIENT.normalizeAppearance(sp.base[sex]);
    chk('the standard ' + sex + ' patient is drawn from real options', r.problems.length === 0, r.problems.join('; '));
  }
  PATIENT.setBases(sp.base);
  const m = PATIENT.baseFor('male'), f = PATIENT.baseFor('female');
  chk('the two standard patients differ only in the hair',
      Object.keys(m).filter(k => m[k] !== f[k]).join() === 'topType');
  chk('a case avatar overrides the base key by key and notes are dropped',
      PATIENT.baseFor('female', { skinColor: 'Pale', authoring_note: 'x' }).skinColor === 'Pale' &&
      PATIENT.baseFor('female', { authoring_note: 'x' }).authoring_note === undefined);
  chk('an unknown value is reported and falls back', PATIENT.normalizeState({ eyes: 'shut', addons: ['nope'] }).problems.length === 2);
  chk('breathing is 0 at end-expiration and 1 at end-inspiration',
      PATIENT._breathCurve(0, 16) === 0 && Math.abs(PATIENT._breathCurve(0.38, 16) - 1) < 1e-9);
  for (let i = 0; i < CASES.length; i++) {
    bind(i);
    const rules = (CASE.content_keys.patient_visual || {}).rules;
    const start = patientVisual(fold(mk([]), 1));
    chk(PACK.prefix + ': the figure resolves at arrival', !!start.value && start.source === (rules ? 'case' : 'default'));
    const bad = (rules || []).map(r => PATIENT.normalizeState(r.value).problems).flat();
    chk(PACK.prefix + ': every authored visual state is drawable', bad.length === 0, bad.join('; '));
    const av = PATIENT.normalizeAppearance(PATIENT.baseFor((CASE.patient || {}).sex, (CASE.patient || {}).avatar));
    chk(PACK.prefix + ': the appearance is drawable', av.problems.length === 0, av.problems.join('; '));
  }
  bind(packIdx);
}

""" + a2)
open(p, "w").write(s); print("patched engine-tests.js")
