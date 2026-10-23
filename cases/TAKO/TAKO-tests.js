/* Case assertions for TAKO (takotsubo with outflow obstruction).
 *
 * New to this pack: a cardiologist who takes over ninety seconds after being called, a
 * case-only button on the Consults tab, two phases with the same numbers and different
 * exits, and a clock that fires whatever the learner does. Times are fractional on
 * purpose (see the v0.21 timing fault).
 *
 * Rewritten in part on 7 October 2026 after the audit. The nurse's lines are now compared
 * with the folded vitals, with each effect-bearing drug acting, and not with the phase's
 * authored numbers. Every behavior fix has a section below.
 */
const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const A0 = [[1.3, 'attach_monitor'], [2.1, 'insert_iv'], [3.4, 'ecg_12_lead'], [4.4, 'ultrasound_cardiac'], [12.2, 'aspirin'],
            [13.7, 'consult_activate_cath_lab']];
const F = (log, t, dm) => fold(mk(log), t, dm);

section('intended path');
let st = F(A0.concat([[20.5, 'exam_card'], [22.5, 'ultrasound_cardiac'],
  [185.2, 'consult_cardiology'], [190.4, 'normal_saline_500ml_bolus'], [191.6, 'phenylephrine_drip']]), 205);
chk('reaches steadied', st.phase === 'steadied', st.phase);
chk('through the obstructed phase', seq(st) === 'presentation > obstructed > steadied', seq(st));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)), [...st.expected].filter(id => !st.satisfied.has(id)).join());
chk('nothing halted, failed or completed', !st.halted && !st.failed && !st.complete);

section('the monitor shows each phase as authored');
const v = (log, t) => F(log, t).vitals;
chk('arrival 115, 96/60', v(A0, 20).heart_rate === 115 && v(A0, 20).systolic_bp === 96);
chk('obstructed 124, 82/50', v(A0, 190).heart_rate === 124 && v(A0, 190).systolic_bp === 82);
chk('untreated shock 138, 70/42', v(A0, 430).heart_rate === 138 && v(A0, 430).systolic_bp === 70);

section('the pressure falls at 180 seconds whatever is done');
chk('still on arrival numbers at 179', F(A0, 179).phase === 'presentation');
chk('obstructed at 181', F(A0, 181).phase === 'obstructed');
chk('with every infarct action done', F(A0, 181).phase === 'obstructed');
chk('with nothing done', F([], 181).phase === 'obstructed');
st = F(A0.concat([[30.5, 'normal_saline_500ml_bolus'], [31.5, 'phenylephrine_drip']]), 185);
chk('unless fluid and a vasoconstrictor are already running', seq(st) === 'presentation > steadied', seq(st));
chk('and that changes nothing before 180', F(A0.concat([[30.5, 'normal_saline_500ml_bolus'], [31.5, 'phenylephrine_drip']]), 170).phase === 'presentation');

section('the nurse recommends cardiology when the pressure falls');
st = F(A0, 205);
chk('twenty seconds after the fall', st.promptFires.some(p => p.id === 'consult_cardiology' && p.t >= 199 && p.t <= 201), JSON.stringify(st.promptFires));
chk('in words', said(st, /cardiology on the phone/));
chk('not on arrival', !F(A0, 170).promptFires.some(p => p.id === 'consult_cardiology'));
st = F([[1.3, 'insert_iv'], [5.5, 'dobutamine_drip']], 40);
chk('and when an inotrope caused the fall', st.phase === 'shock_worse' && st.promptFires.some(p => p.id === 'consult_cardiology'), st.phase);
st = F([[1.3, 'nitroglycerin_sublingual']], 35);
chk('and when a nitrate caused it', st.phase === 'obstructed' && st.promptFires.some(p => p.id === 'consult_cardiology'), st.phase);
st = F([], 445);
chk('and again in untreated shock', st.phase === 'shock_untreated' && st.promptFires.filter(p => p.id === 'consult_cardiology').length === 2, JSON.stringify(st.promptFires));
chk('in normal mode it still comes before the 240-second deterioration',
  F(A0, 419, 3).promptFires.some(p => p.id === 'consult_cardiology' && p.t < 420), JSON.stringify(F(A0, 419, 3).promptFires));

