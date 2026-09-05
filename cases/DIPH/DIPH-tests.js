/* Case assertions for DIPH (diphenhydramine overdose with sodium-channel blockade).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * Everything here names a specific drug, study or phase and belongs to the case pack.
 *
 * Three things in this case are exercised by no other pack, and most of what follows is
 * aimed at them:
 *
 *   1. An UNGUARDED time-guarded transition. The author's instruction is that a seizure
 *      occurs regardless of how well the case is being managed, which is authoring
 *      section 5.1's third pattern, a scheduled natural history. No pack used it before,
 *      and the Python scenario runner could not walk it until the same day this file was
 *      written, so the assertions below check it from both ends: it fires with nobody
 *      doing anything, and it fires just the same after a flawless four minutes.
 *
 *   2. A tag gated on `study S resulted` rather than on a flag. Physostigmine halts the
 *      case before the ECG has come back and does not halt it afterwards, so the
 *      difference between ordered and resulted is the difference between two endings.
 *
 *   3. Four oxygen-delivery actions sharing ONE vital-effect key, so that escalating a
 *      device replaces the previous one instead of stacking with it.
 */

section('intended path');
let st = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'fingerstick_blood_sugar'],
                  [4, 'ecg_12_lead'], [245, 'lorazepam_bolus'], [246, 'na_bicarbonate_bolus'],
                  [262, 'cooling_measures'], [263, 'consult_toxicology']]), 320);
chk('reaches the stabilised phase', st.phase === 'stabilized', st.phase);
chk('phase sequence is arrival, seizure, post-ictal, narrowing, stabilised',
    JSON.stringify(st.phaseSeq.map(p => p.id)) ===
    '["presentation","seizing","post_ictal","stabilizing","stabilized"]',
    JSON.stringify(st.phaseSeq.map(p => p.id)));
chk('no halt', !st.halted, st.halted && st.halted.id);
chk('no arrest', !st.failed);
chk('the arrest deterioration never fired',
    st.timeFires.filter(f => f.to === 'pulseless_vt').length === 0);

section('the seizure is a scheduled natural history and fires regardless');
const idle = fold(mk([]), 300);
chk('doing nothing at all reaches the seizure', idle.phase === 'seizing', idle.phase);
chk('and it fired on the clock rather than on an action',
    idle.timeFires.some(f => f.to === 'seizing' && f.after === 240),
    JSON.stringify(idle.timeFires.map(f => f.from + '->' + f.to + '@' + f.after)));
chk('nothing has happened before four minutes',
    fold(mk([]), 239).phase === 'presentation', fold(mk([]), 239).phase);
chk('it fires at 240 and not later',
    fold(mk([]), 240).phase === 'seizing', fold(mk([]), 240).phase);

/* The author's sentence, in the only form it still holds. Until 5 September 2026 this ran
   with bicarbonate in it and still seized, which was her stated intention. It now has an
   escape, so what is tested is the sentence minus the one drug that buys it. */
const perfect = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'fingerstick_blood_sugar'],
                         [4, 'ecg_12_lead'], [30, 'cooling_measures'],
                         [40, 'consult_toxicology'], [50, 'normal_saline_1l_bolus']]), 300);
chk('a flawless first four minutes without bicarbonate reaches the seizure just the same',
    perfect.phaseSeq.some(p => p.id === 'seizing'),
    JSON.stringify(perfect.phaseSeq.map(p => p.id)));

section('the escape from the seizure needs both drugs');
/* Added on 5 September 2026 and narrowed the same day. The guard is a conjunction because
   bicarbonate is not an anticonvulsant: it treats the conduction, and what prevents a
   drug-induced seizure is the benzodiazepine. See the author_rationale on the rule. */
const bothDrugs = [[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'lorazepam_bolus'],
                   [22, 'na_bicarbonate_bolus']];
const escaped = fold(mk(bothDrugs), 300);
chk('both drugs before four minutes leave the arrival phase',
    escaped.phase === 'stabilizing', escaped.phase);
chk('and the patient never convulses',
    !escaped.phaseSeq.some(p => p.id === 'seizing'),
    JSON.stringify(escaped.phaseSeq.map(p => p.id)));
