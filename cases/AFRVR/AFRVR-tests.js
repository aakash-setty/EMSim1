/* Case assertions for AFRVR (atrial fibrillation with rapid ventricular response and
 * acute decompensated HFrEF).
 *
 * Run by engine/engine-tests.js, which supplies chk, section, mk, fold and the engine.
 * Everything here names a specific drug, study or phase and belongs to the case pack.
 *
 * Three things in this case are not exercised by any other pack and most of what is
 * below is aimed at them: a vital effect authored as four staged steps so a number
 * climbs rather than jumps, a transition delayed from the moment its guard became true
 * rather than from phase entry, and coverage groups on CRITICAL actions, where a
 * covered sibling has to satisfy the covering action's expectation and not merely
 * borrow its tag.
 */

section('intended path');
let st=fold(mk([[1,'attach_monitor'],[2,'insert_iv'],[3,'ecg_12_lead'],[4,'ultrasound_cardiac'],
                [5,'ultrasound_lung'],[6,'non_invasive_positive_pressure_ventilation'],
                [8,'furosemide_40_mg_iv'],[10,'digoxin_bolus'],[45,'digoxin_bolus'],
                [50,'apixaban']]),120);
chk('reaches the stabilized phase',st.phase==='stabilized',st.phase);
chk('phase sequence',
    JSON.stringify(st.phaseSeq.map(p=>p.id))==='["presentation","breathing_supported","stabilized"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id)));
chk('no halt',!st.halted);
chk('no deterioration fired',st.timeFires.filter(f=>f.to==='respiratory_failure').length===0);
chk('every critical action expected on arrival was taken',
    [...st.expectedByPhase['presentation']].every(id=>st.taken.has(id)),
    [...st.expectedByPhase['presentation']].filter(id=>!st.taken.has(id)).join(', '));

section('the monitor is dark until somebody attaches one');
st=fold(mk([[1,'insert_iv'],[2,'ecg_12_lead']]),20);
chk('no monitoring without the act',!st.monitoring);
st=fold(mk([[1,'attach_monitor']]),20);
chk('attaching it is enough',!!st.monitoring&&st.monitoring.id==='attach_monitor');

section('positive pressure raises the saturation over about a minute, in steps');
/* The author asked for a saturation that climbs rather than jumps. The engine cannot
   ramp one effect, so the case authors four two-point steps at 0, 20, 40 and 60
   seconds, each with its own key so they stack. Read the monitor at each step. */
const nivLog=mk([[1,'non_invasive_positive_pressure_ventilation']]);
const sat=t=>fold(nivLog,t).vitals.oxygen_saturation;
chk('breathing-supported baseline is the UNSUPPORTED 88',
    fold(mk([[1,'insert_iv']]),20).vitals.oxygen_saturation===88,
    String(fold(mk([[1,'insert_iv']]),20).vitals.oxygen_saturation));
chk('first step lands immediately: 90',sat(1)===90,String(sat(1)));
chk('still 90 just before the second step',sat(20)===90,String(sat(20)));
chk('second step at 20 seconds: 92',sat(21)===92,String(sat(21)));
chk('third step at 40 seconds: 94',sat(41)===94,String(sat(41)));
chk('fourth step at 60 seconds: 96',sat(61)===96,String(sat(61)));
chk('and it does not keep climbing after that',sat(400)===96,String(sat(400)));
chk('four separate effects are recorded, one per step',
    fold(nivLog,120).vitalFx.filter(f=>f.id==='non_invasive_positive_pressure_ventilation')
      .length===4);
chk('the effect is guarded off by intubation',
    fold(mk([[1,'non_invasive_positive_pressure_ventilation'],[2,'insert_iv'],
             [3,'etomidate_bolus'],[4,'rocuronium_bolus'],[5,'intubate_rapid_sequence']]),120)
      .vitals.oxygen_saturation===96,
    'ventilated phase authors 96 of its own');

section('the diuretic moves nothing on the monitor, and that is the point');
const noDiur=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                      [3,'digoxin_bolus'],[4,'digoxin_bolus']]),200);
const withDiur=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                        [3,'digoxin_bolus'],[4,'digoxin_bolus'],[6,'furosemide_40_mg_iv']]),200);
chk('same phase either way',noDiur.phase===withDiur.phase&&withDiur.phase==='stabilized');
chk('identical vitals with and without the diuretic',
    JSON.stringify(noDiur.vitals)===JSON.stringify(withDiur.vitals),
    JSON.stringify(withDiur.vitals));
