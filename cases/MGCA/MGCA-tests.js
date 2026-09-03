/* Case assertions for MGCA (meningococcaemia with septic shock and adrenal crisis).
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
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus']]),20);
chk('volume without glucocorticoid enters the adrenal branch',st.phase==='adrenal_crisis',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'hydrocortisone_bolus']]),20);
chk('glucocorticoid without the organism enters the meningococcaemia branch',
    st.phase==='progressive_meningococcaemia',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'hydrocortisone_bolus'],
            [4,'vancomycin']]),20);
chk('vancomycin does not count as treating the organism',
    st.phase==='progressive_meningococcaemia',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'ceftriaxone'],[4,'prednisone']]),20);
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
            [480,'norepinephrine_drip']]),800);
chk('rescued inside the last window',st.phase==='stabilized_shock',st.phase);
st=fold(mk([[10,'insert_iv'],[760,'ceftriaxone'],[770,'hydrocortisone_bolus'],
            [780,'norepinephrine_drip']]),800);
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
                'potassium_chloride_kcl','hypertonic_saline_3_infusion',
                'hypertonic_saline_25_bolus']){
  const s=fold(mk([[1,'insert_iv'],[5,h]]),20);
  chk(h+' halts',s.halted&&s.halted.id===h&&s.phase==='halted');
  chk(h+' has a halt reason',!!(s.halted&&s.halted.reason&&s.halted.reason.length>20));
}
st=fold(mk([[1,'insert_iv'],[400,'metoprolol_bolus']]),800);
chk('a harmful action still halts after a deadline has passed',st.phase==='halted',st.phase);

section('prerequisites');
st=fold(mk([[1,'ceftriaxone']]),10);
chk('drug blocked without a line',st.blocked.length===1&&!st.flags.has('abx_given'));
st=fold(mk([[1,'insert_iv'],[2,'normal_saline_1l_bolus'],[3,'lumbar_puncture']]),20);
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
  const s=fold(mk([[1,'insert_iv'],[2,bag]]),20);
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
            [20,'fingerstick_blood_sugar']]),40);
const sugars=(st.orders.fingerstick_blood_sugar||[]).map(o=>o.value&&o.value.components[0].value);
chk('a repeat glucose in the adrenal branch reads lower than on arrival',
    sugars.length===2&&Number(sugars[1])<Number(sugars[0]),sugars.join(' then '));
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
