/* Case assertions for ALLEY (methanol poisoning, washer fluid).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * One section per claim the case makes. Fractional times where two events meet.
 */

const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const START = [[1, 'attach_monitor'], [2, 'insert_iv']];
const LABS = [[10, 'venous_blood_gas'], [10, 'basic_chemistry_chem_7'], [10, 'ethanol_level_etoh'], [10, 'osmolality']];
const V = (log, t) => fold(mk(log), t).vitals;
const lastRead = (st, key) => st.readouts.filter(r => r.key === key).pop();
const gasPh = (st, key) => {
  const o = (st.orders[key || 'venous_blood_gas'] || []).slice(-1)[0];
  const c = o && o.value && o.value.components && o.value.components.find(x => x.label === 'pH');
  return c ? c.value : null;
};

section('intended path');
let st = fold(mk(START.concat(LABS, [[20, 'exam_heent'], [21, 'exam_neuro'], [22, 'exam_abd'], [30, 'fomepizole'], [40, 'na_bicarbonate_bolus'],
  [45, 'folinic_acid'], [50, 'consult_toxicology'], [60, 'consult_renal'], [70, 'handoff_submit']])), 80);
chk('reaches case complete through held and improving',
  seq(st) === 'presentation > held_early > improving > case_complete', seq(st));
chk('nothing halted or failed', !st.halted && !st.failed);
chk('nephrology was not blocked', !st.blocked.some(b => b.id === 'consult_renal'), JSON.stringify(st.blocked));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)),
  [...st.expected].filter(id => !st.satisfied.has(id)).join(', '));

section('doing nothing');
chk('still on arrival at 359', fold(mk([]), 359).phase === 'presentation');
st = fold(mk([]), 361);
chk('drifting at 360', st.phase === 'drifting', st.phase);
chk('and the vision tier moved', st.flags.has('reached_u1'));
st = fold(mk([]), 541);
chk('the floor at 540, 180 s later', st.phase === 'untreated_floor', st.phase);
chk('worst vision tier', st.flags.has('reached_u2'));
st = fold(mk([]), 3000);
chk('and the case never ends on the clock', st.phase === 'untreated_floor' && !st.failed && !st.complete && !st.halted, st.phase);
chk('the nurse asked for a gas and about his eyes on arrival',
  fold(mk([]), 359).promptFires.some(p => p.id === 'venous_blood_gas') &&
  fold(mk([]), 359).promptFires.some(p => p.id === 'interview_topic_vision'),
  JSON.stringify(fold(mk([]), 359).promptFires));
chk('normal mode: both arrival prompts land before the 360-second drift',
  ['venous_blood_gas', 'interview_topic_vision'].every(id =>
    fold(mk([]), 360.5, 3).promptFires.some(p => p.id === id && p.t < 360)),
  JSON.stringify(fold(mk([]), 360.5, 3).promptFires));
chk('normal mode: the osmolality prompt lands inside the 180-second second tier',
  fold(mk([[10, 'ethanol_level_etoh']]), 540.5, 3).promptFires.some(p => p.id === 'osmolality'),
  JSON.stringify(fold(mk([[10, 'ethanol_level_etoh']]), 540.5, 3).promptFires));
chk('the floor prompts for the antidote and then escalates',
  fold(mk([]), 700).promptFires.some(p => p.id === 'fomepizole' && p.level === 1) &&
  fold(mk([]), 700).promptFires.some(p => p.id === 'fomepizole' && p.level === 2),
  JSON.stringify(fold(mk([]), 700).promptFires));

section('fomepizole freezes him at his tier');
st = fold(mk(START.concat([[30, 'fomepizole']])), 600);
chk('held at the arrival tier, no drift', st.phase === 'held_early', st.phase);
chk('vitals unchanged from arrival', st.vitals.respiratory_rate === 27 && st.vitals.heart_rate === 112, JSON.stringify(st.vitals));
st = fold(mk(START.concat([[30, 'fomepizole'], [40, 'venous_blood_gas']])), 50);
chk('a gas after fomepizole still reads 7.19', gasPh(st) === '7.19', gasPh(st));
st = fold(mk(START.concat([[370, 'fomepizole']])), 700);
chk('given after the drift, held at the second tier', st.phase === 'held_mid', st.phase);
st = fold(mk(START.concat([[30, 'fomepizole'], [150, 'na_bicarbonate_bolus']])), 160);
chk('bicarbonate in a held phase moves him to improving', st.phase === 'improving', st.phase);
st = fold(mk(START.concat([[30, 'fomepizole'], [150, 'na_bicarbonate_bolus'], [160, 'venous_blood_gas']])), 170);
chk('and the gas is better', gasPh(st) === '7.29', gasPh(st));
chk('the bicarbonate prompt fires in a held phase',
  fold(mk(START.concat([[30, 'fomepizole']])), 200).promptFires.some(p => p.id === 'na_bicarbonate_bolus'));