chk('the guard is a conjunction of the two flags',
    (PHASE['presentation'].transitions.find(t => t.to === 'stabilizing') || {}).when ===
      'flag bicarb_given set AND flag benzo_given set',
    (PHASE['presentation'].transitions.find(t => t.to === 'stabilizing') || {}).when);
chk('bicarbonate alone does not escape',
    fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'na_bicarbonate_bolus']]), 300)
      .phase !== 'stabilizing');
chk('and the patient still convulses on the clock',
    fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'na_bicarbonate_bolus']]), 300)
      .phaseSeq.some(p => p.id === 'seizing'));
chk('a benzodiazepine alone does not escape either',
    fold(mk([[1, 'insert_iv'], [20, 'lorazepam_bolus']]), 300).phase !== 'stabilizing');
chk('the escape takes ten seconds, matching the other two bicarbonate transitions',
    fold(mk(bothDrugs), 27).phase === 'presentation' &&
    fold(mk(bothDrugs), 33).phase === 'stabilizing');
chk('all three bicarbonate transitions use the same ten seconds',
    CASE.phases.flatMap(p => p.transitions)
      .filter(t => t.to === 'stabilizing' && t.after_seconds !== undefined)
      .every(t => t.after_seconds === 10 && t.measured_from === 'guard_true'),
    JSON.stringify(CASE.phases.flatMap(p => p.transitions)
      .filter(t => t.to === 'stabilizing').map(t => t.after_seconds)));
/* The boundary is 230 seconds and not 240, because the escape has to mature. A resident who
   completes the pair during the last ten seconds seizes anyway, and then leaves the
   post-ictal phase on the flags they already set. */
chk('the pair completed at 225 seconds escapes',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [225, 'na_bicarbonate_bolus']]), 260)
      .phase === 'stabilizing',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [225, 'na_bicarbonate_bolus']]), 260).phase);
chk('completed at 235 seconds it does not, and the seizure fires first',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [235, 'na_bicarbonate_bolus']]), 260)
      .phaseSeq.some(p => p.id === 'seizing'));
chk('but neither flag is wasted: she is out of the seizure and narrowing shortly after',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [235, 'na_bicarbonate_bolus'],
             [255, 'urinalysis'], [270, 'magnesium_level']]), 300).phase === 'stabilizing',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [235, 'na_bicarbonate_bolus'],
             [255, 'urinalysis'], [270, 'magnesium_level']]), 300).phase);
chk('the stabilising phase now runs at 39.6 rather than 39.0',
    PHASE['stabilizing'].vitals.temperature_c === 39.6,
    String(PHASE['stabilizing'].vitals.temperature_c));
chk('and active cooling still takes 0.9 off it',
    Math.abs(fold(mk(bothDrugs.concat([[40, 'cooling_measures']])), 100).vitals.temperature_c
             - 38.7) < 0.001,
    String(fold(mk(bothDrugs.concat([[40, 'cooling_measures']])), 100).vitals.temperature_c));
chk('the narration on the escape is true of the numbers it introduces: the rate falls',
    PHASE['stabilizing'].vitals.heart_rate < PHASE['presentation'].vitals.heart_rate);
chk('physostigmine given just before the escape matures is absorbed by it, which is a gap',
    fold(mk(bothDrugs.concat([[24, 'physostigmine']])), 300).phase === 'stabilizing');

section('amiodarone into the wide-complex rhythm arrests her at once');
const amio = fold(mk([[1, 'insert_iv'], [370, 'amiodarone_bolus_infusion']]), 400);
chk('it reaches the arrest phase', amio.phase === 'pulseless_vt', amio.phase);
chk('instantaneously, not on a clock',
    !amio.timeFires.some(f => f.to === 'pulseless_vt'),
    JSON.stringify(amio.timeFires.map(f => f.to)));
chk('the run is recorded as failed rather than halted', !!amio.failed && !amio.halted);
chk('and the debrief will say it was ended by an action rather than by the clock',
    amio.failed.byClock === false, String(amio.failed.byClock));