chk('furosemide records no vital effect at all',
    !withDiur.vitalFx.some(f=>f.id==='furosemide_40_mg_iv'));
/* Where the diuretic IS visible: the lung. */
const lungPlain=fold(mk([[1,'insert_iv'],[2,'ultrasound_lung']]),20);
const lungAfter=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                         [3,'furosemide_40_mg_iv'],[4,'ultrasound_lung']]),30);
chk('the untreated lung reads diffuse B-lines',
    /Diffuse bilateral B-lines/.test(lungPlain.orders.ultrasound_lung[0].value.report));
chk('the treated lung reads improving',
    /reduced in number/.test(lungAfter.orders.ultrasound_lung[0].value.report));

section('diltiazem is discouraged, not lethal, and you can see what it did');
st=fold(mk([[1,'insert_iv'],[2,'diltiazem_bolus']]),30);
chk('the case is not halted',!st.halted,st.phase);
chk('it satisfies rate control',st.flags.has('rate_control_given'));
chk('the systolic pressure falls by twenty',st.vitals.systolic_bp===112,
    String(st.vitals.systolic_bp));
chk('the diastolic pressure falls by ten',st.vitals.diastolic_bp===68,
    String(st.vitals.diastolic_bp));
chk('the fall has an onset: nothing has moved at 10 seconds',
    fold(mk([[1,'insert_iv'],[2,'diltiazem_bolus']]),10).vitals.systolic_bp===132,
    String(fold(mk([[1,'insert_iv'],[2,'diltiazem_bolus']]),10).vitals.systolic_bp));
const dTag=id=>{const s=fold(mk([[1,'insert_iv'],[2,'ultrasound_cardiac'],[6,id]]),30);
                return (s.timeline.find(x=>x.id===id)||{}).tag;};
chk('still discouraged once the ejection fraction is known',dTag('diltiazem_bolus')==='discouraged',
    String(dTag('diltiazem_bolus')));
chk('a discouraged action is recorded for the debrief',
    fold(mk([[1,'insert_iv'],[2,'diltiazem_bolus']]),30).discouragedTaken.has('diltiazem_bolus'));

section('one push is not enough, and the second one is not instant either');
/* The vision the case is built to: a single dose produces a partial response and the
   patient is still in a rapid ventricular response. What changes the case is the second
   dose, and the flag that carries it is granted on the second administration of the act
   rather than the first. */
const rc1=mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
              [3,'digoxin_bolus']]);
const rc2=mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
              [3,'digoxin_bolus'],[40,'digoxin_bolus']]);
st=fold(rc1,300);
chk('one dose sets rate_control_given',st.flags.has('rate_control_given'));
chk('one dose does NOT make the rate adequate',!st.flags.has('rate_control_adequate'));
chk('and five minutes later the phase has still not turned over',
    st.phase==='breathing_supported',st.phase);
chk('the monitor shows a partial response, 152 down to 130',st.vitals.heart_rate===130,
    String(st.vitals.heart_rate));
st=fold(rc2,45);
chk('the second dose sets rate_control_adequate',st.flags.has('rate_control_adequate'));
chk('five seconds after it, the phase has still not turned over',
    st.phase==='breathing_supported',st.phase);
st=fold(rc2,55);
chk('ten seconds after the second dose it does, with no further action',
    st.phase==='stabilized',st.phase);
chk('and the rate on the monitor is 104',st.vitals.heart_rate===104,String(st.vitals.heart_rate));
chk('the delayed transition is recorded for the debrief',
    st.timeFires.some(f=>f.to==='stabilized'&&f.after===10));
/* Two different agents are two attempts at the same act, because they share one counter. */
chk('metoprolol then amiodarone is two doses, not one of each',
    fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
             [3,'metoprolol_bolus'],[5,'amiodarone_bolus_infusion']]),60)
      .flags.has('rate_control_adequate'));
