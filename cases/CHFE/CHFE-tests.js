/* Case assertions for CHFE (acute decompensated HFrEF).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk and the engine.
 * Everything here names a specific drug, study or phase and therefore belongs to
 * the case pack rather than to the engine.
 */

section('intended path');
let st=fold(mk([[1,'iv_access_peripheral'],[2,'cardiac_monitor'],[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']]),40);
chk('reaches improving',st.phase==='improving',st.phase);
chk('phase sequence',
    JSON.stringify(st.phaseSeq.map(p=>p.id))==='["presentation","niv_supported","stabilizing","improving"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id)));
chk('no halt',!st.halted);
/* Both orders in the same batch are two log entries one second apart at most, and the
   engine re-checks the transitions after each. The mask phase is passed through rather
   than skipped, which is what the phase list should say. */
const batched=fold(mk([[1,'iv_access_peripheral'],[6,'niv_bipap_cpap'],[6,'nitroglycerin_infusion']]),10);
chk('a batch of both reaches stabilizing through the mask phase',
    batched.phase==='stabilizing'&&
    JSON.stringify(batched.phaseSeq.map(p=>p.id))==='["presentation","niv_supported","stabilizing"]',
    JSON.stringify(batched.phaseSeq.map(p=>p.id)));

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

section('the two treatments are not the same treatment');
{
  /* The case exists to separate positive pressure from vasodilation, so the two-by-two
     they describe is asserted corner by corner. */
  const IV=[1,'iv_access_peripheral'], MON=[2,'cardiac_monitor'];
  const at=(steps,t)=>fold(mk(steps),t);

  chk('the mask alone reaches the moderate phase and stops there',
      at([IV,MON,[6,'niv_bipap_cpap']],200).phase==='niv_supported');
  chk('a nitrate alone reaches the other moderate phase and stops there',
      at([IV,MON,[6,'nitroglycerin_infusion']],200).phase==='nitrate_responding');
  chk('the mask added to a nitrate reaches the mild phase',
      at([IV,MON,[6,'nitroglycerin_infusion'],[20,'niv_bipap_cpap']],30).phase==='stabilizing');
  chk('a nitrate added to the mask reaches the mild phase',
      at([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion']],30).phase==='stabilizing');

  /* The sublingual route is a bridge and the case accepts it as one: it sets the shared
     flag and moves the patient, and it is not what is scored. */
  chk('sublingual nitrate moves the patient too',
      at([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_sublingual']],30).phase==='stabilizing');
  chk('both routes set the shared flag',
      at([IV,[6,'nitroglycerin_sublingual']],10).flags.has('nitrate_given')&&
      at([IV,[6,'nitroglycerin_infusion']],10).flags.has('nitrate_given'));
  chk('only the infusion is the scored critical action',
      PROTO.actions.nitroglycerin_infusion.tag.some(r=>r.value==='critical')&&
      !PROTO.actions.nitroglycerin_sublingual.tag.some(r=>r.value==='critical'));

  /* The diuretic is not a substitute for either of them, which is the sequencing lesson
     the case was built on and the one most at risk from adding phases. */
  chk('the diuretic alone moves the patient nowhere',
      at([IV,MON,[6,'furosemide_iv']],200).phase==='presentation');
  chk('the diuretic does not stand in for the nitrate',
      at([IV,MON,[6,'niv_bipap_cpap'],[20,'furosemide_iv']],60).phase==='niv_supported');
}

section('the saturation ladder');
{
  /* The authored baseline is the UNSUPPORTED number in every non-terminal phase and the
     mask is worth four points on top of it. Read the two columns against each other: the
     mask moves the number by four and the baseline by nothing, and the nitrate moves the
     baseline by three with nothing on the patient's face. */
  const SP='oxygen_saturation';
  const spo2=(steps,at)=>fold(mk(steps),at).vitals[SP];
  const base=id=>PHASE[id].vitals[SP];
  const IV=[1,'iv_access_peripheral'], MON=[2,'cardiac_monitor'];

  chk('arrival saturation is 85',spo2([IV,MON],5)===85);
  chk('the mask leaves the baseline where it was',
      base('niv_supported')===base('presentation'),
      base('presentation')+' -> '+base('niv_supported'));
  chk('the mask reads four points higher on the screen',
      spo2([IV,MON,[6,'niv_bipap_cpap']],20)===89);
  chk('positive pressure does not wear off',
      spo2([IV,MON,[6,'niv_bipap_cpap']],200)===89);
  chk('the nitrate moves the baseline instead, with no mask on',
      base('nitrate_responding')===88&&spo2([IV,MON,[6,'nitroglycerin_infusion']],20)===88);
  chk('both together read 94',
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion']],30)===94);
  chk('the nitrate carries no vital effect of its own any more',
      !(PROTO.actions.nitroglycerin_infusion.vital_effects||[]).length&&
      !(PROTO.actions.nitroglycerin_sublingual.vital_effects||[]).length);

  /* Unchanged from the previous design and still the second learning objective. */
  const both=[IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion']];
  const beforeFuro=fold(mk(both),40), afterFuro=fold(mk(both.concat([[50,'furosemide_iv']])),60);
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

section('what happens when the nitrate never comes');
{
  const IV=[1,'iv_access_peripheral'], MON=[2,'cardiac_monitor'];
  const at=(steps,t)=>fold(mk(steps),t);

  chk('doing nothing at all tires him at four minutes',
      at([IV,MON],250).phase==='impending_respiratory_failure');
  chk('and not a second early',at([IV,MON],235).phase==='presentation');
  chk('the mask alone buys four more minutes and no more',
      at([IV,MON,[6,'niv_bipap_cpap']],250).phase==='impending_respiratory_failure'&&
      at([IV,MON,[6,'niv_bipap_cpap']],240).phase==='niv_supported');
  chk('a nitrate with no mask buys five',
      at([IV,MON,[6,'nitroglycerin_infusion']],310).phase==='impending_respiratory_failure'&&
      at([IV,MON,[6,'nitroglycerin_infusion']],300).phase==='nitrate_responding');

  /* Arriving there with the mask already on must not bounce straight back, which is the
     failure mode a second exit rule would have introduced. */
  const tired=at([IV,MON,[6,'niv_bipap_cpap']],400);
  chk('he stays tired while the mask is all he has',
      tired.phase==='impending_respiratory_failure'&&tired.flags.has('on_niv'));
  chk('one treatment does not rescue him',
      at([IV,MON,[260,'niv_bipap_cpap']],300).phase==='impending_respiratory_failure');
  chk('both treatments do',
      at([IV,MON,[260,'niv_bipap_cpap'],[262,'nitroglycerin_infusion']],270).phase==='stabilizing');
  chk('and so does a tube',
      at([IV,MON,[260,'etomidate_iv'],[261,'rocuronium_iv'],[262,'intubation_rsi']],270)
        .phase==='post_intubation_hypotension');

  /* The deterioration is a cost, not an ending. Nothing in this case kills the patient. */
  const forever=at([IV,MON],3000);
  chk('the clock never reaches a terminal phase',
      forever.phase==='impending_respiratory_failure'&&!forever.failed&&!forever.halted,
      forever.phase);
  chk('no transition in the case authors a terminal arrival on the clock',
      !CASE.phases.some(p=>(p.transitions||[]).some(t=>
        t.after_seconds!==undefined&&(PHASE[t.to]||{}).terminal)));

  /* Fairness: both treatments the guard names were asked for, out loud, before it fired. */
  const idle=at([],250);
  const said=id=>idle.promptFires.some(f=>f.id===id&&f.t<=220);
  chk('the mask was asked for before the deadline',said('niv_bipap_cpap'));
  chk('the nitrate was asked for before the deadline',said('nitroglycerin_infusion'));
}

section('the patient as the case gets worse');
{
  const IV=[1,'iv_access_peripheral'];
  const ask=(steps,t)=>fold(mk(steps).concat([{seq:99,t:t-1,kind:'interview',topic:'onset',q:'when did this start'}]),t)
                        .readouts.filter(r=>r.kind==='speech').pop().body;

  chk('on arrival he answers in bursts',/^'Three\.\.\. four days/.test(ask([IV],5)),ask([IV],5));
  chk('on the mask he is still in bursts',
      ask([IV,[2,'niv_bipap_cpap']],10)===ask([IV],5));
  chk('once he is comfortable he answers in sentences',
      /It's been building for three or four days/.test(
        ask([IV,[2,'niv_bipap_cpap'],[3,'nitroglycerin_infusion']],10)));
  chk('when he tires he stops answering',
      /too exhausted to answer/i.test(ask([IV],250)));
  chk('the content is the same in both registers',
      /four this morning/.test(ask([IV],5))&&
      /four this morning/.test(ask([IV,[2,'niv_bipap_cpap'],[3,'nitroglycerin_infusion']],10)));

  /* The nurse does not suggest taking a history from a man who cannot give one. */
  const tired=fold(mk([IV]),400);
  chk('the adherence prompt is not raised once he has tired',
      !tired.promptFires.some(f=>f.id==='interview_topic_medication_adherence'&&
                                 f.t>tired.phaseEntry.impending_respiratory_failure));
}

section('the edema has a severity and it is legible');
{
  /* Lung ultrasound is the readout that says severe, moderate or mild out loud, and the
     word has to match the phase the patient is in rather than the drugs on his chart. */
  const IV=[1,'iv_access_peripheral'];
  /* mk() turns [t, id] pairs into log entries, so the scan step has to go through it
     with the rest rather than being concatenated on afterwards. */
  const scan=(steps,t)=>fold(mk(steps.concat([[t-1,'pocus_lung_cardiac']])),t+20)
                          .orders.pocus_lung_cardiac.pop().value.report;
  chk('severe on arrival',/Lung: severe|three or more B lines per field in all/i.test(scan([IV],5)));
  chk('moderate on the mask',/Lung: moderate/.test(scan([IV,[2,'niv_bipap_cpap']],6)));
  chk('moderate on a nitrate',/Lung: moderate/.test(scan([IV,[2,'nitroglycerin_infusion']],6)));
  chk('mild on both',
      /Lung: mild/.test(scan([IV,[2,'niv_bipap_cpap'],[3,'nitroglycerin_infusion']],6)));
  chk('clearing after the diuretic',
      /clearing/.test(scan([IV,[2,'niv_bipap_cpap'],[3,'nitroglycerin_infusion'],[4,'furosemide_iv']],6)));
  /* The defect this replaced: a diuretic given in the first minute used to clear the
     ultrasound of a patient still in the arrival phase. */
  chk('a diuretic on its own does not clear the scan',
      /Lung: severe|three or more B lines per field in all/i.test(scan([IV,[2,'furosemide_iv']],6)));
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