chk('the clock route still reports itself as the clock',
    fold(mk([]), 600).failed.byClock === true);
chk('the arrest reason is true of both routes',
    /either because two minutes passed|or because an antiarrhythmic/.test(amio.failed.reason),
    amio.failed.reason);
chk('outside that rhythm amiodarone is discouraged and nothing happens',
    fold(mk([[1, 'insert_iv'], [2, 'amiodarone_bolus_infusion']]), 60).phase === 'presentation');
chk('and it is scored as discouraged rather than ignored',
    fold(mk([[1, 'insert_iv'], [2, 'amiodarone_bolus_infusion']]), 60)
      .discouragedTaken.has('amiodarone_bolus_infusion'));
chk('it beats the bicarbonate rescue when both are given together',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'],
             [371, 'amiodarone_bolus_infusion']]), 400).phase === 'pulseless_vt');
chk('the amiodarone rule is listed before the bicarbonate rescue in that phase',
    PHASE['wide_complex_tachycardia'].transitions
      .findIndex(t => t.when === 'flag amiodarone_given set') <
    PHASE['wide_complex_tachycardia'].transitions
      .findIndex(t => t.when === 'flag bicarb_given set'));
chk('the tag stays discouraged, because a harmful tag would halt before the rule is reached',
    A['amiodarone_bolus_infusion'].tag.every(r => r.value === 'discouraged'),
    JSON.stringify(A['amiodarone_bolus_infusion'].tag.map(r => r.value)));

section('the do-nothing trajectory ends in cardiac arrest');
const dead = fold(mk([]), 600);
chk('a resident who never touches anything watches the patient arrest',
    dead.phase === 'pulseless_vt', dead.phase);
chk('the run is recorded as failed rather than halted', !!dead.failed && !dead.halted);
chk('the arrest carries its own reason, not a harmful action reason',
    /no sodium bicarbonate given/.test(dead.failed.reason), dead.failed.reason);
chk('it is not the shared halted phase', dead.phase !== 'halted');
chk('three deteriorations fired on the way', dead.timeFires.length === 3,
    JSON.stringify(dead.timeFires.map(f => f.from + '->' + f.to)));
chk('every deterioration was announced by the nurse',
    dead.nurse.filter(n => n.kind === 'deterioration').length === dead.timeFires.length);
chk('bicarbonate was asked for before the arrest',
    dead.promptFires.some(p => p.id === 'na_bicarbonate_bolus'),
    JSON.stringify(dead.promptFires.map(p => p.id)));

section('each deterioration is cancelled by the action it names');
chk('a benzodiazepine cancels the seizure deterioration',
    fold(mk([[245, 'insert_iv'], [246, 'lorazepam_bolus']]), 420).phase !== 'wide_complex_tachycardia',
    fold(mk([[245, 'insert_iv'], [246, 'lorazepam_bolus']]), 420).phase);
chk('bicarbonate cancels the post-ictal deterioration',
    fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'], [250, 'na_bicarbonate_bolus']]), 500)
      .phase === 'stabilizing');
chk('bicarbonate given before the seizure cancels it in advance',
    !fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'], [245, 'lorazepam_bolus']]), 600)
      .timeFires.some(f => f.to === 'wide_complex_tachycardia'));
chk('bicarbonate rescues the wide-complex phase inside the window',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 420).phase === 'stabilizing',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 420).phase);
chk('and one second past the deadline it does not',
    fold(mk([[1, 'insert_iv'], [481, 'na_bicarbonate_bolus']]), 520).phase === 'pulseless_vt');

section('physostigmine: the difference between ordered and resulted is two endings');
const blind = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'physostigmine']]), 60);
chk('given with no ECG at all it halts the case', !!blind.halted && blind.phase === 'halted');
chk('the halt reason names the QRS', /132/.test(blind.halted.reason), blind.halted.reason);
const pending = fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [5, 'physostigmine']]), 60);
chk('ordered is not resulted: a tracing nobody has read still halts it',
    !!pending.halted, pending.phase);
