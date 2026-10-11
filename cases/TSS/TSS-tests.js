/* Case assertions for TSS (menstrual toxic shock syndrome, retained tampon).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * One section per claim the case makes. The claims that are new to this pack and are
 * exercised nowhere else:
 *
 *   - a disposition that does not end the run (handoff.disposition_intercepts and the
 *     hidden action it logs),
 *   - a prerequisite on an examination having been done,
 *   - three time-guarded rules on one clock in one phase, where the first two are
 *     reached only by a learner who acted early,
 *   - a case with no harmful action and no terminal phase but the handoff.
 *
 * Added on 7 October 2026 after the v0.21 to v0.23a audit, each against a finding:
 *
 *   - what the nurse says, compared with the folded monitor on every effect-bearing route
 *     and not with the phase's authored numbers,
 *   - every prompt and escalation in the default mode, where deadlines are times three,
 *   - each pair of pending timed rules, with fractional times on both sides,
 *   - a stop action that covers its siblings and is refused,
 *   - a follow-up that a dose given before its trigger does not discharge,
 *   - the spoken phrases the nurse and the consultants use for the pelvic examination.
 */

const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const START = [[1, 'attach_monitor'], [2, 'insert_iv']];

section('intended path');
let st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [20, 'exam_gu'],
  [22, 'remove_vaginal_foreign_body'], [24, 'vancomycin'], [25, 'clindamycin'],
  [60, 'lactated_ringer_s_1l_bolus'], [170, 'norepinephrine_drip'],
  [185, 'consult_critical_care']])), 200);
chk('reaches stabilizing', st.phase === 'stabilizing', st.phase);
chk('through the fluid response and its fade',
  seq(st) === 'presentation > fluid_responsive > hypotensive > stabilizing', seq(st));
chk('nothing halted, failed or completed', !st.halted && !st.failed && !st.complete);
chk('every critical action expected anywhere on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)),
  [...st.expected].filter(id => !st.satisfied.has(id)).join(', '));
chk('no prompt was needed', st.promptFires.length === 0, JSON.stringify(st.promptFires));
chk('the second liter discharged its follow-up', st.fuOutstanding.size === 0);

section('the monitor shows each phase as authored');
const V = (log, t) => fold(mk(log), t).vitals;
let v = V([[1, 'attach_monitor']], 10);
chk('arrival: 128, 94/58, 39.4', v.heart_rate === 128 && v.systolic_bp === 94 && v.diastolic_bp === 58 && v.temperature_c === 39.4, JSON.stringify(v));
v = V(START.concat([[5, 'normal_saline_1l_bolus']]), 14);
chk('still the arrival numbers nine seconds after the bolus', v.systolic_bp === 94, String(v.systolic_bp));
v = V(START.concat([[5, 'normal_saline_1l_bolus']]), 30);
chk('fluid response at ten seconds: 114, 104/62', v.heart_rate === 114 && v.systolic_bp === 104, JSON.stringify(v));
v = V(START.concat([[5, 'normal_saline_1l_bolus']]), 200);
chk('and it fades at 150 seconds: 138, 78/42', v.heart_rate === 138 && v.systolic_bp === 78, JSON.stringify(v));

section('doing nothing');
st = fold(mk([]), 299);
chk('still compensated at 299 seconds', st.phase === 'presentation', st.phase);
st = fold(mk([]), 301);
chk('hypotensive at 300', st.phase === 'hypotensive', st.phase);
chk('the nurse asked for a line and for fluid first',
  st.promptFires.some(p => p.id === 'insert_iv' && p.t < 280) &&
  st.promptFires.some(p => p.id === 'normal_saline_1l_bolus' && p.t <= 280),
  JSON.stringify(st.promptFires));
st = fold(mk([]), 545);
chk('profound shock 240 seconds later', st.phase === 'profound_shock', st.phase);
chk('the nurse asked for norepinephrine in the hypotensive phase first',
  st.promptFires.some(p => p.id === 'norepinephrine_drip' && p.t >= 300 && p.t <= 520),
  JSON.stringify(st.promptFires));
st = fold(mk([]), 3000);
chk('and the case never ends on the clock', st.phase === 'profound_shock' && !st.failed && !st.complete && !st.halted);
chk('normal mode: the fluid prompt still lands before the 300-second exit',
  fold(mk([]), 301, 3).promptFires.some(p => p.id === 'normal_saline_1l_bolus' && p.t < 300),
  JSON.stringify(fold(mk([]), 301, 3).promptFires));

section('each bolus buys less');
const fl = START.concat([[5, 'normal_saline_1l_bolus'], [200, 'normal_saline_1l_bolus']]);
chk('hypotensive baseline 78', V(START.concat([[5, 'normal_saline_1l_bolus']]), 199).systolic_bp === 78);
chk('a further bolus lifts it to 84', V(fl, 201).systolic_bp === 84, String(V(fl, 201).systolic_bp));
chk('for a minute', V(fl, 259).systolic_bp === 84 && V(fl, 261).systolic_bp === 78, String(V(fl, 261).systolic_bp));
chk('and it changes no phase', fold(mk(fl), 300).phase === 'hypotensive');
chk('a third bolus does the same and no more',
  V(fl.concat([[205, 'lactated_ringer_s_1l_bolus']]), 206).systolic_bp === 84,
  String(V(fl.concat([[205, 'lactated_ringer_s_1l_bolus']]), 206).systolic_bp));
chk('fluid alone ends in profound shock',
  fold(mk(fl), 420).phase === 'profound_shock', fold(mk(fl), 420).phase);

section('a vasopressor needs fluid, and fluid needs a vasopressor');
st = fold(mk(START.concat([[305, 'norepinephrine_drip']])), 330);
chk('norepinephrine with no fluid stays hypotensive', st.phase === 'hypotensive', st.phase);
chk('and shows a partial rise, 78 to 86', st.vitals.systolic_bp === 86, String(st.vitals.systolic_bp));
st = fold(mk(START.concat([[305, 'norepinephrine_drip'], [310, 'normal_saline_1l_bolus']])), 325);
chk('add fluid and she is supported ten seconds later', st.phase === 'supported', st.phase);
chk('the bolus still adds six for its minute there, then she is at the authored 92/50',
  st.vitals.systolic_bp === 92 + 6 && fold(mk(START.concat([[305, 'norepinephrine_drip'], [310, 'normal_saline_1l_bolus']])), 400).vitals.systolic_bp === 92,
  String(st.vitals.systolic_bp));
chk('so the nurse quotes no figure for it', !said(st, /92 over 50|98 over 50/));
for (const id of ['epinephrine_drip', 'vasopressin_drip', 'phenylephrine_drip']) {
  st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [170, id]])), 190);
  chk(id + ' counts as the vasopressor', st.phase === 'supported' && st.satisfied.has('norepinephrine_drip'), st.phase);
}
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [170, 'dopamine_drip']])), 190);
chk('dopamine runs as a vasopressor and is discouraged',
  st.phase === 'supported' && st.discouragedTaken.has('dopamine_drip'), st.phase);
chk('and does not satisfy the norepinephrine expectation', !st.satisfied.has('norepinephrine_drip'));

section('a vasopressor started early catches the fade');
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'norepinephrine_drip']])), 150);
chk('nothing changes until the fluid response ends', st.phase === 'fluid_responsive', st.phase);
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'norepinephrine_drip']])), 170);
chk('then supported, never hypotensive', seq(st) === 'presentation > fluid_responsive > supported', seq(st));
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'norepinephrine_drip'],
  [40, 'exam_gu'], [41, 'remove_vaginal_foreign_body']])), 170);
chk('with the source out as well, straight to stabilizing',
  seq(st) === 'presentation > fluid_responsive > stabilizing', seq(st));

section('the source');
st = fold(mk(START.concat([[5, 'remove_vaginal_foreign_body']])), 10);
chk('removal is blocked before the pelvic examination',
  st.blocked.some(b => b.id === 'remove_vaginal_foreign_body') && !st.flags.has('source_removed'));
chk('and the nurse says why', /pelvic exam/.test(st.blocked[0].message), st.blocked[0].message);
st = fold(mk(START.concat([[5, 'exam_gu']])), 10);
chk('the pelvic examination finds the tampon',
  /tampon/i.test(st.readouts.filter(r => r.key === 'exam_gu').pop().body.findings));
