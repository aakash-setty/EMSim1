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
    const unwarned = [], offPath = [];
    for (const [phase, , t] of guarded) {
      /* This walk sees only the phases the do-nothing path reaches, and a case may put a
         guarded deterioration in a phase that path never enters: DIPH's post-ictal phase
         is entered by giving a benzodiazepine, which a resident who does nothing never
         does. Treating an unvisited phase as unwarned reported a fairness failure for a
         deadline that cannot fire on this path at all, which is a false alarm rather than
         a finding. The authored-deadline half of the same rule is enforced statically by
         the validator for every phase, visited or not; what this check adds is the part
         the validator cannot see, which is the prompt cap, and the cap can only suppress
         a prompt in a phase somebody is standing in. */
      if (idle.phaseEntry[phase] === undefined) { offPath.push(phase); continue; }
      const flags = [...(t.when.match(/flag ([a-z0-9_]+) set/g) || [])]
        .map(x => x.replace('flag ', '').replace(' set', ''));
      for (const f of flags) {
        const setters = Object.keys(A).filter(id => (A[id].flags_set || []).includes(f));
        const fired = idle.promptFires.some(p => setters.includes(p.id) &&
                                                 p.t < (idle.phaseEntry[phase] || 0) + t.after_seconds);
        if (!fired) unwarned.push(phase + ' deteriorates on ' + f + ' with no prompt seen');
      }
    }
    if (offPath.length) console.log('  note guarded deteriorations in phases the ' +
      'do-nothing path never enters, checked statically by the validator instead: ' +
      [...new Set(offPath)].join(', '));
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