chk('the ECG really was ordered at that moment', pending.ordered.has('ecg_12_lead'));
const seen = fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'physostigmine']]), 60);
chk('once the tracing has resulted it does not halt the case', !seen.halted, seen.phase);
chk('it produces the seizure instead', seen.phase === 'seizing', seen.phase);
chk('the seizure came from the physostigmine rule, ten seconds later',
    seen.timeFires.some(f => f.to === 'seizing' && f.after === 10),
    JSON.stringify(seen.timeFires.map(f => f.to + '@' + f.after)));
chk('and not from the four-minute rule, which had not come due',
    !seen.timeFires.some(f => f.after === 240));
chk('nothing has happened five seconds after the injection',
    fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'physostigmine']]), 25).phase ===
      'presentation');
chk('the flag is set either way', seen.flags.has('physostigmine_given'));
const rescued = fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'physostigmine'],
                         [35, 'lorazepam_bolus'], [36, 'na_bicarbonate_bolus']]), 120);
chk('the seizure it caused is escapable by the ordinary route',
    rescued.phase === 'stabilizing', rescued.phase);
chk('atropine is recommended only once physostigmine has been given',
    A['atropine_bolus'].tag[0].when === 'flag physostigmine_given set');

section('physostigmine is reachable rather than blocked, which is the point');
chk('it authors no case prerequisite of its own',
    !(A['physostigmine'].prerequisites || []).some(p => p.source === 'case'),
    JSON.stringify((A['physostigmine'].prerequisites || []).map(p => p.source)));
const noLine = fold(mk([[1, 'attach_monitor'], [2, 'physostigmine']]), 30);
chk('with no line it is blocked by the catalog default and does NOT halt',
    !noLine.halted && noLine.phase === 'presentation', noLine.phase);
chk('the blocked attempt is recorded', noLine.blocked.length === 1,
    JSON.stringify(noLine.blocked.map(b => b.id)));
chk('and it set no flag', !noLine.flags.has('physostigmine_given'));

section('the other three harmful actions');
chk('flumazenil halts', fold(mk([[1, 'insert_iv'], [2, 'flumazenil']]), 30).phase === 'halted');
chk('a further dose of diphenhydramine halts',
    fold(mk([[1, 'insert_iv'], [2, 'diphenhydramine']]), 30).phase === 'halted');
chk('procainamide in the wide-complex phase halts',
    fold(mk([[1, 'insert_iv'], [370, 'procainamide_drip']]), 400).phase === 'halted');
chk('procainamide before that phase does not halt, it is discouraged',
    fold(mk([[1, 'insert_iv'], [2, 'procainamide_drip']]), 30).phase === 'presentation');
chk('and it is recorded as discouraged rather than ignored',
    fold(mk([[1, 'insert_iv'], [2, 'procainamide_drip']]), 30).discouragedTaken
      .has('procainamide_drip'));
chk('every harmful action in this case carries a halt reason',
    HARMFUL.every(id => !!A[id].halt_reason), HARMFUL.join(', '));
chk('four actions can be harmful here', HARMFUL.length === 4, HARMFUL.join(', '));

section('the tracing changes with the state, and narrows after bicarbonate');
const ecgAt = s => (s.orders.ecg_12_lead || []).slice(-1)[0].value.report;
const arrivalEcg = ecgAt(fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead']]), 40));
chk('the arrival tracing reports a QRS of 132 ms', /QRS duration 132 ms/.test(arrivalEcg),
    arrivalEcg);
chk('and a 5 mm terminal R wave in aVR', /Terminal R wave in lead aVR of 5 mm/.test(arrivalEcg));
chk('it reports findings and not the conclusion',
    !/sodium.channel|blockade|toxic/i.test(arrivalEcg), arrivalEcg);
const laterEcg = ecgAt(fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'],
                                [250, 'na_bicarbonate_bolus'], [275, 'ecg_12_lead']]), 300));