chk('one metoprolol on its own is not',
    !fold(mk([[1,'insert_iv'],[2,'metoprolol_bolus']]),60).flags.has('rate_control_adequate'));
chk('a third dose changes nothing further',
    fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
             [3,'digoxin_bolus'],[5,'digoxin_bolus'],[7,'digoxin_bolus']]),60)
      .flags.has('rate_control_adequate'));

section('the nurse says the agents take time, in red and in the chart');
const said=t=>fold(rc1,t).nurse.filter(x=>/take a bit of time to kick in/i.test(x.text));
chk('she says it when the drug is given',said(20).length===1,String(said(20).length));
chk("it is an alert, so it is colored and it goes into the running chart",
    said(20).every(x=>x.kind==='alert'),said(20).map(x=>x.kind).join(','));
chk('it is not a prompt, so it does not consume a prompt slot and does not trill',
    said(20).every(x=>x.kind!=='prompt'));
chk('the action still narrates normally as well',
    fold(rc1,20).nurse.some(x=>x.kind==='narration'&&/digoxin/i.test(x.text)));
chk('and every route to rate control says it',
    ['diltiazem_bolus','metoprolol_bolus','amiodarone_bolus_infusion','esmolol_drip',
     'propranolol_bolus'].every(id=>
      fold(mk([[1,'insert_iv'],[2,id]]),20).nurse
        .some(x=>x.kind==='alert'&&/take a bit of time to kick in/i.test(x.text))));
chk('a repeat dose says it again',said(60).length===1&&
    fold(rc2,60).nurse.filter(x=>/take a bit of time to kick in/i.test(x.text)).length===2);

section('the nurse asks for the second dose, and stops once it is in');
st=fold(rc1,300);
chk('the obligation fires',st.fuFires.some(f=>f.fid==='second_rate_control_dose'));
chk('and stays open while only one dose is in',
    [...st.fuOutstanding].includes('second_rate_control_dose'),
    [...st.fuOutstanding].join(', '));
st=fold(rc2,300);
chk('the second dose discharges it',
    ![...st.fuOutstanding].includes('second_rate_control_dose'),
    [...st.fuOutstanding].join(', '));
chk('it never fires at all if the second dose came first',
    !fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
              [3,'digoxin_bolus'],[4,'digoxin_bolus']]),300)
       .fuFires.some(f=>f.fid==='second_rate_control_dose'));

section('time-guarded deterioration, and where it stops');
st=fold([],1200);
chk('doing nothing reaches respiratory failure',st.phase==='respiratory_failure',st.phase);
chk('and stays there: this case has no route to a terminal phase on the clock',
    !CASE.phases.find(p=>p.id===st.phase).terminal);
chk('do-nothing trajectory and timing',
    JSON.stringify(st.phaseSeq.map(p=>p.id+'@'+p.t))==='["presentation@0","respiratory_failure@240"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id+'@'+p.t)));
chk('no transition in this case opts in to ending on the clock',
    !CASE.phases.some(p=>(p.transitions||[]).some(t=>t.allow_time_to_terminal)));
st=fold([],239);
chk('nothing fires before the deadline',st.phase==='presentation',st.phase);
st=fold(mk([[1,'non_invasive_positive_pressure_ventilation']]),1200);
chk('positive pressure cancels the deterioration for the rest of the case',
    st.phase==='breathing_supported',st.phase);
st=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus']]),1200);
chk('rate control alone still deteriorates, through the congested phase',
    st.phase==='respiratory_failure',st.phase);
chk('and it went the long way round',
    JSON.stringify(st.phaseSeq.map(p=>p.id))===
    '["presentation","rate_controlled_congested","respiratory_failure"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id)));
chk('one dose alone never leaves the arrival phase before the clock does',
    JSON.stringify(fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),1200).phaseSeq.map(p=>p.id))===
    '["presentation","respiratory_failure"]',
    JSON.stringify(fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),1200).phaseSeq.map(p=>p.id)));

section('the respiratory failure phase reads differently depending on how it was reached');
/* One vitals block per phase, and two routes into this one. The authored rate is the
   untreated patient's; a rate-controlled patient reaching the same phase carries a
   guarded effect so the monitor does not jump from 108 to 166 on a man with nodal
   blockade running. */
