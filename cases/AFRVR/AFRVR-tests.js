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
                [8,'furosemide_40_mg_iv'],[10,'digoxin_bolus'],[12,'apixaban']]),120);
chk('reaches the stabilised phase',st.phase==='stabilized',st.phase);
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
                      [3,'digoxin_bolus']]),200);
const withDiur=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                        [3,'digoxin_bolus'],[4,'furosemide_40_mg_iv']]),200);
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

section('rate control takes a minute, and the case says so');
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus']]),40);
chk('nothing has changed 37 seconds after the drug',st.phase==='breathing_supported',st.phase);
chk('and the rate on the monitor is still 152',st.vitals.heart_rate===152,
    String(st.vitals.heart_rate));
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus']]),70);
chk('the phase turns over at sixty seconds with no further action',st.phase==='stabilized',st.phase);
chk('the rate on the monitor is now 104',st.vitals.heart_rate===104,String(st.vitals.heart_rate));
chk('the delayed transition is recorded for the debrief',
    st.timeFires.some(f=>f.to==='stabilized'&&f.after===60));

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
st=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),1200);
chk('rate control alone still deteriorates, through the congested phase',
    st.phase==='respiratory_failure',st.phase);
chk('and it went the long way round',
    JSON.stringify(st.phaseSeq.map(p=>p.id))===
    '["presentation","rate_controlled_congested","respiratory_failure"]',
    JSON.stringify(st.phaseSeq.map(p=>p.id)));

section('the respiratory failure phase reads differently depending on how it was reached');
/* One vitals block per phase, and two routes into this one. The authored rate is the
   untreated patient's; a rate-controlled patient reaching the same phase carries a
   guarded effect so the monitor does not jump from 108 to 166 on a man with nodal
   blockade running. */
st=fold([],300);
chk('untreated, the rate rises as he tires',st.vitals.heart_rate===166,String(st.vitals.heart_rate));
st=fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),500);
chk('rate-controlled, he reaches the same phase',st.phase==='respiratory_failure',st.phase);
chk('and the monitor reads about 130 rather than 166',st.vitals.heart_rate===131,
    String(st.vitals.heart_rate));
chk('the effect is invisible in every other phase',
    fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),90).vitals.heart_rate===108,
    String(fold(mk([[1,'insert_iv'],[2,'digoxin_bolus']]),90).vitals.heart_rate));

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

section('harmful halts, and every route to them');
for(const bag of ['normal_saline_1l_bolus','normal_saline_500ml_bolus',
                  'lactated_ringer_s_1l_bolus','lactated_ringer_s_500ml_bolus']){
  const s=fold(mk([[1,'insert_iv'],[5,bag]]),20);
  chk(bag+' halts the case',s.halted&&s.phase==='halted',s.phase);
  chk(bag+' carries a halt reason',!!(s.halted&&s.halted.reason&&s.halted.reason.length>20));
}
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
            [3,'digoxin_bolus'],[80,'normal_saline_1l_bolus']]),120);
chk('the same bolus once stabilised is discouraged rather than lethal',
    !st.halted&&st.phase==='stabilized',st.phase);
st=fold(mk([[1,'insert_iv'],[400,'normal_saline_1l_bolus']]),500);
chk('a harmful action still halts after a deadline has passed',st.phase==='halted',st.phase);

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
for(const agent of ['amiodarone_bolus_infusion','metoprolol_bolus']){
  const s=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],
                   [3,agent]]),90);
  chk(agent+' reaches the stabilised phase',s.phase==='stabilized',s.phase);
  chk(agent+' is credited with the covering critical action',s.taken.has('digoxin_bolus'));
  chk(agent+' keeps its own button name',A[agent].name!==A['digoxin_bolus'].name);
}
for(const ac of ['enoxaparin','heparin_bolus_drip']){
  const s=fold(mk([[1,'insert_iv'],[2,ac]]),20);
  chk(ac+' anticoagulates',s.flags.has('anticoagulated'));
  chk(ac+' is credited with the covering critical action',s.taken.has('apixaban'));
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
chk('a repeat tracing after rate control reads about 105',
    /rate approximately 105/.test(st.orders.ecg_12_lead[0].value.report));

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

section('the patient cannot give a history once he is intubated');
st=fold(mk([[1,'insert_iv'],[2,'etomidate_bolus'],[3,'rocuronium_bolus'],
            [4,'intubate_rapid_sequence'],{seq:9,t:10,kind:'interview',topic:'onset',q:'when did this start'}]),20);
const ans=st.readouts.filter(r=>r.kind==='speech').pop().body;
chk('the global alertness rule wins over the topic answer',/intubated and sedated/i.test(ans),ans);

section('handoff');
st=fold(mk([[1,'insert_iv'],[2,'non_invasive_positive_pressure_ventilation'],[3,'digoxin_bolus']])
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
