/* ============================================================
   Engine. Case-agnostic: no clinical knowledge, no case names.
   Mirrors system-design-v2.md section 12 components.

   v2 changes: the action surface is the action catalog, not the case. A case
   action binds onto a catalog entry and supplies the tag, prompt, prerequisites
   and debrief note. Everything else is inert. Study results resolve case first,
   catalog default second, nothing third.
   ============================================================ */

/* ---------- condition language (section 4) ---------- */
function tokenize(s){
  return s.replace(/\(/g,' ( ').replace(/\)/g,' ) ').trim().split(/\s+/).filter(Boolean);
}
function parseCond(s){
  if(s===null||s===undefined||s==='') return {t:'true'};
  const p={i:0,k:tokenize(s)};
  const n=pExpr(p);
  if(p.i<p.k.length) throw new Error('trailing tokens in condition: '+s);
  return n;
}
function pExpr(p){ let a=pTerm(p); while(p.k[p.i]==='OR'){p.i++; a={t:'or',a,b:pTerm(p)};} return a; }
function pTerm(p){ let a=pFac(p); while(p.k[p.i]==='AND'){p.i++; a={t:'and',a,b:pFac(p)};} return a; }
function pFac(p){
  if(p.k[p.i]==='NOT'){p.i++; return {t:'not',a:pFac(p)};}
  if(p.k[p.i]==='('){p.i++; const e=pExpr(p); if(p.k[p.i]!==')') throw new Error('unbalanced parens'); p.i++; return e;}
  return pAtom(p);
}
function pAtom(p){
  const k=p.k, i=p.i;
  if(k[i]==='phase'&&k[i+1]==='is'){p.i=i+3; return {t:'phase',v:k[i+2]};}
  if(k[i]==='flag'&&k[i+2]==='set'){p.i=i+3; return {t:'flag',v:k[i+1]};}
  if(k[i]==='study'&&k[i+2]==='ordered'){p.i=i+3; return {t:'ordered',v:k[i+1]};}
  if(k[i]==='study'&&k[i+2]==='resulted'){p.i=i+3; return {t:'resulted',v:k[i+1]};}
  if(k[i]==='action'&&k[i+2]==='taken'){p.i=i+3; return {t:'taken',v:k[i+1]};}
  /* The catalog ships prerequisites written as "flag F" without the trailing
     keyword, which section 4 does not permit. Accept it here so the prototype can
     run, and record it so the interface can say the grammar is being bent. */
  if(k[i]==='flag'&&(k[i+2]===undefined||k[i+2]==='AND'||k[i+2]==='OR'||k[i+2]===')')){
    LOOSE_CONDITIONS.add(p.k.join(' '));
    p.i=i+2; return {t:'flag',v:k[i+1]};
  }
  throw new Error('unparseable atom near: '+k.slice(i,i+3).join(' '));
}
const LOOSE_CONDITIONS=new Set();

function evalCond(n,st){
  switch(n.t){
    case 'true':     return true;
    case 'and':      return evalCond(n.a,st)&&evalCond(n.b,st);
    case 'or':       return evalCond(n.a,st)||evalCond(n.b,st);
    case 'not':      return !evalCond(n.a,st);
    case 'phase':    return st.phase===n.v;
    case 'flag':     return st.flags.has(n.v);
    case 'ordered':  return st.ordered.has(n.v);
    case 'resulted': return st.resulted.has(n.v);
    /* `satisfied` rather than `taken`: a case that has declared two catalog entries to
       be the same act through also_covers is asserting exactly that, so a condition
       naming either of them has to see the other. `taken` stays the set of buttons the
       resident actually pressed and is what the interface reads. */
    /* `satisfied` falling back to `taken`. A hand-built state -- the test harness, or
       anything outside the fold that wants to resolve one rule -- has no reason to know
       about a second set, and `satisfied` is always a superset of `taken`, so degrading
       to it is exactly right rather than merely safe. */
    case 'taken':    return (st.satisfied||st.taken).has(n.v);
  }
  return false;
}
const _ccache=new Map();
function cond(s){ if(!_ccache.has(s)) _ccache.set(s,parseCond(s)); return _ccache.get(s); }
function test(s,st){ return evalCond(cond(s===null?'':s),st); }

/* resolver: first match wins, unconditional default last */
function resolve(rules,st){
  for(const r of rules){ if(r.when===null||r.when===undefined||test(r.when,st)) return r.value; }
  return null;
}

/* ---------- case selection and the catalog merge ----------
   PROTO is assembled here rather than at build time so that every case shares one
   copy of the catalog. Section 6.2: catalog defaults apply unless the case waives
   them, and case prerequisites are additional rather than a replacement. */
let CASE=null, PROTO=null, PACK=null;
let PHASE={}, ACT={}, FU={}, CK=null, CONTENT={}, GENERAL_STATUS=null;

function orphanCategory(eff){
  if(eff.indexOf('exam_')===0) return 'exam';
  if(eff.indexOf('consult_')===0) return 'consultant';
  if(/^(labs_|echo_|cxr|ct_|pocus)/.test(eff)) return 'investigation';
  if(eff.indexOf('interview_topic_')===0) return 'interview';
  if(eff==='handoff_submit') return 'handoff';
  return 'stabilization';
}