st = fold(mk(START.concat([[5, 'exam_gu'], [6, 'remove_vaginal_foreign_body'], [8, 'exam_gu']])), 10);
chk('removal goes through after it', st.flags.has('source_removed'));
chk('and the examination then says it is out',
  /removed/i.test(st.readouts.filter(r => r.key === 'exam_gu').pop().body.findings));
chk('removal alone changes no phase and no vital sign',
  st.phase === 'presentation' && st.vitals.systolic_bp === 94);
const supp = START.concat([[5, 'normal_saline_1l_bolus'], [170, 'norepinephrine_drip']]);
st = fold(mk(supp), 445);
chk('supported with the source in holds for 269 seconds', st.phase === 'supported', st.phase);
st = fold(mk(supp), 455);
chk('and fails at 270', st.phase === 'profound_shock', st.phase + ' ' + seq(st));
chk('after the nurse asked whether anyone had examined her',
  st.promptFires.some(p => p.id === 'remove_vaginal_foreign_body' && p.level === 1) &&
  st.promptFires.some(p => p.id === 'remove_vaginal_foreign_body' && p.level === 2),
  JSON.stringify(st.promptFires));
chk('the source prompt never fires on arrival',
  !fold(mk([]), 299).promptFires.some(p => p.id === 'remove_vaginal_foreign_body'));
st = fold(mk(supp.concat([[200, 'exam_gu'], [201, 'remove_vaginal_foreign_body']])), 215);
chk('source out in the supported phase: stabilizing ten seconds later', st.phase === 'stabilizing', st.phase);
st = fold(mk(supp.concat([[200, 'exam_gu'], [201, 'remove_vaginal_foreign_body']])), 2000);
chk('and she stays there', st.phase === 'stabilizing');
st = fold(mk(supp.concat([[500, 'exam_gu'], [501, 'remove_vaginal_foreign_body']])), 520);
chk('rescue from profound shock', st.phase === 'stabilizing', st.phase);
st = fold(mk(START.concat([[5, 'ct_abdomen']])), 30);
chk('the CT shows an object in the vagina', /vaginal canal/.test(st.orders.ct_abdomen[0].value.report));
st = fold(mk(START.concat([[3, 'exam_gu'], [4, 'remove_vaginal_foreign_body'], [5, 'ct_abdomen']])), 30);
chk('and does not once it has been removed', !/vaginal canal/.test(st.orders.ct_abdomen[0].value.report));

section('antibiotics are scored and move nothing');
const noAbx = fold(mk(START), 100), abx = fold(mk(START.concat([[5, 'vancomycin'], [6, 'clindamycin'], [7, 'cefepime']])), 100);
chk('identical phase and vitals with and without', noAbx.phase === abx.phase && JSON.stringify(noAbx.vitals) === JSON.stringify(abx.vitals));
chk('vancomycin is expected and satisfied', abx.expected.has('vancomycin') && abx.satisfied.has('vancomycin'));
chk('clindamycin is neither expected nor recommended: not scored, on instruction',
  !abx.expected.has('clindamycin') && !abx.recommendedExpected.has('clindamycin'));
chk('a broad beta-lactam costs nothing', !abx.discouragedTaken.has('cefepime') && !abx.discouragedTaken.has('ceftriaxone'));
chk('and does not stand in for vancomycin',
  !fold(mk(START.concat([[5, 'piperacillin_tazobactam']])), 20).satisfied.has('vancomycin'));
chk('the vancomycin prompt names MRSA and fires when nothing has been given',
  fold(mk(START.concat([[5, 'normal_saline_1l_bolus']])), 140).promptFires.some(p => p.id === 'vancomycin'));

section('a discharge that does not end the case');
chk('the intercept is a hidden action', ACT.attempt_discharge && ACT.attempt_discharge.hidden === true);
chk('the only other hidden action is the follow-up target, and neither is on a tab the learner sees',
  Object.keys(ACT).filter(id => ACT[id].hidden).sort().join() === 'attempt_discharge,sedation_after_tube' &&
  ['attempt_discharge', 'sedation_after_tube'].every(id => ACT[id].tab === 'handoff'),
  Object.keys(ACT).filter(id => ACT[id].hidden).join());
st = fold(mk(START), 10);
chk('discharge on arrival is intercepted', handoffIntercept(st, 'discharge_home') === 'attempt_discharge');
chk('intensive care is not', handoffIntercept(st, 'icu') === null);
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus']])), 30);
chk('discharge after one liter is intercepted', handoffIntercept(st, 'discharge_home') === 'attempt_discharge');
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'attempt_discharge']])), 34);
chk('she is still in the room four seconds later', st.phase === 'fluid_responsive' && !st.complete);
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'attempt_discharge']])), 40);
chk('and on the floor at five', st.phase === 'hypotensive', st.phase);
chk('the run is not over', !st.complete && !st.failed && !st.halted && !st.handoff);
chk('the nurse says what happened', said(st, /went straight down/));
chk('it is recorded as discouraged', st.discouragedTaken.has('attempt_discharge'));
chk('a second discharge is an ordinary handoff', handoffIntercept(st, 'discharge_home') === null);
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'attempt_discharge'],
  [50, 'norepinephrine_drip'], [55, 'exam_gu'], [56, 'remove_vaginal_foreign_body']])), 80);
chk('and she can be recovered from it', st.phase === 'stabilizing', st.phase);
st = fold(mk([]), 305);
chk('discharge from the hypotensive phase is not intercepted', handoffIntercept(st, 'discharge_home') === null);
st = fold(mk(START.concat([{ t: 20, actionId: 'handoff_submit',
  payload: { disposition: 'icu', diagnoses: ['dx_toxic_shock_syndrome', 'dx_septic_shock'] } }])), 30);
chk('an ordinary handoff still completes', !!st.complete && st.phase === 'case_complete');

section('the handed-over patient is the patient who was handed over');
st = fold(mk([{ t: 305, actionId: 'handoff_submit',
  payload: { disposition: 'icu', diagnoses: ['dx_toxic_shock_syndrome'] } }]), 320);
chk('handed over hypotensive, shown hypotensive', st.vitals.systolic_bp === 78, JSON.stringify(st.vitals));

section('the traps are visible and recoverable');
st = fold(mk(START.concat([[5, 'metoprolol_bolus']])), 10);
chk('rate control drops the rate and the pressure', st.vitals.heart_rate === 112 && st.vitals.systolic_bp === 82, JSON.stringify(st.vitals));
chk('and wears off', fold(mk(START.concat([[5, 'metoprolol_bolus']])), 190).vitals.systolic_bp === 94);
for (const id of ['esmolol_drip', 'labetalol_bolus', 'diltiazem_bolus', 'propranolol_bolus'])
  chk(id + ' is the same act', fold(mk(START.concat([[5, id]])), 10).discouragedTaken.has(id));
chk('nothing in this case is harmful', HARMFUL.length === 0, HARMFUL.join());
chk('the only terminal phase is the handoff',
  CASE.phases.filter(p => p.terminal).map(p => p.id).join() === 'case_complete');
st = fold(mk(START.concat([[5, 'acetaminophen']])), 40);
chk('acetaminophen lowers the temperature and nothing else',
  st.vitals.temperature_c === 38.8 && st.vitals.heart_rate === 128, JSON.stringify(st.vitals));

section('the second liter');
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus']])), 70);
chk('the nurse asks for it after one bolus', st.fuFires.some(f => f.fid === 'second_liter'));
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'lactated_ringer_s_1l_bolus']])), 120);
chk('and not after two, whichever crystalloid', !st.fuFires.some(f => f.fid === 'second_liter') && st.flags.has('fluids_30mlkg'));
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'norepinephrine_drip']])), 120);
chk('nor once a vasopressor is running', !st.fuFires.some(f => f.fid === 'second_liter'));

