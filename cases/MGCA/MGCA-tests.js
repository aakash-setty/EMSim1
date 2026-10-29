/* Case assertions for MGCA (meningococcemia with septic shock and adrenal crisis).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk and the engine.
 * Everything here names a specific drug, study or phase and therefore belongs to the
 * case pack rather than to the engine.
 *
 * This is the first case to use time-guarded transitions, so most of what is below
 * exercises the clock. A scenario with a wait cannot be expressed through mk(), which
 * builds a log of actions, so the timing tests drive fold() directly with an explicit
 * `now`: the fold derives deadlines from the case file, so passing a later `now` is
 * exactly what the running engine does when the clock advances.
 */

section('intended path');
let st=fold(mk([[1,'insert_iv'],[2,'fingerstick_blood_sugar'],[3,'basic_chemistry_chem_7'],
                [4,'blood_culture_x_2'],[6,'ceftriaxone'],[8,'hydrocortisone_bolus'],
                [10,'normal_saline_1l_bolus']]),40);
chk('reaches improving',st.phase==='improving',st.phase);
chk('phase sequence',JSON.stringify(st.phaseSeq.map(p=>p.id))==='["presentation","improving"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id)));
chk('no halt',!st.halted);
chk('no deterioration fired',st.timeFires.length===0,JSON.stringify(st.timeFires));

section('the two deficits need two drugs');
/* v0.18a: the crisis follows 90 seconds after volume without glucocorticoid, not on the click. */
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus']]),60);
chk('volume alone does not change her on the same click',st.phase==='presentation',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus']]),120);
chk('volume without glucocorticoid enters the adrenal branch',st.phase==='adrenal_crisis',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'hydrocortisone_bolus']]),20);
chk('glucocorticoid without the organism enters the meningococcemia branch',
    st.phase==='progressive_meningococcemia',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'hydrocortisone_bolus'],
            [4,'vancomycin']]),20);
chk('vancomycin does not count as treating the organism',
    st.phase==='progressive_meningococcemia',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'ceftriaxone'],[4,'prednisone']]),120);
chk('oral steroid does not count as replacement',st.phase==='adrenal_crisis',st.phase);

section('time-guarded transitions');
st=fold([],800);
chk('doing nothing walks the whole case',st.phase==='cardiac_arrest',st.phase);
chk('do-nothing trajectory and timings',
    JSON.stringify(st.phaseSeq.map(p=>p.id+'@'+p.t))===
    '["presentation@0","adrenal_crisis@240","frank_septic_shock@450","cardiac_arrest@750"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id+'@'+p.t)));
chk('three deteriorations recorded for the debrief',st.timeFires.length===3,
    String(st.timeFires.length));
chk('each carries the deadline that expired',st.timeFires.every(f=>f.after>0&&f.when),
    JSON.stringify(st.timeFires.map(f=>f.after)));
st=fold([],239);
chk('nothing fires before the first deadline',st.phase==='presentation',st.phase);

st=fold(mk([[1,'insert_iv'],[2,'ceftriaxone'],[3,'hydrocortisone_bolus'],
            [4,'normal_saline_1l_bolus']]),800);
chk('both drugs before the deadline: the clock never fires',st.phase==='improving',st.phase);
chk('and no deterioration is recorded',st.timeFires.length===0);

st=fold(mk([[1,'insert_iv'],[2,'hydrocortisone_bolus'],[3,'normal_saline_1l_bolus']]),800);
chk('glucocorticoid alone still arrests',st.phase==='cardiac_arrest',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'ceftriaxone'],[3,'normal_saline_1l_bolus']]),800);
chk('antibiotic alone still arrests',st.phase==='cardiac_arrest',st.phase);

/* The pair that carries the lesson: the difference between them is one action inside
   the last window, so a window nobody can hit would show up here. */
st=fold(mk([[10,'insert_iv'],[250,'ceftriaxone'],[470,'hydrocortisone_bolus'],
            [475,'normal_saline_1l_bolus'],[480,'norepinephrine_drip']]),800);
chk('rescued inside the last window',st.phase==='stabilized_shock',st.phase);
st=fold(mk([[10,'insert_iv'],[760,'ceftriaxone'],[770,'hydrocortisone_bolus'],
            [775,'normal_saline_1l_bolus'],[780,'norepinephrine_drip']]),800);
chk('one action too late arrests',st.phase==='cardiac_arrest',st.phase);

section('the nurse narrates a deterioration, and only then');
st=fold([],800);
const det=st.nurse.filter(n=>n.kind==='deterioration');
chk('one narration per deterioration',det.length===3,String(det.length));
chk('narration is on its own kind, not a prompt',
    !st.nurse.some(n=>n.kind==='prompt'&&/harder to rouse|lost her output|spreading up/i.test(n.text)));
