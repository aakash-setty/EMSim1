/* Case assertions for CHFE (acute decompensated HFrEF).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk and the engine.
 * Everything here names a specific drug, study or phase and therefore belongs to
 * the case pack rather than to the engine.
 */

section('intended path');
let st=fold(mk([[1,'iv_access_peripheral'],[2,'cardiac_monitor'],[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']]),40);
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
chk('the old split NIV ids are gone',
    !PROTO.actions.niv_cpap&&!PROTO.actions.niv_bipap&&!PROTO.shadowed.niv_bipap);
chk('NIV reads positive pressure ventilation',
    /Positive pressure ventilation \(BiPAP\/CPAP\)/.test(PROTO.actions.niv_bipap_cpap.name),PROTO.actions.niv_bipap_cpap.name);

section('prompts');
st=fold(mk([]),50);
chk('NIV prompt fires at 45s',st.promptFires.some(p=>p.id==='niv_bipap_cpap'&&p.level===1));
st=fold(mk([[10,'niv_bipap_cpap']]),50);
chk('no prompt once action taken',!st.promptFires.some(p=>p.id==='niv_bipap_cpap'));
st=fold(mk([]),100);
chk('escalation fires at 90s',st.promptFires.some(p=>p.id==='niv_bipap_cpap'&&p.level===2));
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
const post=fold(mk([[1,'iv_access_peripheral'],[2,'niv_bipap_cpap'],[3,'nitroglycerin_infusion'],[6,'exam_pulm']]),10).readouts[0].body.findings;
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
st=fold(mk([[1,'iv_access_peripheral'],[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']]).concat([{seq:9,t:40,actionId:'handoff_submit',payload:{disposition:'icu_or_ccu',diagnosis:PROTO.correctDxId}}]),60);
chk('handoff completes the case',st.phase==='case_complete'&&st.complete);
chk('payload recorded',st.handoff&&st.handoff.disposition==='icu_or_ccu');
chk('expected actions collected',st.expected.size>0,String(st.expected.size));

section('oxygenation is action-driven, not phase-driven');
{
  /* The whole arc in one place. The authored baseline is 87 in every non-terminal
     phase a resident can reach without intubating, and the only things that move the
     number on the screen are positive pressure and, for thirty seconds, a nitrate. */
  const SP='oxygen_saturation';
  const spo2=(steps,at)=>fold(mk(steps),at).vitals[SP];
  const IV=[1,'iv_access_peripheral'], MON=[2,'cardiac_monitor'];

  chk('arrival saturation is 87',spo2([IV,MON],5)===87);

  chk('positive pressure adds three points',spo2([IV,MON,[6,'niv_bipap_cpap']],10)===90);
  chk('positive pressure does not wear off',spo2([IV,MON,[6,'niv_bipap_cpap']],400)===90);
  chk('positive pressure alone does not change the phase',
      fold(mk([IV,MON,[6,'niv_bipap_cpap']]),10).phase==='presentation');

  /* Five points for thirty seconds, from either route, and no more from both. */
  chk('a nitrate adds five points',spo2([IV,MON,[6,'nitroglycerin_infusion']],20)===92);
  chk('the nitrate has lapsed at thirty seconds',
      spo2([IV,MON,[6,'nitroglycerin_infusion']],40)===87);
  chk('a repeat nitrate does the same thing again',
      spo2([IV,MON,[6,'nitroglycerin_infusion'],[50,'nitroglycerin_infusion']],60)===92);
  chk('the two nitrate routes do not stack',
      spo2([IV,MON,[6,'nitroglycerin_infusion'],[7,'nitroglycerin_sublingual']],20)===92);

  /* Mask plus nitrate is the phase change, and the two effects add on the new
     baseline: 87 + 3 + 5 during the window, 87 + 3 after it. */
  const both=[IV,MON,[6,'niv_bipap_cpap'],[8,'nitroglycerin_infusion']];
  chk('mask and nitrate move to stabilizing',fold(mk(both),20).phase==='stabilizing');
  chk('mask and nitrate read 95 during the nitrate window',spo2(both,20)===95);
  chk('and 90 once the nitrate lapses',spo2(both,60)===90);

  /* The point of the change: diuresis moves everything except the saturation. */
  const beforeFuro=fold(mk(both),60), afterFuro=fold(mk(both.concat([[70,'furosemide_iv']])),90);
  chk('furosemide moves to improving',afterFuro.phase==='improving');
  chk('furosemide changes the saturation by nothing',
      afterFuro.vitals[SP]===beforeFuro.vitals[SP],
      beforeFuro.vitals[SP]+' -> '+afterFuro.vitals[SP]);
  chk('furosemide still slows the heart rate',
      afterFuro.vitals.heart_rate<beforeFuro.vitals.heart_rate);
  chk('furosemide still drops the respiratory rate',
      afterFuro.vitals.respiratory_rate<beforeFuro.vitals.respiratory_rate);
  chk('furosemide carries no vital effect at all',
      !(PROTO.actions.furosemide_iv.vital_effects||[]).length);

  /* Intubation takes the mask off, so its effect stops applying and the ventilator
     phases read exactly as authored. */
  const tubed=fold(mk([IV,MON,[6,'niv_bipap_cpap'],[8,'etomidate_iv'],[9,'rocuronium_iv'],
                       [10,'intubation_rsi']]),20);
  chk('intubation ends the positive pressure effect',
      tubed.phase==='post_intubation_hypotension'&&tubed.vitals[SP]===91,
      tubed.phase+' '+tubed.vitals[SP]);

  /* A terminal phase is a written ending and is exempt from every effect. */
  const halt=fold(mk([IV,MON,[6,'niv_bipap_cpap'],[8,'crystalloid_bolus_1l']]),20);
  chk('a halted case reads its authored numbers, effects and all',
      halt.phase==='halted'&&halt.vitals[SP]===PHASE.halted.vitals[SP]);
}

section('the monitor is what shows the vitals');
{
  chk('cardiac_monitor is the action that reveals them',
      PROTO.actions.cardiac_monitor.reveals_vitals===true);
  chk('a resident who never attaches it is never monitored',
      fold(mk([[1,'iv_access_peripheral'],[6,'niv_bipap_cpap']]),300).monitoring===null);
  chk('attaching it is enough on its own',
      !!fold(mk([[2,'cardiac_monitor']]),5).monitoring);
}
