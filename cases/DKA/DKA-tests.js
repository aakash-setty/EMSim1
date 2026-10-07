/* Case assertions for DKA (mild ketoacidosis with a low potassium).
 *
 * New to this pack: no clock that changes her, order carried by which phase an action
 * lands in, a restart read from a repeat-granted flag, and laboratory results keyed to
 * flags inside the arrival phase. Times are fractional on purpose (see the v0.21 timing
 * fault).
 */
const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const F = (log, t, dm) => fold(mk(log), t, dm);
const A0 = [[1.3, 'attach_monitor'], [2.1, 'insert_iv'], [3.4, 'fingerstick_blood_sugar'],
            [4.4, 'venous_blood_gas'], [5.2, 'basic_chemistry_chem_7']];
const last = (st, key) => {
  const o = (st.orders[key] || []).filter(r => r.value).pop();
  return o ? { body: o.value } : st.readouts.filter(r => r.key === key).pop();
};
const K = st => { const r = last(st, 'basic_chemistry_chem_7'); return r && r.body.components.find(c => c.label === 'Potassium').value; };

section('intended path');
let st = F(A0.concat([[12.5, 'normal_saline_1l_bolus'], [20.5, 'potassium_chloride_kcl'], [21.5, 'magnesium_sulfate'],
  [45.5, 'basic_chemistry_chem_7'], [52.5, 'insulin_drip'], [70.5, 'd5_1_2_ns_infusion']]), 80);
chk('reaches treated', st.phase === 'treated', st.phase);
chk('through potassium_replaced', seq(st) === 'presentation > potassium_replaced > treated', seq(st));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)), [...st.expected].filter(id => !st.satisfied.has(id)).join());
chk('nothing halted, failed or completed', !st.halted && !st.failed && !st.complete);
chk('no follow-up left open', st.fuOutstanding.size === 0, [...st.fuOutstanding].join());

section('nothing happens on the clock');
chk('untouched for ten minutes she is as she arrived', seq(F([], 600)) === 'presentation');
chk('with the workup done and nothing given, the same', seq(F(A0, 600)) === 'presentation');
chk('no timed transition ever fires on inaction', F(A0, 600).timeFires.length === 0);

section('the monitor: phases are authored without fluid, and fluid is an effect');
const v = (log, t) => F(log, t).vitals;
chk('arrival 112, 104/64', v(A0, 20).heart_rate === 112 && v(A0, 20).systolic_bp === 104);
chk('after a bolus 102, 110/64', v(A0.concat([[10.5, 'normal_saline_500ml_bolus']]), 30).heart_rate === 102 &&
  v(A0.concat([[10.5, 'normal_saline_500ml_bolus']]), 30).systolic_bp === 110);
chk('two boluses do not stack', v(A0.concat([[10.5, 'normal_saline_1l_bolus'], [12.5, 'lactated_ringer_s_1l_bolus']]), 30).heart_rate === 102);
chk('fluid changes no phase', F(A0.concat([[10.5, 'normal_saline_1l_bolus']]), 300).phase === 'presentation');

section('insulin before potassium');
for (const drug of ['insulin_drip', 'insulin_subcutaneous', 'insulin_bolus']) {
  st = F(A0.concat([[20.5, drug]]), 40);
  chk(drug + ' on arrival drives the potassium down', st.phase === 'potassium_falling', st.phase);
  chk(drug + ' is tagged discouraged there', st.discouraged && [...st.discouraged].includes(drug) || tagOf(drug, F(A0, 20)) === 'discouraged');
}
st = F(A0.concat([[20.5, 'insulin_drip']]), 29);
chk('not before ten seconds', st.phase === 'presentation');
st = F(A0.concat([[20.5, 'insulin_drip']]), 40);
chk('the nurse says she is weak', said(st, /arms and legs feel heavy/));
chk('rate 118 without fluid', st.vitals.heart_rate === 118);
st = F(A0.concat([[20.5, 'insulin_drip'], [40.5, 'basic_chemistry_chem_7'], [41.5, 'ecg_12_lead']]), 60);
chk('a repeat chemistry shows 2.6', K(st) === '2.6', K(st));
chk('the ECG shows prominent U waves and a QTc of 520', /Prominent U waves/.test(last(st, 'ecg_12_lead').body.report) && /520/.test(last(st, 'ecg_12_lead').body.report));
st = F(A0.concat([[20.5, 'insulin_drip']]), 60);
chk('the nurse suggests holding it at 25 seconds', st.promptFires.some(p => p.id === 'stop_insulin'));
st = F(A0.concat([[20.5, 'insulin_drip']]), 85);
chk('and potassium at 45', st.promptFires.some(p => p.id === 'potassium_chloride_kcl'));