st=fold([],300);
chk('untreated, the rate rises as he tires',st.vitals.heart_rate===166,String(st.vitals.heart_rate));
chk('one dose on board, the same phase reads 144',
    fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),500).vitals.heart_rate===144,
    String(fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),500).vitals.heart_rate));
st=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus']]),500);
chk('rate-controlled, he reaches the same phase',st.phase==='respiratory_failure',st.phase);
chk('and the monitor reads about 130 rather than 166',st.vitals.heart_rate===131,
    String(st.vitals.heart_rate));
chk('the partial effect is invisible where the phase carries the rate',
    fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus']]),90)
      .vitals.heart_rate===108,
    String(fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus']]),90)
      .vitals.heart_rate));

section('fairness: the nurse warns before the clock');
st=fold([],1200);
const nivPrompt=st.promptFires.find(p=>p.id==='non_invasive_positive_pressure_ventilation');
chk('positive pressure is prompted before the 240 second deadline',
    !!nivPrompt&&nivPrompt.t<=220,nivPrompt?String(nivPrompt.t):'never');
const esc=st.promptFires.filter(p=>p.id==='non_invasive_positive_pressure_ventilation'&&
                                   p.level===2);
/* It fires twice in a do-nothing run, once in the arrival phase and once again after
   the phase turns over, because prompts are rescheduled on entry to every phase where
   the action is still critical. What matters is the first one, inside the window the
   deterioration is measured against. */
chk('the escalation survives the per-phase prompt cap, inside the deadline',
    esc.some(p=>p.t<240),JSON.stringify(esc.map(p=>p.t)));
const trajInPrompt=st.nurse.filter(n=>n.kind==='prompt')
  .some(n=>/dropping|crashing|getting worse|deteriorat|wearing out|falling/i.test(n.text));
chk('no prompt implies a trajectory',!trajInPrompt);
chk('the deterioration narration is on its own kind, not a prompt',
    st.nurse.some(n=>n.kind==='deterioration'));

/* Physician decision, 5 October 2026 (AFRVR-08). A crystalloid bolus no longer halts the
   case. It has a consequence the learner must rescue, by every route to the same act. */
section('a fluid bolus has a consequence instead of a halt, by every route');
for(const bag of ['normal_saline_1l_bolus','normal_saline_500ml_bolus',
                  'lactated_ringer_s_1l_bolus','lactated_ringer_s_500ml_bolus','d5_ns_bolus']){
  const s=fold(mk([[1,'insert_iv'],[5,bag]]),30);
  chk(bag+' does not halt the case',!s.halted,s.phase);
  chk(bag+' before the mask tips him into respiratory failure',s.phase==='respiratory_failure',s.phase);
  chk(bag+' is scored discouraged',s.discouragedTaken.has(bag)||s.discouragedTaken.has('normal_saline_1l_bolus'));
}
chk('nothing in this case is tagged harmful',
    !CASE.case_actions.some(a=>a.tag.some(r=>r.value==='harmful')));
st=fold(mk([[1,'insert_iv'],[5,'normal_saline_1l_bolus']]),30);
chk('the nurse says what the fluid did',
    st.nurse.some(n=>/fluid has gone straight to his chest/i.test(n.text)));
chk('in respiratory failure after fluid the saturation reads 76',
    st.vitals.oxygen_saturation===76,String(st.vitals.oxygen_saturation));
st=fold(mk([[1,'insert_iv'],[5,'normal_saline_1l_bolus'],
            [30,'non_invasive_positive_pressure_ventilation']]),120);
chk('and the mask still rescues him',st.phase==='breathing_supported',st.phase);
chk('on the mask he reads 90, six under where he would have been',
    st.vitals.oxygen_saturation===90,String(st.vitals.oxygen_saturation));
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [80,'normal_saline_1l_bolus']]),85);
chk('a bolus on the mask does not move the saturation on the click',
    st.vitals.oxygen_saturation===96,String(st.vitals.oxygen_saturation));
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [80,'normal_saline_1l_bolus']]),100);
chk('ten seconds later it has cost six points',
    st.phase==='breathing_supported'&&st.vitals.oxygen_saturation===90,
    st.phase+' '+st.vitals.oxygen_saturation);
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus'],[5,'digoxin_bolus'],[80,'normal_saline_1l_bolus']]),120);
chk('the same bolus once stabilized changes nothing on the monitor',
    !st.halted&&st.phase==='stabilized'&&st.vitals.oxygen_saturation===97,
    st.phase+' '+st.vitals.oxygen_saturation);