section('results follow the patient');
const lac = (log, t) => fold(mk(log), t).orders.lactate.slice(-1)[0].value.components[0].value;
chk('lactate 4.6 on arrival', lac(START.concat([[3, 'lactate']]), 20) === '4.6');
chk('6.8 hypotensive', lac([[1, 'insert_iv'], [305, 'lactate']], 320) === '6.8');
chk('3.8 stabilizing', lac(supp.concat([[200, 'exam_gu'], [201, 'remove_vaginal_foreign_body'], [220, 'lactate']]), 240) === '3.8');
st = fold(mk(START.concat([[3, 'basic_chemistry_chem_7'], [3, 'complete_blood_count_cbc'], [3, 'urinalysis'], [3, 'blood_culture_x_2']])), 20);
chk('creatinine 2.6, flagged', st.orders.basic_chemistry_chem_7[0].value.components.some(c => c.label === 'Creatinine' && c.value === '2.6' && c.abnormal));
chk('platelets 98, flagged', st.orders.complete_blood_count_cbc[0].value.components.some(c => c.label === 'Platelets' && c.value === '98' && c.abnormal));
chk('white cells in the urine with no bacteria and no nitrite',
  st.orders.urinalysis[0].value.components.some(c => c.label === 'WBC' && c.abnormal) &&
  st.orders.urinalysis[0].value.components.some(c => c.label === 'Bacteria' && !c.abnormal) &&
  st.orders.urinalysis[0].value.components.some(c => c.label === 'Nitrite' && !c.abnormal));
chk('blood cultures report no growth', !st.orders.blood_culture_x_2[0].value.abnormal);
chk('every authored study resolved from the case', AUTHORED_STUDIES.every(id =>
  fold(mk([[1, 'insert_iv'], [2, id]]), 30).orders[id][0].source === 'case'));