const trajInPrompt=st.nurse.filter(n=>n.kind==='prompt')
  .some(n=>/dropping|crashing|getting worse|deteriorat|falling/i.test(n.text));
chk('no prompt implies a trajectory',!trajInPrompt);

section('fairness: prompts precede every deadline');
st=fold([],800);
const firstAbx=st.promptFires.find(p=>p.id==='ceftriaxone');
const firstSteroid=st.promptFires.find(p=>p.id==='hydrocortisone_bolus');
chk('the antibiotic is prompted before the 240s deadline',!!firstAbx&&firstAbx.t<240,
    firstAbx?String(firstAbx.t):'never');
chk('the glucocorticoid is prompted before the 240s deadline',!!firstSteroid&&firstSteroid.t<240,
    firstSteroid?String(firstSteroid.t):'never');

section('harmful halts');
for(const h of ['metoprolol_bolus','propranolol_bolus','esmolol_drip','labetalol_bolus',
                'labetalol_drip','diltiazem_bolus','insulin_bolus','insulin_drip',
                'potassium_chloride_kcl']){
  const s=fold(mk([[1,'insert_iv'],[5,h]]),20);
  chk(h+' halts',s.halted&&s.halted.id===h&&s.phase==='halted');
  chk(h+' has a halt reason',!!(s.halted&&s.halted.reason&&s.halted.reason.length>20));
}
/* v0.18a: hypertonic saline is wrong here but not a bedside death, and the 25 percent bag
   needs a central line. */
st=fold(mk([[1,'insert_iv'],[5,'hypertonic_saline_3_infusion']]),20);
chk('hypertonic saline infusion is discouraged, not halting',!st.halted&&st.discouragedTaken.has('hypertonic_saline_3_infusion'));
st=fold(mk([[1,'insert_iv'],[5,'hypertonic_saline_25_bolus']]),20);
chk('concentrated saline is refused through a peripheral line',st.blocked.some(b=>b.id==='hypertonic_saline_25_bolus')&&!st.halted);
st=fold(mk([[1,'insert_iv'],[400,'metoprolol_bolus']]),800);
chk('a harmful action still halts after a deadline has passed',st.phase==='halted',st.phase);

section('prerequisites');
st=fold(mk([[1,'ceftriaxone']]),10);
chk('drug blocked without a line',st.blocked.length===1&&!st.flags.has('abx_given'));
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[100,'lumbar_puncture']]),120);
chk('lumbar puncture blocked once hypotensive',
    st.blocked.some(b=>b.id==='lumbar_puncture')&&!st.flags.has('lumbar_puncture_performed'));
st=fold(mk([[1,'insert_iv'],[2,'lumbar_puncture']]),20);
chk('lumbar puncture permitted while normotensive',st.flags.has('lumbar_puncture_performed'));
st=fold(mk([[1,'insert_iv'],[2,'csf_cell_count']]),20);
chk('cerebrospinal fluid blocked before the puncture',
    st.blocked.some(b=>b.id==='csf_cell_count'));
st=fold(mk([[1,'insert_iv'],[2,'intubate_rapid_sequence']]),20);
chk('intubation blocked without sedation and paralysis',!st.flags.has('intubated'));

section('equivalence group coverage');
for(const bag of ['lactated_ringer_s_1l_bolus','normal_saline_500ml_bolus',
                  'lactated_ringer_s_500ml_bolus']){
  const s=fold(mk([[1,'insert_iv'],[2,bag]]),120);
  chk(bag+' satisfies the volume requirement',s.phase==='adrenal_crisis',s.phase);
}

section('results freeze and trend');
/* Ordered studies land in st.orders, not st.readouts; readouts hold exams, consults
   and interview answers. */
st=fold(mk([[1,'insert_iv'],[2,'lactate']]),30);
chk('lactate resolves from the case, not a catalog default',
    st.orders.lactate&&st.orders.lactate[0].source==='case',
    st.orders.lactate?st.orders.lactate[0].source:'not ordered');
st=fold(mk([[1,'insert_iv'],[2,'fingerstick_blood_sugar'],[3,'normal_saline_1l_bolus'],
            [100,'fingerstick_blood_sugar']]),120);
const sugars=(st.orders.fingerstick_blood_sugar||[]).map(o=>o.value&&o.value.components[0].value);
chk('a repeat glucose in the adrenal branch reads lower than on arrival',
    sugars.length===2&&Number(sugars[1])<Number(sugars[0]),sugars.join(' then '));
