/* Case assertions for CHFE (acute decompensated HFrEF).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk and the engine.
 * Everything here names a specific drug, study or phase and therefore belongs to
 * the case pack rather than to the engine.
 */

section('intended path');
let st=fold(mk([[1,'iv_access_peripheral'],[2,'cardiac_monitor'],[6,'niv_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']]),40);
chk('reaches improving',st.phase==='improving',st.phase);
chk('phase sequence',JSON.stringify(st.phaseSeq.map(p=>p.id))==='["presentation","stabilizing","improving"]',JSON.stringify(st.phaseSeq.map(p=>p.id)));
chk('no halt',!st.halted);

section('harmful halts');
for(const h of ['metoprolol_iv','diltiazem_iv','crystalloid_bolus_1l','dobutamine_infusion']){
  const s=fold(mk([[1,'iv_access_peripheral'],[5,h]]),20);
  chk(h+' halts',s.halted&&s.halted.id===h&&s.phase==='halted');
  chk(h+' has halt reason',!!(s.halted&&s.halted.reason&&s.halted.reason.length>20));
}

section('prerequisites');
st=fold(mk([[1,'intubation_rsi']]),10);
chk('intubation blocked without sedation/paralytic',st.blocked.length===1&&!st.flags.has('intubated'),JSON.stringify(st.blocked.map(b=>b.id)));
chk('block message present',st.blocked[0]&&st.blocked[0].message.length>10);
chk('blocked action logged in timeline',st.timeline.some(x=>x.type==='blocked'));
st=fold(mk([[1,'iv_access_peripheral'],[2,'etomidate_iv'],[3,'rocuronium_iv'],[4,'intubation_rsi']]),10);
chk('intubation proceeds once satisfied',st.flags.has('intubated'),JSON.stringify(st.blocked.map(b=>b.id)));
chk('intubation -> hypotensive phase',st.phase==='post_intubation_hypotension',st.phase);

section('deterioration rescue');
st=fold(mk([[1,'iv_access_peripheral'],[2,'nitroglycerin_infusion'],[3,'etomidate_iv'],[4,'rocuronium_iv'],[5,'intubation_rsi'],[7,'nitroglycerin_stop'],[9,'norepinephrine_infusion']]),20);
chk('rescued to intubated_stabilized',st.phase==='intubated_stabilized',st.phase);
const s2=fold(mk([[1,'iv_access_peripheral'],[2,'etomidate_iv'],[3,'rocuronium_iv'],[4,'intubation_rsi'],[6,'nitroglycerin_infusion']]),20);
chk('nitrate in hypotensive phase halts',s2.halted&&s2.halted.id==='nitroglycerin_infusion');

section('renamed actions');
chk('IV action reads Insert IV',PROTO.actions.iv_access_peripheral.name==='Insert IV',PROTO.actions.iv_access_peripheral.name);
chk('NIV reads positive pressure ventilation',
    /Positive pressure ventilation \(CPAP\/BIPAP\)/.test(PROTO.actions.niv_cpap.name),PROTO.actions.niv_cpap.name);

section('prompts');
st=fold(mk([]),50);
chk('NIV prompt fires at 45s',st.promptFires.some(p=>p.id==='niv_cpap'&&p.level===1));
st=fold(mk([[10,'niv_cpap']]),50);
chk('no prompt once action taken',!st.promptFires.some(p=>p.id==='niv_cpap'));
st=fold(mk([]),100);
chk('escalation fires at 90s',st.promptFires.some(p=>p.id==='niv_cpap'&&p.level===2));
chk('prompt cap respected',Object.keys(st.phaseEntry).length>=1&&st.promptFires.length<=PROTO.promptCap+2,String(st.promptFires.length));
const anyTraj=st.nurse.filter(n=>n.kind==='prompt').some(n=>/dropping|crashing|getting worse|deteriorat|falling/i.test(n.text));
chk('no prompt implies a trajectory',!anyTraj);

section('follow-ups');
st=fold(mk([[1,'iv_access_peripheral'],[2,'etomidate_iv'],[3,'rocuronium_iv'],[4,'intubation_rsi']]),120);
chk('post-intubation sedation prompt fires',st.fuFires.some(f=>f.fid==='post_intubation_sedation'));
st=fold(mk([[1,'iv_access_peripheral'],[2,'etomidate_iv'],[3,'rocuronium_iv'],[4,'intubation_rsi'],[20,'post_intubation_sedation_infusion']]),120);
chk('satisfied follow-up does not prompt',!st.fuFires.some(f=>f.fid==='post_intubation_sedation'));

section('exam changes with treatment');
const pre=fold(mk([[1,'exam_pulm']]),5).readouts[0].body.findings;
const post=fold(mk([[1,'iv_access_peripheral'],[2,'niv_cpap'],[3,'nitroglycerin_infusion'],[6,'exam_pulm']]),10).readouts[0].body.findings;
chk('lung findings differ after treatment',pre!==post);
chk('wheeze present at presentation',/wheeze/i.test(pre));

section('consultants');
const c0=fold(mk([[1,'consult_cardiology']]),5).readouts.pop().body;
const c1=fold(mk([[1,'ecg_12_lead'],[2,'consult_cardiology']]),5).readouts.pop().body;
const c2=fold(mk([[1,'ecg_12_lead'],[2,'labs_troponin_hs'],[20,'consult_cardiology']]),30).readouts.pop().body;
chk('three distinct consultant tiers',c0!==c1&&c1!==c2&&c0!==c2);
chk('no reference to a study never ordered',!/troponin/i.test(c0)||/send|get|need/i.test(c0));

section('interview');
st=fold([{seq:0,t:1,kind:'interview',topic:'orthopnea',q:'how many pillows'}],5);
chk('answer resolved from authored rules',st.readouts[0].body.length>10);
st=fold([{seq:0,t:1,kind:'interview',topic:null,q:'what is your favourite colour'}],5);
chk('unmatched uses fallback',st.readouts[0].body.length>10&&st.readouts[0].matched===null);
st=fold(mk([[1,'iv_access_peripheral'],[2,'etomidate_iv'],[3,'rocuronium_iv'],[4,'intubation_rsi']]).concat([{seq:9,t:6,kind:'interview',topic:'onset',q:'when did it start'}]),20);
chk('alertness gating: intubated patient gives no history',/cannot give any history|does not respond/i.test(st.readouts[st.readouts.length-1].body));

section('handoff');
st=fold(mk([[1,'iv_access_peripheral'],[6,'niv_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']]).concat([{seq:9,t:40,actionId:'handoff_submit',payload:{disposition:'icu_or_ccu',diagnosis:PROTO.correctDxId}}]),60);
chk('handoff completes the case',st.phase==='case_complete'&&st.complete);
chk('payload recorded',st.handoff&&st.handoff.disposition==='icu_or_ccu');
chk('expected actions collected',st.expected.size>0,String(st.expected.size));
