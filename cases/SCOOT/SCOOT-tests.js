/* Case assertions for SCOOT (epidural hematoma with deterioration).
 *
 * Three clocks: the decline at 240 s whatever is done, herniation 300 s after the decline
 * unless neurosurgery has been called, and brainstem compression 300 s after herniation
 * unless osmotherapy is given there. Times are fractional on purpose.
 */
const seq = st => st.phaseSeq.map(p => p.id).join(' > ');
const said = (st, re) => st.nurse.some(n => re.test(n.text));
const F = (log, t, dm) => fold(mk(log), t, dm);
const last = (st, key) => {
  const o = (st.orders[key] || []).filter(r => r.value).pop();
  return o ? { body: o.value } : st.readouts.filter(r => r.key === key).pop();
};
const enteredAt = (st, id) => (st.phaseSeq.find(p => p.id === id) || {}).t;
const LINE = [[1.3, 'attach_monitor'], [2.1, 'insert_iv']];
const WORK = LINE.concat([[3.4, 'exam_neuro'], [5.2, 'ct_head']]);   // CT back at 15.2
const CALLED = WORK.concat([[20.5, 'consult_neurosurgeon']]);
const RSI = t => [[t, 'etomidate_bolus'], [t + 0.5, 'rocuronium_bolus'], [t + 1, 'intubate_rapid_sequence']];
// Into herniation with nothing called: the workup is done, the call never made.
const HERNIATE = WORK;   // decline at 240, herniation at 540

section('intended path');
let st = F(CALLED.concat([[245.5, 'exam_neuro'], [250.5, 'consult_neurosurgeon'], [255.5, 'ondansetron'],
  [260.5, 'complete_blood_count_cbc'], [261.5, 'coagulation_panel'], [262.5, 'blood_type_and_screen'],
  [263.5, 'c_collar'], [264.5, 'ct_c_spine'], [270.5, 'handoff_submit']]), 275);
chk('reaches case_complete through the decline', seq(st) === 'presentation > decline > case_complete', seq(st));
chk('every critical action expected on the path was done',
  [...st.expected].every(id => st.satisfied.has(id)), [...st.expected].filter(id => !st.satisfied.has(id)).join());
chk('the repeat exam and the call back were both expected and both credited',
  st.expected.has('neuro_reexamined') && st.satisfied.has('neuro_reexamined') &&
  st.expected.has('neurosurgery_updated') && st.satisfied.has('neurosurgery_updated'));
chk('no herniation, nothing discouraged', !st.phaseSeq.some(p => p.id === 'herniation') && st.discouragedTaken.size === 0,
  [...st.discouragedTaken].join());