function mergeAction(eff, base, caseAct, extra){
  base = base||{}; caseAct = caseAct||{};
  const waived=(caseAct.prerequisite_overrides||[]).map(w=>w.waived).filter(Boolean);
  const prereqs=[], seen=new Set();
  for(const p of (base.default_prerequisites||[])){
    if(seen.has(p.when)||waived.indexOf(p.when)>=0) continue;
    seen.add(p.when); prereqs.push(Object.assign({},p,{origin:'catalog_default'}));
  }
  for(const p of (caseAct.prerequisites||[])){
    if(seen.has(p.when)) continue;
    seen.add(p.when); prereqs.push(Object.assign({},p,{origin:'case'}));
  }
  const origins=new Set(prereqs.map(p=>p.origin));
  const flags=[...new Set((caseAct.flags_set||[]).concat(base.flags_set_default||[]))];
  const rec={
    id:eff,
    catalog_id:base.id||null,
    name:((extra&&extra.coveredBy)?null:caseAct.display_name)||base.name||eff.replace(/_/g,' '),
    tab:(extra&&extra.tab)||base.tab,
    group:(extra&&extra.group)||base.group,
    category:base.category||(extra&&extra.category)||orphanCategory(eff),
    state_changing:base.state_changing!==undefined?base.state_changing
                  :(caseAct.state_changing!==undefined?caseAct.state_changing:true),
    turnaround_class:base.turnaround_class||null,
    turnaround_override:caseAct.turnaround_override_seconds||null,
    narration_template:base.narration_template||(extra&&extra.narration_template)||null,
    dose_required:!!base.dose_required,
    persistent:!!base.persistent,
    repeatable:base.repeatable!==false,
    prerequisites:prereqs,
    prerequisite_source:origins.size>1?'mixed':(prereqs.length?prereqs[0].origin:'none'),
    prerequisite_waived:waived,
    flags_set:flags,
    default_result:base.default_result||null,
    /* Catalog capability: this act is what puts numbers on the monitor. */
    reveals_vitals:!!base.reveals_vitals,
    bound:!!caseAct.catalog_id,
    orphan:!!(extra&&extra.orphan),
    shadowed:(extra&&extra.shadowed)||[],
    covered_by:(extra&&extra.coveredBy)||null
  };
  if(caseAct.catalog_id){
    rec.tag=caseAct.tag;
    rec.prompt=caseAct.prompt;
    rec.debrief_note=caseAct.debrief_note;
    rec.references=caseAct.references;
    rec.halt_reason=caseAct.halt_reason;
    rec.follow_ups_triggered=caseAct.follow_ups_triggered;
    rec.vital_effects=caseAct.vital_effects;
    /* Optional. Where a case action covers several catalog entries the debrief has to
       name the act rather than one of its routes, or a resident who gave amiodarone is
       told they completed 'Digoxin bolus'. The button keeps the catalog's own name;
       only the critical-action list uses this. */
    rec.expectation_label=caseAct.expectation_label;
    /* Authoring 9.1 has always said a case may override the catalog's narration where
       the standard line would be wrong or confusing. Nothing read it, so the promise was
       not kept. Both this and nurse_alert below are borrowed by a covered sibling, so a
       line authored on a coverage group speaks for every route to the act. */
    rec.narration_override=caseAct.narration_override;
    /* A line the nurse volunteers after the action's own narration. It is rendered red
       and it goes into the running chart, because it is the kind of thing a resident has
       to be able to find again: "these agents take time to work" is useless if it has
       scrolled off the nurse's line by the time they wonder whether the drug failed. */
    rec.nurse_alert=caseAct.nurse_alert;
    /* Flags granted only on the Nth administration of an act. Flags are otherwise
       binary and permanent and section 15 tells authors not to build cases that depend
       on redosing, which is true of everything EXCEPT the one thing this expresses: an
       act that has to be repeated before it works. Counting is per counter rather than
       per action id, so a case can decide whether two doses of one drug and one dose
       each of two drugs are the same thing. */
    rec.flags_set_repeat=caseAct.flags_set_repeat;
    rec.flags_set_timed=caseAct.flags_set_timed;
  }
  return rec;
}

function buildActions(pack){
  const caseActs={};
  pack.case.case_actions.forEach(a=>caseActs[a.catalog_id]=a);
  const hiddenBy={};   // case id bound to a catalog entry another case action already holds
  Object.keys(pack.shadowed||{}).forEach(h=>{
    const owner=pack.shadowed[h];
    (hiddenBy[owner]=hiddenBy[owner]||[]).push(h);
  });
  const out={};
  for(const cid in SHARED.actionsBase){
    const eff=(pack.bindings||{})[cid]||cid;
    /* covers: this catalog entry keeps its own id and name, but takes the case
       fields of another action, so a tag applies to every route to the same act. */
    const via=(pack.covers||{})[cid];
    const ca=caseActs[eff]||(via?caseActs[via]:null);
    out[eff]=mergeAction(eff, SHARED.actionsBase[cid], ca,
                         {shadowed:hiddenBy[eff]||[], coveredBy:via||null});
  }
  for(const eff in (pack.orphans||{})){
    const o=pack.orphans[eff];
    out[eff]=mergeAction(eff, null, caseActs[eff], Object.assign({orphan:true},o));
  }
  return out;
}