section('the interview');
const ask = (topic, t) => fold(mk([{ t, kind: 'interview', topic, q: '?' }]), t + 1).readouts.pop().body;
chk('asked about her period, she cannot remember taking the tampon out',
  /can't remember taking it out/.test(ask('menstrual_and_tampon', 5)), ask('menstrual_and_tampon', 5));
chk('the tampon topic is a must-ask and is never volunteered',
  CASE.interview.must_ask.includes('menstrual_and_tampon') &&
  !CASE.interview.topics.some(t => (t.adjacent || []).includes('menstrual_and_tampon')) &&
  !CASE.interview.topics.find(t => t.topic === 'menstrual_and_tampon').volunteer);
chk('no other answer mentions a tampon',
  CASE.interview.topics.filter(t => t.topic !== 'menstrual_and_tampon')
    .every(t => !/tampon/i.test(JSON.stringify(t.answer) + JSON.stringify(t.volunteer || '') + JSON.stringify(t.facts || ''))));
chk('no answer names the diagnosis',
  CASE.interview.topics.every(t => !/toxic shock|sepsis|septic/i.test(JSON.stringify(t.answer) + JSON.stringify(t.facts || ''))));
chk('the arrival handover names neither the fever, the rash nor her period',
  !/fever|rash|red|period|tampon|temperature/i.test(CASE.patient.arrival_handover), CASE.patient.arrival_handover);
chk('her roommate ate the same meal and is well', /roommate/.test(ask('sick_contacts', 5)) && /fine/.test(ask('sick_contacts', 5)));
chk('drowsy, she gives the same fact in fewer words',
  /don't remember taking the last one out/.test(ask('menstrual_and_tampon', 310)), ask('menstrual_and_tampon', 310));
chk('in profound shock she does not answer', /does not answer/.test(ask('onset', 560)), ask('onset', 560));
chk('every topic has a drowsy answer', CASE.interview.topics.every(t => t.answer.length === 2 && /hypotensive/.test(t.answer[0].when)));

section('what the nurse says is true of the monitor');
/* v0.24 audit, finding 1. This section used to compare each narration with the
   destination phase's AUTHORED vitals. The monitor shows those plus every vital effect
   acting, so the nurse said "92 over 50" beside a monitor reading 98 over 50 and the test
   passed. Now: no timed narration quotes a figure, and each direction it states is
   compared with the folded vitals just before and just after it is spoken, on a route for
   each effect that can be acting in the destination. "Pressure" is judged on the mean
   arterial pressure and on the systolic. The two pinned exceptions at the end are the
   stacks where the systolic alone does not follow. */
const MAPV = v => (v.systolic_bp + 2 * v.diastolic_bp) / 3;
const TRN = {};
for (const p of CASE.phases) for (const tr of (p.transitions || []))
  if (tr.narration) (TRN[tr.narration] = TRN[tr.narration] || []).push({ from: p.id, to: tr.to });
const NARR = Object.keys(TRN);
chk('twelve narrations, and none quotes a figure', NARR.length === 12 && NARR.every(n => !/\d/.test(n)),
  NARR.filter(n => /\d/.test(n)).join(' | '));
const HYPO_MEAN = MAPV(CASE.phases.find(p => p.id === 'hypotensive').vitals);
const CLAIMS = [
  [/pressure has dropped|pressure is back down/, 'pressure down',
    (b, a) => MAPV(a) < MAPV(b), (b, a) => a.systolic_bp < b.systolic_bp],
  [/pressure is better|pressure is up|brought her pressure up/, 'pressure up',
    (b, a) => MAPV(a) > MAPV(b), (b, a) => a.systolic_bp > b.systolic_bp],
  [/rate is up|rate is back up|rate is higher/, 'rate up', (b, a) => a.heart_rate > b.heart_rate, null],
  [/rate is down/, 'rate down', (b, a) => a.heart_rate < b.heart_rate, null],
  [/pressure is steady|keeping her pressure up|holding her pressure/, 'mean above the hypotensive phase',
    (b, a) => MAPV(a) > HYPO_MEAN, null],
];
chk('every narration makes at least one claim this section can test',
  NARR.every(n => CLAIMS.some(c => c[0].test(n))), NARR.filter(n => !CLAIMS.some(c => c[0].test(n))).join(' | '));
const ALERT = Object.fromEntries(CASE.phases.map(p => [p.id, p.appearance.alertness_level]));
for (const n of NARR) for (const { from, to } of TRN[n]) {
  if (/more awake|opening her eyes/.test(n)) chk(from + ' to ' + to + ': "more awake" and she is', ALERT[to] < ALERT[from]);
  if (/getting drowsy|gray and drowsy|barely rouse/.test(n)) chk(from + ' to ' + to + ': drowsier, as said', ALERT[to] > ALERT[from]);
}
const heard = new Set();
/* Fold a route, find every timed narration on it, and test each claim it makes against
   the monitor 4 ms either side of it. systolicToo is false only for the pinned stacks. */
function route(name, steps, wantTo, systolicToo) {
  const log = mk(steps), s = fold(log, 1200);
  let last = null;
  for (const x of s.nurse) {
    if (!TRN[x.text]) continue;
    last = x; heard.add(x.text);
    const b = fold(log, x.t - 0.004).vitals, a = fold(log, x.t + 0.004).vitals;
    for (const [re, what, mean, sys] of CLAIMS) if (re.test(x.text)) {
      const ok = mean(b, a) && (systolicToo === false || !sys || sys(b, a));
      chk(name + ' at ' + x.t + ': ' + what, ok,
        '"' + x.text + '" ' + b.heart_rate + ' ' + b.systolic_bp + '/' + b.diastolic_bp + ' then ' +
        a.heart_rate + ' ' + a.systolic_bp + '/' + a.diastolic_bp);
    }
  }
  chk(name + ': reaches ' + wantTo, s.phaseSeq.some(p => p.id === wantTo), seq(s));
  return s;
}
const IV = [[0.5, 'insert_iv']];
const R = (extra) => IV.concat(extra).sort((x, y) => x[0] - y[0]);
/* into fluid_responsive: only rate control can be acting there */
route('first bolus', R([[5.3, 'normal_saline_1l_bolus']]), 'fluid_responsive');
route('rate control, then the first bolus', R([[3.1, 'metoprolol_bolus'], [5.3, 'normal_saline_1l_bolus']]), 'fluid_responsive');
route('rate control while the first bolus runs', R([[5.3, 'normal_saline_1l_bolus'], [9.1, 'diltiazem_bolus']]), 'fluid_responsive');
/* into hypotensive on the 300-second clock: a vasopressor without fluid, a push dose, rate control */
route('nothing', [], 'profound_shock');
route('a vasopressor on arrival and no fluid', R([[250.5, 'norepinephrine_drip']]), 'profound_shock');
route('vasopressin on arrival and no fluid', R([[250.5, 'vasopressin_drip']]), 'profound_shock');
route('a push dose before the 300-second clock', R([[280.25, 'phenylephrine_bolus']]), 'hypotensive');
route('rate control acting across the 300-second clock', R([[200.5, 'metoprolol_bolus']]), 'hypotensive');
route('rate control that has just worn off at the 300-second clock', R([[119.9, 'metoprolol_bolus']]), 'hypotensive');
/* the faint, from both phases, with a bolus, a push dose, a vasopressor and rate control */
route('discharge on arrival', R([[8.1, 'attempt_discharge']]), 'hypotensive');
route('a bolus, then discharge three seconds later', R([[5.3, 'normal_saline_1l_bolus'], [8.4, 'attempt_discharge']]), 'hypotensive');
route('a bolus, then discharge from the fluid-responsive phase', R([[5.3, 'normal_saline_1l_bolus'], [30.4, 'attempt_discharge']]), 'hypotensive');
route('a push dose, then discharge', R([[5.2, 'phenylephrine_bolus'], [8.1, 'attempt_discharge']]), 'hypotensive');
route('a vasopressor with no fluid, then discharge', R([[5.2, 'norepinephrine_drip'], [8.1, 'attempt_discharge']]), 'hypotensive');
route('rate control, then discharge', R([[5.2, 'metoprolol_bolus'], [8.1, 'attempt_discharge']]), 'hypotensive');
/* the fade, three ways out of fluid_responsive (entered at 15.3, fades at 165.3) */
const FR = [[5.3, 'normal_saline_1l_bolus']];
route('the fade with a second bolus running', R(FR.concat([[140.6, 'lactated_ringer_s_1l_bolus']])), 'hypotensive');
route('the fade with a push dose on board', R(FR.concat([[150.7, 'phenylephrine_bolus']])), 'hypotensive');
route('the fade with rate control on board', R(FR.concat([[100.3, 'metoprolol_bolus']])), 'hypotensive');
const FRP = FR.concat([[30.2, 'norepinephrine_drip']]);
route('caught by a vasopressor', R(FRP), 'supported');
route('caught by a vasopressor, second bolus running', R(FRP.concat([[150.2, 'normal_saline_1l_bolus']])), 'supported');
route('caught by a vasopressor, push dose on board', R(FRP.concat([[140.7, 'phenylephrine_bolus']])), 'supported');
route('caught by a vasopressor, rate control on board', R(FRP.concat([[100.3, 'esmolol_drip']])), 'supported');
const FRPS = FRP.concat([[40, 'exam_gu'], [41.5, 'remove_vaginal_foreign_body']]);
route('everything done early', R(FRPS), 'stabilizing');
route('everything done early, rate control on board', R(FRPS.concat([[120.4, 'metoprolol_bolus']])), 'stabilizing');
/* out of hypotensive, entered at 300 */
route('vasopressor then bolus, the bolus still acting', R([[305.2, 'norepinephrine_drip'], [310.4, 'normal_saline_1l_bolus']]), 'supported');
route('second bolus then vasopressor after the fade', R(FR.concat([[170.1, 'normal_saline_1l_bolus'], [175.6, 'norepinephrine_drip']])), 'supported');
route('vasopressor, push dose, then bolus', R([[305.2, 'norepinephrine_drip'], [306.1, 'phenylephrine_bolus'], [310.4, 'normal_saline_1l_bolus']]), 'supported');
route('vasopressor, rate control, then bolus', R([[305.2, 'norepinephrine_drip'], [307.3, 'metoprolol_bolus'], [310.4, 'normal_saline_1l_bolus']]), 'supported');
const SRC = [[301.2, 'exam_gu'], [302.6, 'remove_vaginal_foreign_body']];
route('source out, vasopressor, then bolus', R(SRC.concat([[305.2, 'norepinephrine_drip'], [310.4, 'normal_saline_1l_bolus']])), 'stabilizing');
route('source out, vasopressor, push dose, then bolus', R(SRC.concat([[305.2, 'norepinephrine_drip'], [306.1, 'phenylephrine_bolus'], [310.4, 'normal_saline_1l_bolus']])), 'stabilizing');
route('source out, vasopressor, rate control, then bolus', R(SRC.concat([[305.2, 'norepinephrine_drip'], [307.3, 'labetalol_bolus'], [310.4, 'normal_saline_1l_bolus']])), 'stabilizing');
/* into profound shock on the 240-second clock */
route('a vasopressor in the hypotensive phase and no fluid', R([[305.2, 'norepinephrine_drip']]), 'profound_shock');
route('fluid alone, a bolus still acting at the 240-second clock', R([[530.3, 'normal_saline_1l_bolus']]), 'profound_shock');
route('a push dose acting at the 240-second clock', R([[500.3, 'phenylephrine_bolus']]), 'profound_shock');
route('rate control acting at the 240-second clock', R([[400.3, 'metoprolol_bolus']]), 'profound_shock');
/* out of supported (entered at 165.3): the source, or the 270-second clock at 435.3 */
route('source out with a bolus and a push dose on board', R(FRP.concat([[200, 'exam_gu'], [228.4, 'normal_saline_1l_bolus'], [229.1, 'phenylephrine_bolus'], [230.5, 'remove_vaginal_foreign_body']])), 'stabilizing');
route('source out with rate control on board', R(FRP.concat([[200, 'exam_gu'], [229.1, 'metoprolol_bolus'], [230.5, 'remove_vaginal_foreign_body']])), 'stabilizing');
route('source missed, a third bolus acting', R(FRP.concat([[420.3, 'normal_saline_1l_bolus']])), 'profound_shock');
route('source missed, a push dose acting', R(FRP.concat([[400.3, 'phenylephrine_bolus']])), 'profound_shock');
route('source missed, rate control acting', R(FRP.concat([[300.3, 'metoprolol_bolus']])), 'profound_shock');
/* out of profound shock */
route('rescue from profound shock, bolus still acting', R([[545.2, 'exam_gu'], [546.6, 'remove_vaginal_foreign_body'], [550.2, 'norepinephrine_drip'], [551.4, 'normal_saline_1l_bolus']]), 'stabilizing');
route('rescue from profound shock, rate control on board', R([[545.2, 'exam_gu'], [546.6, 'remove_vaginal_foreign_body'], [548.3, 'metoprolol_bolus'], [550.2, 'norepinephrine_drip'], [551.4, 'normal_saline_1l_bolus']]), 'stabilizing');
chk('every one of the twelve narrations was heard on at least one route', NARR.every(n => heard.has(n)),
  NARR.filter(n => !heard.has(n)).join(' | '));
/* Known limit, pinned. Two vasopressor effects stacked with no fluid lift the systolic
   above the arrival figure while the diastolic and the mean fall. The line is true of the
   mean and not of the systolic. Recorded in TSS-SEED.md. */
st = route('known limit: vasopressor and push dose, no fluid, at the 300-second clock',
  R([[250.5, 'norepinephrine_drip'], [280.25, 'phenylephrine_bolus']]), 'hypotensive', false);
v = V(R([[250.5, 'norepinephrine_drip'], [280.25, 'phenylephrine_bolus']]), 301);
chk('known limit: the monitor reads 98 over 42 against 94 over 58 on arrival', v.systolic_bp === 98 && v.diastolic_bp === 42, JSON.stringify(v));
route('known limit: vasopressor and push dose, no fluid, then discharge',
  R([[5.2, 'norepinephrine_drip'], [6.3, 'phenylephrine_bolus'], [8.1, 'attempt_discharge']]), 'hypotensive', false);

section('the nurse names the class, because a covered sibling can be the drug running');
const NOREPI = /norepinephrine|levophed/i;
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'vasopressin_drip']])), 500);
chk('vasopressin ordered: the nurse never says norepinephrine is running',
  st.nurse.filter(n => n.kind !== 'prompt').every(n => !NOREPI.test(n.text)),
  st.nurse.filter(n => n.kind !== 'prompt' && NOREPI.test(n.text)).map(n => n.text).join(' | '));
chk('and the alert names the vasopressor', said(st, /^The vasopressor is running/));
chk('no narration, phase label or short label names norepinephrine',
  CASE.phases.every(p => !NOREPI.test(p.label + ' ' + p.short_label) && (p.transitions || []).every(tr => !NOREPI.test(tr.narration || ''))));