section('the rescue needs both steps');
const early = A0.concat([[20.5, 'insulin_drip']]);
chk('potassium alone: still falling', F(early.concat([[40.5, 'potassium_chloride_kcl']]), 200).phase === 'potassium_falling');
chk('hold alone: still falling', F(early.concat([[40.5, 'stop_insulin']]), 200).phase === 'potassium_falling');
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 70);
chk('both: recovering after twenty seconds', st.phase === 'recovering', st.phase);
chk('not at nineteen', F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 61).phase === 'potassium_falling');
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl'], [70.5, 'basic_chemistry_chem_7']]), 80);
chk('potassium back to 3.6', K(st) === '3.6', K(st));
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 400);
chk('she waits there until insulin is restarted', st.phase === 'recovering');
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl'], [80.5, 'insulin_drip']]), 95);
chk('a second insulin order is the restart', st.phase === 'treated' && st.flags.has('insulin_restarted'), st.phase);
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl'], [80.5, 'insulin_subcutaneous']]), 95);
chk('by either route', st.phase === 'treated', st.phase);
st = F(A0.concat([[20.5, 'insulin_subcutaneous'], [40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 70);
chk('a subcutaneous dose is held the same way', st.phase === 'recovering', st.phase);

section('potassium first');
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 39);
chk('not replaced at nineteen seconds', st.phase === 'presentation');
chk('the nurse says it takes a while', said(st, /takes a while to run in/));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 45);
chk('replaced at twenty', st.phase === 'potassium_replaced', st.phase);
chk('the nurse offers a repeat level', said(st, /repeat level/));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [25.5, 'basic_chemistry_chem_7']]), 45);
chk('a sample sent too early still shows 3.1', K(st) === '3.1', K(st));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [45.5, 'basic_chemistry_chem_7']]), 55);
chk('a sample sent after shows 3.6', K(st) === '3.6', K(st));
chk('and discharges the follow-up', st.flags.has('chem_repeated'));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 80);
chk('without a repeat the nurse asks for one', st.fuFires.some(f => f.fid === 'repeat_potassium_after_replacement'));
st = F([[1.5, 'potassium_chloride_kcl']], 30);
chk('intravenous potassium needs a line', st.blocked.some(b => b.id === 'potassium_chloride_kcl') && !st.flags.has('potassium_iv_given'));
st = F(A0.concat([[20.5, 'potassium_chloride_oral']]), 60);
chk('oral potassium is vomited and counts for nothing', st.phase === 'presentation' && said(st, /straight back up/) && !st.flags.has('potassium_iv_given'));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [22.5, 'insulin_drip']]), 50);
chk('insulin two seconds after potassium is still too early', st.phase === 'potassium_falling', seq(st));

section('insulin at the right time');
const ready = A0.concat([[20.5, 'potassium_chloride_kcl']]);
chk('insulin infusion is critical once potassium is replaced', tagOf('insulin_drip', F(ready, 45)) === 'critical');
chk('and discouraged on arrival', tagOf('insulin_drip', F(A0, 20)) === 'discouraged');
st = F(ready.concat([[50.5, 'insulin_drip']]), 65);
chk('infusion reaches treated', st.phase === 'treated');
chk('rate 104', st.vitals.heart_rate === 104);
st = F(ready.concat([[50.5, 'insulin_subcutaneous']]), 65);
chk('subcutaneous reaches treated', st.phase === 'treated');
chk('and satisfies the insulin expectation', st.satisfied.has('insulin_drip'));
st = F(ready.concat([[50.5, 'insulin_drip'], [62.5, 'insulin_glargine_subcutaneous']]), 70);
chk('glargine is recommended once she is treated', tagOf('insulin_glargine_subcutaneous', st) === 'recommended' && st.flags.has('basal_given') && st.phase === 'treated');
chk('the nurse says it is her usual dose', said(st, /her usual dose/));
st = F(A0.concat([[20.5, 'insulin_glargine_subcutaneous']]), 200);
chk('glargine on arrival is unscored and does not drop the potassium', st.phase === 'presentation' && !st.flags.has('insulin_given') && tagOf('insulin_glargine_subcutaneous', st) === 'neutral');
st = F([[1.5, 'insulin_glargine_subcutaneous']], 10);
chk('glargine needs no line', !st.blocked.some(b => b.id === 'insulin_glargine_subcutaneous') && st.flags.has('basal_given'));
st = F(ready.concat([[50.5, 'insulin_glargine_subcutaneous']]), 200);
chk('glargine alone does not treat her', st.phase === 'potassium_replaced' && !st.satisfied.has('insulin_drip'));
st = F(ready.concat([[50.5, 'insulin_bolus']]), 200);
chk('a bolus alone does not', st.phase === 'potassium_replaced');
st = F(ready, 100);
chk('the nurse suggests insulin at 45 seconds', st.promptFires.some(p => p.id === 'insulin_drip'));
st = F(ready.concat([[50.5, 'insulin_drip']]), 140);
chk('the dextrose question follows insulin', st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin') && said(st, /under 250/));
st = F(ready.concat([[50.5, 'insulin_drip'], [70.5, 'd5_1_2_ns_infusion']]), 140);
chk('and is answered by ordering dextrose fluid', !st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
st = F(early, 140);
chk('it is not asked when insulin was given too early', !st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
chk('stopping insulin in the treated phase is discouraged', tagOf('stop_insulin', F(ready.concat([[50.5, 'insulin_drip']]), 65)) === 'discouraged');

section('results follow what was given');
st = F(A0, 20);
chk('arrival potassium 3.1', K(st) === '3.1');
chk('anion gap 18', last(st, 'basic_chemistry_chem_7').body.components.find(c => c.label === 'Anion gap').value === '18');
chk('pH 7.27 with a pCO2 of 36', last(st, 'venous_blood_gas').body.components[0].value === '7.27' && last(st, 'venous_blood_gas').body.components[1].value === '36');
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [45.5, 'beta_hydroxybutyrate']]), 55);
chk('the wait for potassium costs something: ketones 4.6', last(st, 'beta_hydroxybutyrate').body.components[0].value === '4.6');
st = F(A0, 20);
chk('fingerstick 342', last(st, 'fingerstick_blood_sugar').body.components[0].value === '342');
st = F(A0.concat([[20.5, 'normal_saline_1l_bolus'], [22.5, 'basic_chemistry_chem_7']]), 40);
chk('after fluid: glucose lower, bicarbonate unchanged', last(st, 'basic_chemistry_chem_7').body.components.find(c => c.label === 'Glucose').value === '318' &&
  last(st, 'basic_chemistry_chem_7').body.components.find(c => c.label === 'Bicarbonate').value === '16');