/* let-bindings inside an eval are not visible to the caller, so the test harness
   reads them through this instead of touching the variables. */
function engineState(){ return {CASE,PROTO,PACK,PHASE,ACT,FU,CK,CONTENT,GENERAL_STATUS}; }

function selectCase(ref){
  PACK = typeof ref==='number' ? CASES[ref]
       : CASES.find(c=>c.prefix===ref||c.id===ref);
  if(!PACK) throw new Error('no such case: '+ref);
  CASE = PACK.case;
  PROTO = Object.assign({}, SHARED, {
    actions: buildActions(PACK),
    bindingCounts: PACK.bindingCounts,
    shadowed: PACK.shadowed,
    phaseShort: PACK.phaseShort,
    traps: PACK.traps,
    dispOrder: PACK.dispOrder,
    dispLabels: PACK.dispLabels,
    correctDxId: PACK.correctDxId,
    correctDxExplanation: PACK.correctDxExplanation,
    altDx: PACK.altDx,
    altDxDefensible: PACK.altDxDefensible||[],
    promptCap: PACK.promptCap,
    buildNotes: PACK.buildNotes
  });
  PHASE={}; CASE.phases.forEach(p=>PHASE[p.id]=p);
  ACT=PROTO.actions;
  FU={}; (CASE.follow_ups||[]).forEach(f=>FU[f.id]=f);
  CK=CASE.content_keys;
  CONTENT={};
  ['exam','labs','imaging','consultants'].forEach(g=>{
    Object.keys(CK[g]||{}).forEach(k=>{
      if(k==='authoring_note') return;
      const v=CK[g][k];
      CONTENT[k]=Array.isArray(v)?v:v.rules;
    });
  });
  GENERAL_STATUS = CK.general_status ? CK.general_status.rules : null;
  return PACK;
}

/* The line above the exam list. Case rules first, catalog default second. */
function generalStatus(st){
  if(GENERAL_STATUS){
    const v=resolve(GENERAL_STATUS,st);
    if(v) return {value:v,source:'case'};
  }
  return {value:SHARED.generalStatusDefault,source:'catalog_default'};
}

const catOf   = id => (ACT[id]||{}).category;
const IS_STUDY   = id=>catOf(id)==='investigation';
const IS_EXAM    = id=>catOf(id)==='exam';
const IS_CONSULT = id=>catOf(id)==='consultant';

function turnaround(id){
  const a=ACT[id]||{};
  if(a.turnaround_override) return a.turnaround_override;
  return PROTO.turnaround[a.turnaround_class]!==undefined
       ? PROTO.turnaround[a.turnaround_class] : PROTO.turnaround.lab;
}
function tagOf(id,st){
  const a=ACT[id];
  if(!a||!a.tag) return 'neutral';
  return resolve(a.tag,st)||'neutral';
}
function stateChanging(id){
  const a=ACT[id];
  if(!a) return false;
  if(IS_EXAM(id)) return false;
  if(catOf(id)==='interview') return false;
  return a.state_changing!==false;
}
function dispName(id){ return (ACT[id]&&ACT[id].name)||id.replace(/_/g,' '); }

/* ---------- result resolution: case, then catalog default, then nothing ------ */
function resolveResult(id,snap){
  if(CONTENT[id]) return {value:resolve(CONTENT[id],snap),source:'case'};
  const d=(ACT[id]||{}).default_result;
  if(d) return {value:d,source:'catalog_default'};
  return {value:null,source:'none'};
}

/* ---------- the fold (section 5.2) ---------- */
function snapshot(st){
  return {phase:st.phase,flags:new Set(st.flags),ordered:new Set(st.ordered),
          resulted:new Set(st.resulted),taken:new Set(st.taken),
          satisfied:new Set(st.satisfied)};
}
/* difficultyMultiplier scales every nurse prompt deadline, including escalations
   and follow-up prompts. It scales nothing else: result turnaround, transitions and
   tags are unaffected, so the medicine is identical in both modes and only the
   amount of help changes.

   v0.6: this now also means time-guarded transition deadlines are NOT scaled. Scaling
   them would make hard mode more forgiving (slower deterioration) at the same time as
   the later prompts make it less forgiving, and the mode would stop meaning anything.
   Design 17.1. */
