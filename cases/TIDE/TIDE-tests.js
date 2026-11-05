/* Case assertions for TIDE (severe pneumonia, septic shock, failing noninvasive support).
 *
 * Folds real logs through the shipped engine with fractional times. Covers the intended path,
 * the do-nothing walk, every clock and its warning in both modes, the oxygen effects, fluid
 * stacking, the severe-shock lactate, the intubation outcomes, the antibiotic credit, the
 * hidden targets and the nurse lines. Written 4 November 2026 by a language model.
 */
const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const F = (log, t, dm) => fold(mk(log), t, dm);
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const enteredAt = (st, id) => (st.phaseSeq.find(p => p.id === id) || {}).t;
const last = (st, key) => {
  const o = (st.orders[key] || []).filter(r => r.value).pop();
  return o ? { body: o.value } : st.readouts.filter(r => r.key === key).pop();
};
const comp = (st, key, label) => { const r = last(st, key); const c = r && r.body.components && r.body.components.find(c => c.label === label); return c && c.value; };
const LINE = [[1.3, 'attach_monitor'], [2.2, 'insert_iv']];
const ABX = [[4.1, 'ceftriaxone'], [4.6, 'azithromycin']];
const TUBE = t => [[t, 'etomidate_bolus'], [t + 0.4, 'rocuronium_bolus'], [t + 0.8, 'intubate_rapid_sequence']];
// Bolus at 10.5 enters fluid_response, the drift lands at 160.5, the drip at 170.5 enters on_pressor,
// the failing phase follows at 350.5.
const TO_PRESSOR = LINE.concat([[3.4, 'high_flow_nasal_cannula']], ABX,
  [[10.5, 'normal_saline_1l_bolus'], [170.5, 'norepinephrine_drip']]);

section('intended path');
let st = F(TO_PRESSOR.concat([[180.5, 'consult_critical_care'], [190.5, 'hydrocortisone_bolus'],
  [360.5, 'non_invasive_positive_pressure_ventilation'], [365.5, 'preoxygenate_for_intubation']],
  TUBE(370.5), [[380.5, 'fentanyl_bolus'], [390.5, 'propofol_infusion'], [400.5, 'xr_chest']]), 420);
chk('reaches ventilated', st.phase === 'ventilated', st.phase);
chk('through the drift and the failing phase',
  seq(st) === 'arrival > fluid_response > low_after_fluid > on_pressor > failing_support > ventilated', seq(st));
chk('the drift at 160.5', Math.abs(enteredAt(st, 'low_after_fluid') - 160.5) < 0.01, enteredAt(st, 'low_after_fluid'));
chk('the failing phase at 350.5', Math.abs(enteredAt(st, 'failing_support') - 350.5) < 0.01, enteredAt(st, 'failing_support'));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)), [...st.expected].filter(id => !st.satisfied.has(id)).join());
chk('the sedation follow-up is discharged', !st.fuOutstanding.has('sedation_after_the_tube'), [...st.fuOutstanding].join());
chk('the compression is said aloud', said(st, /moving the clock faster/));
chk('the high-flow narration names a hundred percent', said(st, /oxygen up to a hundred percent/));
chk('the BiPAP tube line', said(st, /Lowest sat was ninety-one/));
chk('the film shows the tube', last(st, 'xr_chest').body.image === 'tide-cxr-multifocal-ett');
chk('nothing halted or failed', !st.halted && !st.failed);

section('the do-nothing walk');
st = F([], 800);
chk('arrest at 660', seq(st) === 'arrival > presentation > low_pressure > worsening_shock > arrest', seq(st));
chk('entered arrest at 660', Math.abs(enteredAt(st, 'arrest') - 660) < 0.01, enteredAt(st, 'arrest'));
chk('the pressure drops at 360, two minutes of arrival and four of presentation', Math.abs(enteredAt(st, 'low_pressure') - 360) < 0.01, enteredAt(st, 'low_pressure'));
chk('worsening shock grants severe_shock', st.flags.has('severe_shock'));
st = F([], 800, 3);
chk('the same walk in the default mode', seq(st) === 'arrival > presentation > low_pressure > worsening_shock > arrest', seq(st));
const fp = st.promptFires.filter(p => p.id === 'normal_saline_1l_bolus').map(p => p.t);
chk('the default-mode fluid prompt lands before the drop with room', fp.length && fp[0] <= 340, fp.join());

