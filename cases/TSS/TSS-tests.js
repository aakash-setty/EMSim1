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
chk('at the authored 92/50 and nothing stacked on it',
  st.vitals.systolic_bp === 92 + 6 && fold(mk(START.concat([[305, 'norepinephrine_drip'], [310, 'normal_saline_1l_bolus']])), 400).vitals.systolic_bp === 92,
  String(st.vitals.systolic_bp));
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
chk('no other action in the case is hidden',
  Object.keys(ACT).filter(id => ACT[id].hidden).join() === 'attempt_discharge');
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
/* Every narration on a timed transition quotes numbers. Each pressure it quotes must be
   the destination phase's own, or the nurse and the monitor disagree (authoring 9.5). */
const WORD = { 'seventy': 70 };
for (const p of CASE.phases) for (const tr of (p.transitions || [])) {
  if (!tr.narration) continue;
  const dest = CASE.phases.find(x => x.id === tr.to).vitals;
  const bp = tr.narration.match(/(\d+) over (\d+)/);
  if (bp) chk(p.id + ' to ' + tr.to + ': pressure ' + bp[0] + ' matches',
    +bp[1] === dest.systolic_bp && +bp[2] === dest.diastolic_bp, dest.systolic_bp + '/' + dest.diastolic_bp);
  const hr = tr.narration.match(/rate (?:is |has come down to |of )?(\d+)/);
  if (hr) chk(p.id + ' to ' + tr.to + ': rate ' + hr[1] + ' matches', +hr[1] === dest.heart_rate, String(dest.heart_rate));
}
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
