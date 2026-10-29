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
 *      section 15.1's third pattern, a scheduled natural history. No pack used it before,
 *      and the Python scenario runner could not walk it until the same day this file was
 *      written, so the assertions below check it from both ends: it fires with nobody
 *      doing anything, and it fires just the same after a flawless four minutes. From 5
 *      September to 27 October 2026 it had an escape; physician review DIPH-01 deleted it.
 *
 *   2. Physostigmine, the drug the case is built around. Until v0.18a its tag was gated
 *      on `study S resulted`, which scored reading the tracing and then giving the drug it
 *      forbids more leniently than not reading it. It is now gated on the phase: harmful
 *      in every phase in which the QRS is wide, and discouraged once she has stabilized.
 *
 *   3. Four oxygen-delivery actions sharing ONE vital-effect key, so that escalating a
 *      device replaces the previous one instead of stacking with it.
 */

section('intended path');
let st = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'fingerstick_blood_sugar'],
                  [4, 'ecg_12_lead'], [245, 'lorazepam_bolus'], [246, 'na_bicarbonate_bolus'],
                  [262, 'cooling_measures'], [263, 'consult_toxicology']]), 320);
chk('reaches the stabilized phase', st.phase === 'stabilized', st.phase);
chk('phase sequence is arrival, seizure, post-ictal, narrowing, stabilized',
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

/* The author's sentence. Physician review DIPH-01 (27 October 2026) restored it in full. */
const perfect = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'fingerstick_blood_sugar'],
                         [4, 'ecg_12_lead'], [30, 'cooling_measures'],
                         [40, 'consult_toxicology'], [50, 'normal_saline_1l_bolus']]), 300);
chk('a flawless first four minutes without bicarbonate reaches the seizure just the same',
    perfect.phaseSeq.some(p => p.id === 'seizing'),
    JSON.stringify(perfect.phaseSeq.map(p => p.id)));

section('there is no escape from the seizure (physician review DIPH-01)');
const bothDrugs = [[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'lorazepam_bolus'],
                   [22, 'na_bicarbonate_bolus']];
const both = fold(mk(bothDrugs), 300);
chk('both drugs before four minutes still reach the seizure',
    both.phaseSeq.some(p => p.id === 'seizing'), JSON.stringify(both.phaseSeq.map(p => p.id)));
chk('and she stays in the arrival phase until then',
    fold(mk(bothDrugs), 239).phase === 'presentation', fold(mk(bothDrugs), 239).phase);
chk('no rule takes her from arrival to the narrowing phase',
    !PHASE['presentation'].transitions.some(t => t.to === 'stabilizing'));
chk('the seizure rule is still unguarded and fires at 240',
    PHASE['presentation'].transitions.some(t => t.to === 'seizing' && t.when === null && t.after_seconds === 240));
chk('the drugs are not wasted: she is in the narrowing phase soon after',
    fold(mk(bothDrugs.concat([[250, 'urinalysis']])), 300).phase === 'stabilizing',
    fold(mk(bothDrugs.concat([[250, 'urinalysis']])), 300).phase);
chk('the intended path goes through the seizure again',
    JSON.stringify(CASE.debrief_configuration.intended_path) ===
    '["presentation","seizing","post_ictal","stabilizing","stabilized","case_complete"]');
chk('the seizure note tells the resident it was scheduled, not caused',
    /every run/.test(PHASE['presentation'].transitions.find(t => t.to === 'seizing').debrief_note));
chk('the bicarbonate transitions into the narrowing phase all take ten seconds',
    CASE.phases.flatMap(p => p.transitions)
      .filter(t => t.to === 'stabilizing' && t.after_seconds !== undefined)
      .every(t => t.after_seconds === 10 && t.measured_from === 'guard_true'));
const stabPath = [[1, 'insert_iv'], [2, 'ecg_12_lead'], [245, 'lorazepam_bolus'], [246, 'na_bicarbonate_bolus']];
chk('the stabilizing phase runs at 39.6',
    PHASE['stabilizing'].vitals.temperature_c === 39.6, String(PHASE['stabilizing'].vitals.temperature_c));
chk('and active cooling still takes 0.9 off it',
    Math.abs(fold(mk(stabPath.concat([[262, 'cooling_measures']])), 300).vitals.temperature_c - 38.7) < 0.001,
    String(fold(mk(stabPath.concat([[262, 'cooling_measures']])), 300).vitals.temperature_c));
chk('physostigmine after both drugs on arrival halts the case',
    fold(mk(bothDrugs.concat([[24, 'physostigmine']])), 300).phase === 'halted');

section('amiodarone into the wide-complex rhythm drops her pressure (physician review DIPH-12)');
const amio = fold(mk([[1, 'insert_iv'], [370, 'amiodarone_bolus_infusion']]), 400);
const noAmio = fold(mk([[1, 'insert_iv']]), 400);
chk('she stays in the wide-complex rhythm', amio.phase === 'wide_complex_tachycardia', amio.phase);
chk('the systolic falls by 20 and the diastolic by 12',
    amio.vitals.systolic_bp === noAmio.vitals.systolic_bp - 20 &&
    amio.vitals.diastolic_bp === noAmio.vitals.diastolic_bp - 12,
    amio.vitals.systolic_bp + '/' + amio.vitals.diastolic_bp);