chk('after bicarbonate the QRS reads 104 ms', /QRS duration 104 ms/.test(laterEcg), laterEcg);
chk('and the aVR R wave has come down to 2 mm', /aVR now 2 mm/.test(laterEcg));
const vtEcg = ecgAt(fold(mk([[1, 'insert_iv'], [370, 'ecg_12_lead']]), 400));
chk('in the wide-complex phase it reads a wide-complex tachycardia',
    /wide-complex tachycardia/.test(vtEcg) && /180 ms/.test(vtEcg), vtEcg);

section('the panels move in the directions the treatment moves them');
const get = (cs, label) => (cs.find(c => c.label === label) || {}).value;
const chemBefore = fold(mk([[1, 'insert_iv'], [2, 'basic_chemistry_chem_7']]), 30)
  .orders.basic_chemistry_chem_7[0].value.components;
chk('the pre-treatment bicarbonate is 13, not the source document 34',
    get(chemBefore, 'Bicarbonate') === '13', get(chemBefore, 'Bicarbonate'));
chk('sodium 135 and chloride 109 give an anion gap of 13',
    Number(get(chemBefore, 'Sodium')) - Number(get(chemBefore, 'Chloride')) -
    Number(get(chemBefore, 'Bicarbonate')) === 13);
const chemAfter = fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'],
                           [10, 'basic_chemistry_chem_7']]), 40)
  .orders.basic_chemistry_chem_7[0].value.components;
chk('after bicarbonate the sodium has risen', Number(get(chemAfter, 'Sodium')) > 135);
chk('and the potassium has fallen below the interval',
    Number(get(chemAfter, 'Potassium')) < 3.5 &&
    chemAfter.find(c => c.label === 'Potassium').abnormal);
const gas = fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'],
                     [10, 'arterial_blood_gas']]), 40).orders.arterial_blood_gas[0].value;
chk('the treated gas lands in the 7.50 to 7.55 window the note describes',
    Number(get(gas.components, 'pH')) >= 7.50 && Number(get(gas.components, 'pH')) <= 7.55,
    get(gas.components, 'pH'));

section('the urine screen is positive for tricyclics, and it is a false positive');
const tox = fold(mk([[1, 'urine_tox_screen']]), 20).orders.urine_tox_screen[0].value;
chk('it reads positive', get(tox.components, 'Tricyclic antidepressants') === 'POSITIVE');
chk('the false positive is taught in the debrief note, not printed under the result',
    !/false/i.test(tox.comment || '') && /false positive/i.test(A['urine_tox_screen'].debrief_note),
    tox.comment);

