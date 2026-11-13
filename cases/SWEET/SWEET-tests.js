/* Case assertions for SWEET (refractory anaphylaxis in a 12-year-old).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * One section per claim the case makes. Fractional times where two events meet.
 *
 * Timing (owner, 11 and 13 November 2026): the first ED IM dose acts from 10 s and is gone by
 * 60 s, a later dose from 10 s to 40 s. The infusion runs 10 s after the order.
 */

const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const V = (log, t) => fold(mk(log), t).vitals;
const START = [[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'second_iv']];
const IM = START.concat([[10, 'epinephrine_intramuscular']]);   // phase 2 from 70
const RUN = IM.concat([[75, 'epinephrine_drip']]);              // running, responding from 85
const byPhase = (st, ph) => st.expectedByPhase[ph] || new Set();
let st, v;

section('intended path');
const PATH = START.concat([[10, 'epinephrine_intramuscular'], [12, 'exam_airway'], [13, 'lay_back_legs_raised'],
  [14, 'normal_saline_500ml_bolus'], [75, 'exam_breath'], [76, 'epinephrine_drip'], [77, 'consult_critical_care'],
  [80, 'normal_saline_500ml_bolus'], [120, 'albuterol']]);
st = fold(mk(PATH), 280);
chk('reaches settling through still struggling and talking again',
  seq(st) === 'presentation > persistent > responding > stabilized', seq(st));
st = fold(mk(PATH.concat([[290, 'handoff_submit']])), 300);
chk('and completes', st.phase === 'case_complete' && st.complete, st.phase);
chk('nothing failed or halted', !st.halted && !st.failed);
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)),
  [...st.expected].filter(id => !st.satisfied.has(id)).join(', '));

section('the critical actions (owner, 13 November 2026)');
st = fold(mk([]), 200);
chk('monitor, lines, posture and the PICU call are not critical in any phase reached',
  ['attach_monitor', 'insert_iv', 'second_iv', 'lay_back_legs_raised', 'consult_critical_care'].every(id => !st.expected.has(id)),
  [...st.expected].join(', '));
chk('they are recommended', ['attach_monitor', 'insert_iv', 'lay_back_legs_raised', 'consult_critical_care']
  .every(id => st.recommendedExpected.has(id)), [...st.recommendedExpected].join(', '));
chk('the airway exam, IM epinephrine and a bolus are critical on arrival',
  ['exam_airway', 'epinephrine_intramuscular', 'normal_saline_500ml_bolus'].every(id => byPhase(st, 'presentation').has(id)),
  [...byPhase(st, 'presentation')].join(', '));
chk('the infusion is critical once he is still struggling', byPhase(st, 'persistent').has('epinephrine_drip'));
st = fold(mk(IM), 100);
chk('looking at him again is critical when the ED dose wears off', byPhase(st, 'persistent').has('reassessed_after_epi'));
chk('and is not met by an exam before the dose',
  !fold(mk(START.concat([[5, 'exam_airway'], [10, 'epinephrine_intramuscular']])), 100).satisfied.has('reassessed_after_epi'));
chk('an exam after the dose meets it',
  fold(mk(IM.concat([[80, 'exam_circ']])), 100).satisfied.has('reassessed_after_epi'));
chk('the nurse asks for another look in phase 2', fold(mk(IM), 160).promptFires.some(p => p.id === 'reassessed_after_epi'));
chk('the airway exam after a dose meets both the airway and the reassessment',
  ['exam_airway', 'reassessed_after_epi'].every(id => fold(mk(IM.concat([[80, 'exam_airway']])), 90).satisfied.has(id)));

section('the first ED dose: on at 10 seconds, gone by 60, then worse');
v = V(IM, 15);
chk('nothing yet at 5 seconds', v.heart_rate === 140 && v.systolic_bp === 88, JSON.stringify(v));
v = V(IM, 21);
chk('at 11 seconds the monitor is better (146, 100/62, 28, 95)',
  v.heart_rate === 146 && v.systolic_bp === 100 && v.diastolic_bp === 62 && v.respiratory_rate === 28 && v.oxygen_saturation === 95,
  JSON.stringify(v));
v = V(IM, 49);
chk('full effect to 39 seconds', v.heart_rate === 146 && v.systolic_bp === 100, JSON.stringify(v));
v = V(IM, 55);
chk('fading by two thirds from 40 (144, 96/59, 29, 94)',
  v.heart_rate === 144 && v.systolic_bp === 96 && v.diastolic_bp === 59 && v.respiratory_rate === 29 && v.oxygen_saturation === 94,
  JSON.stringify(v));