section('the quiet start (owner, 5 November 2026)');
{
  /* Default mode: the oxygen question at 1:00, then nothing at all until 4:00. Easy mode keeps
     the same phases, so its asks come sooner but still not inside arrival after oxygen. */
  const n = F([], 400, 3);
  const firsts = n.promptFires.map(p => p.id + '@' + p.t);
  chk('default mode: the oxygen question at 60', n.promptFires.length && n.promptFires[0].id === 'hidden_oxygen' && Math.abs(n.promptFires[0].t - 60) < 0.01, firsts.join());
  chk('default mode: no prompt between 60 and 240', n.promptFires.every(p => p.t <= 60.01 || p.t >= 239.99), firsts.join());
  chk('default mode: the fluid question at 240', n.promptFires.some(p => p.id === 'normal_saline_1l_bolus' && Math.abs(p.t - 240) < 0.01), firsts.join());
  chk('default mode: support at 255 and the antibiotic at 270',
      n.promptFires.some(p => p.id === 'hidden_support' && Math.abs(p.t - 255) < 0.01) &&
      n.promptFires.some(p => p.id === 'hidden_beta_lactam' && Math.abs(p.t - 270) < 0.01), firsts.join());
  chk('default mode: the nurse says nothing at all between 61 and 239', n.nurse.every(x => x.t <= 60.01 || x.t >= 239.99),
      n.nurse.filter(x => x.t > 60.01 && x.t < 239.99).map(x => x.t + ' ' + x.text).join(' | '));
  chk('the move from arrival to presentation is silent', !n.nurse.some(x => Math.abs(x.t - 120) < 0.01));
  const e = F([], 400, 1);
  chk('easy mode: the oxygen question at 20, nothing else until 160', e.promptFires.length && e.promptFires[0].id === 'hidden_oxygen' &&
      e.promptFires.slice(1).every(p => p.t >= 159.99), e.promptFires.map(p => p.id + '@' + p.t).join());
  chk('the oxygen question is not asked again in presentation', F([], 400, 3).promptFires.filter(p => p.id === 'hidden_oxygen').length === 1);
}

section('warnings in the default mode, every clock');
const warned = (log, id, phase, until) => {
  const s = F(log, until, 3);
  const at = enteredAt(s, phase);
  return s.promptFires.some(p => p.id === id && p.t >= at && p.t <= at + until);
};
st = F(LINE.concat([[10.5, 'normal_saline_1l_bolus']]), 400, 3);
const lowAt = enteredAt(st, 'low_after_fluid');
const pp = st.promptFires.filter(p => p.id === 'norepinephrine_drip' && p.t >= lowAt).map(p => p.t);
chk('the pressor prompt in pressure-low-again comes at least 20 s before the drop', pp.length && pp[0] <= lowAt + 130, pp.join() + ' from ' + lowAt);
st = F(TO_PRESSOR, 700, 3);
const failAt = enteredAt(st, 'failing_support');
const ip = st.promptFires.filter(p => p.id === 'intubate_rapid_sequence' && p.t >= failAt).map(p => p.t);
chk('the intubation prompt in the failing phase comes 20 s or more before tiring', ip.length && ip[0] <= failAt + 130, ip.join() + ' from ' + failAt);
const tirAt = enteredAt(st, 'tiring');
const ip2 = st.promptFires.filter(p => p.id === 'intubate_rapid_sequence' && p.t >= tirAt).map(p => p.t);
chk('and again in tiring, 20 s or more before arrest', ip2.length && ip2[0] <= tirAt + 100, ip2.join() + ' from ' + tirAt);
chk('the default-mode walk from the pressor ends in arrest', st.phase === 'arrest', seq(st));