function fold(log, now, difficultyMultiplier){
  const DM = difficultyMultiplier || 1;
  const st={
    phase:CASE.phases[0].id, flags:new Set(), ordered:new Set(), resulted:new Set(), taken:new Set(),
    /* Two sets, because they answer two different questions and conflating them put a
       pressed highlight on a button nobody had pressed.

       `taken` is what the resident did: one entry per button, and it is what the action
       grid reads to draw a control as already used.

       `satisfied` is what has been accomplished: `taken`, plus the covering action of
       anything performed through an also_covers group. A case that binds digoxin,
       amiodarone and metoprolol into one act is asserting that any of them discharges
       it, so giving one has to satisfy the critical action, discharge a follow-up that
       names it, suppress its prompt and make `action X taken` true. None of that means
       the other two buttons were pressed. */
    satisfied:new Set(),
    /* How many times each counter has been administered. Not in the condition language
       and not in the snapshot: a case reads it only through the flag it grants, which is
       what keeps the per-key review matrix finite. */
    adminCount:{},
    orders:{}, phaseEntry:{}, phaseSeq:[], halted:null, complete:null, earlyExit:null,
    /* The third ending. `halted` is a harmful action, `complete` is a handoff, and
       `failed` is the clock walking the case into a terminal phase that is neither.
       Before this existed a case authoring allow_time_to_terminal reached its arrest
       phase and then simply kept running: the monitor showed the last numbers before
       output was lost, the clock carried on, and the interface never noticed the
       patient had died. Set in the fold from the phase table, so no engine code names
       a phase and no case implements an ending. */
    failed:null,
    nurse:[], readouts:[], blocked:[], timeline:[], prompted:new Set(),
    promptFires:[], fuFires:[], fuOutstanding:new Set(), handoff:null, now:now, dm:DM,
    expected:new Set(), expectedByPhase:{}, recommendedTaken:new Set(), defaultsServed:new Set(),
    /* Section 7.3's fifth tier. It was defined in the spec, authored by MGCA on 31
       tag rules, recorded on the timeline, and then read by nothing: the debrief
       surfaced critical, recommended, harmful and the neutral traps, so a
       discouraged action produced no output at all. A tier that carries no weight
       is the defect the tier was added to fix. */
    discouragedTaken:new Set(),
    /* v0.6. guardTrue records when a measured_from:"guard_true" rule first held, so a
       delayed consequence is timed from the action rather than from phase entry.
       timeFires is what the debrief reads to name the deadline that expired. */
    guardTrue:{}, timeFires:[],
    /* v0.7. monitoring is the moment an action carrying the catalog's reveals_vitals
       capability was taken. Until then the interface has no numbers to show and no
       heartbeat to play, because the resident has not put a monitor on the patient.
       It is derived, not authored: no case names it and no case can turn it off. */
    monitoring:null,
    /* v0.7. One record per administration of an action carrying vital_effects, in log
       order. What is ACTIVE at a given moment is derived from these by activeEffects
       below, so a thirty-second effect expires without anything having to be scheduled. */
    vitalFx:[], vitalEffects:[], vitals:null,
    /* v0.8. A flag that lapses. flagGrants records, per flag, whether some action has
       granted it permanently and the latest moment a timed grant runs to; the flag is
       removed only when no live grant remains. flagExpiries is what the debrief and the
       tests read to name the moment something wore off. See expiringFlags below. */
    flagGrants:{}, flagExpiries:[]
  };
  st.phaseEntry[st.phase]=0;
  st.phaseSeq.push({id:st.phase,t:0});

  const ev=[]; let evseq=0;
  const push=(e)=>{ e._s=evseq++; e.done=false; ev.push(e); };
  const promptCount={};

  function onPhaseEntry(phase,t){
    scheduleDeadlines(phase,t);
    const entrySt=snapshot(st); entrySt.phase=phase;
    for(const id in ACT){
      const a=ACT[id];
      /* An entry covered through also_covers borrows another action's case fields so
         that a tag cannot be escaped by choosing a sibling. It must not borrow the
         prompt or the expectation: the resident performs the act once, and four
         entries prompting for one act both nags and consumes the per-phase prompt cap.
         That defect suppressed the glucocorticoid prompt in MGCA and left a
         deterioration unwarned, which is the thing the cap must never do. */
      if(a.covered_by) continue;
      if(a.tag&&tagOf(id,entrySt)==='critical'){
        st.expected.add(id);
        (st.expectedByPhase[phase]=st.expectedByPhase[phase]||new Set()).add(id);
      }
      if(!a.prompt) continue;
      if(tagOf(id,entrySt)!=='critical') continue;
      push({t:t+a.prompt.deadline_seconds*DM,kind:'prompt',id,phase,level:1});
      if(a.prompt.escalation)
        push({t:t+a.prompt.escalation.deadline_seconds*DM,kind:'prompt',id,phase,level:2});
    }
  }
  function cancelPromptsFor(phase){
    for(const e of ev) if((e.kind==='prompt'||e.kind==='deadline')&&e.phase===phase&&!e.done)
      e.done=true;
  }
  /* A time-guarded deadline joins the same schedule as prompts and results. No new
     loop: the fold already merges log entries and derived events in timestamp order,
     and the 5.3 tiebreak (log entries first at equal timestamps) means a resident who
     gets the drug in on the deadline is credited. */
  function scheduleDeadlines(phase,t){
    const p=PHASE[phase];
    if(!p||!p.transitions) return;
    for(let i=0;i<p.transitions.length;i++){
      const tr=p.transitions[i];
      if(tr.after_seconds===undefined) continue;
      if((tr.measured_from||'phase_entry')!=='guard_true'){
        push({t:t+tr.after_seconds,kind:'deadline',phase});
        continue;
      }
      /* A guard_true rule is timed from the moment its guard first holds, which is
         usually later than phase entry, so a deadline scheduled here would fire at the
         wrong time. Two cases. If the guard ALREADY holds on entry -- the resident gave
         the drug in the phase before this one -- the clock starts now and the deadline
         is real. Otherwise transitionDue schedules it at the moment the guard first
         holds. Without both, a guard_true transition could only ever fire on the
         resident's next action, so a case authoring "this takes a minute to work" left
         a resident who gave the drug and then waited watching nothing happen. */
      let holds; try{ holds=test(tr.when,st); }catch(e){ holds=false; }
      if(!holds) continue;
      const k=phase+'|'+i;
      if(st.guardTrue[k]===undefined) st.guardTrue[k]=t;
      push({t:st.guardTrue[k]+tr.after_seconds,kind:'deadline',phase});
    }
  }
  function enterPhase(to,t){
    cancelPromptsFor(st.phase);
    st.phase=to;
    st.phaseEntry[to]=t;
    st.phaseSeq.push({id:to,t});
    if(!PHASE[to].terminal) onPhaseEntry(to,t);
    /* Completion is recorded here rather than after each call site. It used to be
       tested only in applyLog, so a case that authored a time-guarded transition into
       case_complete reached the phase without the run ever being marked complete, and
       the same hole opened again for every new kind of timed event. One place. */
    if(to==='case_complete') st.complete={t};
  }
  /* v0.6: a transition rule may carry after_seconds. It matches only when its guard
     holds AND the deadline has passed, measured from phase entry by default or from
     the moment the guard first became true. A rule without after_seconds is
     instantaneous and behaves exactly as it did in v0.5, so a case that authors none
     is bit-identical. Design 2.1a. */
  function transitionDue(tr,idx,t){
    if(tr.after_seconds===undefined) return true;
    if((tr.measured_from||'phase_entry')==='guard_true'){
      const k=st.phase+'|'+idx;
      if(st.guardTrue[k]===undefined){
        st.guardTrue[k]=t;
        /* The deadline this rule needs did not exist until now, because at phase entry
           the guard was false. Scheduled once, on the first check that finds it true. */
        push({t:t+tr.after_seconds,kind:'deadline',phase:st.phase});
      }
      return t-st.guardTrue[k] >= tr.after_seconds;
    }
    return t-(st.phaseEntry[st.phase]||0) >= tr.after_seconds;
  }
  function checkTransitions(t){
    const p=PHASE[st.phase];
    if(!p||!p.transitions) return;
    for(let i=0;i<p.transitions.length;i++){
      const tr=p.transitions[i];
      if(!test(tr.when,st)) continue;
      if(!transitionDue(tr,i,t)) continue;
      if(tr.to!==st.phase){
        if(tr.after_seconds!==undefined){
          /* The only place a nurse line may describe a trajectory, because one has
             just happened and the monitor is about to show it. Design 2.2. Emitted
             on its own kind so the no-trajectory assertion on prompts stays valid. */
          if(tr.narration) narrate(t,tr.narration,'deterioration');
          st.timeFires.push({t,from:st.phase,to:tr.to,after:tr.after_seconds,
                             when:tr.when,note:tr.debrief_note||''});
        }
        enterPhase(tr.to,t);
      }
      return;
    }
  }

  onPhaseEntry(st.phase,0);

  let li=0;
  for(;;){
    if(st.halted||st.complete||st.earlyExit) break;
    const L=(li<log.length&&log[li].t<=now)?log[li]:null;
    let E=null;
    for(const e of ev){ if(!e.done&&e.t<=now&&(!E||e.t<E.t||(e.t===E.t&&e._s<E._s))) E=e; }
    if(!L&&!E) break;
    let takeLog;
    if(!E) takeLog=true; else if(!L) takeLog=false; else takeLog=(L.t<=E.t);
    if(takeLog){ applyLog(log[li],log[li].t); li++; }
    else { E.done=true; applyEvent(E,E.t); }
  }

  function narrate(t,text,kind){ if(text) st.nurse.push({t,text,kind:kind||'narration'}); }

  /* An obligation is discharged when a listed action has been performed, or when an
     authored condition holds. The second exists because `satisfied_by` is set
     membership and cannot express "again": an obligation to repeat a dose is already
     satisfied by the dose that created it. Either alone is enough; a follow-up with
     neither is never satisfiable and the validator refuses it. */
  function fuSatisfied(f,state){
    if(f.satisfied_by&&f.satisfied_by.some(x=>state.satisfied.has(x))) return true;
    if(f.satisfied_when){
      try{ return test(f.satisfied_when,state); }catch(e){ return false; }
    }
    return false;
  }

  /* ---------- flag grants (design 2.7) ----------
     A permanent grant is absorbing: once any action has set a flag without a duration,
     no later timed grant can take it away, because the permanent one is still true. A
     timed grant extends the flag to the later of its own expiry and any expiry already
     standing, so a second dose refreshes rather than shortening. */
  function grantFlag(f,t,duration){
    st.flags.add(f);
    const g=st.flagGrants[f]||(st.flagGrants[f]={permanent:false,until:-Infinity});
    if(duration===null||duration===undefined){ g.permanent=true; return; }
    if(g.permanent) return;
    const until=t+duration;
    if(until>g.until) g.until=until;
    push({t:until,kind:'flag_expire',flag:f});
  }

  function applyLog(entry,t){
    const id=entry.actionId;
    const a=ACT[id];

    if(entry.kind==='early_exit'){
      st.earlyExit={t}; st.timeline.push({t,id:'early_exit',type:'end',label:'Ended the case early'});
      return;
    }
    if(entry.kind==='interview'){
      const G=CASE.interview.global_answer_rules||[];
      const T=entry.topic?CASE.interview.topics.find(x=>x.topic===entry.topic):null;
      const rules=G.concat(T?T.answer:CASE.interview.out_of_scope_fallback);
      const ans=resolve(rules,st);
      st.timeline.push({t,id:'interview:'+(entry.topic||'unmatched'),type:'observational',
        label:entry.topic?('Asked about '+entry.topic.replace(/_/g,' ')):'Question not understood'});
      st.readouts.push({t,kind:'speech',key:entry.topic||'unmatched',title:entry.q,body:ans,
        matched:entry.topic||null});
      if(entry.topic&&ACT['interview_topic_'+entry.topic]){
        st.taken.add('interview_topic_'+entry.topic);
        st.satisfied.add('interview_topic_'+entry.topic);
      }
      return;
    }
    if(!a) return;

    /* prerequisite checker: the condition is a requirement that must hold */
    for(const pr of (a.prerequisites||[])){
      let ok;
      try{ ok=test(pr.when,st); }catch(e){ ok=true; }   // unparseable catalog condition
      if(!ok){
        st.blocked.push({t,id,message:pr.failure_message,source:pr.origin||a.prerequisite_source});
        st.timeline.push({t,id,type:'blocked',label:'Blocked: '+dispName(id)});
        narrate(t,pr.failure_message,'blocked');
        return;
      }
    }

    st.taken.add(id);
    st.satisfied.add(id);
    /* An entry covered through also_covers borrows the covering action's tag, flags and
       note, so it already advances the case and is scored the same way. It was not
       recorded as having satisfied the covering action itself, which meant the debrief
       listed the critical action as missed by a resident who had performed it by another
       route, and `action X taken` was false after a sibling. Coverage is the case
       asserting the two acts are the same act; recording both is what that assertion
       means. It goes only into `satisfied`: putting it into `taken` as well drew the
       covering action's button as though the resident had pressed that one too. */
    if(a.covered_by) st.satisfied.add(a.covered_by);

    /* Catalog capability, checked before the state-changing split so an act that
       reveals the vitals does so whether or not it changes the patient. */
    if(a.reveals_vitals && !st.monitoring) st.monitoring={t,id};

    if(!stateChanging(id)){
      if(IS_EXAM(id)){
        const r=CONTENT[id]?{value:resolve(CONTENT[id],st),source:'case'}
                           :{value:(ACT[id]||{}).default_result||null,source:'catalog_default'};
        st.readouts.push({t,kind:'exam',key:id,title:dispName(id),
          body:r.value,source:r.source});
        if(r.source!=='case') st.defaultsServed.add(id);
      } else if(IS_CONSULT(id)){
        st.readouts.push({t,kind:'consult',key:id,title:dispName(id),
          body: CONTENT[id]?resolve(CONTENT[id],st):PROTO.globalConsultant,
          source: CONTENT[id]?'case':'catalog_default'});
        if(!CONTENT[id]) st.defaultsServed.add(id);
      }
      st.timeline.push({t,id,type:'observational',label:dispName(id)});
      return;
    }

    const tag=tagOf(id,st);
    st.timeline.push({t,id,type:'state-changing',label:dispName(id),tag});

    if(tag==='harmful'){
      st.halted={t,id,reason:a.halt_reason||'This action halted the case.'};
      enterPhase('halted',t);
      narrate(t,a.halt_reason||'',"halt");
      return;
    }
    if(tag==='recommended') st.recommendedTaken.add(id);
    if(tag==='discouraged') st.discouragedTaken.add(id);
    narrate(t,narrationFor(id),'narration');
    /* On its own kind, so the assertion that no PROMPT describes a trajectory is
       unaffected by it and so the interface can colour it and file it in the chart. Said
       once per administration, which is right: a resident who redoses should hear it
       again. */
    if(a.nurse_alert) narrate(t,a.nurse_alert,'alert');

    (a.flags_set||[]).forEach(f=>grantFlag(f,t,null));
    for(const fr of (a.flags_set_repeat||[])){
      /* The counter defaults to the act rather than to the button, so a sibling covered
         through also_covers counts toward the same total. */
      const key=fr.counter||a.covered_by||id;
      st.adminCount[key]=(st.adminCount[key]||0)+1;
      if(st.adminCount[key]>=fr.after_administrations) grantFlag(fr.flag,t,null);
    }
    for(const tf of (a.flags_set_timed||[])) grantFlag(tf.flag,t,tf.duration_seconds);

    /* An administration, not an effect. Whether it is still acting is decided later,
       against the clock and against its guard, so a repeat dose refreshes rather than
       stacks and a stopped drip stops mattering without a second log entry. */
    for(const fx of (a.vital_effects||[]))
      st.vitalFx.push({t,id,vital:fx.vital,delta:fx.delta,
                       key:fx.key||id,
                       onset:fx.onset_seconds===undefined?null:fx.onset_seconds,
                       duration:fx.duration_seconds===undefined?null:fx.duration_seconds,
                       guard:fx.while===undefined?null:fx.while});

    if(IS_CONSULT(id)){
      st.readouts.push({t,kind:'consult',key:id,title:dispName(id),
        body: CONTENT[id]?resolve(CONTENT[id],st):PROTO.globalConsultant,
        source: CONTENT[id]?'case':'catalog_default'});
      if(!CONTENT[id]) st.defaultsServed.add(id);
    }

    if(IS_STUDY(id)){
      st.ordered.add(id);
      const due=t+turnaround(id);
      const rec={orderT:t,dueT:due,snap:snapshot(st),value:null,source:null};
      (st.orders[id]=st.orders[id]||[]).push(rec);
      push({t:due,kind:'result',id,rec});
    }

    (a.follow_ups_triggered||[]).forEach(fid=>{
      const f=FU[fid]; if(!f) return;
      push({t:t+f.deadline_seconds*DM,kind:'followup',fid});
    });

    if(id==='handoff_submit') st.handoff=entry.payload||null;

    checkTransitions(t);
  }

  function applyEvent(e,t){
    if(e.kind==='result'){
      const r=resolveResult(e.id,e.rec.snap);
      e.rec.value=r.value; e.rec.source=r.source;
      if(r.source==='catalog_default') st.defaultsServed.add(e.id);
      st.resulted.add(e.id);
      const a=ACT[e.id]||{};
      const tmpl={lab:'{name} is back.',imaging:'{name} is up on the screen.',
                  ecg:'{name} is up.',bedside:'{name} is done.'}[a.turnaround_class]||'{name} is back.';
      /* Leads with the name, so it goes through the same sentence rule as the rest. */
      narrate(t,sentence(tmpl.replace('{name}',dispName(e.id))),'result');
      return;
    }
    if(e.kind==='prompt'){
      if(st.satisfied.has(e.id)) return;
      const a=ACT[e.id];
      if(a.prompt.guard&&!test(a.prompt.guard,st)) return;
      promptCount[e.phase]=(promptCount[e.phase]||0);
      if(promptCount[e.phase]>=PROTO.promptCap) return;
      promptCount[e.phase]++;
      narrate(t,e.level===2?a.prompt.escalation.text:a.prompt.text,'prompt');
      st.prompted.add(e.id);
      st.promptFires.push({t,id:e.id,level:e.level});
      return;
    }
    if(e.kind==='deadline'){ checkTransitions(t); return; }
    /* A flag lapsing is a state change with no log entry behind it, which is the whole
       point: the resident did nothing and something stopped working. It has to re-check
       transitions for the same reason a deadline does, or a case could author "when the
       drug is no longer acting, deteriorate" and have it fire only if the resident
       happened to press something afterwards. */
    if(e.kind==='flag_expire'){
      const g=st.flagGrants[e.flag];
      if(!g||g.permanent) return;
      /* A later grant supersedes this expiry. The superseding grant pushed its own
         event, so nothing is lost by returning here. */
      if(g.until>t) return;
      if(!st.flags.has(e.flag)) return;
      st.flags.delete(e.flag);
      st.flagExpiries.push({t,flag:e.flag});
      checkTransitions(t);
      return;
    }
    if(e.kind==='followup'){
      const f=FU[e.fid];
      if(f.applies_when&&!test(f.applies_when,st)) return;
      if(fuSatisfied(f,st)) return;
      promptCount[st.phase]=(promptCount[st.phase]||0)+1;
      narrate(t,f.nurse_prompt,'prompt');
      st.fuFires.push({t,fid:e.fid});
      st.fuOutstanding.add(e.fid);
      return;
    }
  }

  st.pending=[];
  Object.keys(st.orders).forEach(id=>st.orders[id].forEach(o=>{
    if(o.value===null) st.pending.push({id,dueT:o.dueT,orderT:o.orderT});
  }));
  st.fuOutstanding.forEach(fid=>{
    const f=FU[fid];
    if(fuSatisfied(f,st)) st.fuOutstanding.delete(fid);
  });
  st.vitalEffects = activeEffects(st, now);
  st.vitals = effectiveVitals(st);
  /* Terminal by the clock. Tested after everything else so `halted`, `complete` and
     `earlyExit` win: those three carry their own reason and their own debrief, and a
     run that ended by one of them is not additionally a failure. The interface decides
     how long to hold the monitor on the terminal numbers before it ends the run; the
     engine only reports that the run is over and when the phase was entered. */
  if(!st.halted && !st.complete && !st.earlyExit
     && PHASE[st.phase] && PHASE[st.phase].terminal)
    st.failed={phase:st.phase, t:st.phaseEntry[st.phase],
               reason:PHASE[st.phase].timeout_reason||''};
  return st;
}