v = V(IM, 65);
chk('a third left from 50 (142, 92/57, 31, 94)',
  v.heart_rate === 142 && v.systolic_bp === 92 && v.diastolic_bp === 57 && v.respiratory_rate === 31 && v.oxygen_saturation === 94,
  JSON.stringify(v));
st = fold(mk(IM), 69.5);
chk('still on arrival at 59.5 seconds after the dose', st.phase === 'presentation', st.phase);
st = fold(mk(IM), 70.5);
chk('still struggling at 60 seconds after the dose', st.phase === 'persistent', st.phase);
chk('and the monitor is the worse phase, with no effect left', st.vitals.heart_rate === 152 && st.vitals.systolic_bp === 76, JSON.stringify(st.vitals));
chk('the nurse says it wore off', st.nurse.some(n => /worn off/.test(n.text)));

section('no ED epinephrine');
chk('on arrival at 179.5', fold(mk([]), 179.5).phase === 'presentation');
chk('still struggling at 180', fold(mk([]), 180.5).phase === 'persistent');
chk('normal mode: the epinephrine prompt lands before 160',
  fold(mk([]), 179, 3).promptFires.some(p => p.id === 'epinephrine_intramuscular' && p.t <= 160),
  JSON.stringify(fold(mk([]), 179, 3).promptFires));
st = fold(mk([]), 200);
chk('a first ED dose given late is critical in phase 2', byPhase(st, 'persistent').has('epinephrine_intramuscular'));
st = fold(mk(IM), 100);
chk('after a first ED dose, another is recommended in phase 2, not critical',
  !byPhase(st, 'persistent').has('epinephrine_intramuscular') && st.recommendedExpected.has('epinephrine_intramuscular'));
st = fold(mk([]), 700);
chk('the arrival IM prompt does not fire at the edge of arrest',
  !st.promptFires.some(p => p.id === 'epinephrine_intramuscular' && p.t > 480), JSON.stringify(st.promptFires.filter(p => p.t > 480)));

section('doing nothing');
chk('phase 3 at 330', fold(mk([]), 330.5).phase === 'worsening');
chk('phase 4 at 480', fold(mk([]), 480.5).phase === 'peri_arrest');
st = fold(mk([]), 661);
chk('the terminal phase at 660', st.phase === 'bradycardic_arrest' && st.failed, st.phase);

section('the infusion: running 10 seconds after the order');
st = fold(mk(RUN), 84.5);
chk('not yet at 9.5 seconds', st.phase === 'persistent', st.phase);
st = fold(mk(RUN), 85.5);
chk('talking again at 10 seconds', st.phase === 'responding', st.phase);
chk('the nurse says pharmacy is sending it', fold(mk(RUN), 76).nurse.some(n => /Pharmacy/.test(n.text)));
st = fold(mk(RUN.concat([[76, 'consult_critical_care']])), 85.5);
chk('calling PICU does not change it', st.phase === 'responding', seq(st));
st = fold(mk(START.concat([[20, 'epinephrine_drip']])), 30.5);
chk('ordered on arrival before any ED dose: it runs, and is discouraged',
  st.phase === 'responding' && st.discouragedTaken.has('epinephrine_drip'), seq(st));
st = fold(mk(IM), 219.5);
chk('no infusion: still struggling at 149.5 into phase 2', st.phase === 'persistent', st.phase);
st = fold(mk(IM), 220.5);
chk('no infusion: floppy at 150', st.phase === 'worsening', st.phase);
st = fold(mk(IM.concat([[230, 'epinephrine_drip']])), 240.5);
chk('ordered in phase 3: talking again 10 seconds later', st.phase === 'responding', seq(st));
chk('the infusion prompt fires in phase 2', fold(mk(IM), 150).promptFires.some(p => p.id === 'epinephrine_drip'));
chk('normal mode: the infusion prompt lands before the 150-second exit',
  fold(mk(IM), 220, 3).promptFires.some(p => p.id === 'epinephrine_drip' && p.t <= 200),
  JSON.stringify(fold(mk(IM), 220, 3).promptFires));

