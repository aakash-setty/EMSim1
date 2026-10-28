/* Case assertions for DKA (mild ketoacidosis with a low potassium).
 *
 * No clock changes her. Order is carried by which phase an action lands in, and by three
 * hidden case actions credited through also_satisfies on the phase at the moment of an
 * order (early_insulin, insulin_restart, repeat_potassium_level). Laboratory results are
 * keyed to flags inside the arrival phase. Times are fractional on purpose (see the v0.21
 * timing fault). Revised 7 October 2026 after the audit: the race table, every first
 * dose, both follow-ups both ways round, the consultants with nothing back, and every
 * changed nurse line read against the folded monitor.
 */
const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const F = (log, t, dm) => fold(mk(log), t, dm);
const A0 = [[1.3, 'attach_monitor'], [2.1, 'insert_iv'], [3.4, 'fingerstick_blood_sugar'],
            [4.4, 'venous_blood_gas'], [5.2, 'basic_chemistry_chem_7']];
const LINE = [[1.3, 'attach_monitor'], [2.1, 'insert_iv']];
const last = (st, key) => {
  const o = (st.orders[key] || []).filter(r => r.value).pop();
  return o ? { body: o.value } : st.readouts.filter(r => r.key === key).pop();
};
const K = st => { const r = last(st, 'basic_chemistry_chem_7'); return r && r.body.components.find(c => c.label === 'Potassium').value; };
const enteredAt = (st, id) => (st.phaseSeq.find(p => p.id === id) || {}).t;
const lineAt = (st, re) => (st.nurse.find(n => re.test(n.text)) || {}).t;
const FLUTTER = /arms and legs feel heavy and her heart is fluttering/;

section('intended path');
let st = F(A0.concat([[12.5, 'normal_saline_1l_bolus'], [20.5, 'potassium_chloride_kcl'], [21.5, 'magnesium_sulfate'],
  [45.5, 'basic_chemistry_chem_7'], [52.5, 'insulin_drip'], [53.5, 'potassium_chloride_kcl'], [70.5, 'd5_1_2_ns_infusion']]), 80);
chk('reaches treated', st.phase === 'treated', st.phase);
chk('through potassium_replaced', seq(st) === 'presentation > potassium_replaced > treated', seq(st));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)), [...st.expected].filter(id => !st.satisfied.has(id)).join());
chk('nothing halted, failed or completed', !st.halted && !st.failed && !st.complete);
chk('no follow-up left open', st.fuOutstanding.size === 0, [...st.fuOutstanding].join());
chk('the restart is not expected of a learner who never needed it', !st.expected.has('insulin_restart'));
chk('and no hidden target was credited except the repeat level and the potassium with the insulin',
  !st.satisfied.has('early_insulin') && !st.satisfied.has('insulin_restart') && st.satisfied.has('repeat_potassium_level')
  && st.satisfied.has('potassium_maintenance'));

section('nothing happens on the clock');
chk('untouched for ten minutes she is as she arrived', seq(F([], 600)) === 'presentation');
chk('with the workup done and nothing given, the same', seq(F(A0, 600)) === 'presentation');
chk('no timed transition ever fires on inaction', F(A0, 600).timeFires.length === 0);
chk('the same in the default mode', seq(F(A0, 900, 3)) === 'presentation' && F(A0, 900, 3).timeFires.length === 0);

section('the monitor: phases are authored without fluid, and fluid is an effect');
const v = (log, t) => F(log, t).vitals;
chk('arrival 112, 104/64', v(A0, 20).heart_rate === 112 && v(A0, 20).systolic_bp === 104);
chk('after a bolus 102, 110/64', v(A0.concat([[10.5, 'normal_saline_500ml_bolus']]), 30).heart_rate === 102 &&
  v(A0.concat([[10.5, 'normal_saline_500ml_bolus']]), 30).systolic_bp === 110);
chk('two boluses do not stack', v(A0.concat([[10.5, 'normal_saline_1l_bolus'], [12.5, 'lactated_ringer_s_1l_bolus']]), 30).heart_rate === 102);
chk('fluid changes no phase', F(A0.concat([[10.5, 'normal_saline_1l_bolus']]), 300).phase === 'presentation');
for (const inf of ['normal_saline_infusion', 'lactated_ringer_s_infusion']) {
  st = F(A0.concat([[10.5, inf]]), 400);
  chk(inf + ' moves the same two numbers', st.vitals.heart_rate === 102 && st.vitals.systolic_bp === 110);
  chk(inf + ' counts as her fluid', st.flags.has('fluids_given') && st.satisfied.has('normal_saline_1l_bolus'));
  chk(inf + ' stops the fluid prompt', !st.promptFires.some(p => p.id === 'normal_saline_1l_bolus'));
  chk(inf + ' is unscored itself', tagOf(inf, F(A0, 9)) === 'neutral');
}
chk('a bolus and an infusion do not stack',
  v(A0.concat([[10.5, 'normal_saline_1l_bolus'], [12.5, 'normal_saline_infusion']]), 30).heart_rate === 102 &&
  v(A0.concat([[10.5, 'normal_saline_1l_bolus'], [12.5, 'normal_saline_infusion']]), 30).systolic_bp === 110);
st = F(A0.concat([[10.5, 'lactated_ringer_s_infusion'], [12.5, 'exam_circ']]), 20);
chk('the circulation exam reads the same after an infusion as after a bolus', /Hands warming/.test(last(st, 'exam_circ').body.findings));
chk('an infusion with no line is blocked by the catalog rule',
  F([[1.5, 'normal_saline_infusion']], 10).blocked.some(b => b.id === 'normal_saline_infusion'));