section('the decline is natural history');
for (const log of [[], WORK, CALLED, CALLED.concat([[30.5, 'mannitol_bolus']])]) {
  st = F(log, 239.9);
  chk('still on arrival at 239.9 s (' + log.length + ' actions)', st.phase === 'presentation', st.phase);
  st = F(log, 240.1);
  chk('drowsy at 240.1 s (' + log.length + ' actions)', st.phase === 'decline' && Math.abs(enteredAt(st, 'decline') - 240) < 1e-6, seq(st));
}
st = F(WORK, 241);
chk('the nurse says he vomited and is hard to wake', said(st, /He just vomited, and he's hard to keep awake now/));
chk('the monitor barely moves: 138 to 145, 88 to 96', st.vitals.systolic_bp === 145 && st.vitals.heart_rate === 96);
chk('the exam shows it: GCS 12', /GCS 12 \(E3 V4 M5\)/.test(last(F(WORK.concat([[242.5, 'exam_neuro']]), 243), 'exam_neuro').body.findings));
chk('and the pupils are still equal', /equal and reactive/.test(last(F(WORK.concat([[242.5, 'exam_neuro']]), 243), 'exam_neuro').body.findings));

section('neurosurgery needs the scan');
st = F(LINE.concat([[3.5, 'consult_neurosurgeon']]), 5);
chk('before any CT the call is blocked', st.blocked.some(b => b.id === 'consult_neurosurgeon') && !st.flags.has('neurosurgery_called'));
chk('with the neurosurgeon\'s request as the message', /Neurosurgery will want to see his head CT first/.test(st.blocked[0].message), st.blocked[0].message);
st = F(LINE.concat([[3.5, 'ct_head'], [8.5, 'consult_neurosurgeon']]), 10);
chk('with the CT pending it is still blocked', st.blocked.some(b => b.id === 'consult_neurosurgeon'));
st = F(CALLED, 21);
chk('with the CT back it goes through', !st.blocked.length && st.flags.has('neurosurgery_called') && st.satisfied.has('consult_neurosurgeon'));
chk('a CT/CTA counts as the scan', F(LINE.concat([[3.5, 'ct_cta_head_and_neck'], [20.5, 'consult_neurosurgeon']]), 21).flags.has('neurosurgery_called'));
chk('an MRI does not', F(LINE.concat([[3.5, 'mri_mra_head_and_neck'], [20.5, 'consult_neurosurgeon']]), 21).blocked.length === 1);
chk('the arrival call is not the call back', !F(CALLED, 21).satisfied.has('neurosurgery_updated') && !F(CALLED, 21).expected.has('neurosurgery_updated'));
chk('the neurosurgeon books the OR at GCS 15 and asks to hear if he gets drowsy',
  /booking the OR\. Call me straight away if he gets drowsy/.test(last(F(CALLED, 21), 'consult_neurosurgeon').body));
chk('and in the decline knows his GCS is falling',
  /A big collection with shift, and now his GCS is falling/.test(last(F(CALLED.concat([[250.5, 'consult_neurosurgeon']]), 251), 'consult_neurosurgeon').body));

section('herniation is a deterioration on inaction');
st = F(HERNIATE, 539.9);
chk('in the decline at 539.9 s', st.phase === 'decline');
st = F(HERNIATE, 540.1);
chk('herniated at 540.1 s', st.phase === 'herniation' && Math.abs(enteredAt(st, 'herniation') - 540) < 1e-6, seq(st));
chk('the nurse says the right pupil is big', said(st, /His right pupil has gone big/));
chk('Cushing: 178 over 94, pulse 56', st.vitals.systolic_bp === 178 && st.vitals.heart_rate === 56);
st = F(LINE, 541);
chk('no CT ever ordered: herniated too', st.phase === 'herniation');
st = F(CALLED, 900);
chk('called with the scan on arrival: never herniates', st.phase === 'decline' && !st.phaseSeq.some(p => p.id === 'herniation'), seq(st));
st = F(WORK.concat([[539.5, 'consult_neurosurgeon']]), 600);
chk('called in the decline half a second before: never herniates', st.phase === 'decline', seq(st));
st = F(WORK.concat([[540, 'consult_neurosurgeon']]), 600);
chk('called at the deadline itself: the call is applied first', st.phase === 'decline', seq(st));
st = F(WORK.concat([[540.5, 'consult_neurosurgeon']]), 600);
chk('called half a second after: herniated', st.phaseSeq.some(p => p.id === 'herniation'), seq(st));
st = F(LINE.concat([[250.5, 'ct_head'], [261.5, 'consult_neurosurgeon']]), 900);
chk('the scan ordered only after the decline, then the call: no herniation', st.phase === 'decline', seq(st));

section('the rescue in herniation, and the terminal clock');
st = F(HERNIATE.concat([[545.5, 'mannitol_bolus']]), 561);
chk('mannitol in herniation: temporized 15 s later', seq(st).endsWith('herniation > temporized') && Math.abs(enteredAt(st, 'temporized') - 560.5) < 1e-6, seq(st));
chk('the nurse says the pupil is reacting again', said(st, /His right pupil is a little smaller/));
st = F(HERNIATE.concat([[545.5, 'hypertonic_saline_3_infusion']]), 561);
chk('3 percent saline does the same', st.phase === 'temporized');
st = F(HERNIATE.concat([[545.5, 'hypertonic_saline_25_bolus']]), 600);
chk('concentrated saline without a central line is blocked', st.blocked.some(b => b.id === 'hypertonic_saline_25_bolus') && st.phase === 'herniation');
st = F(HERNIATE.concat([[541.5, 'central_venous_catheter_triple_lumen'], [545.5, 'hypertonic_saline_25_bolus']]), 561);
chk('and goes in through one', st.phase === 'temporized');
st = F(WORK.concat([[300.5, 'mannitol_bolus']]), 600);
chk('mannitol in the decline does not count for the herniation that follows', st.phase === 'herniation' && !st.satisfied.has('osmotherapy_for_herniation'), seq(st));
chk('mannitol in the decline is accepted, not discouraged', !st.discouragedTaken.has('mannitol_bolus'));
st = F(HERNIATE, 839.9);
chk('untreated: still herniating at 839.9 s', st.phase === 'herniation');
st = F(HERNIATE, 845.5);
chk('brainstem compression at 840 s, and the run fails', st.phase === 'brainstem_compression' && st.failed, seq(st));
chk('the nurse says both pupils are big', said(st, /Both pupils are big now/));
chk('the eye view: both 6 mm and fixed in brainstem compression',
  JSON.stringify(pupilState(st).value) === JSON.stringify({ state: 'dilated_fixed', size_mm: 6 }), JSON.stringify(pupilState(st)));
st = F(HERNIATE.concat([[839.5, 'mannitol_bolus']]), 860);
chk('osmotherapy half a second before the deadline: temporized', st.phase === 'temporized', seq(st));
st = F(HERNIATE.concat([[840, 'mannitol_bolus']]), 860);
chk('at the deadline itself: the order is applied first', st.phase === 'temporized', seq(st));
st = F(HERNIATE.concat([[840.5, 'mannitol_bolus']]), 860);
chk('half a second after: too late', st.phase === 'brainstem_compression', seq(st));
st = F(HERNIATE.concat([[545.5, 'mannitol_bolus']]), 1500);
chk('temporized has no clock', st.phase === 'temporized');

section('intubate for a reason');
const tubeTag = st => tagOf('intubate_rapid_sequence', st);
chk('discouraged on arrival', tubeTag(F(LINE, 10)) === 'discouraged');
chk('discouraged in the decline', tubeTag(F(LINE, 250)) === 'discouraged');
chk('critical in herniation', tubeTag(F(LINE, 545)) === 'critical');
chk('critical in temporized', tubeTag(F(LINE.concat([[545.5, 'mannitol_bolus']]), 570)) === 'critical');
st = F(WORK.concat(RSI(30.5)), 40);
chk('the tube goes in on arrival', st.flags.has('intubated') && st.discouragedTaken.has('intubate_rapid_sequence'));
st = F(WORK.concat(RSI(30.5), [[35.5, 'exam_neuro']]), 36);
chk('and then the neuro exam cannot be assessed', /GCS cannot be assessed/.test(last(st, 'exam_neuro').body.findings));
chk('nor the history', /intubated and sedated/.test(F(WORK.concat(RSI(30.5), [{ t: 36.5, kind: 'interview', topic: 'headache', q: '?' }]), 37).readouts.pop().body));
st = F(WORK.concat(RSI(30.5)), 241);
chk('the decline still comes, with the intubated narration', st.phase === 'decline' && said(st, /He's sedated on the ventilator/) && !said(st, /He just vomited/));
st = F(WORK.concat(RSI(30.5)), 545);
chk('the tube does not stop herniation without the call', st.phase === 'herniation');
chk('and in herniation the pupils still show it', /Right pupil 6 mm and fixed/.test(last(F(WORK.concat(RSI(30.5), [[545.5, 'exam_neuro']]), 546), 'exam_neuro').body.findings));
st = F(WORK.concat(RSI(30.5)), 600);
chk('an early tube already counts in herniation, and does not prompt again',
  st.satisfied.has('intubate_rapid_sequence') && !st.promptFires.some(p => p.id === 'intubate_rapid_sequence' && p.t > 540));

section('the sedation follow-up');
st = F(WORK.concat([[10.5, 'fentanyl_bolus']], RSI(30.5)), 100);
chk('fentanyl for the headache before the tube does not discharge it', st.fuOutstanding.has('sedation_after_intubation') || said(st, /He's tubed. What do you want running/));
for (const d of ['propofol_infusion', 'ketamine_infusion', 'fentanyl_bolus', 'midazolam_bolus', 'morphine_bolus']) {
  st = F(WORK.concat(RSI(30.5), [[40.5, d]]), 100);
  chk(d + ' after the tube discharges it', st.satisfied.has('post_intubation_sedation') && !said(st, /He's tubed. What do you want running/));
}

section('the trend: re-examine and call back');
st = F(CALLED.concat([[30.5, 'exam_neuro']]), 260);
chk('an exam on arrival does not count as the repeat', st.expected.has('neuro_reexamined') && !st.satisfied.has('neuro_reexamined'));
chk('the nurse says he is harder to wake at 15 s', st.promptFires.some(p => p.id === 'neuro_reexamined' && Math.abs(p.t - 255) < 1e-6));
chk('the call back is prompted at 40 s when neurosurgery already has the scan',
  F(CALLED, 281).promptFires.some(p => p.id === 'neurosurgery_updated') && said(F(CALLED, 281), /Neurosurgery hasn't heard that he's changed/));
chk('not before', !F(CALLED, 279).promptFires.some(p => p.id === 'neurosurgery_updated'));
st = F(WORK, 320);
chk('with no call yet, the call back prompt does not fire (its guard needs a first call)', !st.promptFires.some(p => p.id === 'neurosurgery_updated'));
chk('the first call made in the decline credits both', (st = F(WORK.concat([[250.5, 'consult_neurosurgeon']]), 260)) &&
  st.satisfied.has('consult_neurosurgeon') && st.satisfied.has('neurosurgery_updated'));

section('the warnings come first, in both modes');
st = F(WORK, 560);
chk('easy: the neurosurgery prompt at 70 s into the decline, escalation at 90',
  st.promptFires.some(p => p.id === 'consult_neurosurgeon' && Math.abs(p.t - 310) < 1e-6) &&
  st.promptFires.some(p => p.id === 'consult_neurosurgeon' && p.level === 2 && Math.abs(p.t - 330) < 1e-6),
  st.promptFires.map(p => p.id + '@' + p.t).join());
st = F(WORK, 560, 3);
chk('default: the neurosurgery prompt at 210 and escalation at 270, both before herniation at 300',
  st.promptFires.some(p => p.id === 'consult_neurosurgeon' && Math.abs(p.t - 450) < 1e-6) &&
  st.promptFires.some(p => p.id === 'consult_neurosurgeon' && p.level === 2 && Math.abs(p.t - 510) < 1e-6) &&
  st.phase === 'herniation', st.promptFires.map(p => p.id + '@' + p.t).join());
st = F(LINE, 560, 3);
chk('default, no CT ever: the CT prompt in the decline at 150 s, before the neurosurgery prompt',
  st.promptFires.some(p => p.id === 'ct_head' && Math.abs(p.t - 390) < 1e-6));
st = F(HERNIATE, 860, 3);
chk('default: the osmotherapy prompt at 60 and escalation at 180, before the terminal at 300',
  st.promptFires.some(p => p.id === 'osmotherapy_for_herniation' && Math.abs(p.t - 600) < 1e-6) &&
  st.promptFires.some(p => p.id === 'osmotherapy_for_herniation' && p.level === 2 && Math.abs(p.t - 720) < 1e-6),
  st.promptFires.map(p => p.id + '@' + p.t).join());
st = F([], 120);
chk('on arrival with nothing done: monitor, neuro exam, CT, in that order, and no neurosurgery prompt',
  st.promptFires.map(p => p.id).join() === 'attach_monitor,exam_neuro,ct_head', st.promptFires.map(p => p.id).join());
st = F(WORK, 120);
chk('on arrival with the CT back, the neurosurgery prompt at 70 s', st.promptFires.some(p => p.id === 'consult_neurosurgeon' && Math.abs(p.t - 70) < 1e-6));
chk('the do-nothing path ends in brainstem compression in the default mode too', seq(F([], 900, 3)) === 'presentation > decline > herniation > brainstem_compression');

section('what not to fix');
chk('lowering his pressure is discouraged in herniation', tagOf('labetalol_bolus', F(LINE, 545)) === 'discouraged');
st = F(HERNIATE.concat([[545.5, 'nicardipine_drip']]), 546);
chk('a nicardipine drip is the same act', st.discouragedTaken.has('labetalol_bolus') || st.discouragedTaken.has('nicardipine_drip'), [...st.discouragedTaken].join());
chk('atropine is discouraged in herniation, neutral on arrival', tagOf('atropine_bolus', F(LINE, 545)) === 'discouraged' && tagOf('atropine_bolus', F(LINE, 10)) === 'neutral');
chk('osmotherapy is discouraged at GCS 15 and neutral after', tagOf('mannitol_bolus', F(LINE, 10)) === 'discouraged' && tagOf('mannitol_bolus', F(LINE, 250)) === 'neutral');

section('results and the chart');
const ct = (log, t) => last(F(log, t), 'ct_head').body;
let cb = ct(WORK, 20);
chk('the head CT is the image stack: a still, a series and a caption, and no report text',
  cb.kind === 'image' && cb.image === 'scoot-ct-head' && cb.series === 'scoot-ct-head' && /^CT head without contrast/.test(cb.caption) && !cb.report);
chk('the series and its still are in the build', !!(PROTO.series || {})['scoot-ct-head'] && !!(PROTO.media || {})['scoot-ct-head']);
const SM = (PROTO.series || {})['scoot-ct-head'] || {};
chk('31 images of 389 by 486, 5 mm, starting in the middle of the stack',
  SM.n === 31 && SM.w === 389 && SM.h === 486 && SM.thickness_mm === 5 && SM.start_image === 16 && SM.z_mm.length === 31);
chk('brain window first, then subdural, bone and stroke', SM.windows.map(w => w.name).join() === 'Brain,Subdural,Bone,Stroke');
chk('the Colin27 notice travels with the images', /Colin27/.test(SM.notice) && /Louis Collins/.test(SM.notice));
chk('the read is kept for the debrief and names no diagnosis', /about 50 mL/.test(cb.comment) && /about 6 mm/.test(cb.comment) && !/epidural|subdural hematoma/i.test(cb.comment));
chk('a scan sent in herniation is the same series', ct(HERNIATE.concat([[541.5, 'ct_head']]), 553).series === 'scoot-ct-head');
const cta = last(F(LINE.concat([[3.5, 'ct_cta_head_and_neck']]), 20), 'ct_cta_head_and_neck').body;
chk('the CT/CTA stays a report with the same findings', cta.kind === 'report' && /about 50 mL/.test(cta.report) && /No arterial injury/.test(cta.report));
chk('no imaging text a learner reads names the diagnosis', !/epidural|subdural hematoma|\bEDH\b/i.test(
  JSON.stringify(CASE.content_keys.imaging, (k, v) => (k === 'verify' || k === 'authoring_note') ? undefined : v)));
chk('no consultant line names the diagnosis', !/epidural|subdural/i.test(JSON.stringify(CASE.content_keys.consultants)));
chk('every consultant line is 40 words or fewer',
  Object.values(CASE.content_keys.consultants).filter(Array.isArray).flat().every(r => r.value.split(/\s+/).length <= 40));

section('the twelve-lead follows the monitor');
const ecgAt = (log, t) => last(F(log.concat([[t, 'ecg_12_lead']]), t + 6), 'ecg_12_lead').body;
for (const [t, rate, stem] of [[10.5, 88, 'arrival'], [250.5, 96, 'decline'], [545.5, 56, 'herniation']]) {
  const b = ecgAt(LINE, t);
  chk('at ' + t + ' s the tracing is ' + stem + ' and its caption and read say ' + rate,
    b.image === 'scoot-ecg-' + stem && b.caption.includes('Ventricular rate ' + rate) && b.comment.includes(' at ' + rate + '.') && F(LINE, t + 6).vitals.heart_rate === rate);
}
const tb = last(F(HERNIATE.concat([[545.5, 'mannitol_bolus'], [565.5, 'ecg_12_lead']]), 572), 'ecg_12_lead').body;
chk('after osmotherapy the tracing is at 70', tb.image === 'scoot-ecg-temporized' && tb.caption.includes('70'));

section('prompts');
const promptTexts = CASE.case_actions.filter(a => a.prompt).flatMap(a => [a.prompt.text].concat(a.prompt.escalation ? [a.prompt.escalation.text] : []));
chk('no prompt quotes a number', !promptTexts.some(t => /\d/.test(t)), promptTexts.find(t => /\d/.test(t)));
chk('no prompt names a drug or the diagnosis', !promptTexts.some(t => /mannitol|saline|epidural|hematoma|labetalol/i.test(t)));

section('the handoff');
st = F(CALLED.concat([[245.5, 'exam_neuro'], [250.5, 'consult_neurosurgeon'],
  { t: 260.5, actionId: 'handoff_submit', payload: { disposition: 'operating_room', diagnoses: ['dx_epidural_hematoma'] } }]), 265);
chk('completes the case', st.complete && st.phase === 'case_complete');
chk('and keeps the vitals he was handed over with', st.vitals.heart_rate === 96, String(st.vitals.heart_rate));
const hs = summaryScores(st).find(r => r.id === 'handoff');
chk('the OR and the epidural score full marks', hs.points === 100, JSON.stringify(hs));

section('markers and house style');
const MARK = /\[(UNVERIFIED|PubMed|VERIFY|MODEL OUTPUT)/;
const printed = [];
CASE.follow_ups.forEach(f => printed.push(f.debrief_note, f.nurse_prompt));
const H = CASE.handoff;
[H.correct_disposition, H.correct_diagnosis].concat(H.alternative_dispositions, H.alternative_diagnoses).forEach(x => printed.push(x.explanation));
CASE.case_actions.forEach(a => printed.push(a.narration_override, a.prompt && a.prompt.text, a.prompt && a.prompt.escalation && a.prompt.escalation.text, a.display_name, a.expectation_label));
(CASE.case_actions.flatMap(a => (a.prerequisites || []).map(p => p.failure_message))).forEach(m => printed.push(m));
CASE.phases.forEach(p => { (p.transitions || []).forEach(t => printed.push(t.narration)); printed.push(p.timeout_reason, p.short_label); });
CASE.interview.topics.forEach(t => t.answer.forEach(r => printed.push(r.value)));
CASE.interview.global_answer_rules.forEach(r => printed.push(r.value));
printed.push(JSON.stringify(CASE.content_keys.consultants), JSON.stringify(CASE.content_keys.exam), JSON.stringify(CASE.content_keys.general_status));
chk('no marker in a field the learner reads as written', !printed.some(x => x && MARK.test(x)), printed.find(x => x && MARK.test(x)));
const STYLE = /[—–;]|\bquiet(ly)?\b/i;
const learnerStrings = printed.concat(CASE.case_actions.map(a => a.debrief_note), CASE.debrief_configuration.cross_cutting_teaching_points,
  CASE.phases.flatMap(p => (p.transitions || []).map(t => t.debrief_note)));
chk('house style: no dash, no semicolon and no banned word in anything a learner reads',
  !learnerStrings.some(x => x && STYLE.test(String(x).replace(/\[[^\]]*\]/g, ''))),
  String(learnerStrings.find(x => x && STYLE.test(String(x).replace(/\[[^\]]*\]/g, '')))).slice(0, 120));
chk('no short label names the diagnosis or a drug', !CASE.phases.some(p => /epidural|herniat|mannitol|bleed/i.test(p.short_label)));

section('the eye view agrees with the exam text');
const PV = st => (pupilState(st) || {}).value || {};
const HEENT = st => { const r = resolve(CASE.content_keys.exam.exam_heent, st); return r && (r.findings || r.text || JSON.stringify(r)); };
st = F(WORK, 100);
chk('on arrival: both 3 mm and brisk, and the text says equal and reactive',
  PV(st).state === 'normal' && PV(st).size_mm === 3 && PV(st).reaction === 'brisk' && /Pupils 3 mm, equal and reactive/.test(HEENT(st)), HEENT(st));
st = F(HERNIATE, 600);
chk('in herniation: the right is blown at 6 mm, the left 3 mm and brisk, as the text says',
  st.phase === 'herniation' && PV(st).state === 'blown' && PV(st).side === 'right' && PV(st).affected_mm === 6 &&
  !PV(st).affected_reaction && PV(st).size_mm === 3 && PV(st).reaction === 'brisk' &&
  /Right pupil 6 mm and fixed\. Left 3 mm and reactive/.test(HEENT(st)), JSON.stringify(PV(st)));
st = F(HERNIATE.concat([[545.5, 'mannitol_bolus']]), 600);
chk('temporized: the right 4 mm and sluggish, the left 3 mm and brisk, as the text says',
  st.phase === 'temporized' && PV(st).affected_mm === 4 && PV(st).affected_reaction === 'sluggish' && PV(st).size_mm === 3 &&
  /Right pupil 4 mm and sluggish\. Left 3 mm and reactive/.test(HEENT(st)), JSON.stringify(PV(st)));
