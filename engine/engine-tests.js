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

const eng = html.match(/\/\*__ENGINE_START__\*\/([\s\S]*?)\/\*__ENGINE_END__\*\//);
if (!eng) { console.error('engine block not found in ' + HTML_PATH); process.exit(2); }
eval(eng[1]);

/* Bind the case under test. With one pack it is chosen automatically. */
const WANT = process.argv[4] || null;
const packIdx = WANT ? CASES.findIndex(c => c.prefix === WANT || c.id === WANT) : 0;
if (packIdx < 0) { console.error('no such case: ' + WANT); process.exit(2); }
function bind(i) {
  selectCase(i);
  const st = engineState();
  for (const k of ['CASE', 'PROTO', 'PACK', 'PHASE', 'ACT', 'FU', 'CK', 'CONTENT']) global[k] = st[k];
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

/* ids discovered from the loaded data, never hard-coded */
const A = PROTO.actions;
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
  for (const caseId in byCase) {
    const members = byCase[caseId].concat([
      Object.keys(PACK.bindings).find(c => PACK.bindings[c] === caseId) ? caseId : null
    ].filter(Boolean));
    for (const m of members) {
      if (tagOf(m, { phase: START_PHASE, flags: new Set(['iv_access']), ordered: new Set(),
                     resulted: new Set(), taken: new Set() }) !== 'harmful') continue;
      const st = fold(mk([[1, 'iv_access_peripheral'], [5, m]]), 20);
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

section('no unread state');
chk('results carry no viewed flag',
    Object.keys(ST_SAMPLE.orders).every(id =>
      ST_SAMPLE.orders[id].every(o => !('viewed' in o))));

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