section('the monitor is dark until somebody attaches one');
chk('no monitoring without the act', !fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead']]), 20).monitoring);
chk('attaching it is enough',
    (fold(mk([[1, 'attach_monitor']]), 20).monitoring || {}).id === 'attach_monitor');

section('active cooling moves the temperature and nothing else does');
const tAt = (log, t) => fold(log, t).vitals.temperature_c;
const coolLog = mk([[1, 'cooling_measures']]);
chk('the arrival baseline is the UNCOOLED 40.1', tAt(mk([[1, 'insert_iv']]), 20) === 40.1,
    String(tAt(mk([[1, 'insert_iv']]), 20)));
chk('nothing has moved at 20 seconds: the effect has a 30-second onset',
    tAt(coolLog, 20) === 40.1, String(tAt(coolLog, 20)));
chk('at 40 seconds the temperature has come down 0.9',
    Math.abs(tAt(coolLog, 40) - 39.2) < 0.001, String(tAt(coolLog, 40)));
chk('and it does not keep falling inside the phase',
    Math.abs(tAt(coolLog, 200) - 39.2) < 0.001, String(tAt(coolLog, 200)));
chk('after the seizure it tracks the new phase baseline, still 0.9 below it',
    Math.abs(tAt(coolLog, 300) - 39.5) < 0.001, String(tAt(coolLog, 300)));
chk('paracetamol moves nothing at all',
    fold(mk([[1, 'insert_iv'], [2, 'acetaminophen']]), 60).vitals.temperature_c === 40.1);
chk('and paracetamol is scored as discouraged',
    fold(mk([[1, 'insert_iv'], [2, 'acetaminophen']]), 60).discouragedTaken.has('acetaminophen'));

section('the four oxygen devices share one effect key and do not stack');
const satIn = (extra, t) => fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus']].concat(extra)), t)
  .vitals.oxygen_saturation;
chk('the post-ictal baseline is the UNSUPPORTED 92', satIn([], 260) === 92, String(satIn([], 260)));
chk('a cannula adds two', satIn([[250, 'nasal_cannula_oxygen']], 260) === 94,
    String(satIn([[250, 'nasal_cannula_oxygen']], 260)));
chk('a non-rebreather adds five', satIn([[250, 'non_rebreather_mask']], 260) === 97,
    String(satIn([[250, 'non_rebreather_mask']], 260)));
chk('cannula then mask reads the mask, not the sum',
    satIn([[250, 'nasal_cannula_oxygen'], [251, 'non_rebreather_mask']], 260) === 97,
    String(satIn([[250, 'nasal_cannula_oxygen'], [251, 'non_rebreather_mask']], 260)));
chk('and none of them touches the arrival saturation, which is already 98 on room air',
    fold(mk([[1, 'non_rebreather_mask']]), 30).vitals.oxygen_saturation === 98,
    String(fold(mk([[1, 'non_rebreather_mask']]), 30).vitals.oxygen_saturation));
chk('a mask on an intubated patient does nothing, because the tube is what is oxygenating her',
    fold(mk([[1, 'insert_iv'], [2, 'etomidate_bolus'], [3, 'rocuronium_bolus'],
             [4, 'intubate_rapid_sequence'], [245, 'lorazepam_bolus'],
             [250, 'non_rebreather_mask']]), 260).vitals.oxygen_saturation ===
    fold(mk([[1, 'insert_iv'], [2, 'etomidate_bolus'], [3, 'rocuronium_bolus'],
             [4, 'intubate_rapid_sequence'], [245, 'lorazepam_bolus']]), 260)
      .vitals.oxygen_saturation);

section('the second dose is the one that counts');
const one = fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus']]), 200);
const two = fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'],
                     [30, 'na_bicarbonate_bolus']]), 200);
chk('one bolus sets the treatment flag', one.flags.has('bicarb_given'));
chk('one bolus does not set the titration flag', !one.flags.has('bicarb_titrated'));
chk('two boluses do', two.flags.has('bicarb_titrated'));
chk('one tracing does not set the repeat flag',
    !fold(mk([[1, 'ecg_12_lead']]), 40).flags.has('ecg_repeated'));
chk('two tracings do',
    fold(mk([[1, 'ecg_12_lead'], [30, 'ecg_12_lead']]), 60).flags.has('ecg_repeated'));
chk('the nurse says the delay out loud when the drug goes in',
    one.nurse.some(n => /minute or two/.test(n.text || '')),
    JSON.stringify(one.nurse.map(n => n.kind)));

section('the bicarbonate obligations open and close');
chk('one bolus leaves the reassessment obligation open',
    one.fuOutstanding.has('bicarbonate_reassessment'), [...one.fuOutstanding].join(', '));
chk('a second bolus discharges it', !two.fuOutstanding.has('bicarbonate_reassessment'));
chk('so does starting an infusion',
    !fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'],
              [30, 'na_bicarbonate_infusion']]), 90).fuOutstanding.has('bicarbonate_reassessment'));
chk('a repeat tracing discharges the repeat-ECG obligation',
    !fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'na_bicarbonate_bolus'],
              [40, 'ecg_12_lead']]), 200).fuOutstanding.has('repeat_ecg_after_bicarbonate'));

section('a covered sibling reaches the same place as the action covering it');
chk('midazolam terminates the seizure through the lorazepam coverage',
    fold(mk([[1, 'insert_iv'], [245, 'midazolam_bolus']]), 300).flags.has('benzo_given'));
chk('and it moves the phase',
    fold(mk([[1, 'insert_iv'], [245, 'midazolam_bolus']]), 300).phase === 'post_ictal');