chk('after ten seconds, not on the click',
    fold(mk([[1, 'insert_iv'], [370, 'amiodarone_bolus_infusion']]), 375).vitals.systolic_bp === noAmio.vitals.systolic_bp);
chk('no transition reads the amiodarone flag any more',
    !CASE.phases.some(p => (p.transitions || []).some(t => /amiodarone/.test(t.when || ''))));
chk('the clock route still reports itself as the clock',
    fold(mk([]), 600).failed.byClock === true);
chk('outside that rhythm amiodarone is discouraged and nothing happens',
    fold(mk([[1, 'insert_iv'], [2, 'amiodarone_bolus_infusion']]), 60).phase === 'presentation' &&
    fold(mk([[1, 'insert_iv'], [2, 'amiodarone_bolus_infusion']]), 60).vitals.systolic_bp === PHASE['presentation'].vitals.systolic_bp);
chk('and it is scored as discouraged rather than ignored',
    fold(mk([[1, 'insert_iv'], [2, 'amiodarone_bolus_infusion']]), 60)
      .discouragedTaken.has('amiodarone_bolus_infusion'));
chk('with bicarbonate in the same phase, the bicarbonate still works',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'],
             [371, 'amiodarone_bolus_infusion']]), 400).phase === 'seizing');

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

section('each deterioration is canceled by the action it names');
chk('a benzodiazepine cancels the seizure deterioration',
    fold(mk([[245, 'insert_iv'], [246, 'lorazepam_bolus']]), 420).phase !== 'wide_complex_tachycardia',
    fold(mk([[245, 'insert_iv'], [246, 'lorazepam_bolus']]), 420).phase);
chk('bicarbonate cancels the post-ictal deterioration',
    fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'], [250, 'na_bicarbonate_bolus']]), 500)
      .phase === 'stabilizing');
chk('bicarbonate given before the seizure cancels it in advance',
    !fold(mk([[1, 'insert_iv'], [2, 'na_bicarbonate_bolus'], [245, 'lorazepam_bolus']]), 600)
      .timeFires.some(f => f.to === 'wide_complex_tachycardia'));
chk('bicarbonate with a benzodiazepine rescues the wide-complex phase inside the window',
    fold(mk([[1, 'insert_iv'], [369, 'lorazepam_bolus'], [370, 'na_bicarbonate_bolus']]), 420)
      .phase === 'stabilizing',
    fold(mk([[1, 'insert_iv'], [369, 'lorazepam_bolus'], [370, 'na_bicarbonate_bolus']]), 420).phase);
/* v0.18a. She reaches this phase still convulsing, and bicarbonate is not an
   anticonvulsant. Alone it narrows the complexes and returns her to the seizing phase. */
const bicarbOnly = fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 420);
chk('bicarbonate alone returns her to the seizing phase', bicarbOnly.phase === 'seizing',
    bicarbOnly.phase);
chk('ten seconds after the bicarbonate, with a nurse line that says why',
    bicarbOnly.timeFires.some(f => f.from === 'wide_complex_tachycardia' && f.to === 'seizing'
                                  && f.after === 10) &&
    bicarbOnly.nurse.some(n => n.kind === 'deterioration' && /seizing/.test(n.text)),
    JSON.stringify(bicarbOnly.timeFires.map(f => f.from + '>' + f.to + '@' + f.after)));
/* Physician review DIPH-09: a seizure treated with bicarbonate and no anticonvulsant relapses
   once into the wide-complex rhythm, three minutes after the seizing phase is entered. */
const relapsed = fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 900);
chk('three minutes later she relapses once into the wide-complex rhythm',
    relapsed.phase === 'wide_complex_tachycardia' &&
    relapsed.timeFires.some(f => f.from === 'seizing' && f.to === 'wide_complex_tachycardia' && f.after === 180),
    JSON.stringify(relapsed.timeFires.map(f => f.from + '>' + f.to + '@' + f.after)));
chk('the relapse is announced', relapsed.nurse.some(n => n.kind === 'deterioration' && /broad and fast again/.test(n.text)));
chk('and the earlier bicarbonate does not narrow it again', relapsed.flags.has('seizure_relapsed') &&
    !relapsed.flags.has('bicarb_after_relapse'));
chk('she does not arrest on the clock in the relapsed rhythm', !relapsed.failed);
const fresh = fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [600, 'na_bicarbonate_bolus']]), 1200);
chk('a fresh dose narrows it, and she is still seizing', fresh.phase === 'seizing', fresh.phase);
chk('and she does not relapse a second time',
    fresh.timeFires.filter(f => f.from === 'seizing' && f.to === 'wide_complex_tachycardia' && f.after === 180).length === 1);
chk('a fresh dose and a benzodiazepine reach the narrowing phase',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [600, 'lorazepam_bolus'],
             [601, 'na_bicarbonate_bolus']]), 650).phase === 'stabilizing');
chk('a benzodiazepine alone does not narrow the relapsed rhythm',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [600, 'lorazepam_bolus']]), 650).phase === 'wide_complex_tachycardia');
chk('a relapse from the first seizure needs bicarbonate given while seizing',
    fold(mk([[1, 'insert_iv'], [250, 'na_bicarbonate_bolus']]), 430).phase === 'wide_complex_tachycardia' &&
    fold(mk([[1, 'insert_iv'], [250, 'na_bicarbonate_bolus']]), 410).phase === 'seizing');