chk('no status line names it', CASE.content_keys.general_status.rules.every(r => !NOREPI.test(r.value.findings)));
chk('a consultant names it only as advice to start it',
  Object.keys(CASE.content_keys.consultants).filter(k => k !== 'authoring_note')
    .every(k => CASE.content_keys.consultants[k].every(r => !/norepinephrine running|on norepinephrine/i.test(r.value))));
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, 'vasopressin_drip']])), 200);
chk('the status line in the supported phase says a vasopressor is running',
  st.phase === 'supported' && /Vasopressor running/.test(generalStatus(st).value.findings), generalStatus(st).value.findings);
chk('and the monitor chip reads "on a vasopressor"', CASE.phases.find(p => p.id === 'supported').short_label === 'on a vasopressor');

section('stopping a vasopressor');
st = fold(mk(START.concat([[5, 'stop_norepinephrine'], [6, 'stop_vasopressin'], [7, 'stop_dopamine']])), 10);
chk('with nothing running every stop entry is blocked', st.blocked.length === 3 && st.blocked.every(b => /no vasopressor running/.test(b.message)), JSON.stringify(st.blocked));
chk('and nothing is scored', st.discouragedTaken.size === 0, [...st.discouragedTaken].join());
chk('and the nurse does not say she left anything running', !said(st, /left it running/));
for (const [start, stop] of [['norepinephrine_drip', 'stop_norepinephrine'], ['vasopressin_drip', 'stop_vasopressin'],
  ['epinephrine_drip', 'stop_epinephrine'], ['phenylephrine_drip', 'stop_phenylephrine'], ['dopamine_drip', 'stop_dopamine'],
  ['vasopressin_drip', 'stop_norepinephrine']]) {
  st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [30, start], [200.5, stop]])), 260);
  chk(start + ' then ' + stop + ': refused, scored, still supported',
    st.discouragedTaken.has(stop) && st.flags.has('pressor_running') && st.phase === 'supported' && said(st, /left it running/) &&
    !said(st, /^Stopping/), st.phase + ' ' + [...st.discouragedTaken].join());
}

section('routes the audit found unbound');
for (const id of ['digoxin_bolus', 'amiodarone_bolus_infusion']) {
  st = fold(mk(START.concat([[5, id]])), 10);
  chk(id + ' is rate control: discouraged, with the same effect',
    st.discouragedTaken.has(id) && st.vitals.heart_rate === 112 && st.vitals.systolic_bp === 82, JSON.stringify(st.vitals));
}
chk('two rate-controlling drugs do not stack',
  fold(mk(START.concat([[5, 'metoprolol_bolus'], [6, 'digoxin_bolus']])), 10).vitals.heart_rate === 112);