st=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus'],[30,'normal_saline_1l_bolus']]),45);
chk('fluid in the rate-controlled, congested phase also tips him over',
    st.phase==='respiratory_failure',st.phase);

section('prerequisites');
st=fold(mk([[1,'digoxin_bolus']]),10);
chk('an intravenous drug is blocked without access',
    st.blocked.length===1&&!st.flags.has('rate_control_given'));
st=fold(mk([[1,'intraosseous_line'],[2,'digoxin_bolus']]),10);
chk('an intraosseous needle satisfies the same requirement',
    st.flags.has('rate_control_given')&&st.blocked.length===0);
st=fold(mk([[1,'insert_iv'],[2,'synchronized_cardioversion']]),10);
chk('cardioversion is blocked in a patient who is awake',
    st.blocked.some(b=>b.id==='synchronized_cardioversion')&&!st.flags.has('cardioverted'));
st=fold(mk([[1,'insert_iv'],[2,'etomidate_bolus'],[3,'synchronized_cardioversion']]),10);
chk('and permitted once he has been sedated',st.flags.has('cardioverted'));
st=fold(mk([[1,'insert_iv'],[2,'intubate_rapid_sequence']]),10);
chk('intubation is blocked without sedation and paralysis',!st.flags.has('intubated'));
st=fold(mk([[1,'insert_iv'],[2,'etomidate_bolus'],[3,'rocuronium_bolus'],
            [4,'intubate_rapid_sequence'],[5,'non_invasive_positive_pressure_ventilation']]),20);
chk('the mask is blocked once there is a tube',
    st.blocked.some(b=>b.id==='non_invasive_positive_pressure_ventilation')&&!st.flags.has('on_niv'));

section('coverage groups satisfy the critical action they cover');
/* Two sets, and the difference between them is the whole point. `satisfied` is what has
   been accomplished and is what the debrief scores; `taken` is which buttons were
   pressed and is what the action grid draws as used. Pressing metoprolol used to light
   digoxin up as well, which told the resident they had given a drug they had not. */
/* Physician decision, 5 October 2026 (AFRVR-04). Metoprolol is its own action. It
   satisfies the critical rate-control action only when it is given after positive
   pressure is on, and it is discouraged before that. */
{
  const before=fold(mk([[1,'insert_iv'],[2,'metoprolol_bolus'],[4,'metoprolol_bolus']]),60);
  chk('metoprolol before the mask still slows him',before.phase==='rate_controlled_congested',before.phase);
  chk('metoprolol before the mask is discouraged',before.discouragedTaken.has('metoprolol_bolus'));
  chk('metoprolol before the mask does NOT satisfy critical rate control',
      !before.satisfied.has('digoxin_bolus'));
  const late=fold(mk([[1,'insert_iv'],[2,'metoprolol_bolus'],
                      [10,'non_invasive_positive_pressure_ventilation'],[20,'metoprolol_bolus']]),60);
  chk('a dose given after the mask does satisfy it',late.satisfied.has('digoxin_bolus'));
  const after=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                       [3,'metoprolol_bolus'],[5,'metoprolol_bolus']]),60);
  chk('metoprolol after the mask is not discouraged',!after.discouragedTaken.has('metoprolol_bolus'));
  chk('metoprolol is no longer a covered sibling',!A['metoprolol_bolus'].covered_by);
  chk('the rate-control prompt is not repeated once metoprolol has satisfied it',
      !fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                [3,'metoprolol_bolus']]),1200).promptFires.some(p=>p.id==='digoxin_bolus'));
}
for(const agent of ['amiodarone_bolus_infusion','metoprolol_bolus']){
  const s=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                   [3,agent],[5,agent]]),60);
  chk(agent+' reaches the stabilized phase',s.phase==='stabilized',s.phase);
  chk(agent+' satisfies the covering critical action',s.satisfied.has('digoxin_bolus'));
  chk(agent+' does NOT mark the covering button as pressed',!s.taken.has('digoxin_bolus'));
  chk(agent+' marks its own button as pressed',s.taken.has(agent));
  chk(agent+' keeps its own button name',A[agent].name!==A['digoxin_bolus'].name);
}
for(const ac of ['enoxaparin','heparin_bolus_drip']){
  const s=fold(mk([[1,'insert_iv'],[2,ac]]),20);
  chk(ac+' anticoagulates',s.flags.has('anticoagulated'));
  chk(ac+' satisfies the covering critical action',s.satisfied.has('apixaban'));
  chk(ac+' does NOT mark the apixaban button as pressed',!s.taken.has('apixaban'));
}
/* And the covering action itself still behaves normally when it is the one pressed. */
{
  const s=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),20);
  chk('pressing digoxin marks digoxin and nothing else',
      s.taken.has('digoxin_bolus')&&!s.taken.has('metoprolol_bolus')&&
      !s.taken.has('amiodarone_bolus_infusion'));
}
chk('the debrief names the act rather than one of its drugs',
    !!A['digoxin_bolus'].expectation_label&&
    /rate control/i.test(A['digoxin_bolus'].expectation_label));