/* ---------- vital effects (design 2.3) ----------
   A phase authors the patient's baseline. An action may move one number off that
   baseline for as long as it is acting. The two are separate on purpose: a phase is a
   clinical state and is entered once, so it cannot express "for the next thirty
   seconds", and it cannot express an effect that is undone when the drip is stopped or
   when the patient is intubated.

   Three rules, and they are the whole mechanism:

   DURATION. duration_seconds absent means the effect lasts as long as its guard holds.
   Present, it lapses that many seconds after the administration.

   GUARD. `while` is an ordinary section 4 condition, evaluated against the state as it
   now stands. An effect whose guard has gone false is simply not in the list.

   KEY. Effects sharing a key do not stack: the most recent administration wins. The key
   defaults to the action id, so giving the same drug twice refreshes its effect rather
   than doubling it. Two routes to the same drug should be given the same explicit key,
   for the same reason a harmful tag has to cover every route to the same act.

   Terminal phases are exempt. halted and case_complete author the numbers a reader is
   meant to be left looking at, and an effect still running when the case ends would
   edit the ending. */
const VITAL_BOUNDS={heart_rate:[0,300],systolic_bp:[0,300],diastolic_bp:[0,300],
                    oxygen_saturation:[0,100],respiratory_rate:[0,80],temperature_c:[25,45]};