section('the cardiologist gives the plan and then takes over');
const consult = (log, t) => F(log, t).readouts.filter(r => r.key === 'consult_cardiology').pop().body;
st = F([[5.2, 'consult_cardiology']], 6);
chk('busy until there is an ECG and an echo', st.blocked.some(x => x.id === 'consult_cardiology') && !st.flags.has('cardiology_called') && /twelve-lead and a bedside echo/.test(st.blocked[0].message));
st = F([[1.1, 'insert_iv'], [2.2, 'ecg_12_lead'], [9.5, 'consult_cardiology']], 10);
chk('an ECG alone is not enough', st.blocked.length === 1);
st = F([[1.1, 'ultrasound_cardiac'], [2.2, 'ecg_12_lead'], [3.5, 'consult_cardiology']], 4);
chk('nor is an ECG that has not come back yet', st.blocked.length === 1);
st = F([[1.1, 'insert_iv'], [2.2, 'ecg_12_lead'], [185.5, 'consult_cardiology']], 290);
chk('a refused call brings nobody', st.phase === 'obstructed', st.phase);
chk('a refused call is not counted as made', !st.satisfied.has('consult_cardiology'));
chk('on arrival with both: activate, hold nitrates, and the plan if she falls', /Activate/.test(consult(A0.concat([[20.1, 'consult_cardiology']]), 21)) && /Hold nitrates/.test(consult(A0.concat([[20.1, 'consult_cardiology']]), 21)) && /phenylephrine/.test(consult(A0.concat([[20.1, 'consult_cardiology']]), 21)));
let c = consult(A0.concat([[185.5, 'consult_cardiology']]), 186);
chk('pressure low: reads the echo, names what to avoid and what to give', /apex/i.test(c) && /No nitrates/i.test(c) && /phenylephrine or vasopressin/.test(c) && /250 to 500/.test(c), c);
c = consult(A0.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology']]), 198);
chk('on an inotrope, says stop it first', /^Cardiologist: Stop that inotrope now/.test(c), c);
c = consult(A0.concat([[185.1, 'normal_saline_500ml_bolus'], [187.5, 'consult_cardiology']]), 188);
chk('with fluid given, asks for the vasoconstrictor', /fluid was right/.test(c), c);
const call = A0.concat([[185.5, 'consult_cardiology']]);
chk('not yet there at 89 seconds', F(call, 274).phase === 'obstructed');
st = F(call, 276.5);
chk('takes over at 90', st.phase === 'steadied', st.phase);
chk('and the nurse says who did it', said(st, /Cardiology is at the bedside and has taken over/));
chk('the learner is not credited with the fluid or the pressor',
  !st.satisfied.has('normal_saline_1l_bolus') && !st.satisfied.has('phenylephrine_drip'));
st = F(call.concat([[200.2, 'normal_saline_500ml_bolus'], [201.3, 'vasopressin_drip']]), 213);
chk('a learner who acts on the advice gets there first, by their own hand',
  st.phase === 'steadied' && !said(st, /taken over/) && st.satisfied.has('phenylephrine_drip'), st.phase);
st = F(A0.concat([[20.1, 'consult_cardiology']]), 269);
chk('called on arrival: not there until ninety seconds after the fall', st.phase === 'obstructed', st.phase);
chk('then there', F(A0.concat([[20.1, 'consult_cardiology']]), 271).phase === 'steadied');
st = F(A0.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology']]), 289);
chk('takes over from an inotrope too', st.phase === 'steadied' && said(st, /The inotrope is off/), st.phase);

section('the wrong drugs show what they do and can be undone');
st = F([[1.3, 'insert_iv'], [5.5, 'nitroglycerin']], 17);
chk('nitroglycerin: obstructed in ten seconds, and the fall is counted once', st.phase === 'obstructed' && st.vitals.systolic_bp === 82, st.phase + ' ' + st.vitals.systolic_bp);
chk('and nothing more comes off while she stays obstructed', F([[1.3, 'insert_iv'], [5.5, 'nitroglycerin']], 130).vitals.systolic_bp === 82);
for (const id of ['dobutamine_drip', 'epinephrine_drip', 'dopamine_drip']) {
  st = F([[1.3, 'insert_iv'], [5.5, id]], 17);
  chk(id + ': worse in ten seconds', st.phase === 'shock_worse' && st.discouragedTaken.has(id), st.phase);
}
const ino = A0.concat([[185.1, 'dobutamine_drip']]);
chk('the nurse asks whether to stop it', F(ino, 225).promptFires.some(p => p.id === 'stop_dobutamine'));
st = F(ino.concat([[200.2, 'stop_dobutamine']]), 260);
chk('stopping it alone: still in shock, eight points better', st.phase === 'shock_worse' && st.vitals.systolic_bp === 78, st.phase + ' ' + st.vitals.systolic_bp);
st = F(ino.concat([[200.2, 'normal_saline_500ml_bolus'], [201.2, 'phenylephrine_drip']]), 260);
chk('the right pair with the inotrope still running: no better', st.phase === 'shock_worse', st.phase);
st = F(ino.concat([[200.2, 'stop_epinephrine'], [201.2, 'normal_saline_500ml_bolus'], [202.2, 'phenylephrine_drip']]), 214);
chk('stopped, then the right pair: steadied', st.phase === 'steadied', st.phase);
st = F(A0.concat([[185.1, 'esmolol_drip']]), 190);
chk('a beta blocker before a vasoconstrictor drops her pressure', st.vitals.systolic_bp === 72 && st.discouragedTaken.has('esmolol_drip'), String(st.vitals.systolic_bp));
st = F(A0.concat([[185.1, 'normal_saline_500ml_bolus'], [186.1, 'phenylephrine_drip'], [200.4, 'esmolol_drip']]), 205);
chk('once steadied it slows her and the pressure holds', st.vitals.heart_rate === 90 && st.vitals.systolic_bp === 100 && !st.discouragedTaken.has('esmolol_drip'), JSON.stringify(st.vitals));
st = F(A0.concat([[20.3, 'tenecteplase_tnk_bolus']]), 30);
chk('thrombolysis is discouraged and ends nothing', st.discouragedTaken.has('tenecteplase_tnk_bolus') && !st.halted && st.phase === 'presentation');
chk('nothing in this case is harmful', HARMFUL.length === 0, HARMFUL.join());
chk('the only terminal phase is the handoff', CASE.phases.filter(p => p.terminal).map(p => p.id).join() === 'case_complete');
st = F(A0, 3000);
chk('the do-nothing path stops in untreated shock and never ends', st.phase === 'shock_untreated' && !st.failed && !st.complete);

section('partial treatment shows as partial');
chk('fluid alone: six points for a minute', v(A0.concat([[185.5, 'normal_saline_500ml_bolus']]), 190).systolic_bp === 88 && v(A0.concat([[185.5, 'normal_saline_500ml_bolus']]), 250).systolic_bp === 82);
chk('a vasoconstrictor alone: eight points', v(A0.concat([[185.5, 'phenylephrine_drip']]), 230).systolic_bp === 90);
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'norepinephrine_drip']]), 200);
chk('norepinephrine is accepted and satisfies the vasoconstrictor', st.phase === 'steadied' && st.satisfied.has('phenylephrine_drip') && !st.discouragedTaken.has('norepinephrine_drip'), st.phase);

section('the infarct pathway moves nothing and is scored');
const bare = F([[1.3, 'attach_monitor'], [2.1, 'insert_iv']], 100);
st = F(A0.concat([[15.5, 'heparin_bolus_drip']]), 100);
chk('same phase and vitals with and without', bare.phase === st.phase && JSON.stringify(bare.vitals) === JSON.stringify(st.vitals));
chk('ECG, aspirin and activation are expected', ['ecg_12_lead', 'aspirin', 'consult_activate_cath_lab'].every(id => st.expected.has(id) && st.satisfied.has(id)));
chk('the activation button exists only in this case', ACT.consult_activate_cath_lab.orphan && ACT.consult_activate_cath_lab.tab === 'consultations');
chk('and answers', /Activated/.test(st.readouts.filter(r => r.key === 'consult_activate_cath_lab').pop().body));

section('findings');
const exam = (id, log, t) => F(log.concat([[t - 0.5, id]]), t).readouts.pop().body.findings;
chk('a murmur that changes with posture', /Louder with Valsalva, softer legs raised/.test(exam('exam_card', A0, 20)));
chk('clear lungs and flat neck veins', /Clear/.test(exam('exam_pulm', A0, 20)) && /flat/.test(exam('exam_neck', A0, 20)));
st = F(A0.concat([[20.2, 'ultrasound_cardiac'], [20.3, 'troponin_t'], [20.4, 'ecg_12_lead']]), 40);
chk('the echo describes and does not name', /Apex/.test(st.orders.ultrasound_cardiac[0].value.report) && !/takotsubo|obstruction/i.test(st.orders.ultrasound_cardiac[0].value.report));
chk('the ECG describes and does not name', /ST elevation/.test(st.orders.ecg_12_lead[0].value.comment) && !/takotsubo|infarct/i.test(st.orders.ecg_12_lead[0].value.comment + ' ' + st.orders.ecg_12_lead[0].value.caption));
chk('troponin raised', st.orders.troponin_t[0].value.abnormal);
chk('every authored study resolves from the case', AUTHORED_STUDIES.every(id => F([[1, 'insert_iv'], [2.5, id]], 30).orders[id][0].source === 'case'));