chk('the bicarbonate infusion alone satisfies the treatment flag',
    fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_infusion']]), 30).flags.has('bicarb_given'));
chk('Ringer\'s carries the crystalloid tag through the equivalence group',
    fold(mk([[1, 'insert_iv'], [2, 'lactated_ringer_s_1l_bolus']]), 30).flags.has('fluids_given'));
chk('vancomycin carries the antibiotic flag through the ceftriaxone coverage',
    fold(mk([[1, 'insert_iv'], [2, 'vancomycin']]), 30).flags.has('abx_given'));
chk('magnesium through the bolus entry sets the same flag',
    fold(mk([[1, 'insert_iv'], [2, 'magnesium_sulfate_bolus']]), 30).flags.has('magnesium_given'));

section('the empirical sepsis road is right at time zero and wrong afterwards');
chk('antibiotics on arrival are not discouraged',
    !fold(mk([[1, 'insert_iv'], [2, 'ceftriaxone']]), 30).discouragedTaken.has('ceftriaxone'));
chk('after the toxicology screen has resulted they are',
    fold(mk([[1, 'insert_iv'], [2, 'urine_tox_screen'], [20, 'ceftriaxone']]), 40)
      .discouragedTaken.has('ceftriaxone'));
chk('the same switch applies to the lumbar puncture',
    fold(mk([[1, 'insert_iv'], [2, 'urine_tox_screen'], [20, 'lumbar_puncture']]), 40)
      .discouragedTaken.has('lumbar_puncture'));

section('charcoal turns on the airway rather than on the drug');
chk('discouraged in an unprotected airway',
    fold(mk([[1, 'insert_iv'], [2, 'activated_charcoal']]), 30)
      .discouragedTaken.has('activated_charcoal'));
const tubed = fold(mk([[1, 'insert_iv'], [2, 'etomidate_bolus'], [3, 'rocuronium_bolus'],
                       [4, 'intubate_rapid_sequence'], [5, 'activated_charcoal']]), 40);
chk('intubation actually proceeds once she is sedated and paralysed',
    !tubed.blocked.length && tubed.flags.has('airway_protected'),
    JSON.stringify(tubed.blocked.map(b => b.id)));
chk('and charcoal is no longer discouraged',
    !tubed.discouragedTaken.has('activated_charcoal'));

section('the rescue therapies are ordered behind bicarbonate');
chk('lidocaine before bicarbonate in the wide-complex phase is discouraged',
    fold(mk([[1, 'insert_iv'], [370, 'lidocaine_bolus']]), 400)
      .discouragedTaken.has('lidocaine_bolus'));
chk('and after bicarbonate it is not',
    !fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [372, 'lidocaine_bolus']]), 400)
      .discouragedTaken.has('lidocaine_bolus'));
chk('lipid emulsion is ordered the same way',
    fold(mk([[1, 'insert_iv'], [370, 'intralipid']]), 400).discouragedTaken.has('intralipid') &&
    !fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [372, 'intralipid']]), 400)
      .discouragedTaken.has('intralipid'));

section('the handoff completes from anywhere');
[['arrival', mk([[1, 'attach_monitor'], [2, 'handoff_submit']])],
 ['the seizure', mk([[1, 'attach_monitor'], [245, 'handoff_submit']])],
 ['the wide-complex phase', mk([[1, 'attach_monitor'], [370, 'handoff_submit']])]
].forEach(pair => {
  const h = fold(pair[1], 500);
  chk('a handoff from ' + pair[0] + ' completes the case', h.phase === 'case_complete', h.phase);
});
chk('the handoff rule is first in every non-terminal phase transition list',
    CASE.phases.filter(p => !p.terminal)
      .every(p => p.transitions[0].when === 'action handoff_submit taken'),
    CASE.phases.filter(p => !p.terminal && p.transitions[0].when !== 'action handoff_submit taken')
      .map(p => p.id).join(', '));

section('the disposition and diagnosis lists');
chk('the correct disposition is critical care',
    CASE.handoff.correct_disposition.level_of_care === 'critical_care');
chk('the psychiatric unit is an authored wrong answer with an explanation',
    CASE.handoff.alternative_dispositions.some(
      d => d.id === 'psychiatric_unit' && d.verdict === 'incorrect' && d.explanation.length > 200));
