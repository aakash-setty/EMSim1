/* Case assertions for SWEET (refractory anaphylaxis in a 12-year-old).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * One section per claim the case makes. Fractional times where two events meet.
 */

const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const V = (log, t) => fold(mk(log), t).vitals;
const START = [[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'second_iv']];
const fires = (st, id) => st.promptFires.filter(p => p.id === id);

section('intended path');
let st = fold(mk(START.concat([[10, 'epinephrine_intramuscular'], [12, 'lay_back_legs_raised'],
  [14, 'normal_saline_500ml_bolus'], [140, 'consult_critical_care'], [145, 'epinephrine_drip'],
  [150, 'normal_saline_500ml_bolus'], [210, 'exam_abc'], [212, 'albuterol']])), 460);
chk('reaches settling through still struggling and talking again',
  seq(st) === 'presentation > persistent > responding > stabilized', seq(st));
st = fold(mk(START.concat([[10, 'epinephrine_intramuscular'], [12, 'lay_back_legs_raised'],
  [14, 'normal_saline_500ml_bolus'], [140, 'consult_critical_care'], [145, 'epinephrine_drip'],
  [150, 'normal_saline_500ml_bolus'], [460, 'handoff_submit']])), 470);
chk('and completes', st.phase === 'case_complete' && st.complete, st.phase);
chk('nothing failed or halted', !st.halted && !st.failed);
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)),
  [...st.expected].filter(id => !st.satisfied.has(id)).join(', '));

section('the first ED dose: on at 10 seconds, gone by 120, then worse');
let v = V(START.concat([[10, 'epinephrine_intramuscular']]), 15);
chk('nothing yet at 5 seconds', v.heart_rate === 140 && v.systolic_bp === 88, JSON.stringify(v));
v = V(START.concat([[10, 'epinephrine_intramuscular']]), 21);
chk('at 11 seconds the monitor is better (146, 100/62, 28, 95)',
  v.heart_rate === 146 && v.systolic_bp === 100 && v.diastolic_bp === 62 && v.respiratory_rate === 28 && v.oxygen_saturation === 95,
  JSON.stringify(v));
v = V(START.concat([[10, 'epinephrine_intramuscular']]), 89);
chk('full effect to 79 seconds', v.heart_rate === 146 && v.systolic_bp === 100, JSON.stringify(v));
v = V(START.concat([[10, 'epinephrine_intramuscular']]), 95);
chk('fading by two thirds from 80 (144, 96/59, 29, 94)',
  v.heart_rate === 144 && v.systolic_bp === 96 && v.diastolic_bp === 59 && v.respiratory_rate === 29 && v.oxygen_saturation === 94,
  JSON.stringify(v));
v = V(START.concat([[10, 'epinephrine_intramuscular']]), 115);
chk('a third left from 100 (142, 92/57, 31, 94)',
  v.heart_rate === 142 && v.systolic_bp === 92 && v.diastolic_bp === 57 && v.respiratory_rate === 31 && v.oxygen_saturation === 94,
  JSON.stringify(v));
st = fold(mk(START.concat([[10, 'epinephrine_intramuscular']])), 129.5);
chk('still on arrival at 119.5 seconds after the dose', st.phase === 'presentation', st.phase);
st = fold(mk(START.concat([[10, 'epinephrine_intramuscular']])), 130.5);
chk('still struggling at 120 seconds after the dose', st.phase === 'persistent', st.phase);
chk('and the monitor is the worse phase, with no effect left', st.vitals.heart_rate === 152 && st.vitals.systolic_bp === 76, JSON.stringify(st.vitals));
chk('the nurse says it wore off', st.nurse.some(n => /worn off/.test(n.text)));
chk('he said a bit better, and only after it had started acting',
  fold(mk(START.concat([[10, 'epinephrine_intramuscular']])), 15).flags.has('epi_onset') &&
  !fold(mk(START.concat([[10, 'epinephrine_intramuscular']])), 25).flags.has('epi_onset'));

section('no ED epinephrine');
st = fold(mk([]), 179.5);
chk('on arrival at 179.5', st.phase === 'presentation');
st = fold(mk([]), 180.5);
chk('still struggling at 180', st.phase === 'persistent', st.phase);
chk('the epinephrine prompt fired on arrival', fold(mk([]), 100).promptFires.some(p => p.id === 'epinephrine_intramuscular'));
chk('normal mode: the epinephrine prompt lands before 160',
  fold(mk([]), 179, 3).promptFires.some(p => p.id === 'epinephrine_intramuscular' && p.t <= 160),
  JSON.stringify(fold(mk([]), 179, 3).promptFires));