section('the interview');
const ask = (topic, t) => F([{ t, kind: 'interview', topic, q: '?' }], t + 1).readouts.pop().body;
chk('the trigger is there to be asked for', /buried my husband/.test(ask('what_she_was_doing', 5)));
chk('and the daughter gives the wrong reading', /nerves/.test(ask('what_she_was_doing', 5)));
chk('she has barely eaten or drunk', /Five days/.test(ask('last_oral_intake', 5)));
chk('no answer names the diagnosis', CASE.interview.topics.every(t => !/takotsubo|broken heart|heart attack\b(?! at)/i.test(JSON.stringify(t.answer).replace(/No heart attack/g, ''))));
chk('the handover names no finding', !/ST elevation|murmur|pressure|ECG|stress/i.test(CASE.patient.arrival_handover), CASE.patient.arrival_handover);
chk('with a low pressure she answers in fewer words', ask('onset', 190).length < ask('onset', 5).length);
chk('every topic has a short answer', CASE.interview.topics.every(t => /obstructed/.test(t.answer[0].when)));

section('handoff');
st = F(A0.concat([{ t: 30.5, actionId: 'handoff_submit', payload: { disposition: 'cath_lab',
  diagnoses: ['dx_st_elevation_myocardial_infarction', 'dx_takotsubo_cardiomyopathy', 'dx_cardiogenic_shock',
              'dx_left_ventricular_outflow_tract_obstruction'] } }]), 40);
let hs = summaryScores(st).find(r => r.id === 'handoff');
chk('the lab with an infarct first and all three other diagnoses beside it scores 100', hs.points === 100, JSON.stringify(hs));
st = F(A0.concat([{ t: 30.5, actionId: 'handoff_submit', payload: { disposition: 'cath_lab',
  diagnoses: ['dx_st_elevation_myocardial_infarction', 'dx_left_ventricular_outflow_tract_obstruction'] } }]), 40);
hs = summaryScores(st).find(r => r.id === 'handoff');
/* 23 October 2026: outflow obstruction is the one scored additional diagnosis, so naming it
   with the infarct completes the handoff. Shock and takotsubo are minor and cost nothing. */
chk('outflow obstruction is credited as the additional diagnosis', /1 of 1 additional/.test(hs.detail) && hs.points === 100, hs.detail);
st = F(A0.concat([{ t: 30.5, actionId: 'handoff_submit', payload: { disposition: 'cath_lab', diagnoses: ['dx_takotsubo_cardiomyopathy'] } }]), 40);
hs = summaryScores(st).find(r => r.id === 'handoff');
chk('takotsubo named first is defensible, not correct', /primary diagnosis defensible/.test(hs.detail), hs.detail);
st = F([{ t: 190.5, actionId: 'handoff_submit', payload: { disposition: 'icu', diagnoses: ['dx_panic_attack'] } }], 200);
chk('handed over hypotensive, shown hypotensive', st.vitals.systolic_bp === 82);

section('what the nurse says is true of the monitor');
/* Authoring 7.3. Every timed narration is folded on a route with each effect-bearing drug
   acting, and each claim about a direction is compared with the vitals the monitor shows
   just before and just after the line. The phase's authored numbers are not consulted. */
for (const p of CASE.phases) for (const tr of (p.transitions || [])) {
  if (tr.narration) chk(p.id + ' to ' + tr.to + ': the line quotes no figure', !/\d/.test(tr.narration), tr.narration);
}
const CLAIMS = [
  [/pressure (has dropped|has fallen|is down)/, (b, a) => a.systolic_bp < b.systolic_bp],
  [/pressure is up/, (b, a) => a.systolic_bp > b.systolic_bp],
  [/pressure is holding/, (b, a) => a.systolic_bp >= b.systolic_bp],
  [/rate is up/, (b, a) => a.heart_rate > b.heart_rate],
  [/rate (is down|has come down)/, (b, a) => a.heart_rate < b.heart_rate],
];
let linesChecked = 0;
const truth = (name, log, to, expectLine) => {
  const end = F(log, 5000);
  const hop = end.phaseSeq.filter(x => x.id === to).pop();
  if (!hop) { chk(name + ': reaches ' + to, false, seq(end)); return; }
  const line = end.nurse.find(n => n.t === hop.t && n.kind === 'deterioration');
  const b = F(log, hop.t - 0.01).vitals, a = F(log, hop.t + 0.01).vitals;
  const bad = [];
  let claims = 0;
  for (const [re, ok] of CLAIMS) if (line && re.test(line.text)) { claims++; if (!ok(b, a)) bad.push(String(re)); }
  linesChecked++;
  chk(name + ' -> ' + to, !!line && bad.length === 0 && (!expectLine || expectLine.test(line.text)) && claims > 0 === !/still in shock/.test(line.text),
    (line ? line.text : 'no line') + ' | before ' + b.heart_rate + ' ' + b.systolic_bp + ' after ' + a.heart_rate + ' ' + a.systolic_bp + ' ' + bad.join());
};
const IV = [[1.1, 'insert_iv']];
const BASE = IV.concat([[2.2, 'ecg_12_lead'], [3.3, 'ultrasound_cardiac']]);
/* One extra drug at a time. Each entry is [label, steps]. Times are chosen so the effect is
   acting, or about to act, when the line is spoken. */
const extrasAt = t => [
  ['nothing else', []],
  ['phenylephrine alone', [[t, 'phenylephrine_drip']]],
  ['vasopressin alone', [[t, 'vasopressin_drip']]],
  ['norepinephrine alone', [[t, 'norepinephrine_drip']]],
  ['fluid alone', [[t, 'normal_saline_500ml_bolus']]],
  ['a beta blocker', [[t, 'esmolol_drip']]],
  ['a diuretic', [[t, 'furosemide_40_mg_iv']]],
];
// 1. The scripted fall at 180 seconds.
for (const [n, x] of extrasAt(150.5).concat([['fluid five seconds before', [[175.5, 'lactated_ringer_s_500ml_bolus']]],
     ['a nitrate five seconds before', [[175.5, 'nitroglycerin_sublingual']]],
     ['an inotrope five seconds before', [[175.5, 'dobutamine_drip']]]]))
  truth('the fall, with ' + n, IV.concat(x), 'obstructed', /pressure has fallen/);
// 2. A nitrate on arrival.
for (const id of ['nitroglycerin', 'nitroglycerin_sublingual', 'nitroglycerin_drip', 'nitroprusside_drip'])
  truth(id + ' on arrival', IV.concat([[5.5, id]]), 'obstructed', /since that vasodilator/);