st=fold(mk([[1,'insert_iv'],[2,'d50_bolus'],[4,'fingerstick_blood_sugar'],[200,'fingerstick_blood_sugar']]),220);
const dsug=(st.orders.fingerstick_blood_sugar||[]).map(o=>o.value&&o.value.components[0].value);
chk('dextrose raises the glucose, then without glucocorticoid it falls again',
    dsug.length===2&&Number(dsug[0])>100&&Number(dsug[1])<70,dsug.join(' then '));
/* Result freezing: a study ordered in one phase keeps that phase's value even though
   the patient has since moved on. */
st=fold(mk([[1,'insert_iv'],[2,'lactate'],[3,'normal_saline_1l_bolus']]),40);
chk('a result freezes at the state it was ordered in',
    st.orders.lactate[0].value.components[0].value==='2.8',
    st.orders.lactate[0].value.components[0].value);

section('handoff');
st=fold(mk([[1,'insert_iv'],[2,'ceftriaxone'],[3,'hydrocortisone_bolus'],
            [4,'normal_saline_1l_bolus']])
        .concat([{seq:9,t:40,actionId:'handoff_submit',
                  payload:{disposition:'icu',diagnosis:PROTO.correctDxId}}]),60);
chk('handoff completes the case',st.phase==='case_complete'&&st.complete);
chk('the correct diagnosis resolves to a catalog id',
    PROTO.correctDxId==='dx_meningococcemia',String(PROTO.correctDxId));

section('volunteered answers (v0.18a)');
{
  const sp = st => st.readouts.filter(r => r.kind === 'speech');
  const onArrival = fold(mk([{ t: 5, kind: 'interview', topic: 'headache', q: 'Any headache?' }]), 10);
  const b = sp(onArrival)[0].body;
  chk('on arrival a headache answer also says her neck and the light are fine',
      /neck's fine/.test(b) && /light doesn't bother/.test(b), b.slice(-120));
  chk('and neck stiffness and photophobia count as asked',
      onArrival.askedTopics.has('neck_stiffness') && onArrival.askedTopics.has('photophobia'));
  const crisis = fold(mk([{ t: 250, kind: 'interview', topic: 'headache', q: 'Any headache?' }]), 260);
  chk('in adrenal crisis she is confused and answers only what is asked',
      crisis.phase === 'adrenal_crisis' && sp(crisis)[0].body === '"Bit of a headache. Not the worst thing."' &&
      !crisis.askedTopics.has('neck_stiffness'), crisis.phase + ' ' + sp(crisis)[0].body);
  chk('the menstrual and tampon screen is never volunteered',
      CASE.interview.must_ask.includes('menstrual_and_tampon') &&
      !CASE.interview.topics.some(t => (t.adjacent || []).includes('menstrual_and_tampon')));
}

section('owner corrections, 29 October 2026: not telling her she missed what did not matter');
{
  const NEU = ['doxycycline','epinephrine_drip','vasopressin_drip','epinephrine_bolus','normal_saline_infusion',
               'lactated_ringer_s_infusion','d5_ns_bolus','acetaminophen','ondansetron','cefepime','meropenem',
               'csf_cell_count','csf_gram_stain','csf_protein','csf_glucose','csf_culture','csf_rapid_antigen_test_for_n_meningitidis'];
  chk('alternatives, second agents and the CSF studies are neutral',
      NEU.every(id => A[id].tag.every(r => r.value === 'neutral')), NEU.filter(id => !A[id].tag.every(r => r.value === 'neutral')).join());
  for (const ab of ['cefepime', 'meropenem']) {
    const s = fold(mk([[1,'insert_iv'],[4,'blood_culture_x_2'],[6,ab]]), 20);
    chk(ab + ' counts as the antibiotic', s.satisfied.has('ceftriaxone'));
  }
  const good = fold(mk([[1,'insert_iv'],[2,'fingerstick_blood_sugar'],[3,'basic_chemistry_chem_7'],
                [4,'blood_culture_x_2'],[6,'ceftriaxone'],[8,'hydrocortisone_bolus'],[10,'normal_saline_1l_bolus']]), 200);
  chk('deferring the lumbar puncture leaves no CSF study marked missing',
      ![...good.recommendedExpected].some(id => /^csf_/.test(id)));
  const strip = o => { if (Array.isArray(o)) return o.map(strip); if (o && typeof o === 'object') { const r = {};
    for (const k in o) { if (['variants','expanded_variants','asks','canonical','references','migrations','provenance','review_hints',
      'authored_against','binding_note','author_note','author_rationale','verify','authoring_note'].includes(k)) continue; r[k] = strip(o[k]); } return r; } return o; };
  const UK = /haemo|septicaem|\bRing me|\bround the|trolley|\bquiet/i;
  const flat = JSON.stringify(strip(CASE));
  chk('no British spelling or usage, and no banned word, in learner text', !UK.test(flat), (flat.match(UK) || [''])[0]);
}