st = F(A0.concat([[20.5, 'na_bicarbonate_bolus'], [22.5, 'basic_chemistry_chem_7']]), 40);
chk('after bicarbonate: potassium 2.9 and no phase change', K(st) === '2.9' && st.phase === 'presentation');
chk('bicarbonate infusion is covered', tagOf('na_bicarbonate_infusion', F(A0, 20)) === 'discouraged');
st = F(A0.concat([[20.5, 'magnesium_level']]), 30);
chk('magnesium 1.5', last(st, 'magnesium_level').body.components[0].value === '1.5');
st = F(A0.concat([[20.5, 'magnesium_sulfate_bolus'], [22.5, 'magnesium_level']]), 40);
chk('2.1 after replacement by either entry', last(st, 'magnesium_level').body.components[0].value === '2.1');
st = F(A0.concat([[20.5, 'ecg_12_lead']]), 30);
chk('arrival ECG: small U waves, QTc 460', /U waves/.test(last(st, 'ecg_12_lead').body.report) && /460/.test(last(st, 'ecg_12_lead').body.report));
st = F(A0.concat([[20.5, 'ondansetron'], [22.5, 'ecg_12_lead']]), 35);
chk('after ondansetron the QTc reads 465', /465/.test(last(st, 'ecg_12_lead').body.report));
st = F(A0.concat([[20.5, 'beta_hydroxybutyrate']]), 30);
chk('ketones 4.2', last(st, 'beta_hydroxybutyrate').body.components[0].value === '4.2');
st = F(A0.concat([[20.5, 'arterial_blood_gas']]), 30);
chk('an arterial gas satisfies the gas', st.satisfied.has('venous_blood_gas'));

section('the endocrinologist never quotes a result that is not back');
const endo = (log, t) => last(F(log, t), 'consult_endocrinology').body;
chk('nothing sent: asks for numbers', /need numbers/.test(endo([[2.5, 'consult_endocrinology']], 3)));
chk('chemistry pending: waits for it', /still in the lab/.test(endo([[1.5, 'basic_chemistry_chem_7'], [2.5, 'consult_endocrinology']], 3)));
chk('chemistry back: potassium first', /No insulin\s+yet/.test(endo(A0.concat([[20.5, 'consult_endocrinology']]), 21)));
chk('after early insulin: hold it', /^Endocrinologist: Hold the insulin now/.test(endo(early.concat([[40.5, 'consult_endocrinology']]), 41)));
chk('once replaced: start insulin', /start insulin now/.test(endo(ready.concat([[45.5, 'consult_endocrinology']]), 46)));

section('prompts on arrival');
st = F([], 140);
const ids = st.promptFires.map(p => p.id);
chk('monitor, glucose, bloods and fluid, in that order', ids.join() === 'attach_monitor,fingerstick_blood_sugar,basic_chemistry_chem_7,normal_saline_1l_bolus', ids.join());
chk('no potassium prompt before the chemistry is back', !ids.includes('potassium_chloride_kcl'));
st = F(A0, 140);
chk('with the chemistry back, potassium is prompted', st.promptFires.some(p => p.id === 'potassium_chloride_kcl'), st.promptFires.map(p => p.id).join());
chk('no prompt names a heart rate', !st.nurse.some(n => /\b1[01]\d\b/.test(n.text) && n.kind === 'prompt'));

section('the handoff');
st = F(ready.concat([[50.5, 'insulin_drip'], [70.5, 'handoff_submit']]), 75);
chk('completes the case', st.complete && st.phase === 'case_complete');
chk('and keeps the vitals she was handed over with', st.vitals.heart_rate === 104, String(st.vitals.heart_rate));
st = F(A0.concat([[10.5, 'normal_saline_1l_bolus'], [30.5, 'handoff_submit']]), 35);
chk('handing over an untreated patient shows the untreated patient', st.vitals.heart_rate === 102, String(st.vitals.heart_rate));