section('bicarbonate alone does not stop the clock');
st = fold(mk(START.concat([[60, 'na_bicarbonate_bolus']])), 100);
chk('still the arrival phase', st.phase === 'presentation', st.phase);
chk('the monitor shows the buffered numbers', st.vitals.respiratory_rate === 24 && st.vitals.heart_rate === 104, JSON.stringify(st.vitals));
st = fold(mk(START.concat([[60, 'na_bicarbonate_bolus'], [90, 'venous_blood_gas']])), 100);
chk('a gas while it acts reads 7.28', gasPh(st) === '7.28', gasPh(st));
st = fold(mk(START.concat([[30, 'na_bicarbonate_bolus']])), 230);
chk('it lapses after 180 seconds', !st.flags.has('bicarb_acting') && st.vitals.respiratory_rate === 27, JSON.stringify(st.vitals));
st = fold(mk(START.concat([[200, 'na_bicarbonate_bolus']])), 361);
chk('the drift still comes at 360', st.phase === 'drifting', st.phase);
st = fold(mk(START.concat([[30, 'na_bicarbonate_bolus'], [100, 'fomepizole']])), 110);
chk('fomepizole while it acts goes straight to improving', seq(st) === 'presentation > improving', seq(st));
st = fold(mk(START.concat([[10, 'na_bicarbonate_bolus'], [200, 'fomepizole']])), 210);
chk('fomepizole after it lapses goes to held', st.phase === 'held_early', st.phase);
st = fold(mk(START.concat([[179.5, 'na_bicarbonate_bolus']])), 359.6);
chk('fractional: a bolus lapsing just before the drift', st.phase === 'presentation' && !st.flags.has('bicarb_acting'), st.phase);

section('time away before the antidote');
st = fold(mk(START.concat([[30, 'ct_head']])), 36);
chk('a CT on arrival costs a tier', st.phase === 'drifting' && st.flags.has('reached_u1'), seq(st));
st = fold(mk(START.concat([[30, 'ct_head']])), 60);
chk('one tier per trip, no second move from the same order', st.phase === 'drifting', seq(st));
st = fold(mk(START.concat([[30, 'ct_head'], [40, 'attempt_observation']])), 60);
chk('a second trip away in the next tier costs the next tier', st.phase === 'untreated_floor', seq(st));
st = fold(mk(START.concat([[20, 'fomepizole'], [30, 'ct_head']])), 60);
chk('after fomepizole it costs nothing', st.phase === 'held_early', seq(st));
st = fold(mk(START.concat([[30, 'attempt_observation']])), 36);
chk('the hallway on arrival costs a tier', st.phase === 'drifting', seq(st));
chk('and was recorded as discouraged', st.discouragedTaken.has('attempt_observation'));
chk('observation is intercepted before the antidote', handoffIntercept(fold(mk(START), 10), 'observation_unit') === 'attempt_observation');
chk('and not after it', !handoffIntercept(fold(mk(START.concat([[5, 'fomepizole']])), 10), 'observation_unit'));

section('discharge is a case failure');
chk('discharge is intercepted on arrival', handoffIntercept(fold(mk(START), 10), 'discharge_home') === 'attempt_discharge');
chk('and when improving', handoffIntercept(fold(mk(START.concat([[5, 'fomepizole'], [6, 'na_bicarbonate_bolus']])), 10), 'discharge_home') === 'attempt_discharge');
st = fold(mk(START.concat([[30, 'attempt_discharge']])), 40);
chk('the run ends in the discharged phase', st.phase === 'discharged', st.phase);
chk('not as a completed handoff', !st.complete, String(st.complete));

