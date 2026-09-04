/* Engine test harness. Case-agnostic.
 *
 * Loads a built prototype, evaluates the engine block out of it, runs the checks
 * that hold for any case, then runs the case pack's own assertions.
 *
 *   node engine/engine-tests.js [build/simulator.html] [cases/CHFE/CHFE-tests.js] [CHFE]
 *
 * With no arguments it discovers a single build and a single case test file.
 */
const fs = require('fs');
const path = require('path');
const ROOT = path.dirname(__dirname);

function findSimulator(arg) {
  if (arg && fs.existsSync(arg)) return arg;
  const p = path.join(ROOT, 'build', 'simulator.html');
  if (fs.existsSync(p)) return p;
  console.error('no build/simulator.html; run engine/build_simulator.py first');
  process.exit(2);
}
function findCaseTests(arg) {
  if (arg && fs.existsSync(arg)) return arg;
  const dir = path.join(ROOT, 'cases');
  if (!fs.existsSync(dir)) return null;
  for (const pack of fs.readdirSync(dir)) {
    const p = path.join(dir, pack);
    if (!fs.statSync(p).isDirectory()) continue;
    const hit = fs.readdirSync(p).find(f => f.endsWith('-tests.js'));
    if (hit) return path.join(p, hit);
  }
  return null;
}

const HTML_PATH = findSimulator(process.argv[2]);
const html = fs.readFileSync(HTML_PATH, 'utf8');