section('results freeze, and trend where the case authors a trend');
st=fold(mk([[1,'insert_iv'],[2,'magnesium_level']]),30);
chk('the magnesium resolves from the case, not a catalog default',
    st.orders.magnesium_level[0].source==='case',st.orders.magnesium_level[0].source);
chk('and it is low',st.orders.magnesium_level[0].value.components[0].value==='1.6');
st=fold(mk([[1,'insert_iv'],[2,'magnesium_level'],[3,'magnesium_sulfate_bolus'],
            [20,'magnesium_level']]),40);
const mags=(st.orders.magnesium_level||[]).map(o=>o.value.components[0].value);
chk('a repeat after replacement reads corrected',
    mags.length===2&&mags[0]==='1.6'&&mags[1]==='2.1',mags.join(' then '));
st=fold(mk([[1,'insert_iv'],[2,'ecg_12_lead'],[3,'non_invasive_positive_pressure_ventilation'],
            [4,'digoxin_bolus']]),120);
chk('a tracing taken before rate control still reads 160 when it is read afterwards',
    /rate approximately 160/.test(st.orders.ecg_12_lead[0].value.report));
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus'],[100,'ecg_12_lead']]),140);
chk('a tracing after ONE dose reads about 140, not 105',
    /rate approximately 140/.test(st.orders.ecg_12_lead[0].value.report),
    st.orders.ecg_12_lead[0].value.report.slice(0,60));
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus'],[40,'digoxin_bolus'],[100,'ecg_12_lead']]),140);
chk('a repeat tracing after the second dose reads about 105',
    /rate approximately 105/.test(st.orders.ecg_12_lead[0].value.report));
chk('the ventilated phase has a tracing of its own',
    /rate approximately 118/.test(
      fold(mk([[1,'insert_iv'],[2,'etomidate_bolus'],[3,'rocuronium_bolus'],
               [4,'intubate_rapid_sequence'],[6,'ecg_12_lead']]),40)
        .orders.ecg_12_lead[0].value.report));

section('the consultants do not discuss studies that have not come back');
st=fold(mk([[1,'insert_iv'],[2,'consult_cardiology']]),10);
const cardio=st.readouts.filter(r=>r.key==='consult_cardiology').pop().body;
chk('cardiology asks for the tracing and the probe before advising',
    /twelve-lead/i.test(cardio)&&/left ventricle/i.test(cardio));
chk('and says nothing about an ejection fraction nobody has measured',
    !/thirty to thirty-five/i.test(cardio));
st=fold(mk([[1,'insert_iv'],[2,'ecg_12_lead'],[3,'ultrasound_cardiac'],
            [30,'consult_cardiology']]),40);