chk('a tricyclic overdose is defensible rather than wrong',
    CASE.handoff.alternative_diagnoses.some(
      d => d.catalog_id === 'dx_tricyclic_antidepressant_overdose' &&
           d.verdict === 'acceptable_with_qualification'));
chk('the primary diagnosis names the agent rather than the syndrome',
    CASE.handoff.correct_diagnosis.catalog_id === 'dx_diphenhydramine_overdose',
    CASE.handoff.correct_diagnosis.catalog_id);
chk('five additional diagnoses are authored, each with an explanation',
    CASE.handoff.additional_diagnoses.length === 5 &&
    CASE.handoff.additional_diagnoses.every(d => (d.explanation || '').length > 100),
    String(CASE.handoff.additional_diagnoses.length));
chk('the cardiotoxicity is the first of them, because it is the thing that decides management',
    CASE.handoff.additional_diagnoses[0].catalog_id ===
      'dx_sodium_channel_blocker_cardiotoxicity',
    CASE.handoff.additional_diagnoses[0].catalog_id);
chk('the deliberate nature of the ingestion is named in the handover',
    CASE.handoff.additional_diagnoses.some(d => d.catalog_id === 'dx_suicide_attempt'));
/* The whole case in one assertion. Naming the toxidrome is right and incomplete, so it has
   to be scored twice: credit when it is listed beside the agent, and a defensible verdict
   when it is offered as the primary instead. Authoring 12.1 allows exactly this, and
   before the catalog gained an id for the agent the case could not express it, because the
   toxidrome WAS the correct answer. */
chk('the toxidrome earns credit as an additional diagnosis',
    CASE.handoff.additional_diagnoses.some(d => d.catalog_id === 'dx_anticholinergic_toxidrome'));
chk('and is defensible rather than wrong when offered as the primary',
    CASE.handoff.alternative_diagnoses.some(
      d => d.catalog_id === 'dx_anticholinergic_toxidrome' &&
           d.verdict === 'acceptable_with_qualification'));
chk('no additional diagnosis repeats the primary',
    !CASE.handoff.additional_diagnoses.some(
      d => d.catalog_id === CASE.handoff.correct_diagnosis.catalog_id));
chk('every diagnosis this case names resolves to a real catalog entry',
    [CASE.handoff.correct_diagnosis, ...CASE.handoff.additional_diagnoses,
     ...CASE.handoff.alternative_diagnoses]
      .every(d => SHARED.diagnoses.some(x => x.id === d.catalog_id)),
    [CASE.handoff.correct_diagnosis, ...CASE.handoff.additional_diagnoses,
     ...CASE.handoff.alternative_diagnoses]
      .filter(d => !SHARED.diagnoses.some(x => x.id === d.catalog_id))
      .map(d => d.catalog_id).join(', '));

section('the interview is answered by the mother and withdrawn where she is not there');
const gr = CASE.interview.global_answer_rules;
chk('one global rule', gr.length === 1);
chk('every phase at alertness 2 or above is named in it',
    CASE.phases.filter(p => p.appearance.alertness_level >= 2)
      .every(p => gr[0].when.indexOf(p.id) >= 0),
    CASE.phases.filter(p => p.appearance.alertness_level >= 2 && gr[0].when.indexOf(p.id) < 0)
      .map(p => p.id).join(', '));
chk('the bottle disclosure is an authored topic and names Benadryl',
    /Benadryl/.test(JSON.stringify(
      CASE.interview.topics.find(t => t.topic === 'bottle_or_pills_found').answer)));
chk('no interview answer names a diagnosis',
    !/anticholinergic|toxidrome|sodium.channel/i.test(
      JSON.stringify(CASE.interview.topics.map(t => t.answer))));
chk('the disclosure also reaches a resident who never asks, through the nurse',
    /Benadryl/.test(JSON.stringify(A['consult_toxicology'].prompt)));
chk('every topic carries an echo phrase for the clarifying question',
    CASE.interview.topics.every(t => !!t.echo),
    CASE.interview.topics.filter(t => !t.echo).map(t => t.topic).join(', '));