section('a second IM dose: shorter, and never sooner than no dose');
v = V(IM.concat([[80, 'epinephrine_intramuscular']]), 91);
chk('it works at 10 seconds, smaller (156, 84/44)', v.heart_rate === 156 && v.systolic_bp === 84 && v.diastolic_bp === 44, JSON.stringify(v));
v = V(IM.concat([[80, 'epinephrine_intramuscular']]), 108);
chk('fading from 25', v.heart_rate === 155 && v.systolic_bp === 81, JSON.stringify(v));
v = V(IM.concat([[80, 'epinephrine_intramuscular']]), 115);
chk('a third left from 32', v.heart_rate === 153 && v.systolic_bp === 79, JSON.stringify(v));
v = V(IM.concat([[80, 'epinephrine_intramuscular']]), 121);
chk('and gone by 40', v.heart_rate === 152 && v.systolic_bp === 76, JSON.stringify(v));
st = fold(mk(IM.concat([[80, 'epinephrine_intramuscular']])), 219.5);
chk('given early, he still holds to 150 into the phase', st.phase === 'persistent', st.phase);
st = fold(mk(IM.concat([[80, 'epinephrine_intramuscular']])), 220.5);
chk('and goes floppy at 150, not sooner', st.phase === 'worsening', st.phase);
st = fold(mk(IM.concat([[210, 'epinephrine_intramuscular']])), 245);
chk('given late, it holds him past 150 while it acts', st.phase === 'persistent', st.phase);
st = fold(mk(IM.concat([[210, 'epinephrine_intramuscular']])), 250.5);
chk('and he goes floppy as it wears off (40 seconds after)', st.phase === 'worsening', st.phase);

section('phase 3 and the rescue from phase 4');
st = fold(mk(IM.concat([[230, 'normal_saline_500ml_bolus']])), 370.5);
chk('no infusion in phase 3: silent at 150', st.phase === 'peri_arrest', seq(st));
st = fold(mk(IM.concat([[375, 'epinephrine_intramuscular'], [376, 'normal_saline_500ml_bolus']])), 406.5);
chk('epinephrine and a bolus at the edge bring him back to floppy', st.phase === 'worsening' && st.flags.has('rescued_once'), seq(st));
st = fold(mk(IM.concat([[375, 'epinephrine_intramuscular'], [376, 'normal_saline_500ml_bolus']])), 2000);
chk('and without the infusion he ends in the terminal phase, no second rescue', st.phase === 'bradycardic_arrest', seq(st));
st = fold(mk(IM.concat([[375, 'epinephrine_drip'], [376, 'normal_saline_500ml_bolus']])), 417);
chk('an infusion ordered at the edge counts as the epinephrine, and runs once he is back', st.phase === 'responding', seq(st));
chk('peri-arrest unrescued ends at 180', fold(mk(IM), 550.5).phase === 'bradycardic_arrest', seq(fold(mk(IM), 550.5)));

section('the airway');
const TUBE = [[100, 'ketamine_bolus'], [100, 'rocuronium_bolus'], [101, 'intubate_rapid_sequence']];
st = fold(mk(IM.concat(TUBE)), 105);
chk('a tube with no infusion collapses him', st.phase === 'post_induction_collapse', seq(st));
st = fold(mk(IM.concat(TUBE)), 252);
chk('and ends in the terminal phase at 150 with no bridge', st.phase === 'bradycardic_arrest', seq(st));
st = fold(mk(IM.concat(TUBE, [[105, 'epinephrine_bolus'], [111, 'epinephrine_drip']])), 121.5);
chk('a bridge and the infusion: ventilated 10 seconds after the order', st.phase === 'ventilated', seq(st));
st = fold(mk(RUN.concat([[200, 'ketamine_bolus'], [200, 'rocuronium_bolus'], [201, 'intubate_rapid_sequence']])), 205);
chk('a tube with the infusion running: ventilated', st.phase === 'ventilated', seq(st));
chk('the decision to intubate is discouraged there', st.discouragedTaken.has('intubate_rapid_sequence'));

section('sedation');
st = fold(mk(START.concat([[20, 'lorazepam_bolus']])), 22);
chk('lorazepam on arrival: one phase worse at once', st.phase === 'persistent' && st.discouragedTaken.has('lorazepam_bolus'), st.phase);
st = fold(mk(START.concat([[20, 'midazolam_bolus']])), 22);
chk('midazolam does the same, unscored', st.phase === 'persistent' && !st.discouragedTaken.has('midazolam_bolus'), st.phase);
st = fold(mk(IM.concat([[80, 'morphine_bolus']])), 82);
chk('morphine in phase 2: floppy at once', st.phase === 'worsening', st.phase);
st = fold(mk(RUN.concat([[150, 'lorazepam_bolus']])), 152);
chk('after the infusion runs, a sedative moves no phase', st.phase === 'responding', st.phase);