for (const [n, x] of extrasAt(4.5)) truth('a nitrate on arrival, with ' + n, IV.concat(x, [[20.5, 'nitroglycerin']]), 'obstructed', /since that vasodilator/);
// 3. An inotrope, from each phase it can be given in.
for (const id of ['dobutamine_drip', 'epinephrine_drip', 'dopamine_drip', 'epinephrine_bolus'])
  truth(id + ' on arrival', IV.concat([[5.5, id]]), 'shock_worse', /since that inotrope/);
for (const [n, x] of extrasAt(4.5).concat([['a nitrate with it', [[20.4, 'nitroglycerin']]], ['the inotrope stopped inside the window', [[24.5, 'stop_dobutamine']]]])) {
  truth('an inotrope on arrival, with ' + n, IV.concat(x, [[20.5, 'dobutamine_drip']]), 'shock_worse', /since that inotrope/);
  truth('an inotrope with a low pressure, with ' + n, IV.concat(x.map(e => [e[0] + 180, e[1]]), [[200.5, 'dobutamine_drip']]), 'shock_worse', /since that inotrope/);
  truth('an inotrope in untreated shock, with ' + n, IV.concat(x.map(e => [e[0] + 420, e[1]]), [[440.5, 'dobutamine_drip']]), 'shock_worse', /still in shock/);
}
// 4. The pair already running when the fall comes.
for (const vaso of ['phenylephrine_drip', 'vasopressin_drip', 'norepinephrine_drip'])
  for (const [n, x] of [['nothing else', []], ['a beta blocker', [[100.5, 'esmolol_drip']]], ['a diuretic acting', [[100.5, 'furosemide_40_mg_iv']]], ['a diuretic about to act', [[165.5, 'furosemide_40_mg_iv']]]])
    truth('fluid and ' + vaso + ' before the fall, with ' + n, IV.concat([[30.5, 'normal_saline_500ml_bolus'], [31.5, vaso]], x), 'steadied', /pressure is holding/);
// 5. The pair after the fall, and in untreated shock.
for (const [phase, t0, re] of [['with a low pressure', 180, /That's working/], ['in untreated shock', 420, /She's coming back\./]])
  for (const vaso of ['phenylephrine_drip', 'vasopressin_drip', 'norepinephrine_drip'])
    for (const [n, x] of [['nothing else', []], ['a beta blocker', [[t0 + 2.5, 'esmolol_drip']]], ['a diuretic', [[t0 + 2.5, 'furosemide_40_mg_iv']]],
                          ['a nitrate', [[t0 + 2.5, 'nitroglycerin']]], ['an inotrope started just after the pair', [[t0 + 12.5, 'dobutamine_drip']]]])
      truth('the pair ' + phase + ' (' + vaso + '), with ' + n, IV.concat(x, [[t0 + 8.5, 'normal_saline_500ml_bolus'], [t0 + 9.5, vaso]]), 'steadied', re);
// 6. The 240-second deterioration.
for (const [n, x] of extrasAt(185.5).concat([['fluid late', [[415.5, 'normal_saline_500ml_bolus']]], ['a beta blocker late', [[300.5, 'esmolol_drip']]],
     ['a diuretic late', [[410.5, 'furosemide_40_mg_iv']]], ['a nitrate early', [[185.5, 'nitroglycerin']]], ['a nitrate late', [[400.5, 'nitroglycerin']]]]))
  truth('untreated for four minutes, with ' + n, IV.concat(x), 'shock_untreated', /She's getting worse/);
// 7. Cardiology takes over, from each low-pressure phase.
for (const [n, x] of extrasAt(190.5).concat([['a nitrate', [[190.5, 'nitroglycerin']]], ['an inotrope started five seconds before they arrive', [[270.7, 'dobutamine_drip']]]]))
  truth('cardiology takes over with a low pressure, with ' + n, BASE.concat([[185.7, 'consult_cardiology']], x), 'steadied', /Cardiology is at the bedside/);
for (const [n, x] of extrasAt(430.5).concat([['a nitrate', [[430.5, 'nitroglycerin']]]]))
  truth('cardiology takes over in untreated shock, with ' + n, BASE.concat([[425.7, 'consult_cardiology']], x), 'steadied', /Cardiology is at the bedside/);
for (const [n, x] of extrasAt(200.5).concat([['a nitrate', [[200.5, 'nitroglycerin']]], ['the inotrope already stopped', [[230.5, 'stop_dobutamine']]]]))
  truth('cardiology takes over from an inotrope, with ' + n, BASE.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology']], x), 'steadied', /The inotrope is off/);
// 8. The inotrope stopped and the pair given.
for (const [n, x] of extrasAt(200.5).slice(5).concat([['nothing else', []], ['a nitrate', [[200.5, 'nitroglycerin']]]]))
  for (const vaso of ['phenylephrine_drip', 'norepinephrine_drip'])
    truth('stopped, then the pair (' + vaso + '), with ' + n, IV.concat([[185.1, 'dobutamine_drip']], x, [[210.2, 'stop_dopamine'], [211.2, 'normal_saline_500ml_bolus'], [212.2, vaso]]), 'steadied', /now that inotrope is off/);
chk('every timed narration was folded on at least one route', linesChecked > 100 &&
  CASE.phases.every(p => (p.transitions || []).filter(tr => tr.narration).length <= 5), String(linesChecked));

section('cardiology takes over and the inotrope is gone from the monitor (audit finding 2)');
const takeover = A0.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology']]);
st = F(takeover, 289);
chk('steadied at 100 over 62 with a rate of 104', st.phase === 'steadied' && st.vitals.systolic_bp === 100 && st.vitals.heart_rate === 104, JSON.stringify(st.vitals));
st = F(takeover, 600.5);
chk('and still there five minutes later', st.vitals.systolic_bp === 100 && st.vitals.heart_rate === 104, JSON.stringify(st.vitals));
st = F(takeover.concat([{ t: 300.5, actionId: 'handoff_submit', payload: { disposition: 'cath_lab', diagnoses: ['dx_st_elevation_myocardial_infarction'] } }]), 310);
chk('the handoff inherits the steadied numbers', st.vitals.systolic_bp === 100 && st.vitals.heart_rate === 104, JSON.stringify(st.vitals));
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'dobutamine_drip']]), 230);
chk('an inotrope once steadied, with no cardiology call, still costs her pressure', st.phase === 'steadied' && st.vitals.systolic_bp === 86 && st.vitals.heart_rate === 120, JSON.stringify(st.vitals));
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'dobutamine_drip'], [210.5, 'stop_dobutamine']]), 230);
chk('and stopping it gives the pressure back', st.vitals.systolic_bp === 100 && st.vitals.heart_rate === 104, JSON.stringify(st.vitals));
st = F(A0.concat([[20.1, 'consult_cardiology'], [185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'dobutamine_drip']]), 230);
chk('known limit, pinned: after a cardiology call an inotrope in the steadied phase shows nothing', st.phase === 'steadied' && st.vitals.systolic_bp === 100 && st.discouragedTaken.has('dobutamine_drip'), JSON.stringify(st.vitals));

