/* Case assertions for TAKO (takotsubo with outflow obstruction).
 *
 * New to this pack: a cardiologist who takes over ninety seconds after being called, a
 * case-only button on the Consults tab, two phases with the same numbers and different
 * exits, and a clock that fires whatever the learner does. Times are fractional on
 * purpose (see the v0.21 timing fault).
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
chk('takes over from an inotrope too', st.phase === 'steadied' && said(st, /stopped the inotrope/), st.phase);

section('the wrong drugs show what they do and can be undone');
st = F([[1.3, 'insert_iv'], [5.5, 'nitroglycerin']], 17);
chk('nitroglycerin: obstructed in ten seconds', st.phase === 'obstructed' && st.vitals.systolic_bp === 82 - 12, st.phase + ' ' + st.vitals.systolic_bp);
chk('and the extra fall wears off', F([[1.3, 'insert_iv'], [5.5, 'nitroglycerin']], 130).vitals.systolic_bp === 82);
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
chk('the ECG describes and does not name', /ST elevation/.test(st.orders.ecg_12_lead[0].value.report) && !/takotsubo|infarct/i.test(st.orders.ecg_12_lead[0].value.report));
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
  diagnoses: ['dx_st_elevation_myocardial_infarction', 'dx_takotsubo_cardiomyopathy', 'dx_cardiogenic_shock'] } }]), 40);
let hs = summaryScores(st).find(r => r.id === 'handoff');
chk('the lab with an infarct first and takotsubo beside it scores 100', hs.points === 100, JSON.stringify(hs));
st = F(A0.concat([{ t: 30.5, actionId: 'handoff_submit', payload: { disposition: 'cath_lab', diagnoses: ['dx_takotsubo_cardiomyopathy'] } }]), 40);
hs = summaryScores(st).find(r => r.id === 'handoff');
chk('takotsubo named first is defensible, not correct', /primary diagnosis defensible/.test(hs.detail), hs.detail);
st = F([{ t: 190.5, actionId: 'handoff_submit', payload: { disposition: 'icu', diagnoses: ['dx_panic_attack'] } }], 200);
chk('handed over hypotensive, shown hypotensive', st.vitals.systolic_bp === 82);

section('what the nurse says is true of the monitor');
for (const p of CASE.phases) for (const tr of (p.transitions || [])) {
  if (!tr.narration) continue;
  const dest = CASE.phases.find(x => x.id === tr.to).vitals;
  const bp = tr.narration.match(/(\d+) over (\d+)/);
  if (bp) chk(p.id + ' to ' + tr.to + ': ' + bp[0], +bp[1] === dest.systolic_bp && +bp[2] === dest.diastolic_bp, dest.systolic_bp + '/' + dest.diastolic_bp);
  const hr = tr.narration.match(/[Rr]ate (?:is |of |down to |is down to )?(\d+)/);
  if (hr) chk(p.id + ' to ' + tr.to + ': rate ' + hr[1], +hr[1] === dest.heart_rate, String(dest.heart_rate));
}