chk('the nurse is still asking for an anticonvulsant back in the seizing phase',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 500).promptFires
      .some(p => p.id === 'lorazepam_bolus' && p.t > 380),
    JSON.stringify(fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus']]), 500).promptFires
      .map(p => p.id + '@' + p.t)));
chk('a benzodiazepine then takes her to stabilizing',
    fold(mk([[1, 'insert_iv'], [370, 'na_bicarbonate_bolus'], [400, 'lorazepam_bolus']]), 440)
      .phase === 'stabilizing');
chk('propofol counts as the anticonvulsant in the rescue',
    fold(mk([[1, 'insert_iv'], [369, 'propofol_bolus'], [370, 'na_bicarbonate_bolus']]), 420)
      .phase === 'stabilizing',
    fold(mk([[1, 'insert_iv'], [369, 'propofol_bolus'], [370, 'na_bicarbonate_bolus']]), 420).phase);
chk('and one second past the deadline it does not',
    fold(mk([[1, 'insert_iv'], [481, 'na_bicarbonate_bolus']]), 520).phase === 'pulseless_vt');

section('physostigmine is harmful while the QRS is wide, whether or not the tracing was read');
const blind = fold(mk([[1, 'attach_monitor'], [2, 'insert_iv'], [3, 'physostigmine']]), 60);
chk('given with no ECG at all it halts the case', !!blind.halted && blind.phase === 'halted');
chk('the halt reason names the QRS and aVR', /QRS/.test(blind.halted.reason) &&
    /aVR/.test(blind.halted.reason), blind.halted.reason);
const pending = fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [5, 'physostigmine']]), 60);
chk('ordered and not yet resulted it halts', !!pending.halted, pending.phase);
chk('the ECG really was ordered at that moment', pending.ordered.has('ecg_12_lead'));
const seen = fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [20, 'physostigmine']]), 60);
chk('once the tracing has resulted it still halts the case', !!seen.halted, seen.phase);
chk('in the wide-complex phase it halts',
    fold(mk([[1, 'insert_iv'], [370, 'physostigmine']]), 400).phase === 'halted');
const stabilizedLog = [[1, 'insert_iv'], [2, 'ecg_12_lead'], [245, 'lorazepam_bolus'],
  [246, 'na_bicarbonate_bolus'], [262, 'cooling_measures'], [263, 'consult_toxicology'], [270, 'urinalysis']];
chk('in the narrowing phase it halts (physician review DIPH-02)',
    fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'], [246, 'na_bicarbonate_bolus'],
             [265, 'physostigmine']]), 300).phase === 'halted');
const late = fold(mk(stabilizedLog.concat([[300, 'physostigmine']])), 330);
chk('once she has stabilized it does not halt', !late.halted && late.phase === 'stabilized',
    late.phase);
chk('and it is recorded as discouraged', late.discouragedTaken.has('physostigmine'));
chk('no transition in the case reads the physostigmine flag any more',
    !CASE.phases.some(p => (p.transitions || []).some(t => /physostigmine/.test(t.when || ''))));
chk('atropine is discouraged throughout (physician review DIPH-22)',
    A['atropine_bolus'].tag.length === 1 && A['atropine_bolus'].tag[0].value === 'discouraged',
    JSON.stringify(A['atropine_bolus'].tag));
chk('and it raises her heart rate by 15 after ten seconds, for five minutes',
    fold(mk([[1, 'insert_iv'], [2, 'atropine_bolus']]), 30).vitals.heart_rate === PHASE['presentation'].vitals.heart_rate + 15 &&
    fold(mk([[1, 'insert_iv'], [2, 'atropine_bolus']]), 8).vitals.heart_rate === PHASE['presentation'].vitals.heart_rate &&
    fold(mk([[1, 'insert_iv'], [2, 'atropine_bolus']]), 239).vitals.heart_rate === PHASE['presentation'].vitals.heart_rate + 15);

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

section('the other harmful actions');
chk('flumazenil after a benzodiazepine halts',
    fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [3, 'flumazenil']]), 30).phase === 'halted');
chk('flumazenil with nothing to reverse is discouraged and does not halt',
    fold(mk([[1, 'insert_iv'], [2, 'flumazenil']]), 30).phase === 'presentation' &&
    fold(mk([[1, 'insert_iv'], [2, 'flumazenil']]), 30).discouragedTaken.has('flumazenil'));
chk('a further dose of diphenhydramine halts',
    fold(mk([[1, 'insert_iv'], [2, 'diphenhydramine']]), 30).phase === 'halted');
chk('procainamide in the wide-complex phase halts',
    fold(mk([[1, 'insert_iv'], [370, 'procainamide_drip']]), 400).phase === 'halted');
/* v0.18a. Her QRS is 132 on arrival, so a sodium-channel blocker is harmful from the start. */
chk('procainamide before that phase halts too',
    fold(mk([[1, 'insert_iv'], [2, 'procainamide_drip']]), 30).phase === 'halted');
chk('it is discouraged only once she has stabilized',
    A['procainamide_drip'].tag[0].when === 'phase is stabilized' &&
    A['procainamide_drip'].tag[0].value === 'discouraged' &&
    A['procainamide_drip'].tag[1].value === 'harmful',
    JSON.stringify(A['procainamide_drip'].tag));