st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'dobutamine_drip'], [210.5, 'consult_cardiology']]), 230);
chk('known limit, pinned: a cardiology call in the steadied phase also takes the inotrope off the monitor', st.vitals.systolic_bp === 100 && st.vitals.heart_rate === 104 && !st.flags.has('inotrope_stopped'), JSON.stringify(st.vitals));

section('a nitrate is counted once (audit finding 1)');
st = F(A0.concat([[185.5, 'nitroglycerin']]), 200);
chk('known limit, pinned: a nitrate given with a low pressure shows no further fall there', st.phase === 'obstructed' && st.vitals.systolic_bp === 82 && st.discouragedTaken.has('nitroglycerin'), String(st.vitals.systolic_bp));
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'nitroglycerin_drip']]), 230);
chk('once steadied it costs twelve points', st.vitals.systolic_bp === 88, String(st.vitals.systolic_bp));
chk('for two minutes', F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [200.5, 'nitroglycerin_drip']]), 321).vitals.systolic_bp === 100);
st = F(A0.concat([[425.5, 'nitroglycerin']]), 440);
chk('and in untreated shock', st.vitals.systolic_bp === 58, String(st.vitals.systolic_bp));

section('prompts are true where they fire (audit findings 3 and 4)');
const fires = (st, id) => st.promptFires.filter(p => p.id === id);
const promptText = id => ACT[id].prompt.text;
chk('the cardiology prompt describes a state, not a fall', /pressure is low/.test(promptText('consult_cardiology')) && !/dropped|falling/.test(promptText('consult_cardiology')));
chk('the stop prompt claims no worsening', !/worse/.test(promptText('stop_dobutamine')) && /not helping/.test(promptText('stop_dobutamine')));
st = F(A0.concat([[425.5, 'dobutamine_drip']]), 470);
chk('both fire when untreated shock becomes shock on an inotrope, with the same pressure before and after',
  st.phase === 'shock_worse' && fires(st, 'stop_dobutamine').length === 1 && fires(st, 'consult_cardiology').length === 2 &&
  F(A0.concat([[425.5, 'dobutamine_drip']]), 435.4).vitals.systolic_bp === F(A0.concat([[425.5, 'dobutamine_drip']]), 435.6).vitals.systolic_bp, JSON.stringify(st.promptFires));
st = F([[1.3, 'attach_monitor'], [2.1, 'insert_iv']], 175);
chk('with no ECG, the aspirin prompt is not spoken', fires(st, 'aspirin').length === 0);
chk('nor the catheterization laboratory prompt', fires(st, 'consult_activate_cath_lab').length === 0);
chk('the ECG prompt is', fires(st, 'ecg_12_lead').length === 1 && !said(st, /ST elevation/));
st = F([[1.3, 'attach_monitor'], [2.1, 'insert_iv'], [86.4, 'ecg_12_lead']], 175);
chk('an ECG still printing at the deadline does not count', fires(st, 'aspirin').length === 0 && fires(st, 'consult_activate_cath_lab').length === 1, JSON.stringify(st.promptFires));
st = F([[1.3, 'attach_monitor'], [2.1, 'insert_iv'], [3.4, 'ecg_12_lead']], 175);
chk('with the ECG back, aspirin at 90 and the laboratory at 130', fires(st, 'aspirin')[0].t === 90 && fires(st, 'consult_activate_cath_lab')[0].t === 130, JSON.stringify(st.promptFires));
st = F([], 3000);
chk('on the do-nothing path neither is ever spoken', fires(st, 'aspirin').length === 0 && fires(st, 'consult_activate_cath_lab').length === 0 && !said(st, /ST elevation/));

section('the recheck after fluid counts only after the fluid (audit finding 5)');
const FUID = 'recheck_lungs_after_fluid';
const fu = (log, t) => { const s2 = F(log, t); return { fired: s2.fuFires.some(f => f.fid === FUID), open: s2.fuOutstanding.has(FUID), st: s2 }; };
let r = fu(A0.concat([[20.5, 'exam_pulm'], [21.5, 'ultrasound_lung'], [22.5, 'xr_chest'], [185.5, 'normal_saline_500ml_bolus']]), 260);
chk('a chest exam, a lung ultrasound and a film before the bolus do not discharge it', r.fired && r.open && !r.st.satisfied.has('chest_rechecked'), JSON.stringify(r.st.fuFires));
chk('it is asked sixty seconds after the bolus', r.st.fuFires[0].t === 245.5, JSON.stringify(r.st.fuFires));
chk('and the nurse does not say again', said(r.st, /listen to her chest before she gets any more/) && !said(r.st, /chest again/));
for (const id of ['exam_pulm', 'ultrasound_lung', 'xr_chest']) {
  r = fu(A0.concat([[20.5, 'exam_pulm'], [185.5, 'normal_saline_500ml_bolus'], [200.5, id]]), 260);
  chk(id + ' after the bolus discharges it', !r.fired && !r.open && r.st.satisfied.has('chest_rechecked'), JSON.stringify(r.st.fuFires));
}
r = fu(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [250.5, 'exam_pulm']]), 260);
chk('done after the nurse asks, it is closed', r.fired && !r.open);
r = fu(A0.concat([[185.5, 'lactated_ringer_s_1l_bolus']]), 260);
chk('any crystalloid starts it', r.fired && r.open);
r = fu(A0.concat([[185.5, 'normal_saline_500ml_bolus']]), 400, 3);
chk('in the default mode it is asked at three minutes', F(A0.concat([[185.5, 'normal_saline_500ml_bolus']]), 400, 3).fuFires[0].t === 365.5);
r = fu(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [200.5, 'exam_pulm'], [300.5, 'normal_saline_500ml_bolus']]), 400);
chk('known limit, pinned: a second bolus asks for nothing once the chest was rechecked', !r.fired);
chk('the target is not a button', ACT.chest_rechecked.hidden === true && ACT.chest_rechecked.tab === 'handoff', ACT.chest_rechecked.tab);