function activeEffects(st, now){
  const byKey=new Map();
  for(const fx of st.vitalFx){
    /* Both windows are measured from the administration, which is one rule rather than
       two and is why the validator refuses a duration that does not outlast its onset.
       The active window is [t + onset, t + duration). */
    if(fx.onset!==null && now-fx.t < fx.onset) continue;
    if(fx.duration!==null && now-fx.t >= fx.duration) continue;
    if(fx.guard){
      let ok; try{ ok=test(fx.guard,st); }catch(e){ ok=true; }
      if(!ok) continue;
    }
    const prev=byKey.get(fx.key);
    if(!prev||fx.t>=prev.t) byKey.set(fx.key,fx);
  }
  return [...byKey.values()];
}
/* What the monitor should read. Display and audio both take their numbers from here;
   nothing else in the engine does, because vitals do not enter the condition language
   and a study still reports the phase baseline for the moment it was ordered. */
function effectiveVitals(st){
  const p=PHASE[st.phase];
  const base=p?p.vitals:null;
  if(!base) return null;
  if(p.terminal||!st.vitalEffects.length) return base;
  const out={};
  for(const k in base) out[k]=base[k];
  for(const fx of st.vitalEffects){
    if(typeof out[fx.vital]!=='number') continue;
    const b=VITAL_BOUNDS[fx.vital]||[-Infinity,Infinity];
    out[fx.vital]=Math.min(b[1],Math.max(b[0],out[fx.vital]+fx.delta));
  }
  if(typeof out.temperature_c==='number') out.temperature_c=Math.round(out.temperature_c*10)/10;
  return out;
}