chk('every harmful action in this case carries a halt reason',
    HARMFUL.every(id => !!A[id].halt_reason), HARMFUL.join(', '));
chk('propranolol while the QRS is wide halts (physician review DIPH-27)',
    fold(mk([[1, 'insert_iv'], [2, 'propranolol_bolus']]), 30).phase === 'halted');
chk('and once she has stabilized it is discouraged and does not halt',
    fold(mk(stabilizedLog.concat([[300, 'propranolol_bolus']])), 330).phase === 'stabilized' &&
    fold(mk(stabilizedLog.concat([[300, 'propranolol_bolus']])), 330).discouragedTaken.has('propranolol_bolus'));
chk('propranolol and physostigmine share the same harmful phases',
    A['propranolol_bolus'].tag[0].when === A['physostigmine'].tag[0].when);
chk('five actions can be harmful here', HARMFUL.length === 5, HARMFUL.join(', '));

section('the arrival tracing is a picture, and carries no reading');
/* v0.12. The arrival ECG and the chest film are authored as images with no report text at
   all, on instruction: reading a twelve-lead is the skill this case is testing, and a
   payload that prints "QRS 132 ms" beside the tracing has done the measurement for the
   resident. The consequence to hold onto is that the arrival QRS duration is now absent
   from the interface until the debrief, except in what a consultant says.

   The narrowing phase was briefly a second image and went back to text: the second supplied
   tracing is as broad as the first, so it contradicted the nurse line about the complexes
   narrowing. Since 13 October 2026 (author instruction) it is a picture again, generated from
   its own read, so the read and the picture agree. The assertions below hold the read in
   place as the picture's comment, because a wide tracing under a narrowing line is a silent
   failure that only a person looking at both would see. */