section('the catheterization laboratory needs a twelve-lead that is back (audit finding 16)');
st = F([[1.1, 'insert_iv'], [5.5, 'consult_activate_cath_lab']], 6);
chk('no ECG: refused, in the nurse voice', st.blocked.length === 1 && /will want a twelve-lead before they call the team in/.test(st.blocked[0].message), JSON.stringify(st.blocked));
chk('and it earns nothing', !st.flags.has('cath_lab_activated') && !st.satisfied.has('consult_activate_cath_lab'));
st = F([[1.1, 'insert_iv'], [4.4, 'ecg_12_lead'], [5.5, 'consult_activate_cath_lab']], 6);
chk('ECG still printing: refused with the pending line', st.blocked.length === 1 && /still printing/.test(st.blocked[0].message), JSON.stringify(st.blocked));
chk('and it earns nothing either', !st.flags.has('cath_lab_activated') && !st.satisfied.has('consult_activate_cath_lab'));
st = F([[1.1, 'insert_iv'], [4.4, 'ecg_12_lead'], [9.9, 'consult_activate_cath_lab']], 12);
chk('ECG back: activated and credited', st.blocked.length === 0 && st.flags.has('cath_lab_activated') && st.satisfied.has('consult_activate_cath_lab') &&
  /Activated/.test(st.readouts.filter(x => x.key === 'consult_activate_cath_lab').pop().body));
chk('no reply of the laboratory declines', CASE.content_keys.consultants.consult_activate_cath_lab.every(x => !/Is there one/.test(x.value)));

