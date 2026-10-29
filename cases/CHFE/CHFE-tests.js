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
// 29 October 2026, owner: the crystalloid bolus and norepinephrine no longer halt (section below).
for(const h of ['metoprolol_iv','diltiazem_iv','dobutamine_infusion']){
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
st=fold([{seq:0,t:1,kind:'interview',topic:null,q:'what is your favorite color'}],5);
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

  /* Owner instruction, 28 October 2026: only an infusion or drip moves the phase. The
     sublingual and intravenous boluses lift the saturation by two for one minute, then the
     nurse says it has worn off. The minute is sped up and the line says so. */
  for(const b of ['nitroglycerin_sublingual','nitroglycerin']){
    chk(b+' does not move the patient',
        at([IV,MON,[6,'niv_bipap_cpap'],[20,b]],30).phase==='niv_supported');
    chk(b+' does not set the shared flag',
        !at([IV,[6,b]],10).flags.has('nitrate_given'));
  }
  chk('the infusion sets the shared flag',
      at([IV,[6,'nitroglycerin_infusion']],10).flags.has('nitrate_given'));
  chk('the drip sets the shared flag',
      at([IV,[6,'nitroprusside_drip']],10).flags.has('nitrate_given'));
  chk('a bolus does not hold off the four-minute tiring',
      at([IV,MON,[6,'nitroglycerin_sublingual']],250).phase==='impending_respiratory_failure');
  chk('only the infusion is the scored critical action (nitroprusside credits it)',
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
  chk('both together read 97',
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion']],30)===97);
  chk('the improving phase reads 97 too',
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion'],[30,'furosemide_iv']],40)===97);
  chk('the infusion carries no vital effect of its own',
      !(PROTO.actions.nitroglycerin_infusion.vital_effects||[]).length);

  /* The bolus: two points for sixty seconds, then the nurse's line. */
  const sl=[IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_sublingual']];
  chk('a sublingual dose reads two higher while it acts',spo2(sl,50)===91,String(spo2(sl,50)));
  chk('and drops back after a minute',spo2(sl,85)===89,String(spo2(sl,85)));
  chk('the intravenous bolus does the same',
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin']],50)===91&&
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin']],85)===89);
  chk('a second dose does not stack',
      spo2([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_sublingual'],[40,'nitroglycerin_sublingual']],60)===91);
  const worn=fold(mk(sl),85).nurse.filter(e=>/worn off/.test(e.text||''));
  chk('the nurse says it wore off, once',worn.length===1,String(worn.length));
  chk('and tells the student the timing is sped up',worn.length&&/sped up/.test(worn[0].text));

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
  const halt=fold(mk([IV,MON,[6,'niv_bipap_cpap'],[8,'metoprolol_iv']]),20);
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

section('v0.18a audit fixes');
{
  let s=fold(mk([[1,'iv_access_peripheral'],[2,'ultrasound_cardiac']]),30);
  const us=(s.orders.ultrasound_cardiac||[])[0];
  chk('the cardiac ultrasound returns the authored scan, not a normal ventricle',!!us&&us.source==='case'&&/reduced/i.test(JSON.stringify(us.value)),us?us.source:'not ordered');
  s=fold(mk([[1,'iv_access_peripheral'],[2,'labs_abg']]),30);
  const ab=(s.orders.labs_abg||[])[0];
  chk('the arterial gas is authored, not a normal default',!!ab&&ab.source==='case',ab?ab.source:'not ordered');
  s=fold(mk([[1,'iv_access_peripheral'],[2,'labetalol_bolus']]),20);
  chk('labetalol is the same error as metoprolol',s.phase==='halted',s.phase);
  s=fold(mk([[1,'iv_access_peripheral'],[2,'epinephrine_push_dose']]),20);
  chk('a push-dose epinephrine bolus does not count as a running pressor',!s.flags.has('pressor_running'));
}

section('owner corrections, 29 October 2026');
{
  const IV=[1,'iv_access_peripheral'], MON=[2,'cardiac_monitor'];
  const at=(steps,t)=>fold(mk(steps),t);
  const strong=at([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion']],40);

  /* One act, any route. */
  chk('the mask counts as the oxygen, so the non-rebreather is not marked missing',
      strong.satisfied.has('oxygen_nonrebreather'));
  chk('a tube counts as the oxygen too',
      at([IV,[3,'etomidate_iv'],[4,'rocuronium_iv'],[5,'intubation_rsi']],10).satisfied.has('oxygen_nonrebreather'));
  chk('the boluses and nitroprusside are never expected on top of the infusion',
      ['nitroglycerin_sublingual','nitroglycerin','nitroprusside_drip'].every(id=>!strong.recommendedExpected.has(id)&&!strong.expected.has(id)));
  chk('every recommended action expected on the mask-and-drip run is one he can do once',
      [...strong.recommendedExpected].every(id=>!['nitroglycerin_sublingual','nitroglycerin','nitroprusside_drip'].includes(id)));
  chk('nitroprusside counts in place of the nitroglycerin infusion',
      at([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroprusside_drip']],30).satisfied.has('nitroglycerin_infusion'));

  /* The bolus brings the pressure down for its minute. */
  const SB='systolic_bp', DB='diastolic_bp';
  const bp=(steps,t)=>{ const v=fold(mk(steps),t).vitals; return [v[SB],v[DB]]; };
  const pre=bp([IV,MON,[6,'niv_bipap_cpap']],18);
  for(const b of ['nitroglycerin','nitroglycerin_sublingual']){
    const on=bp([IV,MON,[6,'niv_bipap_cpap'],[20,b]],50), off=bp([IV,MON,[6,'niv_bipap_cpap'],[20,b]],85);
    chk(b+' lowers the pressure by 20 over 8 while it acts',on[0]===pre[0]-20&&on[1]===pre[1]-8,pre+' -> '+on);
    chk(b+' wears off after a minute',off[0]===pre[0]&&off[1]===pre[1],String(off));
  }
  chk('two boluses do not stack',
      bp([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin'],[40,'nitroglycerin']],60)[0]===pre[0]-20);
  const worn=fold(mk([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin']]),85).nurse.filter(e=>/worn off/.test(e.text||''));
  chk('the nurse says the pressure came back up',worn.length===1&&/pressure is back up/.test(worn[0].text));
  chk('while a bolus acts, the nurse does not say his pressure is still right up',
      !fold(mk([IV,MON,[6,'niv_bipap_cpap'],[10,'nitroglycerin'],[60,'nitroglycerin'],[110,'nitroglycerin'],[160,'nitroglycerin']]),200)
        .nurse.some(e=>/still right up/.test(e.text||'')));

  /* A liter of fluid or norepinephrine before the tube: worse, not dead. */
  let st=at([IV,MON,[5,'crystalloid_bolus_1l']],14.9);
  chk('fluid on arrival: no halt, still on arrival for ten seconds',st.phase==='presentation'&&!st.halted,st.phase);
  st=at([IV,MON,[5,'crystalloid_bolus_1l']],16);
  chk('then impending respiratory failure, said by the nurse',
      st.phase==='impending_respiratory_failure'&&!st.halted&&st.nurse.some(e=>/gone to his lungs/.test(e.text||'')),st.phase);
  chk('the bolus is scored down, not halted',st.discouragedTaken.has('crystalloid_bolus_1l'));
  st=at([IV,MON,[5,'crystalloid_bolus_1l'],[30,'niv_bipap_cpap'],[35,'nitroglycerin_infusion']],300);
  chk('the mask and a drip still bring him back, and he stays back',
      st.phase==='stabilizing'&&st.phaseSeq.filter(p=>p.id==='impending_respiratory_failure').length===1,
      st.phaseSeq.map(p=>p.id).join(' > '));
  chk('fluid on the mask tips him over too',
      at([IV,MON,[6,'niv_bipap_cpap'],[20,'crystalloid_bolus_1l']],31).phase==='impending_respiratory_failure');
  st=at([IV,MON,[6,'niv_bipap_cpap'],[20,'nitroglycerin_infusion'],[30,'crystalloid_bolus_1l']],120);
  chk('fluid once he is stabilizing is scored down and moves nothing',
      st.phase==='stabilizing'&&st.discouragedTaken.has('crystalloid_bolus_1l'),st.phase);
  st=at([IV,MON,[5,'norepinephrine_infusion']],16);
  chk('norepinephrine at 188 over 104: impending respiratory failure, no halt',
      st.phase==='impending_respiratory_failure'&&!st.halted&&st.discouragedTaken.has('norepinephrine_infusion'),st.phase);
  chk('only metoprolol, diltiazem and dobutamine halt before the tube, with push-dose epinephrine and the post-tube vasodilators',
      CASE.case_actions.filter(a=>a.tag.some(r=>r.value==='harmful')).map(a=>a.catalog_id).sort().join()===
      ['diltiazem_iv','dobutamine_infusion','epinephrine_push_dose','metoprolol_iv','nitroglycerin','nitroglycerin_infusion','nitroglycerin_sublingual','nitroprusside_drip'].sort().join());

  /* A diuretic given before he stabilized takes him on to improving at once. */
  st=at([IV,MON,[6,'niv_bipap_cpap'],[10,'furosemide_iv'],[20,'nitroglycerin_infusion']],20.5);
  chk('an early diuretic moves him to improving the moment he stabilizes',
      st.phase==='improving'&&st.phaseSeq.map(p=>p.id).join()==='presentation,niv_supported,stabilizing,improving',
      st.phaseSeq.map(p=>p.id+'@'+p.t).join(' > '));

  /* The text after intubation does not assume a nitrate. */
  const tubeNoNitrate=at([IV,[3,'etomidate_iv'],[4,'rocuronium_iv'],[5,'intubation_rsi']],10);
  const tubeOnDrip=at([IV,[2,'nitroglycerin_infusion'],[3,'etomidate_iv'],[4,'rocuronium_iv'],[5,'intubation_rsi']],10);
  for(const k of ['consult_cardiology','consult_critical_care']){
    chk(k+' says stop the nitrate only when a drip is running',
        !/Stop the nitrate/.test(resolve(CASE.content_keys.consultants[k],tubeNoNitrate))&&
        /Stop the nitrate/.test(resolve(CASE.content_keys.consultants[k],tubeOnDrip)));
  }
  chk('the norepinephrine note makes the nitrate conditional',
      /If a nitrate drip was running/.test(CASE.case_actions.find(a=>a.catalog_id==='norepinephrine_infusion').debrief_note));
  chk('the crystalloid note no longer calls it harmful after the tube',
      !/remains harmful/.test(CASE.case_actions.find(a=>a.catalog_id==='crystalloid_bolus_1l').debrief_note));

  /* The gas agrees with the monitor. */
  const abg=resolve(CASE.content_keys.labs.labs_abg.rules,strong);
  const po2=abg.components.find(x=>x.label==='pO2').value;
  chk('the arterial pO2 in stabilizing fits a saturation of 97',Number(po2)>=80&&strong.vitals.oxygen_saturation===97,po2);

  /* US usage and the house's banned word, in everything a learner can read. */
  const strip=o=>{ if(Array.isArray(o)) return o.map(strip); if(o&&typeof o==='object'){ const r={};
    for(const k in o){ if(['variants','expanded_variants','asks','canonical','references','migrations','provenance','review_hints',
      'authored_against','binding_note','author_note','author_rationale'].includes(k)) continue; r[k]=strip(o[k]); } return r; } return o; };
  const UK=/trolley|trousers|fortnight|\bround the|\btablets\b|haemo|aemia\b|oedema|dyspnoea|orthopnoea|\bchemist\b|water tablet|Full blood count|\bquiet|colour|litre\b|randomised|anaesth/i;
  const flat=JSON.stringify(strip(CASE));
  chk('no British spelling or usage, and no banned word, in learner text',!UK.test(flat),(flat.match(UK)||[''])[0]);
}