section('the monitor: devices, fluid, the tube');
const v = (log, t) => F(log, t).vitals;
chk('room air 85 at 32', v(LINE, 5).oxygen_saturation === 85 && v(LINE, 5).respiratory_rate === 32);
chk('cannula 88', v(LINE.concat([[3.4, 'nasal_cannula_oxygen']]), 8).oxygen_saturation === 88);
chk('mask 91 at 30', v(LINE.concat([[3.4, 'non_rebreather_mask']]), 8).oxygen_saturation === 91 && v(LINE.concat([[3.4, 'non_rebreather_mask']]), 8).respiratory_rate === 30);
chk('high flow 92 at 30', v(LINE.concat([[3.4, 'high_flow_nasal_cannula']]), 8).oxygen_saturation === 92);
chk('NIV 93 at 28', v(LINE.concat([[3.4, 'non_invasive_positive_pressure_ventilation']]), 8).oxygen_saturation === 93 && v(LINE.concat([[3.4, 'non_invasive_positive_pressure_ventilation']]), 8).respiratory_rate === 28);
chk('the last device wins: high flow then cannula reads 88',
  v(LINE.concat([[3.4, 'high_flow_nasal_cannula'], [5.4, 'nasal_cannula_oxygen']]), 8).oxygen_saturation === 88);
chk('NIV then cannula restores the rate', v(LINE.concat([[3.4, 'non_invasive_positive_pressure_ventilation'], [5.4, 'nasal_cannula_oxygen']]), 8).respiratory_rate === 32);
st = F(TO_PRESSOR, 360);
chk('failing on high flow reads 88 at 38 (ROX 2.3 at FiO2 1.0)', st.vitals.oxygen_saturation === 88 && st.vitals.respiratory_rate === 38, JSON.stringify(st.vitals));
const B3 = LINE.concat([[3.4, 'high_flow_nasal_cannula'], [10.5, 'normal_saline_1l_bolus'], [12.5, 'normal_saline_1l_bolus'], [14.5, 'lactated_ringer_s_1l_bolus']]);
chk('the third bolus costs three points of saturation and four breaths', v(B3, 20).oxygen_saturation === 89 && v(B3, 20).respiratory_rate === 34, JSON.stringify(v(B3, 20)));
chk('two boluses cost nothing', v(B3.slice(0, -1), 20).oxygen_saturation === 92);
chk('the third bolus is discouraged', tagOf('normal_saline_1l_bolus', F(B3.slice(0, -1), 14)) === 'discouraged');
chk('the first bolus is critical on arrival', tagOf('normal_saline_1l_bolus', F(LINE, 5)) === 'critical');
st = F(TO_PRESSOR.concat([[360.5, 'non_invasive_positive_pressure_ventilation']], TUBE(365.5)), 375);
chk('ventilated: the monitor shows the ventilator rate', st.vitals.respiratory_rate === 24, JSON.stringify(st.vitals));
chk('BiPAP preoxygenation: a nadir near 92 for 30 s', st.vitals.oxygen_saturation === 92, JSON.stringify(st.vitals));
chk('and back to 95 after', F(TO_PRESSOR.concat([[360.5, 'non_invasive_positive_pressure_ventilation']], TUBE(365.5)), 400).vitals.oxygen_saturation === 95);
st = F(TO_PRESSOR.concat(TUBE(365.5)), 375);
chk('high-flow preoxygenation: a nadir of 85', st.vitals.oxygen_saturation === 85, JSON.stringify(st.vitals));
chk('and the middle nurse line', said(st, /dipped to the mid-eighties/));
st = F(LINE.concat([[3.4, 'non_rebreather_mask'], [10.5, 'normal_saline_1l_bolus'], [170.5, 'norepinephrine_drip']], TUBE(365.5)), 375);
chk('mask preoxygenation: a nadir of 77', st.vitals.oxygen_saturation === 77, JSON.stringify(st.vitals));
chk('and the low nurse line', said(st, /dropped into the seventies/));
chk('the drip carries him: the pressure dips by 14 for a minute', F(TO_PRESSOR.concat(TUBE(365.5)), 375).vitals.systolic_bp === 80);