section('the catheterization laboratory can be asked for aloud (catalog audit 3.8)');
{
  const vf = html.match(/\/\*__VOICE_START__\*\/([\s\S]*?)\/\*__VOICE_END__\*\//);
  const VOICE = eval(vf[1] + '\n;VOICE');
  VOICE.build(grab('voice-data'));
  const phrases = ACT.consult_activate_cath_lab.voice_phrases || [];
  chk('eleven phrases are authored', phrases.length === 11, String(phrases.length));
  for (const p of phrases.concat(['Activate Catheterization Lab', 'Code STEMI!', 'please activate the cath lab', 'call the cath lab now'])) {
    const rows = VOICE.parse(p);
    chk('"' + p + '" orders the activation', rows.length === 1 && rows[0].kind === 'ok' && rows[0].id === 'consult_activate_cath_lab', JSON.stringify(rows));
  }
  const echo = VOICE.parse('bedside echo');
  chk('and the bedside echo is still the bedside echo', echo.length === 1 && echo[0].id === 'ultrasound_cardiac', JSON.stringify(echo));
}

section('the default mode warns before the 240-second deterioration (authoring 7.4)');
const exit240 = CASE.phases.find(p => p.id === 'obstructed').transitions.find(tr => tr.after_seconds === 240);
for (const id of ['consult_cardiology', 'normal_saline_1l_bolus', 'phenylephrine_drip'])
  chk(id + ': three times the deadline is under 240', ACT[id].prompt.deadline_seconds * 3 < exit240.after_seconds, String(ACT[id].prompt.deadline_seconds));
for (const [n, log, want] of [['doing nothing', [], ['consult_cardiology', 'normal_saline_1l_bolus', 'phenylephrine_drip']],
     ['the infarct pathway only', A0, ['consult_cardiology', 'normal_saline_1l_bolus', 'phenylephrine_drip']],
     ['fluid alone', A0.concat([[185.5, 'normal_saline_500ml_bolus']]), ['consult_cardiology', 'phenylephrine_drip']],
     ['a vasoconstrictor alone', A0.concat([[185.5, 'phenylephrine_drip']]), ['consult_cardiology', 'normal_saline_1l_bolus']]]) {
  const s3 = F(log, 419.9, 3);
  chk(n + ', default mode: still obstructed just before 240, and every warning has been spoken',
    s3.phase === 'obstructed' && want.every(id => s3.promptFires.some(p => p.id === id && p.t > 180 && p.t < 420)), JSON.stringify(s3.promptFires));
  chk(n + ', default mode: then she deteriorates', F(log, 420.1, 3).phase === 'shock_untreated');
}
st = F([], 419.9, 3);
chk('default mode, in order: cardiology at 60, fluid at 135, a vasoconstrictor at 180 after the fall',
  fires(st, 'consult_cardiology')[0].t === 240 && fires(st, 'normal_saline_1l_bolus')[0].t === 315 && fires(st, 'phenylephrine_drip')[0].t === 360, JSON.stringify(st.promptFires));
st = F([], 241);
chk('easy mode: 20, 45 and 60 after the fall', fires(st, 'consult_cardiology')[0].t === 200 && fires(st, 'normal_saline_1l_bolus')[0].t === 225 && fires(st, 'phenylephrine_drip')[0].t === 240, JSON.stringify(st.promptFires));
st = F(A0, 179.9, 3);
chk('default mode on arrival, recorded: only the monitor and ECG prompts can precede the fall', fires(st, 'aspirin').length === 0 && fires(st, 'consult_activate_cath_lab').length === 0);

section('one treatment, and the last window (authoring 13 step 8)');
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus']]), 430.5);
chk('fluid alone, then the clock: untreated shock', seq(st) === 'presentation > obstructed > shock_untreated', seq(st));
st = F(A0.concat([[185.5, 'vasopressin_drip']]), 430.5);
chk('a vasoconstrictor alone, then the clock: untreated shock', seq(st) === 'presentation > obstructed > shock_untreated', seq(st));
st = F(A0.concat([[405.5, 'normal_saline_500ml_bolus'], [418.5, 'phenylephrine_drip']]), 430.5);
chk('the second drug 1.5 seconds before the deadline: steadied, never in untreated shock', seq(st) === 'presentation > obstructed > steadied', seq(st));
st = F(A0.concat([[405.5, 'normal_saline_500ml_bolus'], [421.5, 'phenylephrine_drip']]), 432.5);
chk('the second drug 1.5 seconds after it: through untreated shock', seq(st) === 'presentation > obstructed > shock_untreated > steadied', seq(st));

section('two timed rules pending at once (authoring 15.4, the table in the SEED)');
const pair = t => [[t, 'normal_saline_500ml_bolus'], [t + 1, 'phenylephrine_drip']];
const lands = (name, log, t, want) => { const s4 = F(log, t); chk(name, seq(s4) === want, seq(s4)); return s4; };
lands('arrival: an inotrope 10.5 seconds before the fall acts first', IV.concat([[169.5, 'dobutamine_drip']]), 200, 'presentation > shock_worse');
lands('arrival: an inotrope 9.5 seconds before the fall goes through the obstructed phase', IV.concat([[170.5, 'dobutamine_drip']]), 200, 'presentation > obstructed > shock_worse');
lands('arrival: the pair running and an inotrope 10.5 seconds before the fall', IV.concat(pair(20.5), [[169.5, 'dobutamine_drip']]), 200, 'presentation > shock_worse');
st = lands('arrival: the pair running and an inotrope 9.5 seconds before the fall is not steadied', IV.concat(pair(20.5), [[170.5, 'dobutamine_drip']]), 200, 'presentation > obstructed > shock_worse');
chk('and the nurse does not say her pressure is holding', !said(st, /pressure is holding/));
st = lands('arrival: the pair running and a nitrate 4.5 seconds before the fall', IV.concat(pair(20.5), [[175.5, 'nitroglycerin']]), 200, 'presentation > obstructed > steadied');
chk('and the nurse does not say her pressure is holding', !said(st, /pressure is holding/) && said(st, /That's working/));
lands('arrival: a nitrate and an inotrope together, the inotrope wins', IV.concat([[5.5, 'nitroglycerin'], [5.5, 'dobutamine_drip']]), 40, 'presentation > shock_worse');
lands('arrival: a nitrate, then an inotrope two seconds later', IV.concat([[5.5, 'nitroglycerin'], [7.5, 'dobutamine_drip']]), 40, 'presentation > obstructed > shock_worse');
st = lands('known limit, pinned: an inotrope stopped inside the ten seconds still makes her worse', IV.concat([[5.5, 'dobutamine_drip'], [9.5, 'stop_dobutamine']]), 40, 'presentation > shock_worse');
chk('and she then needs only the pair', F(IV.concat([[5.5, 'dobutamine_drip'], [9.5, 'stop_dobutamine']], pair(20.5)), 40).phase === 'steadied');
lands('low pressure: an inotrope, then the pair a second later, the inotrope wins', IV.concat([[185.5, 'dobutamine_drip']], pair(186.5)), 230, 'presentation > obstructed > shock_worse');
lands('low pressure: the pair, then an inotrope at the same instant, the inotrope wins', IV.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip'], [186.5, 'dobutamine_drip']]), 230, 'presentation > obstructed > shock_worse');
st = lands('known limit, pinned: the pair, then an inotrope 4.5 seconds later, is steadied with the inotrope acting', IV.concat(pair(185.5), [[191, 'dobutamine_drip']]), 230, 'presentation > obstructed > steadied');
chk('and the monitor shows what the inotrope costs', st.vitals.systolic_bp === 86 && st.vitals.heart_rate === 120, JSON.stringify(st.vitals));
lands('low pressure: cardiology called 90.5 seconds before the deadline arrives in time', BASE.concat([[329.5, 'consult_cardiology']]), 425, 'presentation > obstructed > steadied');
st = lands('known limit, pinned: called 89.5 seconds before it, the count starts again', BASE.concat([[330.5, 'consult_cardiology']]), 505, 'presentation > obstructed > shock_untreated');
chk('and cardiology arrives ninety seconds after the deterioration, 179.5 seconds after the call', F(BASE.concat([[330.5, 'consult_cardiology']]), 509.5).phase === 'shock_untreated' && F(BASE.concat([[330.5, 'consult_cardiology']]), 510.5).phase === 'steadied');
lands('low pressure: the pair completed 10.5 seconds before the deadline', IV.concat([[408.5, 'normal_saline_500ml_bolus'], [409.5, 'phenylephrine_drip']]), 421, 'presentation > obstructed > steadied');
lands('low pressure: the pair completed 9 seconds before it still steadies her without the deterioration', IV.concat([[409.5, 'normal_saline_500ml_bolus'], [411, 'phenylephrine_drip']]), 422, 'presentation > obstructed > steadied');
lands('low pressure: an inotrope 9 seconds before the deadline, the deterioration comes first', IV.concat([[411, 'dobutamine_drip']]), 440, 'presentation > obstructed > shock_untreated > shock_worse');
lands('low pressure: cardiology called, then the pair before they arrive, by the learner', BASE.concat([[185.5, 'consult_cardiology']], pair(260.5)), 272, 'presentation > obstructed > steadied');
st = F(BASE.concat([[185.5, 'consult_cardiology']], pair(260.5)), 300);
chk('and cardiology does not take over afterwards', !said(st, /taken over/));
st = lands('low pressure: cardiology called, the pair 4.5 seconds before they arrive, cardiology gets there first', BASE.concat([[185.5, 'consult_cardiology']], pair(270)), 300, 'presentation > obstructed > steadied');
chk('and the nurse says so', said(st, /taken over/) && st.phaseSeq.pop().t === 275.5);
lands('low pressure: cardiology called, an inotrope 11 seconds before they arrive', BASE.concat([[185.5, 'consult_cardiology'], [264.5, 'dobutamine_drip']]), 300, 'presentation > obstructed > shock_worse');
lands('and they arrive ninety seconds after that', BASE.concat([[185.5, 'consult_cardiology'], [264.5, 'dobutamine_drip']]), 365, 'presentation > obstructed > shock_worse > steadied');
lands('on an inotrope: stopped and the pair given before cardiology arrives', BASE.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology'], [270.5, 'stop_dobutamine']], pair(271.5)), 284, 'presentation > obstructed > shock_worse > steadied');
st = F(BASE.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology'], [270.5, 'stop_dobutamine']], pair(271.5)), 284);
chk('by the learner', !said(st, /taken over/));
st = F(BASE.concat([[185.1, 'dobutamine_drip'], [197.5, 'consult_cardiology'], [280.5, 'stop_dobutamine']], pair(281.5)), 300);
chk('on an inotrope: the same done 5 seconds before they arrive, cardiology gets there first', said(st, /taken over/) && st.phase === 'steadied');
lands('untreated shock: an inotrope started and stopped still moves her to the inotrope phase', IV.concat([[425.5, 'dobutamine_drip'], [430.5, 'stop_dobutamine']]), 450, 'presentation > obstructed > shock_untreated > shock_worse');

section('the wrong drugs have no unbound route (audit finding 11)');
st = F([[1.3, 'insert_iv'], [5.5, 'epinephrine_bolus']], 17);
chk('push-dose epinephrine is the inotrope', st.phase === 'shock_worse' && st.discouragedTaken.has('epinephrine_bolus'), st.phase);
chk('and satisfies the same case action', st.satisfied.has('dobutamine_drip'));
st = F([[1.3, 'insert_iv'], [5.5, 'furosemide_40_mg_iv']], 60);
chk('the diuretic is discouraged and costs eight points after twenty seconds', st.discouragedTaken.has('furosemide_40_mg_iv') && st.vitals.systolic_bp === 88, String(st.vitals.systolic_bp));
st = F(A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_bolus']]), 230);
chk('open question, pinned: push-dose phenylephrine is not the vasoconstrictor', st.phase === 'obstructed' && !st.satisfied.has('phenylephrine_drip'), st.phase);

section('results agree with each other (catalog audit 5.1 to 5.3)');
const order1 = (id, log, t) => F(log.concat([[t, id]]), t + 20).orders[id][0];
const LACT = { 20: '2.6', 190: '3.4', 430: '5.8' };
for (const t of [20, 190, 430]) for (const gasId of ['venous_blood_gas', 'arterial_blood_gas']) {
  const g = order1(gasId, A0, t + 0.5), l = order1('lactate', A0, t + 0.5);
  const row = label => g.value.components.find(x => x.label === label);
  chk(gasId + ' at ' + t + ' s: lactate ' + LACT[t] + ', as the lactate key', g.source === 'case' && row('Lactate').value === LACT[t] && l.value.components[0].value === LACT[t] && row('Lactate').abnormal, JSON.stringify(g.value.components));
  chk(gasId + ' at ' + t + ' s: bicarbonate as the chemistry', row('HCO3').value === order1('basic_chemistry_chem_7', A0, t + 0.5).value.components.find(x => x.label === 'Bicarbonate').value);
  chk(gasId + ' at ' + t + ' s: no pH or pCO2 is invented', !row('pH') && !row('pCO2'));
}
chk('the capillary glucose is the chemistry glucose', order1('fingerstick_blood_sugar', A0, 20.5).value.components[0].value ===
  order1('basic_chemistry_chem_7', A0, 20.5).value.components.find(x => x.label === 'Glucose').value);
chk('the chest film is authored, with the mediastinum the notes cite', order1('xr_chest', A0, 20.5).source === 'case' && /Mediastinum not widened/.test(order1('xr_chest', A0, 20.5).value.comment));
chk('and it is shown as a film, the read kept for the debrief', order1('xr_chest', A0, 20.5).value.kind === 'image' && order1('xr_chest', A0, 20.5).value.image === 'tako-cxr-normal');
chk('the ECG read quotes no rate', !/\d+\./.test(order1('ecg_12_lead', A0, 190.5).value.comment.split('.')[0]) && /^Sinus tachycardia\./.test(order1('ecg_12_lead', A0, 190.5).value.comment));
/* 13 October 2026. The ECG is a tracing per phase rate, with one read and no rate in the caption. */
chk('every ECG rule is a tracing with the one read and no rate in its caption',
  CASE.content_keys.imaging.ecg_12_lead.rules.every(r => r.value.kind === 'image' && r.value.comment === CASE.content_keys.imaging.ecg_12_lead.rules[0].value.comment && !/rate/i.test(r.value.caption)));
chk('no report carries a comment', Object.values(CASE.content_keys.imaging).every(k => !k.rules || k.rules.every(x => !x.value.comment || x.value.kind === 'image')));
chk('no comment names the diagnosis', Object.values(CASE.content_keys.labs).every(k => !k.rules || k.rules.every(x => !/takotsubo|infarct|obstruction/i.test(x.value.comment || ''))));
chk('every authored study has a case action and a note', AUTHORED_STUDIES.every(id => CASE.case_actions.some(a => a.catalog_id === id && a.debrief_note)), AUTHORED_STUDIES.join());

section('once steadied she says so (audit finding 10)');
const steadyLog = A0.concat([[185.5, 'normal_saline_500ml_bolus'], [186.5, 'phenylephrine_drip']]);
const askIn = (log, topic, t) => F(log.concat([{ t, kind: 'interview', topic, q: '?' }]), t + 1).readouts.pop().body;
chk('the pain is easing', /easing/.test(askIn(steadyLog, 'timing_progression', 230.5)) && /easing/.test(askIn(steadyLog, 'severity', 230.5)) && /easing/.test(askIn(steadyLog, 'chest_pain', 230.5)));
chk('the sweating has settled', /settled/.test(askIn(steadyLog, 'sweating', 230.5)));
chk('and she no longer says nothing makes it better', /easing now/.test(askIn(steadyLog, 'aggravating_relieving', 230.5)) && !/Nothing makes it better/.test(askIn(steadyLog, 'aggravating_relieving', 230.5)));
chk('every steadied answer sits before any flag rule', CASE.interview.topics.every(t => { const i = t.answer.findIndex(x => x.when === 'phase is steadied'), j = t.answer.findIndex(x => /^flag /.test(x.when || '')); return i < 0 || j < 0 || i < j; }));
chk('which is what the status line and the skin examination say', /pain easing/.test(JSON.stringify(CASE.content_keys.general_status)) && /Sweating has settled/.test(JSON.stringify(CASE.content_keys.exam.exam_skin)));
chk('on arrival it has not let up', /hasn't let up/.test(askIn(A0, 'timing_progression', 30.5)) && /drenched/.test(askIn(A0, 'sweating', 30.5)));
chk('with a low pressure she is still short', askIn(A0, 'sweating', 190.5) === "'Yes. Cold and clammy.'");

section('the interview bank and the held-out file (authoring 8.3 and 10.6)');
const topicOf = id => CASE.interview.topics.find(t => t.topic === id);
chk('a surgical history that reports an operation is not a pertinent negative', !topicOf('past_surgical_history').pertinent_negative);
chk('every pertinent negative denies in every phase', CASE.interview.topics.filter(t => t.pertinent_negative).every(t => t.answer.every(x => /^'(No|Never|None)\b/.test(x.value))),
  CASE.interview.topics.filter(t => t.pertinent_negative && !t.answer.every(x => /^'(No|Never|None)\b/.test(x.value))).map(t => t.topic).join());
const bank = CASE.interview.out_of_scope_bank.map(q => q.toLowerCase());
for (const q of ['have you ever had a stroke?', 'any back pain?', 'any black stools?', 'any blood when you open your bowels?'])
  chk('the out-of-scope bank does not refuse: ' + q, !bank.includes(q));
const variantsOf = id => topicOf(id).variants.map(x => x.toLowerCase());
chk('a stroke is asked of the bleeding topic', variantsOf('bleeding_risk').includes('have you ever had a stroke?'));
chk('"Any sweats?" belongs to sweating and not to fever', variantsOf('sweating').includes('any sweats?') && !variantsOf('fever_and_chills').includes('any sweats?') && !variantsOf('fever_and_chills').includes('have you been sweating?'));
chk('"Any palpitations?" belongs to palpitations only', variantsOf('palpitations').includes('any palpitations?') && !variantsOf('chest_pain').includes('any palpitations?'));
{
  const f = path.join(ROOT, 'cases', 'TAKO', 'TAKO-matcher-eval-questions.json');
  chk('a held-out question file exists', fs.existsSync(f));
  const held = JSON.parse(fs.readFileSync(f, 'utf8'));
  chk('with at least thirty out-of-scope questions', held.questions.filter(q => q.expect === null).length >= 30);
  chk('management_changing is the key topic list', JSON.stringify(held.management_changing.slice().sort()) === JSON.stringify(CASE.interview.key_topics.slice().sort()));
  const all = new Set();
  for (const t of CASE.interview.topics) for (const x of t.variants) all.add(x.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim());
  for (const x of CASE.interview.out_of_scope_bank) all.add(x.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim());
  const leaked = held.questions.filter(q => all.has(q.q.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim())).map(q => q.q);
  chk('no held-out question sits in a bank', leaked.length === 0, leaked.join(' | '));
}