/* A catalog display name is Title Case because it is a button, and a button's label
   shouts when it is dropped into the middle of a sentence. Lowercasing the whole of it
   was the first fix and it broke the other half: "Normal Saline 1L bolus" became "1l",
   "Furosemide 40 mg IV" became "iv", and "Ringer's" lost a proper noun.

   Only tokens that are ordinary Title Case are lowered. A token carrying a digit, an
   internal capital, an apostrophe or a slash is left exactly as the catalog wrote it,
   because every one of those is a unit, an acronym or a name, and none of them was
   capitalised to look like a button. A hyphenated pair of ordinary words is Title Case
   too, so "Non-Invasive" lowers and "BiPAP/CPAP" does not. */
function softLower(name){
  return String(name||'').split(' ')
    .map(w => /^[A-Z][a-z]+(-[A-Z][a-z]+)*$/.test(w) ? w.toLowerCase() : w)
    .join(' ');
}

/* Some templates lead with the name, so the first word of the sentence is whatever
   softLower left behind. A sentence starts with a capital. */
function sentence(t){
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
}

function narrationFor(id){
  const a=ACT[id]||{};
  if(a.narration_override) return a.narration_override;
  if(a.narration_template){
    /* Dose entry is not implemented, so {dose} is dropped rather than faked. Dropping the
       word and leaving the grammar around it produced "Giving of ceftriaxone", because the
       preposition belongs to the dose and not to the drug. The slot is removed together
       with whatever joins it to the name, in both directions, so "Giving {dose} of {name}"
       becomes "Giving ceftriaxone" and "Starting {name} at {dose}" becomes "Starting
       noradrenaline". If doses are ever implemented, this collapse is the thing to remove
       rather than to work around. */
    return sentence(a.narration_template
             .replace(/\{dose\}\s+of\s+/g,'')
             .replace(/\s+at\s+\{dose\}/g,'')
             .replace(/\{dose\}/g,'')
             .replace('{name}',softLower(a.name))
             .replace(/\s{2,}/g,' ').trim());
  }
  if(IS_STUDY(id)) return sentence(dispName(id))+' is away.';
  return 'Okay: '+softLower(dispName(id))+'.';
}