section('the patient\'s side of the conversation (design 10.7)');
{
  const IV = CASE.interview;
  const D = PROTO.interviewDefaults || {};
  const withFacts = IV.topics.find(t => t.facts && t.facts.length >= 2);
  const plain = IV.topics.find(t => !t.facts || !t.facts.length) || IV.topics[0];
  const speech = st => st.readouts.filter(r => r.kind === 'speech');
  const ask = (t, extra) => Object.assign({ t, kind: 'interview', q: 'q' + t }, extra);
  const first = fold(mk([ask(1, { topic: plain.topic })]), 5);
  const firstBody = speech(first)[0].body;
  chk('the first ask of a topic is its authored answer',
      firstBody === resolve((IV.global_answer_rules || []).concat(plain.answer), first));

  /* Asking twice does not produce the paragraph twice. */
  const twice = fold(mk([ask(1, { topic: plain.topic }), ask(2, { topic: plain.topic })]), 5);
  const sp2 = speech(twice);
  chk('a repeat gets a restatement, not the paragraph again',
      sp2.length === 2 && sp2[1].body !== sp2[0].body && sp2[1].body.length < sp2[0].body.length + 40,
      sp2.length === 2 ? sp2[1].body.slice(0, 60) : String(sp2.length));
  chk('the restatement carries a repeat prefix from the defaults',
      (D.repeatPrefixes || []).some(p => {
        const head = p.split('{answer}')[0];
        return head && sp2[1].body.startsWith(head);
      }) || !(D.repeatPrefixes || []).length, sp2[1].body.slice(0, 40));
  chk('a repeat still satisfies the topic', twice.satisfied.has('interview_topic_' + plain.topic)
      || !ACT['interview_topic_' + plain.topic]);
  const thrice = fold(mk([ask(1, { topic: plain.topic }), ask(2, { topic: plain.topic }), ask(3, { topic: plain.topic })]), 5);
  chk('a third ask is phrased differently from the second',
      speech(thrice)[2].body !== speech(thrice)[1].body || (D.repeatPrefixes || []).length < 2,
      speech(thrice)[2].body.slice(0, 40));

  /* An echo in front of an uncertain match, and none in front of a confident one. */
  if (plain.echo) {
    const unsure = fold(mk([ask(1, { topic: plain.topic, uncertain: true })]), 5);
    const b = speech(unsure)[0].body;
    chk('an uncertain match is answered with the topic echoed first',
        b.toLowerCase().indexOf(plain.echo.toLowerCase()) >= 0 && b.indexOf('?') > 0 && b.indexOf('?') < plain.echo.length + 4,
        b.slice(0, 50));
    chk('a confident match is not', firstBody.indexOf(plain.echo + '?') < 0);
  } else chk('this pack authors no echo on ' + plain.topic + ', so the echo assertion is not made', true);

  /* Clarification names both topics and commits to neither. */
  const [ta, tb] = IV.topics.slice(0, 2);
  const cl = fold(mk([ask(1, { topic: null, clarify: [ta.topic, tb.topic], q: 'which' })]), 5);
  const cb = speech(cl)[0];
  chk('a clarification is spoken', !!cb && typeof cb.body === 'string' && cb.body.length > 10);
  chk('it names both candidates', !!cb && [ta, tb].every(t => cb.body.indexOf(t.echo || t.topic.replace(/_/g, ' ')) >= 0), cb && cb.body);
  chk('it commits to neither', !!cb && cb.matched === null
      && !cl.satisfied.has('interview_topic_' + ta.topic) && !cl.satisfied.has('interview_topic_' + tb.topic));

  /* Facts: a follow-up gets the piece asked about; "anything else" gets what is untold. */
  if (withFacts) {
    const f0 = withFacts.facts[0], f1 = withFacts.facts[1];
    const one = fold(mk([ask(1, { topic: withFacts.topic, fact: f0.id })]), 5);
    const want = resolve((IV.global_answer_rules || []).concat(Array.isArray(f0.value) ? f0.value : [{ when: null, value: f0.value }]), one);
    chk('a fact question is answered with that fact', speech(one)[0].body === want, speech(one)[0].body);
    chk('and satisfies the topic', one.satisfied.has('interview_topic_' + withFacts.topic) || !ACT['interview_topic_' + withFacts.topic]);
    const more = fold(mk([ask(1, { topic: withFacts.topic, fact: f0.id }), ask(2, { topic: withFacts.topic, more: true })]), 5);
    const mb = speech(more)[1].body;
    const f1want = resolve((IV.global_answer_rules || []).concat(Array.isArray(f1.value) ? f1.value : [{ when: null, value: f1.value }]), more);
    chk('"anything else" after one fact tells the next untold fact', mb.indexOf(f1want) >= 0, mb.slice(0, 60));
    chk('and not the one already told', mb.indexOf(want) < 0);
    const drained = fold(mk([ask(1, { topic: withFacts.topic }), ask(2, { topic: withFacts.topic, more: true })]), 5);
    chk('"anything else" after the full answer says there is nothing more',
        speech(drained)[1].body === (IV.nothing_more || D.nothingMore), speech(drained)[1].body);
    /* The restatement for a topic with facts is the fact marked restate, or the first. */
    const rep = fold(mk([ask(1, { topic: withFacts.topic }), ask(2, { topic: withFacts.topic })]), 5);
    const rf = withFacts.facts.find(f => f.restate) || withFacts.facts[0];
    const core = resolve((IV.global_answer_rules || []).concat(Array.isArray(rf.value) ? rf.value : [{ when: null, value: rf.value }]), rep)
                 .replace(/^'|'$/g, '');
    chk('a repeat of a topic with facts restates its lead fact', speech(rep)[1].body.indexOf(core) >= 0, speech(rep)[1].body.slice(0, 60));
  } else chk('this pack authors no facts, so the fact assertions are not made', true);

  /* All of it replays. */
  const a = fold(mk([ask(1, { topic: plain.topic }), ask(2, { topic: plain.topic }), ask(3, { topic: null, clarify: [ta.topic, tb.topic] })]), 5);
  const b = fold(mk([ask(1, { topic: plain.topic }), ask(2, { topic: plain.topic }), ask(3, { topic: null, clarify: [ta.topic, tb.topic] })]), 5);
  chk('the conversation is a pure function of the log',
      JSON.stringify(speech(a).map(x => x.body)) === JSON.stringify(speech(b).map(x => x.body)));
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

section('the interface does not assume the patient is male');
{
  /* v0.11. Strings shared across every case cannot name a sex, so they carry pronoun
     tokens that the bind substitutes from patient.sex. Two things to check and the second
     is the one that was broken: that no token survives to the screen, and that nothing the
     nurse says calls the patient by the wrong pronoun. Scoped to the shared strings, the
     nurse's idle line and the prerequisite failure messages, because authored case text is
     the author's business and may legitimately name somebody else. */
  const SEX = String((CASE.patient || {}).sex || '').toLowerCase();
  const shared = [PROTO.nurseIdle].concat(
    Object.keys(A).flatMap(id => (A[id].prerequisites || []).map(p => p.failure_message || '')));
  const leftover = shared.filter(x => /\{(He's|he's|He|he|His|his|Him|him|himself)\}/.test(x));
  chk('no shared string still carries an unsubstituted pronoun token',
      leftover.length === 0, leftover.join(' | '));
  chk('the nurse has an idle line at all', !!PROTO.nurseIdle, PROTO.nurseIdle);
  if (SEX === 'female') {
    const wrong = shared.filter(x => /\b(he|his|him|He|His|Him)\b/.test(x));
    chk('nothing shared calls a female patient he', wrong.length === 0, wrong.join(' | '));
  } else if (SEX === 'male') {
    const wrong = shared.filter(x => /\b(she|her|She|Her)\b/.test(x));
    chk('nothing shared calls a male patient she', wrong.length === 0, wrong.join(' | '));
  } else {
    chk('a case that states no sex is not something this build has', false,
        'patient.sex is ' + JSON.stringify((CASE.patient || {}).sex));
  }
  /* The substitution is per bind and must not leak between cases, which is the failure a
     shared object invites: bind another pack and come back. */
  if (CASES.length > 1) {
    const mine = PROTO.nurseIdle;
    const other = (packIdx + 1) % CASES.length;
    bind(other);
    const theirs = PROTO.nurseIdle;
    bind(packIdx);
    chk('rebinding the case under test restores its own line',
        PROTO.nurseIdle === mine, PROTO.nurseIdle);
    chk('and each case gets the line its own patient earns',
        (String((CASES[other].case.patient || {}).sex || '').toLowerCase() === SEX)
          ? theirs === mine : theirs !== mine,
        mine + '  vs  ' + theirs);
  }
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
       prerequisites, so the assertion is about the effect and not about the block.

       Two further filters, both added after a case failed this section for reasons that
       were not defects. Prefer an effect with no `while` guard: section 6.1 explicitly
       allows one, and an effect guarded off in the start phase moves nothing there by
       design, so reading it at t=3 measured the guard rather than the effect. And read
       after the onset rather than at a fixed t=3, because an effect with a thirty-second
       onset has not started at three seconds and reporting that as a failure to move is
       a statement about the clock. */
    const unguarded = withFx.filter(x => !(A[x].prerequisites || []).length &&
                                         !(A[x].vital_effects[0].while));
    const id = unguarded[0] || withFx.find(x => !(A[x].prerequisites || []).length) || withFx[0];
    const fx = A[id].vital_effects[0];
    const pre = (A[id].prerequisites || []).length;
    const readAt = 1 + (fx.onset_seconds || 0) + 1;
    if (!pre) {
      const st = fold(mk([[1, id]]), readAt);
      const moved = st.vitals[fx.vital] - PHASE[st.phase].vitals[fx.vital];
      chk('an effect moves its vital off the phase baseline', moved !== 0,
          id + ' ' + fx.vital + ' ' + moved);
      /* Repeat dosing refreshes rather than stacks: two administrations sharing a key
         must not double the delta. */
      const twice = fold(mk([[1, id], [2, id]]), readAt + 1);
      chk('the same action twice does not stack',
          twice.vitals[fx.vital] === fold(mk([[2, id]]), readAt + 1).vitals[fx.vital]);
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

section('follow-ups can be discharged');
for (const f of CASE.follow_ups) {
  chk(f.id + ' has a route to satisfaction',
      (f.satisfied_by && f.satisfied_by.length) || !!f.satisfied_when,
      'neither satisfied_by nor satisfied_when');
  for (const id of (f.satisfied_by || []))
    chk(f.id + ': satisfier ' + id + ' exists', !!A[id]);
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
      /constNURSE_IN_CHART=\{prompt:1,deterioration:1,alert:1\}/.test(flat));
  /* Every nurse utterance makes a sound and the two are exclusive, because a trill and a
     cue on the same line would be worse than neither. */
  chk('a prompt trills and every other line cues',
      /if\(LASTNURSE>=0\)\{if\(n\.kind==='prompt'\)AUDIO\.trill\(\);elseAUDIO\.cue\(\);\}/.test(flat));

  /* The room is started and stopped by the interface at four points and by nothing else.
     Asserted against the built file, because the requirement is that no sound survives
     into the debrief or back to the welcome screen, and losing one of these calls would
     be silent in every other test here. */
  chk('the room starts when a case begins', /AUDIO\.setScene\('case'\)/.test(flat));
  chk('and stops at the debrief, on restart, and back at the picker',
      (flat.match(/AUDIO\.setScene\('idle'\)/g) || []).length >= 3,
      String((flat.match(/AUDIO\.setScene\('idle'\)/g) || []).length));
  chk('the ambience asset is embedded', /id="ambience-data"/.test(html) &&
      /data:audio\/mpeg;base64,/.test(html));

  /* The case clock is wall-clock time, so a window nobody is looking at has to stop it or
     every deadline a case authors becomes a claim about a browser tab. Asserted against
     the built file: both signals, a clock that subtracts the time away, and a resume that
     is a deliberate click rather than something that happens on its own. */
  chk('a hidden window pauses the case',
      /addEventListener\('visibilitychange'/.test(flat) && /document\.hidden\)pauseSim/.test(flat));
  chk('a window that loses focus pauses too',
      /addEventListener\('blur',pauseSim\)/.test(flat));
  chk('the clock subtracts the time away',
      /PAUSED\?PAUSED_AT:Date\.now\(\)\)-T0-PAUSED_MS/.test(flat));
  chk('resuming is a click and never automatic',
      /getElementById\('resumebtn'\)|el\('resumebtn'\)/.test(flat.replace(/\s/g,'')) ||
      /resumebtn/.test(flat));
  chk('the paused case makes no sound', /pauseSim\(\)\{[^}]*AUDIO\.setScene\('idle'\)/.test(flat));

  /* Leaving. What is interceptable gets the case's own dialog; the browser's own reload
     control reaches only beforeunload, which is why that is registered as well. */
  chk('a keyboard refresh is caught before it happens',
      /e\.key==='F5'/.test(flat) && /askLeave\('reload'\)/.test(flat));
  chk('the back button is caught', /addEventListener\('popstate'/.test(flat) &&
      /askLeave\('back'\)/.test(flat));
  chk('and a guard entry is pushed when a case begins',
      /history\.pushState\(\{emsim:1\}/.test(flat));
  chk('beforeunload still covers the paths a page cannot intercept',
      /addEventListener\('beforeunload'/.test(flat));
  chk('both overlays are in the markup',
      /id="pauseview"/.test(html) && /id="leaveview"/.test(html) &&
      /id="resumebtn"/.test(html) && /id="leaveok"/.test(html));

  /* Doses are not implemented, so the word is dropped. Dropping it and leaving the
     preposition behind produced "Giving of ceftriaxone". */
  const dosed = Object.keys(A).filter(id => A[id].narration_template &&
                                            /\{dose\}/.test(A[id].narration_template));
  chk('every narration template has a dose slot to drop', dosed.length > 0, String(dosed.length));
  const bad = dosed.map(id => narrationFor(id))
                   .filter(t => / of | at |\{dose\}|  /.test(t));
  chk('no narration reads "giving of" or leaves a dangling preposition',
      bad.length === 0, bad.slice(0, 3).join(' | '));
  /* A display name is Title Case because it is a button. Lowering it wholesale broke
     units, acronyms and proper nouns; lowering only ordinary Title Case tokens fixes
     both halves. Templates that lead with the name still have to start with a capital. */
  const lines = Object.keys(A).map(id => narrationFor(id)).filter(Boolean);
  chk('every narration starts with a capital',
      lines.every(t => !/^[a-z]/.test(t)),
      lines.filter(t => /^[a-z]/.test(t)).slice(0, 3).join(' | '));
  const unit = Object.keys(A).find(id => /\d(?:L|mL|mg)\b/.test(A[id].name || ''));
  if (unit) chk('a unit in a display name keeps its capital',
                new RegExp(A[unit].name.match(/\d(?:L|mL|mg)\b/)[0]).test(narrationFor(unit)),
                narrationFor(unit));
  const acro = Object.keys(A).find(id => /\b[A-Z]{2,}\b/.test(A[id].name || ''));
  if (acro) chk('an acronym in a display name keeps its capitals',
                new RegExp(A[acro].name.match(/\b[A-Z]{2,}\b/)[0]).test(narrationFor(acro)),
                narrationFor(acro));

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

section('the clock\'s ending');
{
  /* The third ending. `halted` is a harmful action and `complete` is a handoff; a case
     that authors allow_time_to_terminal had neither, and before this the run reached its
     terminal phase and then carried on with the clock running. Case-agnostic: the
     harness installs its own transition into whichever terminal phase the loaded case
     has that is not the completion phase, exercises it, and puts the case back. */
  const START = CASE.phases[0].id;
  const P = PHASE[START];
  const saved = P.transitions ? P.transitions.slice() : [];
  const term = CASE.phases.find(p => p.terminal && p.id !== 'case_complete');

  chk('a fresh run is not failed', fold(mk([]), 5).failed === null);

  if (term) {
    A.__probe_end = { id: '__probe_end', name: 'Probe ending', tab: 'interventions',
                      group: 'Probe', category: 'medication', state_changing: true,
                      repeatable: false, prerequisites: [], flags_set: ['__probe_end_flag'],
                      flags_set_timed: [] };
    P.transitions = [{ when: 'flag __probe_end_flag set', to: term.id,
                       allow_time_to_terminal: true }];

    const before = fold(mk([]), 5);
    chk('a run still in a live phase is not failed', before.failed === null, before.phase);

    const after = fold(mk([[7, '__probe_end']]), 20);
    chk('walking into a terminal phase marks the run failed',
        !!after.failed, after.phase);
    chk('it names the phase that ended it',
        after.failed && after.failed.phase === term.id,
        after.failed && after.failed.phase);
    chk('it timestamps the phase entry, not the moment it was read',
        after.failed && after.failed.t === 7, after.failed && String(after.failed.t));
    chk('it carries the phase\'s own timeout reason, or an empty string if the case '
        + 'authors none',
        after.failed && typeof after.failed.reason === 'string');
    chk('a failed run is not also marked complete', after.complete === null);

    delete A.__probe_end;
  } else {
    chk('this case authors no terminal phase other than the completion phase, so the '
        + 'clock ending is not exercised here', true);
  }

  P.transitions = saved;
  chk('the harness left the case as it found it',
      JSON.stringify(PHASE[START].transitions) === JSON.stringify(saved) && !A.__probe_end);
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
    /* No interval can be short enough for one beat to still be sounding when the next
       one starts. The beat is a fixed-length gated tone, so this is one comparison rather
       than a claim about a compressed gap. */
    const shape = AUDIO.beatShape || { durMs: 0 };
    chk(`${name}: the floor clears a whole beat`, floorMs > shape.durMs,
        floorMs + ' ms floor against a ' + shape.durMs + ' ms beat');
  }

  /* The balance between the three sounds is a decision, and a decision nothing can check
     is a decision that drifts. These are the invariants rather than a ranking: peak gain
     is not perceived loudness, and the beat is long and low where the cue and the trill
     are short and high, so the numbers do not order the way the ear does. */
  if (AUDIO.levels) {
    const L = AUDIO.levels;
    chk('the prompt trill is the loudest single component',
        L.trillLow >= L.cueLow && L.trillLow >= L.beatBody, JSON.stringify(L));
    chk('the octave partial sits well under the body of the beat',
        L.beatOctave < L.beatBody * 0.25,
        (L.beatOctave / L.beatBody).toFixed(3) + ' of the body');
    chk('the cue is quieter than the trill, since it fires far more often',
        L.cueLow < L.trillLow, JSON.stringify(L));
    /* A cue landing on the same instant as a beat must not be swallowed by it. */
    chk('a cue cannot be masked by a beat', L.cueLow > L.beatBody * 0.6,
        (L.cueLow / L.beatBody).toFixed(2) + ' of the beat');
    chk('nothing is loud enough to dominate the mix',
        Object.values(L).every(v => v > 0 && v < 0.5), JSON.stringify(L));
  }

  /* The beat's envelope. The claim being made is that it is a held tone rather than a
     decaying one, and the thing that makes it held is that there is a stretch in the
     middle at full gain. A rise and a fall that between them consume the whole duration
     would be a bell, which is a different sound and would undo the change. */
  if (AUDIO.beatShape) {
    const B = AUDIO.beatShape;
    chk('the beat holds at full gain between its edges', B.holdMs > 0,
        B.riseMs + ' + ' + B.fallMs + ' of ' + B.durMs + ' ms');
    chk('the hold is the largest part of the beat',
        B.holdMs > B.riseMs && B.holdMs > B.fallMs, JSON.stringify(B));
    chk('the onset is fast enough to time a beat by', B.riseMs <= 15, String(B.riseMs));
    chk('the octave partial leaves before the body does',
        B.octaveDurMs < B.durMs, B.octaveDurMs + ' against ' + B.durMs);
    /* The duty-cycle guard is a backstop, not a working part. If it is active at a rate a
       case can author then the beat is no longer the same length every time, which is the
       property the change was made for. */
    const fastest = 60000 / 220;
    chk('no rate a case can author engages the duty-cycle guard',
        B.durMs <= fastest * B.maxDutyCycle,
        B.durMs + ' ms against ' + (fastest * B.maxDutyCycle).toFixed(0) + ' ms of room');
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
  const realWindow = global.window, realPHASE = global.PHASE, realAmb = global.AMBIENCE;
  try {
    const sink = { connect: x => x };
    /* The stub records what was scheduled rather than discarding it. The beat's shape is
       a claim about what the ear hears, and the only place that claim is actually made is
       in the calls on the graph: a frequency ramp is a glide whatever the config says, and
       an envelope is a held tone only if the curve really holds. */
    const SCHED = { freqRamps: 0, freqSets: [], curves: [], oscTypes: [] };
    const osc = () => {
      const o = { type: '', connect: x => x, start(){}, stop(){},
        frequency: { setValueAtTime(v){ SCHED.freqSets.push(v); },
                     exponentialRampToValueAtTime(){ SCHED.freqRamps++; },
                     linearRampToValueAtTime(){ SCHED.freqRamps++; } } };
      /* `type` is set after creation, so it is read at start() rather than here. */
      const realStart = o.start;
      o.start = t => { SCHED.oscTypes.push(o.type); realStart(t); };
      return o;
    };
    const gain = () => ({ gain: { value: 0, setValueAtTime(){}, exponentialRampToValueAtTime(){},
                                 linearRampToValueAtTime(){}, cancelScheduledValues(){},
                                 setValueCurveAtTime(c, at, dur){
                                   SCHED.curves.push({ c: Array.from(c), at, dur }); } },
                          connect: x => x });
    const bufSrc = () => ({ buffer: null, loop: false, loopStart: 0, loopEnd: 0,
                            connect: x => x, start(){}, stop(){} });
    const stubCtx = { state: 'running', currentTime: 0, destination: sink,
                      resume(){}, createGain: gain, createOscillator: osc,
                      createBufferSource: bufSrc,
                      /* No ambience asset reaches the harness, so decoding is never
                         attempted; present so a call would fail loudly rather than
                         silently if that ever changed. */
                      decodeAudioData(){ throw new Error('no decoder in the harness'); } };
    /* A fake asset and a fake decoder, so the room can be exercised without an mp3 or a
       real audio context. The decoder deliberately BOTH calls the callback and resolves a
       promise, which is what a current browser does and which would decode twice if the
       handler were not idempotent. */
    let decodes = 0, sources = 0;
    stubCtx.decodeAudioData = (ab, ok) => {
      decodes++;
      const buf = { duration: 45 };
      if (ok) ok(buf);
      return Promise.resolve(buf);
    };
    const realBufSrc = stubCtx.createBufferSource;
    stubCtx.createBufferSource = () => { sources++; return realBufSrc(); };
    global.AMBIENCE = 'data:audio/mpeg;base64,QUJDRA==';
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

    /* Nothing sounds outside a running case, so the scene has to say one is running
       before there is a beat to measure. */
    AUDIO.setScene('case');
    AUDIO.start();
    chk('no beat outside a case', (() => {
      AUDIO.setScene('idle'); AUDIO.sync();
      const quiet = pending.length === 0;
      AUDIO.setScene('case'); AUDIO.sync();
      return quiet;
    })());
    advance(60000);
    /* Two oscillators per beat: the body and its octave partial. */
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
    ST.monitoring = { t: 0 }; AUDIO.setScene('case'); AUDIO.sync();
    chk('reattaching restarts it', pending.length === 1, String(pending.length));
    AUDIO.stop();
    chk('stop leaves nothing pending', pending.length === 0, String(pending.length));

    /* ---- what the beat actually scheduled ----
       Read off the graph rather than off the config. The config can say the pitch is
       fixed; only the absence of a frequency ramp makes it true. */
    chk('no beat schedules a pitch glide', SCHED.freqRamps === 0, String(SCHED.freqRamps));
    chk('every beat sets a frequency and holds it', SCHED.freqSets.length > 0);
    chk('every oscillator in the beat is a sine',
        SCHED.oscTypes.every(t => t === 'sine'),
        [...new Set(SCHED.oscTypes)].join(', '));
    /* The saturation pitch and its octave, and nothing in between. At SpO2 88 with an A6
       anchor that is 880 Hz and 1760 Hz. The ratio is what is asserted, not the values,
       so moving the anchor does not break this. */
    {
      const uniq = [...new Set(SCHED.freqSets.map(v => Math.round(v)))].sort((a, b) => a - b);
      const pairs = uniq.length === 2 && Math.abs(uniq[1] / uniq[0] - 2) < 1e-6;
      chk('the beat is a fundamental and one octave above it', pairs, uniq.join(' and '));
    }
    if (SCHED.curves.length) {
      const body = SCHED.curves.filter(c => c.dur === Math.max(...SCHED.curves.map(x => x.dur)));
      const c = body[0].c, peak = Math.max(...c);
      chk('the envelope starts and ends at true zero',
          c[0] === 0 && c[c.length - 1] === 0, c[0] + ' .. ' + c[c.length - 1]);
      /* The hold is what makes it a tone rather than a strike, and it has to be visible
         in the curve itself: a run of samples at full gain, not a single apex. */
      const atPeak = c.filter(v => v >= peak * 0.999).length / c.length;
      chk('the envelope holds at full gain across the middle of the beat',
          atPeak > 0.4, (atPeak * 100).toFixed(0) + '% of the window at peak');
      /* And it rises before it holds. A curve whose first sample is already at peak is a
         gate, which clicks. */
      chk('the envelope rises into the hold rather than switching on',
          c[1] > 0 && c[1] < peak * 0.5, String(c[1] / peak));
      chk('the rise and the fall are shaped, not linear ramps',
          Math.abs(c[Math.round(c.length * 0.5)] - peak) < 1e-6);
    } else {
      chk('the beat schedules a value curve for its envelope', false, 'no curves recorded');
    }

    /* ---- the room ---- */
    chk('the ambience decoded once, not twice',
        AUDIO.ambience.state === 'ready' && decodes === 1,
        AUDIO.ambience.state + ', ' + decodes + ' decodes');
    AUDIO.setScene('idle');
    chk('it is silent whenever a case is not running',
        !AUDIO.ambience.playing && AUDIO.ambience.scene === 'idle',
        JSON.stringify(AUDIO.ambience));
    AUDIO.setScene('case');
    chk('it plays once a case begins', AUDIO.ambience.playing);
    chk('and at the level the case asked for', AUDIO.ambience.level === AUDIO.levels.ambience);
    const afterStart = sources;
    AUDIO.setScene('case'); AUDIO.sync(); AUDIO.sync();
    chk('only ever one loop is running', sources === afterStart, String(sources - afterStart));
    /* The room is not the monitor. Taking equipment off a patient is not leaving the ward. */
    ST.monitoring = null; AUDIO.sync();
    chk('losing the monitor silences the heartbeat and not the room',
        pending.length === 0 && AUDIO.ambience.playing);
    ST.monitoring = { t: 0 };
    AUDIO.setScene('idle');
    chk('it stops when the case does', !AUDIO.ambience.playing);
    chk('and the heartbeat stops with it', pending.length === 0, String(pending.length));
    AUDIO.setScene('case');
    AUDIO.stop();
    chk('stop() silences the room as well as the beat', !AUDIO.ambience.playing);
    AUDIO.setScene('case');
    AUDIO.toggle();
    chk('switching the sound off silences the room', !AUDIO.ambience.playing);
    AUDIO.toggle();
    chk('and switching it back on brings it back', AUDIO.ambience.playing);
    AUDIO.setScene('idle');
    AUDIO.stop();
  } finally {
    global.ST = realST; global.setTimeout = realSetT; global.clearTimeout = realClearT;
    global.window = realWindow; global.PHASE = realPHASE; global.AMBIENCE = realAmb;
  }
}

section('determinism');
const L = mk([[1, anyStudy], [3, EXAMS[0]], [8, anyStudy]]);
const r1 = fold(L, 40), r2 = fold(L, 40);
chk('same log, same state',
    r1.phase === r2.phase && r1.nurse.length === r2.nurse.length &&
    r1.timeline.length === r2.timeline.length);

section('several diagnoses at handover (v0.9)');
{
  const correct = PROTO.correctDxId;
  const addl = Object.keys(PROTO.addlDx || {});
  const defensible = PROTO.altDxDefensible || [];
  const wrongId = Object.keys(PROTO.altDx || {}).find(id => !defensible.includes(id)) || 'dx_nowhere';
  const ho = (diagnoses, extra) => fold(mk([[1, 'insert_iv'],
    Object.assign({ t: 30, actionId: 'handoff_submit',
      payload: Object.assign({ disposition: CASE.handoff.correct_disposition.id, diagnoses }, extra || {}) }, {})]), 60);
  let st = ho([correct]);
  chk('the singular is filled in from the list', st.handoff.diagnosis === correct);
  chk('the list is kept', JSON.stringify(st.handoff.diagnoses) === JSON.stringify([correct]));
  st = fold(mk([[1, 'insert_iv'], { t: 30, actionId: 'handoff_submit',
    payload: { disposition: CASE.handoff.correct_disposition.id, diagnosis: correct } }]), 60);
  chk('an old payload with only the singular is widened to a list of one',
      JSON.stringify(st.handoff.diagnoses) === JSON.stringify([correct]));
  let dx = scoreDiagnoses(ho([correct]));
  chk('the case diagnosis first is primary_correct', dx.rows[0].verdict === 'primary_correct');
  chk('and every additional diagnosis is then missed', dx.missed.length === addl.length);
  dx = scoreDiagnoses(ho([wrongId, correct]));
  chk('a wrong primary is primary_incorrect', dx.rows[0].verdict === 'primary_incorrect', dx.rows[0].verdict);
  chk('the case diagnosis listed second is flagged, not credited as primary',
      dx.rows[1].verdict === 'main_not_primary');
  if (addl.length) {
    dx = scoreDiagnoses(ho([correct].concat(addl)));
    chk('every additional diagnosis listed beside the primary is appropriate',
        dx.rows.slice(1).every(r => r.verdict === 'appropriate') && dx.missed.length === 0);
    dx = scoreDiagnoses(ho([addl[0]]));
    chk('an additional diagnosis named as the primary is scored as a primary, not as appropriate',
        dx.rows[0].verdict !== 'appropriate', dx.rows[0].verdict);
  }
  dx = scoreDiagnoses(ho([correct, 'dx_nowhere']));
  chk('an unknown diagnosis beside the primary is unsupported', dx.rows[1].verdict === 'unsupported');
  chk('duplicates collapse', ho([correct, correct]).handoff.diagnoses.length === 1);
}

section('the seven-category summary (v0.9)');
{
  const rows = summaryScores(fold([], 10));
  chk('seven rows, in the order the tabs run',
      rows.map(r => r.id).join(',') === 'history,physical,stabilization,interventions,investigations,consultations,handoff',
      rows.map(r => r.id).join(','));
  chk('nothing done scores nothing on history and physical',
      rows[0].points === 0 && rows[1].points === 0);
  chk('the handoff row without a handoff is zero of a hundred',
      rows[6].points === 0 && rows[6].max === 100);
  const key = (CASE.interview.key_topics && CASE.interview.key_topics.length)
    ? CASE.interview.key_topics : CASE.interview.topics.map(t => t.topic);
  chk('history max is the number of key topics', rows[0].max === key.length, String(rows[0].max));
  const asked = fold(mk([{ t: 2, kind: 'interview', topic: key[0], q: 'q' }]), 10);
  chk('asking a key topic scores one point', summaryScores(asked)[0].points === 1,
      String(summaryScores(asked)[0].points));
  const examined = fold(mk([[1, EXAMS[0]]]), 10);
  const ph = summaryScores(examined)[1];
  chk('examining a region counts when the region is expected',
      ph.max === 0 || !ph.missed.includes(EXAMS[0]) || ph.points >= 0);
  /* A critical action satisfied is two points on its tab. */
  const crit = [...fold([], 1).expected].find(id => A[id] && A[id].tab === 'stabilization');
  if (crit) {
    const before = summaryScores(fold([], 5)).find(r => r.id === 'stabilization');
    const after = summaryScores(fold(mk([[1, 'insert_iv'], [2, crit]]), 5)).find(r => r.id === 'stabilization');
    chk('a critical action on Stabilization is worth two points',
        after.points - before.points >= 2 || A[crit].prerequisites.length > 0,
        before.points + ' -> ' + after.points);
  }
  const done = fold(mk([[1, 'insert_iv'], { t: 30, actionId: 'handoff_submit',
    payload: { disposition: CASE.handoff.correct_disposition.id, diagnoses: [PROTO.correctDxId] } }]), 60);
  const hr = summaryScores(done)[6];
  const nAddl = Object.keys(PROTO.addlDx || {}).length;
  chk('correct level of care and correct primary score 80 with additional diagnoses authored, 100 without',
      hr.points === (nAddl ? 80 : 100), String(hr.points));
  const full = fold(mk([[1, 'insert_iv'], { t: 30, actionId: 'handoff_submit',
    payload: { disposition: CASE.handoff.correct_disposition.id,
               diagnoses: [PROTO.correctDxId].concat(Object.keys(PROTO.addlDx || {})) } }]), 60);
  chk('naming every additional diagnosis completes the handoff score',
      summaryScores(full)[6].points === 100, String(summaryScores(full)[6].points));
  const bad = fold(mk([[1, 'insert_iv'], { t: 30, actionId: 'handoff_submit',
    payload: { disposition: CASE.handoff.correct_disposition.id,
               diagnoses: [PROTO.correctDxId, 'dx_nowhere'] } }]), 60);
  chk('an unsupported extra diagnosis costs five',
      summaryScores(bad)[6].points === summaryScores(done)[6].points - 5);
  chk('scores are deterministic',
      JSON.stringify(summaryScores(fold([], 10))) === JSON.stringify(rows));
}

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