const cardio2=st.readouts.filter(r=>r.key==='consult_cardiology').pop().body;
chk('with both in hand it names the drug to avoid',/diltiazem/i.test(cardio2));
chk('and warns that one dose will not be enough',/twice|another dose|second/i.test(cardio2));
/* And it says something different once a dose is in, and different again once two are. */
const cardioAfter=n=>{
  const steps=[[1,'insert_iv'],[2,'ecg_12_lead'],[3,'ultrasound_cardiac']];
  for(let i=0;i<n;i++) steps.push([5+i,'digoxin_bolus']);
  steps.push([30,'consult_cardiology']);
  return fold(mk(steps),40).readouts.filter(r=>r.key==='consult_cardiology').pop().body;
};
chk('after one dose it says a partial response asks for more of the same strategy',
    /partial response/i.test(cardioAfter(1))&&/same strategy/i.test(cardioAfter(1)));
/* Physician decision, 5 October 2026 (AFRVR-05): nobody advises pushing digoxin twice. */
chk('and it does not advise pushing digoxin again at once',
    /digoxin is loaded over hours/i.test(cardioAfter(1))&&!/give it again/i.test(cardioAfter(1)));
chk('the redose prompt no longer offers another dose of the same drug',
    !/draw up another dose/i.test(FU['second_rate_control_dose'].nurse_prompt));
chk('and warns against switching to the calcium channel blocker',
    /diltiazem/i.test(cardioAfter(1)));
chk('and says to reassess before a third',/reassess before a third/i.test(cardioAfter(1)));
chk('after two doses it moves on to disposition and anticoagulation',
    /anticoagulated/i.test(cardioAfter(2))&&/echocardiogram/i.test(cardioAfter(2)));
chk('and it does not ask for a rate he no longer has',
    !/still up around 140/i.test(cardioAfter(2)));

section('the patient cannot give a history once he is intubated');
st=fold(mk([[1,'insert_iv'],[2,'etomidate_bolus'],[3,'rocuronium_bolus'],
            [4,'intubate_rapid_sequence'],{seq:9,t:10,kind:'interview',topic:'onset',q:'when did this start'}]),20);
const ans=st.readouts.filter(r=>r.kind==='speech').pop().body;
chk('the global alertness rule wins over the topic answer',/intubated and sedated/i.test(ans),ans);

section('the beat is irregularly irregular, in every phase he is still in the rhythm');
const RH_OF = Object.fromEntries(CASE.phases.map(p => [p.id, p.rhythm]));
chk('he arrives in it',RH_OF.presentation==='irregularly_irregular',String(RH_OF.presentation));
chk('rate control does not convert him',
    RH_OF.rate_controlled_congested==='irregularly_irregular'&&
    RH_OF.stabilized==='irregularly_irregular',
    RH_OF.rate_controlled_congested+', '+RH_OF.stabilized);
chk('he is handed over still in it',RH_OF.case_complete==='irregularly_irregular',
    String(RH_OF.case_complete));
chk('every non-terminal phase is irregular',
    CASE.phases.filter(p=>!p.terminal).every(p=>p.rhythm==='irregularly_irregular'),
    CASE.phases.filter(p=>!p.terminal&&p.rhythm!=='irregularly_irregular')
      .map(p=>p.id).join(', '));
/* 5 October 2026: nothing halts this case any more, so it authors no halted phase. */
chk('there is no halted phase',RH_OF.halted===undefined,String(RH_OF.halted));

/* The rates this case actually authors, against the model that will sound them. The
   floor has to clear the lub-dub gap at the fastest rate in the case, and the average
   has to be the rate on the monitor at every one of them. */
if (typeof AUDIO !== 'undefined' && AUDIO.intervalModel) {
  for (const ph of CASE.phases) {
    if (ph.rhythm !== 'irregularly_irregular') continue;
    const mean = 60000 / ph.vitals.heart_rate;
    let sum = 0, lo = Infinity;
    for (let i = 0; i < 40000; i++) {
      const v = AUDIO.intervalModel(mean, 'irregularly_irregular');
      sum += v; if (v < lo) lo = v;
    }
    chk(`${ph.id} at ${ph.vitals.heart_rate} bpm averages the authored rate`,
        Math.abs(60000 / (sum / 40000) - ph.vitals.heart_rate) < 1,
        (60000 / (sum / 40000)).toFixed(2));
    chk(`${ph.id}: no two beats closer than the lub-dub gap`, lo > 200, lo.toFixed(1));
  }
}

section('handoff');
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus'],[5,'digoxin_bolus']])
        .concat([{seq:9,t:100,actionId:'handoff_submit',
                  payload:{disposition:'icu_or_ccu',diagnosis:PROTO.correctDxId}}]),140);