section('pressure, fluid and the vasopressor');
chk('a drip on arrival holds him at the drop', seq(F(LINE.concat([[3.5, 'norepinephrine_drip']]), 400)) === 'arrival > presentation > on_pressor');
chk('a drip during the fluid response holds him at the drift',
  seq(F(LINE.concat([[10.5, 'normal_saline_1l_bolus'], [20.5, 'norepinephrine_drip']]), 200)) === 'arrival > fluid_response > on_pressor');
chk('fluid late moves pressure-low to the fluid response',
  seq(F(LINE.concat([[370.5, 'normal_saline_1l_bolus']]), 380)) === 'arrival > presentation > low_pressure > fluid_response');
chk('a drip without fluid from pressure-low', seq(F(LINE.concat([[370.5, 'norepinephrine_drip']]), 380)) === 'arrival > presentation > low_pressure > on_pressor');
for (const d of ['vasopressin_drip', 'epinephrine_drip', 'phenylephrine_drip', 'dopamine_drip']) {
  st = F(LINE.concat([[10.5, 'normal_saline_1l_bolus'], [170.5, d]]), 180);
  chk(d + ' holds him and meets the vasopressor expectation', st.phase === 'on_pressor' && st.satisfied.has('norepinephrine_drip'), st.phase);
}
chk('dopamine is discouraged', F(LINE, 5) && tagOf('dopamine_drip', F(LINE, 5)) === 'discouraged');
st = F(LINE.concat([[10.5, 'normal_saline_1l_bolus'], [400.5, 'norepinephrine_drip']]), 410);
chk('a late pressor still rescues', st.phase === 'on_pressor' && st.flags.has('severe_shock'), seq(st));
st = F(LINE.concat([[10.5, 'normal_saline_1l_bolus'], [400.5, 'norepinephrine_drip'], [405.5, 'lactate']]), 420);
chk('and the lactate reads 5.4 from then on', comp(st, 'lactate', 'Lactate') === '5.4', comp(st, 'lactate', 'Lactate'));
st = F(TO_PRESSOR.concat([[175.5, 'lactate']]), 190);
chk('on time, the lactate reads 3.8', comp(st, 'lactate', 'Lactate') === '3.8');
st = F(TO_PRESSOR.concat([[175.5, 'stop_norepinephrine']]), 220);
chk('stopping the drip drops the monitor and changes no phase', st.phase === 'on_pressor' && st.vitals.systolic_bp === 70, JSON.stringify(st.vitals));
st = F(TO_PRESSOR.concat([[175.5, 'stop_norepinephrine'], [180.5, 'norepinephrine_drip']]), 220);
chk('restarting it brings the pressure back', st.vitals.systolic_bp === 94, JSON.stringify(st.vitals));