chk('adenosine is unbound and unscored, by a recorded open question', !ACT.adenosine_bolus.bound && !ACT.adenosine_bolus.covered_by);
for (const id of ['normal_saline_infusion', 'lactated_ringer_s_infusion']) {
  st = fold(mk(START.concat([[5, id]])), 301);
  chk(id + ' is not a bolus: no flag, no credit, and she still deteriorates at 300',
    !st.flags.has('fluids_given') && !st.satisfied.has('normal_saline_1l_bolus') && st.phase === 'hypotensive' &&
    !st.discouragedTaken.has(id), st.phase);
  chk(id + ': the nurse says so', said(st, /maintenance rate\. It isn't a bolus/));
  chk(id + ': and still asks for a bolus', st.promptFires.some(p => p.id === 'normal_saline_1l_bolus'));
}
st = fold(mk(START.concat([[5, 'cefotaxime']])), 10);
chk('cefotaxime is broad cover: unpenalized, and not vancomycin',
  st.flags.has('broad_cover_given') && !st.discouragedTaken.has('cefotaxime') && !st.satisfied.has('vancomycin'));
const BMAP = JSON.parse(fs.readFileSync(path.join(ROOT, 'cases', 'TSS', 'TSS-binding-map.json'), 'utf8')).rows;
const brow = id => BMAP.find(r => r.case_id === id) || {};
chk('furosemide is bound through the loop diuretic group', brow('furosemide_40_mg_iv').also_covers_group === 'loop_diuretic');
chk('the stop row covers the stop entry of every infusion that sets the vasopressor flag',
  ['stop_epinephrine', 'stop_vasopressin', 'stop_phenylephrine', 'stop_dopamine'].every(id => brow('stop_norepinephrine').also_covers.includes(id)) &&
  CASE.case_actions.filter(a => (a.flags_set || []).includes('pressor_running')).map(a => a.catalog_id).sort().join() === 'dopamine_drip,norepinephrine_drip');
chk('furosemide is discouraged', fold(mk(START.concat([[5, 'furosemide_40_mg_iv']])), 10).discouragedTaken.has('furosemide_40_mg_iv'));
const SPO2 = (steps, t) => fold(mk(steps), t).vitals.oxygen_saturation;
const O2R = ['nasal_cannula_oxygen', 'non_rebreather_mask', 'bag_valve_mask', 'non_invasive_positive_pressure_ventilation'];
chk('all four oxygen routes share one effect key',
  O2R.every(id => (ACT[id].vital_effects || []).length === 1 && ACT[id].vital_effects[0].key === 'oxygen_support'));
chk('no oxygen route adds anything on arrival', O2R.every(id => SPO2([[5, id]], 10) === 97));
chk('hypotensive: 95, 97 on a cannula, 99 on a mask, a bag or non-invasive ventilation',
  SPO2([], 310) === 95 && SPO2([[305, 'nasal_cannula_oxygen']], 310) === 97 && SPO2([[305, 'non_rebreather_mask']], 310) === 99 &&
  SPO2([[305, 'bag_valve_mask']], 310) === 99 && SPO2([[305, 'non_invasive_positive_pressure_ventilation']], 310) === 99);
chk('and all four together are still 99, not stacked',
  SPO2(O2R.map((id, i) => [305 + i, id]), 312) === 99, String(SPO2(O2R.map((id, i) => [305 + i, id]), 312)));
st = fold(mk([[305, 'nasal_cannula_oxygen']]), 310);
chk('oxygen is recommended once she is hypotensive, as its note says', st.recommendedExpected.has('nasal_cannula_oxygen') || st.recommendedTaken.has('nasal_cannula_oxygen'));

section('every authored study has a case action and a note');
const ABN = AUTHORED_STUDIES.filter(id => (CASE.content_keys.labs[id] || CASE.content_keys.imaging[id]).rules.some(r => r.value.abnormal));
chk('every study with an authored abnormal result (' + ABN.length + ') has one',
  ABN.length === 16 && ABN.every(id => CASE.case_actions.some(a => a.catalog_id === id && a.debrief_note)),
  ABN.filter(id => !CASE.case_actions.some(a => a.catalog_id === id && a.debrief_note)).join());
const PANELS = AUTHORED_STUDIES.map(id => (CASE.content_keys.labs[id] || CASE.content_keys.imaging[id]).rules).flat().map(r => r.value);
chk('no result comment names the diagnosis, her period or the reviewer',
  PANELS.every(vv => !/toxic shock|sepsis|period|menstrual|simplification|the case shows/i.test(vv.comment || '')),
  PANELS.filter(vv => /toxic shock|sepsis|period|menstrual|simplification|the case shows/i.test(vv.comment || '')).map(vv => vv.comment).join(' | '));
chk('no report carries a comment, because a report comment is never shown', PANELS.every(vv => vv.kind !== 'report' || !vv.comment));
st = fold(mk(START.concat([[3, 'ultrasound_fast'], [3.5, 'ct_abdomen'], [4, 'skin_biopsy_of_the_rash']])), 40);
chk('the FAST agrees with the CT about free pelvic fluid',
  /free fluid in the pelvis/.test(st.orders.ultrasound_fast[0].value.report) && /free pelvic fluid/.test(st.orders.ct_abdomen[0].value.report) &&
  st.orders.ultrasound_fast[0].source === 'case');
chk('the skin biopsy says it was taken and gives no result',
  /taken/.test(st.orders.skin_biopsy_of_the_rash[0].value.report) && !/Not applicable/.test(st.orders.skin_biopsy_of_the_rash[0].value.report));
const abgSat = p => CASE.content_keys.labs.arterial_blood_gas.rules.find(r => (r.when || 'phase is presentation') === 'phase is ' + p)
  .value.components.find(c => c.label === 'O2 saturation').value;
chk('the arterial saturation is the phase saturation in every phase',
  CASE.phases.filter(p => !p.terminal).every(p => +abgSat(p.id) === p.vitals.oxygen_saturation));
chk('the monitor trace carries the PR interval the ECG report gives',
  CASE.phases.every(p => p.ecg.pr_ms === 140) && /PR 140 ms/.test(CASE.content_keys.imaging.ecg_12_lead.rules[0].value.report));

section('verification markers sit only where the interface strips them');
const MARK = /\[(UNVERIFIED|PubMed|VERIFY|MODEL OUTPUT)/;
const strippable = new Set();
for (const a of CASE.case_actions) { strippable.add(a.debrief_note); (a.references || []).forEach(r => strippable.add(r)); }
for (const p of CASE.phases) for (const tr of (p.transitions || [])) strippable.add(tr.debrief_note);
(CASE.debrief_configuration.cross_cutting_teaching_points || []).forEach(x => strippable.add(x));
const leaked = [];
(function walk(o, key) {
  if (typeof o === 'string') { if (MARK.test(o) && !strippable.has(o) && !/^(verify|author_note|note|.*_note|.*rationale)$/.test(key || '')) leaked.push(key + ': ' + o.slice(0, 60)); return; }
  if (Array.isArray(o)) return o.forEach(x => walk(x, key));
  if (o && typeof o === 'object') for (const k in o) if (k !== 'provenance') walk(o[k], k);
})(CASE, '');
chk('no marker is printed to the learner', leaked.length === 0, leaked.join(' | '));
for (const id of ['cefazolin', 'dopamine_drip', 'lactate', 'ct_abdomen', 'intravenous_immunoglobulin', 'hydrocortisone_bolus', 'clindamycin', 'vancomycin', 'urinalysis'])
  chk(id + ' carries a marker', MARK.test(ACT[id].debrief_note));
chk('the provenance block lists each reference with how it was read',
  Array.isArray(CASE.provenance.reference_status) && CASE.provenance.reference_status.length >= 6 &&
  CASE.provenance.reference_status.every(r => r.reference && r.how_read && r.status));

section('consultants claim only what was done');
const consult = (steps, t, id) => fold(mk(steps.concat([[t, id]])), t + 1).readouts.pop().body;
chk('on arrival with a vasopressor and the source out, the intensivist does not say fluid is in',
  !/Fluid in/.test(consult(START.concat([[3, 'exam_gu'], [4, 'remove_vaginal_foreign_body'], [5, 'norepinephrine_drip']]), 8, 'consult_critical_care')) &&
  /Has she had fluid/.test(consult(START.concat([[3, 'exam_gu'], [4, 'remove_vaginal_foreign_body'], [5, 'norepinephrine_drip']]), 8, 'consult_critical_care')));
chk('with all three done the intensivist says so, and names a vasopressor',
  /Fluid in, a vasopressor running, source out/.test(consult(supp.concat([[200, 'exam_gu'], [201, 'remove_vaginal_foreign_body']]), 230, 'consult_critical_care')));
chk('and asks for a lactate without saying one was sent',
  !/repeat lactate/.test(consult(supp.concat([[200, 'exam_gu'], [201, 'remove_vaginal_foreign_body']]), 230, 'consult_critical_care')));
chk('in profound shock on the do-nothing path the intensivist does not say Good and claims no treatment',
  /obtunded/.test(consult([], 560, 'consult_critical_care')) && !/Good|Fluid in|running/.test(consult([], 560, 'consult_critical_care')),
  consult([], 560, 'consult_critical_care'));
chk('a vasopressor alone: told it is not enough without fluid',
  /no fluid behind it/.test(consult(START.concat([[5, 'vasopressin_drip']]), 8, 'consult_critical_care')));
chk('no consultant line quotes a laboratory value',
  Object.keys(CASE.content_keys.consultants).filter(k => k !== 'authoring_note').every(k =>
    CASE.content_keys.consultants[k].every(r => !/\d/.test(r.value.replace(/22-year-old|30 per kilo|65/g, '')))));
chk('nephrology asks for a chemistry when none was sent', /Send a chemistry/.test(consult(START, 5, 'consult_renal')));
chk('says it is not back while it is pending', /isn't back/.test(consult(START.concat([[5, 'basic_chemistry_chem_7']]), 6.5, 'consult_renal')));
chk('and advises once it has resulted, quoting no value',
  /not being perfused/.test(consult(START.concat([[5, 'basic_chemistry_chem_7']]), 20, 'consult_renal')) &&
  !/\d/.test(consult(START.concat([[5, 'basic_chemistry_chem_7']]), 20, 'consult_renal')));

section('prompts are true in every phase their guards allow');
const PT = id => ACT[id].prompt;
chk('the source prompt claims no fluid and no drug',
  !/given her fluid|norepinephrine|turn it up/.test(PT('remove_vaginal_foreign_body').text + PT('remove_vaginal_foreign_body').escalation.text));
st = fold(mk([]), 615);
chk('on the do-nothing path it is spoken in profound shock to a patient given nothing, and is true',
  st.promptFires.some(p => p.id === 'remove_vaginal_foreign_body' && p.t === 600) && said(st, /no source has been dealt with/) &&
  !st.flags.has('fluids_given') && !st.flags.has('pressor_running'));
chk('neither fluid line says what is about to happen',
  !/going to/.test(PT('normal_saline_1l_bolus').text + PT('normal_saline_1l_bolus').escalation.text + PT('norepinephrine_drip').text + PT('norepinephrine_drip').escalation.text));
for (const [name, steps] of [['nothing', []], ['a push dose and a bolus', [[1, 'insert_iv'], [410, 'phenylephrine_bolus'], [415, 'normal_saline_1l_bolus']]],
  ['dopamine without fluid', [[1, 'insert_iv'], [305, 'dopamine_drip']]]]) {
  const s = fold(mk(steps), 421), esc = s.promptFires.find(p => p.id === 'norepinephrine_drip' && p.level === 2);
  chk(name + ': when the vasopressor escalation says the mean is still under 65, it is',
    !!esc && MAPV(fold(mk(steps), esc.t).vitals) < 65, JSON.stringify(esc));
}
st = fold(mk([[1, 'second_iv']]), 100);
chk('the line prompt is not spoken to a patient who has a line through Second IV',
  !st.promptFires.some(p => p.id === 'insert_iv') && !said(st, /got no line/));
st = fold(mk(START.concat([[5, 'normal_saline_1l_bolus'], [20, 'metoprolol_bolus'], [30, 'attempt_discharge']])), 31);
chk('the discharge line holds after a liter and rate control: rate 98, still febrile',
  st.vitals.heart_rate === 98 && st.vitals.temperature_c > 38 && said(st, /still has a fever/) && !said(st, /rate is still fast/), JSON.stringify(st.vitals));

section('the default mode: every warning still comes before its deterioration');
/* Authoring 7.4. Normal is the mode a learner starts in and multiplies every prompt
   deadline by three. Deteriorations are not multiplied. The fluid prompt was at 80, which
   is 240 in this mode, the instant the hypotensive phase ends. */
const fired = (s, id, level, before) => s.promptFires.find(p => p.id === id && p.level === level && p.t < before);
st = fold(mk([]), 301.5, 3);
chk('300-second clock, nothing done: the fluid warning comes at 180, with 120 seconds left',
  !!fired(st, 'normal_saline_1l_bolus', 1, 300) && fired(st, 'normal_saline_1l_bolus', 1, 300).t === 180 && st.phase === 'hypotensive',
  JSON.stringify(st.promptFires));
chk('and the monitor and the line were asked for before it',
  !!fired(st, 'attach_monitor', 1, 180) && !!fired(st, 'insert_iv', 1, 180));
st = fold(mk([]), 541.5, 3);
chk('240-second clock, nothing done: vasopressor at 390 and fluid at 480, both before 540',
  !!fired(st, 'norepinephrine_drip', 1, 540) && st.promptFires.some(p => p.id === 'normal_saline_1l_bolus' && p.t === 480) && st.phase === 'profound_shock',
  JSON.stringify(st.promptFires));
st = fold(mk(START.concat([[305.5, 'norepinephrine_drip']])), 541.5, 3);
chk('240-second clock, vasopressor and no fluid: she is told fluid is missing 60 seconds before',
  st.promptFires.some(p => p.id === 'normal_saline_1l_bolus' && p.t === 480) && st.phase === 'profound_shock', JSON.stringify(st.promptFires));
st = fold(mk(START.concat([[5.5, 'normal_saline_1l_bolus']])), 406.5, 3);
chk('240-second clock, fluid and no vasopressor: the vasopressor warning comes 150 seconds before',
  st.promptFires.some(p => p.id === 'norepinephrine_drip' && Math.abs(p.t - 255.5) < 1e-6) && st.phase === 'profound_shock', JSON.stringify(st.promptFires));
st = fold(mk(START.concat([[5.5, 'normal_saline_1l_bolus'], [30.5, 'norepinephrine_drip']])), 436.5, 3);
chk('270-second clock, source missed: the source warning comes 90 seconds before',
  st.promptFires.some(p => p.id === 'remove_vaginal_foreign_body' && p.level === 1 && Math.abs(p.t - 345.5) < 1e-6) && st.phase === 'profound_shock',
  JSON.stringify(st.promptFires));
for (const [id, dl, exit] of [['normal_saline_1l_bolus', 60, 240], ['norepinephrine_drip', 30, 240], ['remove_vaginal_foreign_body', 60, 270]])
  chk(id + ': three times its deadline is strictly less than the ' + exit + '-second exit, with at least 60 seconds to act',
    ACT[id].prompt.deadline_seconds === dl && 3 * dl <= exit - 60);
chk('recorded limit: in the default mode no escalation is heard before the exit it warns about',
  [fold(mk([]), 541.5, 3), fold(mk(START.concat([[5.5, 'normal_saline_1l_bolus'], [30.5, 'norepinephrine_drip']])), 436.5, 3)]
    .every(s => !s.promptFires.some(p => p.level === 2)));
st = fold(mk(START.concat([[5.5, 'normal_saline_1l_bolus']])), 200, 3);
chk('recorded limit: in the default mode the second-liter follow-up comes after the fade',
  st.fuFires.some(f => f.fid === 'second_liter' && Math.abs(f.t - 185.5) < 1e-6) && st.phaseSeq.some(p => p.id === 'hypotensive' && p.t === 165.5),
  JSON.stringify(st.fuFires));
for (const m of [1, 3]) {
  st = fold(mk(START.concat([[5.5, 'normal_saline_1l_bolus']])), 164, m);
  chk('recorded decision: the fade is not warned about, mode x' + m,
    st.phase === 'fluid_responsive' && !st.promptFires.some(p => p.id === 'norepinephrine_drip'), JSON.stringify(st.promptFires));
}

section('two timed rules pending at once, on both sides of each boundary');
/* Authoring 15.4. One check per row of the table in TSS-SEED.md. */
const at = (steps, t) => { const s = fold(mk(steps), t); return s.phaseSeq.map(p => p.id + '@' + p.t).join(' > '); };
const B5 = [[1, 'insert_iv'], [20.2, 'normal_saline_1l_bolus']];
chk('bolus, discharge 3.7 seconds later: the faint comes first', at(B5.concat([[23.9, 'attempt_discharge']]), 60) === 'presentation@0 > hypotensive@28.9', at(B5.concat([[23.9, 'attempt_discharge']]), 60));
chk('bolus, discharge exactly 5 seconds later: both due together, the faint is listed first and wins', at(B5.concat([[25.2, 'attempt_discharge']]), 60) === 'presentation@0 > hypotensive@30.2', at(B5.concat([[25.2, 'attempt_discharge']]), 60));
chk('bolus, discharge 6.2 seconds later: the fluid response first, then the faint 5 seconds into it', at(B5.concat([[26.4, 'attempt_discharge']]), 60) === 'presentation@0 > fluid_responsive@30.2 > hypotensive@35.2', at(B5.concat([[26.4, 'attempt_discharge']]), 60));
st = fold(mk([[294.7, 'attempt_discharge']]), 310);
chk('discharge 5.3 seconds before the 300-second clock: she faints at 299.7', seq(st) === 'presentation > hypotensive' && st.phaseSeq[1].t === 299.7 && said(st, /went straight down/));
st = fold(mk([[296.3, 'attempt_discharge']]), 310);
chk('known limit: discharge 3.7 seconds before it: the clock fires first and the faint is never narrated',
  st.phaseSeq[1].t === 300 && !said(st, /went straight down/) && said(st, /gone gray/) && st.discouragedTaken.has('attempt_discharge'));
chk('a bolus 0.4 seconds before the 300-second clock rescues her', at([[1, 'insert_iv'], [299.6, 'normal_saline_1l_bolus']], 320) === 'presentation@0 > fluid_responsive@309.6');
chk('a bolus 0.4 seconds after it is one action too late', at([[1, 'insert_iv'], [300.4, 'normal_saline_1l_bolus']], 320) === 'presentation@0 > hypotensive@300');
const F5 = [[1, 'insert_iv'], [5.3, 'normal_saline_1l_bolus']];
chk('discharge 5.4 seconds before the fade: the faint comes first', at(F5.concat([[159.9, 'attempt_discharge']]), 200) === 'presentation@0 > fluid_responsive@15.3 > hypotensive@164.9', at(F5.concat([[159.9, 'attempt_discharge']]), 200));
st = fold(mk(F5.concat([[30, 'norepinephrine_drip'], [161.1, 'attempt_discharge']])), 400);
chk('known limit: discharge 4.2 seconds before the fade with a vasopressor running: supported, and she never faints',
  seq(st) === 'presentation > fluid_responsive > supported' && !said(st, /went straight down/) && handoffIntercept(st, 'discharge_home') === null, seq(st));
chk('a vasopressor 0.4 seconds before the fade catches it', at(F5.concat([[164.9, 'norepinephrine_drip']]), 200) === 'presentation@0 > fluid_responsive@15.3 > supported@165.3');
chk('a vasopressor 0.4 seconds after it finds her hypotensive, and holds her 10 seconds later', at(F5.concat([[165.7, 'norepinephrine_drip']]), 200) === 'presentation@0 > fluid_responsive@15.3 > hypotensive@165.3 > supported@175.7');
const H5 = [[1, 'insert_iv'], [305, 'norepinephrine_drip']];
chk('the second half of the pair 0.4 seconds before the 240-second clock rescues her', at(H5.concat([[539.6, 'normal_saline_1l_bolus']]), 600) === 'presentation@0 > hypotensive@300 > supported@549.6');
chk('and 0.4 seconds after it is one action too late', at(H5.concat([[540.4, 'normal_saline_1l_bolus']]), 600) === 'presentation@0 > hypotensive@300 > profound_shock@540');
chk('source out 4.2 seconds into the 10-second wait: supported first, then stabilizing 10 seconds on',
  at(H5.concat([[310, 'normal_saline_1l_bolus'], [311, 'exam_gu'], [314.2, 'remove_vaginal_foreign_body']]), 400) === 'presentation@0 > hypotensive@300 > supported@320 > stabilizing@330');
const S5 = F5.concat([[30, 'norepinephrine_drip'], [40, 'exam_gu']]);
chk('source out 0.4 seconds before the 270-second clock rescues her', at(S5.concat([[434.9, 'remove_vaginal_foreign_body']]), 500) === 'presentation@0 > fluid_responsive@15.3 > supported@165.3 > stabilizing@444.9');
chk('and 0.4 seconds after it she is in profound shock first, and out 15 seconds later', at(S5.concat([[435.7, 'remove_vaginal_foreign_body']]), 500) === 'presentation@0 > fluid_responsive@15.3 > supported@165.3 > profound_shock@435.3 > stabilizing@450.7');

section('sedation after the tube, both ways round');
const TUBE = [[1, 'insert_iv'], [5, 'etomidate_bolus'], [6, 'rocuronium_bolus'], [7.5, 'intubate_rapid_sequence']];
const asked = steps => fold(mk(steps.slice().sort((x, y) => x[0] - y[0])), 200).fuFires.some(f => f.fid === 'post_intubation_sedation');
chk('nothing given: the nurse asks', asked(TUBE));
chk('fentanyl before the tube does not discharge it', asked(TUBE.concat([[4, 'fentanyl_bolus']])));
chk('fentanyl after the tube does', !asked(TUBE.concat([[20.5, 'fentanyl_bolus']])));
chk('midazolam as the induction dose does not', asked([[1, 'insert_iv'], [5, 'midazolam_bolus'], [6, 'rocuronium_bolus'], [7.5, 'intubate_rapid_sequence']]));
for (const id of ['midazolam_bolus', 'lorazepam_bolus', 'morphine_bolus'])
  chk(id + ' after the tube does', !asked(TUBE.concat([[30.5, id]])));
chk('an infusion started before the tube is still running and counts', !asked(TUBE.concat([[4, 'propofol_infusion']])));
chk('an infusion started after it counts', !asked(TUBE.concat([[50.5, 'ketamine_infusion']])));
chk('triggered_by matches the action that lists the follow-up',
  CASE.follow_ups.every(f => CASE.case_actions.filter(a => (a.follow_ups_triggered || []).includes(f.id)).map(a => a.catalog_id).join() === [].concat(f.triggered_by).join()));

section('the words the nurse and the consultants use reach the pelvic examination');
{
  const vf = html.match(/\/\*__VOICE_START__\*\/([\s\S]*?)\/\*__VOICE_END__\*\//);
  const VD = grab('voice-data');
  const VOICE = eval(vf[1] + '\n;VOICE');
  VOICE.build(VD);
  const okIds = t => VOICE.parse(t).filter(r => r.kind === 'ok').map(r => r.id);
  for (const t of ['pelvic exam', 'pelvic examination', 'do a pelvic exam', 'do the pelvic exam first', 'speculum exam'])
    chk('"' + t + '" orders the genitourinary examination and no film',
      okIds(t).join() === 'exam_gu' && !VOICE.parse(t).some(r => (r.ids || []).includes('xr_pelvis')), JSON.stringify(VOICE.parse(t)));
  const said2 = [ACT.remove_vaginal_foreign_body.prompt.text, ACT.remove_vaginal_foreign_body.prerequisites.map(p => p.failure_message).join(' '),
    CASE.content_keys.consultants.consult_ob_gyn.map(r => r.value).join(' '), CASE.content_keys.consultants.consult_critical_care.map(r => r.value).join(' ')].join(' ');
  chk('every time the pack says "pelvic" aloud it says "pelvic exam"',
    (said2.match(/pelvic/g) || []).length > 0 && (said2.match(/pelvic/g) || []).length === (said2.match(/pelvic exam/g) || []).length, said2.match(/.{12}pelvic.{8}/g).join(' | '));
  const bare = VOICE.parse('do a pelvic');
  chk('a bare "pelvic" is offered as a choice that includes the examination, and orders nothing by itself',
    bare.length === 1 && bare[0].kind === 'ambiguous' && bare[0].ids.includes('exam_gu'), JSON.stringify(bare));
  chk('"remove the tampon" reaches the removal', okIds('remove the tampon').join() === 'remove_vaginal_foreign_body');
  chk('"discharge home" orders nothing', okIds('discharge home').length === 0, JSON.stringify(VOICE.parse('discharge home')));
}

section('the interview after the audit');
chk('the out-of-scope bank holds no question a topic owns',
  CASE.interview.out_of_scope_bank.every(q => !CASE.interview.topics.some(t => [t.canonical].concat(t.variants, t.expanded_variants || []).includes(q))));
for (const q of ['Any nosebleeds?', 'Any back pain?', 'Any cramps in your legs?', 'Any blood when you open your bowels?', 'What do you do for a living?'])
  chk('"' + q + '" is not in the out-of-scope bank', !CASE.interview.out_of_scope_bank.includes(q));
chk('"Any black stools?" stays out of scope, by a recorded open question', CASE.interview.out_of_scope_bank.includes('Any black stools?'));
const T = id => CASE.interview.topics.find(t => t.topic === id);
chk('the two answers about her back agree: thighs and calves are worst, and no pain in her sides or back',
  !/back/.test(T('location_of_pain').answer[1].value) && /not in my sides or my back/.test(T('abdominal_pain').answer[1].value) &&
  /Not my back/.test(T('abdominal_pain').answer[0].value));
chk('every topic marked a pertinent negative denies in both of its answers',
  CASE.interview.topics.filter(t => t.pertinent_negative).every(t => t.answer.every(r => /\bNo\b|Nothing|None|don't think so/.test(r.value))),
  CASE.interview.topics.filter(t => t.pertinent_negative && !t.answer.every(r => /\bNo\b|Nothing|None|don't think so/.test(r.value))).map(t => t.topic).join());
chk('six topics carry facts', CASE.interview.topics.filter(t => t.facts).length === 6);
const wordsOf = s => s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean);
for (const id of ['fever_and_chills', 'nausea_vomiting', 'current_medications']) {
  const own = new Set(wordsOf(T(id).answer.map(r => r.value).join(' ')));
  const extra = T(id).facts.flatMap(f => f.value.flatMap(r => wordsOf(r.value))).filter(w => !own.has(w));
  chk(id + ': every word of every new fact is in the topic\'s own answer, so a fact adds nothing', extra.length === 0, extra.join());
}
for (const [host, adj] of [['onset', 'fever_and_chills'], ['onset', 'nausea_vomiting'], ['nausea_vomiting', 'diarrhea']]) {
  const vol = T(adj).volunteer.replace(/'/g, ''), hostAns = T(host).answer[1].value;
  const words = w => w.toLowerCase().replace(/[^a-z0-9 ]/g, '').split(' ').filter(x => x.length > 3);
  chk(adj + ' volunteered on ' + host + ' adds something the answer has not just said',
    words(vol).some(w => !words(hostAns).includes(w)) && vol.split(' ').length < 25, vol);
}
chk('no patient answer uses the British forms the audit named',
  CASE.interview.topics.every(t => !/being sick|in hospital\b|Loads/.test(JSON.stringify(t.answer) + JSON.stringify(t.facts || '') + (t.echo || ''))));

section('the handover names what is true of her');
st = fold(mk(START.concat([{ t: 20, actionId: 'handoff_submit',
  payload: { disposition: 'icu', diagnoses: ['dx_toxic_shock_syndrome', 'dx_hyponatremia', 'dx_hypokalemia',
    'dx_anion_gap_metabolic_acidosis', 'dx_thrombocytopenia', 'dx_retained_vaginal_foreign_body'] } }])), 30);
chk('five more diagnoses are credited beside the primary',
  ['dx_hyponatremia', 'dx_hypokalemia', 'dx_anion_gap_metabolic_acidosis', 'dx_thrombocytopenia', 'dx_retained_vaginal_foreign_body']
    .every(id => CASE.handoff.additional_diagnoses.some(d => d.catalog_id === id && d.explanation)));
chk('nine additional diagnoses in all', CASE.handoff.additional_diagnoses.length === 9);
chk('no prompt quotes a number, because each fires in more than one phase',
  Object.keys(ACT).every(id => !ACT[id].prompt || ACT[id].covered_by ||
    !/\d{2,3} over \d{2}|\b\d{2,3}\b(?! kilos| per kilo)/.test(ACT[id].prompt.text.replace(/65|MRSA/g, ''))),
  Object.keys(ACT).filter(id => ACT[id].prompt && !ACT[id].covered_by && /\d{2,3} over \d{2}/.test(ACT[id].prompt.text)).join());

section('a delayed consequence fires on a clock that is not whole seconds');
/* Found by playing the case in a browser. 12.386 - 7.386 is 4.999999999999999 in floating
   point, so the deadline event arrived and the due test failed, and she stayed on her feet
   until the next click. Every other assertion in every pack logs whole seconds. */
for (const t0 of [7.386, 6.537, 3.1, 19.999, 0.07]) {
  const s2 = fold(mk([[1, 'insert_iv'], [t0, 'attempt_discharge']]), t0 + 5.5);
  chk('discharge at ' + t0 + ' has her down by ' + (t0 + 5.5), s2.phase === 'hypotensive', s2.phase);
}
for (const t0 of [5.386, 12.537, 41.3]) {
  const s2 = fold(mk([[1.2, 'insert_iv'], [t0, 'normal_saline_1l_bolus']]), t0 + 10.5);
  chk('fluid at ' + t0 + ' shows by ' + (t0 + 10.5), s2.phase === 'fluid_responsive', s2.phase);
}