st = fold(mk([[200, 'epinephrine_intramuscular']]), 205);
chk('a first ED dose given late is critical in phase 2', st.expected.has('epinephrine_intramuscular') && st.satisfied.has('epinephrine_intramuscular'));

section('doing nothing');
chk('phase 3 at 330', fold(mk([]), 330.5).phase === 'worsening', fold(mk([]), 330.5).phase);
chk('phase 4 at 480', fold(mk([]), 480.5).phase === 'peri_arrest', fold(mk([]), 480.5).phase);
st = fold(mk([]), 661);
chk('the terminal phase at 660', st.phase === 'bradycardic_arrest' && st.failed, st.phase);

section('phase 2: the infusion window');
const P2 = START.concat([[10, 'epinephrine_intramuscular']]);   // phase 2 from 130
st = fold(mk(P2), 279.5);
chk('no infusion: still struggling at 149.5 into phase 2', st.phase === 'persistent', st.phase);
st = fold(mk(P2), 280.5);
chk('no infusion: floppy at 150', st.phase === 'worsening', st.phase);
st = fold(mk(P2.concat([[140, 'consult_critical_care'], [145, 'epinephrine_drip']])), 204.5);
chk('with help called, not yet running at 59.5 seconds', st.phase === 'persistent', st.phase);
st = fold(mk(P2.concat([[140, 'consult_critical_care'], [145, 'epinephrine_drip']])), 205.5);
chk('with help called, talking again at 60 seconds', st.phase === 'responding', st.phase);
st = fold(mk(P2.concat([[145, 'epinephrine_drip']])), 264.5);
chk('without help, not yet at 119.5', st.phase === 'persistent', st.phase);
st = fold(mk(P2.concat([[145, 'epinephrine_drip']])), 265.5);
chk('without help, talking again at 120', st.phase === 'responding', st.phase);
st = fold(mk(P2.concat([[145, 'epinephrine_drip'], [200, 'consult_critical_care']])), 260.5);
chk('help called after the order: 60 seconds from the call', st.phase === 'responding', st.phase);
st = fold(mk(P2.concat([[260, 'epinephrine_drip']])), 371);
chk('ordered late without help: floppy at 240 (370), before it runs (380)', st.phase === 'worsening', seq(fold(mk(P2.concat([[260, 'epinephrine_drip']])), 371)));
st = fold(mk(P2.concat([[260, 'epinephrine_drip']])), 470);
chk('and then it runs in phase 3 (90 seconds there)', st.phase === 'responding', seq(st));
chk('the infusion prompt fires in phase 2', fold(mk(P2), 200).promptFires.some(p => p.id === 'epinephrine_drip'));
chk('normal mode: the infusion prompt lands before the 150-second exit',
  fold(mk(P2), 280, 3).promptFires.some(p => p.id === 'epinephrine_drip' && p.t <= 260),
  JSON.stringify(fold(mk(P2), 280, 3).promptFires));

section('a second IM dose: shorter, and never sooner than no dose');
v = V(P2.concat([[140, 'epinephrine_intramuscular']]), 151);
chk('it works at 10 seconds, smaller (156, 84/44)', v.heart_rate === 156 && v.systolic_bp === 84 && v.diastolic_bp === 44, JSON.stringify(v));
v = V(P2.concat([[140, 'epinephrine_intramuscular']]), 185);
chk('fading from 40', v.heart_rate === 155 && v.systolic_bp === 81, JSON.stringify(v));
v = V(P2.concat([[140, 'epinephrine_intramuscular']]), 195);
chk('a third left from 50', v.heart_rate === 153 && v.systolic_bp === 79, JSON.stringify(v));
v = V(P2.concat([[140, 'epinephrine_intramuscular']]), 201);
chk('and is gone by 60', v.heart_rate === 152 && v.systolic_bp === 76, JSON.stringify(v));
st = fold(mk(P2.concat([[140, 'epinephrine_intramuscular']])), 279.5);
chk('given early, he still holds to 150 into the phase', st.phase === 'persistent', st.phase);
st = fold(mk(P2.concat([[140, 'epinephrine_intramuscular']])), 280.5);
chk('and goes floppy at 150, not sooner', st.phase === 'worsening', st.phase);
st = fold(mk(P2.concat([[260, 'epinephrine_intramuscular']])), 285);
chk('given late, it holds him past 150 while it acts', st.phase === 'persistent', st.phase);
st = fold(mk(P2.concat([[260, 'epinephrine_intramuscular']])), 320.5);
chk('and he goes floppy as it wears off (60 seconds after)', st.phase === 'worsening', st.phase);
st = fold(mk(P2), 135);
chk('the second dose is recommended, not critical, after a first ED dose',
  !(st.expectedByPhase.persistent || new Set()).has('epinephrine_intramuscular'));