section('stopping and restarting the infusion');
st = fold(mk(RUN.concat([[200, 'stop_epinephrine']])), 319.5);
chk('stopped: still talking to 119.5 seconds', st.phase === 'responding', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine']])), 320.5);
chk('floppy again at 120, in the relapse phase', st.phase === 'relapse' && st.flags.has('relapsed'), seq(st));
chk('the relapse phase shows what phase 3 shows', st.vitals.heart_rate === 160 && st.vitals.systolic_bp === 70, JSON.stringify(st.vitals));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [330, 'epinephrine_drip']])), 340.5);
chk('restarted: talking again 10 seconds later', st.phase === 'responding', seq(st));
chk('and the restart is credited', st.satisfied.has('drip_restarted'));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [330, 'epinephrine_drip']])), 900);
chk('the stop does not play twice', st.phaseSeq.filter(p => p.id === 'relapse').length === 1 && st.phase !== 'relapse', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine']])), 469.5);
chk('not restarted: floppy to 149.5', st.phase === 'relapse', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine']])), 470.5);
chk('and silent at 150', st.phase === 'peri_arrest', seq(st));
chk('the nurse asks about the pump in the relapse phase', st.promptFires.some(p => p.id === 'drip_restarted'));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [480, 'epinephrine_intramuscular'], [481, 'normal_saline_500ml_bolus']])), 512);
chk('rescued from there, he goes back to the relapse phase, not phase 3', st.phase === 'relapse', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [480, 'epinephrine_intramuscular'], [481, 'normal_saline_500ml_bolus']])), 600);
chk('where the old order does not restart itself', st.phase !== 'responding', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [250, 'epinephrine_drip']])), 331);
chk('restarted before the relapse: back 10 seconds after it (known gap)', st.phase === 'responding' && st.phaseSeq.some(p => p.id === 'relapse'), seq(st));
const VENT = RUN.concat([[150, 'ketamine_bolus'], [150, 'rocuronium_bolus'], [151, 'intubate_rapid_sequence'], [200, 'stop_epinephrine']]);
st = fold(mk(VENT), 320.5);
chk('stopped after the tube: the pressure falls at 120', st.phase === 'vent_relapse', seq(st));
st = fold(mk(VENT.concat([[330, 'epinephrine_drip']])), 340.5);
chk('restarted: ventilated again 10 seconds later', st.phase === 'ventilated', seq(st));
st = fold(mk(VENT), 471);
chk('not restarted: the terminal phase at 150', st.phase === 'bradycardic_arrest', seq(st));
st = fold(mk(RUN.concat([[200, 'stop_epinephrine'], [330, 'ketamine_bolus'], [330, 'rocuronium_bolus'], [331, 'intubate_rapid_sequence']])), 335);
chk('a tube in the relapse phase: the stopped-infusion ventilated phase', st.phase === 'vent_relapse', seq(st));

section('fluid and settling');
const ONE = IM.concat([[14, 'normal_saline_500ml_bolus'], [75, 'epinephrine_drip']]);   // responding at 85
st = fold(mk(ONE), 600);
chk('one bolus only: holds at talking again', st.phase === 'responding', seq(st));
chk('and the nurse asks for more fluid', st.promptFires.some(p => p.id === 'fluid_here_p5'));
st = fold(mk(ONE.concat([[150, 'normal_saline_1l_bolus']])), 330.5);
chk('one more bolus there: settling 180 seconds after it', st.phase === 'stabilized', seq(st));
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
st = fold(mk(IM.concat([[80, 'norepinephrine_drip']])), 120);
chk('norepinephrine lifts the pressure and moves no phase', st.phase === 'persistent' && st.vitals.systolic_bp > 76, JSON.stringify(st.vitals));
chk('and is discouraged', st.discouragedTaken.has('norepinephrine_drip'));

section('prompts');
const all = CASE.case_actions.filter(a => a.prompt).map(a => a.prompt.text);
chk('no prompt quotes a number', all.every(t => !/\d/.test(t)), all.filter(t => /\d/.test(t)).join(' | '));