section('insulin before potassium');
for (const drug of ['insulin_drip', 'insulin_subcutaneous', 'insulin_bolus']) {
  st = F(A0.concat([[20.5, drug]]), 40);
  chk(drug + ' on arrival drives the potassium down', st.phase === 'potassium_falling', st.phase);
  chk(drug + ' is tagged discouraged there', st.discouraged && [...st.discouraged].includes(drug) || tagOf(drug, F(A0, 20)) === 'discouraged');
  chk(drug + ' on arrival is recorded as early', st.satisfied.has('early_insulin'));
}
st = F(A0.concat([[20.5, 'insulin_drip']]), 29);
chk('not before ten seconds', st.phase === 'presentation');
st = F(A0.concat([[20.5, 'insulin_drip']]), 40);
chk('the nurse says she is weak', said(st, FLUTTER));
chk('rate 118 without fluid', st.vitals.heart_rate === 118);
st = F(A0.concat([[20.5, 'insulin_drip'], [40.5, 'basic_chemistry_chem_7'], [41.5, 'ecg_12_lead']]), 60);
chk('a repeat chemistry shows 2.6', K(st) === '2.6', K(st));
chk('the ECG shows prominent U waves and a QTc of 520', /Prominent U waves/.test(last(st, 'ecg_12_lead').body.comment) && /520/.test(last(st, 'ecg_12_lead').body.comment));
st = F(A0.concat([[20.5, 'insulin_drip']]), 60);
chk('the nurse suggests holding it at 25 seconds', st.promptFires.some(p => p.id === 'stop_insulin'));
chk('in US usage', said(st, /She's weaker since the insulin/));
st = F(A0.concat([[20.5, 'insulin_drip']]), 139);
chk('no potassium prompt before 110 seconds in the falling phase', !st.promptFires.some(p => p.id === 'potassium_chloride_kcl'));
st = F(A0.concat([[20.5, 'insulin_drip']]), 142);
chk('and potassium at 110', st.promptFires.some(p => p.id === 'potassium_chloride_kcl'));
st = F([[2.5, 'insulin_drip']], 60);
chk('an insulin infusion with no line is blocked and is not early insulin',
  st.blocked.some(b => b.id === 'insulin_drip') && !st.satisfied.has('early_insulin') && st.phase === 'presentation');

/* Authoring 15.4. One test per row of the table in DKA-SEED.md, with fractional times on
   both sides of every boundary. Potassium is ordered at 10.25 seconds in every row. */
section('the race table: insulin and potassium both pending');
const race = (gap, drug) => F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [10.25 + gap, drug || 'insulin_drip']]), 120);
const raceRev = gap => F(LINE.concat([[10.25, 'insulin_drip'], [10.25 + gap, 'potassium_chloride_kcl']]), 28);
for (const gap of [0.5, 5.5, 9.5]) {
  st = raceRev(gap);
  chk('insulin, then potassium ' + gap + ' s later: falls at ten seconds, straight from arrival',
    seq(st) === 'presentation > potassium_falling' && Math.abs(enteredAt(st, 'potassium_falling') - 20.25) < 1e-6, seq(st));
}
st = F(LINE.concat([[10.25, 'insulin_drip'], [25.75, 'potassium_chloride_kcl']]), 44);
chk('insulin, then potassium after the fall: still falling until insulin is held', seq(st) === 'presentation > potassium_falling', seq(st));
for (const gap of [0.5, 5.5, 9.5]) {
  st = race(gap);
  chk('potassium, then insulin ' + gap + ' s later: falls ten seconds after the insulin, straight from arrival',
    seq(st) === 'presentation > potassium_falling' && Math.abs(enteredAt(st, 'potassium_falling') - (20.25 + gap)) < 1e-6,
    seq(st) + ' at ' + enteredAt(st, 'potassium_falling'));
}
st = race(10);
chk('at exactly ten seconds both rules are due and the insulin rule, higher in the list, fires',
  seq(st) === 'presentation > potassium_falling' && Math.abs(enteredAt(st, 'potassium_falling') - 30.25) < 1e-6, seq(st));
for (const gap of [10.5, 11.5, 15.5, 19.5]) {
  st = race(gap);
  chk('potassium, then insulin ' + gap + ' s later: the potassium finishes first and she still falls',
    seq(st) === 'presentation > potassium_replaced > potassium_falling', seq(st));
  chk('  five seconds after the potassium finishes', Math.abs(enteredAt(st, 'potassium_replaced') - 30.25) < 1e-6 &&
    Math.abs(enteredAt(st, 'potassium_falling') - 35.25) < 1e-6, String(enteredAt(st, 'potassium_falling')));
  chk('  and never reaches treated on that order', st.phase === 'potassium_falling');
}
st = race(20);
chk('insulin logged at the instant the potassium finishes is still early',
  seq(st) === 'presentation > potassium_replaced > potassium_falling', seq(st));
for (const gap of [20.5, 25.5, 40.5]) {
  st = race(gap);
  chk('potassium, then insulin ' + gap + ' s later: replaced, then treated ten seconds after the insulin',
    seq(st) === 'presentation > potassium_replaced > treated' && Math.abs(enteredAt(st, 'treated') - (20.25 + gap)) < 1e-6, seq(st));
  chk('  and that insulin is not early insulin', !st.satisfied.has('early_insulin'));
}
for (const drug of ['insulin_subcutaneous', 'insulin_bolus']) {
  st = race(15.5, drug);
  chk(drug + ' 15.5 s after potassium: the same fall', seq(st) === 'presentation > potassium_replaced > potassium_falling', seq(st));
}
st = F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [25.75, 'insulin_bolus'], [31.5, 'insulin_drip']]), 120);
chk('in the replaced phase the early rule (5 s) beats an infusion ordered there (10 s)',
  seq(st) === 'presentation > potassium_replaced > potassium_falling', seq(st));
st = race(15.5);
chk('the fall after the potassium is narrated once, with the same words', st.nurse.filter(n => FLUTTER.test(n.text)).length === 1);
chk('the potassium line comes first and is true', lineAt(st, /run through on the pump/) === 30.25 && lineAt(st, FLUTTER) === 35.25);
chk('the dextrose question is not asked of her', !F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [25.75, 'insulin_drip']]), 300).fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));

section('the rescue needs the hold, with potassium given before or after the fall');
const early = A0.concat([[20.5, 'insulin_drip']]);
chk('potassium alone: still falling', F(early.concat([[40.5, 'potassium_chloride_kcl']]), 200).phase === 'potassium_falling');
chk('hold alone, with no potassium ever given: still falling', F(early.concat([[40.5, 'stop_insulin']]), 200).phase === 'potassium_falling');
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 70);
chk('both: recovering after twenty seconds', st.phase === 'recovering', st.phase);
chk('not at nineteen', F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 61).phase === 'potassium_falling');
st = F(early.concat([[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl'], [70.5, 'basic_chemistry_chem_7']]), 80);
chk('potassium back to 3.6', K(st) === '3.6', K(st));
st = F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [15.75, 'insulin_drip'], [40.5, 'stop_insulin']]), 80);
chk('potassium given before the fall counts: holding insulin is the step that was missing',
  seq(st) === 'presentation > potassium_falling > recovering' && Math.abs(enteredAt(st, 'recovering') - 60.5) < 1e-6, seq(st));
st = F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [25.75, 'insulin_drip'], [40.5, 'stop_insulin']]), 80);
chk('the same when the potassium had finished first',
  seq(st) === 'presentation > potassium_replaced > potassium_falling > recovering', seq(st));