function grab(id) {
  const m = html.match(new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>'));
  if (!m) { console.error('no ' + id + ' block in ' + HTML_PATH); process.exit(2); }
  return JSON.parse(m[1]);
}
global.SHARED = grab('shared-data');
global.CASES = grab('cases-data');
global.window = {};
global.document = { querySelector: () => ({ offsetHeight: 0 }) };
/* ui.js declares ST and is not loaded here. Declaring it null rather than leaving it
   undefined is the honest state for a harness with no run in progress, and it keeps the
   audio module's guards on a value rather than on a missing identifier. */
global.ST = null;

const eng = html.match(/\/\*__ENGINE_START__\*\/([\s\S]*?)\/\*__ENGINE_END__\*\//);
if (!eng) { console.error('engine block not found in ' + HTML_PATH); process.exit(2); }
eval(eng[1]);

/* audio.js is fenced separately in the bundle. It is evaluated here because the
   heartbeat's interval model is a claim about physiology rather than a rendering
   detail, and a claim that nothing can check is a claim nobody should trust. Nothing
   in it touches an AudioContext until a gesture creates one, so it is inert in node. */
const aud = html.match(/\/\*__AUDIO_START__\*\/([\s\S]*?)\/\*__AUDIO_END__\*\//);
/* audio.js binds its module with `const AUDIO = ...`, and a const declared inside a
   direct eval does not leak into the calling scope the way engine.js's function
   declarations do. The trailing expression hands the binding back explicitly rather
   than leaving the harness to discover that AUDIO is undefined and report it as a
   missing fence, which is what happened the first time this was written. */
if (aud) global.AUDIO = eval(aud[1] + '\n;AUDIO');

/* Bind the case under test. With one pack it is chosen automatically. */
const WANT = process.argv[4] || null;
const packIdx = WANT ? CASES.findIndex(c => c.prefix === WANT || c.id === WANT) : 0;
if (packIdx < 0) { console.error('no such case: ' + WANT); process.exit(2); }
function bind(i) {
  selectCase(i);
  const st = engineState();
  for (const k of ['CASE', 'PROTO', 'PACK', 'PHASE', 'ACT', 'FU', 'CK', 'CONTENT']) global[k] = st[k];
  /* A is rebound here rather than captured once. selectCase builds a NEW actions object
     on every call, and the "every packed case binds" section below binds each pack in
     turn, so a reference taken at the top of this file points at the first pack's map
     for the rest of the run. Everything read off it happened to be identical across
     packs, so nothing failed and the staleness was invisible until a test tried to WRITE
     to it. Live binding rather than a stale copy. */
  global.A = st.ACT;
  return st;
}
bind(packIdx);

/* ---------- harness, exposed to the case assertions ---------- */
let fails = 0, count = 0;
global.chk = (name, cond, extra) => {
  count++;
  if (cond) console.log('  ok   ' + name);
  else { console.log('  FAIL ' + name + (extra ? '  ' + extra : '')); fails++; }
};
global.section = name => console.log('\n-- ' + name + ' --');
global.mk = steps => steps.map((s, i) =>
  Array.isArray(s) ? { seq: i, t: s[0], actionId: s[1] } : Object.assign({ seq: i }, s));

/* ids discovered from the loaded data, never hard-coded. A is set by bind(), above. */
const idsWhere = f => Object.keys(A).filter(id => f(A[id]));
global.EXAMS = idsWhere(a => a.category === 'exam');
global.STUDIES = idsWhere(a => a.category === 'investigation');
global.AUTHORED_STUDIES = STUDIES.filter(id =>
  CASE.content_keys.labs[id] || CASE.content_keys.imaging[id]);
global.UNAUTHORED_STUDIES = STUDIES.filter(id =>
  !AUTHORED_STUDIES.includes(id) && A[id].default_result);
global.CONSULTS = idsWhere(a => a.category === 'consultant');
global.HARMFUL = idsWhere(a => (a.tag || []).some(r => r.value === 'harmful'));
global.CRITICAL = idsWhere(a => (a.tag || []).some(r => r.value === 'critical'));
global.START_PHASE = CASE.phases[0].id;

console.log('simulator:  ' + path.relative(ROOT, HTML_PATH));
console.log('cases in build: ' + CASES.map(c => c.prefix).join(', '));
console.log('case under test: ' + PACK.prefix + '  (' + CASE.case_id + ')');
console.log('actions:    ' + Object.keys(A).length +
            '  (exams ' + EXAMS.length + ', studies ' + STUDIES.length +
            ', consults ' + CONSULTS.length + ')');

/* ================= case-agnostic checks ================= */

section('every packed case binds');
for (let i = 0; i < CASES.length; i++) {
  const p = CASES[i];
  let ok = true, why = '';
  try {
    bind(i);
    if (!Object.keys(ACT).length) { ok = false; why = 'no actions'; }
    if (!PROTO.correctDxId) { ok = false; why = 'correct diagnosis does not resolve'; }
    if (!CK.general_status) { ok = false; why = 'no general_status key'; }
  } catch (e) { ok = false; why = e.message; }
  chk('case ' + p.prefix + ' selects and binds', ok, why);
  chk('case ' + p.prefix + ' reports no build notes', (p.buildNotes || []).length === 0,
      (p.buildNotes || []).join('; '));
}
bind(packIdx);

section('condition language');
const s0 = { phase: START_PHASE, flags: new Set(['a']), ordered: new Set(['x']),
             resulted: new Set(), taken: new Set(['e']) };
chk('phase is', test('phase is ' + START_PHASE, s0));
chk('flag set', test('flag a set', s0));
chk('NOT', !test('NOT flag a set', s0));
chk('AND with one level of grouping', test('flag a set AND (study x ordered OR study x resulted)', s0));
chk('ordered is not resulted', test('study x ordered', s0) && !test('study x resulted', s0));
chk('action taken', test('action e taken', s0));
let threw = false; try { parseCond('elapsed > 30'); } catch (e) { threw = true; }
chk('rejects a time predicate', threw);

section('every condition in the case parses');
const bad = [];
(function walk(o) {
  if (Array.isArray(o)) return o.forEach(walk);
  if (o && typeof o === 'object') for (const k in o) {
    if ((k === 'when' || k === 'guard' || k === 'applies_when') && typeof o[k] === 'string') {
      try { parseCond(o[k]); } catch (e) { bad.push(o[k]); }
    } else walk(o[k]);
  }
})(CASE);
chk('all case conditions parse', bad.length === 0, bad.slice(0, 3).join(' | '));

section('reads never change state');
const readRun = fold(mk(EXAMS.map((id, i) => [i + 1, id])), EXAMS.length + 5);
const idleRun = fold(mk([]), EXAMS.length + 5);
chk('every exam leaves phase and flags untouched',
    readRun.phase === idleRun.phase && readRun.flags.size === 0);
chk('every exam returns a finding', readRun.readouts.length === EXAMS.length);

section('exam set and general status');
chk('case authors no exam outside the catalog set',
    Object.keys(CASE.content_keys.exam).filter(k => k !== 'authoring_note')
      .every(k => EXAMS.includes(k)));
chk('every exam payload is exam_findings with an abnormal flag',
    readRun.readouts.every(r => r.body && r.body.kind === 'exam_findings' && 'abnormal' in r.body));
const gs = generalStatus(fold(mk([]), 1));
chk('general status resolves', !!(gs.value && gs.value.findings));
chk('general status is authored by the case', gs.source === 'case');

section('structured results and abnormal flags');
let payloadOk = true, orOk = true;
for (const id of AUTHORED_STUDIES) {
  const key = CASE.content_keys.labs[id] || CASE.content_keys.imaging[id];
  for (const r of key.rules) {
    const v = r.value;
    if (!v || typeof v !== 'object' || !('abnormal' in v)) { payloadOk = false; continue; }
    if (v.components) {
      if (v.abnormal !== v.components.some(c => c.abnormal)) orOk = false;
      if (!v.components.every(c => c.label && c.value !== undefined && 'abnormal' in c)) payloadOk = false;
    }
  }
}
chk('every authored result is a structured payload', payloadOk);
chk('payload abnormal equals the OR of its components', orOk);

section('catalog defaults');
const un = UNAUTHORED_STUDIES[0];
if (un) {
  const st = fold(mk([[1, un]]), 60);
  chk('an unauthored study returns the catalog default',
      st.orders[un] && st.orders[un][0].source === 'catalog_default', un);
  chk('the default is normal', st.orders[un][0].value.abnormal === false);
  chk('the default is recorded for the debrief', st.defaultsServed.has(un));
} else chk('an unauthored study exists to test', false);
const unboundConsult = CONSULTS.find(id => !A[id].bound);
chk('an unbound consultant gets the global response',
    !unboundConsult || /not sure why/.test(fold(mk([[1, unboundConsult]]), 5).readouts[0].body));

section('result timing and freezing');
const anyStudy = AUTHORED_STUDIES.find(id => turnaround(id) > 0) || AUTHORED_STUDIES[0];
chk('pending before the due time',
    turnaround(anyStudy) === 0 || fold(mk([[1, anyStudy]]), 1.5).orders[anyStudy][0].value === null);
chk('resulted after the due time',
    fold(mk([[1, anyStudy]]), turnaround(anyStudy) + 5).resulted.has(anyStudy));
chk('a repeat order creates a second result',
    fold(mk([[1, anyStudy], [20, anyStudy]]), 40).orders[anyStudy].length === 2);
const il = fold(mk([[2, anyStudy], [3, anyStudy]]), 40);
chk('two orders keep distinct order times',
    il.orders[anyStudy][0].orderT !== il.orders[anyStudy][1].orderT);

section('halting');
if (HARMFUL.length) {
  /* Walking to the state in which each harmful action is harmful needs case knowledge,
     so that lives in the case assertions. What is checkable generically is that the
     harmful tag is reachable at all: some authored phase must resolve it to harmful.
     A harmful rule no phase can satisfy is a rule that will never fire. */
  const unreachable = [], noReason = [];
  for (const h of HARMFUL) {
    const hit = CASE.phases.some(ph => tagOf(h, {
      phase: ph.id, flags: new Set(), ordered: new Set(),
      resulted: new Set(), taken: new Set()
    }) === 'harmful');
    if (!hit) unreachable.push(h);
    const r = A[h].halt_reason;
    if (!r || r.length < 20) noReason.push(h);
  }
  chk('every harmful tag is reachable from some phase', unreachable.length === 0, unreachable.join(', '));
  chk('every harmful action carries a halt reason', noReason.length === 0, noReason.join(', '));

  /* And that halting actually stops the fold, using whichever harmful action is
     harmful in the starting phase. */
  const atStart = HARMFUL.find(h => tagOf(h, {
    phase: START_PHASE, flags: new Set(), ordered: new Set(),
    resulted: new Set(), taken: new Set()
  }) === 'harmful' && !(A[h].prerequisites || []).length);
  if (atStart) {
    const st = fold(mk([[1, atStart], [2, EXAMS[0]]]), 20);
    chk('a harmful action halts the case', st.halted && st.halted.id === atStart && st.phase === 'halted');
    chk('nothing after a halt is applied', !st.taken.has(EXAMS[0]));
  } else {
    chk('a harmful action with no prerequisites exists to test', true);
  }
} else chk('a harmful action exists to test', false);

section('catalog action surface');
chk('the whole catalog is rendered', Object.keys(A).length >= 200, String(Object.keys(A).length));
chk('every action has a tab', Object.values(A).every(a => a.tab));
chk('every orderable tab is a real tab',
    PROTO.orderableTabs.every(t => PROTO.tabOrder.includes(t)));
chk('every collapsible tab is a real tab',
    (PROTO.collapsibleTabs || []).every(t => PROTO.tabOrder.includes(t)));

section('tab presentation');
{
  const groupsOf = tab => {
    const g = {};
    Object.keys(A).forEach(id => { if (A[id].tab === tab) (g[A[id].group] = g[A[id].group] || []).push(id); });
    return g;
  };
  for (const tab of PROTO.collapsibleTabs) {
    const n = Object.keys(groupsOf(tab)).length;
    chk('collapsible tab ' + tab + ' has more than one group', n > 1, String(n));
  }
  /* A single-group tab gains nothing from an accordion and loses a click, so the
     configuration should not creep onto one. */
  const flat = PROTO.tabOrder.filter(t => !PROTO.collapsibleTabs.includes(t));
  const wrongly = flat.filter(t => Object.keys(groupsOf(t)).length > 3);
  chk('no many-grouped tab is left flat', wrongly.length === 0, wrongly.join(', '));

  /* A group named as opening by default has to exist on that tab and that tab has to
     be collapsible, or the setting is silently doing nothing. */
  const de = PROTO.defaultExpanded || {};
  for (const tab of Object.keys(de)) {
    chk('default-expanded tab ' + tab + ' is collapsible', PROTO.collapsibleTabs.includes(tab));
    const have = Object.keys(groupsOf(tab));
    const ghost = de[tab].filter(g => !have.includes(g));
    chk('every default-expanded group on ' + tab + ' exists', ghost.length === 0, ghost.join(', '));
  }
  /* Ordered groups likewise: a name in groupOrder that no entry uses is a rename that
     was made in the catalog and not here, and it silently loses its position. */
  for (const tab of Object.keys(PROTO.groupOrder || {})) {
    const have = Object.keys(groupsOf(tab));
    const ghost = PROTO.groupOrder[tab].filter(g => !have.includes(g));
    chk('every ordered group on ' + tab + ' exists', ghost.length === 0, ghost.join(', '));
  }
}

section('difficulty modes');
const D = PROTO.difficulty;
chk('two modes are defined', Object.keys(D.modes).length === 2, Object.keys(D.modes).join(','));
chk('easy leaves prompt deadlines alone', D.modes.easy.prompt_multiplier === 1);
chk('hard triples them', D.modes.hard.prompt_multiplier === 3);
const promptAction = CRITICAL.find(id => A[id].prompt);
if (promptAction) {
  const d = A[promptAction].prompt.deadline_seconds;
  chk('a prompt that has fired in easy mode has not fired in hard mode',
      fold(mk([]), d + 2, 1).promptFires.some(p => p.id === promptAction) &&
      !fold(mk([]), d + 2, 3).promptFires.some(p => p.id === promptAction),
      promptAction + ' at ' + d + 's');
  chk('the same prompt fires in hard mode at three times the deadline',
      fold(mk([]), d * 3 + 2, 3).promptFires.some(p => p.id === promptAction));
  /* Until v0.6 this asserted the phase was still START_PHASE after 300 seconds of
     doing nothing, because no case could change on its own. A case may now author
     time-guarded transitions, so the invariant that actually matters is that the two
     modes produce the SAME trajectory: prompt deadlines are scaled, deterioration
     deadlines are not, so the medicine is identical and only the help differs.
     Design 17.1. */
  const easyEnd = fold(mk([]), 300, 1), hardEnd = fold(mk([]), 300, 3);
  chk('mode changes only the prompts, not the phase',
      easyEnd.phase === hardEnd.phase, easyEnd.phase + ' vs ' + hardEnd.phase);
  chk('mode does not change the trajectory',
      JSON.stringify(easyEnd.phaseSeq) === JSON.stringify(hardEnd.phaseSeq),
      JSON.stringify(easyEnd.phaseSeq.map(p => p.id + '@' + p.t)));
} else chk('a prompted critical action exists to test', false);

section('time-guarded transitions');
{
  const timed = [];
  for (const p of CASE.phases)
    (p.transitions || []).forEach((t, i) => {
      if (t.after_seconds !== undefined) timed.push([p.id, i, t]);
    });
  if (!timed.length) {
    chk('case authors no time-guarded transitions, nothing to test', true);
  } else {
    chk('every time-guarded rule carries narration, a note and a rationale',
        timed.every(([, , t]) => t.narration && t.debrief_note && t.author_rationale));
    chk('a time-driven ending never reuses the shared halted phase',
        timed.every(([, , t]) => t.to !== 'halted'));
    /* The mechanism has to actually run, not merely be authored. */
    const longest = Math.max(...timed.map(([, , t]) => t.after_seconds));
    const idle = fold(mk([]), longest * timed.length + 60, 1);
    chk('doing nothing eventually changes the phase',
        idle.phase !== START_PHASE, idle.phase);
    chk('each deterioration is recorded for the debrief',
        idle.timeFires.length > 0 &&
        idle.timeFires.every(f => f.after > 0 && typeof f.from === 'string'),
        JSON.stringify(idle.timeFires.map(f => f.from + '->' + f.to)));
    /* The one place a nurse line may describe a trajectory is a deterioration, and it
       must not arrive on the prompt channel, or the no-trajectory rule below is
       silently weakened. */
    chk('deterioration narration is on its own channel',
        idle.nurse.filter(n => n.kind === 'deterioration').length === idle.timeFires.length);
    /* The fairness rule the validator enforces on authored deadlines, checked here
       against what actually fires: the prompt cap can suppress a prompt the validator
       thought would be seen. */
    const guarded = timed.filter(([, , t]) => /NOT\s+flag/.test(t.when || ''));
    const unwarned = [];
    for (const [phase, , t] of guarded) {
      const flags = [...(t.when.match(/flag ([a-z0-9_]+) set/g) || [])]
        .map(x => x.replace('flag ', '').replace(' set', ''));
      for (const f of flags) {
        const setters = Object.keys(A).filter(id => (A[id].flags_set || []).includes(f));
        const fired = idle.promptFires.some(p => setters.includes(p.id) &&
                                                 p.t < (idle.phaseEntry[phase] || 0) + t.after_seconds);
        if (!fired) unwarned.push(phase + ' deteriorates on ' + f + ' with no prompt seen');
      }
    }
    chk('every deterioration is preceded by a prompt that actually fires',
        unwarned.length === 0, unwarned.join('; '));
  }
}

const ST_SAMPLE = fold(mk([[1, AUTHORED_STUDIES[0]]]), 40);

section('equivalence group coverage');
{
  const covered = Object.keys(PACK.covers || {});
  chk('covered entries keep their own catalog name',
      covered.every(id => ACT[id] && ACT[id].name && ACT[id].covered_by),
      covered.join(', '));
  /* A harmful tag claimed through a group must halt on every member, or the group
     has created escapes rather than closing them. */
  const byCase = {};
  covered.forEach(id => (byCase[PACK.covers[id]] = byCase[PACK.covers[id]] || []).push(id));
  let allHalt = true, why = '';
  /* The vascular-access action is discovered from the loaded pack rather than named.
     It used to be hard-coded to the reference case's id, so in any other pack the line
     was never inserted, every intravenous member was blocked by its prerequisite
     instead of halting, and the assertion failed for a reason that had nothing to do
     with the group. A case name in the case-agnostic suite is a defect on its own. */
  const ivAct = Object.keys(ACT)
    .find(id => (ACT[id].flags_set || []).includes('iv_access'));
  for (const caseId in byCase) {
    const members = byCase[caseId].concat([
      Object.keys(PACK.bindings).find(c => PACK.bindings[c] === caseId) ? caseId : null
    ].filter(Boolean));
    for (const m of members) {
      if (tagOf(m, { phase: START_PHASE, flags: new Set(['iv_access']), ordered: new Set(),
                     resulted: new Set(), taken: new Set() }) !== 'harmful') continue;
      const st = fold(mk(ivAct ? [[1, ivAct], [5, m]] : [[5, m]]), 20);
      if (!st.halted || st.halted.id !== m) { allHalt = false; why = m; }
    }
  }
  chk('every member of a harmful group halts the case', allHalt, why);
}

section('stop actions');
{
  const stops = Object.keys(ACT).filter(id => SHARED.actionsBase[ACT[id].catalog_id] &&
    (ACT[id].catalog_id || '').indexOf('stop_') === 0);
  chk('the catalog supplies stop actions for persistent infusions', stops.length > 0,
      String(stops.length));
  const persistent = Object.keys(SHARED.actionsBase)
    .filter(id => SHARED.actionsBase[id].persistent);
  const missing = persistent.filter(id =>
    !Object.keys(SHARED.actionsBase).some(s => SHARED.actionsBase[s].stops === id));
  chk('every persistent infusion has a stop action', missing.length === 0, missing.join(', '));
}

section('interview readouts');
{
  /* The chart shows what was learned about the patient. An unmatched question is
     answered by the case's fallback, and the readout records that by leaving `matched`
     null, which is what the interface filters on. If a matched answer ever came back
     with a null topic the filter would swallow real history. */
  const topic = CASE.interview.topics[0].topic;
  const asked = fold(mk([{ t: 1, kind: 'interview', topic, q: CASE.interview.topics[0].canonical },
                          { t: 2, kind: 'interview', topic: null, q: 'zzzz' }]), 10);
  const sp = asked.readouts.filter(r => r.kind === 'speech');
  chk('both questions produced a readout', sp.length === 2, String(sp.length));
  chk('a matched question records its topic', sp[0].matched === topic, String(sp[0].matched));
  chk('an unmatched question records no topic', sp[1].matched === null, String(sp[1].matched));
  chk('the unmatched answer is the case fallback',
      sp[1].body === resolve((CASE.interview.global_answer_rules || [])
                             .concat(CASE.interview.out_of_scope_fallback), asked));
  /* The filter itself lives in ui.js, outside the engine block this harness evaluates,
     so it is asserted against the built file rather than executed. */
  chk('the chart feed filters on matched',
      /r\.kind===\'speech\'&&r\.matched/.test(html.replace(/\s+/g, '')),
      'ui.js feedItems');
}

section('monitor gating');
{
  /* Case-agnostic: whichever action carries reveals_vitals, and there must be exactly
     one route to it or a resident can be shown vitals by an act that is not attaching
     a monitor. */
  const revealers = Object.keys(A).filter(id => A[id].reveals_vitals);
  chk('exactly one action reveals the vitals', revealers.length === 1, revealers.join(', '));
  const rid = revealers[0];
  chk('nothing is monitored before it is taken', fold(mk([]), 60).monitoring === null);
  if (rid) {
    const on = fold(mk([[2, rid]]), 60);
    chk('taking it starts the monitoring', !!on.monitoring && on.monitoring.id === rid);
    chk('the monitoring records when it started', on.monitoring.t === 2);
    /* Monitoring is a fact about the resident's equipment, not about the patient, so
       nothing a case authors may switch it back off. */
    chk('monitoring never turns off again',
        !!fold(mk([[2, rid], [4, EXAMS[0]]]), 300).monitoring);
  }
  chk('vitals are derived whether or not anyone is watching',
      !!fold(mk([]), 30).vitals, 'the fold computes them; the interface hides them');
}

section('vital effects');
{
  const START = CASE.phases[0].id;
  const base = PHASE[START].vitals;
  const withFx = Object.keys(A).filter(id => (A[id].vital_effects || []).length);
  chk('no effect is active before anything is done', fold(mk([]), 30).vitalEffects.length === 0);
  chk('with no effect the vitals are the phase baseline verbatim',
      JSON.stringify(fold(mk([]), 30).vitals) === JSON.stringify(base));
  if (!withFx.length) {
    chk('this case authors no vital effects, so there is nothing further to check', true);
  } else {
    /* Pick an effect whose action is takeable at t=0 in the start phase with no
       prerequisites, so the assertion is about the effect and not about the block. */
    const id = withFx.find(x => !(A[x].prerequisites || []).length) || withFx[0];
    const fx = A[id].vital_effects[0];
    const pre = (A[id].prerequisites || []).length;
    if (!pre) {
      const st = fold(mk([[1, id]]), 3);
      const moved = st.vitals[fx.vital] - PHASE[st.phase].vitals[fx.vital];
      chk('an effect moves its vital off the phase baseline', moved !== 0,
          id + ' ' + fx.vital + ' ' + moved);
      /* Repeat dosing refreshes rather than stacks: two administrations sharing a key
         must not double the delta. */
      const twice = fold(mk([[1, id], [2, id]]), 3);
      chk('the same action twice does not stack',
          twice.vitals[fx.vital] === fold(mk([[2, id]]), 3).vitals[fx.vital]);
      chk('effects sharing a key collapse to one',
          twice.vitalEffects.filter(e => e.key === (fx.key || id)).length === 1);
      if (fx.duration_seconds) {
        const during = fold(mk([[1, id]]), 1 + fx.duration_seconds - 1);
        const after  = fold(mk([[1, id]]), 1 + fx.duration_seconds + 1);
        chk('a timed effect is acting inside its window',
            during.vitalEffects.some(e => e.key === (fx.key || id)));
        chk('a timed effect has lapsed after it',
            !after.vitalEffects.some(e => e.key === (fx.key || id)));
        chk('the vital returns to baseline when it lapses',
            after.vitals[fx.vital] === PHASE[after.phase].vitals[fx.vital]);
      }
    } else {
      chk('every effect-bearing action in this case has a prerequisite, checked in the pack', true);
    }
    /* The whole point of separating effects from phases is that they are display and
       audio only. Nothing about them may reach the condition language. */
    chk('vitals do not enter the condition language',
        !/case 'vital'/.test(String(evalCond)));
  }
  /* Terminal phases author the numbers a reader is left looking at. */
  const term = CASE.phases.filter(p => p.terminal).map(p => p.id);
  chk('every case has at least one terminal phase', term.length > 0, term.join(', '));
}

section('the running chart');
{
  /* feedItems lives in ui.js, outside the engine block this harness evaluates, so the
     ordering and the filter are asserted against the built file. What IS asserted against
     the engine is the vocabulary they depend on: the chart selects nurse utterances by
     kind, so renaming a kind in the fold would empty the chart of prompts without any
     test failing. These two halves have to be checked together or neither is worth much. */
  const flat = html.replace(/\s+/g, '');
  chk('the chart sorts newest first', /out\.sort\(\(a,b\)=>b\.t-a\.t\|\|b\.seq-a\.seq\)/.test(flat));
  chk('the chart follows the newest entry to the top, not the bottom',
      /if\(f\)f\.scrollTop=0;/.test(flat));
  chk('the chart selects nurse lines by kind',
      /constNURSE_IN_CHART=\{prompt:1,deterioration:1\}/.test(flat));

  /* The kinds the fold actually emits. A prompt is the one the chart exists for. */
  const promptAction = CRITICAL.find(id => A[id].prompt);
  if (promptAction) {
    const d = A[promptAction].prompt.deadline_seconds;
    const st = fold(mk([]), d + 2, 1);
    const kinds = new Set(st.nurse.map(n => n.kind));
    chk('the fold emits a nurse line of kind "prompt"', kinds.has('prompt'),
        [...kinds].join(', '));
  }
  {
    /* And of kind "deterioration", where the case has a timed transition that narrates.
       Emitted on its own kind so the no-trajectory assertion on prompts stays valid. */
    const timed = CASE.phases.some(p => (p.transitions || [])
      .some(t => t.after_seconds !== undefined && t.narration));
    if (timed) {
      const long = fold(mk([]), 4000, 1);
      chk('the fold emits a nurse line of kind "deterioration"',
          long.nurse.some(n => n.kind === 'deterioration'));
    } else {
      chk('this case authors no narrated timed transition, so that kind is not exercised here',
          true);
    }
  }
  /* A blocked attempt has to carry its message where the chart can reach it, since the
     chart now renders the reason rather than only the fact. */
  {
    /* A prerequisite that HOLDS at the start blocks nothing, so search for one that
       actually blocks rather than for one that merely exists. CHFE's first gated action
       is guarded on NOT being intubated, which is true on arrival. */
    const gated = Object.keys(A).find(id => (A[id].prerequisites || []).length &&
                                            A[id].category !== 'exam' &&
                                            fold(mk([[1, id]]), 10).blocked.length === 1);
    if (gated) {
      const st = fold(mk([[1, gated]]), 10);
      chk('a blocked attempt records a message the chart can render',
          !!st.blocked[0].message && st.blocked[0].t === 1 && st.blocked[0].id === gated,
          gated);
    } else {
      chk('no action in this case blocks from the arrival state', true);
    }
  }
}

section('expiring flags and delayed onset');
{
  /* Neither case authors these yet, and a mechanic no case uses is a mechanic nobody has
     run. So the harness authors one: a synthetic action and a synthetic transition are
     installed on the loaded case, exercised, and removed. Nothing is written to a case
     file and the assertions below this block see the case exactly as it was. */
  const START = CASE.phases[0].id;
  const P = PHASE[START];
  const savedTransitions = P.transitions ? P.transitions.slice() : [];
  const target = CASE.phases.find(p => p.id !== START && !p.terminal);
  /* Heart rate rather than saturation. Saturation is bounded at 100 and MGCA arrives at
     98, so a +4 probe clamped and the assertion failed for the right reason on the wrong
     case. Heart rate has 280 points of headroom above any authored value, so the probe
     measures the mechanism rather than the bound. The bound gets its own check below. */
  const VIT = 'heart_rate';
  const baseline = P.vitals ? P.vitals[VIT] : null;

  A.__probe_drug = {
    id: '__probe_drug', name: 'Probe drug', tab: 'interventions', group: 'Probe',
    category: 'medication', state_changing: true, repeatable: true, prerequisites: [],
    flags_set: [], flags_set_timed: [{ flag: '__probe_acting', duration_seconds: 30 }],
    vital_effects: [{ vital: VIT, delta: 4, key: '__probe_fx',
                      while: 'flag __probe_acting set' }]
  };
  A.__probe_slow = {
    id: '__probe_slow', name: 'Probe slow drug', tab: 'interventions', group: 'Probe',
    category: 'medication', state_changing: true, repeatable: true, prerequisites: [],
    flags_set: [], flags_set_timed: [],
    vital_effects: [{ vital: VIT, delta: 6, key: '__probe_slow_fx',
                      onset_seconds: 20, duration_seconds: 60 }]
  };
  A.__probe_perm = {
    id: '__probe_perm', name: 'Probe permanent', tab: 'interventions', group: 'Probe',
    category: 'medication', state_changing: true, repeatable: true, prerequisites: [],
    flags_set: ['__probe_acting'], flags_set_timed: []
  };

  /* --- the flag itself --- */
  chk('a timed flag is set when the action is taken',
      fold(mk([[1, '__probe_drug']]), 5).flags.has('__probe_acting'));
  chk('it is still set one second before it lapses',
      fold(mk([[1, '__probe_drug']]), 30).flags.has('__probe_acting'));
  chk('it is gone one second after',
      !fold(mk([[1, '__probe_drug']]), 33).flags.has('__probe_acting'));
  chk('the lapse is recorded with its time',
      (() => { const e = fold(mk([[1, '__probe_drug']]), 40).flagExpiries;
               return e.length === 1 && e[0].flag === '__probe_acting' && e[0].t === 31; })());

  /* --- a repeat dose refreshes rather than shortening --- */
  {
    const twice = fold(mk([[1, '__probe_drug'], [20, '__probe_drug']]), 40);
    chk('a repeat dose extends the flag past the first expiry',
        twice.flags.has('__probe_acting'), 'still set at 40s');
    chk('the first expiry does not fire while a later grant stands',
        twice.flagExpiries.length === 0);
    chk('and it lapses at the later deadline',
        !fold(mk([[1, '__probe_drug'], [20, '__probe_drug']]), 55).flags.has('__probe_acting'));
  }

  /* --- a permanent grant absorbs a timed one, in either order --- */
  chk('a permanent grant taken after a timed one stops it expiring',
      fold(mk([[1, '__probe_drug'], [5, '__probe_perm']]), 60).flags.has('__probe_acting'));
  chk('a permanent grant taken before a timed one is not cancelled by it',
      fold(mk([[1, '__probe_perm'], [5, '__probe_drug']]), 60).flags.has('__probe_acting'));

  /* --- an effect guarded on the flag dies with it --- */
  if (typeof baseline === 'number') {
    chk('an effect guarded on a timed flag acts while the flag stands',
        fold(mk([[1, '__probe_drug']]), 10).vitals[VIT] === baseline + 4);
    chk('and stops when the flag lapses',
        fold(mk([[1, '__probe_drug']]), 40).vitals[VIT] === baseline);

    /* --- onset --- */
    chk('an effect with an onset has not started before it',
        fold(mk([[1, '__probe_slow']]), 10).vitals[VIT] === baseline);
    chk('it is acting after the onset',
        fold(mk([[1, '__probe_slow']]), 30).vitals[VIT] === baseline + 6);
    chk('and its duration is measured from the administration, not from the onset',
        fold(mk([[1, '__probe_slow']]), 60).vitals[VIT] === baseline + 6 &&
        fold(mk([[1, '__probe_slow']]), 62).vitals[VIT] === baseline);

    /* The clamp. A saturation cannot be driven above 100 by an effect, however large the
       delta or however many effects stack, and a case that would need it to has authored
       the wrong baseline rather than discovered a new physiology. */
    A.__probe_huge = {
      id: '__probe_huge', name: 'Probe huge', tab: 'interventions', group: 'Probe',
      category: 'medication', state_changing: true, repeatable: true, prerequisites: [],
      flags_set: [], flags_set_timed: [],
      vital_effects: [{ vital: 'oxygen_saturation', delta: 50, key: '__probe_huge_a' },
                      { vital: 'oxygen_saturation', delta: 50, key: '__probe_huge_b' }]
    };
    chk('effects cannot drive a saturation above 100',
        fold(mk([[1, '__probe_huge']]), 5).vitals.oxygen_saturation === 100);
    A.__probe_huge.vital_effects = [{ vital: 'oxygen_saturation', delta: -400,
                                      key: '__probe_huge_a' }];
    chk('nor below zero',
        fold(mk([[1, '__probe_huge']]), 5).vitals.oxygen_saturation === 0);
    delete A.__probe_huge;
  } else {
    chk('this case authors no vitals, so the effect half is not exercised', true);
  }

  /* --- the point of the whole mechanism: a lapse can move the case --- */
  if (target) {
    P.transitions = [{ when: 'action __probe_drug taken AND NOT flag __probe_acting set',
                       to: target.id }];
    const held = fold(mk([[1, '__probe_drug']]), 20);
    chk('the case does not move while the drug is acting', held.phase === START, held.phase);
    const lapsed = fold(mk([[1, '__probe_drug']]), 40);
    chk('the case moves when the drug wears off, with no further action taken',
        lapsed.phase === target.id, lapsed.phase);
    chk('the move happens at the lapse, not at the next render',
        lapsed.phaseSeq.length === 2 && lapsed.phaseSeq[1].t === 31,
        JSON.stringify(lapsed.phaseSeq));
    /* A resident who redoses before the deadline should not be overtaken by it. */
    chk('redosing before the deadline holds the case where it was',
        fold(mk([[1, '__probe_drug'], [25, '__probe_drug']]), 40).phase === START);
  } else {
    chk('this case has only terminal phases beyond the first, so the lapse-transition '
        + 'assertion is not made here', true);
  }

  P.transitions = savedTransitions;
  delete A.__probe_drug; delete A.__probe_slow; delete A.__probe_perm;
  chk('the harness left the case as it found it',
      JSON.stringify(PHASE[START].transitions) === JSON.stringify(savedTransitions) &&
      !A.__probe_drug);
}

section('no unread state');
chk('results carry no viewed flag',
    Object.keys(ST_SAMPLE.orders).every(id =>
      ST_SAMPLE.orders[id].every(o => !('viewed' in o))));

section('the heartbeat interval model');
if (typeof AUDIO === 'undefined' || !AUDIO.intervalModel) {
  chk('audio block is present in the build', false, 'no __AUDIO_START__ fence');
} else {
  const RH = SHARED.audio.rhythm || {};
  const names = Object.keys(RH).filter(k => k[0] !== '_');
  chk('the rhythm vocabulary exists and includes regular', names.includes('regular'),
      names.join(', '));

  /* A regular rhythm must be exactly the mean, not nearly it. Anything else would
     mean the two cases written before this existed had their beat quietly changed. */
  let exact = true;
  for (const m of [273, 375, 500, 577, 1579, 3000]) {
    for (let i = 0; i < 200; i++) if (AUDIO.intervalModel(m, 'regular') !== m) exact = false;
  }
  chk('a regular rhythm returns the mean interval exactly', exact);
  chk('an unknown rhythm name falls back to the mean',
      AUDIO.intervalModel(500, 'no_such_rhythm') === 500 &&
      AUDIO.intervalModel(500, undefined) === 500);

  /* Statistics over a large sample. The mean is the load-bearing property: the rate on
     the monitor and the average rate in the ear have to be the same number, or the case
     is showing one thing and sounding another. */
  const stats = (mean, rhythm, n) => {
    let s = 0, ss = 0, lo = Infinity, hi = -Infinity, bad = 0;
    for (let i = 0; i < n; i++) {
      const v = AUDIO.intervalModel(mean, rhythm);
      if (!isFinite(v) || v <= 0) { bad++; continue; }
      s += v; ss += v * v; if (v < lo) lo = v; if (v > hi) hi = v;
    }
    const m = s / n;
    return { m, sd: Math.sqrt(ss / n - m * m), lo, hi, bad, cv: Math.sqrt(ss / n - m * m) / m };
  };

  for (const [name, cfg] of Object.entries(RH)) {
    if (name[0] === '_' || !(cfg.refractoryFraction > 0)) continue;
    const floorMs = cfg.absoluteFloorMs || 0;
    for (const mean of [273, 375, 577, 1579]) {
      const st = stats(mean, name, 120000);
      chk(`${name} at ${mean} ms: no bad draws`, st.bad === 0, String(st.bad));
      chk(`${name} at ${mean} ms: the mean is preserved within one percent`,
          Math.abs(st.m - mean) / mean < 0.01,
          st.m.toFixed(1) + ' against ' + mean);
      chk(`${name} at ${mean} ms: nothing shorter than the ${floorMs} ms floor`,
          st.lo >= floorMs - 1e-9, st.lo.toFixed(1));
      chk(`${name} at ${mean} ms: nothing longer than the ceiling`,
          st.hi <= mean * (cfg.ceilingMultiple || 3) + 1e-9, st.hi.toFixed(1));
      chk(`${name} at ${mean} ms: audibly uneven`, st.cv > 0.08, st.cv.toFixed(3));
    }
    /* The spread narrows as the rate rises, because the fixed refractory floor eats
       into the variable part. That is the property that keeps the mean honest at fast
       rates instead of clamping a third of the beats onto the floor. */
    const fast = stats(273, name, 120000), slow = stats(1579, name, 120000);
    chk(`${name}: the spread is narrower at a fast rate than at a slow one`,
        fast.cv < slow.cv, fast.cv.toFixed(3) + ' against ' + slow.cv.toFixed(3));
    /* No interval can be short enough for one beat's second sound to land on the next
       beat's first. The lub-dub gap is 160 ms and is itself compressed below that. */
    chk(`${name}: the floor clears the lub-dub gap`, floorMs > 160, String(floorMs));
  }

  /* Whatever the case under test authors has to be a name the vocabulary holds.
     The validator enforces this too; it is repeated here because the validator reads
     the case file and this reads the built artefact, and a build step between them is
     where a value could still be lost. */
  const badRhythm = CASE.phases.filter(p => p.rhythm && !names.includes(p.rhythm));
  chk('every phase names a rhythm the build knows', badRhythm.length === 0,
      badRhythm.map(p => p.id + '=' + p.rhythm).join(', '));

  /* The extremes of the draw, which is where an infinity or a zero would hide. */
  const real = Math.random;
  try {
    Math.random = () => 0;
    chk('the shortest possible draw is the floor and is finite',
        isFinite(AUDIO.intervalModel(375, 'irregularly_irregular')) &&
        AUDIO.intervalModel(375, 'irregularly_irregular') >= 240);
    Math.random = () => 1 - Number.EPSILON / 4;   /* rounds to 1: -log(0) is Infinity */
    const v = AUDIO.intervalModel(375, 'irregularly_irregular');
    chk('the longest possible draw is clamped and is finite', isFinite(v) && v > 0,
        String(v));
  } finally { Math.random = real; }
}

section('the heartbeat loop');
/* The interval model above is arithmetic and easy to check. The loop around it is
   where the real hazards are: a chain that schedules itself twice beats double, a
   chain that captures the rate when it starts stops following the monitor, and a
   chain that is restarted by every render stutters. None of that is visible in a unit
   of arithmetic, so the loop is driven here against a virtual clock and a stub audio
   context. Everything is restored afterwards. */
if (typeof AUDIO === 'undefined' || !AUDIO.intervalModel) {
  chk('audio available for the loop test', false);
} else {
  const realST = global.ST, realSetT = global.setTimeout, realClearT = global.clearTimeout;
  const realWindow = global.window, realPHASE = global.PHASE;
  try {
    const sink = { connect: x => x };
    const osc = () => ({ type: '', frequency: { setValueAtTime(){}, exponentialRampToValueAtTime(){} },
                         connect: x => x, start(){}, stop(){} });
    const gain = () => ({ gain: { value: 0, setValueAtTime(){}, exponentialRampToValueAtTime(){} },
                          connect: x => x });
    const stubCtx = { state: 'running', currentTime: 0, destination: sink,
                      resume(){}, createGain: gain, createOscillator: osc };
    global.window = { AudioContext: function () { return stubCtx; } };

    /* Virtual clock. One pending timer at most is the property under test, so the
       queue is asserted rather than assumed. */
    let now = 0, pending = [], nextId = 1, maxPending = 0;
    global.setTimeout = (fn, ms) => {
      pending.push({ id: nextId, at: now + ms, fn });
      maxPending = Math.max(maxPending, pending.length);
      return nextId++;
    };
    global.clearTimeout = id => { pending = pending.filter(t => t.id !== id); };
    const advance = to => {
      let guard = 0;
      while (guard++ < 200000) {
        const due = pending.filter(t => t.at <= to).sort((a, b) => a.at - b.at)[0];
        if (!due) break;
        pending = pending.filter(t => t !== due);
        now = due.at; stubCtx.currentTime = now / 1000;
        due.fn();
      }
      now = to; stubCtx.currentTime = to / 1000;
    };

    const phaseId = CASE.phases[0].id;
    global.PHASE = { [phaseId]: { id: phaseId, rhythm: 'irregularly_irregular', vitals: {} } };
    global.ST = { phase: phaseId, monitoring: { t: 0 },
                  vitals: { heart_rate: 160, oxygen_saturation: 88 } };

    let beats = 0;
    const realOsc = stubCtx.createOscillator;
    stubCtx.createOscillator = () => { beats++; return realOsc(); };

    AUDIO.start();
    advance(60000);
    /* Two oscillators per beat, the lub and the dub. */
    const n60 = beats / 2;
    chk('sixty seconds at 160 bpm gives about 160 beats', Math.abs(n60 - 160) <= 12,
        n60.toFixed(0));
    chk('only ever one beat is pending', maxPending <= 1, String(maxPending));

    /* Sixty renders a second must not disturb it. This is the regression the removed
       quantisation used to paper over. */
    beats = 0; const before = pending.length;
    for (let i = 0; i < 600; i++) AUDIO.sync();
    chk('calling sync repeatedly schedules nothing extra',
        pending.length === before && beats === 0, String(pending.length));

    /* The rate is read per beat, so changing it changes the tempo without a restart. */
    beats = 0; ST.vitals.heart_rate = 60;
    advance(now + 60000);
    const slow = beats / 2;
    chk('the tempo follows a change in the heart rate', Math.abs(slow - 60) <= 8,
        slow.toFixed(0));

    /* Losing the monitor stops the beat; regaining it starts it again. */
    ST.monitoring = null; AUDIO.sync();
    chk('no monitor, no pending beat', pending.length === 0, String(pending.length));
    beats = 0; advance(now + 5000);
    chk('and nothing sounds while it is off', beats === 0, String(beats / 2));
    ST.monitoring = { t: 0 }; AUDIO.sync();
    chk('reattaching restarts it', pending.length === 1, String(pending.length));
    AUDIO.stop();
    chk('stop leaves nothing pending', pending.length === 0, String(pending.length));
  } finally {
    global.ST = realST; global.setTimeout = realSetT; global.clearTimeout = realClearT;
    global.window = realWindow; global.PHASE = realPHASE;
  }
}

section('determinism');
const L = mk([[1, anyStudy], [3, EXAMS[0]], [8, anyStudy]]);
const r1 = fold(L, 40), r2 = fold(L, 40);
chk('same log, same state',
    r1.phase === r2.phase && r1.nurse.length === r2.nurse.length &&
    r1.timeline.length === r2.timeline.length);

/* ================= case pack assertions ================= */
const caseTests = findCaseTests(process.argv[3]);
if (caseTests) {
  console.log('\n============ case assertions: ' + path.relative(ROOT, caseTests) + ' ============');
  eval(fs.readFileSync(caseTests, 'utf8'));
} else {
  console.log('\n(no case test file found; engine checks only)');
}

console.log('\n' + count + ' checks, ' + (fails ? fails + ' FAILURES' : 'all passed'));
process.exit(fails ? 1 : 0);