const val = (s, id) => (s.orders[id] || []).slice(-1)[0].value;
const arrivalEcg = val(fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead']]), 40), 'ecg_12_lead');
chk('the arrival tracing is an image', arrivalEcg.kind === 'image', arrivalEcg.kind);
chk('it names a picture this build ships',
    !!PROTO.media[arrivalEcg.image], arrivalEcg.image);
chk('and carries no report text and no components',
    !arrivalEcg.report && !arrivalEcg.components);
chk('it has a caption to title the viewer with', !!arrivalEcg.caption, arrivalEcg.caption);
chk('the caption is a label rather than a reading',
    !/wide|narrow|blockade|sinus|QRS|aVR|ms\b|toxic/i.test(arrivalEcg.caption),
    arrivalEcg.caption);
const laterEcg = val(fold(mk([[1, 'insert_iv'], [2, 'ecg_12_lead'], [245, 'lorazepam_bolus'],
                              [246, 'na_bicarbonate_bolus'], [270, 'ecg_12_lead']]), 290),
                     'ecg_12_lead');
chk('the narrowing phase shows its generated tracing',
    laterEcg.kind === 'image' && laterEcg.image === 'diph-ecg-stabilizing' && !!PROTO.media[laterEcg.image],
    laterEcg.kind + ' ' + laterEcg.image);
chk('with the same bare caption as the arrival tracing', laterEcg.caption === arrivalEcg.caption, laterEcg.caption);
chk('and its read says the tracing is narrower, which is the claim the supplied image contradicted',
    /narrower/.test(laterEcg.comment), laterEcg.comment);
chk('and its QRS agrees with what cardiology reads on the repeat',
    /104 ms/.test(laterEcg.comment), laterEcg.comment);
chk('and its rate agrees with the phase it belongs to',
    /115 per minute/.test(laterEcg.comment), laterEcg.comment);
chk('and it still reports findings rather than the conclusion',
    !/sodium.channel|blockade|toxic/i.test(laterEcg.comment), laterEcg.comment);
const film = val(fold(mk([[1, 'xr_chest']]), 30), 'xr_chest');
chk('the chest film is an image and is flagged normal',
    film.kind === 'image' && film.abnormal === false, film.kind + '/' + film.abnormal);
chk('and it is in the build', !!PROTO.media[film.image], film.image);
chk('the two images are distinct',
    new Set([arrivalEcg.image, film.image]).size === 2);
chk('the second supplied tracing is not in the build, since nothing shows it',
    !PROTO.media['diph-ecg-post-bicarb'],
    Object.keys(PROTO.media).join(', '));
chk('every image the case names exists, and every image it ships is used',
    (() => {
      const named = new Set();
      for (const g of ['labs', 'imaging'])
        for (const k in CASE.content_keys[g]) {
          if (k === 'authoring_note') continue;
          for (const r of CASE.content_keys[g][k].rules)
            if (r.value && r.value.kind === 'image') named.add(r.value.image);
        }
      const shipped = new Set(Object.keys(PROTO.media));
      return [...named].every(x => shipped.has(x)) && [...shipped].every(x => named.has(x));
    })(),
    'named vs shipped');
chk('every image payload is a data URI rather than a path',
    Object.values(PROTO.media).every(u => /^data:image\/(jpeg|png|webp|gif);base64,/.test(u)));

section('every tracing is a picture, and the reading waits for the debrief');
/* Until 13 October 2026 every ECG but the arrival one reported itself in words. Since then
   each is a tracing generated from its read (author instruction), with the bare caption the
   arrival tracing has and the read as the comment the debrief prints. */
const vtEcg = val(fold(mk([[1, 'insert_iv'], [370, 'ecg_12_lead']]), 400), 'ecg_12_lead');
chk('the wide-complex phase shows its generated tracing',
    vtEcg.kind === 'image' && vtEcg.image === 'diph-ecg-wide-complex-tachycardia' && /wide-complex tachycardia/.test(vtEcg.comment), vtEcg.kind);
chk('and its read still reports findings rather than the conclusion',
    !/sodium.channel|blockade|toxic/i.test(vtEcg.comment), vtEcg.comment);
chk('no tracing caption carries a measurement',
    CASE.content_keys.imaging.ecg_12_lead.rules.every(r => r.value.kind === 'image' && !/QRS|ms\b|aVR|\d/.test(r.value.caption)));
chk('the intubated chest film still reports in words, because no image shows a tube',
    val(fold(mk([[1, 'insert_iv'], [2, 'etomidate_bolus'], [3, 'rocuronium_bolus'],
                 [4, 'intubate_rapid_sequence'], [5, 'xr_chest']]), 40), 'xr_chest')
      .kind === 'report');

section('cardiology will read the tracing, and is not prompted for');
const cards = CASE.content_keys.consultants.consult_cardiology;
chk('it reads the QRS out loud once the tracing has resulted',
    cards.some(r => /132 milliseconds/.test(r.value) && /aVR/.test(r.value)),
    'no rule names the QRS');
chk('and reads the repeat once bicarbonate has been given',
    cards.some(r => /104/.test(r.value)));
chk('it hands the management back to toxicology rather than keeping it',
    cards.every(r => !/catheter laboratory is indicated/i.test(r.value)) &&
    cards.some(r => /toxicology/i.test(r.value)));
chk('cardiology is never prompted for, so nothing pushes a resident toward it',
    !A['consult_cardiology'].prompt, JSON.stringify(A['consult_cardiology'].prompt));
chk('and it is tagged neutral, so calling it costs nothing and earns nothing',
    A['consult_cardiology'].tag.every(r => r.value === 'neutral'));

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
/* v0.18a. One or two boluses from a pH of 7.28 do not reach the 7.50 to 7.55 target, so
   the treated gas is on the way there and not past it. */
chk('the treated gas is alkalinized toward the 7.50 to 7.55 target and not past it',
    Number(get(gas.components, 'pH')) > 7.45 && Number(get(gas.components, 'pH')) <= 7.55,
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
chk('the nurse says the delay out loud when the drug goes in (physician review DIPH-41)',
    one.nurse.some(n => /few seconds/.test(n.text || '')),
    JSON.stringify(one.nurse.map(n => n.kind)));

section('the bicarbonate obligations open and close');
chk('one bolus leaves the reassessment obligation open',
    one.fuOutstanding.has('bicarbonate_reassessment'), [...one.fuOutstanding].join(', '));
chk('a second bolus discharges it', !two.fuOutstanding.has('bicarbonate_reassessment'));
chk('the nurse no longer asks "Do you want bicarb?" (owner, 27 October 2026)',
    !A['na_bicarbonate_bolus'].prompt.escalation && !/bicarb/i.test(A['na_bicarbonate_bolus'].prompt.text));
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

section('the empirical sepsis road is right at time zero and neutral afterwards (DIPH-08)');
chk('antibiotics on arrival are recommended',
    fold(mk([[1, 'insert_iv'], [2, 'ceftriaxone']]), 30).recommendedTaken.has('ceftriaxone'));
chk('after the toxicology screen has resulted they are not discouraged',
    !fold(mk([[1, 'insert_iv'], [2, 'urine_tox_screen'], [20, 'ceftriaxone']]), 40)
      .discouragedTaken.has('ceftriaxone'));
chk('nor is the lumbar puncture on arrival',
    !fold(mk([[1, 'insert_iv'], [2, 'urine_tox_screen'], [20, 'lumbar_puncture']]), 40)
      .discouragedTaken.has('lumbar_puncture'));
chk('no tag in the case reads the urine screen',
    !CASE.case_actions.some(a => a.tag.some(r => /urine_tox_screen/.test(r.when || ''))));

section('charcoal turns on the airway rather than on the drug');
chk('discouraged in an unprotected airway',
    fold(mk([[1, 'insert_iv'], [2, 'activated_charcoal']]), 30)
      .discouragedTaken.has('activated_charcoal'));
const tubed = fold(mk([[1, 'insert_iv'], [2, 'etomidate_bolus'], [3, 'rocuronium_bolus'],
                       [4, 'intubate_rapid_sequence'], [5, 'activated_charcoal']]), 40);
chk('intubation actually proceeds once she is sedated and paralyzed',
    !tubed.blocked.length && tubed.flags.has('airway_protected'),
    JSON.stringify(tubed.blocked.map(b => b.id)));
chk('and charcoal is no longer discouraged',
    !tubed.discouragedTaken.has('activated_charcoal'));
chk('nor recommended: it is neutral once she is intubated (DIPH-39)',
    !tubed.recommendedTaken.has('activated_charcoal'));

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
/* 23 October 2026, case author's instruction: one or two major diagnoses are scored. */
chk('one additional diagnosis and four minor ones are authored, each with an explanation',
    CASE.handoff.additional_diagnoses.length === 1 && CASE.handoff.minor_diagnoses.length === 4 &&
    CASE.handoff.additional_diagnoses.concat(CASE.handoff.minor_diagnoses)
      .every(d => (d.explanation || '').length > 100),
    CASE.handoff.additional_diagnoses.length + ' + ' + (CASE.handoff.minor_diagnoses || []).length);
chk('the cardiotoxicity is the first of them, because it is the thing that decides management',
    CASE.handoff.additional_diagnoses[0].catalog_id ===
      'dx_sodium_channel_blocker_cardiotoxicity',
    CASE.handoff.additional_diagnoses[0].catalog_id);
chk('the deliberate nature of the ingestion is credited when named in the handover',
    CASE.handoff.minor_diagnoses.some(d => d.catalog_id === 'dx_suicide_attempt'));
/* The whole case in one assertion. Naming the toxidrome is right and incomplete, so it has
   to be scored twice: credit when it is listed beside the agent, and a defensible verdict
   when it is offered as the primary instead. Authoring 10.2 allows exactly this, and
   before the catalog gained an id for the agent the case could not express it, because the
   toxidrome WAS the correct answer. */
chk('the toxidrome is credited as also true beside the agent',
    CASE.handoff.minor_diagnoses.some(d => d.catalog_id === 'dx_anticholinergic_toxidrome'));
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
chk('the nurse no longer discloses the bottle (physician review DIPH-43)',
    !/Benadryl|bottle/.test(JSON.stringify(A['consult_toxicology'].prompt)));
chk('every topic carries an echo phrase for the clarifying question',
    CASE.interview.topics.every(t => !!t.echo),
    CASE.interview.topics.filter(t => !t.echo).map(t => t.topic).join(', '));

section('volunteered answers (v0.18a)');
{
  const sp = st => st.readouts.filter(r => r.kind === 'speech');
  const early = fold(mk([{ t: 5, kind: 'interview', topic: 'onset', q: 'When did this start?' }]), 10);
  chk('her mother volunteers when she was last well and that she was home alone',
      /seven thirty this morning/.test(sp(early)[0].body) && /home on her own/.test(sp(early)[0].body)
      && early.askedTopics.has('last_seen_well'), sp(early)[0].body.slice(-120));
  const seizing = fold(mk([{ t: 250, kind: 'interview', topic: 'onset', q: 'When did this start?' }]), 260);
  chk('with her mother out of the room nothing is volunteered',
      seizing.phase === 'seizing' && !seizing.askedTopics.has('last_seen_well'), seizing.phase);
  chk('the bottle, what she took, self-harm and intent are never volunteered',
      ['bottle_or_pills_found', 'what_she_took', 'previous_self_harm', 'suicidal_intent']
        .every(m => CASE.interview.must_ask.includes(m)
                 && !CASE.interview.topics.some(t => (t.adjacent || []).includes(m))));
}

section('physician review, 27 October 2026 (Aakash Setty)');
chk('phenytoin on arrival moves her to the wide-complex rhythm after ten seconds (DIPH-23)',
    fold(mk([[1, 'insert_iv'], [2, 'fos_phenytoin']]), 11).phase === 'presentation' &&
    fold(mk([[1, 'insert_iv'], [2, 'fos_phenytoin']]), 13).phase === 'wide_complex_tachycardia');
chk('and so does phenytoin after the seizure',
    fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'], [250, 'fos_phenytoin']]), 270).phase === 'wide_complex_tachycardia');
chk('phenytoin is still discouraged, not harmful',
    A['fos_phenytoin'].tag.every(r => r.value === 'discouraged'));
chk('after phenytoin on arrival, bicarbonate alone takes her to the seizing phase',
    fold(mk([[1, 'insert_iv'], [2, 'fos_phenytoin'], [20, 'na_bicarbonate_bolus']]), 40).phase === 'seizing');
chk('lorazepam is critical only while she is seizing (DIPH-32)',
    A['lorazepam_bolus'].tag.length === 2 && A['lorazepam_bolus'].tag[0].when === 'phase is seizing' &&
    A['lorazepam_bolus'].tag[0].value === 'critical' && A['lorazepam_bolus'].tag[1].value === 'recommended');
chk('critical care consultation is recommended', A['consult_critical_care'].tag.every(r => r.value === 'recommended'));
chk('levetiracetam is discouraged before a benzodiazepine and neutral after (DIPH-10)',
    fold(mk([[1, 'insert_iv'], [2, 'levetiracetam_bolus']]), 20).discouragedTaken.has('levetiracetam_bolus') &&
    !fold(mk([[1, 'insert_iv'], [2, 'lorazepam_bolus'], [3, 'levetiracetam_bolus']]), 20).discouragedTaken.has('levetiracetam_bolus'));
chk('naloxone is neutral throughout (DIPH-37)', A['naloxone_bolus'].tag.every(r => r.value === 'neutral'));
chk('synchronized cardioversion is neutral in the wide-complex rhythm (DIPH-40)',
    !fold(mk([[1, 'insert_iv'], [370, 'synchronized_cardioversion']]), 380).discouragedTaken.has('synchronized_cardioversion') &&
    fold(mk([[1, 'insert_iv'], [2, 'synchronized_cardioversion']]), 20).discouragedTaken.has('synchronized_cardioversion'));
chk('psychiatry is not credited in the post-ictal phase (DIPH-31)',
    !fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus'], [250, 'consult_psychiatry']]), 260).recommendedTaken.has('consult_psychiatry'));
chk('the magnesium is normal and magnesium sulfate is neutral (DIPH-18)',
    fold(mk([[1, 'magnesium_level']]), 30).orders.magnesium_level[0].value.components[0].value === '2.0' &&
    A['magnesium_sulfate'].tag.every(r => r.value === 'neutral'));
const ua = fold(mk([[1, 'urinalysis']]), 30).orders.urinalysis[0].value.components;
chk('the urinalysis is negative for blood and concentrated (DIPH-20)',
    get(ua, 'Blood') === 'Negative' && get(ua, 'Specific gravity') === '1.030' &&
    ua.find(c => c.label === 'Specific gravity').abnormal);
chk('pregnancy is no longer a key topic (DIPH-34)',
    !CASE.interview.key_topics.includes('pregnancy') && CASE.interview.key_topics.length === 11);
chk('six learning objectives (DIPH-35)', CASE.metadata.learning_objectives.length === 6 &&
    CASE.metadata.learning_objectives.some(o => /toxicology/.test(o) && /critical care/.test(o)));
chk('flumazenil halt reason is true in every phase (DIPH-07)',
    !/never been treated/.test(A['flumazenil'].halt_reason));
const toxC = CASE.content_keys.consultants.consult_toxicology, ccC = CASE.content_keys.consultants.consult_critical_care;
chk('toxicology and critical care answer by phase first (DIPH-30)',
    toxC[0].when === 'phase is wide_complex_tachycardia' && toxC[1].when === 'phase is seizing' &&
    ccC[0].when === 'phase is wide_complex_tachycardia' && ccC[1].when === 'phase is seizing' &&
    ![toxC[0], toxC[1], ccC[0], ccC[1]].some(r => /132/.test(r.value)));
chk('cardiology reads the repeat only once there is one',
    CASE.content_keys.consultants.consult_cardiology[1].when.indexOf('flag ecg_repeated set') >= 0);
const wctSeizing = fold(mk([[1, 'insert_iv']]), 370);
const wctPost = fold(mk([[1, 'insert_iv'], [245, 'lorazepam_bolus']]), 440);
chk('reached still seizing, the wide-complex phase draws and examines a seizing patient (DIPH-29)',
    wctSeizing.phase === 'wide_complex_tachycardia' && patientVisual(wctSeizing).value.seizure === true &&
    /seizing/i.test(resolve(CASE.content_keys.exam.exam_neuro, wctSeizing).findings));
chk('reached from the post-ictal phase, eyes closed and obtunded',
    wctPost.phase === 'wide_complex_tachycardia' && patientVisual(wctPost).value.eyes === 'closed' &&
    !patientVisual(wctPost).value.seizure &&
    /Obtunded/.test(resolve(CASE.content_keys.exam.exam_neuro, wctPost).findings));
chk('and she is not talking in that phase',
    !/Talking/.test(resolve(CASE.content_keys.exam.exam_airway, wctPost).findings) &&
    /22/.test(resolve(CASE.content_keys.exam.exam_breath, wctPost).findings));

section('owner corrections, 29 October 2026');
{
  const at = (steps, t) => fold(mk(steps), t);
  const IV = [1, 'insert_iv'];
  const R = (k, s) => resolve(CASE.content_keys.exam[k], s).findings;

  /* Paralysis hides the convulsion. It does not end the seizure. */
  const par = at([IV, [250, 'etomidate_bolus'], [251, 'rocuronium_bolus']], 262);
  chk('paralyzed with no benzodiazepine: she is still in the seizing phase', par.phase === 'seizing', par.phase);
  chk('the neuro exam shows no convulsion once she is paralyzed',
      /Paralyzed/.test(R('exam_neuro', par)) && !/tonic-clonic|jerking|seizing/i.test(R('exam_neuro', par)), R('exam_neuro', par));
  chk('the breathing exam no longer describes chest movement with the seizure',
      !/seizure/i.test(R('exam_breath', par)) && /bag/.test(R('exam_breath', par)), R('exam_breath', par));
  chk('the eyes no longer rove', !/roving/.test(R('exam_heent', par)) || /no roving/.test(R('exam_heent', par)), R('exam_heent', par));
  chk('the figure stops convulsing', patientVisual(par).value.seizure !== true);
  chk('the bedside summary does not say generalized seizure',
      !/seizure/i.test(JSON.stringify(resolve(CASE.content_keys.general_status.rules, par))));
  chk('the nurse does not say she is still seizing once she is paralyzed',
      !at([IV, [250, 'etomidate_bolus'], [251, 'rocuronium_bolus']], 600).nurse.some(e => /still seizing/i.test(e.text || '')));
  chk('the benzodiazepine is still expected and not satisfied by paralysis',
      !par.satisfied.has('lorazepam_bolus') && (par.expected.has('lorazepam_bolus') || par.recommendedExpected.has('lorazepam_bolus')));
  chk('the rocuronium note teaches that paralysis hides the seizure',
      /cannot see whether she is still seizing/.test(A['rocuronium_bolus'].debrief_note || ''));

  /* Not telling her she missed what did not matter. */
  const good = at([[1, 'attach_monitor'], IV, [2, 'second_iv'], [3, 'non_rebreather_mask'], [4, 'ecg_12_lead'],
                   [5, 'venous_blood_gas'], [6, 'urine_hcg_qualitative'], [245, 'lorazepam_bolus'],
                   [246, 'na_bicarbonate_bolus']], 330);
  chk('two IVs count as the vascular access, so the IO is not asked for', good.satisfied.has('intraosseous_line'));
  chk('a non-rebreather counts as the oxygen, so nasal cannula is not asked for', good.satisfied.has('nasal_cannula_oxygen'));
  chk('one gas counts for both', good.satisfied.has('arterial_blood_gas'));
  chk('one pregnancy test counts for both', good.satisfied.has('serum_hcg_quantitative'));
  chk('intubation is neutral: one benzodiazepine that stopped the seizure leaves nothing to ask',
      A['intubate_rapid_sequence'].tag.every(r => r.value === 'neutral') &&
      !good.recommendedExpected.has('intubate_rapid_sequence') && !good.expected.has('intubate_rapid_sequence'));

  /* The gases follow the seizure and the dose. */
  const gas = (steps, t, id) => {
    const s = at(steps, t); const o = (s.orders[id] || []).slice(-1)[0];
    return o && o.value && o.value.components ? Object.fromEntries(o.value.components.map(c => [c.label, c.value])) : {};
  };
  const hh = g => Math.abs(6.1 + Math.log10(Number(g['Bicarbonate']) / (0.03 * Number(g['pCO2']))) - Number(g['pH'])) <= 0.015;
  const V = 'venous_blood_gas', AB = 'arterial_blood_gas';
  const vg = {
    arrival: gas([IV, [5, V]], 60, V),
    seizing: gas([IV, [250, V]], 300, V),
    seizBic: gas([IV, [245, 'na_bicarbonate_bolus'], [250, V]], 300, V),
    one: gas([IV, [5, 'na_bicarbonate_bolus'], [10, V]], 60, V),
    two: gas([IV, [5, 'na_bicarbonate_bolus'], [20, 'na_bicarbonate_bolus'], [30, V]], 80, V),
    drip: gas([IV, [5, 'na_bicarbonate_bolus'], [10, 'na_bicarbonate_infusion'], [30, V]], 80, V),
  };
  chk('venous pH on arrival 7.25', vg.arrival['pH'] === '7.25', JSON.stringify(vg.arrival));
  chk('venous pH while seizing with no bicarbonate is far lower, 6.94', vg.seizing['pH'] === '6.94', JSON.stringify(vg.seizing));
  chk('bicarbonate during the seizure helps but the retained carbon dioxide holds it down, 7.11',
      vg.seizBic['pH'] === '7.11', JSON.stringify(vg.seizBic));
  chk('one dose 7.41, two doses 7.47, an infusion 7.52',
      vg.one['pH'] === '7.41' && vg.two['pH'] === '7.47' && vg.drip['pH'] === '7.52',
      [vg.one['pH'], vg.two['pH'], vg.drip['pH']].join());
  chk('every venous gas agrees with Henderson-Hasselbalch', Object.values(vg).every(hh),
      JSON.stringify(Object.entries(vg).filter(([k, g]) => !hh(g)).map(([k]) => k)));
  const ag = {
    seizBic: gas([IV, [245, 'na_bicarbonate_bolus'], [250, AB]], 300, AB),
    two: gas([IV, [5, 'na_bicarbonate_bolus'], [20, 'na_bicarbonate_bolus'], [30, AB]], 80, AB),
    drip: gas([IV, [5, 'na_bicarbonate_bolus'], [10, 'na_bicarbonate_infusion'], [30, AB]], 80, AB),
  };
  chk('arterial pH 7.16 seizing on bicarbonate, 7.53 after two doses, 7.55 on the infusion',
      ag.seizBic['pH'] === '7.16' && ag.two['pH'] === '7.53' && ag.drip['pH'] === '7.55',
      [ag.seizBic['pH'], ag.two['pH'], ag.drip['pH']].join());
  chk('every new arterial gas agrees with Henderson-Hasselbalch', Object.values(ag).every(hh));

  /* Bicarbonate narrows the monitor on arrival. */
  const qrs = s => { const old = global.ST; global.ST = s; const e = MONITOR.ecgNow(); global.ST = old; return Math.round(e.qrsS * 1000); };
  const before = at([IV], 20), after = at([IV, [5, 'na_bicarbonate_bolus']], 20);
  chk('the monitor complex narrows after bicarbonate on arrival', qrs(after) === 116 && qrs(before) > 116, qrs(before) + ' -> ' + qrs(after));

  /* US usage in learner text. */
  const strip = o => { if (Array.isArray(o)) return o.map(strip); if (o && typeof o === 'object') { const r = {};
    for (const k in o) { if (['variants', 'expanded_variants', 'asks', 'canonical', 'references', 'migrations', 'provenance',
      'review_hints', 'authored_against', 'binding_note', 'author_note', 'author_rationale', 'verify'].includes(k)) continue; r[k] = strip(o[k]); } return r; } return o; };
  const UK = /registrar|half (seven|six|eight)|Paracetamol|\bring (her|me|him)\b|\bsmelt\b|trolley|haemo|aemia\b|kalaem|\bquiet|colour|litre\b|off school/i;
  const flat = JSON.stringify(strip(CASE));
  chk('no British spelling or usage, and no banned word, in learner text', !UK.test(flat), (flat.match(new RegExp('.{40}(' + UK.source + ').{20}', 'i')) || [''])[0]);
}