st = F(LINE.concat([[10.25, 'potassium_chloride_kcl'], [15.75, 'insulin_drip']]), 400);
chk('with potassium given and insulin never held she stays weak', st.phase === 'potassium_falling');
st = F(A0.concat([[20.5, 'insulin_subcutaneous'], [40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]), 70);
chk('a subcutaneous dose is held the same way', st.phase === 'recovering', st.phase);

/* Authoring 18 and section 13 step 7: every first dose. One order placed in the
   recovering phase is the restart, whatever was ordered before it. */
section('after the rescue, one insulin order reaches treated, from every first dose');
const rescue = first => A0.concat(first, [[40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']]);
for (const first of ['insulin_drip', 'insulin_subcutaneous', 'insulin_bolus']) {
  st = F(rescue([[20.5, first]]), 400);
  chk(first + ' first: she waits in recovering until insulin is ordered again', st.phase === 'recovering' && !st.satisfied.has('insulin_restart'));
  for (const again of ['insulin_drip', 'insulin_subcutaneous']) {
    st = F(rescue([[20.5, first]]).concat([[80.5, again]]), 95);
    chk(first + ' first, then one ' + again + ': treated', st.phase === 'treated' && st.satisfied.has('insulin_restart'), seq(st));
    chk('  ten seconds after the order', Math.abs(enteredAt(st, 'treated') - 90.5) < 1e-6);
    chk('  and not at nine', F(rescue([[20.5, first]]).concat([[80.5, again]]), 90).phase === 'recovering');
  }
  st = F(rescue([[20.5, first]]).concat([[80.5, 'insulin_bolus']]), 300);
  chk(first + ' first, then a bolus alone: not treated', st.phase === 'recovering');
}
st = F(rescue([[20.5, 'insulin_drip'], [21.5, 'insulin_subcutaneous']]), 400);
chk('two insulin orders before the hold are not a restart', st.phase === 'recovering' && !st.satisfied.has('insulin_restart'), seq(st));
st = F(rescue([[20.5, 'insulin_drip'], [21.5, 'insulin_drip'], [22.5, 'insulin_drip']]), 400);
chk('nor are three orders of the same infusion', st.phase === 'recovering', seq(st));
st = F(rescue([[20.5, 'insulin_drip'], [21.5, 'insulin_subcutaneous']]).concat([[80.5, 'insulin_drip']]), 95);
chk('and one order after the rescue still treats her', st.phase === 'treated', seq(st));
st = F(rescue([[20.5, 'insulin_drip']]).concat([[80.5, 'insulin_drip']]), 200);
chk('the restart narration is true: insulin was ordered in that phase', said(st, /Insulin is back on/) && st.satisfied.has('insulin_restart'));
chk('the dextrose question follows the restart', st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
/* Known gaps, pinned so that a fix shows up as a failing check. */
st = F(rescue([[20.5, 'insulin_drip']]).concat([[50.5, 'insulin_drip']]), 400);
chk('known gap: insulin reordered during the rescue wait is ignored, and she needs one more order',
  seq(st) === 'presentation > potassium_falling > recovering' && !st.satisfied.has('insulin_restart'), seq(st));
st = F(LINE.concat([[5.5, 'stop_insulin'], [10.25, 'potassium_chloride_kcl'], [15.75, 'insulin_drip']]), 200);
chk('known gap: a hold pressed before any insulin still counts as the hold',
  seq(st) === 'presentation > potassium_falling > recovering', seq(st));

section('the restart is prompted, and it is a critical action of its own');
st = F(rescue([[20.5, 'insulin_drip']]), 62.5 + 46);
chk('infusion first: the nurse asks for the level and the restart at 45 seconds',
  st.promptFires.some(p => p.id === 'insulin_restart') && said(st, /repeat level, and insulin back on if it's 3\.5 or more/));
chk('  and the insulin action, already counted as done, does not prompt', !st.promptFires.some(p => p.id === 'insulin_drip'));
st = F(rescue([[20.5, 'insulin_bolus']]), 62.5 + 46);
chk('bolus first: one prompt, not two', st.promptFires.filter(p => /insulin_(drip|restart)/.test(p.id)).length === 1);
st = F(rescue([[20.5, 'insulin_drip']]).concat([[70.5, 'insulin_subcutaneous']]), 62.5 + 46);
chk('no prompt once it is restarted', !st.promptFires.some(p => p.id === 'insulin_restart'));
st = F(rescue([[20.5, 'insulin_drip']]), 400);
chk('in recovering the restart is expected and not yet done', st.expected.has('insulin_restart') && !st.satisfied.has('insulin_restart'));
chk('it is hidden, sits on no order tab and is critical only in recovering',
  CASE.case_actions.find(a => a.catalog_id === 'insulin_restart').hidden === true &&
  tagOf('insulin_restart', st) === 'critical' && tagOf('insulin_restart', F(A0, 20)) === 'neutral');
st = F(rescue([[20.5, 'insulin_drip']]), 62.5 + 45 * 3 - 1, 3);
chk('default mode: not before 135 seconds', !st.promptFires.some(p => p.id === 'insulin_restart'));
st = F(rescue([[20.5, 'insulin_drip']]), 62.5 + 45 * 3 + 1, 3);
chk('default mode: at 135 seconds', st.promptFires.some(p => p.id === 'insulin_restart'));

section('potassium first');
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 39);
chk('not replaced at nineteen seconds', st.phase === 'presentation');
chk('the nurse says it takes a while', said(st, /takes a while to run in/));
chk('and does not say she is on the monitor', !said(st, /on the monitor/));
st = F([[2.1, 'insert_iv'], [20.5, 'potassium_chloride_kcl']], 39);
chk('with no monitor on, the potassium line is still true', !st.flags.has('monitor_on') && said(st, /It's on the pump\. It takes a while to run in\.$/));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 45);
chk('replaced at twenty', st.phase === 'potassium_replaced', st.phase);
chk('the nurse offers a repeat level', said(st, /repeat level/));
chk('the monitor chip does not say the level is corrected',
  CASE.phases.find(p => p.id === 'potassium_replaced').short_label === 'after potassium');
st = F([[1.5, 'potassium_chloride_kcl']], 30);
chk('intravenous potassium needs a line', st.blocked.some(b => b.id === 'potassium_chloride_kcl') && !st.flags.has('potassium_iv_given'));
chk('in US usage', /She doesn't have a line yet/.test(st.blocked[0].message), st.blocked[0].message);
for (const line of ['central_venous_catheter_triple_lumen', 'central_venous_catheter_cordis', 'intraosseous_line']) {
  st = F([[1.5, line], [9.5, 'potassium_chloride_kcl']], 30);
  chk('potassium goes in through a ' + line, !st.blocked.length && st.flags.has('potassium_iv_given'), JSON.stringify(st.blocked));
}
st = F(A0.concat([[20.5, 'potassium_chloride_oral']]), 60);
chk('oral potassium counts for nothing', st.phase === 'presentation' && !st.flags.has('potassium_iv_given'));
chk('and the nurse no longer says she vomited it', said(st, /I can't promise it stays down/) && !said(st, /straight back up/));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [50.5, 'insulin_drip'], [70.5, 'potassium_chloride_oral']]), 80);
chk('the oral potassium line is true in the treated phase, where she is no longer retching',
  st.phase === 'treated' && said(st, /I can't promise it stays down/) && /no longer retching/.test(JSON.stringify(CASE.content_keys.general_status)));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [22.5, 'insulin_drip']]), 50);
chk('insulin two seconds after potassium is still too early', st.phase === 'potassium_falling', seq(st));

/* Authoring 22.2: both ways round. Only a chemistry sent once the potassium has run in
   discharges the repeat-level follow-up. */
section('the repeat-potassium follow-up');
const fuRepeat = st => st.fuFires.some(f => f.fid === 'repeat_potassium_after_replacement');
st = F(A0.concat([[20.5, 'potassium_chloride_kcl']]), 80);
chk('without a repeat the nurse asks for one, 50 seconds after the order', fuRepeat(st) && st.fuOutstanding.has('repeat_potassium_after_replacement'));
st = F(A0.concat([[8.5, 'normal_saline_1l_bolus'], [12.5, 'basic_chemistry_chem_7'], [20.5, 'potassium_chloride_kcl']]), 80);
chk('two chemistries before the potassium do not discharge it', K(st) === '3.0' && fuRepeat(st) && !st.satisfied.has('repeat_potassium_level'));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [25.5, 'basic_chemistry_chem_7']]), 80);
chk('a sample sent while the potassium runs shows 3.1 and does not discharge it', K(st) === '3.1' && fuRepeat(st));
st = F([[2.1, 'insert_iv'], [20.5, 'potassium_chloride_kcl'], [45.5, 'basic_chemistry_chem_7']], 80);
chk('a first chemistry, sent after replacement, shows 3.6 and discharges it',
  K(st) === '3.6' && !fuRepeat(st) && st.satisfied.has('repeat_potassium_level'));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [45.5, 'basic_chemistry_chem_7']]), 80);
chk('a repeat chemistry sent after replacement discharges it', K(st) === '3.6' && !fuRepeat(st));
st = F(A0.concat([[20.5, 'potassium_chloride_kcl'], [72.5, 'basic_chemistry_chem_7']]), 90);
chk('asked first and answered late, it is closed by the end', fuRepeat(st) && st.fuOutstanding.size === 0);
st = F(early.concat([[40.5, 'potassium_chloride_kcl'], [45.5, 'basic_chemistry_chem_7']]), 120);
chk('a level sent in the falling phase shows 2.6 and leaves it open', K(st) === '2.6' && fuRepeat(st) && st.fuOutstanding.size === 1);
st = F(rescue([[20.5, 'insulin_drip']]).concat([[70.5, 'basic_chemistry_chem_7']]), 120);
chk('a level sent after the rescue discharges it', K(st) === '3.6' && st.satisfied.has('repeat_potassium_level') && !fuRepeat(st));
chk('nothing reads a repeat-granted flag any more',
  !JSON.stringify(CASE.case_actions).includes('flags_set_repeat') && !JSON.stringify(CASE.case_actions).includes('chem_repeated') &&
  !JSON.stringify(CASE.follow_ups).includes('chem_repeated'));
chk('each follow-up names every action that triggers it', CASE.follow_ups.every(f =>
  [].concat(f.triggered_by).slice().sort().join() ===
  CASE.case_actions.filter(a => (a.follow_ups_triggered || []).includes(f.id)).map(a => a.catalog_id).sort().join()));

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
chk('glargine on arrival is unscored and does not drop the potassium',
  st.phase === 'presentation' && !st.flags.has('insulin_given') && !st.satisfied.has('early_insulin') && tagOf('insulin_glargine_subcutaneous', st) === 'neutral');
st = F([[1.5, 'insulin_glargine_subcutaneous']], 10);
chk('glargine needs no line', !st.blocked.some(b => b.id === 'insulin_glargine_subcutaneous') && st.flags.has('basal_given'));
st = F(ready.concat([[50.5, 'insulin_glargine_subcutaneous']]), 200);
chk('glargine alone does not treat her', st.phase === 'potassium_replaced' && !st.satisfied.has('insulin_drip'));
st = F(ready.concat([[50.5, 'insulin_bolus']]), 200);
chk('a bolus alone does not', st.phase === 'potassium_replaced');
st = F(ready, 100);
chk('the nurse asks for the level, and insulin if it allows, at 45 seconds',
  st.promptFires.some(p => p.id === 'insulin_drip') && said(st, /Do you want a repeat level, and insulin if it's 3\.5 or more\?/));
chk('no prompt invites insulin on a dose alone', !CASE.case_actions.some(a => a.prompt && /start insulin now/.test(a.prompt.text)));
st = F(ready.concat([[50.5, 'insulin_drip']]), 140);
chk('the dextrose question follows insulin', st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin') && said(st, /under 250/));
chk('and claims no trend', said(st, /She's on insulin now/) && !said(st, /coming down\. What do you want/));
st = F(ready.concat([[50.5, 'insulin_subcutaneous']]), 140);
chk('it follows subcutaneous insulin too', st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
st = F(ready.concat([[50.5, 'insulin_drip'], [70.5, 'd5_1_2_ns_infusion']]), 140);
chk('and is answered by ordering dextrose fluid', !st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
st = F(ready.concat([[50.5, 'insulin_drip'], [70.5, 'd5_ns_bolus']]), 140);
chk('or by a dextrose bolus given once she is on insulin', !st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
st = F(A0.concat([[8.5, 'd5_ns_bolus'], [20.5, 'potassium_chloride_kcl'], [50.5, 'insulin_drip']]), 140);
chk('a dextrose bolus given on arrival does not answer it', st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
st = F(early, 140);
chk('it is not asked when insulin was given too early', !st.fuFires.some(f => f.fid === 'dextrose_plan_after_insulin'));
chk('stopping insulin in the treated phase is discouraged', tagOf('stop_insulin', F(ready.concat([[50.5, 'insulin_drip']]), 65)) === 'discouraged');

/* Authoring 7.3 and 16. The fluid effect has no end, so every line that gives a
   direction is read against the folded monitor, with fluid and without. */
section('every narration is true of the monitor, with fluid and without');
for (const fluid of [null, 'normal_saline_1l_bolus', 'lactated_ringer_s_infusion']) {
  const pre = fluid ? A0.concat([[8.5, fluid]]) : A0;
  const tag = fluid ? ' (after ' + fluid + ')' : ' (no fluid)';
  const hr = (log, t) => F(pre.concat(log), t).vitals.heart_rate;
  let log = [[20.5, 'insulin_drip']];
  chk('"Her rate has gone up" on the fall from arrival' + tag, said(F(pre.concat(log), 40), /Her rate has gone up/) && hr(log, 40) > hr(log, 30));
  log = [[20.5, 'potassium_chloride_kcl'], [35.5, 'insulin_drip']];
  chk('"Her rate has gone up" on the fall from the replaced phase' + tag, seq(F(pre.concat(log), 60)).endsWith('potassium_replaced > potassium_falling') && hr(log, 60) > hr(log, 44));
  log = [[20.5, 'insulin_drip'], [40.5, 'stop_insulin'], [42.5, 'potassium_chloride_kcl']];
  chk('"her rate has come back down" on recovery' + tag, said(F(pre.concat(log), 75), /her rate has come back down/) && hr(log, 75) < hr(log, 60));
  log = log.concat([[80.5, 'insulin_drip']]);
  chk('"Her rate is settling" after the restart' + tag, said(F(pre.concat(log), 100), /Insulin is back on.*Her rate is settling/) && hr(log, 100) < hr(log, 89));
  log = [[20.5, 'potassium_chloride_kcl'], [50.5, 'insulin_drip']];
  chk('"Her rate is settling" on the intended path' + tag, said(F(pre.concat(log), 70), /Her rate is settling/) && hr(log, 70) < hr(log, 59));
  chk('the treated monitor is ' + (fluid ? 94 : 104) + tag, hr(log, 70) === (fluid ? 94 : 104));
}
chk('no narration quotes a vital sign', CASE.phases.every(p => (p.transitions || []).every(t =>
  !t.narration || !/\b\d{2,3} over \d{2,3}\b|\brate (is|of) \d|\b1[0-2]\d\b/.test(t.narration))));
chk('no narration says the insulin is on hold, which a reorder would make false',
  CASE.phases.every(p => (p.transitions || []).every(t => !/on hold/.test(t.narration || ''))));
st = F(ready.concat([[50.5, 'insulin_drip'], [65.5, 'fingerstick_blood_sugar']]), 75);
chk('"266 on the meter" is the treated fingerstick', last(st, 'fingerstick_blood_sugar').body.components[0].value === '266');
st = F(rescue([[20.5, 'insulin_drip']]).concat([[80.5, 'insulin_drip'], [95.5, 'fingerstick_blood_sugar']]), 105);
chk('on the rescue route too', last(st, 'fingerstick_blood_sugar').body.components[0].value === '266');

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
st = F(A0.concat([[20.5, 'normal_saline_infusion'], [22.5, 'basic_chemistry_chem_7']]), 40);
chk('the same after an infusion', last(st, 'basic_chemistry_chem_7').body.components.find(c => c.label === 'Glucose').value === '318');
st = F(A0.concat([[20.5, 'na_bicarbonate_bolus'], [22.5, 'basic_chemistry_chem_7']]), 40);
chk('after bicarbonate: potassium 2.9 and no phase change', K(st) === '2.9' && st.phase === 'presentation');
chk('bicarbonate infusion is covered', tagOf('na_bicarbonate_infusion', F(A0, 20)) === 'discouraged');
st = F(A0.concat([[20.5, 'magnesium_level']]), 30);
chk('magnesium 1.5', last(st, 'magnesium_level').body.components[0].value === '1.5');
st = F(A0.concat([[20.5, 'magnesium_sulfate_bolus'], [22.5, 'magnesium_level']]), 40);
chk('2.1 after replacement by either entry', last(st, 'magnesium_level').body.components[0].value === '2.1');
st = F(A0.concat([[20.5, 'ecg_12_lead']]), 30);
chk('arrival ECG: small U waves, QTc 460', /U waves/.test(last(st, 'ecg_12_lead').body.comment) && /460/.test(last(st, 'ecg_12_lead').body.comment));
st = F(A0.concat([[20.5, 'ondansetron'], [22.5, 'ecg_12_lead']]), 35);
chk('after ondansetron the QTc reads 465', /465/.test(last(st, 'ecg_12_lead').body.comment));
st = F(A0.concat([[20.5, 'beta_hydroxybutyrate']]), 30);
chk('ketones 4.2', last(st, 'beta_hydroxybutyrate').body.components[0].value === '4.2');
st = F(A0.concat([[20.5, 'arterial_blood_gas']]), 30);
chk('an arterial gas satisfies the gas', st.satisfied.has('venous_blood_gas'));
st = F(A0.concat([[20.5, 'ultrasound_cardiac']]), 35);   // ultrasound 10 s since 28 October 2026
chk('the cardiac ultrasound agrees with a dry patient', last(st, 'ultrasound_cardiac').body.abnormal === true &&
  /small and collapsing/.test(last(st, 'ultrasound_cardiac').body.report) && !st.defaultsServed.has('ultrasound_cardiac'));

/* Authoring 9.4, 16 and 9.2. */
section('results hold findings, and nothing quotes a rate the fluid effect can move');
const eachPayload = fn => {
  for (const block of [CASE.content_keys.labs, CASE.content_keys.imaging]) for (const k in block) {
    const rules = Array.isArray(block[k]) ? block[k] : (block[k] && block[k].rules);
    if (Array.isArray(rules)) rules.forEach(r => fn(k, r.value));
  }
};
let comments = new Set(), reportComments = 0, rated = [];
eachPayload((k, p) => { if (p.comment && p.kind !== 'image') { comments.add(p.comment); if (p.kind === 'report') reportComments++; }
  const words = [p.report, p.kind === 'image' ? p.comment : '', p.kind === 'image' ? p.caption : ''].join(' ');
  if (/\bat \d{2,3}\b|\b\d{2,3} (beats|bpm|a minute)|\brate \d/.test(words)) rated.push(k); });
chk('the only result comment is the anion gap caption', comments.size === 1 && [...comments][0] === 'Anion gap calculated without potassium.', [...comments].join(' | '));
chk('no report carries a comment, since the interface never shows one', reportComments === 0);
chk('no report, tracing read or tracing caption quotes a heart rate', rated.length === 0, rated.join());
/* 13 October 2026. The twelve-lead is a generated tracing whose read is its comment. */
chk('every ECG rule is a tracing with its read kept for the debrief',
  CASE.content_keys.imaging.ecg_12_lead.rules.every(r => r.value.kind === 'image' && /QRS 88 ms/.test(r.value.comment) && /QRS 88 ms/.test(r.value.caption)));
const ecgIn = (log, t) => last(F(log.concat([[t - 6, 'ecg_12_lead']]), t), 'ecg_12_lead').body.comment;
chk('the treated ECG says sinus rhythm, true at 104 and at 94', /^Sinus rhythm\./.test(ecgIn(ready.concat([[50.5, 'insulin_drip']]), 75)));
chk('the falling ECG says QRS 88 ms, as the monitor draws', /QRS 88 ms/.test(ecgIn(early, 45)) &&
  CASE.phases.every(p => p.ecg.qrs_ms === 88) && !JSON.stringify(CASE.content_keys.imaging).includes('QRS 90'));
const findings = JSON.stringify(CASE.content_keys.exam) + JSON.stringify(CASE.content_keys.general_status);
chk('no exam line or status line quotes a pulse', !/[Pp]ulse (about|of|at) \d|rate (about|of) 1\d\d/.test(findings));
st = F(A0.concat([[8.5, 'normal_saline_1l_bolus'], [20.5, 'potassium_chloride_kcl'], [50.5, 'insulin_drip'], [65.5, 'exam_circ'], [66.5, 'exam_card']]), 70);
chk('at 94 on the monitor the treated exam does not say fast', st.vitals.heart_rate === 94 &&
  !/[Ff]ast/.test(last(st, 'exam_circ').body.findings) && !/[Ff]ast/.test(last(st, 'exam_card').body.findings));
st = F(early.concat([[40.5, 'exam_neuro']]), 45);
chk('the falling neurological exam leads with the abnormal finding', /^Proximal weakness/.test(last(st, 'exam_neuro').body.findings));
chk('every exam finding is a chart line of about 15 words', Object.keys(CASE.content_keys.exam).every(k => !Array.isArray(CASE.content_keys.exam[k]) ||
  CASE.content_keys.exam[k].every(r => r.value.findings.split(/\s+/).length <= 16)));

/* Authoring 9.5. `study S resulted` means a result exists, not that it was sent in this
   phase, so no consultant line names a laboratory value at all. */
section('the consultants read no result that is not back, and name no value');
const consult = (who, log, t) => last(F(log.concat([[t, who]]), t + 0.5), who).body;
const endo = (log, t) => consult('consult_endocrinology', log, t);
const icu = (log, t) => consult('consult_critical_care', log, t);
chk('endocrinologist, nothing sent: asks for numbers', /need numbers/.test(endo([], 2.5)));
chk('chemistry pending: waits for it', /still in the lab/.test(endo([[1.5, 'basic_chemistry_chem_7']], 2.5)));
chk('chemistry back, no gas: potassium first, and asks for the gas', /Insulin waits/.test(endo([[1.5, 'basic_chemistry_chem_7']], 20.5)) &&
  /Get a gas/.test(endo([[1.5, 'basic_chemistry_chem_7']], 20.5)) && !/mild/.test(endo([[1.5, 'basic_chemistry_chem_7']], 20.5)));
chk('chemistry and gas back: grades it', /mild on the gas/.test(endo(A0, 20.5)));
chk('an arterial gas counts as the gas', /mild on the gas/.test(endo([[1.5, 'basic_chemistry_chem_7'], [2.5, 'arterial_blood_gas']], 20.5)));
for (const pre of [[], [[8.5, 'normal_saline_1l_bolus']], [[8.5, 'na_bicarbonate_bolus']], [[8.5, 'normal_saline_1l_bolus'], [9.5, 'na_bicarbonate_bolus']]]) {
  st = F(LINE.concat(pre, [[12.5, 'basic_chemistry_chem_7'], [20.5, 'consult_endocrinology']]), 21);
  chk('"under 3.5" is true of the chemistry on the chart (' + K(st) + ')', parseFloat(K(st)) < 3.5 && /under 3\.5/.test(last(st, 'consult_endocrinology').body));
}
chk('after early insulin with no chemistry ever sent: hold it, and no result is claimed',
  /^Endocrinologist: Hold the insulin now/.test(endo(LINE.concat([[20.5, 'insulin_drip']]), 40.5)) &&
  !/was low|pushed it lower|2\.6|3\.1/.test(endo(LINE.concat([[20.5, 'insulin_drip']]), 40.5)));
chk('once replaced: start insulin if the repeat allows, and mild is conditional on the gas',
  /If the repeat potassium is 3\.5 or more/.test(endo(ready, 45.5)) && /if the gas says this is mild/.test(endo(ready, 45.5)));
chk('intensivist, nothing sent: asks why, and for the workup', /not sure why/.test(icu([], 2.5)) && /a gas and a chemistry/.test(icu([], 2.5)));
chk('one study pending: her labs are not back', /labs aren't back/.test(icu([[1.5, 'venous_blood_gas']], 2.5)) && /labs aren't back/.test(icu([[1.5, 'basic_chemistry_chem_7']], 2.5)));
chk('chemistry back, gas never sent: needs the gas', /I need a gas/.test(icu([[1.5, 'basic_chemistry_chem_7']], 20.5)));
chk('gas back, chemistry never sent: needs the chemistry', /I need the chemistry/.test(icu([[1.5, 'venous_blood_gas']], 20.5)));
chk('both back: names the grade', /Mild ketoacidosis/.test(icu(A0, 20.5)));
chk('with nothing back the intensivist does not name the diagnosis', !/ketoacidosis/i.test(icu([], 2.5)) && !/ketoacidosis/i.test(icu([[1.5, 'venous_blood_gas']], 2.5)));
chk('in the falling phase with no chemistry ever sent: no value, and asks for the studies',
  /weak with extra beats after insulin/.test(icu(LINE.concat([[20.5, 'insulin_drip']]), 40.5)) && /get a chemistry and a twelve-lead/.test(icu(LINE.concat([[20.5, 'insulin_drip']]), 40.5)));
const consultText = JSON.stringify(CASE.content_keys.consultants.consult_endocrinology) + JSON.stringify(CASE.content_keys.consultants.consult_critical_care);
chk('no consultant line names a potassium, a pH, a bicarbonate or a glucose result', !/\b(2\.6|2\.9|3\.0|3\.1|3\.6|3\.7|7\.2\d|7\.3\d|348|318|266)\b/.test(consultText));
chk('"mild" is said only where the rule tests the gas, or as a condition',
  [].concat(CASE.content_keys.consultants.consult_endocrinology, CASE.content_keys.consultants.consult_critical_care)
    .every(r => !/[Mm]ild/.test(r.value) || /if the gas says/.test(r.value) || (/blood_gas resulted/.test(r.when || ''))));

section('prompts on arrival');
st = F([], 140);
const ids = st.promptFires.map(p => p.id);
chk('monitor, glucose, bloods and fluid, in that order', ids.join() === 'attach_monitor,fingerstick_blood_sugar,basic_chemistry_chem_7,normal_saline_1l_bolus', ids.join());
chk('no potassium prompt before the chemistry is back', !F([], 400).promptFires.some(p => p.id === 'potassium_chloride_kcl'));
st = F(A0, 140);
chk('with the chemistry back, potassium is prompted at 110', st.promptFires.some(p => p.id === 'potassium_chloride_kcl' && p.t === 110), st.promptFires.map(p => p.id + '@' + p.t).join());
chk('no prompt names a heart rate', !st.nurse.some(n => /\b1[01]\d\b/.test(n.text) && n.kind === 'prompt'));
/* A learner who needed the chemistry prompt (75 s) and acts on it within 30 seconds. */
for (const t of [76.5, 90.5, 104.5]) {
  st = F([[t, 'basic_chemistry_chem_7']], 165);
  const kp = st.promptFires.filter(p => p.id === 'potassium_chloride_kcl');
  chk('chemistry ordered at ' + t + ' s: the first potassium line is the first prompt, not the escalation',
    kp.length === 1 && kp[0].level === 1 && kp[0].t === 110 && said(st, /I'm worried about her potassium/), JSON.stringify(kp));
}
st = F([[76.5, 'basic_chemistry_chem_7']], 175);
chk('the escalation follows at 170 and reads as a warning in its own right',
  st.promptFires.some(p => p.id === 'potassium_chloride_kcl' && p.level === 2 && p.t === 170) && said(st, /^Nothing has gone in for her potassium/));
chk('no prompt says "still"', !CASE.case_actions.some(a => a.prompt && (/\bstill\b/.test(a.prompt.text) || (a.prompt.escalation && /\bstill\b/.test(a.prompt.escalation.text)))));
st = F([], 700, 3);
chk('default mode: the chemistry prompt at 225 and no potassium prompt with nothing sent',
  st.promptFires.some(p => p.id === 'basic_chemistry_chem_7' && p.t === 225) && !st.promptFires.some(p => p.id === 'potassium_chloride_kcl'));
st = F([[240.5, 'basic_chemistry_chem_7']], 335, 3);
chk('default mode: a learner who needed the chemistry prompt hears the potassium prompt at 330',
  st.promptFires.some(p => p.id === 'potassium_chloride_kcl' && p.level === 1 && p.t === 330));
st = F(LINE.concat([[20.5, 'insulin_drip']]), 400);
chk('in the falling phase the escalation claims no result, with no chemistry ever sent',
  said(st, /^Nothing has gone in for her potassium/) && !st.resulted.has('basic_chemistry_chem_7'));
chk('five prompts are inside the cap in every phase', PROTO.promptCap === 5);

section('the interview: marks, volunteers and facts');
const T = id => CASE.interview.topics.find(t => t.topic === id);
const ask = (topic, t, extra) => F([Object.assign({ t, kind: 'interview', topic, q: '?' }, extra || {})], t + 1).readouts.pop().body;
chk('every topic marked a pertinent negative denies', CASE.interview.topics.filter(t => t.pertinent_negative)
  .every(t => t.answer.every(r => /^'(No\b|I don't think so)/.test(r.value))), CASE.interview.topics.filter(t => t.pertinent_negative).map(t => t.topic).join());
chk('fever, headache and family history report something and are not marked',
  ['fever_and_chills', 'headache', 'family_history'].every(id => !T(id).pertinent_negative));
chk('key topics match the held-out file', CASE.interview.key_topics.slice().sort().join() ===
  ['allergies', 'current_medications', 'diabetes_history', 'glucose_monitoring', 'insulin_taken_recently', 'past_medical_history', 'pregnancy', 'sick_contacts', 'thirst_and_urination'].join());
chk('no key topic is volunteered or listed as adjacent', CASE.interview.key_topics.every(id => !T(id).volunteer) &&
  CASE.interview.topics.every(t => (t.adjacent || []).every(a => !CASE.interview.key_topics.includes(a))));
chk('past medical history is must-ask', CASE.interview.must_ask.includes('past_medical_history'));
chk('asking the onset volunteers the diarrhea without repeating the answer', /It's watery, six or seven times a day/.test(ask('onset', 5)) && !/And diarrhea since Sunday/.test(ask('onset', 5)));
chk('asking about the pain volunteers nothing', !/mostly the middle/.test(ask('abdominal_pain', 5)));
chk('asking about urine volunteers nothing about thirst', !/thirsty/.test(ask('urine_output', 5)));
chk('weakness answers the cramps question, on arrival and after early insulin', /No cramps/.test(ask('weakness', 5)) &&
  /No cramps/.test(F(LINE.concat([[20.5, 'insulin_drip'], { t: 40.5, kind: 'interview', topic: 'weakness', q: '?' }]), 41).readouts.pop().body));
chk('the diarrhea answer covers blood and black stools', /No blood in it, and it isn't black/.test(ask('diarrhea', 5)));
chk('the weakness, thirst and social topics hold the questions the bank used to refuse',
  T('weakness').variants.includes('Any cramps in your legs?') && T('thirst_and_urination').variants.includes('Are you up at night to pee?') &&
  T('social_history').variants.includes('What are you studying?') && T('radiation_of_pain').variants.includes('Any back pain?'));
const bank = CASE.interview.out_of_scope_bank.join(' | ');
chk('the out-of-scope bank holds no question she can answer',
  !/night to pass water|weakness in your arms|cramps in your legs|blood when you open|black stools|studying|living\?|back pain|excessive thirst/i.test(bank), bank.slice(0, 200));
chk('palpitations sit under one topic only', !T('chest_pain').variants.concat(T('chest_pain').expanded_variants || []).some(q => /palpitations|heart symptoms/i.test(q)));
chk('no insulin question names tablets', !T('insulin_taken_recently').variants.concat(T('insulin_taken_recently').expanded_variants || []).some(q => /tablet/i.test(q)));
chk('no sick-contact phrasing asks about her own recent illness', !(T('sick_contacts').expanded_variants || []).some(q => /Have you been unwell recently|Any recent infection|Recent cold or flu/.test(q)));
chk('asked a second time, the short form keeps the denial',
  /No cramps/.test(F([{ t: 5, kind: 'interview', topic: 'weakness', q: '?' }, { t: 6, kind: 'interview', topic: 'weakness', q: 'Any cramps in your legs?' }], 7).readouts.pop().body) &&
  /No blood, and it isn't black/.test(F([{ t: 5, kind: 'interview', topic: 'diarrhea', q: '?' }, { t: 6, kind: 'interview', topic: 'diarrhea', q: 'Any black stools?' }], 7).readouts.pop().body));
chk('six topics carry facts, each restating its paragraph', ['onset', 'diarrhea', 'weakness', 'current_medications', 'insulin_taken_recently', 'glucose_monitoring']
  .every(id => (T(id).facts || []).length >= 2 && T(id).facts.some(f => f.restate)));
chk('a dose question gets the dose, not the paragraph', /^'Eighteen units of Lantus at night\.'$/.test(
  F([{ t: 5, kind: 'interview', topic: 'current_medications', q: '?' }, { t: 6, kind: 'interview', topic: 'current_medications', fact: 'basal', q: 'what dose?' }], 7).readouts.pop().body));
chk('US usage in her answers', !/I've got|Loads|ages ago|got flu/.test(JSON.stringify(CASE.interview.topics.map(t => t.answer))));

section('the handoff');
st = F(ready.concat([[50.5, 'insulin_drip'], [70.5, 'handoff_submit']]), 75);
chk('completes the case', st.complete && st.phase === 'case_complete');
chk('and keeps the vitals she was handed over with', st.vitals.heart_rate === 104, String(st.vitals.heart_rate));
st = F(A0.concat([[10.5, 'normal_saline_1l_bolus'], [30.5, 'handoff_submit']]), 35);
chk('handing over an untreated patient shows the untreated patient', st.vitals.heart_rate === 102, String(st.vitals.heart_rate));
st = F(rescue([[20.5, 'insulin_drip']]).concat([[90.5, 'handoff_submit']]), 95);
chk('handed over from recovering with insulin still off, the restart is listed as missed',
  st.complete && st.expected.has('insulin_restart') && !st.satisfied.has('insulin_restart') && st.satisfied.has('insulin_drip'));
const DX = ['dx_diabetic_ketoacidosis', 'dx_hypokalemia', 'dx_hypomagnesemia', 'dx_viral_gastroenteritis', 'dx_hypovolemia'];
const handed = dx => F(ready.concat([[50.5, 'insulin_drip'], { t: 70.5, actionId: 'handoff_submit',
  payload: { disposition: 'stepdown_telemetry', diagnoses: dx } }]), 75);
let hs = summaryScores(handed(DX.concat(['dx_hyponatremia', 'dx_acute_kidney_injury']))).find(r => r.id === 'handoff');
chk('naming the low sodium and the raised creatinine costs nothing', hs.points === 100 && !/unsupported/.test(hs.detail), JSON.stringify(hs));
chk('and neither is credited, because the sodium corrects to normal and the creatinine has no baseline',
  /1 of 1 additional/.test(hs.detail) && !/missed/.test(hs.detail), hs.detail);
hs = summaryScores(handed(DX)).find(r => r.id === 'handoff');
chk('and leaving them out is still 1 of 1 additional diagnoses', /1 of 1 additional/.test(hs.detail), hs.detail);
/* 23 October 2026: the magnesium, the trigger and the volume are minor diagnoses. */
hs = summaryScores(handed(['dx_diabetic_ketoacidosis', 'dx_hypokalemia'])).find(r => r.id === 'handoff');
chk('leaving out hypomagnesemia, the gastroenteritis and hypovolemia costs nothing', hs.points === 100, hs.detail);

section('potassium continues with the insulin (the table\'s middle row, owner decision of 7 October 2026)');
const treatedNoK = A0.concat([[20.5, 'potassium_chloride_kcl'], [45.5, 'basic_chemistry_chem_7'], [52.5, 'insulin_drip']]);
st = F(treatedNoK, 70);
chk('once treated, potassium with the insulin is a critical action', st.phase === 'treated' && st.expected.has('potassium_maintenance') && !st.satisfied.has('potassium_maintenance'));
chk('it is not expected on arrival', !F(A0, 10).expected.has('potassium_maintenance'));
chk('the first potassium order does not credit it', !F(ready, 45).satisfied.has('potassium_maintenance'));
chk('the first order says it takes a while', said(F(ready, 25), /It takes a while to run in/) && !said(F(ready, 25), /Twenty to thirty/));
st = F(treatedNoK, 110.5);
chk('the nurse asks for potassium in her fluids at 45 seconds into treated', st.promptFires.some(p => p.id === 'potassium_maintenance') && said(st, /Do you want potassium in her fluids\?/), JSON.stringify(st.promptFires.map(p => p.id)));
chk('and not before', !F(treatedNoK, 105).promptFires.some(p => p.id === 'potassium_maintenance'));
chk('in the default mode it comes at 135 seconds', F(treatedNoK, 200, 3).promptFires.some(p => p.id === 'potassium_maintenance') && !F(treatedNoK, 195, 3).promptFires.some(p => p.id === 'potassium_maintenance'));
st = F(treatedNoK.concat([[80.5, 'potassium_chloride_kcl']]), 120);
chk('a second potassium order once treated credits it', st.satisfied.has('potassium_maintenance'));
chk('with the second nurse line', said(st, /Twenty to thirty in each liter from here/));
chk('and then no prompt', !st.promptFires.some(p => p.id === 'potassium_maintenance'));
chk('the phase does not change', st.phase === 'treated');
st = F(ready.concat([[45.5, 'basic_chemistry_chem_7'], [47.5, 'potassium_chloride_kcl'], [52.5, 'insulin_drip']]), 70);
chk('a second order placed after the level, before the insulin, counts too', st.satisfied.has('potassium_maintenance') && st.phase === 'treated');
st = F(rescue([[20.5, 'insulin_drip']]), 70);
chk('the rescue potassium in the falling phase is not the maintenance order', !st.satisfied.has('potassium_maintenance') && st.phase === 'recovering');
st = F(rescue([[20.5, 'insulin_drip']]).concat([[80.5, 'insulin_drip'], [82.5, 'potassium_chloride_kcl']]), 100);
chk('after the restart, potassium again is', st.satisfied.has('potassium_maintenance') && st.phase === 'treated');
st = F(treatedNoK.concat([[75.5, 'handoff_submit']]), 80);
chk('handed over on insulin with no potassium in the fluids, it is listed as missed', st.complete && st.expected.has('potassium_maintenance') && !st.satisfied.has('potassium_maintenance'));
chk('the endocrinologist asks for it by name once treated', /potassium in her fluids, 20 to 30 in every liter/.test(endo(treatedNoK, 70)));
chk('and not once it is ordered', !/Now potassium in her fluids/.test(endo(treatedNoK.concat([[80.5, 'potassium_chloride_kcl']]), 90)) && /Good\./.test(endo(treatedNoK.concat([[80.5, 'potassium_chloride_kcl']]), 90)));

section('markers sit only where the interface strips them');
const MARK = /\[(UNVERIFIED|PubMed|VERIFY|MODEL OUTPUT)/;
const printed = [];
CASE.follow_ups.forEach(f => printed.push(f.debrief_note, f.nurse_prompt));
const H = CASE.handoff;
[H.correct_disposition, H.correct_diagnosis].concat(H.alternative_dispositions, H.alternative_diagnoses, H.additional_diagnoses).forEach(x => printed.push(x.explanation));
CASE.case_actions.forEach(a => printed.push(a.narration_override, a.nurse_alert, a.prompt && a.prompt.text, a.prompt && a.prompt.escalation && a.prompt.escalation.text, a.display_name, a.expectation_label));
CASE.phases.forEach(p => (p.transitions || []).forEach(t => printed.push(t.narration)));
CASE.interview.topics.forEach(t => t.answer.forEach(r => printed.push(r.value)));
printed.push(JSON.stringify(CASE.content_keys.consultants), JSON.stringify(CASE.content_keys.exam));
chk('no marker in a field the learner reads as written', !printed.some(x => x && MARK.test(x)));
const cites = a => /consensus report|the report\b|drug label|2009/.test(a.debrief_note || '');
chk('every action note that cites a source carries a marker', CASE.case_actions.filter(cites).every(a => MARK.test(a.debrief_note)),
  CASE.case_actions.filter(a => cites(a) && !MARK.test(a.debrief_note)).map(a => a.catalog_id).join());
chk('the reference status is a list, one entry per reference, each with how it was read',
  Array.isArray(CASE.provenance.reference_status) && CASE.provenance.reference_status.length >= 6 &&
  CASE.provenance.reference_status.every(r => r.reference && r.how_read && r.status));
const STYLE = /[—–;]|\bquiet(ly)?\b/i;
const learnerStrings = printed.concat(CASE.case_actions.map(a => a.debrief_note), CASE.debrief_configuration.cross_cutting_teaching_points,
  CASE.phases.flatMap(p => (p.transitions || []).map(t => t.debrief_note)));
chk('house style: no dash, no semicolon and no banned word in anything a learner reads',
  !learnerStrings.some(x => x && STYLE.test(String(x).replace(/\[[^\]]*\]/g, ''))),
  String(learnerStrings.find(x => x && STYLE.test(String(x).replace(/\[[^\]]*\]/g, '')))).slice(0, 120));