st = fold(mk([]), 200);
chk('and critical in phase 2 when no ED dose was given',
  (st.expectedByPhase.persistent || new Set()).has('epinephrine_intramuscular'));

section('phase 3 and the rescue from phase 4');
const P3 = P2;   // floppy at 280
st = fold(mk(P3.concat([[290, 'consult_critical_care'], [292, 'epinephrine_drip'], [295, 'normal_saline_500ml_bolus']])), 353);
chk('in phase 3 an order with help runs in 60 seconds', st.phase === 'responding', seq(st));
st = fold(mk(P3.concat([[290, 'normal_saline_500ml_bolus']])), 430.5);
chk('no infusion in phase 3: silent at 150', st.phase === 'peri_arrest', st.phase);
st = fold(mk(P3.concat([[290, 'epinephrine_drip']])), 369.5);
chk('ordered without help in phase 3: not yet at 89.5', st.phase === 'worsening', seq(st));
st = fold(mk(P3.concat([[290, 'epinephrine_drip']])), 380.5);
chk('and talking again at 90', st.phase === 'responding', seq(st));
const RELAPSE = START.concat([[10, 'epinephrine_intramuscular'], [140, 'consult_critical_care'],
  [145, 'epinephrine_drip'], [300, 'stop_epinephrine']]);   // floppy again at 420
st = fold(mk(RELAPSE), 659.5);
chk('after a relapse, no restart and no bolus: floppy to 239.5', st.phase === 'worsening', seq(st));
st = fold(mk(RELAPSE), 660.5);
chk('and silent at 240', st.phase === 'peri_arrest', seq(st));
st = fold(mk(RELAPSE.concat([[430, 'normal_saline_500ml_bolus']])), 700);
chk('a bolus there holds him to the 360-second limit', st.phase === 'worsening', seq(st));
st = fold(mk(RELAPSE.concat([[430, 'normal_saline_500ml_bolus']])), 780.5);
chk('and then silent', st.phase === 'peri_arrest', seq(st));
st = fold(mk(P3.concat([[435, 'epinephrine_intramuscular'], [436, 'normal_saline_500ml_bolus']])), 467);
chk('epinephrine and a bolus at the edge bring him back to floppy', st.phase === 'worsening' && st.flags.has('rescued_once'), seq(st));
st = fold(mk(P3.concat([[435, 'epinephrine_intramuscular'], [436, 'normal_saline_500ml_bolus']])), 2000);
chk('and without the infusion he ends in the terminal phase, no second rescue', st.phase === 'bradycardic_arrest', seq(st));
st = fold(mk([]), 660.5);
chk('peri-arrest unrescued ends at 180', st.phase === 'bradycardic_arrest');

section('the airway');
st = fold(mk(P2.concat([[200, 'ketamine_bolus'], [200, 'rocuronium_bolus'], [201, 'intubate_rapid_sequence']])), 205);
chk('a tube with no infusion collapses him', st.phase === 'post_induction_collapse', seq(st));
st = fold(mk(P2.concat([[200, 'ketamine_bolus'], [200, 'rocuronium_bolus'], [201, 'intubate_rapid_sequence']])), 352);
chk('and ends in the terminal phase at 150 with no bridge', st.phase === 'bradycardic_arrest', seq(st));
st = fold(mk(P2.concat([[200, 'ketamine_bolus'], [200, 'rocuronium_bolus'], [201, 'intubate_rapid_sequence'],
  [205, 'epinephrine_bolus'], [210, 'consult_critical_care'], [211, 'epinephrine_drip']])), 272);
chk('a bridge and the infusion: ventilated 60 seconds after the order with help', st.phase === 'ventilated', seq(st));
const RUN = P2.concat([[140, 'consult_critical_care'], [145, 'epinephrine_drip']]);
st = fold(mk(RUN.concat([[300, 'ketamine_bolus'], [300, 'rocuronium_bolus'], [301, 'intubate_rapid_sequence']])), 305);
chk('a tube with the infusion running: ventilated', st.phase === 'ventilated', seq(st));
chk('the decision to intubate is discouraged there', st.discouragedTaken.has('intubate_rapid_sequence'));