section('sedation');
st = fold(mk(START.concat([[30, 'lorazepam_bolus']])), 40);
chk('lorazepam before treatment halts', st.halted && st.phase === 'halted', st.phase);
st = fold(mk(START.concat([[20, 'fomepizole'], [30, 'lorazepam_bolus']])), 40);
chk('and in a held phase', st.halted, st.phase);
st = fold(mk(START.concat([[20, 'fomepizole'], [25, 'na_bicarbonate_bolus'], [30, 'lorazepam_bolus']])), 60);
chk('when improving it does not halt', !st.halted && st.phase === 'improving', st.phase);
chk('and the overlay shows', st.vitals.respiratory_rate === 16, JSON.stringify(st.vitals));
st = fold(mk(START.concat([[30, 'midazolam_bolus']])), 60);
chk('midazolam is ungraded and does not halt', !st.halted && st.phase === 'presentation', st.phase);
chk('the overlay shows on arrival', st.vitals.respiratory_rate === 21, JSON.stringify(st.vitals));
st = fold(mk(START.concat([[30, 'midazolam_bolus'], [40, 'venous_blood_gas']])), 50);
chk('and the gas shows it', gasPh(st) === '7.07', gasPh(st));
st = fold(mk(START.concat([[30, 'midazolam_bolus']])), 190);
chk('and it wears off at 150 seconds', !st.flags.has('sedated') && st.vitals.respiratory_rate === 27, JSON.stringify(st.vitals));

section('blocks');
st = fold(mk(START.concat([[20, 'intubate_rapid_sequence']])), 30);
chk('intubation is blocked', st.blocked.some(b => b.id === 'intubate_rapid_sequence') && !st.flags.has('intubated'));
chk('with the attending\'s question', /indication/.test((st.blocked.find(b => b.id === 'intubate_rapid_sequence') || {}).message || ''),
  JSON.stringify(st.blocked));
st = fold(mk(START.concat([[5, 'consult_renal']])), 10);
chk('nephrology wants the gas and chemistry first', st.blocked.some(b => b.id === 'consult_renal' && /gas and his chemistry/.test(b.message)), JSON.stringify(st.blocked));
st = fold(mk(START.concat([[5, 'venous_blood_gas'], [5, 'basic_chemistry_chem_7'], [20, 'consult_renal']])), 25);
chk('then a reason to suspect', st.blocked.some(b => b.id === 'consult_renal' && /what he drank/.test(b.message)), JSON.stringify(st.blocked));
st = fold(mk(START.concat([[5, 'venous_blood_gas'], [5, 'basic_chemistry_chem_7'], [15, 'exam_heent'], [20, 'consult_renal']])), 25);
chk('the eye exam is enough', st.satisfied.has('consult_renal'), JSON.stringify(st.blocked));
st = fold(mk(START.concat([[5, 'fomepizole']])), 3);
chk('fomepizole needs a line', fold(mk([[5, 'fomepizole']]), 10).blocked.some(b => b.id === 'fomepizole'));

section('vision');
st = fold(mk(START.concat([[20, 'exam_heent']])), 25);
chk('the eye exam counts as asking about vision', st.satisfied.has('interview_topic_vision'));
st = fold(mk([[370, 'exam_heent']]), 380);
chk('the exam worsens with the tier', /monitor/.test(lastRead(st, 'exam_heent').body.findings), lastRead(st, 'exam_heent').body.findings);
st = fold(mk([[30, 'insert_iv'], [370, 'fomepizole'], [380, 'na_bicarbonate_bolus'], [390, 'exam_heent']]), 400);
chk('and stays at the tier reached after treatment', st.phase === 'improving' && /monitor/.test(lastRead(st, 'exam_heent').body.findings));

section('no prompt quotes a vital sign');
chk('no prompt text has a digit', Object.keys(ACT).every(id => {
  const p = ACT[id].prompt; if (!p) return true;
  return !/\d/.test(p.text) && !(p.escalation && /\d/.test(p.escalation.text));
}));

section('trauma survey');
chk('head, neurological and abdominal exams are critical on arrival',
  ['exam_heent', 'exam_neuro', 'exam_abd'].every(id => tagOf(id, fold(mk([]), 5)) === 'critical'));
chk('and when improving',
  ['exam_heent', 'exam_neuro', 'exam_abd'].every(id => tagOf(id, fold(mk(START.concat([[5, 'fomepizole'], [6, 'na_bicarbonate_bolus']])), 10)) === 'critical'));
st = fold(mk(START.concat(LABS, [[30, 'fomepizole'], [40, 'na_bicarbonate_bolus'], [70, 'handoff_submit']])), 80);
chk('skipping them leaves them expected and not done',
  ['exam_neuro', 'exam_abd'].every(id => st.expected.has(id) && !st.satisfied.has(id)), [...st.expected].join());