section('intubation outcomes');
st = F(LINE.concat(TUBE(5.5)), 10);
chk('a tube on arrival with nothing running collapses him', st.phase === 'post_induction_collapse', seq(st));
chk('with the collapse line', said(st, /pressure is falling fast/));
st = F(LINE.concat(TUBE(5.5), [[15.5, 'phenylephrine_bolus']]), 30);
chk('a push-dose bolus bridges without leaving', st.phase === 'post_induction_collapse' && st.satisfied.has('hidden_push_dose'));
st = F(LINE.concat(TUBE(5.5), [[15.5, 'norepinephrine_drip']]), 30);
chk('a drip rescues the collapse', st.phase === 'ventilated', seq(st));
st = F(LINE.concat(TUBE(5.5)), 200);
chk('no drip: arrest 120 s after the collapse', st.phase === 'arrest' && Math.abs(enteredAt(st, 'arrest') - 125.5 - 0.8 + 0.8) < 1.5, seq(st) + ' ' + enteredAt(st, 'arrest'));
st = F(TO_PRESSOR.concat(TUBE(200.5)), 210);
chk('early intubation on the drip skips the failing phase', st.phase === 'ventilated' && !seq(st).includes('failing'), seq(st));
chk('the decision to intubate is neutral before phase 7', tagOf('intubate_rapid_sequence', F(TO_PRESSOR, 200)) === 'neutral');
chk('and critical in phase 7', tagOf('intubate_rapid_sequence', F(TO_PRESSOR, 360)) === 'critical');
st = F(TO_PRESSOR.concat(TUBE(365.5)), 600);
chk('a rocuronium tube with no sedation draws the comfort question', said(st, /Is he comfortable\? He can't move/));
st = F(TO_PRESSOR.concat([[300.5, 'fentanyl_bolus']], TUBE(365.5)), 600);
chk('fentanyl before the tube does not count as sedation after it', said(st, /Is he comfortable/));

section('antibiotics and the steroid');
st = F(LINE.concat([[4.1, 'ceftriaxone']]), 10);
chk('ceftriaxone meets the beta-lactam and not atypical cover', st.satisfied.has('hidden_beta_lactam') && !st.satisfied.has('hidden_atypical'));
st = F(LINE.concat([[4.1, 'levofloxacin']]), 10);
chk('levofloxacin alone meets atypical cover only', st.satisfied.has('hidden_atypical') && !st.satisfied.has('hidden_beta_lactam'));
st = F(LINE.concat([[4.1, 'piperacillin_tazobactam'], [4.6, 'vancomycin']]), 10);
chk('piperacillin-tazobactam meets the beta-lactam', st.satisfied.has('hidden_beta_lactam'));
chk('the antibiotic changes no phase',
  seq(F(TO_PRESSOR, 400)) === seq(F(TO_PRESSOR.filter(e => !['ceftriaxone', 'azithromycin'].includes(e[1])), 400)));
chk('hydrocortisone is recommended on the pressor and neutral before',
  tagOf('hydrocortisone_bolus', F(TO_PRESSOR, 200)) === 'recommended' && tagOf('hydrocortisone_bolus', F(LINE, 5)) === 'neutral');
st = F(TO_PRESSOR.concat([[190.5, 'methylprednisolone_bolus']]), 200);
chk('methylprednisolone meets the steroid', st.satisfied.has('hydrocortisone_bolus'));

section('results');
st = F(LINE.concat([[3.4, 'high_flow_nasal_cannula'], [5.5, 'arterial_blood_gas']]), 15);
chk('the arterial gas on high flow: PaO2 66 at saturation 92', comp(st, 'arterial_blood_gas', 'pO2') === '66', comp(st, 'arterial_blood_gas', 'pO2'));
st = F(LINE.concat([[5.5, 'arterial_blood_gas']]), 15);
chk('on room air: 51', comp(st, 'arterial_blood_gas', 'pO2') === '51');
st = F(TO_PRESSOR.concat([[355.5, 'venous_blood_gas']]), 370);
chk('the failing phase gas: pH 7.18, pCO2 56', comp(st, 'venous_blood_gas', 'pH') === '7.18' && comp(st, 'venous_blood_gas', 'pCO2') === '56');
st = F(LINE.concat([[5.5, 'ultrasound_cardiac']]), 20);
chk('before fluid the cava is small', /Small inferior vena cava/.test(last(st, 'ultrasound_cardiac').body.report));
chk('and the ultrasound after fluid credits reassessment',
  F(LINE.concat([[10.5, 'normal_saline_1l_bolus'], [20.5, 'ultrasound_cardiac']]), 40).satisfied.has('hidden_reassessed'));
chk('a scan before fluid does not', !F(LINE.concat([[5.5, 'ultrasound_cardiac']]), 40).satisfied.has('hidden_reassessed'));

section('properties');
for (const a of CASE.case_actions) {
  if (a.prompt) {
    chk(a.catalog_id + ': its prompt quotes no number', !/\d/.test(a.prompt.text) && !(a.prompt.escalation && /\d/.test(a.prompt.escalation.text)));
  }
}
chk('no clock in the ventilated phase', CASE.phases.find(p => p.id === 'ventilated').transitions.every(t => t.after_seconds == null));
st = F(LINE.concat([[1.5, 'handoff_submit']]), 5);
chk('handoff at once completes the run', st.phase === 'case_complete' && st.complete);