section('sedation');
st = fold(mk(START.concat([[20, 'lorazepam_bolus']])), 22);
chk('lorazepam on arrival: one phase worse at once', st.phase === 'persistent' && st.discouragedTaken.has('lorazepam_bolus'), st.phase);
st = fold(mk(START.concat([[20, 'midazolam_bolus']])), 22);
chk('midazolam does the same, unscored', st.phase === 'persistent' && !st.discouragedTaken.has('midazolam_bolus'), st.phase);
st = fold(mk(P2.concat([[150, 'morphine_bolus']])), 152);
chk('morphine in phase 2: floppy at once', st.phase === 'worsening', st.phase);
st = fold(mk(RUN.concat([[300, 'lorazepam_bolus']])), 302);
chk('after the infusion runs, a sedative moves no phase', st.phase === 'responding', st.phase);

section('stopping and restarting the infusion');
st = fold(mk(RUN.concat([[300, 'stop_epinephrine']])), 421);
chk('stopped: floppy 120 seconds later', st.phase === 'worsening' && st.flags.has('relapsed'), seq(st));
st = fold(mk(RUN.concat([[300, 'stop_epinephrine'], [430, 'epinephrine_drip']])), 461);
chk('restarted: talking again 30 seconds later', st.phase === 'responding', seq(st));
st = fold(mk(RUN.concat([[300, 'stop_epinephrine'], [430, 'epinephrine_drip']])), 900);
chk('and the stop does not play twice', st.phase !== 'worsening' && st.phaseSeq.filter(p => p.id === 'worsening').length === 1, seq(st));

section('fluid and settling');
const ONE = START.concat([[10, 'epinephrine_intramuscular'], [14, 'normal_saline_500ml_bolus'],
  [140, 'consult_critical_care'], [145, 'epinephrine_drip']]);   // responding at 205
st = fold(mk(ONE), 600);
chk('one bolus only: holds at talking again', st.phase === 'responding', seq(st));
chk('and the nurse asks for more fluid', st.promptFires.some(p => p.id === 'fluid_here_p5'));
st = fold(mk(ONE.concat([[300, 'normal_saline_1l_bolus']])), 386);
chk('one more bolus there: settling 180 seconds after entry', st.phase === 'stabilized', seq(st));
v = V(START.concat([[20, 'normal_saline_500ml_bolus']]), 40);
chk('a bolus lifts the pressure while it runs', v.systolic_bp === 95 && v.heart_rate === 135, JSON.stringify(v));
v = V(START.concat([[20, 'lay_back_legs_raised']]), 25);
chk('lying back with legs raised lifts it a little', v.systolic_bp === 93, JSON.stringify(v));

section('the infusion needs the monitor and a second line');
st = fold(mk([[2, 'insert_iv'], [10, 'epinephrine_drip']]), 12);
chk('blocked without the monitor', st.blocked.some(b => b.id === 'epinephrine_drip') && !st.flags.has('epi_drip_ordered'));
st = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [10, 'epinephrine_drip']]), 12);
chk('blocked with only one line', st.blocked.some(b => b.id === 'epinephrine_drip') && !st.flags.has('epi_drip_ordered'));
st = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'intraosseous_line'], [10, 'epinephrine_drip']]), 12);
chk('an IV and an IO will do', st.flags.has('epi_drip_ordered'));

section('adjuncts and other drugs');
st = fold(mk(START.concat([[10, 'diphenhydramine'], [11, 'methylprednisolone_bolus'], [12, 'albuterol']])), 20);
chk('adjuncts before the ED dose are discouraged',
  ['diphenhydramine', 'methylprednisolone_bolus', 'albuterol'].every(id => st.discouragedTaken.has(id)));
st = fold(mk(START.concat([[5, 'epinephrine_intramuscular'], [10, 'diphenhydramine'], [12, 'albuterol']])), 20);
chk('after it they are not', !st.discouragedTaken.has('diphenhydramine') && !st.discouragedTaken.has('albuterol'));
st = fold(mk(P2.concat([[150, 'norepinephrine_drip']])), 200);
chk('norepinephrine lifts the pressure and moves no phase', st.phase === 'persistent' && st.vitals.systolic_bp > 76, JSON.stringify(st.vitals));
chk('and is discouraged', st.discouragedTaken.has('norepinephrine_drip'));

section('prompts');
const all = CASE.case_actions.filter(a => a.prompt).map(a => a.prompt.text).concat(
  CASE.case_actions.filter(a => a.prompt && a.prompt.escalation).map(a => a.prompt.escalation.text));
chk('no prompt quotes a number', all.every(t => !/\d/.test(t)), all.filter(t => /\d/.test(t)).join(' | '));
st = fold(mk([]), 179, 3);
chk('normal mode, doing nothing: the epinephrine prompt is heard before phase 2', fires(st, 'epinephrine_intramuscular').length > 0);