chk('handoff completes the case',st.phase==='case_complete'&&st.complete);
chk('the correct diagnosis resolves to a catalog id',
    PROTO.correctDxId==='dx_atrial_fibrillation_with_rapid_ventricular_response',
    String(PROTO.correctDxId));
chk('the other half of the formulation is marked defensible rather than wrong',
    (PROTO.altDxDefensible||[])
      .includes('dx_acute_decompensated_heart_failure_with_reduced_ejection_fraction'),
    JSON.stringify(PROTO.altDxDefensible));

/* ---- physician decisions of 5 October 2026 ---- */
section('the first dose takes ten seconds to show (AFRVR-19)');
{
  const base=[[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],[20,'digoxin_bolus']];
  chk('five seconds after the first dose the rate has not moved',
      fold(mk(base),25).vitals.heart_rate===152,String(fold(mk(base),25).vitals.heart_rate));
  chk('ten seconds after it, the partial fall shows',
      fold(mk(base),31).vitals.heart_rate===130,String(fold(mk(base),31).vitals.heart_rate));
}
section('a second dose of diltiazem costs more pressure (AFRVR-23)');
{
  const one=fold(mk([[1,'insert_iv'],[2,'diltiazem_bolus']]),30);
  chk('one dose: 132 becomes 112',one.vitals.systolic_bp===112,String(one.vitals.systolic_bp));
  const two=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                     [3,'diltiazem_bolus'],[20,'diltiazem_bolus']]),60);
  chk('two doses control the rate',two.phase==='stabilized',two.phase);
  chk('and the pressure is 94 over 59, ten and five lower than after one',
      two.vitals.systolic_bp===94&&two.vitals.diastolic_bp===59,
      two.vitals.systolic_bp+'/'+two.vitals.diastolic_bp);
  const mixed=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                       [3,'diltiazem_bolus'],[20,'digoxin_bolus']]),60);
  chk('diltiazem then digoxin does not take the extra fall',
      mixed.vitals.systolic_bp===104,String(mixed.vitals.systolic_bp));
}
section('without the mask, rate control buys two minutes, not four (AFRVR-02)');
{
  const s=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus']]),200);
  chk('he tires 120 seconds after the rate comes down',
      JSON.stringify(s.phaseSeq.map(p=>p.id+'@'+p.t))===
        '["presentation@0","rate_controlled_congested@14","respiratory_failure@134"]',
      JSON.stringify(s.phaseSeq.map(p=>p.id+'@'+p.t)));
}
section('the handover screen shows the monitor as it was (AFRVR-32)');
{
  const good=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                      [3,'digoxin_bolus'],[5,'digoxin_bolus'],[100,'handoff_submit']]),120);
  chk('handed over stabilized on the mask, it reads 97',
      good.phase==='case_complete'&&good.vitals.oxygen_saturation===97,
      good.phase+' '+good.vitals.oxygen_saturation);
  const bad=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus'],[4,'digoxin_bolus'],[60,'handoff_submit']]),80);
  chk('handed over rate controlled with no mask, it reads 86 at a rate of 108',
      bad.vitals.oxygen_saturation===86&&bad.vitals.heart_rate===108,
      bad.vitals.oxygen_saturation+' '+bad.vitals.heart_rate);
  const nothing=fold(mk([[300,'handoff_submit']]),320);
  chk('handed over in respiratory failure, it reads 82',
      nothing.vitals.oxygen_saturation===82,String(nothing.vitals.oxygen_saturation));
}
section('scoring changes');
chk('IV access is recommended, not critical (AFRVR-12)',
    !fold([],5).expected.has('insert_iv')&&fold([],5).recommendedExpected.has('insert_iv'));
chk('the monitor stays critical',fold([],5).expected.has('attach_monitor'));
chk('nitroprusside is discouraged (AFRVR-25)',
    fold(mk([[1,'insert_iv'],[2,'nitroprusside_drip']]),10).discouragedTaken.has('nitroprusside_drip'));
chk('the anticoagulation note covers bleeding risk (AFRVR-26)',
    /bleeding risk/i.test(A['apixaban'].debrief_note));
